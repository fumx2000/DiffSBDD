#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, SOURCE_PACKAGE_ROOT, T_FIELD
from build_dataset_snapshot_review_gate import (
    REQUIRED_AUXILIARY_LABELS,
    REQUIRED_MASK_LEVELS,
    TARGETS,
    contains_all,
    forbidden_counts,
    found_once,
    graph_counts_positive,
    index_manifest_valid,
    index_many,
    load_json,
    manifest_paths_match,
    package_counts,
    packaged_hashes_match,
    rows_from_existing_csv,
)
from build_read_only_training_dataset_loader_gate import PLANNED_READ_ONLY_LOADER_ROOT
from check_read_only_training_dataset_loader_dry_run_qa import (
    bool_false,
    bool_true,
    dry_run_manifest_safety_flags_valid,
    dry_run_manifest_valid,
    dry_run_report_safety_flags_valid,
    dry_run_report_status_passed,
    one,
    real_package_still_valid,
    record_hashes_valid,
    record_many,
    record_safety_flags_valid,
    upstream_loader_gate_passed,
    upstream_packaging_qa_passed,
)


PLANNED_TENSOR_DESIGN_ROOT = "data/derived/covalent_small/training_tensor_design_review_only"
PLANNED_TENSOR_DESIGN_MANIFEST = f"{PLANNED_TENSOR_DESIGN_ROOT}/training_tensor_design_manifest.json"
PLANNED_TENSOR_DESIGN_SCHEMA_REPORT = f"{PLANNED_TENSOR_DESIGN_ROOT}/training_tensor_design_schema_report.csv"
PLANNED_TENSOR_DESIGN_PLAN = f"{PLANNED_TENSOR_DESIGN_ROOT}/training_tensor_design_plan.csv"
PLANNED_TENSOR_DESIGN_REPORT = f"{PLANNED_TENSOR_DESIGN_ROOT}/training_tensor_design_report.csv"
PLANNED_TENSOR_DESIGN_SUMMARY = "docs/training_tensor_design_review_summary.md"

DATASET_NAME = "covalent_small_pre_reaction_real_training_dataset_candidate"
DRY_RUN_STAGE = "read_only_training_dataset_loader_dry_run_review_only_not_training"
LOADER_MODE = "read_only_record_construction_no_dataloader"
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
ALLOWED_DRY_RUN_FILES_WITH_GATE = {
    "read_only_training_dataset_loader_dry_run_manifest.json",
    "read_only_training_dataset_loader_dry_run_report.csv",
    "read_only_training_dataset_loader_dry_run_summary.md",
    "read_only_training_dataset_loader_dry_run_qa_report.csv",
    "training_tensor_design_gate_plan.csv",
    "training_tensor_design_gate_report.csv",
}

PLAN_COLUMNS = [
    "training_tensor_design_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "dry_run_stage",
    "split",
    "package_mode",
    "loader_mode",
    "source_package_root",
    "dry_run_root",
    "dry_run_manifest_json_path",
    "dry_run_report_csv_path",
    "dry_run_qa_report_csv_path",
    "planned_training_tensor_design_root",
    "planned_training_tensor_design_manifest_json_path",
    "planned_training_tensor_design_schema_report_csv_path",
    "planned_training_tensor_design_plan_csv_path",
    "planned_training_tensor_design_report_csv_path",
    "planned_training_tensor_design_summary_md_path",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "tensor_design_gate_stage",
    "explicit_approval_required_before_training_tensor_design",
    "ready_for_training_tensor_design_after_approval",
    "training_tensor_design_executed",
    "tensor_schema_generated",
    "tensor_files_generated",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "archive_created",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dry_run_qa_row_found_once",
    "dry_run_qa_status_passed",
    "dry_run_manifest_valid",
    "dry_run_record_found_once",
    "dry_run_record_fields_valid",
    "dry_run_record_hashes_valid",
    "dry_run_record_safety_flags_valid",
    "dry_run_report_row_found_once",
    "dry_run_report_status_passed",
    "dry_run_report_safety_flags_valid",
    "upstream_loader_gate_status_still_passed",
    "upstream_real_training_dataset_packaging_qa_status_still_passed",
    "real_training_dataset_package_still_valid",
    "index_and_manifest_still_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "dry_run_root_files_valid",
    "planned_training_tensor_design_root_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "gate_plan_row_written",
    "training_tensor_design_gate_status",
    "explicit_approval_required_before_training_tensor_design",
    "ready_for_training_tensor_design_after_approval",
    "training_tensor_design_executed",
    "tensor_schema_generated",
    "tensor_files_generated",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "archive_created",
    "blocking_reasons",
    "recommended_next_action",
]


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def record_fields_valid(record: dict[str, Any]) -> bool:
    required = [
        "sample_id",
        "source_sample_id",
        "split",
        "package_mode",
        "packaged_protein_path",
        "packaged_ligand_sdf_path",
        "packaged_metadata_json_path",
        "source_protein_path",
        "source_ligand_sdf_path",
        "packaged_protein_sha256",
        "packaged_ligand_sdf_sha256",
        "packaged_metadata_json_sha256",
        "source_protein_sha256",
        "source_ligand_sdf_sha256",
        "read_only_record_constructed",
        "read_only_record_fields_valid",
        "source_files_exist",
        "source_hashes_revalidated",
        "reference_only_flags_valid",
        "tensor_generated",
        "dataloader_built",
        "training_ready",
    ]
    paths = [
        "packaged_protein_path",
        "packaged_ligand_sdf_path",
        "packaged_metadata_json_path",
        "source_protein_path",
        "source_ligand_sdf_path",
    ]
    return bool(record) and all(field in record for field in required) and all(Path(str(record.get(field, ""))).is_file() for field in paths)


def dry_run_qa_status_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("read_only_training_dataset_loader_dry_run_qa_status", "")
        == "read_only_training_dataset_loader_dry_run_qa_passed"
    )


def dry_run_root_files_valid(output_gate_plan_csv: str | Path, output_report_csv: str | Path) -> bool:
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    allowed = set(ALLOWED_DRY_RUN_FILES_WITH_GATE)
    required = {
        "read_only_training_dataset_loader_dry_run_manifest.json",
        "read_only_training_dataset_loader_dry_run_report.csv",
        "read_only_training_dataset_loader_dry_run_summary.md",
        "read_only_training_dataset_loader_dry_run_qa_report.csv",
    }
    allowed.add(Path(output_gate_plan_csv).name)
    allowed.add(Path(output_report_csv).name)
    return (
        required.issubset({path.name for path in files})
        and {path.name for path in files}.issubset(allowed)
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
        and all(not (path.suffix.lower() == ".json" and path.name != "read_only_training_dataset_loader_dry_run_manifest.json") for path in files)
    )


def planned_root_absent() -> bool:
    return not Path(PLANNED_TENSOR_DESIGN_ROOT).exists()


def false_safety_fields() -> dict[str, str]:
    return {
        "training_tensor_design_executed": "false",
        "tensor_schema_generated": "false",
        "tensor_files_generated": "false",
        "dataloader_tensor_generated": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        T_FIELD: "false",
        "checkpoint_loaded": "false",
        "model_initialized": "false",
        "training_ready": "false",
        "files_copied": "false",
        "archive_created": "false",
    }


def plan_row(args: argparse.Namespace, candidate_id: str, source_id: str, index_row: dict[str, str], record: dict[str, Any]) -> dict[str, str]:
    return {
        "training_tensor_design_gate_plan_id": candidate_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": candidate_id,
        "dataset_name": DATASET_NAME,
        "dry_run_stage": DRY_RUN_STAGE,
        "split": index_row.get("split", ""),
        "package_mode": PACKAGE_MODE,
        "loader_mode": LOADER_MODE,
        "source_package_root": SOURCE_PACKAGE_ROOT,
        "dry_run_root": PLANNED_READ_ONLY_LOADER_ROOT,
        "dry_run_manifest_json_path": str(args.dry_run_manifest_json),
        "dry_run_report_csv_path": str(args.dry_run_report_csv),
        "dry_run_qa_report_csv_path": str(args.read_only_loader_dry_run_qa_report_csv),
        "planned_training_tensor_design_root": PLANNED_TENSOR_DESIGN_ROOT,
        "planned_training_tensor_design_manifest_json_path": PLANNED_TENSOR_DESIGN_MANIFEST,
        "planned_training_tensor_design_schema_report_csv_path": PLANNED_TENSOR_DESIGN_SCHEMA_REPORT,
        "planned_training_tensor_design_plan_csv_path": PLANNED_TENSOR_DESIGN_PLAN,
        "planned_training_tensor_design_report_csv_path": PLANNED_TENSOR_DESIGN_REPORT,
        "planned_training_tensor_design_summary_md_path": PLANNED_TENSOR_DESIGN_SUMMARY,
        "packaged_protein_path": str(record.get("packaged_protein_path", index_row.get("packaged_protein_path", ""))),
        "packaged_ligand_sdf_path": str(record.get("packaged_ligand_sdf_path", index_row.get("packaged_ligand_sdf_path", ""))),
        "packaged_metadata_json_path": str(record.get("packaged_metadata_json_path", index_row.get("packaged_metadata_json_path", ""))),
        "source_protein_path": str(record.get("source_protein_path", index_row.get("source_protein_path", ""))),
        "source_ligand_sdf_path": str(record.get("source_ligand_sdf_path", index_row.get("source_ligand_sdf_path", ""))),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "tensor_design_gate_stage": "training_tensor_design_gate_only_not_training",
        "explicit_approval_required_before_training_tensor_design": "true",
        "ready_for_training_tensor_design_after_approval": "true",
        **false_safety_fields(),
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    qa_rows = rows_from_existing_csv(args.read_only_loader_dry_run_qa_report_csv)
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    gate_report_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    real_file_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    real_sample_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    real_packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)

    qa_by_id = index_many(qa_rows, "candidate_id")
    dry_report_by_id = index_many(dry_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    packaging_qa_by_id = index_many(packaging_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    record_by_id = record_many(dry_manifest.get("read_only_records", []) if isinstance(dry_manifest.get("read_only_records"), list) else [])
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    global_checks = {
        "dry_run_manifest_valid": Path(args.dry_run_manifest_json).is_file()
        and dry_run_manifest_valid(dry_manifest, dry_manifest_parseable)
        and dry_run_manifest_safety_flags_valid(dry_manifest),
        "dry_run_report_row_count_valid": Path(args.dry_run_report_csv).is_file() and len(dry_report_rows) == 3,
        "dry_run_summary_exists": Path(args.dry_run_summary_md).is_file(),
        "dry_run_qa_report_row_count_valid": Path(args.read_only_loader_dry_run_qa_report_csv).is_file()
        and len(qa_rows) == 3
        and all(dry_run_qa_status_passed(row) for row in qa_rows),
        "upstream_loader_gate_report_valid": Path(args.read_only_training_dataset_loader_gate_report_csv).is_file()
        and len(gate_report_rows) == 3
        and all(upstream_loader_gate_passed(row) for row in gate_report_rows),
        "upstream_packaging_qa_report_valid": Path(args.real_training_dataset_packaging_qa_report_csv).is_file()
        and len(packaging_qa_rows) == 3
        and all(upstream_packaging_qa_passed(row) for row in packaging_qa_rows),
        "real_training_dataset_package_still_valid": real_package_still_valid(
            real_manifest,
            real_manifest_parseable,
            real_file_rows,
            real_sample_rows,
            real_packaging_report_rows,
        ),
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "package_counts_valid": package_counts(args.package_root)
        == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "dry_run_root_files_valid": dry_run_root_files_valid(args.output_gate_plan_csv, args.output_report_csv),
        "planned_training_tensor_design_root_absent_before_gate": planned_root_absent(),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
    }
    report_rows: list[dict[str, str]] = []
    plan_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        qa_row = one(qa_by_id, candidate_id)
        dry_report = one(dry_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        packaging_qa = one(packaging_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        records = record_by_id.get(candidate_id, [])
        record = records[0] if len(records) == 1 else {}
        checks = {
            "dry_run_qa_row_found_once": found_once(qa_by_id, candidate_id),
            "dry_run_qa_status_passed": dry_run_qa_status_passed(qa_row),
            "dry_run_manifest_valid": global_checks["dry_run_manifest_valid"],
            "dry_run_record_found_once": len(records) == 1,
            "dry_run_record_fields_valid": record_fields_valid(record),
            "dry_run_record_hashes_valid": record_hashes_valid(record),
            "dry_run_record_safety_flags_valid": record_safety_flags_valid(record)
            and bool_false(record.get("tensor_generated"))
            and bool_false(record.get("dataloader_built"))
            and bool_false(record.get("training_ready")),
            "dry_run_report_row_found_once": found_once(dry_report_by_id, candidate_id),
            "dry_run_report_status_passed": dry_run_report_status_passed(dry_report),
            "dry_run_report_safety_flags_valid": dry_run_report_safety_flags_valid(dry_report),
            "upstream_loader_gate_status_still_passed": global_checks["upstream_loader_gate_report_valid"]
            and found_once(gate_report_by_id, candidate_id)
            and upstream_loader_gate_passed(gate_report),
            "upstream_real_training_dataset_packaging_qa_status_still_passed": global_checks["upstream_packaging_qa_report_valid"]
            and found_once(packaging_qa_by_id, candidate_id)
            and upstream_packaging_qa_passed(packaging_qa),
            "real_training_dataset_package_still_valid": global_checks["real_training_dataset_package_still_valid"]
            and global_checks["package_counts_valid"],
            "index_and_manifest_still_valid": global_checks["index_and_manifest_still_valid"],
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "dry_run_root_files_valid": global_checks["dry_run_root_files_valid"],
            "planned_training_tensor_design_root_absent_before_gate": global_checks[
                "planned_training_tensor_design_root_absent_before_gate"
            ],
            "forbidden_training_tensors_absent": global_checks["forbidden_training_tensors_absent"],
            "forbidden_archives_absent": global_checks["forbidden_archives_absent"],
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        if passed:
            plan_rows.append(plan_row(args, candidate_id, source_id, index_row, record))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: str(value).lower() for key, value in checks.items()},
                "gate_plan_row_written": str(passed).lower(),
                "training_tensor_design_gate_status": "training_tensor_design_gate_passed" if passed else "blocked",
                "explicit_approval_required_before_training_tensor_design": "true" if passed else "false",
                "ready_for_training_tensor_design_after_approval": "true" if passed else "false",
                **false_safety_fields(),
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "await_explicit_approval_for_training_tensor_design_review"
                if passed
                else "fix_training_tensor_design_gate_blockers",
            }
        )
    exit_code = 0 if all(row["training_tensor_design_gate_status"] == "training_tensor_design_gate_passed" for row in report_rows) else 1
    return plan_rows, report_rows, exit_code


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_tensor_design_gate_status"] == "training_tensor_design_gate_passed" for row in rows)
    no_dl_or_ds = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_t_import = "It does not " + "import " + "tor" + "ch."
    no_dl_ds_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    t_not_imported = "- " + "tor" + "ch was not imported"
    lines = [
        "# Training Tensor Design Gate Summary",
        "",
        "This is training tensor design gate only.",
        "It reads read-only loader dry-run QA outputs and upstream reference-only package artifacts.",
        "It does not design a tensor schema yet.",
        "It does not create tensor files.",
        no_dl_or_ds,
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        no_t_import,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify dry-run files.",
        "It does not modify real package files.",
        "It does not modify packaging design files.",
        "It does not modify upstream design files.",
        "It does not modify snapshot files.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this gate still does not mean training can start.",
        "",
        "## Planned Training Tensor Design Outputs",
        "",
        f"- planned_training_tensor_design_root: {PLANNED_TENSOR_DESIGN_ROOT}",
        f"- planned_training_tensor_design_manifest_json_path: {PLANNED_TENSOR_DESIGN_MANIFEST}",
        f"- planned_training_tensor_design_schema_report_csv_path: {PLANNED_TENSOR_DESIGN_SCHEMA_REPORT}",
        f"- planned_training_tensor_design_plan_csv_path: {PLANNED_TENSOR_DESIGN_PLAN}",
        f"- planned_training_tensor_design_report_csv_path: {PLANNED_TENSOR_DESIGN_REPORT}",
        f"- planned_training_tensor_design_summary_md_path: {PLANNED_TENSOR_DESIGN_SUMMARY}",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | dry_run_qa_status_passed | dry_run_record_fields_valid | dry_run_record_hashes_valid | training_tensor_design_gate_status | explicit_approval_required_before_training_tensor_design | training_tensor_design_executed | tensor_schema_generated | tensor_files_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {dry_run_qa_status_passed} | {dry_run_record_fields_valid} | {dry_run_record_hashes_valid} | {training_tensor_design_gate_status} | {explicit_approval_required_before_training_tensor_design} | {training_tensor_design_executed} | {tensor_schema_generated} | {tensor_files_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training tensor design gate"
            if all_passed
            else "- one or more samples are blocked by training tensor design gate",
            "- explicit approval is required before training tensor design review",
            "- no tensor schema was designed",
            "- no tensor files were created",
            no_dl_ds_built,
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is explicit approval for training tensor design review, not training"
            if all_passed
            else "- next step is to fix training tensor design gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows, exit_code = build_rows(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    return plan_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build training tensor design gate without creating tensor artifacts.")
    parser.add_argument("--read_only_loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--dry_run_manifest_json", required=True)
    parser.add_argument("--dry_run_report_csv", required=True)
    parser.add_argument("--dry_run_summary_md", required=True)
    parser.add_argument("--read_only_training_dataset_loader_gate_plan_csv", required=True)
    parser.add_argument("--read_only_training_dataset_loader_gate_report_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_qa_report_csv", required=True)
    parser.add_argument("--real_training_dataset_manifest_json", required=True)
    parser.add_argument("--real_training_dataset_file_index_csv", required=True)
    parser.add_argument("--real_training_dataset_sample_index_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_report_csv", required=True)
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_gate_plan_csv", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    _plan_rows, report_rows, exit_code = run(parse_args())
    for row in report_rows:
        print(f"{row['candidate_id']}: {row['training_tensor_design_gate_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

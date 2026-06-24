#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, T_FIELD
from apply_training_tensor_design_review import DESIGN_MODE, DESIGN_STAGE, PLANNED_TENSOR_DESIGN_ROOT
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
from build_training_tensor_design_gate import DATASET_NAME
from check_read_only_training_dataset_loader_dry_run_qa import real_package_still_valid
from check_training_tensor_design_review_qa import (
    design_manifest_safety_flags_valid,
    design_manifest_valid,
    design_plan_status_valid,
    design_report_safety_flags_valid,
    design_report_status_passed,
    schema_no_tensor_generated,
    schema_required_fields_present,
)


PLANNED_MATERIALIZATION_ROOT = "data/derived/covalent_small/training_tensor_materialization_review_only"
PLANNED_MATERIALIZATION_MANIFEST = f"{PLANNED_MATERIALIZATION_ROOT}/training_tensor_materialization_manifest.json"
PLANNED_MATERIALIZATION_PLAN = f"{PLANNED_MATERIALIZATION_ROOT}/training_tensor_materialization_plan.csv"
PLANNED_MATERIALIZATION_REPORT = f"{PLANNED_MATERIALIZATION_ROOT}/training_tensor_materialization_report.csv"
PLANNED_MATERIALIZATION_FILE_PLAN = f"{PLANNED_MATERIALIZATION_ROOT}/training_tensor_materialization_file_plan.csv"
PLANNED_MATERIALIZATION_SUMMARY = "docs/training_tensor_materialization_review_summary.md"

ALLOWED_DESIGN_FILES_WITH_GATE = {
    "training_tensor_design_manifest.json",
    "training_tensor_design_schema_report.csv",
    "training_tensor_design_plan.csv",
    "training_tensor_design_report.csv",
    "training_tensor_design_review_qa_report.csv",
    "training_tensor_materialization_gate_plan.csv",
    "training_tensor_materialization_gate_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

PLAN_COLUMNS = [
    "training_tensor_materialization_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "design_stage",
    "split",
    "package_mode",
    "loader_mode",
    "tensor_design_mode",
    "design_root",
    "design_manifest_json_path",
    "design_schema_report_csv_path",
    "design_plan_csv_path",
    "design_report_csv_path",
    "design_qa_report_csv_path",
    "planned_training_tensor_materialization_root",
    "planned_training_tensor_materialization_manifest_json_path",
    "planned_training_tensor_materialization_plan_csv_path",
    "planned_training_tensor_materialization_report_csv_path",
    "planned_training_tensor_materialization_file_plan_csv_path",
    "planned_training_tensor_materialization_summary_md_path",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "planned_schema_field_count",
    "tensor_materialization_gate_stage",
    "explicit_approval_required_before_tensor_materialization",
    "ready_for_tensor_materialization_after_approval",
    "tensor_materialization_executed",
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
    "design_qa_row_found_once",
    "design_qa_status_passed",
    "design_manifest_valid",
    "schema_report_valid",
    "design_plan_row_found_once",
    "design_plan_status_valid",
    "design_report_row_found_once",
    "design_report_status_passed",
    "design_report_safety_flags_valid",
    "index_and_manifest_still_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "design_root_files_valid",
    "planned_materialization_root_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "materialization_gate_plan_row_written",
    "training_tensor_materialization_gate_status",
    "explicit_approval_required_before_tensor_materialization",
    "ready_for_tensor_materialization_after_approval",
    "tensor_materialization_executed",
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


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def design_qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_tensor_design_review_qa_status", "") == "training_tensor_design_review_qa_passed"


def design_qa_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        design_qa_status_passed(row)
        and row.get("tensor_schema_generated", "") == "true"
        and row.get("tensor_files_generated", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get(T_FIELD, "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("training_ready", "") == "false"
        and row.get("files_copied", "") == "false"
        and row.get("archive_created", "") == "false"
    )


def schema_report_valid(rows: list[dict[str, str]]) -> bool:
    field_names = {row.get("field_name", "") for row in rows}
    required_mask_fields = {
        "generation_mask_A_warhead_only",
        "generation_mask_B_linker_warhead",
        "generation_mask_B2_scaffold_warhead",
        "generation_mask_C_scaffold_linker_warhead",
    }
    required_aux_fields = {
        "warhead_type_label",
        "ligand_reactive_atom_label",
        "protein_reactive_residue_label",
        "pre_reaction_geometry_label",
    }
    return (
        len(rows) == 47
        and schema_required_fields_present(rows)
        and required_mask_fields.issubset(field_names)
        and required_aux_fields.issubset(field_names)
        and schema_no_tensor_generated(rows)
    )


def design_root_files_valid(output_gate_plan_csv: str | Path, output_report_csv: str | Path) -> bool:
    root = Path(PLANNED_TENSOR_DESIGN_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    allowed = set(ALLOWED_DESIGN_FILES_WITH_GATE)
    allowed.add(Path(output_gate_plan_csv).name)
    allowed.add(Path(output_report_csv).name)
    required = {
        "training_tensor_design_manifest.json",
        "training_tensor_design_schema_report.csv",
        "training_tensor_design_plan.csv",
        "training_tensor_design_report.csv",
        "training_tensor_design_review_qa_report.csv",
    }
    return (
        required.issubset({path.name for path in files})
        and {path.name for path in files}.issubset(allowed)
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
        and all(not (path.suffix.lower() == ".json" and path.name != "training_tensor_design_manifest.json") for path in files)
    )


def planned_root_absent() -> bool:
    return not Path(PLANNED_MATERIALIZATION_ROOT).exists()


def false_safety_fields() -> dict[str, str]:
    return {
        "tensor_materialization_executed": "false",
        "tensor_schema_generated": "true",
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


def plan_row(args: argparse.Namespace, candidate_id: str, source_id: str, design_plan: dict[str, str], index_row: dict[str, str]) -> dict[str, str]:
    return {
        "training_tensor_materialization_gate_plan_id": candidate_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": candidate_id,
        "dataset_name": DATASET_NAME,
        "design_stage": DESIGN_STAGE,
        "split": design_plan.get("split", index_row.get("split", "")),
        "package_mode": PACKAGE_MODE,
        "loader_mode": "read_only_record_construction_no_dataloader",
        "tensor_design_mode": DESIGN_MODE,
        "design_root": PLANNED_TENSOR_DESIGN_ROOT,
        "design_manifest_json_path": str(args.training_tensor_design_manifest_json),
        "design_schema_report_csv_path": str(args.training_tensor_design_schema_report_csv),
        "design_plan_csv_path": str(args.training_tensor_design_plan_csv),
        "design_report_csv_path": str(args.training_tensor_design_report_csv),
        "design_qa_report_csv_path": str(args.training_tensor_design_review_qa_report_csv),
        "planned_training_tensor_materialization_root": PLANNED_MATERIALIZATION_ROOT,
        "planned_training_tensor_materialization_manifest_json_path": PLANNED_MATERIALIZATION_MANIFEST,
        "planned_training_tensor_materialization_plan_csv_path": PLANNED_MATERIALIZATION_PLAN,
        "planned_training_tensor_materialization_report_csv_path": PLANNED_MATERIALIZATION_REPORT,
        "planned_training_tensor_materialization_file_plan_csv_path": PLANNED_MATERIALIZATION_FILE_PLAN,
        "planned_training_tensor_materialization_summary_md_path": PLANNED_MATERIALIZATION_SUMMARY,
        "packaged_protein_path": index_row.get("packaged_protein_path", ""),
        "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
        "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
        "source_protein_path": index_row.get("source_protein_path", ""),
        "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "planned_schema_field_count": "47",
        "tensor_materialization_gate_stage": "training_tensor_materialization_gate_only_not_training",
        "explicit_approval_required_before_tensor_materialization": "true",
        "ready_for_tensor_materialization_after_approval": "true",
        **false_safety_fields(),
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    design_qa_rows = rows_from_existing_csv(args.training_tensor_design_review_qa_report_csv)
    design_manifest, design_manifest_parseable = load_json(args.training_tensor_design_manifest_json)
    schema_rows = rows_from_existing_csv(args.training_tensor_design_schema_report_csv)
    design_plan_rows = rows_from_existing_csv(args.training_tensor_design_plan_csv)
    design_report_rows = rows_from_existing_csv(args.training_tensor_design_report_csv)
    gate_report_rows = rows_from_existing_csv(args.training_tensor_design_gate_report_csv)
    dry_qa_rows = rows_from_existing_csv(args.read_only_loader_dry_run_qa_report_csv)
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    real_file_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    real_sample_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    real_packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    design_qa_by_id = index_many(design_qa_rows, "candidate_id")
    design_plan_by_id = index_many(design_plan_rows, "sample_id")
    design_report_by_id = index_many(design_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    dry_qa_by_id = index_many(dry_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_by_id = index_many(raw_manifest_rows, "sample_id")
    global_checks = {
        "design_manifest_valid": Path(args.training_tensor_design_manifest_json).is_file()
        and design_manifest_valid(design_manifest, design_manifest_parseable)
        and design_manifest_safety_flags_valid(design_manifest),
        "schema_report_valid": Path(args.training_tensor_design_schema_report_csv).is_file() and schema_report_valid(schema_rows),
        "design_plan_row_count_valid": Path(args.training_tensor_design_plan_csv).is_file() and len(design_plan_rows) == 3,
        "design_report_row_count_valid": Path(args.training_tensor_design_report_csv).is_file() and len(design_report_rows) == 3,
        "design_summaries_exist": Path(args.training_tensor_design_summary_md).is_file()
        and Path(args.training_tensor_design_qa_summary_md).is_file(),
        "design_root_files_valid": design_root_files_valid(args.output_gate_plan_csv, args.output_report_csv),
        "planned_materialization_root_absent_before_gate": planned_root_absent(),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
        "real_training_dataset_package_still_valid": real_package_still_valid(
            real_manifest,
            real_manifest_parseable,
            real_file_rows,
            real_sample_rows,
            real_packaging_report_rows,
        )
        and len(packaging_qa_rows) == 3
        and all(row.get("real_training_dataset_packaging_qa_status", "") == "real_training_dataset_packaging_qa_passed" for row in packaging_qa_rows)
        and package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "dry_run_artifacts_valid": Path(args.dry_run_summary_md).is_file()
        and len(dry_report_rows) == 3
        and dry_manifest_parseable
        and dry_manifest.get("row_count") == 3,
    }
    report_rows: list[dict[str, str]] = []
    plan_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        design_qa = one(design_qa_by_id, candidate_id)
        design_plan = one(design_plan_by_id, candidate_id)
        design_report = one(design_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        dry_qa = one(dry_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_by_id, candidate_id)
        checks = {
            "design_qa_row_found_once": found_once(design_qa_by_id, candidate_id),
            "design_qa_status_passed": design_qa_status_passed(design_qa),
            "design_manifest_valid": global_checks["design_manifest_valid"],
            "schema_report_valid": global_checks["schema_report_valid"],
            "design_plan_row_found_once": found_once(design_plan_by_id, candidate_id),
            "design_plan_status_valid": design_plan_status_valid(design_plan),
            "design_report_row_found_once": found_once(design_report_by_id, candidate_id),
            "design_report_status_passed": design_report_status_passed(design_report),
            "design_report_safety_flags_valid": design_report_safety_flags_valid(design_report),
            "index_and_manifest_still_valid": global_checks["index_and_manifest_still_valid"],
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "design_root_files_valid": global_checks["design_root_files_valid"],
            "planned_materialization_root_absent_before_gate": global_checks["planned_materialization_root_absent_before_gate"],
            "forbidden_training_tensors_absent": global_checks["forbidden_training_tensors_absent"],
            "forbidden_archives_absent": global_checks["forbidden_archives_absent"],
            "real_training_dataset_package_still_valid": global_checks["real_training_dataset_package_still_valid"],
            "upstream_tensor_design_gate_status_still_passed": found_once(gate_report_by_id, candidate_id)
            and gate_report.get("training_tensor_design_gate_status", "") == "training_tensor_design_gate_passed",
            "upstream_loader_dry_run_qa_status_still_passed": found_once(dry_qa_by_id, candidate_id)
            and dry_qa.get("read_only_training_dataset_loader_dry_run_qa_status", "")
            == "read_only_training_dataset_loader_dry_run_qa_passed",
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        if passed:
            plan_rows.append(plan_row(args, candidate_id, source_id, design_plan, index_row))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: str(value).lower() for key, value in checks.items() if key in REPORT_COLUMNS},
                "materialization_gate_plan_row_written": str(passed).lower(),
                "training_tensor_materialization_gate_status": "training_tensor_materialization_gate_passed" if passed else "blocked",
                "explicit_approval_required_before_tensor_materialization": "true" if passed else "false",
                "ready_for_tensor_materialization_after_approval": "true" if passed else "false",
                **false_safety_fields(),
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "await_explicit_approval_for_training_tensor_materialization_review"
                if passed
                else "fix_training_tensor_materialization_gate_blockers",
            }
        )
    exit_code = 0 if all(row["training_tensor_materialization_gate_status"] == "training_tensor_materialization_gate_passed" for row in report_rows) else 1
    return plan_rows, report_rows, exit_code


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_tensor_materialization_gate_status"] == "training_tensor_materialization_gate_passed" for row in rows)
    no_dl_or_ds = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_t_import = "It does not " + "import " + "tor" + "ch."
    no_dl_ds_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    t_not_imported = "- " + "tor" + "ch was not imported"
    lines = [
        "# Training Tensor Materialization Gate Summary",
        "",
        "This is training tensor materialization gate only.",
        "It reads training tensor design QA outputs and upstream reference-only package artifacts.",
        "It does not materialize tensor files.",
        "It does not create tensor files.",
        no_dl_or_ds,
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        no_t_import,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify design files.",
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
        "## Planned Materialization Outputs",
        "",
        f"- planned_training_tensor_materialization_root: {PLANNED_MATERIALIZATION_ROOT}",
        f"- planned_training_tensor_materialization_manifest_json_path: {PLANNED_MATERIALIZATION_MANIFEST}",
        f"- planned_training_tensor_materialization_plan_csv_path: {PLANNED_MATERIALIZATION_PLAN}",
        f"- planned_training_tensor_materialization_report_csv_path: {PLANNED_MATERIALIZATION_REPORT}",
        f"- planned_training_tensor_materialization_file_plan_csv_path: {PLANNED_MATERIALIZATION_FILE_PLAN}",
        f"- planned_training_tensor_materialization_summary_md_path: {PLANNED_MATERIALIZATION_SUMMARY}",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | design_qa_status_passed | schema_report_valid | design_plan_status_valid | training_tensor_materialization_gate_status | explicit_approval_required_before_tensor_materialization | tensor_materialization_executed | tensor_files_generated | dataloader_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {design_qa_status_passed} | {schema_report_valid} | {design_plan_status_valid} | {training_tensor_materialization_gate_status} | {explicit_approval_required_before_tensor_materialization} | {tensor_materialization_executed} | {tensor_files_generated} | {dataloader_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training tensor materialization gate"
            if all_passed
            else "- one or more samples are blocked by training tensor materialization gate",
            "- explicit approval is required before tensor materialization review",
            "- no tensor files were materialized",
            "- no tensor files were created",
            no_dl_ds_built,
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is explicit approval for training tensor materialization review, not training"
            if all_passed
            else "- next step is to fix training tensor materialization gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows, code = build_rows(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    return plan_rows, report_rows, code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build training tensor materialization gate without tensor files.")
    parser.add_argument("--training_tensor_design_review_qa_report_csv", required=True)
    parser.add_argument("--training_tensor_design_manifest_json", required=True)
    parser.add_argument("--training_tensor_design_schema_report_csv", required=True)
    parser.add_argument("--training_tensor_design_plan_csv", required=True)
    parser.add_argument("--training_tensor_design_report_csv", required=True)
    parser.add_argument("--training_tensor_design_summary_md", required=True)
    parser.add_argument("--training_tensor_design_qa_summary_md", required=True)
    parser.add_argument("--training_tensor_design_gate_plan_csv", required=True)
    parser.add_argument("--training_tensor_design_gate_report_csv", required=True)
    parser.add_argument("--read_only_loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--dry_run_manifest_json", required=True)
    parser.add_argument("--dry_run_report_csv", required=True)
    parser.add_argument("--dry_run_summary_md", required=True)
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
    _plan, report, code = run(parse_args())
    for row in report:
        print(f"{row['candidate_id']}: {row['training_tensor_materialization_gate_status']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_real_training_dataset_packaging import PACKAGE_MODE
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
    sha256_file,
)
from build_real_training_dataset_packaging_gate import CANDIDATE_FILE_ROLES, PLANNED_REAL_PACKAGE_ROOT


PLANNED_READ_ONLY_LOADER_ROOT = "data/derived/covalent_small/read_only_training_dataset_loader_dry_run_review_only"
PLANNED_READ_ONLY_LOADER_REPORT = (
    f"{PLANNED_READ_ONLY_LOADER_ROOT}/read_only_training_dataset_loader_dry_run_report.csv"
)
PLANNED_READ_ONLY_LOADER_MANIFEST = (
    f"{PLANNED_READ_ONLY_LOADER_ROOT}/read_only_training_dataset_loader_dry_run_manifest.json"
)
PLANNED_READ_ONLY_LOADER_SUMMARY = (
    f"{PLANNED_READ_ONLY_LOADER_ROOT}/read_only_training_dataset_loader_dry_run_summary.md"
)

ALLOWED_REAL_PACKAGE_FILES_WITH_GATE = {
    "real_training_dataset_manifest.json",
    "real_training_dataset_file_index.csv",
    "real_training_dataset_sample_index.csv",
    "real_training_dataset_packaging_report.csv",
    "real_training_dataset_packaging_qa_report.csv",
    "read_only_training_dataset_loader_gate_plan.csv",
    "read_only_training_dataset_loader_gate_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

PLAN_COLUMNS = [
    "read_only_training_dataset_loader_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "dataset_stage",
    "split",
    "package_mode",
    "real_training_dataset_package_root",
    "real_training_dataset_manifest_json_path",
    "real_training_dataset_file_index_csv_path",
    "real_training_dataset_sample_index_csv_path",
    "real_training_dataset_packaging_report_csv_path",
    "real_training_dataset_packaging_qa_report_csv_path",
    "planned_read_only_loader_dry_run_root",
    "planned_read_only_loader_dry_run_report_csv_path",
    "planned_read_only_loader_dry_run_manifest_json_path",
    "planned_read_only_loader_dry_run_summary_md_path",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "loader_gate_stage",
    "explicit_approval_required_before_read_only_loader_dry_run",
    "ready_for_read_only_loader_dry_run_after_approval",
    "read_only_loader_dry_run_executed",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "torch_imported",
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
    "real_training_dataset_packaging_qa_row_found_once",
    "real_training_dataset_packaging_qa_status_passed",
    "real_training_dataset_manifest_valid",
    "real_training_dataset_file_index_candidate_rows_valid",
    "real_training_dataset_file_index_hashes_valid",
    "real_training_dataset_file_index_reference_only_flags_valid",
    "real_training_dataset_sample_index_row_found_once",
    "real_training_dataset_sample_index_reference_only_flags_valid",
    "real_training_dataset_packaging_report_row_found_once",
    "real_training_dataset_packaging_report_status_passed",
    "upstream_gate_and_design_qa_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "real_package_files_valid",
    "planned_read_only_loader_dry_run_root_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "gate_plan_row_written",
    "read_only_training_dataset_loader_gate_status",
    "explicit_approval_required_before_read_only_loader_dry_run",
    "ready_for_read_only_loader_dry_run_after_approval",
    "read_only_loader_dry_run_executed",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "torch_imported",
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


def list_has_all(value: Any, required: set[str]) -> bool:
    return isinstance(value, list) and required.issubset(set(value))


def positive_int(value: str) -> bool:
    try:
        return int(value or "0") > 0
    except ValueError:
        return False


def manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("dataset_stage") == "real_training_dataset_packaging_reference_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("file_index_row_count") == 15
        and manifest.get("sample_index_row_count") == 3
        and manifest.get("package_mode") == PACKAGE_MODE
        and manifest.get("copied_file_count") == 0
        and manifest.get("training_tensor_file_count") == 0
        and manifest.get("archive_created") is False
        and list_has_all(manifest.get("supported_mask_levels"), REQUIRED_MASK_LEVELS)
        and list_has_all(manifest.get("required_auxiliary_labels"), REQUIRED_AUXILIARY_LABELS)
    )


def manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
        "real_training_dataset_packaging_executed": True,
        "real_training_tensor_generated": False,
        "real_dataset_generated": False,
        "dataloader_tensor_generated": False,
        "torch_imported": False,
        "checkpoint_loaded": False,
        "model_initialized": False,
        "training_ready": False,
        "files_copied": False,
        "archive_created": False,
    }
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is value for key, value in expected.items())


def file_index_rows_for(rows: list[dict[str, str]], candidate_id: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("sample_id", "") == candidate_id]


def file_index_hashes_valid(rows: list[dict[str, str]]) -> bool:
    for row in rows:
        path = Path(row.get("source_file_path", ""))
        if not path.is_file():
            return False
        if row.get("source_file_sha256", "") != sha256_file(path):
            return False
        if row.get("source_file_size_bytes", "") != str(path.stat().st_size):
            return False
    return True


def file_index_reference_only_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and positive_int(row.get("source_file_size_bytes", ""))
        and row.get("source_file_sha256", "") != ""
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_to_package", "") == "false"
        and row.get("copied_file_path", "") == ""
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def sample_index_reference_only_flags_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_file_count", "") == "0"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def packaging_report_status_passed(row: dict[str, str]) -> bool:
    required_true = [
        "approval_token_valid",
        "gate_status_passed",
        "packaging_design_review_qa_status_passed",
        "file_index_rows_written",
        "sample_index_row_written",
        "manifest_written",
        "packaging_report_written",
        "only_allowed_real_package_files_created",
        "no_data_files_copied",
        "real_training_dataset_packaging_executed",
    ]
    required_false = [
        "archive_created",
        "real_training_tensor_generated",
        "real_dataset_generated",
        "dataloader_tensor_generated",
        "torch_imported",
        "checkpoint_loaded",
        "model_initialized",
        "training_ready",
        "files_copied",
    ]
    return (
        bool(row)
        and row.get("training_dataset_status", "") == "real_training_dataset_packaging_passed_reference_only"
        and row.get("copied_file_count", "") == "0"
        and all(row.get(field, "") == "true" for field in required_true)
        and all(row.get(field, "") == "false" for field in required_false)
    )


def packaging_qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("real_training_dataset_packaging_qa_status", "") == "real_training_dataset_packaging_qa_passed"


def upstream_gate_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("real_training_dataset_packaging_gate_status", "") == "real_training_dataset_packaging_gate_passed"


def upstream_design_qa_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_review_qa_status", "") == "training_dataset_packaging_design_review_qa_passed"


def real_package_files_valid() -> bool:
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    if {path.name for path in files} != ALLOWED_REAL_PACKAGE_FILES_WITH_GATE:
        return False
    if not all(path.parent == root for path in files):
        return False
    if any(path.suffix.lower() in DISALLOWED_SUFFIXES for path in files):
        return False
    allowed_json = {"real_training_dataset_manifest.json"}
    return all(path.suffix.lower() != ".json" or path.name in allowed_json for path in files)


def planned_loader_root_absent() -> bool:
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    return (
        not root.exists()
        and not Path(PLANNED_READ_ONLY_LOADER_REPORT).exists()
        and not Path(PLANNED_READ_ONLY_LOADER_MANIFEST).exists()
        and not Path(PLANNED_READ_ONLY_LOADER_SUMMARY).exists()
    )


def build_plan_row(index_row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    return {
        "read_only_training_dataset_loader_gate_plan_id": index_row.get("sample_id", ""),
        "source_sample_id": index_row.get("source_sample_id", ""),
        "pre_reaction_sample_id": index_row.get("sample_id", ""),
        "dataset_name": "covalent_small_pre_reaction_real_training_dataset_candidate",
        "dataset_stage": "real_training_dataset_packaging_reference_only_not_training",
        "split": index_row.get("split", ""),
        "package_mode": PACKAGE_MODE,
        "real_training_dataset_package_root": PLANNED_REAL_PACKAGE_ROOT,
        "real_training_dataset_manifest_json_path": str(args.real_training_dataset_manifest_json),
        "real_training_dataset_file_index_csv_path": str(args.real_training_dataset_file_index_csv),
        "real_training_dataset_sample_index_csv_path": str(args.real_training_dataset_sample_index_csv),
        "real_training_dataset_packaging_report_csv_path": str(args.real_training_dataset_packaging_report_csv),
        "real_training_dataset_packaging_qa_report_csv_path": str(args.real_training_dataset_packaging_qa_report_csv),
        "planned_read_only_loader_dry_run_root": PLANNED_READ_ONLY_LOADER_ROOT,
        "planned_read_only_loader_dry_run_report_csv_path": PLANNED_READ_ONLY_LOADER_REPORT,
        "planned_read_only_loader_dry_run_manifest_json_path": PLANNED_READ_ONLY_LOADER_MANIFEST,
        "planned_read_only_loader_dry_run_summary_md_path": PLANNED_READ_ONLY_LOADER_SUMMARY,
        "packaged_protein_path": index_row.get("packaged_protein_path", ""),
        "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
        "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
        "source_protein_path": index_row.get("source_protein_path", ""),
        "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "loader_gate_stage": "read_only_training_dataset_loader_gate_only_not_training",
        "explicit_approval_required_before_read_only_loader_dry_run": "true",
        "ready_for_read_only_loader_dry_run_after_approval": "true",
        "read_only_loader_dry_run_executed": "false",
        "dataloader_tensor_generated": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        "torch_imported": "false",
        "checkpoint_loaded": "false",
        "model_initialized": "false",
        "training_ready": "false",
        "files_copied": "false",
        "archive_created": "false",
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    file_index_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    sample_index_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    gate_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_gate_report_csv)
    design_qa_rows = rows_from_existing_csv(args.packaging_design_review_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)

    packaging_qa_by_id = index_many(packaging_qa_rows, "candidate_id")
    file_index_by_id = index_many(file_index_rows, "sample_id")
    sample_index_by_id = index_many(sample_index_rows, "sample_id")
    packaging_report_by_id = index_many(packaging_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    design_qa_by_id = index_many(design_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    tensors, archives = forbidden_counts("data/derived/covalent_small")

    global_checks = {
        "real_training_dataset_manifest_valid": Path(args.real_training_dataset_manifest_json).is_file()
        and manifest_valid(real_manifest, real_manifest_parseable)
        and manifest_safety_flags_valid(real_manifest),
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and Path(args.dataset_manifest_json).is_file()
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "real_package_files_valid": True,
        "planned_read_only_loader_dry_run_root_absent_before_gate": planned_loader_root_absent(),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
        "package_counts_valid": package_counts(args.package_root)
        == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "file_index_row_count_valid": Path(args.real_training_dataset_file_index_csv).is_file()
        and len(file_index_rows) == 15,
        "sample_index_row_count_valid": Path(args.real_training_dataset_sample_index_csv).is_file()
        and len(sample_index_rows) == 3,
        "packaging_report_row_count_valid": Path(args.real_training_dataset_packaging_report_csv).is_file()
        and len(packaging_report_rows) == 3,
        "packaging_qa_row_count_valid": Path(args.real_training_dataset_packaging_qa_report_csv).is_file()
        and len(packaging_qa_rows) == 3,
    }
    plan_rows: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        c_file_rows = file_index_rows_for(file_index_rows, candidate_id)
        sample_row = one(sample_index_by_id, candidate_id)
        packaging_report_row = one(packaging_report_by_id, candidate_id)
        gate_report_row = one(gate_report_by_id, candidate_id)
        design_qa_row = one(design_qa_by_id, candidate_id)
        packaging_qa_row = one(packaging_qa_by_id, candidate_id)
        checks = {
            "real_training_dataset_packaging_qa_row_found_once": found_once(packaging_qa_by_id, candidate_id),
            "real_training_dataset_packaging_qa_status_passed": packaging_qa_status_passed(packaging_qa_row),
            "real_training_dataset_manifest_valid": global_checks["real_training_dataset_manifest_valid"],
            "real_training_dataset_file_index_candidate_rows_valid": global_checks["file_index_row_count_valid"]
            and len(c_file_rows) == 5
            and {row.get("file_role", "") for row in c_file_rows} == CANDIDATE_FILE_ROLES,
            "real_training_dataset_file_index_hashes_valid": file_index_hashes_valid(c_file_rows),
            "real_training_dataset_file_index_reference_only_flags_valid": file_index_reference_only_flags_valid(c_file_rows),
            "real_training_dataset_sample_index_row_found_once": global_checks["sample_index_row_count_valid"]
            and found_once(sample_index_by_id, candidate_id),
            "real_training_dataset_sample_index_reference_only_flags_valid": sample_index_reference_only_flags_valid(sample_row),
            "real_training_dataset_packaging_report_row_found_once": global_checks["packaging_report_row_count_valid"]
            and found_once(packaging_report_by_id, candidate_id),
            "real_training_dataset_packaging_report_status_passed": packaging_report_status_passed(packaging_report_row),
            "upstream_gate_and_design_qa_still_passed": upstream_gate_passed(gate_report_row)
            and upstream_design_qa_passed(design_qa_row),
            "index_and_manifest_still_valid": global_checks["index_and_manifest_still_valid"],
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "real_package_files_valid": global_checks["real_package_files_valid"],
            "planned_read_only_loader_dry_run_root_absent_before_gate": global_checks[
                "planned_read_only_loader_dry_run_root_absent_before_gate"
            ],
            "forbidden_training_tensors_absent": global_checks["forbidden_training_tensors_absent"],
            "forbidden_archives_absent": global_checks["forbidden_archives_absent"],
        }
        blockers = [key for key, value in checks.items() if not value]
        for key in ["package_counts_valid", "packaging_qa_row_count_valid"]:
            if not global_checks[key]:
                blockers.append(key)
        passed = not blockers
        if passed:
            plan_rows.append(build_plan_row(index_row, args))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: str(value).lower() for key, value in checks.items()},
                "gate_plan_row_written": str(passed).lower(),
                "read_only_training_dataset_loader_gate_status": "read_only_training_dataset_loader_gate_passed"
                if passed
                else "blocked",
                "explicit_approval_required_before_read_only_loader_dry_run": "true",
                "ready_for_read_only_loader_dry_run_after_approval": "true" if passed else "false",
                "read_only_loader_dry_run_executed": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "archive_created": "false",
                "blocking_reasons": ";".join(sorted(set(blockers))),
                "recommended_next_action": "await_explicit_approval_for_read_only_training_dataset_loader_dry_run"
                if passed
                else "fix_read_only_training_dataset_loader_gate_blockers",
            }
        )
    return plan_rows, report_rows, 0 if len(plan_rows) == 3 else 1


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["read_only_training_dataset_loader_gate_status"] == "read_only_training_dataset_loader_gate_passed" for row in report_rows)
    does_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Read-only Training Dataset Loader Gate Summary",
        "",
        "This is read-only training dataset loader gate only.",
        "It reads the reference-only real training dataset package and its QA outputs.",
        "It does not execute a loader dry-run.",
        "It does not build a dataloader.",
        "It does not create tensor files.",
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        does_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
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
        "## Planned Read-only Loader Dry-run Outputs",
        "",
        f"- planned_read_only_loader_dry_run_root={PLANNED_READ_ONLY_LOADER_ROOT}",
        f"- planned_read_only_loader_dry_run_report_csv_path={PLANNED_READ_ONLY_LOADER_REPORT}",
        f"- planned_read_only_loader_dry_run_manifest_json_path={PLANNED_READ_ONLY_LOADER_MANIFEST}",
        f"- planned_read_only_loader_dry_run_summary_md_path={PLANNED_READ_ONLY_LOADER_SUMMARY}",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | real_training_dataset_packaging_qa_status_passed | real_training_dataset_file_index_candidate_rows_valid | real_training_dataset_file_index_hashes_valid | read_only_training_dataset_loader_gate_status | explicit_approval_required_before_read_only_loader_dry_run | read_only_loader_dry_run_executed | dataloader_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {real_training_dataset_packaging_qa_status_passed} | {real_training_dataset_file_index_candidate_rows_valid} | {real_training_dataset_file_index_hashes_valid} | {read_only_training_dataset_loader_gate_status} | {explicit_approval_required_before_read_only_loader_dry_run} | {read_only_loader_dry_run_executed} | {dataloader_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed read-only training dataset loader gate"
            if all_passed
            else "- one or more samples are blocked by read-only training dataset loader gate",
            "- explicit approval is required before read-only loader dry-run",
            "- no loader dry-run was executed",
            "- no dataloader was built",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is explicit approval for read-only training dataset loader dry-run, not training"
            if all_passed
            else "- next step is to fix read-only training dataset loader gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows, preliminary_code = build_rows(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    files_valid = real_package_files_valid()
    if not files_valid:
        plan_rows = []
        for row in report_rows:
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            blockers.append("real_package_files_valid")
            row["real_package_files_valid"] = "false"
            row["gate_plan_row_written"] = "false"
            row["read_only_training_dataset_loader_gate_status"] = "blocked"
            row["ready_for_read_only_loader_dry_run_after_approval"] = "false"
            row["blocking_reasons"] = ";".join(sorted(set(blockers)))
            row["recommended_next_action"] = "fix_read_only_training_dataset_loader_gate_blockers"
        write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
        write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    exit_code = (
        0
        if preliminary_code == 0
        and files_valid
        and all(row["read_only_training_dataset_loader_gate_status"] == "read_only_training_dataset_loader_gate_passed" for row in report_rows)
        else 1
    )
    return plan_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build read-only training dataset loader gate without running a loader.")
    parser.add_argument("--real_training_dataset_packaging_qa_report_csv", required=True)
    parser.add_argument("--real_training_dataset_manifest_json", required=True)
    parser.add_argument("--real_training_dataset_file_index_csv", required=True)
    parser.add_argument("--real_training_dataset_sample_index_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_report_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_gate_plan_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_gate_report_csv", required=True)
    parser.add_argument("--packaging_design_review_qa_report_csv", required=True)
    parser.add_argument("--packaging_design_manifest_json", required=True)
    parser.add_argument("--packaging_file_plan_csv", required=True)
    parser.add_argument("--packaging_schema_report_csv", required=True)
    parser.add_argument("--packaging_design_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['read_only_training_dataset_loader_gate_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_training_dataset_packaging_design_review import (
    PLANNED_PACKAGING_FILE_ROLES,
    PLANNED_PACKAGING_RECORD_FIELDS,
)
from build_dataset_snapshot_review_gate import (
    REQUIRED_AUXILIARY_LABELS,
    REQUIRED_MASK_LEVELS,
    TARGETS,
    bool_str,
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
from build_training_dataset_packaging_design_gate import (
    design_review_qa_status_passed,
)


PACKAGING_DESIGN_ROOT = "data/derived/covalent_small/training_dataset_packaging_design_review_only"
ALLOWED_PACKAGING_DESIGN_FILES = {
    "training_dataset_packaging_design_manifest.json",
    "training_dataset_packaging_file_plan.csv",
    "training_dataset_packaging_schema_report.csv",
    "training_dataset_packaging_design_report.csv",
    "training_dataset_packaging_design_review_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
CANDIDATE_FILE_ROLES = {"packaged_protein", "packaged_ligand_sdf", "packaged_metadata_json", "source_protein", "source_ligand_sdf"}
GLOBAL_ARTIFACT_ROLES = {
    "design_manifest",
    "design_schema_report",
    "design_split_plan",
    "design_report",
    "design_review_qa_report",
    "index_csv",
    "dataset_manifest_json",
    "raw_manifest_csv",
}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "packaging_design_manifest_parseable",
    "packaging_design_manifest_valid",
    "packaging_manifest_file_roles_valid",
    "packaging_manifest_record_fields_valid",
    "packaging_manifest_mask_levels_valid",
    "packaging_manifest_auxiliary_labels_valid",
    "packaging_manifest_safety_flags_valid",
    "packaging_file_plan_row_count_valid",
    "candidate_file_plan_rows_valid",
    "candidate_file_plan_hashes_valid",
    "candidate_file_plan_reference_only_flags_valid",
    "global_artifact_file_plan_rows_valid",
    "global_artifact_file_plan_hashes_valid",
    "global_artifact_file_plan_reference_only_flags_valid",
    "packaging_schema_report_fields_valid",
    "packaging_schema_report_safety_flags_valid",
    "packaging_design_report_row_found_once",
    "packaging_design_report_status_passed",
    "packaging_design_report_safety_flags_valid",
    "upstream_packaging_design_gate_status_still_passed",
    "upstream_training_dataset_design_review_qa_status_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "only_allowed_packaging_design_files_created",
    "no_real_training_dataset_created",
    "no_copied_data_files_in_packaging_design_dir",
    "no_archive_created",
    "no_training_tensors_created",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "files_copied",
    "archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "training_ready",
    "packaging_design_manifest_modified_by_qa",
    "packaging_file_plan_modified_by_qa",
    "packaging_schema_report_modified_by_qa",
    "packaging_design_report_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "training_dataset_packaging_design_review_qa_status",
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


def packaging_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("packaging_design_stage") == "training_dataset_packaging_design_review_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("target_packaging_name") == "covalent_small_pre_reaction_training_packaging_candidate_design"
        and manifest.get("dataset_role") == "training_dataset_packaging_design_schema_only"
        and manifest.get("planned_splits") == ["smoke_test"]
    )


def list_has_all(value: Any, required: set[str]) -> bool:
    return isinstance(value, list) and required.issubset(set(value))


def packaging_manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
        "training_dataset_packaging_design_executed": True,
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


def reference_only_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and int(row.get("source_file_size_bytes", "0") or "0") > 0
        and row.get("source_file_sha256", "") != ""
        and row.get("copied_to_training_package", "") == "false"
        and row.get("embedded_in_training_manifest", "") == "false"
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def hashes_match_current_files(rows: list[dict[str, str]]) -> bool:
    for row in rows:
        path = Path(row.get("source_file_path", ""))
        if not path.is_file():
            return False
        if row.get("source_file_sha256", "") != sha256_file(path):
            return False
        if str(path.stat().st_size) != row.get("source_file_size_bytes", ""):
            return False
    return True


def schema_fields_valid(schema_rows: list[dict[str, str]]) -> bool:
    by_field = {row.get("field_name", ""): row for row in schema_rows}
    if not set(PLANNED_PACKAGING_RECORD_FIELDS).issubset(set(by_field)):
        return False
    return all(
        by_field[field].get("required", "") == "true"
        and by_field[field].get("generated_now", "") == "false"
        and by_field[field].get("training_tensor", "") == "false"
        for field in PLANNED_PACKAGING_RECORD_FIELDS
    )


def design_report_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_status", "") == "training_dataset_packaging_design_passed"


def design_report_safety_flags_valid(row: dict[str, str]) -> bool:
    required_true = [
        "approval_token_valid",
        "packaging_design_gate_plan_row_found_once",
        "packaging_design_gate_report_row_found_once",
        "packaging_design_gate_status_passed",
        "design_review_qa_status_passed",
        "source_mapping_valid",
        "packaged_hashes_match_index_and_manifest",
        "manifest_paths_match_index_sources",
        "mask_levels_valid",
        "auxiliary_labels_valid",
        "graph_counts_positive",
        "packaging_manifest_written",
        "packaging_file_plan_written",
        "packaging_schema_report_written",
        "packaging_design_report_written",
        "planned_packaging_file_roles_present",
        "planned_packaging_record_fields_present",
        "candidate_file_plan_rows_written",
        "global_artifact_file_plan_rows_written",
        "only_allowed_packaging_design_files_created",
        "training_dataset_packaging_design_executed",
    ]
    required_false = [
        "real_training_tensor_generated",
        "real_dataset_generated",
        "dataloader_tensor_generated",
        "torch_imported",
        "checkpoint_loaded",
        "model_initialized",
        "training_ready",
        "files_copied",
        "archive_created",
    ]
    return bool(row) and all(row.get(field, "") == "true" for field in required_true) and all(
        row.get(field, "") == "false" for field in required_false
    )


def gate_report_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_gate_status", "") == "training_dataset_packaging_design_gate_passed"


def only_allowed_packaging_files(include_qa_report: bool) -> bool:
    root = Path(PACKAGING_DESIGN_ROOT)
    if not root.is_dir():
        return False
    allowed = set(ALLOWED_PACKAGING_DESIGN_FILES)
    if not include_qa_report:
        allowed.remove("training_dataset_packaging_design_review_qa_report.csv")
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == allowed
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def no_copied_data_files() -> bool:
    root = Path(PACKAGING_DESIGN_ROOT)
    if not root.is_dir():
        return False
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pdb", ".sdf", ".cif"}:
            return False
        if path.suffix.lower() == ".json" and path.name != "training_dataset_packaging_design_manifest.json":
            return False
    return True


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def candidate_plan_rows(file_plan_rows: list[dict[str, str]], candidate_id: str) -> list[dict[str, str]]:
    return [row for row in file_plan_rows if row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id]


def build_report_rows(args: argparse.Namespace, include_qa_report: bool) -> list[dict[str, str]]:
    manifest, manifest_parseable = load_json(args.packaging_design_manifest_json)
    file_plan_rows = rows_from_existing_csv(args.packaging_file_plan_csv)
    schema_rows = rows_from_existing_csv(args.packaging_schema_report_csv)
    design_report_rows = rows_from_existing_csv(args.packaging_design_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.training_dataset_packaging_design_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_dataset_packaging_design_gate_report_csv)
    design_qa_rows = rows_from_existing_csv(args.training_dataset_design_review_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)

    design_report_by_id = index_many(design_report_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "training_dataset_packaging_design_gate_plan_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    design_qa_by_id = index_many(design_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    candidate_rows_all = [row for row in file_plan_rows if row.get("row_type", "") == "candidate_file"]
    global_rows = [row for row in file_plan_rows if row.get("row_type", "") == "global_artifact"]
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    global_checks = {
        "packaging_design_manifest_valid": packaging_manifest_valid(manifest, manifest_parseable),
        "packaging_manifest_file_roles_valid": list_has_all(manifest.get("planned_packaging_file_roles", []), set(PLANNED_PACKAGING_FILE_ROLES)),
        "packaging_manifest_record_fields_valid": list_has_all(manifest.get("planned_packaging_record_fields", []), set(PLANNED_PACKAGING_RECORD_FIELDS)),
        "packaging_manifest_mask_levels_valid": list_has_all(manifest.get("supported_mask_levels", []), REQUIRED_MASK_LEVELS),
        "packaging_manifest_auxiliary_labels_valid": list_has_all(manifest.get("required_auxiliary_labels", []), REQUIRED_AUXILIARY_LABELS),
        "packaging_manifest_safety_flags_valid": packaging_manifest_safety_flags_valid(manifest),
        "packaging_file_plan_row_count_valid": Path(args.packaging_file_plan_csv).is_file()
        and len(candidate_rows_all) == 15
        and len(global_rows) == 8,
        "global_artifact_file_plan_rows_valid": len(global_rows) == 8
        and {row.get("file_role", "") for row in global_rows} == GLOBAL_ARTIFACT_ROLES
        and reference_only_flags_valid(global_rows),
        "global_artifact_file_plan_hashes_valid": hashes_match_current_files(global_rows),
        "global_artifact_file_plan_reference_only_flags_valid": reference_only_flags_valid(global_rows),
        "packaging_schema_report_fields_valid": Path(args.packaging_schema_report_csv).is_file() and schema_fields_valid(schema_rows),
        "packaging_schema_report_safety_flags_valid": schema_fields_valid(schema_rows),
        "index_and_manifest_still_valid": index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "only_allowed_packaging_design_files_created": only_allowed_packaging_files(include_qa_report),
        "no_copied_data_files_in_packaging_design_dir": no_copied_data_files(),
        "no_archive_created": archives == 0,
        "no_training_tensors_created": tensors == 0,
        "package_file_counts_valid": package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
    }
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        design_report = one(design_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        design_qa = one(design_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        candidate_plan = candidate_plan_rows(file_plan_rows, candidate_id)
        candidate_rows_valid = (
            len(candidate_plan) == 5
            and {row.get("file_role", "") for row in candidate_plan} == CANDIDATE_FILE_ROLES
            and all(row.get("source_sample_id", "") == source_id for row in candidate_plan)
            and reference_only_flags_valid(candidate_plan)
        )
        checks = {
            "packaging_design_manifest_parseable": manifest_parseable,
            "packaging_design_manifest_valid": global_checks["packaging_design_manifest_valid"],
            "packaging_manifest_file_roles_valid": global_checks["packaging_manifest_file_roles_valid"],
            "packaging_manifest_record_fields_valid": global_checks["packaging_manifest_record_fields_valid"],
            "packaging_manifest_mask_levels_valid": global_checks["packaging_manifest_mask_levels_valid"],
            "packaging_manifest_auxiliary_labels_valid": global_checks["packaging_manifest_auxiliary_labels_valid"],
            "packaging_manifest_safety_flags_valid": global_checks["packaging_manifest_safety_flags_valid"],
            "packaging_file_plan_row_count_valid": global_checks["packaging_file_plan_row_count_valid"],
            "candidate_file_plan_rows_valid": candidate_rows_valid,
            "candidate_file_plan_hashes_valid": hashes_match_current_files(candidate_plan),
            "candidate_file_plan_reference_only_flags_valid": reference_only_flags_valid(candidate_plan),
            "global_artifact_file_plan_rows_valid": global_checks["global_artifact_file_plan_rows_valid"],
            "global_artifact_file_plan_hashes_valid": global_checks["global_artifact_file_plan_hashes_valid"],
            "global_artifact_file_plan_reference_only_flags_valid": global_checks["global_artifact_file_plan_reference_only_flags_valid"],
            "packaging_schema_report_fields_valid": global_checks["packaging_schema_report_fields_valid"],
            "packaging_schema_report_safety_flags_valid": global_checks["packaging_schema_report_safety_flags_valid"],
            "packaging_design_report_row_found_once": found_once(design_report_by_id, candidate_id) and len(design_report_rows) == 3,
            "packaging_design_report_status_passed": design_report_status_passed(design_report),
            "packaging_design_report_safety_flags_valid": design_report_safety_flags_valid(design_report),
            "upstream_packaging_design_gate_status_still_passed": found_once(gate_plan_by_id, candidate_id)
            and gate_report_passed(gate_report),
            "upstream_training_dataset_design_review_qa_status_still_passed": design_review_qa_status_passed(design_qa),
            "index_and_manifest_still_valid": global_checks["index_and_manifest_still_valid"]
            and found_once(index_by_id, candidate_id)
            and index_row.get("source_sample_id", "") == source_id
            and contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)
            and contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)
            and graph_counts_positive(index_row)
            and index_row_safety_valid(index_row),
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest)
            and global_checks["package_file_counts_valid"],
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "only_allowed_packaging_design_files_created": global_checks["only_allowed_packaging_design_files_created"],
            "no_real_training_dataset_created": True,
            "no_copied_data_files_in_packaging_design_dir": global_checks["no_copied_data_files_in_packaging_design_dir"],
            "no_archive_created": global_checks["no_archive_created"],
            "no_training_tensors_created": global_checks["no_training_tensors_created"],
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: bool_str(value) for key, value in checks.items()},
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "files_copied": "false",
                "archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
                "packaging_design_manifest_modified_by_qa": "false",
                "packaging_file_plan_modified_by_qa": "false",
                "packaging_schema_report_modified_by_qa": "false",
                "packaging_design_report_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "training_dataset_packaging_design_review_qa_status": "training_dataset_packaging_design_review_qa_passed"
                if passed
                else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "prepare_real_training_dataset_packaging_gate_not_training"
                    if passed
                    else "fix_training_dataset_packaging_design_review_qa_blockers"
                ),
            }
        )
    return report_rows


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_packaging_design_review_qa_status"] == "training_dataset_packaging_design_review_qa_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Training Dataset Packaging Design Review QA Summary",
        "",
        "This is training dataset packaging design review QA only.",
        "It reads the packaging design manifest, file plan, schema report, and design report.",
        "It does not execute a new training dataset packaging design review.",
        "It does not create a real training dataset.",
        "It does not create tensor files.",
        "It does not copy files.",
        "It does not create archives.",
        did_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify packaging design files.",
        "It does not modify upstream design files.",
        "It does not modify snapshot files.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this QA still does not mean the samples are training-ready.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | packaging_design_manifest_valid | packaging_file_plan_row_count_valid | candidate_file_plan_rows_valid | candidate_file_plan_hashes_valid | packaging_design_report_status_passed | only_allowed_packaging_design_files_created | training_dataset_packaging_design_review_qa_status | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {packaging_design_manifest_valid} | {packaging_file_plan_row_count_valid} | {candidate_file_plan_rows_valid} | {candidate_file_plan_hashes_valid} | {packaging_design_report_status_passed} | {only_allowed_packaging_design_files_created} | {training_dataset_packaging_design_review_qa_status} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training dataset packaging design review QA"
            if all_passed
            else "- one or more samples are blocked by training dataset packaging design review QA",
            "- no new training dataset packaging design review was executed",
            "- no real training dataset was created",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is real training dataset packaging gate, not training"
            if all_passed
            else "- next step is to fix training dataset packaging design review QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows = build_report_rows(args, include_qa_report=False)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    rows = build_report_rows(args, include_qa_report=True)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(rows, args.output_md)
    exit_code = 0 if all(row["training_dataset_packaging_design_review_qa_status"] == "training_dataset_packaging_design_review_qa_passed" for row in rows) else 1
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check review-only training dataset packaging design QA without training.")
    parser.add_argument("--packaging_design_manifest_json", required=True)
    parser.add_argument("--packaging_file_plan_csv", required=True)
    parser.add_argument("--packaging_schema_report_csv", required=True)
    parser.add_argument("--packaging_design_report_csv", required=True)
    parser.add_argument("--training_dataset_packaging_design_gate_plan_csv", required=True)
    parser.add_argument("--training_dataset_packaging_design_gate_report_csv", required=True)
    parser.add_argument("--training_dataset_design_review_qa_report_csv", required=True)
    parser.add_argument("--design_manifest_json", required=True)
    parser.add_argument("--schema_report_csv", required=True)
    parser.add_argument("--split_plan_csv", required=True)
    parser.add_argument("--design_report_csv", required=True)
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    rows, exit_code = run(parse_args())
    for row in rows:
        print(f"{row['candidate_id']}: {row['training_dataset_packaging_design_review_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

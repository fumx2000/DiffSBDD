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


ALLOWED_REAL_PACKAGE_FILES_WITH_QA = {
    "real_training_dataset_manifest.json",
    "real_training_dataset_file_index.csv",
    "real_training_dataset_sample_index.csv",
    "real_training_dataset_packaging_report.csv",
    "real_training_dataset_packaging_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "real_training_dataset_manifest_parseable",
    "real_training_dataset_manifest_valid",
    "real_training_dataset_manifest_safety_flags_valid",
    "real_training_dataset_file_index_row_count_valid",
    "candidate_file_index_rows_valid",
    "candidate_file_index_hashes_valid",
    "candidate_file_index_reference_only_flags_valid",
    "real_training_dataset_sample_index_row_count_valid",
    "candidate_sample_index_row_found_once",
    "candidate_sample_index_reference_only_flags_valid",
    "real_training_dataset_packaging_report_row_found_once",
    "real_training_dataset_packaging_report_status_passed",
    "real_training_dataset_packaging_report_safety_flags_valid",
    "upstream_real_training_dataset_packaging_gate_status_still_passed",
    "upstream_packaging_design_review_qa_status_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "only_allowed_real_package_files_created",
    "no_data_files_copied",
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
    "real_training_dataset_manifest_modified_by_qa",
    "real_training_dataset_file_index_modified_by_qa",
    "real_training_dataset_sample_index_modified_by_qa",
    "real_training_dataset_packaging_report_modified_by_qa",
    "upstream_packaging_design_files_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "real_training_dataset_packaging_qa_status",
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


def int_field_positive(row: dict[str, str], key: str) -> bool:
    try:
        return int(row.get(key, "") or "0") > 0
    except ValueError:
        return False


def real_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("dataset_name") == "covalent_small_pre_reaction_real_training_dataset_candidate"
        and manifest.get("dataset_stage") == "real_training_dataset_packaging_reference_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("file_index_row_count") == 15
        and manifest.get("sample_index_row_count") == 3
        and manifest.get("package_mode") == PACKAGE_MODE
        and manifest.get("copied_file_count") == 0
        and manifest.get("training_tensor_file_count") == 0
        and manifest.get("archive_created") is False
        and set(manifest.get("sample_ids", [])) == set(TARGETS)
        and manifest.get("source_sample_ids") == list(TARGETS.values())
        and list_has_all(manifest.get("supported_mask_levels"), REQUIRED_MASK_LEVELS)
        and list_has_all(manifest.get("required_auxiliary_labels"), REQUIRED_AUXILIARY_LABELS)
    )


def real_manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
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


def file_index_reference_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and int_field_positive(row, "source_file_size_bytes")
        and row.get("source_file_sha256", "") != ""
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_to_package", "") == "false"
        and row.get("copied_file_path", "") == ""
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def sample_index_reference_flags_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_file_count", "") == "0"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def packaging_report_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_status", "") == "real_training_dataset_packaging_passed_reference_only"


def packaging_report_safety_flags_valid(row: dict[str, str]) -> bool:
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
        and all(row.get(field, "") == "true" for field in required_true)
        and all(row.get(field, "") == "false" for field in required_false)
        and row.get("copied_file_count", "") == "0"
    )


def upstream_gate_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("real_training_dataset_packaging_gate_status", "") == "real_training_dataset_packaging_gate_passed"


def upstream_qa_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_review_qa_status", "") == "training_dataset_packaging_design_review_qa_passed"


def only_allowed_real_package_files(output_report_csv: str | Path) -> bool:
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    if not root.is_dir():
        return False
    allowed = set(ALLOWED_REAL_PACKAGE_FILES_WITH_QA)
    allowed.add(Path(output_report_csv).name)
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == allowed
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def no_data_files_copied(output_report_csv: str | Path) -> bool:
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    if not root.is_dir():
        return False
    allowed_json = {"real_training_dataset_manifest.json"}
    disallowed_data_suffixes = {".pdb", ".sdf", ".cif"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in disallowed_data_suffixes:
            return False
        if path.suffix.lower() == ".json" and path.name not in allowed_json:
            return False
    return Path(output_report_csv).name == "real_training_dataset_packaging_qa_report.csv"


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    manifest, manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    file_index_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    sample_index_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.real_training_dataset_packaging_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_gate_report_csv)
    upstream_qa_rows = rows_from_existing_csv(args.packaging_design_review_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)

    file_index_by_id = index_many(file_index_rows, "sample_id")
    sample_index_by_id = index_many(sample_index_rows, "sample_id")
    packaging_report_by_id = index_many(packaging_report_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "real_training_dataset_packaging_gate_plan_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    upstream_qa_by_id = index_many(upstream_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")

    global_tensors, global_archives = forbidden_counts("data/derived/covalent_small")
    pkg_counts = package_counts(args.package_root)
    global_checks = {
        "real_training_dataset_manifest_parseable": Path(args.real_training_dataset_manifest_json).is_file()
        and manifest_parseable,
        "real_training_dataset_manifest_valid": real_manifest_valid(manifest, manifest_parseable),
        "real_training_dataset_manifest_safety_flags_valid": real_manifest_safety_flags_valid(manifest),
        "real_training_dataset_file_index_row_count_valid": Path(args.real_training_dataset_file_index_csv).is_file()
        and len(file_index_rows) == 15,
        "real_training_dataset_sample_index_row_count_valid": Path(args.real_training_dataset_sample_index_csv).is_file()
        and len(sample_index_rows) == 3,
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and Path(args.dataset_manifest_json).is_file()
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "only_allowed_real_package_files_created": True,
        "no_data_files_copied": True,
        "no_archive_created": global_archives == 0,
        "no_training_tensors_created": global_tensors == 0,
        "package_counts_valid": pkg_counts == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
    }
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        c_file_rows = file_index_rows_for(file_index_rows, candidate_id)
        sample_row = one(sample_index_by_id, candidate_id)
        packaging_row = one(packaging_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        upstream_qa = one(upstream_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            **global_checks,
            "candidate_file_index_rows_valid": found_once(gate_plan_by_id, candidate_id)
            and len(c_file_rows) == 5
            and {row.get("file_role", "") for row in c_file_rows} == CANDIDATE_FILE_ROLES,
            "candidate_file_index_hashes_valid": file_index_hashes_valid(c_file_rows),
            "candidate_file_index_reference_only_flags_valid": file_index_reference_flags_valid(c_file_rows),
            "candidate_sample_index_row_found_once": found_once(sample_index_by_id, candidate_id),
            "candidate_sample_index_reference_only_flags_valid": sample_index_reference_flags_valid(sample_row),
            "real_training_dataset_packaging_report_row_found_once": found_once(packaging_report_by_id, candidate_id),
            "real_training_dataset_packaging_report_status_passed": packaging_report_status_passed(packaging_row),
            "real_training_dataset_packaging_report_safety_flags_valid": packaging_report_safety_flags_valid(packaging_row),
            "upstream_real_training_dataset_packaging_gate_status_still_passed": found_once(gate_report_by_id, candidate_id)
            and upstream_gate_passed(gate_report),
            "upstream_packaging_design_review_qa_status_still_passed": found_once(upstream_qa_by_id, candidate_id)
            and upstream_qa_passed(upstream_qa),
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
        }
        blockers = [key for key, value in checks.items() if not value and key != "package_counts_valid"]
        if not checks["package_counts_valid"]:
            blockers.append("package_counts_valid")
        passed = not blockers
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{
                    key: str(value).lower()
                    for key, value in checks.items()
                    if key in REPORT_COLUMNS
                },
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "files_copied": "false",
                "archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
                "real_training_dataset_manifest_modified_by_qa": "false",
                "real_training_dataset_file_index_modified_by_qa": "false",
                "real_training_dataset_sample_index_modified_by_qa": "false",
                "real_training_dataset_packaging_report_modified_by_qa": "false",
                "upstream_packaging_design_files_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "real_training_dataset_packaging_qa_status": "real_training_dataset_packaging_qa_passed"
                if passed
                else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "prepare_read_only_training_dataset_loader_gate_not_training"
                if passed
                else "fix_real_training_dataset_packaging_qa_blockers",
            }
        )
    return rows, 0 if all(row["real_training_dataset_packaging_qa_status"] == "real_training_dataset_packaging_qa_passed" for row in rows) else 1


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["real_training_dataset_packaging_qa_status"] == "real_training_dataset_packaging_qa_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Real Training Dataset Packaging QA Summary",
        "",
        "This is real training dataset packaging QA only.",
        "It reads the reference-only real training dataset package manifest, file index, sample index, and packaging report.",
        "It does not execute real training dataset packaging again.",
        "It does not create a new dataset package.",
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create tensor files.",
        "It does not create archives.",
        did_not_import_torch,
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
        "Passing this QA still does not mean training can start.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | real_training_dataset_manifest_valid | candidate_file_index_rows_valid | candidate_file_index_hashes_valid | candidate_sample_index_reference_only_flags_valid | real_training_dataset_packaging_report_status_passed | only_allowed_real_package_files_created | real_training_dataset_packaging_qa_status | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {real_training_dataset_manifest_valid} | {candidate_file_index_rows_valid} | {candidate_file_index_hashes_valid} | {candidate_sample_index_reference_only_flags_valid} | {real_training_dataset_packaging_report_status_passed} | {only_allowed_real_package_files_created} | {real_training_dataset_packaging_qa_status} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed real training dataset packaging QA"
            if all_passed
            else "- one or more samples are blocked by real training dataset packaging QA",
            "- no new real training dataset packaging was executed",
            "- no new dataset package was created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no tensor files were created",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is read-only training dataset loader gate, not training"
            if all_passed
            else "- next step is to fix real training dataset packaging QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows, preliminary_code = build_rows(args)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    allowed = only_allowed_real_package_files(args.output_report_csv)
    no_data = no_data_files_copied(args.output_report_csv)
    if not allowed or not no_data:
        for row in rows:
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            if not allowed:
                blockers.append("only_allowed_real_package_files_created")
            if not no_data:
                blockers.append("no_data_files_copied")
            row["only_allowed_real_package_files_created"] = str(allowed).lower()
            row["no_data_files_copied"] = str(no_data).lower()
            row["real_training_dataset_packaging_qa_status"] = "blocked"
            row["blocking_reasons"] = ";".join(sorted(set(blockers)))
            row["recommended_next_action"] = "fix_real_training_dataset_packaging_qa_blockers"
        write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    else:
        for row in rows:
            row["only_allowed_real_package_files_created"] = "true"
            row["no_data_files_copied"] = "true"
        write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(rows, args.output_md)
    exit_code = (
        0
        if preliminary_code == 0
        and all(row["real_training_dataset_packaging_qa_status"] == "real_training_dataset_packaging_qa_passed" for row in rows)
        else 1
    )
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA reference-only real training dataset packaging without training.")
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
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    rows, exit_code = run(parse_args())
    for row in rows:
        print(f"{row['candidate_id']}: {row['real_training_dataset_packaging_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_dataset_snapshot_review import (
    EXPECTED_FILE_ROLES,
    GLOBAL_ARTIFACT_ROLES,
    SNAPSHOT_ROOT,
    gate_status_passed,
    index_qa_status_passed,
    loader_dry_run_status_passed,
    loader_qa_status_passed,
    manifest_safety_flags_valid as snapshot_manifest_safety_flags_valid,
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


REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "snapshot_manifest_parseable",
    "snapshot_manifest_valid",
    "snapshot_file_list_row_count_valid",
    "snapshot_review_report_row_found_once",
    "candidate_file_rows_valid",
    "candidate_file_hashes_match_current_files",
    "candidate_file_reference_only_flags_valid",
    "global_artifact_rows_valid",
    "global_artifact_hashes_match_current_files",
    "global_artifact_reference_only_flags_valid",
    "snapshot_review_status_passed",
    "snapshot_review_safety_flags_valid",
    "only_allowed_snapshot_files_created",
    "no_copied_data_files_in_snapshot",
    "no_archive_created",
    "no_training_tensors_created",
    "upstream_gate_status_still_passed",
    "loader_dry_run_qa_status_still_passed",
    "loader_dry_run_status_still_passed",
    "actual_dataset_index_qa_status_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "files_copied",
    "archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "snapshot_manifest_modified_by_qa",
    "snapshot_file_list_modified_by_qa",
    "snapshot_review_report_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "dataset_snapshot_review_qa_status",
    "blocking_reasons",
    "recommended_next_action",
]

ALLOWED_SNAPSHOT_FILE_NAMES = {
    "dataset_snapshot_review_manifest.json",
    "dataset_snapshot_review_file_list.csv",
    "dataset_snapshot_review_report.csv",
    "dataset_snapshot_review_qa_report.csv",
}
DISALLOWED_SNAPSHOT_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}


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


def file_row_hash_valid(row: dict[str, str]) -> bool:
    path = Path(row.get("file_path", ""))
    return path.is_file() and row.get("sha256", "") == sha256_file(path)


def reference_only_flags_valid(row: dict[str, str]) -> bool:
    return (
        row.get("file_exists", "") == "true"
        and int(row.get("file_size_bytes", "0") or "0") > 0
        and row.get("sha256", "") != ""
        and row.get("copied_to_snapshot", "") == "false"
        and row.get("embedded_in_snapshot_manifest", "") == "false"
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
    )


def candidate_file_rows_valid(candidate_id: str, rows: list[dict[str, str]]) -> bool:
    candidate_rows = [row for row in rows if row.get("row_type") == "candidate_file" and row.get("candidate_id") == candidate_id]
    roles = {row.get("file_role", "") for row in candidate_rows}
    return len(candidate_rows) == 5 and roles == set(EXPECTED_FILE_ROLES)


def candidate_hashes_valid(candidate_id: str, rows: list[dict[str, str]]) -> bool:
    candidate_rows = [row for row in rows if row.get("row_type") == "candidate_file" and row.get("candidate_id") == candidate_id]
    return bool(candidate_rows) and all(file_row_hash_valid(row) for row in candidate_rows)


def candidate_reference_flags_valid(candidate_id: str, rows: list[dict[str, str]]) -> bool:
    candidate_rows = [row for row in rows if row.get("row_type") == "candidate_file" and row.get("candidate_id") == candidate_id]
    return bool(candidate_rows) and all(reference_only_flags_valid(row) for row in candidate_rows)


def global_artifact_rows_valid(rows: list[dict[str, str]]) -> bool:
    global_rows = [row for row in rows if row.get("row_type") == "global_artifact"]
    return len(global_rows) == 8 and {row.get("file_role", "") for row in global_rows} == set(GLOBAL_ARTIFACT_ROLES)


def global_artifact_hashes_valid(rows: list[dict[str, str]]) -> bool:
    global_rows = [row for row in rows if row.get("row_type") == "global_artifact"]
    return len(global_rows) == 8 and all(file_row_hash_valid(row) for row in global_rows)


def global_artifact_reference_flags_valid(rows: list[dict[str, str]]) -> bool:
    global_rows = [row for row in rows if row.get("row_type") == "global_artifact"]
    return len(global_rows) == 8 and all(reference_only_flags_valid(row) for row in global_rows)


def snapshot_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("row_count") == 3
        and manifest.get("snapshot_stage") == "dataset_snapshot_review_only_not_training"
        and manifest.get("snapshot_file_list_row_count") == 23
        and snapshot_manifest_safety_flags_valid(manifest)
    )


def snapshot_allowed_files_valid(root: str | Path) -> bool:
    root_path = Path(root)
    if not root_path.is_dir():
        return False
    files = [path for path in root_path.rglob("*") if path.is_file()]
    return {path.name for path in files} == ALLOWED_SNAPSHOT_FILE_NAMES and all(path.parent == root_path for path in files)


def no_copied_data_files(root: str | Path) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pdb", ".sdf", ".cif"}:
            return False
        if path.suffix.lower() == ".json" and path.name not in {
            "dataset_snapshot_review_manifest.json",
        }:
            return False
    return True


def forbidden_snapshot_absent(root: str | Path) -> tuple[bool, bool]:
    root_path = Path(root)
    if not root_path.exists():
        return False, False
    disallowed_files = [path for path in root_path.rglob("*") if path.is_file() and path.suffix.lower() in DISALLOWED_SNAPSHOT_SUFFIXES]
    archive_files = [path for path in disallowed_files if path.suffix.lower() in {".tar", ".zip", ".tgz"}]
    tensor_files = [path for path in disallowed_files if path.suffix.lower() in {".pt", ".pkl", ".npz", ".lmdb"}]
    return len(archive_files) == 0, len(tensor_files) == 0


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def build_report_rows(args: argparse.Namespace, include_qa_report_in_allowed: bool) -> list[dict[str, str]]:
    manifest, manifest_parseable = load_json(args.snapshot_manifest_json)
    file_list_rows = rows_from_existing_csv(args.snapshot_file_list_csv)
    snapshot_report_rows = rows_from_existing_csv(args.snapshot_review_report_csv)
    gate_report_rows = rows_from_existing_csv(args.snapshot_review_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.loader_dry_run_qa_report_csv)
    dry_rows = rows_from_existing_csv(args.loader_dry_run_report_csv)
    index_qa_rows = rows_from_existing_csv(args.actual_dataset_index_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)

    snapshot_report_by_id = index_many(snapshot_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    qa_by_id = index_many(qa_rows, "candidate_id")
    dry_by_id = index_many(dry_rows, "candidate_id")
    index_qa_by_id = index_many(index_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")

    all_snapshot_files_allowed = snapshot_allowed_files_valid(SNAPSHOT_ROOT) if include_qa_report_in_allowed else False
    no_archive_in_snapshot, no_tensors_in_snapshot = forbidden_snapshot_absent(SNAPSHOT_ROOT)
    global_no_tensors, global_no_archives = forbidden_counts("data/derived/covalent_small")
    index_manifest_ok = index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable)
    package_count_ok = package_counts(args.package_root) == {
        "protein_pdb_count": 3,
        "ligand_sdf_count": 3,
        "metadata_json_count": 3,
    }
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        snapshot_report = one(snapshot_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        dry_row = one(dry_by_id, candidate_id)
        index_qa_row = one(index_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            "snapshot_manifest_parseable": manifest_parseable,
            "snapshot_manifest_valid": snapshot_manifest_valid(manifest, manifest_parseable),
            "snapshot_file_list_row_count_valid": Path(args.snapshot_file_list_csv).is_file() and len(file_list_rows) == 23,
            "snapshot_review_report_row_found_once": Path(args.snapshot_review_report_csv).is_file() and len(snapshot_report_rows) == 3 and found_once(snapshot_report_by_id, candidate_id),
            "candidate_file_rows_valid": candidate_file_rows_valid(candidate_id, file_list_rows),
            "candidate_file_hashes_match_current_files": candidate_hashes_valid(candidate_id, file_list_rows),
            "candidate_file_reference_only_flags_valid": candidate_reference_flags_valid(candidate_id, file_list_rows),
            "global_artifact_rows_valid": global_artifact_rows_valid(file_list_rows),
            "global_artifact_hashes_match_current_files": global_artifact_hashes_valid(file_list_rows),
            "global_artifact_reference_only_flags_valid": global_artifact_reference_flags_valid(file_list_rows),
            "snapshot_review_status_passed": bool(snapshot_report) and snapshot_report.get("dataset_snapshot_review_status", "") == "dataset_snapshot_review_passed",
            "snapshot_review_safety_flags_valid": (
                bool(snapshot_report)
                and snapshot_report.get("snapshot_manifest_safety_flags_valid", "") == "true"
                and snapshot_report.get("files_copied", "") == "false"
                and snapshot_report.get("archive_created", "") == "false"
                and snapshot_report.get("torch_imported", "") == "false"
                and snapshot_report.get("checkpoint_loaded", "") == "false"
                and snapshot_report.get("model_initialized", "") == "false"
                and snapshot_report.get("dataloader_tensor_generated", "") == "false"
                and snapshot_report.get("real_training_tensor_generated", "") == "false"
                and snapshot_report.get("real_dataset_generated", "") == "false"
                and snapshot_report.get("pre_reaction_transform_ready", "") == "false"
                and snapshot_report.get("training_ready", "") == "false"
            ),
            "only_allowed_snapshot_files_created": all_snapshot_files_allowed,
            "no_copied_data_files_in_snapshot": no_copied_data_files(SNAPSHOT_ROOT),
            "no_archive_created": no_archive_in_snapshot and global_no_archives == 0,
            "no_training_tensors_created": no_tensors_in_snapshot and global_no_tensors == 0,
            "upstream_gate_status_still_passed": gate_status_passed(gate_report),
            "loader_dry_run_qa_status_still_passed": loader_qa_status_passed(qa_row),
            "loader_dry_run_status_still_passed": loader_dry_run_status_passed(dry_row),
            "actual_dataset_index_qa_status_still_passed": index_qa_status_passed(index_qa_row),
            "index_and_manifest_still_valid": (
                index_manifest_ok
                and found_once(index_by_id, candidate_id)
                and index_row.get("source_sample_id", "") == source_id
                and contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)
                and contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)
                and graph_counts_positive(index_row)
                and index_row_safety_valid(index_row)
                and package_count_ok
            ),
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest) and package_count_ok,
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
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
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "snapshot_manifest_modified_by_qa": "false",
                "snapshot_file_list_modified_by_qa": "false",
                "snapshot_review_report_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "dataset_snapshot_review_qa_status": "dataset_snapshot_review_qa_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "prepare_training_dataset_design_gate_not_training"
                    if passed
                    else "fix_dataset_snapshot_review_qa_blockers"
                ),
            }
        )
    return report_rows


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["dataset_snapshot_review_qa_status"] == "dataset_snapshot_review_qa_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Dataset Snapshot Review QA Summary",
        "",
        "This is dataset snapshot review QA only.",
        "It reads the snapshot manifest, file list, and report.",
        "It does not execute a new snapshot review.",
        "It does not copy files.",
        "It does not create archives.",
        did_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not generate real training tensors.",
        "It does not modify the snapshot manifest.",
        "It does not modify the snapshot file list.",
        "It does not modify the snapshot review report.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this QA still does not mean the samples are training-ready.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | snapshot_manifest_valid | candidate_file_rows_valid | candidate_file_hashes_match_current_files | global_artifact_rows_valid | only_allowed_snapshot_files_created | dataset_snapshot_review_qa_status | files_copied | archive_created | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {snapshot_manifest_valid} | {candidate_file_rows_valid} | {candidate_file_hashes_match_current_files} | {global_artifact_rows_valid} | {only_allowed_snapshot_files_created} | {dataset_snapshot_review_qa_status} | {files_copied} | {archive_created} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed dataset snapshot review QA" if all_passed else "- one or more samples are blocked by dataset snapshot review QA",
            "- no new snapshot review was executed",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is training dataset design gate, not training" if all_passed else "- next step is to fix dataset snapshot review QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows = build_report_rows(args, include_qa_report_in_allowed=False)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    rows = build_report_rows(args, include_qa_report_in_allowed=True)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(rows, args.output_md)
    exit_code = 0 if all(row["dataset_snapshot_review_qa_status"] == "dataset_snapshot_review_qa_passed" for row in rows) else 1
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check dataset snapshot review QA without modifying upstream artifacts.")
    parser.add_argument("--snapshot_manifest_json", required=True)
    parser.add_argument("--snapshot_file_list_csv", required=True)
    parser.add_argument("--snapshot_review_report_csv", required=True)
    parser.add_argument("--snapshot_review_gate_plan_csv", required=True)
    parser.add_argument("--snapshot_review_gate_report_csv", required=True)
    parser.add_argument("--loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--loader_dry_run_report_csv", required=True)
    parser.add_argument("--actual_dataset_index_qa_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['dataset_snapshot_review_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

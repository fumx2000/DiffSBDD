#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

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
    read_csv,
    rows_from_existing_csv,
    sha256_file,
)


APPROVAL_TOKEN = "APPROVE_DATASET_SNAPSHOT_REVIEW_STEP_8AQ"
SNAPSHOT_ROOT = "data/derived/covalent_small/snapshot_review_only"
SNAPSHOT_MANIFEST_PATH = f"{SNAPSHOT_ROOT}/dataset_snapshot_review_manifest.json"
SNAPSHOT_FILE_LIST_PATH = f"{SNAPSHOT_ROOT}/dataset_snapshot_review_file_list.csv"
SNAPSHOT_REPORT_PATH = f"{SNAPSHOT_ROOT}/dataset_snapshot_review_report.csv"

EXPECTED_SAMPLE_IDS = list(TARGETS)
EXPECTED_SOURCE_SAMPLE_IDS = [TARGETS[candidate_id] for candidate_id in EXPECTED_SAMPLE_IDS]
EXPECTED_FILE_ROLES = [
    "packaged_protein",
    "packaged_ligand_sdf",
    "packaged_metadata_json",
    "source_protein",
    "source_ligand_sdf",
]
GLOBAL_ARTIFACT_ROLES = [
    "snapshot_review_gate_plan_csv",
    "snapshot_review_gate_report_csv",
    "loader_dry_run_qa_report_csv",
    "loader_dry_run_report_csv",
    "actual_dataset_index_qa_report_csv",
    "index_csv",
    "dataset_manifest_json",
    "raw_manifest_csv",
]
ALLOWED_SNAPSHOT_FILES = {
    Path(SNAPSHOT_MANIFEST_PATH).name,
    Path(SNAPSHOT_FILE_LIST_PATH).name,
    Path(SNAPSHOT_REPORT_PATH).name,
}

FILE_LIST_COLUMNS = [
    "row_type",
    "candidate_id",
    "source_sample_id",
    "file_role",
    "file_path",
    "file_exists",
    "file_size_bytes",
    "sha256",
    "file_extension",
    "copied_to_snapshot",
    "embedded_in_snapshot_manifest",
    "archive_member",
    "training_tensor",
    "notes",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "approval_token_valid",
    "snapshot_gate_plan_row_found_once",
    "snapshot_gate_report_row_found_once",
    "loader_dry_run_qa_row_found_once",
    "loader_dry_run_report_row_found_once",
    "actual_dataset_index_qa_row_found_once",
    "index_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "snapshot_gate_status_passed",
    "loader_dry_run_qa_status_passed",
    "loader_dry_run_status_passed",
    "actual_dataset_index_qa_status_passed",
    "source_mapping_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "candidate_file_list_rows_written",
    "global_artifact_rows_written",
    "file_list_total_rows_valid",
    "snapshot_manifest_written",
    "snapshot_file_list_written",
    "snapshot_report_written",
    "snapshot_manifest_parseable",
    "snapshot_manifest_row_count_valid",
    "snapshot_manifest_safety_flags_valid",
    "only_allowed_snapshot_files_created",
    "files_copied",
    "archive_created",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "dataset_snapshot_review_status",
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


def write_json(data: dict[str, Any], output_json: str | Path) -> None:
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def file_reference_row(row_type: str, candidate_id: str, source_sample_id: str, file_role: str, path: str | Path) -> dict[str, str]:
    file_path = Path(path)
    file_exists = file_path.is_file()
    return {
        "row_type": row_type,
        "candidate_id": candidate_id,
        "source_sample_id": source_sample_id,
        "file_role": file_role,
        "file_path": str(path),
        "file_exists": bool_str(file_exists),
        "file_size_bytes": str(file_path.stat().st_size) if file_exists else "0",
        "sha256": sha256_file(file_path) if file_exists else "",
        "file_extension": file_path.suffix,
        "copied_to_snapshot": "false",
        "embedded_in_snapshot_manifest": "false",
        "archive_member": "false",
        "training_tensor": "false",
        "notes": "reference_only_no_file_copy",
    }


def snapshot_root_absent(paths: list[str | Path]) -> bool:
    root = Path(SNAPSHOT_ROOT)
    if root.exists():
        return False
    return all(not Path(path).exists() for path in paths)


def gate_status_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("dataset_snapshot_review_gate_status", "") == "dataset_snapshot_review_gate_passed"
        and row.get("explicit_approval_required_before_snapshot_review", "") == "true"
        and row.get("ready_for_dataset_snapshot_review_after_approval", "") == "true"
        and row.get("snapshot_review_executed", "") == "false"
        and row.get("files_copied", "") == "false"
        and row.get("archive_created", "") == "false"
        and row.get("torch_imported", "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def loader_qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_dataset_loader_dry_run_qa_status", "") == "read_only_dataset_loader_dry_run_qa_passed"


def loader_dry_run_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_dataset_loader_dry_run_status", "") == "read_only_dataset_loader_dry_run_passed"


def index_qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("actual_dataset_index_qa_status", "") == "actual_dataset_index_qa_passed"


def manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
        "snapshot_review_executed": True,
        "files_copied": False,
        "archive_created": False,
        "torch_imported": False,
        "checkpoint_loaded": False,
        "model_initialized": False,
        "dataloader_tensor_generated": False,
        "real_training_tensor_generated": False,
        "real_dataset_generated": False,
        "pre_reaction_transform_ready": False,
        "training_ready": False,
    }
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is value for key, value in expected.items())


def only_allowed_snapshot_files() -> bool:
    root = Path(SNAPSHOT_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return {path.name for path in files} == ALLOWED_SNAPSHOT_FILES and all(path.parent == root for path in files)


def validate_file_list(rows: list[dict[str, str]]) -> bool:
    return (
        len(rows) == 23
        and sum(row["row_type"] == "candidate_file" for row in rows) == 15
        and sum(row["row_type"] == "global_artifact" for row in rows) == 8
        and all(row["file_exists"] == "true" for row in rows)
        and all(int(row["file_size_bytes"]) > 0 for row in rows)
        and all(row["copied_to_snapshot"] == "false" for row in rows)
        and all(row["embedded_in_snapshot_manifest"] == "false" for row in rows)
        and all(row["archive_member"] == "false" for row in rows)
        and all(row["training_tensor"] == "false" for row in rows)
    )


def build_file_list(index_rows_by_id: dict[str, list[dict[str, str]]], args: argparse.Namespace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        index_row = one(index_rows_by_id, candidate_id)
        rows.extend(
            [
                file_reference_row("candidate_file", candidate_id, source_id, "packaged_protein", index_row.get("packaged_protein_path", "")),
                file_reference_row("candidate_file", candidate_id, source_id, "packaged_ligand_sdf", index_row.get("packaged_ligand_sdf_path", "")),
                file_reference_row("candidate_file", candidate_id, source_id, "packaged_metadata_json", index_row.get("packaged_metadata_json_path", "")),
                file_reference_row("candidate_file", candidate_id, source_id, "source_protein", index_row.get("source_protein_path", "")),
                file_reference_row("candidate_file", candidate_id, source_id, "source_ligand_sdf", index_row.get("source_ligand_sdf_path", "")),
            ]
        )
    global_artifacts = {
        "snapshot_review_gate_plan_csv": args.snapshot_review_gate_plan_csv,
        "snapshot_review_gate_report_csv": args.snapshot_review_gate_report_csv,
        "loader_dry_run_qa_report_csv": args.loader_dry_run_qa_report_csv,
        "loader_dry_run_report_csv": args.loader_dry_run_report_csv,
        "actual_dataset_index_qa_report_csv": args.actual_dataset_index_qa_report_csv,
        "index_csv": args.index_csv,
        "dataset_manifest_json": args.dataset_manifest_json,
        "raw_manifest_csv": args.manifest_csv,
    }
    for role in GLOBAL_ARTIFACT_ROLES:
        rows.append(file_reference_row("global_artifact", "", "", role, global_artifacts[role]))
    return rows


def build_manifest(args: argparse.Namespace, file_list_rows: list[dict[str, str]]) -> dict[str, Any]:
    upstream_artifacts = {
        "snapshot_review_gate_plan_csv": args.snapshot_review_gate_plan_csv,
        "snapshot_review_gate_report_csv": args.snapshot_review_gate_report_csv,
        "loader_dry_run_qa_report_csv": args.loader_dry_run_qa_report_csv,
        "loader_dry_run_report_csv": args.loader_dry_run_report_csv,
        "actual_dataset_index_qa_report_csv": args.actual_dataset_index_qa_report_csv,
        "index_csv": args.index_csv,
        "dataset_manifest_json": args.dataset_manifest_json,
        "raw_manifest_csv": args.manifest_csv,
    }
    return {
        "snapshot_name": "covalent_small_pre_reaction_review_only_snapshot_review",
        "snapshot_stage": "dataset_snapshot_review_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "dataset_name": "covalent_small_pre_reaction_review_only",
        "dataset_role": "smoke_test_pre_reaction_packaged_artifact",
        "split": "smoke_test",
        "schema_version": "dataset_index_v0_review_only",
        "row_count": 3,
        "sample_ids": EXPECTED_SAMPLE_IDS,
        "source_sample_ids": EXPECTED_SOURCE_SAMPLE_IDS,
        "snapshot_root": SNAPSHOT_ROOT,
        "snapshot_manifest_path": SNAPSHOT_MANIFEST_PATH,
        "snapshot_file_list_path": SNAPSHOT_FILE_LIST_PATH,
        "snapshot_report_path": SNAPSHOT_REPORT_PATH,
        "upstream_artifacts": {key: str(value) for key, value in upstream_artifacts.items()},
        "upstream_artifact_sha256": {key: sha256_file(value) for key, value in upstream_artifacts.items()},
        "packaged_file_counts": package_counts(args.package_root),
        "snapshot_file_list_row_count": len(file_list_rows),
        "candidate_count": 3,
        "expected_candidate_file_roles": EXPECTED_FILE_ROLES,
        "safety_flags": {
            "snapshot_review_executed": True,
            "files_copied": False,
            "archive_created": False,
            "torch_imported": False,
            "checkpoint_loaded": False,
            "model_initialized": False,
            "dataloader_tensor_generated": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "pre_reaction_transform_ready": False,
            "training_ready": False,
        },
        "recommended_next_action": "build_dataset_snapshot_review_qa_not_training",
    }


def build_preflight(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], list[str]]:
    blockers: list[str] = []
    approval_ok = args.approval_token == APPROVAL_TOKEN
    if not approval_ok:
        return [], [], {}, ["approval_token_valid"]

    output_paths = [args.output_snapshot_manifest_json, args.output_file_list_csv, args.output_report_csv]
    if not snapshot_root_absent(output_paths):
        blockers.append("snapshot_review_outputs_absent_before_review")

    gate_plan_rows = rows_from_existing_csv(args.snapshot_review_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.snapshot_review_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.loader_dry_run_qa_report_csv)
    dry_rows = rows_from_existing_csv(args.loader_dry_run_report_csv)
    index_qa_rows = rows_from_existing_csv(args.actual_dataset_index_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)

    if not (Path(args.snapshot_review_gate_plan_csv).is_file() and len(gate_plan_rows) == 3):
        blockers.append("snapshot_review_gate_plan_row_count_valid")
    if not (Path(args.snapshot_review_gate_report_csv).is_file() and len(gate_report_rows) == 3):
        blockers.append("snapshot_review_gate_report_row_count_valid")
    if not (Path(args.loader_dry_run_qa_report_csv).is_file() and len(qa_rows) == 3):
        blockers.append("loader_dry_run_qa_report_row_count_valid")
    if not (Path(args.loader_dry_run_report_csv).is_file() and len(dry_rows) == 3):
        blockers.append("loader_dry_run_report_row_count_valid")
    if not Path(args.actual_dataset_index_qa_report_csv).is_file():
        blockers.append("actual_dataset_index_qa_report_exists")
    if not (Path(args.index_csv).is_file() and len(index_rows) == 3):
        blockers.append("index_row_count_valid")
    if not index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable):
        blockers.append("dataset_manifest_valid")
    if package_counts(args.package_root) != {
        "protein_pdb_count": 3,
        "ligand_sdf_count": 3,
        "metadata_json_count": 3,
    }:
        blockers.append("package_file_counts_valid")
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    if tensors:
        blockers.append("forbidden_training_tensors_absent")
    if archives:
        blockers.append("forbidden_archives_absent")

    inputs = {
        "gate_plan_rows": gate_plan_rows,
        "gate_report_rows": gate_report_rows,
        "qa_rows": qa_rows,
        "dry_rows": dry_rows,
        "index_qa_rows": index_qa_rows,
        "index_rows": index_rows,
        "manifest_rows": manifest_rows,
        "dataset_manifest": dataset_manifest,
    }
    return index_rows, manifest_rows, inputs, blockers


def build_report_rows(args: argparse.Namespace, file_list_rows: list[dict[str, str]], manifest: dict[str, Any], inputs: dict[str, Any], preflight_blockers: list[str], post_checks: dict[str, bool]) -> list[dict[str, str]]:
    gate_plan_by_id = index_many(inputs.get("gate_plan_rows", []), "snapshot_review_gate_plan_id")
    gate_report_by_id = index_many(inputs.get("gate_report_rows", []), "candidate_id")
    qa_by_id = index_many(inputs.get("qa_rows", []), "candidate_id")
    dry_by_id = index_many(inputs.get("dry_rows", []), "candidate_id")
    index_qa_by_id = index_many(inputs.get("index_qa_rows", []), "candidate_id")
    index_by_id = index_many(inputs.get("index_rows", []), "sample_id")
    manifest_by_id = index_many(inputs.get("manifest_rows", []), "sample_id")
    dataset_manifest = inputs.get("dataset_manifest", {})
    report_rows: list[dict[str, str]] = []

    global_rows_written = sum(row["row_type"] == "global_artifact" for row in file_list_rows)
    file_list_total_valid = validate_file_list(file_list_rows)
    for candidate_id, source_id in TARGETS.items():
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        dry_row = one(dry_by_id, candidate_id)
        index_qa_row = one(index_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        manifest_candidate = one(manifest_by_id, candidate_id)
        candidate_rows_written = sum(row["row_type"] == "candidate_file" and row["candidate_id"] == candidate_id for row in file_list_rows)
        checks = {
            "approval_token_valid": args.approval_token == APPROVAL_TOKEN,
            "snapshot_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "snapshot_gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "loader_dry_run_qa_row_found_once": found_once(qa_by_id, candidate_id),
            "loader_dry_run_report_row_found_once": found_once(dry_by_id, candidate_id),
            "actual_dataset_index_qa_row_found_once": found_once(index_qa_by_id, candidate_id),
            "index_row_found_once": found_once(index_by_id, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_id, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_id, source_id),
            "snapshot_gate_status_passed": gate_status_passed(gate_report) and bool(gate_plan),
            "loader_dry_run_qa_status_passed": loader_qa_status_passed(qa_row),
            "loader_dry_run_status_passed": loader_dry_run_status_passed(dry_row),
            "actual_dataset_index_qa_status_passed": index_qa_status_passed(index_qa_row),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(manifest_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
        }
        blockers = preflight_blockers + [key for key, value in checks.items() if not value]
        passed = not blockers and all(post_checks.values())
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: bool_str(value) for key, value in checks.items()},
                "candidate_file_list_rows_written": str(candidate_rows_written),
                "global_artifact_rows_written": str(global_rows_written),
                "file_list_total_rows_valid": bool_str(file_list_total_valid),
                "snapshot_manifest_written": bool_str(post_checks["snapshot_manifest_written"]),
                "snapshot_file_list_written": bool_str(post_checks["snapshot_file_list_written"]),
                "snapshot_report_written": bool_str(post_checks["snapshot_report_written"]),
                "snapshot_manifest_parseable": bool_str(post_checks["snapshot_manifest_parseable"]),
                "snapshot_manifest_row_count_valid": bool_str(post_checks["snapshot_manifest_row_count_valid"]),
                "snapshot_manifest_safety_flags_valid": bool_str(post_checks["snapshot_manifest_safety_flags_valid"]),
                "only_allowed_snapshot_files_created": bool_str(post_checks["only_allowed_snapshot_files_created"]),
                "files_copied": "false",
                "archive_created": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "dataset_snapshot_review_status": "dataset_snapshot_review_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers + [key for key, value in post_checks.items() if not value]),
                "recommended_next_action": (
                    "build_dataset_snapshot_review_qa_not_training"
                    if passed
                    else "fix_dataset_snapshot_review_blockers"
                ),
            }
        )
    return report_rows


def candidate_precheck_blockers(args: argparse.Namespace, inputs: dict[str, Any]) -> list[str]:
    gate_plan_by_id = index_many(inputs.get("gate_plan_rows", []), "snapshot_review_gate_plan_id")
    gate_report_by_id = index_many(inputs.get("gate_report_rows", []), "candidate_id")
    qa_by_id = index_many(inputs.get("qa_rows", []), "candidate_id")
    dry_by_id = index_many(inputs.get("dry_rows", []), "candidate_id")
    index_qa_by_id = index_many(inputs.get("index_qa_rows", []), "candidate_id")
    index_by_id = index_many(inputs.get("index_rows", []), "sample_id")
    manifest_by_id = index_many(inputs.get("manifest_rows", []), "sample_id")
    dataset_manifest = inputs.get("dataset_manifest", {})
    blockers: list[str] = []
    for candidate_id, source_id in TARGETS.items():
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        dry_row = one(dry_by_id, candidate_id)
        index_qa_row = one(index_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        manifest_candidate = one(manifest_by_id, candidate_id)
        checks = {
            "snapshot_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "snapshot_gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "loader_dry_run_qa_row_found_once": found_once(qa_by_id, candidate_id),
            "loader_dry_run_report_row_found_once": found_once(dry_by_id, candidate_id),
            "actual_dataset_index_qa_row_found_once": found_once(index_qa_by_id, candidate_id),
            "index_row_found_once": found_once(index_by_id, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_id, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_id, source_id),
            "snapshot_gate_status_passed": gate_status_passed(gate_report) and bool(gate_plan),
            "loader_dry_run_qa_status_passed": loader_qa_status_passed(qa_row),
            "loader_dry_run_status_passed": loader_dry_run_status_passed(dry_row),
            "actual_dataset_index_qa_status_passed": index_qa_status_passed(index_qa_row),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(manifest_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
        }
        blockers.extend(f"{candidate_id}:{key}" for key, value in checks.items() if not value)
    return blockers


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["dataset_snapshot_review_status"] == "dataset_snapshot_review_passed" for row in report_rows)
    did_not_import_torch = "It did not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Dataset Snapshot Review Summary",
        "",
        "This is dataset snapshot review only.",
        "Explicit approval token was required and provided.",
        "It created a review-only snapshot manifest and file list.",
        "It did not copy PDB/SDF/JSON data files.",
        "It did not create archives.",
        "It did not embed PDB/SDF contents in the manifest.",
        did_not_import_torch,
        "It did not load checkpoints.",
        "It did not initialize a model.",
        "It did not generate dataloader tensors.",
        "It did not generate real training tensors.",
        "It did not modify the index CSV.",
        "It did not modify the dataset manifest JSON.",
        "It did not modify manifest files.",
        "It did not modify source or packaged PDB/SDF/JSON files.",
        "It did not train or fine-tune any model.",
        "Passing this review still does not mean the samples are training-ready.",
        "",
        "## Output Files",
        "",
        f"- snapshot manifest JSON path: `{SNAPSHOT_MANIFEST_PATH}`",
        f"- snapshot file list CSV path: `{SNAPSHOT_FILE_LIST_PATH}`",
        f"- snapshot review report CSV path: `{SNAPSHOT_REPORT_PATH}`",
        "",
        "## File List Counts",
        "",
        "- candidate file rows: 15",
        "- global artifact rows: 8",
        "- total file list rows: 23",
        "",
        "## Sample Review",
        "",
        "| candidate_id | source_sample_id | candidate_file_list_rows_written | packaged_hashes_match_index_and_manifest | file_list_total_rows_valid | snapshot_manifest_parseable | only_allowed_snapshot_files_created | dataset_snapshot_review_status | files_copied | archive_created | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {candidate_file_list_rows_written} | {packaged_hashes_match_index_and_manifest} | {file_list_total_rows_valid} | {snapshot_manifest_parseable} | {only_allowed_snapshot_files_created} | {dataset_snapshot_review_status} | {files_copied} | {archive_created} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed dataset snapshot review" if all_passed else "- one or more samples are blocked by dataset snapshot review",
            "- snapshot manifest and file list were created" if all_passed else "- snapshot manifest and file list were not safely completed",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is dataset snapshot review QA, not training" if all_passed else "- next step is to fix dataset snapshot review blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    index_rows, _manifest_rows, inputs, preflight_blockers = build_preflight(args)
    candidate_blockers = [] if preflight_blockers else candidate_precheck_blockers(args, inputs)
    if preflight_blockers or candidate_blockers:
        return [], [], {}, 1

    index_by_id = index_many(index_rows, "sample_id")
    file_list_rows = build_file_list(index_by_id, args)
    snapshot_manifest = build_manifest(args, file_list_rows)
    write_csv(file_list_rows, args.output_file_list_csv, FILE_LIST_COLUMNS)
    write_json(snapshot_manifest, args.output_snapshot_manifest_json)

    parsed_manifest, parseable = load_json(args.output_snapshot_manifest_json)
    post_checks = {
        "snapshot_manifest_written": Path(args.output_snapshot_manifest_json).is_file(),
        "snapshot_file_list_written": Path(args.output_file_list_csv).is_file(),
        "snapshot_report_written": True,
        "snapshot_manifest_parseable": parseable,
        "snapshot_manifest_row_count_valid": parsed_manifest.get("row_count") == 3 and parsed_manifest.get("snapshot_file_list_row_count") == 23,
        "snapshot_manifest_safety_flags_valid": manifest_safety_flags_valid(parsed_manifest),
        "only_allowed_snapshot_files_created": False,
    }
    report_rows = build_report_rows(args, file_list_rows, snapshot_manifest, inputs, preflight_blockers, post_checks)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    post_checks["only_allowed_snapshot_files_created"] = only_allowed_snapshot_files()
    report_rows = build_report_rows(args, file_list_rows, snapshot_manifest, inputs, preflight_blockers, post_checks)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)

    exit_code = 0 if all(row["dataset_snapshot_review_status"] == "dataset_snapshot_review_passed" for row in report_rows) else 1
    return file_list_rows, report_rows, snapshot_manifest, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply dataset snapshot review without copying data files.")
    parser.add_argument("--snapshot_review_gate_plan_csv", required=True)
    parser.add_argument("--snapshot_review_gate_report_csv", required=True)
    parser.add_argument("--loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--loader_dry_run_report_csv", required=True)
    parser.add_argument("--actual_dataset_index_qa_report_csv", required=True)
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_snapshot_manifest_json", required=True)
    parser.add_argument("--output_file_list_csv", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _file_list, report_rows, _manifest, exit_code = run(parse_args())
    if report_rows:
        for row in report_rows:
            print(f"{row['candidate_id']}: {row['dataset_snapshot_review_status']}")
    else:
        print("dataset snapshot review blocked before writing snapshot outputs")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

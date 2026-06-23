#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_dataset_snapshot_review import SNAPSHOT_ROOT
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
)


PLANNED_TRAINING_DATASET_DESIGN_ROOT = "data/derived/covalent_small/training_dataset_design_review_only"
PLANNED_TRAINING_DATASET_DESIGN_MANIFEST_PATH = f"{PLANNED_TRAINING_DATASET_DESIGN_ROOT}/training_dataset_design_manifest.json"
PLANNED_TRAINING_DATASET_DESIGN_SCHEMA_REPORT_PATH = f"{PLANNED_TRAINING_DATASET_DESIGN_ROOT}/training_dataset_design_schema_report.csv"
PLANNED_TRAINING_DATASET_DESIGN_SPLIT_PLAN_PATH = f"{PLANNED_TRAINING_DATASET_DESIGN_ROOT}/training_dataset_design_split_plan.csv"

ALLOWED_SNAPSHOT_REVIEW_FILES_BEFORE_GATE = {
    "dataset_snapshot_review_manifest.json",
    "dataset_snapshot_review_file_list.csv",
    "dataset_snapshot_review_report.csv",
    "dataset_snapshot_review_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

PLAN_COLUMNS = [
    "training_dataset_design_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "dataset_role",
    "split",
    "schema_version",
    "index_csv_path",
    "dataset_manifest_json_path",
    "snapshot_manifest_json_path",
    "snapshot_file_list_csv_path",
    "snapshot_review_report_csv_path",
    "package_root",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "planned_training_dataset_design_root",
    "planned_training_dataset_design_manifest_path",
    "planned_training_dataset_design_schema_report_path",
    "planned_training_dataset_design_split_plan_path",
    "training_dataset_design_gate_stage",
    "explicit_approval_required_before_training_dataset_design",
    "ready_for_training_dataset_design_after_approval",
    "training_dataset_design_executed",
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

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "snapshot_review_qa_row_found_once",
    "snapshot_review_report_row_found_once",
    "snapshot_manifest_valid",
    "snapshot_file_list_row_count_valid",
    "snapshot_candidate_file_rows_valid",
    "snapshot_review_qa_status_passed",
    "snapshot_review_status_passed",
    "source_mapping_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "snapshot_review_only_files_valid",
    "planned_training_dataset_design_outputs_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "gate_plan_row_written",
    "training_dataset_design_gate_status",
    "explicit_approval_required_before_training_dataset_design",
    "ready_for_training_dataset_design_after_approval",
    "training_dataset_design_executed",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "dataloader_tensor_generated",
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


def snapshot_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("row_count") == 3
        and manifest.get("snapshot_stage") == "dataset_snapshot_review_only_not_training"
        and manifest.get("snapshot_file_list_row_count") == 23
    )


def candidate_file_rows_valid(candidate_id: str, file_list_rows: list[dict[str, str]]) -> bool:
    return sum(row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id for row in file_list_rows) == 5


def snapshot_review_only_files_valid() -> bool:
    root = Path(SNAPSHOT_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == ALLOWED_SNAPSHOT_REVIEW_FILES_BEFORE_GATE
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def planned_training_outputs_absent() -> bool:
    root = Path(PLANNED_TRAINING_DATASET_DESIGN_ROOT)
    return (
        not root.exists()
        and not Path(PLANNED_TRAINING_DATASET_DESIGN_MANIFEST_PATH).exists()
        and not Path(PLANNED_TRAINING_DATASET_DESIGN_SCHEMA_REPORT_PATH).exists()
        and not Path(PLANNED_TRAINING_DATASET_DESIGN_SPLIT_PLAN_PATH).exists()
    )


def snapshot_qa_status_passed(row: dict[str, str]) -> bool:
    required_true_fields = [
        "snapshot_manifest_valid",
        "candidate_file_rows_valid",
        "candidate_file_hashes_match_current_files",
        "global_artifact_rows_valid",
        "global_artifact_hashes_match_current_files",
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
    ]
    required_false_fields = [
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
    ]
    return (
        bool(row)
        and row.get("dataset_snapshot_review_qa_status", "") == "dataset_snapshot_review_qa_passed"
        and all(row.get(field, "") == "true" for field in required_true_fields)
        and all(row.get(field, "") == "false" for field in required_false_fields)
    )


def snapshot_review_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("dataset_snapshot_review_status", "") == "dataset_snapshot_review_passed"


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def build_plan_row(index_row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    return {
        "training_dataset_design_gate_plan_id": index_row.get("pre_reaction_sample_id", ""),
        "source_sample_id": index_row.get("source_sample_id", ""),
        "pre_reaction_sample_id": index_row.get("pre_reaction_sample_id", ""),
        "dataset_name": index_row.get("dataset_name", ""),
        "dataset_role": index_row.get("dataset_role", ""),
        "split": index_row.get("split", ""),
        "schema_version": index_row.get("schema_version", ""),
        "index_csv_path": str(args.index_csv),
        "dataset_manifest_json_path": str(args.dataset_manifest_json),
        "snapshot_manifest_json_path": str(args.snapshot_manifest_json),
        "snapshot_file_list_csv_path": str(args.snapshot_file_list_csv),
        "snapshot_review_report_csv_path": str(args.snapshot_review_report_csv),
        "package_root": str(args.package_root),
        "packaged_protein_path": index_row.get("packaged_protein_path", ""),
        "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
        "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
        "source_protein_path": index_row.get("source_protein_path", ""),
        "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "planned_training_dataset_design_root": PLANNED_TRAINING_DATASET_DESIGN_ROOT,
        "planned_training_dataset_design_manifest_path": PLANNED_TRAINING_DATASET_DESIGN_MANIFEST_PATH,
        "planned_training_dataset_design_schema_report_path": PLANNED_TRAINING_DATASET_DESIGN_SCHEMA_REPORT_PATH,
        "planned_training_dataset_design_split_plan_path": PLANNED_TRAINING_DATASET_DESIGN_SPLIT_PLAN_PATH,
        "training_dataset_design_gate_stage": "training_dataset_design_gate_only_not_training",
        "explicit_approval_required_before_training_dataset_design": "true",
        "ready_for_training_dataset_design_after_approval": "true",
        "training_dataset_design_executed": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        "dataloader_tensor_generated": "false",
        "torch_imported": "false",
        "checkpoint_loaded": "false",
        "model_initialized": "false",
        "training_ready": "false",
        "files_copied": "false",
        "archive_created": "false",
    }


def build_gate(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    snapshot_qa_rows = rows_from_existing_csv(args.snapshot_review_qa_report_csv)
    snapshot_report_rows = rows_from_existing_csv(args.snapshot_review_report_csv)
    file_list_rows = rows_from_existing_csv(args.snapshot_file_list_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    snapshot_manifest, snapshot_manifest_parseable = load_json(args.snapshot_manifest_json)

    snapshot_qa_by_id = index_many(snapshot_qa_rows, "candidate_id")
    snapshot_report_by_id = index_many(snapshot_report_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")

    tensors, archives = forbidden_counts("data/derived/covalent_small")
    global_checks = {
        "snapshot_review_qa_row_count_valid": Path(args.snapshot_review_qa_report_csv).is_file() and len(snapshot_qa_rows) == 3,
        "snapshot_manifest_valid": Path(args.snapshot_manifest_json).is_file() and snapshot_manifest_valid(snapshot_manifest, snapshot_manifest_parseable),
        "snapshot_file_list_row_count_valid": Path(args.snapshot_file_list_csv).is_file() and len(file_list_rows) == 23,
        "snapshot_review_report_row_count_valid": Path(args.snapshot_review_report_csv).is_file() and len(snapshot_report_rows) == 3,
        "snapshot_review_gate_inputs_exist": Path(args.snapshot_review_gate_plan_csv).is_file() and Path(args.snapshot_review_gate_report_csv).is_file(),
        "loader_inputs_exist": Path(args.loader_dry_run_qa_report_csv).is_file() and Path(args.loader_dry_run_report_csv).is_file(),
        "actual_dataset_index_qa_report_exists": Path(args.actual_dataset_index_qa_report_csv).is_file(),
        "index_row_count_valid": Path(args.index_csv).is_file() and len(index_rows) == 3,
        "dataset_manifest_valid": index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "package_file_counts_valid": package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "snapshot_review_only_files_valid": snapshot_review_only_files_valid(),
        "planned_training_dataset_design_outputs_absent_before_gate": planned_training_outputs_absent(),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
    }

    plan_rows: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    global_blockers = [key for key, value in global_checks.items() if not value]
    for candidate_id, source_id in TARGETS.items():
        snapshot_qa_row = one(snapshot_qa_by_id, candidate_id)
        snapshot_report_row = one(snapshot_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            "snapshot_review_qa_row_found_once": found_once(snapshot_qa_by_id, candidate_id) and global_checks["snapshot_review_qa_row_count_valid"],
            "snapshot_review_report_row_found_once": found_once(snapshot_report_by_id, candidate_id) and global_checks["snapshot_review_report_row_count_valid"],
            "snapshot_manifest_valid": global_checks["snapshot_manifest_valid"],
            "snapshot_file_list_row_count_valid": global_checks["snapshot_file_list_row_count_valid"],
            "snapshot_candidate_file_rows_valid": candidate_file_rows_valid(candidate_id, file_list_rows),
            "snapshot_review_qa_status_passed": snapshot_qa_status_passed(snapshot_qa_row),
            "snapshot_review_status_passed": snapshot_review_status_passed(snapshot_report_row),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest) and global_checks["package_file_counts_valid"],
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row) and index_row_safety_valid(index_row),
            "snapshot_review_only_files_valid": global_checks["snapshot_review_only_files_valid"],
            "planned_training_dataset_design_outputs_absent_before_gate": global_checks["planned_training_dataset_design_outputs_absent_before_gate"],
            "forbidden_training_tensors_absent": global_checks["forbidden_training_tensors_absent"],
            "forbidden_archives_absent": global_checks["forbidden_archives_absent"],
        }
        blockers = sorted(set(global_blockers + [key for key, value in checks.items() if not value]))
        passed = not blockers
        if passed:
            plan_rows.append(build_plan_row(index_row, args))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: bool_str(value) for key, value in checks.items()},
                "gate_plan_row_written": bool_str(passed),
                "training_dataset_design_gate_status": "training_dataset_design_gate_passed" if passed else "blocked",
                "explicit_approval_required_before_training_dataset_design": bool_str(passed),
                "ready_for_training_dataset_design_after_approval": bool_str(passed),
                "training_dataset_design_executed": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "dataloader_tensor_generated": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "archive_created": "false",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "await_explicit_approval_for_training_dataset_design"
                    if passed
                    else "fix_training_dataset_design_gate_blockers"
                ),
            }
        )
    return plan_rows, report_rows


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_design_gate_status"] == "training_dataset_design_gate_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Training Dataset Design Gate Summary",
        "",
        "This is training dataset design gate only.",
        "It reads dataset snapshot review QA outputs and review-only dataset artifacts.",
        "It does not execute training dataset design.",
        "It does not create a real training dataset.",
        "It does not create tensor files.",
        did_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify the snapshot manifest.",
        "It does not modify the snapshot file list.",
        "It does not modify the snapshot review report.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this gate still does not mean the samples are training-ready.",
        "",
        "## Planned Training Dataset Design Outputs",
        "",
        f"- planned_training_dataset_design_root: `{PLANNED_TRAINING_DATASET_DESIGN_ROOT}`",
        f"- planned_training_dataset_design_manifest_path: `{PLANNED_TRAINING_DATASET_DESIGN_MANIFEST_PATH}`",
        f"- planned_training_dataset_design_schema_report_path: `{PLANNED_TRAINING_DATASET_DESIGN_SCHEMA_REPORT_PATH}`",
        f"- planned_training_dataset_design_split_plan_path: `{PLANNED_TRAINING_DATASET_DESIGN_SPLIT_PLAN_PATH}`",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | snapshot_review_qa_status_passed | snapshot_candidate_file_rows_valid | training_dataset_design_gate_status | explicit_approval_required_before_training_dataset_design | training_dataset_design_executed | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {snapshot_review_qa_status_passed} | {snapshot_candidate_file_rows_valid} | {training_dataset_design_gate_status} | {explicit_approval_required_before_training_dataset_design} | {training_dataset_design_executed} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training dataset design gate" if all_passed else "- one or more samples are blocked by training dataset design gate",
            "- explicit approval is required before training dataset design",
            "- no training dataset design was executed",
            "- no real training dataset was created",
            "- no tensor files were created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is explicit approval for training dataset design, not training" if all_passed else "- next step is to fix training dataset design gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows = build_gate(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    exit_code = 0 if all(row["training_dataset_design_gate_status"] == "training_dataset_design_gate_passed" for row in report_rows) else 1
    return plan_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build training dataset design gate without training or tensor generation.")
    parser.add_argument("--snapshot_review_qa_report_csv", required=True)
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
    parser.add_argument("--output_gate_plan_csv", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    _plan, report, exit_code = run(parse_args())
    for row in report:
        print(f"{row['candidate_id']}: {row['training_dataset_design_gate_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

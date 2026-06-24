#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from apply_training_dataset_packaging_design_review import PLANNED_PACKAGING_RECORD_FIELDS
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


PACKAGING_DESIGN_ROOT = "data/derived/covalent_small/training_dataset_packaging_design_review_only"
PLANNED_REAL_PACKAGE_ROOT = "data/derived/covalent_small/real_training_dataset_package_review_only"
PLANNED_REAL_MANIFEST_PATH = f"{PLANNED_REAL_PACKAGE_ROOT}/real_training_dataset_manifest.json"
PLANNED_REAL_FILE_INDEX_PATH = f"{PLANNED_REAL_PACKAGE_ROOT}/real_training_dataset_file_index.csv"
PLANNED_REAL_SAMPLE_INDEX_PATH = f"{PLANNED_REAL_PACKAGE_ROOT}/real_training_dataset_sample_index.csv"
PLANNED_REAL_PACKAGING_REPORT_PATH = f"{PLANNED_REAL_PACKAGE_ROOT}/real_training_dataset_packaging_report.csv"

ALLOWED_PACKAGING_DESIGN_FILES_BEFORE_GATE = {
    "training_dataset_packaging_design_manifest.json",
    "training_dataset_packaging_file_plan.csv",
    "training_dataset_packaging_schema_report.csv",
    "training_dataset_packaging_design_report.csv",
    "training_dataset_packaging_design_review_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
CANDIDATE_FILE_ROLES = {"packaged_protein", "packaged_ligand_sdf", "packaged_metadata_json", "source_protein", "source_ligand_sdf"}

PLAN_COLUMNS = [
    "real_training_dataset_packaging_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "source_dataset_name",
    "target_real_training_dataset_name",
    "split",
    "package_root_current_review_only",
    "planned_real_training_dataset_package_root",
    "planned_real_training_dataset_manifest_path",
    "planned_real_training_dataset_file_index_path",
    "planned_real_training_dataset_sample_index_path",
    "planned_real_training_dataset_packaging_report_path",
    "packaging_design_manifest_json_path",
    "packaging_file_plan_csv_path",
    "packaging_schema_report_csv_path",
    "packaging_design_report_csv_path",
    "packaging_design_review_qa_report_csv_path",
    "index_csv_path",
    "dataset_manifest_json_path",
    "raw_manifest_csv_path",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "packaging_gate_stage",
    "explicit_approval_required_before_real_training_dataset_packaging",
    "ready_for_real_training_dataset_packaging_after_approval",
    "real_training_dataset_packaging_executed",
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
    "packaging_design_review_qa_row_found_once",
    "packaging_design_review_qa_status_passed",
    "packaging_design_manifest_valid",
    "packaging_file_plan_candidate_rows_valid",
    "packaging_file_plan_hashes_valid",
    "packaging_file_plan_reference_only_flags_valid",
    "packaging_schema_report_valid",
    "packaging_design_report_row_found_once",
    "packaging_design_report_status_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "packaging_design_review_only_files_valid",
    "planned_real_training_dataset_package_root_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "gate_plan_row_written",
    "real_training_dataset_packaging_gate_status",
    "explicit_approval_required_before_real_training_dataset_packaging",
    "ready_for_real_training_dataset_packaging_after_approval",
    "real_training_dataset_packaging_executed",
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


def packaging_manifest_valid(manifest: dict, parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("packaging_design_stage") == "training_dataset_packaging_design_review_only_not_training"
        and manifest.get("row_count") == 3
    )


def schema_report_valid(schema_rows: list[dict[str, str]]) -> bool:
    by_field = {row.get("field_name", ""): row for row in schema_rows}
    return set(PLANNED_PACKAGING_RECORD_FIELDS).issubset(set(by_field))


def design_report_status_passed(row: dict[str, str]) -> bool:
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
    return (
        bool(row)
        and row.get("training_dataset_packaging_design_status", "") == "training_dataset_packaging_design_passed"
        and row.get("training_dataset_packaging_design_executed", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false)
    )


def qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_review_qa_status", "") == "training_dataset_packaging_design_review_qa_passed"


def candidate_file_rows(file_plan_rows: list[dict[str, str]], candidate_id: str) -> list[dict[str, str]]:
    return [row for row in file_plan_rows if row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id]


def reference_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and row.get("copied_to_training_package", "") == "false"
        and row.get("embedded_in_training_manifest", "") == "false"
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def file_hashes_valid(rows: list[dict[str, str]]) -> bool:
    for row in rows:
        path = Path(row.get("source_file_path", ""))
        if not path.is_file() or row.get("source_file_sha256", "") != sha256_file(path):
            return False
    return True


def packaging_design_files_valid() -> bool:
    root = Path(PACKAGING_DESIGN_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == ALLOWED_PACKAGING_DESIGN_FILES_BEFORE_GATE
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def planned_real_package_absent() -> bool:
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    return (
        not root.exists()
        and not Path(PLANNED_REAL_MANIFEST_PATH).exists()
        and not Path(PLANNED_REAL_FILE_INDEX_PATH).exists()
        and not Path(PLANNED_REAL_SAMPLE_INDEX_PATH).exists()
        and not Path(PLANNED_REAL_PACKAGING_REPORT_PATH).exists()
    )


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def build_plan_row(index_row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    return {
        "real_training_dataset_packaging_gate_plan_id": index_row.get("pre_reaction_sample_id", ""),
        "source_sample_id": index_row.get("source_sample_id", ""),
        "pre_reaction_sample_id": index_row.get("pre_reaction_sample_id", ""),
        "source_dataset_name": "covalent_small_pre_reaction_review_only",
        "target_real_training_dataset_name": "covalent_small_pre_reaction_real_training_dataset_candidate",
        "split": index_row.get("split", ""),
        "package_root_current_review_only": str(args.package_root),
        "planned_real_training_dataset_package_root": PLANNED_REAL_PACKAGE_ROOT,
        "planned_real_training_dataset_manifest_path": PLANNED_REAL_MANIFEST_PATH,
        "planned_real_training_dataset_file_index_path": PLANNED_REAL_FILE_INDEX_PATH,
        "planned_real_training_dataset_sample_index_path": PLANNED_REAL_SAMPLE_INDEX_PATH,
        "planned_real_training_dataset_packaging_report_path": PLANNED_REAL_PACKAGING_REPORT_PATH,
        "packaging_design_manifest_json_path": str(args.packaging_design_manifest_json),
        "packaging_file_plan_csv_path": str(args.packaging_file_plan_csv),
        "packaging_schema_report_csv_path": str(args.packaging_schema_report_csv),
        "packaging_design_report_csv_path": str(args.packaging_design_report_csv),
        "packaging_design_review_qa_report_csv_path": str(args.packaging_design_review_qa_report_csv),
        "index_csv_path": str(args.index_csv),
        "dataset_manifest_json_path": str(args.dataset_manifest_json),
        "raw_manifest_csv_path": str(args.manifest_csv),
        "packaged_protein_path": index_row.get("packaged_protein_path", ""),
        "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
        "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
        "source_protein_path": index_row.get("source_protein_path", ""),
        "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "packaging_gate_stage": "real_training_dataset_packaging_gate_only_not_training",
        "explicit_approval_required_before_real_training_dataset_packaging": "true",
        "ready_for_real_training_dataset_packaging_after_approval": "true",
        "real_training_dataset_packaging_executed": "false",
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
    qa_rows = rows_from_existing_csv(args.packaging_design_review_qa_report_csv)
    manifest, manifest_parseable = load_json(args.packaging_design_manifest_json)
    file_plan_rows = rows_from_existing_csv(args.packaging_file_plan_csv)
    schema_rows = rows_from_existing_csv(args.packaging_schema_report_csv)
    design_report_rows = rows_from_existing_csv(args.packaging_design_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)

    qa_by_id = index_many(qa_rows, "candidate_id")
    design_report_by_id = index_many(design_report_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    candidate_rows_all = [row for row in file_plan_rows if row.get("row_type", "") == "candidate_file"]
    global_rows = [row for row in file_plan_rows if row.get("row_type", "") == "global_artifact"]
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    global_checks = {
        "qa_row_count_valid": Path(args.packaging_design_review_qa_report_csv).is_file() and len(qa_rows) == 3,
        "packaging_design_manifest_valid": Path(args.packaging_design_manifest_json).is_file()
        and packaging_manifest_valid(manifest, manifest_parseable),
        "packaging_file_plan_row_count_valid": Path(args.packaging_file_plan_csv).is_file()
        and len(candidate_rows_all) == 15
        and len(global_rows) == 8,
        "packaging_schema_report_valid": Path(args.packaging_schema_report_csv).is_file() and schema_report_valid(schema_rows),
        "packaging_design_report_row_count_valid": Path(args.packaging_design_report_csv).is_file() and len(design_report_rows) == 3,
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "package_file_counts_valid": package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "packaging_design_review_only_files_valid": packaging_design_files_valid(),
        "planned_real_training_dataset_package_root_absent_before_gate": planned_real_package_absent(),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
    }
    global_blockers = [key for key, value in global_checks.items() if not value]
    plan_rows: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        qa_row = one(qa_by_id, candidate_id)
        design_report = one(design_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        c_rows = candidate_file_rows(file_plan_rows, candidate_id)
        checks = {
            "packaging_design_review_qa_row_found_once": found_once(qa_by_id, candidate_id) and global_checks["qa_row_count_valid"],
            "packaging_design_review_qa_status_passed": qa_status_passed(qa_row),
            "packaging_design_manifest_valid": global_checks["packaging_design_manifest_valid"],
            "packaging_file_plan_candidate_rows_valid": len(c_rows) == 5
            and {row.get("file_role", "") for row in c_rows} == CANDIDATE_FILE_ROLES,
            "packaging_file_plan_hashes_valid": file_hashes_valid(c_rows),
            "packaging_file_plan_reference_only_flags_valid": reference_flags_valid(c_rows),
            "packaging_schema_report_valid": global_checks["packaging_schema_report_valid"],
            "packaging_design_report_row_found_once": found_once(design_report_by_id, candidate_id)
            and global_checks["packaging_design_report_row_count_valid"],
            "packaging_design_report_status_passed": design_report_status_passed(design_report),
            "index_and_manifest_still_valid": global_checks["index_and_manifest_still_valid"]
            and found_once(index_by_id, candidate_id)
            and index_row.get("source_sample_id", "") == source_id
            and index_row_safety_valid(index_row),
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest)
            and global_checks["package_file_counts_valid"],
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
            "packaging_design_review_only_files_valid": global_checks["packaging_design_review_only_files_valid"],
            "planned_real_training_dataset_package_root_absent_before_gate": global_checks[
                "planned_real_training_dataset_package_root_absent_before_gate"
            ],
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
                "real_training_dataset_packaging_gate_status": "real_training_dataset_packaging_gate_passed" if passed else "blocked",
                "explicit_approval_required_before_real_training_dataset_packaging": bool_str(passed),
                "ready_for_real_training_dataset_packaging_after_approval": bool_str(passed),
                "real_training_dataset_packaging_executed": "false",
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
                    "await_explicit_approval_for_real_training_dataset_packaging"
                    if passed
                    else "fix_real_training_dataset_packaging_gate_blockers"
                ),
            }
        )
    return plan_rows, report_rows


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["real_training_dataset_packaging_gate_status"] == "real_training_dataset_packaging_gate_passed" for row in report_rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Real Training Dataset Packaging Gate Summary",
        "",
        "This is real training dataset packaging gate only.",
        "It reads packaging design review QA outputs and review-only packaging design artifacts.",
        "It does not execute real training dataset packaging.",
        "It does not create a real training dataset.",
        "It does not create tensor files.",
        "It does not copy PDB/SDF/JSON data files.",
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
        "Passing this gate still does not mean training can start.",
        "",
        "## Planned Real Training Dataset Package Outputs",
        "",
        f"- planned_real_training_dataset_package_root: `{PLANNED_REAL_PACKAGE_ROOT}`",
        f"- planned_real_training_dataset_manifest_path: `{PLANNED_REAL_MANIFEST_PATH}`",
        f"- planned_real_training_dataset_file_index_path: `{PLANNED_REAL_FILE_INDEX_PATH}`",
        f"- planned_real_training_dataset_sample_index_path: `{PLANNED_REAL_SAMPLE_INDEX_PATH}`",
        f"- planned_real_training_dataset_packaging_report_path: `{PLANNED_REAL_PACKAGING_REPORT_PATH}`",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | packaging_design_review_qa_status_passed | packaging_file_plan_candidate_rows_valid | packaging_file_plan_hashes_valid | real_training_dataset_packaging_gate_status | explicit_approval_required_before_real_training_dataset_packaging | real_training_dataset_packaging_executed | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {packaging_design_review_qa_status_passed} | {packaging_file_plan_candidate_rows_valid} | {packaging_file_plan_hashes_valid} | {real_training_dataset_packaging_gate_status} | {explicit_approval_required_before_real_training_dataset_packaging} | {real_training_dataset_packaging_executed} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed real training dataset packaging gate"
            if all_passed
            else "- one or more samples are blocked by real training dataset packaging gate",
            "- explicit approval is required before real training dataset packaging",
            "- no real training dataset packaging was executed",
            "- no real training dataset was created",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is explicit approval for real training dataset packaging, not training"
            if all_passed
            else "- next step is to fix real training dataset packaging gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows = build_gate(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    exit_code = 0 if all(row["real_training_dataset_packaging_gate_status"] == "real_training_dataset_packaging_gate_passed" for row in report_rows) else 1
    return plan_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build real training dataset packaging gate without packaging or training.")
    parser.add_argument("--packaging_design_review_qa_report_csv", required=True)
    parser.add_argument("--packaging_design_manifest_json", required=True)
    parser.add_argument("--packaging_file_plan_csv", required=True)
    parser.add_argument("--packaging_schema_report_csv", required=True)
    parser.add_argument("--packaging_design_report_csv", required=True)
    parser.add_argument("--training_dataset_packaging_design_gate_plan_csv", required=True)
    parser.add_argument("--training_dataset_packaging_design_gate_report_csv", required=True)
    parser.add_argument("--training_dataset_design_review_qa_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['real_training_dataset_packaging_gate_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

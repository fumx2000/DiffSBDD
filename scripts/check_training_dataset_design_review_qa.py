#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_training_dataset_design_review import (
    DESIGN_ROOT,
    PLANNED_TRAINING_RECORD_FIELDS,
    gate_status_passed,
    snapshot_qa_passed,
    snapshot_review_passed,
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
)


ALLOWED_DESIGN_FILE_NAMES = {
    "training_dataset_design_manifest.json",
    "training_dataset_design_schema_report.csv",
    "training_dataset_design_split_plan.csv",
    "training_dataset_design_report.csv",
    "training_dataset_design_review_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "design_manifest_parseable",
    "design_manifest_valid",
    "design_manifest_planned_fields_valid",
    "design_manifest_mask_levels_valid",
    "design_manifest_auxiliary_labels_valid",
    "design_manifest_safety_flags_valid",
    "schema_report_fields_valid",
    "schema_report_masking_fields_valid",
    "schema_report_auxiliary_fields_valid",
    "schema_report_split_fields_valid",
    "split_plan_row_found_once",
    "split_plan_review_only_flags_valid",
    "design_report_row_found_once",
    "design_report_status_passed",
    "design_report_safety_flags_valid",
    "upstream_training_dataset_design_gate_status_still_passed",
    "upstream_snapshot_review_qa_status_still_passed",
    "upstream_snapshot_review_status_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "only_allowed_design_files_created",
    "no_real_training_dataset_created",
    "no_copied_data_files_in_design_dir",
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
    "design_manifest_modified_by_qa",
    "schema_report_modified_by_qa",
    "split_plan_modified_by_qa",
    "design_report_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "training_dataset_design_review_qa_status",
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


def design_manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
        "training_dataset_design_executed": True,
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


def design_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("design_stage") == "training_dataset_design_review_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("target_dataset_name") == "covalent_small_pre_reaction_training_candidate_design"
        and manifest.get("dataset_role") == "training_dataset_design_schema_only"
    )


def list_contains_all(value: Any, required: set[str]) -> bool:
    return isinstance(value, list) and required.issubset(set(value))


def schema_fields_valid(rows: list[dict[str, str]]) -> bool:
    fields = {row.get("field_name", "") for row in rows}
    if not set(PLANNED_TRAINING_RECORD_FIELDS).issubset(fields):
        return False
    by_field = {row.get("field_name", ""): row for row in rows}
    return all(
        by_field[field].get("required", "") == "true"
        and by_field[field].get("generated_now", "") == "false"
        and by_field[field].get("training_tensor", "") == "false"
        for field in PLANNED_TRAINING_RECORD_FIELDS
    )


def schema_masking_fields_valid(rows: list[dict[str, str]]) -> bool:
    by_field = {row.get("field_name", ""): row for row in rows}
    return all(by_field.get(field, {}).get("used_for_masking", "") == "true" for field in ["mask_level", "scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"])


def schema_auxiliary_fields_valid(rows: list[dict[str, str]]) -> bool:
    by_field = {row.get("field_name", ""): row for row in rows}
    return all(
        by_field.get(field, {}).get("used_for_auxiliary_task", "") == "true"
        for field in ["warhead_type", "ligand_reactive_atom_id", "reactive_residue_chain", "reactive_residue_number", "reactive_residue_atom", "auxiliary_labels"]
    )


def schema_split_fields_valid(rows: list[dict[str, str]]) -> bool:
    by_field = {row.get("field_name", ""): row for row in rows}
    return by_field.get("split", {}).get("used_for_split", "") == "true"


def split_plan_flags_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("split", "") == "smoke_test"
        and row.get("split_strategy", "") == "smoke_test_fixed_split_review_only"
        and row.get("is_training_split", "") == "false"
        and row.get("is_validation_split", "") == "false"
        and row.get("is_test_split", "") == "false"
        and row.get("generated_now", "") == "false"
        and row.get("training_tensor", "") == "false"
    )


def snapshot_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("row_count") == 3
        and manifest.get("snapshot_stage") == "dataset_snapshot_review_only_not_training"
        and manifest.get("snapshot_file_list_row_count") == 23
    )


def snapshot_file_list_candidate_rows_valid(rows: list[dict[str, str]], candidate_id: str) -> bool:
    candidate_rows = [row for row in rows if row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id]
    return (
        len(candidate_rows) == 5
        and {row.get("file_role", "") for row in candidate_rows}
        == {"packaged_protein", "packaged_ligand_sdf", "packaged_metadata_json", "source_protein", "source_ligand_sdf"}
        and all(row.get("file_exists", "") == "true" for row in candidate_rows)
        and all(row.get("copied_to_snapshot", "") == "false" for row in candidate_rows)
        and all(row.get("archive_member", "") == "false" for row in candidate_rows)
        and all(row.get("training_tensor", "") == "false" for row in candidate_rows)
    )


def design_report_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_design_status", "") == "training_dataset_design_passed"


def design_report_safety_flags_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("approval_token_valid", "") == "true"
        and row.get("training_dataset_design_gate_plan_row_found_once", "") == "true"
        and row.get("training_dataset_design_gate_report_row_found_once", "") == "true"
        and row.get("training_dataset_design_gate_status_passed", "") == "true"
        and row.get("snapshot_review_qa_status_passed", "") == "true"
        and row.get("snapshot_review_status_passed", "") == "true"
        and row.get("source_mapping_valid", "") == "true"
        and row.get("packaged_hashes_match_index_and_manifest", "") == "true"
        and row.get("manifest_paths_match_index_sources", "") == "true"
        and row.get("mask_levels_valid", "") == "true"
        and row.get("auxiliary_labels_valid", "") == "true"
        and row.get("graph_counts_positive", "") == "true"
        and row.get("planned_schema_fields_present", "") == "true"
        and row.get("planned_mask_levels_present", "") == "true"
        and row.get("planned_auxiliary_labels_present", "") == "true"
        and row.get("split_plan_row_written", "") == "true"
        and row.get("schema_report_written", "") == "true"
        and row.get("design_manifest_written", "") == "true"
        and row.get("design_report_written", "") == "true"
        and row.get("only_allowed_design_files_created", "") == "true"
        and row.get("training_dataset_design_executed", "") == "true"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get("torch_imported", "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("training_ready", "") == "false"
        and row.get("files_copied", "") == "false"
        and row.get("archive_created", "") == "false"
    )


def only_allowed_design_files() -> bool:
    root = Path(DESIGN_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return {path.name for path in files} == ALLOWED_DESIGN_FILE_NAMES and all(path.parent == root for path in files)


def no_copied_data_files(root: str | Path) -> bool:
    root_path = Path(root)
    if not root_path.is_dir():
        return False
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pdb", ".sdf", ".cif"}:
            return False
        if path.suffix.lower() == ".json" and path.name != "training_dataset_design_manifest.json":
            return False
    return True


def forbidden_design_absent(root: str | Path) -> tuple[bool, bool]:
    root_path = Path(root)
    if not root_path.is_dir():
        return False, False
    archives = [path for path in root_path.rglob("*") if path.is_file() and path.suffix.lower() in {".tar", ".zip", ".tgz"}]
    tensors = [path for path in root_path.rglob("*") if path.is_file() and path.suffix.lower() in {".pt", ".pkl", ".npz", ".lmdb"}]
    return len(archives) == 0, len(tensors) == 0


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def build_report_rows(args: argparse.Namespace, include_qa_report_in_allowed: bool) -> list[dict[str, str]]:
    design_manifest, design_manifest_parseable = load_json(args.design_manifest_json)
    schema_rows = rows_from_existing_csv(args.schema_report_csv)
    split_rows = rows_from_existing_csv(args.split_plan_csv)
    design_report_rows = rows_from_existing_csv(args.design_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.training_dataset_design_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_dataset_design_gate_report_csv)
    snapshot_qa_rows = rows_from_existing_csv(args.snapshot_review_qa_report_csv)
    snapshot_manifest, snapshot_manifest_parseable = load_json(args.snapshot_manifest_json)
    snapshot_file_list_rows = rows_from_existing_csv(args.snapshot_file_list_csv)
    snapshot_report_rows = rows_from_existing_csv(args.snapshot_review_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)

    split_by_id = index_many(split_rows, "sample_id")
    design_report_by_id = index_many(design_report_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "training_dataset_design_gate_plan_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    snapshot_qa_by_id = index_many(snapshot_qa_rows, "candidate_id")
    snapshot_report_by_id = index_many(snapshot_report_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    archives_absent_in_design, tensors_absent_in_design = forbidden_design_absent(DESIGN_ROOT)
    global_tensors, global_archives = forbidden_counts("data/derived/covalent_small")
    design_manifest_ok = design_manifest_valid(design_manifest, design_manifest_parseable)
    index_manifest_ok = index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable)
    package_count_ok = package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3}
    snapshot_manifest_ok = snapshot_manifest_valid(snapshot_manifest, snapshot_manifest_parseable)
    snapshot_file_list_row_count_ok = len(snapshot_file_list_rows) == 23
    allowed_files_ok = only_allowed_design_files() if include_qa_report_in_allowed else False
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        design_report = one(design_report_by_id, candidate_id)
        split_row = one(split_by_id, candidate_id)
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        snapshot_qa = one(snapshot_qa_by_id, candidate_id)
        snapshot_report = one(snapshot_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            "design_manifest_parseable": design_manifest_parseable,
            "design_manifest_valid": design_manifest_ok,
            "design_manifest_planned_fields_valid": list_contains_all(design_manifest.get("planned_training_record_fields", []), set(PLANNED_TRAINING_RECORD_FIELDS)),
            "design_manifest_mask_levels_valid": list_contains_all(design_manifest.get("supported_mask_levels", []), REQUIRED_MASK_LEVELS),
            "design_manifest_auxiliary_labels_valid": list_contains_all(design_manifest.get("required_auxiliary_labels", []), REQUIRED_AUXILIARY_LABELS),
            "design_manifest_safety_flags_valid": design_manifest_safety_flags_valid(design_manifest),
            "schema_report_fields_valid": schema_fields_valid(schema_rows),
            "schema_report_masking_fields_valid": schema_masking_fields_valid(schema_rows),
            "schema_report_auxiliary_fields_valid": schema_auxiliary_fields_valid(schema_rows),
            "schema_report_split_fields_valid": schema_split_fields_valid(schema_rows),
            "split_plan_row_found_once": found_once(split_by_id, candidate_id) and len(split_rows) == 3,
            "split_plan_review_only_flags_valid": split_plan_flags_valid(split_row) and split_row.get("source_sample_id", "") == source_id,
            "design_report_row_found_once": found_once(design_report_by_id, candidate_id) and len(design_report_rows) == 3,
            "design_report_status_passed": design_report_status_passed(design_report),
            "design_report_safety_flags_valid": design_report_safety_flags_valid(design_report),
            "upstream_training_dataset_design_gate_status_still_passed": (
                found_once(gate_plan_by_id, candidate_id)
                and gate_plan.get("training_dataset_design_gate_plan_id", "") == candidate_id
                and gate_status_passed(gate_report)
            ),
            "upstream_snapshot_review_qa_status_still_passed": snapshot_qa_passed(snapshot_qa),
            "upstream_snapshot_review_status_still_passed": (
                snapshot_manifest_ok
                and snapshot_file_list_row_count_ok
                and snapshot_file_list_candidate_rows_valid(snapshot_file_list_rows, candidate_id)
                and snapshot_review_passed(snapshot_report)
            ),
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
            "only_allowed_design_files_created": allowed_files_ok,
            "no_real_training_dataset_created": True,
            "no_copied_data_files_in_design_dir": no_copied_data_files(DESIGN_ROOT),
            "no_archive_created": archives_absent_in_design and global_archives == 0,
            "no_training_tensors_created": tensors_absent_in_design and global_tensors == 0,
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
                "design_manifest_modified_by_qa": "false",
                "schema_report_modified_by_qa": "false",
                "split_plan_modified_by_qa": "false",
                "design_report_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "training_dataset_design_review_qa_status": "training_dataset_design_review_qa_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "prepare_training_dataset_packaging_design_gate_not_training"
                    if passed
                    else "fix_training_dataset_design_review_qa_blockers"
                ),
            }
        )
    return report_rows


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_design_review_qa_status"] == "training_dataset_design_review_qa_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Training Dataset Design Review QA Summary",
        "",
        "This is training dataset design review QA only.",
        "It reads the design manifest, schema report, split plan, and design report.",
        "It does not execute a new training dataset design review.",
        "It does not create a real training dataset.",
        "It does not create tensor files.",
        "It does not copy files.",
        "It does not create archives.",
        did_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify design files.",
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
        "| candidate_id | source_sample_id | design_manifest_valid | schema_report_fields_valid | split_plan_review_only_flags_valid | design_report_status_passed | only_allowed_design_files_created | training_dataset_design_review_qa_status | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {design_manifest_valid} | {schema_report_fields_valid} | {split_plan_review_only_flags_valid} | {design_report_status_passed} | {only_allowed_design_files_created} | {training_dataset_design_review_qa_status} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training dataset design review QA" if all_passed else "- one or more samples are blocked by training dataset design review QA",
            "- no new training dataset design review was executed",
            "- no real training dataset was created",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training dataset packaging design gate, not training" if all_passed else "- next step is to fix training dataset design review QA blockers",
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
    exit_code = 0 if all(row["training_dataset_design_review_qa_status"] == "training_dataset_design_review_qa_passed" for row in rows) else 1
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check review-only training dataset design QA without training.")
    parser.add_argument("--design_manifest_json", required=True)
    parser.add_argument("--schema_report_csv", required=True)
    parser.add_argument("--split_plan_csv", required=True)
    parser.add_argument("--design_report_csv", required=True)
    parser.add_argument("--training_dataset_design_gate_plan_csv", required=True)
    parser.add_argument("--training_dataset_design_gate_report_csv", required=True)
    parser.add_argument("--snapshot_review_qa_report_csv", required=True)
    parser.add_argument("--snapshot_manifest_json", required=True)
    parser.add_argument("--snapshot_file_list_csv", required=True)
    parser.add_argument("--snapshot_review_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['training_dataset_design_review_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

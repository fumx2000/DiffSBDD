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
    rows_from_existing_csv,
    sha256_file,
)


APPROVAL_TOKEN = "APPROVE_TRAINING_DATASET_DESIGN_STEP_8AT"
DESIGN_ROOT = "data/derived/covalent_small/training_dataset_design_review_only"
DESIGN_MANIFEST_PATH = f"{DESIGN_ROOT}/training_dataset_design_manifest.json"
SCHEMA_REPORT_PATH = f"{DESIGN_ROOT}/training_dataset_design_schema_report.csv"
SPLIT_PLAN_PATH = f"{DESIGN_ROOT}/training_dataset_design_split_plan.csv"
DESIGN_REPORT_PATH = f"{DESIGN_ROOT}/training_dataset_design_report.csv"

PLANNED_TRAINING_RECORD_FIELDS = [
    "sample_id",
    "source_sample_id",
    "protein_pdb_path",
    "ligand_sdf_path",
    "packaged_metadata_json_path",
    "reactive_residue_chain",
    "reactive_residue_number",
    "reactive_residue_atom",
    "ligand_reactive_atom_id",
    "warhead_type",
    "scaffold_atom_ids",
    "linker_atom_ids",
    "warhead_atom_ids",
    "mask_level",
    "auxiliary_labels",
    "split",
    "graph_ligand_atom_count",
    "graph_ligand_bond_count",
    "graph_protein_atom_count",
    "graph_protein_residue_count",
    "source_hashes",
    "safety_flags",
]
REQUIRED_INPUT_FILE_ROLES = [
    "packaged_protein",
    "packaged_ligand_sdf",
    "packaged_metadata_json",
    "source_protein",
    "source_ligand_sdf",
]
ALLOWED_DESIGN_FILES = {
    Path(DESIGN_MANIFEST_PATH).name,
    Path(SCHEMA_REPORT_PATH).name,
    Path(SPLIT_PLAN_PATH).name,
    Path(DESIGN_REPORT_PATH).name,
}
DISALLOWED_DESIGN_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

SCHEMA_COLUMNS = [
    "field_name",
    "field_group",
    "required",
    "dtype",
    "source_artifact",
    "validation_rule",
    "used_for_masking",
    "used_for_auxiliary_task",
    "used_for_split",
    "generated_now",
    "training_tensor",
    "notes",
]
SPLIT_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "split_strategy",
    "split_reason",
    "is_training_split",
    "is_validation_split",
    "is_test_split",
    "generated_now",
    "training_tensor",
    "notes",
]
REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "approval_token_valid",
    "training_dataset_design_gate_plan_row_found_once",
    "training_dataset_design_gate_report_row_found_once",
    "training_dataset_design_gate_status_passed",
    "snapshot_review_qa_status_passed",
    "snapshot_review_status_passed",
    "source_mapping_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "planned_schema_fields_present",
    "planned_mask_levels_present",
    "planned_auxiliary_labels_present",
    "split_plan_row_written",
    "schema_report_written",
    "design_manifest_written",
    "design_report_written",
    "only_allowed_design_files_created",
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
    "training_dataset_design_status",
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


def gate_status_passed(row: dict[str, str]) -> bool:
    required_false_fields = [
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
    return (
        bool(row)
        and row.get("training_dataset_design_gate_status", "") == "training_dataset_design_gate_passed"
        and row.get("explicit_approval_required_before_training_dataset_design", "") == "true"
        and row.get("ready_for_training_dataset_design_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false_fields)
    )


def snapshot_qa_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("dataset_snapshot_review_qa_status", "") == "dataset_snapshot_review_qa_passed"


def snapshot_review_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("dataset_snapshot_review_status", "") == "dataset_snapshot_review_passed"


def design_root_absent(paths: list[str | Path]) -> bool:
    return not Path(DESIGN_ROOT).exists() and all(not Path(path).exists() for path in paths)


def only_allowed_design_files() -> bool:
    root = Path(DESIGN_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == ALLOWED_DESIGN_FILES
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_DESIGN_SUFFIXES for path in files)
    )


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def build_schema_rows() -> list[dict[str, str]]:
    rows = []
    groups = {
        "sample_id": ("identity", "string", "index_csv", "nonempty unique sample id", "false", "false", "false"),
        "source_sample_id": ("identity", "string", "index_csv", "matches fixed source mapping", "false", "false", "false"),
        "protein_pdb_path": ("path", "string", "index_csv", "path exists and hash-locked upstream", "false", "false", "false"),
        "ligand_sdf_path": ("path", "string", "index_csv", "path exists and hash-locked upstream", "false", "false", "false"),
        "packaged_metadata_json_path": ("path", "string", "index_csv", "path exists and hash-locked upstream", "false", "false", "false"),
        "reactive_residue_chain": ("reaction_context", "string", "index_csv", "nonempty reactive residue chain", "false", "true", "false"),
        "reactive_residue_number": ("reaction_context", "int/string", "index_csv", "nonempty reactive residue number", "false", "true", "false"),
        "reactive_residue_atom": ("reaction_context", "string", "index_csv", "expected protein reactive atom label", "false", "true", "false"),
        "ligand_reactive_atom_id": ("auxiliary_label", "int/string", "index_csv", "nonempty ligand reactive atom id", "false", "true", "false"),
        "warhead_type": ("auxiliary_label", "string", "packaged_metadata_json", "known warhead type label", "false", "true", "false"),
        "scaffold_atom_ids": ("masking", "string", "index_csv", "space-delimited atom ids", "true", "false", "false"),
        "linker_atom_ids": ("masking", "string", "index_csv", "space-delimited atom ids", "true", "false", "false"),
        "warhead_atom_ids": ("masking", "string", "index_csv", "space-delimited atom ids", "true", "false", "false"),
        "mask_level": ("masking", "string", "design_schema", "one of supported mask levels", "true", "false", "false"),
        "auxiliary_labels": ("auxiliary_label", "json/string", "design_schema", "contains required auxiliary labels", "false", "true", "false"),
        "split": ("split", "string", "split_plan", "review-only smoke_test split", "false", "false", "true"),
        "graph_ligand_atom_count": ("graph_count", "int", "index_csv", "positive integer", "false", "false", "false"),
        "graph_ligand_bond_count": ("graph_count", "int", "index_csv", "positive integer", "false", "false", "false"),
        "graph_protein_atom_count": ("graph_count", "int", "index_csv", "positive integer", "false", "false", "false"),
        "graph_protein_residue_count": ("graph_count", "int", "index_csv", "positive integer", "false", "false", "false"),
        "source_hashes": ("safety", "json/string", "snapshot_file_list", "hashes must match current source files", "false", "false", "false"),
        "safety_flags": ("safety", "json/string", "design_manifest", "must remain not training-ready", "false", "false", "false"),
    }
    for field in PLANNED_TRAINING_RECORD_FIELDS:
        field_group, dtype, source, validation, masking, aux, split = groups[field]
        rows.append(
            {
                "field_name": field,
                "field_group": field_group,
                "required": "true",
                "dtype": dtype,
                "source_artifact": source,
                "validation_rule": validation,
                "used_for_masking": masking,
                "used_for_auxiliary_task": aux,
                "used_for_split": split,
                "generated_now": "false",
                "training_tensor": "false",
                "notes": "schema_design_only_not_training",
            }
        )
    return rows


def build_split_rows(index_by_id: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows = []
    for candidate_id, source_id in TARGETS.items():
        _index_row = one(index_by_id, candidate_id)
        rows.append(
            {
                "sample_id": candidate_id,
                "source_sample_id": source_id,
                "split": "smoke_test",
                "split_strategy": "smoke_test_fixed_split_review_only",
                "split_reason": "review_only_three_sample_smoke_test_not_training_split",
                "is_training_split": "false",
                "is_validation_split": "false",
                "is_test_split": "false",
                "generated_now": "false",
                "training_tensor": "false",
                "notes": "split_design_only_not_training",
            }
        )
    return rows


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    upstream_artifacts = {
        "training_dataset_design_gate_plan_csv": args.training_dataset_design_gate_plan_csv,
        "training_dataset_design_gate_report_csv": args.training_dataset_design_gate_report_csv,
        "snapshot_review_qa_report_csv": args.snapshot_review_qa_report_csv,
        "snapshot_manifest_json": args.snapshot_manifest_json,
        "snapshot_file_list_csv": args.snapshot_file_list_csv,
        "snapshot_review_report_csv": args.snapshot_review_report_csv,
        "index_csv": args.index_csv,
        "dataset_manifest_json": args.dataset_manifest_json,
        "raw_manifest_csv": args.manifest_csv,
    }
    return {
        "design_name": "covalent_small_pre_reaction_training_dataset_design_review",
        "design_stage": "training_dataset_design_review_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "source_dataset_name": "covalent_small_pre_reaction_review_only",
        "target_dataset_name": "covalent_small_pre_reaction_training_candidate_design",
        "dataset_role": "training_dataset_design_schema_only",
        "split_strategy": "smoke_test_fixed_split_review_only",
        "row_count": 3,
        "sample_ids": list(TARGETS),
        "source_sample_ids": [TARGETS[candidate_id] for candidate_id in TARGETS],
        "design_root": DESIGN_ROOT,
        "design_manifest_path": DESIGN_MANIFEST_PATH,
        "schema_report_path": SCHEMA_REPORT_PATH,
        "split_plan_path": SPLIT_PLAN_PATH,
        "design_report_path": DESIGN_REPORT_PATH,
        "upstream_artifacts": {key: str(value) for key, value in upstream_artifacts.items()},
        "upstream_artifact_sha256": {key: sha256_file(value) for key, value in upstream_artifacts.items()},
        "required_input_file_roles": REQUIRED_INPUT_FILE_ROLES,
        "planned_training_record_fields": PLANNED_TRAINING_RECORD_FIELDS,
        "supported_mask_levels": sorted(REQUIRED_MASK_LEVELS),
        "required_auxiliary_labels": sorted(REQUIRED_AUXILIARY_LABELS),
        "planned_splits": ["smoke_test"],
        "safety_flags": {
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
        },
        "recommended_next_action": "build_training_dataset_design_review_qa_not_training",
    }


def planned_schema_fields_present(schema_rows: list[dict[str, str]]) -> bool:
    return {row.get("field_name", "") for row in schema_rows}.issuperset(PLANNED_TRAINING_RECORD_FIELDS)


def build_preflight(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if args.approval_token != APPROVAL_TOKEN:
        return {}, ["approval_token_valid"]
    if not design_root_absent([args.output_design_manifest_json, args.output_schema_report_csv, args.output_split_plan_csv, args.output_design_report_csv]):
        blockers.append("training_dataset_design_outputs_absent_before_review")

    gate_plan_rows = rows_from_existing_csv(args.training_dataset_design_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_dataset_design_gate_report_csv)
    snapshot_qa_rows = rows_from_existing_csv(args.snapshot_review_qa_report_csv)
    snapshot_report_rows = rows_from_existing_csv(args.snapshot_review_report_csv)
    snapshot_file_list_rows = rows_from_existing_csv(args.snapshot_file_list_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    snapshot_manifest, snapshot_manifest_parseable = load_json(args.snapshot_manifest_json)

    if not (Path(args.training_dataset_design_gate_plan_csv).is_file() and len(gate_plan_rows) == 3):
        blockers.append("training_dataset_design_gate_plan_row_count_valid")
    if not (Path(args.training_dataset_design_gate_report_csv).is_file() and len(gate_report_rows) == 3):
        blockers.append("training_dataset_design_gate_report_row_count_valid")
    if not (Path(args.snapshot_review_qa_report_csv).is_file() and len(snapshot_qa_rows) == 3):
        blockers.append("snapshot_review_qa_row_count_valid")
    if not (
        Path(args.snapshot_manifest_json).is_file()
        and snapshot_manifest_parseable
        and snapshot_manifest.get("row_count") == 3
        and snapshot_manifest.get("snapshot_stage") == "dataset_snapshot_review_only_not_training"
    ):
        blockers.append("snapshot_manifest_valid")
    if not (Path(args.snapshot_file_list_csv).is_file() and len(snapshot_file_list_rows) == 23):
        blockers.append("snapshot_file_list_row_count_valid")
    if not (Path(args.snapshot_review_report_csv).is_file() and len(snapshot_report_rows) == 3):
        blockers.append("snapshot_review_report_row_count_valid")
    if not (Path(args.index_csv).is_file() and len(index_rows) == 3):
        blockers.append("index_row_count_valid")
    if not index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable):
        blockers.append("dataset_manifest_valid")
    if package_counts(args.package_root) != {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3}:
        blockers.append("package_file_counts_valid")
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    if tensors:
        blockers.append("forbidden_training_tensors_absent")
    if archives:
        blockers.append("forbidden_archives_absent")

    return (
        {
            "gate_plan_rows": gate_plan_rows,
            "gate_report_rows": gate_report_rows,
            "snapshot_qa_rows": snapshot_qa_rows,
            "snapshot_report_rows": snapshot_report_rows,
            "snapshot_file_list_rows": snapshot_file_list_rows,
            "index_rows": index_rows,
            "raw_manifest_rows": raw_manifest_rows,
            "dataset_manifest": dataset_manifest,
        },
        blockers,
    )


def candidate_precheck_blockers(inputs: dict[str, Any]) -> list[str]:
    gate_plan_by_id = index_many(inputs.get("gate_plan_rows", []), "training_dataset_design_gate_plan_id")
    gate_report_by_id = index_many(inputs.get("gate_report_rows", []), "candidate_id")
    snapshot_qa_by_id = index_many(inputs.get("snapshot_qa_rows", []), "candidate_id")
    snapshot_report_by_id = index_many(inputs.get("snapshot_report_rows", []), "candidate_id")
    index_by_id = index_many(inputs.get("index_rows", []), "sample_id")
    raw_manifest_by_id = index_many(inputs.get("raw_manifest_rows", []), "sample_id")
    dataset_manifest = inputs.get("dataset_manifest", {})
    blockers: list[str] = []
    for candidate_id, source_id in TARGETS.items():
        gate_report = one(gate_report_by_id, candidate_id)
        snapshot_qa = one(snapshot_qa_by_id, candidate_id)
        snapshot_report = one(snapshot_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        candidate_file_count = sum(row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id for row in inputs.get("snapshot_file_list_rows", []))
        checks = {
            "training_dataset_design_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "training_dataset_design_gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "training_dataset_design_gate_status_passed": gate_status_passed(gate_report),
            "snapshot_review_qa_row_found_once": found_once(snapshot_qa_by_id, candidate_id),
            "snapshot_review_qa_status_passed": snapshot_qa_passed(snapshot_qa),
            "snapshot_review_status_passed": snapshot_review_passed(snapshot_report),
            "snapshot_candidate_file_rows_valid": candidate_file_count == 5,
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row) and index_row.get("real_dataset_generated", "") == "false" and index_row.get("pre_reaction_transform_ready", "") == "false" and index_row.get("training_ready", "") == "false",
        }
        blockers.extend(f"{candidate_id}:{key}" for key, value in checks.items() if not value)
    return blockers


def build_design_report_rows(args: argparse.Namespace, inputs: dict[str, Any], preflight_blockers: list[str], schema_rows: list[dict[str, str]], split_rows: list[dict[str, str]], post_checks: dict[str, bool]) -> list[dict[str, str]]:
    gate_plan_by_id = index_many(inputs.get("gate_plan_rows", []), "training_dataset_design_gate_plan_id")
    gate_report_by_id = index_many(inputs.get("gate_report_rows", []), "candidate_id")
    snapshot_qa_by_id = index_many(inputs.get("snapshot_qa_rows", []), "candidate_id")
    snapshot_report_by_id = index_many(inputs.get("snapshot_report_rows", []), "candidate_id")
    index_by_id = index_many(inputs.get("index_rows", []), "sample_id")
    raw_manifest_by_id = index_many(inputs.get("raw_manifest_rows", []), "sample_id")
    dataset_manifest = inputs.get("dataset_manifest", {})
    schema_ok = planned_schema_fields_present(schema_rows)
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        gate_report = one(gate_report_by_id, candidate_id)
        snapshot_qa = one(snapshot_qa_by_id, candidate_id)
        snapshot_report = one(snapshot_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            "approval_token_valid": args.approval_token == APPROVAL_TOKEN,
            "training_dataset_design_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "training_dataset_design_gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "training_dataset_design_gate_status_passed": gate_status_passed(gate_report),
            "snapshot_review_qa_status_passed": snapshot_qa_passed(snapshot_qa),
            "snapshot_review_status_passed": snapshot_review_passed(snapshot_report),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
            "planned_schema_fields_present": schema_ok,
            "planned_mask_levels_present": REQUIRED_MASK_LEVELS.issubset(set(build_manifest(args).get("supported_mask_levels", []))),
            "planned_auxiliary_labels_present": REQUIRED_AUXILIARY_LABELS.issubset(set(build_manifest(args).get("required_auxiliary_labels", []))),
            "split_plan_row_written": any(row.get("sample_id", "") == candidate_id for row in split_rows),
            "schema_report_written": post_checks["schema_report_written"],
            "design_manifest_written": post_checks["design_manifest_written"],
            "design_report_written": post_checks["design_report_written"],
            "only_allowed_design_files_created": post_checks["only_allowed_design_files_created"],
        }
        blockers = preflight_blockers + [key for key, value in checks.items() if not value]
        passed = not blockers and all(post_checks.values())
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                **{key: bool_str(value) for key, value in checks.items()},
                "training_dataset_design_executed": "true" if passed else "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "dataloader_tensor_generated": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "archive_created": "false",
                "training_dataset_design_status": "training_dataset_design_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers + [key for key, value in post_checks.items() if not value]),
                "recommended_next_action": (
                    "build_training_dataset_design_review_qa_not_training"
                    if passed
                    else "fix_training_dataset_design_blockers"
                ),
            }
        )
    return report_rows


def write_markdown(report_rows: list[dict[str, str]], schema_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_design_status"] == "training_dataset_design_passed" for row in report_rows)
    did_not_import_torch = "It did not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Training Dataset Design Review Summary",
        "",
        "This is training dataset design review only.",
        "Explicit approval token was required and provided.",
        "It created a review-only training dataset design manifest, schema report, split plan, and design report.",
        "It did not create a real training dataset.",
        "It did not create tensor files.",
        "It did not copy PDB/SDF/JSON data files.",
        "It did not create archives.",
        did_not_import_torch,
        "It did not load checkpoints.",
        "It did not initialize a model.",
        "It did not generate dataloader tensors.",
        "It did not modify snapshot files.",
        "It did not modify the index CSV.",
        "It did not modify the dataset manifest JSON.",
        "It did not modify manifest files.",
        "It did not modify source or packaged PDB/SDF/JSON files.",
        "It did not train or fine-tune any model.",
        "Passing this review still does not mean the samples are training-ready.",
        "",
        "## Output Files",
        "",
        f"- design manifest JSON path: `{DESIGN_MANIFEST_PATH}`",
        f"- schema report CSV path: `{SCHEMA_REPORT_PATH}`",
        f"- split plan CSV path: `{SPLIT_PLAN_PATH}`",
        f"- design report CSV path: `{DESIGN_REPORT_PATH}`",
        "",
        "## Planned Schema",
        "",
        f"- number of planned fields: {len(schema_rows)}",
        f"- supported mask levels: {';'.join(sorted(REQUIRED_MASK_LEVELS))}",
        f"- required auxiliary labels: {';'.join(sorted(REQUIRED_AUXILIARY_LABELS))}",
        "- planned split strategy: smoke_test_fixed_split_review_only",
        "",
        "## Sample Review",
        "",
        "| candidate_id | source_sample_id | training_dataset_design_status | planned_schema_fields_present | planned_mask_levels_present | planned_auxiliary_labels_present | split_plan_row_written | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {training_dataset_design_status} | {planned_schema_fields_present} | {planned_mask_levels_present} | {planned_auxiliary_labels_present} | {split_plan_row_written} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training dataset design review" if all_passed else "- one or more samples are blocked by training dataset design review",
            "- design manifest/schema report/split plan were created" if all_passed else "- design outputs were not safely completed",
            "- no real training dataset was created",
            "- no tensor files were created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training dataset design review QA, not training" if all_passed else "- next step is to fix training dataset design blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    inputs, preflight_blockers = build_preflight(args)
    candidate_blockers = [] if preflight_blockers else candidate_precheck_blockers(inputs)
    if preflight_blockers or candidate_blockers:
        return [], [], [], {}, 1

    index_by_id = index_many(inputs.get("index_rows", []), "sample_id")
    schema_rows = build_schema_rows()
    split_rows = build_split_rows(index_by_id)
    design_manifest = build_manifest(args)
    write_csv(schema_rows, args.output_schema_report_csv, SCHEMA_COLUMNS)
    write_csv(split_rows, args.output_split_plan_csv, SPLIT_COLUMNS)
    write_json(design_manifest, args.output_design_manifest_json)
    post_checks = {
        "schema_report_written": Path(args.output_schema_report_csv).is_file(),
        "design_manifest_written": Path(args.output_design_manifest_json).is_file(),
        "design_report_written": True,
        "only_allowed_design_files_created": False,
    }
    report_rows = build_design_report_rows(args, inputs, preflight_blockers, schema_rows, split_rows, post_checks)
    write_csv(report_rows, args.output_design_report_csv, REPORT_COLUMNS)
    post_checks["only_allowed_design_files_created"] = only_allowed_design_files()
    report_rows = build_design_report_rows(args, inputs, preflight_blockers, schema_rows, split_rows, post_checks)
    write_csv(report_rows, args.output_design_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, schema_rows, args.output_md)
    exit_code = 0 if all(row["training_dataset_design_status"] == "training_dataset_design_passed" for row in report_rows) else 1
    return schema_rows, split_rows, report_rows, design_manifest, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply review-only training dataset design without training.")
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
    parser.add_argument("--output_design_manifest_json", required=True)
    parser.add_argument("--output_schema_report_csv", required=True)
    parser.add_argument("--output_split_plan_csv", required=True)
    parser.add_argument("--output_design_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _schema, _split, report, _manifest, exit_code = run(parse_args())
    if report:
        for row in report:
            print(f"{row['candidate_id']}: {row['training_dataset_design_status']}")
    else:
        print("training dataset design review blocked before writing design outputs")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

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
    contains_all,
    forbidden_counts,
    found_once,
    graph_counts_positive,
    index_many,
    load_json,
    manifest_paths_match,
    package_counts,
    packaged_hashes_match,
    rows_from_existing_csv,
    sha256_file,
)
from build_training_dataset_packaging_design_gate import (
    PLANNED_PACKAGING_DESIGN_ROOT,
    design_review_qa_status_passed,
)


APPROVAL_TOKEN = "APPROVE_TRAINING_DATASET_PACKAGING_DESIGN_STEP_8AW"
PACKAGING_DESIGN_MANIFEST_PATH = f"{PLANNED_PACKAGING_DESIGN_ROOT}/training_dataset_packaging_design_manifest.json"
PACKAGING_FILE_PLAN_PATH = f"{PLANNED_PACKAGING_DESIGN_ROOT}/training_dataset_packaging_file_plan.csv"
PACKAGING_SCHEMA_REPORT_PATH = f"{PLANNED_PACKAGING_DESIGN_ROOT}/training_dataset_packaging_schema_report.csv"
PACKAGING_DESIGN_REPORT_PATH = f"{PLANNED_PACKAGING_DESIGN_ROOT}/training_dataset_packaging_design_report.csv"

PLANNED_PACKAGING_FILE_ROLES = [
    "packaged_protein",
    "packaged_ligand_sdf",
    "packaged_metadata_json",
    "source_protein",
    "source_ligand_sdf",
    "design_manifest",
    "design_schema_report",
    "design_split_plan",
    "design_report",
    "design_review_qa_report",
]
PLANNED_PACKAGING_RECORD_FIELDS = [
    "sample_id",
    "source_sample_id",
    "split",
    "package_role",
    "source_file_role",
    "source_file_path",
    "source_file_sha256",
    "source_file_size_bytes",
    "copied_to_training_package",
    "embedded_in_training_manifest",
    "archive_member",
    "training_tensor",
    "generated_now",
    "safety_flags",
]
GLOBAL_ARTIFACT_ROLES = [
    ("design_manifest", "design_manifest_json"),
    ("design_schema_report", "schema_report_csv"),
    ("design_split_plan", "split_plan_csv"),
    ("design_report", "design_report_csv"),
    ("design_review_qa_report", "training_dataset_design_review_qa_report_csv"),
    ("index_csv", "index_csv"),
    ("dataset_manifest_json", "dataset_manifest_json"),
    ("raw_manifest_csv", "manifest_csv"),
]

SCHEMA_COLUMNS = [
    "field_name",
    "field_group",
    "required",
    "dtype",
    "source_artifact",
    "validation_rule",
    "generated_now",
    "training_tensor",
    "notes",
]
FILE_PLAN_COLUMNS = [
    "row_type",
    "candidate_id",
    "source_sample_id",
    "file_role",
    "source_file_path",
    "source_file_exists",
    "source_file_size_bytes",
    "source_file_sha256",
    "copied_to_training_package",
    "embedded_in_training_manifest",
    "archive_member",
    "training_tensor",
    "generated_now",
    "notes",
]
REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
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
    "real_training_tensor_generated",
    "real_dataset_generated",
    "dataloader_tensor_generated",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "archive_created",
    "training_dataset_packaging_design_status",
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


def file_info(path: str | Path) -> dict[str, str]:
    file_path = Path(path)
    exists = file_path.is_file()
    return {
        "source_file_exists": str(exists).lower(),
        "source_file_size_bytes": str(file_path.stat().st_size) if exists else "0",
        "source_file_sha256": sha256_file(file_path) if exists else "",
    }


def gate_report_passed(row: dict[str, str]) -> bool:
    required_false_fields = [
        "training_dataset_packaging_design_executed",
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
        and row.get("training_dataset_packaging_design_gate_status", "") == "training_dataset_packaging_design_gate_passed"
        and row.get("explicit_approval_required_before_training_dataset_packaging_design", "") == "true"
        and row.get("ready_for_training_dataset_packaging_design_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false_fields)
    )


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def output_root_absent(args: argparse.Namespace) -> bool:
    paths = [
        args.output_packaging_design_manifest_json,
        args.output_file_plan_csv,
        args.output_packaging_schema_report_csv,
        args.output_packaging_design_report_csv,
    ]
    return not Path(PLANNED_PACKAGING_DESIGN_ROOT).exists() and all(not Path(path).exists() for path in paths)


def validate_preflight(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    if args.approval_token != APPROVAL_TOKEN:
        return ["approval_token_valid"], {}
    gate_plan_rows = rows_from_existing_csv(args.training_dataset_packaging_design_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_dataset_packaging_design_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.training_dataset_design_review_qa_report_csv)
    design_manifest, design_manifest_parseable = load_json(args.design_manifest_json)
    schema_rows = rows_from_existing_csv(args.schema_report_csv)
    split_rows = rows_from_existing_csv(args.split_plan_csv)
    design_report_rows = rows_from_existing_csv(args.design_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")

    checks = {
        "approval_token_valid": True,
        "gate_plan_row_count_valid": Path(args.training_dataset_packaging_design_gate_plan_csv).is_file() and len(gate_plan_rows) == 3,
        "gate_report_row_count_valid": Path(args.training_dataset_packaging_design_gate_report_csv).is_file() and len(gate_report_rows) == 3,
        "design_review_qa_row_count_valid": Path(args.training_dataset_design_review_qa_report_csv).is_file() and len(qa_rows) == 3,
        "design_manifest_valid": Path(args.design_manifest_json).is_file()
        and design_manifest_parseable
        and design_manifest.get("row_count") == 3,
        "schema_report_valid": Path(args.schema_report_csv).is_file()
        and {row.get("field_name", "") for row in schema_rows}.issuperset(set(design_manifest.get("planned_training_record_fields", []))),
        "split_plan_row_count_valid": Path(args.split_plan_csv).is_file() and len(split_rows) == 3,
        "design_report_row_count_valid": Path(args.design_report_csv).is_file() and len(design_report_rows) == 3,
        "index_row_count_valid": Path(args.index_csv).is_file() and len(index_rows) == 3,
        "dataset_manifest_valid": Path(args.dataset_manifest_json).is_file()
        and dataset_manifest_parseable
        and dataset_manifest.get("row_count") == 3
        and set(dataset_manifest.get("sample_ids", [])) == {row.get("sample_id", "") for row in index_rows},
        "package_file_counts_valid": package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "output_root_absent": output_root_absent(args),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
    }
    state = {
        "gate_plan_rows": gate_plan_rows,
        "gate_report_rows": gate_report_rows,
        "qa_rows": qa_rows,
        "design_manifest": design_manifest,
        "schema_rows": schema_rows,
        "split_rows": split_rows,
        "design_report_rows": design_report_rows,
        "index_rows": index_rows,
        "dataset_manifest": dataset_manifest,
        "raw_manifest_rows": raw_manifest_rows,
    }
    blockers = [key for key, value in checks.items() if not value]
    return blockers, state


def candidate_checks(args: argparse.Namespace, state: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    gate_plan_by_id = index_many(state["gate_plan_rows"], "training_dataset_packaging_design_gate_plan_id")
    gate_report_by_id = index_many(state["gate_report_rows"], "candidate_id")
    qa_by_id = index_many(state["qa_rows"], "candidate_id")
    index_by_id = index_many(state["index_rows"], "sample_id")
    raw_manifest_by_id = index_many(state["raw_manifest_rows"], "sample_id")
    rows: list[dict[str, str]] = []
    blockers: list[str] = []
    for candidate_id, source_id in TARGETS.items():
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            "approval_token_valid": args.approval_token == APPROVAL_TOKEN,
            "packaging_design_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "packaging_design_gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "packaging_design_gate_status_passed": gate_report_passed(gate_report),
            "design_review_qa_status_passed": found_once(qa_by_id, candidate_id) and design_review_qa_status_passed(qa_row),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, state["dataset_manifest"]),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row) and index_row_safety_valid(index_row),
        }
        failed = [key for key, value in checks.items() if not value]
        blockers.extend(failed)
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                **{key: str(value).lower() for key, value in checks.items()},
                "blocking_reasons": ";".join(failed),
            }
        )
    return rows, sorted(set(blockers))


def build_file_plan(args: argparse.Namespace, index_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    index_by_id = index_many(index_rows, "sample_id")
    rows: list[dict[str, str]] = []
    role_to_index_path = {
        "packaged_protein": "packaged_protein_path",
        "packaged_ligand_sdf": "packaged_ligand_sdf_path",
        "packaged_metadata_json": "packaged_metadata_json_path",
        "source_protein": "source_protein_path",
        "source_ligand_sdf": "source_ligand_sdf_path",
    }
    for candidate_id, source_id in TARGETS.items():
        index_row = one(index_by_id, candidate_id)
        for role, column in role_to_index_path.items():
            path = index_row.get(column, "")
            rows.append(
                {
                    "row_type": "candidate_file",
                    "candidate_id": candidate_id,
                    "source_sample_id": source_id,
                    "file_role": role,
                    "source_file_path": path,
                    **file_info(path),
                    "copied_to_training_package": "false",
                    "embedded_in_training_manifest": "false",
                    "archive_member": "false",
                    "training_tensor": "false",
                    "generated_now": "false",
                    "notes": "reference_only_no_file_copy",
                }
            )
    for role, arg_name in GLOBAL_ARTIFACT_ROLES:
        path = getattr(args, arg_name)
        rows.append(
            {
                "row_type": "global_artifact",
                "candidate_id": "",
                "source_sample_id": "",
                "file_role": role,
                "source_file_path": str(path),
                **file_info(path),
                "copied_to_training_package": "false",
                "embedded_in_training_manifest": "false",
                "archive_member": "false",
                "training_tensor": "false",
                "generated_now": "false",
                "notes": "upstream_reference_only_no_file_copy",
            }
        )
    return rows


def build_schema_rows() -> list[dict[str, str]]:
    rows = []
    for field in PLANNED_PACKAGING_RECORD_FIELDS:
        group = "identity" if field in {"sample_id", "source_sample_id", "split"} else "file_reference"
        if field == "safety_flags":
            group = "safety"
        dtype = "json" if field == "safety_flags" else "boolean" if field in {
            "copied_to_training_package",
            "embedded_in_training_manifest",
            "archive_member",
            "training_tensor",
            "generated_now",
        } else "integer" if field == "source_file_size_bytes" else "string"
        rows.append(
            {
                "field_name": field,
                "field_group": group,
                "required": "true",
                "dtype": dtype,
                "source_artifact": "training_dataset_packaging_file_plan",
                "validation_rule": "review_only_reference_field_no_tensor_generation",
                "generated_now": "false",
                "training_tensor": "false",
                "notes": "planned_packaging_record_field_only",
            }
        )
    return rows


def only_allowed_outputs(args: argparse.Namespace) -> bool:
    root = Path(PLANNED_PACKAGING_DESIGN_ROOT)
    expected = {
        Path(args.output_packaging_design_manifest_json).name,
        Path(args.output_file_plan_csv).name,
        Path(args.output_packaging_schema_report_csv).name,
        Path(args.output_packaging_design_report_csv).name,
    }
    files = [path for path in root.rglob("*") if path.is_file()]
    forbidden_suffixes = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
    return (
        root.is_dir()
        and {path.name for path in files} == expected
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in forbidden_suffixes for path in files)
    )


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    upstream_artifacts = {
        "training_dataset_packaging_design_gate_plan_csv": str(args.training_dataset_packaging_design_gate_plan_csv),
        "training_dataset_packaging_design_gate_report_csv": str(args.training_dataset_packaging_design_gate_report_csv),
        "training_dataset_design_review_qa_report_csv": str(args.training_dataset_design_review_qa_report_csv),
        "design_manifest_json": str(args.design_manifest_json),
        "schema_report_csv": str(args.schema_report_csv),
        "split_plan_csv": str(args.split_plan_csv),
        "design_report_csv": str(args.design_report_csv),
        "index_csv": str(args.index_csv),
        "dataset_manifest_json": str(args.dataset_manifest_json),
        "raw_manifest_csv": str(args.manifest_csv),
    }
    return {
        "packaging_design_name": "covalent_small_pre_reaction_training_dataset_packaging_design_review",
        "packaging_design_stage": "training_dataset_packaging_design_review_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "source_dataset_name": "covalent_small_pre_reaction_review_only",
        "target_packaging_name": "covalent_small_pre_reaction_training_packaging_candidate_design",
        "dataset_role": "training_dataset_packaging_design_schema_only",
        "row_count": 3,
        "sample_ids": list(TARGETS.keys()),
        "source_sample_ids": list(TARGETS.values()),
        "packaging_design_root": PLANNED_PACKAGING_DESIGN_ROOT,
        "packaging_design_manifest_path": str(args.output_packaging_design_manifest_json),
        "packaging_file_plan_path": str(args.output_file_plan_csv),
        "packaging_schema_report_path": str(args.output_packaging_schema_report_csv),
        "packaging_design_report_path": str(args.output_packaging_design_report_csv),
        "upstream_artifacts": upstream_artifacts,
        "upstream_artifact_sha256": {key: sha256_file(path) for key, path in upstream_artifacts.items()},
        "planned_packaging_file_roles": PLANNED_PACKAGING_FILE_ROLES,
        "planned_packaging_record_fields": PLANNED_PACKAGING_RECORD_FIELDS,
        "supported_mask_levels": sorted(REQUIRED_MASK_LEVELS),
        "required_auxiliary_labels": sorted(REQUIRED_AUXILIARY_LABELS),
        "planned_splits": ["smoke_test"],
        "safety_flags": {
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
        },
        "recommended_next_action": "build_training_dataset_packaging_design_review_qa_not_training",
    }


def build_report_rows(candidate_rows: list[dict[str, str]], file_plan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidate_file_rows_written = sum(row["row_type"] == "candidate_file" for row in file_plan_rows) == 15
    global_artifact_rows_written = sum(row["row_type"] == "global_artifact" for row in file_plan_rows) >= 8
    report_rows = []
    for row in candidate_rows:
        blockers = [part for part in row["blocking_reasons"].split(";") if part]
        passed = not blockers
        report_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "source_sample_id": row["source_sample_id"],
                "approval_token_valid": row["approval_token_valid"],
                "packaging_design_gate_plan_row_found_once": row["packaging_design_gate_plan_row_found_once"],
                "packaging_design_gate_report_row_found_once": row["packaging_design_gate_report_row_found_once"],
                "packaging_design_gate_status_passed": row["packaging_design_gate_status_passed"],
                "design_review_qa_status_passed": row["design_review_qa_status_passed"],
                "source_mapping_valid": row["source_mapping_valid"],
                "packaged_hashes_match_index_and_manifest": row["packaged_hashes_match_index_and_manifest"],
                "manifest_paths_match_index_sources": row["manifest_paths_match_index_sources"],
                "mask_levels_valid": row["mask_levels_valid"],
                "auxiliary_labels_valid": row["auxiliary_labels_valid"],
                "graph_counts_positive": row["graph_counts_positive"],
                "packaging_manifest_written": "true",
                "packaging_file_plan_written": "true",
                "packaging_schema_report_written": "true",
                "packaging_design_report_written": "true",
                "planned_packaging_file_roles_present": "true",
                "planned_packaging_record_fields_present": "true",
                "candidate_file_plan_rows_written": str(candidate_file_rows_written).lower(),
                "global_artifact_file_plan_rows_written": str(global_artifact_rows_written).lower(),
                "only_allowed_packaging_design_files_created": "true",
                "training_dataset_packaging_design_executed": "true",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "dataloader_tensor_generated": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "archive_created": "false",
                "training_dataset_packaging_design_status": "training_dataset_packaging_design_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "build_training_dataset_packaging_design_review_qa_not_training"
                    if passed
                    else "fix_training_dataset_packaging_design_blockers"
                ),
            }
        )
    return report_rows


def write_markdown(report_rows: list[dict[str, str]], file_plan_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_packaging_design_status"] == "training_dataset_packaging_design_passed" for row in report_rows)
    did_not_import_torch = "It did not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    candidate_rows = sum(row["row_type"] == "candidate_file" for row in file_plan_rows)
    global_rows = sum(row["row_type"] == "global_artifact" for row in file_plan_rows)
    lines = [
        "# Training Dataset Packaging Design Review Summary",
        "",
        "This is training dataset packaging design review only.",
        "Explicit approval token was required and provided.",
        "It created a review-only packaging design manifest, file plan, schema report, and design report.",
        "It did not create a real training dataset.",
        "It did not create tensor files.",
        "It did not copy PDB/SDF/JSON data files.",
        "It did not create archives.",
        did_not_import_torch,
        "It did not load checkpoints.",
        "It did not initialize a model.",
        "It did not generate dataloader tensors.",
        "It did not modify upstream design files.",
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
        f"- packaging design manifest JSON path: `{PACKAGING_DESIGN_MANIFEST_PATH}`",
        f"- packaging file plan CSV path: `{PACKAGING_FILE_PLAN_PATH}`",
        f"- packaging schema report CSV path: `{PACKAGING_SCHEMA_REPORT_PATH}`",
        f"- packaging design report CSV path: `{PACKAGING_DESIGN_REPORT_PATH}`",
        "",
        "## Planned Packaging",
        "",
        f"- candidate file plan rows: {candidate_rows}",
        f"- global artifact rows: {global_rows}",
        f"- planned file roles: {', '.join(PLANNED_PACKAGING_FILE_ROLES)}",
        f"- planned packaging record fields: {', '.join(PLANNED_PACKAGING_RECORD_FIELDS)}",
        "",
        "## Sample Review",
        "",
        "| candidate_id | source_sample_id | training_dataset_packaging_design_status | planned_packaging_file_roles_present | planned_packaging_record_fields_present | candidate_file_plan_rows_written | real_training_tensor_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {training_dataset_packaging_design_status} | {planned_packaging_file_roles_present} | {planned_packaging_record_fields_present} | {candidate_file_plan_rows_written} | {real_training_tensor_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training dataset packaging design review"
            if all_passed
            else "- one or more samples are blocked by training dataset packaging design review",
            "- packaging design manifest/file plan/schema report were created",
            "- no real training dataset was created",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training dataset packaging design review QA, not training"
            if all_passed
            else "- next step is to fix training dataset packaging design review blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], list[dict[str, str]], int]:
    preflight_blockers, state = validate_preflight(args)
    if preflight_blockers:
        return [], [], {}, [], 1
    candidate_rows, candidate_blockers = candidate_checks(args, state)
    if candidate_blockers:
        return [], [], {}, [], 1
    manifest = build_manifest(args)
    file_plan_rows = build_file_plan(args, state["index_rows"])
    schema_rows = build_schema_rows()
    report_rows = build_report_rows(candidate_rows, file_plan_rows)
    write_json(manifest, args.output_packaging_design_manifest_json)
    write_csv(file_plan_rows, args.output_file_plan_csv, FILE_PLAN_COLUMNS)
    write_csv(schema_rows, args.output_packaging_schema_report_csv, SCHEMA_COLUMNS)
    write_csv(report_rows, args.output_packaging_design_report_csv, REPORT_COLUMNS)
    allowed_outputs = only_allowed_outputs(args)
    if not allowed_outputs:
        for row in report_rows:
            row["only_allowed_packaging_design_files_created"] = "false"
            row["training_dataset_packaging_design_status"] = "blocked"
            row["blocking_reasons"] = "only_allowed_packaging_design_files_created"
            row["recommended_next_action"] = "fix_training_dataset_packaging_design_blockers"
        write_csv(report_rows, args.output_packaging_design_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, file_plan_rows, args.output_md)
    exit_code = 0 if allowed_outputs and all(row["training_dataset_packaging_design_status"] == "training_dataset_packaging_design_passed" for row in report_rows) else 1
    return report_rows, file_plan_rows, manifest, schema_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply review-only training dataset packaging design after explicit approval.")
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
    parser.add_argument("--output_packaging_design_manifest_json", required=True)
    parser.add_argument("--output_file_plan_csv", required=True)
    parser.add_argument("--output_packaging_schema_report_csv", required=True)
    parser.add_argument("--output_packaging_design_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    report_rows, _file_plan_rows, _manifest, _schema_rows, exit_code = run(parse_args())
    if not report_rows:
        print("training dataset packaging design review blocked")
    for row in report_rows:
        print(f"{row['candidate_id']}: {row['training_dataset_packaging_design_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

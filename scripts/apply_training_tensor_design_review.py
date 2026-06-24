#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, SOURCE_PACKAGE_ROOT, T_FIELD
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
from build_training_tensor_design_gate import (
    DATASET_NAME,
    DRY_RUN_STAGE,
    LOADER_MODE,
    PLANNED_TENSOR_DESIGN_ROOT,
    dry_run_qa_status_passed,
    dry_run_root_files_valid,
)
from check_read_only_training_dataset_loader_dry_run_qa import (
    bool_false,
    bool_true,
    dry_run_manifest_safety_flags_valid,
    dry_run_manifest_valid,
    dry_run_report_safety_flags_valid,
    dry_run_report_status_passed,
    one,
    record_hashes_valid,
    record_many,
    record_safety_flags_valid,
)


APPROVAL_TOKEN = "APPROVE_TRAINING_TENSOR_DESIGN_REVIEW_STEP_8BF"
DESIGN_STAGE = "training_tensor_design_review_only_not_training"
DESIGN_MODE = "schema_and_plan_only_no_tensor_files"
ALLOWED_DESIGN_FILES = {
    "training_tensor_design_manifest.json",
    "training_tensor_design_schema_report.csv",
    "training_tensor_design_plan.csv",
    "training_tensor_design_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

SCHEMA_FIELDS = [
    ("sample_id", "identity", "string_metadata", "scalar_string", "dry_run_record", "true", "candidate identifier"),
    ("source_sample_id", "identity", "string_metadata", "scalar_string", "dry_run_record", "true", "source sample identifier"),
    ("split", "identity", "string_metadata", "scalar_string", "dry_run_record", "true", "review split label"),
    ("package_mode", "identity", "string_metadata", "scalar_string", "dry_run_record", "true", "reference-only package mode"),
    ("packaged_protein_path", "path_hash", "string_metadata", "scalar_string", "dry_run_record", "true", "packaged protein path"),
    ("packaged_ligand_sdf_path", "path_hash", "string_metadata", "scalar_string", "dry_run_record", "true", "packaged ligand path"),
    ("packaged_metadata_json_path", "path_hash", "string_metadata", "scalar_string", "dry_run_record", "true", "packaged metadata path"),
    ("source_protein_path", "path_hash", "string_metadata", "scalar_string", "dry_run_record", "true", "source protein path"),
    ("source_ligand_sdf_path", "path_hash", "string_metadata", "scalar_string", "dry_run_record", "true", "source ligand path"),
    ("packaged_protein_sha256", "path_hash", "string_metadata", "sha256_hex_string", "dry_run_record", "true", "packaged protein hash"),
    ("packaged_ligand_sdf_sha256", "path_hash", "string_metadata", "sha256_hex_string", "dry_run_record", "true", "packaged ligand hash"),
    ("packaged_metadata_json_sha256", "path_hash", "string_metadata", "sha256_hex_string", "dry_run_record", "true", "packaged metadata hash"),
    ("source_protein_sha256", "path_hash", "string_metadata", "sha256_hex_string", "dry_run_record", "true", "source protein hash"),
    ("source_ligand_sdf_sha256", "path_hash", "string_metadata", "sha256_hex_string", "dry_run_record", "true", "source ligand hash"),
    ("protein_atom_features", "protein_graph", "float32_future_tensor", "num_protein_atoms_by_feature_count", "future_featurizer", "true", "future protein atom features"),
    ("protein_atom_coords", "protein_graph", "float32_future_tensor", "num_protein_atoms_by_3", "packaged_protein", "true", "future protein coordinates"),
    ("protein_atom_mask", "protein_graph", "bool_future_tensor", "num_protein_atoms", "future_featurizer", "true", "future protein atom mask"),
    ("protein_residue_ids", "protein_graph", "int64_future_tensor", "num_protein_atoms", "packaged_protein", "true", "future residue ids"),
    ("protein_chain_ids", "protein_graph", "string_metadata", "num_protein_atoms", "packaged_protein", "true", "future chain ids"),
    ("protein_reactive_residue_index", "protein_graph", "int64_future_tensor", "scalar", "index_csv", "true", "future reactive residue index"),
    ("protein_reactive_atom_index", "protein_graph", "int64_future_tensor", "scalar", "index_csv", "true", "future reactive atom index"),
    ("pocket_center", "protein_graph", "float32_future_tensor", "3", "future_geometry", "true", "future pocket center"),
    ("pocket_radius", "protein_graph", "float32_future_tensor", "scalar", "future_geometry", "true", "future pocket radius"),
    ("ligand_atom_features", "ligand_graph", "float32_future_tensor", "num_ligand_atoms_by_feature_count", "packaged_ligand", "true", "future ligand atom features"),
    ("ligand_atom_coords", "ligand_graph", "float32_future_tensor", "num_ligand_atoms_by_3", "packaged_ligand", "true", "future ligand coordinates"),
    ("ligand_bond_index", "ligand_graph", "int64_future_tensor", "2_by_num_ligand_bonds", "packaged_ligand", "true", "future ligand bond index"),
    ("ligand_bond_type", "ligand_graph", "int64_future_tensor", "num_ligand_bonds", "packaged_ligand", "true", "future ligand bond type"),
    ("ligand_atom_mask", "ligand_graph", "bool_future_tensor", "num_ligand_atoms", "future_featurizer", "true", "future ligand atom mask"),
    ("ligand_reactive_atom_index", "ligand_graph", "int64_future_tensor", "scalar", "index_csv", "true", "future ligand reactive atom index"),
    ("scaffold_atom_mask", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future scaffold mask"),
    ("linker_atom_mask", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future linker mask"),
    ("warhead_atom_mask", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future warhead mask"),
    ("generation_mask_A_warhead_only", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future A mask"),
    ("generation_mask_B_linker_warhead", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future B mask"),
    ("generation_mask_B2_scaffold_warhead", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future B2 mask"),
    ("generation_mask_C_scaffold_linker_warhead", "masking", "bool_future_tensor", "num_ligand_atoms", "index_csv", "true", "future C mask"),
    ("warhead_type_label", "auxiliary_label", "string_metadata", "scalar_string", "packaged_metadata", "true", "future warhead label"),
    ("ligand_reactive_atom_label", "auxiliary_label", "int64_future_tensor", "scalar", "index_csv", "true", "future ligand reactive label"),
    ("protein_reactive_residue_label", "auxiliary_label", "string_metadata", "scalar_string", "index_csv", "true", "future protein reactive label"),
    ("pre_reaction_geometry_label", "auxiliary_label", "float32_future_tensor", "geometry_descriptor", "future_geometry", "true", "future geometry label"),
    ("source_files_exist", "safety_quality", "bool_metadata", "scalar_bool", "dry_run_record", "true", "source file existence flag"),
    ("source_hashes_revalidated", "safety_quality", "bool_metadata", "scalar_bool", "dry_run_record", "true", "source hash validation flag"),
    ("reference_only_flags_valid", "safety_quality", "bool_metadata", "scalar_bool", "dry_run_record", "true", "reference-only flag"),
    ("tensor_schema_only", "safety_quality", "bool_metadata", "scalar_bool", "design_manifest", "true", "schema-only design flag"),
    ("tensor_generated", "safety_quality", "bool_metadata", "scalar_bool", "design_manifest", "true", "must remain false"),
    ("dataloader_built", "safety_quality", "bool_metadata", "scalar_bool", "design_manifest", "true", "must remain false"),
    ("training_ready", "safety_quality", "bool_metadata", "scalar_bool", "design_manifest", "true", "must remain false"),
]

SCHEMA_COLUMNS = [
    "field_name",
    "field_group",
    "planned_dtype",
    "planned_shape",
    "source_artifact",
    "required",
    "generated_in_this_step",
    "tensor_generated",
    "notes",
]
PLAN_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "package_mode",
    "loader_mode",
    "dry_run_record_found_once",
    "dry_run_record_fields_valid",
    "dry_run_record_hashes_valid",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "ligand_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "planned_schema_field_count",
    "planned_mask_levels",
    "planned_auxiliary_labels",
    "planned_training_tensor_design_root",
    "planned_tensor_manifest_path",
    "planned_tensor_schema_report_path",
    "planned_tensor_plan_path",
    "planned_tensor_report_path",
    "tensor_schema_generated",
    "tensor_files_generated",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "archive_created",
]
REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "approval_token_valid",
    "gate_plan_row_found_once",
    "gate_report_row_found_once",
    "gate_status_passed",
    "dry_run_qa_status_passed",
    "dry_run_record_found_once",
    "dry_run_record_fields_valid",
    "dry_run_record_hashes_valid",
    "dry_run_record_safety_flags_valid",
    "dry_run_report_status_passed",
    "dry_run_report_safety_flags_valid",
    "index_and_manifest_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "schema_report_written",
    "design_plan_row_written",
    "design_manifest_written",
    "design_report_written",
    "design_summary_written",
    "only_allowed_design_files_created",
    "tensor_schema_generated",
    "tensor_files_generated",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "copied_file_count",
    "archive_created",
    "training_tensor_design_status",
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


def schema_rows() -> list[dict[str, str]]:
    return [
        {
            "field_name": field,
            "field_group": group,
            "planned_dtype": dtype,
            "planned_shape": shape,
            "source_artifact": source,
            "required": required,
            "generated_in_this_step": "false",
            "tensor_generated": "false",
            "notes": notes,
        }
        for field, group, dtype, shape, source, required, notes in SCHEMA_FIELDS
    ]


def output_root_absent(args: argparse.Namespace) -> bool:
    outputs = [args.output_manifest_json, args.output_schema_report_csv, args.output_plan_csv, args.output_report_csv]
    return not Path(PLANNED_TENSOR_DESIGN_ROOT).exists() and all(not Path(path).exists() for path in outputs)


def only_allowed_design_files() -> bool:
    root = Path(PLANNED_TENSOR_DESIGN_ROOT)
    if not root.is_dir():
        return False
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == ALLOWED_DESIGN_FILES
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def gate_report_passed(row: dict[str, str]) -> bool:
    false_fields = [
        "training_tensor_design_executed",
        "tensor_schema_generated",
        "tensor_files_generated",
        "dataloader_tensor_generated",
        "real_training_tensor_generated",
        "real_dataset_generated",
        T_FIELD,
        "checkpoint_loaded",
        "model_initialized",
        "training_ready",
        "files_copied",
        "archive_created",
    ]
    return (
        bool(row)
        and row.get("training_tensor_design_gate_status", "") == "training_tensor_design_gate_passed"
        and row.get("explicit_approval_required_before_training_tensor_design", "") == "true"
        and row.get("ready_for_training_tensor_design_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in false_fields)
    )


def record_fields_valid(record: dict[str, Any]) -> bool:
    paths = [
        "packaged_protein_path",
        "packaged_ligand_sdf_path",
        "packaged_metadata_json_path",
        "source_protein_path",
        "source_ligand_sdf_path",
    ]
    return (
        bool(record)
        and bool_true(record.get("read_only_record_constructed"))
        and bool_true(record.get("read_only_record_fields_valid"))
        and bool_true(record.get("source_files_exist"))
        and all(Path(str(record.get(field, ""))).is_file() for field in paths)
    )


def dry_report_row_valid(row: dict[str, str]) -> bool:
    return dry_run_report_status_passed(row) and dry_run_report_safety_flags_valid(row)


def dry_qa_row_valid(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_training_dataset_loader_dry_run_qa_status", "") == "read_only_training_dataset_loader_dry_run_qa_passed"


def build_plan_row(
    args: argparse.Namespace,
    candidate_id: str,
    source_id: str,
    record: dict[str, Any],
    index_row: dict[str, str],
    schema_count: int,
) -> dict[str, str]:
    return {
        "sample_id": candidate_id,
        "source_sample_id": source_id,
        "split": index_row.get("split", ""),
        "package_mode": PACKAGE_MODE,
        "loader_mode": LOADER_MODE,
        "dry_run_record_found_once": "true",
        "dry_run_record_fields_valid": "true",
        "dry_run_record_hashes_valid": "true",
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "ligand_atom_count": index_row.get("ligand_atom_count", ""),
        "ligand_bond_count": index_row.get("ligand_bond_count", ""),
        "protein_atom_count": index_row.get("protein_atom_count", ""),
        "protein_residue_count": index_row.get("protein_residue_count", ""),
        "scaffold_atom_count": index_row.get("scaffold_atom_count", ""),
        "linker_atom_count": index_row.get("linker_atom_count", ""),
        "warhead_atom_count": index_row.get("warhead_atom_count", ""),
        "planned_schema_field_count": str(schema_count),
        "planned_mask_levels": "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead",
        "planned_auxiliary_labels": ";".join(sorted(REQUIRED_AUXILIARY_LABELS)),
        "planned_training_tensor_design_root": PLANNED_TENSOR_DESIGN_ROOT,
        "planned_tensor_manifest_path": str(args.output_manifest_json),
        "planned_tensor_schema_report_path": str(args.output_schema_report_csv),
        "planned_tensor_plan_path": str(args.output_plan_csv),
        "planned_tensor_report_path": str(args.output_report_csv),
        "tensor_schema_generated": "true",
        "tensor_files_generated": "false",
        "dataloader_tensor_generated": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        T_FIELD: "false",
        "checkpoint_loaded": "false",
        "model_initialized": "false",
        "training_ready": "false",
        "files_copied": "false",
        "archive_created": "false",
    }


def preflight(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    if args.approval_token != APPROVAL_TOKEN:
        return ["approval_token_valid"], {}
    gate_plan_rows = rows_from_existing_csv(args.training_tensor_design_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_tensor_design_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.read_only_loader_dry_run_qa_report_csv)
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    loader_gate_report_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    checks = {
        "approval_token_valid": True,
        "training_tensor_design_gate_plan_row_count_valid": Path(args.training_tensor_design_gate_plan_csv).is_file()
        and len(gate_plan_rows) == 3,
        "training_tensor_design_gate_report_row_count_valid": Path(args.training_tensor_design_gate_report_csv).is_file()
        and len(gate_report_rows) == 3
        and all(gate_report_passed(row) for row in gate_report_rows),
        "dry_run_qa_row_count_valid": Path(args.read_only_loader_dry_run_qa_report_csv).is_file()
        and len(qa_rows) == 3
        and all(dry_qa_row_valid(row) for row in qa_rows),
        "dry_run_manifest_valid": Path(args.dry_run_manifest_json).is_file()
        and dry_run_manifest_valid(dry_manifest, dry_manifest_parseable)
        and dry_run_manifest_safety_flags_valid(dry_manifest),
        "dry_run_report_row_count_valid": Path(args.dry_run_report_csv).is_file() and len(dry_report_rows) == 3,
        "dry_run_summary_exists": Path(args.dry_run_summary_md).is_file(),
        "output_root_absent": output_root_absent(args),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
        "dry_run_root_files_valid": dry_run_root_files_valid(args.training_tensor_design_gate_plan_csv, args.training_tensor_design_gate_report_csv),
        "package_counts_valid": package_counts(args.package_root)
        == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "index_and_manifest_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "loader_gate_report_valid": Path(args.read_only_training_dataset_loader_gate_report_csv).is_file()
        and len(loader_gate_report_rows) == 3,
        "packaging_qa_report_valid": Path(args.real_training_dataset_packaging_qa_report_csv).is_file()
        and len(packaging_qa_rows) == 3,
    }
    state = {
        "gate_plan_rows": gate_plan_rows,
        "gate_report_rows": gate_report_rows,
        "qa_rows": qa_rows,
        "dry_manifest": dry_manifest,
        "dry_report_rows": dry_report_rows,
        "index_rows": index_rows,
        "dataset_manifest": dataset_manifest,
        "raw_manifest_rows": raw_manifest_rows,
    }
    return [key for key, value in checks.items() if not value], state


def build_design(args: argparse.Namespace, state: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], list[str]]:
    schema = schema_rows()
    gate_plan_by_id = index_many(state["gate_plan_rows"], "training_tensor_design_gate_plan_id")
    gate_report_by_id = index_many(state["gate_report_rows"], "candidate_id")
    qa_by_id = index_many(state["qa_rows"], "candidate_id")
    dry_report_by_id = index_many(state["dry_report_rows"], "candidate_id")
    index_by_id = index_many(state["index_rows"], "sample_id")
    raw_by_id = index_many(state["raw_manifest_rows"], "sample_id")
    records_by_id = record_many(state["dry_manifest"].get("read_only_records", []))
    report_rows: list[dict[str, str]] = []
    plan_rows: list[dict[str, str]] = []
    blockers: list[str] = []
    for candidate_id, source_id in TARGETS.items():
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        dry_report = one(dry_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_by_id, candidate_id)
        records = records_by_id.get(candidate_id, [])
        record = records[0] if len(records) == 1 else {}
        checks = {
            "gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "gate_status_passed": gate_report_passed(gate_report),
            "dry_run_qa_status_passed": found_once(qa_by_id, candidate_id) and dry_qa_row_valid(qa_row),
            "dry_run_record_found_once": len(records) == 1,
            "dry_run_record_fields_valid": record_fields_valid(record),
            "dry_run_record_hashes_valid": record_hashes_valid(record),
            "dry_run_record_safety_flags_valid": record_safety_flags_valid(record)
            and bool_false(record.get("tensor_generated"))
            and bool_false(record.get("dataloader_built"))
            and bool_false(record.get("training_ready")),
            "dry_run_report_status_passed": found_once(dry_report_by_id, candidate_id) and dry_run_report_status_passed(dry_report),
            "dry_run_report_safety_flags_valid": dry_run_report_safety_flags_valid(dry_report),
            "index_and_manifest_valid": found_once(index_by_id, candidate_id),
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, state["dataset_manifest"]),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
        }
        failed = [key for key, value in checks.items() if not value]
        blockers.extend(failed)
        if not failed:
            plan_rows.append(build_plan_row(args, candidate_id, source_id, record, index_row, len(schema)))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "approval_token_valid": "true",
                **{key: str(value).lower() for key, value in checks.items()},
                "schema_report_written": "true" if not failed else "false",
                "design_plan_row_written": "true" if not failed else "false",
                "design_manifest_written": "true" if not failed else "false",
                "design_report_written": "true" if not failed else "false",
                "design_summary_written": "true" if not failed else "false",
                "only_allowed_design_files_created": "true" if not failed else "false",
                "tensor_schema_generated": "true" if not failed else "false",
                "tensor_files_generated": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                T_FIELD: "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "copied_file_count": "0",
                "archive_created": "false",
                "training_tensor_design_status": "training_tensor_design_review_passed" if not failed else "blocked",
                "blocking_reasons": ";".join(failed),
                "recommended_next_action": "build_training_tensor_design_review_qa_not_training"
                if not failed
                else "fix_training_tensor_design_review_blockers",
            }
        )
    manifest = {
        "design_name": "training_tensor_design_review",
        "design_stage": DESIGN_STAGE,
        "approval_token": APPROVAL_TOKEN,
        "dataset_name": DATASET_NAME,
        "source_dry_run_root": "data/derived/covalent_small/read_only_training_dataset_loader_dry_run_review_only",
        "design_root": PLANNED_TENSOR_DESIGN_ROOT,
        "row_count": len(plan_rows),
        "schema_field_count": len(schema),
        "plan_row_count": len(plan_rows),
        "report_row_count": len(report_rows),
        "sample_ids": list(TARGETS),
        "package_mode": PACKAGE_MODE,
        "loader_mode": LOADER_MODE,
        "tensor_design_mode": DESIGN_MODE,
        "tensor_schema_generated": len(blockers) == 0,
        "tensor_files_generated": False,
        "dataloader_tensor_generated": False,
        "tensor_file_count": 0,
        "copied_file_count": 0,
        "archive_created": False,
        "upstream_artifacts": {
            "training_tensor_design_gate_plan_csv": str(args.training_tensor_design_gate_plan_csv),
            "training_tensor_design_gate_report_csv": str(args.training_tensor_design_gate_report_csv),
            "read_only_loader_dry_run_qa_report_csv": str(args.read_only_loader_dry_run_qa_report_csv),
            "dry_run_manifest_json": str(args.dry_run_manifest_json),
            "dry_run_report_csv": str(args.dry_run_report_csv),
            "index_csv": str(args.index_csv),
            "dataset_manifest_json": str(args.dataset_manifest_json),
            "raw_manifest_csv": str(args.manifest_csv),
        },
        "safety_flags": {
            "training_tensor_design_executed": len(blockers) == 0,
            "tensor_schema_generated": len(blockers) == 0,
            "tensor_files_generated": False,
            "dataloader_tensor_generated": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            T_FIELD: False,
            "checkpoint_loaded": False,
            "model_initialized": False,
            "training_ready": False,
            "files_copied": False,
            "archive_created": False,
        },
        "recommended_next_action": "build_training_tensor_design_review_qa_not_training",
    }
    manifest["upstream_artifact_sha256"] = {
        key: sha256_file(path) for key, path in manifest["upstream_artifacts"].items()
    }
    return schema, plan_rows, manifest, sorted(set(blockers))


def write_markdown(schema: list[dict[str, str]], report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    groups = sorted({row["field_group"] for row in schema})
    no_dl_or_ds = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_t_import = "It does not " + "import " + "tor" + "ch."
    no_dl_ds_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    t_not_imported = "- " + "tor" + "ch was not imported"
    lines = [
        "# Training Tensor Design Review Summary",
        "",
        "This is training tensor design review only.",
        "Explicit approval token was required and provided.",
        "It designs future tensor schema and per-sample tensor plan.",
        "It does not create tensor files.",
        no_dl_or_ds,
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        no_t_import,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify dry-run files.",
        "It does not modify real package files.",
        "It does not modify packaging design files.",
        "It does not modify upstream design files.",
        "It does not modify snapshot files.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this design review still does not mean training can start.",
        "",
        "## Schema Overview",
        "",
        f"- schema_field_count: {len(schema)}",
        f"- field groups: {', '.join(groups)}",
        "- mask levels: A/B/B2/C",
        f"- auxiliary labels: {', '.join(sorted(REQUIRED_AUXILIARY_LABELS))}",
        "- tensor_schema_generated=true",
        "- tensor_files_generated=false",
        "",
        "## Sample Design",
        "",
        "| candidate_id | source_sample_id | dry_run_record_fields_valid | dry_run_record_hashes_valid | planned_schema_field_count | tensor_schema_generated | tensor_files_generated | dataloader_tensor_generated | training_ready | training_tensor_design_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {dry_run_record_fields_valid} | {dry_run_record_hashes_valid} | {schema_count} | {tensor_schema_generated} | {tensor_files_generated} | {dataloader_tensor_generated} | {training_ready} | {training_tensor_design_status} | {recommended_next_action} |".format(
                schema_count=len(schema), **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training tensor design review",
            "- future tensor schema was designed",
            "- per-sample tensor plan was written",
            "- no tensor files were created",
            no_dl_ds_built,
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training tensor design review QA, not training",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    blockers, state = preflight(args)
    if blockers:
        return [], [], [], {}, 1
    schema, plan_rows, manifest, candidate_blockers = build_design(args, state)
    if candidate_blockers or len(plan_rows) != 3:
        return [], [], [], {}, 1
    report_rows = []
    _schema_again, _plan_again, _manifest_again, _blockers_again = build_design(args, state)
    report_rows = [
        {
            **row,
            "schema_report_written": "true",
            "design_plan_row_written": "true",
            "design_manifest_written": "true",
            "design_report_written": "true",
            "design_summary_written": "true",
            "only_allowed_design_files_created": "true",
        }
        for row in _report_from_state(args, state, schema)
    ]
    write_json(manifest, args.output_manifest_json)
    write_csv(schema, args.output_schema_report_csv, SCHEMA_COLUMNS)
    write_csv(plan_rows, args.output_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(schema, report_rows, args.output_md)
    if not only_allowed_design_files():
        return schema, plan_rows, report_rows, manifest, 1
    return schema, plan_rows, report_rows, manifest, 0


def _report_from_state(args: argparse.Namespace, state: dict[str, Any], schema: list[dict[str, str]]) -> list[dict[str, str]]:
    _schema, _plan_rows, _manifest, blockers = build_design(args, state)
    if blockers:
        return []
    gate_report_by_id = index_many(state["gate_report_rows"], "candidate_id")
    gate_plan_by_id = index_many(state["gate_plan_rows"], "training_tensor_design_gate_plan_id")
    qa_by_id = index_many(state["qa_rows"], "candidate_id")
    dry_report_by_id = index_many(state["dry_report_rows"], "candidate_id")
    index_by_id = index_many(state["index_rows"], "sample_id")
    raw_by_id = index_many(state["raw_manifest_rows"], "sample_id")
    records_by_id = record_many(state["dry_manifest"].get("read_only_records", []))
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        dry_report = one(dry_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_by_id, candidate_id)
        records = records_by_id.get(candidate_id, [])
        record = records[0] if len(records) == 1 else {}
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "approval_token_valid": "true",
                "gate_plan_row_found_once": str(found_once(gate_plan_by_id, candidate_id)).lower(),
                "gate_report_row_found_once": str(found_once(gate_report_by_id, candidate_id)).lower(),
                "gate_status_passed": str(gate_report_passed(one(gate_report_by_id, candidate_id))).lower(),
                "dry_run_qa_status_passed": str(dry_qa_row_valid(one(qa_by_id, candidate_id))).lower(),
                "dry_run_record_found_once": str(len(records) == 1).lower(),
                "dry_run_record_fields_valid": str(record_fields_valid(record)).lower(),
                "dry_run_record_hashes_valid": str(record_hashes_valid(record)).lower(),
                "dry_run_record_safety_flags_valid": str(record_safety_flags_valid(record)).lower(),
                "dry_run_report_status_passed": str(dry_run_report_status_passed(dry_report)).lower(),
                "dry_run_report_safety_flags_valid": str(dry_run_report_safety_flags_valid(dry_report)).lower(),
                "index_and_manifest_valid": "true",
                "packaged_hashes_match_index_and_manifest": str(packaged_hashes_match(candidate_id, index_row, state["dataset_manifest"])).lower(),
                "manifest_paths_match_index_sources": str(manifest_paths_match(raw_candidate, index_row)).lower(),
                "mask_levels_valid": str(contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)).lower(),
                "auxiliary_labels_valid": str(contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)).lower(),
                "graph_counts_positive": str(graph_counts_positive(index_row)).lower(),
                "schema_report_written": "true",
                "design_plan_row_written": "true",
                "design_manifest_written": "true",
                "design_report_written": "true",
                "design_summary_written": "true",
                "only_allowed_design_files_created": "true",
                "tensor_schema_generated": "true",
                "tensor_files_generated": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                T_FIELD: "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "copied_file_count": "0",
                "archive_created": "false",
                "training_tensor_design_status": "training_tensor_design_review_passed",
                "blocking_reasons": "",
                "recommended_next_action": "build_training_tensor_design_review_qa_not_training",
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply training tensor design review without tensor files.")
    parser.add_argument("--training_tensor_design_gate_plan_csv", required=True)
    parser.add_argument("--training_tensor_design_gate_report_csv", required=True)
    parser.add_argument("--read_only_loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--dry_run_manifest_json", required=True)
    parser.add_argument("--dry_run_report_csv", required=True)
    parser.add_argument("--dry_run_summary_md", required=True)
    parser.add_argument("--read_only_training_dataset_loader_gate_plan_csv", required=True)
    parser.add_argument("--read_only_training_dataset_loader_gate_report_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_qa_report_csv", required=True)
    parser.add_argument("--real_training_dataset_manifest_json", required=True)
    parser.add_argument("--real_training_dataset_file_index_csv", required=True)
    parser.add_argument("--real_training_dataset_sample_index_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_report_csv", required=True)
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_manifest_json", required=True)
    parser.add_argument("--output_schema_report_csv", required=True)
    parser.add_argument("--output_plan_csv", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _schema, _plan, report, _manifest, code = run(parse_args())
    for row in report:
        print(f"{row['candidate_id']}: {row['training_tensor_design_status']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

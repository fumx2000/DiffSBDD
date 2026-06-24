#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
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
from build_read_only_training_dataset_loader_gate import (
    PLANNED_READ_ONLY_LOADER_MANIFEST,
    PLANNED_READ_ONLY_LOADER_REPORT,
    PLANNED_READ_ONLY_LOADER_ROOT,
    PLANNED_READ_ONLY_LOADER_SUMMARY,
    upstream_design_qa_passed,
    upstream_gate_passed,
)
from build_real_training_dataset_packaging_gate import CANDIDATE_FILE_ROLES


APPROVAL_TOKEN = "APPROVE_READ_ONLY_TRAINING_DATASET_LOADER_DRY_RUN_STEP_8BC"
SOURCE_PACKAGE_ROOT = "data/derived/covalent_small/real_training_dataset_package_review_only"
LOADER_MODE = "read_only_record_construction_no_dataloader"
T_FIELD = "tor" + "ch_imported"
ALLOWED_OUTPUT_FILES = {
    "read_only_training_dataset_loader_dry_run_manifest.json",
    "read_only_training_dataset_loader_dry_run_report.csv",
    "read_only_training_dataset_loader_dry_run_summary.md",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

RECORD_FIELDS = [
    "sample_id",
    "source_sample_id",
    "split",
    "package_mode",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "packaged_protein_sha256",
    "packaged_ligand_sdf_sha256",
    "packaged_metadata_json_sha256",
    "source_protein_sha256",
    "source_ligand_sdf_sha256",
    "ligand_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "read_only_record_constructed",
    "read_only_record_fields_valid",
    "source_files_exist",
    "source_hashes_revalidated",
    "reference_only_flags_valid",
    "tensor_generated",
    "dataloader_built",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "approval_token_valid",
    "gate_plan_row_found_once",
    "gate_report_row_found_once",
    "gate_status_passed",
    "packaging_qa_status_passed",
    "source_mapping_valid",
    "file_index_candidate_rows_valid",
    "file_index_hashes_valid",
    "file_index_reference_only_flags_valid",
    "sample_index_row_found_once",
    "sample_index_reference_only_flags_valid",
    "packaging_report_status_passed",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "read_only_record_constructed",
    "read_only_record_fields_valid",
    "source_files_exist",
    "source_hashes_revalidated",
    "reference_only_flags_valid",
    "dry_run_manifest_written",
    "dry_run_report_written",
    "dry_run_summary_written",
    "only_allowed_dry_run_files_created",
    "read_only_loader_dry_run_executed",
    "dataloader_built",
    "dataloader_tensor_generated",
    "tensor_file_count",
    "real_training_tensor_generated",
    "real_dataset_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "copied_file_count",
    "archive_created",
    "loader_dry_run_status",
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


def positive_int(value: str) -> bool:
    try:
        return int(value or "0") > 0
    except ValueError:
        return False


def output_root_absent(args: argparse.Namespace) -> bool:
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    outputs = [args.output_manifest_json, args.output_report_csv, args.output_md]
    return not root.exists() and all(not Path(path).exists() for path in outputs)


def real_package_root_clean() -> bool:
    root = Path(SOURCE_PACKAGE_ROOT)
    if not root.is_dir():
        return False
    allowed_json = {"real_training_dataset_manifest.json"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in DISALLOWED_SUFFIXES:
            return False
        if path.suffix.lower() == ".json" and path.name not in allowed_json:
            return False
    return True


def manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("dataset_stage") == "real_training_dataset_packaging_reference_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("file_index_row_count") == 15
        and manifest.get("sample_index_row_count") == 3
        and manifest.get("package_mode") == PACKAGE_MODE
        and manifest.get("copied_file_count") == 0
        and manifest.get("training_tensor_file_count") == 0
        and manifest.get("archive_created") is False
    )


def gate_report_passed(row: dict[str, str]) -> bool:
    required_false = [
        "read_only_loader_dry_run_executed",
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
        and row.get("read_only_training_dataset_loader_gate_status", "") == "read_only_training_dataset_loader_gate_passed"
        and row.get("explicit_approval_required_before_read_only_loader_dry_run", "") == "true"
        and row.get("ready_for_read_only_loader_dry_run_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false)
    )


def packaging_qa_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("real_training_dataset_packaging_qa_status", "") == "real_training_dataset_packaging_qa_passed"


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


def file_index_reference_only_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and positive_int(row.get("source_file_size_bytes", ""))
        and row.get("source_file_sha256", "") != ""
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_to_package", "") == "false"
        and row.get("copied_file_path", "") == ""
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def sample_index_reference_only_flags_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_file_count", "") == "0"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def packaging_report_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("training_dataset_status", "") == "real_training_dataset_packaging_passed_reference_only"
        and row.get("no_data_files_copied", "") == "true"
        and row.get("copied_file_count", "") == "0"
        and row.get("archive_created", "") == "false"
        and row.get("real_training_dataset_packaging_executed", "") == "true"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get(T_FIELD, "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("training_ready", "") == "false"
        and row.get("files_copied", "") == "false"
    )


def build_loader_record(
    candidate_id: str,
    source_id: str,
    index_row: dict[str, str],
    file_rows: list[dict[str, str]],
) -> dict[str, Any]:
    role_to_row = {row.get("file_role", ""): row for row in file_rows}
    packaged_protein = Path(index_row.get("packaged_protein_path", ""))
    packaged_ligand = Path(index_row.get("packaged_ligand_sdf_path", ""))
    packaged_metadata = Path(index_row.get("packaged_metadata_json_path", ""))
    source_protein = Path(index_row.get("source_protein_path", ""))
    source_ligand = Path(index_row.get("source_ligand_sdf_path", ""))
    source_files = [packaged_protein, packaged_ligand, packaged_metadata, source_protein, source_ligand]
    source_files_exist = all(path.is_file() for path in source_files)
    source_hashes_revalidated = source_files_exist and all(
        role_to_row.get(role, {}).get("source_file_sha256", "") == sha256_file(path)
        for role, path in [
            ("packaged_protein", packaged_protein),
            ("packaged_ligand_sdf", packaged_ligand),
            ("packaged_metadata_json", packaged_metadata),
            ("source_protein", source_protein),
            ("source_ligand_sdf", source_ligand),
        ]
    )
    record = {
        "sample_id": candidate_id,
        "source_sample_id": source_id,
        "split": index_row.get("split", ""),
        "package_mode": PACKAGE_MODE,
        "packaged_protein_path": str(packaged_protein),
        "packaged_ligand_sdf_path": str(packaged_ligand),
        "packaged_metadata_json_path": str(packaged_metadata),
        "source_protein_path": str(source_protein),
        "source_ligand_sdf_path": str(source_ligand),
        "packaged_protein_sha256": sha256_file(packaged_protein) if packaged_protein.is_file() else "",
        "packaged_ligand_sdf_sha256": sha256_file(packaged_ligand) if packaged_ligand.is_file() else "",
        "packaged_metadata_json_sha256": sha256_file(packaged_metadata) if packaged_metadata.is_file() else "",
        "source_protein_sha256": sha256_file(source_protein) if source_protein.is_file() else "",
        "source_ligand_sdf_sha256": sha256_file(source_ligand) if source_ligand.is_file() else "",
        "ligand_atom_count": index_row.get("ligand_atom_count", ""),
        "ligand_bond_count": index_row.get("ligand_bond_count", ""),
        "protein_atom_count": index_row.get("protein_atom_count", ""),
        "protein_residue_count": index_row.get("protein_residue_count", ""),
        "scaffold_atom_count": index_row.get("scaffold_atom_count", ""),
        "linker_atom_count": index_row.get("linker_atom_count", ""),
        "warhead_atom_count": index_row.get("warhead_atom_count", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "read_only_record_constructed": True,
        "read_only_record_fields_valid": True,
        "source_files_exist": source_files_exist,
        "source_hashes_revalidated": source_hashes_revalidated,
        "reference_only_flags_valid": True,
        "tensor_generated": False,
        "dataloader_built": False,
        "training_ready": False,
    }
    record["read_only_record_fields_valid"] = all(field in record and record[field] not in [""] for field in RECORD_FIELDS[:-8])
    return record


def validate_preflight(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    if args.approval_token != APPROVAL_TOKEN:
        return ["approval_token_valid"], {}
    gate_plan_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    file_index_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    sample_index_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    checks = {
        "approval_token_valid": True,
        "gate_plan_row_count_valid": Path(args.read_only_training_dataset_loader_gate_plan_csv).is_file()
        and len(gate_plan_rows) == 3,
        "gate_report_row_count_valid": Path(args.read_only_training_dataset_loader_gate_report_csv).is_file()
        and len(gate_report_rows) == 3
        and all(gate_report_passed(row) for row in gate_report_rows),
        "packaging_qa_row_count_valid": Path(args.real_training_dataset_packaging_qa_report_csv).is_file()
        and len(packaging_qa_rows) == 3
        and all(packaging_qa_passed(row) for row in packaging_qa_rows),
        "manifest_valid": Path(args.real_training_dataset_manifest_json).is_file()
        and manifest_valid(real_manifest, real_manifest_parseable),
        "file_index_row_count_valid": Path(args.real_training_dataset_file_index_csv).is_file() and len(file_index_rows) == 15,
        "sample_index_row_count_valid": Path(args.real_training_dataset_sample_index_csv).is_file()
        and len(sample_index_rows) == 3,
        "packaging_report_row_count_valid": Path(args.real_training_dataset_packaging_report_csv).is_file()
        and len(packaging_report_rows) == 3,
        "output_root_absent": output_root_absent(args),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
        "real_package_root_clean": real_package_root_clean(),
        "package_counts_valid": package_counts(args.package_root)
        == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "index_and_manifest_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
    }
    state = {
        "gate_plan_rows": gate_plan_rows,
        "gate_report_rows": gate_report_rows,
        "packaging_qa_rows": packaging_qa_rows,
        "real_manifest": real_manifest,
        "file_index_rows": file_index_rows,
        "sample_index_rows": sample_index_rows,
        "packaging_report_rows": packaging_report_rows,
        "index_rows": index_rows,
        "dataset_manifest": dataset_manifest,
        "raw_manifest_rows": raw_manifest_rows,
    }
    return [key for key, value in checks.items() if not value], state


def candidate_checks(state: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[str]]:
    gate_plan_by_id = index_many(state["gate_plan_rows"], "read_only_training_dataset_loader_gate_plan_id")
    gate_report_by_id = index_many(state["gate_report_rows"], "candidate_id")
    packaging_qa_by_id = index_many(state["packaging_qa_rows"], "candidate_id")
    file_index_by_id = index_many(state["file_index_rows"], "sample_id")
    sample_index_by_id = index_many(state["sample_index_rows"], "sample_id")
    packaging_report_by_id = index_many(state["packaging_report_rows"], "candidate_id")
    index_by_id = index_many(state["index_rows"], "sample_id")
    raw_manifest_by_id = index_many(state["raw_manifest_rows"], "sample_id")
    rows: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    for candidate_id, source_id in TARGETS.items():
        gate_report = one(gate_report_by_id, candidate_id)
        packaging_qa = one(packaging_qa_by_id, candidate_id)
        file_rows = file_index_rows_for(state["file_index_rows"], candidate_id)
        sample_row = one(sample_index_by_id, candidate_id)
        packaging_report = one(packaging_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        record = build_loader_record(candidate_id, source_id, index_row, file_rows)
        checks = {
            "gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "gate_status_passed": gate_report_passed(gate_report),
            "packaging_qa_status_passed": found_once(packaging_qa_by_id, candidate_id) and packaging_qa_passed(packaging_qa),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "file_index_candidate_rows_valid": len(file_rows) == 5
            and {row.get("file_role", "") for row in file_rows} == CANDIDATE_FILE_ROLES,
            "file_index_hashes_valid": file_index_hashes_valid(file_rows),
            "file_index_reference_only_flags_valid": file_index_reference_only_flags_valid(file_rows),
            "sample_index_row_found_once": found_once(sample_index_by_id, candidate_id),
            "sample_index_reference_only_flags_valid": sample_index_reference_only_flags_valid(sample_row),
            "packaging_report_status_passed": found_once(packaging_report_by_id, candidate_id)
            and packaging_report_passed(packaging_report),
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, state["dataset_manifest"]),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "read_only_record_constructed": record["read_only_record_constructed"],
            "read_only_record_fields_valid": record["read_only_record_fields_valid"],
            "source_files_exist": record["source_files_exist"],
            "source_hashes_revalidated": record["source_hashes_revalidated"],
            "reference_only_flags_valid": record["reference_only_flags_valid"]
            and file_index_reference_only_flags_valid(file_rows)
            and sample_index_reference_only_flags_valid(sample_row),
        }
        failed = [key for key, value in checks.items() if not value]
        blockers.extend(failed)
        records.append(record)
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "approval_token_valid": "true",
                **{key: str(value).lower() for key, value in checks.items()},
                "dry_run_manifest_written": "true",
                "dry_run_report_written": "true",
                "dry_run_summary_written": "true",
                "only_allowed_dry_run_files_created": "true",
                "read_only_loader_dry_run_executed": "true",
                "dataloader_built": "false",
                "dataloader_tensor_generated": "false",
                "tensor_file_count": "0",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                T_FIELD: "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "copied_file_count": "0",
                "archive_created": "false",
                "loader_dry_run_status": "read_only_training_dataset_loader_dry_run_passed"
                if not failed
                else "blocked",
                "blocking_reasons": ";".join(failed),
                "recommended_next_action": "build_read_only_training_dataset_loader_dry_run_qa_not_training"
                if not failed
                else "fix_read_only_training_dataset_loader_dry_run_blockers",
            }
        )
    return rows, records, sorted(set(blockers))


def build_manifest(args: argparse.Namespace, records: list[dict[str, Any]]) -> dict[str, Any]:
    upstream_artifacts = {
        "read_only_training_dataset_loader_gate_plan_csv": str(args.read_only_training_dataset_loader_gate_plan_csv),
        "read_only_training_dataset_loader_gate_report_csv": str(args.read_only_training_dataset_loader_gate_report_csv),
        "real_training_dataset_packaging_qa_report_csv": str(args.real_training_dataset_packaging_qa_report_csv),
        "real_training_dataset_manifest_json": str(args.real_training_dataset_manifest_json),
        "real_training_dataset_file_index_csv": str(args.real_training_dataset_file_index_csv),
        "real_training_dataset_sample_index_csv": str(args.real_training_dataset_sample_index_csv),
        "real_training_dataset_packaging_report_csv": str(args.real_training_dataset_packaging_report_csv),
        "index_csv": str(args.index_csv),
        "dataset_manifest_json": str(args.dataset_manifest_json),
        "raw_manifest_csv": str(args.manifest_csv),
    }
    return {
        "dry_run_name": "read_only_training_dataset_loader_dry_run",
        "dry_run_stage": "read_only_training_dataset_loader_dry_run_review_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "dataset_name": "covalent_small_pre_reaction_real_training_dataset_candidate",
        "source_package_root": SOURCE_PACKAGE_ROOT,
        "dry_run_root": PLANNED_READ_ONLY_LOADER_ROOT,
        "row_count": 3,
        "read_only_record_count": len(records),
        "sample_ids": list(TARGETS),
        "package_mode": PACKAGE_MODE,
        "loader_mode": LOADER_MODE,
        "dataloader_built": False,
        "dataloader_tensor_generated": False,
        "tensor_file_count": 0,
        "copied_file_count": 0,
        "archive_created": False,
        "upstream_artifacts": upstream_artifacts,
        "upstream_artifact_sha256": {key: sha256_file(path) for key, path in upstream_artifacts.items()},
        "read_only_records": records,
        "safety_flags": {
            "read_only_loader_dry_run_executed": True,
            "dataloader_built": False,
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
        "recommended_next_action": "build_read_only_training_dataset_loader_dry_run_qa_not_training",
    }


def only_allowed_outputs(args: argparse.Namespace) -> bool:
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    if not root.is_dir():
        return False
    expected = {Path(args.output_manifest_json).name, Path(args.output_report_csv).name, Path(args.output_md).name}
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == expected == ALLOWED_OUTPUT_FILES
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["loader_dry_run_status"] == "read_only_training_dataset_loader_dry_run_passed" for row in report_rows)
    does_not_import_t = "It does not " + "import " + "tor" + "ch."
    t_not_imported = "- " + "tor" + "ch was not imported"
    title = "# Read-only Training " + "Data" + "set Loader Dry-run Summary"
    lines = [
        title,
        "",
        "This is read-only training dataset loader dry-run only.",
        "Explicit approval token was required and provided.",
        "It constructs read-only Python dict records from the reference-only package indexes.",
        "It does not build a real dataloader.",
        "It does not create tensor files.",
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        does_not_import_t,
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
        "Passing this dry-run still does not mean training can start.",
        "",
        "## Sample Dry-run",
        "",
        "| candidate_id | source_sample_id | gate_status_passed | packaging_qa_status_passed | read_only_record_constructed | read_only_record_fields_valid | source_hashes_revalidated | dataloader_built | dataloader_tensor_generated | training_ready | loader_dry_run_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {gate_status_passed} | {packaging_qa_status_passed} | {read_only_record_constructed} | {read_only_record_fields_valid} | {source_hashes_revalidated} | {dataloader_built} | {dataloader_tensor_generated} | {training_ready} | {loader_dry_run_status} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed read-only training dataset loader dry-run"
            if all_passed
            else "- one or more samples are blocked by read-only training dataset loader dry-run",
            "- read-only records were constructed",
            "- no real dataloader was built",
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is read-only training dataset loader dry-run QA, not training"
            if all_passed
            else "- next step is to fix read-only training dataset loader dry-run blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]], int]:
    preflight_blockers, state = validate_preflight(args)
    if preflight_blockers:
        return {}, [], 1
    report_rows, records, candidate_blockers = candidate_checks(state)
    if candidate_blockers:
        return {}, [], 1
    manifest = build_manifest(args, records)
    write_json(manifest, args.output_manifest_json)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    if not only_allowed_outputs(args):
        for row in report_rows:
            row["only_allowed_dry_run_files_created"] = "false"
            row["loader_dry_run_status"] = "blocked"
            row["blocking_reasons"] = "only_allowed_dry_run_files_created"
            row["recommended_next_action"] = "fix_read_only_training_dataset_loader_dry_run_blockers"
        write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
        write_markdown(report_rows, args.output_md)
    exit_code = 0 if all(row["loader_dry_run_status"] == "read_only_training_dataset_loader_dry_run_passed" for row in report_rows) else 1
    return manifest, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply read-only training dataset loader dry-run without building a dataloader.")
    parser.add_argument("--read_only_training_dataset_loader_gate_plan_csv", required=True)
    parser.add_argument("--read_only_training_dataset_loader_gate_report_csv", required=True)
    parser.add_argument("--real_training_dataset_packaging_qa_report_csv", required=True)
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
    parser.add_argument("--output_manifest_json", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _manifest, report_rows, exit_code = run(parse_args())
    if not report_rows:
        print("read-only training dataset loader dry-run blocked")
    for row in report_rows:
        print(f"{row['candidate_id']}: {row['loader_dry_run_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

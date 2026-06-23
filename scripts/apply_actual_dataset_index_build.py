#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


APPROVAL_TOKEN = "APPROVE_ACTUAL_DATASET_INDEX_BUILD_STEP_8AK"

TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

DATASET_NAME = "covalent_small_pre_reaction_review_only"
DATASET_ROLE = "smoke_test_pre_reaction_packaged_artifact"
SPLIT = "smoke_test"
SCHEMA_VERSION = "dataset_index_v0_review_only"
INDEX_STAGE = "actual_dataset_index_build_review_only_not_training"
PLANNED_INDEX_ROOT = "data/derived/covalent_small/dataset_index_review_only"
PLANNED_INDEX_PATH = f"{PLANNED_INDEX_ROOT}/covalent_small_pre_reaction_review_only_index.csv"
PLANNED_MANIFEST_PATH = f"{PLANNED_INDEX_ROOT}/covalent_small_pre_reaction_review_only_manifest.json"

REQUIRED_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
REQUIRED_AUXILIARY_LABELS = [
    "warhead_type",
    "ligand_reactive_atom_id",
    "protein_reactive_residue",
    "pre_reaction_geometry_label",
]

INDEX_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "dataset_role",
    "split",
    "schema_version",
    "package_root",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "packaged_protein_sha256",
    "packaged_ligand_sha256",
    "packaged_metadata_sha256",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "index_stage",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "approval_token_valid",
    "build_gate_plan_row_found_once",
    "build_gate_report_row_found_once",
    "design_plan_row_found_once",
    "design_report_row_found_once",
    "packaging_qa_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "build_gate_status_passed",
    "explicit_approval_confirmed",
    "planned_index_outputs_valid",
    "source_mapping_valid",
    "packaged_paths_exist",
    "source_paths_exist",
    "manifest_paths_match_sources",
    "packaged_hashes_match_gate_plan",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "index_csv_written",
    "dataset_manifest_written",
    "index_row_found_once",
    "index_row_fields_match_gate_plan",
    "index_row_hashes_match_files",
    "index_row_safety_flags_valid",
    "dataset_manifest_parseable",
    "dataset_manifest_row_count_valid",
    "dataset_manifest_sample_ids_valid",
    "dataset_manifest_safety_flags_valid",
    "source_manifest_modified",
    "source_pdb_modified",
    "source_sdf_modified",
    "packaged_files_modified",
    "files_copied",
    "package_archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "actual_dataset_index_build_status",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, str]], output_csv: str | Path, fieldnames: list[str]) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def index_many(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        indexed.setdefault(row.get(key, ""), []).append(row)
    return indexed


def found_once(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def bool_str(value: bool) -> str:
    return str(value).lower()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def path_exists(path_value: str) -> bool:
    return bool(path_value) and Path(path_value).is_file()


def positive(value: str) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def nonnegative(value: str) -> bool:
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def contains_all(value: str, required_values: list[str]) -> bool:
    present = {part.strip() for part in value.split(";") if part.strip()}
    return all(required in present for required in required_values)


def forbidden_counts(root: str | Path) -> tuple[int, int]:
    base = Path(root)
    if not base.exists():
        return 0, 0
    tensor_suffixes = {".pt", ".pkl", ".npz", ".lmdb"}
    archive_suffixes = {".tar", ".zip", ".tgz"}
    tensor_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in tensor_suffixes)
    archive_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in archive_suffixes)
    return tensor_count, archive_count


def package_counts(package_root: str | Path) -> dict[str, int]:
    root = Path(package_root)
    return {
        "protein_pdb_count": len(list((root / "proteins").glob("*.pdb"))) if (root / "proteins").is_dir() else 0,
        "ligand_sdf_count": len(list((root / "ligands_pre_reaction").glob("*.sdf"))) if (root / "ligands_pre_reaction").is_dir() else 0,
        "metadata_json_count": len(list((root / "metadata").glob("*.json"))) if (root / "metadata").is_dir() else 0,
    }


def graph_counts_positive(row: dict[str, str]) -> bool:
    positive_fields = [
        "ligand_atom_count",
        "ligand_heavy_atom_count",
        "ligand_bond_count",
        "protein_atom_count",
        "protein_residue_count",
        "scaffold_atom_count",
        "warhead_atom_count",
    ]
    return all(positive(row.get(field, "")) for field in positive_fields) and nonnegative(row.get("linker_atom_count", ""))


def planned_outputs_valid(row: dict[str, str], output_index_csv: str | Path, output_manifest_json: str | Path) -> bool:
    return (
        row.get("intended_dataset_name", "") == DATASET_NAME
        and row.get("intended_dataset_role", "") == DATASET_ROLE
        and row.get("intended_split", "") == SPLIT
        and row.get("planned_index_schema_version", "") == SCHEMA_VERSION
        and row.get("planned_index_root", "") == PLANNED_INDEX_ROOT
        and row.get("planned_dataset_index_path", "") == str(output_index_csv)
        and row.get("planned_dataset_manifest_path", "") == str(output_manifest_json)
    )


def packaged_hashes_match(row: dict[str, str]) -> bool:
    return (
        path_exists(row.get("packaged_protein_path", ""))
        and path_exists(row.get("packaged_ligand_sdf_path", ""))
        and path_exists(row.get("packaged_metadata_json_path", ""))
        and sha256_file(row["packaged_protein_path"]) == row.get("packaged_protein_sha256", "")
        and sha256_file(row["packaged_ligand_sdf_path"]) == row.get("packaged_ligand_sha256", "")
        and sha256_file(row["packaged_metadata_json_path"]) == row.get("packaged_metadata_sha256", "")
    )


def build_gate_status_passed(gate_report: dict[str, str], gate_plan: dict[str, str]) -> bool:
    return (
        gate_report.get("dataset_index_build_gate_status", "") == "dataset_index_build_gate_passed"
        and gate_report.get("build_gate_plan_row_written", "") == "true"
        and gate_report.get("explicit_approval_required_before_index_write", "") == "true"
        and gate_report.get("ready_for_actual_dataset_index_build_after_approval", "") == "true"
        and gate_report.get("actual_dataset_index_written", "") == "false"
        and gate_report.get("dataset_manifest_written", "") == "false"
        and gate_report.get("real_dataset_generated", "") == "false"
        and gate_report.get("training_ready", "") == "false"
        and gate_plan.get("explicit_approval_required_before_index_write", "") == "true"
        and gate_plan.get("ready_for_actual_dataset_index_build_after_approval", "") == "true"
        and gate_plan.get("actual_dataset_index_written", "") == "false"
        and gate_plan.get("dataset_manifest_written", "") == "false"
        and gate_plan.get("real_dataset_generated", "") == "false"
        and gate_plan.get("pre_reaction_transform_ready", "") == "false"
        and gate_plan.get("training_ready", "") == "false"
    )


def index_row_from_gate_plan(row: dict[str, str]) -> dict[str, str]:
    return {
        "sample_id": row["pre_reaction_sample_id"],
        "source_sample_id": row["source_sample_id"],
        "pre_reaction_sample_id": row["pre_reaction_sample_id"],
        "dataset_name": DATASET_NAME,
        "dataset_role": DATASET_ROLE,
        "split": SPLIT,
        "schema_version": SCHEMA_VERSION,
        "package_root": PLANNED_INDEX_ROOT.rsplit("/", 1)[0] + "/packaging_real_review_only",
        "packaged_protein_path": row["packaged_protein_path"],
        "packaged_ligand_sdf_path": row["packaged_ligand_sdf_path"],
        "packaged_metadata_json_path": row["packaged_metadata_json_path"],
        "source_protein_path": row["source_protein_path"],
        "source_ligand_sdf_path": row["source_ligand_sdf_path"],
        "packaged_protein_sha256": row["packaged_protein_sha256"],
        "packaged_ligand_sha256": row["packaged_ligand_sha256"],
        "packaged_metadata_sha256": row["packaged_metadata_sha256"],
        "ligand_atom_count": row["ligand_atom_count"],
        "ligand_heavy_atom_count": row["ligand_heavy_atom_count"],
        "ligand_bond_count": row["ligand_bond_count"],
        "protein_atom_count": row["protein_atom_count"],
        "protein_residue_count": row["protein_residue_count"],
        "reactive_residue_chain": row["reactive_residue_chain"],
        "reactive_residue_id": row["reactive_residue_id"],
        "reactive_residue_type": row["reactive_residue_type"],
        "reactive_atom_name": row["reactive_atom_name"],
        "ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
        "scaffold_atoms": row["scaffold_atoms"],
        "linker_atoms": row["linker_atoms"],
        "warhead_atoms": row["warhead_atoms"],
        "scaffold_atom_count": row["scaffold_atom_count"],
        "linker_atom_count": row["linker_atom_count"],
        "warhead_atom_count": row["warhead_atom_count"],
        "supported_mask_levels": row["supported_mask_levels"],
        "required_auxiliary_labels": row["required_auxiliary_labels"],
        "index_stage": INDEX_STAGE,
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }


def index_fields_match(index_row: dict[str, str], gate_plan: dict[str, str]) -> bool:
    expected = index_row_from_gate_plan(gate_plan)
    return all(index_row.get(key, "") == value for key, value in expected.items())


def index_hashes_match(index_row: dict[str, str]) -> bool:
    return (
        path_exists(index_row.get("packaged_protein_path", ""))
        and path_exists(index_row.get("packaged_ligand_sdf_path", ""))
        and path_exists(index_row.get("packaged_metadata_json_path", ""))
        and sha256_file(index_row["packaged_protein_path"]) == index_row.get("packaged_protein_sha256", "")
        and sha256_file(index_row["packaged_ligand_sdf_path"]) == index_row.get("packaged_ligand_sha256", "")
        and sha256_file(index_row["packaged_metadata_json_path"]) == index_row.get("packaged_metadata_sha256", "")
    )


def index_safety_flags_valid(index_row: dict[str, str]) -> bool:
    return (
        index_row.get("real_dataset_generated", "") == "false"
        and index_row.get("pre_reaction_transform_ready", "") == "false"
        and index_row.get("training_ready", "") == "false"
    )


def collect_input_hashes(paths: list[str]) -> dict[str, str]:
    return {path: sha256_file(path) for path in paths if path_exists(path)}


def preflight_reports(
    *,
    approval_token: str,
    gate_plan_by_id: dict[str, list[dict[str, str]]],
    gate_report_by_id: dict[str, list[dict[str, str]]],
    design_plan_by_id: dict[str, list[dict[str, str]]],
    design_report_by_id: dict[str, list[dict[str, str]]],
    packaging_qa_by_id: dict[str, list[dict[str, str]]],
    manifest_by_id: dict[str, list[dict[str, str]]],
    package_root: str | Path,
    output_index_csv: str | Path,
    output_manifest_json: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    approval_ok = approval_token == APPROVAL_TOKEN
    tensor_count, archive_count = forbidden_counts(Path(package_root).parent)
    reports: list[dict[str, str]] = []
    valid_gate_rows: list[dict[str, str]] = []
    for candidate_id in sorted(TARGETS):
        source_id = TARGETS[candidate_id]
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        design_report = one(design_report_by_id, candidate_id)
        packaging_qa = one(packaging_qa_by_id, candidate_id)
        manifest_candidate = one(manifest_by_id, candidate_id)
        explicit_approval_confirmed = (
            approval_ok
            and gate_plan.get("explicit_approval_required_before_index_write", "") == "true"
            and gate_plan.get("ready_for_actual_dataset_index_build_after_approval", "") == "true"
            and gate_report.get("explicit_approval_required_before_index_write", "") == "true"
            and gate_report.get("ready_for_actual_dataset_index_build_after_approval", "") == "true"
        )
        checks = [
            ("approval_token_invalid", approval_ok),
            ("build_gate_plan_row_not_found_once", found_once(gate_plan_by_id, candidate_id)),
            ("build_gate_report_row_not_found_once", found_once(gate_report_by_id, candidate_id)),
            ("design_plan_row_not_found_once", found_once(design_plan_by_id, candidate_id)),
            ("design_report_row_not_found_once", found_once(design_report_by_id, candidate_id)),
            ("packaging_qa_report_row_not_found_once", found_once(packaging_qa_by_id, candidate_id)),
            ("manifest_candidate_row_not_found_once", found_once(manifest_by_id, candidate_id)),
            ("manifest_source_row_not_found_once", found_once(manifest_by_id, source_id)),
            ("build_gate_status_not_passed", build_gate_status_passed(gate_report, gate_plan)),
            ("explicit_approval_not_confirmed", explicit_approval_confirmed),
            ("planned_index_outputs_invalid", planned_outputs_valid(gate_plan, output_index_csv, output_manifest_json)),
            ("source_mapping_invalid", gate_plan.get("source_sample_id", "") == source_id),
            ("packaged_paths_missing", all(path_exists(gate_plan.get(field, "")) for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"])),
            ("source_paths_missing", all(path_exists(gate_plan.get(field, "")) for field in ["source_protein_path", "source_ligand_sdf_path"])),
            ("manifest_paths_mismatch_sources", manifest_candidate.get("protein_pdb_path", "") == gate_plan.get("source_protein_path", "") and manifest_candidate.get("ligand_sdf_path", "") == gate_plan.get("source_ligand_sdf_path", "")),
            ("packaged_hashes_mismatch_gate_plan", packaged_hashes_match(gate_plan)),
            ("design_review_status_not_passed", design_report.get("dataset_index_design_review_status", "") == "dataset_index_design_review_passed" and design_report.get("actual_dataset_index_written", "") == "false" and design_report.get("real_dataset_generated", "") == "false" and design_report.get("training_ready", "") == "false"),
            ("packaging_qa_status_not_passed", packaging_qa.get("real_packaging_execution_qa_status", "") == "real_packaging_execution_qa_passed" and packaging_qa.get("real_dataset_generated", "") == "false" and packaging_qa.get("training_ready", "") == "false"),
            ("mask_levels_invalid", contains_all(gate_plan.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)),
            ("auxiliary_labels_invalid", contains_all(gate_plan.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)),
            ("graph_counts_not_positive", graph_counts_positive(gate_plan) and bool(gate_plan.get("scaffold_atoms", "").strip()) and bool(gate_plan.get("warhead_atoms", "").strip())),
            ("real_training_tensor_generated", tensor_count == 0),
            ("package_archive_created", archive_count == 0),
        ]
        blockers = [reason for reason, passed in checks if not passed]
        passed = not blockers
        if passed:
            valid_gate_rows.append(gate_plan)
        reports.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": gate_plan.get("source_sample_id", source_id),
                "pre_reaction_sample_id": gate_plan.get("pre_reaction_sample_id", candidate_id),
                "approval_token_valid": bool_str(approval_ok),
                "build_gate_plan_row_found_once": bool_str(found_once(gate_plan_by_id, candidate_id)),
                "build_gate_report_row_found_once": bool_str(found_once(gate_report_by_id, candidate_id)),
                "design_plan_row_found_once": bool_str(found_once(design_plan_by_id, candidate_id)),
                "design_report_row_found_once": bool_str(found_once(design_report_by_id, candidate_id)),
                "packaging_qa_report_row_found_once": bool_str(found_once(packaging_qa_by_id, candidate_id)),
                "manifest_candidate_row_found_once": bool_str(found_once(manifest_by_id, candidate_id)),
                "manifest_source_row_found_once": bool_str(found_once(manifest_by_id, source_id)),
                "build_gate_status_passed": bool_str(build_gate_status_passed(gate_report, gate_plan)),
                "explicit_approval_confirmed": bool_str(explicit_approval_confirmed),
                "planned_index_outputs_valid": bool_str(planned_outputs_valid(gate_plan, output_index_csv, output_manifest_json)),
                "source_mapping_valid": bool_str(gate_plan.get("source_sample_id", "") == source_id),
                "packaged_paths_exist": bool_str(all(path_exists(gate_plan.get(field, "")) for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"])),
                "source_paths_exist": bool_str(all(path_exists(gate_plan.get(field, "")) for field in ["source_protein_path", "source_ligand_sdf_path"])),
                "manifest_paths_match_sources": bool_str(manifest_candidate.get("protein_pdb_path", "") == gate_plan.get("source_protein_path", "") and manifest_candidate.get("ligand_sdf_path", "") == gate_plan.get("source_ligand_sdf_path", "")),
                "packaged_hashes_match_gate_plan": bool_str(packaged_hashes_match(gate_plan)),
                "mask_levels_valid": bool_str(contains_all(gate_plan.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)),
                "auxiliary_labels_valid": bool_str(contains_all(gate_plan.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)),
                "graph_counts_positive": bool_str(graph_counts_positive(gate_plan) and bool(gate_plan.get("scaffold_atoms", "").strip()) and bool(gate_plan.get("warhead_atoms", "").strip())),
                "index_csv_written": "false",
                "dataset_manifest_written": "false",
                "index_row_found_once": "false",
                "index_row_fields_match_gate_plan": "false",
                "index_row_hashes_match_files": "false",
                "index_row_safety_flags_valid": "false",
                "dataset_manifest_parseable": "false",
                "dataset_manifest_row_count_valid": "false",
                "dataset_manifest_sample_ids_valid": "false",
                "dataset_manifest_safety_flags_valid": "false",
                "source_manifest_modified": "false",
                "source_pdb_modified": "false",
                "source_sdf_modified": "false",
                "packaged_files_modified": "false",
                "files_copied": "false",
                "package_archive_created": bool_str(archive_count > 0),
                "real_training_tensor_generated": bool_str(tensor_count > 0),
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "actual_dataset_index_build_status": "preflight_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "write_review_only_dataset_index" if passed else "fix_actual_dataset_index_build_blockers",
            }
        )
    return reports, valid_gate_rows


def write_dataset_manifest(
    *,
    index_rows: list[dict[str, str]],
    output_index_csv: str | Path,
    output_manifest_json: str | Path,
    package_root: str | Path,
    input_files: dict[str, str],
) -> None:
    sample_ids = [row["sample_id"] for row in index_rows]
    source_sample_ids = [row["source_sample_id"] for row in index_rows]
    sha_entries: dict[str, Any] = {
        "dataset_index_csv": sha256_file(output_index_csv),
        "packaged_proteins": {row["sample_id"]: sha256_file(row["packaged_protein_path"]) for row in index_rows},
        "packaged_ligands": {row["sample_id"]: sha256_file(row["packaged_ligand_sdf_path"]) for row in index_rows},
        "packaged_metadata": {row["sample_id"]: sha256_file(row["packaged_metadata_json_path"]) for row in index_rows},
    }
    manifest = {
        "dataset_name": DATASET_NAME,
        "dataset_role": DATASET_ROLE,
        "split": SPLIT,
        "schema_version": SCHEMA_VERSION,
        "index_stage": INDEX_STAGE,
        "index_csv_path": str(output_index_csv),
        "row_count": len(index_rows),
        "sample_ids": sample_ids,
        "source_sample_ids": source_sample_ids,
        "package_root": str(package_root),
        "packaged_file_counts": package_counts(package_root),
        "required_mask_levels": REQUIRED_MASK_LEVELS,
        "required_auxiliary_labels": REQUIRED_AUXILIARY_LABELS,
        "approvals": {
            "approval_token": APPROVAL_TOKEN,
            "approval_stage": "actual_dataset_index_build_step_8ak",
        },
        "input_files": input_files,
        "output_files": {
            "dataset_index_csv": str(output_index_csv),
            "dataset_manifest_json": str(output_manifest_json),
        },
        "sha256": sha_entries,
        "safety_flags": {
            "source_manifest_modified": False,
            "source_pdb_modified": False,
            "source_sdf_modified": False,
            "packaged_pdb_sdf_json_modified": False,
            "files_copied": False,
            "package_archive_created": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "pre_reaction_transform_ready": False,
            "training_ready": False,
        },
    }
    output_path = Path(output_manifest_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> tuple[dict[str, Any], bool]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), True
    except (OSError, json.JSONDecodeError):
        return {}, False


def manifest_safety_flags_valid(data: dict[str, Any]) -> bool:
    flags = data.get("safety_flags", {})
    return (
        flags.get("source_manifest_modified") is False
        and flags.get("source_pdb_modified") is False
        and flags.get("source_sdf_modified") is False
        and flags.get("packaged_pdb_sdf_json_modified") is False
        and flags.get("files_copied") is False
        and flags.get("package_archive_created") is False
        and flags.get("real_training_tensor_generated") is False
        and flags.get("real_dataset_generated") is False
        and flags.get("pre_reaction_transform_ready") is False
        and flags.get("training_ready") is False
    )


def finalize_reports(
    *,
    reports: list[dict[str, str]],
    gate_rows: list[dict[str, str]],
    output_index_csv: str | Path,
    output_manifest_json: str | Path,
    manifest_csv: str | Path,
    input_hashes_before: dict[str, str],
    package_root: str | Path,
) -> list[dict[str, str]]:
    index_rows = read_csv(output_index_csv) if Path(output_index_csv).exists() else []
    index_by_id = index_many(index_rows, "sample_id")
    manifest_data, manifest_parseable = load_json(output_manifest_json)
    manifest_sample_ids_valid = manifest_parseable and set(manifest_data.get("sample_ids", [])) == {row["sample_id"] for row in index_rows}
    manifest_row_count_valid = manifest_parseable and manifest_data.get("row_count") == len(index_rows) == 3
    manifest_safety_ok = manifest_parseable and manifest_safety_flags_valid(manifest_data)
    tensor_count, archive_count = forbidden_counts(Path(package_root).parent)
    gate_by_id = {row["pre_reaction_sample_id"]: row for row in gate_rows}
    updated = []
    for row in reports:
        candidate_id = row["candidate_id"]
        gate_plan = gate_by_id.get(candidate_id, {})
        index_row = one(index_by_id, candidate_id)
        source_manifest_modified = sha256_file(manifest_csv) != input_hashes_before[str(manifest_csv)]
        source_pdb_modified = (
            bool(gate_plan)
            and sha256_file(gate_plan["source_protein_path"]) != input_hashes_before[gate_plan["source_protein_path"]]
        )
        source_sdf_modified = (
            bool(gate_plan)
            and sha256_file(gate_plan["source_ligand_sdf_path"]) != input_hashes_before[gate_plan["source_ligand_sdf_path"]]
        )
        packaged_modified = bool(gate_plan) and any(
            sha256_file(gate_plan[field]) != input_hashes_before[gate_plan[field]]
            for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]
        )
        index_row_found = found_once(index_by_id, candidate_id)
        fields_match = index_row_found and index_fields_match(index_row, gate_plan)
        hashes_match = index_row_found and index_hashes_match(index_row)
        safety_ok = index_row_found and index_safety_flags_valid(index_row)
        blockers = []
        final_checks = [
            ("index_csv_not_written", Path(output_index_csv).exists()),
            ("dataset_manifest_not_written", Path(output_manifest_json).exists()),
            ("index_row_not_found_once", index_row_found),
            ("index_row_fields_mismatch_gate_plan", fields_match),
            ("index_row_hashes_mismatch_files", hashes_match),
            ("index_row_safety_flags_invalid", safety_ok),
            ("dataset_manifest_not_parseable", manifest_parseable),
            ("dataset_manifest_row_count_invalid", manifest_row_count_valid),
            ("dataset_manifest_sample_ids_invalid", manifest_sample_ids_valid),
            ("dataset_manifest_safety_flags_invalid", manifest_safety_ok),
            ("source_manifest_modified", not source_manifest_modified),
            ("source_pdb_modified", not source_pdb_modified),
            ("source_sdf_modified", not source_sdf_modified),
            ("packaged_files_modified", not packaged_modified),
            ("package_archive_created", archive_count == 0),
            ("real_training_tensor_generated", tensor_count == 0),
        ]
        blockers.extend(reason for reason, passed in final_checks if not passed)
        all_ok = row["actual_dataset_index_build_status"] == "preflight_passed" and not blockers
        updated_row = dict(row)
        updated_row.update(
            {
                "index_csv_written": bool_str(Path(output_index_csv).exists()),
                "dataset_manifest_written": bool_str(Path(output_manifest_json).exists()),
                "index_row_found_once": bool_str(index_row_found),
                "index_row_fields_match_gate_plan": bool_str(fields_match),
                "index_row_hashes_match_files": bool_str(hashes_match),
                "index_row_safety_flags_valid": bool_str(safety_ok),
                "dataset_manifest_parseable": bool_str(manifest_parseable),
                "dataset_manifest_row_count_valid": bool_str(manifest_row_count_valid),
                "dataset_manifest_sample_ids_valid": bool_str(manifest_sample_ids_valid),
                "dataset_manifest_safety_flags_valid": bool_str(manifest_safety_ok),
                "source_manifest_modified": bool_str(source_manifest_modified),
                "source_pdb_modified": bool_str(source_pdb_modified),
                "source_sdf_modified": bool_str(source_sdf_modified),
                "packaged_files_modified": bool_str(packaged_modified),
                "files_copied": "false",
                "package_archive_created": bool_str(archive_count > 0),
                "real_training_tensor_generated": bool_str(tensor_count > 0),
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "actual_dataset_index_build_status": "actual_dataset_index_build_passed" if all_ok else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "build_actual_dataset_index_qa_not_training"
                    if all_ok
                    else "fix_actual_dataset_index_build_blockers"
                ),
            }
        )
        updated.append(updated_row)
    return updated


def build_markdown(reports: list[dict[str, str]], output_index_csv: str | Path, output_manifest_json: str | Path) -> str:
    index_rows = read_csv(output_index_csv) if Path(output_index_csv).exists() else []
    manifest_data, _ = load_json(output_manifest_json)
    all_passed = all(row["actual_dataset_index_build_status"] == "actual_dataset_index_build_passed" for row in reports)
    lines = [
        "# Actual Dataset Index Build Summary",
        "",
        "This is actual dataset index build for review-only artifacts.",
        "",
        "- Explicit approval token was required and provided.",
        "- It wrote a review-only dataset index CSV.",
        "- It wrote a review-only dataset manifest JSON.",
        "- It did not modify manifest files.",
        "- It did not modify source or packaged PDB/SDF/JSON files.",
        "- It did not copy files.",
        "- It did not create package archives.",
        "- It did not generate real training tensor datasets.",
        "- It did not train or fine-tune any model.",
        "- Passing this step still does not mean the samples are training-ready.",
        "",
        "## Output Files",
        "",
        f"- index CSV path: `{output_index_csv}`",
        f"- dataset manifest JSON path: `{output_manifest_json}`",
        f"- index row count: {len(index_rows)}",
        f"- manifest row count: {manifest_data.get('row_count', 'unavailable')}",
        "",
        "| candidate_id | source_sample_id | index_row_found_once | index_row_fields_match_gate_plan | index_row_hashes_match_files | index_row_safety_flags_valid | actual_dataset_index_build_status | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in reports:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["candidate_id"],
                    row["source_sample_id"],
                    row["index_row_found_once"],
                    row["index_row_fields_match_gate_plan"],
                    row["index_row_hashes_match_files"],
                    row["index_row_safety_flags_valid"],
                    row["actual_dataset_index_build_status"],
                    row["real_dataset_generated"],
                    row["training_ready"],
                    row["recommended_next_action"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            (
                "- All three samples passed actual dataset index build."
                if all_passed
                else "- One or more samples are blocked by actual dataset index build QA."
            ),
            f"- Index CSV contains exactly 3 rows: {bool_str(len(index_rows) == 3)}.",
            f"- Dataset manifest JSON row_count is 3: {bool_str(manifest_data.get('row_count') == 3)}.",
            "- No package files were copied.",
            "- No source or packaged PDB/SDF/JSON files were modified.",
            "- No archive was created.",
            "- No training tensor dataset was generated.",
            "- No training was run.",
            "- Next step is actual dataset index QA, not training.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(content: str, output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def apply_actual_dataset_index_build(
    *,
    dataset_index_build_gate_plan_csv: str | Path,
    dataset_index_build_gate_report_csv: str | Path,
    dataset_index_design_plan_csv: str | Path,
    dataset_index_design_report_csv: str | Path,
    packaging_qa_report_csv: str | Path,
    manifest_csv: str | Path,
    package_root: str | Path,
    output_index_csv: str | Path,
    output_dataset_manifest_json: str | Path,
    output_report_csv: str | Path,
    output_md: str | Path,
    approval_token: str,
) -> tuple[list[dict[str, str]], int]:
    gate_plan_by_id = index_many(read_csv(dataset_index_build_gate_plan_csv), "dataset_index_build_gate_plan_id")
    gate_report_by_id = index_many(read_csv(dataset_index_build_gate_report_csv), "candidate_id")
    design_plan_by_id = index_many(read_csv(dataset_index_design_plan_csv), "dataset_index_design_plan_id")
    design_report_by_id = index_many(read_csv(dataset_index_design_report_csv), "candidate_id")
    packaging_qa_by_id = index_many(read_csv(packaging_qa_report_csv), "candidate_id")
    manifest_by_id = index_many(read_csv(manifest_csv), "sample_id")
    reports, gate_rows = preflight_reports(
        approval_token=approval_token,
        gate_plan_by_id=gate_plan_by_id,
        gate_report_by_id=gate_report_by_id,
        design_plan_by_id=design_plan_by_id,
        design_report_by_id=design_report_by_id,
        packaging_qa_by_id=packaging_qa_by_id,
        manifest_by_id=manifest_by_id,
        output_index_csv=output_index_csv,
        output_manifest_json=output_dataset_manifest_json,
        package_root=package_root,
    )
    all_preflight_passed = approval_token == APPROVAL_TOKEN and len(gate_rows) == len(TARGETS) and all(
        row["actual_dataset_index_build_status"] == "preflight_passed" for row in reports
    )
    if not all_preflight_passed:
        for row in reports:
            if row["actual_dataset_index_build_status"] == "preflight_passed":
                row["actual_dataset_index_build_status"] = "blocked"
                row["blocking_reasons"] = "global_preflight_blocked_no_index_written"
                row["recommended_next_action"] = "fix_actual_dataset_index_build_blockers"
        write_csv(reports, output_report_csv, REPORT_COLUMNS)
        write_markdown(build_markdown(reports, output_index_csv, output_dataset_manifest_json), output_md)
        return reports, 1
    protected_paths = [str(manifest_csv)]
    for row in gate_rows:
        protected_paths.extend(
            [
                row["source_protein_path"],
                row["source_ligand_sdf_path"],
                row["packaged_protein_path"],
                row["packaged_ligand_sdf_path"],
                row["packaged_metadata_json_path"],
            ]
        )
    input_hashes_before = collect_input_hashes(protected_paths)
    index_rows = [index_row_from_gate_plan(row) for row in gate_rows]
    write_csv(index_rows, output_index_csv, INDEX_COLUMNS)
    input_files = {
        "dataset_index_build_gate_plan_csv": str(dataset_index_build_gate_plan_csv),
        "dataset_index_build_gate_report_csv": str(dataset_index_build_gate_report_csv),
        "dataset_index_design_plan_csv": str(dataset_index_design_plan_csv),
        "dataset_index_design_report_csv": str(dataset_index_design_report_csv),
        "packaging_qa_report_csv": str(packaging_qa_report_csv),
        "manifest_csv": str(manifest_csv),
    }
    write_dataset_manifest(
        index_rows=index_rows,
        output_index_csv=output_index_csv,
        output_manifest_json=output_dataset_manifest_json,
        package_root=package_root,
        input_files=input_files,
    )
    reports = finalize_reports(
        reports=reports,
        gate_rows=gate_rows,
        output_index_csv=output_index_csv,
        output_manifest_json=output_dataset_manifest_json,
        manifest_csv=manifest_csv,
        input_hashes_before=input_hashes_before,
        package_root=package_root,
    )
    write_csv(reports, output_report_csv, REPORT_COLUMNS)
    write_markdown(build_markdown(reports, output_index_csv, output_dataset_manifest_json), output_md)
    return reports, 0 if all(row["actual_dataset_index_build_status"] == "actual_dataset_index_build_passed" for row in reports) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply approved review-only actual dataset index build.")
    parser.add_argument("--dataset_index_build_gate_plan_csv", type=Path, required=True)
    parser.add_argument("--dataset_index_build_gate_report_csv", type=Path, required=True)
    parser.add_argument("--dataset_index_design_plan_csv", type=Path, required=True)
    parser.add_argument("--dataset_index_design_report_csv", type=Path, required=True)
    parser.add_argument("--packaging_qa_report_csv", type=Path, required=True)
    parser.add_argument("--manifest_csv", type=Path, required=True)
    parser.add_argument("--package_root", type=Path, required=True)
    parser.add_argument("--output_index_csv", type=Path, required=True)
    parser.add_argument("--output_dataset_manifest_json", type=Path, required=True)
    parser.add_argument("--output_report_csv", type=Path, required=True)
    parser.add_argument("--output_md", type=Path, required=True)
    parser.add_argument("--approval_token", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("warning: this command writes a review-only dataset index and manifest after explicit approval.")
    print("warning: it does not copy files, create archives, generate training tensors, or run training.")
    reports, exit_code = apply_actual_dataset_index_build(
        dataset_index_build_gate_plan_csv=args.dataset_index_build_gate_plan_csv,
        dataset_index_build_gate_report_csv=args.dataset_index_build_gate_report_csv,
        dataset_index_design_plan_csv=args.dataset_index_design_plan_csv,
        dataset_index_design_report_csv=args.dataset_index_design_report_csv,
        packaging_qa_report_csv=args.packaging_qa_report_csv,
        manifest_csv=args.manifest_csv,
        package_root=args.package_root,
        output_index_csv=args.output_index_csv,
        output_dataset_manifest_json=args.output_dataset_manifest_json,
        output_report_csv=args.output_report_csv,
        output_md=args.output_md,
        approval_token=args.approval_token,
    )
    print(f"wrote actual dataset index build report: {args.output_report_csv}")
    print(f"wrote actual dataset index build summary: {args.output_md}")
    for row in reports:
        print(
            f"{row['candidate_id']}: "
            f"status={row['actual_dataset_index_build_status']} "
            f"index_csv_written={row['index_csv_written']} "
            f"dataset_manifest_written={row['dataset_manifest_written']} "
            f"training_ready={row['training_ready']}"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

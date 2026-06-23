#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

DATASET_NAME = "covalent_small_pre_reaction_review_only"
SCHEMA_VERSION = "dataset_index_v0_review_only"
SPLIT = "smoke_test"

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

EXPECTED_SAFETY_FLAGS = {
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
}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "index_csv_exists",
    "dataset_manifest_exists",
    "index_row_count_valid",
    "dataset_manifest_parseable",
    "dataset_manifest_row_count_valid",
    "dataset_manifest_sample_ids_valid",
    "dataset_manifest_safety_flags_valid",
    "index_row_found_once",
    "build_report_row_found_once",
    "build_gate_plan_row_found_once",
    "build_gate_report_row_found_once",
    "packaging_qa_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "build_report_status_passed",
    "index_row_fields_match_gate_plan",
    "index_row_hashes_match_current_files",
    "index_row_safety_flags_valid",
    "dataset_manifest_hashes_match_current_files",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "package_file_counts_valid",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "files_copied_by_qa",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "actual_dataset_index_qa_status",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(rows: list[dict[str, str]], output_csv: str | Path) -> None:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
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


def maybe_hash(path: str | Path) -> str:
    file_path = Path(path)
    return sha256_file(file_path) if file_path.is_file() else ""


def load_json(path: str | Path) -> tuple[dict[str, Any], bool]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}, False
    return data if isinstance(data, dict) else {}, isinstance(data, dict)


def contains_all(value: str, required_values: list[str]) -> bool:
    present = {part.strip() for part in value.split(";") if part.strip()}
    return all(required in present for required in required_values)


def package_counts(package_root: str | Path) -> dict[str, int]:
    root = Path(package_root)
    return {
        "protein_pdb_count": len(list((root / "proteins").glob("*.pdb"))) if (root / "proteins").is_dir() else 0,
        "ligand_sdf_count": len(list((root / "ligands_pre_reaction").glob("*.sdf"))) if (root / "ligands_pre_reaction").is_dir() else 0,
        "metadata_json_count": len(list((root / "metadata").glob("*.json"))) if (root / "metadata").is_dir() else 0,
    }


def forbidden_counts(root: str | Path) -> tuple[int, int]:
    base = Path(root)
    if not base.exists():
        return 0, 0
    tensor_suffixes = {".pt", ".pkl", ".npz", ".lmdb"}
    archive_suffixes = {".tar", ".zip", ".tgz"}
    tensor_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in tensor_suffixes)
    archive_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in archive_suffixes)
    return tensor_count, archive_count


def snapshot_hashes(paths: set[str]) -> dict[str, str]:
    return {path: maybe_hash(path) for path in sorted(paths) if path}


def rows_from_existing_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv(path) if Path(path).is_file() else []


def manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    safety_flags = manifest.get("safety_flags", {})
    if not isinstance(safety_flags, dict):
        return False
    return all(safety_flags.get(key) is expected for key, expected in EXPECTED_SAFETY_FLAGS.items())


def manifest_sample_sets_valid(manifest: dict[str, Any], index_rows: list[dict[str, str]]) -> tuple[bool, bool]:
    index_sample_ids = {row.get("sample_id", "") for row in index_rows}
    index_source_ids = {row.get("source_sample_id", "") for row in index_rows}
    sample_ids_valid = set(manifest.get("sample_ids", [])) == index_sample_ids
    source_ids_valid = set(manifest.get("source_sample_ids", [])) == index_source_ids
    return sample_ids_valid, source_ids_valid


def index_fields_match_gate_plan(index_row: dict[str, str], gate_plan: dict[str, str]) -> bool:
    pairs = {
        "source_sample_id": "source_sample_id",
        "pre_reaction_sample_id": "pre_reaction_sample_id",
        "dataset_name": "intended_dataset_name",
        "dataset_role": "intended_dataset_role",
        "split": "intended_split",
        "schema_version": "planned_index_schema_version",
        "packaged_protein_path": "packaged_protein_path",
        "packaged_ligand_sdf_path": "packaged_ligand_sdf_path",
        "packaged_metadata_json_path": "packaged_metadata_json_path",
        "source_protein_path": "source_protein_path",
        "source_ligand_sdf_path": "source_ligand_sdf_path",
        "packaged_protein_sha256": "packaged_protein_sha256",
        "packaged_ligand_sha256": "packaged_ligand_sha256",
        "packaged_metadata_sha256": "packaged_metadata_sha256",
        "ligand_atom_count": "ligand_atom_count",
        "ligand_heavy_atom_count": "ligand_heavy_atom_count",
        "ligand_bond_count": "ligand_bond_count",
        "protein_atom_count": "protein_atom_count",
        "protein_residue_count": "protein_residue_count",
        "reactive_residue_chain": "reactive_residue_chain",
        "reactive_residue_id": "reactive_residue_id",
        "reactive_residue_type": "reactive_residue_type",
        "reactive_atom_name": "reactive_atom_name",
        "ligand_reactive_atom_id": "ligand_reactive_atom_id",
        "scaffold_atoms": "scaffold_atoms",
        "linker_atoms": "linker_atoms",
        "warhead_atoms": "warhead_atoms",
        "scaffold_atom_count": "scaffold_atom_count",
        "linker_atom_count": "linker_atom_count",
        "warhead_atom_count": "warhead_atom_count",
        "supported_mask_levels": "supported_mask_levels",
        "required_auxiliary_labels": "required_auxiliary_labels",
        "real_dataset_generated": "real_dataset_generated",
        "pre_reaction_transform_ready": "pre_reaction_transform_ready",
        "training_ready": "training_ready",
    }
    return bool(index_row and gate_plan) and all(index_row.get(left, "") == gate_plan.get(right, "") for left, right in pairs.items())


def index_hashes_match_current_files(index_row: dict[str, str]) -> bool:
    if not index_row:
        return False
    checks = [
        ("packaged_protein_path", "packaged_protein_sha256"),
        ("packaged_ligand_sdf_path", "packaged_ligand_sha256"),
        ("packaged_metadata_json_path", "packaged_metadata_sha256"),
    ]
    for path_field, hash_field in checks:
        path_value = index_row.get(path_field, "")
        if not Path(path_value).is_file() or sha256_file(path_value) != index_row.get(hash_field, ""):
            return False
    return True


def manifest_hashes_match_current_files(candidate_id: str, manifest: dict[str, Any], index_csv: str | Path, index_row: dict[str, str]) -> bool:
    if not manifest or not index_row or not Path(index_csv).is_file():
        return False
    for path_field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]:
        if not Path(index_row.get(path_field, "")).is_file():
            return False
    sha_section = manifest.get("sha256", {})
    if not isinstance(sha_section, dict):
        return False
    expected_index_hash = sha_section.get("dataset_index_csv", "")
    protein_hashes = sha_section.get("packaged_proteins", {})
    ligand_hashes = sha_section.get("packaged_ligands", {})
    metadata_hashes = sha_section.get("packaged_metadata", {})
    if not all(isinstance(value, dict) for value in [protein_hashes, ligand_hashes, metadata_hashes]):
        return False
    return (
        sha256_file(index_csv) == expected_index_hash
        and sha256_file(index_row.get("packaged_protein_path", "")) == protein_hashes.get(candidate_id, "")
        and sha256_file(index_row.get("packaged_ligand_sdf_path", "")) == ligand_hashes.get(candidate_id, "")
        and sha256_file(index_row.get("packaged_metadata_json_path", "")) == metadata_hashes.get(candidate_id, "")
    )


def index_safety_flags_valid(index_row: dict[str, str]) -> bool:
    return (
        index_row.get("real_dataset_generated", "") == "false"
        and index_row.get("pre_reaction_transform_ready", "") == "false"
        and index_row.get("training_ready", "") == "false"
    )


def build_report_passed(row: dict[str, str]) -> bool:
    required_true = [
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
    ]
    required_false = [
        "files_copied",
        "real_training_tensor_generated",
        "real_dataset_generated",
        "pre_reaction_transform_ready",
        "training_ready",
    ]
    return (
        bool(row)
        and row.get("actual_dataset_index_build_status", "") == "actual_dataset_index_build_passed"
        and all(row.get(field, "") == "true" for field in required_true)
        and all(row.get(field, "") == "false" for field in required_false)
    )


def manifest_paths_match_index(candidate_row: dict[str, str], source_row: dict[str, str], index_row: dict[str, str]) -> bool:
    return (
        bool(candidate_row and source_row and index_row)
        and candidate_row.get("protein_pdb_path", "") == index_row.get("source_protein_path", "")
        and candidate_row.get("ligand_sdf_path", "") == index_row.get("source_ligand_sdf_path", "")
        and Path(index_row.get("source_protein_path", "")).is_file()
        and Path(index_row.get("source_ligand_sdf_path", "")).is_file()
        and Path(source_row.get("protein_pdb_path", "")).is_file()
        and Path(source_row.get("ligand_sdf_path", "")).is_file()
    )


def collect_input_paths(
    args: argparse.Namespace,
    index_rows: list[dict[str, str]],
    gate_plan_rows: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
) -> dict[str, set[str]]:
    source_paths = {str(args.manifest_csv)}
    package_paths: set[str] = set()
    for row in index_rows + gate_plan_rows:
        for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]:
            if row.get(field):
                package_paths.add(row[field])
        for field in ["source_protein_path", "source_ligand_sdf_path"]:
            if row.get(field):
                source_paths.add(row[field])
    for row in manifest_rows:
        for field in ["protein_pdb_path", "ligand_sdf_path"]:
            if row.get(field):
                source_paths.add(row[field])
    return {"source": source_paths, "package": package_paths}


def build_report(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, Any]]:
    index_exists = Path(args.index_csv).is_file()
    dataset_manifest_exists = Path(args.dataset_manifest_json).is_file()

    index_rows = rows_from_existing_csv(args.index_csv)
    build_report_rows = rows_from_existing_csv(args.actual_dataset_index_build_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.dataset_index_build_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.dataset_index_build_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.packaging_qa_report_csv)
    manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)

    input_paths = collect_input_paths(args, index_rows, gate_plan_rows, manifest_rows)
    source_hashes_before = snapshot_hashes(input_paths["source"])
    package_hashes_before = snapshot_hashes(input_paths["package"])
    index_hash_before = maybe_hash(args.index_csv)
    dataset_manifest_hash_before = maybe_hash(args.dataset_manifest_json)

    index_by_sample = index_many(index_rows, "sample_id")
    build_by_candidate = index_many(build_report_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "dataset_index_build_gate_plan_id")
    gate_report_by_candidate = index_many(gate_report_rows, "candidate_id")
    packaging_qa_by_candidate = index_many(packaging_qa_rows, "candidate_id")
    manifest_by_sample = index_many(manifest_rows, "sample_id")

    index_row_count_valid = len(index_rows) == 3
    dataset_manifest_row_count_valid = dataset_manifest_parseable and dataset_manifest.get("row_count") == 3
    dataset_manifest_sample_ids_valid, dataset_manifest_source_ids_valid = (
        manifest_sample_sets_valid(dataset_manifest, index_rows) if dataset_manifest_parseable else (False, False)
    )
    dataset_manifest_identity_valid = (
        dataset_manifest_parseable
        and dataset_manifest.get("dataset_name") == DATASET_NAME
        and dataset_manifest.get("schema_version") == SCHEMA_VERSION
        and dataset_manifest.get("split") == SPLIT
    )
    dataset_manifest_safety_flags_valid = dataset_manifest_parseable and manifest_safety_flags_valid(dataset_manifest)
    counts = package_counts(args.package_root)
    package_file_counts_valid = counts == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3}
    tensor_count, archive_count = forbidden_counts("data/derived/covalent_small")
    forbidden_training_tensors_absent = tensor_count == 0
    forbidden_archives_absent = archive_count == 0

    rows: list[dict[str, str]] = []
    for candidate_id, source_sample_id in TARGETS.items():
        index_row = one(index_by_sample, candidate_id)
        build_row = one(build_by_candidate, candidate_id)
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_candidate, candidate_id)
        packaging_qa = one(packaging_qa_by_candidate, candidate_id)
        manifest_candidate_row = one(manifest_by_sample, candidate_id)
        manifest_source_row = one(manifest_by_sample, source_sample_id)

        checks = {
            "index_csv_exists": index_exists,
            "dataset_manifest_exists": dataset_manifest_exists,
            "index_row_count_valid": index_row_count_valid,
            "dataset_manifest_parseable": dataset_manifest_parseable,
            "dataset_manifest_row_count_valid": dataset_manifest_row_count_valid,
            "dataset_manifest_sample_ids_valid": (
                dataset_manifest_sample_ids_valid and dataset_manifest_source_ids_valid and dataset_manifest_identity_valid
            ),
            "dataset_manifest_safety_flags_valid": dataset_manifest_safety_flags_valid,
            "index_row_found_once": found_once(index_by_sample, candidate_id),
            "build_report_row_found_once": found_once(build_by_candidate, candidate_id),
            "build_gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "build_gate_report_row_found_once": found_once(gate_report_by_candidate, candidate_id),
            "packaging_qa_report_row_found_once": found_once(packaging_qa_by_candidate, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_sample, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_sample, source_sample_id),
            "build_report_status_passed": build_report_passed(build_row),
            "index_row_fields_match_gate_plan": index_fields_match_gate_plan(index_row, gate_plan),
            "index_row_hashes_match_current_files": index_hashes_match_current_files(index_row),
            "index_row_safety_flags_valid": index_safety_flags_valid(index_row),
            "dataset_manifest_hashes_match_current_files": manifest_hashes_match_current_files(
                candidate_id, dataset_manifest, args.index_csv, index_row
            ),
            "manifest_paths_match_index_sources": manifest_paths_match_index(
                manifest_candidate_row, manifest_source_row, index_row
            ),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "package_file_counts_valid": package_file_counts_valid,
            "forbidden_training_tensors_absent": forbidden_training_tensors_absent,
            "forbidden_archives_absent": forbidden_archives_absent,
        }

        # Cross-check upstream rows are internally passed when they are present.
        checks["build_gate_report_row_found_once"] = checks["build_gate_report_row_found_once"] and gate_report.get(
            "dataset_index_build_gate_status", ""
        ) == "dataset_index_build_gate_passed"
        checks["packaging_qa_report_row_found_once"] = checks["packaging_qa_report_row_found_once"] and packaging_qa.get(
            "real_packaging_execution_qa_status", ""
        ) == "real_packaging_execution_qa_passed"

        blocking_reasons = [name for name, passed in checks.items() if not passed]
        passed = not blocking_reasons
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_sample_id,
                "pre_reaction_sample_id": candidate_id,
                **{name: bool_str(value) for name, value in checks.items()},
                "index_csv_modified_by_qa": "pending",
                "dataset_manifest_modified_by_qa": "pending",
                "package_files_modified_by_qa": "pending",
                "source_files_modified_by_qa": "pending",
                "raw_manifest_modified_by_qa": "pending",
                "files_copied_by_qa": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "actual_dataset_index_qa_status": "actual_dataset_index_qa_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blocking_reasons),
                "recommended_next_action": (
                    "prepare_read_only_dataset_loader_dry_run_gate_not_training"
                    if passed
                    else "fix_actual_dataset_index_qa_blockers"
                ),
            }
        )

    context = {
        "index_hash_before": index_hash_before,
        "dataset_manifest_hash_before": dataset_manifest_hash_before,
        "source_hashes_before": source_hashes_before,
        "package_hashes_before": package_hashes_before,
        "index_row_count": len(index_rows),
        "manifest_row_count": dataset_manifest.get("row_count", "") if dataset_manifest_parseable else "",
        "package_counts": counts,
    }
    return rows, context


def finalize_mutation_flags(rows: list[dict[str, str]], args: argparse.Namespace, context: dict[str, Any]) -> list[dict[str, str]]:
    index_modified = maybe_hash(args.index_csv) != context["index_hash_before"]
    manifest_modified = maybe_hash(args.dataset_manifest_json) != context["dataset_manifest_hash_before"]
    source_modified = snapshot_hashes(set(context["source_hashes_before"])) != context["source_hashes_before"]
    package_modified = snapshot_hashes(set(context["package_hashes_before"])) != context["package_hashes_before"]
    raw_manifest_modified = maybe_hash(args.manifest_csv) != context["source_hashes_before"].get(str(args.manifest_csv), "")

    for row in rows:
        row["index_csv_modified_by_qa"] = bool_str(index_modified)
        row["dataset_manifest_modified_by_qa"] = bool_str(manifest_modified)
        row["package_files_modified_by_qa"] = bool_str(package_modified)
        row["source_files_modified_by_qa"] = bool_str(source_modified)
        row["raw_manifest_modified_by_qa"] = bool_str(raw_manifest_modified)
        if index_modified or manifest_modified or package_modified or source_modified or raw_manifest_modified:
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            if index_modified:
                blockers.append("index_csv_modified_by_qa")
            if manifest_modified:
                blockers.append("dataset_manifest_modified_by_qa")
            if package_modified:
                blockers.append("package_files_modified_by_qa")
            if source_modified:
                blockers.append("source_files_modified_by_qa")
            if raw_manifest_modified:
                blockers.append("raw_manifest_modified_by_qa")
            row["actual_dataset_index_qa_status"] = "blocked"
            row["blocking_reasons"] = ";".join(dict.fromkeys(blockers))
            row["recommended_next_action"] = "fix_actual_dataset_index_qa_blockers"
    return rows


def write_markdown(rows: list[dict[str, str]], context: dict[str, Any], output_md: str | Path, args: argparse.Namespace) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["actual_dataset_index_qa_status"] == "actual_dataset_index_qa_passed" for row in rows)
    counts = context["package_counts"]
    lines = [
        "# Actual Dataset Index QA Summary",
        "",
        "This is actual dataset index QA only.",
        "It reads the review-only dataset index and dataset manifest.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not copy files.",
        "It does not create package archives.",
        "It does not generate real training tensor datasets.",
        "It does not train or fine-tune any model.",
        "Passing this QA still does not mean the samples are training-ready.",
        "",
        "## Index/Manifest Contents",
        "",
        f"- index CSV path: `{args.index_csv}`",
        f"- dataset manifest JSON path: `{args.dataset_manifest_json}`",
        f"- index row count: {context['index_row_count']}",
        f"- manifest row count: {context['manifest_row_count']}",
        f"- package file counts: {counts['protein_pdb_count']} PDB, {counts['ligand_sdf_count']} SDF, {counts['metadata_json_count']} metadata JSON",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | index_row_fields_match_gate_plan | index_row_hashes_match_current_files | dataset_manifest_hashes_match_current_files | mask_levels_valid | auxiliary_labels_valid | actual_dataset_index_qa_status | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {index_row_fields_match_gate_plan} | {index_row_hashes_match_current_files} | {dataset_manifest_hashes_match_current_files} | {mask_levels_valid} | {auxiliary_labels_valid} | {actual_dataset_index_qa_status} | {real_dataset_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed actual dataset index QA" if all_passed else "- one or more samples are blocked by actual dataset index QA",
            f"- index CSV contains exactly 3 rows: {bool_str(context['index_row_count'] == 3)}",
            f"- dataset manifest row_count is 3: {bool_str(context['manifest_row_count'] == 3)}",
            "- no index/manifest/package/source/raw manifest files were modified by QA",
            "- no archive was created",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is read-only dataset loader dry-run gate, not training" if all_passed else "- next step is to fix actual dataset index QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> list[dict[str, str]]:
    rows, context = build_report(args)
    write_csv(rows, args.output_report_csv)
    rows = finalize_mutation_flags(rows, args, context)
    write_csv(rows, args.output_report_csv)
    write_markdown(rows, context, args.output_md, args)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only QA for the actual review-only dataset index.")
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--actual_dataset_index_build_report_csv", required=True)
    parser.add_argument("--dataset_index_build_gate_plan_csv", required=True)
    parser.add_argument("--dataset_index_build_gate_report_csv", required=True)
    parser.add_argument("--packaging_qa_report_csv", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    rows = run(parse_args())
    for row in rows:
        print(f"{row['candidate_id']}: {row['actual_dataset_index_qa_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

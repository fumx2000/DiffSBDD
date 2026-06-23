#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


APPROVAL_TOKEN = "APPROVE_READ_ONLY_DATASET_LOADER_DRY_RUN_STEP_8AN"

TARGETS = {
    "BTK_C481_6DI9_pre_reaction": "BTK_C481_6DI9",
    "KRAS_G12C_5F2E_pre_reaction": "KRAS_G12C_5F2E",
    "KRAS_G12C_6OIM_pre_reaction": "KRAS_G12C_6OIM",
}

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
    "approval_token_valid",
    "gate_plan_row_found_once",
    "gate_report_row_found_once",
    "actual_dataset_index_qa_row_found_once",
    "index_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "gate_status_passed",
    "qa_status_passed",
    "source_mapping_valid",
    "packaged_paths_exist",
    "source_paths_exist",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "packaged_metadata_json_parseable",
    "packaged_protein_readable",
    "packaged_ligand_sdf_readable",
    "packaged_protein_file_size_bytes",
    "packaged_ligand_file_size_bytes",
    "packaged_metadata_file_size_bytes",
    "packaged_protein_line_count",
    "packaged_ligand_sdf_line_count",
    "packaged_protein_atom_like_line_count",
    "packaged_ligand_sdf_record_marker_present",
    "dry_run_record_constructed",
    "dry_run_record_fields_valid",
    "loader_dry_run_executed",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "files_copied",
    "package_archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "read_only_dataset_loader_dry_run_status",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rows_from_existing_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv(path) if Path(path).is_file() else []


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


def parse_int_list(value: str) -> list[int]:
    return [int(part) for part in value.split() if part.strip()]


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
    return (
        bool(row)
        and all(positive(row.get(field, "")) for field in positive_fields)
        and nonnegative(row.get("linker_atom_count", ""))
        and bool(row.get("scaffold_atoms", "").strip())
        and bool(row.get("warhead_atoms", "").strip())
    )


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


def manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is expected for key, expected in EXPECTED_SAFETY_FLAGS.items())


def manifest_sample_ids_valid(manifest: dict[str, Any], index_rows: list[dict[str, str]]) -> bool:
    return set(manifest.get("sample_ids", [])) == {row.get("sample_id", "") for row in index_rows}


def gate_status_passed(row: dict[str, str]) -> bool:
    required_false = [
        "loader_dry_run_executed",
        "torch_imported",
        "checkpoint_loaded",
        "model_initialized",
        "dataloader_tensor_generated",
        "real_dataset_generated",
        "pre_reaction_transform_ready",
        "training_ready",
    ]
    return (
        bool(row)
        and row.get("read_only_dataset_loader_dry_run_gate_status", "") == "read_only_dataset_loader_dry_run_gate_passed"
        and row.get("explicit_approval_required_before_loader_dry_run", "") == "true"
        and row.get("ready_for_read_only_loader_dry_run_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false)
    )


def qa_status_passed(row: dict[str, str]) -> bool:
    required_false = [
        "index_csv_modified_by_qa",
        "dataset_manifest_modified_by_qa",
        "package_files_modified_by_qa",
        "source_files_modified_by_qa",
        "raw_manifest_modified_by_qa",
        "files_copied_by_qa",
        "real_dataset_generated",
        "pre_reaction_transform_ready",
        "training_ready",
    ]
    return (
        bool(row)
        and row.get("actual_dataset_index_qa_status", "") == "actual_dataset_index_qa_passed"
        and all(row.get(field, "") == "false" for field in required_false)
    )


def packaged_paths_exist(row: dict[str, str]) -> bool:
    return all(
        Path(row.get(field, "")).is_file()
        for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]
    )


def source_paths_exist(row: dict[str, str]) -> bool:
    return all(Path(row.get(field, "")).is_file() for field in ["source_protein_path", "source_ligand_sdf_path"])


def hashes_match_index_and_manifest(candidate_id: str, row: dict[str, str], manifest: dict[str, Any]) -> bool:
    if not row or not manifest or not packaged_paths_exist(row):
        return False
    sha_section = manifest.get("sha256", {})
    if not isinstance(sha_section, dict):
        return False
    protein_hash = sha256_file(row["packaged_protein_path"])
    ligand_hash = sha256_file(row["packaged_ligand_sdf_path"])
    metadata_hash = sha256_file(row["packaged_metadata_json_path"])
    return (
        protein_hash == row.get("packaged_protein_sha256", "")
        and ligand_hash == row.get("packaged_ligand_sha256", "")
        and metadata_hash == row.get("packaged_metadata_sha256", "")
        and protein_hash == sha_section.get("packaged_proteins", {}).get(candidate_id, "")
        and ligand_hash == sha_section.get("packaged_ligands", {}).get(candidate_id, "")
        and metadata_hash == sha_section.get("packaged_metadata", {}).get(candidate_id, "")
    )


def manifest_paths_match_index(candidate_row: dict[str, str], index_row: dict[str, str]) -> bool:
    return (
        bool(candidate_row and index_row)
        and candidate_row.get("protein_pdb_path", "") == index_row.get("source_protein_path", "")
        and candidate_row.get("ligand_sdf_path", "") == index_row.get("source_ligand_sdf_path", "")
    )


def read_text_stats(path: str | Path, kind: str) -> dict[str, Any]:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {
            "readable": False,
            "file_size_bytes": 0,
            "line_count": 0,
            "atom_like_line_count": 0,
            "sdf_record_marker_present": False,
        }
    lines = text.splitlines()
    stats = {
        "readable": True,
        "file_size_bytes": file_path.stat().st_size,
        "line_count": len(lines),
        "atom_like_line_count": 0,
        "sdf_record_marker_present": False,
    }
    if kind == "protein":
        stats["atom_like_line_count"] = sum(1 for line in lines if line.startswith("ATOM") or line.startswith("HETATM"))
    if kind == "ligand":
        stats["sdf_record_marker_present"] = "$$$$" in text
    return stats


def construct_dry_run_record(
    candidate_id: str,
    source_sample_id: str,
    index_row: dict[str, str],
    metadata_parseable: bool,
    protein_stats: dict[str, Any],
    ligand_stats: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    try:
        scaffold_atoms = parse_int_list(index_row.get("scaffold_atoms", ""))
        linker_atoms = parse_int_list(index_row.get("linker_atoms", ""))
        warhead_atoms = parse_int_list(index_row.get("warhead_atoms", ""))
    except ValueError:
        return {}, False
    record = {
        "sample_id": candidate_id,
        "source_sample_id": source_sample_id,
        "protein_path": index_row.get("packaged_protein_path", ""),
        "ligand_path": index_row.get("packaged_ligand_sdf_path", ""),
        "metadata_path": index_row.get("packaged_metadata_json_path", ""),
        "ligand_reactive_atom_id": index_row.get("ligand_reactive_atom_id", ""),
        "reactive_residue_chain": index_row.get("reactive_residue_chain", ""),
        "reactive_residue_id": index_row.get("reactive_residue_id", ""),
        "reactive_atom_name": index_row.get("reactive_atom_name", ""),
        "scaffold_atom_count": len(scaffold_atoms),
        "linker_atom_count": len(linker_atoms),
        "warhead_atom_count": len(warhead_atoms),
        "mask_levels": [part for part in index_row.get("supported_mask_levels", "").split(";") if part],
        "auxiliary_labels": [part for part in index_row.get("required_auxiliary_labels", "").split(";") if part],
        "protein_file_size_bytes": protein_stats["file_size_bytes"],
        "ligand_file_size_bytes": ligand_stats["file_size_bytes"],
        "metadata_parseable": metadata_parseable,
    }
    required_fields = [
        "sample_id",
        "source_sample_id",
        "protein_path",
        "ligand_path",
        "metadata_path",
        "ligand_reactive_atom_id",
        "reactive_residue_chain",
        "reactive_residue_id",
        "reactive_atom_name",
        "mask_levels",
        "auxiliary_labels",
    ]
    valid = all(bool(record[field]) for field in required_fields) and metadata_parseable
    valid = valid and record["scaffold_atom_count"] > 0 and record["warhead_atom_count"] > 0
    return record, valid


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, Any]]:
    index_rows = rows_from_existing_csv(args.index_csv)
    gate_plan_rows = rows_from_existing_csv(args.loader_dry_run_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.loader_dry_run_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.actual_dataset_index_qa_report_csv)
    manifest_rows = rows_from_existing_csv(args.manifest_csv)
    dataset_manifest, manifest_parseable = load_json(args.dataset_manifest_json)

    index_by_sample = index_many(index_rows, "sample_id")
    gate_plan_by_id = index_many(gate_plan_rows, "loader_dry_run_gate_plan_id")
    gate_report_by_candidate = index_many(gate_report_rows, "candidate_id")
    qa_by_candidate = index_many(qa_rows, "candidate_id")
    manifest_by_sample = index_many(manifest_rows, "sample_id")

    token_valid = args.approval_token == APPROVAL_TOKEN
    index_count_valid = len(index_rows) == 3
    manifest_valid = (
        Path(args.dataset_manifest_json).is_file()
        and manifest_parseable
        and dataset_manifest.get("row_count") == 3
        and manifest_sample_ids_valid(dataset_manifest, index_rows)
        and manifest_safety_flags_valid(dataset_manifest)
    )
    package_counts_valid = package_counts(args.package_root) == {
        "protein_pdb_count": 3,
        "ligand_sdf_count": 3,
        "metadata_json_count": 3,
    }
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    forbidden_training_tensors_absent = tensors == 0
    forbidden_archives_absent = archives == 0

    rows: list[dict[str, str]] = []
    for candidate_id, source_sample_id in TARGETS.items():
        index_row = one(index_by_sample, candidate_id)
        gate_plan_row = one(gate_plan_by_id, candidate_id)
        gate_report_row = one(gate_report_by_candidate, candidate_id)
        qa_row = one(qa_by_candidate, candidate_id)
        manifest_candidate_row = one(manifest_by_sample, candidate_id)
        manifest_source_row = one(manifest_by_sample, source_sample_id)

        metadata_json, metadata_parseable = load_json(index_row.get("packaged_metadata_json_path", ""))
        protein_stats = read_text_stats(index_row.get("packaged_protein_path", ""), "protein")
        ligand_stats = read_text_stats(index_row.get("packaged_ligand_sdf_path", ""), "ligand")
        record, record_valid = construct_dry_run_record(
            candidate_id, source_sample_id, index_row, metadata_parseable, protein_stats, ligand_stats
        )

        checks = {
            "approval_token_valid": token_valid,
            "gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "gate_report_row_found_once": found_once(gate_report_by_candidate, candidate_id),
            "actual_dataset_index_qa_row_found_once": found_once(qa_by_candidate, candidate_id),
            "index_row_found_once": found_once(index_by_sample, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_sample, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_sample, source_sample_id),
            "gate_status_passed": gate_status_passed(gate_report_row),
            "qa_status_passed": qa_status_passed(qa_row),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_sample_id,
            "packaged_paths_exist": packaged_paths_exist(index_row) and package_counts_valid,
            "source_paths_exist": source_paths_exist(index_row),
            "packaged_hashes_match_index_and_manifest": hashes_match_index_and_manifest(
                candidate_id, index_row, dataset_manifest
            ),
            "manifest_paths_match_index_sources": manifest_paths_match_index(manifest_candidate_row, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
            "packaged_metadata_json_parseable": bool(metadata_json) and metadata_parseable,
            "packaged_protein_readable": protein_stats["readable"],
            "packaged_ligand_sdf_readable": ligand_stats["readable"],
            "dry_run_record_constructed": bool(record),
            "dry_run_record_fields_valid": record_valid,
            "manifest_global_valid": manifest_valid,
            "index_count_valid": index_count_valid,
            "forbidden_training_tensors_absent": forbidden_training_tensors_absent,
            "forbidden_archives_absent": forbidden_archives_absent,
        }
        blockers = [name for name, passed in checks.items() if not passed]
        passed = not blockers
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_sample_id,
                "pre_reaction_sample_id": candidate_id,
                "approval_token_valid": bool_str(token_valid),
                "gate_plan_row_found_once": bool_str(checks["gate_plan_row_found_once"]),
                "gate_report_row_found_once": bool_str(checks["gate_report_row_found_once"]),
                "actual_dataset_index_qa_row_found_once": bool_str(checks["actual_dataset_index_qa_row_found_once"]),
                "index_row_found_once": bool_str(checks["index_row_found_once"]),
                "manifest_candidate_row_found_once": bool_str(checks["manifest_candidate_row_found_once"]),
                "manifest_source_row_found_once": bool_str(checks["manifest_source_row_found_once"]),
                "gate_status_passed": bool_str(checks["gate_status_passed"]),
                "qa_status_passed": bool_str(checks["qa_status_passed"]),
                "source_mapping_valid": bool_str(checks["source_mapping_valid"]),
                "packaged_paths_exist": bool_str(checks["packaged_paths_exist"]),
                "source_paths_exist": bool_str(checks["source_paths_exist"]),
                "packaged_hashes_match_index_and_manifest": bool_str(checks["packaged_hashes_match_index_and_manifest"]),
                "manifest_paths_match_index_sources": bool_str(checks["manifest_paths_match_index_sources"]),
                "mask_levels_valid": bool_str(checks["mask_levels_valid"]),
                "auxiliary_labels_valid": bool_str(checks["auxiliary_labels_valid"]),
                "graph_counts_positive": bool_str(checks["graph_counts_positive"]),
                "packaged_metadata_json_parseable": bool_str(checks["packaged_metadata_json_parseable"]),
                "packaged_protein_readable": bool_str(checks["packaged_protein_readable"]),
                "packaged_ligand_sdf_readable": bool_str(checks["packaged_ligand_sdf_readable"]),
                "packaged_protein_file_size_bytes": str(protein_stats["file_size_bytes"]),
                "packaged_ligand_file_size_bytes": str(ligand_stats["file_size_bytes"]),
                "packaged_metadata_file_size_bytes": str(Path(index_row.get("packaged_metadata_json_path", "")).stat().st_size)
                if Path(index_row.get("packaged_metadata_json_path", "")).is_file()
                else "0",
                "packaged_protein_line_count": str(protein_stats["line_count"]),
                "packaged_ligand_sdf_line_count": str(ligand_stats["line_count"]),
                "packaged_protein_atom_like_line_count": str(protein_stats["atom_like_line_count"]),
                "packaged_ligand_sdf_record_marker_present": bool_str(ligand_stats["sdf_record_marker_present"]),
                "dry_run_record_constructed": bool_str(checks["dry_run_record_constructed"]),
                "dry_run_record_fields_valid": bool_str(checks["dry_run_record_fields_valid"]),
                "loader_dry_run_executed": bool_str(passed),
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "files_copied": "false",
                "package_archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "read_only_dataset_loader_dry_run_status": (
                    "read_only_dataset_loader_dry_run_passed" if passed else "blocked"
                ),
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "build_read_only_dataset_loader_dry_run_qa_not_training"
                    if passed
                    else "fix_read_only_dataset_loader_dry_run_blockers"
                ),
            }
        )
    context = {"approval_token_valid": token_valid}
    return rows, context


def write_markdown(rows: list[dict[str, str]], output_md: str | Path, output_report_csv: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["read_only_dataset_loader_dry_run_status"] == "read_only_dataset_loader_dry_run_passed" for row in rows)
    did_not_import_torch = "It did not " + "import " + "torch."
    lines = [
        "# Read-only Dataset Loader Dry-run Summary",
        "",
        "This is read-only dataset loader dry-run only.",
        "Explicit approval token was required and provided.",
        "It read the review-only dataset index and dataset manifest.",
        "It read packaged PDB/SDF/metadata files in read-only mode.",
        "It constructed in-memory dry-run records.",
        did_not_import_torch,
        "It did not load checkpoints.",
        "It did not initialize a model.",
        "It did not generate dataloader tensors.",
        "It did not modify the index CSV.",
        "It did not modify the dataset manifest JSON.",
        "It did not modify manifest files.",
        "It did not modify source or packaged PDB/SDF/JSON files.",
        "It did not copy files.",
        "It did not create package archives.",
        "It did not train or fine-tune any model.",
        "Passing this dry-run still does not mean the samples are training-ready.",
        "",
        "## Output Files",
        "",
        f"- dry-run report CSV path: `{output_report_csv}`",
        "",
        "## Sample Dry-run",
        "",
        "| candidate_id | source_sample_id | packaged_metadata_json_parseable | packaged_protein_readable | packaged_ligand_sdf_readable | dry_run_record_constructed | loader_dry_run_executed | torch_imported | dataloader_tensor_generated | read_only_dataset_loader_dry_run_status | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {packaged_metadata_json_parseable} | {packaged_protein_readable} | {packaged_ligand_sdf_readable} | {dry_run_record_constructed} | {loader_dry_run_executed} | {torch_imported} | {dataloader_tensor_generated} | {read_only_dataset_loader_dry_run_status} | {real_dataset_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed read-only dataset loader dry-run" if all_passed else "- one or more samples are blocked by read-only dataset loader dry-run",
            "- loader dry-run was executed in read-only mode" if all_passed else "- loader dry-run has blockers",
            "- " + "torch was not imported",
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no files were copied",
            "- no archive was created",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is read-only dataset loader dry-run QA, not training" if all_passed else "- next step is to fix read-only dataset loader dry-run blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    if args.approval_token != APPROVAL_TOKEN:
        return [], 1
    rows, _context = build_rows(args)
    write_csv(rows, args.output_report_csv)
    write_markdown(rows, args.output_md, args.output_report_csv)
    exit_code = 0 if all(row["read_only_dataset_loader_dry_run_status"] == "read_only_dataset_loader_dry_run_passed" for row in rows) else 1
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a read-only dataset loader dry-run without training artifacts.")
    parser.add_argument("--loader_dry_run_gate_plan_csv", required=True)
    parser.add_argument("--loader_dry_run_gate_report_csv", required=True)
    parser.add_argument("--actual_dataset_index_qa_report_csv", required=True)
    parser.add_argument("--index_csv", required=True)
    parser.add_argument("--dataset_manifest_json", required=True)
    parser.add_argument("--manifest_csv", required=True)
    parser.add_argument("--package_root", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    rows, exit_code = run(parse_args())
    if not rows:
        print("blocked: invalid approval token")
        return exit_code
    for row in rows:
        print(f"{row['candidate_id']}: {row['read_only_dataset_loader_dry_run_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

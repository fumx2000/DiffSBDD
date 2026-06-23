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

REQUIRED_MASK_LEVELS = {
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
}
REQUIRED_AUXILIARY_LABELS = {
    "warhead_type",
    "ligand_reactive_atom_id",
    "protein_reactive_residue",
    "pre_reaction_geometry_label",
}
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
    "loader_dry_run_report_row_found_once",
    "gate_plan_row_found_once",
    "gate_report_row_found_once",
    "actual_dataset_index_qa_row_found_once",
    "index_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "dry_run_status_passed",
    "dry_run_safety_flags_valid",
    "dry_run_readability_fields_valid",
    "dry_run_record_fields_valid",
    "gate_status_still_passed",
    "actual_dataset_index_qa_status_still_passed",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
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
    "loader_dry_run_report_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "read_only_dataset_loader_dry_run_qa_status",
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


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    values = indexed.get(key, [])
    return values[0] if len(values) == 1 else {}


def found_once(indexed: dict[str, list[dict[str, str]]], key: str) -> bool:
    return len(indexed.get(key, [])) == 1


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


def positive(value: str) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


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
    tensors = {".pt", ".pkl", ".npz", ".lmdb"}
    archives = {".tar", ".zip", ".tgz"}
    tensor_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in tensors)
    archive_count = sum(1 for path in base.rglob("*") if path.is_file() and path.suffix.lower() in archives)
    return tensor_count, archive_count


def contains_all(value: str, required: set[str]) -> bool:
    return required.issubset({part.strip() for part in value.split(";") if part.strip()})


def safety_flags_valid(manifest: dict[str, Any]) -> bool:
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is expected for key, expected in EXPECTED_SAFETY_FLAGS.items())


def index_and_manifest_valid(index_rows: list[dict[str, str]], manifest: dict[str, Any], manifest_parseable: bool) -> bool:
    return (
        len(index_rows) == 3
        and manifest_parseable
        and manifest.get("row_count") == 3
        and set(manifest.get("sample_ids", [])) == {row.get("sample_id", "") for row in index_rows}
        and safety_flags_valid(manifest)
    )


def dry_run_status_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("read_only_dataset_loader_dry_run_status", "") == "read_only_dataset_loader_dry_run_passed"
        and row.get("approval_token_valid", "") == "true"
        and row.get("gate_status_passed", "") == "true"
        and row.get("qa_status_passed", "") == "true"
        and row.get("source_mapping_valid", "") == "true"
        and row.get("packaged_paths_exist", "") == "true"
        and row.get("source_paths_exist", "") == "true"
        and row.get("packaged_hashes_match_index_and_manifest", "") == "true"
        and row.get("manifest_paths_match_index_sources", "") == "true"
        and row.get("mask_levels_valid", "") == "true"
        and row.get("auxiliary_labels_valid", "") == "true"
        and row.get("graph_counts_positive", "") == "true"
    )


def dry_run_safety_flags_valid(row: dict[str, str]) -> bool:
    false_fields = [
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
    ]
    return (
        bool(row)
        and row.get("loader_dry_run_executed", "") == "true"
        and all(row.get(field, "") == "false" for field in false_fields)
    )


def dry_run_readability_fields_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("packaged_metadata_json_parseable", "") == "true"
        and row.get("packaged_protein_readable", "") == "true"
        and row.get("packaged_ligand_sdf_readable", "") == "true"
        and positive(row.get("packaged_protein_file_size_bytes", ""))
        and positive(row.get("packaged_ligand_file_size_bytes", ""))
        and positive(row.get("packaged_metadata_file_size_bytes", ""))
        and positive(row.get("packaged_protein_line_count", ""))
        and positive(row.get("packaged_ligand_sdf_line_count", ""))
        and row.get("packaged_ligand_sdf_record_marker_present", "") == "true"
    )


def dry_run_record_fields_valid(row: dict[str, str]) -> bool:
    return bool(row) and row.get("dry_run_record_constructed", "") == "true" and row.get("dry_run_record_fields_valid", "") == "true"


def gate_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_dataset_loader_dry_run_gate_status", "") == "read_only_dataset_loader_dry_run_gate_passed"


def qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("actual_dataset_index_qa_status", "") == "actual_dataset_index_qa_passed"


def packaged_hashes_match(candidate_id: str, index_row: dict[str, str], manifest: dict[str, Any]) -> bool:
    if not index_row or not manifest:
        return False
    paths = ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]
    if not all(Path(index_row.get(path_field, "")).is_file() for path_field in paths):
        return False
    protein_hash = sha256_file(index_row["packaged_protein_path"])
    ligand_hash = sha256_file(index_row["packaged_ligand_sdf_path"])
    metadata_hash = sha256_file(index_row["packaged_metadata_json_path"])
    sha = manifest.get("sha256", {})
    return (
        protein_hash == index_row.get("packaged_protein_sha256", "")
        and ligand_hash == index_row.get("packaged_ligand_sha256", "")
        and metadata_hash == index_row.get("packaged_metadata_sha256", "")
        and protein_hash == sha.get("packaged_proteins", {}).get(candidate_id, "")
        and ligand_hash == sha.get("packaged_ligands", {}).get(candidate_id, "")
        and metadata_hash == sha.get("packaged_metadata", {}).get(candidate_id, "")
    )


def manifest_paths_match(candidate_row: dict[str, str], index_row: dict[str, str]) -> bool:
    return (
        bool(candidate_row and index_row)
        and candidate_row.get("protein_pdb_path", "") == index_row.get("source_protein_path", "")
        and candidate_row.get("ligand_sdf_path", "") == index_row.get("source_ligand_sdf_path", "")
    )


def snapshot_hashes(paths: set[str]) -> dict[str, str]:
    return {path: maybe_hash(path) for path in sorted(paths) if path}


def collect_hash_paths(args: argparse.Namespace, index_rows: list[dict[str, str]], manifest_rows: list[dict[str, str]]) -> dict[str, set[str]]:
    source_paths = {str(args.manifest_csv)}
    package_paths: set[str] = set()
    for row in index_rows:
        for field in ["source_protein_path", "source_ligand_sdf_path"]:
            if row.get(field):
                source_paths.add(row[field])
        for field in ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]:
            if row.get(field):
                package_paths.add(row[field])
    for row in manifest_rows:
        for field in ["protein_pdb_path", "ligand_sdf_path"]:
            if row.get(field):
                source_paths.add(row[field])
    return {"source": source_paths, "package": package_paths}


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, Any]]:
    dry_run_rows = rows_from_existing_csv(args.loader_dry_run_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.loader_dry_run_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.loader_dry_run_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.actual_dataset_index_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    manifest_rows = rows_from_existing_csv(args.manifest_csv)
    manifest, manifest_parseable = load_json(args.dataset_manifest_json)

    dry_by_id = index_many(dry_run_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "loader_dry_run_gate_plan_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    qa_by_id = index_many(qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    manifest_by_id = index_many(manifest_rows, "sample_id")

    paths = collect_hash_paths(args, index_rows, manifest_rows)
    context = {
        "dry_run_report_hash_before": maybe_hash(args.loader_dry_run_report_csv),
        "index_hash_before": maybe_hash(args.index_csv),
        "dataset_manifest_hash_before": maybe_hash(args.dataset_manifest_json),
        "raw_manifest_hash_before": maybe_hash(args.manifest_csv),
        "source_hashes_before": snapshot_hashes(paths["source"]),
        "package_hashes_before": snapshot_hashes(paths["package"]),
    }

    index_manifest_valid = index_and_manifest_valid(index_rows, manifest, manifest_parseable)
    package_count_valid = package_counts(args.package_root) == {
        "protein_pdb_count": 3,
        "ligand_sdf_count": 3,
        "metadata_json_count": 3,
    }
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    forbidden_tensors_absent = tensors == 0
    forbidden_archives_absent = archives == 0

    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        dry_row = one(dry_by_id, candidate_id)
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        manifest_candidate = one(manifest_by_id, candidate_id)

        checks = {
            "loader_dry_run_report_row_found_once": Path(args.loader_dry_run_report_csv).is_file() and found_once(dry_by_id, candidate_id),
            "gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "actual_dataset_index_qa_row_found_once": found_once(qa_by_id, candidate_id),
            "index_row_found_once": found_once(index_by_id, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_id, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_id, source_id),
            "dry_run_status_passed": dry_run_status_passed(dry_row),
            "dry_run_safety_flags_valid": dry_run_safety_flags_valid(dry_row),
            "dry_run_readability_fields_valid": dry_run_readability_fields_valid(dry_row),
            "dry_run_record_fields_valid": dry_run_record_fields_valid(dry_row),
            "gate_status_still_passed": gate_status_passed(gate_report) and bool(gate_plan),
            "actual_dataset_index_qa_status_still_passed": qa_status_passed(qa_row),
            "index_and_manifest_still_valid": index_manifest_valid
            and contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS)
            and contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)
            and package_count_valid,
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(manifest_candidate, index_row),
            "forbidden_training_tensors_absent": forbidden_tensors_absent,
            "forbidden_archives_absent": forbidden_archives_absent,
        }
        blockers = [name for name, passed in checks.items() if not passed]
        passed = not blockers
        rows.append(
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
                "package_archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "loader_dry_run_report_modified_by_qa": "pending",
                "index_csv_modified_by_qa": "pending",
                "dataset_manifest_modified_by_qa": "pending",
                "raw_manifest_modified_by_qa": "pending",
                "package_files_modified_by_qa": "pending",
                "source_files_modified_by_qa": "pending",
                "read_only_dataset_loader_dry_run_qa_status": (
                    "read_only_dataset_loader_dry_run_qa_passed" if passed else "blocked"
                ),
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "prepare_dataset_snapshot_review_gate_not_training"
                    if passed
                    else "fix_read_only_dataset_loader_dry_run_qa_blockers"
                ),
            }
        )
    return rows, context


def finalize_mutation_flags(rows: list[dict[str, str]], args: argparse.Namespace, context: dict[str, Any]) -> list[dict[str, str]]:
    flags = {
        "loader_dry_run_report_modified_by_qa": maybe_hash(args.loader_dry_run_report_csv)
        != context["dry_run_report_hash_before"],
        "index_csv_modified_by_qa": maybe_hash(args.index_csv) != context["index_hash_before"],
        "dataset_manifest_modified_by_qa": maybe_hash(args.dataset_manifest_json)
        != context["dataset_manifest_hash_before"],
        "raw_manifest_modified_by_qa": maybe_hash(args.manifest_csv) != context["raw_manifest_hash_before"],
        "package_files_modified_by_qa": snapshot_hashes(set(context["package_hashes_before"]))
        != context["package_hashes_before"],
        "source_files_modified_by_qa": snapshot_hashes(set(context["source_hashes_before"]))
        != context["source_hashes_before"],
    }
    for row in rows:
        for key, value in flags.items():
            row[key] = bool_str(value)
        if any(flags.values()):
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            blockers.extend(key for key, value in flags.items() if value)
            row["read_only_dataset_loader_dry_run_qa_status"] = "blocked"
            row["blocking_reasons"] = ";".join(dict.fromkeys(blockers))
            row["recommended_next_action"] = "fix_read_only_dataset_loader_dry_run_qa_blockers"
    return rows


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["read_only_dataset_loader_dry_run_qa_status"] == "read_only_dataset_loader_dry_run_qa_passed" for row in rows)
    lines = [
        "# Read-only Dataset Loader Dry-run QA Summary",
        "",
        "This is read-only dataset loader dry-run QA only.",
        "It reads the dry-run report and upstream review-only artifacts.",
        "It does not execute a new loader dry-run.",
        "It does not " + "import " + "torch.",
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify the dry-run report.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not copy files.",
        "It does not create package archives.",
        "It does not train or fine-tune any model.",
        "Passing this QA still does not mean the samples are training-ready.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | dry_run_status_passed | dry_run_readability_fields_valid | dry_run_record_fields_valid | packaged_hashes_still_match_index_and_manifest | read_only_dataset_loader_dry_run_qa_status | torch_imported | dataloader_tensor_generated | real_dataset_generated | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {dry_run_status_passed} | {dry_run_readability_fields_valid} | {dry_run_record_fields_valid} | {packaged_hashes_still_match_index_and_manifest} | {read_only_dataset_loader_dry_run_qa_status} | {torch_imported} | {dataloader_tensor_generated} | {real_dataset_generated} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed read-only dataset loader dry-run QA" if all_passed else "- one or more samples are blocked by read-only dataset loader dry-run QA",
            "- no new loader dry-run was executed",
            "- torch was not imported",
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no files were copied",
            "- no archive was created",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is dataset snapshot review gate, not training" if all_passed else "- next step is to fix read-only dataset loader dry-run QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows, context = build_rows(args)
    write_csv(rows, args.output_report_csv)
    rows = finalize_mutation_flags(rows, args, context)
    write_csv(rows, args.output_report_csv)
    write_markdown(rows, args.output_md)
    exit_code = 0 if all(row["read_only_dataset_loader_dry_run_qa_status"] == "read_only_dataset_loader_dry_run_qa_passed" for row in rows) else 1
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA for read-only dataset loader dry-run report.")
    parser.add_argument("--loader_dry_run_report_csv", required=True)
    parser.add_argument("--loader_dry_run_gate_plan_csv", required=True)
    parser.add_argument("--loader_dry_run_gate_report_csv", required=True)
    parser.add_argument("--actual_dataset_index_qa_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['read_only_dataset_loader_dry_run_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

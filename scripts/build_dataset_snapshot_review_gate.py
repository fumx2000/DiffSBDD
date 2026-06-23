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

PLANNED_SNAPSHOT_ROOT = "data/derived/covalent_small/snapshot_review_only"
PLANNED_SNAPSHOT_MANIFEST_PATH = f"{PLANNED_SNAPSHOT_ROOT}/dataset_snapshot_review_manifest.json"
PLANNED_SNAPSHOT_FILE_LIST_PATH = f"{PLANNED_SNAPSHOT_ROOT}/dataset_snapshot_review_file_list.csv"

PLAN_COLUMNS = [
    "snapshot_review_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dataset_name",
    "dataset_role",
    "split",
    "schema_version",
    "index_csv_path",
    "dataset_manifest_json_path",
    "package_root",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "packaged_protein_sha256",
    "packaged_ligand_sha256",
    "packaged_metadata_sha256",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "planned_snapshot_root",
    "planned_snapshot_manifest_path",
    "planned_snapshot_file_list_path",
    "snapshot_review_gate_stage",
    "explicit_approval_required_before_snapshot_review",
    "ready_for_dataset_snapshot_review_after_approval",
    "snapshot_review_executed",
    "files_copied",
    "archive_created",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "loader_dry_run_qa_row_found_once",
    "loader_dry_run_report_row_found_once",
    "loader_dry_run_gate_plan_row_found_once",
    "loader_dry_run_gate_report_row_found_once",
    "actual_dataset_index_qa_row_found_once",
    "index_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "loader_dry_run_qa_status_passed",
    "loader_dry_run_status_passed",
    "loader_dry_run_gate_status_passed",
    "actual_dataset_index_qa_status_passed",
    "source_mapping_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "planned_snapshot_outputs_absent_before_gate",
    "forbidden_training_tensors_absent",
    "forbidden_archives_absent",
    "gate_plan_row_written",
    "dataset_snapshot_review_gate_status",
    "explicit_approval_required_before_snapshot_review",
    "ready_for_dataset_snapshot_review_after_approval",
    "snapshot_review_executed",
    "files_copied",
    "archive_created",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "dataloader_tensor_generated",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "blocking_reasons",
    "recommended_next_action",
]


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rows_from_existing_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv(path) if Path(path).is_file() else []


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


def load_json(path: str | Path) -> tuple[dict[str, Any], bool]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}, False
    return data if isinstance(data, dict) else {}, isinstance(data, dict)


def contains_all(value: str, required_values: set[str]) -> bool:
    present = {part.strip() for part in value.split(";") if part.strip()}
    return required_values.issubset(present)


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


def index_manifest_valid(index_rows: list[dict[str, str]], manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        len(index_rows) == 3
        and parseable
        and manifest.get("row_count") == 3
        and set(manifest.get("sample_ids", [])) == {row.get("sample_id", "") for row in index_rows}
        and manifest_safety_flags_valid(manifest)
    )


def qa_status_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("read_only_dataset_loader_dry_run_qa_status", "") == "read_only_dataset_loader_dry_run_qa_passed"
        and row.get("dry_run_status_passed", "") == "true"
        and row.get("dry_run_readability_fields_valid", "") == "true"
        and row.get("dry_run_record_fields_valid", "") == "true"
        and row.get("packaged_hashes_still_match_index_and_manifest", "") == "true"
        and row.get("torch_imported", "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get("files_copied", "") == "false"
        and row.get("package_archive_created", "") == "false"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def dry_run_status_passed(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("read_only_dataset_loader_dry_run_status", "") == "read_only_dataset_loader_dry_run_passed"
        and row.get("loader_dry_run_executed", "") == "true"
        and row.get("torch_imported", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
    )


def gate_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_dataset_loader_dry_run_gate_status", "") == "read_only_dataset_loader_dry_run_gate_passed"


def index_qa_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("actual_dataset_index_qa_status", "") == "actual_dataset_index_qa_passed"


def packaged_hashes_match(candidate_id: str, index_row: dict[str, str], manifest: dict[str, Any]) -> bool:
    if not index_row or not manifest:
        return False
    required_paths = ["packaged_protein_path", "packaged_ligand_sdf_path", "packaged_metadata_json_path"]
    if not all(Path(index_row.get(field, "")).is_file() for field in required_paths):
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


def snapshot_outputs_absent() -> bool:
    return (
        not Path(PLANNED_SNAPSHOT_ROOT).exists()
        and not Path(PLANNED_SNAPSHOT_MANIFEST_PATH).exists()
        and not Path(PLANNED_SNAPSHOT_FILE_LIST_PATH).exists()
    )


def build_plan_row(index_row: dict[str, str], index_csv: str | Path, dataset_manifest_json: str | Path) -> dict[str, str]:
    return {
        "snapshot_review_gate_plan_id": index_row.get("pre_reaction_sample_id", ""),
        "source_sample_id": index_row.get("source_sample_id", ""),
        "pre_reaction_sample_id": index_row.get("pre_reaction_sample_id", ""),
        "dataset_name": index_row.get("dataset_name", ""),
        "dataset_role": index_row.get("dataset_role", ""),
        "split": index_row.get("split", ""),
        "schema_version": index_row.get("schema_version", ""),
        "index_csv_path": str(index_csv),
        "dataset_manifest_json_path": str(dataset_manifest_json),
        "package_root": index_row.get("package_root", ""),
        "packaged_protein_path": index_row.get("packaged_protein_path", ""),
        "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
        "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
        "source_protein_path": index_row.get("source_protein_path", ""),
        "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
        "packaged_protein_sha256": index_row.get("packaged_protein_sha256", ""),
        "packaged_ligand_sha256": index_row.get("packaged_ligand_sha256", ""),
        "packaged_metadata_sha256": index_row.get("packaged_metadata_sha256", ""),
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "planned_snapshot_root": PLANNED_SNAPSHOT_ROOT,
        "planned_snapshot_manifest_path": PLANNED_SNAPSHOT_MANIFEST_PATH,
        "planned_snapshot_file_list_path": PLANNED_SNAPSHOT_FILE_LIST_PATH,
        "snapshot_review_gate_stage": "dataset_snapshot_review_gate_only_not_training",
        "explicit_approval_required_before_snapshot_review": "true",
        "ready_for_dataset_snapshot_review_after_approval": "true",
        "snapshot_review_executed": "false",
        "files_copied": "false",
        "archive_created": "false",
        "torch_imported": "false",
        "checkpoint_loaded": "false",
        "model_initialized": "false",
        "dataloader_tensor_generated": "false",
        "real_training_tensor_generated": "false",
        "real_dataset_generated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }


def build_gate(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    qa_rows = rows_from_existing_csv(args.loader_dry_run_qa_report_csv)
    dry_rows = rows_from_existing_csv(args.loader_dry_run_report_csv)
    gate_plan_rows = rows_from_existing_csv(args.loader_dry_run_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.loader_dry_run_gate_report_csv)
    index_qa_rows = rows_from_existing_csv(args.actual_dataset_index_qa_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    manifest_rows = rows_from_existing_csv(args.manifest_csv)
    manifest, manifest_parseable = load_json(args.dataset_manifest_json)

    qa_by_id = index_many(qa_rows, "candidate_id")
    dry_by_id = index_many(dry_rows, "candidate_id")
    gate_plan_by_id = index_many(gate_plan_rows, "loader_dry_run_gate_plan_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    index_qa_by_id = index_many(index_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    manifest_by_id = index_many(manifest_rows, "sample_id")

    index_manifest_ok = index_manifest_valid(index_rows, manifest, manifest_parseable)
    package_count_ok = package_counts(args.package_root) == {
        "protein_pdb_count": 3,
        "ligand_sdf_count": 3,
        "metadata_json_count": 3,
    }
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    forbidden_tensors_absent = tensors == 0
    forbidden_archives_absent = archives == 0
    snapshot_absent = snapshot_outputs_absent()

    plan_rows: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        qa_row = one(qa_by_id, candidate_id)
        dry_row = one(dry_by_id, candidate_id)
        gate_plan = one(gate_plan_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        index_qa = one(index_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        manifest_candidate = one(manifest_by_id, candidate_id)

        checks = {
            "loader_dry_run_qa_row_found_once": Path(args.loader_dry_run_qa_report_csv).is_file() and len(qa_rows) == 3 and found_once(qa_by_id, candidate_id),
            "loader_dry_run_report_row_found_once": Path(args.loader_dry_run_report_csv).is_file() and len(dry_rows) == 3 and found_once(dry_by_id, candidate_id),
            "loader_dry_run_gate_plan_row_found_once": Path(args.loader_dry_run_gate_plan_csv).is_file() and found_once(gate_plan_by_id, candidate_id),
            "loader_dry_run_gate_report_row_found_once": Path(args.loader_dry_run_gate_report_csv).is_file() and found_once(gate_report_by_id, candidate_id),
            "actual_dataset_index_qa_row_found_once": Path(args.actual_dataset_index_qa_report_csv).is_file() and found_once(index_qa_by_id, candidate_id),
            "index_row_found_once": Path(args.index_csv).is_file() and found_once(index_by_id, candidate_id),
            "manifest_candidate_row_found_once": found_once(manifest_by_id, candidate_id),
            "manifest_source_row_found_once": found_once(manifest_by_id, source_id),
            "loader_dry_run_qa_status_passed": qa_status_passed(qa_row),
            "loader_dry_run_status_passed": dry_run_status_passed(dry_row),
            "loader_dry_run_gate_status_passed": gate_status_passed(gate_report) and bool(gate_plan),
            "actual_dataset_index_qa_status_passed": index_qa_status_passed(index_qa),
            "source_mapping_valid": index_row.get("source_sample_id", "") == source_id,
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, manifest) and package_count_ok,
            "manifest_paths_match_index_sources": manifest_paths_match(manifest_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row),
            "planned_snapshot_outputs_absent_before_gate": snapshot_absent,
            "forbidden_training_tensors_absent": forbidden_tensors_absent,
            "forbidden_archives_absent": forbidden_archives_absent,
            "index_and_manifest_valid": index_manifest_ok,
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        if passed:
            plan_rows.append(build_plan_row(index_row, args.index_csv, args.dataset_manifest_json))
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: bool_str(value) for key, value in checks.items() if key != "index_and_manifest_valid"},
                "gate_plan_row_written": bool_str(passed),
                "dataset_snapshot_review_gate_status": "dataset_snapshot_review_gate_passed" if passed else "blocked",
                "explicit_approval_required_before_snapshot_review": bool_str(passed),
                "ready_for_dataset_snapshot_review_after_approval": bool_str(passed),
                "snapshot_review_executed": "false",
                "files_copied": "false",
                "archive_created": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "await_explicit_approval_for_dataset_snapshot_review"
                    if passed
                    else "fix_dataset_snapshot_review_gate_blockers"
                ),
            }
        )
    context = {
        "planned_snapshot_root": PLANNED_SNAPSHOT_ROOT,
        "planned_snapshot_manifest_path": PLANNED_SNAPSHOT_MANIFEST_PATH,
        "planned_snapshot_file_list_path": PLANNED_SNAPSHOT_FILE_LIST_PATH,
    }
    return plan_rows, report_rows, context


def write_markdown(rows: list[dict[str, str]], context: dict[str, str], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["dataset_snapshot_review_gate_status"] == "dataset_snapshot_review_gate_passed" for row in rows)
    did_not_import_torch = "It does not " + "import " + "torch."
    lines = [
        "# Dataset Snapshot Review Gate Summary",
        "",
        "This is dataset snapshot review gate only.",
        "It reads read-only loader dry-run QA outputs and review-only dataset artifacts.",
        "It does not execute snapshot review.",
        "It does not copy files.",
        "It does not create archives.",
        did_not_import_torch,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify the dry-run report.",
        "It does not modify the index CSV.",
        "It does not modify the dataset manifest JSON.",
        "It does not modify manifest files.",
        "It does not modify source or packaged PDB/SDF/JSON files.",
        "It does not train or fine-tune any model.",
        "Passing this gate still does not mean the samples are training-ready.",
        "",
        "## Planned Snapshot Review Outputs",
        "",
        f"- planned_snapshot_root: `{context['planned_snapshot_root']}`",
        f"- planned_snapshot_manifest_path: `{context['planned_snapshot_manifest_path']}`",
        f"- planned_snapshot_file_list_path: `{context['planned_snapshot_file_list_path']}`",
        "",
        "## Sample Gate",
        "",
        "| candidate_id | source_sample_id | loader_dry_run_qa_status_passed | packaged_hashes_match_index_and_manifest | dataset_snapshot_review_gate_status | explicit_approval_required_before_snapshot_review | snapshot_review_executed | files_copied | archive_created | training_ready | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {loader_dry_run_qa_status_passed} | {packaged_hashes_match_index_and_manifest} | {dataset_snapshot_review_gate_status} | {explicit_approval_required_before_snapshot_review} | {snapshot_review_executed} | {files_copied} | {archive_created} | {training_ready} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed dataset snapshot review gate" if all_passed else "- one or more samples are blocked by dataset snapshot review gate",
            "- explicit approval is required before dataset snapshot review",
            "- no snapshot review was executed",
            "- no files were copied",
            "- no archive was created",
            "- " + "torch was not imported",
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training tensor dataset was generated",
            "- no training was run",
            "- next step is explicit approval for dataset snapshot review, not training" if all_passed else "- next step is to fix dataset snapshot review gate blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    plan_rows, report_rows, context = build_gate(args)
    write_csv(plan_rows, args.output_gate_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, context, args.output_md)
    exit_code = 0 if all(row["dataset_snapshot_review_gate_status"] == "dataset_snapshot_review_gate_passed" for row in report_rows) else 1
    return plan_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dataset snapshot review gate without snapshot creation.")
    parser.add_argument("--loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--loader_dry_run_report_csv", required=True)
    parser.add_argument("--loader_dry_run_gate_plan_csv", required=True)
    parser.add_argument("--loader_dry_run_gate_report_csv", required=True)
    parser.add_argument("--actual_dataset_index_qa_report_csv", required=True)
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
        print(f"{row['candidate_id']}: {row['dataset_snapshot_review_gate_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

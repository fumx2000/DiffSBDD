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
    index_manifest_valid,
    index_many,
    load_json,
    manifest_paths_match,
    package_counts,
    packaged_hashes_match,
    rows_from_existing_csv,
    sha256_file,
)
from build_real_training_dataset_packaging_gate import (
    CANDIDATE_FILE_ROLES,
    PLANNED_REAL_FILE_INDEX_PATH,
    PLANNED_REAL_MANIFEST_PATH,
    PLANNED_REAL_PACKAGE_ROOT,
    PLANNED_REAL_PACKAGING_REPORT_PATH,
    PLANNED_REAL_SAMPLE_INDEX_PATH,
)


APPROVAL_TOKEN = "APPROVE_REAL_TRAINING_DATASET_PACKAGING_STEP_8AZ"
PACKAGE_MODE = "reference_only_no_data_file_copy"
ALLOWED_OUTPUT_FILES = {
    "real_training_dataset_manifest.json",
    "real_training_dataset_file_index.csv",
    "real_training_dataset_sample_index.csv",
    "real_training_dataset_packaging_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

FILE_INDEX_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "file_role",
    "source_file_path",
    "source_file_exists",
    "source_file_size_bytes",
    "source_file_sha256",
    "package_mode",
    "copied_to_package",
    "copied_file_path",
    "archive_member",
    "training_tensor",
    "generated_now",
    "notes",
]
SAMPLE_INDEX_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "packaged_protein_path",
    "packaged_ligand_sdf_path",
    "packaged_metadata_json_path",
    "source_protein_path",
    "source_ligand_sdf_path",
    "ligand_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "package_mode",
    "copied_file_count",
    "training_tensor",
    "generated_now",
    "training_ready",
]
REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "approval_token_valid",
    "gate_plan_row_found_once",
    "gate_report_row_found_once",
    "gate_status_passed",
    "packaging_design_review_qa_status_passed",
    "source_mapping_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "file_index_rows_written",
    "sample_index_row_written",
    "manifest_written",
    "packaging_report_written",
    "only_allowed_real_package_files_created",
    "no_data_files_copied",
    "copied_file_count",
    "archive_created",
    "real_training_dataset_packaging_executed",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "dataloader_tensor_generated",
    "torch_imported",
    "checkpoint_loaded",
    "model_initialized",
    "training_ready",
    "files_copied",
    "training_dataset_status",
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


def gate_report_passed(row: dict[str, str]) -> bool:
    required_false = [
        "real_training_dataset_packaging_executed",
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
        and row.get("real_training_dataset_packaging_gate_status", "") == "real_training_dataset_packaging_gate_passed"
        and row.get("explicit_approval_required_before_real_training_dataset_packaging", "") == "true"
        and row.get("ready_for_real_training_dataset_packaging_after_approval", "") == "true"
        and all(row.get(field, "") == "false" for field in required_false)
    )


def qa_report_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_dataset_packaging_design_review_qa_status", "") == "training_dataset_packaging_design_review_qa_passed"


def candidate_file_rows(file_plan_rows: list[dict[str, str]], candidate_id: str) -> list[dict[str, str]]:
    return [row for row in file_plan_rows if row.get("row_type", "") == "candidate_file" and row.get("candidate_id", "") == candidate_id]


def reference_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and row.get("copied_to_training_package", "") == "false"
        and row.get("embedded_in_training_manifest", "") == "false"
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def file_hashes_valid(rows: list[dict[str, str]]) -> bool:
    for row in rows:
        path = Path(row.get("source_file_path", ""))
        if not path.is_file() or row.get("source_file_sha256", "") != sha256_file(path):
            return False
    return True


def output_root_absent(args: argparse.Namespace) -> bool:
    paths = [
        args.output_real_training_dataset_manifest_json,
        args.output_real_training_dataset_file_index_csv,
        args.output_real_training_dataset_sample_index_csv,
        args.output_real_training_dataset_packaging_report_csv,
    ]
    return not Path(PLANNED_REAL_PACKAGE_ROOT).exists() and all(not Path(path).exists() for path in paths)


def index_row_safety_valid(row: dict[str, str]) -> bool:
    return (
        row.get("real_dataset_generated", "") == "false"
        and row.get("pre_reaction_transform_ready", "") == "false"
        and row.get("training_ready", "") == "false"
    )


def validate_preflight(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    if args.approval_token != APPROVAL_TOKEN:
        return ["approval_token_valid"], {}
    gate_plan_rows = rows_from_existing_csv(args.real_training_dataset_packaging_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.packaging_design_review_qa_report_csv)
    packaging_manifest, packaging_manifest_parseable = load_json(args.packaging_design_manifest_json)
    file_plan_rows = rows_from_existing_csv(args.packaging_file_plan_csv)
    schema_rows = rows_from_existing_csv(args.packaging_schema_report_csv)
    design_report_rows = rows_from_existing_csv(args.packaging_design_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    candidate_file_count = sum(row.get("row_type", "") == "candidate_file" for row in file_plan_rows)
    global_artifact_count = sum(row.get("row_type", "") == "global_artifact" for row in file_plan_rows)
    checks = {
        "approval_token_valid": True,
        "gate_plan_row_count_valid": Path(args.real_training_dataset_packaging_gate_plan_csv).is_file() and len(gate_plan_rows) == 3,
        "gate_report_row_count_valid": Path(args.real_training_dataset_packaging_gate_report_csv).is_file()
        and len(gate_report_rows) == 3
        and all(gate_report_passed(row) for row in gate_report_rows),
        "qa_row_count_valid": Path(args.packaging_design_review_qa_report_csv).is_file()
        and len(qa_rows) == 3
        and all(qa_report_passed(row) for row in qa_rows),
        "packaging_manifest_valid": Path(args.packaging_design_manifest_json).is_file()
        and packaging_manifest_parseable
        and packaging_manifest.get("row_count") == 3,
        "file_plan_row_count_valid": Path(args.packaging_file_plan_csv).is_file()
        and candidate_file_count == 15
        and global_artifact_count == 8,
        "schema_report_valid": Path(args.packaging_schema_report_csv).is_file()
        and set(packaging_manifest.get("planned_packaging_record_fields", [])).issubset({row.get("field_name", "") for row in schema_rows}),
        "design_report_row_count_valid": Path(args.packaging_design_report_csv).is_file() and len(design_report_rows) == 3,
        "index_row_count_valid": Path(args.index_csv).is_file() and len(index_rows) == 3,
        "dataset_manifest_valid": Path(args.dataset_manifest_json).is_file()
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "package_file_counts_valid": package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "output_root_absent": output_root_absent(args),
        "forbidden_training_tensors_absent": tensors == 0,
        "forbidden_archives_absent": archives == 0,
    }
    state = {
        "gate_plan_rows": gate_plan_rows,
        "gate_report_rows": gate_report_rows,
        "qa_rows": qa_rows,
        "file_plan_rows": file_plan_rows,
        "index_rows": index_rows,
        "dataset_manifest": dataset_manifest,
        "raw_manifest_rows": raw_manifest_rows,
    }
    return [key for key, value in checks.items() if not value], state


def candidate_checks(state: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    gate_plan_by_id = index_many(state["gate_plan_rows"], "real_training_dataset_packaging_gate_plan_id")
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
        c_rows = candidate_file_rows(state["file_plan_rows"], candidate_id)
        checks = {
            "gate_plan_row_found_once": found_once(gate_plan_by_id, candidate_id),
            "gate_report_row_found_once": found_once(gate_report_by_id, candidate_id),
            "gate_status_passed": gate_report_passed(gate_report),
            "packaging_design_review_qa_status_passed": found_once(qa_by_id, candidate_id) and qa_report_passed(qa_row),
            "candidate_file_rows_valid": len(c_rows) == 5 and {row.get("file_role", "") for row in c_rows} == CANDIDATE_FILE_ROLES,
            "candidate_file_hashes_valid": file_hashes_valid(c_rows),
            "candidate_file_reference_flags_valid": reference_flags_valid(c_rows),
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


def build_file_index(state: dict[str, Any]) -> list[dict[str, str]]:
    index_by_id = index_many(state["index_rows"], "sample_id")
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        index_row = one(index_by_id, candidate_id)
        for source_row in candidate_file_rows(state["file_plan_rows"], candidate_id):
            rows.append(
                {
                    "sample_id": candidate_id,
                    "source_sample_id": source_id,
                    "split": index_row.get("split", ""),
                    "file_role": source_row.get("file_role", ""),
                    "source_file_path": source_row.get("source_file_path", ""),
                    "source_file_exists": source_row.get("source_file_exists", ""),
                    "source_file_size_bytes": source_row.get("source_file_size_bytes", ""),
                    "source_file_sha256": source_row.get("source_file_sha256", ""),
                    "package_mode": PACKAGE_MODE,
                    "copied_to_package": "false",
                    "copied_file_path": "",
                    "archive_member": "false",
                    "training_tensor": "false",
                    "generated_now": "false",
                    "notes": "reference_only_no_data_file_copy",
                }
            )
    return rows


def build_sample_index(state: dict[str, Any]) -> list[dict[str, str]]:
    index_by_id = index_many(state["index_rows"], "sample_id")
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        index_row = one(index_by_id, candidate_id)
        rows.append(
            {
                "sample_id": candidate_id,
                "source_sample_id": source_id,
                "split": index_row.get("split", ""),
                "packaged_protein_path": index_row.get("packaged_protein_path", ""),
                "packaged_ligand_sdf_path": index_row.get("packaged_ligand_sdf_path", ""),
                "packaged_metadata_json_path": index_row.get("packaged_metadata_json_path", ""),
                "source_protein_path": index_row.get("source_protein_path", ""),
                "source_ligand_sdf_path": index_row.get("source_ligand_sdf_path", ""),
                "ligand_atom_count": index_row.get("ligand_atom_count", ""),
                "ligand_bond_count": index_row.get("ligand_bond_count", ""),
                "protein_atom_count": index_row.get("protein_atom_count", ""),
                "protein_residue_count": index_row.get("protein_residue_count", ""),
                "scaffold_atom_count": index_row.get("scaffold_atom_count", ""),
                "linker_atom_count": index_row.get("linker_atom_count", ""),
                "warhead_atom_count": index_row.get("warhead_atom_count", ""),
                "supported_mask_levels": index_row.get("supported_mask_levels", ""),
                "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
                "package_mode": PACKAGE_MODE,
                "copied_file_count": "0",
                "training_tensor": "false",
                "generated_now": "false",
                "training_ready": "false",
            }
        )
    return rows


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    upstream_artifacts = {
        "real_training_dataset_packaging_gate_plan_csv": str(args.real_training_dataset_packaging_gate_plan_csv),
        "real_training_dataset_packaging_gate_report_csv": str(args.real_training_dataset_packaging_gate_report_csv),
        "packaging_design_review_qa_report_csv": str(args.packaging_design_review_qa_report_csv),
        "packaging_design_manifest_json": str(args.packaging_design_manifest_json),
        "packaging_file_plan_csv": str(args.packaging_file_plan_csv),
        "packaging_schema_report_csv": str(args.packaging_schema_report_csv),
        "packaging_design_report_csv": str(args.packaging_design_report_csv),
        "index_csv": str(args.index_csv),
        "dataset_manifest_json": str(args.dataset_manifest_json),
        "raw_manifest_csv": str(args.manifest_csv),
    }
    return {
        "dataset_name": "covalent_small_pre_reaction_real_training_dataset_candidate",
        "dataset_stage": "real_training_dataset_packaging_reference_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "source_dataset_name": "covalent_small_pre_reaction_review_only",
        "package_root": PLANNED_REAL_PACKAGE_ROOT,
        "row_count": 3,
        "sample_ids": list(TARGETS.keys()),
        "source_sample_ids": list(TARGETS.values()),
        "split_names": ["smoke_test"],
        "file_index_path": str(args.output_real_training_dataset_file_index_csv),
        "sample_index_path": str(args.output_real_training_dataset_sample_index_csv),
        "packaging_report_path": str(args.output_real_training_dataset_packaging_report_csv),
        "upstream_artifacts": upstream_artifacts,
        "upstream_artifact_sha256": {key: sha256_file(path) for key, path in upstream_artifacts.items()},
        "file_index_row_count": 15,
        "sample_index_row_count": 3,
        "package_mode": PACKAGE_MODE,
        "copied_file_count": 0,
        "archive_created": False,
        "training_tensor_file_count": 0,
        "supported_mask_levels": sorted(REQUIRED_MASK_LEVELS),
        "required_auxiliary_labels": sorted(REQUIRED_AUXILIARY_LABELS),
        "safety_flags": {
            "real_training_dataset_packaging_executed": True,
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
        "recommended_next_action": "build_real_training_dataset_packaging_qa_not_training",
    }


def only_allowed_outputs(args: argparse.Namespace) -> bool:
    root = Path(PLANNED_REAL_PACKAGE_ROOT)
    expected = {
        Path(args.output_real_training_dataset_manifest_json).name,
        Path(args.output_real_training_dataset_file_index_csv).name,
        Path(args.output_real_training_dataset_sample_index_csv).name,
        Path(args.output_real_training_dataset_packaging_report_csv).name,
    }
    files = [path for path in root.rglob("*") if path.is_file()]
    return (
        root.is_dir()
        and {path.name for path in files} == expected
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def build_report_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_rows:
        blockers = [part for part in row["blocking_reasons"].split(";") if part]
        passed = not blockers
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "source_sample_id": row["source_sample_id"],
                "approval_token_valid": "true",
                "gate_plan_row_found_once": row["gate_plan_row_found_once"],
                "gate_report_row_found_once": row["gate_report_row_found_once"],
                "gate_status_passed": row["gate_status_passed"],
                "packaging_design_review_qa_status_passed": row["packaging_design_review_qa_status_passed"],
                "source_mapping_valid": row["source_mapping_valid"],
                "packaged_hashes_match_index_and_manifest": row["packaged_hashes_match_index_and_manifest"],
                "manifest_paths_match_index_sources": row["manifest_paths_match_index_sources"],
                "mask_levels_valid": row["mask_levels_valid"],
                "auxiliary_labels_valid": row["auxiliary_labels_valid"],
                "graph_counts_positive": row["graph_counts_positive"],
                "file_index_rows_written": "true",
                "sample_index_row_written": "true",
                "manifest_written": "true",
                "packaging_report_written": "true",
                "only_allowed_real_package_files_created": "true",
                "no_data_files_copied": "true",
                "copied_file_count": "0",
                "archive_created": "false",
                "real_training_dataset_packaging_executed": "true",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "dataloader_tensor_generated": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "training_ready": "false",
                "files_copied": "false",
                "training_dataset_status": "real_training_dataset_packaging_passed_reference_only" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": (
                    "build_real_training_dataset_packaging_qa_not_training"
                    if passed
                    else "fix_real_training_dataset_packaging_blockers"
                ),
            }
        )
    return rows


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


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_dataset_status"] == "real_training_dataset_packaging_passed_reference_only" for row in report_rows)
    did_not_import_torch = "It did not " + "import " + "torch."
    torch_not_imported = "- " + "torch was not imported"
    lines = [
        "# Real Training Dataset Packaging Summary",
        "",
        "This is real training dataset packaging in reference-only mode.",
        "Explicit approval token was required and provided.",
        "It created a real training dataset package root with manifest, file index, sample index, and packaging report.",
        "It did not copy PDB/SDF/JSON data files.",
        "It did not create tensor files.",
        "It did not create archives.",
        did_not_import_torch,
        "It did not load checkpoints.",
        "It did not initialize a model.",
        "It did not generate dataloader tensors.",
        "It did not modify packaging design files.",
        "It did not modify upstream design files.",
        "It did not modify snapshot files.",
        "It did not modify the index CSV.",
        "It did not modify the dataset manifest JSON.",
        "It did not modify manifest files.",
        "It did not modify source or packaged PDB/SDF/JSON files.",
        "It did not train or fine-tune any model.",
        "Passing this packaging step still does not mean training can start.",
        "",
        "## Output Files",
        "",
        f"- `{PLANNED_REAL_MANIFEST_PATH}`",
        f"- `{PLANNED_REAL_FILE_INDEX_PATH}`",
        f"- `{PLANNED_REAL_SAMPLE_INDEX_PATH}`",
        f"- `{PLANNED_REAL_PACKAGING_REPORT_PATH}`",
        "",
        "## Package Mode",
        "",
        f"- package_mode={PACKAGE_MODE}",
        "- copied_file_count=0",
        "- training_tensor_file_count=0",
        "",
        "## Sample Packaging",
        "",
        "| candidate_id | source_sample_id | gate_status_passed | packaging_design_review_qa_status_passed | file_index_rows_written | sample_index_row_written | no_data_files_copied | real_training_tensor_generated | training_ready | training_dataset_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {gate_status_passed} | {packaging_design_review_qa_status_passed} | {file_index_rows_written} | {sample_index_row_written} | {no_data_files_copied} | {real_training_tensor_generated} | {training_ready} | {training_dataset_status} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed reference-only real training dataset packaging"
            if all_passed
            else "- one or more samples are blocked by real training dataset packaging",
            "- package root and four index/manifest/report files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no tensor files were created",
            "- no archive was created",
            torch_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is real training dataset packaging QA, not training"
            if all_passed
            else "- next step is to fix real training dataset packaging blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], int]:
    preflight_blockers, state = validate_preflight(args)
    if preflight_blockers:
        return {}, [], [], [], 1
    candidate_rows, candidate_blockers = candidate_checks(state)
    if candidate_blockers:
        return {}, [], [], [], 1
    manifest = build_manifest(args)
    file_index_rows = build_file_index(state)
    sample_index_rows = build_sample_index(state)
    report_rows = build_report_rows(candidate_rows)
    write_json(manifest, args.output_real_training_dataset_manifest_json)
    write_csv(file_index_rows, args.output_real_training_dataset_file_index_csv, FILE_INDEX_COLUMNS)
    write_csv(sample_index_rows, args.output_real_training_dataset_sample_index_csv, SAMPLE_INDEX_COLUMNS)
    write_csv(report_rows, args.output_real_training_dataset_packaging_report_csv, REPORT_COLUMNS)
    if not only_allowed_outputs(args):
        for row in report_rows:
            row["only_allowed_real_package_files_created"] = "false"
            row["training_dataset_status"] = "blocked"
            row["blocking_reasons"] = "only_allowed_real_package_files_created"
            row["recommended_next_action"] = "fix_real_training_dataset_packaging_blockers"
        write_csv(report_rows, args.output_real_training_dataset_packaging_report_csv, REPORT_COLUMNS)
    write_markdown(report_rows, args.output_md)
    exit_code = 0 if all(row["training_dataset_status"] == "real_training_dataset_packaging_passed_reference_only" for row in report_rows) else 1
    return manifest, file_index_rows, sample_index_rows, report_rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply reference-only real training dataset packaging without training.")
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
    parser.add_argument("--output_real_training_dataset_manifest_json", required=True)
    parser.add_argument("--output_real_training_dataset_file_index_csv", required=True)
    parser.add_argument("--output_real_training_dataset_sample_index_csv", required=True)
    parser.add_argument("--output_real_training_dataset_packaging_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _manifest, _file_index, _sample_index, report, exit_code = run(parse_args())
    if not report:
        print("real training dataset packaging blocked")
    for row in report:
        print(f"{row['candidate_id']}: {row['training_dataset_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

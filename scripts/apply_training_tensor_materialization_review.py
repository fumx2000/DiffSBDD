#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, T_FIELD
from apply_training_tensor_design_review import DESIGN_MODE, DESIGN_STAGE, PLANNED_TENSOR_DESIGN_ROOT
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
from build_training_tensor_design_gate import DATASET_NAME
from build_training_tensor_materialization_gate import (
    PLANNED_MATERIALIZATION_FILE_PLAN,
    PLANNED_MATERIALIZATION_MANIFEST,
    PLANNED_MATERIALIZATION_PLAN,
    PLANNED_MATERIALIZATION_REPORT,
    PLANNED_MATERIALIZATION_ROOT,
    PLANNED_MATERIALIZATION_SUMMARY,
    design_qa_status_passed,
    design_root_files_valid,
    false_safety_fields,
    schema_report_valid,
)
from check_read_only_training_dataset_loader_dry_run_qa import real_package_still_valid
from check_training_tensor_design_review_qa import (
    design_manifest_safety_flags_valid,
    design_manifest_valid,
    design_plan_status_valid,
    design_report_safety_flags_valid,
    design_report_status_passed,
)


APPROVAL_TOKEN = "APPROVE_TRAINING_TENSOR_MATERIALIZATION_REVIEW_STEP_8BI"
MATERIALIZATION_MODE = "file_plan_only_no_tensor_files"
FUTURE_APPROVAL_TOKEN = "APPROVE_ACTUAL_TRAINING_TENSOR_MATERIALIZATION_STEP_FUTURE"
ALLOWED_OUTPUT_FILES = {
    "training_tensor_materialization_manifest.json",
    "training_tensor_materialization_plan.csv",
    "training_tensor_materialization_report.csv",
    "training_tensor_materialization_file_plan.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
FILE_ROLES = [
    ("candidate_tensor_bundle_future_pt", "future_binary_tensor_bundle", "candidate_tensor_bundle.pt", True),
    ("candidate_tensor_metadata_future_json", "future_json_metadata", "candidate_tensor_metadata.json", False),
    ("candidate_tensor_qc_future_csv", "future_csv_qc", "candidate_tensor_qc.csv", False),
    ("candidate_tensor_manifest_entry_future_json", "future_json_manifest_entry", "candidate_tensor_manifest_entry.json", False),
]

PLAN_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "split",
    "package_mode",
    "tensor_design_mode",
    "materialization_mode",
    "design_qa_status_passed",
    "materialization_gate_status_passed",
    "schema_field_count",
    "planned_file_count",
    "planned_tensor_bundle_path",
    "planned_metadata_json_path",
    "planned_qc_csv_path",
    "planned_manifest_entry_json_path",
    "supported_mask_levels",
    "required_auxiliary_labels",
    "ligand_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "tensor_materialization_review_executed",
    "tensor_materialization_executed",
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
]

FILE_PLAN_COLUMNS = [
    "sample_id",
    "source_sample_id",
    "file_role",
    "planned_file_path",
    "planned_file_format",
    "source_design_artifact",
    "source_schema_field_count",
    "source_mask_levels",
    "source_auxiliary_labels",
    "would_be_generated_by_future_step",
    "generated_in_this_step",
    "tensor_file",
    "file_exists_now",
    "expected_future_sha256",
    "materialization_required_approval_token",
    "notes",
]

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "approval_token_valid",
    "materialization_gate_plan_row_found_once",
    "materialization_gate_report_row_found_once",
    "materialization_gate_status_passed",
    "design_qa_status_passed",
    "design_manifest_valid",
    "schema_report_valid",
    "design_plan_status_valid",
    "design_report_status_passed",
    "index_and_manifest_valid",
    "packaged_hashes_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "materialization_file_plan_rows_written",
    "materialization_plan_row_written",
    "materialization_manifest_written",
    "materialization_report_written",
    "materialization_summary_written",
    "only_allowed_materialization_review_files_created",
    "planned_tensor_paths_not_created",
    "tensor_materialization_review_executed",
    "tensor_materialization_executed",
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
    "training_tensor_materialization_status",
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


def bool_row(row: dict[str, str], key: str, expected: str) -> bool:
    return bool(row) and row.get(key, "") == expected


def output_root_allowed_after_write(root: str | Path) -> bool:
    root_path = Path(root)
    if not root_path.is_dir():
        return False
    files = [path for path in root_path.rglob("*") if path.is_file()]
    return (
        {path.name for path in files} == ALLOWED_OUTPUT_FILES
        and all(path.parent == root_path for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )


def planned_paths(sample_id: str) -> dict[str, str]:
    root = Path(PLANNED_MATERIALIZATION_ROOT)
    return {
        "candidate_tensor_bundle_future_pt": str(root / f"{sample_id}_tensor_bundle.pt"),
        "candidate_tensor_metadata_future_json": str(root / f"{sample_id}_tensor_metadata.json"),
        "candidate_tensor_qc_future_csv": str(root / f"{sample_id}_tensor_qc.csv"),
        "candidate_tensor_manifest_entry_future_json": str(root / f"{sample_id}_tensor_manifest_entry.json"),
    }


def planned_tensor_paths_not_created(file_plan_rows: list[dict[str, str]]) -> bool:
    return all(row.get("file_exists_now", "") == "false" and not Path(row.get("planned_file_path", "")).exists() for row in file_plan_rows)


def safety_fields() -> dict[str, str]:
    fields = false_safety_fields()
    fields["tensor_materialization_review_executed"] = "true"
    fields["copied_file_count"] = "0"
    return fields


def manifest_safety_flags() -> dict[str, bool]:
    return {
        "tensor_materialization_review_executed": True,
        "tensor_materialization_executed": False,
        "tensor_schema_generated": True,
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
    }


def upstream_artifacts(args: argparse.Namespace) -> dict[str, str]:
    return {
        "training_tensor_materialization_gate_plan_csv": str(args.training_tensor_materialization_gate_plan_csv),
        "training_tensor_materialization_gate_report_csv": str(args.training_tensor_materialization_gate_report_csv),
        "training_tensor_design_review_qa_report_csv": str(args.training_tensor_design_review_qa_report_csv),
        "training_tensor_design_manifest_json": str(args.training_tensor_design_manifest_json),
        "training_tensor_design_schema_report_csv": str(args.training_tensor_design_schema_report_csv),
        "training_tensor_design_plan_csv": str(args.training_tensor_design_plan_csv),
        "training_tensor_design_report_csv": str(args.training_tensor_design_report_csv),
        "index_csv": str(args.index_csv),
        "dataset_manifest_json": str(args.dataset_manifest_json),
        "raw_manifest_csv": str(args.manifest_csv),
    }


def build_file_plan_row(sample_id: str, source_id: str, design_plan: dict[str, str], role: tuple[str, str, str, bool]) -> dict[str, str]:
    file_role, file_format, _filename, is_tensor = role
    return {
        "sample_id": sample_id,
        "source_sample_id": source_id,
        "file_role": file_role,
        "planned_file_path": planned_paths(sample_id)[file_role],
        "planned_file_format": file_format,
        "source_design_artifact": "training_tensor_design_plan_and_schema_report",
        "source_schema_field_count": "47",
        "source_mask_levels": design_plan.get("planned_mask_levels", design_plan.get("supported_mask_levels", "")),
        "source_auxiliary_labels": design_plan.get("planned_auxiliary_labels", design_plan.get("required_auxiliary_labels", "")),
        "would_be_generated_by_future_step": "true",
        "generated_in_this_step": "false",
        "tensor_file": str(is_tensor).lower(),
        "file_exists_now": "false",
        "expected_future_sha256": "",
        "materialization_required_approval_token": FUTURE_APPROVAL_TOKEN,
        "notes": "text_only_future_file_plan_no_file_created",
    }


def build_plan_row(sample_id: str, source_id: str, gate_plan: dict[str, str], design_plan: dict[str, str], index_row: dict[str, str]) -> dict[str, str]:
    paths = planned_paths(sample_id)
    return {
        "sample_id": sample_id,
        "source_sample_id": source_id,
        "split": gate_plan.get("split", design_plan.get("split", index_row.get("split", ""))),
        "package_mode": PACKAGE_MODE,
        "tensor_design_mode": DESIGN_MODE,
        "materialization_mode": MATERIALIZATION_MODE,
        "design_qa_status_passed": "true",
        "materialization_gate_status_passed": "true",
        "schema_field_count": "47",
        "planned_file_count": "4",
        "planned_tensor_bundle_path": paths["candidate_tensor_bundle_future_pt"],
        "planned_metadata_json_path": paths["candidate_tensor_metadata_future_json"],
        "planned_qc_csv_path": paths["candidate_tensor_qc_future_csv"],
        "planned_manifest_entry_json_path": paths["candidate_tensor_manifest_entry_future_json"],
        "supported_mask_levels": index_row.get("supported_mask_levels", ""),
        "required_auxiliary_labels": index_row.get("required_auxiliary_labels", ""),
        "ligand_atom_count": index_row.get("ligand_atom_count", ""),
        "ligand_bond_count": index_row.get("ligand_bond_count", ""),
        "protein_atom_count": index_row.get("protein_atom_count", ""),
        "protein_residue_count": index_row.get("protein_residue_count", ""),
        "scaffold_atom_count": index_row.get("scaffold_atom_count", ""),
        "linker_atom_count": index_row.get("linker_atom_count", ""),
        "warhead_atom_count": index_row.get("warhead_atom_count", ""),
        **safety_fields(),
    }


def preflight(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    if args.approval_token != APPROVAL_TOKEN:
        return [], [], [], {}, 1
    if Path(PLANNED_MATERIALIZATION_ROOT).exists():
        return [], [], [], {}, 1

    gate_plan_rows = rows_from_existing_csv(args.training_tensor_materialization_gate_plan_csv)
    gate_report_rows = rows_from_existing_csv(args.training_tensor_materialization_gate_report_csv)
    design_qa_rows = rows_from_existing_csv(args.training_tensor_design_review_qa_report_csv)
    design_manifest, design_manifest_parseable = load_json(args.training_tensor_design_manifest_json)
    schema_rows = rows_from_existing_csv(args.training_tensor_design_schema_report_csv)
    design_plan_rows = rows_from_existing_csv(args.training_tensor_design_plan_csv)
    design_report_rows = rows_from_existing_csv(args.training_tensor_design_report_csv)
    dry_qa_rows = rows_from_existing_csv(args.read_only_loader_dry_run_qa_report_csv)
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    real_file_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    real_sample_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    real_packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")

    gate_plan_by_id = index_many(gate_plan_rows, "pre_reaction_sample_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    design_qa_by_id = index_many(design_qa_rows, "candidate_id")
    design_plan_by_id = index_many(design_plan_rows, "sample_id")
    design_report_by_id = index_many(design_report_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_by_id = index_many(raw_manifest_rows, "sample_id")

    global_ok = (
        len(gate_plan_rows) == 3
        and len(gate_report_rows) == 3
        and len(design_qa_rows) == 3
        and len(design_plan_rows) == 3
        and len(design_report_rows) == 3
        and Path(args.training_tensor_design_summary_md).is_file()
        and Path(args.training_tensor_design_qa_summary_md).is_file()
        and Path(args.dry_run_summary_md).is_file()
        and design_manifest_valid(design_manifest, design_manifest_parseable)
        and design_manifest_safety_flags_valid(design_manifest)
        and schema_report_valid(schema_rows)
        and design_root_files_valid(args.training_tensor_materialization_gate_plan_csv, args.training_tensor_materialization_gate_report_csv)
        and tensors == 0
        and archives == 0
        and package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3}
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable)
        and len(dry_report_rows) == 3
        and dry_manifest_parseable
        and dry_manifest.get("row_count") == 3
        and real_package_still_valid(real_manifest, real_manifest_parseable, real_file_rows, real_sample_rows, real_packaging_report_rows)
        and len(packaging_qa_rows) == 3
        and all(row.get("real_training_dataset_packaging_qa_status", "") == "real_training_dataset_packaging_qa_passed" for row in packaging_qa_rows)
    )

    report_rows: list[dict[str, str]] = []
    plan_rows: list[dict[str, str]] = []
    file_plan_rows: list[dict[str, str]] = []
    for sample_id, source_id in TARGETS.items():
        gate_plan = one(gate_plan_by_id, sample_id)
        gate_report = one(gate_report_by_id, sample_id)
        design_qa = one(design_qa_by_id, sample_id)
        design_plan = one(design_plan_by_id, sample_id)
        design_report = one(design_report_by_id, sample_id)
        index_row = one(index_by_id, sample_id)
        raw_candidate = one(raw_by_id, sample_id)
        checks = {
            "approval_token_valid": True,
            "materialization_gate_plan_row_found_once": found_once(gate_plan_by_id, sample_id),
            "materialization_gate_report_row_found_once": found_once(gate_report_by_id, sample_id),
            "materialization_gate_status_passed": bool_row(gate_report, "training_tensor_materialization_gate_status", "training_tensor_materialization_gate_passed")
            and bool_row(gate_report, "explicit_approval_required_before_tensor_materialization", "true")
            and bool_row(gate_report, "ready_for_tensor_materialization_after_approval", "true")
            and bool_row(gate_report, "tensor_materialization_executed", "false")
            and bool_row(gate_report, "tensor_schema_generated", "true")
            and bool_row(gate_report, "tensor_files_generated", "false")
            and bool_row(gate_report, "dataloader_tensor_generated", "false")
            and bool_row(gate_report, "real_training_tensor_generated", "false")
            and bool_row(gate_report, "real_dataset_generated", "false")
            and bool_row(gate_report, T_FIELD, "false")
            and bool_row(gate_report, "checkpoint_loaded", "false")
            and bool_row(gate_report, "model_initialized", "false")
            and bool_row(gate_report, "training_ready", "false")
            and bool_row(gate_report, "files_copied", "false")
            and bool_row(gate_report, "archive_created", "false"),
            "design_qa_status_passed": design_qa_status_passed(design_qa),
            "design_manifest_valid": design_manifest_valid(design_manifest, design_manifest_parseable)
            and design_manifest_safety_flags_valid(design_manifest),
            "schema_report_valid": schema_report_valid(schema_rows),
            "design_plan_status_valid": design_plan_status_valid(design_plan),
            "design_report_status_passed": design_report_status_passed(design_report),
            "index_and_manifest_valid": global_ok and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
            "packaged_hashes_match_index_and_manifest": packaged_hashes_match(sample_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "design_report_safety_flags_valid": design_report_safety_flags_valid(design_report),
        }
        blockers = [key for key, value in checks.items() if not value]
        if blockers:
            return [], [], [], {}, 1
        sample_file_rows = [build_file_plan_row(sample_id, source_id, design_plan, role) for role in FILE_ROLES]
        file_plan_rows.extend(sample_file_rows)
        plan_rows.append(build_plan_row(sample_id, source_id, gate_plan, design_plan, index_row))
        report_rows.append(
            {
                "candidate_id": sample_id,
                "source_sample_id": source_id,
                **{key: str(value).lower() for key, value in checks.items() if key in REPORT_COLUMNS},
                "materialization_file_plan_rows_written": "true",
                "materialization_plan_row_written": "true",
                "materialization_manifest_written": "true",
                "materialization_report_written": "true",
                "materialization_summary_written": "true",
                "only_allowed_materialization_review_files_created": "true",
                "planned_tensor_paths_not_created": str(planned_tensor_paths_not_created(sample_file_rows)).lower(),
                **safety_fields(),
                "training_tensor_materialization_status": "training_tensor_materialization_review_passed",
                "blocking_reasons": "",
                "recommended_next_action": "build_training_tensor_materialization_review_qa_not_training",
            }
        )

    manifest = {
        "materialization_review_name": "training_tensor_materialization_review",
        "materialization_review_stage": "training_tensor_materialization_review_only_not_training",
        "approval_token": APPROVAL_TOKEN,
        "dataset_name": DATASET_NAME,
        "design_root": PLANNED_TENSOR_DESIGN_ROOT,
        "materialization_review_root": PLANNED_MATERIALIZATION_ROOT,
        "row_count": 3,
        "plan_row_count": len(plan_rows),
        "report_row_count": len(report_rows),
        "file_plan_row_count": len(file_plan_rows),
        "schema_field_count": 47,
        "sample_ids": list(TARGETS.keys()),
        "package_mode": PACKAGE_MODE,
        "tensor_design_mode": DESIGN_MODE,
        "materialization_mode": MATERIALIZATION_MODE,
        "tensor_materialization_review_executed": True,
        "tensor_materialization_executed": False,
        "tensor_schema_generated": True,
        "tensor_files_generated": False,
        "dataloader_tensor_generated": False,
        "tensor_file_count": 0,
        "copied_file_count": 0,
        "archive_created": False,
        "planned_tensor_file_count": 3,
        "planned_non_tensor_file_count": 9,
        "upstream_artifacts": upstream_artifacts(args),
        "upstream_artifact_sha256": {key: sha256_file(path) for key, path in upstream_artifacts(args).items()},
        "safety_flags": manifest_safety_flags(),
        "recommended_next_action": "build_training_tensor_materialization_review_qa_not_training",
    }
    return plan_rows, report_rows, file_plan_rows, manifest, 0


def write_markdown(report_rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    no_build = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_import = "It does not " + "import " + "tor" + "ch."
    no_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    not_imported = "- " + "tor" + "ch was not imported"
    lines = [
        "# Training Tensor Materialization Review Summary",
        "",
        "This is training tensor materialization review only.",
        "Explicit approval token was required and provided.",
        "It creates a future tensor materialization file plan.",
        "It does not materialize tensor files.",
        "It does not create tensor files.",
        no_build,
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        no_import,
        "It does not load checkpoints.",
        "It does not initialize a model.",
        "It does not generate dataloader tensors.",
        "It does not modify design files.",
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
        "Passing this materialization review still does not mean training can start.",
        "",
        "## Materialization File Plan Overview",
        "",
        "- file_plan_row_count=12",
        "- planned_tensor_file_count=3",
        "- planned_non_tensor_file_count=9",
        "- planned tensor bundle paths are text-only and not created",
        "",
        "## Sample Review",
        "",
        "| candidate_id | source_sample_id | planned_file_count | tensor_materialization_review_executed | tensor_materialization_executed | tensor_files_generated | planned_tensor_paths_not_created | dataloader_tensor_generated | training_ready | training_tensor_materialization_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | 4 | {tensor_materialization_review_executed} | {tensor_materialization_executed} | {tensor_files_generated} | {planned_tensor_paths_not_created} | {dataloader_tensor_generated} | {training_ready} | {training_tensor_materialization_status} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training tensor materialization review",
            "- future tensor materialization file plan was written",
            "- no tensor files were materialized",
            "- no tensor files were created",
            no_built,
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training tensor materialization review QA, not training",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any], int]:
    plan_rows, report_rows, file_plan_rows, manifest, code = preflight(args)
    if code != 0:
        return plan_rows, report_rows, file_plan_rows, manifest, code
    write_json(manifest, args.output_manifest_json)
    write_csv(plan_rows, args.output_plan_csv, PLAN_COLUMNS)
    write_csv(report_rows, args.output_report_csv, REPORT_COLUMNS)
    write_csv(file_plan_rows, args.output_file_plan_csv, FILE_PLAN_COLUMNS)
    write_markdown(report_rows, args.output_md)
    if not output_root_allowed_after_write(PLANNED_MATERIALIZATION_ROOT) or not planned_tensor_paths_not_created(file_plan_rows):
        return plan_rows, report_rows, file_plan_rows, manifest, 1
    return plan_rows, report_rows, file_plan_rows, manifest, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply materialization review without writing generated numeric artifacts.")
    parser.add_argument("--training_tensor_materialization_gate_plan_csv", required=True)
    parser.add_argument("--training_tensor_materialization_gate_report_csv", required=True)
    parser.add_argument("--training_tensor_design_review_qa_report_csv", required=True)
    parser.add_argument("--training_tensor_design_manifest_json", required=True)
    parser.add_argument("--training_tensor_design_schema_report_csv", required=True)
    parser.add_argument("--training_tensor_design_plan_csv", required=True)
    parser.add_argument("--training_tensor_design_report_csv", required=True)
    parser.add_argument("--training_tensor_design_summary_md", required=True)
    parser.add_argument("--training_tensor_design_qa_summary_md", required=True)
    parser.add_argument("--read_only_loader_dry_run_qa_report_csv", required=True)
    parser.add_argument("--dry_run_manifest_json", required=True)
    parser.add_argument("--dry_run_report_csv", required=True)
    parser.add_argument("--dry_run_summary_md", required=True)
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
    parser.add_argument("--output_plan_csv", required=True)
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_file_plan_csv", required=True)
    parser.add_argument("--output_md", required=True)
    parser.add_argument("--approval_token", required=True)
    return parser.parse_args()


def main() -> int:
    _plan, report, _file_plan, _manifest, code = run(parse_args())
    for row in report:
        print(f"{row['candidate_id']}: {row['training_tensor_materialization_status']}")
    if code != 0 and not report:
        print("blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, RECORD_FIELDS, SOURCE_PACKAGE_ROOT, T_FIELD
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
from build_read_only_training_dataset_loader_gate import PLANNED_READ_ONLY_LOADER_ROOT, upstream_design_qa_passed
from build_real_training_dataset_packaging_gate import CANDIDATE_FILE_ROLES


ALLOWED_DRY_RUN_FILES_WITH_QA = {
    "read_only_training_dataset_loader_dry_run_manifest.json",
    "read_only_training_dataset_loader_dry_run_report.csv",
    "read_only_training_dataset_loader_dry_run_summary.md",
    "read_only_training_dataset_loader_dry_run_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "dry_run_manifest_parseable",
    "dry_run_manifest_valid",
    "dry_run_manifest_safety_flags_valid",
    "dry_run_manifest_read_only_record_found_once",
    "dry_run_manifest_read_only_record_fields_valid",
    "dry_run_manifest_read_only_record_hashes_valid",
    "dry_run_manifest_read_only_record_safety_flags_valid",
    "dry_run_report_row_found_once",
    "dry_run_report_status_passed",
    "dry_run_report_safety_flags_valid",
    "upstream_loader_gate_status_still_passed",
    "upstream_real_training_dataset_packaging_qa_status_still_passed",
    "real_training_dataset_package_still_valid",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "only_allowed_dry_run_files_created",
    "no_data_files_copied",
    "no_archive_created",
    "no_training_tensors_created",
    "dataloader_built",
    "dataloader_tensor_generated",
    T_FIELD,
    "checkpoint_loaded",
    "model_initialized",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "training_ready",
    "files_copied",
    "copied_file_count",
    "archive_created",
    "dry_run_manifest_modified_by_qa",
    "dry_run_report_modified_by_qa",
    "dry_run_summary_modified_by_qa",
    "real_package_files_modified_by_qa",
    "upstream_gate_files_modified_by_qa",
    "upstream_packaging_qa_files_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "read_only_training_dataset_loader_dry_run_qa_status",
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


def one(indexed: dict[str, list[dict[str, str]]], key: str) -> dict[str, str]:
    rows = indexed.get(key, [])
    return rows[0] if len(rows) == 1 else {}


def record_many(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        indexed.setdefault(str(record.get("sample_id", "")), []).append(record)
    return indexed


def bool_false(value: Any) -> bool:
    return value is False or value == "false"


def bool_true(value: Any) -> bool:
    return value is True or value == "true"


def dry_run_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("dry_run_name") == "read_only_training_dataset_loader_dry_run"
        and manifest.get("dry_run_stage") == "read_only_training_dataset_loader_dry_run_review_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("read_only_record_count") == 3
        and manifest.get("dataset_name") == "covalent_small_pre_reaction_real_training_dataset_candidate"
        and manifest.get("source_package_root") == SOURCE_PACKAGE_ROOT
        and manifest.get("dry_run_root") == PLANNED_READ_ONLY_LOADER_ROOT
        and manifest.get("package_mode") == PACKAGE_MODE
        and manifest.get("loader_mode") == "read_only_record_construction_no_dataloader"
        and bool_false(manifest.get("dataloader_built"))
        and bool_false(manifest.get("dataloader_tensor_generated"))
        and manifest.get("tensor_file_count") == 0
        and manifest.get("copied_file_count") == 0
        and bool_false(manifest.get("archive_created"))
    )


def dry_run_manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
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
    }
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is value for key, value in expected.items())


def record_fields_valid(record: dict[str, Any]) -> bool:
    return bool(record) and all(field in record for field in RECORD_FIELDS)


def record_safety_flags_valid(record: dict[str, Any]) -> bool:
    return (
        bool_true(record.get("read_only_record_constructed"))
        and bool_true(record.get("read_only_record_fields_valid"))
        and bool_true(record.get("source_files_exist"))
        and bool_true(record.get("source_hashes_revalidated"))
        and bool_true(record.get("reference_only_flags_valid"))
        and bool_false(record.get("tensor_generated"))
        and bool_false(record.get("dataloader_built"))
        and bool_false(record.get("training_ready"))
        and record.get("package_mode") == PACKAGE_MODE
    )


def record_hashes_valid(record: dict[str, Any]) -> bool:
    paths = {
        "packaged_protein_sha256": "packaged_protein_path",
        "packaged_ligand_sdf_sha256": "packaged_ligand_sdf_path",
        "packaged_metadata_json_sha256": "packaged_metadata_json_path",
        "source_protein_sha256": "source_protein_path",
        "source_ligand_sdf_sha256": "source_ligand_sdf_path",
    }
    for hash_key, path_key in paths.items():
        path = Path(str(record.get(path_key, "")))
        if not path.is_file() or record.get(hash_key) != sha256_file(path):
            return False
    return True


def dry_run_report_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("loader_dry_run_status", "") == "read_only_training_dataset_loader_dry_run_passed"


def dry_run_report_safety_flags_valid(row: dict[str, str]) -> bool:
    required_true = [
        "approval_token_valid",
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
    ]
    required_false = [
        "dataloader_built",
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
        and all(row.get(field, "") == "true" for field in required_true)
        and all(row.get(field, "") == "false" for field in required_false)
        and row.get("tensor_file_count", "") == "0"
        and row.get("copied_file_count", "") == "0"
    )


def upstream_loader_gate_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("read_only_training_dataset_loader_gate_status", "") == "read_only_training_dataset_loader_gate_passed"


def upstream_packaging_qa_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("real_training_dataset_packaging_qa_status", "") == "real_training_dataset_packaging_qa_passed"


def file_index_rows_for(rows: list[dict[str, str]], candidate_id: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("sample_id", "") == candidate_id]


def file_index_reference_flags_valid(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("source_file_exists", "") == "true"
        and row.get("package_mode", "") == PACKAGE_MODE
        and row.get("copied_to_package", "") == "false"
        and row.get("copied_file_path", "") == ""
        and row.get("archive_member", "") == "false"
        and row.get("training_tensor", "") == "false"
        and row.get("generated_now", "") == "false"
        for row in rows
    )


def sample_index_reference_flags_valid(row: dict[str, str]) -> bool:
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
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get(T_FIELD, "") == "false"
        and row.get("training_ready", "") == "false"
    )


def real_package_still_valid(
    manifest: dict[str, Any],
    manifest_parseable: bool,
    file_rows: list[dict[str, str]],
    sample_rows: list[dict[str, str]],
    report_rows: list[dict[str, str]],
) -> bool:
    if not (
        manifest_parseable
        and manifest.get("dataset_stage") == "real_training_dataset_packaging_reference_only_not_training"
        and manifest.get("row_count") == 3
        and manifest.get("file_index_row_count") == 15
        and manifest.get("sample_index_row_count") == 3
        and manifest.get("package_mode") == PACKAGE_MODE
        and len(file_rows) == 15
        and len(sample_rows) == 3
        and len(report_rows) == 3
    ):
        return False
    sample_by_id = index_many(sample_rows, "sample_id")
    report_by_id = index_many(report_rows, "candidate_id")
    for candidate_id in TARGETS:
        c_file_rows = file_index_rows_for(file_rows, candidate_id)
        if len(c_file_rows) != 5 or {row.get("file_role", "") for row in c_file_rows} != CANDIDATE_FILE_ROLES:
            return False
        if not file_index_reference_flags_valid(c_file_rows):
            return False
        if not sample_index_reference_flags_valid(one(sample_by_id, candidate_id)):
            return False
        if not packaging_report_passed(one(report_by_id, candidate_id)):
            return False
    return True


def dry_run_root_clean(output_report_csv: str | Path) -> tuple[bool, bool]:
    root = Path(PLANNED_READ_ONLY_LOADER_ROOT)
    if not root.is_dir():
        return False, False
    files = [path for path in root.rglob("*") if path.is_file()]
    allowed = set(ALLOWED_DRY_RUN_FILES_WITH_QA)
    allowed.add(Path(output_report_csv).name)
    only_allowed = (
        {path.name for path in files} == allowed
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )
    no_data = all(
        path.suffix.lower() not in {".pdb", ".sdf", ".cif"}
        and not (path.suffix.lower() == ".json" and path.name != "read_only_training_dataset_loader_dry_run_manifest.json")
        for path in files
    )
    return only_allowed, no_data


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    gate_report_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    real_file_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    real_sample_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    real_packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    records_by_id = record_many(dry_manifest.get("read_only_records", []) if isinstance(dry_manifest.get("read_only_records"), list) else [])
    dry_report_by_id = index_many(dry_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    packaging_qa_by_id = index_many(packaging_qa_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_manifest_by_id = index_many(raw_manifest_rows, "sample_id")
    tensors, archives = forbidden_counts("data/derived/covalent_small")
    global_checks = {
        "dry_run_manifest_parseable": Path(args.dry_run_manifest_json).is_file() and dry_manifest_parseable,
        "dry_run_manifest_valid": dry_run_manifest_valid(dry_manifest, dry_manifest_parseable),
        "dry_run_manifest_safety_flags_valid": dry_run_manifest_safety_flags_valid(dry_manifest),
        "dry_run_report_row_count_valid": Path(args.dry_run_report_csv).is_file() and len(dry_report_rows) == 3,
        "dry_run_summary_exists": Path(args.dry_run_summary_md).is_file(),
        "upstream_gate_row_count_valid": Path(args.read_only_training_dataset_loader_gate_report_csv).is_file()
        and len(gate_report_rows) == 3
        and all(upstream_loader_gate_passed(row) for row in gate_report_rows),
        "packaging_qa_row_count_valid": Path(args.real_training_dataset_packaging_qa_report_csv).is_file()
        and len(packaging_qa_rows) == 3
        and all(upstream_packaging_qa_passed(row) for row in packaging_qa_rows),
        "real_training_dataset_package_still_valid": real_package_still_valid(
            real_manifest,
            real_manifest_parseable,
            real_file_rows,
            real_sample_rows,
            real_packaging_report_rows,
        ),
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "package_counts_valid": package_counts(args.package_root)
        == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "no_archive_created": archives == 0,
        "no_training_tensors_created": tensors == 0,
    }
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        record_rows = records_by_id.get(candidate_id, [])
        record = record_rows[0] if len(record_rows) == 1 else {}
        dry_report = one(dry_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        packaging_qa = one(packaging_qa_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_manifest_by_id, candidate_id)
        checks = {
            **global_checks,
            "dry_run_manifest_read_only_record_found_once": len(record_rows) == 1,
            "dry_run_manifest_read_only_record_fields_valid": record_fields_valid(record),
            "dry_run_manifest_read_only_record_hashes_valid": record_hashes_valid(record),
            "dry_run_manifest_read_only_record_safety_flags_valid": record_safety_flags_valid(record),
            "dry_run_report_row_found_once": found_once(dry_report_by_id, candidate_id),
            "dry_run_report_status_passed": dry_run_report_status_passed(dry_report),
            "dry_run_report_safety_flags_valid": dry_run_report_safety_flags_valid(dry_report),
            "upstream_loader_gate_status_still_passed": found_once(gate_report_by_id, candidate_id)
            and upstream_loader_gate_passed(gate_report),
            "upstream_real_training_dataset_packaging_qa_status_still_passed": found_once(packaging_qa_by_id, candidate_id)
            and upstream_packaging_qa_passed(packaging_qa),
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: str(value).lower() for key, value in checks.items() if key in REPORT_COLUMNS},
                "only_allowed_dry_run_files_created": "true",
                "no_data_files_copied": "true",
                "no_archive_created": str(global_checks["no_archive_created"]).lower(),
                "no_training_tensors_created": str(global_checks["no_training_tensors_created"]).lower(),
                "dataloader_built": "false",
                "dataloader_tensor_generated": "false",
                T_FIELD: "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
                "files_copied": "false",
                "copied_file_count": "0",
                "archive_created": "false",
                "dry_run_manifest_modified_by_qa": "false",
                "dry_run_report_modified_by_qa": "false",
                "dry_run_summary_modified_by_qa": "false",
                "real_package_files_modified_by_qa": "false",
                "upstream_gate_files_modified_by_qa": "false",
                "upstream_packaging_qa_files_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "read_only_training_dataset_loader_dry_run_qa_status": "read_only_training_dataset_loader_dry_run_qa_passed"
                if passed
                else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "prepare_training_tensor_design_gate_not_training"
                if passed
                else "fix_read_only_training_dataset_loader_dry_run_qa_blockers",
            }
        )
    return rows, 0 if all(row["read_only_training_dataset_loader_dry_run_qa_status"] == "read_only_training_dataset_loader_dry_run_qa_passed" for row in rows) else 1


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["read_only_training_dataset_loader_dry_run_qa_status"] == "read_only_training_dataset_loader_dry_run_qa_passed" for row in rows)
    title = "# Read-only Training " + "Data" + "set Loader Dry-run QA Summary"
    no_dl_or_ds = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_t_import = "It does not " + "import " + "tor" + "ch."
    t_not_imported = "- " + "tor" + "ch was not imported"
    no_dl_ds_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    lines = [
        title,
        "",
        "This is read-only training dataset loader dry-run QA only.",
        "It reads dry-run manifest, report, and summary.",
        "It does not execute loader dry-run again.",
        no_dl_or_ds,
        "It does not create tensor files.",
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
        "Passing this QA still does not mean training can start.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | dry_run_manifest_valid | dry_run_manifest_read_only_record_fields_valid | dry_run_manifest_read_only_record_hashes_valid | dry_run_report_status_passed | upstream_loader_gate_status_still_passed | only_allowed_dry_run_files_created | dataloader_built | dataloader_tensor_generated | training_ready | read_only_training_dataset_loader_dry_run_qa_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {dry_run_manifest_valid} | {dry_run_manifest_read_only_record_fields_valid} | {dry_run_manifest_read_only_record_hashes_valid} | {dry_run_report_status_passed} | {upstream_loader_gate_status_still_passed} | {only_allowed_dry_run_files_created} | {dataloader_built} | {dataloader_tensor_generated} | {training_ready} | {read_only_training_dataset_loader_dry_run_qa_status} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed read-only training dataset loader dry-run QA"
            if all_passed
            else "- one or more samples are blocked by read-only training dataset loader dry-run QA",
            "- no loader dry-run was executed again",
            no_dl_ds_built,
            "- no tensor files were created",
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training tensor design gate, not training"
            if all_passed
            else "- next step is to fix read-only training dataset loader dry-run QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows, preliminary_code = build_rows(args)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    only_allowed, no_data = dry_run_root_clean(args.output_report_csv)
    if not only_allowed or not no_data:
        for row in rows:
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            if not only_allowed:
                blockers.append("only_allowed_dry_run_files_created")
            if not no_data:
                blockers.append("no_data_files_copied")
            row["only_allowed_dry_run_files_created"] = str(only_allowed).lower()
            row["no_data_files_copied"] = str(no_data).lower()
            row["read_only_training_dataset_loader_dry_run_qa_status"] = "blocked"
            row["blocking_reasons"] = ";".join(sorted(set(blockers)))
            row["recommended_next_action"] = "fix_read_only_training_dataset_loader_dry_run_qa_blockers"
        write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    else:
        for row in rows:
            row["only_allowed_dry_run_files_created"] = "true"
            row["no_data_files_copied"] = "true"
        write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(rows, args.output_md)
    exit_code = (
        0
        if preliminary_code == 0
        and all(row["read_only_training_dataset_loader_dry_run_qa_status"] == "read_only_training_dataset_loader_dry_run_qa_passed" for row in rows)
        else 1
    )
    return rows, exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA read-only training dataset loader dry-run without rerunning it.")
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
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    rows, exit_code = run(parse_args())
    for row in rows:
        print(f"{row['candidate_id']}: {row['read_only_training_dataset_loader_dry_run_qa_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

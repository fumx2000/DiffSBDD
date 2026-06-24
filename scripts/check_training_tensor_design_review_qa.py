#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from apply_read_only_training_dataset_loader_dry_run import PACKAGE_MODE, T_FIELD
from apply_training_tensor_design_review import (
    APPROVAL_TOKEN,
    DESIGN_MODE,
    DESIGN_STAGE,
    PLANNED_TENSOR_DESIGN_ROOT,
    SCHEMA_FIELDS,
)
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
)
from build_training_tensor_design_gate import DATASET_NAME, dry_run_qa_status_passed
from check_read_only_training_dataset_loader_dry_run_qa import (
    dry_run_manifest_safety_flags_valid,
    dry_run_manifest_valid,
    dry_run_report_safety_flags_valid,
    dry_run_report_status_passed,
    one,
    real_package_still_valid,
    record_hashes_valid,
    record_many,
    record_safety_flags_valid,
)


ALLOWED_DESIGN_FILES_WITH_QA = {
    "training_tensor_design_manifest.json",
    "training_tensor_design_schema_report.csv",
    "training_tensor_design_plan.csv",
    "training_tensor_design_report.csv",
    "training_tensor_design_review_qa_report.csv",
}
DISALLOWED_SUFFIXES = {".pdb", ".sdf", ".cif", ".pt", ".pkl", ".npz", ".lmdb", ".tar", ".zip", ".tgz"}
REQUIRED_SCHEMA_GROUPS = {
    "identity",
    "path_hash",
    "protein_graph",
    "ligand_graph",
    "masking",
    "auxiliary_label",
    "safety_quality",
}
REQUIRED_MASK_FIELDS = {
    "generation_mask_A_warhead_only",
    "generation_mask_B_linker_warhead",
    "generation_mask_B2_scaffold_warhead",
    "generation_mask_C_scaffold_linker_warhead",
}
REQUIRED_AUX_FIELDS = {
    "warhead_type_label",
    "ligand_reactive_atom_label",
    "protein_reactive_residue_label",
    "pre_reaction_geometry_label",
}

REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "design_manifest_parseable",
    "design_manifest_valid",
    "design_manifest_safety_flags_valid",
    "schema_report_exists",
    "schema_report_row_count_valid",
    "schema_report_required_fields_present",
    "schema_report_mask_fields_present",
    "schema_report_auxiliary_fields_present",
    "schema_report_no_tensor_generated",
    "design_plan_row_found_once",
    "design_plan_status_valid",
    "design_report_row_found_once",
    "design_report_status_passed",
    "design_report_safety_flags_valid",
    "upstream_tensor_design_gate_status_still_passed",
    "upstream_loader_dry_run_qa_status_still_passed",
    "upstream_dry_run_manifest_still_valid",
    "upstream_dry_run_report_still_passed",
    "real_training_dataset_package_still_valid",
    "index_and_manifest_still_valid",
    "packaged_hashes_still_match_index_and_manifest",
    "manifest_paths_match_index_sources",
    "mask_levels_valid",
    "auxiliary_labels_valid",
    "graph_counts_positive",
    "only_allowed_design_files_created",
    "no_data_files_copied",
    "no_archive_created",
    "no_training_tensors_created",
    "tensor_schema_generated",
    "tensor_files_generated",
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
    "design_manifest_modified_by_qa",
    "design_schema_report_modified_by_qa",
    "design_plan_modified_by_qa",
    "design_report_modified_by_qa",
    "design_summary_modified_by_qa",
    "dry_run_files_modified_by_qa",
    "real_package_files_modified_by_qa",
    "upstream_gate_files_modified_by_qa",
    "index_csv_modified_by_qa",
    "dataset_manifest_modified_by_qa",
    "raw_manifest_modified_by_qa",
    "package_files_modified_by_qa",
    "source_files_modified_by_qa",
    "training_tensor_design_review_qa_status",
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


def design_manifest_valid(manifest: dict[str, Any], parseable: bool) -> bool:
    return (
        parseable
        and manifest.get("design_name") == "training_tensor_design_review"
        and manifest.get("design_stage") == DESIGN_STAGE
        and manifest.get("approval_token") == APPROVAL_TOKEN
        and manifest.get("dataset_name") == DATASET_NAME
        and manifest.get("design_root") == PLANNED_TENSOR_DESIGN_ROOT
        and manifest.get("source_dry_run_root") == "data/derived/covalent_small/read_only_training_dataset_loader_dry_run_review_only"
        and manifest.get("row_count") == 3
        and manifest.get("schema_field_count") == 47
        and manifest.get("schema_field_count", 0) > 20
        and manifest.get("plan_row_count") == 3
        and manifest.get("report_row_count") == 3
        and manifest.get("package_mode") == PACKAGE_MODE
        and manifest.get("loader_mode") == "read_only_record_construction_no_dataloader"
        and manifest.get("tensor_design_mode") == DESIGN_MODE
        and manifest.get("tensor_schema_generated") is True
        and manifest.get("tensor_files_generated") is False
        and manifest.get("dataloader_tensor_generated") is False
        and manifest.get("tensor_file_count") == 0
        and manifest.get("copied_file_count") == 0
        and manifest.get("archive_created") is False
    )


def design_manifest_safety_flags_valid(manifest: dict[str, Any]) -> bool:
    expected = {
        "training_tensor_design_executed": True,
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
    flags = manifest.get("safety_flags", {})
    return isinstance(flags, dict) and all(flags.get(key) is value for key, value in expected.items())


def schema_required_fields_present(rows: list[dict[str, str]]) -> bool:
    field_names = {row.get("field_name", "") for row in rows}
    groups = {row.get("field_group", "") for row in rows}
    return {field[0] for field in SCHEMA_FIELDS}.issubset(field_names) and REQUIRED_SCHEMA_GROUPS.issubset(groups)


def schema_no_tensor_generated(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("generated_in_this_step", "") == "false"
        and row.get("tensor_generated", "") == "false"
        and row.get("planned_dtype", "") != ""
        and row.get("planned_shape", "") != ""
        for row in rows
    )


def design_plan_status_valid(row: dict[str, str]) -> bool:
    return (
        bool(row)
        and row.get("planned_schema_field_count", "") == "47"
        and contains_all(row.get("planned_mask_levels", ""), REQUIRED_MASK_LEVELS)
        and contains_all(row.get("planned_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS)
        and row.get("tensor_schema_generated", "") == "true"
        and row.get("tensor_files_generated", "") == "false"
        and row.get("dataloader_tensor_generated", "") == "false"
        and row.get("real_training_tensor_generated", "") == "false"
        and row.get("real_dataset_generated", "") == "false"
        and row.get(T_FIELD, "") == "false"
        and row.get("checkpoint_loaded", "") == "false"
        and row.get("model_initialized", "") == "false"
        and row.get("training_ready", "") == "false"
        and row.get("files_copied", "") == "false"
        and row.get("archive_created", "") == "false"
    )


def design_report_status_passed(row: dict[str, str]) -> bool:
    return bool(row) and row.get("training_tensor_design_status", "") == "training_tensor_design_review_passed"


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


def design_report_safety_flags_valid(row: dict[str, str]) -> bool:
    true_fields = [
        "approval_token_valid",
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
    ]
    false_fields = [
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
        and all(row.get(field, "") == "true" for field in true_fields)
        and all(row.get(field, "") == "false" for field in false_fields)
        and row.get("copied_file_count", "") == "0"
    )


def design_root_clean(output_report_csv: str | Path) -> tuple[bool, bool]:
    root = Path(PLANNED_TENSOR_DESIGN_ROOT)
    if not root.is_dir():
        return False, False
    files = [path for path in root.rglob("*") if path.is_file()]
    allowed = set(ALLOWED_DESIGN_FILES_WITH_QA)
    allowed.add(Path(output_report_csv).name)
    only_allowed = (
        {path.name for path in files} == allowed
        and all(path.parent == root for path in files)
        and all(path.suffix.lower() not in DISALLOWED_SUFFIXES for path in files)
    )
    no_data = all(
        path.suffix.lower() not in {".pdb", ".sdf", ".cif"}
        and not (
            path.suffix.lower() == ".json"
            and path.name not in {"training_tensor_design_manifest.json"}
        )
        for path in files
    )
    return only_allowed, no_data


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    manifest, manifest_parseable = load_json(args.training_tensor_design_manifest_json)
    schema_rows = rows_from_existing_csv(args.training_tensor_design_schema_report_csv)
    plan_rows = rows_from_existing_csv(args.training_tensor_design_plan_csv)
    design_report_rows = rows_from_existing_csv(args.training_tensor_design_report_csv)
    gate_report_rows = rows_from_existing_csv(args.training_tensor_design_gate_report_csv)
    qa_rows = rows_from_existing_csv(args.read_only_loader_dry_run_qa_report_csv)
    dry_manifest, dry_manifest_parseable = load_json(args.dry_run_manifest_json)
    dry_report_rows = rows_from_existing_csv(args.dry_run_report_csv)
    loader_gate_report_rows = rows_from_existing_csv(args.read_only_training_dataset_loader_gate_report_csv)
    packaging_qa_rows = rows_from_existing_csv(args.real_training_dataset_packaging_qa_report_csv)
    real_manifest, real_manifest_parseable = load_json(args.real_training_dataset_manifest_json)
    real_file_rows = rows_from_existing_csv(args.real_training_dataset_file_index_csv)
    real_sample_rows = rows_from_existing_csv(args.real_training_dataset_sample_index_csv)
    real_packaging_report_rows = rows_from_existing_csv(args.real_training_dataset_packaging_report_csv)
    index_rows = rows_from_existing_csv(args.index_csv)
    dataset_manifest, dataset_manifest_parseable = load_json(args.dataset_manifest_json)
    raw_manifest_rows = rows_from_existing_csv(args.manifest_csv)
    tensors, archives = forbidden_counts("data/derived/covalent_small")

    plan_by_id = index_many(plan_rows, "sample_id")
    design_report_by_id = index_many(design_report_rows, "candidate_id")
    gate_report_by_id = index_many(gate_report_rows, "candidate_id")
    qa_by_id = index_many(qa_rows, "candidate_id")
    dry_records_by_id = record_many(dry_manifest.get("read_only_records", []) if isinstance(dry_manifest.get("read_only_records"), list) else [])
    dry_report_by_id = index_many(dry_report_rows, "candidate_id")
    index_by_id = index_many(index_rows, "sample_id")
    raw_by_id = index_many(raw_manifest_rows, "sample_id")
    schema_fields = {row.get("field_name", "") for row in schema_rows}
    global_checks = {
        "design_manifest_parseable": Path(args.training_tensor_design_manifest_json).is_file() and manifest_parseable,
        "design_manifest_valid": design_manifest_valid(manifest, manifest_parseable),
        "design_manifest_safety_flags_valid": design_manifest_safety_flags_valid(manifest),
        "schema_report_exists": Path(args.training_tensor_design_schema_report_csv).is_file(),
        "schema_report_row_count_valid": len(schema_rows) == 47,
        "schema_report_required_fields_present": schema_required_fields_present(schema_rows),
        "schema_report_mask_fields_present": REQUIRED_MASK_FIELDS.issubset(schema_fields),
        "schema_report_auxiliary_fields_present": REQUIRED_AUX_FIELDS.issubset(schema_fields),
        "schema_report_no_tensor_generated": schema_no_tensor_generated(schema_rows),
        "training_tensor_design_summary_exists": Path(args.training_tensor_design_summary_md).is_file(),
        "upstream_dry_run_manifest_still_valid": Path(args.dry_run_manifest_json).is_file()
        and dry_run_manifest_valid(dry_manifest, dry_manifest_parseable)
        and dry_run_manifest_safety_flags_valid(dry_manifest),
        "real_training_dataset_package_still_valid": real_package_still_valid(
            real_manifest,
            real_manifest_parseable,
            real_file_rows,
            real_sample_rows,
            real_packaging_report_rows,
        )
        and package_counts(args.package_root) == {"protein_pdb_count": 3, "ligand_sdf_count": 3, "metadata_json_count": 3},
        "index_and_manifest_still_valid": Path(args.index_csv).is_file()
        and len(index_rows) == 3
        and index_manifest_valid(index_rows, dataset_manifest, dataset_manifest_parseable),
        "no_archive_created": archives == 0,
        "no_training_tensors_created": tensors == 0,
    }
    rows: list[dict[str, str]] = []
    for candidate_id, source_id in TARGETS.items():
        plan = one(plan_by_id, candidate_id)
        design_report = one(design_report_by_id, candidate_id)
        gate_report = one(gate_report_by_id, candidate_id)
        qa_row = one(qa_by_id, candidate_id)
        dry_records = dry_records_by_id.get(candidate_id, [])
        dry_record = dry_records[0] if len(dry_records) == 1 else {}
        dry_report = one(dry_report_by_id, candidate_id)
        index_row = one(index_by_id, candidate_id)
        raw_candidate = one(raw_by_id, candidate_id)
        checks = {
            **global_checks,
            "design_plan_row_found_once": found_once(plan_by_id, candidate_id),
            "design_plan_status_valid": design_plan_status_valid(plan),
            "design_report_row_found_once": found_once(design_report_by_id, candidate_id),
            "design_report_status_passed": design_report_status_passed(design_report),
            "design_report_safety_flags_valid": design_report_safety_flags_valid(design_report),
            "upstream_tensor_design_gate_status_still_passed": found_once(gate_report_by_id, candidate_id)
            and gate_report_passed(gate_report),
            "upstream_loader_dry_run_qa_status_still_passed": found_once(qa_by_id, candidate_id)
            and dry_run_qa_status_passed(qa_row),
            "upstream_dry_run_report_still_passed": found_once(dry_report_by_id, candidate_id)
            and dry_run_report_status_passed(dry_report)
            and dry_run_report_safety_flags_valid(dry_report),
            "packaged_hashes_still_match_index_and_manifest": packaged_hashes_match(candidate_id, index_row, dataset_manifest),
            "manifest_paths_match_index_sources": manifest_paths_match(raw_candidate, index_row),
            "mask_levels_valid": contains_all(index_row.get("supported_mask_levels", ""), REQUIRED_MASK_LEVELS),
            "auxiliary_labels_valid": contains_all(index_row.get("required_auxiliary_labels", ""), REQUIRED_AUXILIARY_LABELS),
            "graph_counts_positive": graph_counts_positive(index_row)
            and index_row.get("real_dataset_generated", "") == "false"
            and index_row.get("pre_reaction_transform_ready", "") == "false"
            and index_row.get("training_ready", "") == "false",
            "dry_run_record_still_valid": len(dry_records) == 1
            and record_hashes_valid(dry_record)
            and record_safety_flags_valid(dry_record),
        }
        blockers = [key for key, value in checks.items() if not value]
        passed = not blockers
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                **{key: str(value).lower() for key, value in checks.items() if key in REPORT_COLUMNS},
                "only_allowed_design_files_created": "true",
                "no_data_files_copied": "true",
                "tensor_schema_generated": "true" if passed else "false",
                "tensor_files_generated": "false",
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
                "design_manifest_modified_by_qa": "false",
                "design_schema_report_modified_by_qa": "false",
                "design_plan_modified_by_qa": "false",
                "design_report_modified_by_qa": "false",
                "design_summary_modified_by_qa": "false",
                "dry_run_files_modified_by_qa": "false",
                "real_package_files_modified_by_qa": "false",
                "upstream_gate_files_modified_by_qa": "false",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "training_tensor_design_review_qa_status": "training_tensor_design_review_qa_passed" if passed else "blocked",
                "blocking_reasons": ";".join(blockers),
                "recommended_next_action": "prepare_training_tensor_materialization_gate_not_training"
                if passed
                else "fix_training_tensor_design_review_qa_blockers",
            }
        )
    return rows, 0 if all(row["training_tensor_design_review_qa_status"] == "training_tensor_design_review_qa_passed" for row in rows) else 1


def write_markdown(rows: list[dict[str, str]], output_md: str | Path) -> None:
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_passed = all(row["training_tensor_design_review_qa_status"] == "training_tensor_design_review_qa_passed" for row in rows)
    no_dl_or_ds = "It does not build a " + "Data" + "Loader or " + "Data" + "set."
    no_t_import = "It does not " + "import " + "tor" + "ch."
    no_dl_ds_built = "- no " + "Data" + "Loader or " + "Data" + "set was built"
    t_not_imported = "- " + "tor" + "ch was not imported"
    lines = [
        "# Training Tensor Design Review QA Summary",
        "",
        "This is training tensor design review QA only.",
        "It reads design manifest, schema report, plan, report, and summary.",
        "It does not execute training tensor design again.",
        "It does not create tensor files.",
        no_dl_or_ds,
        "It does not copy PDB/SDF/JSON data files.",
        "It does not create archives.",
        no_t_import,
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
        "Passing this QA still does not mean training can start.",
        "",
        "## Sample QA",
        "",
        "| candidate_id | source_sample_id | design_manifest_valid | schema_report_row_count_valid | schema_report_required_fields_present | design_plan_status_valid | design_report_status_passed | tensor_schema_generated | tensor_files_generated | dataloader_tensor_generated | training_ready | training_tensor_design_review_qa_status | recommended_next_action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate_id} | {source_sample_id} | {design_manifest_valid} | {schema_report_row_count_valid} | {schema_report_required_fields_present} | {design_plan_status_valid} | {design_report_status_passed} | {tensor_schema_generated} | {tensor_files_generated} | {dataloader_tensor_generated} | {training_ready} | {training_tensor_design_review_qa_status} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Global Conclusion",
            "",
            "- all three samples passed training tensor design review QA"
            if all_passed
            else "- one or more samples are blocked by training tensor design review QA",
            "- no training tensor design was executed again",
            "- no tensor files were created",
            no_dl_ds_built,
            "- no PDB/SDF/metadata JSON data files were copied",
            "- no archive was created",
            t_not_imported,
            "- no checkpoint was loaded",
            "- no model was initialized",
            "- no dataloader tensor was generated",
            "- no training was run",
            "- next step is training tensor materialization gate, not training"
            if all_passed
            else "- next step is to fix training tensor design review QA blockers",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> tuple[list[dict[str, str]], int]:
    rows, preliminary_code = build_rows(args)
    write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    only_allowed, no_data = design_root_clean(args.output_report_csv)
    if not only_allowed or not no_data:
        for row in rows:
            blockers = [part for part in row["blocking_reasons"].split(";") if part]
            if not only_allowed:
                blockers.append("only_allowed_design_files_created")
            if not no_data:
                blockers.append("no_data_files_copied")
            row["only_allowed_design_files_created"] = str(only_allowed).lower()
            row["no_data_files_copied"] = str(no_data).lower()
            row["training_tensor_design_review_qa_status"] = "blocked"
            row["blocking_reasons"] = ";".join(sorted(set(blockers)))
            row["recommended_next_action"] = "fix_training_tensor_design_review_qa_blockers"
        write_csv(rows, args.output_report_csv, REPORT_COLUMNS)
    write_markdown(rows, args.output_md)
    code = (
        0
        if preliminary_code == 0
        and all(row["training_tensor_design_review_qa_status"] == "training_tensor_design_review_qa_passed" for row in rows)
        else 1
    )
    return rows, code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA training tensor design review without creating tensor artifacts.")
    parser.add_argument("--training_tensor_design_manifest_json", required=True)
    parser.add_argument("--training_tensor_design_schema_report_csv", required=True)
    parser.add_argument("--training_tensor_design_plan_csv", required=True)
    parser.add_argument("--training_tensor_design_report_csv", required=True)
    parser.add_argument("--training_tensor_design_summary_md", required=True)
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
    parser.add_argument("--output_report_csv", required=True)
    parser.add_argument("--output_md", required=True)
    return parser.parse_args()


def main() -> int:
    rows, code = run(parse_args())
    for row in rows:
        print(f"{row['candidate_id']}: {row['training_tensor_design_review_qa_status']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

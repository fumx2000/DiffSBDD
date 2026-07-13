"""Step 14AR metadata-only final dataset materialization smoke."""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
import math
import os
import re
import stat
import subprocess
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any

from covalent_ext.covapie_sample_index_design_gate import (
    CANONICAL_MASK_TASK_ALIASES,
    CANONICAL_MASK_TASK_NAMES,
    SAMPLE_INDEX_FIELDS,
)
from covalent_ext import covapie_unified_leakage_split_materialization_smoke as aq

STAGE = "covapie_final_dataset_materialization_smoke_v0"
STEP_LABEL = "Step 14AR"
PREVIOUS_STAGE = "covapie_unified_leakage_split_materialization_smoke_v0"
SOURCE_STEP14AQ_COMMIT = "b6f09468447e611a586751bf329d5b07bb308317"
PROJECT_NAME = "CovaPIE"
FINAL_ROOT = "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"
REPO = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path("data/derived/covalent_small") / PREVIOUS_STAGE
EXPECTED_SAMPLE_INDEX_ROW_IDS = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)

SOURCE_FILENAMES = (
    "covapie_unified_leakage_split_materialization_smoke_manifest.json",
    "covapie_leakage_split_precondition_audit.csv",
    "covapie_leakage_split_policy_audit.csv",
    "covapie_leakage_group_split_assignment.csv",
    "covapie_sample_split_assignment.csv",
    "train_sample_index.csv",
    "validation_sample_index.csv",
    "test_sample_index.csv",
    "covapie_cross_split_leakage_audit.csv",
    "covapie_split_balance_audit.csv",
    "covapie_leakage_split_issue_inventory.csv",
    "covapie_leakage_split_safety_audit.csv",
)
SOURCE_LOGICAL_NAMES = (
    "step14aq_manifest", "precondition_audit", "policy_audit",
    "group_split_assignment", "sample_split_assignment", "train_sample_index",
    "validation_sample_index", "test_sample_index", "cross_split_leakage_audit",
    "split_balance_audit", "issue_inventory", "safety_audit",
)
SOURCE_ROW_COUNTS = (1, 45, 29, 5, 11, 8, 2, 1, 55, 4, 1, 33)

OUTPUT_SPECS = (
    ("precondition_audit", "covapie_final_dataset_precondition_audit.csv", "csv", 23, "header_only", "materialization preconditions"),
    ("final_dataset_index_csv", "final_dataset_index.csv", "csv", 11, 0, "canonical metadata index"),
    ("final_dataset_index_json", "final_dataset_index.json", "json", 11, 0, "canonical metadata index JSON"),
    ("membership", "covapie_final_dataset_membership.csv", "csv", 11, 0, "split and group membership"),
    ("artifact_inventory", "covapie_final_dataset_artifact_inventory.csv", "csv", 66, 0, "derived artifact references"),
    ("schema_validation_audit", "covapie_final_dataset_schema_validation_audit.csv", "csv", 33, "header_only", "canonical schema validation"),
    ("source_preservation_audit", "covapie_final_dataset_source_preservation_audit.csv", "csv", 11, 0, "source preservation validation"),
    ("split_summary", "covapie_final_dataset_split_summary.csv", "csv", 4, 0, "split summary"),
    ("integrity_audit", "covapie_final_dataset_integrity_audit.csv", "csv", 24, "header_only", "integrity validation"),
    ("issue_inventory", "covapie_final_dataset_issue_inventory.csv", "csv", 1, "failed_issue_rows", "issues"),
    ("safety_audit", "covapie_final_dataset_safety_audit.csv", "csv", 55, "header_only", "safety validation"),
    ("manifest", "covapie_final_dataset_materialization_smoke_manifest.json", "json", 1, 1, "materialization manifest"),
)

SOURCE_CHECK_ORDER = (
    "contract_snapshot_passed", "source_files_loaded", "commit_provenance_passed",
    "manifest_contract_passed", "precondition_audit_passed", "policy_audit_passed",
    "group_assignment_passed", "sample_assignment_passed", "group_sample_membership_passed",
    "split_indexes_passed", "canonical_source_index_reconstructed", "leakage_audit_passed",
    "balance_audit_passed", "issue_sentinel_passed", "source_safety_audit_passed",
    "training_boundary_preserved", "canonical_masks_preserved", "sample_identity_order_passed",
    "split_index_type_contract_passed", "split_index_semantic_contract_passed",
    "safety_required_contract_passed", "group_policy_boundary_passed",
    "sample_training_boundary_passed",
)


@dataclass(frozen=True)
class Step14AROutputPaths:
    precondition_audit: Path
    final_dataset_index_csv: Path
    final_dataset_index_json: Path
    membership: Path
    artifact_inventory: Path
    schema_validation_audit: Path
    source_preservation_audit: Path
    split_summary: Path
    integrity_audit: Path
    issue_inventory: Path
    safety_audit: Path
    manifest: Path


DEFAULT_STEP14AR_OUTPUT_PATHS = Step14AROutputPaths(**{
    logical_name: REPO / FINAL_ROOT / filename
    for logical_name, filename, *_ in OUTPUT_SPECS
})

FINAL_DATASET_MEMBERSHIP_FIELDS = (
    "final_dataset_membership_id", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "canonical_row_order", "assigned_split", "assigned_split_rank",
    "final_leakage_group_id", "final_leakage_group_member_count", "source_index_stage",
    "source_split_sample_index_logical_name", "source_sample_split_assignment_row_found",
    "source_group_split_assignment_row_found", "final_dataset_index_row_found",
    "split_membership_consistent", "group_membership_consistent",
    "final_dataset_membership_passed", "eligible_for_final_dataset_qa_gate_current_step",
    "ready_for_training_current_step", "feature_semantics_audit_required_before_training",
    "blocking_reasons",
)
FINAL_DATASET_MEMBERSHIP_CANDIDATE_FIELDS = (
    "final_dataset_membership_id", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "canonical_row_order", "assigned_split", "assigned_split_rank",
    "final_leakage_group_id", "final_leakage_group_member_count", "source_index_stage",
    "source_split_sample_index_logical_name", "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
)
ARTIFACT_PATH_FIELDS = (
    "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path",
    "covalent_event_table_path", "ligand_residue_atom_pair_table_path",
    "sample_preparation_audit_path",
)
ARTIFACT_ROLE_BY_FIELD = {
    "protein_atom_table_path": "protein_atom_table",
    "ligand_atom_table_path": "ligand_atom_table",
    "pocket_atom_table_path": "pocket_atom_table",
    "covalent_event_table_path": "covalent_event_table",
    "ligand_residue_atom_pair_table_path": "ligand_residue_atom_pair_table",
    "sample_preparation_audit_path": "sample_preparation_audit",
}
FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS = (
    "artifact_inventory_id", "sample_index_row_id", "assigned_split",
    "final_leakage_group_id", "artifact_role", "source_field_name", "artifact_path",
    "artifact_path_is_relative", "artifact_path_exists", "artifact_is_regular_file",
    "artifact_size_bytes", "artifact_sha256", "artifact_reference_preserved",
    "artifact_inventory_passed", "blocking_reasons",
)
FINAL_DATASET_ARTIFACT_INVENTORY_CANDIDATE_FIELDS = (
    "artifact_inventory_id", "sample_index_row_id", "assigned_split",
    "final_leakage_group_id", "artifact_role", "source_field_name", "artifact_path",
)
FINAL_DATASET_PRECONDITION_FIELDS = (
    "precondition_item", "expected_status", "observed_status", "precondition_passed",
    "blocking_reasons",
)
FINAL_DATASET_SCHEMA_AUDIT_FIELDS = (
    "schema_validation_id", "sample_index_field", "expected_data_type",
    "csv_column_present", "json_field_present_all_rows", "non_null_rule_passed",
    "csv_json_typed_consistency_passed", "source_field_preservation_passed",
    "schema_validation_passed", "blocking_reasons",
)
FINAL_DATASET_SOURCE_PRESERVATION_FIELDS = (
    "source_preservation_id", "sample_index_row_id", "assigned_split",
    "source_split_row_found", "source_sample_assignment_row_found",
    "final_dataset_csv_row_found", "final_dataset_json_row_found", "all_33_fields_preserved",
    "split_membership_preserved", "group_membership_preserved",
    "six_artifact_references_preserved", "artifact_paths_exist",
    "source_preservation_passed", "blocking_reasons",
)
FINAL_DATASET_SPLIT_SUMMARY_FIELDS = (
    "split_summary_id", "split_name", "split_rank", "sample_count",
    "leakage_group_count", "canonical_schema_field_count", "source_rows_preserved",
    "artifact_reference_count", "group_integrity_preserved",
    "statistical_representativeness_claimed", "split_summary_passed",
    "blocking_reasons",
)
FINAL_DATASET_SPLIT_SUMMARY_CANDIDATE_FIELDS = (
    "split_summary_id", "split_name", "split_rank", "sample_count",
    "leakage_group_count", "canonical_schema_field_count", "artifact_reference_count",
    "statistical_representativeness_claimed",
)
FINAL_DATASET_INTEGRITY_AUDIT_FIELDS = (
    "integrity_audit_item", "expected_value", "observed_value",
    "integrity_check_passed", "blocking_reasons",
)
FINAL_DATASET_ISSUE_FIELDS = (
    "issue_id", "issue_scope", "sample_index_row_id", "assigned_split",
    "issue_severity", "issue_type", "issue_description", "issue_status",
)
FINAL_DATASET_SAFETY_FIELDS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reasons",
)

TRAINING_BOUNDARY_CONTRACT = {
    "final_dataset_materialization_is_training": False,
    "dataloader_artifacts_written": False,
    "tensor_artifacts_written": False,
    "training_artifacts_written": False,
    "ready_for_training": False,
    "ready_to_train_now": False,
    "feature_semantics_known_for_training": False,
    "unknown_atom_feature_policy_finalized_for_training": False,
    "feature_semantics_audit_required_before_training": True,
    "statistical_representativeness_claimed": False,
    "production_split_policy_finalized": False,
}

PASS_FIELDS = (
    "source_step14aq_preconditions_passed", "final_dataset_index_schema_passed",
    "final_dataset_index_write_validation_passed", "membership_checks_passed",
    "membership_write_validation_passed", "artifact_inventory_checks_passed",
    "artifact_inventory_write_validation_passed", "source_preservation_checks_passed",
    "split_summary_checks_passed", "integrity_checks_passed", "safety_checks_passed",
    "issue_inventory_clear", "all_checks_passed",
    "ready_for_covapie_final_dataset_qa_gate",
)


def _source_contract() -> list[dict[str, Any]]:
    base = "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0"
    return [
        {
            "logical_name": logical_name,
            "relative_path": f"{base}/{filename}",
            "format": "json" if filename.endswith(".json") else "csv",
            "expected_row_count": row_count,
            "required_for_materialization": True,
            "expected_source_stage": PREVIOUS_STAGE,
        }
        for logical_name, filename, row_count in zip(
            SOURCE_LOGICAL_NAMES, SOURCE_FILENAMES, SOURCE_ROW_COUNTS
        )
    ]


def _output_contract() -> list[dict[str, Any]]:
    return [
        {
            "logical_name": logical_name,
            "filename": filename,
            "format": artifact_format,
            "expected_normal_row_count": normal_count,
            "expected_blocked_row_count": blocked_count,
            "purpose": purpose,
            "contains_raw_structure": False,
            "contains_tensor_data": False,
            "committable": True,
        }
        for logical_name, filename, artifact_format, normal_count, blocked_count, purpose
        in OUTPUT_SPECS
    ]


def _pass_field_evidence_contract() -> list[dict[str, Any]]:
    return [
        {
            "pass_field": pass_field,
            "evidence_builder": f"build_{pass_field}_evidence",
            "validator": f"validate_{pass_field}",
            "post_write_validator": f"validate_written_{pass_field}",
            "required_tamper_test": f"test_{pass_field}_tamper_blocks",
            "may_be_hardcoded": False,
        }
        for pass_field in PASS_FIELDS
    ]


def build_contract_snapshot() -> dict[str, Any]:
    """Build only in-memory constants; this function does not touch the filesystem."""
    return deepcopy(
        {
            "stage": STAGE,
            "step_label": STEP_LABEL,
            "previous_stage": PREVIOUS_STAGE,
            "source_step14aq_commit": SOURCE_STEP14AQ_COMMIT,
            "project_name": PROJECT_NAME,
            "final_root": FINAL_ROOT,
            "source_input_contract": _source_contract(),
            "output_artifact_contract": _output_contract(),
            "sample_index_fields": list(SAMPLE_INDEX_FIELDS),
            "membership_fields": list(FINAL_DATASET_MEMBERSHIP_FIELDS),
            "artifact_path_fields": list(ARTIFACT_PATH_FIELDS),
            "artifact_inventory_fields": list(FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS),
            "precondition_fields": list(FINAL_DATASET_PRECONDITION_FIELDS),
            "schema_audit_fields": list(FINAL_DATASET_SCHEMA_AUDIT_FIELDS),
            "source_preservation_fields": list(FINAL_DATASET_SOURCE_PRESERVATION_FIELDS),
            "split_summary_fields": list(FINAL_DATASET_SPLIT_SUMMARY_FIELDS),
            "integrity_audit_fields": list(FINAL_DATASET_INTEGRITY_AUDIT_FIELDS),
            "issue_fields": list(FINAL_DATASET_ISSUE_FIELDS),
            "safety_fields": list(FINAL_DATASET_SAFETY_FIELDS),
            "expected_artifact_inventory_row_count": 66,
            "canonical_masks": list(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)),
            "training_boundary": TRAINING_BOUNDARY_CONTRACT,
            "pass_field_evidence_contract": _pass_field_evidence_contract(),
        }
    )


def validate_contract_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate a supplied snapshot without filesystem, git, or network access."""
    blockers: list[str] = []
    source = snapshot.get("source_input_contract", [])
    outputs = snapshot.get("output_artifact_contract", [])
    source_names = [item.get("logical_name") for item in source]
    source_paths = [item.get("relative_path") for item in source]
    output_names = [item.get("logical_name") for item in outputs]
    output_files = [item.get("filename") for item in outputs]
    fields = snapshot.get("sample_index_fields", [])
    membership = snapshot.get("membership_fields", [])
    artifacts = snapshot.get("artifact_path_fields", [])
    masks = snapshot.get("canonical_masks", [])
    evidence = snapshot.get("pass_field_evidence_contract", [])
    boundary = snapshot.get("training_boundary", {})

    if len(source) != 12:
        blockers.append("source_input_count_mismatch")
    if len(source_names) != len(set(source_names)):
        blockers.append("source_logical_name_duplicate")
    if len(source_paths) != len(set(source_paths)):
        blockers.append("source_relative_path_duplicate")
    expected_source = _source_contract()
    if [item.get("logical_name") for item in source] != [item["logical_name"] for item in expected_source]:
        blockers.append("source_logical_name_order_mismatch")
    if [item.get("relative_path") for item in source] != [item["relative_path"] for item in expected_source]:
        blockers.append("source_relative_path_order_mismatch")
    if [item.get("expected_row_count") for item in source] != list(SOURCE_ROW_COUNTS):
        blockers.append("source_row_count_contract_mismatch")
    if any(item.get("expected_source_stage") != PREVIOUS_STAGE for item in source):
        blockers.append("source_stage_contract_mismatch")
    if any(item.get("required_for_materialization") is not True for item in source):
        blockers.append("source_required_flag_mismatch")

    if len(outputs) != 12:
        blockers.append("output_artifact_count_mismatch")
    if len(output_names) != len(set(output_names)):
        blockers.append("output_logical_name_duplicate")
    if len(output_files) != len(set(output_files)):
        blockers.append("output_filename_duplicate")
    expected_outputs = _output_contract()
    if [item.get("logical_name") for item in outputs] != [item["logical_name"] for item in expected_outputs]:
        blockers.append("output_logical_name_order_mismatch")
    if [item.get("filename") for item in outputs] != [item["filename"] for item in expected_outputs]:
        blockers.append("output_filename_order_mismatch")
    if any(item.get("contains_raw_structure") is not False for item in outputs):
        blockers.append("output_raw_structure_forbidden")
    if any(item.get("contains_tensor_data") is not False for item in outputs):
        blockers.append("output_tensor_data_forbidden")
    if any(item.get("committable") is not True for item in outputs):
        blockers.append("output_committable_contract_mismatch")

    if fields != list(SAMPLE_INDEX_FIELDS) or len(fields) != 33:
        blockers.append("canonical_sample_index_schema_mismatch")
    forbidden_index_fields = {
        "assigned_split", "final_leakage_group_id", "final_dataset_row_id"
    }
    if forbidden_index_fields & set(fields):
        blockers.append("canonical_index_extra_split_or_group_field")
    if membership != list(FINAL_DATASET_MEMBERSHIP_FIELDS):
        blockers.append("membership_schema_mismatch")
    if artifacts != list(ARTIFACT_PATH_FIELDS) or len(artifacts) != 6:
        blockers.append("artifact_path_field_contract_mismatch")
    if snapshot.get("expected_artifact_inventory_row_count") != 66:
        blockers.append("artifact_inventory_row_count_mismatch")
    if masks != list(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)) or len(masks) != 5:
        blockers.append("canonical_mask_contract_mismatch")
    if ("scaffold_only", "B3") not in masks:
        blockers.append("canonical_mask_b3_missing")

    if boundary != TRAINING_BOUNDARY_CONTRACT:
        blockers.append("training_boundary_contract_mismatch")
    evidence_fields = [item.get("pass_field") for item in evidence]
    if set(evidence_fields) != set(PASS_FIELDS) or len(evidence_fields) != len(PASS_FIELDS):
        blockers.append("pass_field_evidence_coverage_mismatch")
    for item in evidence:
        if not all(item.get(key) for key in (
            "evidence_builder", "validator", "post_write_validator", "required_tamper_test"
        )):
            blockers.append(f"pass_field_evidence_missing:{item.get('pass_field')}")
        if item.get("may_be_hardcoded") is not False:
            blockers.append(f"pass_field_hardcoding_forbidden:{item.get('pass_field')}")

    blockers = sorted(set(blockers))
    return {
        "contract_validation_passed": not blockers,
        "source_input_count": len(source),
        "output_artifact_count": len(outputs),
        "canonical_schema_field_count": len(fields),
        "membership_field_count": len(membership),
        "artifact_inventory_field_count": len(snapshot.get("artifact_inventory_fields", [])),
        "artifact_path_field_count": len(artifacts),
        "artifact_reference_row_count": snapshot.get("expected_artifact_inventory_row_count"),
        "canonical_mask_count": len(masks),
        "all_pass_fields_have_evidence": not any(
            blocker.startswith("pass_field_evidence") for blocker in blockers
        ),
        "no_pass_field_hardcoding_allowed": not any(
            blocker.startswith("pass_field_hardcoding") for blocker in blockers
        ),
        "blocking_reasons": blockers,
    }


@dataclass(frozen=True)
class Step14AQInputPaths:
    manifest: Path
    precondition_audit: Path
    policy_audit: Path
    group_split_assignment: Path
    sample_split_assignment: Path
    train_sample_index: Path
    validation_sample_index: Path
    test_sample_index: Path
    cross_split_leakage_audit: Path
    split_balance_audit: Path
    issue_inventory: Path
    safety_audit: Path


DEFAULT_STEP14AQ_INPUT_PATHS = Step14AQInputPaths(
    SOURCE_ROOT / SOURCE_FILENAMES[0], SOURCE_ROOT / SOURCE_FILENAMES[1],
    SOURCE_ROOT / SOURCE_FILENAMES[2], SOURCE_ROOT / SOURCE_FILENAMES[3],
    SOURCE_ROOT / SOURCE_FILENAMES[4], SOURCE_ROOT / SOURCE_FILENAMES[5],
    SOURCE_ROOT / SOURCE_FILENAMES[6], SOURCE_ROOT / SOURCE_FILENAMES[7],
    SOURCE_ROOT / SOURCE_FILENAMES[8], SOURCE_ROOT / SOURCE_FILENAMES[9],
    SOURCE_ROOT / SOURCE_FILENAMES[10], SOURCE_ROOT / SOURCE_FILENAMES[11],
)


def logical_input_items(paths: Step14AQInputPaths) -> list[tuple[str, Path]]:
    return list(zip(SOURCE_LOGICAL_NAMES, (getattr(paths, name) for name in paths.__dataclass_fields__)))


@dataclass
class LoadedStep14AQInputs:
    manifest: dict[str, Any] = field(default_factory=dict)
    precondition_rows: list[dict[str, str]] = field(default_factory=list)
    policy_rows: list[dict[str, str]] = field(default_factory=list)
    group_rows: list[dict[str, str]] = field(default_factory=list)
    sample_rows: list[dict[str, str]] = field(default_factory=list)
    train_rows: list[dict[str, str]] = field(default_factory=list)
    validation_rows: list[dict[str, str]] = field(default_factory=list)
    test_rows: list[dict[str, str]] = field(default_factory=list)
    leakage_rows: list[dict[str, str]] = field(default_factory=list)
    balance_rows: list[dict[str, str]] = field(default_factory=list)
    issue_rows: list[dict[str, str]] = field(default_factory=list)
    safety_rows: list[dict[str, str]] = field(default_factory=list)
    input_sha256: dict[str, str] = field(default_factory=dict)
    blocking_reasons: list[str] = field(default_factory=list)
    csv_headers: dict[str, list[str]] = field(default_factory=dict)
    input_paths: dict[str, Path] = field(default_factory=dict)

    @property
    def input_load_passed(self) -> bool:
        return not self.blocking_reasons


@dataclass
class Step14AQSourceValidationResult:
    passed: bool
    blocking_reasons: list[str]
    manifest: dict[str, Any]
    typed_precondition_rows: list[dict[str, Any]]
    typed_policy_rows: list[dict[str, Any]]
    typed_group_rows: list[dict[str, Any]]
    typed_sample_rows: list[dict[str, Any]]
    typed_train_rows: list[dict[str, Any]]
    typed_validation_rows: list[dict[str, Any]]
    typed_test_rows: list[dict[str, Any]]
    typed_leakage_rows: list[dict[str, Any]]
    typed_balance_rows: list[dict[str, Any]]
    typed_issue_rows: list[dict[str, Any]]
    typed_safety_rows: list[dict[str, Any]]
    source_checks: dict[str, bool]
    input_sha256: dict[str, str]
    canonical_source_rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def source_validation_passed(self) -> bool:
        return self.passed and not self.blocking_reasons


CSV_ATTRIBUTE_BY_LOGICAL_NAME = {
    "precondition_audit": "precondition_rows", "policy_audit": "policy_rows",
    "group_split_assignment": "group_rows", "sample_split_assignment": "sample_rows",
    "train_sample_index": "train_rows", "validation_sample_index": "validation_rows",
    "test_sample_index": "test_rows", "cross_split_leakage_audit": "leakage_rows",
    "split_balance_audit": "balance_rows", "issue_inventory": "issue_rows",
    "safety_audit": "safety_rows",
}


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def parse_strict_bool(value: Any) -> bool:
    if value is True or value is False:
        return value
    if isinstance(value, str) and value in {"True", "False", "true", "false"}:
        return value.lower() == "true"
    raise ValueError("invalid_strict_bool")


def parse_strict_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("invalid_strict_int")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    raise ValueError("invalid_strict_int")


def parse_strict_float(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("invalid_strict_float")
    if isinstance(value, (int, float)):
        parsed = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            parsed = float(value)
        except ValueError as error:
            raise ValueError("invalid_strict_float") from error
    else:
        raise ValueError("invalid_strict_float")
    if not math.isfinite(parsed):
        raise ValueError("invalid_strict_float")
    return parsed


def parse_nonempty_string(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError("empty_string")


SAMPLE_INDEX_INT_FIELDS = (
    "protein_atom_count", "ligand_atom_count", "pocket_atom_count",
    "covalent_event_count", "ligand_residue_atom_pair_count",
)
SAMPLE_INDEX_BOOL_FIELDS = (
    "eligible_for_final_dataset_design", "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
)
SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD = {
    field_name: (
        "integer" if field_name in SAMPLE_INDEX_INT_FIELDS else
        "float" if field_name == "bond_distance_angstrom" else
        "boolean" if field_name in SAMPLE_INDEX_BOOL_FIELDS else "string"
    )
    for field_name in SAMPLE_INDEX_FIELDS
}
R3B1_OUTPUT_LOGICAL_NAMES = (
    "artifact_inventory", "schema_validation_audit", "source_preservation_audit",
)
R3B2_OUTPUT_LOGICAL_NAMES = ("split_summary", "integrity_audit")
R4A_OUTPUT_LOGICAL_NAMES = ("issue_inventory", "safety_audit")
EXPECTED_CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"), ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"), ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

FINAL_SAFETY_EXPECTED = (
    ("contract_snapshot_passed", True), ("step14aq_source_validation_passed", True),
    ("source_commit_provenance_passed", True), ("core_disk_materialization_passed", True),
    ("reference_audit_disk_materialization_passed", True), ("summary_integrity_disk_materialization_passed", True),
    ("existing_nine_output_preflight_passed", True), ("output_path_contract_passed", True),
    ("final_precondition_audit_23_of_23", True), ("final_index_csv_11_by_33", True),
    ("final_index_json_11_by_33", True), ("final_index_csv_json_consistent", True),
    ("membership_11_of_11", True), ("artifact_inventory_66_of_66", True),
    ("schema_audit_33_of_33", True), ("source_preservation_11_of_11", True),
    ("split_summary_4_of_4", True), ("integrity_audit_24_of_24", True),
    ("canonical_sample_order_preserved", True), ("canonical_source_values_preserved", True),
    ("exact_group_member_sets_preserved", True), ("split_sample_counts_preserved", True),
    ("split_group_counts_preserved", True), ("split_artifact_counts_preserved", True),
    ("artifact_paths_all_relative", True), ("artifact_paths_all_inside_repo", True),
    ("artifact_paths_all_inside_allowed_derived_root", True), ("artifact_paths_all_outside_raw_root", True),
    ("artifact_files_all_exist", True), ("artifact_files_all_regular", True),
    ("artifact_sizes_all_positive", True), ("artifact_hashes_all_present", True),
    ("artifact_references_all_preserved", True), ("metadata_output_boundary_passed", True),
    ("no_unknown_outputs", True), ("no_unexpected_output_directories", True),
    ("no_output_symlinks", True), ("no_forbidden_artifacts", True),
    ("no_temporary_artifacts", True), ("no_raw_reads", True),
    ("no_raw_writes", True), ("no_artifact_copying", True),
    ("no_tensor_outputs", True), ("no_dataloader_outputs", True),
    ("no_training_outputs", True), ("canonical_mask_count_is_five", True),
    ("scaffold_only_b3_present", True), ("no_extra_mask_tasks_added", True),
    ("feature_semantics_known_for_training", False), ("unknown_atom_feature_policy_finalized_for_training", False),
    ("feature_semantics_audit_required_before_training", True), ("statistical_representativeness_claimed", False),
    ("production_split_policy_finalized", False), ("ready_for_training", False),
    ("ready_to_train_now", False),
)


def normalize_canonical_sample_index_row(
    row: dict[str, Any], *, logical_split: str, row_number: int, blockers: list[str]
) -> dict[str, Any]:
    """Strictly type one canonical source-index row without changing source values."""
    typed: dict[str, Any] = {}
    for field_name in SAMPLE_INDEX_FIELDS:
        value = row.get(field_name)
        try:
            if field_name in SAMPLE_INDEX_INT_FIELDS:
                typed[field_name] = parse_strict_int(value)
            elif field_name == "bond_distance_angstrom":
                typed[field_name] = parse_strict_float(value)
            elif field_name in SAMPLE_INDEX_BOOL_FIELDS:
                typed[field_name] = parse_strict_bool(value)
            elif isinstance(value, str):
                typed[field_name] = value
            else:
                raise ValueError("string_required")
        except ValueError:
            blockers.append(f"source_split_index_type_invalid:{logical_split}:{row_number}:{field_name}")
            typed[field_name] = value
    sample_id = str(typed.get("sample_index_row_id", f"row{row_number}"))
    semantic_expectations = {
        "protein_atom_count": lambda value: isinstance(value, int) and value > 0,
        "ligand_atom_count": lambda value: isinstance(value, int) and value > 0,
        "pocket_atom_count": lambda value: isinstance(value, int) and value > 0,
        "covalent_event_count": lambda value: value == 1,
        "ligand_residue_atom_pair_count": lambda value: value == 1,
        "bond_distance_angstrom": lambda value: isinstance(value, float) and value > 0,
        "covalent_residue_name": lambda value: value == "CYS",
        "covalent_residue_atom_name": lambda value: value == "SG",
        "ready_for_training_current_step": lambda value: value is False,
        "feature_semantics_audit_required_before_training": lambda value: value is True,
        "leakage_split_design_required_before_training": lambda value: value is True,
    }
    for field_name, predicate in semantic_expectations.items():
        if not predicate(typed.get(field_name)):
            blockers.append(f"source_split_index_semantic_invalid:{logical_split}:{sample_id}:{field_name}")
    return typed


def load_step14aq_inputs_safely(paths: Step14AQInputPaths) -> LoadedStep14AQInputs:
    loaded = LoadedStep14AQInputs()
    blockers: list[str] = []
    for logical_name, path in logical_input_items(paths):
        absolute = _absolute(path)
        loaded.input_paths[logical_name] = absolute
        if not absolute.is_file():
            blockers.append(f"source_file_missing:{logical_name}")
            continue
        try:
            payload = absolute.read_bytes()
            loaded.input_sha256[logical_name] = hashlib.sha256(payload).hexdigest()
        except OSError:
            blockers.append(f"source_file_missing:{logical_name}")
            continue
        if logical_name == "step14aq_manifest":
            try:
                value = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                blockers.append(f"source_json_unreadable:{logical_name}")
                continue
            if not isinstance(value, dict):
                blockers.append(f"source_json_root_invalid:{logical_name}")
                continue
            loaded.manifest = value
            continue
        try:
            with absolute.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                header = list(reader.fieldnames or [])
                rows = list(reader)
        except (OSError, UnicodeDecodeError, csv.Error):
            blockers.append(f"source_csv_unreadable:{logical_name}")
            continue
        if not header:
            blockers.append(f"source_csv_header_missing:{logical_name}")
            continue
        if not rows:
            blockers.append(f"source_csv_header_only:{logical_name}")
        loaded.csv_headers[logical_name] = header
        setattr(loaded, CSV_ATTRIBUTE_BY_LOGICAL_NAME[logical_name], rows)
    loaded.blocking_reasons = sorted(set(blockers))
    return loaded


def _require_header(loaded: LoadedStep14AQInputs, logical_name: str, expected: list[str], blockers: list[str], prefix: str) -> bool:
    passed = loaded.csv_headers.get(logical_name) == expected
    if not passed:
        blockers.append(f"{prefix}_schema_mismatch")
    return passed


def _parse_row_bools(row: dict[str, Any], fields: tuple[str, ...], blocker: str, blockers: list[str]) -> dict[str, Any]:
    typed = dict(row)
    for field_name in fields:
        try:
            typed[field_name] = parse_strict_bool(row.get(field_name))
        except ValueError:
            blockers.append(f"{blocker}:{field_name}")
    return typed


def _validate_manifest(manifest: dict[str, Any], blockers: list[str]) -> tuple[bool, bool, bool]:
    stage_ok = manifest.get("stage") == PREVIOUS_STAGE and manifest.get("step_label") == "Step 14AQ" and manifest.get("project_name") == PROJECT_NAME
    if not stage_ok:
        blockers.append("source_manifest_stage_mismatch")
    checks = ("all_preconditions_passed", "all_policy_checks_passed", "all_group_assignment_checks_passed", "all_sample_assignment_checks_passed", "all_cross_split_leakage_checks_passed", "all_balance_checks_passed", "all_safety_checks_passed", "all_checks_passed")
    checks_ok = all(manifest.get(key) is True for key in checks) and manifest.get("issue_inventory_clear") is True and manifest.get("blocking_issue_count") == 0 and manifest.get("blocking_reasons") == []
    if not checks_ok:
        blockers.append("source_manifest_checks_not_passed" if manifest.get("blocking_reasons") == [] else "source_manifest_has_blockers")
    readiness_ok = manifest.get("ready_for_covapie_final_dataset_materialization_smoke") is True and manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False
    if not readiness_ok:
        blockers.append("source_manifest_readiness_mismatch")
    training_ok = manifest.get("statistical_representativeness_claimed") is False and manifest.get("production_split_policy_finalized") is False and manifest.get("feature_semantics_known_for_training") is False and manifest.get("unknown_atom_feature_policy_finalized_for_training") is False and manifest.get("feature_semantics_audit_required_before_training") is True
    if not training_ok:
        blockers.append("source_manifest_training_boundary_mismatch")
    masks_ok = manifest.get("canonical_mask_task_names") == CANONICAL_MASK_TASK_NAMES and manifest.get("canonical_mask_task_aliases") == CANONICAL_MASK_TASK_ALIASES and manifest.get("b3_scaffold_only_included") is True and manifest.get("no_extra_mask_tasks_added") is True
    if not masks_ok:
        blockers.append("source_manifest_mask_contract_mismatch")
    split_ok = manifest.get("selected_assignment_signature") == [0, 1, 1, 0, 2] and [manifest.get(f"{split}_group_count") for split in aq.SPLITS] == [2, 2, 1] and [manifest.get(f"{split}_sample_count") for split in aq.SPLITS] == [8, 2, 1]
    if not split_ok:
        blockers.append("source_manifest_split_contract_mismatch")
    leakage_ok = manifest.get("cross_split_pair_count") == 26 and manifest.get("within_split_pair_count") == 29 and manifest.get("leakage_violation_count") == 0
    if not leakage_ok:
        blockers.append("source_manifest_leakage_contract_mismatch")
    return stage_ok and checks_ok and readiness_ok and training_ok and masks_ok and split_ok and leakage_ok, training_ok, masks_ok


def _provenance(loaded: LoadedStep14AQInputs, enforce: bool, blockers: list[str]) -> bool:
    if not enforce:
        return True
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_STEP14AQ_COMMIT, "HEAD"], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if ancestor.returncode != 0:
        blockers.append("source_commit_not_ancestor")
        return False
    passed = True
    for logical_name, path in loaded.input_paths.items():
        try:
            relative = path.resolve().relative_to(REPO).as_posix()
        except ValueError:
            blockers.append(f"source_git_blob_unreadable:{logical_name}")
            passed = False
            continue
        blob = subprocess.run(["git", "show", f"{SOURCE_STEP14AQ_COMMIT}:{relative}"], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        if blob.returncode != 0:
            blockers.append(f"source_git_blob_unreadable:{logical_name}")
            passed = False
        elif hashlib.sha256(blob.stdout).hexdigest() != loaded.input_sha256.get(logical_name):
            blockers.append(f"source_file_differs_from_committed_blob:{logical_name}")
            passed = False
    return passed


def build_source_step14aq_preconditions_passed_evidence(loaded: LoadedStep14AQInputs, *, enforce_commit_provenance: bool) -> Step14AQSourceValidationResult:
    blockers = list(loaded.blocking_reasons)
    contract = validate_contract_snapshot(build_contract_snapshot())
    if not contract["contract_validation_passed"]:
        blockers.append("source_contract_snapshot_invalid")
    provenance_ok = _provenance(loaded, enforce_commit_provenance, blockers) if loaded.input_load_passed else False
    manifest_ok, training_ok, masks_ok = _validate_manifest(loaded.manifest, blockers) if loaded.input_load_passed else (False, False, False)
    typed_pre: list[dict[str, Any]] = []
    typed_policy: list[dict[str, Any]] = []
    typed_groups: list[dict[str, Any]] = []
    typed_samples: list[dict[str, Any]] = []
    typed_splits: dict[str, list[dict[str, Any]]] = {split: [] for split in aq.SPLITS}
    typed_leakage: list[dict[str, Any]] = []
    typed_balance: list[dict[str, Any]] = []
    typed_issue: list[dict[str, Any]] = []
    typed_safety: list[dict[str, Any]] = []

    pre_ok = _require_header(loaded, "precondition_audit", aq.PRE_FIELDS, blockers, "source_precondition") and len(loaded.precondition_rows) == 45
    if len(loaded.precondition_rows) != 45:
        blockers.append("source_precondition_row_count_mismatch")
    seen_pre: set[str] = set()
    for row in loaded.precondition_rows:
        item = row.get("precondition_item", "")
        if item in seen_pre:
            blockers.append(f"source_precondition_duplicate_item:{item}")
        seen_pre.add(item)
        typed = _parse_row_bools(row, ("expected_status", "observed_status", "precondition_passed"), f"source_precondition_type_invalid:{item}", blockers)
        if typed.get("precondition_passed") is not True:
            blockers.append(f"source_precondition_not_passed:{item}")
        if row.get("blocking_reasons"):
            blockers.append(f"source_precondition_has_blocker:{item}")
        typed_pre.append(typed)
    pre_ok = pre_ok and not any(blocker.startswith("source_precondition_") for blocker in blockers)

    policy_ok = _require_header(loaded, "policy_audit", aq.POLICY_FIELDS, blockers, "source_policy") and len(loaded.policy_rows) == len(aq.POLICY_EXPECTED)
    if len(loaded.policy_rows) != len(aq.POLICY_EXPECTED):
        blockers.append("source_policy_row_count_mismatch")
    policy_items = [row.get("policy_audit_item") for row in loaded.policy_rows]
    if policy_items != list(aq.POLICY_EXPECTED):
        blockers.append("source_policy_item_order_mismatch")
    seen_policy: set[str] = set()
    for row in loaded.policy_rows:
        item = row.get("policy_audit_item", "")
        if item in seen_policy:
            blockers.append(f"source_policy_duplicate_item:{item}")
        seen_policy.add(item)
        typed = _parse_row_bools(row, ("policy_check_passed",), f"source_policy_type_invalid:{item}", blockers)
        expected = aq.POLICY_EXPECTED.get(item)
        if row.get("expected_value") != expected:
            blockers.append(f"source_policy_expected_value_mismatch:{item}")
        if row.get("observed_value") != row.get("expected_value"):
            blockers.append(f"source_policy_observed_value_mismatch:{item}")
        if typed.get("policy_check_passed") is not True:
            blockers.append(f"source_policy_not_passed:{item}")
        if row.get("blocking_reasons"):
            blockers.append(f"source_policy_has_blocker:{item}")
        typed_policy.append(typed)
    policy_ok = policy_ok and not any(blocker.startswith("source_policy_") for blocker in blockers)

    group_ok = _require_header(loaded, "group_split_assignment", aq.GROUP_FIELDS, blockers, "source_group") and len(loaded.group_rows) == 5
    if len(loaded.group_rows) != 5:
        blockers.append("source_group_row_count_mismatch")
    group_by_id: dict[str, list[dict[str, Any]]] = {}
    all_members: list[str] = []
    signature = loaded.manifest.get("selected_assignment_signature", [])
    for number, row in enumerate(loaded.group_rows, 1):
        typed = _parse_row_bools(row, ("group_kept_intact", "group_split_assignment_passed", "eligible_for_final_dataset_materialization_smoke", "ready_for_training_current_step", "feature_semantics_audit_required_before_training"), f"source_group_type_invalid:{number}", blockers)
        try:
            typed["group_order"] = parse_strict_int(row.get("group_order")); typed["member_count"] = parse_strict_int(row.get("member_count")); typed["assigned_split_rank"] = parse_strict_int(row.get("assigned_split_rank"))
        except ValueError:
            blockers.append(f"source_group_type_invalid:{number}")
        gid = row.get("final_leakage_group_id", "")
        group_by_id.setdefault(gid, []).append(typed)
        expected_gid = f"COVAPIE_LEAKAGE_GROUP_{number:06d}"
        if row.get("group_split_assignment_id") != f"COVAPIE_GROUP_SPLIT_{number:06d}" or gid != expected_gid or typed.get("group_order") != number:
            blockers.append(f"source_group_id_or_order_mismatch:{number}")
        members = row.get("member_sample_index_row_ids", "").split(";") if row.get("member_sample_index_row_ids") else []
        all_members.extend(members)
        if not members or members != sorted(members) or len(members) != len(set(members)) or typed.get("member_count") != len(members):
            blockers.append(f"source_group_member_contract_mismatch:{gid}")
        expected_split = aq.SPLITS[signature[number - 1]] if isinstance(signature, list) and len(signature) == 5 and isinstance(signature[number - 1], int) else None
        if row.get("assigned_split") != expected_split or typed.get("assigned_split_rank") != aq.RANK.get(row.get("assigned_split")):
            blockers.append(f"source_group_split_mapping_mismatch:{gid}")
        if row.get("split_policy") != aq.POLICY:
            blockers.append(f"source_group_policy_mismatch:{gid}")
        if not row.get("final_leakage_group_status"):
            blockers.append(f"source_group_status_missing:{gid}")
        if not row.get("source_stage_composition"):
            blockers.append(f"source_group_stage_composition_missing:{gid}")
        if not all(typed.get(name) is expected for name, expected in (("group_kept_intact", True), ("group_split_assignment_passed", True), ("eligible_for_final_dataset_materialization_smoke", True), ("ready_for_training_current_step", False), ("feature_semantics_audit_required_before_training", True))) or row.get("blocking_reasons"):
            blockers.append(f"source_group_boundary_mismatch:{gid}")
        typed_groups.append(typed)
    if any(len(rows) != 1 for rows in group_by_id.values()) or len(group_by_id) != 5:
        blockers.append("source_group_duplicate_or_missing")
    group_ok = group_ok and not any(blocker.startswith("source_group_") for blocker in blockers)

    sample_ok = _require_header(loaded, "sample_split_assignment", aq.SAMPLE_FIELDS, blockers, "source_sample") and len(loaded.sample_rows) == 11
    if len(loaded.sample_rows) != 11:
        blockers.append("source_sample_row_count_mismatch")
    sample_by_id: dict[str, list[dict[str, Any]]] = {}
    for number, row in enumerate(loaded.sample_rows, 1):
        typed = _parse_row_bools(row, ("group_assignment_row_found", "source_unified_row_found", "source_assignment_row_found", "sample_split_assignment_passed", "eligible_for_final_dataset_materialization_smoke", "ready_for_training_current_step", "feature_semantics_audit_required_before_training", "leakage_split_design_required_before_training"), f"source_sample_type_invalid:{number}", blockers)
        try:
            typed["final_leakage_group_member_count"] = parse_strict_int(row.get("final_leakage_group_member_count"))
        except ValueError:
            blockers.append(f"source_sample_type_invalid:{number}")
        sid = row.get("sample_index_row_id", ""); sample_by_id.setdefault(sid, []).append(typed)
        if row.get("sample_split_assignment_id") != f"COVAPIE_SAMPLE_SPLIT_{number:06d}":
            blockers.append(f"source_sample_assignment_id_mismatch:{number}")
        if not row.get("pdb_id") or not row.get("ligand_comp_id"):
            blockers.append(f"source_sample_id_or_identity_mismatch:{number}")
        group = group_by_id.get(row.get("final_leakage_group_id", ""), [])
        if len(group) != 1:
            blockers.append(f"source_sample_group_missing:{sid}")
        else:
            group_row = group[0]
            if typed.get("final_leakage_group_member_count") != group_row.get("member_count") or sid not in str(group_row.get("member_sample_index_row_ids", "")).split(";"):
                blockers.append(f"source_sample_group_membership_mismatch:{sid}")
            if row.get("assigned_split") != group_row.get("assigned_split"):
                blockers.append(f"source_sample_assigned_split_mismatch:{sid}")
        if row.get("assigned_split") not in aq.SPLITS or row.get("split_unit_type") != "final_leakage_group_id":
            blockers.append(f"source_sample_split_contract_mismatch:{sid}")
        if row.get("source_index_stage") not in {"pilot", "expansion"}:
            blockers.append(f"source_sample_source_stage_invalid:{sid}")
        if not all(typed.get(name) is expected for name, expected in (("group_assignment_row_found", True), ("source_unified_row_found", True), ("source_assignment_row_found", True), ("sample_split_assignment_passed", True), ("eligible_for_final_dataset_materialization_smoke", True), ("ready_for_training_current_step", False), ("feature_semantics_audit_required_before_training", True), ("leakage_split_design_required_before_training", True))) or row.get("blocking_reasons"):
            blockers.append(f"source_sample_training_boundary_mismatch:{sid}")
        if not all(typed.get(name) is expected for name, expected in (("group_assignment_row_found", True), ("source_unified_row_found", True), ("source_assignment_row_found", True), ("sample_split_assignment_passed", True), ("eligible_for_final_dataset_materialization_smoke", True), ("ready_for_training_current_step", False), ("feature_semantics_audit_required_before_training", True))) or row.get("blocking_reasons"):
            blockers.append(f"source_sample_boundary_mismatch:{sid}")
        typed_samples.append(typed)
    if any(len(rows) != 1 for rows in sample_by_id.values()) or len(sample_by_id) != 11:
        blockers.append("source_sample_duplicate_or_missing")
    if [row.get("sample_index_row_id") for row in typed_samples] != list(EXPECTED_SAMPLE_INDEX_ROW_IDS):
        blockers.append("source_sample_identity_order_mismatch")
    if set(all_members) != set(EXPECTED_SAMPLE_INDEX_ROW_IDS) or len(all_members) != len(set(all_members)) or len(all_members) != len(EXPECTED_SAMPLE_INDEX_ROW_IDS):
        blockers.append("source_group_sample_membership_mismatch")
    group_sample_ok = not any(blocker.startswith("source_group_sample") or blocker.startswith("source_sample_group") or blocker.startswith("source_sample_assigned") for blocker in blockers)
    sample_ok = sample_ok and not any(blocker.startswith("source_sample_") for blocker in blockers)

    split_specs = (("train", "train_sample_index", loaded.train_rows, 8), ("validation", "validation_sample_index", loaded.validation_rows, 2), ("test", "test_sample_index", loaded.test_rows, 1))
    split_ok = True; split_multimap: dict[str, list[dict[str, Any]]] = {}
    for split, logical_name, rows, expected_count in split_specs:
        if not _require_header(loaded, logical_name, list(SAMPLE_INDEX_FIELDS), blockers, "source_split_index") or len(rows) != expected_count:
            split_ok = False; blockers.append(f"source_split_index_count_mismatch:{split}")
        local_seen: set[str] = set()
        for row_number, row in enumerate(rows, 1):
            typed_row = normalize_canonical_sample_index_row(row, logical_split=split, row_number=row_number, blockers=blockers)
            sid = typed_row.get("sample_index_row_id", "")
            if sid in local_seen:
                blockers.append(f"source_split_index_duplicate_sample:{split}:{sid}"); split_ok = False
            local_seen.add(sid); split_multimap.setdefault(sid, []).append(typed_row)
            sample = sample_by_id.get(sid, [])
            if len(sample) != 1 or typed_row.get("pdb_id") != sample[0].get("pdb_id") or typed_row.get("ligand_comp_id") != sample[0].get("ligand_comp_id") or sample[0].get("assigned_split") != split:
                blockers.append(f"source_split_index_assignment_mismatch:{split}:{sid}"); split_ok = False
            typed_splits[split].append(typed_row)
    if any(rows_for_id and len(rows_for_id) != 1 for rows_for_id in split_multimap.values()) or set(split_multimap) != set(EXPECTED_SAMPLE_INDEX_ROW_IDS):
        blockers.append("source_split_indexes_union_mismatch"); split_ok = False
    canonical_source_rows = [split_multimap[sid][0] for sid in EXPECTED_SAMPLE_INDEX_ROW_IDS if len(split_multimap.get(sid, [])) == 1]
    canonical_ok = split_ok and len(canonical_source_rows) == 11 and [row.get("sample_index_row_id") for row in canonical_source_rows] == list(EXPECTED_SAMPLE_INDEX_ROW_IDS)

    leakage_ok = _require_header(loaded, "cross_split_leakage_audit", aq.LEAK_FIELDS, blockers, "source_leakage") and len(loaded.leakage_rows) == 55
    if len(loaded.leakage_rows) != 55:
        blockers.append("source_leakage_row_count_mismatch")
    expected_pairs = list(combinations(EXPECTED_SAMPLE_INDEX_ROW_IDS, 2)); cross_count = 0; violation_count = 0; signal_cross_counts = {field: 0 for field in aq.LEAK_SIGNAL_FIELDS}
    for number, row in enumerate(loaded.leakage_rows, 1):
        typed = _parse_row_bools(row, tuple(aq.LEAK_BOOL_FIELDS), f"source_leakage_type_invalid:{number}", blockers); typed_leakage.append(typed)
        left, right = row.get("left_sample_index_row_id", ""), row.get("right_sample_index_row_id", "")
        if row.get("split_leakage_audit_id") != f"COVAPIE_SPLIT_LEAKAGE_{number:06d}" or (left, right) != (expected_pairs[number - 1] if number <= len(expected_pairs) else (None, None)):
            blockers.append(f"source_leakage_pair_mismatch:{number}")
        left_sample, right_sample = sample_by_id.get(left, []), sample_by_id.get(right, [])
        if len(left_sample) != 1 or len(right_sample) != 1:
            blockers.append(f"source_leakage_unknown_sample:{number}")
            continue
        l, r = left_sample[0], right_sample[0]; recomputed_cross = l.get("assigned_split") != r.get("assigned_split")
        if row.get("left_final_leakage_group_id") != l.get("final_leakage_group_id") or row.get("right_final_leakage_group_id") != r.get("final_leakage_group_id") or row.get("left_split") != l.get("assigned_split") or row.get("right_split") != r.get("assigned_split") or typed.get("cross_split_pair") != recomputed_cross:
            blockers.append(f"source_leakage_assignment_mismatch:{number}")
        signal = any(typed.get(field) is True for field in aq.LEAK_SIGNAL_FIELDS); recomputed_violation = recomputed_cross and signal
        if typed.get("leakage_violation") != recomputed_violation or typed.get("pair_split_leakage_passed") is not True or row.get("blocking_reasons"):
            blockers.append(f"source_leakage_pass_mismatch:{number}")
        cross_count += int(recomputed_cross); violation_count += int(recomputed_violation)
        if recomputed_cross:
            for field_name in signal_cross_counts:
                signal_cross_counts[field_name] += int(typed.get(field_name) is True)
    if cross_count != 26 or len(loaded.leakage_rows) - cross_count != 29 or violation_count != 0 or any(signal_cross_counts.values()):
        blockers.append("source_leakage_recomputed_count_mismatch")
    leakage_ok = leakage_ok and not any(blocker.startswith("source_leakage_") for blocker in blockers)

    balance_ok = _require_header(loaded, "split_balance_audit", aq.BALANCE_FIELDS, blockers, "source_balance") and len(loaded.balance_rows) == 4
    expected_balance_names = [*aq.SPLITS, "total"]
    if len(loaded.balance_rows) != 4 or [row.get("split_name") for row in loaded.balance_rows] != expected_balance_names:
        blockers.append("source_balance_row_order_mismatch")
    for number, row in enumerate(loaded.balance_rows, 1):
        typed = _parse_row_bools(row, ("minimum_one_group_passed", "group_integrity_passed", "statistically_representative", "balance_audit_passed"), f"source_balance_type_invalid:{number}", blockers)
        try:
            typed["actual_sample_count"] = parse_strict_int(row.get("actual_sample_count")); typed["actual_group_count"] = parse_strict_int(row.get("actual_group_count"))
        except ValueError:
            blockers.append(f"source_balance_type_invalid:{number}")
        typed_balance.append(typed); split = row.get("split_name", "")
        expected_samples = len(sample_by_id) if split == "total" else sum(item.get("assigned_split") == split for item in typed_samples)
        expected_groups = len(group_by_id) if split == "total" else sum(item[0].get("assigned_split") == split for item in group_by_id.values() if len(item) == 1)
        if row.get("split_balance_audit_id") != f"COVAPIE_BALANCE_{number:06d}" or typed.get("actual_sample_count") != expected_samples or typed.get("actual_group_count") != expected_groups:
            blockers.append(f"source_balance_count_mismatch:{split}")
        total_samples, total_groups = len(sample_by_id), len(group_by_id)
        expected_sr = Fraction(expected_samples, total_samples); expected_gr = Fraction(expected_groups, total_groups); target = Fraction(1, 1) if split == "total" else aq.TARGET[split]
        if row.get("actual_sample_ratio") != str(expected_sr) or row.get("actual_group_ratio") != str(expected_gr) or row.get("sample_ratio_absolute_deviation") != str(abs(expected_sr - target)) or row.get("group_ratio_absolute_deviation") != str(abs(expected_gr - target)):
            blockers.append(f"source_balance_ratio_mismatch:{split}")
        if not (typed.get("minimum_one_group_passed") is True and typed.get("group_integrity_passed") is True and typed.get("statistically_representative") is False and typed.get("balance_audit_passed") is True) or row.get("blocking_reasons"):
            blockers.append(f"source_balance_pass_mismatch:{split}")
    balance_ok = balance_ok and not any(blocker.startswith("source_balance_") for blocker in blockers)

    issue_ok = _require_header(loaded, "issue_inventory", aq.ISSUE_FIELDS, blockers, "source_issue") and len(loaded.issue_rows) == 1
    sentinel = {"issue_id": "NO_UNIFIED_LEAKAGE_SPLIT_MATERIALIZATION_ISSUES", "issue_scope": "current_11_sample_group_level_split_smoke_v0", "issue_severity": "none", "issue_type": "no_issues", "issue_status": "passed"}
    if len(loaded.issue_rows) != 1 or any(loaded.issue_rows[0].get(key) != value for key, value in sentinel.items()):
        blockers.append("source_issue_sentinel_mismatch")
    typed_issue = [dict(row) for row in loaded.issue_rows]
    issue_ok = issue_ok and not any(blocker.startswith("source_issue_") for blocker in blockers)

    safety_ok = _require_header(loaded, "safety_audit", aq.SAFETY_FIELDS, blockers, "source_safety") and len(loaded.safety_rows) == len(aq.SAFETY_EXPECTED_NORMAL)
    if [row.get("safety_item") for row in loaded.safety_rows] != list(aq.SAFETY_EXPECTED_NORMAL):
        blockers.append("source_safety_item_order_mismatch")
    seen_safety: set[str] = set()
    for row in loaded.safety_rows:
        item = row.get("safety_item", "")
        if item in seen_safety:
            blockers.append(f"source_safety_duplicate_item:{item}")
        seen_safety.add(item)
        typed = _parse_row_bools(row, ("required_status", "observed_status", "safety_passed"), f"source_safety_type_invalid:{item}", blockers)
        expected_required = aq.SAFETY_EXPECTED_NORMAL.get(item)
        if typed.get("required_status") != expected_required:
            blockers.append(f"source_safety_required_status_mismatch:{item}")
        if typed.get("required_status") != typed.get("observed_status") or typed.get("observed_status") != expected_required or typed.get("safety_passed") is not True or row.get("blocking_reasons"):
            blockers.append(f"source_safety_pass_mismatch:{item}")
        typed_safety.append(typed)
    safety_ok = safety_ok and not any(blocker.startswith("source_safety_") for blocker in blockers)

    checks = {
        "contract_snapshot_passed": contract["contract_validation_passed"], "source_files_loaded": loaded.input_load_passed,
        "commit_provenance_passed": provenance_ok, "manifest_contract_passed": manifest_ok,
        "precondition_audit_passed": pre_ok, "policy_audit_passed": policy_ok,
        "group_assignment_passed": group_ok, "sample_assignment_passed": sample_ok,
        "group_sample_membership_passed": group_sample_ok, "split_indexes_passed": split_ok,
        "canonical_source_index_reconstructed": canonical_ok, "leakage_audit_passed": leakage_ok,
        "balance_audit_passed": balance_ok, "issue_sentinel_passed": issue_ok,
        "source_safety_audit_passed": safety_ok, "training_boundary_preserved": training_ok,
        "canonical_masks_preserved": masks_ok,
        "sample_identity_order_passed": [row.get("sample_index_row_id") for row in typed_samples] == list(EXPECTED_SAMPLE_INDEX_ROW_IDS),
        "split_index_type_contract_passed": not any(blocker.startswith("source_split_index_type_invalid") for blocker in blockers),
        "split_index_semantic_contract_passed": not any(blocker.startswith("source_split_index_semantic_invalid") for blocker in blockers),
        "safety_required_contract_passed": not any(blocker.startswith("source_safety_required_status_mismatch") for blocker in blockers),
        "group_policy_boundary_passed": not any(blocker.startswith("source_group_policy_") or blocker.startswith("source_group_status_") or blocker.startswith("source_group_stage_") for blocker in blockers),
        "sample_training_boundary_passed": not any(blocker.startswith("source_sample_training_boundary_") or blocker.startswith("source_sample_source_stage_") for blocker in blockers),
    }
    if tuple(checks) != SOURCE_CHECK_ORDER:
        blockers.append("source_check_order_or_coverage_mismatch")
    blockers = sorted(set(blockers))
    passed = all(checks.values()) and not blockers
    return Step14AQSourceValidationResult(passed, blockers, loaded.manifest, typed_pre, typed_policy, typed_groups, typed_samples, typed_splits["train"], typed_splits["validation"], typed_splits["test"], typed_leakage, typed_balance, typed_issue, typed_safety, checks, loaded.input_sha256, canonical_source_rows)


def validate_source_step14aq_preconditions_passed(result: Step14AQSourceValidationResult) -> dict[str, Any]:
    return {
        "source_step14aq_preconditions_passed": result.source_validation_passed,
        "source_check_count": len(result.source_checks),
        "all_source_checks_passed": all(result.source_checks.values()),
        "blocking_reasons": list(result.blocking_reasons),
    }


@dataclass
class ArtifactReferenceReadActivity:
    read_paths: set[str] = field(default_factory=set)
    raw_read_attempted: bool = False


def sha256_regular_file(path: Path, activity: ArtifactReferenceReadActivity) -> str:
    """Hash an already-authorized regular derived file with bounded-memory reads."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    activity.read_paths.add(str(path.resolve()))
    return digest.hexdigest()


@dataclass
class FinalDatasetIndexValidationResult:
    passed: bool
    blocking_reasons: list[str]
    validated_rows: list[dict[str, Any]]
    row_count_passed: bool
    schema_passed: bool
    canonical_order_passed: bool
    source_values_preserved: bool
    unique_sample_ids_passed: bool
    artifact_reference_fields_present: bool


def build_candidate_final_dataset_index_rows(source_validation: Step14AQSourceValidationResult) -> list[dict[str, Any]]:
    return deepcopy(source_validation.canonical_source_rows)


def build_final_dataset_index_schema_passed_evidence(candidate_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult) -> FinalDatasetIndexValidationResult:
    blockers: list[str] = []
    if not source_validation.source_validation_passed:
        blockers.append("final_index_source_validation_not_passed")
    row_count = len(candidate_rows) == 11
    if not row_count:
        blockers.append("final_index_row_count_mismatch")
    schema_ok = True; order_ok = True; values_ok = True; artifacts_ok = True
    ids: list[str] = []
    source_rows = source_validation.canonical_source_rows
    forbidden = {"assigned_split", "final_leakage_group_id", "final_dataset_row_id"}
    for number, row in enumerate(candidate_rows, 1):
        sample = row.get("sample_index_row_id", f"row{number}")
        if list(row) != list(SAMPLE_INDEX_FIELDS):
            schema_ok = False; blockers.append(f"final_index_schema_mismatch:{number}")
        for field_name in forbidden & set(row):
            blockers.append(f"final_index_forbidden_extra_field:{field_name}")
        ids.append(sample)
        if number > len(source_rows) or row != source_rows[number - 1]:
            values_ok = False
            reference = source_rows[number - 1] if number <= len(source_rows) else {}
            for field_name in SAMPLE_INDEX_FIELDS:
                if row.get(field_name) != reference.get(field_name):
                    blockers.append(f"final_index_source_value_mismatch:{sample}:{field_name}")
        for field_name in ARTIFACT_PATH_FIELDS:
            if not isinstance(row.get(field_name), str) or not row.get(field_name):
                artifacts_ok = False; blockers.append(f"final_index_artifact_reference_missing:{sample}:{field_name}")
    if ids != list(EXPECTED_SAMPLE_INDEX_ROW_IDS):
        order_ok = False; blockers.append("final_index_sample_order_mismatch")
    unique = len(ids) == len(set(ids))
    for sample in sorted({sample for sample in ids if ids.count(sample) > 1}):
        blockers.append(f"final_index_duplicate_sample:{sample}")
    blockers = sorted(set(blockers)); passed = not blockers
    return FinalDatasetIndexValidationResult(passed, blockers, deepcopy(candidate_rows), row_count, schema_ok, order_ok, values_ok, unique, artifacts_ok)


def validate_final_dataset_index_schema_passed(result: FinalDatasetIndexValidationResult) -> dict[str, Any]:
    return {"final_dataset_index_schema_passed": result.passed, "final_dataset_index_row_count": len(result.validated_rows), "final_dataset_index_schema_field_count": len(SAMPLE_INDEX_FIELDS), "blocking_reasons": list(result.blocking_reasons)}


SPLIT_LOGICAL_NAME = {"train": "train_sample_index", "validation": "validation_sample_index", "test": "test_sample_index"}


@dataclass
class MembershipValidationResult:
    passed: bool
    blocking_reasons: list[str]
    validated_rows: list[dict[str, Any]]
    row_count_passed: bool
    schema_passed: bool
    canonical_order_passed: bool
    source_rows_found: bool
    split_membership_consistent: bool
    group_membership_consistent: bool
    training_boundary_preserved: bool


def _multi(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    values: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        values.setdefault(str(row.get(key, "")), []).append(row)
    return values


def build_candidate_final_dataset_membership_rows(validated_final_index_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult) -> list[dict[str, Any]]:
    samples = _multi(source_validation.typed_sample_rows, "sample_index_row_id")
    rows: list[dict[str, Any]] = []
    for number, index_row in enumerate(validated_final_index_rows, 1):
        sample = samples.get(index_row["sample_index_row_id"], [{}])[0]
        split = sample.get("assigned_split", "")
        rows.append({
            "final_dataset_membership_id": f"COVAPIE_FINAL_DATASET_MEMBERSHIP_{number:06d}",
            "sample_index_row_id": index_row["sample_index_row_id"], "pdb_id": index_row["pdb_id"],
            "ligand_comp_id": index_row["ligand_comp_id"], "canonical_row_order": number,
            "assigned_split": split, "assigned_split_rank": aq.RANK.get(split),
            "final_leakage_group_id": sample.get("final_leakage_group_id", ""),
            "final_leakage_group_member_count": sample.get("final_leakage_group_member_count"),
            "source_index_stage": sample.get("source_index_stage", ""),
            "source_split_sample_index_logical_name": SPLIT_LOGICAL_NAME.get(split, ""),
            "ready_for_training_current_step": False,
            "feature_semantics_audit_required_before_training": True,
        })
    return rows


def build_membership_checks_passed_evidence(candidate_rows: list[dict[str, Any]], validated_final_index_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult) -> MembershipValidationResult:
    blockers: list[str] = []
    samples = _multi(source_validation.typed_sample_rows, "sample_index_row_id")
    groups = _multi(source_validation.typed_group_rows, "final_leakage_group_id")
    indexes = _multi(validated_final_index_rows, "sample_index_row_id")
    rows: list[dict[str, Any]] = []
    if len(candidate_rows) != 11:
        blockers.append("membership_row_count_mismatch")
    ids = [row.get("sample_index_row_id") for row in candidate_rows]
    if ids != list(EXPECTED_SAMPLE_INDEX_ROW_IDS):
        blockers.append("membership_sample_order_mismatch")
    for sample_id in sorted({item for item in ids if ids.count(item) > 1}):
        blockers.append(f"membership_duplicate_sample:{sample_id}")
    source_found = split_ok = group_ok = training_ok = schema_ok = True
    for number, row in enumerate(candidate_rows, 1):
        sample_id = row.get("sample_index_row_id", f"row{number}"); local: list[str] = []
        row_schema_ok = list(row) == list(FINAL_DATASET_MEMBERSHIP_CANDIDATE_FIELDS)
        if not row_schema_ok:
            local.append(f"membership_schema_mismatch:{number}")
        if row.get("final_dataset_membership_id") != f"COVAPIE_FINAL_DATASET_MEMBERSHIP_{number:06d}" or row.get("canonical_row_order") != number:
            local.append(f"membership_id_mismatch:{number}")
        index_rows, sample_rows = indexes.get(sample_id, []), samples.get(sample_id, [])
        if len(index_rows) == 0: local.append(f"membership_final_index_missing:{sample_id}")
        if len(index_rows) > 1: local.append(f"membership_final_index_duplicate:{sample_id}")
        if len(sample_rows) == 0: local.append(f"membership_source_sample_missing:{sample_id}")
        if len(sample_rows) > 1: local.append(f"membership_source_sample_duplicate:{sample_id}")
        source_sample_found = len(sample_rows) == 1
        index_found = len(index_rows) == 1
        index = index_rows[0] if index_found else {}; sample = sample_rows[0] if source_sample_found else {}
        group_rows = groups.get(sample.get("final_leakage_group_id", ""), [])
        if len(group_rows) == 0: local.append(f"membership_source_group_missing:{sample_id}")
        if len(group_rows) > 1: local.append(f"membership_source_group_duplicate:{sample_id}")
        source_group_found = len(group_rows) == 1
        group = group_rows[0] if source_group_found else {}
        identity_consistent = index_found and row.get("pdb_id") == index.get("pdb_id") and row.get("ligand_comp_id") == index.get("ligand_comp_id")
        if not identity_consistent:
            local.append(f"membership_identity_mismatch:{sample_id}")
        split_matches_sample = source_sample_found and row.get("assigned_split") == sample.get("assigned_split")
        rank_matches_sample = source_sample_found and row.get("assigned_split_rank") == aq.RANK.get(sample.get("assigned_split"))
        logical_name_matches_sample = source_sample_found and row.get("source_split_sample_index_logical_name") == SPLIT_LOGICAL_NAME.get(sample.get("assigned_split"))
        group_split_matches_sample = source_group_found and source_sample_found and group.get("assigned_split") == sample.get("assigned_split")
        if not split_matches_sample:
            local.append(f"membership_split_mismatch:{sample_id}")
        if not rank_matches_sample:
            local.append(f"membership_split_rank_mismatch:{sample_id}")
        group_matches_sample = source_sample_found and row.get("final_leakage_group_id") == sample.get("final_leakage_group_id")
        if not group_matches_sample:
            local.append(f"membership_group_mismatch:{sample_id}")
        group_count_matches = source_sample_found and source_group_found and row.get("final_leakage_group_member_count") == sample.get("final_leakage_group_member_count") and row.get("final_leakage_group_member_count") == group.get("member_count")
        if not group_count_matches:
            local.append(f"membership_group_count_mismatch:{sample_id}")
        source_stage_matches = source_sample_found and row.get("source_index_stage") == sample.get("source_index_stage")
        if not source_stage_matches:
            local.append(f"membership_source_stage_mismatch:{sample_id}")
        if not logical_name_matches_sample:
            local.append(f"membership_source_logical_name_mismatch:{sample_id}")
        member_list_matches = source_group_found and sample_id in str(group.get("member_sample_index_row_ids", "")).split(";")
        if not member_list_matches or not group_split_matches_sample:
            local.append(f"membership_group_member_list_mismatch:{sample_id}")
        row_training_boundary_ok = row.get("ready_for_training_current_step") is False and row.get("feature_semantics_audit_required_before_training") is True
        if not row_training_boundary_ok:
            local.append(f"membership_training_boundary_mismatch:{sample_id}")
        split_member = source_sample_found and source_group_found and index_found and split_matches_sample and rank_matches_sample and logical_name_matches_sample and group_split_matches_sample
        group_member = source_sample_found and source_group_found and index_found and group_matches_sample and group_count_matches and member_list_matches and group_split_matches_sample
        passed = row_schema_ok and source_sample_found and source_group_found and index_found and identity_consistent and split_member and group_member and source_stage_matches and row_training_boundary_ok and not local
        source_found &= source_sample_found and source_group_found and index_found; split_ok &= split_member; group_ok &= group_member; training_ok &= row_training_boundary_ok; schema_ok &= row_schema_ok
        evidence = {
            "source_sample_split_assignment_row_found": source_sample_found,
            "source_group_split_assignment_row_found": source_group_found,
            "final_dataset_index_row_found": index_found,
            "split_membership_consistent": split_member,
            "group_membership_consistent": group_member,
            "final_dataset_membership_passed": passed,
            "eligible_for_final_dataset_qa_gate_current_step": passed,
            "blocking_reasons": ";".join(local),
        }
        rows.append({field_name: evidence[field_name] if field_name in evidence else row.get(field_name) for field_name in FINAL_DATASET_MEMBERSHIP_FIELDS})
        blockers.extend(local)
    blockers = sorted(set(blockers)); return MembershipValidationResult(not blockers, blockers, rows, len(candidate_rows) == 11, schema_ok, ids == list(EXPECTED_SAMPLE_INDEX_ROW_IDS), source_found, split_ok, group_ok, training_ok)


def validate_membership_checks_passed(result: MembershipValidationResult) -> dict[str, Any]:
    return {"membership_checks_passed": result.passed, "membership_row_count": len(result.validated_rows), "membership_passed_count": sum(row["final_dataset_membership_passed"] for row in result.validated_rows), "blocking_reasons": list(result.blocking_reasons)}


def build_candidate_artifact_inventory_rows(validated_final_index_rows: list[dict[str, Any]], validated_membership_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    memberships = _multi(validated_membership_rows, "sample_index_row_id"); rows: list[dict[str, Any]] = []
    for sample_number, index in enumerate(validated_final_index_rows, 1):
        membership = memberships.get(index["sample_index_row_id"], [{}])[0]
        for field_number, field_name in enumerate(ARTIFACT_PATH_FIELDS, 1):
            number = (sample_number - 1) * len(ARTIFACT_PATH_FIELDS) + field_number
            rows.append({"artifact_inventory_id": f"COVAPIE_FINAL_ARTIFACT_{number:06d}", "sample_index_row_id": index["sample_index_row_id"], "assigned_split": membership.get("assigned_split", ""), "final_leakage_group_id": membership.get("final_leakage_group_id", ""), "artifact_role": ARTIFACT_ROLE_BY_FIELD[field_name], "source_field_name": field_name, "artifact_path": index.get(field_name, "")})
    return rows


@dataclass
class ArtifactInventoryValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_rows: list[dict[str, Any]]
    row_count_passed: bool; schema_passed: bool; ordering_passed: bool; references_preserved: bool
    all_paths_relative: bool; all_paths_inside_repo: bool; all_paths_inside_allowed_derived_root: bool; no_raw_references: bool
    all_paths_exist: bool; all_files_regular: bool; all_sizes_positive: bool
    all_hashes_present: bool; activity: ArtifactReferenceReadActivity


def build_artifact_inventory_checks_passed_evidence(candidate_rows: list[dict[str, Any]], validated_final_index_rows: list[dict[str, Any]], validated_membership_rows: list[dict[str, Any]], *, repo_root: Path = REPO) -> ArtifactInventoryValidationResult:
    blockers: list[str] = []; activity = ArtifactReferenceReadActivity(); rows: list[dict[str, Any]] = []
    indexes = _multi(validated_final_index_rows, "sample_index_row_id"); memberships = _multi(validated_membership_rows, "sample_index_row_id"); expected = build_candidate_artifact_inventory_rows(validated_final_index_rows, validated_membership_rows); root = repo_root.resolve(); derived = (root / "data/derived/covalent_small").resolve(); raw = (root / "data/raw").resolve()
    if len(candidate_rows) != 66: blockers.append("artifact_inventory_row_count_mismatch")
    flags = {"schema": True, "ordering": True, "references": True, "relative": True, "inside": True, "derived": True, "raw": True, "exists": True, "regular": True, "size": True, "hash": True}
    seen: set[tuple[str, str]] = set()
    for number, row in enumerate(candidate_rows, 1):
        sample = row.get("sample_index_row_id", f"row{number}"); field_name = row.get("source_field_name", ""); local: list[str] = []
        expected_row = expected[number - 1] if number <= len(expected) else {}
        row_schema_ok = list(row) == list(FINAL_DATASET_ARTIFACT_INVENTORY_CANDIDATE_FIELDS)
        if not row_schema_ok: local.append(f"artifact_inventory_schema_mismatch:{number}")
        if row.get("artifact_inventory_id") != f"COVAPIE_FINAL_ARTIFACT_{number:06d}": local.append(f"artifact_inventory_id_mismatch:{number}")
        if any(row.get(key) != expected_row.get(key) for key in ("sample_index_row_id", "assigned_split", "final_leakage_group_id", "source_field_name")): local.append(f"artifact_inventory_order_mismatch:{number}")
        key = (sample, field_name)
        if key in seen: local.append(f"artifact_inventory_duplicate_sample_field:{sample}:{field_name}")
        seen.add(key)
        index_rows, membership_rows = indexes.get(sample, []), memberships.get(sample, [])
        if len(index_rows) != 1: local.append(f"artifact_inventory_unknown_sample:{sample}")
        if len(membership_rows) != 1 or row.get("assigned_split") != (membership_rows[0].get("assigned_split") if membership_rows else None) or row.get("final_leakage_group_id") != (membership_rows[0].get("final_leakage_group_id") if membership_rows else None): local.append(f"artifact_inventory_membership_mismatch:{sample}")
        if field_name not in ARTIFACT_PATH_FIELDS or row.get("artifact_role") != ARTIFACT_ROLE_BY_FIELD.get(field_name): local.append(f"artifact_inventory_role_mismatch:{sample}:{field_name}")
        source_path = index_rows[0].get(field_name) if len(index_rows) == 1 else None
        if row.get("artifact_path") != source_path: local.append(f"artifact_inventory_reference_mismatch:{sample}:{field_name}")
        path_text = row.get("artifact_path", ""); path = Path(path_text) if isinstance(path_text, str) else Path("")
        relative = isinstance(path_text, str) and bool(path_text) and not path.is_absolute(); no_parent_traversal = relative and ".." not in path.parts
        exists = regular = size_positive = False; size = 0; digest = ""; inside = inside_allowed_derived = outside_raw = False
        if not relative: local.append(f"artifact_inventory_absolute_path:{sample}:{field_name}")
        elif not no_parent_traversal: local.append(f"artifact_inventory_parent_traversal:{sample}:{field_name}")
        else:
            resolved = (root / path).resolve()
            try: resolved.relative_to(root); inside = True
            except ValueError: local.append(f"artifact_inventory_outside_repo:{sample}:{field_name}")
            if inside:
                try: resolved.relative_to(derived); inside_allowed_derived = True
                except ValueError: local.append(f"artifact_inventory_not_derived:{sample}:{field_name}")
                try: resolved.relative_to(raw); local.append(f"artifact_inventory_raw_reference:{sample}:{field_name}")
                except ValueError: outside_raw = True
                authorized_for_file_access = relative and no_parent_traversal and inside and inside_allowed_derived and outside_raw
                if authorized_for_file_access:
                    exists = resolved.exists()
                    regular = exists and resolved.is_file()
                    if not exists:
                        local.append(f"artifact_inventory_missing_file:{sample}:{field_name}")
                    elif not regular:
                        local.append(f"artifact_inventory_not_regular_file:{sample}:{field_name}")
                    else:
                        size = resolved.stat().st_size; size_positive = size > 0
                        if not size_positive:
                            local.append(f"artifact_inventory_empty_file:{sample}:{field_name}")
                        else:
                            try: digest = sha256_regular_file(resolved, activity)
                            except OSError: local.append(f"artifact_inventory_hash_failed:{sample}:{field_name}")
        flags["schema"] &= row_schema_ok; flags["relative"] &= relative; flags["inside"] &= inside; flags["derived"] &= inside_allowed_derived; flags["raw"] &= outside_raw; flags["exists"] &= exists; flags["regular"] &= regular; flags["size"] &= size_positive; flags["hash"] &= bool(re.fullmatch(r"[0-9a-f]{64}", digest)); flags["ordering"] &= not any(item.startswith("artifact_inventory_order") or item.startswith("artifact_inventory_id") for item in local); flags["references"] &= not any(item.startswith("artifact_inventory_reference") for item in local)
        passed = not local
        evidence = {"artifact_path_is_relative": relative, "artifact_path_exists": exists, "artifact_is_regular_file": regular, "artifact_size_bytes": size if regular else 0, "artifact_sha256": digest, "artifact_reference_preserved": not any(item.startswith("artifact_inventory_reference") for item in local), "artifact_inventory_passed": passed, "blocking_reasons": ";".join(local)}
        rows.append({field_name: evidence[field_name] if field_name in evidence else row.get(field_name) for field_name in FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS}); blockers.extend(local)
    blockers = sorted(set(blockers)); return ArtifactInventoryValidationResult(not blockers, blockers, rows, len(candidate_rows) == 66, flags["schema"], flags["ordering"], flags["references"], flags["relative"], flags["inside"], flags["derived"], flags["raw"], flags["exists"], flags["regular"], flags["size"], flags["hash"], activity)


def validate_artifact_inventory_checks_passed(result: ArtifactInventoryValidationResult) -> dict[str, Any]:
    return {"artifact_inventory_checks_passed": result.passed, "artifact_inventory_row_count": len(result.validated_rows), "artifact_inventory_passed_count": sum(row["artifact_inventory_passed"] for row in result.validated_rows), "artifact_reference_read_count": len(result.activity.read_paths), "artifact_paths_inside_allowed_derived_root": result.all_paths_inside_allowed_derived_root, "raw_read_attempted": result.activity.raw_read_attempted, "blocking_reasons": list(result.blocking_reasons)}


@dataclass
class SplitSummaryValidationResult:
    passed: bool
    blocking_reasons: list[str]
    validated_rows: list[dict[str, Any]]
    schema_passed: bool


def _expected_split_summary_rows(index_rows: list[dict[str, Any]], membership_rows: list[dict[str, Any]], artifact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, split in enumerate((*aq.SPLITS, "total"), 1):
        rank = aq.RANK.get(split, -1)
        members = membership_rows if split == "total" else [row for row in membership_rows if row.get("assigned_split") == split]
        groups = {row.get("final_leakage_group_id") for row in members}
        artifacts = artifact_rows if split == "total" else [row for row in artifact_rows if row.get("assigned_split") == split]
        rows.append({"split_summary_id": f"COVAPIE_FINAL_SPLIT_SUMMARY_{number:06d}", "split_name": split, "split_rank": rank, "sample_count": len(members), "leakage_group_count": len(groups), "canonical_schema_field_count": len(SAMPLE_INDEX_FIELDS), "artifact_reference_count": len(artifacts), "statistical_representativeness_claimed": False})
    return rows


def build_candidate_split_summary_rows(validated_final_index_rows: list[dict[str, Any]], validated_membership_rows: list[dict[str, Any]], validated_artifact_inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _expected_split_summary_rows(validated_final_index_rows, validated_membership_rows, validated_artifact_inventory_rows)


def build_split_summary_checks_passed_evidence(candidate_rows: list[dict[str, Any]], validated_final_index_rows: list[dict[str, Any]], validated_membership_rows: list[dict[str, Any]], validated_artifact_inventory_rows: list[dict[str, Any]]) -> SplitSummaryValidationResult:
    blockers: list[str] = []; expected = _expected_split_summary_rows(validated_final_index_rows, validated_membership_rows, validated_artifact_inventory_rows); rows: list[dict[str, Any]] = []; schema_ok = True
    if len(candidate_rows) != 4: blockers.append("split_summary_row_count_mismatch")
    if [row.get("split_name") for row in candidate_rows] != [*aq.SPLITS, "total"]: blockers.append("split_summary_order_mismatch")
    for number, row in enumerate(candidate_rows, 1):
        expected_row = expected[number - 1] if number <= len(expected) else {}; split = row.get("split_name", f"row{number}"); local: list[str] = []
        row_schema_ok = list(row) == list(FINAL_DATASET_SPLIT_SUMMARY_CANDIDATE_FIELDS)
        if not row_schema_ok: local.append(f"split_summary_schema_mismatch:{number}")
        if row.get("split_summary_id") != f"COVAPIE_FINAL_SPLIT_SUMMARY_{number:06d}": local.append(f"split_summary_id_mismatch:{number}")
        for field, prefix in (("sample_count", "sample_count"), ("leakage_group_count", "group_count"), ("artifact_reference_count", "artifact_count"), ("canonical_schema_field_count", "schema_count")):
            if row.get(field) != expected_row.get(field): local.append(f"split_summary_{prefix}_mismatch:{split}")
        if row.get("split_rank") != expected_row.get("split_rank"): local.append(f"split_summary_order_mismatch")
        if row.get("statistical_representativeness_claimed") is not False: local.append(f"split_summary_statistical_claim_mismatch:{split}")
        source_preserved = len(validated_final_index_rows) == 11 and all(row.get("final_dataset_membership_passed") for row in validated_membership_rows)
        group_integrity = all(row.get("group_membership_consistent") for row in validated_membership_rows)
        if not source_preserved: local.append(f"split_summary_source_preservation_failed:{split}")
        if not group_integrity: local.append(f"split_summary_group_integrity_failed:{split}")
        passed = row_schema_ok and not local
        schema_ok &= row_schema_ok
        evidence = {"source_rows_preserved": source_preserved, "group_integrity_preserved": group_integrity, "split_summary_passed": passed, "blocking_reasons": ";".join(local)}
        rows.append({field_name: evidence[field_name] if field_name in evidence else row.get(field_name) for field_name in FINAL_DATASET_SPLIT_SUMMARY_FIELDS}); blockers.extend(local)
    blockers = sorted(set(blockers)); return SplitSummaryValidationResult(not blockers, blockers, rows, schema_ok)


def validate_split_summary_checks_passed(result: SplitSummaryValidationResult) -> dict[str, Any]:
    return {"split_summary_checks_passed": result.passed, "split_summary_row_count": len(result.validated_rows), "split_summary_passed_count": sum(row["split_summary_passed"] for row in result.validated_rows), "blocking_reasons": list(result.blocking_reasons)}


FINAL_DATASET_INTEGRITY_EXPECTED = (
    ("source_step14aq_preconditions_passed", "true"), ("final_dataset_index_row_count", "11"),
    ("final_dataset_index_schema_field_count", "33"), ("canonical_sample_order_preserved", "true"),
    ("canonical_source_values_preserved", "true"), ("membership_row_count", "11"),
    ("membership_passed_count", "11"), ("train_sample_count", "8"),
    ("validation_sample_count", "2"), ("test_sample_count", "1"),
    ("train_group_count", "2"), ("validation_group_count", "2"),
    ("test_group_count", "1"), ("artifact_inventory_row_count", "66"),
    ("artifact_roles_per_sample", "6"), ("artifact_paths_all_relative", "true"),
    ("artifact_paths_all_inside_repo", "true"), ("artifact_paths_all_exist", "true"),
    ("artifact_files_all_regular", "true"), ("artifact_hashes_all_present", "true"),
    ("no_raw_references", "true"), ("training_boundary_preserved", "true"),
    ("statistical_representativeness_claimed", "false"), ("production_split_policy_finalized", "false"),
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_integrity_observations(source_validation: Step14AQSourceValidationResult, final_index_validation: FinalDatasetIndexValidationResult, membership_validation: MembershipValidationResult, artifact_inventory_validation: ArtifactInventoryValidationResult, split_summary_validation: SplitSummaryValidationResult) -> dict[str, str]:
    memberships = membership_validation.validated_rows
    split_counts = {split: sum(row.get("assigned_split") == split for row in memberships) for split in aq.SPLITS}
    group_counts = {split: len({row.get("final_leakage_group_id") for row in memberships if row.get("assigned_split") == split}) for split in aq.SPLITS}
    index_rows = final_index_validation.validated_rows
    if index_rows and all(list(row) == list(index_rows[0]) for row in index_rows):
        index_field_count = str(len(index_rows[0]))
    else:
        index_field_count = "inconsistent"
    artifacts_by_sample = _multi(artifact_inventory_validation.validated_rows, "sample_index_row_id")
    expected_samples = set(EXPECTED_SAMPLE_INDEX_ROW_IDS)
    roles_are_complete = set(artifacts_by_sample) == expected_samples and all(
        len(rows) == len(ARTIFACT_PATH_FIELDS)
        and {row.get("source_field_name") for row in rows} == set(ARTIFACT_PATH_FIELDS)
        and all(row.get("artifact_role") == ARTIFACT_ROLE_BY_FIELD.get(row.get("source_field_name")) for row in rows)
        for rows in artifacts_by_sample.values()
    )
    artifact_roles_per_sample = str(len(ARTIFACT_PATH_FIELDS)) if roles_are_complete else "inconsistent"
    summary_rows = split_summary_validation.validated_rows
    summary_claims = [row.get("statistical_representativeness_claimed") for row in summary_rows]
    if len(summary_claims) != 4 or any(not isinstance(value, bool) for value in summary_claims):
        statistical_claim = "invalid"
    else:
        statistical_claim = "true" if any(summary_claims) else "false"
    policy_value = source_validation.manifest.get("production_split_policy_finalized")
    production_policy = _bool_text(policy_value) if isinstance(policy_value, bool) else "invalid"
    source_training_boundary = source_validation.source_checks.get("training_boundary_preserved") is True
    membership_rows_preserve_boundary = bool(memberships) and all(
        row.get("ready_for_training_current_step") is False
        and row.get("feature_semantics_audit_required_before_training") is True
        for row in memberships
    )
    training_boundary = source_training_boundary and membership_validation.training_boundary_preserved and membership_rows_preserve_boundary
    return {"source_step14aq_preconditions_passed": _bool_text(source_validation.source_validation_passed), "final_dataset_index_row_count": str(len(index_rows)), "final_dataset_index_schema_field_count": index_field_count, "canonical_sample_order_preserved": _bool_text(final_index_validation.canonical_order_passed), "canonical_source_values_preserved": _bool_text(final_index_validation.source_values_preserved), "membership_row_count": str(len(memberships)), "membership_passed_count": str(sum(row.get("final_dataset_membership_passed") is True for row in memberships)), "train_sample_count": str(split_counts["train"]), "validation_sample_count": str(split_counts["validation"]), "test_sample_count": str(split_counts["test"]), "train_group_count": str(group_counts["train"]), "validation_group_count": str(group_counts["validation"]), "test_group_count": str(group_counts["test"]), "artifact_inventory_row_count": str(len(artifact_inventory_validation.validated_rows)), "artifact_roles_per_sample": artifact_roles_per_sample, "artifact_paths_all_relative": _bool_text(artifact_inventory_validation.all_paths_relative), "artifact_paths_all_inside_repo": _bool_text(artifact_inventory_validation.all_paths_inside_repo), "artifact_paths_all_exist": _bool_text(artifact_inventory_validation.all_paths_exist), "artifact_files_all_regular": _bool_text(artifact_inventory_validation.all_files_regular), "artifact_hashes_all_present": _bool_text(artifact_inventory_validation.all_hashes_present), "no_raw_references": _bool_text(artifact_inventory_validation.no_raw_references), "training_boundary_preserved": _bool_text(training_boundary), "statistical_representativeness_claimed": statistical_claim, "production_split_policy_finalized": production_policy}


def build_integrity_checks_passed_evidence(observations: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for item, expected in FINAL_DATASET_INTEGRITY_EXPECTED:
        observed = str(observations.get(item, "<missing>")); passed = observed == expected
        rows.append({"integrity_audit_item": item, "expected_value": expected, "observed_value": observed, "integrity_check_passed": passed, "blocking_reasons": "" if passed else f"final_integrity_mismatch:{item}:expected={expected}:observed={observed}"})
    return rows


def validate_integrity_checks_passed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []; expected_items = [item for item, _ in FINAL_DATASET_INTEGRITY_EXPECTED]; expected_values = dict(FINAL_DATASET_INTEGRITY_EXPECTED); items = [row.get("integrity_audit_item") for row in rows]; schema_ok = True
    if len(rows) != 24: blockers.append("final_integrity_row_count_mismatch")
    if items != expected_items or len(items) != len(set(items)): blockers.append("final_integrity_item_contract_mismatch")
    recomputed_pass_count = 0
    for number, row in enumerate(rows, 1):
        item = row.get("integrity_audit_item", f"row{number}")
        if list(row) != list(FINAL_DATASET_INTEGRITY_AUDIT_FIELDS):
            schema_ok = False; blockers.append(f"final_integrity_schema_mismatch:{number}")
        frozen_expected = expected_values.get(item)
        if frozen_expected is None:
            continue
        if row.get("expected_value") != frozen_expected:
            blockers.append(f"final_integrity_expected_value_mismatch:{item}")
        observed = row.get("observed_value")
        recomputed_pass = isinstance(observed, str) and observed == frozen_expected
        if recomputed_pass:
            recomputed_pass_count += 1
        else:
            blockers.append(f"final_integrity_mismatch:{item}:expected={frozen_expected}:observed={observed}")
        if type(row.get("integrity_check_passed")) is not bool or row.get("integrity_check_passed") != recomputed_pass:
            blockers.append(f"final_integrity_pass_flag_mismatch:{item}")
        reason = row.get("blocking_reasons")
        expected_reason_prefix = f"final_integrity_mismatch:{item}"
        if recomputed_pass and reason != "":
            blockers.append(f"final_integrity_blocking_reason_mismatch:{item}")
        if not recomputed_pass and (not isinstance(reason, str) or expected_reason_prefix not in reason):
            blockers.append(f"final_integrity_blocking_reason_mismatch:{item}")
    blockers = sorted(set(blockers)); return {"integrity_checks_passed": not blockers, "integrity_row_count": len(rows), "integrity_passed_count": recomputed_pass_count, "integrity_schema_passed": schema_ok, "blocking_reasons": blockers}


@dataclass
class FinalDatasetInMemoryMaterializationResult:
    passed: bool; blocking_reasons: list[str]; source_validation: Step14AQSourceValidationResult
    final_index_validation: FinalDatasetIndexValidationResult | None
    membership_validation: MembershipValidationResult | None
    artifact_inventory_validation: ArtifactInventoryValidationResult | None
    split_summary_validation: SplitSummaryValidationResult | None
    integrity_rows: list[dict[str, Any]]; integrity_validation: dict[str, Any]
    ready_for_disk_materialization: bool; ready_for_covapie_final_dataset_qa_gate: bool = False
    ready_for_training: bool = False; ready_to_train_now: bool = False

    @property
    def in_memory_materialization_passed(self) -> bool:
        return self.passed and not self.blocking_reasons


def build_in_memory_final_dataset_materialization(source_validation: Step14AQSourceValidationResult) -> FinalDatasetInMemoryMaterializationResult:
    if not source_validation.source_validation_passed:
        return FinalDatasetInMemoryMaterializationResult(False, ["in_memory_source_validation_not_passed", *source_validation.blocking_reasons], source_validation, None, None, None, None, [], {"integrity_checks_passed": False, "integrity_row_count": 0, "integrity_passed_count": 0, "blocking_reasons": ["in_memory_source_validation_not_passed"]}, False)
    index = build_final_dataset_index_schema_passed_evidence(build_candidate_final_dataset_index_rows(source_validation), source_validation)
    membership = build_membership_checks_passed_evidence(build_candidate_final_dataset_membership_rows(index.validated_rows, source_validation), index.validated_rows, source_validation)
    inventory = build_artifact_inventory_checks_passed_evidence(build_candidate_artifact_inventory_rows(index.validated_rows, membership.validated_rows), index.validated_rows, membership.validated_rows)
    summary = build_split_summary_checks_passed_evidence(build_candidate_split_summary_rows(index.validated_rows, membership.validated_rows, inventory.validated_rows), index.validated_rows, membership.validated_rows, inventory.validated_rows)
    integrity_rows = build_integrity_checks_passed_evidence(build_integrity_observations(source_validation, index, membership, inventory, summary)); integrity = validate_integrity_checks_passed(integrity_rows)
    blockers = sorted(set(index.blocking_reasons + membership.blocking_reasons + inventory.blocking_reasons + summary.blocking_reasons + integrity["blocking_reasons"])); passed = not blockers
    return FinalDatasetInMemoryMaterializationResult(passed, blockers, source_validation, index, membership, inventory, summary, integrity_rows, integrity, passed)


CORE_OUTPUT_LOGICAL_NAMES = (
    "precondition_audit", "final_dataset_index_csv", "final_dataset_index_json", "membership",
)


def _output_path_items(paths: Step14AROutputPaths) -> list[tuple[str, Path]]:
    return [(logical_name, getattr(paths, logical_name)) for logical_name, *_ in OUTPUT_SPECS]


def validate_step14ar_output_paths(paths: Step14AROutputPaths, *, repo_root: Path = REPO) -> dict[str, Any]:
    blockers: list[str] = []
    root = repo_root.resolve()
    final_root = root / FINAL_ROOT
    items = _output_path_items(paths)
    expected_names = {logical_name: filename for logical_name, filename, *_ in OUTPUT_SPECS}
    if len(items) != 12:
        blockers.append("output_path_count_mismatch")
    seen_names: set[str] = set()
    all_inside_final_root = True
    for logical_name, raw_value in items:
        path = Path(raw_value)
        if ".." in path.parts:
            blockers.append(f"output_path_parent_traversal:{logical_name}")
        absolute = path if path.is_absolute() else root / path
        if absolute.name != expected_names.get(logical_name):
            blockers.append(f"output_filename_mismatch:{logical_name}")
        if absolute.name in seen_names:
            blockers.append(f"output_filename_duplicate:{absolute.name}")
        seen_names.add(absolute.name)
        try:
            relative = absolute.relative_to(root)
        except ValueError:
            blockers.append(f"output_path_outside_repo:{logical_name}")
            all_inside_final_root = False
            continue
        if absolute.parent != final_root:
            blockers.append(f"output_path_outside_final_root:{logical_name}")
            all_inside_final_root = False
        cursor = root
        escaped_symlink = False
        for part in relative.parts:
            cursor /= part
            if cursor.is_symlink():
                escaped_symlink = True
                break
        if escaped_symlink:
            blockers.append(f"output_path_symlink_escape:{logical_name}")
        resolved = absolute.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError:
            blockers.append(f"output_path_outside_repo:{logical_name}")
        raw_root = root / "data/raw"
        try:
            resolved.relative_to(raw_root)
            blockers.append(f"output_path_raw_forbidden:{logical_name}")
        except ValueError:
            pass
    blockers = sorted(set(blockers))
    return {
        "output_path_contract_passed": not blockers,
        "output_path_count": len(items),
        "output_filenames_unique": len(seen_names) == len(items),
        "all_outputs_inside_final_root": all_inside_final_root and not any("symlink_escape" in item for item in blockers),
        "blocking_reasons": blockers,
    }


@dataclass
class DiskWriteActivity:
    read_paths: set[str] = field(default_factory=set)
    written_paths: set[str] = field(default_factory=set)
    temporary_paths: set[str] = field(default_factory=set)


def atomic_write_text(path: Path, text: str, activity: DiskWriteActivity) -> None:
    if path.is_symlink() or (path.exists() and path.is_dir()):
        raise OSError("output_path_not_regular_file")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    if temporary.is_symlink() or (temporary.exists() and temporary.is_dir()):
        raise OSError("temporary_path_not_regular_file")
    activity.temporary_paths.add(str(temporary))
    try:
        temporary.write_text(text, encoding="utf-8", newline="")
        os.replace(temporary, path)
        activity.written_paths.add(str(path.resolve()))
    finally:
        if temporary.exists() and not temporary.is_dir():
            temporary.unlink()
        activity.temporary_paths.discard(str(temporary))


def write_csv_atomic(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...], activity: DiskWriteActivity) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(fields), extrasaction="raise", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic_write_text(path, output.getvalue(), activity)


def write_json_atomic(path: Path, value: Any, activity: DiskWriteActivity) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False, allow_nan=False) + "\n", activity)


def read_csv_with_header(path: Path, activity: DiskWriteActivity) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); header = list(reader.fieldnames or []); rows = list(reader)
    activity.read_paths.add(str(path.resolve()))
    return header, rows


def read_json_safely(path: Path, activity: DiskWriteActivity) -> Any:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    activity.read_paths.add(str(path.resolve()))
    return value


def build_final_dataset_precondition_rows(source_validation: Step14AQSourceValidationResult) -> list[dict[str, Any]]:
    return [
        {
            "precondition_item": item,
            "expected_status": True,
            "observed_status": source_validation.source_checks.get(item),
            "precondition_passed": source_validation.source_checks.get(item) is True,
            "blocking_reasons": "" if source_validation.source_checks.get(item) is True else f"source_check_failed:{item}",
        }
        for item in SOURCE_CHECK_ORDER
    ]


def validate_final_dataset_precondition_rows(rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult) -> dict[str, Any]:
    blockers: list[str] = []
    if len(rows) != 23: blockers.append("final_precondition_row_count_mismatch")
    if [row.get("precondition_item") for row in rows] != list(SOURCE_CHECK_ORDER) or len({row.get("precondition_item") for row in rows}) != len(rows): blockers.append("final_precondition_item_contract_mismatch")
    for number, row in enumerate(rows, 1):
        item = row.get("precondition_item", f"row{number}")
        if list(row) != list(FINAL_DATASET_PRECONDITION_FIELDS): blockers.append(f"final_precondition_schema_mismatch:{number}")
        observed = source_validation.source_checks.get(item)
        passed = observed is True
        if row.get("expected_status") is not True or row.get("observed_status") is not observed or row.get("precondition_passed") is not passed or row.get("blocking_reasons") != ("" if passed else f"source_check_failed:{item}"):
            blockers.append(f"final_precondition_semantics_mismatch:{item}")
    return {"final_precondition_rows_passed": not blockers, "precondition_row_count": len(rows), "precondition_passed_count": sum(row.get("precondition_passed") is True for row in rows), "blocking_reasons": sorted(set(blockers))}


def validate_written_source_step14aq_preconditions_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"source_precondition_write_validation_passed": False, "source_precondition_row_count": 0, "source_precondition_passed_count": 0, "typed_rows": [], "blocking_reasons": ["source_precondition_csv_unreadable"]}
    if header != list(FINAL_DATASET_PRECONDITION_FIELDS): blockers.append("source_precondition_csv_schema_mismatch")
    if len(disk_rows) != 23: blockers.append("source_precondition_csv_row_count_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field_name in ("expected_status", "observed_status", "precondition_passed"):
            try: typed[field_name] = parse_strict_bool(row.get(field_name))
            except ValueError: blockers.append(f"source_precondition_csv_type_invalid:{number}:{field_name}")
        typed_rows.append(typed)
    if typed_rows != expected_rows: blockers.append("source_precondition_csv_content_mismatch")
    return {"source_precondition_write_validation_passed": not blockers, "source_precondition_row_count": len(disk_rows), "source_precondition_passed_count": sum(row.get("precondition_passed") is True for row in typed_rows), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def _parse_disk_index_rows(rows: list[dict[str, Any]], prefix: str, blockers: list[str]) -> list[dict[str, Any]]:
    typed_rows: list[dict[str, Any]] = []
    for number, row in enumerate(rows, 1):
        typed: dict[str, Any] = {}
        for field_name in SAMPLE_INDEX_FIELDS:
            value = row.get(field_name)
            try:
                if field_name in SAMPLE_INDEX_INT_FIELDS: typed[field_name] = parse_strict_int(value)
                elif field_name == "bond_distance_angstrom": typed[field_name] = parse_strict_float(value)
                elif field_name in SAMPLE_INDEX_BOOL_FIELDS: typed[field_name] = parse_strict_bool(value)
                elif isinstance(value, str): typed[field_name] = value
                else: raise ValueError("string_required")
            except ValueError:
                blockers.append(f"{prefix}_type_invalid:{number}:{field_name}"); typed[field_name] = value
        typed_rows.append(typed)
    return typed_rows


def _validate_index_rows(expected_rows: list[dict[str, Any]], typed_rows: list[dict[str, Any]], prefix: str, blockers: list[str]) -> None:
    if len(typed_rows) != 11: blockers.append(f"{prefix}_row_count_mismatch")
    if [row.get("sample_index_row_id") for row in typed_rows] != list(EXPECTED_SAMPLE_INDEX_ROW_IDS): blockers.append(f"{prefix}_order_mismatch")
    for number, row in enumerate(typed_rows, 1):
        sample = row.get("sample_index_row_id", f"row{number}")
        expected = expected_rows[number - 1] if number <= len(expected_rows) else {}
        for field_name in SAMPLE_INDEX_FIELDS:
            if row.get(field_name) != expected.get(field_name): blockers.append(f"{prefix}_content_mismatch:{sample}:{field_name}")
        if any(not isinstance(row.get(field_name), str) or not row.get(field_name) for field_name in ARTIFACT_PATH_FIELDS) or row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True or row.get("leakage_split_design_required_before_training") is not True:
            blockers.append(f"{prefix}_boundary_mismatch:{sample}")


def validate_written_final_dataset_index_csv(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"final_index_csv_write_validation_passed": False, "row_count": 0, "schema_field_count": 0, "canonical_order_passed": False, "source_values_preserved": False, "typed_rows": [], "blocking_reasons": ["final_index_csv_unreadable"]}
    if header != list(SAMPLE_INDEX_FIELDS): blockers.append("final_index_csv_schema_mismatch")
    typed_rows = _parse_disk_index_rows(disk_rows, "final_index_csv", blockers); _validate_index_rows(expected_rows, typed_rows, "final_index_csv", blockers)
    return {"final_index_csv_write_validation_passed": not blockers, "row_count": len(disk_rows), "schema_field_count": len(header), "canonical_order_passed": [row.get("sample_index_row_id") for row in typed_rows] == list(EXPECTED_SAMPLE_INDEX_ROW_IDS), "source_values_preserved": typed_rows == expected_rows, "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def validate_written_final_dataset_index_json(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []
    try: value = read_json_safely(path, activity)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"final_index_json_write_validation_passed": False, "row_count": 0, "schema_field_count": 0, "canonical_order_passed": False, "source_values_preserved": False, "typed_rows": [], "blocking_reasons": ["final_index_json_unreadable"]}
    if not isinstance(value, list): return {"final_index_json_write_validation_passed": False, "row_count": 0, "schema_field_count": 0, "canonical_order_passed": False, "source_values_preserved": False, "typed_rows": [], "blocking_reasons": ["final_index_json_root_invalid"]}
    if len(value) != 11: blockers.append("final_index_json_row_count_mismatch")
    for number, row in enumerate(value, 1):
        if not isinstance(row, dict) or list(row) != list(SAMPLE_INDEX_FIELDS): blockers.append(f"final_index_json_schema_mismatch:{number}")
    typed_rows = _parse_disk_index_rows([row if isinstance(row, dict) else {} for row in value], "final_index_json", blockers); _validate_index_rows(expected_rows, typed_rows, "final_index_json", blockers)
    return {"final_index_json_write_validation_passed": not blockers, "row_count": len(value), "schema_field_count": len(value[0]) if value and isinstance(value[0], dict) else 0, "canonical_order_passed": [row.get("sample_index_row_id") for row in typed_rows] == list(EXPECTED_SAMPLE_INDEX_ROW_IDS), "source_values_preserved": typed_rows == expected_rows, "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def validate_final_dataset_index_cross_format(csv_validation: dict[str, Any], json_validation: dict[str, Any]) -> dict[str, Any]:
    passed = csv_validation.get("final_index_csv_write_validation_passed") is True and json_validation.get("final_index_json_write_validation_passed") is True and csv_validation.get("typed_rows") == json_validation.get("typed_rows")
    return {"final_index_csv_json_consistent": passed, "blocking_reasons": [] if passed else ["final_index_cross_format_mismatch"]}


MEMBERSHIP_INT_FIELDS = ("canonical_row_order", "assigned_split_rank", "final_leakage_group_member_count")
MEMBERSHIP_BOOL_FIELDS = tuple(field_name for field_name in FINAL_DATASET_MEMBERSHIP_FIELDS if field_name.endswith("_found") or field_name.endswith("_consistent") or field_name.endswith("_passed") or field_name in {"eligible_for_final_dataset_qa_gate_current_step", "ready_for_training_current_step", "feature_semantics_audit_required_before_training"})


def validate_written_membership_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"membership_write_validation_passed": False, "membership_row_count": 0, "membership_passed_count": 0, "typed_rows": [], "blocking_reasons": ["membership_csv_unreadable"]}
    if header != list(FINAL_DATASET_MEMBERSHIP_FIELDS): blockers.append("membership_csv_schema_mismatch")
    if len(disk_rows) != 11: blockers.append("membership_csv_row_count_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed: dict[str, Any] = {}
        for field_name in FINAL_DATASET_MEMBERSHIP_FIELDS:
            value = row.get(field_name)
            try:
                if field_name in MEMBERSHIP_INT_FIELDS: typed[field_name] = parse_strict_int(value)
                elif field_name in MEMBERSHIP_BOOL_FIELDS: typed[field_name] = parse_strict_bool(value)
                elif isinstance(value, str): typed[field_name] = value
                else: raise ValueError("string_required")
            except ValueError:
                blockers.append(f"membership_csv_type_invalid:{number}:{field_name}"); typed[field_name] = value
        typed_rows.append(typed)
    if [row.get("final_dataset_membership_id") for row in typed_rows] != [f"COVAPIE_FINAL_DATASET_MEMBERSHIP_{number:06d}" for number in range(1, 12)] or [row.get("canonical_row_order") for row in typed_rows] != list(range(1, 12)):
        blockers.append("membership_csv_order_mismatch")
    for number, row in enumerate(typed_rows, 1):
        sample = row.get("sample_index_row_id", f"row{number}"); expected = expected_rows[number - 1] if number <= len(expected_rows) else {}
        for field_name in FINAL_DATASET_MEMBERSHIP_FIELDS:
            if row.get(field_name) != expected.get(field_name): blockers.append(f"membership_csv_content_mismatch:{sample}:{field_name}")
        if row.get("final_dataset_membership_passed") is not True or row.get("eligible_for_final_dataset_qa_gate_current_step") != row.get("final_dataset_membership_passed"):
            blockers.append(f"membership_csv_pass_mismatch:{sample}")
        if row.get("ready_for_training_current_step") is not False or row.get("feature_semantics_audit_required_before_training") is not True:
            blockers.append(f"membership_csv_training_boundary_mismatch:{sample}")
    return {"membership_write_validation_passed": not blockers, "membership_row_count": len(disk_rows), "membership_passed_count": sum(row.get("final_dataset_membership_passed") is True for row in typed_rows), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


@dataclass
class CoreDiskMaterializationResult:
    passed: bool; blocking_reasons: list[str]; output_paths: Step14AROutputPaths
    precondition_rows: list[dict[str, Any]]; final_index_rows: list[dict[str, Any]]; membership_rows: list[dict[str, Any]]
    output_path_validation: dict[str, Any]; precondition_write_validation: dict[str, Any]
    final_index_csv_write_validation: dict[str, Any]; final_index_json_write_validation: dict[str, Any]
    final_index_cross_format_validation: dict[str, Any]; membership_write_validation: dict[str, Any]
    activity: DiskWriteActivity; ready_for_remaining_disk_materialization: bool
    ready_for_covapie_final_dataset_qa_gate: bool = False; ready_for_training: bool = False; ready_to_train_now: bool = False

    @property
    def core_disk_materialization_passed(self) -> bool:
        return self.passed and not self.blocking_reasons


def _validation_failure(name: str, blockers: list[str]) -> dict[str, Any]:
    return {name: False, "blocking_reasons": blockers, "typed_rows": []}


def _write_blocked_core_outputs(paths: Step14AROutputPaths, activity: DiskWriteActivity) -> None:
    write_csv_atomic(paths.precondition_audit, [], FINAL_DATASET_PRECONDITION_FIELDS, activity)
    write_csv_atomic(paths.final_dataset_index_csv, [], SAMPLE_INDEX_FIELDS, activity)
    write_json_atomic(paths.final_dataset_index_json, [], activity)
    write_csv_atomic(paths.membership, [], FINAL_DATASET_MEMBERSHIP_FIELDS, activity)


def materialize_final_dataset_core_to_disk(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, *, output_paths: Step14AROutputPaths = DEFAULT_STEP14AR_OUTPUT_PATHS, repo_root: Path = REPO) -> CoreDiskMaterializationResult:
    activity = DiskWriteActivity(); path_validation = validate_step14ar_output_paths(output_paths, repo_root=repo_root)
    if not path_validation["output_path_contract_passed"]:
        blockers = list(path_validation["blocking_reasons"])
        return CoreDiskMaterializationResult(False, blockers, output_paths, [], [], [], path_validation, _validation_failure("source_precondition_write_validation_passed", blockers), _validation_failure("final_index_csv_write_validation_passed", blockers), _validation_failure("final_index_json_write_validation_passed", blockers), _validation_failure("final_index_csv_json_consistent", blockers), _validation_failure("membership_write_validation_passed", blockers), activity, False)
    if not source_validation.source_validation_passed or not in_memory_result.in_memory_materialization_passed:
        blockers = sorted(set([*([] if source_validation.source_validation_passed else ["core_disk_source_validation_not_passed", *source_validation.blocking_reasons]), *([] if in_memory_result.in_memory_materialization_passed else ["core_disk_in_memory_validation_not_passed", *in_memory_result.blocking_reasons])]))
        _write_blocked_core_outputs(output_paths, activity)
        return CoreDiskMaterializationResult(False, blockers, output_paths, [], [], [], path_validation, _validation_failure("source_precondition_write_validation_passed", blockers), _validation_failure("final_index_csv_write_validation_passed", blockers), _validation_failure("final_index_json_write_validation_passed", blockers), _validation_failure("final_index_csv_json_consistent", blockers), _validation_failure("membership_write_validation_passed", blockers), activity, False)
    precondition_rows = build_final_dataset_precondition_rows(source_validation)
    precondition_contract = validate_final_dataset_precondition_rows(precondition_rows, source_validation)
    final_index_rows = in_memory_result.final_index_validation.validated_rows if in_memory_result.final_index_validation else []
    membership_rows = in_memory_result.membership_validation.validated_rows if in_memory_result.membership_validation else []
    write_csv_atomic(output_paths.precondition_audit, precondition_rows, FINAL_DATASET_PRECONDITION_FIELDS, activity)
    precondition_validation = validate_written_source_step14aq_preconditions_passed(precondition_rows, output_paths.precondition_audit, activity)
    write_csv_atomic(output_paths.final_dataset_index_csv, final_index_rows, SAMPLE_INDEX_FIELDS, activity)
    csv_validation = validate_written_final_dataset_index_csv(final_index_rows, output_paths.final_dataset_index_csv, activity)
    write_json_atomic(output_paths.final_dataset_index_json, final_index_rows, activity)
    json_validation = validate_written_final_dataset_index_json(final_index_rows, output_paths.final_dataset_index_json, activity)
    cross_validation = validate_final_dataset_index_cross_format(csv_validation, json_validation)
    write_csv_atomic(output_paths.membership, membership_rows, FINAL_DATASET_MEMBERSHIP_FIELDS, activity)
    membership_validation = validate_written_membership_checks_passed(membership_rows, output_paths.membership, activity)
    blockers = sorted(set(precondition_contract["blocking_reasons"] + precondition_validation["blocking_reasons"] + csv_validation["blocking_reasons"] + json_validation["blocking_reasons"] + cross_validation["blocking_reasons"] + membership_validation["blocking_reasons"]))
    passed = not blockers
    return CoreDiskMaterializationResult(passed, blockers, output_paths, precondition_rows, final_index_rows, membership_rows, path_validation, precondition_validation, csv_validation, json_validation, cross_validation, membership_validation, activity, passed)


ARTIFACT_INVENTORY_BOOL_FIELDS = ("artifact_path_is_relative", "artifact_path_exists", "artifact_is_regular_file", "artifact_reference_preserved", "artifact_inventory_passed")
SCHEMA_AUDIT_BOOL_FIELDS = ("csv_column_present", "json_field_present_all_rows", "non_null_rule_passed", "csv_json_typed_consistency_passed", "source_field_preservation_passed", "schema_validation_passed")
SOURCE_PRESERVATION_BOOL_FIELDS = ("source_split_row_found", "source_sample_assignment_row_found", "final_dataset_csv_row_found", "final_dataset_json_row_found", "all_33_fields_preserved", "split_membership_preserved", "group_membership_preserved", "six_artifact_references_preserved", "artifact_paths_exist", "source_preservation_passed")


def validate_written_artifact_inventory_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"artifact_inventory_write_validation_passed": False, "artifact_inventory_row_count": 0, "artifact_inventory_passed_count": 0, "unique_sample_field_count": 0, "typed_rows": [], "blocking_reasons": ["artifact_inventory_csv_unreadable"]}
    if header != list(FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS): blockers.append("artifact_inventory_csv_schema_mismatch")
    if len(disk_rows) != 66: blockers.append("artifact_inventory_csv_row_count_mismatch")
    seen: set[tuple[str, str]] = set()
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field_name in FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS:
            try:
                if field_name == "artifact_size_bytes": typed[field_name] = parse_strict_int(row.get(field_name))
                elif field_name in ARTIFACT_INVENTORY_BOOL_FIELDS: typed[field_name] = parse_strict_bool(row.get(field_name))
                elif not isinstance(row.get(field_name), str): raise ValueError("string_required")
            except ValueError: blockers.append(f"artifact_inventory_csv_type_invalid:{number}:{field_name}")
        sample, field_name = typed.get("sample_index_row_id", f"row{number}"), typed.get("source_field_name", "")
        key = (sample, field_name)
        if key in seen: blockers.append(f"artifact_inventory_csv_duplicate_sample_field:{sample}:{field_name}")
        seen.add(key)
        expected = expected_rows[number - 1] if number <= len(expected_rows) else {}
        if typed.get("artifact_inventory_id") != f"COVAPIE_FINAL_ARTIFACT_{number:06d}" or field_name not in ARTIFACT_PATH_FIELDS or typed.get("artifact_role") != ARTIFACT_ROLE_BY_FIELD.get(field_name): blockers.append(f"artifact_inventory_csv_id_or_order_mismatch:{number}")
        for name in FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS:
            if typed.get(name) != expected.get(name): blockers.append(f"artifact_inventory_csv_content_mismatch:{sample}:{name}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(typed.get("artifact_sha256", ""))): blockers.append(f"artifact_inventory_csv_hash_invalid:{sample}:{field_name}")
        if not isinstance(typed.get("artifact_path"), str) or not typed.get("artifact_path") or Path(typed["artifact_path"]).is_absolute() or typed.get("artifact_path_exists") is not True or typed.get("artifact_is_regular_file") is not True or typed.get("artifact_size_bytes", 0) <= 0: blockers.append(f"artifact_inventory_csv_path_contract_mismatch:{sample}:{field_name}")
        if typed.get("artifact_reference_preserved") is not True or typed.get("artifact_inventory_passed") is not True or typed.get("blocking_reasons") != "": blockers.append(f"artifact_inventory_csv_pass_mismatch:{sample}:{field_name}")
        typed_rows.append(typed)
    return {"artifact_inventory_write_validation_passed": not blockers, "artifact_inventory_row_count": len(disk_rows), "artifact_inventory_passed_count": sum(row.get("artifact_inventory_passed") is True for row in typed_rows), "unique_sample_field_count": len(seen), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def validate_written_artifact_inventory_write_validation_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    return validate_written_artifact_inventory_checks_passed(expected_rows, path, activity)


def build_candidate_final_dataset_schema_validation_rows(source_validation: Step14AQSourceValidationResult, core_disk_result: CoreDiskMaterializationResult) -> list[dict[str, Any]]:
    return [{"schema_validation_id": f"COVAPIE_FINAL_SCHEMA_{number:06d}", "sample_index_field": field_name, "expected_data_type": SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD[field_name]} for number, field_name in enumerate(SAMPLE_INDEX_FIELDS, 1)]


@dataclass
class SchemaAuditValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_rows: list[dict[str, Any]]
    row_count_passed: bool; schema_passed: bool; field_order_passed: bool; all_fields_present: bool; all_types_passed: bool; csv_json_consistent: bool; source_values_preserved: bool


def build_final_dataset_index_schema_audit_evidence(candidate_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult, core_disk_result: CoreDiskMaterializationResult) -> SchemaAuditValidationResult:
    blockers: list[str] = []; rows: list[dict[str, Any]] = []
    csv_rows = core_disk_result.final_index_csv_write_validation.get("typed_rows", []); json_rows = core_disk_result.final_index_json_write_validation.get("typed_rows", []); csv_header = core_disk_result.final_index_csv_write_validation.get("schema_field_count") == len(SAMPLE_INDEX_FIELDS)
    if len(candidate_rows) != 33: blockers.append("schema_audit_row_count_mismatch")
    field_order = [row.get("sample_index_field") for row in candidate_rows] == list(SAMPLE_INDEX_FIELDS)
    if not field_order: blockers.append("schema_audit_field_order_mismatch")
    all_fields = all_types = cross = preserved = schema_ok = True
    for number, candidate in enumerate(candidate_rows, 1):
        field_name = candidate.get("sample_index_field", f"row{number}"); local: list[str] = []
        candidate_ok = list(candidate) == ["schema_validation_id", "sample_index_field", "expected_data_type"]
        if not candidate_ok: local.append(f"schema_audit_candidate_schema_mismatch:{number}")
        if candidate.get("schema_validation_id") != f"COVAPIE_FINAL_SCHEMA_{number:06d}": local.append(f"schema_audit_id_mismatch:{number}")
        expected_type = SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD.get(field_name)
        if candidate.get("expected_data_type") != expected_type: local.append(f"schema_audit_expected_type_mismatch:{field_name}")
        csv_present = csv_header and all(field_name in row for row in csv_rows)
        json_present = bool(json_rows) and all(field_name in row and list(row) == list(SAMPLE_INDEX_FIELDS) for row in json_rows)
        if not csv_present: local.append(f"schema_audit_csv_column_missing:{field_name}")
        if not json_present: local.append(f"schema_audit_json_field_missing:{field_name}")
        values = [row.get(field_name) for row in csv_rows]
        predicate = {"string": lambda value: isinstance(value, str) and bool(value), "integer": lambda value: isinstance(value, int) and not isinstance(value, bool), "float": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), "boolean": lambda value: value is True or value is False}.get(expected_type, lambda value: False)
        types_ok = len(values) == 11 and all(predicate(value) for value in values)
        consistency = len(csv_rows) == len(json_rows) == 11 and [row.get(field_name) for row in csv_rows] == [row.get(field_name) for row in json_rows]
        source_ok = len(source_validation.canonical_source_rows) == 11 and [row.get(field_name) for row in csv_rows] == [row.get(field_name) for row in source_validation.canonical_source_rows]
        if not types_ok: local.append(f"schema_audit_non_null_failed:{field_name}")
        if not consistency: local.append(f"schema_audit_csv_json_type_mismatch:{field_name}")
        if not source_ok: local.append(f"schema_audit_source_preservation_failed:{field_name}")
        passed = candidate_ok and not local
        all_fields &= csv_present and json_present; all_types &= types_ok; cross &= consistency; preserved &= source_ok; schema_ok &= candidate_ok
        evidence = {"csv_column_present": csv_present, "json_field_present_all_rows": json_present, "non_null_rule_passed": types_ok, "csv_json_typed_consistency_passed": consistency, "source_field_preservation_passed": source_ok, "schema_validation_passed": passed, "blocking_reasons": ";".join(local)}
        rows.append({field: evidence[field] if field in evidence else candidate.get(field) for field in FINAL_DATASET_SCHEMA_AUDIT_FIELDS}); blockers.extend(local)
    blockers = sorted(set(blockers)); return SchemaAuditValidationResult(not blockers, blockers, rows, len(candidate_rows) == 33, schema_ok, field_order, all_fields, all_types, cross, preserved)


def validate_written_final_dataset_index_schema_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"schema_audit_write_validation_passed": False, "schema_audit_row_count": 0, "schema_audit_passed_count": 0, "typed_rows": [], "blocking_reasons": ["schema_audit_csv_unreadable"]}
    if header != list(FINAL_DATASET_SCHEMA_AUDIT_FIELDS): blockers.append("schema_audit_csv_schema_mismatch")
    if len(disk_rows) != 33: blockers.append("schema_audit_csv_row_count_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field in SCHEMA_AUDIT_BOOL_FIELDS:
            try: typed[field] = parse_strict_bool(row.get(field))
            except ValueError: blockers.append(f"schema_audit_csv_type_invalid:{number}:{field}")
        field_name = typed.get("sample_index_field", f"row{number}"); expected = expected_rows[number - 1] if number <= len(expected_rows) else {}
        if typed.get("schema_validation_id") != f"COVAPIE_FINAL_SCHEMA_{number:06d}" or field_name != (SAMPLE_INDEX_FIELDS[number - 1] if number <= len(SAMPLE_INDEX_FIELDS) else None) or typed.get("expected_data_type") != SAMPLE_INDEX_EXPECTED_TYPE_BY_FIELD.get(field_name): blockers.append("schema_audit_csv_order_mismatch")
        for name in FINAL_DATASET_SCHEMA_AUDIT_FIELDS:
            if typed.get(name) != expected.get(name): blockers.append(f"schema_audit_csv_content_mismatch:{field_name}:{name}")
        if typed.get("schema_validation_passed") is not True or typed.get("blocking_reasons") != "": blockers.append(f"schema_audit_csv_pass_mismatch:{field_name}")
        typed_rows.append(typed)
    return {"schema_audit_write_validation_passed": not blockers, "schema_audit_row_count": len(disk_rows), "schema_audit_passed_count": sum(row.get("schema_validation_passed") is True for row in typed_rows), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def build_candidate_source_preservation_rows(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, artifact_inventory_write_validation: dict[str, Any]) -> list[dict[str, Any]]:
    samples = _multi(source_validation.typed_sample_rows, "sample_index_row_id")
    return [{"source_preservation_id": f"COVAPIE_FINAL_SOURCE_PRESERVATION_{number:06d}", "sample_index_row_id": sample_id, "assigned_split": samples.get(sample_id, [{}])[0].get("assigned_split", "")} for number, sample_id in enumerate(EXPECTED_SAMPLE_INDEX_ROW_IDS, 1)]


@dataclass
class SourcePreservationValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_rows: list[dict[str, Any]]
    row_count_passed: bool; schema_passed: bool; canonical_order_passed: bool; all_33_fields_preserved: bool; split_membership_preserved: bool; group_membership_preserved: bool; artifact_references_preserved: bool


def build_source_preservation_checks_passed_evidence(candidate_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, artifact_inventory_write_validation: dict[str, Any]) -> SourcePreservationValidationResult:
    blockers: list[str] = []; rows: list[dict[str, Any]] = []
    split_rows = _multi(source_validation.typed_train_rows + source_validation.typed_validation_rows + source_validation.typed_test_rows, "sample_index_row_id"); split_names: dict[str, list[str]] = {}
    for split_name, source_rows in (("train", source_validation.typed_train_rows), ("validation", source_validation.typed_validation_rows), ("test", source_validation.typed_test_rows)):
        for source_row in source_rows: split_names.setdefault(source_row.get("sample_index_row_id", ""), []).append(split_name)
    samples = _multi(source_validation.typed_sample_rows, "sample_index_row_id"); groups = _multi(source_validation.typed_group_rows, "final_leakage_group_id"); csv_rows = _multi(core_disk_result.final_index_csv_write_validation.get("typed_rows", []), "sample_index_row_id"); json_rows = _multi(core_disk_result.final_index_json_write_validation.get("typed_rows", []), "sample_index_row_id"); memberships = _multi(core_disk_result.membership_write_validation.get("typed_rows", []), "sample_index_row_id"); inventory = _multi(artifact_inventory_write_validation.get("typed_rows", []), "sample_index_row_id"); canonical = _multi(source_validation.canonical_source_rows, "sample_index_row_id")
    if len(candidate_rows) != 11: blockers.append("source_preservation_row_count_mismatch")
    if [row.get("sample_index_row_id") for row in candidate_rows] != list(EXPECTED_SAMPLE_INDEX_ROW_IDS): blockers.append("source_preservation_sample_order_mismatch")
    flags = {"schema": True, "fields": True, "split": True, "group": True, "artifact": True}
    for number, candidate in enumerate(candidate_rows, 1):
        sample = candidate.get("sample_index_row_id", f"row{number}"); local: list[str] = []
        candidate_ok = list(candidate) == ["source_preservation_id", "sample_index_row_id", "assigned_split"]
        if not candidate_ok: local.append(f"source_preservation_candidate_schema_mismatch:{number}")
        if candidate.get("source_preservation_id") != f"COVAPIE_FINAL_SOURCE_PRESERVATION_{number:06d}": local.append(f"source_preservation_id_mismatch:{number}")
        split, assignment, csv_row, json_row, member, canon = split_rows.get(sample, []), samples.get(sample, []), csv_rows.get(sample, []), json_rows.get(sample, []), memberships.get(sample, []), canonical.get(sample, [])
        for name, value in (("source_split", split), ("sample_assignment", assignment), ("final_csv", csv_row), ("final_json", json_row)):
            if len(value) == 0: local.append(f"source_preservation_{name}_missing:{sample}")
            elif len(value) > 1: local.append(f"source_preservation_{name}_duplicate:{sample}")
        field_rows_unique = all(len(value) == 1 for value in (split, csv_row, json_row, canon)); split_value = split[0] if len(split) == 1 else {}; assign = assignment[0] if len(assignment) == 1 else {}; csv_value = csv_row[0] if len(csv_row) == 1 else {}; json_value = json_row[0] if len(json_row) == 1 else {}; membership = member[0] if len(member) == 1 else {}; canonical_value = canon[0] if len(canon) == 1 else {}
        fields_ok = field_rows_unique and all(split_value.get(field) == canonical_value.get(field) == csv_value.get(field) == json_value.get(field) for field in SAMPLE_INDEX_FIELDS)
        if not fields_ok:
            for field in SAMPLE_INDEX_FIELDS:
                if not (field_rows_unique and split_value.get(field) == canonical_value.get(field) == csv_value.get(field) == json_value.get(field)): local.append(f"source_preservation_field_mismatch:{sample}:{field}")
        source_split_names = split_names.get(sample, [])
        split_ok = len(assignment) == 1 and len(member) == 1 and len(split) == 1 and len(source_split_names) == 1 and candidate.get("assigned_split") == assign.get("assigned_split") == membership.get("assigned_split") == source_split_names[0]
        if not split_ok: local.append(f"source_preservation_split_mismatch:{sample}")
        group_rows = groups.get(assign.get("final_leakage_group_id", ""), []); group = group_rows[0] if len(group_rows) == 1 else {}
        group_ok = len(assignment) == 1 and len(member) == 1 and len(group_rows) == 1 and membership.get("final_leakage_group_id") == assign.get("final_leakage_group_id") and sample in str(group.get("member_sample_index_row_ids", "")).split(";") and group.get("assigned_split") == assign.get("assigned_split") and membership.get("final_leakage_group_member_count") == assign.get("final_leakage_group_member_count") == group.get("member_count")
        if not group_ok: local.append(f"source_preservation_group_mismatch:{sample}")
        artifacts = inventory.get(sample, []); artifact_ok = len(artifacts) == 6 and {row.get("source_field_name") for row in artifacts} == set(ARTIFACT_PATH_FIELDS)
        reference_ok = artifact_ok; paths_ok = artifact_ok
        for item in artifacts:
            field = item.get("source_field_name", "")
            item_ok = item.get("artifact_path") == csv_value.get(field) and item.get("artifact_reference_preserved") is True and item.get("artifact_inventory_passed") is True
            path_ok = item.get("artifact_path_exists") is True and item.get("artifact_is_regular_file") is True and item.get("artifact_size_bytes", 0) > 0 and bool(re.fullmatch(r"[0-9a-f]{64}", str(item.get("artifact_sha256", ""))))
            if not item_ok: local.append(f"source_preservation_artifact_reference_mismatch:{sample}:{field}")
            if not path_ok: local.append(f"source_preservation_artifact_path_invalid:{sample}:{field}")
            reference_ok &= item_ok; paths_ok &= path_ok
        if not artifact_ok: local.append(f"source_preservation_artifact_count_mismatch:{sample}")
        passed = candidate_ok and len(split) == 1 and len(assignment) == 1 and len(csv_row) == 1 and len(json_row) == 1 and fields_ok and split_ok and group_ok and reference_ok and paths_ok and not local
        flags["schema"] &= candidate_ok; flags["fields"] &= fields_ok; flags["split"] &= split_ok; flags["group"] &= group_ok; flags["artifact"] &= reference_ok and paths_ok
        evidence = {"source_split_row_found": len(split) == 1, "source_sample_assignment_row_found": len(assignment) == 1, "final_dataset_csv_row_found": len(csv_row) == 1, "final_dataset_json_row_found": len(json_row) == 1, "all_33_fields_preserved": fields_ok, "split_membership_preserved": split_ok, "group_membership_preserved": group_ok, "six_artifact_references_preserved": reference_ok, "artifact_paths_exist": paths_ok, "source_preservation_passed": passed, "blocking_reasons": ";".join(local)}
        rows.append({field: evidence[field] if field in evidence else candidate.get(field) for field in FINAL_DATASET_SOURCE_PRESERVATION_FIELDS}); blockers.extend(local)
    blockers = sorted(set(blockers)); return SourcePreservationValidationResult(not blockers, blockers, rows, len(candidate_rows) == 11, flags["schema"], [row.get("sample_index_row_id") for row in candidate_rows] == list(EXPECTED_SAMPLE_INDEX_ROW_IDS), flags["fields"], flags["split"], flags["group"], flags["artifact"])


def validate_written_source_preservation_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"source_preservation_write_validation_passed": False, "source_preservation_row_count": 0, "source_preservation_passed_count": 0, "typed_rows": [], "blocking_reasons": ["source_preservation_csv_unreadable"]}
    if header != list(FINAL_DATASET_SOURCE_PRESERVATION_FIELDS): blockers.append("source_preservation_csv_schema_mismatch")
    if len(disk_rows) != 11: blockers.append("source_preservation_csv_row_count_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field in SOURCE_PRESERVATION_BOOL_FIELDS:
            try: typed[field] = parse_strict_bool(row.get(field))
            except ValueError: blockers.append(f"source_preservation_csv_type_invalid:{number}:{field}")
        sample = typed.get("sample_index_row_id", f"row{number}"); expected = expected_rows[number - 1] if number <= len(expected_rows) else {}
        if typed.get("source_preservation_id") != f"COVAPIE_FINAL_SOURCE_PRESERVATION_{number:06d}" or sample != (EXPECTED_SAMPLE_INDEX_ROW_IDS[number - 1] if number <= len(EXPECTED_SAMPLE_INDEX_ROW_IDS) else None): blockers.append("source_preservation_csv_order_mismatch")
        for name in FINAL_DATASET_SOURCE_PRESERVATION_FIELDS:
            if typed.get(name) != expected.get(name): blockers.append(f"source_preservation_csv_content_mismatch:{sample}:{name}")
        if typed.get("source_preservation_passed") is not True or typed.get("blocking_reasons") != "": blockers.append(f"source_preservation_csv_pass_mismatch:{sample}")
        typed_rows.append(typed)
    return {"source_preservation_write_validation_passed": not blockers, "source_preservation_row_count": len(disk_rows), "source_preservation_passed_count": sum(row.get("source_preservation_passed") is True for row in typed_rows), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


@dataclass
class ReferenceAuditDiskMaterializationResult:
    passed: bool; blocking_reasons: list[str]; output_paths: Step14AROutputPaths
    artifact_inventory_rows: list[dict[str, Any]]; schema_audit_rows: list[dict[str, Any]]; source_preservation_rows: list[dict[str, Any]]
    artifact_inventory_write_validation: dict[str, Any]; schema_audit_validation: SchemaAuditValidationResult | None; schema_audit_write_validation: dict[str, Any]
    source_preservation_validation: SourcePreservationValidationResult | None; source_preservation_write_validation: dict[str, Any]
    preflight_core_validation: dict[str, Any]; activity: DiskWriteActivity; ready_for_summary_and_integrity_disk_materialization: bool
    ready_for_covapie_final_dataset_qa_gate: bool = False; ready_for_training: bool = False; ready_to_train_now: bool = False

    @property
    def reference_audit_disk_materialization_passed(self) -> bool:
        return self.passed and not self.blocking_reasons


def _r3a_preflight(core: CoreDiskMaterializationResult, activity: DiskWriteActivity) -> dict[str, Any]:
    pre = validate_written_source_step14aq_preconditions_passed(core.precondition_rows, core.output_paths.precondition_audit, activity)
    csv_result = validate_written_final_dataset_index_csv(core.final_index_rows, core.output_paths.final_dataset_index_csv, activity)
    json_result = validate_written_final_dataset_index_json(core.final_index_rows, core.output_paths.final_dataset_index_json, activity)
    cross = validate_final_dataset_index_cross_format(csv_result, json_result)
    membership = validate_written_membership_checks_passed(core.membership_rows, core.output_paths.membership, activity)
    passed = all((pre["source_precondition_write_validation_passed"], csv_result["final_index_csv_write_validation_passed"], json_result["final_index_json_write_validation_passed"], cross["final_index_csv_json_consistent"], membership["membership_write_validation_passed"]))
    return {"precondition": pre, "csv": csv_result, "json": json_result, "cross": cross, "membership": membership, "preflight_core_validation_passed": passed, "blocking_reasons": sorted(set(pre["blocking_reasons"] + csv_result["blocking_reasons"] + json_result["blocking_reasons"] + cross["blocking_reasons"] + membership["blocking_reasons"]))}


def _write_blocked_reference_audits(paths: Step14AROutputPaths, activity: DiskWriteActivity) -> None:
    write_csv_atomic(paths.artifact_inventory, [], FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS, activity)
    write_csv_atomic(paths.schema_validation_audit, [], FINAL_DATASET_SCHEMA_AUDIT_FIELDS, activity)
    write_csv_atomic(paths.source_preservation_audit, [], FINAL_DATASET_SOURCE_PRESERVATION_FIELDS, activity)


def materialize_reference_audits_to_disk(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, *, output_paths: Step14AROutputPaths = DEFAULT_STEP14AR_OUTPUT_PATHS, repo_root: Path = REPO) -> ReferenceAuditDiskMaterializationResult:
    activity = DiskWriteActivity(); paths = validate_step14ar_output_paths(output_paths, repo_root=repo_root)
    empty = _validation_failure
    if not paths["output_path_contract_passed"]:
        blockers = paths["blocking_reasons"]
        return ReferenceAuditDiskMaterializationResult(False, blockers, output_paths, [], [], [], empty("artifact_inventory_write_validation_passed", blockers), None, empty("schema_audit_write_validation_passed", blockers), None, empty("source_preservation_write_validation_passed", blockers), {"preflight_core_validation_passed": False, "blocking_reasons": blockers}, activity, False)
    preflight_activity = DiskWriteActivity()
    preflight = _r3a_preflight(core_disk_result, preflight_activity) if core_disk_result.core_disk_materialization_passed else {"preflight_core_validation_passed": False, "blocking_reasons": ["r3a_core_result_not_passed"]}
    prerequisites = source_validation.source_validation_passed and in_memory_result.in_memory_materialization_passed and core_disk_result.core_disk_materialization_passed and core_disk_result.ready_for_remaining_disk_materialization and preflight["preflight_core_validation_passed"]
    if not prerequisites:
        blockers = sorted(set([*preflight["blocking_reasons"], *([] if source_validation.source_validation_passed else ["r3b1_source_validation_not_passed"]), *([] if in_memory_result.in_memory_materialization_passed else ["r3b1_in_memory_result_not_passed"]), *([] if core_disk_result.core_disk_materialization_passed else ["r3b1_core_result_not_passed"])]))
        _write_blocked_reference_audits(output_paths, activity)
        return ReferenceAuditDiskMaterializationResult(False, blockers, output_paths, [], [], [], empty("artifact_inventory_write_validation_passed", blockers), None, empty("schema_audit_write_validation_passed", blockers), None, empty("source_preservation_write_validation_passed", blockers), preflight, activity, False)
    inventory_rows = in_memory_result.artifact_inventory_validation.validated_rows if in_memory_result.artifact_inventory_validation else []
    write_csv_atomic(output_paths.artifact_inventory, inventory_rows, FINAL_DATASET_ARTIFACT_INVENTORY_FIELDS, activity)
    inventory_validation = validate_written_artifact_inventory_checks_passed(inventory_rows, output_paths.artifact_inventory, activity)
    candidates = build_candidate_final_dataset_schema_validation_rows(source_validation, core_disk_result)
    schema = build_final_dataset_index_schema_audit_evidence(candidates, source_validation, core_disk_result)
    write_csv_atomic(output_paths.schema_validation_audit, schema.validated_rows, FINAL_DATASET_SCHEMA_AUDIT_FIELDS, activity)
    schema_write = validate_written_final_dataset_index_schema_passed(schema.validated_rows, output_paths.schema_validation_audit, activity)
    preservation_candidates = build_candidate_source_preservation_rows(source_validation, in_memory_result, core_disk_result, inventory_validation)
    preservation = build_source_preservation_checks_passed_evidence(preservation_candidates, source_validation, in_memory_result, core_disk_result, inventory_validation)
    write_csv_atomic(output_paths.source_preservation_audit, preservation.validated_rows, FINAL_DATASET_SOURCE_PRESERVATION_FIELDS, activity)
    preservation_write = validate_written_source_preservation_checks_passed(preservation.validated_rows, output_paths.source_preservation_audit, activity)
    blockers = sorted(set(inventory_validation["blocking_reasons"] + schema.blocking_reasons + schema_write["blocking_reasons"] + preservation.blocking_reasons + preservation_write["blocking_reasons"]))
    passed = not blockers
    return ReferenceAuditDiskMaterializationResult(passed, blockers, output_paths, inventory_rows, schema.validated_rows, preservation.validated_rows, inventory_validation, schema, schema_write, preservation, preservation_write, preflight, activity, passed)


def preflight_existing_seven_outputs(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult) -> dict[str, Any]:
    activity = DiskWriteActivity(); core = _r3a_preflight(core_disk_result, activity)
    inventory = validate_written_artifact_inventory_checks_passed(reference_audit_result.artifact_inventory_rows, reference_audit_result.output_paths.artifact_inventory, activity)
    schema = validate_written_final_dataset_index_schema_passed(reference_audit_result.schema_audit_rows, reference_audit_result.output_paths.schema_validation_audit, activity)
    preservation = validate_written_source_preservation_checks_passed(reference_audit_result.source_preservation_rows, reference_audit_result.output_paths.source_preservation_audit, activity)
    passed = core["preflight_core_validation_passed"] and inventory["artifact_inventory_write_validation_passed"] and schema["schema_audit_write_validation_passed"] and preservation["source_preservation_write_validation_passed"]
    blockers = sorted(set(core["blocking_reasons"] + inventory["blocking_reasons"] + schema["blocking_reasons"] + preservation["blocking_reasons"]))
    return {"preflight_existing_outputs_passed": passed, "preflight_output_count": len(activity.read_paths), "core_preflight_passed": core["preflight_core_validation_passed"], "artifact_inventory_preflight_passed": inventory["artifact_inventory_write_validation_passed"], "schema_audit_preflight_passed": schema["schema_audit_write_validation_passed"], "source_preservation_preflight_passed": preservation["source_preservation_write_validation_passed"], "core": core, "inventory": inventory, "schema": schema, "preservation": preservation, "read_paths": activity.read_paths, "blocking_reasons": blockers}


def validate_step14ar_metadata_output_boundary(output_paths: Step14AROutputPaths, *, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve(); final_root = (root / FINAL_ROOT); blockers: list[str] = []; allowed = {filename for _, filename, *_ in OUTPUT_SPECS}; forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".npy")
    unknown = forbidden_count = temporary_count = 0
    if final_root.exists():
        for item in final_root.iterdir():
            if item.is_dir(): blockers.append(f"step14ar_unexpected_directory:{item.name}"); unknown += 1; continue
            name = item.name
            if name not in allowed: blockers.append(f"step14ar_unknown_output:{name}"); unknown += 1
            if name.endswith((".tmp", ".part")): blockers.append(f"step14ar_temporary_artifact:{name}"); temporary_count += 1
            if name.endswith(forbidden) or any(token in name.lower() for token in ("tensor", "dataloader", "checkpoint", "optimizer", "training_batch")):
                blockers.append(f"step14ar_forbidden_artifact:{name}"); forbidden_count += 1
    blockers = sorted(set(blockers)); return {"metadata_output_boundary_passed": not blockers, "existing_output_count": len(list(final_root.iterdir())) if final_root.exists() else 0, "unknown_output_count": unknown, "forbidden_artifact_count": forbidden_count, "temporary_artifact_count": temporary_count, "blocking_reasons": blockers}


def build_candidate_disk_split_summary_rows(source_validation: Step14AQSourceValidationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, preflight: dict[str, Any]) -> list[dict[str, Any]]:
    membership = preflight["core"]["membership"]["typed_rows"]; inventory = preflight["inventory"]["typed_rows"]
    rows = []
    for number, split in enumerate((*aq.SPLITS, "total"), 1):
        members = membership if split == "total" else [row for row in membership if row["assigned_split"] == split]; artifacts = inventory if split == "total" else [row for row in inventory if row["assigned_split"] == split]
        rows.append({"split_summary_id": f"COVAPIE_FINAL_SPLIT_SUMMARY_{number:06d}", "split_name": split, "split_rank": aq.RANK.get(split, -1), "sample_count": len(members), "leakage_group_count": len({row["final_leakage_group_id"] for row in members}), "canonical_schema_field_count": len(preflight["schema"]["typed_rows"]), "artifact_reference_count": len(artifacts), "statistical_representativeness_claimed": False})
    return rows


@dataclass
class DiskSplitSummaryValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_rows: list[dict[str, Any]]
    row_count_passed: bool; schema_passed: bool; order_passed: bool; sample_counts_passed: bool; group_counts_passed: bool; artifact_counts_passed: bool; source_preservation_passed: bool; group_integrity_passed: bool; in_memory_consistency_passed: bool


def build_disk_split_summary_checks_passed_evidence(candidate_rows: list[dict[str, Any]], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, preflight: dict[str, Any]) -> DiskSplitSummaryValidationResult:
    blockers: list[str] = []; rows: list[dict[str, Any]] = []; expected = build_candidate_disk_split_summary_rows(source_validation, core_disk_result, reference_audit_result, preflight); membership = preflight["core"]["membership"]["typed_rows"]; inventory = preflight["inventory"]["typed_rows"]; preservation = _multi(preflight["preservation"]["typed_rows"], "sample_index_row_id"); groups = _multi(source_validation.typed_group_rows, "final_leakage_group_id")
    if len(candidate_rows) != 4: blockers.append("disk_split_summary_row_count_mismatch")
    flags = {name: True for name in ("schema", "order", "sample", "group", "artifact", "source", "integrity", "memory")}
    for number, candidate in enumerate(candidate_rows, 1):
        split = candidate.get("split_name", f"row{number}"); local: list[str] = []; expected_row = expected[number - 1] if number <= 4 else {}
        schema_ok = list(candidate) == list(FINAL_DATASET_SPLIT_SUMMARY_CANDIDATE_FIELDS)
        if not schema_ok: local.append(f"disk_split_summary_candidate_schema_mismatch:{number}")
        if candidate.get("split_summary_id") != f"COVAPIE_FINAL_SPLIT_SUMMARY_{number:06d}" or split != (*aq.SPLITS, "total")[number - 1] or candidate.get("split_rank") != aq.RANK.get(split, -1): local.append(f"disk_split_summary_id_or_order_mismatch:{number}")
        for field, prefix in (("sample_count", "sample_count"), ("leakage_group_count", "group_count"), ("canonical_schema_field_count", "schema_count"), ("artifact_reference_count", "artifact_count")):
            if candidate.get(field) != expected_row.get(field): local.append(f"disk_split_summary_{prefix}_mismatch:{split}")
        relevant = membership if split == "total" else [row for row in membership if row["assigned_split"] == split]; ids = {row["sample_index_row_id"] for row in relevant}; expected_ids = set(EXPECTED_SAMPLE_INDEX_ROW_IDS) if split == "total" else {row["sample_index_row_id"] for row in source_validation.typed_sample_rows if row["assigned_split"] == split}
        source_ok = ids == expected_ids and all(len(preservation.get(sample, [])) == 1 and all(preservation[sample][0].get(name) is True for name in ("source_split_row_found", "source_sample_assignment_row_found", "final_dataset_csv_row_found", "final_dataset_json_row_found", "all_33_fields_preserved", "split_membership_preserved", "source_preservation_passed")) and preservation[sample][0].get("assigned_split") == (split if split != "total" else preservation[sample][0].get("assigned_split")) for sample in ids)
        expected_group_rows = source_validation.typed_group_rows if split == "total" else [row for row in source_validation.typed_group_rows if row["assigned_split"] == split]
        expected_group_ids = {row["final_leakage_group_id"] for row in expected_group_rows}; disk_by_group = _multi(relevant, "final_leakage_group_id")
        group_ok = set(disk_by_group) == expected_group_ids
        for group_id in expected_group_ids:
            source_group = [row for row in source_validation.typed_group_rows if row["final_leakage_group_id"] == group_id]
            if len(source_group) == 0: local.append(f"disk_split_summary_group_source_missing:{group_id}"); group_ok = False; continue
            if len(source_group) > 1: local.append(f"disk_split_summary_group_source_duplicate:{group_id}"); group_ok = False; continue
            source_group = source_group[0]; disk_members = disk_by_group.get(group_id, []); expected_members = set(str(source_group.get("member_sample_index_row_ids", "")).split(";"))
            if {row["sample_index_row_id"] for row in disk_members} != expected_members: local.append(f"disk_split_summary_group_member_set_mismatch:{group_id}"); group_ok = False
            if len(disk_members) != source_group.get("member_count") or any(row.get("final_leakage_group_member_count") != source_group.get("member_count") for row in disk_members): local.append(f"disk_split_summary_group_member_count_mismatch:{group_id}"); group_ok = False
            if source_group.get("assigned_split") != (split if split != "total" else source_group.get("assigned_split")) or any(row.get("assigned_split") != source_group.get("assigned_split") for row in disk_members): local.append(f"disk_split_summary_group_split_mismatch:{group_id}"); group_ok = False
            if any(row.get("group_membership_consistent") is not True or row.get("final_dataset_membership_passed") is not True for row in disk_members): group_ok = False
        if any(len({row["assigned_split"] for row in rows}) > 1 for rows in _multi(membership, "final_leakage_group_id").values()):
            for group_id, group_rows in _multi(membership, "final_leakage_group_id").items():
                if len({row["assigned_split"] for row in group_rows}) > 1: local.append(f"disk_split_summary_group_cross_split:{group_id}"); group_ok = False
        if not source_ok: local.append(f"disk_split_summary_source_preservation_failed:{split}")
        if not group_ok: local.append(f"disk_split_summary_group_integrity_failed:{split}")
        if candidate.get("statistical_representativeness_claimed") is not False: local.append(f"disk_split_summary_statistical_claim_mismatch:{split}")
        passed = schema_ok and not local; evidence = {"source_rows_preserved": source_ok, "group_integrity_preserved": group_ok, "split_summary_passed": passed, "blocking_reasons": ";".join(local)}
        rows.append({field: evidence[field] if field in evidence else candidate.get(field) for field in FINAL_DATASET_SPLIT_SUMMARY_FIELDS}); blockers.extend(local)
        flags["schema"] &= schema_ok; flags["order"] &= not any("id_or_order" in item for item in local); flags["sample"] &= not any("sample_count" in item for item in local); flags["group"] &= not any("group_count" in item for item in local); flags["artifact"] &= not any("artifact_count" in item for item in local); flags["source"] &= source_ok; flags["integrity"] &= group_ok
    memory_ok = rows == (in_memory_result.split_summary_validation.validated_rows if in_memory_result.split_summary_validation else [])
    if not memory_ok: blockers.append("disk_summary_in_memory_mismatch")
    blockers = sorted(set(blockers)); return DiskSplitSummaryValidationResult(not blockers, blockers, rows, len(candidate_rows) == 4, flags["schema"], flags["order"], flags["sample"], flags["group"], flags["artifact"], flags["source"], flags["integrity"], memory_ok)


def validate_written_split_summary_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"split_summary_write_validation_passed": False, "split_summary_row_count": 0, "split_summary_passed_count": 0, "typed_rows": [], "blocking_reasons": ["split_summary_csv_unreadable"]}
    if header != list(FINAL_DATASET_SPLIT_SUMMARY_FIELDS): blockers.append("split_summary_csv_schema_mismatch")
    if len(disk_rows) != 4: blockers.append("split_summary_csv_row_count_mismatch")
    int_fields = ("split_rank", "sample_count", "leakage_group_count", "canonical_schema_field_count", "artifact_reference_count")
    bool_fields = ("source_rows_preserved", "group_integrity_preserved", "statistical_representativeness_claimed", "split_summary_passed")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field in int_fields:
            try: typed[field] = parse_strict_int(row.get(field))
            except ValueError: blockers.append(f"split_summary_csv_type_invalid:{number}:{field}")
        for field in bool_fields:
            try: typed[field] = parse_strict_bool(row.get(field))
            except ValueError: blockers.append(f"split_summary_csv_type_invalid:{number}:{field}")
        expected = expected_rows[number - 1] if number <= len(expected_rows) else {}; split = typed.get("split_name", f"row{number}")
        if typed.get("split_summary_id") != f"COVAPIE_FINAL_SPLIT_SUMMARY_{number:06d}" or split != (*aq.SPLITS, "total")[number - 1]: blockers.append("split_summary_csv_order_mismatch")
        for name in FINAL_DATASET_SPLIT_SUMMARY_FIELDS:
            if typed.get(name) != expected.get(name): blockers.append(f"split_summary_csv_content_mismatch:{split}:{name}")
        if typed.get("source_rows_preserved") is not True or typed.get("group_integrity_preserved") is not True or typed.get("statistical_representativeness_claimed") is not False or typed.get("split_summary_passed") is not True or typed.get("blocking_reasons") != "": blockers.append(f"split_summary_csv_pass_mismatch:{split}")
        typed_rows.append(typed)
    return {"split_summary_write_validation_passed": not blockers, "split_summary_row_count": len(disk_rows), "split_summary_passed_count": sum(row.get("split_summary_passed") is True for row in typed_rows), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def build_disk_integrity_observations(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, disk_summary: DiskSplitSummaryValidationResult, *, repo_root: Path = REPO, output_boundary_validation: dict[str, Any] | None = None) -> dict[str, str]:
    core = _r3a_preflight(core_disk_result, DiskWriteActivity()); inventory = reference_audit_result.artifact_inventory_write_validation["typed_rows"]; summary = disk_summary.validated_rows; membership = core["membership"]["typed_rows"]; schema = reference_audit_result.schema_audit_write_validation["typed_rows"]; preservation = reference_audit_result.source_preservation_write_validation["typed_rows"]
    counts = {row["split_name"]: row for row in summary}; root = repo_root.resolve(); derived = (root / "data/derived/covalent_small").resolve(); raw = (root / "data/raw").resolve()
    def path_safe(row):
        value = row.get("artifact_path", ""); path = Path(value) if isinstance(value, str) else Path("")
        if not value or path.is_absolute() or ".." in path.parts: return False
        resolved = (root / path).resolve()
        try: resolved.relative_to(root); resolved.relative_to(derived)
        except ValueError: return False
        try: resolved.relative_to(raw); return False
        except ValueError: return True
    by_sample = _multi(inventory, "sample_index_row_id"); roles_ok = len(by_sample) == 11 and all(len(rows) == 6 and {r["source_field_name"] for r in rows} == set(ARTIFACT_PATH_FIELDS) and all(r["artifact_role"] == ARTIFACT_ROLE_BY_FIELD.get(r["source_field_name"]) for r in rows) for rows in by_sample.values())
    claim = "invalid" if len(summary) != 4 or any(not isinstance(row.get("statistical_representativeness_claimed"), bool) for row in summary) else ("true" if any(row["statistical_representativeness_claimed"] for row in summary) else "false")
    policy = source_validation.manifest.get("production_split_policy_finalized"); boundary_ok = (output_boundary_validation or {}).get("metadata_output_boundary_passed") is True; training = source_validation.source_checks.get("training_boundary_preserved") is True and all(row.get("ready_for_training_current_step") is False and row.get("feature_semantics_audit_required_before_training") is True and row.get("leakage_split_design_required_before_training") is True for row in core["csv"]["typed_rows"]) and all(row.get("ready_for_training_current_step") is False and row.get("feature_semantics_audit_required_before_training") is True for row in membership) and boundary_ok
    expected_order = list(EXPECTED_SAMPLE_INDEX_ROW_IDS); canonical_order = [r.get("sample_index_row_id") for r in core["csv"]["typed_rows"]] == expected_order and [r.get("sample_index_row_id") for r in core["json"]["typed_rows"]] == expected_order and [r.get("sample_index_row_id") for r in membership] == expected_order and [r.get("sample_index_row_id") for r in preservation] == expected_order
    return {"source_step14aq_preconditions_passed": _bool_text(source_validation.source_validation_passed and core["precondition"]["source_precondition_passed_count"] == 23), "final_dataset_index_row_count": "11" if core["csv"]["row_count"] == core["json"]["row_count"] == 11 else "inconsistent", "final_dataset_index_schema_field_count": "33" if core["csv"]["schema_field_count"] == core["json"]["schema_field_count"] == 33 and len(schema) == 33 and all(r.get("schema_validation_passed") is True for r in schema) else "inconsistent", "canonical_sample_order_preserved": _bool_text(canonical_order), "canonical_source_values_preserved": _bool_text(all(r.get("source_field_preservation_passed") is True for r in schema) and all(r.get("all_33_fields_preserved") is True for r in preservation)), "membership_row_count": str(len(membership)), "membership_passed_count": str(sum(r.get("final_dataset_membership_passed") is True for r in membership)), "train_sample_count": str(counts.get("train", {}).get("sample_count", -1)), "validation_sample_count": str(counts.get("validation", {}).get("sample_count", -1)), "test_sample_count": str(counts.get("test", {}).get("sample_count", -1)), "train_group_count": str(counts.get("train", {}).get("leakage_group_count", -1)), "validation_group_count": str(counts.get("validation", {}).get("leakage_group_count", -1)), "test_group_count": str(counts.get("test", {}).get("leakage_group_count", -1)), "artifact_inventory_row_count": str(len(inventory)), "artifact_roles_per_sample": "6" if roles_ok else "inconsistent", "artifact_paths_all_relative": _bool_text(all(isinstance(r.get("artifact_path"), str) and r["artifact_path"] and not Path(r["artifact_path"]).is_absolute() for r in inventory)), "artifact_paths_all_inside_repo": _bool_text(all(path_safe(r) for r in inventory)), "artifact_paths_all_exist": _bool_text(all(r.get("artifact_path_exists") is True for r in inventory)), "artifact_files_all_regular": _bool_text(all(r.get("artifact_is_regular_file") is True for r in inventory)), "artifact_hashes_all_present": _bool_text(all(re.fullmatch(r"[0-9a-f]{64}", str(r.get("artifact_sha256", ""))) for r in inventory)), "no_raw_references": _bool_text(all(path_safe(r) for r in inventory) and in_memory_result.artifact_inventory_validation.no_raw_references), "training_boundary_preserved": _bool_text(training), "statistical_representativeness_claimed": claim, "production_split_policy_finalized": _bool_text(policy) if isinstance(policy, bool) else "invalid"}


def validate_written_integrity_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"integrity_write_validation_passed": False, "integrity_row_count": 0, "integrity_passed_count": 0, "integrity_schema_passed": False, "typed_rows": [], "blocking_reasons": ["integrity_csv_unreadable"]}
    if header != list(FINAL_DATASET_INTEGRITY_AUDIT_FIELDS): blockers.append("integrity_csv_schema_mismatch")
    if len(disk_rows) != 24: blockers.append("integrity_csv_row_count_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        try: typed["integrity_check_passed"] = parse_strict_bool(row.get("integrity_check_passed"))
        except ValueError: blockers.append(f"integrity_csv_type_invalid:{number}:integrity_check_passed")
        typed_rows.append(typed)
    if typed_rows != expected_rows: blockers.append("integrity_csv_content_mismatch")
    validation = validate_integrity_checks_passed(typed_rows); blockers.extend(validation["blocking_reasons"])
    return {"integrity_write_validation_passed": not blockers, "integrity_row_count": len(disk_rows), "integrity_passed_count": validation["integrity_passed_count"], "integrity_schema_passed": validation.get("integrity_schema_passed", False), "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


@dataclass
class SummaryIntegrityDiskMaterializationResult:
    passed: bool; blocking_reasons: list[str]; output_paths: Step14AROutputPaths; split_summary_rows: list[dict[str, Any]]; split_summary_validation: DiskSplitSummaryValidationResult | None; split_summary_write_validation: dict[str, Any]; disk_integrity_observations: dict[str, str]; integrity_rows: list[dict[str, Any]]; integrity_validation: dict[str, Any]; integrity_write_validation: dict[str, Any]; preflight_existing_outputs: dict[str, Any]; activity: DiskWriteActivity; ready_for_issue_safety_manifest_materialization: bool
    ready_for_covapie_final_dataset_qa_gate: bool = False; ready_for_training: bool = False; ready_to_train_now: bool = False
    @property
    def summary_integrity_disk_materialization_passed(self) -> bool: return self.passed and not self.blocking_reasons


def materialize_summary_and_integrity_to_disk(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, *, output_paths: Step14AROutputPaths = DEFAULT_STEP14AR_OUTPUT_PATHS, repo_root: Path = REPO) -> SummaryIntegrityDiskMaterializationResult:
    activity = DiskWriteActivity(); paths = validate_step14ar_output_paths(output_paths, repo_root=repo_root)
    if not paths["output_path_contract_passed"]:
        return SummaryIntegrityDiskMaterializationResult(False, paths["blocking_reasons"], output_paths, [], None, _validation_failure("split_summary_write_validation_passed", paths["blocking_reasons"]), {}, [], _validation_failure("integrity_checks_passed", paths["blocking_reasons"]), _validation_failure("integrity_write_validation_passed", paths["blocking_reasons"]), {"preflight_existing_outputs_passed": False, "blocking_reasons": paths["blocking_reasons"]}, activity, False)
    preflight = preflight_existing_seven_outputs(source_validation, in_memory_result, core_disk_result, reference_audit_result)
    prerequisites = source_validation.source_validation_passed and in_memory_result.in_memory_materialization_passed and core_disk_result.core_disk_materialization_passed and reference_audit_result.reference_audit_disk_materialization_passed and preflight["preflight_existing_outputs_passed"]
    if not prerequisites:
        blockers = sorted(set(preflight["blocking_reasons"] + ["r3b2_prerequisite_not_passed"])); write_csv_atomic(output_paths.split_summary, [], FINAL_DATASET_SPLIT_SUMMARY_FIELDS, activity); write_csv_atomic(output_paths.integrity_audit, [], FINAL_DATASET_INTEGRITY_AUDIT_FIELDS, activity)
        return SummaryIntegrityDiskMaterializationResult(False, blockers, output_paths, [], None, _validation_failure("split_summary_write_validation_passed", blockers), {}, [], _validation_failure("integrity_checks_passed", blockers), _validation_failure("integrity_write_validation_passed", blockers), preflight, activity, False)
    candidates = build_candidate_disk_split_summary_rows(source_validation, core_disk_result, reference_audit_result, preflight); summary = build_disk_split_summary_checks_passed_evidence(candidates, source_validation, in_memory_result, core_disk_result, reference_audit_result, preflight)
    write_csv_atomic(output_paths.split_summary, summary.validated_rows, FINAL_DATASET_SPLIT_SUMMARY_FIELDS, activity); summary_write = validate_written_split_summary_checks_passed(summary.validated_rows, output_paths.split_summary, activity)
    boundary = validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root)
    observations = build_disk_integrity_observations(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary, repo_root=repo_root, output_boundary_validation=boundary); integrity_rows = build_integrity_checks_passed_evidence(observations); integrity = validate_integrity_checks_passed(integrity_rows)
    if integrity_rows != in_memory_result.integrity_rows: integrity["blocking_reasons"] = sorted(set(integrity["blocking_reasons"] + ["disk_integrity_in_memory_mismatch"]))
    write_csv_atomic(output_paths.integrity_audit, integrity_rows, FINAL_DATASET_INTEGRITY_AUDIT_FIELDS, activity); integrity_write = validate_written_integrity_checks_passed(integrity_rows, output_paths.integrity_audit, activity)
    blockers = sorted(set(summary.blocking_reasons + summary_write["blocking_reasons"] + boundary["blocking_reasons"] + integrity["blocking_reasons"] + integrity_write["blocking_reasons"])); passed = not blockers
    return SummaryIntegrityDiskMaterializationResult(passed, blockers, output_paths, summary.validated_rows, summary, summary_write, observations, integrity_rows, integrity, integrity_write, preflight, activity, passed)


EXISTING_NINE_LOGICAL_NAMES = (*CORE_OUTPUT_LOGICAL_NAMES, *R3B1_OUTPUT_LOGICAL_NAMES, *R3B2_OUTPUT_LOGICAL_NAMES)
EXISTING_ELEVEN_LOGICAL_NAMES = (*EXISTING_NINE_LOGICAL_NAMES, *R4A_OUTPUT_LOGICAL_NAMES)


def validate_declared_output_file_nodes(logical_names: tuple[str, ...], output_paths: Step14AROutputPaths, *, repo_root: Path) -> dict[str, Any]:
    blockers: list[str] = []; regular_count = symlink_count = missing_count = 0; root = repo_root.resolve(); final_root = (root / FINAL_ROOT).resolve(); expected_names = {name: filename for name, filename, *_ in OUTPUT_SPECS}
    for logical_name in logical_names:
        path = Path(getattr(output_paths, logical_name)); absolute = path if path.is_absolute() else root / path
        if absolute.name != expected_names.get(logical_name): blockers.append(f"declared_output_filename_mismatch:{logical_name}")
        if ".." in path.parts: blockers.append(f"declared_output_outside_final_root:{logical_name}")
        try: absolute.parent.resolve().relative_to(final_root)
        except ValueError: blockers.append(f"declared_output_outside_final_root:{logical_name}")
        try: node = absolute.lstat()
        except FileNotFoundError: blockers.append(f"declared_output_missing:{logical_name}"); missing_count += 1; continue
        if stat.S_ISLNK(node.st_mode): blockers.append(f"declared_output_symlink_forbidden:{logical_name}"); symlink_count += 1; continue
        if not stat.S_ISREG(node.st_mode): blockers.append(f"declared_output_not_regular_file:{logical_name}"); continue
        regular_count += 1
    blockers = sorted(set(blockers)); return {"declared_output_nodes_passed": not blockers, "expected_node_count": len(logical_names), "regular_file_count": regular_count, "symlink_count": symlink_count, "missing_count": missing_count, "blocking_reasons": blockers}


def preflight_existing_nine_outputs(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, *, repo_root: Path) -> dict[str, Any]:
    nodes = validate_declared_output_file_nodes(EXISTING_NINE_LOGICAL_NAMES, summary_integrity_result.output_paths, repo_root=repo_root)
    if not nodes["declared_output_nodes_passed"]:
        return {"preflight_existing_nine_outputs_passed": False, "preflight_output_count": 0, "declared_output_nodes_passed": False, "core_preflight_passed": False, "reference_preflight_passed": False, "summary_preflight_passed": False, "integrity_preflight_passed": False, "read_paths": set(), "node_validation": nodes, "blocking_reasons": nodes["blocking_reasons"]}
    seven = preflight_existing_seven_outputs(source_validation, in_memory_result, core_disk_result, reference_audit_result); activity = DiskWriteActivity()
    summary = validate_written_split_summary_checks_passed(summary_integrity_result.split_summary_rows, summary_integrity_result.output_paths.split_summary, activity); integrity = validate_written_integrity_checks_passed(summary_integrity_result.integrity_rows, summary_integrity_result.output_paths.integrity_audit, activity)
    read_paths = set(seven["read_paths"]) | activity.read_paths; passed = seven["preflight_existing_outputs_passed"] and summary["split_summary_write_validation_passed"] and integrity["integrity_write_validation_passed"] and len(read_paths) == 9
    blockers = sorted(set(seven["blocking_reasons"] + summary["blocking_reasons"] + integrity["blocking_reasons"] + ([] if len(read_paths) == 9 else ["nine_output_preflight_read_count_mismatch"])))
    return {"preflight_existing_nine_outputs_passed": passed, "preflight_output_count": len(read_paths), "declared_output_nodes_passed": True, "core_preflight_passed": seven["core_preflight_passed"], "reference_preflight_passed": seven["artifact_inventory_preflight_passed"] and seven["schema_audit_preflight_passed"] and seven["source_preservation_preflight_passed"], "summary_preflight_passed": summary["split_summary_write_validation_passed"], "integrity_preflight_passed": integrity["integrity_write_validation_passed"], "read_paths": read_paths, "node_validation": nodes, "seven": seven, "summary": summary, "integrity": integrity, "blocking_reasons": blockers}


@dataclass(frozen=True)
class ArtifactDiskPathBoundaryResult:
    all_relative_and_traversal_free: bool; all_inside_repo: bool; all_inside_allowed_derived_root: bool; all_outside_raw_root: bool; blocking_reasons: list[str]


def _artifact_disk_path_contract(rows: list[dict[str, Any]], repo_root: Path) -> ArtifactDiskPathBoundaryResult:
    root = Path(os.path.abspath(repo_root)); derived = root / "data/derived/covalent_small"; raw = root / "data/raw"; relative_ok = inside_repo_ok = derived_ok = outside_raw = True; blockers: list[str] = []
    for row in rows:
        sample, field = row.get("sample_index_row_id", ""), row.get("source_field_name", ""); value = row.get("artifact_path", ""); path = Path(value) if isinstance(value, str) else Path("")
        relative = bool(value) and not path.is_absolute() and ".." not in path.parts; relative_ok &= relative
        if not relative: inside_repo_ok = derived_ok = outside_raw = False; blockers.append(f"artifact_disk_path_relative_invalid:{sample}:{field}"); continue
        # Lexical normalization keeps this evidence path-only: no exists/stat/open/hash.
        resolved = Path(os.path.abspath(root / path))
        try: resolved.relative_to(root); inside_repo = True
        except ValueError: inside_repo = False
        try: resolved.relative_to(derived); inside_derived = inside_repo
        except ValueError: inside_derived = False
        try: resolved.relative_to(raw); raw_free = False
        except ValueError: raw_free = True
        inside_repo_ok &= inside_repo; derived_ok &= inside_derived; outside_raw &= raw_free
        if not inside_repo: blockers.append(f"artifact_disk_path_outside_repo:{sample}:{field}")
        if not inside_derived: blockers.append(f"artifact_disk_path_not_allowed_derived:{sample}:{field}")
        if not raw_free: blockers.append(f"artifact_disk_path_raw_forbidden:{sample}:{field}")
    return ArtifactDiskPathBoundaryResult(relative_ok, inside_repo_ok, derived_ok, outside_raw, sorted(set(blockers)))


@dataclass(frozen=True)
class R4APlannedWriteValidation:
    passed: bool; planned_write_paths: tuple[str, ...]; exact_r4a_output_set: bool; all_inside_final_root: bool; all_outside_raw_root: bool; disjoint_from_referenced_artifacts: bool; no_tensor_write_paths: bool; no_dataloader_write_paths: bool; no_training_write_paths: bool; blocking_reasons: list[str]


def validate_r4a_planned_writes(output_paths: Step14AROutputPaths, artifact_inventory_rows: list[dict[str, Any]], *, repo_root: Path) -> R4APlannedWriteValidation:
    root = repo_root.resolve(); final_root = (root / FINAL_ROOT).resolve(); raw_root = (root / "data/raw").resolve(); planned = tuple((Path(getattr(output_paths, name)) if Path(getattr(output_paths, name)).is_absolute() else root / Path(getattr(output_paths, name))).resolve() for name in R4A_OUTPUT_LOGICAL_NAMES); expected = tuple((final_root / next(filename for logical, filename, *_ in OUTPUT_SPECS if logical == name)).resolve() for name in R4A_OUTPUT_LOGICAL_NAMES); blockers: list[str] = []
    exact = len(planned) == 2 and planned == expected
    if not exact: blockers.append("r4a_planned_write_set_mismatch")
    inside = raw_free = True
    artifact_targets = {(root / Path(row.get("artifact_path", ""))).resolve() for row in artifact_inventory_rows if isinstance(row.get("artifact_path"), str) and row.get("artifact_path")}
    disjoint = True; forbidden_ok = dataloader_ok = training_ok = True; forbidden_suffixes = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".npy")
    for path in planned:
        try: path.relative_to(final_root)
        except ValueError: inside = False; blockers.append(f"r4a_planned_write_outside_final_root:{path.name}")
        try: path.relative_to(raw_root); raw_free = False; blockers.append(f"r4a_planned_raw_write:{path.name}")
        except ValueError: pass
        if path in artifact_targets: disjoint = False; blockers.append(f"r4a_planned_artifact_overwrite:{path.name}")
        lowered = path.name.lower()
        if path.name.endswith(forbidden_suffixes) or any(token in lowered for token in ("tensor", "checkpoint", "optimizer")): forbidden_ok = False; blockers.append(f"r4a_planned_forbidden_write:{path.name}")
        if "dataloader" in lowered: dataloader_ok = False; blockers.append(f"r4a_planned_forbidden_write:{path.name}")
        if "training" in lowered: training_ok = False; blockers.append(f"r4a_planned_forbidden_write:{path.name}")
    blockers = sorted(set(blockers)); return R4APlannedWriteValidation(not blockers, tuple(str(path) for path in planned), exact, inside, raw_free, disjoint, forbidden_ok, dataloader_ok, training_ok, blockers)


def build_final_safety_observations(contract_validation: dict[str, Any], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, nine_output_preflight: dict[str, Any], metadata_boundary: dict[str, Any], planned_write_validation: R4APlannedWriteValidation, *, repo_root: Path) -> dict[str, bool]:
    pre = nine_output_preflight.get("seven", {}); core = pre.get("core", {}); inventory_validation = pre.get("inventory", reference_audit_result.artifact_inventory_write_validation); inventory = inventory_validation.get("typed_rows", []); schema = pre.get("schema", reference_audit_result.schema_audit_write_validation).get("typed_rows", []); preservation = pre.get("preservation", reference_audit_result.source_preservation_write_validation).get("typed_rows", []); summary = nine_output_preflight.get("summary", summary_integrity_result.split_summary_write_validation).get("typed_rows", []); integrity = nine_output_preflight.get("integrity", summary_integrity_result.integrity_write_validation).get("typed_rows", [])
    path_boundary = _artifact_disk_path_contract(inventory, repo_root); count_rows = {row.get("split_name"): row for row in summary}; node = nine_output_preflight.get("node_validation", {}); boundary_blockers = metadata_boundary.get("blocking_reasons", []); root = repo_root.resolve(); raw_root = (root / "data/raw").resolve()
    canonical_order = next((row.get("observed_value") == "true" for row in integrity if row.get("integrity_audit_item") == "canonical_sample_order_preserved"), False); source_values = all(row.get("source_field_preservation_passed") is True for row in schema) and all(row.get("all_33_fields_preserved") is True for row in preservation)
    summary_counts = lambda field, expected: [count_rows.get(split, {}).get(field) for split in (*aq.SPLITS, "total")] == expected
    actual_mask_pairs = tuple(zip(CANONICAL_MASK_TASK_NAMES, CANONICAL_MASK_TASK_ALIASES)); preflight_paths = nine_output_preflight.get("read_paths", set())
    def outside_raw(path_text: str) -> bool:
        try: Path(path_text).resolve().relative_to(raw_root); return False
        except ValueError: return True
    no_raw_reads = in_memory_result.artifact_inventory_validation is not None and in_memory_result.artifact_inventory_validation.activity.raw_read_attempted is False and len(preflight_paths) == 9 and all(outside_raw(path) for path in preflight_paths) and node.get("declared_output_nodes_passed") is True
    disk_index_rows = core.get("csv", core_disk_result.final_index_csv_write_validation).get("typed_rows", []); disk_membership_rows = core.get("membership", core_disk_result.membership_write_validation).get("typed_rows", [])
    observed_ready_for_training = any((source_validation.manifest.get("ready_for_training") is True, in_memory_result.ready_for_training is True, core_disk_result.ready_for_training is True, reference_audit_result.ready_for_training is True, summary_integrity_result.ready_for_training is True, any(row.get("ready_for_training_current_step") is True for row in disk_index_rows), any(row.get("ready_for_training_current_step") is True for row in disk_membership_rows)))
    observed_ready_to_train_now = any((source_validation.manifest.get("ready_to_train_now") is True, in_memory_result.ready_to_train_now is True, core_disk_result.ready_to_train_now is True, reference_audit_result.ready_to_train_now is True, summary_integrity_result.ready_to_train_now is True))
    return {
        "contract_snapshot_passed": contract_validation.get("contract_validation_passed") is True,
        "step14aq_source_validation_passed": source_validation.source_validation_passed,
        "source_commit_provenance_passed": source_validation.source_checks.get("commit_provenance_passed") is True,
        "core_disk_materialization_passed": core_disk_result.core_disk_materialization_passed,
        "reference_audit_disk_materialization_passed": reference_audit_result.reference_audit_disk_materialization_passed,
        "summary_integrity_disk_materialization_passed": summary_integrity_result.summary_integrity_disk_materialization_passed,
        "existing_nine_output_preflight_passed": nine_output_preflight.get("preflight_existing_nine_outputs_passed") is True,
        "output_path_contract_passed": core_disk_result.output_path_validation.get("output_path_contract_passed") is True,
        "final_precondition_audit_23_of_23": core.get("precondition", core_disk_result.precondition_write_validation).get("source_precondition_passed_count") == 23,
        "final_index_csv_11_by_33": core.get("csv", core_disk_result.final_index_csv_write_validation).get("row_count") == 11 and core.get("csv", core_disk_result.final_index_csv_write_validation).get("schema_field_count") == 33,
        "final_index_json_11_by_33": core.get("json", core_disk_result.final_index_json_write_validation).get("row_count") == 11 and core.get("json", core_disk_result.final_index_json_write_validation).get("schema_field_count") == 33,
        "final_index_csv_json_consistent": core.get("cross", core_disk_result.final_index_cross_format_validation).get("final_index_csv_json_consistent") is True,
        "membership_11_of_11": core.get("membership", core_disk_result.membership_write_validation).get("membership_passed_count") == 11,
        "artifact_inventory_66_of_66": inventory_validation.get("artifact_inventory_passed_count") == 66,
        "schema_audit_33_of_33": len(schema) == 33 and all(row.get("schema_validation_passed") is True for row in schema),
        "source_preservation_11_of_11": len(preservation) == 11 and all(row.get("source_preservation_passed") is True for row in preservation),
        "split_summary_4_of_4": len(summary) == 4 and all(row.get("split_summary_passed") is True for row in summary),
        "integrity_audit_24_of_24": len(integrity) == 24 and all(row.get("integrity_check_passed") is True for row in integrity),
        "canonical_sample_order_preserved": canonical_order,
        "canonical_source_values_preserved": source_values,
        "exact_group_member_sets_preserved": summary_integrity_result.split_summary_validation is not None and summary_integrity_result.split_summary_validation.group_integrity_passed,
        "split_sample_counts_preserved": summary_counts("sample_count", [8, 2, 1, 11]),
        "split_group_counts_preserved": summary_counts("leakage_group_count", [2, 2, 1, 5]),
        "split_artifact_counts_preserved": summary_counts("artifact_reference_count", [48, 12, 6, 66]),
        "artifact_paths_all_relative": path_boundary.all_relative_and_traversal_free,
        "artifact_paths_all_inside_repo": path_boundary.all_inside_repo,
        "artifact_paths_all_inside_allowed_derived_root": path_boundary.all_inside_allowed_derived_root,
        "artifact_paths_all_outside_raw_root": path_boundary.all_outside_raw_root,
        "artifact_files_all_exist": len(inventory) == 66 and all(row.get("artifact_path_exists") is True for row in inventory),
        "artifact_files_all_regular": len(inventory) == 66 and all(row.get("artifact_is_regular_file") is True for row in inventory),
        "artifact_sizes_all_positive": len(inventory) == 66 and all(row.get("artifact_size_bytes", 0) > 0 for row in inventory),
        "artifact_hashes_all_present": len(inventory) == 66 and all(re.fullmatch(r"[0-9a-f]{64}", str(row.get("artifact_sha256", ""))) for row in inventory),
        "artifact_references_all_preserved": len(inventory) == 66 and all(row.get("artifact_reference_preserved") is True and row.get("artifact_inventory_passed") is True for row in inventory),
        "metadata_output_boundary_passed": metadata_boundary.get("metadata_output_boundary_passed") is True,
        "no_unknown_outputs": metadata_boundary.get("unknown_output_count") == 0,
        "no_unexpected_output_directories": not any(item.startswith("step14ar_unexpected_directory") for item in boundary_blockers),
        "no_output_symlinks": node.get("symlink_count") == 0,
        "no_forbidden_artifacts": metadata_boundary.get("forbidden_artifact_count") == 0,
        "no_temporary_artifacts": metadata_boundary.get("temporary_artifact_count") == 0,
        "no_raw_reads": no_raw_reads,
        "no_raw_writes": planned_write_validation.all_outside_raw_root,
        "no_artifact_copying": planned_write_validation.exact_r4a_output_set and planned_write_validation.disjoint_from_referenced_artifacts,
        "no_tensor_outputs": planned_write_validation.no_tensor_write_paths and metadata_boundary.get("forbidden_artifact_count") == 0,
        "no_dataloader_outputs": planned_write_validation.no_dataloader_write_paths and not any("dataloader" in item.lower() for item in boundary_blockers),
        "no_training_outputs": planned_write_validation.no_training_write_paths and not any("training" in item.lower() for item in boundary_blockers),
        "canonical_mask_count_is_five": len(actual_mask_pairs) == 5,
        "scaffold_only_b3_present": ("scaffold_only", "B3") in actual_mask_pairs,
        "no_extra_mask_tasks_added": actual_mask_pairs == EXPECTED_CANONICAL_MASK_PAIRS,
        "feature_semantics_known_for_training": source_validation.manifest.get("feature_semantics_known_for_training") is True,
        "unknown_atom_feature_policy_finalized_for_training": source_validation.manifest.get("unknown_atom_feature_policy_finalized_for_training") is True,
        "feature_semantics_audit_required_before_training": source_validation.manifest.get("feature_semantics_audit_required_before_training") is True,
        "statistical_representativeness_claimed": any(row.get("statistical_representativeness_claimed") is True for row in summary),
        "production_split_policy_finalized": source_validation.manifest.get("production_split_policy_finalized") is True,
        "ready_for_training": observed_ready_for_training,
        "ready_to_train_now": observed_ready_to_train_now,
    }


def build_final_safety_rows(observations: dict[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for item, required in FINAL_SAFETY_EXPECTED:
        observed = observations.get(item); passed = type(observed) is bool and observed is required
        rows.append({"safety_item": item, "required_status": required, "observed_status": observed, "safety_passed": passed, "blocking_reasons": "" if passed else f"final_safety_mismatch:{item}:required={str(required).lower()}:observed={str(observed).lower()}"})
    return rows


@dataclass
class FinalSafetyValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_rows: list[dict[str, Any]]; row_count_passed: bool; schema_passed: bool; item_order_passed: bool; expected_contract_passed: bool; observation_contract_passed: bool; passed_count: int


def build_safety_checks_passed_evidence(rows: list[dict[str, Any]]) -> FinalSafetyValidationResult:
    blockers: list[str] = []; expected = dict(FINAL_SAFETY_EXPECTED); items = [row.get("safety_item") for row in rows]; schema_ok = True; expected_ok = observation_ok = True; passed_count = 0
    if len(rows) != 55: blockers.append("final_safety_row_count_mismatch")
    order_ok = items == [item for item, _ in FINAL_SAFETY_EXPECTED] and len(items) == len(set(items))
    if not order_ok: blockers.append("final_safety_item_contract_mismatch")
    for number, row in enumerate(rows, 1):
        item = row.get("safety_item", f"row{number}"); required = expected.get(item)
        if list(row) != list(FINAL_DATASET_SAFETY_FIELDS): blockers.append(f"final_safety_schema_mismatch:{number}"); schema_ok = False
        if type(row.get("required_status")) is not bool or row.get("required_status") is not required: blockers.append(f"final_safety_required_mismatch:{item}"); expected_ok = False
        observed = row.get("observed_status"); recomputed = type(observed) is bool and observed is required
        if type(observed) is not bool: blockers.append(f"final_safety_observation_invalid:{item}"); observation_ok = False
        if type(row.get("safety_passed")) is not bool or row.get("safety_passed") is not recomputed: blockers.append(f"final_safety_pass_flag_mismatch:{item}")
        expected_reason = "" if recomputed else f"final_safety_mismatch:{item}:required={str(required).lower()}:observed={str(observed).lower()}"
        if row.get("blocking_reasons") != expected_reason: blockers.append(f"final_safety_blocking_reason_mismatch:{item}")
        if recomputed: passed_count += 1
        else: blockers.append(expected_reason)
    blockers = sorted(set(blockers)); return FinalSafetyValidationResult(not blockers, blockers, [{field: row.get(field) for field in FINAL_DATASET_SAFETY_FIELDS} for row in rows], len(rows) == 55, schema_ok, order_ok, expected_ok, observation_ok, passed_count)


def validate_safety_checks_passed(result: FinalSafetyValidationResult) -> dict[str, Any]:
    return {"safety_checks_passed": result.passed, "safety_row_count": len(result.validated_rows), "safety_passed_count": result.passed_count, "blocking_reasons": list(result.blocking_reasons)}


ISSUE_SENTINEL = {"issue_id": "NO_COVAPIE_FINAL_DATASET_MATERIALIZATION_ISSUES", "issue_scope": "current_11_sample_final_dataset_materialization_smoke_v0", "sample_index_row_id": "", "assigned_split": "", "issue_severity": "none", "issue_type": "no_issues", "issue_description": "no_blocking_issues_detected", "issue_status": "passed"}


def build_final_issue_inventory_rows(blockers: list[str]) -> list[dict[str, str]]:
    unique = sorted(set(blockers))
    if not unique: return [dict(ISSUE_SENTINEL)]
    rows = []
    for number, blocker in enumerate(unique, 1):
        sample = next((sample_id for sample_id in EXPECTED_SAMPLE_INDEX_ROW_IDS if sample_id in blocker), ""); split = next((split for split in aq.SPLITS if f":{split}" in blocker), "")
        rows.append({"issue_id": f"COVAPIE_FINAL_DATASET_ISSUE_{number:06d}", "issue_scope": ISSUE_SENTINEL["issue_scope"], "sample_index_row_id": sample, "assigned_split": split, "issue_severity": "blocking", "issue_type": blocker.split(":", 1)[0], "issue_description": blocker, "issue_status": "open"})
    return rows


def validate_issue_inventory_clear(rows: list[dict[str, Any]], expected_blockers: list[str]) -> dict[str, Any]:
    blockers: list[str] = []; unique = sorted(set(expected_blockers)); expected = build_final_issue_inventory_rows(unique)
    if rows != expected: blockers.append("final_issue_inventory_content_mismatch")
    clear = not unique and rows == [ISSUE_SENTINEL]
    if unique and any(row.get("issue_id") == ISSUE_SENTINEL["issue_id"] for row in rows): blockers.append("final_issue_sentinel_with_blockers")
    return {"issue_inventory_validation_passed": not blockers, "issue_inventory_clear": clear, "blocking_issue_count": 0 if clear else len(rows), "issue_row_count": len(rows), "blocking_reasons": blockers}


def validate_written_safety_checks_passed(expected_rows: list[dict[str, Any]], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []; typed_rows: list[dict[str, Any]] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"safety_write_validation_passed": False, "safety_row_count": 0, "safety_passed_count": 0, "typed_rows": [], "blocking_reasons": ["final_safety_csv_unreadable"]}
    if header != list(FINAL_DATASET_SAFETY_FIELDS): blockers.append("final_safety_csv_schema_mismatch")
    for number, row in enumerate(disk_rows, 1):
        typed = dict(row)
        for field in ("required_status", "observed_status", "safety_passed"):
            try: typed[field] = parse_strict_bool(row.get(field))
            except ValueError: blockers.append(f"final_safety_csv_type_invalid:{number}:{field}")
        typed_rows.append(typed)
    if typed_rows != expected_rows: blockers.append("final_safety_csv_content_mismatch")
    validation = build_safety_checks_passed_evidence(typed_rows); blockers.extend(validation.blocking_reasons)
    return {"safety_write_validation_passed": not blockers, "safety_row_count": len(disk_rows), "safety_passed_count": validation.passed_count, "typed_rows": typed_rows, "blocking_reasons": sorted(set(blockers))}


def validate_written_issue_inventory_clear(expected_rows: list[dict[str, str]], expected_blockers: list[str], path: Path, activity: DiskWriteActivity) -> dict[str, Any]:
    blockers: list[str] = []
    try: header, disk_rows = read_csv_with_header(path, activity)
    except (OSError, UnicodeDecodeError, csv.Error): return {"issue_write_validation_passed": False, "issue_inventory_clear": False, "blocking_issue_count": 0, "issue_row_count": 0, "typed_rows": [], "blocking_reasons": ["final_issue_csv_unreadable"]}
    if header != list(FINAL_DATASET_ISSUE_FIELDS): blockers.append("final_issue_csv_schema_mismatch")
    if disk_rows != expected_rows: blockers.append("final_issue_csv_content_mismatch")
    validation = validate_issue_inventory_clear(disk_rows, expected_blockers); blockers.extend(validation["blocking_reasons"])
    return {"issue_write_validation_passed": not blockers, "issue_inventory_clear": validation["issue_inventory_clear"], "blocking_issue_count": validation["blocking_issue_count"], "issue_row_count": len(disk_rows), "typed_rows": disk_rows, "blocking_reasons": sorted(set(blockers))}


@dataclass
class IssueSafetyDiskMaterializationResult:
    passed: bool; blocking_reasons: list[str]; output_paths: Step14AROutputPaths; safety_observations: dict[str, bool]; safety_rows: list[dict[str, Any]]; safety_validation: FinalSafetyValidationResult | None; safety_write_validation: dict[str, Any]; issue_rows: list[dict[str, str]]; issue_validation: dict[str, Any]; issue_write_validation: dict[str, Any]; preflight_existing_nine_outputs: dict[str, Any]; metadata_output_boundary_before_write: dict[str, Any]; metadata_output_boundary_after_write: dict[str, Any]; planned_write_validation: R4APlannedWriteValidation | None; after_write_node_validation: dict[str, Any]; activity: DiskWriteActivity; ready_for_manifest_materialization: bool
    ready_for_covapie_final_dataset_qa_gate: bool = False; ready_for_training: bool = False; ready_to_train_now: bool = False
    @property
    def issue_safety_disk_materialization_passed(self) -> bool: return self.passed and not self.blocking_reasons


def materialize_issue_and_safety_to_disk(contract_validation: dict[str, Any], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, *, output_paths: Step14AROutputPaths = DEFAULT_STEP14AR_OUTPUT_PATHS, repo_root: Path = REPO, allow_existing_manifest: bool = False) -> IssueSafetyDiskMaterializationResult:
    activity = DiskWriteActivity(); empty = _validation_failure
    manifest_path = Path(output_paths.manifest)
    manifest_path = manifest_path if manifest_path.is_absolute() else repo_root / manifest_path
    manifest_blockers: list[str] = []
    try: manifest_node = manifest_path.lstat()
    except FileNotFoundError: manifest_node = None
    except OSError: manifest_blockers.append("r4a_existing_manifest_lstat_failed"); manifest_node = None
    if manifest_node is not None:
        if stat.S_ISLNK(manifest_node.st_mode): manifest_blockers.append("r4a_existing_manifest_symlink_forbidden")
        elif not stat.S_ISREG(manifest_node.st_mode): manifest_blockers.append("r4a_existing_manifest_not_regular_file")
        elif not allow_existing_manifest: manifest_blockers.append("r4a_existing_manifest_not_allowed")
    if manifest_blockers:
        blockers = sorted(set(manifest_blockers))
        return IssueSafetyDiskMaterializationResult(False, blockers, output_paths, {}, [], None, empty("safety_write_validation_passed", blockers), [], {"issue_inventory_clear": False, "blocking_issue_count": 0}, empty("issue_write_validation_passed", blockers), {"preflight_existing_nine_outputs_passed": False, "blocking_reasons": blockers}, {}, {}, None, {}, activity, False)
    path_validation = validate_step14ar_output_paths(output_paths, repo_root=repo_root)
    if not path_validation["output_path_contract_passed"]:
        blockers = path_validation["blocking_reasons"]
        return IssueSafetyDiskMaterializationResult(False, blockers, output_paths, {}, [], None, empty("safety_write_validation_passed", blockers), [], {"issue_inventory_clear": False, "blocking_issue_count": 0}, empty("issue_write_validation_passed", blockers), {"preflight_existing_nine_outputs_passed": False, "blocking_reasons": blockers}, {}, {}, None, {}, activity, False)
    preflight = preflight_existing_nine_outputs(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, repo_root=repo_root); boundary_before = validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root)
    inventory_rows = preflight.get("seven", {}).get("inventory", reference_audit_result.artifact_inventory_write_validation).get("typed_rows", [])
    planned = validate_r4a_planned_writes(output_paths, inventory_rows, repo_root=repo_root)
    observations = build_final_safety_observations(contract_validation, source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, preflight, boundary_before, planned, repo_root=repo_root)
    safety_rows = build_final_safety_rows(observations); safety_validation = build_safety_checks_passed_evidence(safety_rows)
    prerequisite_blockers = [*preflight["blocking_reasons"], *boundary_before["blocking_reasons"], *planned.blocking_reasons, *safety_validation.blocking_reasons]
    issue_rows = build_final_issue_inventory_rows(prerequisite_blockers); issue_validation = validate_issue_inventory_clear(issue_rows, prerequisite_blockers)
    write_csv_atomic(output_paths.safety_audit, safety_rows, FINAL_DATASET_SAFETY_FIELDS, activity); safety_write = validate_written_safety_checks_passed(safety_rows, output_paths.safety_audit, activity)
    write_csv_atomic(output_paths.issue_inventory, issue_rows, FINAL_DATASET_ISSUE_FIELDS, activity); issue_write = validate_written_issue_inventory_clear(issue_rows, prerequisite_blockers, output_paths.issue_inventory, activity)
    boundary_after = validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root); after_nodes = validate_declared_output_file_nodes(EXISTING_ELEVEN_LOGICAL_NAMES, output_paths, repo_root=repo_root)
    blockers = sorted(set(prerequisite_blockers + safety_write["blocking_reasons"] + issue_validation["blocking_reasons"] + issue_write["blocking_reasons"] + boundary_after["blocking_reasons"] + after_nodes["blocking_reasons"])); allowed_counts = {11, 12} if allow_existing_manifest else {11}; passed = not blockers and issue_write["issue_inventory_clear"] and boundary_after["existing_output_count"] in allowed_counts and after_nodes["regular_file_count"] == 11
    return IssueSafetyDiskMaterializationResult(passed, blockers, output_paths, observations, safety_rows, safety_validation, safety_write, issue_rows, issue_validation, issue_write, preflight, boundary_before, boundary_after, planned, after_nodes, activity, passed)


ALL_TWELVE_LOGICAL_NAMES = tuple(logical_name for logical_name, *_ in OUTPUT_SPECS)
NON_MANIFEST_OUTPUT_ENTRY_FIELDS = ("logical_name", "relative_path", "format", "row_count", "sha256")
FINAL_MANIFEST_FIELDS = (
    "stage", "step_label", "project_name", "manifest_schema_version", "previous_stage",
    "source_step14aq_commit", "source_input_count", "source_input_sha256",
    "output_artifact_count", "non_manifest_output_count", "non_manifest_outputs",
    "final_dataset_index_row_count", "canonical_schema_field_count", "membership_row_count",
    "artifact_inventory_row_count", "schema_audit_row_count", "source_preservation_row_count",
    "split_summary_row_count", "integrity_audit_row_count", "safety_audit_row_count",
    "issue_inventory_row_count", "blocking_issue_count", "split_sample_counts",
    "split_group_counts", "split_artifact_counts", "canonical_mask_pairs",
    "source_step14aq_preconditions_passed", "final_dataset_index_schema_passed",
    "final_dataset_index_write_validation_passed", "membership_checks_passed",
    "membership_write_validation_passed", "artifact_inventory_checks_passed",
    "artifact_inventory_write_validation_passed", "source_preservation_checks_passed",
    "split_summary_checks_passed", "integrity_checks_passed", "safety_checks_passed",
    "issue_inventory_clear", "metadata_output_boundary_passed", "all_output_nodes_regular",
    "all_checks_passed", "ready_for_covapie_final_dataset_qa_gate", "ready_for_training",
    "ready_to_train_now", "feature_semantics_known_for_training",
    "unknown_atom_feature_policy_finalized_for_training",
    "feature_semantics_audit_required_before_training", "statistical_representativeness_claimed",
    "production_split_policy_finalized", "contains_raw_structure", "contains_tensor_data",
    "raw_read_attempted", "recommended_next_step", "blocking_reasons",
)
FINAL_MANIFEST_PASS_FIELDS = (
    "source_step14aq_preconditions_passed", "final_dataset_index_schema_passed",
    "final_dataset_index_write_validation_passed", "membership_checks_passed",
    "membership_write_validation_passed", "artifact_inventory_checks_passed",
    "artifact_inventory_write_validation_passed", "source_preservation_checks_passed",
    "split_summary_checks_passed", "integrity_checks_passed", "safety_checks_passed",
    "issue_inventory_clear", "metadata_output_boundary_passed", "all_output_nodes_regular",
)
EXPECTED_SPLIT_SAMPLE_COUNTS = {"train": 8, "validation": 2, "test": 1, "total": 11}
EXPECTED_SPLIT_GROUP_COUNTS = {"train": 2, "validation": 2, "test": 1, "total": 5}
EXPECTED_SPLIT_ARTIFACT_COUNTS = {"train": 48, "validation": 12, "test": 6, "total": 66}


def preflight_existing_eleven_outputs(contract_validation: dict[str, Any], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, issue_safety_result: IssueSafetyDiskMaterializationResult, *, repo_root: Path) -> dict[str, Any]:
    nodes = validate_declared_output_file_nodes(EXISTING_ELEVEN_LOGICAL_NAMES, issue_safety_result.output_paths, repo_root=repo_root)
    if not nodes["declared_output_nodes_passed"]:
        return {"preflight_existing_eleven_outputs_passed": False, "preflight_output_count": 0, "declared_output_nodes_passed": False, "core_preflight_passed": False, "reference_preflight_passed": False, "summary_integrity_preflight_passed": False, "safety_preflight_passed": False, "issue_preflight_passed": False, "read_paths": set(), "node_validation": nodes, "blocking_reasons": list(nodes["blocking_reasons"])}
    nine = preflight_existing_nine_outputs(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, repo_root=repo_root)
    activity = DiskWriteActivity()
    safety = validate_written_safety_checks_passed(issue_safety_result.safety_rows, issue_safety_result.output_paths.safety_audit, activity)
    issue = validate_written_issue_inventory_clear(issue_safety_result.issue_rows, [], issue_safety_result.output_paths.issue_inventory, activity)
    read_paths = set(nine.get("read_paths", set())) | activity.read_paths
    root = repo_root.resolve(); raw_root = root / "data/raw"; raw_reads = []
    for value in read_paths:
        try: Path(value).resolve().relative_to(raw_root); raw_reads.append(value)
        except ValueError: pass
    passed = contract_validation.get("contract_validation_passed") is True and nine.get("preflight_existing_nine_outputs_passed") is True and safety["safety_write_validation_passed"] and safety["safety_passed_count"] == 55 and issue["issue_write_validation_passed"] and issue["issue_inventory_clear"] and issue["blocking_issue_count"] == 0 and len(read_paths) == 11 and not raw_reads
    blockers = [*contract_validation.get("blocking_reasons", []), *nine.get("blocking_reasons", []), *safety["blocking_reasons"], *issue["blocking_reasons"]]
    if len(read_paths) != 11: blockers.append("eleven_output_preflight_read_count_mismatch")
    if raw_reads: blockers.append("eleven_output_preflight_raw_read_forbidden")
    return {"preflight_existing_eleven_outputs_passed": passed and not blockers, "preflight_output_count": len(read_paths), "declared_output_nodes_passed": nodes["declared_output_nodes_passed"], "core_preflight_passed": nine.get("core_preflight_passed", False), "reference_preflight_passed": nine.get("reference_preflight_passed", False), "summary_integrity_preflight_passed": nine.get("summary_preflight_passed", False) and nine.get("integrity_preflight_passed", False), "safety_preflight_passed": safety["safety_write_validation_passed"] and safety["safety_passed_count"] == 55, "issue_preflight_passed": issue["issue_write_validation_passed"] and issue["issue_inventory_clear"], "read_paths": read_paths, "node_validation": nodes, "nine": nine, "safety": safety, "issue": issue, "blocking_reasons": sorted(set(blockers))}


@dataclass(frozen=True)
class ManifestPlannedWriteValidation:
    passed: bool; manifest_path: str; exact_manifest_path: bool; inside_final_root: bool; outside_raw_root: bool; disjoint_from_referenced_artifacts: bool; disjoint_from_other_outputs: bool; safe_existing_node: bool; blocking_reasons: list[str]


def validate_manifest_planned_write(output_paths: Step14AROutputPaths, artifact_inventory_rows: list[dict[str, Any]], *, repo_root: Path) -> ManifestPlannedWriteValidation:
    root = Path(os.path.abspath(repo_root)); final_root = root / FINAL_ROOT; raw_root = root / "data/raw"; raw = Path(output_paths.manifest); manifest = Path(os.path.abspath(raw if raw.is_absolute() else root / raw)); expected = final_root / OUTPUT_SPECS[-1][1]; blockers: list[str] = []
    exact = manifest == expected
    if not exact: blockers.append("manifest_planned_path_mismatch")
    try: manifest.relative_to(final_root); inside = True
    except ValueError: inside = False; blockers.append("manifest_planned_outside_final_root")
    try: manifest.relative_to(raw_root); outside_raw = False; blockers.append("manifest_planned_raw_write")
    except ValueError: outside_raw = True
    other_outputs = {Path(os.path.abspath(Path(getattr(output_paths, name)) if Path(getattr(output_paths, name)).is_absolute() else root / Path(getattr(output_paths, name)))) for name in EXISTING_ELEVEN_LOGICAL_NAMES}
    output_disjoint = manifest not in other_outputs
    if not output_disjoint: blockers.append("manifest_planned_output_collision")
    artifact_targets = {Path(os.path.abspath(root / Path(row.get("artifact_path", "")))) for row in artifact_inventory_rows if isinstance(row.get("artifact_path"), str) and row.get("artifact_path")}
    artifact_disjoint = manifest not in artifact_targets
    if not artifact_disjoint: blockers.append("manifest_planned_artifact_collision")
    if manifest.suffix != ".json" or manifest.name != OUTPUT_SPECS[-1][1] or manifest.name.endswith((".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".npy")):
        blockers.append("manifest_forbidden_extension")
    safe_node = True
    try: node = manifest.lstat()
    except FileNotFoundError: pass
    except OSError: safe_node = False; blockers.append("manifest_existing_not_regular_file")
    else:
        if stat.S_ISLNK(node.st_mode): safe_node = False; blockers.append("manifest_existing_symlink_forbidden")
        elif not stat.S_ISREG(node.st_mode): safe_node = False; blockers.append("manifest_existing_not_regular_file")
    blockers = sorted(set(blockers)); return ManifestPlannedWriteValidation(not blockers, str(manifest), exact, inside, outside_raw, artifact_disjoint, output_disjoint, safe_node, blockers)


@dataclass
class ManifestEvidenceActivity:
    read_paths: set[str] = field(default_factory=set)
    raw_read_attempted: bool = False


def sha256_validated_metadata_file(path: Path, activity: ManifestEvidenceActivity) -> str:
    path = Path(path); parts = path.resolve(strict=False).parts
    if any(parts[index:index + 2] == ("data", "raw") for index in range(len(parts) - 1)):
        activity.raw_read_attempted = True; raise OSError("manifest_evidence_raw_read_forbidden")
    node = path.lstat()
    if stat.S_ISLNK(node.st_mode) or not stat.S_ISREG(node.st_mode): raise OSError("manifest_evidence_node_not_regular")
    payload = path.read_bytes(); activity.read_paths.add(str(path.resolve())); return hashlib.sha256(payload).hexdigest()


def _eleven_typed_rows(preflight: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    nine = preflight.get("nine", {}); seven = nine.get("seven", {}); core = seven.get("core", {})
    return {
        "precondition_audit": core.get("precondition", {}).get("typed_rows", []),
        "final_dataset_index_csv": core.get("csv", {}).get("typed_rows", []),
        "final_dataset_index_json": core.get("json", {}).get("typed_rows", []),
        "membership": core.get("membership", {}).get("typed_rows", []),
        "artifact_inventory": seven.get("inventory", {}).get("typed_rows", []),
        "schema_validation_audit": seven.get("schema", {}).get("typed_rows", []),
        "source_preservation_audit": seven.get("preservation", {}).get("typed_rows", []),
        "split_summary": nine.get("summary", {}).get("typed_rows", []),
        "integrity_audit": nine.get("integrity", {}).get("typed_rows", []),
        "issue_inventory": preflight.get("issue", {}).get("typed_rows", []),
        "safety_audit": preflight.get("safety", {}).get("typed_rows", []),
    }


def build_non_manifest_output_inventory(output_paths: Step14AROutputPaths, preflight: dict[str, Any], activity: ManifestEvidenceActivity, *, repo_root: Path) -> list[dict[str, Any]]:
    typed = _eleven_typed_rows(preflight); rows: list[dict[str, Any]] = []
    for logical_name, filename, artifact_format, *_ in OUTPUT_SPECS[:11]:
        path = Path(getattr(output_paths, logical_name)); absolute = path if path.is_absolute() else repo_root / path
        rows.append({"logical_name": logical_name, "relative_path": str(Path(FINAL_ROOT) / filename), "format": artifact_format, "row_count": len(typed[logical_name]), "sha256": sha256_validated_metadata_file(absolute, activity)})
    return rows


def _manifest_pass_evidence(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, issue_safety_result: IssueSafetyDiskMaterializationResult, preflight: dict[str, Any]) -> dict[str, bool]:
    nine = preflight.get("nine", {}); seven = nine.get("seven", {}); core = seven.get("core", {})
    return {
        "source_step14aq_preconditions_passed": source_validation.source_validation_passed and all(source_validation.source_checks.values()),
        "final_dataset_index_schema_passed": reference_audit_result.schema_audit_write_validation.get("schema_audit_write_validation_passed") is True,
        "final_dataset_index_write_validation_passed": core.get("csv", {}).get("final_index_csv_write_validation_passed") is True and core.get("json", {}).get("final_index_json_write_validation_passed") is True and core.get("cross", {}).get("final_index_csv_json_consistent") is True,
        "membership_checks_passed": in_memory_result.membership_validation is not None and in_memory_result.membership_validation.passed,
        "membership_write_validation_passed": core.get("membership", {}).get("membership_write_validation_passed") is True,
        "artifact_inventory_checks_passed": in_memory_result.artifact_inventory_validation is not None and in_memory_result.artifact_inventory_validation.passed,
        "artifact_inventory_write_validation_passed": seven.get("inventory", {}).get("artifact_inventory_write_validation_passed") is True,
        "source_preservation_checks_passed": seven.get("preservation", {}).get("source_preservation_write_validation_passed") is True,
        "split_summary_checks_passed": nine.get("summary", {}).get("split_summary_write_validation_passed") is True,
        "integrity_checks_passed": nine.get("integrity", {}).get("integrity_write_validation_passed") is True,
        "safety_checks_passed": preflight.get("safety", {}).get("safety_write_validation_passed") is True and preflight.get("safety", {}).get("safety_passed_count") == 55,
        "issue_inventory_clear": preflight.get("issue", {}).get("issue_inventory_clear") is True and preflight.get("issue", {}).get("blocking_issue_count") == 0,
        "metadata_output_boundary_passed": issue_safety_result.metadata_output_boundary_after_write.get("metadata_output_boundary_passed") is True,
        "all_output_nodes_regular": preflight.get("node_validation", {}).get("regular_file_count") == 11 and preflight.get("node_validation", {}).get("declared_output_nodes_passed") is True,
    }


def _manifest_actual_evidence(source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, issue_safety_result: IssueSafetyDiskMaterializationResult, preflight: dict[str, Any], planned: ManifestPlannedWriteValidation, outputs: list[dict[str, Any]]) -> dict[str, Any]:
    typed = _eleven_typed_rows(preflight); summary = typed["split_summary"]
    split = lambda field: {row["split_name"]: row[field] for row in summary}
    return {"source_hashes": {name: source_validation.input_sha256.get(name, "") for name in SOURCE_LOGICAL_NAMES}, "outputs": outputs, "counts": {"final_dataset_index_row_count": len(typed["final_dataset_index_csv"]), "canonical_schema_field_count": len(typed["schema_validation_audit"]), "membership_row_count": len(typed["membership"]), "artifact_inventory_row_count": len(typed["artifact_inventory"]), "schema_audit_row_count": len(typed["schema_validation_audit"]), "source_preservation_row_count": len(typed["source_preservation_audit"]), "split_summary_row_count": len(summary), "integrity_audit_row_count": len(typed["integrity_audit"]), "safety_audit_row_count": len(typed["safety_audit"]), "issue_inventory_row_count": len(typed["issue_inventory"]), "blocking_issue_count": preflight.get("issue", {}).get("blocking_issue_count", 0)}, "split_sample_counts": split("sample_count"), "split_group_counts": split("leakage_group_count"), "split_artifact_counts": split("artifact_reference_count"), "mask_pairs": [list(pair) for pair in EXPECTED_CANONICAL_MASK_PAIRS], "pass_fields": _manifest_pass_evidence(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, issue_safety_result, preflight), "preflight_passed": preflight.get("preflight_existing_eleven_outputs_passed") is True, "planned_passed": planned.passed, "blocking_reasons": sorted(set(preflight.get("blocking_reasons", []) + planned.blocking_reasons))}


def build_final_manifest(contract_validation: dict[str, Any], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, issue_safety_result: IssueSafetyDiskMaterializationResult, eleven_output_preflight: dict[str, Any], manifest_planned_write_validation: ManifestPlannedWriteValidation, non_manifest_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = _manifest_actual_evidence(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, issue_safety_result, eleven_output_preflight, manifest_planned_write_validation, non_manifest_outputs); blockers = evidence["blocking_reasons"]; pass_fields = evidence["pass_fields"]; all_checks = contract_validation.get("contract_validation_passed") is True and all(pass_fields.values()) and evidence["preflight_passed"] and evidence["planned_passed"] and evidence["counts"]["blocking_issue_count"] == 0 and not blockers
    manifest: dict[str, Any] = {"stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME, "manifest_schema_version": "v0", "previous_stage": PREVIOUS_STAGE, "source_step14aq_commit": SOURCE_STEP14AQ_COMMIT, "source_input_count": len(SOURCE_LOGICAL_NAMES), "source_input_sha256": evidence["source_hashes"], "output_artifact_count": len(OUTPUT_SPECS), "non_manifest_output_count": len(non_manifest_outputs), "non_manifest_outputs": non_manifest_outputs}
    manifest.update(evidence["counts"]); manifest.update({"split_sample_counts": evidence["split_sample_counts"], "split_group_counts": evidence["split_group_counts"], "split_artifact_counts": evidence["split_artifact_counts"], "canonical_mask_pairs": evidence["mask_pairs"]}); manifest.update(pass_fields)
    manifest.update({"all_checks_passed": all_checks, "ready_for_covapie_final_dataset_qa_gate": all_checks, "ready_for_training": False, "ready_to_train_now": False, "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "statistical_representativeness_claimed": False, "production_split_policy_finalized": False, "contains_raw_structure": False, "contains_tensor_data": False, "raw_read_attempted": False, "recommended_next_step": "covapie_final_dataset_qa_gate_v0", "blocking_reasons": blockers})
    return {field: manifest[field] for field in FINAL_MANIFEST_FIELDS}


@dataclass
class FinalManifestValidationResult:
    passed: bool; blocking_reasons: list[str]; validated_manifest: dict[str, Any]; schema_passed: bool; source_hash_contract_passed: bool; output_inventory_contract_passed: bool; count_contract_passed: bool; split_contract_passed: bool; canonical_mask_contract_passed: bool; pass_field_contract_passed: bool; training_boundary_passed: bool; qa_readiness_passed: bool


def validate_final_manifest(manifest: Any, actual_evidence: dict[str, Any], *, repo_root: Path) -> FinalManifestValidationResult:
    blockers: list[str] = []
    if not isinstance(manifest, dict): return FinalManifestValidationResult(False, ["final_manifest_root_invalid"], {}, False, False, False, False, False, False, False, False, False)
    schema = list(manifest) == list(FINAL_MANIFEST_FIELDS)
    if not schema: blockers.append("final_manifest_schema_mismatch")
    source = manifest.get("source_input_count") == 12 and isinstance(manifest.get("source_input_sha256"), dict) and list(manifest.get("source_input_sha256", {})) == list(SOURCE_LOGICAL_NAMES) and manifest.get("source_input_sha256") == actual_evidence["source_hashes"] and all(re.fullmatch(r"[0-9a-f]{64}", value or "") for value in manifest.get("source_input_sha256", {}).values())
    if not source: blockers.append("final_manifest_source_hash_contract_mismatch")
    outputs = manifest.get("non_manifest_outputs"); output_ok = isinstance(outputs, list) and len(outputs) == 11 and manifest.get("non_manifest_output_count") == 11 and manifest.get("output_artifact_count") == 12
    if not output_ok: blockers.append("final_manifest_output_count_mismatch")
    if isinstance(outputs, list):
        expected_outputs = actual_evidence["outputs"]
        if [row.get("logical_name") if isinstance(row, dict) else None for row in outputs] != [row["logical_name"] for row in expected_outputs]: blockers.append("final_manifest_output_order_mismatch"); output_ok = False
        for number, row in enumerate(outputs):
            if not isinstance(row, dict): output_ok = False; continue
            logical = row.get("logical_name", f"row{number}"); expected = expected_outputs[number] if number < len(expected_outputs) else {}
            if list(row) != list(NON_MANIFEST_OUTPUT_ENTRY_FIELDS): blockers.append(f"final_manifest_output_schema_mismatch:{logical}"); output_ok = False
            if logical == "manifest" or row.get("relative_path", "").endswith(OUTPUT_SPECS[-1][1]) or "manifest_sha256" in row: blockers.append("final_manifest_self_hash_forbidden"); output_ok = False
            if row.get("relative_path") != expected.get("relative_path"): blockers.append(f"final_manifest_output_path_mismatch:{logical}"); output_ok = False
            if row.get("format") != expected.get("format"): blockers.append(f"final_manifest_output_format_mismatch:{logical}"); output_ok = False
            if row.get("row_count") != expected.get("row_count"): blockers.append(f"final_manifest_output_row_count_mismatch:{logical}"); output_ok = False
            if row.get("sha256") != expected.get("sha256"): blockers.append(f"final_manifest_output_hash_mismatch:{logical}"); output_ok = False
    counts = all(manifest.get(field) == value and type(manifest.get(field)) is int for field, value in actual_evidence["counts"].items())
    if not counts: blockers.append("final_manifest_count_contract_mismatch")
    split = manifest.get("split_sample_counts") == actual_evidence["split_sample_counts"] and manifest.get("split_group_counts") == actual_evidence["split_group_counts"] and manifest.get("split_artifact_counts") == actual_evidence["split_artifact_counts"] and list(manifest.get("split_sample_counts", {})) == [*aq.SPLITS, "total"] and list(manifest.get("split_group_counts", {})) == [*aq.SPLITS, "total"] and list(manifest.get("split_artifact_counts", {})) == [*aq.SPLITS, "total"]
    if not split: blockers.append("final_manifest_split_contract_mismatch")
    masks = manifest.get("canonical_mask_pairs") == actual_evidence["mask_pairs"] == [list(pair) for pair in EXPECTED_CANONICAL_MASK_PAIRS]
    if not masks: blockers.append("final_manifest_mask_contract_mismatch")
    pass_ok = True
    for field, expected in actual_evidence["pass_fields"].items():
        if type(manifest.get(field)) is not bool or manifest.get(field) is not expected: blockers.append(f"final_manifest_pass_field_mismatch:{field}"); pass_ok = False
    expected_all = all(actual_evidence["pass_fields"].values()) and actual_evidence["preflight_passed"] and actual_evidence["planned_passed"] and actual_evidence["counts"]["blocking_issue_count"] == 0 and not actual_evidence["blocking_reasons"]
    if type(manifest.get("all_checks_passed")) is not bool or manifest.get("all_checks_passed") is not expected_all: blockers.append("final_manifest_all_checks_mismatch")
    qa = type(manifest.get("ready_for_covapie_final_dataset_qa_gate")) is bool and manifest.get("ready_for_covapie_final_dataset_qa_gate") is manifest.get("all_checks_passed")
    if not qa: blockers.append("final_manifest_qa_readiness_mismatch")
    training = all((manifest.get("ready_for_training") is False, manifest.get("ready_to_train_now") is False, manifest.get("feature_semantics_known_for_training") is False, manifest.get("unknown_atom_feature_policy_finalized_for_training") is False, manifest.get("feature_semantics_audit_required_before_training") is True, manifest.get("statistical_representativeness_claimed") is False, manifest.get("production_split_policy_finalized") is False, manifest.get("contains_raw_structure") is False, manifest.get("contains_tensor_data") is False, manifest.get("raw_read_attempted") is False))
    if not training: blockers.append("final_manifest_training_boundary_mismatch")
    if manifest.get("blocking_reasons") != actual_evidence["blocking_reasons"]: blockers.append("final_manifest_blocking_reason_mismatch")
    if manifest.get("recommended_next_step") != "covapie_final_dataset_qa_gate_v0": blockers.append("final_manifest_recommended_next_step_mismatch")
    basics = manifest.get("stage") == STAGE and manifest.get("step_label") == STEP_LABEL and manifest.get("project_name") == PROJECT_NAME and manifest.get("manifest_schema_version") == "v0" and manifest.get("previous_stage") == PREVIOUS_STAGE and manifest.get("source_step14aq_commit") == SOURCE_STEP14AQ_COMMIT
    if not basics: blockers.append("final_manifest_schema_mismatch")
    blockers = sorted(set(blockers)); return FinalManifestValidationResult(not blockers, blockers, manifest, schema, source, output_ok, counts, split, masks, pass_ok, training, qa)


def validate_written_final_manifest(expected_manifest: dict[str, Any], path: Path, activity: DiskWriteActivity, actual_evidence: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    blockers: list[str] = []
    try: value = read_json_safely(path, activity)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError): return {"manifest_write_validation_passed": False, "manifest_root_is_object": False, "manifest_field_count": 0, "manifest_all_checks_passed": False, "manifest_ready_for_qa_gate": False, "typed_manifest": {}, "blocking_reasons": ["final_manifest_disk_unreadable"]}
    if not isinstance(value, dict): blockers.append("final_manifest_root_invalid")
    if value != expected_manifest: blockers.append("final_manifest_disk_content_mismatch")
    validation = validate_final_manifest(value, actual_evidence, repo_root=repo_root); blockers.extend(validation.blocking_reasons)
    blockers = sorted(set(blockers)); return {"manifest_write_validation_passed": not blockers, "manifest_root_is_object": isinstance(value, dict), "manifest_field_count": len(value) if isinstance(value, dict) else 0, "manifest_all_checks_passed": value.get("all_checks_passed") is True if isinstance(value, dict) else False, "manifest_ready_for_qa_gate": value.get("ready_for_covapie_final_dataset_qa_gate") is True if isinstance(value, dict) else False, "typed_manifest": value if isinstance(value, dict) else {}, "blocking_reasons": blockers}


def build_blocked_manifest(source_validation: Step14AQSourceValidationResult, blockers: list[str]) -> dict[str, Any]:
    manifest = {"stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME, "manifest_schema_version": "v0", "previous_stage": PREVIOUS_STAGE, "source_step14aq_commit": SOURCE_STEP14AQ_COMMIT, "source_input_count": len(SOURCE_LOGICAL_NAMES), "source_input_sha256": {name: source_validation.input_sha256.get(name, "") for name in SOURCE_LOGICAL_NAMES}, "output_artifact_count": 12, "non_manifest_output_count": 0, "non_manifest_outputs": [], "final_dataset_index_row_count": 0, "canonical_schema_field_count": 0, "membership_row_count": 0, "artifact_inventory_row_count": 0, "schema_audit_row_count": 0, "source_preservation_row_count": 0, "split_summary_row_count": 0, "integrity_audit_row_count": 0, "safety_audit_row_count": 0, "issue_inventory_row_count": 0, "blocking_issue_count": len(set(blockers)), "split_sample_counts": {name: 0 for name in (*aq.SPLITS, "total")}, "split_group_counts": {name: 0 for name in (*aq.SPLITS, "total")}, "split_artifact_counts": {name: 0 for name in (*aq.SPLITS, "total")}, "canonical_mask_pairs": [list(pair) for pair in EXPECTED_CANONICAL_MASK_PAIRS]}
    manifest.update({field: False for field in FINAL_MANIFEST_PASS_FIELDS}); manifest.update({"all_checks_passed": False, "ready_for_covapie_final_dataset_qa_gate": False, "ready_for_training": False, "ready_to_train_now": False, "feature_semantics_known_for_training": False, "unknown_atom_feature_policy_finalized_for_training": False, "feature_semantics_audit_required_before_training": True, "statistical_representativeness_claimed": False, "production_split_policy_finalized": False, "contains_raw_structure": False, "contains_tensor_data": False, "raw_read_attempted": False, "recommended_next_step": "covapie_final_dataset_qa_gate_v0", "blocking_reasons": sorted(set(blockers))})
    return {field: manifest[field] for field in FINAL_MANIFEST_FIELDS}


def validate_blocked_manifest(manifest: Any) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(manifest, dict) or list(manifest) != list(FINAL_MANIFEST_FIELDS): blockers.append("blocked_manifest_schema_mismatch")
    elif manifest.get("all_checks_passed") is not False or manifest.get("ready_for_covapie_final_dataset_qa_gate") is not False or manifest.get("ready_for_training") is not False or manifest.get("ready_to_train_now") is not False or manifest.get("feature_semantics_audit_required_before_training") is not True or not manifest.get("blocking_reasons") or manifest.get("non_manifest_outputs") != []: blockers.append("blocked_manifest_boundary_mismatch")
    return {"blocked_manifest_validation_passed": not blockers, "blocking_reasons": blockers}


@dataclass
class FinalManifestMaterializationResult:
    passed: bool; blocking_reasons: list[str]; output_paths: Step14AROutputPaths; manifest: dict[str, Any]; manifest_validation: FinalManifestValidationResult | None; manifest_write_validation: dict[str, Any]; preflight_existing_eleven_outputs: dict[str, Any]; manifest_planned_write_validation: ManifestPlannedWriteValidation | None; manifest_evidence_activity: ManifestEvidenceActivity; activity: DiskWriteActivity; final_node_validation: dict[str, Any]; final_metadata_boundary: dict[str, Any]; final_output_sha256: dict[str, str]; ready_for_covapie_final_dataset_qa_gate: bool; ready_for_training: bool = False; ready_to_train_now: bool = False
    @property
    def final_manifest_materialization_passed(self) -> bool: return self.passed and not self.blocking_reasons


def materialize_final_manifest_and_gate(contract_validation: dict[str, Any], source_validation: Step14AQSourceValidationResult, in_memory_result: FinalDatasetInMemoryMaterializationResult, core_disk_result: CoreDiskMaterializationResult, reference_audit_result: ReferenceAuditDiskMaterializationResult, summary_integrity_result: SummaryIntegrityDiskMaterializationResult, issue_safety_result: IssueSafetyDiskMaterializationResult, *, output_paths: Step14AROutputPaths = DEFAULT_STEP14AR_OUTPUT_PATHS, repo_root: Path = REPO) -> FinalManifestMaterializationResult:
    activity = DiskWriteActivity(); evidence_activity = ManifestEvidenceActivity(); empty_write = {"manifest_write_validation_passed": False, "blocking_reasons": []}; empty_preflight: dict[str, Any] = {}; empty_nodes: dict[str, Any] = {}; empty_boundary: dict[str, Any] = {}
    path_validation = validate_step14ar_output_paths(output_paths, repo_root=repo_root)
    if not path_validation["output_path_contract_passed"]: return FinalManifestMaterializationResult(False, path_validation["blocking_reasons"], output_paths, {}, None, empty_write, empty_preflight, None, evidence_activity, activity, empty_nodes, empty_boundary, {}, False)
    artifact_rows = issue_safety_result.preflight_existing_nine_outputs.get("seven", {}).get("inventory", {}).get("typed_rows", [])
    planned = validate_manifest_planned_write(output_paths, artifact_rows, repo_root=repo_root)
    if not planned.passed: return FinalManifestMaterializationResult(False, planned.blocking_reasons, output_paths, {}, None, empty_write, empty_preflight, planned, evidence_activity, activity, empty_nodes, empty_boundary, {}, False)
    preflight = preflight_existing_eleven_outputs(contract_validation, source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, issue_safety_result, repo_root=repo_root)
    prerequisite_blockers = sorted(set(contract_validation.get("blocking_reasons", []) + source_validation.blocking_reasons + in_memory_result.blocking_reasons + core_disk_result.blocking_reasons + reference_audit_result.blocking_reasons + summary_integrity_result.blocking_reasons + issue_safety_result.blocking_reasons + preflight.get("blocking_reasons", [])))
    prerequisites = all((contract_validation.get("contract_validation_passed") is True, source_validation.source_validation_passed, in_memory_result.in_memory_materialization_passed, core_disk_result.core_disk_materialization_passed, reference_audit_result.reference_audit_disk_materialization_passed, summary_integrity_result.summary_integrity_disk_materialization_passed, issue_safety_result.issue_safety_disk_materialization_passed, issue_safety_result.ready_for_manifest_materialization, preflight.get("preflight_existing_eleven_outputs_passed") is True)) and not prerequisite_blockers
    if not prerequisites:
        blockers = prerequisite_blockers or ["final_manifest_prerequisite_not_passed"]; manifest = build_blocked_manifest(source_validation, blockers); write_json_atomic(output_paths.manifest, manifest, activity); blocked = validate_blocked_manifest(manifest); readback = read_json_safely(output_paths.manifest, activity); write_validation = {"manifest_write_validation_passed": blocked["blocked_manifest_validation_passed"] and readback == manifest, "manifest_root_is_object": isinstance(readback, dict), "manifest_field_count": len(readback) if isinstance(readback, dict) else 0, "manifest_all_checks_passed": False, "manifest_ready_for_qa_gate": False, "typed_manifest": readback, "blocking_reasons": []}
        return FinalManifestMaterializationResult(False, blockers, output_paths, manifest, None, write_validation, preflight, planned, evidence_activity, activity, {}, validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root), {}, False)
    outputs = build_non_manifest_output_inventory(output_paths, preflight, evidence_activity, repo_root=repo_root); evidence = _manifest_actual_evidence(source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, issue_safety_result, preflight, planned, outputs); manifest = build_final_manifest(contract_validation, source_validation, in_memory_result, core_disk_result, reference_audit_result, summary_integrity_result, issue_safety_result, preflight, planned, outputs); validation = validate_final_manifest(manifest, evidence, repo_root=repo_root)
    if not validation.passed:
        blockers = validation.blocking_reasons; blocked = build_blocked_manifest(source_validation, blockers); write_json_atomic(output_paths.manifest, blocked, activity); readback = read_json_safely(output_paths.manifest, activity); write_validation = {"manifest_write_validation_passed": validate_blocked_manifest(readback)["blocked_manifest_validation_passed"], "manifest_root_is_object": isinstance(readback, dict), "manifest_field_count": len(readback) if isinstance(readback, dict) else 0, "manifest_all_checks_passed": False, "manifest_ready_for_qa_gate": False, "typed_manifest": readback, "blocking_reasons": []}
        return FinalManifestMaterializationResult(False, blockers, output_paths, blocked, validation, write_validation, preflight, planned, evidence_activity, activity, {}, validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root), {}, False)
    before_hashes = {row["logical_name"]: row["sha256"] for row in outputs}; write_json_atomic(output_paths.manifest, manifest, activity); write_validation = validate_written_final_manifest(manifest, output_paths.manifest, activity, evidence, repo_root=repo_root); nodes = validate_declared_output_file_nodes(ALL_TWELVE_LOGICAL_NAMES, output_paths, repo_root=repo_root); boundary = validate_step14ar_metadata_output_boundary(output_paths, repo_root=repo_root); final_hashes: dict[str, str] = {}
    if nodes.get("declared_output_nodes_passed"):
        for logical_name in ALL_TWELVE_LOGICAL_NAMES:
            path = Path(getattr(output_paths, logical_name)); absolute = path if path.is_absolute() else repo_root / path; final_hashes[logical_name] = hashlib.sha256(absolute.read_bytes()).hexdigest()
    hash_preserved = all(final_hashes.get(name) == value for name, value in before_hashes.items())
    blockers = [*write_validation["blocking_reasons"], *nodes.get("blocking_reasons", []), *boundary.get("blocking_reasons", [])]
    if boundary.get("existing_output_count") != 12: blockers.append("final_metadata_output_count_mismatch")
    if not hash_preserved: blockers.append("non_manifest_output_hash_changed")
    if len(evidence_activity.read_paths) != 11 or evidence_activity.raw_read_attempted: blockers.append("manifest_evidence_activity_mismatch")
    passed = not blockers and write_validation["manifest_write_validation_passed"] and nodes.get("regular_file_count") == 12 and boundary.get("existing_output_count") == 12 and manifest["all_checks_passed"] is True
    blockers = sorted(set(blockers)); return FinalManifestMaterializationResult(passed, blockers, output_paths, manifest, validation, write_validation, preflight, planned, evidence_activity, activity, nodes, boundary, final_hashes, passed)

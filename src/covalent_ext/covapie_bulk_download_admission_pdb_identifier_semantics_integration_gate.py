"""Read-only Step14AU-B2 overlay for frozen PDB identifier semantics.

This successor view never rewrites the Step14AU-A blocker-discovery outputs.
It copies their metadata rows and applies the already-frozen Step14AU-B1 PDB
contract only to ADMIT_002, ``pdb_id``, and ``pdb_id_format_contract``.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext.covapie_bulk_download_admission_pdb_identifier_semantics_design_gate import (
    CANONICAL_PATTERN,
    EXTENDED_PATTERN,
    LEGACY_PATTERN,
    PdbIdentifierNormalizationResult,
    normalize_pdb_identifier,
)


STAGE = "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1"
STEP_LABEL = "Step14AU-B2"
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = "covapie_pdb_identifier_semantics_integration_gate_v1_manifest_v1"
PREVIOUS_STAGES = (
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
    "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1",
)
RECOMMENDED_NEXT_STEP = "resolve_next_covapie_bulk_download_admission_semantics_blocker"
BLOCKED_NEXT_STEP = "resolve_covapie_pdb_identifier_semantics_integration_gate_blockers"

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP14AU_A_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
STEP14AU_B1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1"
)

AU_A_FILENAMES = (
    "covapie_bulk_download_admission_rule_executability_matrix.csv",
    "covapie_bulk_download_admission_field_semantics_matrix.csv",
    "covapie_bulk_download_admission_evaluation_context_contract.csv",
    "covapie_bulk_download_admission_implementation_safety_audit.csv",
    "covapie_bulk_download_admission_implementation_issue_inventory.csv",
    "covapie_bulk_download_admission_implementation_precondition_manifest.json",
)
B1_FILENAMES = (
    "covapie_pdb_identifier_semantics_contract.csv",
    "covapie_pdb_identifier_normalization_examples.csv",
    "covapie_pdb_identifier_source_boundary_audit.csv",
    "covapie_pdb_identifier_safety_audit.csv",
    "covapie_pdb_identifier_issue_inventory.csv",
    "covapie_pdb_identifier_semantics_design_manifest.json",
)
SOURCE_SHA256 = {
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[0]): "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[1]): "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[2]): "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[3]): "a8942ae2b17d5dcaf367e2f7ab783fd2a0732449e72e04cc16e9fd9b3f7402c6",
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[4]): "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    str(STEP14AU_A_ROOT / AU_A_FILENAMES[5]): "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[0]): "cabbbf025f4336a6789ead032a01c8ee329efcca46f981e5b37f0843af301be4",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[1]): "35ea09ae36ddf2311b1dcf5a313d18e62888c68e542eb068bd98c04900379ce9",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[2]): "859a359ea2deab113c6d82fa7e63530496abcdfbd5dfe2aa52a50e3735cc4082",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[3]): "034240c5493d891ce44cef8dc6221b42c77eb8d5d2f7833bf83d6777e63050cf",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[4]): "761b1483e56f189d31575b6f2e0f26106cc15f38d4e700806bf349187e218d88",
    str(STEP14AU_B1_ROOT / B1_FILENAMES[5]): "4b8bf6a9754e8c416359c8ac9616628c83f0e09941240c78db1d21f3bdb37b70",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
RULE_SOURCE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase",
    "candidate_field_dependencies", "batch_context_dependencies",
    "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required",
    "pure_in_memory_interface_possible", "dependency_contract_passed",
    "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition", "blocking_reasons",
)
FIELD_SOURCE_COLUMNS = (
    "field_name", "requirement_phase", "source_value_contract", "candidate_record_field",
    "producer_scope", "dependent_rules", "batch_context_required", "evaluation_context_dependencies",
    "allowed_values_defined", "normalization_defined", "exact_validation_defined",
    "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    "field_contract_mapping_passed",
)
CONTEXT_SOURCE_COLUMNS = (
    "context_item", "context_scope", "required_by_rules", "provided_by_future_caller",
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator",
    "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
    "implementation_ready", "blocking_reasons",
)
ISSUE_SOURCE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason",
)
LINEAGE_COLUMNS = ("source_stage", "integration_source_stage", "integration_applied", "integration_reason")
RULE_COLUMNS = RULE_SOURCE_COLUMNS + LINEAGE_COLUMNS
FIELD_COLUMNS = FIELD_SOURCE_COLUMNS + LINEAGE_COLUMNS
CONTEXT_COLUMNS = CONTEXT_SOURCE_COLUMNS + LINEAGE_COLUMNS
ISSUE_COLUMNS = ISSUE_SOURCE_COLUMNS + ("issue_origin", "integration_transition")
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink", "sha256_expected",
    "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = ("safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason")
CSV_OUTPUTS = (
    "covapie_pdb_identifier_integrated_rule_matrix.csv",
    "covapie_pdb_identifier_integrated_field_matrix.csv",
    "covapie_pdb_identifier_integrated_context_matrix.csv",
    "covapie_pdb_identifier_integration_safety_audit.csv",
    "covapie_pdb_identifier_integration_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_pdb_identifier_semantics_integration_manifest.json"
SAFETY_ITEMS = (
    "network_access_used_current_step", "raw_directory_traversed_current_step",
    "artifact_reference_paths_followed_current_step", "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step", "raw_files_written_current_step",
    "torch_imported", "numpy_imported", "rdkit_used", "biopython_used", "gemmi_used",
    "dataloader_instantiated", "checkpoint_loaded", "model_forward_called", "loss_compute_called",
    "training_allowed",
)
REMAINING_ISSUE_IDS = (
    "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED",
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "LIGAND_COMP_ID_SEMANTICS_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)
REMOVED_ISSUE_ID = "PDB_ID_FORMAT_SEMANTICS_UNRESOLVED"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()], cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _source_paths() -> tuple[Path, ...]:
    return tuple(STEP14AU_A_ROOT / name for name in AU_A_FILENAMES) + tuple(
        STEP14AU_B1_ROOT / name for name in B1_FILENAMES
    )


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _source_boundary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _source_paths():
        absolute = _repo_path(path)
        observed = _sha256(absolute) if absolute.is_file() and not absolute.is_symlink() else ""
        passed = _tracked_by_git(path) and absolute.is_file() and not absolute.is_symlink() and observed == SOURCE_SHA256[path.as_posix()]
        rows.append({
            "source_relative_path": path.as_posix(), "tracked_by_git": _bool_text(_tracked_by_git(path)),
            "regular_file": _bool_text(absolute.is_file()), "symlink": _bool_text(absolute.is_symlink()),
            "sha256_expected": SOURCE_SHA256[path.as_posix()], "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    return (
        len(rows) == 12
        and all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == 12
        and all(
            row["tracked_by_git"] == "true" and row["regular_file"] == "true" and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true"
            for row in rows
        )
    )


def _load_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(STEP14AU_A_ROOT / AU_A_FILENAMES[0]),
        "field_rows": _read_csv(STEP14AU_A_ROOT / AU_A_FILENAMES[1]),
        "context_rows": _read_csv(STEP14AU_A_ROOT / AU_A_FILENAMES[2]),
        "safety_rows": _read_csv(STEP14AU_A_ROOT / AU_A_FILENAMES[3]),
        "issue_rows": _read_csv(STEP14AU_A_ROOT / AU_A_FILENAMES[4]),
        "au_manifest": json.loads(_repo_path(STEP14AU_A_ROOT / AU_A_FILENAMES[5]).read_text(encoding="utf-8")),
        "b1_contract": _read_csv(STEP14AU_B1_ROOT / B1_FILENAMES[0]),
        "b1_examples": _read_csv(STEP14AU_B1_ROOT / B1_FILENAMES[1]),
        "b1_source_rows": _read_csv(STEP14AU_B1_ROOT / B1_FILENAMES[2]),
        "b1_safety_rows": _read_csv(STEP14AU_B1_ROOT / B1_FILENAMES[3]),
        "b1_issue_rows": _read_csv(STEP14AU_B1_ROOT / B1_FILENAMES[4]),
        "b1_manifest": json.loads(_repo_path(STEP14AU_B1_ROOT / B1_FILENAMES[5]).read_text(encoding="utf-8")),
    }


def _validate_source_semantics(source: dict[str, Any]) -> bool:
    au_rules = source["rule_rows"]
    au_fields = source["field_rows"]
    au_contexts = source["context_rows"]
    au_issues = source["issue_rows"]
    au_manifest = source["au_manifest"]
    b1_manifest = source["b1_manifest"]
    return (
        len(au_rules) == 15 and all(tuple(row.keys()) == RULE_SOURCE_COLUMNS for row in au_rules)
        and len(au_fields) == 17 and all(tuple(row.keys()) == FIELD_SOURCE_COLUMNS for row in au_fields)
        and len(au_contexts) == 18 and all(tuple(row.keys()) == CONTEXT_SOURCE_COLUMNS for row in au_contexts)
        and len(au_issues) == 13 and all(tuple(row.keys()) == ISSUE_SOURCE_COLUMNS for row in au_issues)
        and [row["issue_id"] for row in au_issues].count(REMOVED_ISSUE_ID) == 1
        and au_manifest.get("stage") == PREVIOUS_STAGES[0]
        and au_manifest.get("issue_count") == 13
        and au_manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and b1_manifest.get("stage") == PREVIOUS_STAGES[1]
        and b1_manifest.get("ready_for_pdb_identifier_semantics_integration") is True
        and b1_manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and source["b1_issue_rows"] == [{
            "issue_id": "NO_ISSUES", "issue_type": "no_pdb_identifier_semantics_design_issues",
            "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
        }]
        and len(source["b1_contract"]) == 20 and len(source["b1_examples"]) == 29
        and all(row.get("example_passed") == "true" for row in source["b1_examples"])
    )


def _lineage(applied: bool) -> dict[str, str]:
    return {
        "source_stage": PREVIOUS_STAGES[0],
        "integration_source_stage": PREVIOUS_STAGES[1] if applied else "",
        "integration_applied": _bool_text(applied),
        "integration_reason": "PDB identifier semantics contract frozen" if applied else "",
    }


def _overlay_rule_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for source in source_rows:
        row = dict(source)
        applied = row["admission_rule_id"] == "ADMIT_002"
        if applied:
            row.update({
                "dependency_contract_passed": "true", "semantics_complete": "true",
                "deterministic_evaluation_possible_now": "true",
                "deterministic_evaluation_possible_after_contract_freeze": "true",
                "implementation_disposition": "rule_logic_ready", "blocking_reasons": "",
            })
        row.update(_lineage(applied))
        result.append(row)
    return result


def _overlay_field_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for source in source_rows:
        row = dict(source)
        applied = row["field_name"] == "pdb_id"
        if applied:
            row.update({
                "allowed_values_defined": "true", "normalization_defined": "true",
                "exact_validation_defined": "true", "implementation_semantics_complete": "true",
                "semantics_evidence": PREVIOUS_STAGES[1], "blocking_reasons": "",
            })
        row.update(_lineage(applied))
        result.append(row)
    return result


def _overlay_context_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for source in source_rows:
        row = dict(source)
        applied = row["context_item"] == "pdb_id_format_contract"
        if applied:
            row.update({
                "deterministic_now": "true", "deterministic_after_contract_freeze": "true",
                "exact_contract_defined": "true", "implementation_ready": "true", "blocking_reasons": "",
            })
        row.update(_lineage(applied))
        result.append(row)
    return result


def _overlay_issue_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for source in source_rows:
        if source["issue_id"] == REMOVED_ISSUE_ID:
            continue
        row = dict(source)
        row.update({
            "issue_origin": "step14au_a_remaining_semantics_blocker", "integration_transition": "unchanged",
        })
        result.append(row)
    return result


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "required_status": "false", "observed_status": "false",
        "safety_passed": "true", "blocking_reason": "",
    } for item in SAFETY_ITEMS]


def _validate_lineage_rows(
    rule_rows: list[dict[str, str]], field_rows: list[dict[str, str]], context_rows: list[dict[str, str]],
) -> bool:
    """Validate lineage independently from source-value overlay semantics."""
    expected = (
        (rule_rows, "admission_rule_id", "ADMIT_002"),
        (field_rows, "field_name", "pdb_id"),
        (context_rows, "context_item", "pdb_id_format_contract"),
    )
    for rows, identifier, integrated_id in expected:
        if not rows or any(row.get("source_stage") != PREVIOUS_STAGES[0] for row in rows):
            return False
        if [row.get(identifier) for row in rows if row.get("integration_applied") == "true"] != [integrated_id]:
            return False
        for row in rows:
            applied = row.get(identifier) == integrated_id
            if row.get("integration_applied") != _bool_text(applied):
                return False
            if row.get("integration_source_stage") != (PREVIOUS_STAGES[1] if applied else ""):
                return False
            if row.get("integration_reason") != ("PDB identifier semantics contract frozen" if applied else ""):
                return False
    return True


def _validate_integrated_rule_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    if len(rows) != 15 or len(source_rows) != 15 or any(tuple(row.keys()) != RULE_COLUMNS for row in rows):
        return False
    if [row["admission_rule_id"] for row in rows] != [row["admission_rule_id"] for row in source_rows]:
        return False
    allowed = {
        "dependency_contract_passed", "semantics_complete", "deterministic_evaluation_possible_now",
        "deterministic_evaluation_possible_after_contract_freeze", "implementation_disposition", "blocking_reasons",
    }
    for row, source in zip(rows, source_rows):
        if row["admission_rule_id"] != "ADMIT_002":
            if any(row[column] != source[column] for column in RULE_SOURCE_COLUMNS):
                return False
            continue
        if any(row[column] != source[column] for column in RULE_SOURCE_COLUMNS if column not in allowed):
            return False
        if any(row[column] != "true" for column in (
            "dependency_contract_passed", "semantics_complete", "deterministic_evaluation_possible_now",
            "deterministic_evaluation_possible_after_contract_freeze",
        )):
            return False
        if row["implementation_disposition"] != "rule_logic_ready" or row["blocking_reasons"] != "":
            return False
    return [row["admission_rule_id"] for row in rows if row["semantics_complete"] == "true"] == ["ADMIT_002", "ADMIT_014", "ADMIT_015"]


def _validate_integrated_field_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    if len(rows) != 17 or len(source_rows) != 17 or any(tuple(row.keys()) != FIELD_COLUMNS for row in rows):
        return False
    if [row["field_name"] for row in rows] != [row["field_name"] for row in source_rows]:
        return False
    allowed = {
        "allowed_values_defined", "normalization_defined", "exact_validation_defined",
        "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    }
    for row, source in zip(rows, source_rows):
        if row["field_name"] != "pdb_id":
            if any(row[column] != source[column] for column in FIELD_SOURCE_COLUMNS):
                return False
            continue
        if any(row[column] != source[column] for column in FIELD_SOURCE_COLUMNS if column not in allowed):
            return False
        if any(row[column] != "true" for column in (
            "allowed_values_defined", "normalization_defined", "exact_validation_defined",
            "implementation_semantics_complete",
        )):
            return False
        if row["semantics_evidence"] != PREVIOUS_STAGES[1] or row["blocking_reasons"] != "":
            return False
    return [row["field_name"] for row in rows if row["implementation_semantics_complete"] == "true"] == ["pdb_id"]


def _validate_integrated_context_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    if len(rows) != 18 or len(source_rows) != 18 or any(tuple(row.keys()) != CONTEXT_COLUMNS for row in rows):
        return False
    if [row["context_item"] for row in rows] != [row["context_item"] for row in source_rows]:
        return False
    allowed = {
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
        "implementation_ready", "blocking_reasons",
    }
    for row, source in zip(rows, source_rows):
        if row["context_item"] != "pdb_id_format_contract":
            if any(row[column] != source[column] for column in CONTEXT_SOURCE_COLUMNS):
                return False
            continue
        if any(row[column] != source[column] for column in CONTEXT_SOURCE_COLUMNS if column not in allowed):
            return False
        if any(row[column] != "true" for column in (
            "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined", "implementation_ready",
        )) or row["blocking_reasons"] != "":
            return False
    return (
        sum(row["deterministic_now"] == "true" for row in rows) == 6
        and sum(row["deterministic_after_contract_freeze"] == "true" for row in rows) == 18
        and sum(row["implementation_ready"] == "true" for row in rows) == 6
    )


def _validate_issue_transition_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    expected = [row for row in source_rows if row["issue_id"] != REMOVED_ISSUE_ID]
    if len(rows) != 12 or len(expected) != 12 or any(tuple(row.keys()) != ISSUE_COLUMNS for row in rows):
        return False
    for row, source in zip(rows, expected):
        if any(row[column] != source[column] for column in ISSUE_SOURCE_COLUMNS):
            return False
        if row["issue_origin"] != "step14au_a_remaining_semantics_blocker" or row["integration_transition"] != "unchanged":
            return False
    return [row["issue_id"] for row in rows] == list(REMAINING_ISSUE_IDS)


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return rows == _safety_rows() and all(tuple(row.keys()) == SAFETY_COLUMNS for row in rows)


def evaluate_admit_002_pdb_identifier(value: object) -> dict[str, object]:
    """Evaluate only frozen PDB syntax; it makes no existence claim."""
    result: PdbIdentifierNormalizationResult = normalize_pdb_identifier(value)
    return {
        "admission_rule_id": "ADMIT_002", "passed": result.syntax_valid,
        "canonical_pdb_id": result.canonical_pdb_id, "input_form": result.input_form,
        "blocking_reason": result.blocking_reason,
    }


def _failure_issue_rows(
    domain_rows: list[dict[str, str]], section_status: tuple[tuple[str, bool], ...],
) -> list[dict[str, str]]:
    specs = {
        "source": ("PDB_IDENTIFIER_INTEGRATION_SOURCE_BOUNDARY_FAILED", "pdb_identifier_integration_source_boundary_failed", "", ""),
        "lineage": ("PDB_IDENTIFIER_INTEGRATION_LINEAGE_VALIDATION_FAILED", "pdb_identifier_integration_lineage_validation_failed", "pdb_id", "ADMIT_002"),
        "rules": ("PDB_IDENTIFIER_INTEGRATED_RULE_VALIDATION_FAILED", "pdb_identifier_integrated_rule_validation_failed", "pdb_id", "ADMIT_002"),
        "fields": ("PDB_IDENTIFIER_INTEGRATED_FIELD_VALIDATION_FAILED", "pdb_identifier_integrated_field_validation_failed", "pdb_id", "ADMIT_002"),
        "contexts": ("PDB_IDENTIFIER_INTEGRATED_CONTEXT_VALIDATION_FAILED", "pdb_identifier_integrated_context_validation_failed", "pdb_id", "ADMIT_002"),
        "issues": ("PDB_IDENTIFIER_ISSUE_TRANSITION_VALIDATION_FAILED", "pdb_identifier_issue_transition_validation_failed", "", ""),
        "safety": ("PDB_IDENTIFIER_INTEGRATION_SAFETY_VALIDATION_FAILED", "pdb_identifier_integration_safety_validation_failed", "", ""),
    }
    failures = []
    for section, passed in section_status:
        if passed:
            continue
        issue_id, reason, fields, rules = specs[section]
        failures.append({
            "issue_id": issue_id, "issue_type": "pdb_identifier_integration_gate_validation_failure",
            "affected_fields": fields, "affected_rules": rules, "severity": "blocking", "status": "open",
            "blocking_scope": "integration_gate", "blocking_reason": reason,
            "issue_origin": "step14au_b2_integration_gate_failure", "integration_transition": "added_by_gate_failure",
        })
    return [*domain_rows, *failures]


def _build_materialization(
    source: dict[str, Any], *, source_rows: list[dict[str, str]] | None = None,
    rule_rows: list[dict[str, str]] | None = None, field_rows: list[dict[str, str]] | None = None,
    context_rows: list[dict[str, str]] | None = None, issue_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    rule_rows = _overlay_rule_rows(source["rule_rows"]) if rule_rows is None else rule_rows
    field_rows = _overlay_field_rows(source["field_rows"]) if field_rows is None else field_rows
    context_rows = _overlay_context_rows(source["context_rows"]) if context_rows is None else context_rows
    issue_rows = _overlay_issue_rows(source["issue_rows"]) if issue_rows is None else issue_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    source_passed = _validate_source_rows(source_rows) and _validate_source_semantics(source)
    lineage_passed = _validate_lineage_rows(rule_rows, field_rows, context_rows)
    rules_passed = _validate_integrated_rule_rows(rule_rows, source["rule_rows"])
    fields_passed = _validate_integrated_field_rows(field_rows, source["field_rows"])
    contexts_passed = _validate_integrated_context_rows(context_rows, source["context_rows"])
    issues_passed = _validate_issue_transition_rows(issue_rows, source["issue_rows"])
    safety_passed = _validate_safety_rows(safety_rows)
    section_status = (
        ("source", source_passed), ("lineage", lineage_passed), ("rules", rules_passed),
        ("fields", fields_passed), ("contexts", contexts_passed), ("issues", issues_passed),
        ("safety", safety_passed),
    )
    all_checks_passed = all(passed for _, passed in section_status)
    domain_issue_rows = _overlay_issue_rows(source["issue_rows"])
    return {
        "source_rows": source_rows, "rule_rows": rule_rows, "field_rows": field_rows,
        "context_rows": context_rows, "issue_rows": _failure_issue_rows(domain_issue_rows, section_status), "safety_rows": safety_rows,
        "remaining_issue_count": len(domain_issue_rows),
        "all_source_boundary_checks_passed": source_passed,
        "all_integration_lineage_checks_passed": lineage_passed,
        "all_integrated_rule_checks_passed": rules_passed,
        "all_integrated_field_checks_passed": fields_passed,
        "all_integrated_context_checks_passed": contexts_passed,
        "all_issue_transition_checks_passed": issues_passed,
        "all_safety_checks_passed": safety_passed,
        "all_checks_passed": all_checks_passed,
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    outputs = (
        (CSV_OUTPUTS[0], RULE_COLUMNS, result["rule_rows"]),
        (CSV_OUTPUTS[1], FIELD_COLUMNS, result["field_rows"]),
        (CSV_OUTPUTS[2], CONTEXT_COLUMNS, result["context_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    )
    for name, columns, rows in outputs:
        _write_csv(root / name, columns, rows)
    return {name: _sha256(root / name) for name in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    rules, fields, contexts, issues = (result["rule_rows"], result["field_rows"], result["context_rows"], result["issue_rows"])
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stages": list(PREVIOUS_STAGES),
        "source_read_boundary": "only_step14au_a_and_step14au_b1_12_committed_metadata_outputs",
        "source_input_count": len(SOURCE_SHA256), "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "integrated_rule_count": len(rules), "integrated_field_count": len(fields), "integrated_context_count": len(contexts),
        "changed_rule_ids": ["ADMIT_002"], "changed_field_names": ["pdb_id"],
        "changed_context_items": ["pdb_id_format_contract"], "removed_issue_ids": [REMOVED_ISSUE_ID],
        "remaining_issue_count": result["remaining_issue_count"],
        "rule_dependency_contract_passed_count": sum(row["dependency_contract_passed"] == "true" for row in rules),
        "semantics_complete_rule_count": sum(row["semantics_complete"] == "true" for row in rules),
        "semantics_incomplete_rule_count": sum(row["semantics_complete"] != "true" for row in rules),
        "semantics_complete_field_count": sum(row["implementation_semantics_complete"] == "true" for row in fields),
        "semantics_incomplete_field_count": sum(row["implementation_semantics_complete"] != "true" for row in fields),
        "evaluation_context_item_count": len(contexts),
        "deterministic_now_context_count": sum(row["deterministic_now"] == "true" for row in contexts),
        "deterministic_after_contract_freeze_context_count": sum(row["deterministic_after_contract_freeze"] == "true" for row in contexts),
        "ready_evaluation_context_count": sum(row["implementation_ready"] == "true" for row in contexts),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS], "canonical_mask_task_count": 5,
        "pdb_identifier_semantics_integrated": result["all_checks_passed"], "admit_002_rule_logic_ready": result["all_checks_passed"],
        "ready_for_admission_evaluator_interface_implementation": result["all_checks_passed"],
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "network_access_used_current_step": False, "raw_structure_read_current_step": False,
        "candidate_records_materialized_current_step": False, "download_queue_materialized_current_step": False,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_integration_lineage_checks_passed": result["all_integration_lineage_checks_passed"],
        "all_integrated_rule_checks_passed": result["all_integrated_rule_checks_passed"],
        "all_integrated_field_checks_passed": result["all_integrated_field_checks_passed"],
        "all_integrated_context_checks_passed": result["all_integrated_context_checks_passed"],
        "all_issue_transition_checks_passed": result["all_issue_transition_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"], "all_checks_passed": result["all_checks_passed"],
        "blocking_reasons": [row["issue_id"] for row in issues],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if result["all_checks_passed"] else BLOCKED_NEXT_STEP,
        "non_manifest_output_count": len(CSV_OUTPUTS), "output_file_count": len(CSV_OUTPUTS) + 1,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
    }


def run_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize the deterministic successor overlay without candidate evaluation."""
    result = _build_materialization(_load_source())
    output_sha256 = _write_outputs(output_root, result)
    manifest = _manifest_payload(result, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest

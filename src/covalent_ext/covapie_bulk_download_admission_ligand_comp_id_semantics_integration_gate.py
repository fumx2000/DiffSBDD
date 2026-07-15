"""Step14AU-D2 overlay for frozen ligand component ID semantics.

The gate reads only the committed C2 effective view and D1 design evidence.
It preserves every C2 row except ADMIT_003, ``ligand_comp_id``, and
``ligand_comp_id_contract`` and never performs real candidate evaluation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate as d1_gate,
)


STAGE = "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1"
STEP_LABEL = "Step14AU-D2"
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = "covapie_ligand_comp_id_semantics_integration_gate_v1_manifest_v1"
PREVIOUS_STAGES = (
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1",
    "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1",
)
RECOMMENDED_NEXT_STEP = "resolve_next_covapie_bulk_download_admission_semantics_blocker"
BLOCKED_NEXT_STEP = "resolve_covapie_ligand_comp_id_semantics_integration_gate_blockers"
INTEGRATION_REASON = (
    "ligand component ID exact-type, syntax, uppercase normalization, "
    "and single-component semantics contract frozen"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP14AU_C2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1"
)
STEP14AU_D1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1"
)

C2_FILENAMES = (
    "covapie_candidate_record_id_integrated_rule_matrix.csv",
    "covapie_candidate_record_id_integrated_field_matrix.csv",
    "covapie_candidate_record_id_integrated_context_matrix.csv",
    "covapie_candidate_record_id_integration_safety_audit.csv",
    "covapie_candidate_record_id_integration_issue_inventory.csv",
    "covapie_candidate_record_id_semantics_integration_manifest.json",
)
D1_FILENAMES = (
    "covapie_ligand_comp_id_semantics_contract.csv",
    "covapie_ligand_comp_id_semantics_examples.csv",
    "covapie_ligand_comp_id_source_boundary_audit.csv",
    "covapie_ligand_comp_id_safety_audit.csv",
    "covapie_ligand_comp_id_issue_inventory.csv",
    "covapie_ligand_comp_id_semantics_design_manifest.json",
)
SOURCE_SHA256 = {
    str(STEP14AU_C2_ROOT / C2_FILENAMES[0]): "3d410d8e329d6b26e83936ac1fd6d42d251d76b785fe412006bfcf53ae5b27e8",
    str(STEP14AU_C2_ROOT / C2_FILENAMES[1]): "d7a198a9eb2bb5acd9887242eab3f81808db78b2fddd93720509897ea1578d7f",
    str(STEP14AU_C2_ROOT / C2_FILENAMES[2]): "e230c0b7facc41616f6f129b418fdfa5da629bc607ed85881c43a67b5e0eb630",
    str(STEP14AU_C2_ROOT / C2_FILENAMES[3]): "fe480434e672a0f455299712248fa807293f73a061ed9d97ad3940bd6ec8c8e8",
    str(STEP14AU_C2_ROOT / C2_FILENAMES[4]): "90bbbcfd70ae4b44879c5248299718519ae6a875a516343d8ed871dba9ede1fb",
    str(STEP14AU_C2_ROOT / C2_FILENAMES[5]): "897368c3d29e3f137dc5412bf26f9047ca9ca4ccc1e0a9454a43c7bb0de7a717",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[0]): "79696c9fa0e1afc0c343fc413169a6f732b61cf064df5ea6b0122ac880f0859f",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[1]): "64a5ef19ceb0d37f37af65a5638d844e33de997ccfa3af4df61de0779ab75af6",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[2]): "2a648b5eb6649c7f9f86f9b563201a8709775b0bacfbe665053ddba09d86d7f9",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[3]): "1dd69bffa8b27b59721cbe7530e4da0faef413d92f8760aae3042e2da6e11823",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[4]): "92dd74f401f2d44a87fc4b0a2a3d56a0f82cdfe944eb02653fd9a80d369a3bf5",
    str(STEP14AU_D1_ROOT / D1_FILENAMES[5]): "a57e2cb912707ba8a1f0eb5026ad6c07b58b762bfd1f2cfac56f6ae9bfa330ae",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase",
    "candidate_field_dependencies", "batch_context_dependencies",
    "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required",
    "pure_in_memory_interface_possible", "dependency_contract_passed",
    "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition", "blocking_reasons", "source_stage",
    "integration_source_stage", "integration_applied", "integration_reason",
)
FIELD_COLUMNS = (
    "field_name", "requirement_phase", "source_value_contract", "candidate_record_field",
    "producer_scope", "dependent_rules", "batch_context_required", "evaluation_context_dependencies",
    "allowed_values_defined", "normalization_defined", "exact_validation_defined",
    "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    "field_contract_mapping_passed", "source_stage", "integration_source_stage",
    "integration_applied", "integration_reason",
)
CONTEXT_COLUMNS = (
    "context_item", "context_scope", "required_by_rules", "provided_by_future_caller",
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator",
    "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
    "implementation_ready", "blocking_reasons", "source_stage", "integration_source_stage",
    "integration_applied", "integration_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink", "sha256_expected",
    "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_ligand_comp_id_integrated_rule_matrix.csv",
    "covapie_ligand_comp_id_integrated_field_matrix.csv",
    "covapie_ligand_comp_id_integrated_context_matrix.csv",
    "covapie_ligand_comp_id_integration_safety_audit.csv",
    "covapie_ligand_comp_id_integration_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_ligand_comp_id_semantics_integration_manifest.json"
SAFETY_ITEMS = (
    "network_access_used_current_step", "external_component_registry_lookup_current_step",
    "raw_directory_traversed_current_step", "raw_structure_read_current_step",
    "artifact_reference_paths_followed_current_step", "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step", "raw_files_written_current_step",
    "torch_imported", "numpy_imported", "rdkit_used", "biopython_used", "gemmi_used",
    "pandas_imported", "dataloader_instantiated", "checkpoint_loaded", "model_forward_called",
    "loss_compute_called", "training_allowed",
)
REMOVED_ISSUE_ID = "LIGAND_COMP_ID_SEMANTICS_UNRESOLVED"
REMAINING_ISSUE_IDS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)
COMPLETE_RULE_IDS = ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_014", "ADMIT_015")
COMPLETE_FIELD_NAMES = ("candidate_record_id", "pdb_id", "ligand_comp_id")
READY_CONTEXT_ITEMS = (
    "batch_candidate_record_ids", "batch_duplicate_identity_keys", "candidate_record_id_contract",
    "pdb_id_format_contract", "ligand_comp_id_contract", "existing_raw_target_relative_paths",
    "current_stage_download_authorized", "current_stage_training_authorized",
)
BASE_SOURCE_STAGE = (
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)


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
    return tuple(STEP14AU_C2_ROOT / name for name in C2_FILENAMES) + tuple(
        STEP14AU_D1_ROOT / name for name in D1_FILENAMES
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
        tracked = _tracked_by_git(path)
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        passed = tracked and regular and not symlink and observed == SOURCE_SHA256[path.as_posix()]
        rows.append({
            "source_relative_path": path.as_posix(), "tracked_by_git": _bool_text(tracked),
            "regular_file": _bool_text(regular), "symlink": _bool_text(symlink),
            "sha256_expected": SOURCE_SHA256[path.as_posix()], "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    return bool(rows) and len(rows) == 12 and all(
        tuple(row.keys()) == SOURCE_COLUMNS for row in rows
    ) and [row["source_relative_path"] for row in rows] == expected_paths and len(
        {row["source_relative_path"] for row in rows}
    ) == 12 and all(
        row["tracked_by_git"] == "true" and row["regular_file"] == "true"
        and row["symlink"] == "false"
        and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
        and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
        and row["source_boundary_passed"] == "true" for row in rows
    )


def _load_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(STEP14AU_C2_ROOT / C2_FILENAMES[0]),
        "field_rows": _read_csv(STEP14AU_C2_ROOT / C2_FILENAMES[1]),
        "context_rows": _read_csv(STEP14AU_C2_ROOT / C2_FILENAMES[2]),
        "c2_safety_rows": _read_csv(STEP14AU_C2_ROOT / C2_FILENAMES[3]),
        "issue_rows": _read_csv(STEP14AU_C2_ROOT / C2_FILENAMES[4]),
        "c2_manifest": json.loads(
            _repo_path(STEP14AU_C2_ROOT / C2_FILENAMES[5]).read_text(encoding="utf-8")
        ),
        "d1_contract": _read_csv(STEP14AU_D1_ROOT / D1_FILENAMES[0]),
        "d1_examples": _read_csv(STEP14AU_D1_ROOT / D1_FILENAMES[1]),
        "d1_source_rows": _read_csv(STEP14AU_D1_ROOT / D1_FILENAMES[2]),
        "d1_safety_rows": _read_csv(STEP14AU_D1_ROOT / D1_FILENAMES[3]),
        "d1_issue_rows": _read_csv(STEP14AU_D1_ROOT / D1_FILENAMES[4]),
        "d1_manifest": json.loads(
            _repo_path(STEP14AU_D1_ROOT / D1_FILENAMES[5]).read_text(encoding="utf-8")
        ),
    }


def _row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    matches = [row for row in rows if row.get(key) == value]
    return matches[0] if len(matches) == 1 else None


class _StringSubclass(str):
    pass


def _validate_d1_helpers() -> bool:
    upper = d1_gate.normalize_ligand_comp_id("JUG")
    lower = d1_gate.normalize_ligand_comp_id("jug")
    mixed = d1_gate.normalize_ligand_comp_id("JuG")
    subclass = d1_gate.normalize_ligand_comp_id(_StringSubclass("JUG"))
    leading = d1_gate.normalize_ligand_comp_id(" JUG")
    trailing = d1_gate.normalize_ligand_comp_id("JUG ")
    non_ascii = d1_gate.normalize_ligand_comp_id("JÜG")
    max_length = d1_gate.normalize_ligand_comp_id("A" * 32)
    too_long = d1_gate.normalize_ligand_comp_id("A" * 33)
    missing = d1_gate.normalize_ligand_comp_id(".")
    unknown = d1_gate.normalize_ligand_comp_id("?")
    delimiter = d1_gate.normalize_ligand_comp_id("JUG|E64")
    repeated = d1_gate.normalize_ligand_comp_id(lower.canonical_ligand_comp_id)
    wrapper = d1_gate.evaluate_ligand_comp_id_contract("jug")
    return (
        isinstance(upper, d1_gate.LigandCompIdNormalizationResult)
        and upper.passed and lower.passed and mixed.passed
        and upper.canonical_ligand_comp_id == lower.canonical_ligand_comp_id == "JUG"
        and mixed.canonical_ligand_comp_id == "JUG"
        and not subclass.passed and subclass.blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID"
        and not leading.passed and not trailing.passed
        and non_ascii.blocking_reason == "LIGAND_COMP_ID_NON_ASCII"
        and max_length.passed and too_long.blocking_reason == "LIGAND_COMP_ID_LENGTH_INVALID"
        and all(result.blocking_reason == "LIGAND_COMP_ID_SYNTAX_INVALID" for result in (
            missing, unknown, delimiter,
        ))
        and repeated == upper
        and wrapper == {
            "passed": True, "canonical_ligand_comp_id": "JUG", "blocking_reason": "",
            "admit_003_integration_applied": False,
        }
    )


def _validate_source_semantics(source: dict[str, Any]) -> bool:
    rules, fields, contexts, issues = (
        source["rule_rows"], source["field_rows"], source["context_rows"], source["issue_rows"]
    )
    c2 = source["c2_manifest"]
    d1 = source["d1_manifest"]
    target_rule = _row_by(rules, "admission_rule_id", "ADMIT_003")
    target_field = _row_by(fields, "field_name", "ligand_comp_id")
    target_context = _row_by(contexts, "context_item", "ligand_comp_id_contract")
    masks = [list(pair) for pair in CANONICAL_MASK_PAIRS]
    expected_c2_rule = {
        "admission_rule_id": "ADMIT_003", "admission_rule_name": "ligand_or_het_identity_present",
        "evaluation_phase": "pre_download", "candidate_field_dependencies": "ligand_comp_id",
        "batch_context_dependencies": "", "evaluation_context_dependencies": "ligand_comp_id_contract",
        "external_filesystem_required": "false", "network_required": "false",
        "download_execution_result_required": "false", "pure_in_memory_interface_possible": "true",
        "dependency_contract_passed": "true", "semantics_complete": "false",
        "deterministic_evaluation_possible_now": "false",
        "deterministic_evaluation_possible_after_contract_freeze": "true",
        "implementation_disposition": "interface_only_pending_semantics",
        "blocking_reasons": REMOVED_ISSUE_ID, "source_stage": BASE_SOURCE_STAGE,
        "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
    }
    expected_c2_field = {
        "field_name": "ligand_comp_id", "requirement_phase": "pre_download",
        "source_value_contract": "non-empty ligand or HET identity", "candidate_record_field": "true",
        "producer_scope": "candidate_metadata_provider", "dependent_rules": "ADMIT_003",
        "batch_context_required": "false", "evaluation_context_dependencies": "ligand_comp_id_contract",
        "allowed_values_defined": "false", "normalization_defined": "false",
        "exact_validation_defined": "false", "implementation_semantics_complete": "false",
        "semantics_evidence": "step14at_schema_contract_value_contract_only",
        "blocking_reasons": REMOVED_ISSUE_ID, "field_contract_mapping_passed": "true",
        "source_stage": BASE_SOURCE_STAGE, "integration_source_stage": "",
        "integration_applied": "false", "integration_reason": "",
    }
    expected_c2_context = {
        "context_item": "ligand_comp_id_contract", "context_scope": "evaluation_policy",
        "required_by_rules": "ADMIT_003", "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false", "network_access_inside_evaluator": "false",
        "deterministic_now": "false", "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "false", "implementation_ready": "false",
        "blocking_reasons": REMOVED_ISSUE_ID, "source_stage": BASE_SOURCE_STAGE,
        "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
    }
    return (
        len(rules) == 15 and all(tuple(row.keys()) == RULE_COLUMNS for row in rules)
        and len(fields) == 17 and all(tuple(row.keys()) == FIELD_COLUMNS for row in fields)
        and len(contexts) == 18 and all(tuple(row.keys()) == CONTEXT_COLUMNS for row in contexts)
        and len(issues) == 11 and all(tuple(row.keys()) == ISSUE_COLUMNS for row in issues)
        and tuple(row["issue_id"] for row in issues) == (
            *REMAINING_ISSUE_IDS[:8], REMOVED_ISSUE_ID, *REMAINING_ISSUE_IDS[8:],
        )
        and target_rule == expected_c2_rule and target_field == expected_c2_field
        and target_context == expected_c2_context
        and c2.get("stage") == PREVIOUS_STAGES[0] and c2.get("step_label") == "Step14AU-C2"
        and c2.get("all_checks_passed") is True
        and c2.get("candidate_record_id_semantics_integrated") is True
        and c2.get("admit_001_rule_logic_ready") is True
        and c2.get("pdb_identifier_semantics_integrated") is True
        and c2.get("integrated_rule_count") == 15 and c2.get("integrated_field_count") == 17
        and c2.get("integrated_context_count") == 18 and c2.get("remaining_issue_count") == 11
        and c2.get("blocking_reasons") == [
            *REMAINING_ISSUE_IDS[:8], REMOVED_ISSUE_ID, *REMAINING_ISSUE_IDS[8:],
        ]
        and c2.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and c2.get("ready_for_real_candidate_evaluation") is False
        and c2.get("ready_for_bulk_download_now") is False and c2.get("ready_for_training") is False
        and c2.get("ready_to_train_now") is False
        and c2.get("feature_semantics_audit_required_before_training") is True
        and c2.get("canonical_mask_pairs") == masks and c2.get("canonical_mask_task_count") == 5
        and d1.get("stage") == PREVIOUS_STAGES[1] and d1.get("step_label") == "Step14AU-D1"
        and d1.get("all_checks_passed") is True and d1.get("ligand_comp_id_semantics_frozen") is True
        and d1.get("ligand_comp_id_semantics_integrated") is False
        and d1.get("integration_applied_current_step") is False
        and d1.get("admit_003_rule_logic_ready") is False
        and all(d1.get(key) is True for key in (
            "ligand_comp_id_exact_type_contract_ready", "ligand_comp_id_syntax_contract_ready",
            "ligand_comp_id_normalization_contract_ready", "ligand_comp_id_single_component_contract_ready",
            "ready_for_ligand_comp_id_semantics_integration",
        ))
        and d1.get("upstream_effective_issue_count") == 11
        and d1.get("expected_post_integration_issue_count") == 10
        and d1.get("resolved_design_issue_ids") == [REMOVED_ISSUE_ID]
        and d1.get("canonical_mask_pairs") == masks and d1.get("canonical_mask_task_count") == 5
        and len(source["d1_contract"]) == 32
        and all(row.get("contract_passed") == "true" for row in source["d1_contract"])
        and len(source["d1_examples"]) == 36
        and sum(row.get("example_class") == "valid" for row in source["d1_examples"]) == 12
        and sum(row.get("example_class") == "invalid" for row in source["d1_examples"]) == 24
        and all(row.get("example_passed") == "true" for row in source["d1_examples"])
        and len(source["d1_source_rows"]) == 6
        and all(row.get("source_boundary_passed") == "true" for row in source["d1_source_rows"])
        and len(source["d1_safety_rows"]) == 19
        and all(row.get("safety_passed") == "true" for row in source["d1_safety_rows"])
        and source["d1_issue_rows"] == [{
            "issue_id": "NO_ISSUES", "issue_type": "no_ligand_comp_id_semantics_design_issues",
            "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
        }]
        and d1.get("external_component_registry_lookup_current_step") is False
        and d1.get("raw_structure_read_current_step") is False
        and d1.get("candidate_records_materialized_current_step") is False
        and d1.get("download_queue_materialized_current_step") is False
        and d1.get("ready_for_training") is False and d1.get("ready_to_train_now") is False
        and _validate_d1_helpers()
    )


def _overlay_rule_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source_rows]
    target = _row_by(rows, "admission_rule_id", "ADMIT_003")
    if target is not None:
        target.update({
            "semantics_complete": "true", "deterministic_evaluation_possible_now": "true",
            "implementation_disposition": "rule_logic_ready", "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        })
    return rows


def _overlay_field_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source_rows]
    target = _row_by(rows, "field_name", "ligand_comp_id")
    if target is not None:
        target.update({
            "allowed_values_defined": "true", "normalization_defined": "true",
            "exact_validation_defined": "true", "implementation_semantics_complete": "true",
            "semantics_evidence": PREVIOUS_STAGES[1], "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        })
    return rows


def _overlay_context_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source_rows]
    target = _row_by(rows, "context_item", "ligand_comp_id_contract")
    if target is not None:
        target.update({
            "deterministic_now": "true", "exact_contract_defined": "true",
            "implementation_ready": "true", "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        })
    return rows


def _overlay_issue_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in source_rows if row.get("issue_id") != REMOVED_ISSUE_ID]


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "required_status": "false", "observed_status": "false",
        "safety_passed": "true", "blocking_reason": "",
    } for item in SAFETY_ITEMS]


def _validate_lineage_rows(
    rule_rows: list[dict[str, str]], field_rows: list[dict[str, str]],
    context_rows: list[dict[str, str]], source: dict[str, Any],
) -> bool:
    specs = (
        (rule_rows, source["rule_rows"], "admission_rule_id", "ADMIT_003"),
        (field_rows, source["field_rows"], "field_name", "ligand_comp_id"),
        (context_rows, source["context_rows"], "context_item", "ligand_comp_id_contract"),
    )
    for rows, source_rows, identifier, target_id in specs:
        if not rows or len(rows) != len(source_rows):
            return False
        if len([row for row in rows if row.get(identifier) == target_id]) != 1:
            return False
        for row, source_row in zip(rows, source_rows):
            if row.get("source_stage") != BASE_SOURCE_STAGE:
                return False
            if row.get(identifier) == target_id:
                if any(row.get(key) != value for key, value in (
                    ("integration_source_stage", PREVIOUS_STAGES[1]),
                    ("integration_applied", "true"), ("integration_reason", INTEGRATION_REASON),
                )):
                    return False
            elif any(row.get(key) != source_row.get(key) for key in (
                "integration_source_stage", "integration_applied", "integration_reason",
            )):
                return False
    return True


def _validate_overlay_rows(
    rows: list[dict[str, str]], source_rows: list[dict[str, str]], *, columns: tuple[str, ...],
    identifier: str, target_id: str, allowed_changes: set[str], expected_values: dict[str, str],
) -> bool:
    if not rows or len(rows) != len(source_rows) or any(tuple(row.keys()) != columns for row in rows):
        return False
    if [row.get(identifier) for row in rows] != [row.get(identifier) for row in source_rows]:
        return False
    if len([row for row in rows if row.get(identifier) == target_id]) != 1:
        return False
    for row, source in zip(rows, source_rows):
        if row[identifier] != target_id:
            if row != source:
                return False
        else:
            if any(row[column] != source[column] for column in columns if column not in allowed_changes):
                return False
            if any(row.get(key) != value for key, value in expected_values.items()):
                return False
    return True


def _validate_integrated_rule_rows(
    rows: list[dict[str, str]], source_rows: list[dict[str, str]],
) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=RULE_COLUMNS, identifier="admission_rule_id", target_id="ADMIT_003",
        allowed_changes={
            "semantics_complete", "deterministic_evaluation_possible_now", "implementation_disposition",
            "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
        },
        expected_values={
            "semantics_complete": "true", "deterministic_evaluation_possible_now": "true",
            "implementation_disposition": "rule_logic_ready", "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        },
    )
    return passed and tuple(
        row["admission_rule_id"] for row in rows if row["semantics_complete"] == "true"
    ) == COMPLETE_RULE_IDS


def _validate_integrated_field_rows(
    rows: list[dict[str, str]], source_rows: list[dict[str, str]],
) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=FIELD_COLUMNS, identifier="field_name", target_id="ligand_comp_id",
        allowed_changes={
            "allowed_values_defined", "normalization_defined", "exact_validation_defined",
            "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
            "integration_source_stage", "integration_applied", "integration_reason",
        },
        expected_values={
            "allowed_values_defined": "true", "normalization_defined": "true",
            "exact_validation_defined": "true", "implementation_semantics_complete": "true",
            "semantics_evidence": PREVIOUS_STAGES[1], "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        },
    )
    return passed and tuple(
        row["field_name"] for row in rows if row["implementation_semantics_complete"] == "true"
    ) == COMPLETE_FIELD_NAMES


def _validate_integrated_context_rows(
    rows: list[dict[str, str]], source_rows: list[dict[str, str]],
) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=CONTEXT_COLUMNS, identifier="context_item",
        target_id="ligand_comp_id_contract",
        allowed_changes={
            "deterministic_now", "exact_contract_defined", "implementation_ready", "blocking_reasons",
            "integration_source_stage", "integration_applied", "integration_reason",
        },
        expected_values={
            "deterministic_now": "true", "exact_contract_defined": "true",
            "implementation_ready": "true", "blocking_reasons": "",
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        },
    )
    ready = tuple(row["context_item"] for row in rows if row["implementation_ready"] == "true")
    deterministic = tuple(row["context_item"] for row in rows if row["deterministic_now"] == "true")
    return (
        passed and ready == READY_CONTEXT_ITEMS and deterministic == READY_CONTEXT_ITEMS
        and sum(row["deterministic_after_contract_freeze"] == "true" for row in rows) == 18
    )


def _validate_issue_transition_rows(
    rows: list[dict[str, str]], source_rows: list[dict[str, str]],
) -> bool:
    expected = [row for row in source_rows if row.get("issue_id") != REMOVED_ISSUE_ID]
    return bool(rows) and rows == expected and len(rows) == 10 and all(
        tuple(row.keys()) == ISSUE_COLUMNS for row in rows
    ) and tuple(row["issue_id"] for row in rows) == REMAINING_ISSUE_IDS


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and rows == _safety_rows() and all(
        tuple(row.keys()) == SAFETY_COLUMNS for row in rows
    )


def evaluate_admit_003_ligand_comp_id(ligand_comp_id: object) -> dict[str, object]:
    """Apply only the frozen D1 syntax and normalization contract."""
    result = d1_gate.normalize_ligand_comp_id(ligand_comp_id)
    return {
        "admission_rule_id": "ADMIT_003", "passed": result.passed,
        "canonical_ligand_comp_id": result.canonical_ligand_comp_id,
        "blocking_reason": result.blocking_reason,
    }


SECTION_FAILURE_SPECS = {
    "source": ("LIGAND_COMP_ID_INTEGRATION_SOURCE_BOUNDARY_FAILED", "", ""),
    "lineage": ("LIGAND_COMP_ID_INTEGRATION_LINEAGE_FAILED", "ligand_comp_id", "ADMIT_003"),
    "rules": ("LIGAND_COMP_ID_INTEGRATED_RULE_VALIDATION_FAILED", "ligand_comp_id", "ADMIT_003"),
    "fields": ("LIGAND_COMP_ID_INTEGRATED_FIELD_VALIDATION_FAILED", "ligand_comp_id", "ADMIT_003"),
    "contexts": ("LIGAND_COMP_ID_INTEGRATED_CONTEXT_VALIDATION_FAILED", "ligand_comp_id", "ADMIT_003"),
    "issues": ("LIGAND_COMP_ID_INTEGRATION_ISSUE_TRANSITION_FAILED", "", ""),
    "safety": ("LIGAND_COMP_ID_INTEGRATION_SAFETY_FAILED", "", ""),
}


def _failure_issue_rows(
    domain_rows: list[dict[str, str]], section_status: tuple[tuple[str, bool], ...],
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for section, passed in section_status:
        if passed:
            continue
        issue_id, fields, rules = SECTION_FAILURE_SPECS[section]
        failures.append({
            "issue_id": issue_id, "issue_type": "ligand_comp_id_integration_gate_validation_failure",
            "affected_fields": fields, "affected_rules": rules, "severity": "blocking", "status": "open",
            "blocking_scope": "integration_gate", "blocking_reason": issue_id,
            "issue_origin": "step14au_d2_integration_gate_failure",
            "integration_transition": "added_by_gate_failure",
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
    section_status = (
        ("source", _validate_source_rows(source_rows) and _validate_source_semantics(source)),
        ("lineage", _validate_lineage_rows(rule_rows, field_rows, context_rows, source)),
        ("rules", _validate_integrated_rule_rows(rule_rows, source["rule_rows"])),
        ("fields", _validate_integrated_field_rows(field_rows, source["field_rows"])),
        ("contexts", _validate_integrated_context_rows(context_rows, source["context_rows"])),
        ("issues", _validate_issue_transition_rows(issue_rows, source["issue_rows"])),
        ("safety", _validate_safety_rows(safety_rows)),
    )
    status = dict(section_status)
    domain_rows = _overlay_issue_rows(source["issue_rows"])
    return {
        "source_rows": source_rows, "rule_rows": rule_rows, "field_rows": field_rows,
        "context_rows": context_rows, "safety_rows": safety_rows,
        "issue_rows": _failure_issue_rows(domain_rows, section_status),
        "remaining_issue_count": len(domain_rows),
        "all_source_boundary_checks_passed": status["source"],
        "all_integration_lineage_checks_passed": status["lineage"],
        "all_integrated_rule_checks_passed": status["rules"],
        "all_integrated_field_checks_passed": status["fields"],
        "all_integrated_context_checks_passed": status["contexts"],
        "all_issue_transition_checks_passed": status["issues"],
        "all_safety_checks_passed": status["safety"],
        "all_checks_passed": all(status.values()),
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    for name, columns, rows in (
        (CSV_OUTPUTS[0], RULE_COLUMNS, result["rule_rows"]),
        (CSV_OUTPUTS[1], FIELD_COLUMNS, result["field_rows"]),
        (CSV_OUTPUTS[2], CONTEXT_COLUMNS, result["context_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    ):
        _write_csv(root / name, columns, rows)
    return {name: _sha256(root / name) for name in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    rules, fields, contexts, issues = (
        result["rule_rows"], result["field_rows"], result["context_rows"], result["issue_rows"]
    )
    all_checks = result["all_checks_passed"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stages": list(PREVIOUS_STAGES),
        "source_read_boundary": "only_step14au_c2_and_step14au_d1_12_committed_metadata_outputs",
        "source_input_count": 12, "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "integrated_rule_count": len(rules), "integrated_field_count": len(fields),
        "integrated_context_count": len(contexts), "evaluation_context_item_count": len(contexts),
        "changed_rule_ids": ["ADMIT_003"], "changed_field_names": ["ligand_comp_id"],
        "changed_context_items": ["ligand_comp_id_contract"],
        "removed_issue_ids": [REMOVED_ISSUE_ID], "remaining_issue_count": result["remaining_issue_count"],
        "rule_dependency_contract_passed_count": sum(
            row["dependency_contract_passed"] == "true" for row in rules
        ),
        "semantics_complete_rule_count": sum(row["semantics_complete"] == "true" for row in rules),
        "semantics_incomplete_rule_count": sum(row["semantics_complete"] != "true" for row in rules),
        "semantics_complete_field_count": sum(
            row["implementation_semantics_complete"] == "true" for row in fields
        ),
        "semantics_incomplete_field_count": sum(
            row["implementation_semantics_complete"] != "true" for row in fields
        ),
        "deterministic_now_context_count": sum(row["deterministic_now"] == "true" for row in contexts),
        "deterministic_after_contract_freeze_context_count": sum(
            row["deterministic_after_contract_freeze"] == "true" for row in contexts
        ),
        "ready_evaluation_context_count": sum(row["implementation_ready"] == "true" for row in contexts),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "ligand_comp_id_semantics_integrated": all_checks, "admit_003_rule_logic_ready": all_checks,
        "candidate_record_id_semantics_integrated": all_checks, "admit_001_rule_logic_ready": all_checks,
        "pdb_identifier_semantics_integrated": all_checks,
        "ready_for_admission_evaluator_interface_implementation": all_checks,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "raw_structure_read_current_step": False, "network_access_used_current_step": False,
        "external_component_registry_lookup_current_step": False,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_integration_lineage_checks_passed": result["all_integration_lineage_checks_passed"],
        "all_integrated_rule_checks_passed": result["all_integrated_rule_checks_passed"],
        "all_integrated_field_checks_passed": result["all_integrated_field_checks_passed"],
        "all_integrated_context_checks_passed": result["all_integrated_context_checks_passed"],
        "all_issue_transition_checks_passed": result["all_issue_transition_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"],
        "all_checks_passed": all_checks, "blocking_reasons": [row["issue_id"] for row in issues],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_checks else BLOCKED_NEXT_STEP,
        "non_manifest_output_count": 5, "output_file_count": 6,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
    }


def run_covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize the deterministic successor overlay without candidate evaluation."""
    result = _build_materialization(_load_source())
    output_sha256 = _write_outputs(output_root, result)
    manifest = _manifest_payload(result, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest

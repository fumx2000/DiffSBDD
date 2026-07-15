"""Read-only Step14AU-C2 overlay for frozen candidate record ID semantics.

This successor view never rewrites the Step14AU-B2 or Step14AU-C1 outputs.
It copies B2 metadata rows and applies the already-frozen C1 contract only to
ADMIT_001, ``candidate_record_id``, and ``candidate_record_id_contract``.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_bulk_download_admission_candidate_record_id_semantics_design_gate as c1_gate,
)


STAGE = "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1"
STEP_LABEL = "Step14AU-C2"
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = "covapie_candidate_record_id_semantics_integration_gate_v1_manifest_v1"
PREVIOUS_STAGES = (
    "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1",
    "covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1",
)
RECOMMENDED_NEXT_STEP = "resolve_next_covapie_bulk_download_admission_semantics_blocker"
BLOCKED_NEXT_STEP = "resolve_covapie_candidate_record_id_semantics_integration_gate_blockers"

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP14AU_B2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1"
)
STEP14AU_C1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1"
)

B2_FILENAMES = (
    "covapie_pdb_identifier_integrated_rule_matrix.csv",
    "covapie_pdb_identifier_integrated_field_matrix.csv",
    "covapie_pdb_identifier_integrated_context_matrix.csv",
    "covapie_pdb_identifier_integration_safety_audit.csv",
    "covapie_pdb_identifier_integration_issue_inventory.csv",
    "covapie_pdb_identifier_semantics_integration_manifest.json",
)
C1_FILENAMES = (
    "covapie_candidate_record_id_semantics_contract.csv",
    "covapie_candidate_record_id_semantics_examples.csv",
    "covapie_candidate_record_id_source_boundary_audit.csv",
    "covapie_candidate_record_id_safety_audit.csv",
    "covapie_candidate_record_id_issue_inventory.csv",
    "covapie_candidate_record_id_semantics_design_manifest.json",
)
SOURCE_SHA256 = {
    str(STEP14AU_B2_ROOT / B2_FILENAMES[0]): "99e3a4c8c127af4ac900343a90dfd2eebde73a2f75e9c1a3b27782144858e317",
    str(STEP14AU_B2_ROOT / B2_FILENAMES[1]): "56388107014e0295c3124bac4660280ff41393e8a8cb6ffa1b50e4028be3c8da",
    str(STEP14AU_B2_ROOT / B2_FILENAMES[2]): "dc816f74777a5cdced360048ac1cfdc27f711132868f04204d122c9d8f54c5af",
    str(STEP14AU_B2_ROOT / B2_FILENAMES[3]): "fe480434e672a0f455299712248fa807293f73a061ed9d97ad3940bd6ec8c8e8",
    str(STEP14AU_B2_ROOT / B2_FILENAMES[4]): "8857f22fda3ce281dab13772ee322e9c1af838d7895e410d19084731f9637a21",
    str(STEP14AU_B2_ROOT / B2_FILENAMES[5]): "abbcbb129c8c26c5bcc6436e69ae55c56ff75bd2742d816ca805ab26a9258865",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[0]): "92f624705a611c0dac011229d13d6a3ba87fc1ab7a3e0bc9c090952a0838b318",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[1]): "1654d36a42cd405866ed152750508dbc46ed78371b7ebb25e47e8bfe9c8bbb9e",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[2]): "2c038fdcc748410991183829aa8c1725a7145439fe0da8d4abd467645b2c6e01",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[3]): "32c1e319bf2d81cae5217ac4a83822244c98cad6f5b5655eed54a52a07de4e3b",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[4]): "83af7cc18e67d28a7fb56e8b9bbe92c4ff09f6c822b439298534047104bde99e",
    str(STEP14AU_C1_ROOT / C1_FILENAMES[5]): "9649265b413b5c2641a0fd0a51fc85ba5dc19bd76f6932d507293fca1e3d3ced",
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
SAFETY_COLUMNS = ("safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason")
CSV_OUTPUTS = (
    "covapie_candidate_record_id_integrated_rule_matrix.csv",
    "covapie_candidate_record_id_integrated_field_matrix.csv",
    "covapie_candidate_record_id_integrated_context_matrix.csv",
    "covapie_candidate_record_id_integration_safety_audit.csv",
    "covapie_candidate_record_id_integration_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_candidate_record_id_semantics_integration_manifest.json"
SAFETY_ITEMS = (
    "network_access_used_current_step", "raw_directory_traversed_current_step",
    "artifact_reference_paths_followed_current_step", "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step", "raw_files_written_current_step",
    "torch_imported", "numpy_imported", "rdkit_used", "biopython_used", "gemmi_used",
    "dataloader_instantiated", "checkpoint_loaded", "model_forward_called", "loss_compute_called",
    "training_allowed",
)
REMOVED_ISSUE_ID = "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"
REMAINING_ISSUE_IDS = (
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
COMPLETE_RULE_IDS = ("ADMIT_001", "ADMIT_002", "ADMIT_014", "ADMIT_015")
COMPLETE_FIELD_NAMES = ("candidate_record_id", "pdb_id")
READY_CONTEXT_ITEMS = (
    "batch_candidate_record_ids", "batch_duplicate_identity_keys", "candidate_record_id_contract",
    "pdb_id_format_contract", "existing_raw_target_relative_paths",
    "current_stage_download_authorized", "current_stage_training_authorized",
)
INTEGRATION_REASON = "candidate record ID syntax and batch uniqueness semantics contract frozen"
B2_SOURCE_STAGE = (
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
B1_INTEGRATION_STAGE = "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1"
B1_INTEGRATION_REASON = "PDB identifier semantics contract frozen"


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
    return tuple(STEP14AU_B2_ROOT / name for name in B2_FILENAMES) + tuple(
        STEP14AU_C1_ROOT / name for name in C1_FILENAMES
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
    return bool(rows) and (
        len(rows) == 12
        and all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == 12
        and all(
            row["tracked_by_git"] == "true" and row["regular_file"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true"
            for row in rows
        )
    )


def _load_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(STEP14AU_B2_ROOT / B2_FILENAMES[0]),
        "field_rows": _read_csv(STEP14AU_B2_ROOT / B2_FILENAMES[1]),
        "context_rows": _read_csv(STEP14AU_B2_ROOT / B2_FILENAMES[2]),
        "b2_safety_rows": _read_csv(STEP14AU_B2_ROOT / B2_FILENAMES[3]),
        "issue_rows": _read_csv(STEP14AU_B2_ROOT / B2_FILENAMES[4]),
        "b2_manifest": json.loads(_repo_path(STEP14AU_B2_ROOT / B2_FILENAMES[5]).read_text(encoding="utf-8")),
        "c1_contract": _read_csv(STEP14AU_C1_ROOT / C1_FILENAMES[0]),
        "c1_examples": _read_csv(STEP14AU_C1_ROOT / C1_FILENAMES[1]),
        "c1_source_rows": _read_csv(STEP14AU_C1_ROOT / C1_FILENAMES[2]),
        "c1_safety_rows": _read_csv(STEP14AU_C1_ROOT / C1_FILENAMES[3]),
        "c1_issue_rows": _read_csv(STEP14AU_C1_ROOT / C1_FILENAMES[4]),
        "c1_manifest": json.loads(_repo_path(STEP14AU_C1_ROOT / C1_FILENAMES[5]).read_text(encoding="utf-8")),
    }


def _row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    matches = [row for row in rows if row.get(key) == value]
    return matches[0] if len(matches) == 1 else None


def _validate_c1_helpers() -> bool:
    valid = c1_gate.normalize_candidate_record_id("HR_0002")
    leading = c1_gate.normalize_candidate_record_id(" HR_0002")
    upper = c1_gate.normalize_candidate_record_id("ABC")
    lower = c1_gate.normalize_candidate_record_id("abc")
    unique = c1_gate.evaluate_candidate_record_id_batch_uniqueness(
        "HR_0002", ["HR_0002", "HR_0003"]
    )
    tuple_batch = c1_gate.evaluate_candidate_record_id_batch_uniqueness(
        "HR_0002", ("HR_0002", "HR_0003")
    )
    duplicate = c1_gate.evaluate_candidate_record_id_batch_uniqueness(
        "HR_0002", ["HR_0002", "HR_0002"]
    )
    missing = c1_gate.evaluate_candidate_record_id_batch_uniqueness("HR_0002", ["HR_0003"])
    invalid = c1_gate.evaluate_candidate_record_id_batch_uniqueness(
        "HR_0002", ["HR_0002", " bad"]
    )
    wrong_type = c1_gate.evaluate_candidate_record_id_batch_uniqueness("HR_0002", {"HR_0002"})
    return (
        isinstance(valid, c1_gate.CandidateRecordIdNormalizationResult)
        and valid.syntax_valid and valid.canonical_candidate_record_id == "HR_0002"
        and not leading.syntax_valid
        and upper.syntax_valid and lower.syntax_valid
        and upper.canonical_candidate_record_id != lower.canonical_candidate_record_id
        and isinstance(unique, c1_gate.CandidateRecordIdBatchEvaluationResult)
        and unique.passed and tuple_batch.passed
        and not duplicate.passed and not missing.passed
        and not invalid.passed and not wrong_type.passed
    )


def _validate_source_semantics(source: dict[str, Any]) -> bool:
    rules, fields, contexts, issues = (
        source["rule_rows"], source["field_rows"], source["context_rows"], source["issue_rows"]
    )
    b2 = source["b2_manifest"]
    c1 = source["c1_manifest"]
    target_rule = _row_by(rules, "admission_rule_id", "ADMIT_001")
    target_field = _row_by(fields, "field_name", "candidate_record_id")
    target_context = _row_by(contexts, "context_item", "candidate_record_id_contract")
    expected_masks = [list(pair) for pair in CANONICAL_MASK_PAIRS]
    return (
        len(rules) == 15 and all(tuple(row.keys()) == RULE_COLUMNS for row in rules)
        and len(fields) == 17 and all(tuple(row.keys()) == FIELD_COLUMNS for row in fields)
        and len(contexts) == 18 and all(tuple(row.keys()) == CONTEXT_COLUMNS for row in contexts)
        and len(issues) == 12 and all(tuple(row.keys()) == ISSUE_COLUMNS for row in issues)
        and [row["issue_id"] for row in issues] == [REMOVED_ISSUE_ID, *REMAINING_ISSUE_IDS]
        and b2.get("stage") == PREVIOUS_STAGES[0] and b2.get("step_label") == "Step14AU-B2"
        and b2.get("all_checks_passed") is True and b2.get("pdb_identifier_semantics_integrated") is True
        and b2.get("integrated_rule_count") == 15 and b2.get("integrated_field_count") == 17
        and b2.get("integrated_context_count") == 18 and b2.get("remaining_issue_count") == 12
        and b2.get("blocking_reasons") == [REMOVED_ISSUE_ID, *REMAINING_ISSUE_IDS]
        and b2.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and b2.get("ready_for_real_candidate_evaluation") is False
        and b2.get("ready_for_bulk_download_now") is False
        and b2.get("ready_for_training") is False and b2.get("ready_to_train_now") is False
        and b2.get("canonical_mask_pairs") == expected_masks and b2.get("canonical_mask_task_count") == 5
        and target_rule is not None
        and target_rule["candidate_field_dependencies"] == "candidate_record_id"
        and target_rule["batch_context_dependencies"] == "batch_candidate_record_ids"
        and target_rule["evaluation_context_dependencies"] == "candidate_record_id_contract"
        and target_rule["dependency_contract_passed"] == "true"
        and target_rule["semantics_complete"] == "false"
        and target_rule["deterministic_evaluation_possible_now"] == "false"
        and target_rule["deterministic_evaluation_possible_after_contract_freeze"] == "true"
        and target_rule["implementation_disposition"] == "interface_only_pending_semantics"
        and target_rule["blocking_reasons"] == REMOVED_ISSUE_ID
        and target_rule["integration_applied"] == "false"
        and target_field is not None and target_field["candidate_record_field"] == "true"
        and target_field["dependent_rules"] == "ADMIT_001" and target_field["batch_context_required"] == "true"
        and target_field["evaluation_context_dependencies"] == "candidate_record_id_contract"
        and all(target_field[key] == "false" for key in (
            "allowed_values_defined", "normalization_defined", "exact_validation_defined",
            "implementation_semantics_complete",
        ))
        and target_field["blocking_reasons"] == REMOVED_ISSUE_ID and target_field["integration_applied"] == "false"
        and target_context is not None and target_context["required_by_rules"] == "ADMIT_001"
        and target_context["provided_by_future_caller"] == "true"
        and target_context["deterministic_now"] == "false"
        and target_context["deterministic_after_contract_freeze"] == "true"
        and target_context["exact_contract_defined"] == "false"
        and target_context["implementation_ready"] == "false"
        and target_context["blocking_reasons"] == REMOVED_ISSUE_ID
        and target_context["integration_applied"] == "false"
        and c1.get("stage") == PREVIOUS_STAGES[1] and c1.get("step_label") == "Step14AU-C1"
        and c1.get("all_checks_passed") is True
        and c1.get("candidate_record_id_semantics_frozen") is True
        and c1.get("candidate_record_id_semantics_integrated") is False
        and c1.get("integration_applied_current_step") is False and c1.get("admit_001_rule_logic_ready") is False
        and c1.get("candidate_record_id_syntax_contract_ready") is True
        and c1.get("candidate_record_id_batch_uniqueness_contract_ready") is True
        and c1.get("ready_for_candidate_record_id_semantics_integration") is True
        and c1.get("upstream_effective_issue_count") == 12
        and c1.get("expected_post_integration_issue_count") == 11
        and c1.get("resolved_design_issue_ids") == [REMOVED_ISSUE_ID]
        and len(source["c1_contract"]) == 30 and len(source["c1_examples"]) == 50
        and all(row.get("example_passed") == "true" for row in source["c1_examples"])
        and len(source["c1_source_rows"]) == 6
        and all(row.get("source_boundary_passed") == "true" for row in source["c1_source_rows"])
        and len(source["c1_safety_rows"]) == 19
        and all(row.get("safety_passed") == "true" for row in source["c1_safety_rows"])
        and source["c1_issue_rows"] == [{
            "issue_id": "NO_ISSUES", "issue_type": "no_candidate_record_id_semantics_design_issues",
            "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
        }]
        and c1.get("ready_for_real_candidate_evaluation") is False
        and c1.get("ready_for_bulk_download_now") is False
        and c1.get("ready_for_training") is False and c1.get("ready_to_train_now") is False
        and c1.get("canonical_mask_pairs") == expected_masks and c1.get("canonical_mask_task_count") == 5
        and _validate_c1_helpers()
    )


def _overlay_rule_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source_rows]
    target = _row_by(rows, "admission_rule_id", "ADMIT_001")
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
    target = _row_by(rows, "field_name", "candidate_record_id")
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
    target = _row_by(rows, "context_item", "candidate_record_id_contract")
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
    rule_rows: list[dict[str, str]], field_rows: list[dict[str, str]], context_rows: list[dict[str, str]],
) -> bool:
    expected = (
        (rule_rows, "admission_rule_id", "ADMIT_001", "ADMIT_002"),
        (field_rows, "field_name", "candidate_record_id", "pdb_id"),
        (context_rows, "context_item", "candidate_record_id_contract", "pdb_id_format_contract"),
    )
    for rows, identifier, integrated_id, b1_integrated_id in expected:
        if not rows:
            return False
        if len([row for row in rows if row.get(identifier) == integrated_id]) != 1:
            return False
        for row in rows:
            if row.get("source_stage") != B2_SOURCE_STAGE:
                return False
            if row.get(identifier) == integrated_id:
                if row.get("integration_source_stage") != PREVIOUS_STAGES[1]:
                    return False
                if row.get("integration_applied") != "true" or row.get("integration_reason") != INTEGRATION_REASON:
                    return False
            elif row.get(identifier) == b1_integrated_id:
                if row.get("integration_source_stage") != B1_INTEGRATION_STAGE:
                    return False
                if row.get("integration_applied") != "true" or row.get("integration_reason") != B1_INTEGRATION_REASON:
                    return False
            elif any(row.get(key) != value for key, value in (
                ("integration_source_stage", ""), ("integration_applied", "false"),
                ("integration_reason", ""),
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


def _validate_integrated_rule_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=RULE_COLUMNS, identifier="admission_rule_id", target_id="ADMIT_001",
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
    return passed and tuple(row["admission_rule_id"] for row in rows if row["semantics_complete"] == "true") == COMPLETE_RULE_IDS


def _validate_integrated_field_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=FIELD_COLUMNS, identifier="field_name", target_id="candidate_record_id",
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


def _validate_integrated_context_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    passed = _validate_overlay_rows(
        rows, source_rows, columns=CONTEXT_COLUMNS, identifier="context_item",
        target_id="candidate_record_id_contract",
        allowed_changes={
            "deterministic_now", "exact_contract_defined", "implementation_ready", "blocking_reasons",
            "integration_source_stage", "integration_applied", "integration_reason",
        },
        expected_values={
            "deterministic_now": "true", "exact_contract_defined": "true", "implementation_ready": "true",
            "blocking_reasons": "", "integration_source_stage": PREVIOUS_STAGES[1],
            "integration_applied": "true", "integration_reason": INTEGRATION_REASON,
        },
    )
    ready = tuple(row["context_item"] for row in rows if row["implementation_ready"] == "true")
    deterministic = tuple(row["context_item"] for row in rows if row["deterministic_now"] == "true")
    return (
        passed and ready == READY_CONTEXT_ITEMS and deterministic == READY_CONTEXT_ITEMS
        and sum(row["deterministic_after_contract_freeze"] == "true" for row in rows) == 18
    )


def _validate_issue_transition_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    expected = [row for row in source_rows if row.get("issue_id") != REMOVED_ISSUE_ID]
    return bool(rows) and rows == expected and len(rows) == 11 and all(
        tuple(row.keys()) == ISSUE_COLUMNS for row in rows
    ) and tuple(row["issue_id"] for row in rows) == REMAINING_ISSUE_IDS


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and rows == _safety_rows() and all(tuple(row.keys()) == SAFETY_COLUMNS for row in rows)


def evaluate_admit_001_candidate_record_id(
    candidate_record_id: object, batch_candidate_record_ids: object,
) -> dict[str, object]:
    """Apply only the frozen C1 syntax and batch uniqueness contract."""
    result = c1_gate.evaluate_candidate_record_id_batch_uniqueness(
        candidate_record_id, batch_candidate_record_ids
    )
    normalized = c1_gate.normalize_candidate_record_id(candidate_record_id)
    return {
        "admission_rule_id": "ADMIT_001", "passed": result.passed,
        "normalized_candidate_record_id": normalized.canonical_candidate_record_id,
        "blocking_reason": result.blocking_reason,
    }


SECTION_FAILURE_SPECS = {
    "source": ("CANDIDATE_RECORD_ID_INTEGRATION_SOURCE_BOUNDARY_FAILED", "", ""),
    "lineage": ("CANDIDATE_RECORD_ID_INTEGRATION_LINEAGE_FAILED", "candidate_record_id", "ADMIT_001"),
    "rules": ("CANDIDATE_RECORD_ID_INTEGRATED_RULE_VALIDATION_FAILED", "candidate_record_id", "ADMIT_001"),
    "fields": ("CANDIDATE_RECORD_ID_INTEGRATED_FIELD_VALIDATION_FAILED", "candidate_record_id", "ADMIT_001"),
    "contexts": ("CANDIDATE_RECORD_ID_INTEGRATED_CONTEXT_VALIDATION_FAILED", "candidate_record_id", "ADMIT_001"),
    "issues": ("CANDIDATE_RECORD_ID_INTEGRATION_ISSUE_TRANSITION_FAILED", "", ""),
    "safety": ("CANDIDATE_RECORD_ID_INTEGRATION_SAFETY_FAILED", "", ""),
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
            "issue_id": issue_id, "issue_type": "candidate_record_id_integration_gate_validation_failure",
            "affected_fields": fields, "affected_rules": rules, "severity": "blocking", "status": "open",
            "blocking_scope": "integration_gate", "blocking_reason": issue_id,
            "issue_origin": "step14au_c2_integration_gate_failure", "integration_transition": "added_by_gate_failure",
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
    section_status = (
        ("source", source_passed),
        ("lineage", _validate_lineage_rows(rule_rows, field_rows, context_rows)),
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
        "source_read_boundary": "only_step14au_b2_and_step14au_c1_12_committed_metadata_outputs",
        "source_input_count": 12, "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "integrated_rule_count": len(rules), "integrated_field_count": len(fields),
        "integrated_context_count": len(contexts),
        "changed_rule_ids": ["ADMIT_001"], "changed_field_names": ["candidate_record_id"],
        "changed_context_items": ["candidate_record_id_contract"], "removed_issue_ids": [REMOVED_ISSUE_ID],
        "remaining_issue_count": result["remaining_issue_count"],
        "rule_dependency_contract_passed_count": sum(row["dependency_contract_passed"] == "true" for row in rules),
        "semantics_complete_rule_count": sum(row["semantics_complete"] == "true" for row in rules),
        "semantics_incomplete_rule_count": sum(row["semantics_complete"] != "true" for row in rules),
        "semantics_complete_field_count": sum(row["implementation_semantics_complete"] == "true" for row in fields),
        "semantics_incomplete_field_count": sum(row["implementation_semantics_complete"] != "true" for row in fields),
        "evaluation_context_item_count": len(contexts),
        "deterministic_now_context_count": sum(row["deterministic_now"] == "true" for row in contexts),
        "deterministic_after_contract_freeze_context_count": sum(
            row["deterministic_after_contract_freeze"] == "true" for row in contexts
        ),
        "ready_evaluation_context_count": sum(row["implementation_ready"] == "true" for row in contexts),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS], "canonical_mask_task_count": 5,
        "candidate_record_id_semantics_integrated": all_checks,
        "admit_001_rule_logic_ready": all_checks, "pdb_identifier_semantics_integrated": all_checks,
        "ready_for_admission_evaluator_interface_implementation": all_checks,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "raw_structure_read_current_step": False, "network_access_used_current_step": False,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_integration_lineage_checks_passed": result["all_integration_lineage_checks_passed"],
        "all_integrated_rule_checks_passed": result["all_integrated_rule_checks_passed"],
        "all_integrated_field_checks_passed": result["all_integrated_field_checks_passed"],
        "all_integrated_context_checks_passed": result["all_integrated_context_checks_passed"],
        "all_issue_transition_checks_passed": result["all_issue_transition_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"], "all_checks_passed": all_checks,
        "blocking_reasons": [row["issue_id"] for row in issues],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_checks else BLOCKED_NEXT_STEP,
        "non_manifest_output_count": 5, "output_file_count": 6,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
    }


def run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(
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

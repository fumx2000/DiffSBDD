"""Step14AU-E0-P3 covalent residue locator schema successor overlay.

The gate reads only the six committed D2 outputs and six committed P2 outputs.
It appends five metadata fields, extends only ADMIT_004 dependencies, and does
not evaluate candidates or dereference any structure artifact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate
    as p2_gate,
)


STEP_LABEL = "Step14AU-E0-P3"
STAGE = (
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_integration_gate_v1"
)
PROJECT_NAME = "CovaPIE"
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_"
    "minimal_schema_extension_integration_gate_v1_manifest_v1"
)
PREVIOUS_STAGES = (
    "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1",
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_design_gate_v1",
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_covalent_residue_locator_"
    "parser_and_provider_provenance_export_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_"
    "schema_extension_integration_gate_blockers"
)
INTEGRATION_REASON = "five-field covalent residue locator metadata schema extension frozen"
SOURCE_READ_BOUNDARY = (
    "only_step14au_d2_and_step14au_e0_p2_12_committed_metadata_outputs"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
D2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate_v1"
)
P2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_"
    "covalent_residue_locator_minimal_schema_extension_integration_gate_v1"
)

D2_FILENAMES = (
    "covapie_ligand_comp_id_integrated_rule_matrix.csv",
    "covapie_ligand_comp_id_integrated_field_matrix.csv",
    "covapie_ligand_comp_id_integrated_context_matrix.csv",
    "covapie_ligand_comp_id_integration_safety_audit.csv",
    "covapie_ligand_comp_id_integration_issue_inventory.csv",
    "covapie_ligand_comp_id_semantics_integration_manifest.json",
)
P2_FILENAMES = (
    "covapie_covalent_residue_locator_schema_extension_contract.csv",
    "covapie_covalent_residue_locator_existing_sample_backfill_audit.csv",
    "covapie_covalent_residue_locator_source_boundary_audit.csv",
    "covapie_covalent_residue_locator_safety_audit.csv",
    "covapie_covalent_residue_locator_issue_inventory.csv",
    "covapie_covalent_residue_locator_minimal_schema_extension_design_manifest.json",
)
SOURCE_SHA256 = {
    str(D2_ROOT / D2_FILENAMES[0]): "e0b22771761719c6b2796638628eca3d27d417441b92ac231d1610a8b18b2760",
    str(D2_ROOT / D2_FILENAMES[1]): "828b0e2fe3c26e1e81513cbe4fb48e221e604fa90fb1842972c29f3c2a44266f",
    str(D2_ROOT / D2_FILENAMES[2]): "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8",
    str(D2_ROOT / D2_FILENAMES[3]): "1dd69bffa8b27b59721cbe7530e4da0faef413d92f8760aae3042e2da6e11823",
    str(D2_ROOT / D2_FILENAMES[4]): "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    str(D2_ROOT / D2_FILENAMES[5]): "f74e9f138fb1c5375174192fa4e7ba843feafba1ea3c6c0bb49a77617ccc6540",
    str(P2_ROOT / P2_FILENAMES[0]): "cfe7afde4ef146ea03f6d5d85f8db0cfc0b2ce0bfc5eb94bd6f8bc305f453d89",
    str(P2_ROOT / P2_FILENAMES[1]): "a52a366af0f380cccb4a4d9a7dbb692561ca04bd4a31e65f119f8c7047c11691",
    str(P2_ROOT / P2_FILENAMES[2]): "952de935e3b873d832f774df8688fbf111994f39bdb1f0476293598e4a429659",
    str(P2_ROOT / P2_FILENAMES[3]): "d695c574be443fae48f824fa6b460206d230967cd0315308053c979bc44e0494",
    str(P2_ROOT / P2_FILENAMES[4]): "aa8baf1e238447ec199ffdcb0064c2718def764d16c73e7ccf82b3b124218199",
    str(P2_ROOT / P2_FILENAMES[5]): "7e35e287fb629ae35b8dd83f4cb166ef95013001bbca18beae9653f6564d498b",
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
    "field_name", "requirement_phase", "source_value_contract",
    "candidate_record_field", "producer_scope", "dependent_rules",
    "batch_context_required", "evaluation_context_dependencies",
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
    "source_relative_path", "tracked_by_git", "regular_file", "symlink",
    "sha256_expected", "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason",
)
CSV_OUTPUTS = (
    "covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv",
    "covapie_covalent_residue_locator_schema_integrated_field_matrix.csv",
    "covapie_covalent_residue_locator_schema_integrated_context_matrix.csv",
    "covapie_covalent_residue_locator_schema_integration_safety_audit.csv",
    "covapie_covalent_residue_locator_schema_integration_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_covalent_residue_locator_schema_extension_integration_manifest.json"

ADMIT_004_OLD_DEPENDENCIES = (
    "covalent_residue_name|covalent_residue_chain_id|covalent_residue_index|"
    "covalent_residue_atom_name"
)
ADMIT_004_NEW_DEPENDENCIES = (
    ADMIT_004_OLD_DEPENDENCIES + "|" + "|".join(p2_gate.PROPOSED_FIELD_NAMES)
)
ADMIT_004_BLOCKERS = (
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED|"
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
)
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
RESOLVED_P2_ISSUE_IDS = ("COVALENT_RESIDUE_LOCATOR_EXTENSION_NOT_YET_INTEGRATED",)
REMAINING_P2_FOLLOWUP_ISSUE_IDS = (
    "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_NOT_YET_EXPORTABLE",
)
COMPLETE_RULE_IDS = ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_014", "ADMIT_015")
COMPLETE_FIELD_NAMES = (
    "candidate_record_id", "pdb_id", "ligand_comp_id",
    "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
READY_CONTEXT_ITEMS = (
    "batch_candidate_record_ids", "batch_duplicate_identity_keys", "candidate_record_id_contract",
    "pdb_id_format_contract", "ligand_comp_id_contract", "existing_raw_target_relative_paths",
    "current_stage_download_authorized", "current_stage_training_authorized",
)
SAFETY_ITEMS = (
    "network_access_used_current_step", "external_registry_lookup_current_step",
    "ignored_raw_directory_traversed_current_step", "ignored_raw_structure_read_current_step",
    "checkpoint_read_current_step", "artifact_reference_paths_followed_current_step",
    "d2_source_files_modified_current_step", "p2_source_files_modified_current_step",
    "parser_modified_current_step", "sample_index_producer_modified_current_step",
    "candidate_provider_implemented_current_step", "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step", "raw_files_written_current_step",
    "torch_imported", "numpy_imported", "rdkit_used", "model_forward_called",
    "loss_compute_called", "training_allowed",
)
SECTION_FAILURE_IDS = {
    "source_boundary": "P3_SOURCE_BOUNDARY_VALIDATION_FAILED",
    "d2_predecessor": "P3_D2_PREDECESSOR_VALIDATION_FAILED",
    "p2_predecessor": "P3_P2_PREDECESSOR_VALIDATION_FAILED",
    "p2_helpers": "P3_P2_HELPER_VALIDATION_FAILED",
    "integrated_rules": "P3_INTEGRATED_RULE_VALIDATION_FAILED",
    "integrated_fields": "P3_INTEGRATED_FIELD_VALIDATION_FAILED",
    "integrated_contexts": "P3_INTEGRATED_CONTEXT_VALIDATION_FAILED",
    "issue_preservation": "P3_ISSUE_PRESERVATION_VALIDATION_FAILED",
    "safety": "P3_SAFETY_VALIDATION_FAILED",
}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()],
        cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _source_paths() -> tuple[Path, ...]:
    return tuple(D2_ROOT / name for name in D2_FILENAMES) + tuple(
        P2_ROOT / name for name in P2_FILENAMES
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
    for relative_path in _source_paths():
        absolute = _repo_path(relative_path)
        tracked = _tracked_by_git(relative_path)
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[relative_path.as_posix()]
        passed = tracked and regular and not symlink and observed == expected
        rows.append({
            "source_relative_path": relative_path.as_posix(),
            "tracked_by_git": _bool_text(tracked), "regular_file": _bool_text(regular),
            "symlink": _bool_text(symlink), "sha256_expected": expected,
            "sha256_observed": observed, "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_boundary_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    return (
        bool(rows) and len(rows) == 12
        and all(tuple(row) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == 12
        and all(
            row["tracked_by_git"] == "true" and row["regular_file"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true" for row in rows
        )
    )


def _load_source() -> dict[str, Any]:
    return {
        "d2_rule_rows": _read_csv(D2_ROOT / D2_FILENAMES[0]),
        "d2_field_rows": _read_csv(D2_ROOT / D2_FILENAMES[1]),
        "d2_context_rows": _read_csv(D2_ROOT / D2_FILENAMES[2]),
        "d2_safety_rows": _read_csv(D2_ROOT / D2_FILENAMES[3]),
        "d2_issue_rows": _read_csv(D2_ROOT / D2_FILENAMES[4]),
        "d2_manifest": json.loads(_repo_path(D2_ROOT / D2_FILENAMES[5]).read_text(encoding="utf-8")),
        "p2_contract_rows": _read_csv(P2_ROOT / P2_FILENAMES[0]),
        "p2_backfill_rows": _read_csv(P2_ROOT / P2_FILENAMES[1]),
        "p2_source_rows": _read_csv(P2_ROOT / P2_FILENAMES[2]),
        "p2_safety_rows": _read_csv(P2_ROOT / P2_FILENAMES[3]),
        "p2_issue_rows": _read_csv(P2_ROOT / P2_FILENAMES[4]),
        "p2_manifest": json.loads(_repo_path(P2_ROOT / P2_FILENAMES[5]).read_text(encoding="utf-8")),
    }


def _row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    matches = [row for row in rows if row.get(key) == value]
    return matches[0] if len(matches) == 1 else None


def _expected_admit_004() -> dict[str, str]:
    return {
        "admission_rule_id": "ADMIT_004", "admission_rule_name": "covalent_residue_identity_present",
        "evaluation_phase": "pre_download", "candidate_field_dependencies": ADMIT_004_OLD_DEPENDENCIES,
        "batch_context_dependencies": "", "evaluation_context_dependencies": "covalent_residue_identity_contract",
        "external_filesystem_required": "false", "network_required": "false",
        "download_execution_result_required": "false", "pure_in_memory_interface_possible": "true",
        "dependency_contract_passed": "true", "semantics_complete": "false",
        "deterministic_evaluation_possible_now": "false",
        "deterministic_evaluation_possible_after_contract_freeze": "true",
        "implementation_disposition": "interface_only_pending_semantics",
        "blocking_reasons": ADMIT_004_BLOCKERS,
        "source_stage": "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
        "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
    }


def _validate_d2_predecessor(source: dict[str, Any]) -> bool:
    rules = source["d2_rule_rows"]
    fields = source["d2_field_rows"]
    contexts = source["d2_context_rows"]
    issues = source["d2_issue_rows"]
    manifest = source["d2_manifest"]
    masks = [list(pair) for pair in CANONICAL_MASK_PAIRS]
    return (
        bool(rules) and len(rules) == 15 and all(tuple(row) == RULE_COLUMNS for row in rules)
        and len(fields) == 17 and all(tuple(row) == FIELD_COLUMNS for row in fields)
        and len(contexts) == 18 and all(tuple(row) == CONTEXT_COLUMNS for row in contexts)
        and len(issues) == 10 and all(tuple(row) == ISSUE_COLUMNS for row in issues)
        and tuple(row["issue_id"] for row in issues) == REMAINING_ISSUE_IDS
        and not set(p2_gate.PROPOSED_FIELD_NAMES).intersection(row["field_name"] for row in fields)
        and _row_by(rules, "admission_rule_id", "ADMIT_004") == _expected_admit_004()
        and manifest.get("stage") == PREVIOUS_STAGES[0]
        and manifest.get("step_label") == "Step14AU-D2" and manifest.get("all_checks_passed") is True
        and manifest.get("integrated_rule_count") == 15 and manifest.get("integrated_field_count") == 17
        and manifest.get("integrated_context_count") == 18 and manifest.get("remaining_issue_count") == 10
        and manifest.get("semantics_complete_rule_count") == 5
        and manifest.get("semantics_complete_field_count") == 3
        and manifest.get("ready_evaluation_context_count") == 8
        and manifest.get("candidate_record_id_semantics_integrated") is True
        and manifest.get("pdb_identifier_semantics_integrated") is True
        and manifest.get("ligand_comp_id_semantics_integrated") is True
        and manifest.get("admit_003_rule_logic_ready") is True
        and manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False
        and manifest.get("feature_semantics_audit_required_before_training") is True
        and manifest.get("canonical_mask_pairs") == masks and manifest.get("canonical_mask_task_count") == 5
        and tuple(row["admission_rule_id"] for row in rules if row["semantics_complete"] == "true")
        == COMPLETE_RULE_IDS
        and tuple(row["field_name"] for row in fields if row["implementation_semantics_complete"] == "true")
        == COMPLETE_FIELD_NAMES[:3]
        and tuple(row["context_item"] for row in contexts if row["implementation_ready"] == "true")
        == READY_CONTEXT_ITEMS
    )


def _validate_p2_predecessor(source: dict[str, Any]) -> bool:
    manifest = source["p2_manifest"]
    issues = source["p2_issue_rows"]
    return (
        manifest.get("stage") == PREVIOUS_STAGES[1]
        and manifest.get("step_label") == "Step14AU-E0-P2" and manifest.get("all_checks_passed") is True
        and manifest.get("source_input_count") == 24
        and len(source["p2_source_rows"]) == 24
        and all(row.get("source_boundary_passed") == "true" for row in source["p2_source_rows"])
        and len(source["p2_contract_rows"]) == 40
        and all(row.get("contract_passed") == "true" for row in source["p2_contract_rows"])
        and len(source["p2_backfill_rows"]) == 11
        and all(row.get("audit_passed") == "true" for row in source["p2_backfill_rows"])
        and len(source["p2_safety_rows"]) == 20
        and all(row.get("safety_passed") == "true" for row in source["p2_safety_rows"])
        and [row.get("issue_id") for row in issues]
        == [*REMAINING_P2_FOLLOWUP_ISSUE_IDS, *RESOLVED_P2_ISSUE_IDS]
        and manifest.get("covalent_residue_locator_schema_extension_frozen") is True
        and manifest.get("covalent_residue_locator_schema_extension_integrated") is False
        and manifest.get("current_effective_field_count") == 17
        and manifest.get("proposed_extension_field_count") == 5
        and manifest.get("proposed_post_extension_field_count") == 22
        and manifest.get("current_effective_context_count") == 18
        and manifest.get("current_effective_remaining_issue_count") == 10
        and manifest.get("proposed_field_names") == list(p2_gate.PROPOSED_FIELD_NAMES)
        and all(manifest.get(key) is True for key in (
            "namespace_contract_ready", "same_namespace_contract_ready", "insertion_code_state_contract_ready",
            "provenance_source_id_contract_ready", "provenance_sha256_contract_ready",
            "parser_insertion_code_support_required", "provider_provenance_binding_required",
            "ready_for_schema_extension_integration", "feature_semantics_audit_required_before_training",
        ))
        and manifest.get("insertion_code_present_value_grammar_fully_frozen") is False
        and manifest.get("auth_label_conflict_sample_count") == 3
        and manifest.get("namespace_provable_insertion_unknown_sample_count") == 8
        and manifest.get("fully_provable_pre_download_sample_count") == 0
        and manifest.get("insertion_unknown_sample_count") == 11
        and manifest.get("samples_admissible_after_schema_extension_only") == 0
        and manifest.get("admit_004_rule_logic_ready") is False
        and manifest.get("ready_for_e1_residue_identity_semantics_design") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False
        and manifest.get("recommended_next_step")
        == "integrate_covapie_covalent_residue_locator_minimal_fields_into_admission_schema_v1"
    )


class _StringSubclass(str):
    pass


def _validate_p2_helpers() -> bool:
    auth = p2_gate.normalize_covalent_residue_locator_namespace("auth")
    label = p2_gate.normalize_covalent_residue_locator_namespace("label")
    upper = p2_gate.normalize_covalent_residue_locator_namespace("AUTH")
    mixed = p2_gate.normalize_covalent_residue_locator_namespace("Auth")
    subclass = p2_gate.normalize_covalent_residue_locator_namespace(_StringSubclass("auth"))
    absent = p2_gate.validate_covalent_residue_insertion_code("absent", "")
    present = p2_gate.validate_covalent_residue_insertion_code("present", "A")
    unknown = p2_gate.validate_covalent_residue_insertion_code("unknown", "")
    source_id = p2_gate.normalize_covalent_residue_locator_provenance_source_id("provider:row/1")
    source_ws = p2_gate.normalize_covalent_residue_locator_provenance_source_id(" provider:row/1")
    digest = "a" * 64
    valid_hash = p2_gate.validate_covalent_residue_locator_provenance_sha256(digest)
    upper_hash = p2_gate.validate_covalent_residue_locator_provenance_sha256("A" * 64)
    prefixed_hash = p2_gate.validate_covalent_residue_locator_provenance_sha256("sha256:" + digest)
    return (
        auth.passed and label.passed and not upper.passed and not mixed.passed and not subclass.passed
        and absent.passed and present.passed
        and p2_gate.validate_covalent_residue_insertion_code("present", "A").passed
        and not unknown.passed and unknown.schema_combination_valid and unknown.blocks_admit_004
        and unknown.blocking_reason == "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
        and unknown.state == "unknown" and unknown.state != "absent"
        and source_id.passed and not source_ws.passed
        and valid_hash.passed and not upper_hash.passed and not prefixed_hash.passed
    )


def _overlay_rule_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source_rows]
    target = _row_by(rows, "admission_rule_id", "ADMIT_004")
    if target is not None:
        target.update({
            "candidate_field_dependencies": ADMIT_004_NEW_DEPENDENCIES,
            "integration_source_stage": PREVIOUS_STAGES[1], "integration_applied": "true",
            "integration_reason": INTEGRATION_REASON,
        })
    return rows


def _new_field_rows() -> list[dict[str, str]]:
    specs = (
        (p2_gate.PROPOSED_FIELD_NAMES[0],
         "exact lowercase auth or label applying jointly to residue chain and index",
         "true", "true", "true", "true", ""),
        (p2_gate.PROPOSED_FIELD_NAMES[1],
         "exact lowercase absent, present, or unknown insertion-code provenance state",
         "true", "true", "true", "true", ""),
        (p2_gate.PROPOSED_FIELD_NAMES[2],
         "insertion-code value paired with state; present-value grammar not fully frozen",
         "false", "true", "false", "false", "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"),
        (p2_gate.PROPOSED_FIELD_NAMES[3],
         "stable provider-supplied locator evidence source identifier",
         "true", "true", "true", "true", ""),
        (p2_gate.PROPOSED_FIELD_NAMES[4],
         "lowercase 64-hex SHA256 for locator provenance evidence",
         "true", "true", "true", "true", ""),
    )
    return [{
        "field_name": name,
        "requirement_phase": "pre_download",
        "source_value_contract": contract,
        "candidate_record_field": "true",
        "producer_scope": "candidate_metadata_provider",
        "dependent_rules": "ADMIT_004",
        "batch_context_required": "false",
        "evaluation_context_dependencies": "covalent_residue_identity_contract",
        "allowed_values_defined": allowed,
        "normalization_defined": normalized,
        "exact_validation_defined": exact,
        "implementation_semantics_complete": complete,
        "semantics_evidence": PREVIOUS_STAGES[1],
        "blocking_reasons": blocker,
        "field_contract_mapping_passed": "true",
        "source_stage": PREVIOUS_STAGES[1],
        "integration_source_stage": PREVIOUS_STAGES[1],
        "integration_applied": "true",
        "integration_reason": INTEGRATION_REASON,
    } for name, contract, allowed, normalized, exact, complete, blocker in specs]


def _overlay_field_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [*(dict(row) for row in source_rows), *_new_field_rows()]


def _overlay_context_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in source_rows]


def _overlay_issue_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in source_rows]


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "required_status": "false", "observed_status": "false",
        "safety_passed": "true", "blocking_reason": "",
    } for item in SAFETY_ITEMS]


def _validate_integrated_rule_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    if not rows or len(rows) != 15 or len(source_rows) != 15:
        return False
    if any(tuple(row) != RULE_COLUMNS for row in rows):
        return False
    if [row["admission_rule_id"] for row in rows] != [row["admission_rule_id"] for row in source_rows]:
        return False
    allowed = {"candidate_field_dependencies", "integration_source_stage", "integration_applied", "integration_reason"}
    for row, old in zip(rows, source_rows):
        if row["admission_rule_id"] != "ADMIT_004":
            if row != old:
                return False
        elif (
            any(row[key] != old[key] for key in RULE_COLUMNS if key not in allowed)
            or row["candidate_field_dependencies"] != ADMIT_004_NEW_DEPENDENCIES
            or row["integration_source_stage"] != PREVIOUS_STAGES[1]
            or row["integration_applied"] != "true"
            or row["integration_reason"] != INTEGRATION_REASON
            or row["semantics_complete"] != "false"
            or row["blocking_reasons"] != ADMIT_004_BLOCKERS
        ):
            return False
    return tuple(row["admission_rule_id"] for row in rows if row["semantics_complete"] == "true") == COMPLETE_RULE_IDS


def _validate_integrated_field_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    return (
        bool(rows) and len(source_rows) == 17 and len(rows) == 22
        and all(tuple(row) == FIELD_COLUMNS for row in rows)
        and rows[:17] == source_rows and rows[17:] == _new_field_rows()
        and tuple(row["field_name"] for row in rows[17:]) == tuple(p2_gate.PROPOSED_FIELD_NAMES)
        and len({row["field_name"] for row in rows}) == 22
        and tuple(row["field_name"] for row in rows if row["implementation_semantics_complete"] == "true")
        == COMPLETE_FIELD_NAMES
    )


def _validate_integrated_context_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    return (
        bool(rows) and len(rows) == 18 and rows == source_rows
        and all(tuple(row) == CONTEXT_COLUMNS for row in rows)
        and tuple(row["context_item"] for row in rows if row["implementation_ready"] == "true")
        == READY_CONTEXT_ITEMS
        and sum(row["deterministic_now"] == "true" for row in rows) == 8
        and sum(row["deterministic_after_contract_freeze"] == "true" for row in rows) == 18
        and _row_by(rows, "context_item", "covalent_residue_identity_contract") == {
            "context_item": "covalent_residue_identity_contract", "context_scope": "evaluation_policy",
            "required_by_rules": "ADMIT_004", "provided_by_future_caller": "true",
            "filesystem_access_inside_evaluator": "false", "network_access_inside_evaluator": "false",
            "deterministic_now": "false", "deterministic_after_contract_freeze": "true",
            "exact_contract_defined": "false", "implementation_ready": "false",
            "blocking_reasons": "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
            "source_stage": "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
            "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
        }
    )


def _validate_issue_preservation_rows(rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> bool:
    return (
        bool(rows) and len(rows) == 10 and rows == source_rows
        and all(tuple(row) == ISSUE_COLUMNS for row in rows)
        and tuple(row["issue_id"] for row in rows) == REMAINING_ISSUE_IDS
        and all(row["issue_id"] != "NO_ISSUES" for row in rows)
    )


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and len(rows) == 20 and rows == _safety_rows() and all(
        tuple(row) == SAFETY_COLUMNS for row in rows
    )


def _build_materialization(
    source: dict[str, Any] | None = None, *,
    source_rows: list[dict[str, str]] | None = None,
    rule_rows: list[dict[str, str]] | None = None,
    field_rows: list[dict[str, str]] | None = None,
    context_rows: list[dict[str, str]] | None = None,
    issue_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
    helper_status: bool | None = None,
) -> dict[str, Any]:
    source = _load_source() if source is None else source
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    rule_rows = _overlay_rule_rows(source["d2_rule_rows"]) if rule_rows is None else rule_rows
    field_rows = _overlay_field_rows(source["d2_field_rows"]) if field_rows is None else field_rows
    context_rows = _overlay_context_rows(source["d2_context_rows"]) if context_rows is None else context_rows
    domain_issue_rows = _overlay_issue_rows(source["d2_issue_rows"])
    issue_rows_to_validate = domain_issue_rows if issue_rows is None else issue_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    helper_status = _validate_p2_helpers() if helper_status is None else helper_status
    status = {
        "source_boundary": _validate_source_boundary_rows(source_rows),
        "d2_predecessor": _validate_d2_predecessor(source),
        "p2_predecessor": _validate_p2_predecessor(source),
        "p2_helpers": helper_status,
        "integrated_rules": _validate_integrated_rule_rows(rule_rows, source["d2_rule_rows"]),
        "integrated_fields": _validate_integrated_field_rows(field_rows, source["d2_field_rows"]),
        "integrated_contexts": _validate_integrated_context_rows(context_rows, source["d2_context_rows"]),
        "issue_preservation": _validate_issue_preservation_rows(
            issue_rows_to_validate, source["d2_issue_rows"]
        ),
        "safety": _validate_safety_rows(safety_rows),
    }
    failures = [SECTION_FAILURE_IDS[name] for name, passed in status.items() if not passed]
    return {
        "source_rows": source_rows, "rule_rows": rule_rows, "field_rows": field_rows,
        "context_rows": context_rows, "issue_rows": domain_issue_rows, "safety_rows": safety_rows,
        **{f"all_{name}_checks_passed": passed for name, passed in status.items()},
        "all_checks_passed": all(status.values()), "validation_failures": failures,
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
    passed = result["all_checks_passed"]
    rules, fields, contexts = result["rule_rows"], result["field_rows"], result["context_rows"]
    domain_blockers = list(REMAINING_ISSUE_IDS)
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stages": list(PREVIOUS_STAGES),
        "source_read_boundary": SOURCE_READ_BOUNDARY, "source_input_count": 12,
        "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_file_count": 6,
        "non_manifest_output_count": 5, "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "predecessor_field_count": 17, "added_field_count": 5,
        "integrated_field_count": len(fields), "added_field_names": list(p2_gate.PROPOSED_FIELD_NAMES),
        "predecessor_context_count": 18, "integrated_context_count": len(contexts),
        "predecessor_rule_count": 15, "integrated_rule_count": len(rules),
        "changed_rule_ids": ["ADMIT_004"], "changed_context_items": [],
        "unchanged_predecessor_field_row_count": 17,
        "unchanged_context_row_count": 18, "unchanged_non_target_rule_row_count": 14,
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
        "remaining_issue_count": len(result["issue_rows"]),
        "covalent_residue_locator_schema_extension_frozen": True,
        "covalent_residue_locator_schema_extension_integrated": passed,
        "resolved_p2_issue_ids": list(RESOLVED_P2_ISSUE_IDS) if passed else [],
        "remaining_p2_followup_issue_ids": list(REMAINING_P2_FOLLOWUP_ISSUE_IDS),
        "insertion_code_provenance_export_ready": False,
        "insertion_code_present_value_grammar_fully_frozen": False,
        "parser_insertion_code_support_required": True,
        "provider_provenance_binding_required": True,
        "existing_sample_count": 11, "insertion_unknown_sample_count": 11,
        "fully_provable_pre_download_sample_count": 0,
        "samples_admissible_after_schema_extension_only": 0,
        "admit_004_rule_logic_ready": False,
        "covalent_residue_identity_semantics_resolved": False,
        "covalent_residue_atom_name_semantics_resolved": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_parser_and_provider_provenance_export_design": passed,
        "ready_for_admission_evaluator_interface_implementation": passed,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "ignored_raw_structure_read_current_step": False, "checkpoint_read_current_step": False,
        "parser_modified_current_step": False, "sample_index_producer_modified_current_step": False,
        "candidate_provider_implemented_current_step": False,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_d2_predecessor_checks_passed": result["all_d2_predecessor_checks_passed"],
        "all_p2_predecessor_checks_passed": result["all_p2_predecessor_checks_passed"],
        "all_p2_helper_checks_passed": result["all_p2_helpers_checks_passed"],
        "all_integrated_rule_checks_passed": result["all_integrated_rules_checks_passed"],
        "all_integrated_field_checks_passed": result["all_integrated_fields_checks_passed"],
        "all_integrated_context_checks_passed": result["all_integrated_contexts_checks_passed"],
        "all_issue_preservation_checks_passed": result["all_issue_preservation_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"],
        "all_checks_passed": passed, "validation_failures": result["validation_failures"],
        "blocking_reasons": domain_blockers,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize the deterministic 22-field metadata-only successor view."""
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    if root.is_symlink():
        raise RuntimeError("output root must not be a symlink")
    result = _build_materialization()
    output_sha256 = _write_outputs(root, result)
    manifest = _manifest_payload(result, output_sha256)
    (root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1()

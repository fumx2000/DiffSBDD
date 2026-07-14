#!/usr/bin/env python3
"""Verify the deterministic, truthfully blocked Step14AU-A audit."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext.covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate import (  # noqa: E402
    CANONICAL_MASK_PAIRS,
    CSV_OUTPUTS,
    DEFAULT_OUTPUT_ROOT,
    MANIFEST_FILENAME,
    SOURCE_SHA256,
    STAGE,
    run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1,
)


EXPECTED_ISSUE_IDS = [
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
    "PDB_ID_FORMAT_SEMANTICS_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_manifest(manifest: dict[str, object], first_hashes: dict[str, str]) -> None:
    """Fail closed when any subsequently printed truth has drifted."""
    assert manifest["stage"] == STAGE
    assert manifest["source_input_count"] == 6
    assert manifest["source_input_sha256"] == SOURCE_SHA256
    assert (manifest["rule_count"], manifest["field_count"]) == (15, 17)
    assert (
        manifest["pre_download_field_count"],
        manifest["pre_final_split_field_count"],
        manifest["post_download_field_count"],
    ) == (12, 1, 4)
    assert manifest["artifact_reference_paths_not_recursively_opened"] is True
    assert manifest["candidate_records_materialized"] is False
    assert manifest["download_queue_materialized"] is False
    assert manifest["network_access_used_current_step"] is False
    assert manifest["raw_structure_read_current_step"] is False
    assert manifest["all_source_boundary_checks_passed"] is True
    assert manifest["all_rule_dependency_contract_checks_passed"] is True
    assert manifest["all_rule_semantics_complete"] is False
    assert manifest["all_field_contract_mapping_checks_passed"] is True
    assert manifest["all_field_semantics_complete"] is False
    assert manifest["all_evaluation_context_contract_checks_passed"] is True
    assert manifest["all_evaluation_contexts_ready"] is False
    assert manifest["all_safety_checks_passed"] is True
    assert manifest["precondition_audit_completed"] is True
    assert manifest["all_checks_passed"] is False
    assert manifest["rule_dependency_contract_passed_count"] == 15
    assert (
        manifest["semantics_complete_rule_count"],
        manifest["semantics_incomplete_rule_count"],
    ) == (2, 13)
    assert (
        manifest["semantics_complete_field_count"],
        manifest["semantics_incomplete_field_count"],
    ) == (0, 17)
    assert (
        manifest["evaluation_context_item_count"],
        manifest["deterministic_now_context_count"],
        manifest["deterministic_after_contract_freeze_context_count"],
        manifest["ready_evaluation_context_count"],
    ) == (18, 5, 18, 5)
    assert manifest["issue_count"] == len(EXPECTED_ISSUE_IDS)
    assert manifest["blocking_reasons"] == EXPECTED_ISSUE_IDS
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["ready_for_admission_evaluator_interface_implementation"] is True
    assert manifest["ready_for_admission_evaluator_rule_logic_implementation"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == (
        "resolve_covapie_bulk_download_admission_implementation_precondition_blockers"
    )
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {name: first_hashes[name] for name in CSV_OUTPUTS}
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "/home/" not in serialized


def _validate_issue_inventory(root: Path) -> None:
    with (root / CSV_OUTPUTS[4]).open(encoding="utf-8") as handle:
        issue_ids = [row.split(",", 1)[0] for row in handle.read().splitlines()[1:]]
    assert issue_ids == EXPECTED_ISSUE_IDS


def main() -> int:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT
    run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(root)
    first_hashes = {name: _sha256(root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    run_covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1(root)
    second_hashes = {name: _sha256(root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    assert first_hashes == second_hashes
    manifest = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    _validate_manifest(manifest, first_hashes)
    _validate_issue_inventory(root)
    print(f"stage={STAGE}")
    print("all_source_boundary_checks_passed=true")
    print("all_rule_dependency_contract_checks_passed=true")
    print("all_rule_semantics_complete=false")
    print("all_field_contract_mapping_checks_passed=true")
    print("all_field_semantics_complete=false")
    print("all_evaluation_context_contract_checks_passed=true")
    print("all_evaluation_contexts_ready=false")
    print("all_safety_checks_passed=true")
    print("precondition_audit_completed=true")
    print("all_checks_passed=false")
    print("rule_count=15")
    print("rule_dependency_contract_passed_count=15")
    print("semantics_complete_rule_count=2")
    print("semantics_incomplete_rule_count=13")
    print("field_count=17")
    print("semantics_complete_field_count=0")
    print("semantics_incomplete_field_count=17")
    print("evaluation_context_item_count=18")
    print("deterministic_now_context_count=5")
    print("deterministic_after_contract_freeze_context_count=18")
    print("ready_evaluation_context_count=5")
    print("issue_count=13")
    print("canonical_mask_task_count=5")
    print("feature_semantics_audit_required_before_training=true")
    print("ready_for_admission_evaluator_interface_implementation=true")
    print("ready_for_admission_evaluator_rule_logic_implementation=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("admission_implementation_precondition_output_hashes_byte_identical=true")
    print("covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

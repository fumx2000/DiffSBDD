from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from functools import lru_cache
from pathlib import Path

import pytest

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_real_provider_export_blocking_row_quarantine_materialization_v1
    as gate,
)

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / (
    "scripts/check_covapie_real_provider_export_blocking_row_"
    "quarantine_materialization_v1.py"
)
NESTED_ENV = "COVAPIE_REAL_PROVIDER_QUARANTINE_NESTED_LIFECYCLE"


@lru_cache(maxsize=1)
def _result():
    return (
        gate.derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1(
            ROOT
        )
    )


@lru_cache(maxsize=1)
def _artifacts():
    return (
        gate.build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1(
            ROOT
        )
    )


def _rows(name: str) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(_artifacts()[name].decode(), newline=""))
    )


def _base(path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{gate.BASE_COMMIT}:{path.as_posix()}"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def test_public_api_and_frozen_decisions() -> None:
    assert gate.__all__ == (
        "RealProviderExportBlockingRowQuarantineMaterializationDecision",
        "RealProviderExportQuarantineFailureCaseDecision",
        "build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1",
        "derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1",
        "evaluate_covapie_real_provider_export_quarantine_failure_case_v1",
        "serialize_covapie_real_provider_export_blocking_row_quarantine_materialization_decision_v1",
    )
    decision = _result()["decision"]
    assert (
        gate.RealProviderExportBlockingRowQuarantineMaterializationDecision
        .__dataclass_params__.frozen
    )
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "invalid"
    assert tuple(item.name for item in fields(type(decision))) == (
        "schema_version", "outcome", "predecessor_verified",
        "quarantine_scope_compatible", "blocking_row_count",
        "quarantine_row_count", "unique_quarantine_row_count",
        "quarantine_identity_projection_verified",
        "source_provenance_preserved_count",
        "provider_admitted_exclusion_count",
        "provider_passed_exclusion_count",
        "future_canonical_exclusion_count", "tensorization_exclusion_count",
        "training_exclusion_count", "provider_rows_mutated",
        "existing_final_dataset_modified", "quarantine_materialized",
        "provider_blocking_effect_contained", "provider_issue_resolved",
        "provider_values_resolved", "provider_reexport_still_required",
        "ready_for_feature_semantics_audit", "ready_for_tensorization",
        "feature_semantics_audit_completed", "ready_for_training",
        "recommended_next_step",
    )
    failure = (
        gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
            ROOT, "predecessor_sha_drift"
        )
    )
    assert gate.RealProviderExportQuarantineFailureCaseDecision.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        failure.outcome = "materialized"
    assert tuple(item.name for item in fields(type(failure))) == (
        "failure_case", "outcome", "failure_detected",
        "candidate_quarantine_registry_valid",
        "candidate_exclusion_registry_valid",
        "provider_issue_transition_applied",
        "provider_issue_effective_status",
        "ready_for_feature_semantics_audit", "ready_for_tensorization",
        "ready_for_training",
    )


def test_formal_base_and_all_frozen_sha256() -> None:
    shown = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", gate.BASE_COMMIT),
        cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.splitlines()
    assert shown == [
        gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_TREE, gate.BASE_SUBJECT
    ]
    for path, digest in gate.FROZEN_SHA256.items():
        assert gate._sha(_base(path)) == digest


def test_predecessor_manifest_is_exactly_quarantine_ready() -> None:
    manifest = json.loads(_base(gate.POLICY_MANIFEST))
    assert gate._predecessor_manifest_verified(manifest)
    assert manifest["blocking_row_count"] == 11
    assert manifest["quarantine_required_count"] == 11
    assert manifest["contradictory_or_invalid_count"] == 0
    assert manifest["provider_rows_mutated"] is False
    assert manifest["quarantine_materialized"] is False
    assert manifest["provider_issue_resolved"] is False


def test_quarantine_scope_is_forward_only_and_compatible() -> None:
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    assert gate.QUARANTINE_SCOPE == "real_provider_export_ingestion_path_only"
    assert manifest["quarantine_scope"] == gate.QUARANTINE_SCOPE
    assert manifest["quarantine_scope_compatible"] is True
    assert manifest["existing_final_dataset_modified"] is False
    assert manifest["existing_canonical_samples_deleted"] is False
    assert manifest["atom_pair_validation_artifacts_modified"] is False
    assert (
        manifest[
            "quarantine_retroactively_invalidates_current_canonical_samples"
        ]
        is False
    )


def test_source_inventory_is_base_bound_and_complete() -> None:
    rows = _rows(gate.SOURCE_INVENTORY_FILE)
    assert len(rows) == len(gate.SOURCE_ROLES) == 12
    assert {row["source_role"] for row in rows} == {
        role for role, _, _ in gate.SOURCE_ROLES
    }
    for row in rows:
        path = Path(row["source_path"])
        assert row["source_sha256"] == gate.FROZEN_SHA256[path]
        assert row["committed_in_base"] == "true"
        assert row["verified"] == "true"
        assert not row["source_path"].startswith("data/raw/")


def test_exact11_quarantine_identity_projection() -> None:
    rows = _rows(gate.QUARANTINE_INVENTORY_FILE)
    assert len(rows) == 11
    assert [row["quarantine_id"] for row in rows] == [
        f"REAL_PROVIDER_EXPORT_QUARANTINE_{index:06d}"
        for index in range(1, 12)
    ]
    assert [row["blocking_row_identity"] for row in rows] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    assert len({row["candidate_identity"] for row in rows}) == 11


def test_quarantine_rows_preserve_unknown_and_admit_004_block() -> None:
    rows = _rows(gate.QUARANTINE_INVENTORY_FILE)
    assert all(row["observed_insertion_code_state"] == "unknown" for row in rows)
    assert all(row["observed_insertion_code"] == "" for row in rows)
    assert all(row["admission_rule_id"] == "ADMIT_004" for row in rows)
    assert all(row["admit_004_outcome"] == "blocked" for row in rows)
    assert all(row["admit_004_reason"] == gate.UNKNOWN_REASON for row in rows)
    assert all(row["audit_disposition"] == gate.AUDIT_DISPOSITION for row in rows)
    assert all(row["quarantine_status"] == gate.QUARANTINE_STATUS for row in rows)


def test_shared_quarantine_projection_helper_covers_exact_schema_and_types() -> None:
    state = gate._baseline_state(ROOT)
    audit = state["audit_rows"][0]
    provider = gate._keyed(
        state["sidecar_rows"], "binding_row_id"
    )["REAL_LOCATOR_BINDING_000001"]
    expected = gate._expected_quarantine_row_v1(
        row_order=1, audit_row=audit, provider_row=provider
    )
    assert expected == state["quarantine_rows"][0]
    assert tuple(expected) == gate.QUARANTINE_COLUMNS
    assert len(expected) == 33
    assert type(expected["quarantine_row_order"]) is int
    assert all(
        type(value) is str
        for key, value in expected.items()
        if key != "quarantine_row_order"
    )
    assert gate._quarantine_inventory_exact_schema_valid(
        state["quarantine_rows"]
    )
    assert gate._quarantine_inventory_exact_types_valid(
        state["quarantine_rows"]
    )


def test_shared_exclusion_projection_helper_covers_exact_schema_and_types() -> None:
    state = gate._baseline_state(ROOT)
    expected = gate._expected_exclusion_row_v1(
        state["quarantine_rows"][0], gate.EXCLUSION_SCOPES[0]
    )
    assert expected == state["exclusion_rows"][0]
    assert tuple(expected) == gate.EXCLUSION_COLUMNS
    assert len(expected) == 10
    assert all(type(value) is str for value in expected.values())
    assert expected["exclusion_reason"] == gate.EXCLUSION_REASON
    assert gate._exclusion_inventory_exact_schema_valid(
        state["exclusion_rows"]
    )
    assert gate._exclusion_inventory_exact_types_valid(
        state["exclusion_rows"]
    )


def test_provider_rows_and_provenance_are_preserved() -> None:
    rows = _rows(gate.QUARANTINE_INVENTORY_FILE)
    sidecars = gate._keyed(
        gate._csv_rows(_base(gate.PROVIDER_SIDECAR)), "binding_row_id"
    )
    assert len(sidecars) == 11
    for row in rows:
        identity = row["blocking_row_identity"]
        source = sidecars[identity]
        assert row["original_provider_export_status"] == "exported_blocking"
        assert row["original_provider_row_source_sha256"] == (
            gate.FROZEN_SHA256[gate.PROVIDER_SIDECAR]
        )
        assert row["original_provider_row_selector"] == (
            f"binding_row_id={identity}"
        )
        assert row["provider_provenance_source_id"] == source[
            "covalent_residue_locator_provenance_source_id"
        ]
        assert row["provider_provenance_sha256"] == source[
            "covalent_residue_locator_provenance_sha256"
        ]
        assert row["provider_row_mutated"] == "false"
        assert row["provider_value_resolved"] == "false"
        assert row["provider_reexport_required"] == "true"
        assert row["verified"] == "true"


def test_original_provider_and_boundary_artifacts_are_byte_identical() -> None:
    for path in (
        gate.PROVIDER_SIDECAR, gate.INTEGRATION_OVERLAY,
        gate.INTEGRATION_EVIDENCE, gate.FINAL_DATASET_INDEX,
        gate.ATOM_PAIR_MANIFEST,
    ):
        assert path.read_bytes() == _base(path)


def test_exact55_exclusion_matrix_and_no_sixth_scope() -> None:
    rows = _rows(gate.EXCLUSION_MATRIX_FILE)
    assert len(rows) == 55
    assert {row["exclusion_scope"] for row in rows} == set(
        gate.EXCLUSION_SCOPES
    )
    assert len({
        (row["quarantine_id"], row["exclusion_scope"]) for row in rows
    }) == 55
    for row in rows:
        assert row["expected_membership"] == "false"
        assert row["observed_membership"] == "false"
        assert row["source_quarantine_status"] == gate.QUARANTINE_STATUS
        assert row["fails_closed"] == "true"
        assert row["verified"] == "true"


def test_all_five_exclusion_counts_are_exact11() -> None:
    decision = _result()["decision"]
    assert decision.provider_admitted_exclusion_count == 11
    assert decision.provider_passed_exclusion_count == 11
    assert decision.future_canonical_exclusion_count == 11
    assert decision.tensorization_exclusion_count == 11
    assert decision.training_exclusion_count == 11


def test_issue_transition_changes_only_provider_four_successor_fields() -> None:
    predecessor = gate._keyed(
        gate._csv_rows(_base(gate.POLICY_ISSUES)), "issue_id"
    )
    current = gate._keyed(_rows(gate.ISSUE_INVENTORY_FILE), "issue_id")
    changed_fields = {
        "successor_effective_status", "successor_transition_stage",
        "successor_transition_action", "successor_transition_evidence",
    }
    assert set(current) == set(predecessor)
    for issue_id, row in predecessor.items():
        changed = {key for key in row if row[key] != current[issue_id][key]}
        assert changed == (changed_fields if issue_id == gate.ISSUE_ID else set())
    provider = current[gate.ISSUE_ID]
    assert provider["successor_effective_status"] == "resolved"
    assert provider["successor_transition_stage"] == gate.STAGE
    assert provider["successor_transition_action"] == (
        "resolved_by_fail_closed_quarantine_containment_v1"
    )


def test_prevalidation_issue_is_open_and_core_does_not_require_resolution() -> None:
    state = gate._baseline_state(ROOT)
    predecessor = state["predecessor_issue_rows"]
    prevalidation = state["candidate_issue_rows"]
    assert prevalidation == predecessor
    assert gate._provider_issue_effective_status(prevalidation) == "open"
    assert gate._prevalidation_issue_inventory_valid(
        prevalidation, predecessor
    )
    assert gate._core_materialization_valid(state) is False
    state["failure_matrix_complete"] = True
    assert gate._core_materialization_valid(state) is True
    assert gate._provider_issue_effective_status(
        state["candidate_issue_rows"]
    ) == "open"


def test_provider_issue_transition_is_postvalidation_and_exactly_once() -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = True
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["core_materialization_valid"] is True
    assert evaluation["provider_issue_transition_applied"] is True
    assert evaluation["provider_issue_effective_status"] == "resolved"
    assert gate._successor_issue_inventory_valid(
        state["predecessor_issue_rows"], evaluation["issue_rows"],
        materialization_success=True,
    )
    unchanged = gate._apply_provider_issue_transition_after_success_v1(
        state["predecessor_issue_rows"], materialization_success=False
    )
    assert unchanged == state["predecessor_issue_rows"]
    assert gate._provider_issue_effective_status(unchanged) == "open"
    with pytest.raises(TypeError):
        gate._apply_provider_issue_transition_after_success_v1(
            state["predecessor_issue_rows"], materialization_success=1
        )


def test_invalid_state_returns_predecessor_open_issue_inventory() -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = False
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["materialization_success"] is False
    assert evaluation["issue_rows"] == state["predecessor_issue_rows"]
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"


def test_atom_pair_issue_remains_resolved_and_unchanged() -> None:
    predecessor = gate._keyed(
        gate._csv_rows(_base(gate.POLICY_ISSUES)), "issue_id"
    )
    current = gate._keyed(_rows(gate.ISSUE_INVENTORY_FILE), "issue_id")
    assert current[gate.ATOM_PAIR_ISSUE_ID] == predecessor[gate.ATOM_PAIR_ISSUE_ID]
    assert current[gate.ATOM_PAIR_ISSUE_ID]["successor_effective_status"] == (
        "resolved"
    )


@pytest.mark.parametrize("failure_case", gate.FAILURE_CASES)
def test_failure_matrix_cases_execute_and_fail_closed(
    failure_case: str,
) -> None:
    decision = (
        gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
            ROOT, failure_case
        )
    )
    assert decision.outcome == "invalid"
    assert decision.failure_detected is True
    assert decision.provider_issue_transition_applied is False
    assert decision.provider_issue_effective_status == "open"
    assert decision.ready_for_feature_semantics_audit is False
    assert decision.ready_for_tensorization is False
    assert decision.ready_for_training is False


@pytest.mark.parametrize(
    "failure_case",
    (
        "quarantine_provider_export_identity_mismatch",
        "quarantine_pdb_or_ligand_projection_mismatch",
        "quarantine_residue_projection_mismatch",
        "quarantine_insertion_state_or_code_mismatch",
        "quarantine_admit_004_projection_mismatch",
        "quarantine_reason_mismatch",
    ),
)
def test_exact7_quarantine_projection_failures_invalidate_both_registries(
    failure_case: str,
) -> None:
    decision = (
        gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
            ROOT, failure_case
        )
    )
    assert decision.candidate_quarantine_registry_valid is False
    assert decision.candidate_exclusion_registry_valid is False
    assert decision.provider_issue_transition_applied is False
    assert decision.provider_issue_effective_status == "open"


def test_exact7_exclusion_reason_failure_preserves_only_quarantine_registry() -> None:
    decision = (
        gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
            ROOT, "exclusion_reason_mismatch"
        )
    )
    assert decision.candidate_quarantine_registry_valid is True
    assert decision.candidate_exclusion_registry_valid is False
    assert decision.provider_issue_transition_applied is False
    assert decision.provider_issue_effective_status == "open"


@pytest.mark.parametrize(
    "field",
    (
        "provider_export_row_identity",
        "pdb_id",
        "ligand_identity",
        "residue_name",
        "residue_chain_or_asym_id",
        "residue_sequence_id",
        "observed_insertion_code_state",
        "observed_insertion_code",
        "admission_rule_id",
        "admit_004_outcome",
        "admit_004_reason",
        "quarantine_reason",
        "original_provider_export_status",
        "original_provider_row_source_path",
        "original_provider_row_source_sha256",
        "original_provider_row_selector",
        "provider_provenance_source_id",
        "provider_provenance_sha256",
    ),
)
def test_every_required_quarantine_projection_field_fails_closed(
    field: str,
) -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = True
    state["quarantine_rows"][0][field] = "TAMPERED"
    assert gate._candidate_quarantine_registry_valid(state) is False
    assert gate._candidate_exclusion_registry_valid(state) is False
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"


@pytest.mark.parametrize(
    "tamper",
    (
        "missing_field",
        "extra_field",
        "wrong_field_order",
        "bool_row_order",
        "non_string_value",
        "non_list_registry",
        "non_exact_dict_row",
    ),
)
def test_quarantine_exact_schema_and_types_fail_closed(tamper: str) -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = True
    row = state["quarantine_rows"][0]
    if tamper == "missing_field":
        row.pop("pdb_id")
    elif tamper == "extra_field":
        row["extra"] = "value"
    elif tamper == "wrong_field_order":
        state["quarantine_rows"][0] = dict(reversed(tuple(row.items())))
    elif tamper == "bool_row_order":
        row["quarantine_row_order"] = True
    elif tamper == "non_string_value":
        row["pdb_id"] = 1
    elif tamper == "non_list_registry":
        state["quarantine_rows"] = tuple(state["quarantine_rows"])
    elif tamper == "non_exact_dict_row":
        class DictSubclass(dict):
            pass
        state["quarantine_rows"][0] = DictSubclass(row)
    assert gate._candidate_quarantine_registry_valid(state) is False
    assert gate._candidate_exclusion_registry_valid(state) is False
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"


@pytest.mark.parametrize(
    "field",
    (
        "blocking_row_identity",
        "candidate_identity",
        "expected_membership",
        "observed_membership",
        "exclusion_reason",
        "source_quarantine_status",
        "fails_closed",
        "verified",
    ),
)
def test_every_required_exclusion_contract_field_fails_closed(
    field: str,
) -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = True
    state["exclusion_rows"][0][field] = "TAMPERED"
    assert gate._candidate_quarantine_registry_valid(state) is True
    assert gate._candidate_exclusion_registry_valid(state) is False
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"


@pytest.mark.parametrize(
    "tamper",
    (
        "missing_field",
        "extra_field",
        "wrong_field_order",
        "non_string_value",
        "non_list_registry",
        "non_exact_dict_row",
    ),
)
def test_exclusion_exact_schema_and_types_fail_closed(tamper: str) -> None:
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = True
    row = state["exclusion_rows"][0]
    if tamper == "missing_field":
        row.pop("exclusion_reason")
    elif tamper == "extra_field":
        row["extra"] = "value"
    elif tamper == "wrong_field_order":
        state["exclusion_rows"][0] = dict(reversed(tuple(row.items())))
    elif tamper == "non_string_value":
        row["verified"] = True
    elif tamper == "non_list_registry":
        state["exclusion_rows"] = tuple(state["exclusion_rows"])
    elif tamper == "non_exact_dict_row":
        class DictSubclass(dict):
            pass
        state["exclusion_rows"][0] = DictSubclass(row)
    assert gate._candidate_quarantine_registry_valid(state) is True
    assert gate._candidate_exclusion_registry_valid(state) is False
    evaluation = gate._materialization_evaluation(state)
    assert evaluation["provider_issue_transition_applied"] is False
    assert evaluation["provider_issue_effective_status"] == "open"


@pytest.mark.parametrize(
    ("failure_case", "quarantine_valid", "exclusion_valid"),
    (
        ("missing_quarantine_row", False, False),
        ("duplicate_quarantine_id", False, False),
        ("provider_issue_resolved_before_exact11_quarantine", False, False),
        ("provider_issue_resolved_before_exact55_exclusions", True, False),
        ("predecessor_sha_drift", True, True),
        ("provider_admitted_membership_true", False, False),
    ),
)
def test_failure_observations_report_actual_registry_validity(
    failure_case: str,
    quarantine_valid: bool,
    exclusion_valid: bool,
) -> None:
    decision = (
        gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
            ROOT, failure_case
        )
    )
    assert decision.candidate_quarantine_registry_valid is quarantine_valid
    assert decision.candidate_exclusion_registry_valid is exclusion_valid
    assert decision.provider_issue_transition_applied is False
    assert decision.provider_issue_effective_status == "open"


def test_premature_provider_issue_transition_is_actually_requested_and_rejected() -> None:
    for case in (
        "provider_issue_resolved_before_exact11_quarantine",
        "provider_issue_resolved_before_exact55_exclusions",
    ):
        state = gate._baseline_state(ROOT)
        state["failure_matrix_complete"] = True
        gate._apply_failure_case(state, case)
        assert gate._provider_issue_effective_status(
            state["candidate_issue_rows"]
        ) == "resolved"
        evaluation = gate._materialization_evaluation(state)
        assert evaluation["core_materialization_valid"] is False
        assert evaluation["provider_issue_transition_applied"] is False
        assert evaluation["provider_issue_effective_status"] == "open"
        assert evaluation["issue_rows"] == state["predecessor_issue_rows"]


def test_failure_matrix_is_complete_and_issue_resolution_prerequisite() -> None:
    rows = _rows(gate.FAILURE_MATRIX_FILE)
    assert len(rows) == 36
    assert [row["failure_case"] for row in rows] == list(gate.FAILURE_CASES)
    assert all(row["expected_outcome"] == "invalid" for row in rows)
    assert all(row["observed_outcome"] == "invalid" for row in rows)
    assert all(row["failure_detected"] == "true" for row in rows)
    assert all(
        row["provider_issue_transition_applied"] == "false" for row in rows
    )
    assert all(
        row["provider_issue_effective_status"] == "open" for row in rows
    )
    assert all(
        row["ready_for_feature_semantics_audit"] == "false" for row in rows
    )
    assert all(row["ready_for_tensorization"] == "false" for row in rows)
    assert all(row["ready_for_training"] == "false" for row in rows)
    assert all(row["fails_closed"] == "true" for row in rows)
    assert all(row["verified"] == "true" for row in rows)
    for row in rows:
        observed = (
            gate.evaluate_covapie_real_provider_export_quarantine_failure_case_v1(
                ROOT, row["failure_case"]
            )
        )
        assert row["candidate_quarantine_registry_valid"] == (
            "true" if observed.candidate_quarantine_registry_valid else "false"
        )
        assert row["candidate_exclusion_registry_valid"] == (
            "true" if observed.candidate_exclusion_registry_valid else "false"
        )
    state = gate._baseline_state(ROOT)
    state["failure_matrix_complete"] = False
    decision = gate._decision_from_state(state)
    assert decision.outcome == "invalid"
    assert decision.provider_issue_resolved is False


def test_success_registry_and_issue_evidence_sha_remain_frozen() -> None:
    expected = {
        gate.SOURCE_INVENTORY_FILE:
            "e7ca01a1282aa478ca51ee6adba403942912922bb1719d531eb358ca4329f85d",
        gate.QUARANTINE_INVENTORY_FILE:
            "e16f1c763b6f72385b3f7bac5d1e2df61d506d50ea39287fd7a313968e40d53d",
        gate.EXCLUSION_MATRIX_FILE:
            "c62ac606d3d760517e012d37e344b297acf28227b0d27688a349872e45a8d82e",
        gate.ISSUE_INVENTORY_FILE:
            "540492e7b8a429ba251954da3aad2d7228e587c7f81044f09356cd3e984196aa",
    }
    for name, digest in expected.items():
        assert gate._sha(_artifacts()[name]) == digest


def test_success_decision_has_exact_readiness_boundary() -> None:
    decision = _result()["decision"]
    assert decision.outcome == "materialized"
    assert decision.predecessor_verified is True
    assert decision.quarantine_scope_compatible is True
    assert decision.blocking_row_count == 11
    assert decision.quarantine_row_count == 11
    assert decision.unique_quarantine_row_count == 11
    assert decision.quarantine_identity_projection_verified is True
    assert decision.source_provenance_preserved_count == 11
    assert decision.provider_rows_mutated is False
    assert decision.existing_final_dataset_modified is False
    assert decision.quarantine_materialized is True
    assert decision.provider_blocking_effect_contained is True
    assert decision.provider_issue_resolved is True
    assert decision.provider_values_resolved is False
    assert decision.provider_reexport_still_required is True
    assert decision.ready_for_feature_semantics_audit is True
    assert decision.ready_for_tensorization is False
    assert decision.feature_semantics_audit_completed is False
    assert decision.ready_for_training is False
    assert decision.recommended_next_step == gate.RECOMMENDED_NEXT_STEP


def test_manifest_truthfulness_masks_and_output_sha256() -> None:
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    assert manifest["materialization_outcome"] == "materialized"
    assert manifest["provider_rows_present"] is True
    assert manifest["provider_rows_quarantined"] is True
    assert manifest["provider_values_resolved"] is False
    assert manifest["provider_reexport_still_required"] is True
    assert manifest["provider_coverage_complete"] is False
    assert manifest["provider_blocking_effect_contained"] is True
    assert manifest["provider_issue_resolved"] is True
    assert manifest["prevalidation_provider_issue_effective_status"] == "open"
    assert manifest["provider_issue_transition_applied_after_validation"] is True
    assert manifest["provider_issue_transition_preconditions_verified"] is True
    assert manifest["provider_issue_transition_applied_exactly_once"] is True
    assert manifest["provider_issue_transition_changed_field_count"] == 4
    assert manifest["quarantine_inventory_full_field_projection_verified"] is True
    assert manifest["quarantine_inventory_exact_schema_verified"] is True
    assert manifest["quarantine_inventory_exact_types_verified"] is True
    assert manifest["exclusion_inventory_full_field_projection_verified"] is True
    assert manifest["exclusion_inventory_exact_schema_verified"] is True
    assert manifest["exclusion_inventory_exact_types_verified"] is True
    assert manifest["failure_matrix_row_count"] == 36
    assert manifest["failure_observation_semantics_truthful"] is True
    assert manifest["failure_matrix_uses_actual_registry_validity"] is True
    assert manifest["invalid_candidate_provider_issue_effective_status"] == "open"
    assert manifest["failure_matrix_required_for_issue_resolution"] is True
    assert manifest["effective_open_issue_count"] == 0
    assert manifest["effective_open_issues"] == []
    assert manifest["ready_for_feature_semantics_audit"] is True
    assert manifest["ready_for_tensorization"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in gate.CANONICAL_MASKS
    ]
    for name, digest in manifest["evidence_sha256"].items():
        assert gate._sha(_artifacts()[name]) == digest
    assert gate.MANIFEST_FILE not in manifest["evidence_sha256"]


def test_no_provider_raw_tensor_model_or_training_activity_claimed() -> None:
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    for key in (
        "provider_used", "network_used", "download_used", "raw_read",
        "raw_write", "checkpoint_access", "model_changed",
        "dataloader_changed", "forward_changed", "loss_changed",
        "training_used", "pair_tensor_materialized",
        "pair_tensor_shape_defined", "negative_pair_construction_defined",
        "negative_sampling_defined", "pair_loss_mask_defined",
        "pair_head_implemented", "pair_contrastive_loss_implemented",
    ):
        assert manifest[key] is False


def test_decision_serialization_and_all_artifacts_are_deterministic() -> None:
    builds = [
        gate.build_covapie_real_provider_export_blocking_row_quarantine_materialization_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    ]
    assert builds[0] == builds[1] == builds[2]
    decisions = [
        gate.derive_covapie_real_provider_export_blocking_row_quarantine_materialization_v1(
            ROOT
        )["decision"]
        for _ in range(3)
    ]
    assert decisions[0] == decisions[1] == decisions[2]
    serialized = [
        gate.serialize_covapie_real_provider_export_blocking_row_quarantine_materialization_decision_v1(
            decision
        )
        for decision in decisions
    ]
    assert serialized[0] == serialized[1] == serialized[2]
    with pytest.raises(TypeError):
        gate.serialize_covapie_real_provider_export_blocking_row_quarantine_materialization_decision_v1(
            object()
        )


def test_isolated_import_has_no_output_or_file_side_effects() -> None:
    before = subprocess.run(
        ("git", "status", "--short", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    result = subprocess.run(
        (
            sys.executable, "-B", "-c",
            "import covalent_ext."
            "covapie_real_provider_export_blocking_row_"
            "quarantine_materialization_v1",
        ),
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    after = subprocess.run(
        ("git", "status", "--short", "--untracked-files=all"),
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""
    assert before == after


def test_checker_is_deterministic_and_reports_boundaries() -> None:
    env = {
        **os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"
    }
    first = subprocess.run(
        (sys.executable, "-B", str(CHECKER)), cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    second = subprocess.run(
        (sys.executable, "-B", str(CHECKER)), cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"materialization_outcome=materialized" in first.stdout
    assert b"quarantine_exclusion_matrix_row_count=55" in first.stdout
    assert b"provider_values_resolved=false" in first.stdout
    assert b"ready_for_training=false" in first.stdout


def test_shared_lifecycle_three_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.environ.get(NESTED_ENV) == "1":
        assert _result()["decision"].outcome == "materialized"
        return
    spec = importlib.util.spec_from_file_location("quarantine_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = checker
    spec.loader.exec_module(checker)
    real_capture = lifecycle._capture_state
    states: list[str] = []
    outputs: list[bytes] = []

    def capture(repository, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit", "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        ):
            env = {
                **os.environ, NESTED_ENV: "1",
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src",
            }
            targeted = subprocess.run(
                (
                    sys.executable, "-m", "pytest", "-q", "-p",
                    "no:cacheprovider", checker.EXACT10[1].as_posix(),
                ),
                cwd=repository, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT, tmp_path, base_commit=gate.BASE_COMMIT,
        formal_commit_subject=gate.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit", "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert outputs[0] == outputs[1] == outputs[2]
    assert report.candidate_parent == gate.BASE_COMMIT
    assert report.candidate_subject == gate.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True

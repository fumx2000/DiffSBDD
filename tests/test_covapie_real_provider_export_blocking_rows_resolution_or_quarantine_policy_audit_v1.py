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
    covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1
    as gate,
)

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1.py"
NESTED_ENV = "COVAPIE_BLOCKING_ROW_POLICY_AUDIT_NESTED_LIFECYCLE"


@lru_cache(maxsize=1)
def _result():
    return gate.derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
        ROOT
    )


@lru_cache(maxsize=1)
def _artifacts():
    return gate.build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1(
        ROOT
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


def _classify(**overrides):
    values = {
        "state_field_present": True,
        "code_field_present": True,
        "state": "absent",
        "code": "",
        "provider_provenance_complete": True,
        "residue_identity_unique": True,
        "auth_label_consistent": True,
        "raw_required": False,
        "heuristic_required": False,
        "admit_outcome": "blocked",
        "admit_reason": "BLOCKED",
        "recorded_provider_status": "exported_blocking",
        "recorded_blocking_reason": "BLOCKED",
    }
    values.update(overrides)
    return gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        **values
    )


def test_public_api_and_frozen_decision() -> None:
    assert gate.__all__ == (
        "RealProviderExportBlockingRowsPolicyAuditDecision",
        "RealProviderExportResolutionOrQuarantinePolicyCaseDecision",
        "build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1",
        "classify_covapie_real_provider_export_blocking_row_evidence_v1",
        "derive_covapie_real_provider_export_blocking_rows_policy_audit_v1",
        "evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1",
        "serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1",
    )
    decision = _result()["decision"]
    assert gate.RealProviderExportBlockingRowsPolicyAuditDecision.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "invalid"
    assert tuple(item.name for item in fields(type(decision))) == (
        "schema_version", "outcome", "predecessor_verified",
        "blocking_row_count", "unique_blocking_row_count",
        "admit_004_contract_verified",
        "resolvable_from_committed_evidence_count",
        "quarantine_required_count", "contradictory_or_invalid_count",
        "all_rows_classified", "resolution_or_quarantine_policy_frozen",
        "provider_rows_mutated", "provider_issue_resolved",
        "ready_for_resolution_materialization",
        "ready_for_quarantine_materialization",
        "ready_for_feature_semantics_audit", "ready_for_tensorization",
        "ready_for_training", "recommended_next_step",
    )
    policy = (
        gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
            "POLICY_004"
        )
    )
    assert (
        gate.RealProviderExportResolutionOrQuarantinePolicyCaseDecision
        .__dataclass_params__.frozen
    )
    with pytest.raises(FrozenInstanceError):
        policy.disposition = "invalid"
    assert tuple(item.name for item in fields(type(policy))) == (
        "case_id", "disposition", "reason", "resolution_allowed",
        "quarantine_allowed", "contradiction_resolution_required",
        "provider_row_mutation_allowed", "fails_closed",
    )


def test_base_and_predecessor_sha_and_contract() -> None:
    shown = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", gate.BASE_COMMIT),
        cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.splitlines()
    assert shown == [
        gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_TREE, gate.BASE_SUBJECT
    ]
    for path, digest in gate.FROZEN_SHA256.items():
        assert gate._sha(_base(path)) == digest
    assert gate.FROZEN_SHA256[gate.PREDECESSOR_SOURCE] == (
        "57b1acbf33950e4211d8d9404b3d3c0579f69683dbf4fc60299e0941ab906bea"
    )
    assert gate.FROZEN_SHA256[gate.PREDECESSOR_MANIFEST] == (
        "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152"
    )
    assert gate.FROZEN_SHA256[gate.PREDECESSOR_ISSUES] == (
        "09ee8271157343c4fd39c2edd73e38d6f0e896b8da247d8e3a8588c0b1cd0afa"
    )
    assert _result()["decision"].predecessor_verified is True


def test_issue_origin_and_exact11_are_dynamically_located() -> None:
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    rows = _rows(gate.BLOCKING_MATRIX_FILE)
    assert manifest["blocking_row_count"] == 11
    assert len(rows) == 11
    assert len({row["blocking_row_identity"] for row in rows}) == 11
    assert [row["blocking_row_identity"] for row in rows] == [
        f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)
    ]
    issues = {
        row["issue_id"]: row for row in gate._csv_rows(_base(gate.PREDECESSOR_ISSUES))
    }
    provider = issues[gate.ISSUE_ID]
    assert provider["issue_origin"] == gate.ISSUE_ORIGIN
    assert provider["affected_fields"] == (
        "covalent_residue_insertion_code_state|"
        "covalent_residue_insertion_code"
    )
    assert provider["affected_rules"] == "ADMIT_004"


def test_admit_004_vocabulary_and_exact_state_code_semantics() -> None:
    assert gate.STATE_VOCABULARY == ("absent", "present", "unknown")
    assert gate._state_code_valid("absent", "") is True
    assert gate._state_code_valid("unknown", "") is True
    assert gate._state_code_valid("present", "A") is True
    assert gate._state_code_valid("present", "") is False
    assert gate._state_code_valid("absent", "A") is False
    assert gate._state_code_valid("unknown", "A") is False
    assert gate._state_code_valid("unsupported", "") is False
    assert _result()["decision"].admit_004_contract_verified is True


def test_blank_code_is_not_automatically_absent() -> None:
    unknown = gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state_field_present=True, code_field_present=True,
        state="unknown", code="", provider_provenance_complete=True,
        residue_identity_unique=True, auth_label_consistent=True,
        raw_required=True, heuristic_required=False, admit_outcome="blocked",
        admit_reason=gate.UNKNOWN_REASON,
        recorded_provider_status="exported_blocking",
        recorded_blocking_reason=gate.UNKNOWN_REASON,
    )
    assert unknown[0] == gate.DISPOSITIONS[1]
    absent = gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state_field_present=True, code_field_present=True,
        state="absent", code="", provider_provenance_complete=True,
        residue_identity_unique=True, auth_label_consistent=True,
        raw_required=False, heuristic_required=False, admit_outcome="blocked",
        admit_reason="BLOCKED", recorded_provider_status="exported_blocking",
        recorded_blocking_reason="BLOCKED",
    )
    assert absent[0] == gate.DISPOSITIONS[0]


def test_explicit_insertion_and_no_insertion_resolution_candidates() -> None:
    common = dict(
        state_field_present=True, code_field_present=True,
        provider_provenance_complete=True, residue_identity_unique=True,
        auth_label_consistent=True, raw_required=False,
        heuristic_required=False, admit_outcome="blocked",
        admit_reason="BLOCKED", recorded_provider_status="exported_blocking",
        recorded_blocking_reason="BLOCKED",
    )
    assert gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state="present", code="A", **common
    )[0] == gate.DISPOSITIONS[0]
    assert gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state="absent", code="", **common
    )[0] == gate.DISPOSITIONS[0]


@pytest.mark.parametrize("flag", (0, 1, None, "true"))
@pytest.mark.parametrize("field", ("state_field_present", "code_field_present"))
def test_classifier_rejects_nonexact_presence_flags(
    field: str, flag: object
) -> None:
    with pytest.raises(TypeError, match="exact built-in bool"):
        _classify(**{field: flag})


def test_missing_state_and_missing_code_are_evidence_insufficiency() -> None:
    missing_state = _classify(state_field_present=False, state="", code="")
    missing_code = _classify(
        code_field_present=False, state="absent", code=None
    )
    assert missing_state == (
        gate.DISPOSITIONS[1],
        "missing insertion-code state requires provider re-export or curated explicit evidence",
    )
    assert missing_code == (
        gate.DISPOSITIONS[1],
        "missing insertion-code value field requires provider re-export or curated explicit evidence",
    )
    assert _classify(state="unsupported", code="")[0] == gate.DISPOSITIONS[2]
    assert missing_state != _classify(state="unsupported", code="")


def test_absent_state_with_missing_code_field_is_not_defaulted_to_empty() -> None:
    missing = _classify(
        state_field_present=True, code_field_present=False,
        state="absent", code="",
    )
    explicit = _classify(
        state_field_present=True, code_field_present=True,
        state="absent", code="",
    )
    assert missing[0] == gate.DISPOSITIONS[1]
    assert explicit[0] == gate.DISPOSITIONS[0]


def test_executable_policy_evaluator_exact17_and_unknown_case() -> None:
    decisions = [
        gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
            case_id
        )
        for case_id, _ in gate.POLICY_CASES
    ]
    assert len(decisions) == len({item.case_id for item in decisions}) == 17
    by_id = {item.case_id: item for item in decisions}
    assert by_id["POLICY_004"].disposition == gate.DISPOSITIONS[1]
    assert by_id["POLICY_005"].disposition == gate.DISPOSITIONS[1]
    assert by_id["POLICY_008"].disposition == gate.DISPOSITIONS[2]
    unknown = (
        gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
            "POLICY_UNKNOWN"
        )
    )
    assert unknown.disposition == gate.DISPOSITIONS[2]
    assert unknown.contradiction_resolution_required is True
    assert unknown.resolution_allowed is unknown.quarantine_allowed is False
    with pytest.raises(TypeError):
        gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(  # type: ignore[arg-type]
            4
        )


def test_policy_csv_is_generated_from_executable_evaluator() -> None:
    rows = _rows(gate.POLICY_MATRIX_FILE)
    assert len(rows) == 17
    assert [row["case_id"] for row in rows] == [
        case_id for case_id, _ in gate.POLICY_CASES
    ]
    for row in rows:
        decision = (
            gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                row["case_id"]
            )
        )
        assert row["expected_disposition"] == decision.disposition
        assert row["expected_reason"] == decision.reason
        assert row["resolution_allowed"] == str(decision.resolution_allowed)
        assert row["quarantine_allowed"] == str(decision.quarantine_allowed)
        assert row["contradiction_resolution_required"] == str(
            decision.contradiction_resolution_required
        )
        assert row["provider_row_mutation_allowed"] == str(
            decision.provider_row_mutation_allowed
        )
        assert row["fails_closed"] == str(decision.fails_closed)
        assert row["verified"] == "True"


def test_classifier_and_policy_evaluator_key_cases_are_consistent() -> None:
    case_ids = (
        "POLICY_001", "POLICY_002", "POLICY_003", "POLICY_004",
        "POLICY_005", "POLICY_006", "POLICY_007", "POLICY_008",
        "POLICY_013", "POLICY_014", "POLICY_015", "POLICY_017",
    )
    for case_id in case_ids:
        inputs = gate._policy_classifier_inputs(case_id)
        assert inputs is not None
        classifier = (
            gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
                **inputs
            )
        )
        policy = (
            gate.evaluate_covapie_real_provider_export_resolution_or_quarantine_policy_case_v1(
                case_id
            )
        )
        assert classifier == (policy.disposition, policy.reason)
    assert gate._policy_classifier_consistency_verified() is True


@pytest.mark.parametrize(
    "overrides",
    (
        {"provider_provenance_complete": False},
        {"residue_identity_unique": False},
        {"auth_label_consistent": False},
        {"raw_required": True},
        {"heuristic_required": True},
    ),
)
def test_insufficient_evidence_quarantines(overrides: dict[str, bool]) -> None:
    values = dict(
        state_field_present=True, code_field_present=True,
        state="absent", code="", provider_provenance_complete=True,
        residue_identity_unique=True, auth_label_consistent=True,
        raw_required=False, heuristic_required=False, admit_outcome="blocked",
        admit_reason="BLOCKED", recorded_provider_status="exported_blocking",
        recorded_blocking_reason="BLOCKED",
    )
    values.update(overrides)
    assert gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        **values
    )[0] == gate.DISPOSITIONS[1]


@pytest.mark.parametrize(
    ("state", "code"),
    (("present", ""), ("absent", "A"), ("unknown", "A"), ("invalid", "")),
)
def test_state_code_contradictions_are_invalid(state: str, code: str) -> None:
    result = gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state_field_present=True, code_field_present=True,
        state=state, code=code, provider_provenance_complete=True,
        residue_identity_unique=True, auth_label_consistent=True,
        raw_required=False, heuristic_required=False, admit_outcome="blocked",
        admit_reason="BLOCKED", recorded_provider_status="exported_blocking",
        recorded_blocking_reason="BLOCKED",
    )
    assert result[0] == gate.DISPOSITIONS[2]


def test_outcome_mismatch_and_duplicate_conflict_fail_closed() -> None:
    mismatch = gate.classify_covapie_real_provider_export_blocking_row_evidence_v1(
        state_field_present=True, code_field_present=True,
        state="unknown", code="", provider_provenance_complete=True,
        residue_identity_unique=True, auth_label_consistent=True,
        raw_required=True, heuristic_required=False, admit_outcome="passed",
        admit_reason="", recorded_provider_status="exported_blocking",
        recorded_blocking_reason=gate.UNKNOWN_REASON,
    )
    assert mismatch[0] == gate.DISPOSITIONS[2]
    policy = {row["input_condition"]: row for row in _rows(gate.POLICY_MATRIX_FILE)}
    assert policy["duplicate conflicting evidence"][
        "expected_disposition"
    ] == gate.DISPOSITIONS[2]
    assert policy["duplicate conflicting evidence"][
        "contradiction_resolution_required"
    ] == "True"


def test_all_real_rows_reproduce_block_and_classify_quarantine() -> None:
    rows = _rows(gate.BLOCKING_MATRIX_FILE)
    assert all(row["observed_insertion_code_state"] == "unknown" for row in rows)
    assert all(row["observed_insertion_code"] == "" for row in rows)
    assert all(row["state_code_combination_valid"] == "True" for row in rows)
    assert all(row["admit_004_outcome"] == "blocked" for row in rows)
    assert all(row["admit_004_reason"] == gate.UNKNOWN_REASON for row in rows)
    assert all(row["audit_disposition"] == gate.DISPOSITIONS[1] for row in rows)
    assert all(row["raw_required_to_resolve"] == "True" for row in rows)
    assert all(row["heuristic_inference_required"] == "False" for row in rows)
    assert all(row["verified"] == "True" for row in rows)


def test_evidence_sufficiency_matrix_covers_exact15_items_per_row() -> None:
    rows = _rows(gate.SUFFICIENCY_MATRIX_FILE)
    assert len(rows) == 11 * 15
    grouped: dict[str, set[str]] = {}
    for row in rows:
        grouped.setdefault(row["blocking_row_identity"], set()).add(
            row["evidence_item"]
        )
        assert row["verified"] == "True"
    assert len(grouped) == 11
    assert all(len(items) == 15 for items in grouped.values())


def test_policy_frozen_issue_open_and_dynamic_next_step() -> None:
    decision = _result()["decision"]
    assert decision.outcome == "audited_policy_frozen"
    assert decision.resolvable_from_committed_evidence_count == 0
    assert decision.quarantine_required_count == 11
    assert decision.contradictory_or_invalid_count == 0
    assert decision.all_rows_classified is True
    assert decision.resolution_or_quarantine_policy_frozen is True
    assert decision.provider_rows_mutated is False
    assert decision.provider_issue_resolved is False
    assert decision.ready_for_resolution_materialization is False
    assert decision.ready_for_quarantine_materialization is True
    assert decision.recommended_next_step == (
        "materialize_covapie_real_provider_export_blocking_row_quarantine_v1"
    )


def test_issue_inventory_is_byte_identical_and_continuity_is_preserved() -> None:
    payload = _artifacts()[gate.ISSUE_INVENTORY_FILE]
    assert payload == _base(gate.PREDECESSOR_ISSUES)
    assert gate._sha(payload) == (
        "09ee8271157343c4fd39c2edd73e38d6f0e896b8da247d8e3a8588c0b1cd0afa"
    )
    issue_map = {row["issue_id"]: row for row in gate._csv_rows(payload)}
    assert issue_map["COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"][
        "successor_effective_status"
    ] == "resolved"
    assert issue_map[gate.ISSUE_ID]["successor_effective_status"] == "open"


def test_manifest_safety_and_exact5_masks() -> None:
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    for key in (
        "provider_rows_mutated", "provider_reexport_performed",
        "quarantine_materialized", "resolution_materialized",
        "provider_issue_resolved", "issue_status_changed",
        "ready_for_feature_semantics_audit", "ready_for_tensorization",
        "pair_tensor_materialized", "provider_used", "network_used",
        "download_used", "raw_read", "raw_write", "checkpoint_access",
        "model_changed", "dataloader_changed", "forward_changed",
        "loss_changed", "training_used", "feature_semantics_audit_completed",
        "feature_semantics_known", "unknown_atom_feature_policy_resolved",
        "ready_for_training",
    ):
        assert manifest[key] is False
    assert manifest["canonical_masks"] == [
        {"semantic_name": name, "display_alias": alias}
        for name, alias in gate.CANONICAL_MASKS
    ]
    assert {"semantic_name": "scaffold_only", "display_alias": "B3"} in (
        manifest["canonical_masks"]
    )


def test_three_builds_and_every_evidence_byte_are_deterministic() -> None:
    builds = [
        gate.build_covapie_real_provider_export_blocking_rows_policy_audit_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    ]
    assert builds[0] == builds[1] == builds[2]
    decisions = [
        gate.serialize_covapie_real_provider_export_blocking_rows_policy_audit_decision_v1(
            gate.derive_covapie_real_provider_export_blocking_rows_policy_audit_v1(
                ROOT
            )["decision"]
        )
        for _ in range(3)
    ]
    assert decisions[0] == decisions[1] == decisions[2]


def test_materialized_files_match_builder_and_evidence_sha() -> None:
    for name, payload in _artifacts().items():
        assert (ROOT / gate.OUTPUT_ROOT / name).read_bytes() == payload
    manifest = json.loads(_artifacts()[gate.MANIFEST_FILE])
    for name, digest in manifest["evidence_sha256"].items():
        assert gate._sha(_artifacts()[name]) == digest
    assert manifest["source_inventory_row_count"] == 28
    assert manifest["blocking_row_audit_matrix_row_count"] == 11
    assert manifest["evidence_sufficiency_matrix_row_count"] == 165
    assert manifest["policy_matrix_row_count"] == 17
    assert manifest["issue_inventory_row_count"] == 30
    assert manifest["policy_matrix_executable"] is True
    assert manifest["policy_matrix_classifier_consistency_verified"] is True
    assert manifest["missing_state_disposition"] == gate.DISPOSITIONS[1]
    assert manifest["missing_code_field_disposition"] == gate.DISPOSITIONS[1]
    assert manifest["unsupported_state_disposition"] == gate.DISPOSITIONS[2]


def test_checker_independently_reconstructs_and_is_deterministic() -> None:
    env = {
        **os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"
    }
    first = subprocess.run(
        (sys.executable, "-B", CHECKER.as_posix()), cwd=ROOT, env=env,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    second = subprocess.run(
        (sys.executable, "-B", CHECKER.as_posix()), cwd=ROOT, env=env,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"audit_outcome=audited_policy_frozen" in first.stdout
    assert b"quarantine_required_count=11" in first.stdout
    assert b"provider_issue_resolved=false" in first.stdout
    assert b"ready_for_training=false" in first.stdout


def test_shared_lifecycle_three_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.environ.get(NESTED_ENV) == "1":
        assert _result()["decision"].outcome == "audited_policy_frozen"
        return
    spec = importlib.util.spec_from_file_location("blocking_policy_checker", CHECKER)
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
                (sys.executable, "-m", "pytest", "-q", "-p",
                 "no:cacheprovider", checker.EXACT10[1].as_posix()),
                cwd=repository, env=env, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository, env=env, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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

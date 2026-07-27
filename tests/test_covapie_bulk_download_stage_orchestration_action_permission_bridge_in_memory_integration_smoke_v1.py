"""Tests for the two-chain action-permission bridge integration smoke V1."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle
from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as bridge_contract,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_v1
    as bridge_runtime,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as call_site_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


CHECKER_PATH = (
    ROOT
    / "scripts"
    / (
        "check_covapie_bulk_download_stage_orchestration_action_permission_"
        "bridge_in_memory_integration_smoke_v1.py"
    )
)
NESTED_LIFECYCLE_ENV = (
    "COVAPIE_ACTION_PERMISSION_BRIDGE_IN_MEMORY_SMOKE_NESTED_LIFECYCLE"
)


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_action_permission_bridge_in_memory_smoke_checker",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _report() -> smoke.ActionPermissionBridgeIntegrationSmokeReport:
    return (
        smoke.run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke()
    )


def test_public_no_argument_api_and_frozen_dataclasses_are_exact() -> None:
    signature = inspect.signature(
        smoke.run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke
    )
    assert tuple(signature.parameters) == ()
    assert smoke.ActionPermissionBridgeChainObservation.__dataclass_params__.frozen
    assert (
        smoke.ActionPermissionBridgeIntegrationSmokeReport.__dataclass_params__.frozen
    )
    assert tuple(
        item.name
        for item in fields(smoke.ActionPermissionBridgeChainObservation)
    ) == (
        "profile_name",
        "source_mode",
        "stage_scope_id",
        "candidate_count",
        "admit_014_outcome",
        "candidate_combined_outcomes",
        "call_site_outcome",
        "call_site_reason",
        "bridge_outcome",
        "bridge_reason",
        "source_lineage_verified",
        "transition_eligible",
        "action_permission_granted",
        "download_action_invoked",
        "bridge_io_used",
    )
    with pytest.raises(FrozenInstanceError):
        _report().observations[0].source_mode = "changed"


def test_current_blocked_actual_chain_is_exact() -> None:
    item = _report().observations[0]
    assert (
        item.profile_name,
        item.source_mode,
        item.stage_scope_id,
        item.candidate_count,
        item.admit_014_outcome,
        item.candidate_combined_outcomes,
        item.call_site_outcome,
        item.call_site_reason,
        item.bridge_outcome,
        item.bridge_reason,
        item.source_lineage_verified,
        item.transition_eligible,
    ) == (
        "canonical_single_candidate_exact4",
        "current_blocked",
        "download_execution_permission",
        1,
        "blocked",
        ("blocked",),
        "blocked",
        "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED",
        "blocked",
        "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED",
        True,
        False,
    )


def test_future_eligible_actual_chain_stops_before_transition() -> None:
    item = _report().observations[1]
    assert (
        item.profile_name,
        item.source_mode,
        item.stage_scope_id,
        item.candidate_count,
        item.admit_014_outcome,
        item.candidate_combined_outcomes,
        item.call_site_outcome,
        item.call_site_reason,
        item.bridge_outcome,
        item.bridge_reason,
        item.source_lineage_verified,
        item.transition_eligible,
    ) == (
        "canonical_single_candidate_exact4",
        "future_eligible",
        "download_execution_permission",
        1,
        "passed",
        ("passed",),
        "blocked",
        "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED",
        "eligible",
        "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE",
        True,
        True,
    )


def test_report_has_zero_permission_transition_action_and_io() -> None:
    report = _report()
    assert report.observation_count == len(report.observations) == 2
    assert report.actual_orchestrator_called is True
    assert report.actual_call_site_runtime_called is True
    assert report.actual_bridge_runtime_called is True
    assert report.runtime_identities_unchanged is True
    assert report.monkeypatch_used_for_success_evidence is False
    assert report.permission_transition_attempted is False
    assert report.permission_transition_completed is False
    assert (
        report.transition_eligible_count,
        report.action_permission_granted_count,
        report.download_action_count,
        report.bridge_io_count,
    ) == (1, 0, 0, 0)
    assert report.ready_for_download is False
    assert report.ready_for_training is False
    assert all(
        (
            item.action_permission_granted,
            item.download_action_invoked,
            item.bridge_io_used,
        )
        == (False, False, False)
        for item in report.observations
    )


def test_checker_independently_builds_two_complete_exact19_chains() -> None:
    checker = _checker()
    chains = checker.build_actual_chains()
    rows = checker.build_exact19_rows(chains)
    assert len(chains) == 2
    assert len(rows) == 2 * len(bridge_contract.DECISION_FIELDS) == 38
    assert all(row["verified"] == "true" for row in rows)
    assert {row["source_mode"] for row in rows} == {
        "current_blocked",
        "future_eligible",
    }
    assert {row["decision_field"] for row in rows} == set(
        bridge_contract.DECISION_FIELDS
    )


def test_three_reports_serialization_matrix_and_evidence_are_deterministic() -> None:
    reports = tuple(_report() for _ in range(3))
    serialized = tuple(
        smoke.serialize_integration_smoke_report(report)
        for report in reports
    )
    assert reports[0] == reports[1] == reports[2]
    assert serialized[0] == serialized[1] == serialized[2]
    assert b"0x" not in serialized[0]
    checker = _checker()
    matrices = tuple(checker.build_exact19_rows() for _ in range(3))
    assert matrices[0] == matrices[1] == matrices[2]
    assert checker.build_evidence_payloads() == checker.build_evidence_payloads()


def test_success_preserves_all_runtime_and_registered_handler_identities() -> None:
    before = (
        orchestration_runtime.orchestrate_stage_admission_scope,
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )
    _report()
    after = (
        orchestration_runtime.orchestrate_stage_admission_scope,
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )
    assert all(before[index] is after[index] for index in (0, 1, 2, 3, 4, 6))
    assert all(
        left[0] == right[0] and left[1] is right[1]
        for left, right in zip(before[5], after[5], strict=True)
    )


@pytest.mark.parametrize(
    ("target", "attribute"),
    (
        (orchestration_runtime, "orchestrate_stage_admission_scope"),
        (
            call_site_runtime,
            "evaluate_bulk_download_stage_orchestration_call_site",
        ),
        (
            bridge_runtime,
            "evaluate_bulk_download_stage_orchestration_action_permission_bridge",
        ),
        (dispatch_runtime, "evaluate_admission_rule"),
        (
            aggregation_runtime,
            "aggregate_admission_rule_evaluations",
        ),
    ),
)
def test_preexisting_callable_replacement_is_detected_before_execution(
    monkeypatch: pytest.MonkeyPatch, target: object, attribute: str
) -> None:
    def replacement(*_args, **_kwargs):
        raise AssertionError("replacement must not execute")

    monkeypatch.setattr(target, attribute, replacement)
    with pytest.raises(RuntimeError, match="identity"):
        _report()


def test_preexisting_registry_and_handler_replacements_are_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(
            dispatch_runtime,
            "EVALUATOR_REGISTRY",
            dict(dispatch_runtime.EVALUATOR_REGISTRY),
        )
        with pytest.raises(RuntimeError, match="identity"):
            _report()
    rule_id = next(iter(dispatch_runtime.EVALUATOR_REGISTRY))
    replaced_handlers = dict(dispatch_runtime.EVALUATOR_REGISTRY)
    replaced_handlers[rule_id] = lambda *_args, **_kwargs: None
    with monkeypatch.context() as patch:
        patch.setattr(
            dispatch_runtime,
            "EVALUATOR_REGISTRY",
            MappingProxyType(replaced_handlers),
        )
        with pytest.raises(RuntimeError, match="identity"):
            _report()


def test_provenance_identity_safety_issue_and_manifest_evidence() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    provenance = checker.build_fixture_provenance_rows()
    identities = checker.build_runtime_identity_rows()
    assert len(provenance) == 2
    assert tuple(row["source_mode"] for row in provenance) == (
        "current_blocked",
        "future_eligible",
    )
    assert all(row["forged_success_source"] == "false" for row in provenance)
    assert len(identities) == 7
    assert all(row["identity_unchanged"] == "true" for row in identities)
    assert len(payloads[checker.SAFETY_NAME].decode().splitlines()) == 24
    issue = payloads[checker.ISSUE_NAME]
    assert hashlib.sha256(issue).hexdigest() == (
        "fb4d2dfae7ffc056e3856c94e2f5a135"
        "d468eb3801144f9a698f95d9b812ace7"
    )
    assert issue == (ROOT / checker.PREDECESSOR_ISSUE_PATH).read_bytes()
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    assert manifest["canonical_masks"][3] == {
        "semantic_name": "scaffold_only",
        "alias": "B3",
    }
    assert manifest["effective_open_issues"] == [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]
    assert manifest["permission_transition_attempted"] is False
    assert manifest["permission_transition_completed"] is False
    assert manifest["transition_eligible_count"] == 1
    assert manifest["action_permission_granted_count"] == 0
    assert manifest["download_action_count"] == 0
    assert manifest["bridge_io_count"] == 0
    assert manifest["ready_for_download"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["recommended_next_step"] == smoke.RECOMMENDED_NEXT_STEP
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]


def test_exact6_evidence_matches_materialized_files() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    assert tuple(payloads) == checker.OUTPUT_NAMES
    for name, payload in payloads.items():
        path = ROOT / checker.OUTPUT_ROOT / name
        assert path.is_file() and not path.is_symlink()
        assert path.read_bytes() == payload


def test_source_ast_has_actual_chain_and_no_action_surface() -> None:
    checker = _checker()
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert {
        "orchestration_runtime.orchestrate_stage_admission_scope",
        "call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site",
        "bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge",
    } <= calls
    assert not any(
        name.endswith(
            (
                "_build_bridge_decision",
                "_project_source",
                "_source_lineage_is_exact",
            )
        )
        for name in calls
    )
    assert "setattr(" not in source
    assert "Callable" not in source
    checker._verify_source_policy()


def test_checker_process_reports_required_closed_summary() -> None:
    result = subprocess.run(
        (sys.executable, "-B", str(CHECKER_PATH)),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(SRC),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == b""
    summary = json.loads(result.stdout)
    assert summary["observation_count"] == 2
    assert summary["exact19_matrix_rows"] == 38
    assert summary["current_blocked"] is True
    assert summary["future_eligible"] is True
    assert summary["runtime_identities_unchanged"] is True
    assert summary["permission_transition_attempted"] is False
    assert summary["permission_transition_completed"] is False
    assert summary["transition_eligible_count"] == 1
    assert summary["action_permission_granted_count"] == 0
    assert summary["download_action_count"] == 0
    assert summary["bridge_io_count"] == 0
    assert summary["ready_for_download"] is False
    assert summary["ready_for_training"] is False


def test_lifecycle_uses_shared_harness_with_exact10() -> None:
    checker = _checker()
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "lifecycle.exercise_hermetic_git_lifecycle_matrix" in calls
    assert len(checker.EXACT10) == 10


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert smoke.BASE_COMMIT == (
            "beb42c497d3f0e47e009b2dc84aac929938824e5"
        )
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    states: list[str] = []
    targeted_outputs: list[bytes] = []
    checker_outputs: list[bytes] = []

    def capture_with_validation(repository, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        ):
            environment = os.environ.copy()
            environment[NESTED_LIFECYCLE_ENV] = "1"
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONPATH"] = "src"
            targeted = subprocess.run(
                (
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    checker.EXACT10[1].as_posix(),
                ),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            checked = subprocess.run(
                (
                    sys.executable,
                    "-B",
                    checker.EXACT10[2].as_posix(),
                ),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            targeted_outputs.append(targeted.stdout)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture_with_validation)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=checker.BASE_COMMIT,
        formal_commit_subject=checker.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert len(targeted_outputs) == 3
    assert all(b"passed" in output for output in targeted_outputs)
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == checker.BASE_COMMIT
    assert report.candidate_subject == checker.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert not any(
        Path(state.repository_path).exists()
        for state in (
            report.pre_commit,
            report.detached_candidate_post_commit,
            report.formal_main_post_commit_unpushed,
            report.formal_main_post_push,
        )
    )

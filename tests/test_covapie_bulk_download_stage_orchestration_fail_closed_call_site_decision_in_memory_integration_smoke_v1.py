"""Tests for the actual-chain call-site decision integration smoke V1."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

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
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as decision_contract,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as decision_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as orchestration_contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


CHECKER_PATH = (
    ROOT
    / "scripts"
    / (
        "check_covapie_bulk_download_stage_orchestration_fail_closed_call_"
        "site_decision_in_memory_integration_smoke_v1.py"
    )
)
NESTED_LIFECYCLE_ENV = (
    "COVAPIE_CALL_SITE_DECISION_IN_MEMORY_SMOKE_NESTED_LIFECYCLE"
)


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_call_site_decision_in_memory_smoke_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _report() -> smoke.CallSiteDecisionIntegrationSmokeReport:
    return (
        smoke.run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke()
    )


def test_public_smoke_api_is_no_argument_frozen_and_exact() -> None:
    signature = inspect.signature(
        smoke.run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke
    )
    assert tuple(signature.parameters) == ()
    assert smoke.CallSiteDecisionChainObservation.__dataclass_params__.frozen
    assert (
        smoke.CallSiteDecisionIntegrationSmokeReport.__dataclass_params__.frozen
    )
    assert tuple(
        field.name
        for field in fields(smoke.CallSiteDecisionChainObservation)
    ) == (
        "fixture_profile",
        "source_path_kind",
        "scope_id",
        "candidate_count",
        "orchestrator_completed",
        "orchestration_error_code",
        "decision_outcome",
        "decision_reason",
        "decision_source_kind",
        "decision_source_scope_id",
        "decision_source_error_code",
        "invalid_candidate_indexes",
        "blocked_candidate_indexes",
        "failing_candidate_indexes",
        "action_permission_granted",
        "download_action_invoked",
        "call_site_io_used",
    )


def test_report_has_fixed_six_actual_observations_and_closed_counts() -> None:
    report = _report()
    assert report.observation_count == len(report.observations) == 6
    assert report.actual_orchestrator_called is True
    assert report.actual_decision_runtime_called is True
    assert report.actual_orchestration_error_consumed is True
    assert report.runtime_callable_identities_unchanged is True
    assert report.monkeypatch_used_for_success_evidence is False
    assert (
        report.authorized_decision_count,
        report.download_action_count,
        report.call_site_io_count,
    ) == (0, 0, 0)
    assert (
        report.network_used,
        report.provider_used,
        report.download_used,
        report.training_used,
        report.ready_for_download,
        report.ready_for_training,
    ) == (False, False, False, False, False, False)


def test_single_candidate_exact4_result_paths_obey_scope_precedence() -> None:
    observations = _report().observations[:4]
    assert tuple(item.scope_id for item in observations) == (
        orchestration_contract.SCOPE_IDS
    )
    download, *wrong_scope = observations
    assert (
        download.source_path_kind,
        download.candidate_count,
        download.decision_outcome,
        download.decision_reason,
        download.blocked_candidate_indexes,
        download.failing_candidate_indexes,
    ) == (
        "orchestration_result",
        1,
        "blocked",
        "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED",
        (0,),
        (0,),
    )
    for item in wrong_scope:
        assert item.candidate_count == 1
        assert item.decision_outcome == "invalid"
        assert item.decision_reason == "BULK_DOWNLOAD_STAGE_SCOPE_INVALID"
        assert (
            item.invalid_candidate_indexes,
            item.blocked_candidate_indexes,
            item.failing_candidate_indexes,
        ) == ((), (), ())


def test_two_candidate_training_result_is_wrong_scope_before_diagnostics() -> None:
    item = _report().observations[4]
    assert item.fixture_profile == "canonical_two_candidate_training_scope"
    assert item.scope_id == "training_execution_admission_permission"
    assert item.candidate_count == 2
    assert item.decision_outcome == "invalid"
    assert item.decision_reason == "BULK_DOWNLOAD_STAGE_SCOPE_INVALID"
    assert (
        item.invalid_candidate_indexes,
        item.blocked_candidate_indexes,
        item.failing_candidate_indexes,
    ) == ((), (), ())
    assert item.action_permission_granted is False


def test_actual_orchestration_error_is_consumed_unmodified_fail_closed() -> None:
    item = _report().observations[5]
    assert item.source_path_kind == "orchestration_error"
    assert item.orchestrator_completed is False
    assert item.scope_id == smoke.INVALID_SCOPE_ID
    assert item.orchestration_error_code in orchestration_contract.ERROR_CODES
    assert item.orchestration_error_code == (
        "STAGE_ORCHESTRATION_SCOPE_ID_INVALID"
    )
    assert item.decision_source_error_code == item.orchestration_error_code
    assert item.decision_outcome == "invalid"
    assert item.decision_reason == (
        "BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED"
    )
    assert item.candidate_count == 0


def test_every_observation_has_closed_action_and_io_fields() -> None:
    for item in _report().observations:
        assert item.decision_source_scope_id == item.scope_id
        assert item.action_permission_granted is False
        assert item.download_action_invoked is False
        assert item.call_site_io_used is False


def test_three_runs_and_serialized_reports_are_byte_identical() -> None:
    reports = tuple(_report() for _ in range(3))
    serialized = tuple(
        smoke.serialize_integration_smoke_report(report)
        for report in reports
    )
    assert reports[0] == reports[1] == reports[2]
    assert serialized[0] == serialized[1] == serialized[2]
    assert b"0x" not in serialized[0]


def test_success_path_preserves_all_runtime_callable_identities() -> None:
    before = (
        orchestration_runtime.orchestrate_stage_admission_scope,
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )
    _report()
    after = (
        orchestration_runtime.orchestrate_stage_admission_scope,
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )
    assert all(before[index] is after[index] for index in (0, 1, 2, 3, 5))
    assert all(
        left[0] == right[0] and left[1] is right[1]
        for left, right in zip(before[4], after[4], strict=True)
    )


@pytest.mark.parametrize(
    ("target", "attribute"),
    (
        (orchestration_runtime, "orchestrate_stage_admission_scope"),
        (
            decision_runtime,
            "evaluate_bulk_download_stage_orchestration_call_site",
        ),
        (dispatch_runtime, "evaluate_admission_rule"),
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


def test_preexisting_registry_replacement_is_detected_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dispatch_runtime,
        "EVALUATOR_REGISTRY",
        dict(dispatch_runtime.EVALUATOR_REGISTRY),
    )
    with pytest.raises(RuntimeError, match="identity"):
        _report()


def test_checker_independently_executes_exact15_result_and_error_matrices() -> None:
    checker = _checker()
    result_chains, error_chain = checker.build_actual_chains()
    result_rows = checker.build_result_rows(result_chains)
    error_rows = checker.build_error_rows(error_chain)
    assert len(result_chains) == 5
    assert type(error_chain[1]) is orchestration_contract.StageAdmissionOrchestrationError
    assert len(result_rows) == 5 * len(decision_contract.DECISION_FIELDS) == 75
    assert len(error_rows) == len(decision_contract.DECISION_FIELDS) == 15
    assert all(row["verified"] == "true" for row in (*result_rows, *error_rows))
    assert {
        row["decision_exact15_field"] for row in result_rows
    } == set(decision_contract.DECISION_FIELDS)


def test_provenance_safety_and_issue_continuity_are_direct() -> None:
    checker = _checker()
    provenance = checker.build_fixture_provenance_rows()
    assert len(provenance) == 6
    assert all(
        row["verified"] == "true"
        and "no_forged_source" in row["projection_policy"]
        for row in provenance
    )
    payloads = checker.build_evidence_payloads()
    assert len(payloads[checker.SAFETY_NAME].decode().splitlines()) == (
        len(checker.SAFETY_ITEMS) + 1
    )
    issue = payloads[checker.ISSUE_NAME]
    assert hashlib.sha256(issue).hexdigest() == (
        "fb4d2dfae7ffc056e3856c94e2f5a135"
        "d468eb3801144f9a698f95d9b812ace7"
    )
    assert issue == (ROOT / checker.PREDECESSOR_ISSUE_PATH).read_bytes()


def test_evidence_exact6_is_deterministic_and_matches_files() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    assert first == second
    assert tuple(first) == checker.OUTPUT_NAMES
    for name, payload in first.items():
        path = ROOT / checker.OUTPUT_ROOT / name
        assert path.is_file() and not path.is_symlink()
        assert path.read_bytes() == payload


def test_manifest_preserves_masks_gates_counts_and_hashes() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    assert manifest["canonical_masks"] == [
        {"semantic_name": "warhead_only", "alias": "A"},
        {"semantic_name": "linker_plus_warhead", "alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
        {"semantic_name": "scaffold_only", "alias": "B3"},
        {
            "semantic_name": "scaffold_plus_linker_plus_warhead",
            "alias": "C",
        },
    ]
    assert manifest["effective_open_issues"] == [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]
    assert manifest["result_exact15_row_count"] == 75
    assert manifest["error_exact15_row_count"] == 15
    assert manifest["authorized_decision_count"] == 0
    assert manifest["download_action_count"] == 0
    assert manifest["call_site_io_count"] == 0
    assert manifest["current_permission"] is False
    assert manifest["action_permission_granted"] is False
    assert manifest["ready_for_download"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["feature_semantics_known"] is False
    assert manifest["unknown_atom_feature_policy"] == (
        "UNKNOWN_ATOM_FEATURE_POLICY"
    )
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]
    assert all(
        manifest["evidence_sha256"][name]
        == hashlib.sha256(payloads[name]).hexdigest()
        for name in checker.CSV_NAMES
    )


def test_source_ast_proves_no_success_replacement_injection_or_shortcut() -> None:
    checker = _checker()
    smoke_path = ROOT / checker.EXACT10[0]
    source = smoke_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("run_covapie_bulk_download")
    )
    assert not run_node.args.args
    assert not run_node.args.kwonlyargs
    assert run_node.args.vararg is None and run_node.args.kwarg is None
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert (
        "orchestration_runtime.orchestrate_stage_admission_scope" in calls
    )
    assert (
        "decision_runtime.evaluate_bulk_download_stage_orchestration_call_site"
        in calls
    )
    assert not any(
        name.endswith(
            (
                "classify_bulk_download_stage_orchestration_call_site_contract_design",
                "_build_decision",
                "_stage_result_is_valid",
                "_orchestration_error_is_valid",
            )
        )
        for name in calls
    )
    assert "monkeypatch" not in {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    assert "setattr(" not in source
    assert "Callable" not in source
    checker._verify_source_policy()


def test_lifecycle_is_shared_harness_only() -> None:
    checker = _checker()
    test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(test_tree)
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
            "6e5f3b02183086fea4bb4f35fd03a5c5def7ed8e"
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

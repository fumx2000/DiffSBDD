"""Tests for the stage-global in-memory integration smoke V1."""

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
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_IN_MEMORY_SMOKE_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_in_memory_smoke_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_api_is_no_argument_frozen_and_injection_free() -> None:
    signature = inspect.signature(
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke
    )
    assert tuple(signature.parameters) == ()
    for value_type in (
        smoke.CanonicalInMemoryFixtureProfile,
        smoke.InMemoryIntegrationCandidateObservation,
        smoke.InMemoryIntegrationScopeObservation,
        smoke.InMemoryIntegrationSmokeReport,
    ):
        assert value_type.__dataclass_params__.frozen is True
    assert tuple(
        field.name
        for field in fields(smoke.InMemoryIntegrationSmokeReport)
    ) == (
        "observations",
        "direct_dispatch_parity_verified",
        "direct_aggregation_parity_verified",
        "committed_runtime_identity_unchanged",
        "stage_global_identity_reuse_verified",
        "normal_retained_vector_identity_verified",
        "network_used",
        "provider_used",
        "download_used",
        "training_used",
        "ready_for_training",
    )


def test_fixture_profiles_exact4_identity_and_two_candidate_contract() -> None:
    single, two = smoke.build_canonical_in_memory_fixture_profiles()
    assert (single.fixture_profile, two.fixture_profile) == (
        smoke.FIXTURE_PROFILE_SINGLE,
        smoke.FIXTURE_PROFILE_TWO,
    )
    assert single.scopes == contract.SCOPE_IDS
    assert two.scopes == ("training_execution_admission_permission",)
    assert len(single.candidate_inputs) == 1
    assert len(two.candidate_inputs) == 2
    assert (
        two.candidate_inputs[0].candidate_record
        is not two.candidate_inputs[1].candidate_record
    )
    assert (
        two.candidate_inputs[0].evaluation_context
        is not two.candidate_inputs[1].evaluation_context
    )
    assert two.batch_context["batch_candidate_record_ids"] == (
        "REC_1",
        "REC_2",
    )
    assert two.batch_context["batch_duplicate_identity_keys"] == ()
    assert len(
        {
            item.candidate_record["duplicate_identity_key"]
            for item in two.candidate_inputs
        }
    ) == 2
    before = single.candidate_inputs[0]
    for _scope in single.scopes:
        assert single.candidate_inputs[0] is before
        assert single.candidate_inputs[0].candidate_record is before.candidate_record
        assert (
            single.candidate_inputs[0].evaluation_context
            is before.evaluation_context
        )


def test_fixture_provenance_is_complete_resolved_and_source_backed() -> None:
    checker = _checker()
    rows = smoke.build_fixture_provenance_rows()
    assert len(rows) == 113
    assert {row["fixture_profile"] for row in rows} == set(
        smoke.FIXTURE_PROFILE_IDS
    )
    assert all(
        row["ambiguity_status"] == "resolved_from_committed_contract"
        and row["verified"] == "true"
        and row["semantic_source_path"] in checker.COMMITTED_SOURCE_SHA256
        and not row["canonical_value"].startswith("<")
        for row in rows
    )
    assert not any("0x" in row["canonical_value"] for row in rows)
    assert {
        row["container_name"].split("[", 1)[0] for row in rows
    } == {
        "candidate_record",
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    }


def test_actual_smoke_outputs_match_committed_rule_semantics() -> None:
    report = (
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()
    )
    assert len(report.observations) == 5
    assert report.direct_dispatch_parity_verified is True
    assert report.direct_aggregation_parity_verified is True
    assert report.committed_runtime_identity_unchanged is True
    assert report.stage_global_identity_reuse_verified is True
    assert report.normal_retained_vector_identity_verified is True
    assert (
        report.network_used,
        report.provider_used,
        report.download_used,
        report.training_used,
        report.ready_for_training,
    ) == (False, False, False, False, False)
    assert tuple(
        (item.dispatcher_call_count, item.aggregator_call_count)
        for item in report.observations
    ) == ((11, 1), (13, 1), (14, 1), (15, 1), (28, 2))
    for observation in report.observations:
        assert observation.orchestration_io_used is False
        assert observation.action_permission_granted is False
        for candidate in observation.candidate_observations:
            result = dict(
                zip(
                    candidate.ordered_rule_ids,
                    zip(
                        candidate.ordered_outcomes,
                        candidate.ordered_reasons,
                        strict=True,
                    ),
                    strict=True,
                )
            )
            assert result["ADMIT_014"] == (
                "blocked",
                "BULK_DOWNLOAD_NOT_AUTHORIZED",
            )
            if "ADMIT_015" in result:
                assert result["ADMIT_015"] == (
                    "blocked",
                    "TRAINING_NOT_AUTHORIZED",
                )
            assert all(
                outcome == "passed"
                for rule_id, (outcome, _reason) in result.items()
                if rule_id not in ("ADMIT_014", "ADMIT_015")
            )
            assert candidate.combined_outcome == "blocked"
            assert candidate.combined_reason == (
                "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED"
            )


def test_three_actual_smoke_runs_and_serializations_are_byte_stable() -> None:
    reports = tuple(
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()
        for _ in range(3)
    )
    serialized = tuple(smoke.serialize_smoke_report(value) for value in reports)
    assert reports[0] == reports[1] == reports[2]
    assert serialized[0] == serialized[1] == serialized[2]
    assert b"0x" not in serialized[0]


def test_checker_independent_direct_baseline_has_full_true_parity() -> None:
    rows = _checker().build_direct_parity_rows()
    assert len(rows) == 1323
    assert all(row["parity_verified"] == "true" for row in rows)
    assert {row["comparison_area"] for row in rows} == {
        "unified_stage_global_result",
        "unified_candidate_result",
        "combined_verdict",
        "stage_result",
        "stage_global_identity_reuse",
        "normal_retained_vector_identity",
    }
    assert {
        row["comparison_item"].split(".", 1)[-1]
        for row in rows
        if row["comparison_area"].startswith("unified_")
    } >= set(dispatch_runtime.RESULT_FIELDS)
    assert {
        row["comparison_item"]
        for row in rows
        if row["comparison_area"] == "combined_verdict"
    } == set(aggregation_runtime.RESULT_FIELDS)
    identity_rows = tuple(
        row
        for row in rows
        if row["comparison_area"]
        in (
            "stage_global_identity_reuse",
            "normal_retained_vector_identity",
        )
    )
    assert len(identity_rows) == 15
    assert sum(
        row["comparison_area"] == "stage_global_identity_reuse"
        for row in identity_rows
    ) == 9
    assert sum(
        row["comparison_area"] == "normal_retained_vector_identity"
        for row in identity_rows
    ) == 6
    assert all(
        row["orchestrator_value"] == "true"
        and row["direct_baseline_value"] == "true"
        and row["parity_verified"] == "true"
        for row in identity_rows
    )


def test_evidence_payloads_are_deterministic_and_match_exact6() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    assert first == second
    assert tuple(first) == checker.OUTPUT_NAMES
    for name, payload in first.items():
        path = ROOT / checker.OUTPUT_ROOT / name
        assert path.is_file() and not path.is_symlink()
        assert path.read_bytes() == payload


def test_manifest_safety_masks_issues_and_training_gate() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    required_false = (
        "monkeypatch_used_for_success_evidence",
        "network_used",
        "provider_used",
        "download_used",
        "training_used",
        "current_permission",
        "action_permission_granted",
        "feature_semantics_audit_completed",
        "feature_semantics_known",
        "unknown_atom_feature_policy_resolved",
        "ready_for_training",
    )
    assert all(manifest[name] is False for name in required_false)
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["stage_global_result_identity_reuse_verified"] is True
    assert manifest["normal_retained_vector_identity_verified"] is True
    assert tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    ) == smoke.CANONICAL_MASKS
    assert tuple(manifest["effective_open_issues"]) == (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    )
    assert manifest["recommended_next_step"] == smoke.RECOMMENDED_NEXT_STEP
    assert payloads[checker.ISSUE_NAME] == (
        ROOT / checker.PREDECESSOR_ISSUE_PATH
    ).read_bytes()


def test_safety_audit_is_exact_closed_false_vector() -> None:
    checker = _checker()
    payload = checker.build_evidence_payloads()[checker.SAFETY_NAME]
    text = payload.decode("utf-8")
    assert len(text.splitlines()) == 20
    assert all(
        f"{item},false,false,true\n" in text
        for item in checker.SAFETY_ITEMS
    )


def test_success_path_does_not_replace_actual_runtime_identities() -> None:
    before = (
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
        orchestration_runtime.orchestrate_stage_admission_scope,
    )
    smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()
    after = (
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
        orchestration_runtime.orchestrate_stage_admission_scope,
    )
    assert before[0] is after[0]
    assert before[1] is after[1]
    assert all(
        left[0] == right[0] and left[1] is right[1]
        for left, right in zip(before[2], after[2], strict=True)
    )
    assert before[3] is after[3]
    assert before[4] is after[4]


def test_actual_orchestrator_identity_graph_is_verified_for_every_scope() -> None:
    observations = 0
    stage_identity_edges = 0
    retained_vector_edges = 0
    for fixture in smoke.build_canonical_in_memory_fixture_profiles():
        for scope_id in fixture.scopes:
            orchestrated = (
                orchestration_runtime.orchestrate_stage_admission_scope(
                    scope_id,
                    fixture.candidate_inputs,
                    batch_context=fixture.batch_context,
                    stage_authorization_context=(
                        fixture.stage_authorization_context
                    ),
                )
            )
            vectors = tuple(
                item.ordered_rule_evaluations
                for item in orchestrated.candidate_results
            )
            verdicts = tuple(
                item.combined_verdict
                for item in orchestrated.candidate_results
            )
            smoke._validate_stage_global_identity_reuse(
                orchestrated.required_rule_ids,
                orchestrated.stage_global_rule_evaluations,
                vectors,
            )
            smoke._validate_normal_retained_vector_identity(
                vectors, verdicts
            )
            for candidate in orchestrated.candidate_results:
                for stage_index, rule_id in enumerate(
                    orchestrated.stage_global_rule_ids
                ):
                    vector_index = orchestrated.required_rule_ids.index(
                        rule_id
                    )
                    assert (
                        candidate.ordered_rule_evaluations[vector_index]
                        is orchestrated.stage_global_rule_evaluations[
                            stage_index
                        ]
                    )
                    stage_identity_edges += 1
                assert (
                    candidate.combined_verdict.rule_evaluations
                    is candidate.ordered_rule_evaluations
                )
                retained_vector_edges += 1
            observations += 1
    assert observations == 5
    assert stage_identity_edges == 9
    assert retained_vector_edges == 6


def test_identity_validators_reject_equal_but_copied_objects() -> None:
    fixture = smoke.build_canonical_in_memory_fixture_profiles()[0]
    scope_id = fixture.scopes[0]
    orchestrated = orchestration_runtime.orchestrate_stage_admission_scope(
        scope_id,
        fixture.candidate_inputs,
        batch_context=fixture.batch_context,
        stage_authorization_context=fixture.stage_authorization_context,
    )
    original_stage = orchestrated.stage_global_rule_evaluations[0]
    copied_stage = type(original_stage)(**vars(original_stage))
    assert copied_stage == original_stage
    assert copied_stage is not original_stage
    vector = orchestrated.candidate_results[0].ordered_rule_evaluations
    stage_vector_index = orchestrated.required_rule_ids.index(
        original_stage.admission_rule_id
    )
    copied_stage_vector_values = list(vector)
    copied_stage_vector_values[stage_vector_index] = copied_stage
    copied_stage_vector = tuple(copied_stage_vector_values)
    assert copied_stage_vector == vector
    assert copied_stage_vector is not vector
    with pytest.raises(RuntimeError, match="stage-global result identity"):
        smoke._validate_stage_global_identity_reuse(
            orchestrated.required_rule_ids,
            orchestrated.stage_global_rule_evaluations,
            (copied_stage_vector,),
        )

    copied_vector = tuple(list(vector))
    assert copied_vector == vector
    assert copied_vector is not vector
    with pytest.raises(RuntimeError, match="retained-vector identity"):
        smoke._validate_normal_retained_vector_identity(
            (copied_vector,),
            (orchestrated.candidate_results[0].combined_verdict,),
        )


def test_preexisting_dispatcher_replacement_is_detected_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(*_args, **_kwargs):
        raise AssertionError("fake dispatcher must not execute")

    monkeypatch.setattr(dispatch_runtime, "evaluate_admission_rule", fake)
    with pytest.raises(RuntimeError, match="dispatcher"):
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()


def test_preexisting_registry_replacement_is_detected_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dispatch_runtime,
        "EVALUATOR_REGISTRY",
        dict(dispatch_runtime.EVALUATOR_REGISTRY),
    )
    with pytest.raises(RuntimeError, match="registry"):
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()


def test_sources_have_no_success_runtime_replacement_or_injection() -> None:
    checker = _checker()
    source_path = ROOT / checker.EXACT10[0]
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    run_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke"
    )
    assert run_node.args.args == []
    assert run_node.args.defaults == []
    assert run_node.args.kwonlyargs == []
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"setattr", "delattr"}
        for node in ast.walk(run_node)
    )
    source = source_path.read_text(encoding="utf-8")
    assert "fake dispatcher" not in source
    assert "registry injection" not in source
    assert "monkeypatch" not in source
    assert sum(
        isinstance(node, ast.Compare)
        and any(isinstance(operator, (ast.Is, ast.IsNot)) for operator in node.ops)
        for node in ast.walk(tree)
    ) >= 4


def test_lifecycle_sources_only_use_shared_harness_contract() -> None:
    checker = _checker()
    test_source = Path(__file__).read_text(encoding="utf-8")
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    forbidden_commands = tuple(
        " ".join(parts)
        for parts in (
            ("git", "init", "--bare"),
            ("git", "clone"),
            ("git", "worktree", "add"),
            ("git", "push"),
        )
    )
    assert not any(
        command in test_source or command in checker_source
        for command in forbidden_commands
    )
    tree = ast.parse(test_source)
    calls = tuple(
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    )
    assert (
        "lifecycle.exercise_hermetic_git_lifecycle_matrix" in calls
    )
    assert not any(
        isinstance(node, ast.FunctionDef)
        and any(token in node.name for token in ("clone", "bare", "worktree"))
        for node in ast.walk(tree)
    )
    assert len(checker.EXACT10) == 10


def test_shared_harness_three_ambient_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert smoke.BASE_COMMIT == (
            "92aaa56a590e063b8fb0defda54444dc3bd1e6f8"
        )
        return

    checker = _checker()
    real_capture = lifecycle._capture_state
    checker_outputs: list[bytes] = []
    targeted_runs: list[bytes] = []
    observed_lifecycles: list[str] = []

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
            assert targeted.returncode == 0
            assert targeted.stderr == b""
            checked = subprocess.run(
                (
                    sys.executable,
                    checker.EXACT10[2].as_posix(),
                ),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert checked.returncode == 0
            assert checked.stderr == b""
            observed_lifecycles.append(state.lifecycle)
            targeted_runs.append(targeted.stdout)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture_with_validation)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=smoke.BASE_COMMIT,
        formal_commit_subject=smoke.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert observed_lifecycles == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert len(targeted_runs) == 3
    assert all(b"passed" in output for output in targeted_runs)
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == smoke.BASE_COMMIT
    assert report.candidate_subject == smoke.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert not any(Path(state.repository_path).exists() for state in (
        report.pre_commit,
        report.detached_candidate_post_commit,
        report.formal_main_post_commit_unpushed,
        report.formal_main_post_push,
    ))


def test_evidence_sha256_manifest_excludes_self_hash() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    assert tuple(sorted(manifest["evidence_sha256"])) == tuple(
        sorted(checker.CSV_NAMES)
    )
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]
    assert all(
        manifest["evidence_sha256"][name]
        == hashlib.sha256(payloads[name]).hexdigest()
        for name in checker.CSV_NAMES
    )

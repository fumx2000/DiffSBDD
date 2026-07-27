from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / "check_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_ACTION_PERMISSION_BRIDGE_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_action_permission_bridge_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_design_api_is_exact_keyword_only_and_runtime_absent() -> None:
    function = (
        design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "orchestration_result",
        "call_site_decision",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    assert not hasattr(
        design,
        "evaluate_bulk_download_stage_orchestration_action_permission_bridge",
    )
    assert not any(
        token in name
        for name in signature.parameters
        for token in (
            "callable",
            "dispatcher",
            "aggregator",
            "orchestrator",
            "filesystem",
            "network",
            "provider",
        )
    )


def test_bridge_decision_is_frozen_exact19_with_exact_vocabularies() -> None:
    cls = design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
    assert is_dataclass(cls)
    assert cls.__dataclass_params__.frozen is True
    assert tuple(item.name for item in fields(cls)) == design.DECISION_FIELDS
    assert len(design.DECISION_FIELDS) == 19
    assert design.OUTCOME_VOCABULARY == ("eligible", "blocked", "invalid")
    assert design.REASON_VOCABULARY == (
        "ACTION_PERMISSION_BRIDGE_RESULT_TYPE_INVALID",
        "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_TYPE_INVALID",
        "ACTION_PERMISSION_BRIDGE_STAGE_RESULT_INVARIANT_INVALID",
        "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_INVARIANT_INVALID",
        "ACTION_PERMISSION_BRIDGE_STAGE_SCOPE_INVALID",
        "ACTION_PERMISSION_BRIDGE_STAGE_IO_INVARIANT_INVALID",
        "ACTION_PERMISSION_BRIDGE_SOURCE_ALREADY_TRANSITIONED",
        "ACTION_PERMISSION_BRIDGE_SOURCE_LINEAGE_MISMATCH",
        "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_INVALID",
        "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED",
        "ACTION_PERMISSION_BRIDGE_CANDIDATE_VERDICT_BLOCKED",
        "ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING",
        "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE",
    )


def test_current_blocked_actual_pair_preserves_diagnostics_and_zero_action() -> None:
    checker = _checker()
    result, call_site_decision = checker._source_pair(authorized=False)
    decision = checker._classify(result, call_site_decision)
    assert result.stage_global_rule_evaluations[0].admission_rule_id == "ADMIT_014"
    assert result.stage_global_rule_evaluations[0].outcome == "blocked"
    assert decision.outcome == "blocked"
    assert decision.reason == design.REASON_VOCABULARY[9]
    assert decision.invalid_candidate_indexes == ()
    assert decision.blocked_candidate_indexes == (0,)
    assert decision.failing_candidate_indexes == (0,)
    assert decision.source_lineage_verified is True
    assert decision.transition_eligible is False
    assert decision.action_permission_granted is False
    assert decision.download_action_invoked is False
    assert decision.bridge_io_used is False
    expected = checker._expected_projection(
        outcome="blocked",
        reason=checker.R_ADMIT_014_BLOCKED,
        result=result,
        decision=call_site_decision,
        evidence_level="diagnostic",
        source_lineage_verified=True,
    )
    assert checker._exact19_verified(expected, decision)


def test_future_eligible_actual_pair_is_eligible_but_never_authorized() -> None:
    checker = _checker()
    result, call_site_decision = checker._source_pair(authorized=True)
    assert all(
        item.outcome == "passed"
        for item in result.stage_global_rule_evaluations
    )
    assert all(
        item.combined_verdict.outcome == "passed"
        for item in result.candidate_results
    )
    assert call_site_decision.outcome == "blocked"
    assert (
        call_site_decision.reason
        == "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"
    )
    decision = checker._classify(result, call_site_decision)
    assert decision.outcome == "eligible"
    assert decision.reason == design.REASON_VOCABULARY[12]
    assert decision.passed is True
    assert decision.blocks_transition is False
    assert decision.source_lineage_verified is True
    assert decision.transition_eligible is True
    assert decision.action_permission_granted is False
    assert decision.download_action_invoked is False
    assert decision.bridge_io_used is False
    expected = checker._expected_projection(
        outcome="eligible",
        reason=checker.R_TRANSITION_ELIGIBLE,
        result=result,
        decision=call_site_decision,
        evidence_level="diagnostic",
        source_lineage_verified=True,
    )
    assert checker._exact19_verified(expected, decision)


def test_truth_matrix_covers_all_required_groups_and_is_fail_closed() -> None:
    checker = _checker()
    rows = checker.build_truth_rows()
    assert len(rows) == 50
    assert len({row["case_id"] for row in rows}) == 50
    assert {row["case_group"] for row in rows} == {
        "type",
        "stage_result_invariant",
        "decision_invariant",
        "scope_io_transition",
        "lineage",
        "candidate_authority",
        "precedence",
    }
    assert all(row["verified"] == "true" for row in rows)
    assert all(
        json.loads(row["observed_action_permission_granted"]) is False
        for row in rows
    )
    assert all(
        json.loads(row["observed_download_action_invoked"]) is False
        for row in rows
    )
    assert all(
        json.loads(row["observed_bridge_io_used"]) is False
        for row in rows
    )
    assert all(
        row["exact_decision_type_verified"] == "true"
        for row in rows
    )


def test_stage_and_decision_deep_invariant_mutations_are_covered() -> None:
    checker = _checker()
    rows = {row["case_id"]: row for row in checker.build_truth_rows()}
    required_stage = {
        "STAGE_SCHEMA",
        "STAGE_STORAGE",
        "STAGE_TUPLE_SUBCLASS",
        "STAGE_COUNT",
        "STAGE_MEMBERSHIP",
        "STAGE_CARDINALITY",
        "STAGE_IDENTITY",
        "RETAINED_IDENTITY",
        "UNIFIED_CORRUPT",
        "COMBINED_CORRUPT",
    }
    required_decision = {
        "DECISION_SCHEMA",
        "DECISION_STORAGE",
        "DECISION_SOURCE_KIND",
        "DECISION_SCOPE_UNKNOWN",
        "DECISION_DIAGNOSTICS",
        "DECISION_FAILING",
        "DECISION_PERMISSION_TYPE",
        "DECISION_DOWNLOAD_ACTION",
        "DECISION_IO",
    }
    assert required_stage | required_decision <= set(rows)
    assert all(
        json.loads(rows[case_id]["observed_reason"])
        == design.REASON_VOCABULARY[2]
        for case_id in required_stage
    )
    assert all(
        json.loads(rows[case_id]["observed_reason"])
        == design.REASON_VOCABULARY[3]
        for case_id in required_decision
    )


def test_source_lineage_mutations_are_rejected_before_business_eligibility() -> None:
    checker = _checker()
    rows = {row["case_id"]: row for row in checker.build_truth_rows()}
    for case_id in (
        "LINEAGE_COUNT",
        "LINEAGE_SCOPE",
        "LINEAGE_DIAGNOSTIC",
        "LINEAGE_OUTCOME",
        "LINEAGE_REASON",
        "LINEAGE_UNRELATED",
        "PRECEDENCE_LINEAGE_OVER_BUSINESS",
    ):
        assert json.loads(rows[case_id]["observed_outcome"]) == "invalid"
        assert (
            json.loads(rows[case_id]["observed_reason"])
            == design.REASON_VOCABULARY[7]
        )


def test_authorized_projection_is_exact_lineage_mismatch_and_reason_11_reserved() -> None:
    checker = _checker()
    result, pending = checker._source_pair(authorized=True)
    forged = replace(
        pending,
        outcome="authorized",
        passed=True,
        blocks_download=False,
        reason="",
    )
    observed = checker._classify(result, forged)
    assert observed.outcome == "invalid"
    assert observed.reason == checker.R_LINEAGE_MISMATCH
    assert observed.source_lineage_verified is False
    assert observed.transition_eligible is False
    assert (
        design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_REASON_RESERVED
        is True
    )
    assert (
        design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_BRANCH_REACHABLE
        is False
    )
    rows = {row["case_id"]: row for row in checker.build_truth_rows()}
    for case_id in (
        "DECISION_NOT_PENDING",
        "PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE",
    ):
        assert json.loads(rows[case_id]["observed_outcome"]) == "invalid"
        assert (
            json.loads(rows[case_id]["observed_reason"])
            == checker.R_LINEAGE_MISMATCH
        )
        assert (
            json.loads(rows[case_id]["observed_source_lineage_verified"])
            is False
        )
    assert all(
        json.loads(row["observed_reason"]) != checker.R_NOT_PERMISSION_PENDING
        for row in rows.values()
    )


def test_truth_rows_verify_full_exact19_and_tampering_fails_closed() -> None:
    checker = _checker()
    rows = checker.build_truth_rows()
    assert len(checker.EXACT19_FIELDS) == 19
    assert len(checker.TRUTH_COLUMNS) == 43
    assert all(
        f"expected_{field_name}" in checker.TRUTH_COLUMNS
        and f"observed_{field_name}" in checker.TRUTH_COLUMNS
        for field_name in checker.EXACT19_FIELDS
    )
    assert all(row["verified"] == "true" for row in rows)
    result, call_site_decision = checker._source_pair(authorized=True)
    observed = checker._classify(result, call_site_decision)
    expected = checker._expected_projection(
        outcome="eligible",
        reason=checker.R_TRANSITION_ELIGIBLE,
        result=result,
        decision=call_site_decision,
        evidence_level="diagnostic",
        source_lineage_verified=True,
    )
    mutations = {
        "source_scope_id": "__tampered__",
        "candidate_count": 2,
        "admit_014_outcome": "blocked",
        "candidate_combined_outcomes": ("blocked",),
        "call_site_decision_outcome": "invalid",
        "call_site_decision_reason": checker.R_LINEAGE_MISMATCH,
        "invalid_candidate_indexes": (0,),
        "blocked_candidate_indexes": (0,),
        "failing_candidate_indexes": (0,),
        "source_lineage_verified": False,
        "transition_eligible": False,
    }
    for field_name, value in mutations.items():
        row = checker._truth_row(
            f"TAMPER_{field_name}",
            "tamper",
            field_name,
            replace(expected, **{field_name: value}),
            result,
            call_site_decision,
        )
        assert row["verified"] == "false"
    tuple_subclass = checker._TupleSubclass(
        expected.candidate_combined_outcomes
    )
    assert checker._truth_row(
        "TAMPER_TUPLE_SUBCLASS",
        "tamper",
        "tuple subclass",
        replace(expected, candidate_combined_outcomes=tuple_subclass),
        result,
        call_site_decision,
    )["verified"] == "false"
    assert checker._truth_row(
        "TAMPER_BOOL_AS_INT",
        "tamper",
        "bool-as-int",
        replace(expected, transition_eligible=1),
        result,
        call_site_decision,
    )["verified"] == "false"

    class BridgeDecisionSubclass(
        design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
    ):
        pass

    subclass = BridgeDecisionSubclass(**vars(observed))
    assert checker._truth_row(
        "TAMPER_DECISION_SUBCLASS",
        "tamper",
        "exact decision subclass",
        expected,
        result,
        call_site_decision,
        observed_override=subclass,
    )["verified"] == "false"


def test_invariant_projection_is_full_exact19_canonical_json() -> None:
    checker = _checker()
    truth = checker.build_truth_rows()
    rows = checker.build_invariant_rows(truth)
    assert len(rows) >= 23
    for row in rows:
        expected = row["expected_projection"]
        observed = row["observed_projection"]
        assert expected == observed
        assert tuple(json.loads(expected)) == tuple(
            sorted(checker.EXACT19_FIELDS)
        )
        assert len(json.loads(expected)) == 19
        assert row["verified"] == "true"


def test_design_uses_no_predecessor_private_helper() -> None:
    checker = _checker()
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private_calls = tuple(
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "call_site_contract"
            and node.func.attr.startswith("_")
        )
    )
    assert private_calls == ()
    assert "coherent_nonpending_projection" not in source


def test_admit_014_and_candidate_precedence_is_exact() -> None:
    checker = _checker()
    rows = {row["case_id"]: row for row in checker.build_truth_rows()}
    expected = {
        "PRECEDENCE_INVALID_OVER_ADMIT": design.REASON_VOCABULARY[8],
        "PRECEDENCE_ADMIT_OVER_BLOCKED": design.REASON_VOCABULARY[9],
        "PRECEDENCE_BLOCKED_OVER_ELIGIBLE": design.REASON_VOCABULARY[10],
        "PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE": design.REASON_VOCABULARY[7],
        "PRECEDENCE_ELIGIBLE": design.REASON_VOCABULARY[12],
    }
    assert {
        case_id: json.loads(rows[case_id]["observed_reason"])
        for case_id in expected
    } == expected


def test_decision_constructor_enforces_eligible_permission_separation() -> None:
    checker = _checker()
    result, call_site_decision = checker._source_pair(authorized=True)
    eligible = checker._classify(result, call_site_decision)
    with pytest.raises(ValueError):
        replace(eligible, action_permission_granted=True)
    with pytest.raises(ValueError):
        replace(eligible, download_action_invoked=True)
    with pytest.raises(ValueError):
        replace(eligible, bridge_io_used=True)
    with pytest.raises(ValueError):
        replace(eligible, transition_eligible=False)


def test_public_invariant_safety_and_issue_evidence_is_executable() -> None:
    checker = _checker()
    truth = checker.build_truth_rows()
    public = checker.build_public_rows()
    invariants = checker.build_invariant_rows(truth)
    safety = checker.build_safety_rows(truth)
    assert len(public) == 19
    assert len(invariants) == 23
    assert len(safety) == 23
    assert all(row["verified"] == "true" for row in public)
    assert all(row["verified"] == "true" for row in invariants)
    assert all(row["verified"] == "true" for row in safety)
    assert all(row["expected_projection"] == row["observed_projection"] for row in invariants)
    assert all(row["mutation_or_positive_probe"] not in ("", "verified") for row in invariants)
    assert (ROOT / checker.EXACT10[8]).read_bytes() == checker.PREDECESSOR_ISSUE_PATH.read_bytes()


def test_design_source_has_no_forbidden_capability_or_formal_runtime() -> None:
    checker = _checker()
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imports.intersection(
        {
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "pathlib",
            "shutil",
            "os",
            "torch",
        }
    )
    assert "open(" not in source
    assert (
        "def evaluate_bulk_download_stage_orchestration_action_permission_bridge"
        not in source
    )


def test_manifest_freezes_masks_training_gate_and_readiness_false() -> None:
    checker = _checker()
    manifest = json.loads((ROOT / checker.EXACT10[-1]).read_text(encoding="utf-8"))
    assert manifest["truth_row_count"] == 50
    assert manifest["truth_group_count"] == 7
    assert manifest["source_lineage_invariant_row_count"] == 23
    assert manifest["public_contract_row_count"] == 19
    assert manifest["safety_row_count"] == 23
    assert manifest["issue_inventory_data_row_count"] == 30
    assert manifest["unknown_atom_feature_policy"] == "UNKNOWN_ATOM_FEATURE_POLICY"
    assert manifest["unknown_atom_feature_policy_resolved"] is False
    assert manifest["feature_semantics_known"] is False
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["ready_for_download"] is False
    assert manifest["ready_for_training"] is False
    assert tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    ) == checker.CANONICAL_MASKS


def test_checker_is_independent_and_stdout_is_deterministic() -> None:
    source = CHECKER_PATH.read_text(encoding="utf-8")
    assert "fixture_runtime.build_canonical_in_memory_fixture_profiles()" in source
    assert "orchestration_runtime.orchestrate_stage_admission_scope(" in source
    assert "call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(" in source
    for forbidden in (
        "design.build_truth",
        "design.build_invariant",
        "design.build_expected",
        "design.build_evidence",
    ):
        assert forbidden not in source
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    first = subprocess.run(
        (sys.executable, "-B", str(CHECKER_PATH)),
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    second = subprocess.run(
        (sys.executable, "-B", str(CHECKER_PATH)),
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


def test_exact10_evidence_bytes_and_manifest_hashes_are_verified() -> None:
    checker = _checker()
    report = checker.check()
    assert report["current_blocked_path"] is True
    assert report["future_eligible_path"] is True
    assert report["source_lineage"] is True
    assert report["admit_014_authority"] is True
    assert report["transition_eligible_count"] > 0
    assert report["action_permission_granted_count"] == 0
    assert report["download_action_count"] == 0
    assert report["bridge_io_count"] == 0
    assert report["ready_for_download"] is False
    assert report["ready_for_training"] is False


def test_isolated_import_is_silent() -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    code = (
        "import covalent_ext."
        "covapie_bulk_download_stage_orchestration_"
        "action_permission_bridge_contract_design_gate"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_lifecycle_sources_use_shared_harness_only() -> None:
    checker = _checker()
    source = Path(__file__).read_text(encoding="utf-8")
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
    }
    assert "lifecycle.exercise_hermetic_git_lifecycle_matrix" in calls
    assert len(checker.EXACT10) == 10
    for forbidden in (
        "git " + "init --bare",
        "git " + "clone",
        "git " + "worktree add",
        "git " + "push",
    ):
        assert forbidden not in source
        assert forbidden not in CHECKER_PATH.read_text(encoding="utf-8")


def test_shared_harness_three_ambient_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert design.BASE_COMMIT == "f24bc241b1a492a514ed44649d57220a68c3ae6d"
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    checker_outputs = []
    targeted_outputs = []
    observed_states = []

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
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert targeted.returncode == checked.returncode == 0
            assert targeted.stderr == checked.stderr == b""
            observed_states.append(state.lifecycle)
            targeted_outputs.append(targeted.stdout)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture_with_validation)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=design.BASE_COMMIT,
        formal_commit_subject=design.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert observed_states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert len(targeted_outputs) == 3
    assert all(b"passed" in output for output in targeted_outputs)
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == design.BASE_COMMIT
    assert report.candidate_subject == design.FORMAL_COMMIT_SUBJECT
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

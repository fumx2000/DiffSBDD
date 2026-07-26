from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as runtime,
)
from covalent_ext import (
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py"
)
RUNTIME_PATH = (
    ROOT
    / "src"
    / "covalent_ext"
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_DECISION_RUNTIME_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_call_site_decision_runtime_checker",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _evaluate(*, result=None, error=None):
    return runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=result,
        orchestration_error=error,
    )


def test_runtime_public_api_signature_annotations_and_identity_are_exact() -> None:
    function = runtime.evaluate_bulk_download_stage_orchestration_call_site
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    assert runtime.__all__ == (
        "BulkDownloadStageOrchestrationCallSiteDecisionDesign",
        "evaluate_bulk_download_stage_orchestration_call_site",
    )
    assert tuple(signature.parameters) == (
        "orchestration_result",
        "orchestration_error",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    assert not any(
        parameter.kind
        in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for parameter in signature.parameters.values()
    )
    assert hints["orchestration_result"] == (
        contract.StageAdmissionOrchestrationResult | None
    )
    assert hints["orchestration_error"] == (
        contract.StageAdmissionOrchestrationError | None
    )
    assert hints["return"] is (
        design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    )
    assert runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign is (
        design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    )
    assert tuple(
        item.name
        for item in fields(
            runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        )
    ) == design.DECISION_FIELDS


def test_runtime_source_is_independent_and_has_no_injection_or_io_surface() -> None:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert (
        "design.classify_bulk_download_stage_orchestration_call_site_contract_design"
        not in calls
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "design"
        and node.func.attr.startswith("_")
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and "checker" in ast.unparse(node)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "setattr", "getattr"}
        for node in ast.walk(tree)
    )
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert not imports & {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "torch",
        "os",
        "pathlib",
        "shutil",
    }
    function_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "evaluate_bulk_download_stage_orchestration_call_site"
    )
    assert function_node.args.vararg is None
    assert function_node.args.kwarg is None
    assert not function_node.args.posonlyargs
    assert not function_node.args.args
    assert len(function_node.args.kwonlyargs) == 2
    assert all(default is None for default in function_node.args.kw_defaults)
    assert not isinstance(
        next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name
            == "evaluate_bulk_download_stage_orchestration_call_site"
        ),
        (ast.Assign, ast.AnnAssign),
    )


def test_exact_one_of_and_exact_source_types_fail_closed() -> None:
    checker = _checker()
    real = checker._runtime_result()
    error = checker._legal_error(contract.ERROR_CODES[0])
    for decision in (
        _evaluate(),
        _evaluate(result=real, error=error),
    ):
        assert decision.outcome == "invalid"
        assert decision.reason == design.REASON_VOCABULARY[0]
        assert decision.source_kind == "invalid_input"
        assert decision.candidate_count == 0
    for value in (
        object(),
        checker._ResultSubclass(**vars(real)),
    ):
        decision = _evaluate(result=value)
        assert decision.reason == design.REASON_VOCABULARY[1]
    for value in (
        RuntimeError("wrong"),
        checker._ErrorSubclass(**vars(error)),
    ):
        decision = _evaluate(error=value)
        assert decision.reason == design.REASON_VOCABULARY[2]


def test_all_exact8_error_codes_preserve_only_scope_and_code() -> None:
    checker = _checker()
    for code in contract.ERROR_CODES:
        error = checker._legal_error(code)
        try:
            raise error from RuntimeError("private cause must not project")
        except contract.StageAdmissionOrchestrationError as caught:
            decision = _evaluate(error=caught)
        assert type(decision) is (
            design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        )
        assert decision.outcome == "invalid"
        assert decision.reason == design.REASON_VOCABULARY[4]
        assert decision.source_kind == "orchestration_error"
        assert decision.source_scope_id == design.DOWNLOAD_SCOPE_ID
        assert decision.source_error_code == code
        assert decision.candidate_count == 0
        assert decision.invalid_candidate_indexes == ()
        assert decision.blocked_candidate_indexes == ()
        assert decision.failing_candidate_indexes == ()
        assert "private cause" not in repr(decision)


def test_malformed_exact8_and_stage_exact12_fail_closed() -> None:
    checker = _checker()
    truth_rows, _ = checker.evaluate_registry()
    error_rows = tuple(
        row
        for row in truth_rows
        if row["case_group"] == "error_invariant"
    )
    stage_rows = tuple(
        row
        for row in truth_rows
        if row["case_group"] == "stage_result_invariant"
    )
    assert len(error_rows) == 9
    assert len(stage_rows) == 20
    assert {
        row["observed_reason"] for row in error_rows
    } == {design.REASON_VOCABULARY[3]}
    assert {
        row["observed_reason"] for row in stage_rows
    } == {design.REASON_VOCABULARY[5]}
    assert all(row["verified"] == "true" for row in (*error_rows, *stage_rows))


def test_scope_io_permission_candidate_precedence_is_exact() -> None:
    checker = _checker()
    truth_rows, _ = checker.evaluate_registry()
    by_id = {row["case_id"]: row for row in truth_rows}
    expected = {
        "stage_invariant_precedes_scope_io_permission_candidate": (
            "invalid",
            design.REASON_VOCABULARY[5],
        ),
        "wrong_scope_precedes_io_permission_candidate": (
            "invalid",
            design.REASON_VOCABULARY[6],
        ),
        "io_precedes_permission_and_candidate": (
            "invalid",
            design.REASON_VOCABULARY[7],
        ),
        "action_permission_precedes_invalid_and_blocked": (
            "invalid",
            design.REASON_VOCABULARY[8],
        ),
        "candidate_invalid_precedes_blocked": (
            "invalid",
            design.REASON_VOCABULARY[9],
        ),
        "candidate_blocked_precedes_permission_not_granted": (
            "blocked",
            design.REASON_VOCABULARY[10],
        ),
        "cross_all_passed_permission_false": (
            "blocked",
            design.REASON_VOCABULARY[11],
        ),
    }
    for case_id, (outcome, reason) in expected.items():
        assert by_id[case_id]["observed_outcome"] == outcome
        assert by_id[case_id]["observed_reason"] == reason
        assert by_id[case_id]["verified"] == "true"
    cross = tuple(
        row
        for row in truth_rows
        if row["case_group"] == "cross_phase_precedence"
    )
    assert len(cross) == 9


def test_candidate_diagnostics_cover_positions_multiples_and_union_order() -> None:
    checker = _checker()
    truth_rows, _ = checker.evaluate_registry()
    by_id = {row["case_id"]: row for row in truth_rows}
    expected = {
        "blocked_first": ("[]", "[0]", "[0]"),
        "blocked_middle": ("[]", "[1]", "[1]"),
        "blocked_last": ("[]", "[2]", "[2]"),
        "multiple_blocked": ("[]", "[0,2]", "[0,2]"),
        "invalid_first": ("[0]", "[]", "[0]"),
        "invalid_middle": ("[1]", "[]", "[1]"),
        "invalid_last": ("[2]", "[]", "[2]"),
        "multiple_invalid": ("[0,2]", "[]", "[0,2]"),
        "blocked_and_invalid": ("[1]", "[0]", "[0,1]"),
        "invalid_and_blocked": ("[0]", "[1]", "[0,1]"),
    }
    for case_id, projection in expected.items():
        row = by_id[case_id]
        assert (
            row["observed_invalid_candidate_indexes"],
            row["observed_blocked_candidate_indexes"],
            row["observed_failing_candidate_indexes"],
        ) == projection
        assert row["verified"] == "true"


def test_equal_copies_fail_identity_and_rejected_branch_is_canonical() -> None:
    checker = _checker()
    truth_rows, _ = checker.evaluate_registry()
    by_id = {row["case_id"]: row for row in truth_rows}
    for case_id in (
        "copied_equal_stage_result",
        "copied_equal_retained_vector",
        "corrupted_rejected_diagnostics",
    ):
        assert by_id[case_id]["observed_reason"] == (
            design.REASON_VOCABULARY[5]
        )
    rejected = by_id["rejected_canonical_source_invalid_verdict"]
    assert rejected["observed_outcome"] == "invalid"
    assert rejected["observed_reason"] == design.REASON_VOCABULARY[9]
    assert rejected["observed_invalid_candidate_indexes"] == "[0]"


def test_runtime_truth_registry_is_exact_77_cases_and_11_groups() -> None:
    checker = _checker()
    truth_rows, _ = checker.evaluate_registry()
    frozen = checker._read_design_truth()
    assert len(truth_rows) == 77
    assert len({row["case_id"] for row in truth_rows}) == 77
    assert tuple(
        (row["case_group"], row["case_id"]) for row in truth_rows
    ) == tuple((row["case_group"], row["case_id"]) for row in frozen)
    assert Counter(row["case_group"] for row in truth_rows) == Counter(
        row["case_group"] for row in frozen
    )
    assert len({row["case_group"] for row in truth_rows}) == 11
    assert all(row["verified"] == "true" for row in truth_rows)


def test_field_level_three_way_parity_is_exact_1155() -> None:
    checker = _checker()
    _, parity_rows = checker.evaluate_registry()
    assert len(parity_rows) == 77 * 15 == 1155
    assert all(
        row["design_parity_verified"] == "true"
        and row["runtime_parity_verified"] == "true"
        and row["three_way_parity_verified"] == "true"
        for row in parity_rows
    )
    assert Counter(row["decision_field"] for row in parity_rows) == {
        field_name: 77 for field_name in design.DECISION_FIELDS
    }


def test_current_real_path_is_committed_orchestrator_admit_014_blocked() -> None:
    checker = _checker()
    result = checker._runtime_result()
    decision = _evaluate(result=result)
    assert result.scope_id == design.DOWNLOAD_SCOPE_ID
    assert result.candidate_count == 1
    assert result.candidate_results[0].combined_verdict.blocked_rule_ids == (
        "ADMIT_014",
    )
    assert decision.source_kind == "orchestration_result"
    assert decision.source_scope_id == design.DOWNLOAD_SCOPE_ID
    assert decision.candidate_count == 1
    assert decision.invalid_candidate_indexes == ()
    assert decision.blocked_candidate_indexes == (0,)
    assert decision.failing_candidate_indexes == (0,)
    assert decision.action_permission_granted is False
    assert decision.outcome == "blocked"
    assert decision.reason == design.REASON_VOCABULARY[10]
    assert decision.download_action_invoked is False
    assert decision.call_site_io_used is False


def test_zero_authorized_zero_action_and_deterministic_evidence() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    assert first == second
    manifest = checker.verify_payloads(first)
    assert manifest["authorized_decision_count"] == 0
    assert manifest["download_action_count"] == 0
    assert manifest["runtime_design_classifier_called"] is False
    assert manifest["runtime_design_private_helpers_called"] is False
    assert manifest["current_permission"] is False
    assert manifest["action_permission_granted"] is False
    assert manifest["ready_for_download"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_completed"] is False


def test_materialized_exact6_match_checker_and_manifest_hashes() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    checker.verify_payloads(payloads)
    checker._verify_materialized(payloads)
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    assert tuple(payloads) == checker.OUTPUT_NAMES
    assert len(payloads) == 6
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]
    for name in checker.CSV_NAMES:
        assert manifest["evidence_sha256"][name] == hashlib.sha256(
            payloads[name]
        ).hexdigest()
    assert hashlib.sha256(payloads[checker.ISSUE_NAME]).hexdigest() == (
        "fb4d2dfae7ffc056e3856c94e2f5a135"
        "d468eb3801144f9a698f95d9b812ace7"
    )


def test_manifest_preserves_masks_issues_and_training_blockers() -> None:
    checker = _checker()
    manifest = checker.verify_payloads(checker.build_evidence_payloads())
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
    assert manifest["unknown_atom_feature_policy"] == (
        "UNKNOWN_ATOM_FEATURE_POLICY"
    )
    assert manifest["unknown_atom_feature_policy_resolved"] is False
    assert manifest["feature_semantics_known"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["step12d_warning"] == (
        "Step12D was a smoke legality check, not a final "
        "training-feature contract"
    )


def test_checker_is_self_contained_and_lifecycle_uses_shared_harness_only() -> None:
    checker = _checker()
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    checker_tree = ast.parse(checker_source)
    imports = tuple(
        ast.unparse(node)
        for node in ast.walk(checker_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    assert not any("call_site_contract_v1" in item for item in imports)
    assert hasattr(checker, "build_case_registry")
    assert len(checker.build_case_registry()) == 77
    test_source = Path(__file__).read_text(encoding="utf-8")
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(ast.parse(test_source))
        if isinstance(node, ast.Call)
    }
    assert "lifecycle.exercise_hermetic_git_lifecycle_matrix" in calls
    for forbidden in (
        "git init --bare",
        "git clone",
        "git worktree add",
        "git push",
    ):
        assert forbidden not in checker_source
        assert forbidden not in RUNTIME_PATH.read_text(encoding="utf-8")


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign is (
            design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        )
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    observed_states: list[str] = []
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
            observed_states.append(state.lifecycle)
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
    assert observed_states == [
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

from __future__ import annotations

import ast
import hashlib
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
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as design,
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
    / "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_CALL_SITE_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_call_site_contract_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_design_api_is_exact_keyword_only_and_injection_free() -> None:
    function = (
        design.classify_bulk_download_stage_orchestration_call_site_contract_design
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "orchestration_result",
        "orchestration_error",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    assert not hasattr(
        design, "evaluate_bulk_download_stage_orchestration_call_site"
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


def test_decision_is_frozen_exact15_with_exact_vocabularies() -> None:
    cls = design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    assert is_dataclass(cls)
    assert cls.__dataclass_params__.frozen is True
    assert tuple(item.name for item in fields(cls)) == design.DECISION_FIELDS
    assert len(design.DECISION_FIELDS) == 15
    assert design.OUTCOME_VOCABULARY == (
        "authorized",
        "blocked",
        "invalid",
    )
    assert design.SOURCE_KIND_VOCABULARY == (
        "invalid_input",
        "orchestration_error",
        "orchestration_result",
    )
    assert len(design.REASON_VOCABULARY) == 12


def test_exact_one_of_cardinality_is_fail_closed_with_fixed_projection() -> None:
    checker = _checker()
    real = checker._runtime_result()
    error = checker._legal_error(contract.ERROR_CODES[0])
    for decision in (
        checker._classify(),
        checker._classify(result=real, error=error),
    ):
        assert decision.outcome == "invalid"
        assert decision.reason == design.REASON_VOCABULARY[0]
        assert decision.source_kind == "invalid_input"
        assert decision.source_scope_id == ""
        assert decision.source_error_code == ""
        assert decision.candidate_count == 0
        assert decision.invalid_candidate_indexes == ()
        assert decision.blocked_candidate_indexes == ()
        assert decision.failing_candidate_indexes == ()
        assert decision.action_permission_granted is False
        assert decision.download_action_invoked is False
        assert decision.call_site_io_used is False


def test_exact_source_types_reject_wrong_types_and_subclasses() -> None:
    checker = _checker()
    real = checker._runtime_result()
    error = checker._legal_error(contract.ERROR_CODES[0])
    result_subclass = checker._ResultSubclass(**vars(real))
    error_subclass = checker._ErrorSubclass(**vars(error))
    for value in (object(), result_subclass):
        decision = checker._classify(result=value)
        assert decision.reason == design.REASON_VOCABULARY[1]
    for value in (RuntimeError("x"), error_subclass):
        decision = checker._classify(error=value)
        assert decision.reason == design.REASON_VOCABULARY[2]


def test_all_exact8_error_codes_fail_closed_and_preserve_only_code() -> None:
    checker = _checker()
    for code in contract.ERROR_CODES:
        error = checker._legal_error(code)
        try:
            raise error from RuntimeError(
                "message that must not be projected"
            )
        except contract.StageAdmissionOrchestrationError as sourced:
            error = sourced
        decision = checker._classify(error=error)
        assert decision.outcome == "invalid"
        assert decision.reason == design.REASON_VOCABULARY[4]
        assert decision.source_kind == "orchestration_error"
        assert decision.source_scope_id == design.DOWNLOAD_SCOPE_ID
        assert decision.source_error_code == code
        assert decision.candidate_count == 0
        assert decision.invalid_candidate_indexes == ()
        assert decision.blocked_candidate_indexes == ()
        assert decision.failing_candidate_indexes == ()
        assert decision.action_permission_granted is False
        assert decision.download_action_invoked is False
        assert decision.call_site_io_used is False
        assert "message that must not be projected" not in repr(decision)
        assert decision.blocks_download is True


def test_malformed_exact8_fields_storage_and_bool_as_int_are_invalid() -> None:
    checker = _checker()
    rows = checker.build_truth_rows()
    malformed = tuple(
        row
        for row in rows
        if row["case_group"] == "error_invariant"
    )
    assert len(malformed) == 9
    assert all(row["observed_outcome"] == "invalid" for row in malformed)
    assert all(
        row["observed_reason"] == design.REASON_VOCABULARY[3]
        for row in malformed
    )


def test_current_real_download_scope_projection_is_exact_and_zero_action() -> None:
    checker = _checker()
    decision = checker._classify(result=checker._runtime_result())
    assert decision.candidate_count == 1
    assert decision.invalid_candidate_indexes == ()
    assert decision.blocked_candidate_indexes == (0,)
    assert decision.failing_candidate_indexes == (0,)
    assert decision.action_permission_granted is False
    assert decision.outcome == "blocked"
    assert decision.reason == design.REASON_VOCABULARY[10]
    assert decision.download_action_invoked is False
    assert decision.call_site_io_used is False


def test_only_download_scope_is_accepted_by_call_site() -> None:
    checker = _checker()
    for scope_id in contract.SCOPE_IDS:
        decision = checker._classify(
            result=checker._runtime_result(scope_id)
        )
        if scope_id == design.DOWNLOAD_SCOPE_ID:
            assert decision.outcome == "blocked"
        else:
            assert decision.outcome == "invalid"
            assert decision.reason == design.REASON_VOCABULARY[6]


def test_stage_exact12_and_candidate_exact5_mutations_fail_closed() -> None:
    checker = _checker()
    rows = checker.build_truth_rows()
    mutations = tuple(
        row
        for row in rows
        if row["case_group"] == "stage_result_invariant"
    )
    assert len(mutations) >= 15
    assert all(row["observed_outcome"] == "invalid" for row in mutations)
    assert all(
        row["observed_reason"] == design.REASON_VOCABULARY[5]
        for row in mutations
    )


def test_equal_but_copied_stage_and_retained_vector_identities_are_invalid() -> None:
    checker = _checker()
    rows = {
        row["case_id"]: row
        for row in checker.build_truth_rows()
        if row["case_group"] == "identity"
    }
    assert rows["stage_and_vector_identity_valid"]["verified"] == "true"
    for case_id in (
        "copied_equal_stage_result",
        "copied_equal_retained_vector",
    ):
        assert rows[case_id]["observed_outcome"] == "invalid"
        assert rows[case_id]["observed_reason"] == design.REASON_VOCABULARY[5]


def test_rejected_canonical_is_candidate_invalid_and_corruption_is_stage_invalid() -> None:
    checker = _checker()
    rows = {
        row["case_id"]: row
        for row in checker.build_truth_rows()
        if row["case_group"] == "identity"
    }
    canonical = rows["rejected_canonical_source_invalid_verdict"]
    assert canonical["observed_outcome"] == "invalid"
    assert canonical["observed_reason"] == design.REASON_VOCABULARY[9]
    corrupted = rows["corrupted_rejected_diagnostics"]
    assert corrupted["observed_outcome"] == "invalid"
    assert corrupted["observed_reason"] == design.REASON_VOCABULARY[5]


def test_candidate_diagnostics_and_precedence_cover_positions_and_mixtures() -> None:
    checker = _checker()
    rows = tuple(
        row
        for row in checker.build_truth_rows()
        if row["case_group"] == "candidate_precedence"
    )
    assert len(rows) == 12
    assert all(row["verified"] == "true" for row in rows)
    expected = {
        "all_passed_permission_false": (1, "[]", "[]", "[]", "false"),
        "blocked_first": (3, "[]", "[0]", "[0]", "false"),
        "blocked_middle": (3, "[]", "[1]", "[1]", "false"),
        "blocked_last": (3, "[]", "[2]", "[2]", "false"),
        "multiple_blocked": (3, "[]", "[0,2]", "[0,2]", "false"),
        "invalid_first": (3, "[0]", "[]", "[0]", "false"),
        "invalid_middle": (3, "[1]", "[]", "[1]", "false"),
        "invalid_last": (3, "[2]", "[]", "[2]", "false"),
        "multiple_invalid": (3, "[0,2]", "[]", "[0,2]", "false"),
        "blocked_and_invalid": (2, "[1]", "[0]", "[0,1]", "false"),
        "invalid_and_blocked": (2, "[0]", "[1]", "[0,1]", "false"),
        "action_true_precedes_invalid_and_blocked": (
            2,
            "[1]",
            "[0]",
            "[0,1]",
            "true",
        ),
    }
    assert {row["case_id"] for row in rows} == set(expected)
    for row in rows:
        count, invalid, blocked, failing, action = expected[row["case_id"]]
        assert row["observed_candidate_count"] == str(count)
        assert row["observed_invalid_candidate_indexes"] == invalid
        assert row["observed_blocked_candidate_indexes"] == blocked
        assert row["observed_failing_candidate_indexes"] == failing
        assert row["observed_action_permission_granted"] == action


def test_action_permission_true_precedes_candidate_invalid_and_blocked() -> None:
    checker = _checker()
    source = checker.build_result_for_candidate_outcomes(
        ("blocked", "invalid")
    )
    decision = checker._classify(
        result=replace(source, action_permission_granted=True)
    )
    assert decision.outcome == "invalid"
    assert decision.reason == design.REASON_VOCABULARY[8]
    assert decision.invalid_candidate_indexes == (1,)
    assert decision.blocked_candidate_indexes == (0,)
    assert decision.action_permission_granted is True
    assert decision.download_action_invoked is False


def test_all_passed_with_permission_false_remains_blocked() -> None:
    checker = _checker()
    source = checker.build_result_for_candidate_outcomes(
        ("passed", "passed")
    )
    decision = checker._classify(result=source)
    assert decision.outcome == "blocked"
    assert decision.reason == design.REASON_VOCABULARY[11]
    assert decision.invalid_candidate_indexes == ()
    assert decision.blocked_candidate_indexes == ()
    assert decision.failing_candidate_indexes == ()
    assert decision.action_permission_granted is False


def test_evidence_payloads_match_exact6_and_manifest_has_no_self_hash() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    assert first == second
    assert tuple(first) == checker.OUTPUT_NAMES
    assert len(first) == 6
    manifest = json.loads(first[checker.MANIFEST_NAME])
    assert tuple(manifest["evidence_sha256"]) == tuple(
        sorted(checker.CSV_NAMES)
    )
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]
    for name in checker.CSV_NAMES:
        assert manifest["evidence_sha256"][name] == hashlib.sha256(
            first[name]
        ).hexdigest()
    checker.verify_payloads(first)


def test_manifest_rows_issues_pre_masks_and_training_gate_are_frozen() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    manifest = json.loads(payloads[checker.MANIFEST_NAME])
    assert manifest["public_result_contract_row_count"] == 38
    assert manifest["truth_row_count"] == 77
    assert manifest["truth_group_count"] == 11
    assert manifest["truth_group_counts"]["cross_phase_precedence"] == 9
    assert manifest["source_result_invariant_row_count"] == 31
    assert manifest["safety_audit_row_count"] == 22
    assert manifest["issue_inventory_row_count"] == 30
    assert hashlib.sha256(payloads[checker.ISSUE_NAME]).hexdigest() == (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    )
    assert manifest["precondition_continuity"] == {
        "row_count": 45,
        "complete_count": 43,
        "supported_but_not_frozen_count": 0,
        "incomplete_count": 2,
        "implementation_blocking_count": 2,
        "transition_count": 0,
        "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
    }
    assert tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    ) == checker.CANONICAL_MASKS
    for key in (
        "current_authorized_branch_reachable",
        "future_action_permission_bridge_implemented",
        "download_callable_accepted",
        "download_callable_invoked",
        "current_permission",
        "action_permission_granted",
        "ready_for_download",
        "feature_semantics_known",
        "feature_semantics_audit_completed",
        "ready_for_training",
    ):
        assert manifest[key] is False
    for key in (
        "full_exact15_truth_projection_verified",
        "cross_phase_precedence_verified",
        "candidate_diagnostic_projection_verified",
        "error_exact8_full_projection_verified",
        "invariant_matrix_executable_evidence_verified",
    ):
        assert manifest[key] is True
    assert manifest["feature_semantics_audit_required_before_training"] is True


def test_design_source_ast_has_no_io_action_or_model_surface() -> None:
    checker = _checker()
    checker._verify_design_source_policy()
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imported_roots & {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "torch",
        "shutil",
        "os",
        "pathlib",
    }
    assert "shell=True" not in source


def test_checker_is_independent_and_all_truth_is_zero_authorized_zero_download() -> None:
    checker = _checker()
    source = CHECKER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert (
        "design.classify_bulk_download_stage_orchestration_call_site_contract_design"
        in calls
    )
    assert "design.build_truth_rows" not in calls
    assert "design.build_invariant_rows" not in calls
    assert "design.build_evidence_payloads" not in calls
    rows = checker.build_truth_rows()
    assert all(row["observed_passed"] == "false" for row in rows)
    assert all(
        row["observed_download_action_invoked"] == "false"
        for row in rows
    )
    assert all(row["observed_call_site_io_used"] == "false" for row in rows)
    assert all(row["verified"] == "true" for row in rows)


def test_every_truth_row_compares_full_exact15_projection() -> None:
    checker = _checker()
    rows = checker.build_truth_rows()
    assert len(rows) == 77
    assert set(rows[0]) == set(checker.TRUTH_COLUMNS)
    for row in rows:
        assert row["exact_decision_type_verified"] == "true"
        for name in design.DECISION_FIELDS:
            assert row[f"expected_{name}"] == row[f"observed_{name}"]
        assert row["verified"] == "true"


def test_truth_verification_detects_diagnostic_and_source_tampering() -> None:
    checker = _checker()
    decision = checker._classify(result=checker._runtime_result())
    expected = checker._expected(
        "blocked",
        checker.CANDIDATE_VERDICT_BLOCKED,
        "orchestration_result",
        source_scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_count=1,
        blocked_candidate_indexes=(0,),
    )
    assert checker._decision_matches_expected(decision, expected)
    mutations = (
        replace(expected, invalid_candidate_indexes=(0,)),
        replace(expected, blocked_candidate_indexes=()),
        replace(expected, failing_candidate_indexes=()),
        replace(expected, source_kind="invalid_input"),
        replace(expected, source_scope_id=""),
        replace(expected, source_error_code="unexpected"),
    )
    for index, mutation in enumerate(mutations):
        assert not checker._decision_matches_expected(decision, mutation)
        row = checker._truth_row(
            "tamper_probe",
            f"tamper_{index}",
            decision,
            mutation,
        )
        assert row["verified"] == "false"


def test_cross_phase_precedence_has_nine_executable_exact15_cases() -> None:
    checker = _checker()
    rows = {
        row["case_id"]: row
        for row in checker.build_truth_rows()
        if row["case_group"] == "cross_phase_precedence"
    }
    expected_reasons = {
        "cardinality_precedes_wrong_result_and_error_types": (
            checker.INPUT_CARDINALITY_INVALID
        ),
        "stage_invariant_precedes_scope_io_permission_candidate": (
            checker.STAGE_RESULT_INVARIANT_INVALID
        ),
        "wrong_scope_precedes_io_permission_candidate": (
            checker.STAGE_SCOPE_INVALID
        ),
        "io_precedes_permission_and_candidate": (
            checker.STAGE_IO_INVARIANT_INVALID
        ),
        "action_permission_precedes_invalid_and_blocked": (
            checker.ACTION_PERMISSION_TRANSITION_UNAUTHORIZED
        ),
        "candidate_invalid_precedes_blocked": (
            checker.CANDIDATE_VERDICT_INVALID
        ),
        "candidate_blocked_precedes_permission_not_granted": (
            checker.CANDIDATE_VERDICT_BLOCKED
        ),
        "cross_all_passed_permission_false": (
            checker.ACTION_PERMISSION_NOT_GRANTED
        ),
        "legal_error_precedes_success_shaped_coordinates": (
            checker.ERROR_FAIL_CLOSED
        ),
    }
    assert set(rows) == set(expected_reasons)
    for case_id, reason in expected_reasons.items():
        row = rows[case_id]
        assert row["expected_reason"] == reason
        assert row["observed_reason"] == reason
        assert row["verified"] == "true"


def test_invariant_matrix_is_executable_truth_linked_evidence() -> None:
    checker = _checker()
    truth_rows = checker.build_truth_rows()
    truth_by_case = {row["case_id"]: row for row in truth_rows}
    invariant_rows = checker.build_invariant_rows(truth_rows)
    assert len(invariant_rows) == 31
    required_areas = {
        "stage_exact12",
        "scope",
        "membership",
        "cardinality",
        "stage_identity",
        "candidate_exact5",
        "unified",
        "combined",
        "retained_vector",
        "rejected",
        "orchestration_error_exact8",
        "action_permission",
        "diagnostics",
        "side_effect",
    }
    assert {row["invariant_area"] for row in invariant_rows} == required_areas
    for row in invariant_rows:
        assert row["evidence_case_id"] in truth_by_case
        assert truth_by_case[row["evidence_case_id"]]["verified"] == "true"
        assert row["expected_projection"] == row["observed_projection"]
        assert row["mutation_or_positive_probe"] not in ("", "verified")
        assert row["verified"] == "true"
        assert "expected=verified" not in repr(row)


def test_design_classifier_sha_is_byte_identical() -> None:
    checker = _checker()
    assert hashlib.sha256((ROOT / checker.EXACT10[0]).read_bytes()).hexdigest() == (
        "96c93e727cbd8f127311969788b08c39f34735f1c5423952e24399d2d3e04c35"
    )


def test_lifecycle_sources_use_shared_harness_only() -> None:
    checker = _checker()
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "lifecycle.exercise_hermetic_git_lifecycle_matrix" in calls
    assert len(checker.EXACT10) == 10
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    design_source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    for forbidden in (
        "git init --bare",
        "git clone",
        "git worktree add",
        "git push",
    ):
        assert forbidden not in checker_source
        assert forbidden not in design_source


def test_shared_harness_three_ambient_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert design.BASE_COMMIT == (
            "0963f4dbbd4d16eab8aaac1640d224ec135673ed"
        )
        return
    checker = _checker()
    real_capture = lifecycle._capture_state
    checker_outputs: list[bytes] = []
    targeted_outputs: list[bytes] = []
    observed_states: list[str] = []

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
                (sys.executable, checker.EXACT10[2].as_posix()),
                cwd=repository,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            assert checked.returncode == 0
            assert checked.stderr == b""
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

from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)
from covalent_ext import (
    covapie_post_admission_control_plane_completion_and_next_training_preparation_blocker_review_gate_v1
    as review,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts"
    / (
        "check_covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1.py"
    )
)
NESTED_LIFECYCLE_ENV = "COVAPIE_POST_ADMISSION_REVIEW_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_post_admission_review_checker", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _decision():
    return review.review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1(
        control_plane_complete=True,
        effective_open_issues=(
            review.ATOM_PAIR_BLOCKER,
            review.PROVIDER_BLOCKER,
        ),
        atom_pair_evidence_verified=True,
        provider_export_evidence_verified=True,
    )


def test_review_public_api_and_frozen_decision() -> None:
    decision = _decision()
    assert review.__all__ == (
        "PostAdmissionNextBlockerSelectionDecision",
        "DEPENDENCY_ORDER",
        "review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1",
        "serialize_post_admission_next_blocker_selection_decision",
    )
    assert tuple(item.name for item in fields(type(decision))) == (
        "schema_version",
        "outcome",
        "control_plane_complete",
        "selected_next_blocker",
        "deferred_blocker",
        "selection_reason",
        "selected_blocker_category",
        "deferred_blocker_category",
        "selected_next_step",
        "permission_layer_expansion_required",
        "provider_execution_required_now",
        "feature_semantics_audit_required_before_training",
        "ready_for_download",
        "ready_for_training",
    )
    assert decision.outcome == "selected"
    assert type(decision).__dataclass_params__.frozen is True
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in inspect.signature(
            review.review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1
        ).parameters.values()
    )


def test_review_fails_closed_on_incomplete_or_contradictory_evidence() -> None:
    cases = (
        (False, (review.ATOM_PAIR_BLOCKER, review.PROVIDER_BLOCKER), True, True),
        (True, (review.PROVIDER_BLOCKER, review.ATOM_PAIR_BLOCKER), True, True),
        (True, (review.ATOM_PAIR_BLOCKER, review.PROVIDER_BLOCKER), False, True),
        (True, (review.ATOM_PAIR_BLOCKER, review.PROVIDER_BLOCKER), True, False),
    )
    for complete, issues, atom, provider in cases:
        decision = review.review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1(
            control_plane_complete=complete,
            effective_open_issues=issues,
            atom_pair_evidence_verified=atom,
            provider_export_evidence_verified=provider,
        )
        assert decision.outcome == "invalid"
        assert decision.control_plane_complete is False
        assert decision.selected_next_blocker == ""
        assert decision.ready_for_download is False
        assert decision.ready_for_training is False


def test_control_plane_completion_inventory_is_direct_evidence() -> None:
    checker = _checker()
    rows = checker.build_control_plane_rows()
    assert len(rows) == 16
    assert all(row["verified"] == "true" for row in rows)
    assert all(row["evidence_path"] and row["evidence_sha256"] for row in rows)
    assert {row["control_plane_component"] for row in rows} >= {
        "unified ADMIT_001-015 runtime",
        "combined aggregation",
        "stage orchestration runtime",
        "call-site runtime",
        "bridge runtime",
        "current blocked chain",
        "future eligible chain",
        "permission transition attempted",
        "download action count",
    }


def test_control_plane_complete_does_not_enable_download_or_training() -> None:
    decision = _decision()
    assert decision.control_plane_complete is True
    assert decision.ready_for_download is False
    assert decision.ready_for_training is False
    assert decision.feature_semantics_audit_required_before_training is True


def test_blocker_comparison_contains_exactly_two_open_rows() -> None:
    rows = _checker().build_comparison_rows()
    assert len(rows) == 2
    assert tuple(row["blocker_id"] for row in rows) == (
        review.ATOM_PAIR_BLOCKER,
        review.PROVIDER_BLOCKER,
    )
    assert all(row["current_status"] == "open" for row in rows)


def test_selected_and_deferred_blockers_follow_dependency_evidence() -> None:
    rows = {
        row["blocker_id"]: row
        for row in _checker().build_comparison_rows()
    }
    atom = rows[review.ATOM_PAIR_BLOCKER]
    provider = rows[review.PROVIDER_BLOCKER]
    assert atom["selection_disposition"] == "selected_next"
    assert atom["blocks_feature_semantics_audit"] == "true"
    assert atom["blocks_label_tensor_contract"] == "true"
    assert atom["requires_real_provider_execution"] == "false"
    assert provider["selection_disposition"] == "deferred_open"
    assert provider["affected_rules"] == "ADMIT_004"
    assert provider["can_remain_quarantined_temporarily"] == "true"


def test_selection_preserves_issue_inventory_byte_identity() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    source = (ROOT / checker.PREDECESSOR_ISSUE_PATH).read_bytes()
    assert payloads[checker.ISSUE_NAME] == source
    assert len(checker._read_csv(checker.PREDECESSOR_ISSUE_PATH)) == 30
    assert _decision().selected_next_blocker == review.ATOM_PAIR_BLOCKER


def test_dependency_order_is_exact_and_review_implements_none() -> None:
    rows = _checker().build_dependency_rows()
    assert len(rows) == 9
    assert tuple(row["dependency_step"] for row in rows) == review.DEPENDENCY_ORDER
    assert [row["dependency_order"] for row in rows] == [
        str(index) for index in range(1, 10)
    ]
    assert all(row["implemented_current_review"] == "false" for row in rows)


def test_selected_next_step_is_current_semantics_audit_not_design() -> None:
    decision = _decision()
    assert decision.selected_next_step == (
        "audit_covapie_covalent_bond_atom_pair_current_semantics_"
        "and_downstream_consumers_v1"
    )
    assert "design_covapie_covalent_bond_atom_pair_encoding_contract_v1" not in (
        decision.selected_next_step
    )


def test_no_permission_or_control_plane_expansion() -> None:
    checker = _checker()
    decision = _decision()
    safety = {row["safety_item"]: row for row in checker.build_safety_rows()}
    assert decision.permission_layer_expansion_required is False
    assert safety["permission_layer_expansion_required"]["observed_executed"] == "false"
    assert safety["control_plane_code_change_required"]["observed_executed"] == "false"
    checker._verify_control_sources_unchanged()


def test_no_provider_download_model_or_training_activity() -> None:
    rows = {row["safety_item"]: row for row in _checker().build_safety_rows()}
    assert len(rows) == 19
    for name in (
        "provider",
        "download",
        "model_change",
        "forward_change",
        "loss_change",
        "parameter_update",
        "training",
        "feature_semantics_audit_completed",
        "ready_for_download",
        "ready_for_training",
    ):
        assert rows[name]["observed_executed"] == "false"


def test_all_evidence_and_decision_serialization_are_deterministic() -> None:
    checker = _checker()
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    third = checker.build_evidence_payloads()
    assert first == second == third
    decisions = (_decision(), _decision(), _decision())
    assert decisions[0] == decisions[1] == decisions[2]
    assert (
        review.serialize_post_admission_next_blocker_selection_decision(decisions[0])
        == review.serialize_post_admission_next_blocker_selection_decision(decisions[1])
        == review.serialize_post_admission_next_blocker_selection_decision(decisions[2])
    )
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imports & {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "socket",
        "torch",
    }


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _decision().outcome == "selected"
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
    assert all(b"13 passed" in output for output in targeted_outputs)
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

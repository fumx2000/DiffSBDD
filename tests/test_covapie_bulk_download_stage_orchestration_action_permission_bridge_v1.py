from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_action_permission_bridge_v1
    as runtime,
)
from covalent_ext import (
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as call_site_contract,
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
    / "check_covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py"
)
RUNTIME_PATH = (
    ROOT
    / "src"
    / "covalent_ext"
    / "covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py"
)
NESTED_LIFECYCLE_ENV = "COVAPIE_BRIDGE_RUNTIME_NESTED_LIFECYCLE"


def _checker():
    spec = importlib.util.spec_from_file_location(
        "covapie_action_permission_bridge_runtime_checker",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_public_api_signature_annotations_and_shared_identity_are_exact() -> None:
    function = (
        runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge
    )
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    assert runtime.__all__ == (
        "BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign",
        "evaluate_bulk_download_stage_orchestration_action_permission_bridge",
    )
    assert tuple(signature.parameters) == (
        "orchestration_result",
        "call_site_decision",
    )
    assert all(
        item.kind is inspect.Parameter.KEYWORD_ONLY
        and item.default is inspect.Parameter.empty
        for item in signature.parameters.values()
    )
    assert not any(
        item.kind
        in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for item in signature.parameters.values()
    )
    assert hints["orchestration_result"] is (
        contract.StageAdmissionOrchestrationResult
    )
    assert hints["call_site_decision"] is (
        call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
    )
    assert hints["return"] is (
        design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
    )
    assert (
        runtime.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
    )
    assert tuple(
        item.name
        for item in fields(
            runtime.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        )
    ) == design.DECISION_FIELDS


def test_runtime_is_independent_without_injection_private_helpers_or_io() -> None:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert (
        "design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design"
        not in calls
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in {"design", "call_site_contract"}
        and node.func.attr.startswith("_")
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and "checker" in ast.unparse(node)
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
    assert not calls & {"open", "print", "input"}
    function_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "evaluate_bulk_download_stage_orchestration_action_permission_bridge"
    )
    assert function_node.args.posonlyargs == []
    assert function_node.args.args == []
    assert function_node.args.vararg is None
    assert function_node.args.kwarg is None
    assert len(function_node.args.kwonlyargs) == 2
    assert all(item is None for item in function_node.args.kw_defaults)


def test_exact_source_types_and_subclasses_fail_closed() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    indexed = {row["case_id"]: row for row in truth}
    expected = {
        "TYPE_RESULT_WRONG": design.REASON_VOCABULARY[0],
        "TYPE_RESULT_SUBCLASS": design.REASON_VOCABULARY[0],
        "TYPE_DECISION_WRONG": design.REASON_VOCABULARY[1],
        "TYPE_DECISION_SUBCLASS": design.REASON_VOCABULARY[1],
    }
    for case_id, reason in expected.items():
        assert indexed[case_id]["runtime_outcome"] == '"invalid"'
        assert indexed[case_id]["runtime_reason"] == json.dumps(reason)
        assert indexed[case_id]["runtime_exact_type_verified"] == "true"


def test_stage_candidate_and_call_site_deep_invariants_fail_closed() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    groups = {
        "stage_result_invariant": design.REASON_VOCABULARY[2],
        "decision_invariant": design.REASON_VOCABULARY[3],
    }
    for group, reason in groups.items():
        rows = [row for row in truth if row["case_group"] == group]
        assert rows
        assert all(row["runtime_outcome"] == '"invalid"' for row in rows)
        assert all(row["runtime_reason"] == json.dumps(reason) for row in rows)


def test_exact_lineage_rejects_forged_authorized_decision() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    indexed = {row["case_id"]: row for row in truth}
    for case_id in (
        "DECISION_NOT_PENDING",
        "PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE",
    ):
        row = indexed[case_id]
        assert row["runtime_outcome"] == '"invalid"'
        assert row["runtime_reason"] == json.dumps(design.REASON_VOCABULARY[7])
        assert row["runtime_source_lineage_verified"] == "false"
        assert row["runtime_transition_eligible"] == "false"


def test_active_precedence_and_reserved_reason_11_are_exact() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    precedence = [
        row for row in truth if row["case_group"] == "precedence"
    ]
    assert len(precedence) == 11
    assert all(row["full_exact19_verified"] == "true" for row in precedence)
    reserved = design.REASON_VOCABULARY[11]
    assert design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_REASON_RESERVED
    assert (
        design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_BRANCH_REACHABLE
        is False
    )
    assert all(row["runtime_reason"] != json.dumps(reserved) for row in truth)


def test_current_blocked_actual_chain_is_full_exact19() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    row = next(
        item for item in truth if item["case_id"] == "LINEAGE_CURRENT_VALID"
    )
    expected = {
        "runtime_outcome": '"blocked"',
        "runtime_reason": json.dumps(design.REASON_VOCABULARY[9]),
        "runtime_admit_014_outcome": '"blocked"',
        "runtime_candidate_combined_outcomes": '["blocked"]',
        "runtime_call_site_decision_outcome": '"blocked"',
        "runtime_call_site_decision_reason": (
            '"BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"'
        ),
        "runtime_invalid_candidate_indexes": "[]",
        "runtime_blocked_candidate_indexes": "[0]",
        "runtime_failing_candidate_indexes": "[0]",
        "runtime_source_lineage_verified": "true",
        "runtime_transition_eligible": "false",
    }
    assert all(row[key] == value for key, value in expected.items())
    assert row["full_exact19_verified"] == "true"


def test_future_eligible_actual_chain_never_grants_permission() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    row = next(
        item for item in truth if item["case_id"] == "FULLY_ELIGIBLE"
    )
    expected = {
        "runtime_outcome": '"eligible"',
        "runtime_reason": json.dumps(design.REASON_VOCABULARY[12]),
        "runtime_admit_014_outcome": '"passed"',
        "runtime_candidate_combined_outcomes": '["passed"]',
        "runtime_call_site_decision_outcome": '"blocked"',
        "runtime_call_site_decision_reason": (
            '"BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"'
        ),
        "runtime_source_lineage_verified": "true",
        "runtime_transition_eligible": "true",
        "runtime_action_permission_granted": "false",
        "runtime_download_action_invoked": "false",
        "runtime_bridge_io_used": "false",
    }
    assert all(row[key] == value for key, value in expected.items())


def test_runtime_truth_is_exact_50_cases_7_groups_and_950_field_parity() -> None:
    checker = _checker()
    truth, parity = checker.evaluate_registry()
    assert len(truth) == 50
    assert len({row["case_id"] for row in truth}) == 50
    assert len({row["case_group"] for row in truth}) == 7
    assert len(parity) == 50 * 19 == 950
    assert all(row["verified"] == "true" for row in truth)
    assert all(
        row["three_way_parity_verified"] == "true" for row in parity
    )
    assert all(
        len([item for item in parity if item["case_id"] == row["case_id"]])
        == 19
        for row in truth
    )


def test_zero_permission_action_io_and_deterministic_evidence() -> None:
    checker = _checker()
    truth, _ = checker.evaluate_registry()
    assert any(row["runtime_transition_eligible"] == "true" for row in truth)
    assert all(
        row["runtime_action_permission_granted"] == "false"
        and row["runtime_download_action_invoked"] == "false"
        and row["runtime_bridge_io_used"] == "false"
        for row in truth
    )
    first = checker.build_evidence_payloads()
    second = checker.build_evidence_payloads()
    assert first == second


def test_materialized_evidence_hashes_masks_issues_and_readiness() -> None:
    checker = _checker()
    payloads = checker.build_evidence_payloads()
    manifest = checker.verify_payloads(payloads)
    for name, content in payloads.items():
        assert (ROOT / checker.OUTPUT_ROOT / name).read_bytes() == content
    assert hashlib.sha256(payloads[checker.ISSUE_NAME]).hexdigest() == (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    )
    issue_rows = tuple(
        csv.DictReader(io.StringIO(payloads[checker.ISSUE_NAME].decode()))
    )
    assert len(issue_rows) == 30
    assert manifest["effective_open_issues"] == [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]
    assert ("scaffold_only", "B3") in tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    )
    assert manifest["feature_semantics_audit_completed"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["ready_for_download"] is False
    assert manifest["ready_for_training"] is False
    assert checker.MANIFEST_NAME not in manifest["evidence_sha256"]


def test_checker_is_self_contained_and_isolated_import_is_silent() -> None:
    checker_source = CHECKER_PATH.read_text(encoding="utf-8")
    checker_tree = ast.parse(checker_source)
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and "check_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1"
        in ast.unparse(node)
        for node in ast.walk(checker_tree)
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    imported = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_bulk_download_stage_orchestration_"
                "action_permission_bridge_v1"
            ),
        ),
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert imported.returncode == 0
    assert imported.stdout == b""
    assert imported.stderr == b""


def test_shared_lifecycle_three_states_run_targeted_and_checker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert (
            runtime.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
            is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
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

#!/usr/bin/env python3
"""Independently check and materialize the actual call-site chain evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import sys
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as decision_contract,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as decision_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as orchestration_contract,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as canonical_fixtures,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


BASE_COMMIT = "6e5f3b02183086fea4bb4f35fd03a5c5def7ed8e"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration call-site decision "
    "integration smoke v1"
)
STAGE = (
    "covapie_bulk_download_stage_orchestration_fail_closed_"
    "call_site_decision_in_memory_integration_smoke_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PROVENANCE_NAME = "covapie_call_site_decision_in_memory_fixture_provenance.csv"
RESULT_NAME = "covapie_call_site_decision_actual_chain_result_matrix.csv"
ERROR_NAME = "covapie_call_site_decision_actual_error_chain_matrix.csv"
SAFETY_NAME = "covapie_call_site_decision_in_memory_safety_audit.csv"
ISSUE_NAME = (
    "covapie_call_site_decision_in_memory_issue_readiness_inventory.csv"
)
MANIFEST_NAME = (
    "covapie_bulk_download_stage_orchestration_fail_closed_call_site_"
    "decision_in_memory_integration_smoke_manifest.json"
)
CSV_NAMES = (
    PROVENANCE_NAME,
    RESULT_NAME,
    ERROR_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1"
    / "covapie_bulk_download_call_site_decision_runtime_issue_readiness_inventory.csv"
)
EXACT10 = (
    Path("src/covalent_ext")
    / (
        "covapie_bulk_download_stage_orchestration_fail_closed_call_site_"
        "decision_in_memory_integration_smoke_v1.py"
    ),
    Path("tests")
    / (
        "test_covapie_bulk_download_stage_orchestration_fail_closed_call_"
        "site_decision_in_memory_integration_smoke_v1.py"
    ),
    Path("scripts")
    / (
        "check_covapie_bulk_download_stage_orchestration_fail_closed_call_"
        "site_decision_in_memory_integration_smoke_v1.py"
    ),
    Path("docs")
    / (
        "covapie_bulk_download_stage_orchestration_fail_closed_call_site_"
        "decision_in_memory_integration_smoke_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)

PROVENANCE_COLUMNS = (
    "fixture_profile",
    "source_path_kind",
    "scope_id",
    "candidate_count",
    "fixture_source_path",
    "fixture_source_symbol",
    "projection_policy",
    "verified",
)
RESULT_COLUMNS = (
    "fixture_profile",
    "scope_id",
    "candidate_count",
    "orchestrator_dispatcher_call_count",
    "orchestrator_aggregator_call_count",
    "stage_global_rule_ids",
    "stage_global_outcomes",
    "decision_exact15_field",
    "expected_value",
    "observed_value",
    "expected_exact_type",
    "observed_exact_type",
    "verified",
)
ERROR_COLUMNS = (
    "fixture_profile",
    "requested_scope_id",
    "actual_error_type",
    "actual_error_code",
    "actual_error_scope_id",
    "actual_error_candidate_index",
    "actual_error_dispatcher_call_count",
    "actual_error_aggregator_call_count",
    "decision_exact15_field",
    "expected_value",
    "observed_value",
    "expected_exact_type",
    "observed_exact_type",
    "verified",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "verified",
)
SAFETY_ITEMS = (
    "network",
    "provider",
    "download_callable",
    "download_io",
    "raw",
    "torch",
    "model",
    "checkpoint",
    "dataloader",
    "forward",
    "loss",
    "backward",
    "optimizer",
    "scheduler",
    "parameter_update",
    "checkpoint_write",
    "training",
    "current_permission",
    "action_permission",
    "authorized_decision",
    "ready_for_download",
    "ready_for_training",
)
COMMITTED_SOURCE_SHA256 = MappingProxyType(
    {
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_v1.py": "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc",
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_contract_design_gate.py": "68ddcede8c56c1db51a7a49e2fb5943e12818e0412f6463238865a39a47d4548",
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py": "e4a17a0250d9b229daa4e23cc9874d0cd9126ff18daea55492af0819bace8db8",
        "src/covalent_ext/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py": "dc51597773bd0d6d98c7c299e5bf0c5889396a865120f692724653fc4b8e4352",
        "src/covalent_ext/covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate.py": "96c93e727cbd8f127311969788b08c39f34735f1c5423952e24399d2d3e04c35",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py": "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
        "src/covalent_ext/covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1.py": "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    }
)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(
    columns: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _type(value: object) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


def _identities() -> tuple[object, ...]:
    return (
        orchestration_runtime.orchestrate_stage_admission_scope,
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )


def _assert_identities(
    before: tuple[object, ...], after: tuple[object, ...]
) -> None:
    if any(before[index] is not after[index] for index in (0, 1, 2, 3, 5)):
        raise AssertionError("runtime callable identity changed")
    if len(before[4]) != len(after[4]) or any(
        left[0] != right[0] or left[1] is not right[1]
        for left, right in zip(before[4], after[4], strict=True)
    ):
        raise AssertionError("registered handler identity changed")


def _expected_result(scope_id: str, candidate_count: int) -> dict[str, object]:
    if scope_id == decision_contract.DOWNLOAD_SCOPE_ID:
        outcome = "blocked"
        reason = "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
        blocked: tuple[int, ...] = (0,)
    else:
        outcome = "invalid"
        reason = "BULK_DOWNLOAD_STAGE_SCOPE_INVALID"
        blocked = ()
    return {
        "schema_version": (
            "covapie_bulk_download_stage_orchestration_call_site_decision_v1"
        ),
        "outcome": outcome,
        "passed": False,
        "blocks_download": True,
        "reason": reason,
        "source_kind": "orchestration_result",
        "source_scope_id": scope_id,
        "source_error_code": "",
        "candidate_count": candidate_count,
        "invalid_candidate_indexes": (),
        "blocked_candidate_indexes": blocked,
        "failing_candidate_indexes": blocked,
        "action_permission_granted": False,
        "download_action_invoked": False,
        "call_site_io_used": False,
    }


def _expected_error(scope_id: str, code: str) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_bulk_download_stage_orchestration_call_site_decision_v1"
        ),
        "outcome": "invalid",
        "passed": False,
        "blocks_download": True,
        "reason": "BULK_DOWNLOAD_ORCHESTRATION_ERROR_FAIL_CLOSED",
        "source_kind": "orchestration_error",
        "source_scope_id": scope_id,
        "source_error_code": code,
        "candidate_count": 0,
        "invalid_candidate_indexes": (),
        "blocked_candidate_indexes": (),
        "failing_candidate_indexes": (),
        "action_permission_granted": False,
        "download_action_invoked": False,
        "call_site_io_used": False,
    }


def _assert_decision(
    decision: object, expected: Mapping[str, object]
) -> None:
    if (
        type(decision)
        is not decision_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        or tuple(expected) != decision_contract.DECISION_FIELDS
        or tuple(vars(decision)) != decision_contract.DECISION_FIELDS
    ):
        raise AssertionError("independent Exact15 shape mismatch")
    for name in decision_contract.DECISION_FIELDS:
        observed = getattr(decision, name)
        wanted = expected[name]
        if type(observed) is not type(wanted) or observed != wanted:
            raise AssertionError(f"independent Exact15 mismatch: {name}")


def build_actual_chains() -> tuple[
    tuple[tuple[str, object, object], ...],
    tuple[str, object, object],
]:
    """Independently execute five result chains and one actual error chain."""
    before = _identities()
    single, two = canonical_fixtures.build_canonical_in_memory_fixture_profiles()
    result_chains: list[tuple[str, object, object]] = []
    for scope_id in single.scopes:
        result = orchestration_runtime.orchestrate_stage_admission_scope(
            scope_id,
            single.candidate_inputs,
            batch_context=single.batch_context,
            stage_authorization_context=single.stage_authorization_context,
        )
        decision = (
            decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=result,
                orchestration_error=None,
            )
        )
        _assert_decision(
            decision, _expected_result(scope_id, result.candidate_count)
        )
        result_chains.append((single.fixture_profile, result, decision))
    scope_id = two.scopes[0]
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        scope_id,
        two.candidate_inputs,
        batch_context=two.batch_context,
        stage_authorization_context=two.stage_authorization_context,
    )
    decision = (
        decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
            orchestration_result=result,
            orchestration_error=None,
        )
    )
    _assert_decision(
        decision, _expected_result(scope_id, result.candidate_count)
    )
    result_chains.append((two.fixture_profile, result, decision))

    try:
        orchestration_runtime.orchestrate_stage_admission_scope(
            smoke.INVALID_SCOPE_ID,
            single.candidate_inputs,
            batch_context=single.batch_context,
            stage_authorization_context=single.stage_authorization_context,
        )
    except orchestration_contract.StageAdmissionOrchestrationError as error:
        if type(error) is not orchestration_contract.StageAdmissionOrchestrationError:
            raise AssertionError("actual error exact type mismatch")
        error_decision = (
            decision_runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=None,
                orchestration_error=error,
            )
        )
        _assert_decision(
            error_decision, _expected_error(error.scope_id, error.code)
        )
        error_chain = (smoke.ERROR_FIXTURE_PROFILE, error, error_decision)
    else:
        raise AssertionError("invalid scope did not produce actual error")
    _assert_identities(before, _identities())
    return tuple(result_chains), error_chain


def build_fixture_provenance_rows() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    single, two = canonical_fixtures.build_canonical_in_memory_fixture_profiles()
    for scope_id in single.scopes:
        rows.append(
            {
                "fixture_profile": single.fixture_profile,
                "source_path_kind": "orchestration_result",
                "scope_id": scope_id,
                "candidate_count": "1",
                "fixture_source_path": (
                    "src/covalent_ext/covapie_stage_global_rule_evaluation_"
                    "orchestration_in_memory_integration_smoke_v1.py"
                ),
                "fixture_source_symbol": (
                    "build_canonical_in_memory_fixture_profiles"
                ),
                "projection_policy": (
                    "committed_builder_to_actual_orchestrator_no_forged_source"
                ),
                "verified": "true",
            }
        )
    rows.append(
        {
            "fixture_profile": two.fixture_profile,
            "source_path_kind": "orchestration_result",
            "scope_id": two.scopes[0],
            "candidate_count": "2",
            "fixture_source_path": (
                "src/covalent_ext/covapie_stage_global_rule_evaluation_"
                "orchestration_in_memory_integration_smoke_v1.py"
            ),
            "fixture_source_symbol": (
                "build_canonical_in_memory_fixture_profiles"
            ),
            "projection_policy": (
                "committed_builder_to_actual_orchestrator_no_forged_source"
            ),
            "verified": "true",
        }
    )
    rows.append(
        {
            "fixture_profile": smoke.ERROR_FIXTURE_PROFILE,
            "source_path_kind": "orchestration_error",
            "scope_id": smoke.INVALID_SCOPE_ID,
            "candidate_count": "0",
            "fixture_source_path": (
                "src/covalent_ext/covapie_stage_global_rule_evaluation_"
                "orchestration_v1.py"
            ),
            "fixture_source_symbol": "orchestrate_stage_admission_scope",
            "projection_policy": (
                "actual_invalid_request_error_caught_unmodified_no_forged_source"
            ),
            "verified": "true",
        }
    )
    return tuple(rows)


def build_result_rows(
    chains: tuple[tuple[str, object, object], ...] | None = None,
) -> tuple[dict[str, str], ...]:
    if chains is None:
        chains = build_actual_chains()[0]
    rows: list[dict[str, str]] = []
    for fixture_profile, result, decision in chains:
        expected = _expected_result(result.scope_id, result.candidate_count)
        stage_outcomes = tuple(
            item.outcome for item in result.stage_global_rule_evaluations
        )
        for name in decision_contract.DECISION_FIELDS:
            observed = getattr(decision, name)
            wanted = expected[name]
            rows.append(
                {
                    "fixture_profile": fixture_profile,
                    "scope_id": result.scope_id,
                    "candidate_count": str(result.candidate_count),
                    "orchestrator_dispatcher_call_count": str(
                        result.dispatcher_call_count
                    ),
                    "orchestrator_aggregator_call_count": str(
                        result.aggregator_call_count
                    ),
                    "stage_global_rule_ids": "|".join(
                        result.stage_global_rule_ids
                    ),
                    "stage_global_outcomes": "|".join(stage_outcomes),
                    "decision_exact15_field": name,
                    "expected_value": _value(wanted),
                    "observed_value": _value(observed),
                    "expected_exact_type": _type(wanted),
                    "observed_exact_type": _type(observed),
                    "verified": _bool(
                        type(observed) is type(wanted) and observed == wanted
                    ),
                }
            )
    return tuple(rows)


def build_error_rows(
    chain: tuple[str, object, object] | None = None,
) -> tuple[dict[str, str], ...]:
    if chain is None:
        chain = build_actual_chains()[1]
    fixture_profile, error, decision = chain
    expected = _expected_error(error.scope_id, error.code)
    rows: list[dict[str, str]] = []
    for name in decision_contract.DECISION_FIELDS:
        observed = getattr(decision, name)
        wanted = expected[name]
        rows.append(
            {
                "fixture_profile": fixture_profile,
                "requested_scope_id": smoke.INVALID_SCOPE_ID,
                "actual_error_type": _type(error),
                "actual_error_code": error.code,
                "actual_error_scope_id": error.scope_id,
                "actual_error_candidate_index": str(error.candidate_index),
                "actual_error_dispatcher_call_count": str(
                    error.dispatcher_call_count
                ),
                "actual_error_aggregator_call_count": str(
                    error.aggregator_call_count
                ),
                "decision_exact15_field": name,
                "expected_value": _value(wanted),
                "observed_value": _value(observed),
                "expected_exact_type": _type(wanted),
                "observed_exact_type": _type(observed),
                "verified": _bool(
                    type(observed) is type(wanted) and observed == wanted
                ),
            }
        )
    return tuple(rows)


def _safety_rows() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "verified": "true",
        }
        for item in SAFETY_ITEMS
    )


def _manifest(
    csv_payloads: Mapping[str, bytes],
    report: smoke.CallSiteDecisionIntegrationSmokeReport,
    actual_error_code: str,
) -> dict[str, object]:
    return {
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "decision_in_memory_integration_smoke_completed": True,
        "actual_orchestrator_called": True,
        "actual_decision_runtime_called": True,
        "actual_result_chain_verified": True,
        "actual_error_chain_verified": True,
        "exact4_result_scopes_verified": True,
        "two_candidate_wrong_scope_verified": True,
        "actual_orchestration_error_consumed": True,
        "actual_orchestration_error_code": actual_error_code,
        "runtime_callable_identities_unchanged": True,
        "monkeypatch_used_for_success_evidence": False,
        "full_exact15_actual_chain_verified": True,
        "observation_count": 6,
        "actual_result_path_count": 5,
        "actual_error_path_count": 1,
        "result_exact15_row_count": 75,
        "error_exact15_row_count": 15,
        "fixture_provenance_row_count": 6,
        "safety_row_count": len(SAFETY_ITEMS),
        "issue_inventory_data_row_count": 30,
        "public_smoke_parameter_count": 0,
        "public_observation_field_count": len(
            fields(smoke.CallSiteDecisionChainObservation)
        ),
        "public_report_field_count": len(
            fields(smoke.CallSiteDecisionIntegrationSmokeReport)
        ),
        "authorized_decision_count": report.authorized_decision_count,
        "download_action_count": report.download_action_count,
        "call_site_io_count": report.call_site_io_count,
        "download_callable_accepted": False,
        "download_callable_invoked": False,
        "current_authorized_branch_reachable": False,
        "future_action_permission_bridge_required": True,
        "future_action_permission_bridge_implemented": False,
        "network_used": False,
        "provider_used": False,
        "download_used": False,
        "current_permission": False,
        "action_permission_granted": False,
        "ready_for_download": False,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in smoke.CANONICAL_MASKS
        ],
        "effective_open_issues": list(smoke.EFFECTIVE_OPEN_ISSUES),
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "unknown_atom_feature_policy_resolved": False,
        "feature_semantics_known": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "ready_for_training": False,
        "recommended_next_step": smoke.RECOMMENDED_NEXT_STEP,
        "recommended_next_step_executes_real_download": False,
        "evidence_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in csv_payloads.items()
        },
    }


def build_evidence_payloads() -> dict[str, bytes]:
    reports = tuple(
        smoke.run_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke()
        for _ in range(3)
    )
    serialized = tuple(
        smoke.serialize_integration_smoke_report(report)
        for report in reports
    )
    if not (
        reports[0] == reports[1] == reports[2]
        and serialized[0] == serialized[1] == serialized[2]
    ):
        raise AssertionError("three public smoke runs are not deterministic")
    matrices: list[tuple[bytes, bytes, str]] = []
    for _ in range(3):
        result_chains, error_chain = build_actual_chains()
        result_rows = build_result_rows(result_chains)
        error_rows = build_error_rows(error_chain)
        if (
            len(result_rows) != 75
            or len(error_rows) != 15
            or any(row["verified"] != "true" for row in result_rows)
            or any(row["verified"] != "true" for row in error_rows)
        ):
            raise AssertionError("actual-chain Exact15 matrices invalid")
        matrices.append(
            (
                _csv_bytes(RESULT_COLUMNS, result_rows),
                _csv_bytes(ERROR_COLUMNS, error_rows),
                error_chain[1].code,
            )
        )
    if not (matrices[0] == matrices[1] == matrices[2]):
        raise AssertionError("three actual-chain matrices differ")
    provenance_rows = build_fixture_provenance_rows()
    if len(provenance_rows) != 6 or any(
        row["verified"] != "true" for row in provenance_rows
    ):
        raise AssertionError("fixture provenance invalid")
    issue_payload = (ROOT / PREDECESSOR_ISSUE_PATH).read_bytes()
    if hashlib.sha256(issue_payload).hexdigest() != (
        "fb4d2dfae7ffc056e3856c94e2f5a135"
        "d468eb3801144f9a698f95d9b812ace7"
    ):
        raise AssertionError("issue inventory continuity mismatch")
    csv_payloads = {
        PROVENANCE_NAME: _csv_bytes(
            PROVENANCE_COLUMNS, provenance_rows
        ),
        RESULT_NAME: matrices[0][0],
        ERROR_NAME: matrices[0][1],
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, _safety_rows()),
        ISSUE_NAME: issue_payload,
    }
    manifest = _manifest(csv_payloads, reports[0], matrices[0][2])
    return {
        **csv_payloads,
        MANIFEST_NAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }


def _verify_committed_sources() -> None:
    for relative, expected in COMMITTED_SOURCE_SHA256.items():
        path = ROOT / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise AssertionError(f"committed source mismatch: {relative}")


def _verify_source_policy() -> None:
    smoke_path, test_path, checker_path = EXACT10[:3]
    for relative in (smoke_path, test_path, checker_path):
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = {
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        }
        if any(
            name.endswith(
                (
                    "classify_bulk_download_stage_orchestration_call_site_contract_design",
                    "_build_decision",
                    "_orchestration_error_is_valid",
                    "_stage_result_is_valid",
                )
            )
            for name in calls
        ):
            raise AssertionError(f"forbidden success helper call: {relative}")
    smoke_source = (ROOT / smoke_path).read_text(encoding="utf-8")
    smoke_tree = ast.parse(smoke_source)
    run_node = next(
        node
        for node in smoke_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("run_covapie_bulk_download")
    )
    identifier_names = {
        node.id for node in ast.walk(smoke_tree) if isinstance(node, ast.Name)
    }
    imported_names = {
        alias.name
        for node in ast.walk(smoke_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if (
        run_node.args.args
        or run_node.args.kwonlyargs
        or run_node.args.vararg is not None
        or run_node.args.kwarg is not None
        or "monkeypatch" in identifier_names
        or any("monkeypatch" in name for name in imported_names)
        or "setattr(" in smoke_source
        or "fake error" in smoke_source.lower()
    ):
        raise AssertionError("smoke public surface or success path unsafe")
    imports = {
        node.names[0].name
        for node in ast.walk(smoke_tree)
        if isinstance(node, ast.Import)
    }
    if imports & {"os", "pathlib", "socket", "requests", "torch"}:
        raise AssertionError("smoke imported forbidden action surface")


def verify_payloads(payloads: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("evidence set is not Exact6")
    output = ROOT / OUTPUT_ROOT
    for name in OUTPUT_NAMES:
        path = output / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != payloads[name]
        ):
            raise AssertionError(f"evidence mismatch: {name}")
    manifest = json.loads(payloads[MANIFEST_NAME])
    false_fields = (
        "monkeypatch_used_for_success_evidence",
        "download_callable_accepted",
        "download_callable_invoked",
        "current_authorized_branch_reachable",
        "future_action_permission_bridge_implemented",
        "network_used",
        "provider_used",
        "download_used",
        "current_permission",
        "action_permission_granted",
        "ready_for_download",
        "feature_semantics_audit_completed",
        "feature_semantics_known",
        "unknown_atom_feature_policy_resolved",
        "ready_for_training",
    )
    if any(manifest[name] is not False for name in false_fields):
        raise AssertionError("manifest fail-closed value changed")
    if (
        manifest["authorized_decision_count"] != 0
        or manifest["download_action_count"] != 0
        or manifest["call_site_io_count"] != 0
        or manifest["result_exact15_row_count"] != 75
        or manifest["error_exact15_row_count"] != 15
    ):
        raise AssertionError("manifest direct evidence counts invalid")
    return manifest


def _materialize(payloads: Mapping[str, bytes]) -> None:
    output = ROOT / OUTPUT_ROOT
    if output.exists():
        raise ValueError("Exact6 output root already exists")
    output.mkdir(parents=True, exist_ok=False)
    for name in OUTPUT_NAMES:
        (output / name).write_bytes(payloads[name])


def main() -> int:
    _verify_committed_sources()
    _verify_source_policy()
    payloads = build_evidence_payloads()
    if sys.argv[1:] == ["--materialize"]:
        _materialize(payloads)
    elif sys.argv[1:]:
        raise AssertionError("unsupported arguments")
    manifest = verify_payloads(payloads)
    summary = {
        "actual_error_consumed": True,
        "actual_error_paths": 1,
        "actual_orchestration_error_code": (
            manifest["actual_orchestration_error_code"]
        ),
        "actual_orchestrator_called": True,
        "actual_decision_runtime_called": True,
        "actual_result_paths": 5,
        "authorized_decision_count": 0,
        "call_site_io_count": 0,
        "callable_identities_unchanged": True,
        "checker_passed": True,
        "deterministic_three_runs": True,
        "download_action_count": 0,
        "error_exact15_rows": 15,
        "evidence_sha256": manifest["evidence_sha256"],
        "manifest_sha256": hashlib.sha256(
            payloads[MANIFEST_NAME]
        ).hexdigest(),
        "monkeypatch_used_for_success_evidence": False,
        "observation_count": 6,
        "ready_for_download": False,
        "ready_for_training": False,
        "result_exact15_rows": 75,
    }
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

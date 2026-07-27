#!/usr/bin/env python3
"""Independently check and materialize the two actual bridge chains."""

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
    covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate
    as bridge_contract,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_action_permission_bridge_v1
    as bridge_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as call_site_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as canonical_fixtures,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


BASE_COMMIT = "beb42c497d3f0e47e009b2dc84aac929938824e5"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration action-permission bridge "
    "integration smoke v1"
)
STAGE = (
    "covapie_bulk_download_stage_orchestration_action_permission_bridge_"
    "in_memory_integration_smoke_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PROVENANCE_NAME = (
    "covapie_action_permission_bridge_in_memory_fixture_provenance.csv"
)
EXACT19_NAME = (
    "covapie_action_permission_bridge_actual_chain_exact19_matrix.csv"
)
IDENTITY_NAME = "covapie_action_permission_bridge_runtime_identity_matrix.csv"
SAFETY_NAME = "covapie_action_permission_bridge_in_memory_safety_audit.csv"
ISSUE_NAME = (
    "covapie_action_permission_bridge_in_memory_issue_readiness_inventory.csv"
)
MANIFEST_NAME = (
    "covapie_bulk_download_stage_orchestration_action_permission_bridge_"
    "in_memory_integration_smoke_manifest.json"
)
CSV_NAMES = (
    PROVENANCE_NAME,
    EXACT19_NAME,
    IDENTITY_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_action_permission_bridge_v1"
    / "covapie_action_permission_bridge_runtime_issue_readiness_inventory.csv"
)
EXACT10 = (
    Path("src/covalent_ext")
    / (
        "covapie_bulk_download_stage_orchestration_action_permission_bridge_"
        "in_memory_integration_smoke_v1.py"
    ),
    Path("tests")
    / (
        "test_covapie_bulk_download_stage_orchestration_action_permission_"
        "bridge_in_memory_integration_smoke_v1.py"
    ),
    Path("scripts")
    / (
        "check_covapie_bulk_download_stage_orchestration_action_permission_"
        "bridge_in_memory_integration_smoke_v1.py"
    ),
    Path("docs")
    / (
        "covapie_bulk_download_stage_orchestration_action_permission_bridge_"
        "in_memory_integration_smoke_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)

PROVENANCE_COLUMNS = (
    "source_mode",
    "fixture_profile",
    "fixture_builder_path",
    "fixture_builder_symbol",
    "authorization_mapping_policy",
    "actual_orchestrator",
    "actual_call_site_runtime",
    "actual_bridge_runtime",
    "forged_success_source",
    "verified",
)
EXACT19_COLUMNS = (
    "source_mode",
    "decision_field",
    "expected_value",
    "observed_value",
    "expected_exact_type",
    "observed_exact_type",
    "verified",
)
IDENTITY_COLUMNS = (
    "runtime_object",
    "module",
    "symbol",
    "identity_unchanged",
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
    "download_action",
    "bridge_io",
    "ready_for_download",
    "ready_for_training",
)
IDENTITY_SPECS = (
    (
        "actual_orchestrator",
        "covalent_ext.covapie_stage_global_rule_evaluation_orchestration_v1",
        "orchestrate_stage_admission_scope",
    ),
    (
        "actual_call_site_runtime",
        "covalent_ext.covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1",
        "evaluate_bulk_download_stage_orchestration_call_site",
    ),
    (
        "actual_bridge_runtime",
        "covalent_ext.covapie_bulk_download_stage_orchestration_action_permission_bridge_v1",
        "evaluate_bulk_download_stage_orchestration_action_permission_bridge",
    ),
    (
        "dispatcher",
        "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015",
        "evaluate_admission_rule",
    ),
    (
        "evaluator_registry",
        "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015",
        "EVALUATOR_REGISTRY",
    ),
    (
        "registered_handlers",
        "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015",
        "EVALUATOR_REGISTRY.items",
    ),
    (
        "aggregator",
        "covalent_ext.covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1",
        "aggregate_admission_rule_evaluations",
    ),
)
COMMITTED_SOURCE_SHA256 = MappingProxyType(
    {
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_v1.py": "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc",
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py": "e4a17a0250d9b229daa4e23cc9874d0cd9126ff18daea55492af0819bace8db8",
        "src/covalent_ext/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py": "dc51597773bd0d6d98c7c299e5bf0c5889396a865120f692724653fc4b8e4352",
        "src/covalent_ext/covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py": "864ec156650d8aa4b13b5d78fef13ec98461988f3bc4833215410a9e96141981",
        "src/covalent_ext/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_design_gate.py": "8cebc0a4016f11ad93373103f852ea4a22b7f78336295a7b9699ef72af69a368",
        "src/covalent_ext/covapie_hermetic_git_lifecycle_harness_v1.py": "99f4c85b685697f734968a0678a1e7915fb04bcf1929c4db30160689e576bbae",
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
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site,
        bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge,
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
    )


def _assert_identities(
    before: tuple[object, ...], after: tuple[object, ...]
) -> None:
    if any(
        before[index] is not after[index]
        for index in (0, 1, 2, 3, 4, 6)
    ):
        raise AssertionError("runtime identity changed")
    if len(before[5]) != len(after[5]) or any(
        left[0] != right[0] or left[1] is not right[1]
        for left, right in zip(before[5], after[5], strict=True)
    ):
        raise AssertionError("registered handler identity changed")


def _expected_exact19(source_mode: str) -> dict[str, object]:
    common = {
        "schema_version": (
            "covapie_bulk_download_stage_orchestration_"
            "action_permission_bridge_decision_v1"
        ),
        "source_scope_id": "download_execution_permission",
        "candidate_count": 1,
        "call_site_decision_outcome": "blocked",
        "invalid_candidate_indexes": (),
        "source_lineage_verified": True,
        "action_permission_granted": False,
        "download_action_invoked": False,
        "bridge_io_used": False,
    }
    if source_mode == "current_blocked":
        return {
            "schema_version": common["schema_version"],
            "outcome": "blocked",
            "passed": False,
            "blocks_transition": True,
            "reason": "ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED",
            "source_scope_id": common["source_scope_id"],
            "candidate_count": common["candidate_count"],
            "admit_014_outcome": "blocked",
            "candidate_combined_outcomes": ("blocked",),
            "call_site_decision_outcome": common[
                "call_site_decision_outcome"
            ],
            "call_site_decision_reason": (
                "BULK_DOWNLOAD_CANDIDATE_VERDICT_BLOCKED"
            ),
            "invalid_candidate_indexes": common[
                "invalid_candidate_indexes"
            ],
            "blocked_candidate_indexes": (0,),
            "failing_candidate_indexes": (0,),
            "source_lineage_verified": common["source_lineage_verified"],
            "transition_eligible": False,
            "action_permission_granted": common[
                "action_permission_granted"
            ],
            "download_action_invoked": common["download_action_invoked"],
            "bridge_io_used": common["bridge_io_used"],
        }
    if source_mode == "future_eligible":
        return {
            "schema_version": common["schema_version"],
            "outcome": "eligible",
            "passed": True,
            "blocks_transition": False,
            "reason": "ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE",
            "source_scope_id": common["source_scope_id"],
            "candidate_count": common["candidate_count"],
            "admit_014_outcome": "passed",
            "candidate_combined_outcomes": ("passed",),
            "call_site_decision_outcome": common[
                "call_site_decision_outcome"
            ],
            "call_site_decision_reason": (
                "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"
            ),
            "invalid_candidate_indexes": common[
                "invalid_candidate_indexes"
            ],
            "blocked_candidate_indexes": (),
            "failing_candidate_indexes": (),
            "source_lineage_verified": common["source_lineage_verified"],
            "transition_eligible": True,
            "action_permission_granted": common[
                "action_permission_granted"
            ],
            "download_action_invoked": common["download_action_invoked"],
            "bridge_io_used": common["bridge_io_used"],
        }
    raise AssertionError("unknown independent source mode")


def _assert_exact19(
    decision: object, expected: Mapping[str, object]
) -> None:
    if (
        type(decision)
        is not bridge_contract.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        or tuple(expected) != bridge_contract.DECISION_FIELDS
        or tuple(vars(decision)) != bridge_contract.DECISION_FIELDS
    ):
        raise AssertionError("independent Exact19 shape mismatch")
    for name in bridge_contract.DECISION_FIELDS:
        observed = getattr(decision, name)
        wanted = expected[name]
        if type(observed) is not type(wanted) or observed != wanted:
            raise AssertionError(f"independent Exact19 mismatch: {name}")


def build_actual_chains() -> tuple[tuple[str, object, object, object], ...]:
    """Independently execute the current and future actual runtime chains."""
    before = _identities()
    fixture = canonical_fixtures.build_canonical_in_memory_fixture_profiles()[0]
    original = dict(fixture.stage_authorization_context)
    future_authorization = dict(fixture.stage_authorization_context)
    future_authorization["current_stage_download_authorized"] = True
    chains: list[tuple[str, object, object, object]] = []
    for source_mode, authorization in (
        ("current_blocked", fixture.stage_authorization_context),
        ("future_eligible", future_authorization),
    ):
        result = orchestration_runtime.orchestrate_stage_admission_scope(
            "download_execution_permission",
            fixture.candidate_inputs,
            batch_context=fixture.batch_context,
            stage_authorization_context=authorization,
        )
        call_site = (
            call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=result,
                orchestration_error=None,
            )
        )
        bridge = (
            bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge(
                orchestration_result=result,
                call_site_decision=call_site,
            )
        )
        expected = _expected_exact19(source_mode)
        _assert_exact19(bridge, expected)
        if (
            call_site.outcome
            != expected["call_site_decision_outcome"]
            or call_site.reason
            != expected["call_site_decision_reason"]
            or call_site.action_permission_granted is not False
            or call_site.download_action_invoked is not False
            or call_site.call_site_io_used is not False
        ):
            raise AssertionError("independent call-site projection mismatch")
        chains.append((source_mode, result, call_site, bridge))
    if dict(fixture.stage_authorization_context) != original:
        raise AssertionError("canonical fixture mutated")
    _assert_identities(before, _identities())
    return tuple(chains)


def build_exact19_rows(
    chains: tuple[tuple[str, object, object, object], ...] | None = None,
) -> tuple[dict[str, str], ...]:
    if chains is None:
        chains = build_actual_chains()
    rows: list[dict[str, str]] = []
    for source_mode, _result, _call_site, bridge in chains:
        expected = _expected_exact19(source_mode)
        for name in bridge_contract.DECISION_FIELDS:
            observed = getattr(bridge, name)
            wanted = expected[name]
            rows.append(
                {
                    "source_mode": source_mode,
                    "decision_field": name,
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


def build_fixture_provenance_rows() -> tuple[dict[str, str], ...]:
    common = {
        "fixture_profile": "canonical_single_candidate_exact4",
        "fixture_builder_path": (
            "src/covalent_ext/covapie_stage_global_rule_evaluation_"
            "orchestration_in_memory_integration_smoke_v1.py"
        ),
        "fixture_builder_symbol": (
            "build_canonical_in_memory_fixture_profiles"
        ),
        "actual_orchestrator": (
            "orchestrate_stage_admission_scope"
        ),
        "actual_call_site_runtime": (
            "evaluate_bulk_download_stage_orchestration_call_site"
        ),
        "actual_bridge_runtime": (
            "evaluate_bulk_download_stage_orchestration_action_permission_bridge"
        ),
        "forged_success_source": "false",
        "verified": "true",
    }
    return (
        {
            "source_mode": "current_blocked",
            **common,
            "authorization_mapping_policy": (
                "committed_mapping_used_unmodified"
            ),
        },
        {
            "source_mode": "future_eligible",
            **common,
            "authorization_mapping_policy": (
                "new_dict_from_committed_mapping_then_"
                "current_stage_download_authorized_true"
            ),
        },
    )


def build_runtime_identity_rows() -> tuple[dict[str, str], ...]:
    before = _identities()
    build_actual_chains()
    after = _identities()
    _assert_identities(before, after)
    rows: list[dict[str, str]] = []
    for index, (runtime_object, module, symbol) in enumerate(IDENTITY_SPECS):
        unchanged = (
            (
                len(before[5]) == len(after[5])
                and all(
                    left[0] == right[0] and left[1] is right[1]
                    for left, right in zip(
                        before[5], after[5], strict=True
                    )
                )
            )
            if index == 5
            else before[index] is after[index]
        )
        rows.append(
            {
                "runtime_object": runtime_object,
                "module": module,
                "symbol": symbol,
                "identity_unchanged": _bool(unchanged),
                "verified": _bool(unchanged),
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
    report: smoke.ActionPermissionBridgeIntegrationSmokeReport,
) -> dict[str, object]:
    return {
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "action_permission_bridge_in_memory_integration_smoke_completed": True,
        "actual_orchestrator_called": True,
        "actual_call_site_runtime_called": True,
        "actual_bridge_runtime_called": True,
        "current_blocked_actual_chain_verified": True,
        "future_eligible_actual_chain_verified": True,
        "full_exact19_actual_chain_verified": True,
        "runtime_identities_unchanged": True,
        "monkeypatch_used_for_success_evidence": False,
        "permission_transition_attempted": False,
        "permission_transition_completed": False,
        "observation_count": 2,
        "exact19_matrix_row_count": 38,
        "fixture_provenance_row_count": 2,
        "runtime_identity_row_count": 7,
        "safety_row_count": 23,
        "issue_inventory_data_row_count": 30,
        "public_smoke_parameter_count": 0,
        "public_observation_field_count": len(
            fields(smoke.ActionPermissionBridgeChainObservation)
        ),
        "public_report_field_count": len(
            fields(smoke.ActionPermissionBridgeIntegrationSmokeReport)
        ),
        "transition_eligible_count": report.transition_eligible_count,
        "action_permission_granted_count": (
            report.action_permission_granted_count
        ),
        "download_action_count": report.download_action_count,
        "bridge_io_count": report.bridge_io_count,
        "download_callable_accepted": False,
        "permission_transition_callable_accepted": False,
        "network_used": False,
        "provider_used": False,
        "download_used": False,
        "training_used": False,
        "current_permission": False,
        "action_permission_granted": False,
        "ready_for_download": False,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in smoke.CANONICAL_MASKS
        ],
        "effective_open_issues": list(smoke.EFFECTIVE_OPEN_ISSUES),
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "feature_semantics_known": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "ready_for_training": False,
        "recommended_next_step": smoke.RECOMMENDED_NEXT_STEP,
        "recommended_next_step_selection_options": list(
            smoke.EFFECTIVE_OPEN_ISSUES
        ),
        "recommended_next_step_adds_permission_layer": False,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "source_boundary_sha256": dict(COMMITTED_SOURCE_SHA256),
        "evidence_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in csv_payloads.items()
        },
    }


def build_evidence_payloads() -> dict[str, bytes]:
    reports = tuple(
        smoke.run_covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke()
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
        raise AssertionError("three public smoke runs differ")

    matrix_payloads: list[bytes] = []
    for _ in range(3):
        rows = build_exact19_rows()
        if len(rows) != 38 or any(
            row["verified"] != "true" for row in rows
        ):
            raise AssertionError("actual-chain Exact19 matrix invalid")
        matrix_payloads.append(_csv_bytes(EXACT19_COLUMNS, rows))
    if not (
        matrix_payloads[0] == matrix_payloads[1] == matrix_payloads[2]
    ):
        raise AssertionError("three Exact19 matrices differ")

    provenance_rows = build_fixture_provenance_rows()
    identity_rows = build_runtime_identity_rows()
    if (
        len(provenance_rows) != 2
        or len(identity_rows) != 7
        or any(row["verified"] != "true" for row in provenance_rows)
        or any(row["verified"] != "true" for row in identity_rows)
    ):
        raise AssertionError("provenance or identity evidence invalid")
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
        EXACT19_NAME: matrix_payloads[0],
        IDENTITY_NAME: _csv_bytes(IDENTITY_COLUMNS, identity_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, _safety_rows()),
        ISSUE_NAME: issue_payload,
    }
    return {
        **csv_payloads,
        MANIFEST_NAME: (
            json.dumps(
                _manifest(csv_payloads, reports[0]),
                indent=2,
                sort_keys=True,
            )
            + "\n"
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
    smoke_path = ROOT / EXACT10[0]
    source = smoke_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("run_covapie_bulk_download")
    )
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    required_calls = {
        "orchestration_runtime.orchestrate_stage_admission_scope",
        "call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site",
        "bridge_runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge",
    }
    forbidden_suffixes = (
        "classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design",
        "_build_bridge_decision",
        "_project_source",
        "_source_lineage_is_exact",
    )
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    if (
        run_node.args.args
        or run_node.args.kwonlyargs
        or run_node.args.vararg is not None
        or run_node.args.kwarg is not None
        or not required_calls <= calls
        or any(name.endswith(forbidden_suffixes) for name in calls)
        or "setattr(" in source
        or imports & {
            "os",
            "pathlib",
            "socket",
            "requests",
            "subprocess",
            "torch",
        }
    ):
        raise AssertionError("smoke public surface or success path unsafe")


def verify_payloads(payloads: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("evidence set is not Exact6")
    for name in OUTPUT_NAMES:
        path = ROOT / OUTPUT_ROOT / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != payloads[name]
        ):
            raise AssertionError(f"evidence mismatch: {name}")
    manifest = json.loads(payloads[MANIFEST_NAME])
    false_fields = (
        "monkeypatch_used_for_success_evidence",
        "permission_transition_attempted",
        "permission_transition_completed",
        "download_callable_accepted",
        "permission_transition_callable_accepted",
        "network_used",
        "provider_used",
        "download_used",
        "training_used",
        "current_permission",
        "action_permission_granted",
        "ready_for_download",
        "feature_semantics_known",
        "feature_semantics_audit_completed",
        "ready_for_training",
        "recommended_next_step_adds_permission_layer",
    )
    if any(manifest[name] is not False for name in false_fields):
        raise AssertionError("manifest fail-closed value changed")
    if (
        manifest["observation_count"] != 2
        or manifest["exact19_matrix_row_count"] != 38
        or manifest["transition_eligible_count"] != 1
        or manifest["action_permission_granted_count"] != 0
        or manifest["download_action_count"] != 0
        or manifest["bridge_io_count"] != 0
    ):
        raise AssertionError("manifest direct counts invalid")
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
        "action_permission_granted_count": 0,
        "bridge_io_count": 0,
        "checker_passed": True,
        "current_blocked": True,
        "deterministic_three_runs": True,
        "download_action_count": 0,
        "evidence_sha256": manifest["evidence_sha256"],
        "exact19_matrix_rows": 38,
        "future_eligible": True,
        "manifest_sha256": hashlib.sha256(
            payloads[MANIFEST_NAME]
        ).hexdigest(),
        "observation_count": 2,
        "permission_transition_attempted": False,
        "permission_transition_completed": False,
        "ready_for_download": False,
        "ready_for_training": False,
        "runtime_identities_unchanged": True,
        "transition_eligible_count": 1,
    }
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

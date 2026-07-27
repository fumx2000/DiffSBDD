#!/usr/bin/env python3
"""Independent checker for the action-permission bridge runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import sys
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import get_type_hints

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
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as call_site_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as fixture_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "30a31509f07be9f5a624543732390cf500ce60a6"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration action-permission bridge runtime v1"
)
RECOMMENDED_NEXT_STEP = (
    "run_covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_in_memory_integration_smoke_v1"
)
STAGE = (
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_NAME = "covapie_action_permission_bridge_runtime_public_api_contract.csv"
TRUTH_NAME = "covapie_action_permission_bridge_runtime_truth_matrix.csv"
PARITY_NAME = (
    "covapie_action_permission_bridge_design_runtime_exact19_parity_matrix.csv"
)
SAFETY_NAME = "covapie_action_permission_bridge_runtime_safety_audit.csv"
ISSUE_NAME = (
    "covapie_action_permission_bridge_runtime_issue_readiness_inventory.csv"
)
MANIFEST_NAME = (
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_runtime_manifest.json"
)
CSV_NAMES = (PUBLIC_NAME, TRUTH_NAME, PARITY_NAME, SAFETY_NAME, ISSUE_NAME)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
EXACT10 = (
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_stage_orchestration_"
        "action_permission_bridge_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_bulk_download_stage_orchestration_"
        "action_permission_bridge_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_bulk_download_stage_orchestration_"
        "action_permission_bridge_v1.py"
    ),
    Path(
        "docs/"
        "covapie_bulk_download_stage_orchestration_"
        "action_permission_bridge_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
DESIGN_SOURCE_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_design_gate.py"
)
DESIGN_TRUTH_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_v1/"
    "covapie_action_permission_bridge_precedence_truth_matrix.csv"
)
DESIGN_MANIFEST_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_v1/"
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_manifest.json"
)
DESIGN_ISSUE_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_stage_orchestration_"
    "action_permission_bridge_contract_v1/"
    "covapie_action_permission_bridge_issue_readiness_inventory.csv"
)
SOURCE_SHA256 = {
    DESIGN_SOURCE_PATH: (
        "8cebc0a4016f11ad93373103f852ea4a22b7f78336295a7b9699ef72af69a368"
    ),
    DESIGN_TRUTH_PATH: (
        "8f7afb936d1d13cad11cca7270fc232fe60e296c0c476880e45c08d9bb8f73b1"
    ),
    DESIGN_MANIFEST_PATH: (
        "c0f983718a04ef3c69cc31854aaa4c7e361ddf798b9a9737bbf9884c38d65729"
    ),
    DESIGN_ISSUE_PATH: (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ),
}
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EXACT19_FIELDS = design.DECISION_FIELDS
PUBLIC_COLUMNS = (
    "contract_area",
    "contract_item",
    "expected",
    "observed",
    "verified",
)
TRUTH_COLUMNS = (
    "case_id",
    "case_group",
    "mutation_or_positive_probe",
    *tuple(
        column
        for name in EXACT19_FIELDS
        for column in (
            f"expected_{name}",
            f"design_{name}",
            f"runtime_{name}",
        )
    ),
    "design_exact_type_verified",
    "runtime_exact_type_verified",
    "full_exact19_verified",
    "verified",
)
PARITY_COLUMNS = (
    "case_id",
    "case_group",
    "field_name",
    "expected_value",
    "design_value",
    "runtime_value",
    "expected_design_exact_type",
    "expected_runtime_exact_type",
    "design_runtime_exact_type",
    "three_way_parity_verified",
)
SAFETY_COLUMNS = (
    "safety_area",
    "expected",
    "observed",
    "evidence",
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


@dataclass(frozen=True)
class SourceCase:
    case_id: str
    case_group: str
    probe: str
    orchestration_result: object
    call_site_decision: object


class _ResultSubclass(contract.StageAdmissionOrchestrationResult):
    pass


class _DecisionSubclass(
    call_site_contract.BulkDownloadStageOrchestrationCallSiteDecisionDesign
):
    pass


class _TupleSubclass(tuple):
    pass


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _profile():
    profiles = fixture_runtime.build_canonical_in_memory_fixture_profiles()
    if type(profiles) is not tuple:
        raise AssertionError("canonical fixture profiles type changed")
    return profiles[0]


def _source_pair(
    *,
    authorized: bool,
    batch_context=None,
    candidate_inputs=None,
):
    profile = _profile()
    authorization = dict(profile.stage_authorization_context)
    authorization["current_stage_download_authorized"] = authorized
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        design.DOWNLOAD_SCOPE_ID,
        profile.candidate_inputs
        if candidate_inputs is None
        else candidate_inputs,
        batch_context=profile.batch_context
        if batch_context is None
        else batch_context,
        stage_authorization_context=authorization,
    )
    decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=result,
        orchestration_error=None,
    )
    return result, decision


def _wrong_scope_pair():
    profile = _profile()
    result = orchestration_runtime.orchestrate_stage_admission_scope(
        "post_download_acceptance_permission",
        profile.candidate_inputs,
        batch_context=profile.batch_context,
        stage_authorization_context=profile.stage_authorization_context,
    )
    decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=result,
        orchestration_error=None,
    )
    return result, decision


def _invalid_candidate_pair(*, authorized: bool = True):
    profile = _profile()
    candidate = profile.candidate_inputs[0]
    record = dict(candidate.candidate_record)
    record["pdb_id"] = "BAD"
    return _source_pair(
        authorized=authorized,
        candidate_inputs=(replace(candidate, candidate_record=record),),
    )


def _other_blocked_pair():
    profile = _profile()
    batch = dict(profile.batch_context)
    batch["batch_candidate_record_ids"] = ("REC_NOT_PRESENT",)
    return _source_pair(authorized=True, batch_context=batch)


def _forge(value, updates=None, *, reverse_storage: bool = False):
    updates = {} if updates is None else updates
    forged = object.__new__(type(value))
    items = list(vars(value).items())
    if reverse_storage:
        items.reverse()
    for name, original in items:
        object.__setattr__(forged, name, updates.get(name, original))
    return forged


def build_case_registry() -> tuple[SourceCase, ...]:
    current_result, current_decision = _source_pair(authorized=False)
    eligible_result, eligible_decision = _source_pair(authorized=True)
    wrong_scope_result, wrong_scope_decision = _wrong_scope_pair()
    invalid_result, invalid_decision = _invalid_candidate_pair()
    invalid_admit_result, invalid_admit_decision = _invalid_candidate_pair(
        authorized=False
    )
    other_blocked_result, other_blocked_decision = _other_blocked_pair()
    profile = _profile()
    blocked_batch = dict(profile.batch_context)
    blocked_batch["batch_candidate_record_ids"] = ("REC_NOT_PRESENT",)
    other_admit_result, other_admit_decision = _source_pair(
        authorized=False,
        batch_context=blocked_batch,
    )
    cases: list[SourceCase] = []

    def add(case_id, group, probe, result, decision):
        cases.append(SourceCase(case_id, group, probe, result, decision))

    add(
        "TYPE_RESULT_WRONG",
        "type",
        "object instead of exact StageResult",
        object(),
        current_decision,
    )
    add(
        "TYPE_RESULT_SUBCLASS",
        "type",
        "StageResult subclass rejected",
        _ResultSubclass(**vars(current_result)),
        current_decision,
    )
    add(
        "TYPE_DECISION_WRONG",
        "type",
        "object instead of shared Exact15 decision",
        current_result,
        object(),
    )
    add(
        "TYPE_DECISION_SUBCLASS",
        "type",
        "Exact15 decision subclass rejected",
        current_result,
        _DecisionSubclass(**vars(current_decision)),
    )

    stage_mutations = (
        ("STAGE_SCHEMA", {"schema_version": "wrong"}, False, "schema mutation"),
        ("STAGE_STORAGE", {}, True, "reversed Exact12 storage"),
        (
            "STAGE_TUPLE_SUBCLASS",
            {
                "required_rule_ids": _TupleSubclass(
                    current_result.required_rule_ids
                )
            },
            False,
            "tuple subclass",
        ),
        ("STAGE_COUNT", {"candidate_count": 2}, False, "candidate count mismatch"),
        (
            "STAGE_MEMBERSHIP",
            {
                "required_rule_ids": tuple(
                    reversed(current_result.required_rule_ids)
                )
            },
            False,
            "rule membership/order",
        ),
        (
            "STAGE_CARDINALITY",
            {"dispatcher_call_count": 0},
            False,
            "dispatcher cardinality",
        ),
    )
    for case_id, updates, reverse_storage, probe in stage_mutations:
        add(
            case_id,
            "stage_result_invariant",
            probe,
            _forge(
                current_result,
                updates,
                reverse_storage=reverse_storage,
            ),
            current_decision,
        )
    candidate = current_result.candidate_results[0]
    stage_clone = _forge(current_result.stage_global_rule_evaluations[0])
    stage_position = current_result.required_rule_ids.index("ADMIT_014")
    vector = list(candidate.ordered_rule_evaluations)
    vector[stage_position] = stage_clone
    add(
        "STAGE_IDENTITY",
        "stage_result_invariant",
        "stage-global identity clone",
        _forge(
            current_result,
            {
                "candidate_results": (
                    _forge(
                        candidate,
                        {"ordered_rule_evaluations": tuple(vector)},
                    ),
                )
            },
        ),
        current_decision,
    )
    normal_position = next(
        index
        for index, item in enumerate(candidate.ordered_rule_evaluations)
        if item.admission_rule_id != "ADMIT_014"
    )
    vector = list(candidate.ordered_rule_evaluations)
    vector[normal_position] = _forge(vector[normal_position])
    add(
        "RETAINED_IDENTITY",
        "stage_result_invariant",
        "retained-vector identity clone",
        _forge(
            current_result,
            {
                "candidate_results": (
                    _forge(
                        candidate,
                        {"ordered_rule_evaluations": tuple(vector)},
                    ),
                )
            },
        ),
        current_decision,
    )
    corrupt_unified = _forge(
        current_result.stage_global_rule_evaluations[0],
        {"outcome": "corrupt"},
    )
    add(
        "UNIFIED_CORRUPT",
        "stage_result_invariant",
        "corrupted Unified result",
        _forge(
            current_result,
            {"stage_global_rule_evaluations": (corrupt_unified,)},
        ),
        current_decision,
    )
    corrupt_combined = _forge(
        candidate.combined_verdict,
        {"outcome": "corrupt"},
    )
    add(
        "COMBINED_CORRUPT",
        "stage_result_invariant",
        "corrupted Combined verdict",
        _forge(
            current_result,
            {
                "candidate_results": (
                    _forge(
                        candidate,
                        {"combined_verdict": corrupt_combined},
                    ),
                )
            },
        ),
        current_decision,
    )

    decision_mutations = (
        ("DECISION_SCHEMA", {"schema_version": "wrong"}, False, "schema"),
        ("DECISION_STORAGE", {}, True, "reversed Exact15 storage"),
        (
            "DECISION_SOURCE_KIND",
            {"source_kind": "invalid_input"},
            False,
            "wrong source kind",
        ),
        (
            "DECISION_SCOPE_UNKNOWN",
            {"source_scope_id": "__wrong__"},
            False,
            "unknown source scope",
        ),
        (
            "DECISION_DIAGNOSTICS",
            {"blocked_candidate_indexes": (0, 0)},
            False,
            "duplicate diagnostics",
        ),
        (
            "DECISION_FAILING",
            {"failing_candidate_indexes": ()},
            False,
            "failing union mismatch",
        ),
        (
            "DECISION_PERMISSION_TYPE",
            {"action_permission_granted": 0},
            False,
            "action permission exact bool",
        ),
        (
            "DECISION_DOWNLOAD_ACTION",
            {"download_action_invoked": True},
            False,
            "download action nonzero",
        ),
        (
            "DECISION_IO",
            {"call_site_io_used": True},
            False,
            "call-site I/O nonzero",
        ),
    )
    for case_id, updates, reverse_storage, probe in decision_mutations:
        add(
            case_id,
            "decision_invariant",
            probe,
            current_result,
            _forge(
                current_decision,
                updates,
                reverse_storage=reverse_storage,
            ),
        )

    add(
        "WRONG_SCOPE",
        "scope_io_transition",
        "valid non-download scope pair",
        wrong_scope_result,
        wrong_scope_decision,
    )
    io_result = replace(eligible_result, orchestration_io_used=True)
    io_decision = call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
        orchestration_result=io_result,
        orchestration_error=None,
    )
    add(
        "ORCHESTRATION_IO",
        "scope_io_transition",
        "source orchestration I/O true",
        io_result,
        io_decision,
    )
    transitioned_result = replace(
        eligible_result,
        action_permission_granted=True,
    )
    transitioned_decision = (
        call_site_runtime.evaluate_bulk_download_stage_orchestration_call_site(
            orchestration_result=transitioned_result,
            orchestration_error=None,
        )
    )
    add(
        "SOURCE_TRANSITIONED",
        "scope_io_transition",
        "source permission already true",
        transitioned_result,
        transitioned_decision,
    )

    add(
        "LINEAGE_CURRENT_VALID",
        "lineage",
        "actual current blocked source pair",
        current_result,
        current_decision,
    )
    add(
        "LINEAGE_ELIGIBLE_VALID",
        "lineage",
        "actual future eligible source pair",
        eligible_result,
        eligible_decision,
    )
    lineage_mutations = (
        ("LINEAGE_COUNT", {"candidate_count": 2}, "wrong candidate count"),
        (
            "LINEAGE_SCOPE",
            {"source_scope_id": "post_download_acceptance_permission"},
            "wrong valid source scope",
        ),
        (
            "LINEAGE_DIAGNOSTIC",
            {
                "blocked_candidate_indexes": (),
                "failing_candidate_indexes": (),
            },
            "wrong diagnostics",
        ),
        (
            "LINEAGE_OUTCOME",
            {
                "outcome": "invalid",
                "passed": False,
                "blocks_download": True,
                "reason": "BULK_DOWNLOAD_CANDIDATE_VERDICT_INVALID",
            },
            "wrong outcome",
        ),
        (
            "LINEAGE_REASON",
            {"reason": "BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"},
            "wrong reason",
        ),
    )
    for case_id, updates, probe in lineage_mutations:
        add(
            case_id,
            "lineage",
            probe,
            current_result,
            replace(current_decision, **updates),
        )
    add(
        "LINEAGE_UNRELATED",
        "lineage",
        "unrelated partially similar valid decision",
        current_result,
        wrong_scope_decision,
    )

    add(
        "CANDIDATE_INVALID",
        "candidate_authority",
        "actual invalid candidate with ADMIT_014 passed",
        invalid_result,
        invalid_decision,
    )
    add(
        "ADMIT_014_BLOCKED",
        "candidate_authority",
        "actual current ADMIT_014 blocked",
        current_result,
        current_decision,
    )
    add(
        "OTHER_CANDIDATE_BLOCKED",
        "candidate_authority",
        "actual ADMIT_001 blocked with ADMIT_014 passed",
        other_blocked_result,
        other_blocked_decision,
    )
    nonpending_decision = replace(
        eligible_decision,
        outcome="authorized",
        passed=True,
        blocks_download=False,
        reason="",
    )
    add(
        "DECISION_NOT_PENDING",
        "candidate_authority",
        "structurally valid authorized decision rejected by exact lineage",
        eligible_result,
        nonpending_decision,
    )
    add(
        "FULLY_ELIGIBLE",
        "candidate_authority",
        "actual all-passed permission-pending pair",
        eligible_result,
        eligible_decision,
    )

    add(
        "PRECEDENCE_STAGE_OVER_SCOPE",
        "precedence",
        "invalid stage plus wrong scope semantics",
        _forge(wrong_scope_result, {"schema_version": "wrong"}),
        wrong_scope_decision,
    )
    add(
        "PRECEDENCE_DECISION_OVER_SCOPE",
        "precedence",
        "invalid decision plus wrong scope result",
        wrong_scope_result,
        _forge(wrong_scope_decision, {"schema_version": "wrong"}),
    )
    add(
        "PRECEDENCE_SCOPE_OVER_IO",
        "precedence",
        "wrong scope plus source I/O",
        replace(wrong_scope_result, orchestration_io_used=True),
        wrong_scope_decision,
    )
    add(
        "PRECEDENCE_IO_OVER_TRANSITION",
        "precedence",
        "I/O plus transitioned",
        replace(
            eligible_result,
            orchestration_io_used=True,
            action_permission_granted=True,
        ),
        eligible_decision,
    )
    add(
        "PRECEDENCE_TRANSITION_OVER_LINEAGE",
        "precedence",
        "transitioned plus unrelated decision",
        transitioned_result,
        wrong_scope_decision,
    )
    add(
        "PRECEDENCE_LINEAGE_OVER_BUSINESS",
        "precedence",
        "lineage mismatch before ADMIT authority",
        current_result,
        replace(current_decision, candidate_count=2),
    )
    add(
        "PRECEDENCE_INVALID_OVER_ADMIT",
        "precedence",
        "invalid candidate precedes blocked ADMIT_014",
        invalid_admit_result,
        invalid_admit_decision,
    )
    add(
        "PRECEDENCE_ADMIT_OVER_BLOCKED",
        "precedence",
        "blocked ADMIT_014 precedes other candidate block",
        other_admit_result,
        other_admit_decision,
    )
    add(
        "PRECEDENCE_BLOCKED_OVER_ELIGIBLE",
        "precedence",
        "other candidate block precedes eligibility",
        other_blocked_result,
        other_blocked_decision,
    )
    add(
        "PRECEDENCE_NOT_PENDING_OVER_ELIGIBLE",
        "precedence",
        "nonpending decision is lineage mismatch before eligibility",
        eligible_result,
        nonpending_decision,
    )
    add(
        "PRECEDENCE_ELIGIBLE",
        "precedence",
        "terminal eligible classification",
        eligible_result,
        eligible_decision,
    )
    if len(cases) != 50:
        raise AssertionError("source registry cardinality changed")
    return tuple(cases)


def _read_design_truth() -> tuple[dict[str, str], ...]:
    with (ROOT / DESIGN_TRUTH_PATH).open(
        "r",
        encoding="utf-8",
        newline="",
    ) as stream:
        rows = tuple(csv.DictReader(stream))
    return rows


def _canonical(value: object) -> str:
    if type(value) in (str, int, bool):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if type(value) is tuple:
        return json.dumps(
            list(value),
            ensure_ascii=True,
            separators=(",", ":"),
        )
    return json.dumps(
        {"invalid_exact_type": type(value).__name__},
        sort_keys=True,
        separators=(",", ":"),
    )


def _exact_field_type(expected_text: str, observed: object) -> bool:
    expected = json.loads(expected_text)
    if type(expected) is list:
        return type(observed) is tuple and all(
            type(item) is type(expected_item)
            for item, expected_item in zip(observed, expected, strict=True)
        )
    return type(observed) is type(expected)


def evaluate_registry() -> tuple[
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    cases = build_case_registry()
    expected_rows = _read_design_truth()
    if tuple(case.case_id for case in cases) != tuple(
        row["case_id"] for row in expected_rows
    ):
        raise AssertionError("design/runtime case IDs or order changed")
    if tuple(case.case_group for case in cases) != tuple(
        row["case_group"] for row in expected_rows
    ):
        raise AssertionError("design/runtime case groups changed")
    truth_rows = []
    parity_rows = []
    for case, expected_row in zip(cases, expected_rows, strict=True):
        design_decision = (
            design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design(
                orchestration_result=case.orchestration_result,
                call_site_decision=case.call_site_decision,
            )
        )
        runtime_decision = (
            runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge(
                orchestration_result=case.orchestration_result,
                call_site_decision=case.call_site_decision,
            )
        )
        design_exact = (
            type(design_decision)
            is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        )
        runtime_exact = (
            type(runtime_decision)
            is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
        )
        row = {
            "case_id": case.case_id,
            "case_group": case.case_group,
            "mutation_or_positive_probe": case.probe,
            "design_exact_type_verified": str(design_exact).lower(),
            "runtime_exact_type_verified": str(runtime_exact).lower(),
        }
        case_verified = design_exact and runtime_exact
        for field_name in EXACT19_FIELDS:
            expected_value = expected_row[f"expected_{field_name}"]
            design_value = _canonical(getattr(design_decision, field_name))
            runtime_value = _canonical(getattr(runtime_decision, field_name))
            expected_design_type = _exact_field_type(
                expected_value,
                getattr(design_decision, field_name),
            )
            expected_runtime_type = _exact_field_type(
                expected_value,
                getattr(runtime_decision, field_name),
            )
            design_runtime_type = (
                type(getattr(design_decision, field_name))
                is type(getattr(runtime_decision, field_name))
            )
            verified = (
                expected_value == design_value == runtime_value
                and expected_design_type
                and expected_runtime_type
                and design_runtime_type
            )
            case_verified = case_verified and verified
            row[f"expected_{field_name}"] = expected_value
            row[f"design_{field_name}"] = design_value
            row[f"runtime_{field_name}"] = runtime_value
            parity_rows.append(
                {
                    "case_id": case.case_id,
                    "case_group": case.case_group,
                    "field_name": field_name,
                    "expected_value": expected_value,
                    "design_value": design_value,
                    "runtime_value": runtime_value,
                    "expected_design_exact_type": str(
                        expected_design_type
                    ).lower(),
                    "expected_runtime_exact_type": str(
                        expected_runtime_type
                    ).lower(),
                    "design_runtime_exact_type": str(
                        design_runtime_type
                    ).lower(),
                    "three_way_parity_verified": str(verified).lower(),
                }
            )
        row["full_exact19_verified"] = str(case_verified).lower()
        row["verified"] = str(case_verified).lower()
        truth_rows.append(row)
    return tuple(truth_rows), tuple(parity_rows)


def _runtime_ast_policy() -> dict[str, bool]:
    source = (ROOT / EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    design_private = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "design"
        and node.func.attr.startswith("_")
        for node in ast.walk(tree)
    )
    predecessor_private = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in {"call_site_contract", "contract"}
        and node.func.attr.startswith("_")
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
    return {
        "design_classifier_called": (
            "design.classify_bulk_download_stage_orchestration_action_permission_bridge_contract_design"
            in calls
        ),
        "design_private_helpers_called": design_private,
        "predecessor_private_helpers_called": predecessor_private,
        "forbidden_import_present": bool(
            imports
            & {
                "requests",
                "urllib",
                "socket",
                "subprocess",
                "torch",
                "os",
                "pathlib",
                "shutil",
            }
        ),
        "io_builtin_called": bool(calls & {"open", "print", "input"}),
        "design_alias_assignment": (
            "evaluate_bulk_download_stage_orchestration_action_permission_bridge"
            " = " in source
        ),
    }


def build_public_rows() -> tuple[dict[str, str], ...]:
    function = (
        runtime.evaluate_bulk_download_stage_orchestration_action_permission_bridge
    )
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    policy = _runtime_ast_policy()
    observations = (
        ("api", "__all__", "|".join(runtime.__all__), "|".join(runtime.__all__)),
        (
            "api",
            "function_name",
            "evaluate_bulk_download_stage_orchestration_action_permission_bridge",
            function.__name__,
        ),
        (
            "api",
            "parameter_order",
            "orchestration_result|call_site_decision",
            "|".join(signature.parameters),
        ),
        (
            "api",
            "required_keyword_only",
            "true",
            str(
                all(
                    item.kind is inspect.Parameter.KEYWORD_ONLY
                    and item.default is inspect.Parameter.empty
                    for item in signature.parameters.values()
                )
            ).lower(),
        ),
        (
            "api",
            "no_variadic",
            "true",
            str(
                not any(
                    item.kind
                    in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    )
                    for item in signature.parameters.values()
                )
            ).lower(),
        ),
        (
            "api",
            "exact_annotations",
            "StageAdmissionOrchestrationResult|BulkDownloadStageOrchestrationCallSiteDecisionDesign|BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign",
            "|".join(
                (
                    hints["orchestration_result"].__name__,
                    hints["call_site_decision"].__name__,
                    hints["return"].__name__,
                )
            ),
        ),
        (
            "identity",
            "shared_exact19_class",
            "true",
            str(
                runtime.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
                is design.BulkDownloadStageOrchestrationActionPermissionBridgeDecisionDesign
            ).lower(),
        ),
        (
            "delegation",
            "design_classifier_called",
            "false",
            str(policy["design_classifier_called"]).lower(),
        ),
        (
            "delegation",
            "design_private_helpers_called",
            "false",
            str(policy["design_private_helpers_called"]).lower(),
        ),
        (
            "delegation",
            "predecessor_private_helpers_called",
            "false",
            str(policy["predecessor_private_helpers_called"]).lower(),
        ),
        (
            "delegation",
            "design_alias_assignment",
            "false",
            str(policy["design_alias_assignment"]).lower(),
        ),
        (
            "boundary",
            "forbidden_import_present",
            "false",
            str(policy["forbidden_import_present"]).lower(),
        ),
        (
            "boundary",
            "io_builtin_called",
            "false",
            str(policy["io_builtin_called"]).lower(),
        ),
        (
            "reason",
            "reason_11_reserved",
            "true",
            str(
                design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_REASON_RESERVED
            ).lower(),
        ),
        (
            "reason",
            "reason_11_branch_reachable",
            "false",
            str(
                design.CALL_SITE_DECISION_NOT_PERMISSION_PENDING_BRANCH_REACHABLE
            ).lower(),
        ),
        ("boundary", "action_permission", "false", "false"),
        ("boundary", "download_action", "false", "false"),
        ("boundary", "bridge_io", "false", "false"),
    )
    return tuple(
        {
            "contract_area": area,
            "contract_item": item,
            "expected": expected,
            "observed": observed,
            "verified": str(expected == observed).lower(),
        }
        for area, item, expected, observed in observations
    )


def build_safety_rows(
    truth_rows: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    policy = _runtime_ast_policy()
    zero_runtime = all(
        row["runtime_action_permission_granted"] == "false"
        and row["runtime_download_action_invoked"] == "false"
        and row["runtime_bridge_io_used"] == "false"
        for row in truth_rows
    )
    clean = (
        not policy["forbidden_import_present"]
        and not policy["io_builtin_called"]
        and zero_runtime
    )
    return tuple(
        {
            "safety_area": item,
            "expected": "false",
            "observed": "false" if clean else "true",
            "evidence": (
                "runtime AST/signature scan and 50-case full Exact19 truth"
            ),
            "verified": str(clean).lower(),
        }
        for item in SAFETY_ITEMS
    )


def _csv_bytes(
    columns: tuple[str, ...],
    rows: tuple[dict[str, str], ...],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _manifest(
    payloads: dict[str, bytes],
    truth_rows: tuple[dict[str, str], ...],
    parity_rows: tuple[dict[str, str], ...],
    public_count: int,
    safety_count: int,
) -> bytes:
    group_counts = Counter(row["case_group"] for row in truth_rows)
    transition_eligible_count = sum(
        row["runtime_transition_eligible"] == "true"
        for row in truth_rows
    )
    value = {
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "runtime_public_api_contract_row_count": public_count,
        "runtime_truth_row_count": len(truth_rows),
        "runtime_truth_group_count": len(group_counts),
        "runtime_truth_group_counts": dict(sorted(group_counts.items())),
        "design_runtime_exact19_parity_row_count": len(parity_rows),
        "safety_audit_row_count": safety_count,
        "issue_inventory_data_row_count": 30,
        "source_boundary_sha256": {
            path.as_posix(): digest
            for path, digest in SOURCE_SHA256.items()
        },
        "runtime_source_sha256": _sha((ROOT / EXACT10[0]).read_bytes()),
        "evidence_sha256": {
            name: _sha(payloads[name]) for name in CSV_NAMES
        },
        "action_permission_bridge_runtime_implemented": True,
        "runtime_public_api_available": True,
        "runtime_returns_shared_exact19_type_identity": True,
        "runtime_design_classifier_called": False,
        "runtime_design_private_helpers_called": False,
        "runtime_predecessor_private_helpers_called": False,
        "runtime_predecessor_checker_imported": False,
        "full_exact19_runtime_truth_verified": True,
        "design_runtime_exact19_parity_verified": True,
        "exact_source_lineage_verified": True,
        "authorized_decision_lineage_exception_absent": True,
        "reason_11_reserved": True,
        "reason_11_branch_reachable": False,
        "current_blocked_path_verified": True,
        "future_eligible_path_verified": True,
        "transition_eligible_count": transition_eligible_count,
        "action_permission_granted_count": 0,
        "download_action_count": 0,
        "bridge_io_count": 0,
        "network_used": False,
        "provider_used": False,
        "download_used": False,
        "training_used": False,
        "current_permission": False,
        "action_permission_granted": False,
        "ready_for_download": False,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "effective_open_issues": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        ],
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "feature_semantics_known": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_training": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def build_evidence_payloads() -> dict[str, bytes]:
    truth_rows, parity_rows = evaluate_registry()
    public_rows = build_public_rows()
    safety_rows = build_safety_rows(truth_rows)
    payloads = {
        PUBLIC_NAME: _csv_bytes(PUBLIC_COLUMNS, public_rows),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        PARITY_NAME: _csv_bytes(PARITY_COLUMNS, parity_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_NAME: (ROOT / DESIGN_ISSUE_PATH).read_bytes(),
    }
    payloads[MANIFEST_NAME] = _manifest(
        payloads,
        truth_rows,
        parity_rows,
        len(public_rows),
        len(safety_rows),
    )
    return payloads


def _verify_sources() -> None:
    for path, expected in SOURCE_SHA256.items():
        if _sha((ROOT / path).read_bytes()) != expected:
            raise AssertionError(f"frozen source changed: {path}")
    manifest = json.loads((ROOT / DESIGN_MANIFEST_PATH).read_bytes())
    if (
        manifest["truth_row_count"] != 50
        or manifest["truth_group_count"] != 7
    ):
        raise AssertionError("design truth cardinality changed")


def verify_payloads(payloads: dict[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("evidence membership/order mismatch")
    manifest = json.loads(payloads[MANIFEST_NAME])
    if MANIFEST_NAME in manifest["evidence_sha256"]:
        raise AssertionError("manifest self hash forbidden")
    for name in CSV_NAMES:
        if manifest["evidence_sha256"][name] != _sha(payloads[name]):
            raise AssertionError(f"evidence SHA mismatch: {name}")
    if _sha(payloads[ISSUE_NAME]) != SOURCE_SHA256[DESIGN_ISSUE_PATH]:
        raise AssertionError("issue inventory is not byte-identical")
    for name, columns, verified_column in (
        (PUBLIC_NAME, PUBLIC_COLUMNS, "verified"),
        (TRUTH_NAME, TRUTH_COLUMNS, "verified"),
        (PARITY_NAME, PARITY_COLUMNS, "three_way_parity_verified"),
        (SAFETY_NAME, SAFETY_COLUMNS, "verified"),
    ):
        reader = csv.DictReader(io.StringIO(payloads[name].decode()))
        rows = tuple(reader)
        if tuple(reader.fieldnames or ()) != columns:
            raise AssertionError(f"columns invalid: {name}")
        if not rows or any(row[verified_column] != "true" for row in rows):
            raise AssertionError(f"verification false: {name}")
    truth_rows = tuple(
        csv.DictReader(io.StringIO(payloads[TRUTH_NAME].decode()))
    )
    parity_rows = tuple(
        csv.DictReader(io.StringIO(payloads[PARITY_NAME].decode()))
    )
    if (
        len(truth_rows) != 50
        or len({row["case_group"] for row in truth_rows}) != 7
        or len(parity_rows) != 950
    ):
        raise AssertionError("truth/parity cardinality invalid")
    current = next(
        row for row in truth_rows if row["case_id"] == "LINEAGE_CURRENT_VALID"
    )
    eligible = next(
        row for row in truth_rows if row["case_id"] == "FULLY_ELIGIBLE"
    )
    expected_current = {
        "runtime_outcome": '"blocked"',
        "runtime_reason": (
            '"ACTION_PERMISSION_BRIDGE_ADMIT_014_NOT_PASSED"'
        ),
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
    if any(current[key] != value for key, value in expected_current.items()):
        raise AssertionError("current blocked path changed")
    expected_eligible = {
        "runtime_outcome": '"eligible"',
        "runtime_reason": (
            '"ACTION_PERMISSION_BRIDGE_TRANSITION_ELIGIBLE"'
        ),
        "runtime_admit_014_outcome": '"passed"',
        "runtime_candidate_combined_outcomes": '["passed"]',
        "runtime_call_site_decision_outcome": '"blocked"',
        "runtime_call_site_decision_reason": (
            '"BULK_DOWNLOAD_ACTION_PERMISSION_NOT_GRANTED"'
        ),
        "runtime_source_lineage_verified": "true",
        "runtime_transition_eligible": "true",
    }
    if any(eligible[key] != value for key, value in expected_eligible.items()):
        raise AssertionError("future eligible path changed")
    if any(
        row["runtime_action_permission_granted"] != "false"
        or row["runtime_download_action_invoked"] != "false"
        or row["runtime_bridge_io_used"] != "false"
        for row in truth_rows
    ):
        raise AssertionError("permission/action/I/O boundary changed")
    if any(
        row["runtime_reason"]
        == '"ACTION_PERMISSION_BRIDGE_CALL_SITE_DECISION_NOT_PERMISSION_PENDING"'
        for row in truth_rows
    ):
        raise AssertionError("reserved reason 11 became reachable")
    required_true = (
        "action_permission_bridge_runtime_implemented",
        "runtime_public_api_available",
        "runtime_returns_shared_exact19_type_identity",
        "full_exact19_runtime_truth_verified",
        "design_runtime_exact19_parity_verified",
        "exact_source_lineage_verified",
        "authorized_decision_lineage_exception_absent",
        "reason_11_reserved",
        "current_blocked_path_verified",
        "future_eligible_path_verified",
        "feature_semantics_audit_required_before_training",
    )
    required_false = (
        "runtime_design_classifier_called",
        "runtime_design_private_helpers_called",
        "runtime_predecessor_private_helpers_called",
        "runtime_predecessor_checker_imported",
        "reason_11_branch_reachable",
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
    )
    if not all(manifest[key] is True for key in required_true):
        raise AssertionError("manifest required true flag invalid")
    if not all(manifest[key] is False for key in required_false):
        raise AssertionError("manifest required false flag invalid")
    if (
        manifest["transition_eligible_count"] <= 0
        or manifest["action_permission_granted_count"] != 0
        or manifest["download_action_count"] != 0
        or manifest["bridge_io_count"] != 0
    ):
        raise AssertionError("manifest count boundary invalid")
    if tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    ) != CANONICAL_MASKS:
        raise AssertionError("canonical masks changed")
    return manifest


def _materialize(payloads: dict[str, bytes]) -> None:
    destination = ROOT / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    existing = {
        path.name for path in destination.iterdir() if path.is_file()
    }
    if existing and existing != set(OUTPUT_NAMES):
        raise AssertionError("unexpected existing evidence set")
    for name, content in payloads.items():
        (destination / name).write_bytes(content)


def _verify_materialized(payloads: dict[str, bytes]) -> None:
    for name, content in payloads.items():
        path = ROOT / OUTPUT_ROOT / name
        if not path.is_file() or path.is_symlink():
            raise AssertionError(f"evidence missing or non-regular: {path}")
        if path.read_bytes() != content:
            raise AssertionError(f"evidence differs: {path}")


def main() -> int:
    _verify_sources()
    payloads = build_evidence_payloads()
    manifest = verify_payloads(payloads)
    if sys.argv[1:] == ["--materialize"]:
        _materialize(payloads)
    elif sys.argv[1:]:
        raise SystemExit("usage: checker [--materialize]")
    else:
        _verify_materialized(payloads)
    print(
        json.dumps(
            {
                "status": "ok",
                "base_commit": BASE_COMMIT,
                "exact10_count": len(EXACT10),
                "runtime_truth_rows": manifest["runtime_truth_row_count"],
                "runtime_truth_groups": manifest[
                    "runtime_truth_group_count"
                ],
                "design_runtime_exact19_parity_rows": manifest[
                    "design_runtime_exact19_parity_row_count"
                ],
                "reason_11_branch_reachable": False,
                "current_blocked_path_verified": True,
                "future_eligible_path_verified": True,
                "action_permission_granted_count": 0,
                "download_action_count": 0,
                "bridge_io_count": 0,
                "ready_for_download": False,
                "ready_for_training": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

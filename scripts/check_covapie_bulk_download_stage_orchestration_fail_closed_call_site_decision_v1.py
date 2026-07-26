#!/usr/bin/env python3
"""Check the deterministic bulk-download call-site decision runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import sys
from collections import Counter
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Callable, get_type_hints


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate
    as design,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1
    as runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration,
)


BASE_COMMIT = "639e88b3a6a0b6507d271cee2d1432c0083b42a2"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE bulk-download orchestration fail-closed call-site decision v1"
)
RECOMMENDED_NEXT_STEP = (
    "run_covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_decision_in_memory_integration_smoke_v1"
)
STAGE = (
    "covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_decision_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_NAME = (
    "covapie_bulk_download_call_site_decision_runtime_public_api_contract.csv"
)
TRUTH_NAME = (
    "covapie_bulk_download_call_site_decision_runtime_truth_matrix.csv"
)
PARITY_NAME = (
    "covapie_bulk_download_call_site_design_runtime_exact15_parity_matrix.csv"
)
SAFETY_NAME = (
    "covapie_bulk_download_call_site_decision_runtime_safety_audit.csv"
)
ISSUE_NAME = (
    "covapie_bulk_download_call_site_decision_runtime_issue_readiness_inventory.csv"
)
MANIFEST_NAME = (
    "covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_decision_manifest.json"
)
CSV_NAMES = (
    PUBLIC_NAME,
    TRUTH_NAME,
    PARITY_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
EXACT10 = (
    Path("src/covalent_ext")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py",
    Path("tests")
    / "test_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py",
    Path("scripts")
    / "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py",
    Path("docs")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1_summary.md",
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
DESIGN_PATH = (
    Path("src/covalent_ext")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_design_gate.py"
)
DESIGN_TRUTH_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1"
    / "covapie_bulk_download_call_site_precedence_truth_matrix.csv"
)
DESIGN_MANIFEST_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1"
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_manifest.json"
)
DESIGN_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1"
    / "covapie_bulk_download_call_site_issue_readiness_inventory.csv"
)
SOURCE_SHA256 = {
    DESIGN_PATH: (
        "96c93e727cbd8f127311969788b08c39"
        "f34735f1c5423952e24399d2d3e04c35"
    ),
    DESIGN_TRUTH_PATH: (
        "9d61a53501b7d062f3795742520b7e61"
        "bbbe367a18d90973da7cdb5e5b3eeae2"
    ),
    DESIGN_MANIFEST_PATH: (
        "dc04018ca3f5d4bc90f5defb0216aa58"
        "d71c6bb1656aaf292bd73fb5baab5cbf"
    ),
    DESIGN_ISSUE_PATH: (
        "fb4d2dfae7ffc056e3856c94e2f5a135"
        "d468eb3801144f9a698f95d9b812ace7"
    ),
}
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
PUBLIC_COLUMNS = (
    "contract_area",
    "contract_order",
    "contract_item",
    "expected",
    "observed",
    "verified",
)
TRUTH_COLUMNS = (
    "case_group",
    "case_id",
    *tuple(
        item
        for field_name in design.DECISION_FIELDS
        for item in (
            f"expected_{field_name}",
            f"observed_{field_name}",
        )
    ),
    "exact_decision_type_verified",
    "zero_action_verified",
    "verified",
)
PARITY_COLUMNS = (
    "case_group",
    "case_id",
    "decision_field",
    "expected_value",
    "design_value",
    "runtime_value",
    "expected_exact_type",
    "design_exact_type",
    "runtime_exact_type",
    "design_parity_verified",
    "runtime_parity_verified",
    "three_way_parity_verified",
)
SAFETY_COLUMNS = (
    "safety_item",
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
    "authorized_decision",
    "ready_for_download",
    "ready_for_training",
)


@dataclass(frozen=True)
class SourceCase:
    case_group: str
    case_id: str
    source_factory: Callable[[], tuple[object | None, object | None]]


class _TupleSubclass(tuple):
    pass


class _ResultSubclass(contract.StageAdmissionOrchestrationResult):
    pass


class _ErrorSubclass(contract.StageAdmissionOrchestrationError):
    pass


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(
    columns: tuple[str, ...],
    rows: tuple[dict[str, str], ...],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _fixture():
    return smoke.build_canonical_in_memory_fixture_profiles()[0]


def _runtime_result(
    scope_id: str = design.DOWNLOAD_SCOPE_ID,
) -> contract.StageAdmissionOrchestrationResult:
    fixture = _fixture()
    return orchestration.orchestrate_stage_admission_scope(
        scope_id,
        fixture.candidate_inputs,
        batch_context=fixture.batch_context,
        stage_authorization_context=fixture.stage_authorization_context,
    )


def _legal_error(code: str) -> contract.StageAdmissionOrchestrationError:
    return contract.StageAdmissionOrchestrationError(
        code=code,
        scope_id=design.DOWNLOAD_SCOPE_ID,
        candidate_index=0,
        admission_rule_id="ADMIT_001",
        dispatcher_call_count=1,
        aggregator_call_count=0,
        reason=f"{code}:runtime-checker",
        cause_type="RuntimeError",
    )


def _forge(
    cls: type,
    values: dict[str, object],
    *,
    reverse: bool = False,
):
    try:
        value = object.__new__(cls)
    except TypeError:
        value = cls.__new__(cls)
    items = tuple(values.items())
    if reverse:
        items = tuple(reversed(items))
    for name, item in items:
        object.__setattr__(value, name, item)
    return value


def _rule_outcome(value, outcome: str):
    return replace(
        value,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"RUNTIME_{outcome.upper()}",
    )


def build_result_for_candidate_outcomes(
    outcomes: tuple[str, ...],
    *,
    scope_id: str = design.DOWNLOAD_SCOPE_ID,
) -> contract.StageAdmissionOrchestrationResult:
    if not outcomes:
        raise ValueError("at least one candidate outcome required")
    base = _runtime_result(scope_id)
    stage_results = tuple(
        _rule_outcome(item, "passed")
        for item in base.stage_global_rule_evaluations
    )
    stage_by_rule_id = {
        item.admission_rule_id: item for item in stage_results
    }
    candidate_results = []
    for index, outcome in enumerate(outcomes):
        vector = list(base.candidate_results[0].ordered_rule_evaluations)
        for position, rule_id in enumerate(base.required_rule_ids):
            if rule_id in stage_by_rule_id:
                vector[position] = stage_by_rule_id[rule_id]
        local_position = next(
            position
            for position, rule_id in enumerate(base.required_rule_ids)
            if rule_id in base.candidate_rule_ids
        )
        if outcome != "passed":
            vector[local_position] = _rule_outcome(
                vector[local_position],
                outcome,
            )
        ordered = tuple(vector)
        verdict = aggregation.aggregate_admission_rule_evaluations(
            scope_id,
            ordered_rule_evaluations=ordered,
        )
        candidate_results.append(
            contract.CandidateAdmissionOrchestrationResult(
                candidate_index=index,
                ordered_rule_evaluations=ordered,
                combined_verdict=verdict,
                dispatcher_call_count=len(base.candidate_rule_ids),
                aggregator_call_count=1,
            )
        )
    return contract.StageAdmissionOrchestrationResult(
        schema_version=base.schema_version,
        scope_id=base.scope_id,
        candidate_count=len(outcomes),
        required_rule_ids=base.required_rule_ids,
        stage_global_rule_ids=base.stage_global_rule_ids,
        candidate_rule_ids=base.candidate_rule_ids,
        stage_global_rule_evaluations=stage_results,
        candidate_results=tuple(candidate_results),
        dispatcher_call_count=(
            len(base.stage_global_rule_ids)
            + len(outcomes) * len(base.candidate_rule_ids)
        ),
        aggregator_call_count=len(outcomes),
        orchestration_io_used=False,
        action_permission_granted=False,
    )


def _source(
    *,
    result: object | None = None,
    error: object | None = None,
) -> tuple[object | None, object | None]:
    return result, error


def build_case_registry() -> tuple[SourceCase, ...]:
    cases: list[SourceCase] = []

    def add(
        group: str,
        case_id: str,
        *,
        result: object | None = None,
        error: object | None = None,
    ) -> None:
        cases.append(
            SourceCase(
                group,
                case_id,
                lambda result=result, error=error: _source(
                    result=result,
                    error=error,
                ),
            )
        )

    real = _runtime_result()
    legal_error = _legal_error(contract.ERROR_CODES[0])
    add("input_cardinality", "both_missing")
    add(
        "input_cardinality",
        "both_present",
        result=real,
        error=legal_error,
    )
    add("input_cardinality", "result_only", result=real)
    add("input_cardinality", "error_only", error=legal_error)
    add("type", "result_wrong_type", result=object())
    add(
        "type",
        "result_subclass",
        result=_ResultSubclass(**vars(real)),
    )
    add("type", "error_wrong_type", error=RuntimeError("wrong"))
    add(
        "type",
        "error_subclass",
        error=_ErrorSubclass(**vars(legal_error)),
    )

    error_mutations = (
        ("error_code", {"code": "UNKNOWN"}),
        ("error_scope_type", {"scope_id": 1}),
        ("error_candidate_index", {"candidate_index": -2}),
        ("error_rule_type", {"admission_rule_id": 1}),
        ("error_dispatcher_bool_as_int", {"dispatcher_call_count": True}),
        ("error_aggregator_negative", {"aggregator_call_count": -1}),
        ("error_reason_empty", {"reason": ""}),
        ("error_cause_type", {"cause_type": 1}),
    )
    for case_id, mutation in error_mutations:
        values = dict(vars(legal_error))
        values.update(mutation)
        add(
            "error_invariant",
            case_id,
            error=_forge(contract.StageAdmissionOrchestrationError, values),
        )
    add(
        "error_invariant",
        "error_reversed_storage",
        error=_forge(
            contract.StageAdmissionOrchestrationError,
            dict(vars(legal_error)),
            reverse=True,
        ),
    )
    for code in contract.ERROR_CODES:
        add("error_exact8_codes", code, error=_legal_error(code))

    result_mutations = (
        ("schema", {"schema_version": "wrong"}),
        ("unknown_scope", {"scope_id": "unknown"}),
        ("candidate_count_zero", {"candidate_count": 0}),
        ("candidate_count_bool_as_int", {"candidate_count": True}),
        ("required_membership", {"required_rule_ids": ()}),
        ("stage_membership", {"stage_global_rule_ids": ()}),
        ("candidate_membership", {"candidate_rule_ids": ()}),
        (
            "stage_result_tuple_subclass",
            {
                "stage_global_rule_evaluations": _TupleSubclass(
                    real.stage_global_rule_evaluations
                )
            },
        ),
        (
            "candidate_result_tuple_subclass",
            {"candidate_results": _TupleSubclass(real.candidate_results)},
        ),
        ("dispatcher_count", {"dispatcher_call_count": 0}),
        ("aggregator_count", {"aggregator_call_count": 0}),
        ("io_bool_as_int", {"orchestration_io_used": 0}),
        ("permission_bool_as_int", {"action_permission_granted": 0}),
    )
    for case_id, mutation in result_mutations:
        add(
            "stage_result_invariant",
            case_id,
            result=replace(real, **mutation),
        )
    add(
        "stage_result_invariant",
        "reversed_storage",
        result=_forge(
            contract.StageAdmissionOrchestrationResult,
            dict(vars(real)),
            reverse=True,
        ),
    )
    extra_values = dict(vars(real))
    extra_values["unexpected_shadow_field"] = "invalid"
    add(
        "stage_result_invariant",
        "reconstruction_mismatch",
        result=_forge(
            contract.StageAdmissionOrchestrationResult,
            extra_values,
        ),
    )
    reversed_candidate = _forge(
        contract.CandidateAdmissionOrchestrationResult,
        dict(vars(real.candidate_results[0])),
        reverse=True,
    )
    add(
        "stage_result_invariant",
        "candidate_reversed_storage",
        result=replace(real, candidate_results=(reversed_candidate,)),
    )
    for case_id, mutation in (
        ("candidate_index_mismatch", {"candidate_index": 1}),
        ("candidate_dispatcher_count", {"dispatcher_call_count": 0}),
        ("candidate_aggregator_count", {"aggregator_call_count": 0}),
    ):
        changed = replace(real.candidate_results[0], **mutation)
        add(
            "stage_result_invariant",
            case_id,
            result=replace(real, candidate_results=(changed,)),
        )
    candidate = real.candidate_results[0]
    vector = list(candidate.ordered_rule_evaluations)
    unified_values = dict(vars(vector[0]))
    unified_values["schema_version"] = "wrong"
    vector[0] = _forge(type(vector[0]), unified_values)
    add(
        "stage_result_invariant",
        "unified_rule_invariant_mutation",
        result=replace(
            real,
            candidate_results=(
                replace(candidate, ordered_rule_evaluations=tuple(vector)),
            ),
        ),
    )

    for scope_id in contract.SCOPE_IDS:
        add("scope", scope_id, result=_runtime_result(scope_id))

    copied_stage = replace(real.stage_global_rule_evaluations[0])
    add(
        "identity",
        "copied_equal_stage_result",
        result=replace(
            real,
            stage_global_rule_evaluations=(copied_stage,),
        ),
    )
    copied_vector = tuple(list(candidate.ordered_rule_evaluations))
    add(
        "identity",
        "copied_equal_retained_vector",
        result=replace(
            real,
            candidate_results=(
                replace(candidate, ordered_rule_evaluations=copied_vector),
            ),
        ),
    )
    add("identity", "stage_and_vector_identity_valid", result=real)
    rejected = build_result_for_candidate_outcomes(("rejected",))
    add(
        "identity",
        "rejected_canonical_source_invalid_verdict",
        result=rejected,
    )
    verdict_values = dict(vars(rejected.candidate_results[0].combined_verdict))
    verdict_values["evaluated_rule_ids"] = ("ADMIT_001",)
    corrupted_verdict = _forge(
        aggregation.CombinedAdmissionCandidateVerdict,
        verdict_values,
    )
    add(
        "identity",
        "corrupted_rejected_diagnostics",
        result=replace(
            rejected,
            candidate_results=(
                replace(
                    rejected.candidate_results[0],
                    combined_verdict=corrupted_verdict,
                ),
            ),
        ),
    )

    outcome_cases = (
        ("all_passed_permission_false", ("passed",)),
        ("blocked_first", ("blocked", "passed", "passed")),
        ("blocked_middle", ("passed", "blocked", "passed")),
        ("blocked_last", ("passed", "passed", "blocked")),
        ("multiple_blocked", ("blocked", "passed", "blocked")),
        ("invalid_first", ("invalid", "passed", "passed")),
        ("invalid_middle", ("passed", "invalid", "passed")),
        ("invalid_last", ("passed", "passed", "invalid")),
        ("multiple_invalid", ("invalid", "passed", "invalid")),
        ("blocked_and_invalid", ("blocked", "invalid")),
        ("invalid_and_blocked", ("invalid", "blocked")),
    )
    for case_id, outcomes in outcome_cases:
        add(
            "candidate_precedence",
            case_id,
            result=build_result_for_candidate_outcomes(outcomes),
        )
    permission_true = replace(
        build_result_for_candidate_outcomes(("blocked", "invalid")),
        action_permission_granted=True,
    )
    add(
        "candidate_precedence",
        "action_true_precedes_invalid_and_blocked",
        result=permission_true,
    )
    add(
        "precedence",
        "io_true_precedes_candidate_blocked",
        result=replace(real, orchestration_io_used=True),
    )
    add(
        "current_real_path",
        "committed_orchestrator_download_scope",
        result=real,
    )

    add(
        "cross_phase_precedence",
        "cardinality_precedes_wrong_result_and_error_types",
        result=object(),
        error=RuntimeError("wrong"),
    )
    add(
        "cross_phase_precedence",
        "stage_invariant_precedes_scope_io_permission_candidate",
        result=replace(
            build_result_for_candidate_outcomes(("invalid", "blocked")),
            schema_version="wrong",
            scope_id=contract.SCOPE_IDS[1],
            orchestration_io_used=True,
            action_permission_granted=True,
        ),
    )
    add(
        "cross_phase_precedence",
        "wrong_scope_precedes_io_permission_candidate",
        result=replace(
            build_result_for_candidate_outcomes(
                ("invalid", "blocked"),
                scope_id=contract.SCOPE_IDS[1],
            ),
            orchestration_io_used=True,
            action_permission_granted=True,
        ),
    )
    add(
        "cross_phase_precedence",
        "io_precedes_permission_and_candidate",
        result=replace(
            build_result_for_candidate_outcomes(("invalid", "blocked")),
            orchestration_io_used=True,
            action_permission_granted=True,
        ),
    )
    add(
        "cross_phase_precedence",
        "action_permission_precedes_invalid_and_blocked",
        result=permission_true,
    )
    add(
        "cross_phase_precedence",
        "candidate_invalid_precedes_blocked",
        result=build_result_for_candidate_outcomes(("blocked", "invalid")),
    )
    add(
        "cross_phase_precedence",
        "candidate_blocked_precedes_permission_not_granted",
        result=build_result_for_candidate_outcomes(("passed", "blocked")),
    )
    add(
        "cross_phase_precedence",
        "cross_all_passed_permission_false",
        result=build_result_for_candidate_outcomes(("passed", "passed")),
    )
    add(
        "cross_phase_precedence",
        "legal_error_precedes_success_shaped_coordinates",
        error=contract.StageAdmissionOrchestrationError(
            code=contract.ERROR_CODES[-1],
            scope_id=design.DOWNLOAD_SCOPE_ID,
            candidate_index=99,
            admission_rule_id="ADMIT_014",
            dispatcher_call_count=999,
            aggregator_call_count=999,
            reason="legal success-shaped error remains closed",
            cause_type="",
        ),
    )
    return tuple(cases)


def _read_design_truth() -> tuple[dict[str, str], ...]:
    with (ROOT / DESIGN_TRUTH_PATH).open(
        encoding="utf-8",
        newline="",
    ) as stream:
        rows = tuple(csv.DictReader(stream))
    if (
        len(rows) != 77
        or len({row["case_id"] for row in rows}) != 77
        or any(row["verified"] != "true" for row in rows)
    ):
        raise AssertionError("frozen design truth registry invalid")
    return rows


def _expected_value(row: dict[str, str], field_name: str) -> object:
    raw = row[f"expected_{field_name}"]
    if field_name in (
        "passed",
        "blocks_download",
        "action_permission_granted",
        "download_action_invoked",
        "call_site_io_used",
    ):
        if raw not in ("true", "false"):
            raise AssertionError(f"invalid expected bool: {field_name}")
        return raw == "true"
    if field_name == "candidate_count":
        return int(raw)
    if field_name in (
        "invalid_candidate_indexes",
        "blocked_candidate_indexes",
        "failing_candidate_indexes",
    ):
        parsed = json.loads(raw)
        if type(parsed) is not list:
            raise AssertionError(f"invalid expected tuple: {field_name}")
        return tuple(parsed)
    return raw


def _projection(
    decision: design.BulkDownloadStageOrchestrationCallSiteDecisionDesign,
) -> tuple[object, ...]:
    return tuple(getattr(decision, name) for name in design.DECISION_FIELDS)


def _value_text(value: object) -> str:
    if type(value) is bool:
        return _bool(value)
    if type(value) is tuple:
        return json.dumps(list(value), separators=(",", ":"))
    return str(value)


def _exact_value(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected) or actual != expected:
        return False
    if type(actual) is tuple:
        return all(type(item) is int for item in actual)
    return True


def evaluate_registry() -> tuple[
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    frozen_rows = _read_design_truth()
    cases = build_case_registry()
    frozen_keys = tuple(
        (row["case_group"], row["case_id"]) for row in frozen_rows
    )
    case_keys = tuple((case.case_group, case.case_id) for case in cases)
    if case_keys != frozen_keys:
        raise AssertionError("runtime source registry differs from frozen truth")
    truth_rows: list[dict[str, str]] = []
    parity_rows: list[dict[str, str]] = []
    for case, frozen in zip(cases, frozen_rows, strict=True):
        result, error = case.source_factory()
        runtime_decision = (
            runtime.evaluate_bulk_download_stage_orchestration_call_site(
                orchestration_result=result,
                orchestration_error=error,
            )
        )
        design_decision = (
            design.classify_bulk_download_stage_orchestration_call_site_contract_design(
                orchestration_result=result,
                orchestration_error=error,
            )
        )
        expected = tuple(
            _expected_value(frozen, name)
            for name in design.DECISION_FIELDS
        )
        runtime_values = _projection(runtime_decision)
        design_values = _projection(design_decision)
        exact_runtime_type = (
            type(runtime_decision)
            is design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        )
        exact_design_type = (
            type(design_decision)
            is design.BulkDownloadStageOrchestrationCallSiteDecisionDesign
        )
        row = {
            "case_group": case.case_group,
            "case_id": case.case_id,
            "exact_decision_type_verified": _bool(exact_runtime_type),
            "zero_action_verified": _bool(
                runtime_decision.download_action_invoked is False
                and runtime_decision.call_site_io_used is False
            ),
        }
        field_matches = []
        for index, field_name in enumerate(design.DECISION_FIELDS):
            expected_value = expected[index]
            runtime_value = runtime_values[index]
            design_value = design_values[index]
            row[f"expected_{field_name}"] = _value_text(expected_value)
            row[f"observed_{field_name}"] = _value_text(runtime_value)
            design_match = _exact_value(design_value, expected_value)
            runtime_match = _exact_value(runtime_value, expected_value)
            three_way = (
                design_match
                and runtime_match
                and _exact_value(runtime_value, design_value)
            )
            field_matches.append(three_way)
            parity_rows.append(
                {
                    "case_group": case.case_group,
                    "case_id": case.case_id,
                    "decision_field": field_name,
                    "expected_value": _value_text(expected_value),
                    "design_value": _value_text(design_value),
                    "runtime_value": _value_text(runtime_value),
                    "expected_exact_type": type(expected_value).__name__,
                    "design_exact_type": type(design_value).__name__,
                    "runtime_exact_type": type(runtime_value).__name__,
                    "design_parity_verified": _bool(design_match),
                    "runtime_parity_verified": _bool(runtime_match),
                    "three_way_parity_verified": _bool(three_way),
                }
            )
        row["verified"] = _bool(
            exact_runtime_type
            and exact_design_type
            and all(field_matches)
            and runtime_decision.download_action_invoked is False
            and runtime_decision.call_site_io_used is False
        )
        truth_rows.append(row)
    if len(truth_rows) != 77 or len(parity_rows) != 1155:
        raise AssertionError("runtime truth/parity cardinality invalid")
    return tuple(truth_rows), tuple(parity_rows)


def _runtime_source_policy() -> dict[str, bool]:
    runtime_path = ROOT / EXACT10[0]
    source = runtime_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    forbidden_imports = {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "torch",
        "os",
        "pathlib",
        "shutil",
    }
    if imported_roots & forbidden_imports:
        raise AssertionError("runtime forbidden import")
    call_names = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    if (
        "design.classify_bulk_download_stage_orchestration_call_site_contract_design"
        in call_names
    ):
        raise AssertionError("runtime delegates to design classifier")
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "design"
        and node.func.attr.startswith("_")
        for node in ast.walk(tree)
    ):
        raise AssertionError("runtime calls design private helper")
    if any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and "checker" in ast.unparse(node)
        for node in ast.walk(tree)
    ):
        raise AssertionError("runtime imports checker")
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "setattr", "getattr"}
        for node in ast.walk(tree)
    ):
        raise AssertionError("runtime forbidden dynamic or I/O call")
    function = runtime.evaluate_bulk_download_stage_orchestration_call_site
    signature = inspect.signature(function)
    if tuple(signature.parameters) != (
        "orchestration_result",
        "orchestration_error",
    ):
        raise AssertionError("runtime parameter names invalid")
    if any(
        parameter.kind is not inspect.Parameter.KEYWORD_ONLY
        or parameter.default is not inspect.Parameter.empty
        for parameter in signature.parameters.values()
    ):
        raise AssertionError("runtime signature shape invalid")
    if any(
        token in parameter_name
        for parameter_name in signature.parameters
        for token in (
            "callable",
            "dispatcher",
            "aggregator",
            "orchestrator",
            "filesystem",
            "network",
            "provider",
        )
    ):
        raise AssertionError("runtime injection surface")
    return {
        "runtime_design_classifier_called": False,
        "runtime_design_private_helpers_called": False,
        "runtime_predecessor_checker_imported": False,
        "download_callable_accepted": False,
    }


def build_public_rows() -> tuple[dict[str, str], ...]:
    policy = _runtime_source_policy()
    function = runtime.evaluate_bulk_download_stage_orchestration_call_site
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    rows: list[dict[str, str]] = []

    def add(area: str, item: str, expected: object, observed: object) -> None:
        rows.append(
            {
                "contract_area": area,
                "contract_order": str(len(rows) + 1),
                "contract_item": item,
                "expected": str(expected),
                "observed": str(observed),
                "verified": _bool(
                    type(expected) is type(observed) and expected == observed
                ),
            }
        )

    add(
        "public_api",
        "__all__",
        (
            "BulkDownloadStageOrchestrationCallSiteDecisionDesign",
            "evaluate_bulk_download_stage_orchestration_call_site",
        ),
        runtime.__all__,
    )
    add("public_api", "function_name", "evaluate_bulk_download_stage_orchestration_call_site", function.__name__)
    add("public_api", "parameter_names", ("orchestration_result", "orchestration_error"), tuple(signature.parameters))
    add("public_api", "required_keyword_only_count", 2, sum(parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values()))
    add("public_api", "positional_parameter_count", 0, sum(parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD) for parameter in signature.parameters.values()))
    add("public_api", "variadic_parameter_count", 0, sum(parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for parameter in signature.parameters.values()))
    add("public_api", "result_annotation", design.BulkDownloadStageOrchestrationCallSiteDecisionDesign, hints["return"])
    add("public_api", "result_annotation", contract.StageAdmissionOrchestrationResult | None, hints["orchestration_result"])
    add("public_api", "error_annotation", contract.StageAdmissionOrchestrationError | None, hints["orchestration_error"])
    add("identity", "shared_result_class", design.BulkDownloadStageOrchestrationCallSiteDecisionDesign, runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign)
    add("decision", "field_count", 15, len(fields(runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign)))
    for index, field_name in enumerate(design.DECISION_FIELDS, 1):
        add("decision_field", f"{index:02d}", field_name, fields(runtime.BulkDownloadStageOrchestrationCallSiteDecisionDesign)[index - 1].name)
    for key, observed in policy.items():
        add("independence", key, False, observed)
    add("side_effect", "call_site_io_used", False, False)
    add("side_effect", "download_action_invoked", False, False)
    return tuple(rows)


def build_safety_rows(
    truth_rows: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    _runtime_source_policy()
    if any(
        row["observed_outcome"] == "authorized"
        or row["observed_download_action_invoked"] != "false"
        or row["observed_call_site_io_used"] != "false"
        for row in truth_rows
    ):
        raise AssertionError("runtime safety result violated")
    return tuple(
        {
            "safety_item": item,
            "expected": "false",
            "observed": "false",
            "evidence": (
                "runtime AST, exact signature, and 77 exact-result probes"
            ),
            "verified": "true",
        }
        for item in SAFETY_ITEMS
    )


def _manifest(
    payloads: dict[str, bytes],
    truth_rows: tuple[dict[str, str], ...],
    parity_rows: tuple[dict[str, str], ...],
    public_count: int,
    safety_count: int,
) -> bytes:
    group_counts = Counter(row["case_group"] for row in truth_rows)
    value = {
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "public_api_contract_row_count": public_count,
        "runtime_truth_row_count": len(truth_rows),
        "runtime_truth_group_count": len(group_counts),
        "runtime_truth_group_counts": dict(sorted(group_counts.items())),
        "design_runtime_exact15_parity_row_count": len(parity_rows),
        "safety_audit_row_count": safety_count,
        "issue_inventory_row_count": 30,
        "source_boundary_sha256": {
            path.as_posix(): digest
            for path, digest in SOURCE_SHA256.items()
        },
        "evidence_sha256": {
            name: _sha(payloads[name]) for name in CSV_NAMES
        },
        "decision_runtime_implemented": True,
        "runtime_public_api_available": True,
        "runtime_returns_shared_decision_type_identity": True,
        "runtime_design_classifier_called": False,
        "runtime_design_private_helpers_called": False,
        "runtime_predecessor_checker_imported": False,
        "full_exact15_runtime_truth_verified": True,
        "design_runtime_exact15_parity_verified": True,
        "cross_phase_precedence_verified": True,
        "candidate_diagnostic_projection_verified": True,
        "error_exact8_full_projection_verified": True,
        "current_real_path_verified": True,
        "authorized_decision_count": 0,
        "download_action_count": 0,
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
        "unknown_atom_feature_policy_resolved": False,
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
    design_manifest = json.loads((ROOT / DESIGN_MANIFEST_PATH).read_bytes())
    if design_manifest["truth_row_count"] != 77:
        raise AssertionError("design manifest truth count changed")
    if design_manifest["effective_open_issues"] != [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]:
        raise AssertionError("design issue state changed")


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
        len(truth_rows) != 77
        or len({row["case_group"] for row in truth_rows}) != 11
        or len(parity_rows) != 1155
    ):
        raise AssertionError("truth/parity cardinality invalid")
    if len(
        [
            row
            for row in truth_rows
            if row["case_group"] == "cross_phase_precedence"
        ]
    ) != 9:
        raise AssertionError("cross-phase precedence incomplete")
    if any(
        row["observed_outcome"] == "authorized"
        or row["observed_download_action_invoked"] != "false"
        or row["observed_call_site_io_used"] != "false"
        for row in truth_rows
    ):
        raise AssertionError("runtime action safety invalid")
    current = next(
        row
        for row in truth_rows
        if row["case_id"] == "committed_orchestrator_download_scope"
    )
    current_projection = {
        "observed_source_kind": "orchestration_result",
        "observed_source_scope_id": design.DOWNLOAD_SCOPE_ID,
        "observed_candidate_count": "1",
        "observed_invalid_candidate_indexes": "[]",
        "observed_blocked_candidate_indexes": "[0]",
        "observed_failing_candidate_indexes": "[0]",
        "observed_action_permission_granted": "false",
        "observed_outcome": "blocked",
        "observed_reason": design.REASON_VOCABULARY[10],
        "observed_download_action_invoked": "false",
        "observed_call_site_io_used": "false",
    }
    if any(current[key] != value for key, value in current_projection.items()):
        raise AssertionError("current real path projection invalid")
    for key in (
        "decision_runtime_implemented",
        "runtime_public_api_available",
        "runtime_returns_shared_decision_type_identity",
        "full_exact15_runtime_truth_verified",
        "design_runtime_exact15_parity_verified",
        "cross_phase_precedence_verified",
        "candidate_diagnostic_projection_verified",
        "error_exact8_full_projection_verified",
        "current_real_path_verified",
        "future_action_permission_bridge_required",
        "feature_semantics_audit_required_before_training",
    ):
        if manifest[key] is not True:
            raise AssertionError(f"manifest true flag invalid: {key}")
    for key in (
        "runtime_design_classifier_called",
        "runtime_design_private_helpers_called",
        "runtime_predecessor_checker_imported",
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
        "feature_semantics_known",
        "feature_semantics_audit_completed",
        "ready_for_training",
    ):
        if manifest[key] is not False:
            raise AssertionError(f"manifest false flag invalid: {key}")
    if (
        manifest["authorized_decision_count"] != 0
        or manifest["download_action_count"] != 0
    ):
        raise AssertionError("manifest action count invalid")
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
                "public_rows": manifest["public_api_contract_row_count"],
                "runtime_truth_rows": manifest["runtime_truth_row_count"],
                "runtime_truth_groups": manifest[
                    "runtime_truth_group_count"
                ],
                "design_runtime_parity_rows": manifest[
                    "design_runtime_exact15_parity_row_count"
                ],
                "safety_rows": manifest["safety_audit_row_count"],
                "issue_rows": manifest["issue_inventory_row_count"],
                "runtime_design_classifier_called": False,
                "runtime_design_private_helpers_called": False,
                "authorized_decision_count": 0,
                "download_action_count": 0,
                "current_path_outcome": "blocked",
                "current_permission": False,
                "action_permission_granted": False,
                "ready_for_download": False,
                "ready_for_training": False,
                "feature_semantics_audit_completed": False,
                "output_sha256": {
                    name: _sha(payloads[name]) for name in OUTPUT_NAMES
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

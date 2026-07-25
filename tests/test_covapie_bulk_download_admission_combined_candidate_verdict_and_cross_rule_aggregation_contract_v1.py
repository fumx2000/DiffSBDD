"""Targeted tests for the design-only combined-verdict aggregation contract."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_design_gate
    as gate,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004
    as runtime_type_owner,
)


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / gate.DEFAULT_OUTPUT_ROOT


def _load_checker():
    path = (
        ROOT
        / "scripts/check_covapie_bulk_download_admission_combined_candidate_"
        "verdict_and_cross_rule_aggregation_contract_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "combined_aggregation_checker_for_tests", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _pass(scope: str):
    return gate._all_pass(scope)


def _replace(vector: tuple[object, ...], index: int, value: object):
    return tuple(
        value if position == index else item
        for position, item in enumerate(vector)
    )


def _mutate(value, **changes: object):
    payload = dict(vars(value))
    payload.update(changes)
    return gate.UnifiedAdmissionRuleEvaluationContractDesign(**payload)


def _classify(scope: object, vector: object):
    return gate.classify_combined_candidate_verdict_contract_design(
        scope, ordered_rule_evaluations=vector
    )


def _actual_runtime_evaluation(
    outcome: str = "passed",
    **changes: object,
):
    payload = {
        "schema_version": gate.INPUT_RESULT_SCHEMA_VERSION,
        "admission_rule_id": "ADMIT_001",
        "admission_rule_name": gate.RULE_NAMES["ADMIT_001"],
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": "" if outcome == "passed" else f"ACTUAL_{outcome.upper()}",
        "normalized_values": (),
        "validated_candidate_fields": (),
        "consumed_candidate_fields": (),
        "consumed_context_items": (),
        "evaluator_io_used": False,
        "adapter_id": gate.ADAPTER_IDS["ADMIT_001"],
    }
    payload.update(changes)
    return runtime_type_owner.UnifiedAdmissionRuleEvaluation(**payload)


def _mirror_actual_runtime(value):
    return gate.UnifiedAdmissionRuleEvaluationContractDesign(**vars(value))


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def test_future_public_api_is_frozen_but_not_implemented() -> None:
    assert gate.FUTURE_FUNCTION_NAME == "aggregate_admission_rule_evaluations"
    assert gate.FUTURE_API_SIGNATURE == (
        "aggregate_admission_rule_evaluations(scope_id: str, *, "
        "ordered_rule_evaluations: tuple[UnifiedAdmissionRuleEvaluation, ...]) "
        "-> CombinedAdmissionCandidateVerdict"
    )
    assert not hasattr(gate, gate.FUTURE_FUNCTION_NAME)
    rows = _csv(DERIVED / gate.PUBLIC_API_FILENAME)
    frozen = {row["contract_item"]: row["frozen_value"] for row in rows}
    assert len(rows) == 24
    assert frozen["scope_id_parameter_kind"] == "positional_or_keyword"
    assert frozen["ordered_vector_parameter_kind"] == "keyword_only"
    assert frozen["parameter_defaults"] == "none"
    assert frozen["var_positional"] == "forbidden"
    assert frozen["var_keyword"] == "forbidden"
    assert frozen["candidate_parameter"] == "forbidden"
    assert frozen["context_parameters"] == "forbidden"
    assert frozen["dispatcher_injection"] == "forbidden"
    assert frozen["registry_injection"] == "forbidden"
    assert frozen["runtime_outcome_vocabulary"] == (
        "passed|blocked|invalid|rejected"
    )
    assert frozen["aggregation_admissible_child_outcomes"] == (
        "passed|blocked|invalid"
    )
    assert frozen["runtime_nested_duplicate_policy"] == (
        "permitted_by_exact_shape_contract_and_not_interpreted_by_aggregator"
    )


def test_design_oracle_exact_signature_and_boundary() -> None:
    signature = inspect.signature(
        gate.classify_combined_candidate_verdict_contract_design
    )
    assert tuple(signature.parameters) == (
        "scope_id",
        "ordered_rule_evaluations",
    )
    assert (
        signature.parameters["scope_id"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    assert (
        signature.parameters["ordered_rule_evaluations"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )


def test_input_mirror_exact13_matches_runtime_contract() -> None:
    mirror = gate.UnifiedAdmissionRuleEvaluationContractDesign
    assert tuple(field.name for field in fields(mirror)) == gate.INPUT_RESULT_FIELDS
    actual = runtime_type_owner.UnifiedAdmissionRuleEvaluation
    assert runtime.UnifiedAdmissionRuleEvaluation is actual
    assert actual.__module__.endswith(
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004"
    )
    assert tuple(field.name for field in fields(actual)) == gate.INPUT_RESULT_FIELDS
    assert tuple(get_type_hints(actual).items()) == (
        ("schema_version", str),
        ("admission_rule_id", str),
        ("admission_rule_name", str),
        ("outcome", str),
        ("passed", bool),
        ("blocks_candidate", bool),
        ("reason", str),
        ("normalized_values", tuple[tuple[str, str], ...]),
        ("validated_candidate_fields", tuple[tuple[str, str], ...]),
        ("consumed_candidate_fields", tuple[str, ...]),
        ("consumed_context_items", tuple[str, ...]),
        ("evaluator_io_used", bool),
        ("adapter_id", str),
    )
    assert runtime_type_owner.RESULT_FIELDS == gate.INPUT_RESULT_FIELDS
    assert runtime_type_owner.RESULT_SCHEMA_VERSION == gate.INPUT_RESULT_SCHEMA_VERSION
    assert runtime_type_owner.OUTCOME_VOCABULARY == (
        "passed",
        "blocked",
        "invalid",
        "rejected",
    )
    assert mirror is not runtime.UnifiedAdmissionRuleEvaluation
    runtime_manifest = json.loads(
        (
            ROOT
            / "data/derived/covalent_small/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
            "admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json"
        ).read_bytes()
    )
    assert runtime_manifest["result_fields"] == list(gate.INPUT_RESULT_FIELDS)
    assert runtime_manifest["result_schema_version"] == gate.INPUT_RESULT_SCHEMA_VERSION
    assert runtime_manifest["outcome_vocabulary"] == list(
        gate.RUNTIME_OUTCOME_VOCABULARY
    )
    assert runtime_manifest["rule_names"] == gate.RULE_NAMES
    assert runtime_manifest["adapter_ids"] == gate.ADAPTER_IDS
    current_manifest = json.loads(
        (DERIVED / gate.MANIFEST_FILENAME).read_bytes()
    )
    contract = current_manifest["input_single_rule_result_contract"]
    assert contract["runtime_owner"] == (
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004"
    )
    assert contract["runtime_outcomes"] == [
        "passed",
        "blocked",
        "invalid",
        "rejected",
    ]
    assert contract["aggregation_admissible_outcomes"] == [
        "passed",
        "blocked",
        "invalid",
    ]
    assert contract["runtime_nested_duplicates_rejected"] is False
    assert contract["aggregator_interprets_nested_payloads"] is False
    assert contract["rejected_is_runtime_valid"] is True
    assert contract["rejected_is_aggregation_admissible"] is False


def test_future_result_mirror_exact13_types_order_reconstruction_and_frozen() -> None:
    vector = _pass(gate.SCOPE_IDS[0])
    result = _classify(gate.SCOPE_IDS[0], vector)
    assert tuple(field.name for field in fields(type(result))) == gate.FUTURE_RESULT_FIELDS
    assert tuple(vars(result)) == gate.FUTURE_RESULT_FIELDS
    assert tuple(type(value) for value in vars(result).values()) == (
        str,
        str,
        str,
        bool,
        bool,
        str,
        tuple,
        tuple,
        tuple,
        tuple,
        tuple,
        tuple,
        bool,
    )
    assert type(result)(**vars(result)) == result
    with pytest.raises(Exception):
        result.outcome = "blocked"


def test_exact4_scope_membership_order() -> None:
    assert gate.SCOPE_IDS == (
        "download_execution_permission",
        "post_download_acceptance_permission",
        "pre_final_split_acceptance_permission",
        "training_execution_admission_permission",
    )
    assert tuple(len(gate.REQUIRED_RULE_IDS[item]) for item in gate.SCOPE_IDS) == (
        11,
        13,
        14,
        15,
    )
    assert gate.REQUIRED_RULE_IDS[gate.SCOPE_IDS[3]] == gate.RULE_IDS


def test_exact6_reason_vocabulary_and_validation_precedence() -> None:
    assert gate.REASON_VOCABULARY == (
        "COMBINED_ADMISSION_SCOPE_ID_INVALID",
        "COMBINED_ADMISSION_RULE_EVALUATION_VECTOR_TYPE_INVALID",
        "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID",
        "COMBINED_ADMISSION_RULE_MEMBERSHIP_INVALID",
        "COMBINED_ADMISSION_REQUIRED_RULE_INVALID",
        "COMBINED_ADMISSION_REQUIRED_RULE_BLOCKED",
    )
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    assert manifest["validation_precedence"] == [
        "scope_id",
        "ordered_vector_exact_tuple",
        "all_child_runtime_exact13_structure",
        "all_child_aggregation_identity_and_outcome_admissibility",
        "full_exact_membership",
        "all_child_invalid_outcomes",
        "all_child_blocked_outcomes",
        "all_child_passed",
    ]
    assert manifest["fail_closed_precedence"] == [
        "invalid",
        "blocked",
        "passed",
    ]


@pytest.mark.parametrize("scope", ("unknown", True, None))
def test_scope_invalid_projection(scope: object) -> None:
    result = _classify(scope, [])
    assert result == gate.CombinedAdmissionCandidateVerdictContractDesign(
        gate.FUTURE_RESULT_SCHEMA_VERSION,
        scope if type(scope) is str else "",
        "invalid",
        False,
        True,
        gate.SCOPE_ID_INVALID_REASON,
        (),
        (),
        (),
        (),
        (),
        (),
        False,
    )


@pytest.mark.parametrize("vector", ([], {}, "value", None))
def test_vector_type_invalid_projection(vector: object) -> None:
    scope = gate.SCOPE_IDS[0]
    result = _classify(scope, vector)
    assert result.reason == gate.VECTOR_TYPE_INVALID_REASON
    assert result.required_rule_ids == gate.REQUIRED_RULE_IDS[scope]
    assert result.evaluated_rule_ids == ()
    assert result.rule_evaluations == ()
    assert result.invalid_rule_ids == result.blocked_rule_ids == result.failing_rule_ids == ()


@pytest.mark.parametrize(
    "invalid_child",
    (
        object(),
        "child",
        None,
    ),
)
def test_element_invariant_invalid_discards_all_input_objects(
    invalid_child: object,
) -> None:
    scope = gate.SCOPE_IDS[0]
    vector = _replace(_pass(scope), 0, invalid_child)
    result = _classify(scope, vector)
    assert result.reason == gate.EVALUATION_INVARIANT_INVALID_REASON
    assert result.evaluated_rule_ids == ()
    assert result.rule_evaluations == ()
    assert result.invalid_rule_ids == result.blocked_rule_ids == result.failing_rule_ids == ()
    assert invalid_child not in result.rule_evaluations


class ChildSubclass(gate.UnifiedAdmissionRuleEvaluationContractDesign):
    pass


def test_child_subclass_is_rejected() -> None:
    scope = gate.SCOPE_IDS[0]
    base = _pass(scope)[0]
    result = _classify(
        scope,
        _replace(_pass(scope), 0, ChildSubclass(**vars(base))),
    )
    assert result.reason == gate.EVALUATION_INVARIANT_INVALID_REASON


BLOCKED_CASES = tuple(
    (scope, index, rule)
    for scope in gate.SCOPE_IDS
    for index, rule in enumerate(gate.REQUIRED_RULE_IDS[scope])
)


@pytest.mark.parametrize(("scope", "index", "rule"), BLOCKED_CASES)
def test_every_required_rule_blocked(scope: str, index: int, rule: str) -> None:
    vector = _replace(_pass(scope), index, gate._evaluation(rule, "blocked"))
    result = _classify(scope, vector)
    assert result.outcome == "blocked"
    assert result.reason == gate.REQUIRED_RULE_BLOCKED_REASON
    assert result.invalid_rule_ids == ()
    assert result.blocked_rule_ids == (rule,)
    assert result.failing_rule_ids == (rule,)
    assert result.rule_evaluations is vector


@pytest.mark.parametrize(("scope", "index", "rule"), BLOCKED_CASES)
def test_every_required_rule_invalid(scope: str, index: int, rule: str) -> None:
    vector = _replace(_pass(scope), index, gate._evaluation(rule, "invalid"))
    result = _classify(scope, vector)
    assert result.outcome == "invalid"
    assert result.reason == gate.REQUIRED_RULE_INVALID_REASON
    assert result.invalid_rule_ids == (rule,)
    assert result.blocked_rule_ids == ()
    assert result.failing_rule_ids == (rule,)
    assert result.rule_evaluations is vector


@pytest.mark.parametrize("scope", gate.SCOPE_IDS)
def test_full_vector_invalid_blocked_and_failing_projections(scope: str) -> None:
    required = gate.REQUIRED_RULE_IDS[scope]
    vector = _replace(
        _pass(scope), 0, gate._evaluation(required[0], "blocked")
    )
    vector = _replace(
        vector, 1, gate._evaluation(required[1], "invalid")
    )
    vector = _replace(
        vector, len(vector) - 1, gate._evaluation(required[-1], "blocked")
    )
    result = _classify(scope, vector)
    assert result.outcome == "invalid"
    assert result.invalid_rule_ids == (required[1],)
    assert result.blocked_rule_ids == (required[0], required[-1])
    assert result.failing_rule_ids == (
        required[0],
        required[1],
        required[-1],
    )
    assert result.rule_evaluations is vector


@pytest.mark.parametrize("scope", gate.SCOPE_IDS)
def test_all_invalid_and_all_blocked_are_fully_collected(scope: str) -> None:
    required = gate.REQUIRED_RULE_IDS[scope]
    invalid = tuple(gate._evaluation(rule, "invalid") for rule in required)
    blocked = tuple(gate._evaluation(rule, "blocked") for rule in required)
    invalid_result = _classify(scope, invalid)
    blocked_result = _classify(scope, blocked)
    assert invalid_result.invalid_rule_ids == required
    assert invalid_result.failing_rule_ids == required
    assert blocked_result.blocked_rule_ids == required
    assert blocked_result.failing_rule_ids == required


@pytest.mark.parametrize("scope", gate.SCOPE_IDS)
@pytest.mark.parametrize("position", ("first", "middle", "last"))
def test_missing_first_middle_last_is_membership_invalid(
    scope: str, position: str
) -> None:
    vector = _pass(scope)
    index = {
        "first": 0,
        "middle": len(vector) // 2,
        "last": len(vector) - 1,
    }[position]
    result = _classify(scope, vector[:index] + vector[index + 1 :])
    assert result.reason == gate.MEMBERSHIP_INVALID_REASON
    assert result.evaluated_rule_ids != result.required_rule_ids
    assert result.rule_evaluations == ()


@pytest.mark.parametrize("scope", gate.SCOPE_IDS)
def test_extra_duplicate_reorder_unknown_and_external_substitution(scope: str) -> None:
    canonical = _pass(scope)
    external = (
        "ADMIT_010"
        if "ADMIT_010" not in gate.REQUIRED_RULE_IDS[scope]
        else (
            "ADMIT_015"
            if "ADMIT_015" not in gate.REQUIRED_RULE_IDS[scope]
            else "ADMIT_999"
        )
    )
    vectors = (
        canonical + (gate._evaluation(external),),
        canonical + (canonical[0],),
        (canonical[1], canonical[0]) + canonical[2:],
        canonical[:-1] + (gate._evaluation("ADMIT_999"),),
        canonical[:-1] + (gate._evaluation(external),),
    )
    for vector in vectors:
        result = _classify(scope, vector)
        assert result.reason == gate.MEMBERSHIP_INVALID_REASON
        assert result.evaluated_rule_ids == tuple(
            item.admission_rule_id for item in vector
        )
        assert result.rule_evaluations == ()


FIELD_TYPE_MUTATIONS = (
    ("schema_version", 7),
    ("admission_rule_id", 7),
    ("admission_rule_name", 7),
    ("outcome", 7),
    ("passed", 0),
    ("blocks_candidate", 0),
    ("reason", 7),
    ("normalized_values", []),
    ("validated_candidate_fields", []),
    ("consumed_candidate_fields", []),
    ("consumed_context_items", []),
    ("evaluator_io_used", True),
    ("adapter_id", 7),
)


@pytest.mark.parametrize(("field_name", "replacement"), FIELD_TYPE_MUTATIONS)
def test_every_exact13_field_type_mutation_fails_closed(
    field_name: str, replacement: object
) -> None:
    scope = gate.SCOPE_IDS[0]
    vector = _replace(
        _pass(scope),
        0,
        _mutate(_pass(scope)[0], **{field_name: replacement}),
    )
    assert _classify(scope, vector).reason == gate.EVALUATION_INVARIANT_INVALID_REASON


LOGICAL_MUTATIONS = (
    {"schema_version": "v2"},
    {"admission_rule_name": "wrong"},
    {"adapter_id": "wrong"},
    {"outcome": "unknown_outcome", "passed": False, "blocks_candidate": True, "reason": "x"},
    {"passed": False},
    {"blocks_candidate": True},
    {"reason": "nonempty"},
    {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": ""},
    {"normalized_values": (("a",),)},
    {"validated_candidate_fields": (("a",),)},
)


@pytest.mark.parametrize("changes", LOGICAL_MUTATIONS)
def test_schema_name_adapter_outcome_reason_and_nested_drift(
    changes: dict[str, object],
) -> None:
    scope = gate.SCOPE_IDS[0]
    vector = _replace(_pass(scope), 0, _mutate(_pass(scope)[0], **changes))
    assert _classify(scope, vector).reason == gate.EVALUATION_INVARIANT_INVALID_REASON


def test_actual_runtime_rejected_is_structurally_valid_but_aggregation_inadmissible() -> None:
    actual = _actual_runtime_evaluation("rejected")
    assert type(actual) is runtime_type_owner.UnifiedAdmissionRuleEvaluation
    assert actual.outcome == "rejected"
    mirror = _mirror_actual_runtime(actual)
    assert gate._runtime_structure_valid(mirror) is True
    assert gate._aggregation_identity_and_outcome_admissible(mirror) is False
    scope = gate.SCOPE_IDS[0]
    vector = _replace(_pass(scope), 0, mirror)
    result = _classify(scope, vector)
    assert result.reason == gate.EVALUATION_INVARIANT_INVALID_REASON
    assert result.evaluated_rule_ids == ()
    assert result.rule_evaluations == ()


@pytest.mark.parametrize(
    ("field_name", "duplicate_value"),
    (
        ("normalized_values", (("a", "1"), ("a", "2"))),
        ("validated_candidate_fields", (("a", "1"), ("a", "2"))),
        ("consumed_candidate_fields", ("a", "a")),
        ("consumed_context_items", ("a", "a")),
    ),
)
def test_actual_runtime_duplicate_nested_payload_is_shape_valid_and_passes_aggregation(
    field_name: str,
    duplicate_value: tuple[object, ...],
) -> None:
    actual = _actual_runtime_evaluation(**{field_name: duplicate_value})
    assert getattr(actual, field_name) == duplicate_value
    mirror = _mirror_actual_runtime(actual)
    assert gate._runtime_structure_valid(mirror) is True
    assert gate._aggregation_identity_and_outcome_admissible(mirror) is True
    scope = gate.SCOPE_IDS[0]
    vector = _replace(_pass(scope), 0, mirror)
    result = _classify(scope, vector)
    assert result.outcome == "passed"
    assert result.reason == ""
    assert result.rule_evaluations is vector


def test_actual_runtime_rejects_unknown_outcome_string() -> None:
    with pytest.raises(ValueError, match="outcome invalid"):
        _actual_runtime_evaluation(
            "unknown_outcome",
            passed=False,
            blocks_candidate=True,
            reason="ACTUAL_UNKNOWN_OUTCOME",
        )
    mirror = _mutate(
        _pass(gate.SCOPE_IDS[0])[0],
        outcome="unknown_outcome",
        passed=False,
        blocks_candidate=True,
        reason="MIRROR_UNKNOWN_OUTCOME",
    )
    assert gate._runtime_structure_valid(mirror) is False


def test_valid_vector_identity_and_all_pass_projection() -> None:
    for scope in gate.SCOPE_IDS:
        vector = _pass(scope)
        result = _classify(scope, vector)
        assert result.rule_evaluations is vector
        assert result.required_rule_ids == result.evaluated_rule_ids
        assert result.outcome == "passed"
        assert result.passed is True
        assert result.blocks_scope_action is False
        assert result.reason == ""
        assert result.invalid_rule_ids == result.blocked_rule_ids == result.failing_rule_ids == ()


def test_no_dispatcher_handler_io_permission_or_execution_mutation() -> None:
    before = (
        gate.DISPATCHER_CALL_COUNT,
        gate.SINGLE_RULE_HANDLER_CALL_COUNT,
        gate.CURRENT_PERMISSION,
        gate.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
    )
    _classify(gate.SCOPE_IDS[3], _pass(gate.SCOPE_IDS[3]))
    assert before == (0, 0, False, 0)
    assert (
        gate.DISPATCHER_CALL_COUNT,
        gate.SINGLE_RULE_HANDLER_CALL_COUNT,
        gate.CURRENT_PERMISSION,
        gate.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
    ) == before


def test_pre36_issue_and_readiness_continuity() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    pre = manifest["precondition_continuity"]
    assert (
        pre["complete_count"],
        pre["supported_but_not_frozen_count"],
        pre["incomplete_count"],
        pre["implementation_blocking_count"],
    ) == (42, 0, 3, 3)
    assert pre["remaining_open_precondition_ids"] == [
        "PRE_036",
        "PRE_038",
        "PRE_042",
    ]
    assert pre["pre_036_required_state"] == "implemented only after contract"
    assert pre["pre_036_remains_open_because_aggregator_not_implemented"] is True
    readiness = manifest["readiness"]
    assert all(readiness[key] is True for key in gate.TRUE_READINESS)
    assert all(readiness[key] is False for key in gate.FALSE_READINESS)


def test_issue_inventory_exact30_byte_identical_zero_transition() -> None:
    source = (
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/covapie_combined_permission_issue_readiness_inventory.csv"
    )
    output = DERIVED / gate.ISSUE_FILENAME
    assert source.read_bytes() == output.read_bytes()
    rows = _csv(output)
    assert len(rows) == 30
    assert {
        row["issue_id"]
        for row in rows
        if row["successor_effective_status"] == "open"
    } == {
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    }


def test_b3_and_feature_semantics_warning_remain() -> None:
    assert gate.CANONICAL_MASKS[3] == ("scaffold_only", "B3")
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    assert manifest["canonical_mask_count"] == 5
    assert "Step12D was only a smoke legality check" in manifest["feature_semantics_warning"]
    assert manifest["readiness"]["feature_semantics_audit_completed"] is False
    assert manifest["readiness"]["ready_for_training"] is False


def test_truth_matrix_201_rows_23_groups_and_all_pass() -> None:
    rows = _csv(DERIVED / gate.TRUTH_FILENAME)
    assert len(rows) == len(gate._truth_cases()) == 201
    assert len({row["case_group"] for row in rows}) == 23
    assert all(row["case_passed"] == "true" for row in rows)
    assert {row["case_group"] for row in rows} >= {
        "canonical_all_pass",
        "every_required_rule_blocked",
        "every_required_rule_invalid",
        "multi_invalid_full_collection",
        "multi_blocked_full_collection",
        "invalid_blocked_full_collection",
        "identity_preservation",
        "runtime_valid_rejected_aggregation_inadmissible",
        "runtime_valid_duplicate_nested_compatibility",
    }
    by_id = {row["case_id"]: row for row in rows}
    assert by_id[
        "runtime_rejected_outcome_is_aggregation_inadmissible"
    ]["observed_reason"] == gate.EVALUATION_INVARIANT_INVALID_REASON
    for case_id in (
        "duplicate_normalized_keys",
        "duplicate_validated_fields",
        "duplicate_consumed_candidate_fields",
        "duplicate_consumed_context_items",
    ):
        assert by_id[case_id]["observed_outcome"] == "passed"
        assert by_id[case_id]["input_tuple_identity_retained"] == "true"


def test_safety_exact30_and_all_pass() -> None:
    rows = _csv(DERIVED / gate.SAFETY_FILENAME)
    assert len(rows) == 30
    assert all(row["safety_passed"] == "true" for row in rows)
    states = {row["audit_item"]: row["observed_state"] for row in rows}
    assert states["dispatcher_calls"] == "0"
    assert states["single_rule_handler_calls"] == "0"
    assert states["aggregator_implementation"] == "false"
    assert states["combined_verdict_implementation"] == "false"
    assert states["ready_for_training"] == "false"


def test_source_snapshot_exact12_and_sha_truth() -> None:
    snapshot = gate.build_frozen_source_snapshot(ROOT)
    assert len(snapshot) == 12
    assert tuple(item.relative_path for item in snapshot) == gate.SOURCE_PATHS
    assert snapshot[7].relative_path == Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_minimal_unified_dispatch_shell_"
        "with_admit_004.py"
    )
    assert all(
        item.base_tree_mode == item.index_mode == "100644"
        and item.index_stage == 0
        and hashlib.sha256(item.content).hexdigest() == item.expected_sha256
        for item in snapshot
    )


def test_manifest_hash_truth_no_self_hash_and_exact10() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    assert manifest["manifest_self_sha256_recorded"] is False
    assert manifest["exact10_file_count"] == 10
    assert manifest["stage_owned_staging_namespace_closure"] == {
        "materializer_staging_name_prefix": gate.STAGING_NAME_PREFIX,
        "staging_prefix_belongs_to_current_stage": True,
        "empty_retained_staging_detected_by_recursive_lifecycle": True,
        "partial_retained_staging_detected": True,
        "legacy_misnamed_staging_prefix": (
            ".combined-permission-semantics-stage-"
        ),
        "legacy_misnamed_empty_staging_rejected": True,
        "git_empty_directory_visibility_not_relied_upon": True,
        "business_semantics_changed": False,
    }
    assert manifest["embedded_stage_residue_lifecycle_closure"] == {
        "four_bounded_support_roots": [
            "src/covalent_ext",
            "scripts",
            "tests",
            "docs",
        ],
        "support_root_stage_match_policy": (
            "complete_stage_token_at_any_basename_position"
        ),
        "embedded_stage_file_residue_rejected": True,
        "embedded_stage_directory_residue_rejected": True,
        "matched_directory_descendants_observed": True,
        "git_ignored_same_stage_residue_rejected": True,
        "git_untracked_inventory_not_relied_upon": True,
        "unrelated_ignored_regular_file_outside_stage_family_allowed": True,
        "derived_parent_prefix_policy_unchanged": True,
        "business_semantics_changed": False,
    }
    for path, digest in manifest["derived_output_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    for path, digest in manifest["support_file_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_production_checker_and_disk_exact_equality() -> None:
    checker = _load_checker()
    expected = checker._local_expected(checker._source_snapshot())
    actual = gate.build_artifacts(
        gate.build_frozen_source_snapshot(ROOT), repo_root=ROOT
    )
    observed = checker.read_exact6_no_follow()
    checker._verify_observed_artifacts(actual, expected)
    checker._verify_observed_artifacts(observed, expected)
    assert actual == expected == observed


def test_duplicate_json_key_rejected() -> None:
    with pytest.raises(ValueError, match="unique keys"):
        gate._json(b'{"a":1,"a":2}')


def test_synchronized_csv_and_manifest_tamper_rejected() -> None:
    checker = _load_checker()
    expected = checker._local_expected(checker._source_snapshot())
    tampered = dict(expected)
    name = checker.PUBLIC_API_NAME
    tampered[name] = expected[name].replace(b"keyword_only", b"positional", 1)
    manifest = json.loads(tampered[checker.MANIFEST_NAME])
    manifest["derived_output_sha256"][
        (checker.DERIVED_ROOT / name).as_posix()
    ] = hashlib.sha256(tampered[name]).hexdigest()
    tampered[checker.MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    with pytest.raises(ValueError, match="reconstruction mismatch"):
        checker._verify_observed_artifacts(tampered, expected)


def test_source_tamper_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._pinned_read
    target = gate.SOURCE_PATHS[0]

    def tampered(root: Path, relative: Path, **kwargs: object) -> bytes:
        content = original(root, relative, **kwargs)
        return content + b"x" if relative == target else content

    monkeypatch.setattr(gate, "_pinned_read", tampered)
    with pytest.raises(ValueError, match="source bytes/SHA drift"):
        gate.build_frozen_source_snapshot(ROOT)


def test_source_reader_rejects_leaf_replacement(
    tmp_path: Path,
) -> None:
    (tmp_path / "parent").mkdir()
    leaf = tmp_path / "parent/leaf"
    leaf.write_bytes(b"same")

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            leaf.rename(tmp_path / "parent/old")
            leaf.write_bytes(b"same")

    with pytest.raises(ValueError, match="leaf"):
        gate._pinned_read(tmp_path, Path("parent/leaf"), hook=replace)


def test_source_reader_rejects_parent_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "leaf").write_bytes(b"value")
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        gate._pinned_read(tmp_path, Path("alias/leaf"))


def _write_exact6(root: Path, prefix: bytes = b"value") -> None:
    root.mkdir(parents=True)
    for name in gate.OUTPUT_FILES:
        (root / name).write_bytes(prefix + name.encode())


def test_exact6_reader_rejects_root_replacement(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root, b"old")

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            root.rename(tmp_path / "old-root")
            _write_exact6(root, b"new")

    with pytest.raises(ValueError, match="root"):
        gate._read_output_set(root, hook=replace)


def test_materializer_new_directory_existing_noop_and_tamper(
    tmp_path: Path,
) -> None:
    payloads = gate.build_artifacts(
        gate.build_frozen_source_snapshot(ROOT), repo_root=ROOT
    )
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)
    gate._materialize_set(plan, payloads)
    root_inode = os.lstat(plan.root).st_ino
    before = {
        name: os.lstat(plan.root / name).st_ino for name in gate.OUTPUT_FILES
    }
    assert not any(
        item.name.startswith(gate.STAGING_NAME_PREFIX)
        for item in tmp_path.iterdir()
    )
    gate._materialize_set(
        gate._inspect_output_target(Path("evidence"), tmp_path), payloads
    )
    assert os.lstat(plan.root).st_ino == root_inode
    assert before == {
        name: os.lstat(plan.root / name).st_ino for name in gate.OUTPUT_FILES
    }
    assert not any(
        item.name.startswith(gate.STAGING_NAME_PREFIX)
        for item in tmp_path.iterdir()
    )
    (plan.root / gate.OUTPUT_FILES[0]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="payload"):
        gate._materialize_set(
            gate._inspect_output_target(Path("evidence"), tmp_path), payloads
        )


def test_materializer_einval_retains_authenticated_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}

    def fail_rename(*_args: object) -> int:
        ctypes.set_errno(22)
        return -1

    monkeypatch.setattr(gate, "_RENAMEAT2", fail_rename)
    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(
            gate._inspect_output_target(Path("evidence"), tmp_path), payloads
        )
    retained = captured.value.authenticated_retained_path
    assert retained is not None and retained.is_dir()
    assert retained.name.startswith(gate.STAGING_NAME_PREFIX)
    assert set(os.listdir(retained)) == set(gate.OUTPUT_FILES)
    assert not (tmp_path / "evidence").exists()


def test_materializer_first_leaf_create_failure_retains_empty_stage_owned_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    original_open = gate.os.open

    def fail_first_leaf(
        path: object, flags: int, *args: object, **kwargs: object
    ) -> int:
        if (
            path == gate.OUTPUT_FILES[0]
            and flags & os.O_CREAT
        ):
            raise OSError("synthetic first leaf create failure")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(gate.os, "open", fail_first_leaf)
    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(
            gate._inspect_output_target(Path("evidence"), tmp_path),
            payloads,
        )
    retained = captured.value.authenticated_retained_path
    assert retained is not None
    assert retained.is_dir()
    assert retained.name.startswith(gate.STAGING_NAME_PREFIX)
    assert tuple(retained.iterdir()) == ()
    assert not (tmp_path / "evidence").exists()


def test_production_source_has_no_dispatch_or_torch_or_implementation() -> None:
    source = (ROOT / gate.SUPPORT_PATHS[0]).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "evaluate_admission_rule(" not in source
    assert "def aggregate_admission_rule_evaluations(" not in source
    assert '"cross_rule_aggregation_implemented": True' not in source


def test_stage_owned_staging_prefix_matches_independent_checker_authority() -> None:
    checker = _load_checker()
    production_source = (ROOT / gate.SUPPORT_PATHS[0]).read_text(
        encoding="utf-8"
    )
    checker_source = (ROOT / gate.SUPPORT_PATHS[1]).read_text(
        encoding="utf-8"
    )
    assert gate.STAGING_NAME_PREFIX == checker.STAGING_NAME_PREFIX
    assert gate.STAGING_NAME_PREFIX == (
        f"{gate.STAGE}.__staging__."
    )
    assert len(os.fsencode(gate.STAGING_NAME_PREFIX)) + 32 < 255
    assert ".combined-permission-semantics-stage-" not in production_source
    assert "LEGACY_MISNAMED_STAGING_PREFIX" in checker_source
    assert ".combined-permission-semantics-stage-" in checker_source


def test_checker_has_independent_expected_no_overlay_or_write_tree() -> None:
    source = (ROOT / gate.SUPPORT_PATHS[1]).read_text(encoding="utf-8")
    assert "candidate.build_artifacts" in source
    assert "candidate.build_artifacts(" not in source.split("def _local_expected", 1)[1].split(
        "def _verify_observed_artifacts", 1
    )[0]
    assert "include_revised2" not in source
    assert '"write-tree"' not in source
    assert "full_index" in source


def test_recursive_inventory_normal_and_generic_symlink_rejected(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    checker.assert_exact10_recursive_inventory(ROOT)
    for path in (
        "src/covalent_ext",
        "scripts",
        "tests",
        "docs",
        "data/derived/covalent_small",
    ):
        (tmp_path / path).mkdir(parents=True, exist_ok=True)
    (tmp_path / "target").write_bytes(b"x")
    (tmp_path / "docs/unrelated-link").symlink_to(tmp_path / "target")
    with pytest.raises(ValueError, match="symlink"):
        checker._bounded_recursive_stage_inventory(tmp_path)


def test_recursive_inventory_matching_residue_rejected(tmp_path: Path) -> None:
    checker = _load_checker()
    for path in (
        "src/covalent_ext",
        "scripts",
        "tests",
        "docs",
        "data/derived/covalent_small",
    ):
        (tmp_path / path).mkdir(parents=True, exist_ok=True)
    residue = tmp_path / "docs" / f"{checker.STAGE}_residue"
    residue.write_bytes(b"x")
    observed, _roots = checker._bounded_recursive_stage_inventory(tmp_path)
    assert Path("docs") / residue.name in observed


def _make_lifecycle_repo(root: Path, *, commit_candidate: bool) -> tuple[object, str]:
    checker = _load_checker()
    subprocess.run(("git", "init", "-q"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.email", "test@example.invalid"), cwd=root, check=True)
    subprocess.run(("git", "config", "user.name", "Test"), cwd=root, check=True)
    (root / "baseline").write_bytes(b"base")
    subprocess.run(("git", "add", "baseline"), cwd=root, check=True)
    subprocess.run(("git", "commit", "-q", "-m", "base"), cwd=root, check=True)
    base = _git(root, "rev-parse", "HEAD")
    for relative in checker.EXACT10:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.as_posix().encode())
    if commit_candidate:
        subprocess.run(
            ("git", "add", *(path.as_posix() for path in checker.EXACT10)),
            cwd=root,
            check=True,
        )
        subprocess.run(("git", "commit", "-q", "-m", "candidate"), cwd=root, check=True)
    return checker, base


def _git_untracked(root: Path) -> tuple[str, ...]:
    return tuple(
        value
        for value in _git(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).splitlines()
        if value
    )


def _ignore_in_synthetic_repo(root: Path, pattern: str) -> None:
    exclude = root / ".git/info/exclude"
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write(f"{pattern}\n")


@pytest.mark.parametrize(
    "support_root",
    (
        Path("src/covalent_ext"),
        Path("scripts"),
        Path("tests"),
        Path("docs"),
    ),
)
def test_four_bounded_roots_reject_ignored_embedded_stage_file(
    tmp_path: Path,
    support_root: Path,
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    ignored = support_root / "ignored"
    _ignore_in_synthetic_repo(
        tmp_path, f"{ignored.as_posix()}/"
    )
    hidden = (
        tmp_path
        / ignored
        / f"prefix_{checker.STAGE}_hidden.txt"
    )
    hidden.parent.mkdir(parents=True, exist_ok=True)
    hidden.write_bytes(b"ignored same-stage residue")
    assert checker.STAGE in hidden.name
    assert not hidden.name.startswith(checker.STAGE)
    assert _git_untracked(tmp_path) == tuple(
        sorted(path.as_posix() for path in checker.EXACT10)
    )
    with pytest.raises(ValueError, match="same-stage|recursive"):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    with pytest.raises(ValueError, match="same-stage|recursive"):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base
        )


def test_embedded_stage_directory_observes_all_descendants_and_is_rejected(
    tmp_path: Path,
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    bundle_name = f"prefix_{checker.STAGE}_bundle"
    _ignore_in_synthetic_repo(
        tmp_path, f"docs/{bundle_name}/"
    )
    bundle = tmp_path / "docs" / bundle_name
    bundle.mkdir()
    child = bundle / "arbitrary.txt"
    child.write_bytes(b"descendant without stage token")
    assert checker.STAGE in bundle.name
    assert not bundle.name.startswith(checker.STAGE)
    assert checker.STAGE not in child.name
    assert _git_untracked(tmp_path) == tuple(
        sorted(path.as_posix() for path in checker.EXACT10)
    )
    observed, _roots = checker._bounded_recursive_stage_inventory(
        tmp_path
    )
    assert Path("docs") / bundle_name in observed
    assert Path("docs") / bundle_name / child.name in observed
    with pytest.raises(ValueError, match="same-stage|recursive"):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    with pytest.raises(ValueError, match="same-stage|recursive"):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base
        )


def test_unrelated_ignored_regular_file_remains_allowed(
    tmp_path: Path,
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    _ignore_in_synthetic_repo(tmp_path, "docs/ignored/")
    note = tmp_path / "docs/ignored/ordinary_unrelated_note.txt"
    note.parent.mkdir()
    note.write_bytes(b"unrelated")
    assert checker.STAGE not in note.name
    assert checker.STAGE not in note.parent.name
    assert _git_untracked(tmp_path) == tuple(
        sorted(path.as_posix() for path in checker.EXACT10)
    )
    checker.assert_exact10_recursive_inventory(
        tmp_path, checker.EXACT10
    )
    assert checker.verify_lifecycle(
        tmp_path, checker.EXACT10, base=base
    ) == "pre_commit"


def test_lifecycle_rejects_empty_stage_owned_staging_hidden_from_git(
    tmp_path: Path,
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    residue = (
        tmp_path
        / "data/derived/covalent_small"
        / f"{checker.STAGING_NAME_PREFIX}deadbeef"
    )
    residue.mkdir()
    assert _git_untracked(tmp_path) == tuple(
        sorted(path.as_posix() for path in checker.EXACT10)
    )
    with pytest.raises(
        ValueError,
        match="same-stage|matching derived root|stage-owned",
    ):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    with pytest.raises(
        ValueError,
        match="same-stage|matching derived root|stage-owned",
    ):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base
        )


def test_lifecycle_rejects_empty_legacy_misnamed_staging_hidden_from_git(
    tmp_path: Path,
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    residue = (
        tmp_path
        / "data/derived/covalent_small"
        / f"{checker.LEGACY_MISNAMED_STAGING_PREFIX}deadbeef"
    )
    residue.mkdir()
    assert _git_untracked(tmp_path) == tuple(
        sorted(path.as_posix() for path in checker.EXACT10)
    )
    with pytest.raises(
        ValueError,
        match="legacy misnamed current-stage staging residue rejected",
    ):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    with pytest.raises(
        ValueError,
        match="legacy misnamed current-stage staging residue rejected",
    ):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base
        )


def test_partial_retained_staging_uses_prefix_and_lifecycle_rejects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    original_open = gate.os.open

    def fail_second_leaf(
        path: object, flags: int, *args: object, **kwargs: object
    ) -> int:
        if (
            path == gate.OUTPUT_FILES[1]
            and flags & os.O_CREAT
        ):
            raise OSError("synthetic partial staging failure")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(gate.os, "open", fail_second_leaf)
    plan = gate._inspect_output_target(
        Path("data/derived/covalent_small/unused-final"),
        tmp_path,
    )
    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(plan, payloads)
    retained = captured.value.authenticated_retained_path
    assert retained is not None and retained.is_dir()
    assert retained.name.startswith(gate.STAGING_NAME_PREFIX)
    assert tuple(item.name for item in retained.iterdir()) == (
        gate.OUTPUT_FILES[0],
    )
    assert not plan.root.exists()
    with pytest.raises(ValueError, match="same-stage|matching derived root"):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    with pytest.raises(ValueError):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base
        )


def test_stage_owned_staging_symlink_rejected_without_following_target(
    tmp_path: Path,
) -> None:
    checker, _base = _make_lifecycle_repo(
        tmp_path, commit_candidate=False
    )
    external = tmp_path / "external-target"
    external.mkdir()
    marker = external / "marker"
    marker.write_bytes(b"unchanged")
    residue = (
        tmp_path
        / "data/derived/covalent_small"
        / f"{checker.STAGING_NAME_PREFIX}symlink"
    )
    residue.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        checker.assert_exact10_recursive_inventory(
            tmp_path, checker.EXACT10
        )
    assert residue.is_symlink()
    assert marker.read_bytes() == b"unchanged"
    assert external.is_dir()


@pytest.mark.parametrize("commit_candidate", (False, True))
def test_lifecycle_precommit_and_postcommit(
    tmp_path: Path, commit_candidate: bool
) -> None:
    checker, base = _make_lifecycle_repo(
        tmp_path, commit_candidate=commit_candidate
    )
    expected = "post_commit" if commit_candidate else "pre_commit"
    assert checker.verify_lifecycle(
        tmp_path, checker.EXACT10, base=base
    ) == expected


def test_lifecycle_rejects_index_drift(tmp_path: Path) -> None:
    checker, base = _make_lifecycle_repo(tmp_path, commit_candidate=False)
    unrelated = tmp_path / "unrelated"
    unrelated.write_bytes(b"x")

    def drift(event: str, _path: Path) -> None:
        if event == "after_top_root_open":
            subprocess.run(("git", "add", "unrelated"), cwd=tmp_path, check=True)

    with pytest.raises(
        ValueError,
        match="staged|drift|dirty|untracked inventory",
    ):
        checker.verify_lifecycle(
            tmp_path, checker.EXACT10, base=base, hook=drift
        )


def test_production_and_checker_source_snapshot_reject_head_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = iter((gate.BASE_COMMIT, "0" * 40))
    monkeypatch.setattr(gate, "_strict_head", lambda _root: next(observed))
    with pytest.raises(ValueError, match="HEAD drift"):
        gate.build_frozen_source_snapshot(ROOT)
    checker = _load_checker()
    observed_checker = iter((checker.BASE_COMMIT, "0" * 40))
    monkeypatch.setattr(
        checker, "_strict_head", lambda _root=checker.ROOT: next(observed_checker)
    )
    with pytest.raises(ValueError, match="HEAD drift"):
        checker._source_snapshot()


def test_final_checker_lifecycle_is_last_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    events: list[str] = []
    payloads = {
        name: (b"{}\n" if name == checker.MANIFEST_NAME else b"csv")
        for name in checker.OUTPUT_NAMES
    }
    manifest = {
        "truth_matrix": {"row_count": 201, "group_count": 23},
        "safety_audit": {"row_count": 30},
    }
    lifecycle_calls = 0

    def lifecycle(*_args: object, **_kwargs: object) -> str:
        nonlocal lifecycle_calls
        lifecycle_calls += 1
        events.append(f"lifecycle-{lifecycle_calls}")
        return "pre_commit"

    class Candidate:
        @staticmethod
        def build_frozen_source_snapshot(*_args: object, **_kwargs: object):
            events.append("candidate-snapshot")
            return ()

        @staticmethod
        def build_artifacts(*_args: object, **_kwargs: object):
            events.append("candidate-artifacts")
            return payloads

    monkeypatch.setattr(checker, "_capture_lifecycle_state", lambda *_args, **_kwargs: "stable")
    monkeypatch.setattr(checker, "verify_lifecycle", lifecycle)
    monkeypatch.setattr(checker, "_source_snapshot", lambda: [])
    monkeypatch.setattr(checker, "_local_expected", lambda _snapshot: payloads)
    monkeypatch.setattr(checker, "read_exact6_no_follow", lambda: payloads)
    monkeypatch.setattr(checker, "_load_candidate", lambda: Candidate())
    monkeypatch.setattr(checker, "_verify_observed_artifacts", lambda *_args: manifest)
    report = checker._verify_complete_checker_run()
    assert events[-1] == "lifecycle-2"
    assert events.index("candidate-artifacts") < events.index("lifecycle-2")
    assert report["full_recursive_lifecycle_run_count"] == 2


def test_checker_full_main_or_detached_candidate_lifecycle() -> None:
    checker = _load_checker()
    report = checker._verify_complete_checker_run()
    assert report["lifecycle"] in {"pre_commit", "post_commit"}
    assert report["full_recursive_lifecycle_run_count"] == 2
    assert report["issue_transition_count"] == 0
    assert report["source_attestation_count"] == 12
    assert report["public_api_contract_row_count"] == 24
    assert report["truth_row_count"] == 201
    assert report["truth_group_count"] == 23
    assert report["stage_owned_staging_namespace_closure"] is True
    assert report["embedded_stage_residue_lifecycle_closure"] is True
    assert report["recommended_next_step"] == (
        "implement_covapie_combined_candidate_verdict_and_cross_rule_"
        "aggregation_v1"
    )

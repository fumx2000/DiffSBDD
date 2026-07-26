from __future__ import annotations

import importlib.util
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1 as aggregation,
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate as design,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_stage_global_rule_evaluation_orchestration_contract_v1.py"
)
spec = importlib.util.spec_from_file_location("stage_orchestration_checker", CHECKER_PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def _run_git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    return completed.stdout


def _initialize_local_remote(tmp_path: Path) -> Path:
    bare = tmp_path / "remote.git"
    _run_git(tmp_path, "init", "--bare", "--initial-branch=main", str(bare))
    _run_git(
        ROOT,
        "push",
        str(bare),
        f"{checker.BASE}:refs/heads/main",
    )
    _run_git(bare, "symbolic-ref", "HEAD", "refs/heads/main")
    return bare


def _copy_exact10(destination: Path) -> None:
    for relative in checker.EXACT10:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def _commit_exact10(repository: Path) -> str:
    _run_git(repository, "config", "user.name", "CovaPIE lifecycle test")
    _run_git(repository, "config", "user.email", "covapie-lifecycle@example.invalid")
    _run_git(
        repository,
        "add",
        "--",
        *[path.as_posix() for path in checker.EXACT10],
    )
    _run_git(
        repository,
        "commit",
        "-m",
        checker.FORMAL_COMMIT_SUBJECT,
    )
    return _run_git(repository, "rev-parse", "HEAD").decode().strip()


def _run_local_checker(repository: Path, expected_lifecycle: str) -> dict:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            str(repository / checker.CHECKER_PATH),
        ),
        cwd=repository,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert completed.stderr == b""
    report = json.loads(completed.stdout)
    assert report["lifecycle"] == expected_lifecycle
    assert report["lifecycle_mode_count"] == 4
    assert report["formal_commit_subject"] == checker.FORMAL_COMMIT_SUBJECT
    return report


def _inputs(count: int = 1):
    record = MappingProxyType({"candidate": object()})
    evaluation = MappingProxyType({"evaluation": object()})
    download = MappingProxyType({"download": object()})
    values = tuple(
        design.AdmissionCandidateOrchestrationInput(
            record, evaluation, download
        )
        for _ in range(count)
    )
    return values, record, evaluation, download


def _plan(scope: str, count: int = 1):
    values, _, _, _ = _inputs(count)
    batch = MappingProxyType({"batch": object()})
    authorization = MappingProxyType({"authorization": object()})
    return design.classify_stage_global_orchestration_contract_design(
        scope,
        values,
        batch_context=batch,
        stage_authorization_context=authorization,
    )


def test_future_production_api_is_frozen_but_not_implemented():
    assert not hasattr(design, "orchestrate_stage_admission_scope")
    rows = design._contract_rows()
    api = [row for row in rows if row["contract_area"] == "future_public_api"]
    assert len(api) == 18
    assert api[0]["observed_contract"] == "orchestrate_stage_admission_scope"
    defaults = {
        row["contract_item"]: row["observed_contract"]
        for row in api
        if row["contract_item"].endswith("_default")
    }
    assert defaults == {
        "scope_id_default": "absent",
        "candidate_inputs_default": "absent",
        "batch_context_default": "absent",
        "stage_authorization_context_default": "absent",
    }
    assert api[-1]["contract_passed"] == "true"


def test_design_classifier_exact_signature():
    signature = inspect.signature(
        design.classify_stage_global_orchestration_contract_design
    )
    parameters = tuple(signature.parameters.values())
    assert tuple(item.name for item in parameters) == (
        "scope_id",
        "candidate_inputs",
        "batch_context",
        "stage_authorization_context",
    )
    assert tuple(item.kind for item in parameters) == (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.KEYWORD_ONLY,
    )
    assert all(item.default is inspect.Parameter.empty for item in parameters)


@pytest.mark.parametrize(
    ("cls", "expected"),
    (
        (design.AdmissionCandidateOrchestrationInput, design.INPUT_FIELDS),
        (
            design.CandidateAdmissionOrchestrationResult,
            design.CANDIDATE_RESULT_FIELDS,
        ),
        (design.StageAdmissionOrchestrationResult, design.STAGE_RESULT_FIELDS),
        (design.StageAdmissionOrchestrationError, design.ERROR_FIELDS),
    ),
)
def test_future_mirror_dataclasses_are_exact_frozen_non_slotted(cls, expected):
    assert tuple(field.name for field in fields(cls)) == expected
    assert cls.__dataclass_params__.frozen is True
    assert "__slots__" not in cls.__dict__


def test_input_exact3_annotations_and_identity():
    assert tuple(
        design.AdmissionCandidateOrchestrationInput.__annotations__
    ) == design.INPUT_FIELDS
    values, record, evaluation, download = _inputs()
    assert values[0].candidate_record is record
    assert values[0].evaluation_context is evaluation
    assert values[0].download_result_context is download
    with pytest.raises(FrozenInstanceError):
        values[0].candidate_record = {}  # type: ignore[misc]


def test_candidate_result_exact5_annotations():
    assert tuple(
        design.CandidateAdmissionOrchestrationResult.__annotations__
    ) == design.CANDIDATE_RESULT_FIELDS


def test_stage_result_exact12_annotations_and_schema():
    assert tuple(
        design.StageAdmissionOrchestrationResult.__annotations__
    ) == design.STAGE_RESULT_FIELDS
    assert (
        design.STAGE_RESULT_SCHEMA_VERSION
        == "covapie_stage_admission_orchestration_result_v1"
    )


def test_error_exact8_fields_and_codes():
    assert tuple(design.StageAdmissionOrchestrationError.__annotations__) == (
        design.ERROR_FIELDS
    )
    assert len(design.ERROR_CODES) == 8
    assert design.ERROR_CODES == checker.ERROR_CODES
    assert issubclass(design.StageAdmissionOrchestrationError, Exception)
    error = design.StageAdmissionOrchestrationError(
        design.ERROR_CODES[0],
        "",
        -1,
        "",
        0,
        0,
        design.ERROR_CODES[0],
        "",
    )
    assert tuple(vars(error)) == design.ERROR_FIELDS
    assert error.args == (error.reason,)
    assert str(error) == error.reason


@pytest.mark.parametrize(
    ("changes", "error_type"),
    (
        ({"code": "wrong"}, ValueError),
        ({"scope_id": 1}, TypeError),
        ({"candidate_index": -2}, ValueError),
        ({"admission_rule_id": 1}, TypeError),
        ({"dispatcher_call_count": -1}, ValueError),
        ({"aggregator_call_count": True}, ValueError),
        ({"reason": ""}, ValueError),
        ({"cause_type": object()}, TypeError),
    ),
)
def test_error_constructor_fails_closed(changes, error_type):
    values = {
        "code": design.ERROR_CODES[0],
        "scope_id": "",
        "candidate_index": -1,
        "admission_rule_id": "",
        "dispatcher_call_count": 0,
        "aggregator_call_count": 0,
        "reason": design.ERROR_CODES[0],
        "cause_type": "",
    }
    values.update(changes)
    with pytest.raises(error_type):
        design.StageAdmissionOrchestrationError(**values)


def test_public_api_result_contract_exact54():
    rows = design._contract_rows()
    assert rows == checker._public_rows()
    assert len(rows) == 54
    assert all(row["contract_passed"] == "true" for row in rows)


@pytest.mark.parametrize(
    ("scope", "required_count", "stage_count", "candidate_count"),
    (
        ("download_execution_permission", 11, 1, 10),
        ("post_download_acceptance_permission", 13, 1, 12),
        ("pre_final_split_acceptance_permission", 14, 1, 13),
        ("training_execution_admission_permission", 15, 2, 13),
    ),
)
def test_exact4_scope_partition(
    scope, required_count, stage_count, candidate_count
):
    required = design.REQUIRED_RULE_IDS[scope]
    stage_rules = design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_rules = design.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    assert len(required) == required_count
    assert len(stage_rules) == stage_count
    assert len(candidate_rules) == candidate_count
    assert set(stage_rules).isdisjoint(candidate_rules)
    assert tuple(
        rule
        for rule in required
        if rule in stage_rules or rule in candidate_rules
    ) == required


def test_stage_global_membership_and_order():
    assert all(
        rules == ("ADMIT_014",)
        for rules in tuple(design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE.values())[:3]
    )
    assert design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[
        "training_execution_admission_permission"
    ] == ("ADMIT_014", "ADMIT_015")


def test_admit_014_never_candidate_scoped_and_admit_015_training_only():
    assert all(
        "ADMIT_014" not in rules
        for rules in design.CANDIDATE_RULE_IDS_BY_SCOPE.values()
    )
    assert all(
        ("ADMIT_015" in rules)
        is (scope == "training_execution_admission_permission")
        for scope, rules in design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE.items()
    )


def test_sentinel_is_immutable_empty_mapping():
    sentinel = design.STAGE_GLOBAL_CANDIDATE_SENTINEL
    assert type(sentinel) is MappingProxyType
    assert tuple(sentinel) == ()
    with pytest.raises(TypeError):
        sentinel["candidate"] = object()  # type: ignore[index]


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
@pytest.mark.parametrize("count", (1, 2, 3))
def test_design_plan_cardinality(scope, count):
    plan = _plan(scope, count)
    stage = len(design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
    candidate = len(design.CANDIDATE_RULE_IDS_BY_SCOPE[scope])
    assert plan.dispatcher_call_count == stage + candidate * count
    assert plan.aggregator_call_count == count
    assert plan.orchestration_io_used is False
    assert plan.action_permission_granted is False


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
def test_dispatcher_call_order(scope):
    plan = _plan(scope, 2)
    expected = tuple(
        [(-1, rule) for rule in plan.stage_global_rule_ids]
        + [
            (candidate_index, rule)
            for candidate_index in range(2)
            for rule in plan.candidate_rule_ids
        ]
    )
    assert plan.dispatcher_call_order == expected


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
def test_complete_vector_assembly_and_identity(scope):
    plan = _plan(scope, 3)
    for candidate in plan.candidate_plans:
        assert tuple(
            token.admission_rule_id
            for token in candidate.ordered_rule_results
        ) == plan.required_rule_ids
        assert tuple(
            token.admission_rule_id
            for token in candidate.candidate_rule_results
        ) == plan.candidate_rule_ids
        assert candidate.dispatcher_call_count == len(plan.candidate_rule_ids)
        assert candidate.aggregator_call_count == 1
    for token in plan.stage_global_rule_results:
        position = plan.required_rule_ids.index(token.admission_rule_id)
        assert all(
            candidate.ordered_rule_results[position] is token
            for candidate in plan.candidate_plans
        )


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
def test_candidate_tuple_and_input_identity_preserved(scope):
    values, record, evaluation, download = _inputs(3)
    batch = MappingProxyType({"batch": object()})
    authorization = MappingProxyType({"authorization": object()})
    plan = design.classify_stage_global_orchestration_contract_design(
        scope,
        values,
        batch_context=batch,
        stage_authorization_context=authorization,
    )
    assert plan.candidate_inputs is values
    assert plan.batch_context is batch
    assert plan.stage_authorization_context is authorization
    assert all(
        item.candidate_input is values[index]
        for index, item in enumerate(plan.candidate_plans)
    )
    assert values[0].candidate_record is record
    assert values[0].evaluation_context is evaluation
    assert values[0].download_result_context is download


class InputSubclass(design.AdmissionCandidateOrchestrationInput):
    pass


@pytest.mark.parametrize(
    ("scope", "inputs", "batch", "authorization", "code"),
    (
        (
            "invalid",
            (design.AdmissionCandidateOrchestrationInput({}, None, None),),
            None,
            None,
            design.ERROR_CODES[0],
        ),
        (
            design.SCOPE_IDS[0],
            [],
            None,
            None,
            design.ERROR_CODES[1],
        ),
        (
            design.SCOPE_IDS[0],
            (),
            None,
            None,
            design.ERROR_CODES[1],
        ),
        (
            design.SCOPE_IDS[0],
            (object(),),
            None,
            None,
            design.ERROR_CODES[2],
        ),
        (
            design.SCOPE_IDS[0],
            (InputSubclass({}, None, None),),
            None,
            None,
            design.ERROR_CODES[2],
        ),
        (
            design.SCOPE_IDS[0],
            (design.AdmissionCandidateOrchestrationInput(object(), None, None),),
            None,
            None,
            design.ERROR_CODES[2],
        ),
        (
            design.SCOPE_IDS[0],
            (design.AdmissionCandidateOrchestrationInput({}, object(), None),),
            None,
            None,
            design.ERROR_CODES[2],
        ),
        (
            design.SCOPE_IDS[0],
            (design.AdmissionCandidateOrchestrationInput({}, None, object()),),
            None,
            None,
            design.ERROR_CODES[2],
        ),
        (
            design.SCOPE_IDS[0],
            (design.AdmissionCandidateOrchestrationInput({}, None, None),),
            object(),
            None,
            design.ERROR_CODES[3],
        ),
        (
            design.SCOPE_IDS[0],
            (design.AdmissionCandidateOrchestrationInput({}, None, None),),
            None,
            object(),
            design.ERROR_CODES[4],
        ),
    ),
)
def test_all_top_level_input_validation_fail_closed(
    scope, inputs, batch, authorization, code
):
    with pytest.raises(design.StageAdmissionOrchestrationError) as captured:
        design.classify_stage_global_orchestration_contract_design(
            scope,
            inputs,
            batch_context=batch,
            stage_authorization_context=authorization,
        )
    error = captured.value
    assert error.code == code
    assert (
        error.candidate_index,
        error.admission_rule_id,
        error.dispatcher_call_count,
        error.aggregator_call_count,
        error.reason,
        error.cause_type,
    ) == (-1, "", 0, 0, code, "")


def test_validation_precedence_candidate_before_context():
    with pytest.raises(design.StageAdmissionOrchestrationError) as captured:
        design.classify_stage_global_orchestration_contract_design(
            design.SCOPE_IDS[0],
            (object(),),
            batch_context=object(),
            stage_authorization_context=object(),
        )
    assert captured.value.code == design.ERROR_CODES[2]


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
def test_failure_coordinate_formulas_cover_stage_and_candidate_matrix(scope):
    stage_ids = design.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_ids = design.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    global_count = len(stage_ids)
    candidate_count = len(candidate_ids)
    for position, rule_id in enumerate(stage_ids, 1):
        coordinate = design.compute_failure_coordinate_design(
            scope,
            "stage_global_dispatch",
            candidate_index=-1,
            rule_position=position,
        )
        assert tuple(vars(coordinate).values()) == (
            -1,
            rule_id,
            position,
            0,
        )
    for candidate_index in (0, 1, 2):
        for position in (1, (candidate_count + 1) // 2, candidate_count):
            coordinate = design.compute_failure_coordinate_design(
                scope,
                "candidate_dispatch",
                candidate_index=candidate_index,
                rule_position=position,
            )
            assert tuple(vars(coordinate).values()) == (
                candidate_index,
                candidate_ids[position - 1],
                global_count
                + candidate_index * candidate_count
                + position,
                candidate_index,
            )
        coordinate = design.compute_failure_coordinate_design(
            scope,
            "candidate_aggregator",
            candidate_index=candidate_index,
            rule_position=0,
        )
        assert tuple(vars(coordinate).values()) == (
            candidate_index,
            "",
            global_count + (candidate_index + 1) * candidate_count,
            candidate_index + 1,
        )


def test_failure_delivery_raises_from_exception_with_deterministic_projection():
    cause = RuntimeError("address-like-cause-detail-must-not-project")
    with pytest.raises(design.StageAdmissionOrchestrationError) as captured:
        design.raise_orchestration_failure_from_cause_design(
            design.SCOPE_IDS[-1],
            "candidate_dispatch",
            candidate_index=2,
            rule_position=3,
            cause=cause,
        )
    error = captured.value
    assert error.__cause__ is cause
    assert error.cause_type == "RuntimeError"
    assert error.args == (error.reason,)
    assert "address-like-cause-detail" not in error.reason
    assert (
        error.candidate_index,
        error.admission_rule_id,
        error.dispatcher_call_count,
        error.aggregator_call_count,
    ) == (2, "ADMIT_003", 31, 2)


def test_failure_delivery_rejects_baseexception():
    with pytest.raises(TypeError, match="must inherit Exception"):
        design.raise_orchestration_failure_from_cause_design(
            design.SCOPE_IDS[-1],
            "stage_global_dispatch",
            candidate_index=-1,
            rule_position=1,
            cause=KeyboardInterrupt(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("rule_id", design.RULE_IDS)
def test_unified_exact13_validator_accepts_all_rules(rule_id):
    result = design._design_unified_result(rule_id)
    assert (
        design.validate_unified_rule_evaluation_design(
            result,
            expected_rule_id=rule_id,
            scope_id=design.SCOPE_IDS[-1],
            candidate_index=0,
            dispatcher_call_count=1,
            aggregator_call_count=0,
        )
        is result
    )


def test_unified_rejected_is_structurally_valid_and_not_reinterpreted():
    result = design._design_unified_result("ADMIT_001", "rejected")
    assert result.outcome == "rejected"
    assert result.blocks_candidate is True
    assert (
        design.validate_unified_rule_evaluation_design(
            result,
            expected_rule_id="ADMIT_001",
            scope_id=design.SCOPE_IDS[0],
            candidate_index=0,
            dispatcher_call_count=1,
            aggregator_call_count=0,
        )
        is result
    )
    assert design.ACTUAL_AGGREGATOR_CALL_COUNT == 0


def test_unified_exact13_validator_negative_mutations_are_actual():
    valid = design._design_unified_result("ADMIT_001")

    class UnifiedSubclass(type(valid)):
        pass

    subclass = UnifiedSubclass(**vars(valid))
    reverse_storage = object.__new__(type(valid))
    for name in reversed(design.UNIFIED_RESULT_FIELDS):
        object.__setattr__(reverse_storage, name, vars(valid)[name])
    mutations = (
        (subclass, "ADMIT_001"),
        (valid, "ADMIT_002"),
        (
            design._forged_dataclass(type(valid), valid, adapter_id="wrong"),
            "ADMIT_001",
        ),
        (
            design._forged_dataclass(
                type(valid), valid, admission_rule_name="wrong"
            ),
            "ADMIT_001",
        ),
        (
            design._forged_dataclass(
                type(valid), valid, schema_version="wrong"
            ),
            "ADMIT_001",
        ),
        (
            design._forged_dataclass(
                type(valid),
                valid,
                normalized_values=(("key", object()),),
            ),
            "ADMIT_001",
        ),
        (
            design._forged_dataclass(type(valid), valid, passed=1),
            "ADMIT_001",
        ),
        (reverse_storage, "ADMIT_001"),
    )
    for value, expected_rule_id in mutations:
        with pytest.raises(
            design.StageAdmissionOrchestrationError
        ) as captured:
            design.validate_unified_rule_evaluation_design(
                value,
                expected_rule_id=expected_rule_id,
                scope_id=design.SCOPE_IDS[-1],
                candidate_index=0,
                dispatcher_call_count=1,
                aggregator_call_count=0,
            )
        assert captured.value.code == design.ERROR_CODES[6]


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
@pytest.mark.parametrize("outcome", ("passed", "blocked", "invalid"))
def test_combined_exact13_validator_accepts_exact4_scope_outcomes(scope, outcome):
    vector, verdict = design._design_combined_verdict(scope, outcome)
    assert (
        design.validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=scope,
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
        is verdict
    )


def test_rejected_branch_uses_committed_aggregator_constants():
    assert aggregation.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES == (
        "passed",
        "blocked",
        "invalid",
    )
    assert (
        design.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
        == aggregation.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
    )
    assert (
        design.COMBINED_EVALUATION_INVARIANT_INVALID_REASON
        == aggregation.EVALUATION_INVARIANT_INVALID_REASON
        == "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID"
    )


@pytest.mark.parametrize("scope", design.SCOPE_IDS)
@pytest.mark.parametrize("position_name", ("first", "middle", "last"))
def test_rejected_canonical_verdict_exact4_positions(scope, position_name):
    required = design.REQUIRED_RULE_IDS[scope]
    positions = {
        "first": 1,
        "middle": (len(required) + 1) // 2,
        "last": len(required),
    }
    position = positions[position_name]
    vector = design._design_rejected_ordered_vector(scope, (position,))
    verdict = design._design_rejected_aggregator_fail_closed_verdict(scope)
    assert tuple(item.admission_rule_id for item in vector) == required
    assert tuple(item.outcome for item in vector) == tuple(
        "rejected" if index == position else "passed"
        for index in range(1, len(required) + 1)
    )
    for item, rule_id in zip(vector, required, strict=True):
        assert (
            design.validate_unified_rule_evaluation_design(
                item,
                expected_rule_id=rule_id,
                scope_id=scope,
                candidate_index=0,
                dispatcher_call_count=1,
                aggregator_call_count=0,
            )
            is item
        )
    assert (
        design.validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=scope,
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
        is verdict
    )
    assert tuple(vars(verdict).values()) == (
        design.COMBINED_RESULT_SCHEMA_VERSION,
        scope,
        "invalid",
        False,
        True,
        aggregation.EVALUATION_INVARIANT_INVALID_REASON,
        required,
        (),
        (),
        (),
        (),
        (),
        False,
    )


@pytest.mark.parametrize(
    ("rejected_positions", "additional"),
    (
        ((1, 15), ()),
        ((1,), ((8, "blocked"),)),
        ((1,), ((15, "invalid"),)),
        ((1,), ((8, "blocked"), (15, "invalid"))),
    ),
)
def test_rejected_precedes_blocked_invalid_and_multiple(
    rejected_positions, additional
):
    scope = design.SCOPE_IDS[-1]
    vector = design._design_rejected_ordered_vector(
        scope,
        rejected_positions,
        additional_outcomes=additional,
    )
    verdict = design._design_rejected_aggregator_fail_closed_verdict(scope)
    assert any(item.outcome == "rejected" for item in vector)
    assert (
        design.validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=scope,
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
        is verdict
    )
    assert verdict.reason == aggregation.EVALUATION_INVARIANT_INVALID_REASON
    assert (
        verdict.evaluated_rule_ids,
        verdict.rule_evaluations,
        verdict.invalid_rule_ids,
        verdict.blocked_rule_ids,
        verdict.failing_rule_ids,
    ) == ((), (), (), (), ())


def test_rejected_canonical_wrong_reason_and_retained_vector_fail_closed():
    scope = design.SCOPE_IDS[0]
    vector = design._design_rejected_ordered_vector(scope, (1,))
    verdict = design._design_rejected_aggregator_fail_closed_verdict(scope)
    mutations = (
        design._forged_dataclass(
            type(verdict),
            verdict,
            reason=design.COMBINED_REQUIRED_RULE_INVALID_REASON,
        ),
        design._forged_dataclass(
            type(verdict),
            verdict,
            evaluated_rule_ids=design.REQUIRED_RULE_IDS[scope],
            rule_evaluations=vector,
        ),
    )
    for value in mutations:
        with pytest.raises(
            design.StageAdmissionOrchestrationError
        ) as captured:
            design.validate_combined_candidate_verdict_design(
                value,
                expected_scope_id=scope,
                ordered_rule_evaluations=vector,
                candidate_index=0,
                dispatcher_call_count=len(vector),
                aggregator_call_count=1,
            )
        assert captured.value.code == design.ERROR_CODES[7]


def test_combined_validator_branch_isolation_and_normal_identity():
    scope = design.SCOPE_IDS[0]
    normal_vector, normal_verdict = design._design_combined_verdict(
        scope, "passed"
    )
    rejected_vector = design._design_rejected_ordered_vector(scope, (1,))
    rejected_verdict = (
        design._design_rejected_aggregator_fail_closed_verdict(scope)
    )
    copied_vector = tuple([*normal_vector])
    copied_verdict = design._forged_dataclass(
        type(normal_verdict),
        normal_verdict,
        rule_evaluations=copied_vector,
    )
    for value, vector in (
        (rejected_verdict, normal_vector),
        (normal_verdict, rejected_vector),
        (copied_verdict, normal_vector),
    ):
        with pytest.raises(
            design.StageAdmissionOrchestrationError
        ) as captured:
            design.validate_combined_candidate_verdict_design(
                value,
                expected_scope_id=scope,
                ordered_rule_evaluations=vector,
                candidate_index=0,
                dispatcher_call_count=len(vector),
                aggregator_call_count=1,
            )
        assert captured.value.code == design.ERROR_CODES[7]


def test_rejected_truth_evidence_never_calls_real_aggregator(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("real aggregator callable invoked")

    monkeypatch.setattr(
        aggregation,
        "aggregate_admission_rule_evaluations",
        blocked,
    )
    rows = design._truth_rows()
    assert all(row["case_passed"] == "true" for row in rows)
    assert design.ACTUAL_AGGREGATOR_CALL_COUNT == 0


def test_combined_exact13_validator_negative_mutations_are_actual():
    scope = design.SCOPE_IDS[0]
    vector, verdict = design._design_combined_verdict(scope, "passed")

    class VerdictSubclass(type(verdict)):
        pass

    subclass = VerdictSubclass(**vars(verdict))
    copied_vector = tuple([*vector])
    reverse_storage = object.__new__(type(verdict))
    for name in reversed(design.COMBINED_RESULT_FIELDS):
        object.__setattr__(reverse_storage, name, vars(verdict)[name])
    mutations = (
        (subclass, scope, vector),
        (verdict, design.SCOPE_IDS[1], vector),
        (
            design._forged_dataclass(
                type(verdict),
                verdict,
                evaluated_rule_ids=tuple(reversed(verdict.evaluated_rule_ids)),
            ),
            scope,
            vector,
        ),
        (
            design._forged_dataclass(
                type(verdict), verdict, rule_evaluations=copied_vector
            ),
            scope,
            vector,
        ),
        (
            design._forged_dataclass(
                type(verdict), verdict, schema_version="wrong"
            ),
            scope,
            vector,
        ),
        (
            design._forged_dataclass(type(verdict), verdict, passed=1),
            scope,
            vector,
        ),
        (reverse_storage, scope, vector),
    )
    for value, expected_scope, expected_vector in mutations:
        with pytest.raises(
            design.StageAdmissionOrchestrationError
        ) as captured:
            design.validate_combined_candidate_verdict_design(
                value,
                expected_scope_id=expected_scope,
                ordered_rule_evaluations=expected_vector,
                candidate_index=0,
                dispatcher_call_count=len(expected_vector),
                aggregator_call_count=1,
            )
        assert captured.value.code == design.ERROR_CODES[7]


def test_call_plan_exact53_and_occurrence_counts():
    rows = design._call_plan_rows()
    assert rows == checker._call_rows()
    assert len(rows) == 53
    assert sum(row["admission_rule_id"] == "ADMIT_014" for row in rows) == 4
    assert sum(row["admission_rule_id"] == "ADMIT_015" for row in rows) == 1
    assert all(row["contract_passed"] == "true" for row in rows)


@pytest.mark.parametrize("rule_id", design.RULE_IDS)
def test_context_routing_authority_for_every_rule(rule_id):
    rows = [
        row
        for row in design._call_plan_rows()
        if row["admission_rule_id"] == rule_id
    ]
    expected = design._CONTEXT_ROUTING[rule_id]
    assert rows
    assert all(
        (
            row["batch_context_source"],
            row["evaluation_context_source"],
            row["download_result_context_source"],
            row["stage_authorization_context_source"],
        )
        == expected
        for row in rows
    )
    assert all(
        row["contract_evidence_source"].endswith(rule_id) for row in rows
    )


def test_truth_generator_exact307_50_and_checker_independence():
    rows = design._truth_rows()
    assert rows == checker._truth_rows()
    assert len(rows) == design.TRUTH_ROW_COUNT == 307
    assert len({row["case_group"] for row in rows}) == design.TRUTH_GROUP_COUNT == 50
    assert all(row["case_passed"] == "true" for row in rows)


def test_truth_contains_normal_no_short_circuit_and_error_stop_contracts():
    groups = {row["case_group"] for row in design._truth_rows()}
    assert {
        "no_normal_result_short_circuit",
        "blocked_stage_result_diagnostics_continue",
        "invalid_candidate_result_later_candidates_continue",
        "unified_rejected_structurally_valid",
        "rejected_exact4_position_validator_valid",
        "rejected_mixed_precedence_validator_valid",
        "rejected_combined_validator_fail_closed",
        "combined_validator_branch_isolation_fail_closed",
        "stage_global_dispatch_failure_formula",
        "candidate_dispatch_failure_formula",
        "candidate_aggregator_failure_formula",
        "unified_result_validator_fail_closed",
        "combined_result_validator_fail_closed",
    } <= groups


def test_safety_exact30():
    rows = design._safety_rows()
    assert rows == checker._safety_rows()
    assert len(rows) == 30
    assert all(row["safety_passed"] == "true" for row in rows)


def test_static_source_has_no_real_dispatch_or_aggregation_calls():
    checker._assert_static_no_runtime_calls()


def test_source_boundary_exact16_and_exact14_actual_sha():
    assert len(design.SOURCE_BOUNDARY) == 16
    assert design.SOURCE_BOUNDARY == checker.SOURCE_BOUNDARY
    assert (
        design.SOURCE_BOUNDARY[10][1]
        == "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2"
    )


@pytest.fixture(scope="module")
def independent_snapshot():
    return checker._source_snapshot()


@pytest.fixture(scope="module")
def candidate_snapshot():
    return design.build_frozen_source_snapshot(ROOT)


@pytest.fixture(scope="module")
def expected_artifacts(independent_snapshot):
    return checker._expected_artifacts(independent_snapshot)


@pytest.fixture(scope="module")
def actual_artifacts(candidate_snapshot):
    return design.build_artifacts(candidate_snapshot, repo_root=ROOT)


def test_source_attestation_production_checker_equality(
    independent_snapshot, candidate_snapshot
):
    assert len(independent_snapshot) == len(candidate_snapshot) == 16
    assert tuple(row["path"] for row in independent_snapshot) == tuple(
        item.relative_path.as_posix() for item in candidate_snapshot
    )
    assert tuple(row["content"] for row in independent_snapshot) == tuple(
        item.content for item in candidate_snapshot
    )


def test_precondition_continuity_43_0_2_2(independent_snapshot):
    checker._assert_preconditions(independent_snapshot)


def test_issue_exact30_byte_identity(independent_snapshot):
    issue = independent_snapshot[7]["content"]
    checker._assert_issue(issue)
    assert (
        design._sha(issue)
        == "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    )


def test_production_checker_disk_artifact_equality(
    expected_artifacts, actual_artifacts
):
    assert actual_artifacts == expected_artifacts
    assert checker._read_disk() == expected_artifacts


def test_dynamic_monkeypatch_proves_zero_real_calls(
    candidate_snapshot,
):
    checker._assert_dynamic_no_runtime_calls(design, candidate_snapshot)


def test_manifest_complete_hash_truth_and_readiness(expected_artifacts):
    manifest = json.loads(expected_artifacts[design.MANIFEST_FILENAME])
    assert manifest["manifest_self_sha256_recorded"] is False
    assert design.MANIFEST_FILENAME not in manifest["derived_output_sha256"]
    assert manifest["api_result_contract_row_count"] == 54
    assert manifest["call_plan_row_count"] == 53
    assert manifest["truth_matrix"]["row_count"] == 307
    assert manifest["truth_matrix"]["group_count"] == 50
    assert manifest["safety_audit"]["row_count"] == 30
    hardening = manifest["infrastructure_hardening"]
    assert hardening["lifecycle_mode_count"] == 4
    assert hardening["pre_commit_lifecycle_supported"] is True
    assert hardening["detached_candidate_post_commit_supported"] is True
    assert hardening["formal_main_post_commit_unpushed_supported"] is True
    assert hardening["formal_main_post_push_supported"] is True
    assert hardening["formal_commit_subject_frozen"] is True
    assert hardening["formal_main_real_local_git_simulation_passed"] is True
    assert manifest["precondition_continuity"]["transition_count"] == 0
    assert manifest["issue_continuity"]["transition_count"] == 0
    assert manifest["readiness"]["ready_for_training"] is False
    assert set(manifest["future_public_api"]["parameter_defaults"].values()) == {
        "absent"
    }
    assert manifest["error_contract"]["inherits_exception"] is True
    assert manifest["error_contract"]["all_failures_raise_error"] is True
    assert (
        manifest["error_contract"]["caught_cause_base"]
        == "Exception_only_not_BaseException"
    )
    assert manifest["failure_coordinate_formulas"]["attempt_inclusive"] is True
    assert (
        manifest["result_invariant_validators"]["unified_rule_evaluation"][
            "failure_code"
        ]
        == design.ERROR_CODES[6]
    )
    assert (
        manifest["result_invariant_validators"]["combined_candidate_verdict"][
            "failure_code"
        ]
        == design.ERROR_CODES[7]
    )
    combined = manifest["result_invariant_validators"][
        "combined_candidate_verdict"
    ]
    assert combined["normal_outcome_retained_vector_identity_required"] is True
    assert combined["rejected_input_complete_vector_required"] is True
    assert combined["rejected_fail_closed_empty_diagnostics_required"] is True
    assert combined["rejected_fail_closed_retained_vector_forbidden"] is True
    assert (
        combined["rejected_aggregator_reason"]
        == aggregation.EVALUATION_INVARIANT_INVALID_REASON
    )
    assert combined["aggregator_admissible_child_outcomes"] == [
        "passed",
        "blocked",
        "invalid",
    ]
    assert manifest["runtime_safety_boundary"] == {
        "real_orchestrator_implemented": False,
        "actual_dispatcher_called": False,
        "actual_handler_called": False,
        "actual_aggregator_called": False,
        "download_action_performed": False,
        "training_action_performed": False,
        "action_permission_granted": False,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "feature_semantics_audit_still_required": True,
        "ready_for_training": False,
    }
    assert manifest["v1_action_permission_boundary"] == {
        "action_permission_granted": False,
        "all_combined_verdicts_passed_does_not_grant_action": True,
        "combined_verdict_is_diagnostic_not_execution_authorization": True,
        "rules_and_diagnostic_aggregation_are_in_memory_only": True,
        "download_or_training_triggered": False,
        "future_action_permission_bridge_requires_separate_contract_and_gate": True,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
    }
    assert manifest["recommended_next_step"] == design.RECOMMENDED_NEXT_STEP


def test_canonical_masks_exact5_including_b3(expected_artifacts):
    manifest = json.loads(expected_artifacts[design.MANIFEST_FILENAME])
    assert [(row["semantic_name"], row["alias"]) for row in manifest["canonical_masks"]] == [
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    ]


def test_feature_semantics_warning_preserved(expected_artifacts):
    manifest = json.loads(expected_artifacts[design.MANIFEST_FILENAME])
    warning = manifest["feature_semantics_warning"]
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in warning
    assert "feature_semantics_known=False" in warning
    assert "Step12D" in manifest["step12d_warning"]


def test_new_directory_materialization_and_existing_noop(
    tmp_path, actual_artifacts
):
    root = tmp_path / design.STAGE
    result = design._materialize(root, actual_artifacts, repo_root=ROOT)
    before = os.lstat(result)
    assert {
        name: design._pinned_regular_read(tmp_path, Path(design.STAGE) / name)
        for name in design.OUTPUT_FILES
    } == actual_artifacts
    assert design._materialize(root, actual_artifacts, repo_root=ROOT) == root
    after = os.lstat(result)
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)


def test_existing_materialization_tamper_fails_closed(
    tmp_path, actual_artifacts
):
    root = tmp_path / design.STAGE
    design._materialize(root, actual_artifacts, repo_root=ROOT)
    target = root / design.PUBLIC_API_RESULT_FILENAME
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="existing output payload drift"):
        design._materialize(root, actual_artifacts, repo_root=ROOT)


def test_materializer_retains_authenticated_staging_on_hook_failure(
    tmp_path, actual_artifacts
):
    root = tmp_path / design.STAGE

    def fail(event, path):
        assert event == "before_rename"
        assert path.is_dir()
        raise RuntimeError("injected")

    with pytest.raises(design.MaterializationRetentionError) as captured:
        design._materialize(root, actual_artifacts, repo_root=ROOT, hook=fail)
    retained = captured.value.authenticated_retained_path
    assert retained is not None and retained.is_dir()
    assert not root.exists()


def test_pinned_read_rejects_symlink_leaf(tmp_path):
    source = tmp_path / "source"
    source.write_text("x")
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises((OSError, ValueError)):
        design._pinned_regular_read(tmp_path, Path("link"))


def test_ref_inventory_and_current_lifecycle_formal_closures():
    lifecycle = checker._recursive_lifecycle()
    checker._assert_persistent_refs(lifecycle.refs)

    if lifecycle.lifecycle in (
        "pre_commit",
        "detached_candidate_post_commit",
    ):
        expected_main = checker.BASE
        expected_origin = checker.BASE
    elif lifecycle.lifecycle == "formal_main_post_commit_unpushed":
        expected_main = lifecycle.head
        expected_origin = checker.BASE
    elif lifecycle.lifecycle == "formal_main_post_push":
        expected_main = lifecycle.head
        expected_origin = lifecycle.head
    else:
        raise AssertionError(
            f"unexpected lifecycle: {lifecycle.lifecycle}"
        )

    checker._assert_formal_refs(
        lifecycle.refs,
        expected_main=expected_main,
        expected_origin=expected_origin,
        origin_head=lifecycle.origin_head,
    )
    assert any(
        row.name == "refs/heads/main" for row in lifecycle.refs
    )


def test_recursive_lifecycle_contract():
    lifecycle = checker._recursive_lifecycle()
    assert lifecycle.lifecycle in checker.LIFECYCLE_MODES
    if lifecycle.lifecycle == "pre_commit":
        assert lifecycle.head == checker.BASE
        assert lifecycle.branch == "main"
        assert lifecycle.origin_head == (
            "refs/remotes/origin/main",
            checker.BASE,
        )
    elif lifecycle.lifecycle == "detached_candidate_post_commit":
        assert lifecycle.branch == ""
        assert len(lifecycle.worktrees) == 2
    else:
        assert lifecycle.branch == "main"
        assert len(lifecycle.worktrees) == 1


def test_lifecycle_vocabulary_exact4_and_formal_subject():
    assert checker.LIFECYCLE_MODES == (
        "pre_commit",
        "detached_candidate_post_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    )
    assert (
        checker.FORMAL_COMMIT_SUBJECT
        == "add CovaPIE stage-global rule evaluation orchestration contract v1"
    )


@pytest.mark.parametrize(
    ("main_oid", "origin_oid"),
    (
        ("candidate", checker.BASE),
        ("candidate", "candidate"),
    ),
)
def test_formal_main_ref_states_are_lifecycle_specific(main_oid, origin_oid):
    refs = (
        checker.RefRecord("refs/heads/main", main_oid, "commit"),
        checker.RefRecord("refs/remotes/origin/HEAD", origin_oid, "commit"),
        checker.RefRecord("refs/remotes/origin/main", origin_oid, "commit"),
    )
    checker._assert_persistent_refs(refs)
    checker._assert_formal_refs(
        refs,
        expected_main=main_oid,
        expected_origin=origin_oid,
        origin_head=("refs/remotes/origin/main", origin_oid),
    )


def test_formal_main_unpushed_cannot_be_misreported_as_pushed():
    refs = (
        checker.RefRecord("refs/heads/main", "candidate", "commit"),
        checker.RefRecord("refs/remotes/origin/HEAD", checker.BASE, "commit"),
        checker.RefRecord("refs/remotes/origin/main", checker.BASE, "commit"),
    )
    with pytest.raises(ValueError, match="formal ref closure"):
        checker._assert_formal_refs(
            refs,
            expected_main="candidate",
            expected_origin="candidate",
            origin_head=("refs/remotes/origin/main", checker.BASE),
        )


def test_formal_main_pushed_cannot_be_misreported_as_unpushed():
    refs = (
        checker.RefRecord("refs/heads/main", "candidate", "commit"),
        checker.RefRecord("refs/remotes/origin/HEAD", "candidate", "commit"),
        checker.RefRecord("refs/remotes/origin/main", "candidate", "commit"),
    )
    with pytest.raises(ValueError, match="formal ref closure"):
        checker._assert_formal_refs(
            refs,
            expected_main="candidate",
            expected_origin=checker.BASE,
            origin_head=("refs/remotes/origin/main", "candidate"),
        )


@pytest.mark.parametrize(
    "extra_ref",
    (
        checker.RefRecord("refs/heads/review", checker.BASE, "commit"),
        checker.RefRecord("refs/tags/candidate", checker.BASE, "commit"),
        checker.RefRecord("refs/candidate/temporary", checker.BASE, "commit"),
    ),
)
def test_additional_branch_tag_or_persistent_ref_is_rejected(extra_ref):
    refs = (
        checker.RefRecord("refs/heads/main", checker.BASE, "commit"),
        checker.RefRecord("refs/remotes/origin/HEAD", checker.BASE, "commit"),
        checker.RefRecord("refs/remotes/origin/main", checker.BASE, "commit"),
        extra_ref,
    )
    with pytest.raises(ValueError, match="persistent ref forbidden"):
        checker._assert_persistent_refs(refs)


@pytest.mark.parametrize(
    ("parent", "subject", "paths", "wrong_mode", "message"),
    (
        (
            "wrong-parent",
            checker.FORMAL_COMMIT_SUBJECT,
            tuple(path.as_posix() for path in checker.EXACT10),
            False,
            "parent/subject",
        ),
        (
            checker.BASE,
            "wrong subject",
            tuple(path.as_posix() for path in checker.EXACT10),
            False,
            "parent/subject",
        ),
        (
            checker.BASE,
            checker.FORMAL_COMMIT_SUBJECT,
            tuple(path.as_posix() for path in checker.EXACT10) + ("extra.txt",),
            False,
            "Exact10",
        ),
        (
            checker.BASE,
            checker.FORMAL_COMMIT_SUBJECT,
            tuple(path.as_posix() for path in checker.EXACT10[:-1]),
            False,
            "Exact10",
        ),
        (
            checker.BASE,
            checker.FORMAL_COMMIT_SUBJECT,
            tuple(path.as_posix() for path in checker.EXACT10),
            True,
            "modes",
        ),
    ),
)
def test_formal_candidate_commit_negative_cases(
    monkeypatch, parent, subject, paths, wrong_mode, message
):
    def fake_git(*arguments, **kwargs):
        if arguments[:3] == ("show", "-s", "--format=%P"):
            return f"{parent}\n".encode()
        if arguments[:3] == ("show", "-s", "--format=%s"):
            return f"{subject}\n".encode()
        if arguments[0] == "diff-tree":
            return b"\0".join(path.encode() for path in paths) + b"\0"
        if arguments[0] == "ls-tree":
            lines = []
            for position, path in enumerate(checker.EXACT10):
                mode = "100755" if wrong_mode and position == 0 else "100644"
                lines.append(
                    f"{mode} blob {'0' * 40}\t{path.as_posix()}\n".encode()
                )
            return b"".join(lines)
        raise AssertionError(arguments)

    monkeypatch.setattr(checker, "_git", fake_git)
    with pytest.raises(ValueError, match=message):
        checker._assert_candidate_commit("candidate")


@pytest.mark.parametrize("field", ("refs", "branch", "worktrees", "lifecycle"))
def test_first_final_ref_branch_worktree_and_lifecycle_drift_rejected(field):
    current = checker._recursive_lifecycle()
    replacement_lifecycle = next(
        mode
        for mode in checker.LIFECYCLE_MODES
        if mode != current.lifecycle
    )
    assert replacement_lifecycle != current.lifecycle

    replacements = {
        "refs": current.refs[:-1],
        "branch": "detached",
        "worktrees": (),
        "lifecycle": replacement_lifecycle,
    }
    final = current._replace(**{field: replacements[field]})
    assert final != current

    with pytest.raises(ValueError, match="lifecycle drift"):
        checker._assert_lifecycle_stable(current, final)


def test_real_local_formal_main_unpushed_and_pushed_lifecycles(tmp_path):
    bare = _initialize_local_remote(tmp_path)
    clone = tmp_path / "formal-main"
    _run_git(tmp_path, "clone", str(bare), str(clone))
    _copy_exact10(clone)
    _run_local_checker(clone, "pre_commit")
    candidate = _commit_exact10(clone)
    assert _run_git(clone, "show", "-s", "--format=%P", candidate).decode().strip() == (
        checker.BASE
    )
    first_unpushed = _run_local_checker(
        clone, "formal_main_post_commit_unpushed"
    )
    second_unpushed = _run_local_checker(
        clone, "formal_main_post_commit_unpushed"
    )
    assert first_unpushed == second_unpushed
    _run_git(clone, "push", "origin", "main")
    assert _run_git(clone, "rev-parse", "origin/main").decode().strip() == candidate
    first_pushed = _run_local_checker(clone, "formal_main_post_push")
    second_pushed = _run_local_checker(clone, "formal_main_post_push")
    assert first_pushed == second_pushed


def test_real_local_detached_candidate_post_commit_lifecycle(tmp_path):
    bare = _initialize_local_remote(tmp_path)
    clone = tmp_path / "main"
    candidate_root = tmp_path / "candidate"
    _run_git(tmp_path, "clone", str(bare), str(clone))
    _run_git(
        clone,
        "worktree",
        "add",
        "--detach",
        str(candidate_root),
        checker.BASE,
    )
    _copy_exact10(candidate_root)
    candidate = _commit_exact10(candidate_root)
    assert _run_git(
        candidate_root, "show", "-s", "--format=%s", candidate
    ).decode().strip() == checker.FORMAL_COMMIT_SUBJECT
    first = _run_local_checker(
        candidate_root, "detached_candidate_post_commit"
    )
    second = _run_local_checker(
        candidate_root, "detached_candidate_post_commit"
    )
    assert first == second


def test_exact10_inventory_and_modes():
    assert len(design.EXACT10) == 10
    for path in design.EXACT10:
        item = os.lstat(ROOT / path)
        assert stat.S_ISREG(item.st_mode)
        assert not stat.S_ISLNK(item.st_mode)


def test_no_protected_source_or_training_diff():
    protected = (
        "equivariant_diffusion",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
        "checkpoints",
    )
    changed = checker._git("diff", "--name-only").decode().splitlines()
    assert not any(
        path == prefix or path.startswith(f"{prefix}/")
        for path in changed
        for prefix in protected
    )


def test_no_forbidden_suffix_or_tmp_part():
    forbidden = (
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    )
    assert not any(path.name.endswith(forbidden) for path in design.EXACT10)


def test_raw_historical_baseline_exact53_and_untouched():
    tracked = [
        item
        for item in checker._git("ls-files", "-z", "--", "data/raw").split(b"\0")
        if item
    ]
    assert len(tracked) == 53
    assert checker._git("diff", "--name-only", "--", "data/raw") == b""
    assert checker._git("diff", "--cached", "--name-only", "--", "data/raw") == b""

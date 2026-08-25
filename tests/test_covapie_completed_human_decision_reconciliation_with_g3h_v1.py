from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_g3h_v1 as subject,
)


FORMAL = REPO.parent / subject._G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
ERROR = subject.CompletedDecisionReconciliationWithG3HError
GENERIC_ERROR = predecessor.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_decision_reconciliation_with_g3h_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_g3h_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _formal() -> dict[str, object]:
    return json.loads(FORMAL.read_bytes())


def _real_g3h_binding() -> predecessor.SourceBinding:
    return predecessor.SourceBinding(
        source_path=(
            subject._G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=subject._G3H_FORMAL_DECISION_BYTE_COUNT,
        sha256=subject._G3H_FORMAL_DECISION_SHA256,
        schema_version=subject._G3H_FORMAL_DECISION_SCHEMA,
        review_unit_id=subject._G3H_REVIEW_UNIT_ID,
    )


def _project_mapping(
    formal: dict[str, object],
) -> predecessor.NormalizedDecisionSource:
    return subject._project_g3h_decision_mapping_v1(formal, _real_g3h_binding())


def _synthetic_row(
    event_id: str,
    unit_id: str,
    *,
    status: str = predecessor.CURRENTLY_UNREVIEWED,
) -> dict[str, str]:
    eligible = status == predecessor.CURRENTLY_UNREVIEWED
    return {
        "raw_priority_rank": "1",
        "raw_review_unit_id": unit_id,
        "raw_unit_event_count": "1",
        "canonical_event_id": event_id,
        "current_review_status": status,
        "current_status_authority_sources_json": (
            '["synthetic/historical_reconciliation.csv"]'
        ),
        "calibration_eligible": str(eligible).lower(),
        "calibration_exclusion_reason": "" if eligible else status,
    }


def _synthetic_source(
    path: str,
    unit_id: str,
    event_id: str,
) -> predecessor.NormalizedDecisionSource:
    payload = (path + unit_id).encode("utf-8")
    binding = predecessor.SourceBinding(
        source_path=path,
        path_namespace="synthetic",
        byte_count=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        schema_version="synthetic_completed_decision_v1",
        review_unit_id=unit_id,
    )
    fact = predecessor.NormalizedCompletedDecisionFact(
        canonical_event_id=event_id,
        review_unit_id=unit_id,
        human_review_completed=True,
        legacy_completed_review_status=predecessor.COMPLETED_HUMAN_POSITIVE,
        task_relevance_disposition=predecessor.TASK_RELEVANT,
        chemistry_disposition=predecessor.CHEMISTRY_POSITIVE,
        training_disposition=predecessor.TRAINING_INCLUDE,
        human_training_excluded=False,
        source_decision_schema=binding.schema_version,
        source_decision_sha256=binding.sha256,
        source_binding_path=binding.source_path,
    )
    return predecessor.NormalizedDecisionSource(binding=binding, facts=(fact,))


def test_happy_path_real_g3h_projection_exact8() -> None:
    payload = FORMAL.read_bytes()
    source = subject.project_g3h_formal_decision_v1(payload)
    assert len(payload) == subject._G3H_FORMAL_DECISION_BYTE_COUNT == 22456
    assert hashlib.sha256(payload).hexdigest() == (
        subject._G3H_FORMAL_DECISION_SHA256
    )
    assert type(source) is predecessor.NormalizedDecisionSource
    assert type(source.binding) is predecessor.SourceBinding
    assert len(source.facts) == 8
    assert tuple(fact.canonical_event_id for fact in source.facts) == (
        subject._G3H_EVENT_IDS
    )
    assert all(
        type(fact) is predecessor.NormalizedCompletedDecisionFact
        and fact.human_review_completed is True
        and fact.legacy_completed_review_status
        == predecessor.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == predecessor.TASK_RELEVANT
        and fact.chemistry_disposition == predecessor.CHEMISTRY_POSITIVE
        and fact.training_disposition == predecessor.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._G3H_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._G3H_FORMAL_DECISION_SHA256
        and fact.source_binding_path
        == subject._G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in source.facts
    )


def test_formal_byte_count_mutation_fails_closed() -> None:
    with pytest.raises(ERROR, match="G3H_SOURCE_BYTE_COUNT_MISMATCH"):
        subject.project_g3h_formal_decision_v1(FORMAL.read_bytes() + b" ")


def test_formal_sha_mutation_fails_closed() -> None:
    payload = bytearray(FORMAL.read_bytes())
    payload[1] = ord("!")
    with pytest.raises(ERROR, match="G3H_SOURCE_SHA256_MISMATCH"):
        subject.project_g3h_formal_decision_v1(bytes(payload))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("schema_version", "wrong_schema"),
        ("decision_status", "PENDING"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
        ("pdb_id", "4I3V"),
        ("ligand_component_id", "OTHER"),
        ("exact_event_count", 7),
        ("human_review_completed", False),
        ("human_decision_created", False),
        ("human_review_decision_created", False),
        ("human_approval_recorded", False),
        ("formal_authority_created", False),
    ),
)
def test_formal_identity_mutation_fails_closed(field: str, value: object) -> None:
    formal = _formal()
    formal[field] = value
    with pytest.raises(ERROR, match="G3H_FORMAL_DECISION_IDENTITY_INVALID"):
        _project_mapping(formal)


def test_human_approval_false_fails_closed() -> None:
    formal = _formal()
    formal["human_approval"]["approval_recorded"] = False
    with pytest.raises(ERROR, match="G3H_HUMAN_APPROVAL_INVALID"):
        _project_mapping(formal)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("exact_event_count", 7),
        ("completed_human_review_event_count", 7),
        ("task_relevance_decision", "NOT_RELEVANT"),
        ("task_relevant_event_count", 7),
        ("chemistry_support_disposition", "NEGATIVE"),
        ("chemistry_positive_event_count", 7),
        ("chemistry_negative_event_count", 1),
        ("negative_chemistry", True),
        ("task_domain_negative", True),
        ("human_training_excluded_positive_event_count", 7),
        ("training_admission_created", True),
        ("training_dataset_changed", True),
    ),
)
def test_unit_decision_mutation_fails_closed(field: str, value: object) -> None:
    formal = _formal()
    formal["unit_level_human_decisions"][field] = value
    with pytest.raises(ERROR, match="G3H_UNIT_DECISION_INVALID"):
        _project_mapping(formal)


def test_missing_event_fails_closed() -> None:
    formal = _formal()
    formal["event_level_human_decisions"].pop()
    with pytest.raises(ERROR, match="G3H_EXACT8_EVENT_COUNT_INVALID"):
        _project_mapping(formal)


def test_duplicate_event_fails_closed() -> None:
    formal = _formal()
    formal["event_level_human_decisions"][-1] = deepcopy(
        formal["event_level_human_decisions"][0]
    )
    with pytest.raises(ERROR, match="G3H_EVENT_ID_DUPLICATE"):
        _project_mapping(formal)


def test_unexpected_ninth_event_fails_closed() -> None:
    formal = _formal()
    ninth = deepcopy(formal["event_level_human_decisions"][-1])
    ninth["canonical_event_id"] = "COVAPIE_CYS_SG_EVENT_V1:4I3W:I:UNEXPECTED"
    formal["event_level_human_decisions"].append(ninth)
    with pytest.raises(ERROR, match="G3H_EXACT8_EVENT_COUNT_INVALID"):
        _project_mapping(formal)


def test_one_canonical_event_id_mutation_fails_closed() -> None:
    formal = _formal()
    formal["event_level_human_decisions"][0]["canonical_event_id"] += ":MUTATED"
    with pytest.raises(ERROR, match="G3H_EVENT_ID_UNEXPECTED"):
        _project_mapping(formal)


@pytest.mark.parametrize(
    ("field", "value", "error_token"),
    (
        (
            "human_task_relevance_decision",
            "NOT_RELEVANT",
            "G3H_EVENT_TASK_RELEVANCE_INVALID",
        ),
        (
            "human_chemistry_support_disposition",
            "NEGATIVE",
            "G3H_EVENT_CHEMISTRY_DISPOSITION_INVALID",
        ),
        (
            "negative_chemistry",
            True,
            "G3H_EVENT_CHEMISTRY_DISPOSITION_INVALID",
        ),
        (
            "task_domain_negative",
            True,
            "G3H_EVENT_CHEMISTRY_DISPOSITION_INVALID",
        ),
        (
            "human_event_training_use_disposition",
            "INCLUDE",
            "G3H_EVENT_TRAINING_DISPOSITION_INVALID",
        ),
        (
            "human_training_excluded",
            False,
            "G3H_EVENT_TRAINING_DISPOSITION_INVALID",
        ),
        (
            "training_admitted",
            True,
            "G3H_EVENT_TRAINING_DISPOSITION_INVALID",
        ),
        (
            "decision_finalized",
            False,
            "G3H_EVENT_DECISION_NOT_FINALIZED",
        ),
    ),
)
def test_event_semantic_mutation_fails_closed(
    field: str, value: object, error_token: str
) -> None:
    formal = _formal()
    formal["event_level_human_decisions"][0][field] = value
    with pytest.raises(ERROR, match=error_token):
        _project_mapping(formal)


def test_real_exact3_source_composition() -> None:
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(REPO)
    assert len(sources) == 3
    assert tuple(len(source.facts) for source in sources) == (8, 16, 8)
    assert tuple(source.binding.schema_version for source in sources) == (
        predecessor.FFQ_FORMAL_DECISION_SCHEMA,
        predecessor.POA_FORMAL_DECISION_SCHEMA,
        subject._G3H_FORMAL_DECISION_SCHEMA,
    )
    assert len({source.binding.review_unit_id for source in sources}) == 3
    assert len({source.binding.stable_identity for source in sources}) == 3


def test_real_reconciliation_counts_and_training_dispositions() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_g3h_v1(REPO)
    assert type(result) is predecessor.ReconciliationResult
    assert len(result.reconciled_rows) == 338
    assert len(result.source_bindings) == 3
    assert len(result.normalized_facts) == 32
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 32,
        "completed_positive_unit_count": 3,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 56,
        "completed_total_unit_count": 7,
        "in_progress_event_count": 9,
        "in_progress_unit_count": 1,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
    }
    assert 273 + 9 == 282
    assert 32 + 24 == 56
    assert 56 + 282 == 338
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        predecessor.TRAINING_INCLUDE: 12,
        predecessor.TRAINING_EXCLUDE: 20,
    }


def test_g3h_rows_move_from_unreviewed_to_positive_with_exact_authority() -> None:
    historical = predecessor.load_real_historical_reconciliation_v1(REPO)
    result = subject.reconcile_real_completed_human_decisions_with_g3h_v1(REPO)
    old_by_id = {row["canonical_event_id"]: row for row in historical}
    new_by_id = {row["canonical_event_id"]: row for row in result.reconciled_rows}
    expected_authority = json.dumps(
        [subject._G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()],
        separators=(",", ":"),
    )
    for event_id in subject._G3H_EVENT_IDS:
        assert old_by_id[event_id]["current_review_status"] == (
            predecessor.CURRENTLY_UNREVIEWED
        )
        assert new_by_id[event_id]["current_review_status"] == (
            predecessor.COMPLETED_HUMAN_POSITIVE
        )
        assert new_by_id[event_id]["current_status_authority_sources_json"] == (
            expected_authority
        )
        assert new_by_id[event_id]["calibration_eligible"] == "false"
        assert new_by_id[event_id]["calibration_exclusion_reason"] == (
            predecessor.COMPLETED_HUMAN_POSITIVE
        )


def test_g3h_delta_is_positive_plus8_pending_minus8_and_exclude_plus8() -> None:
    before = predecessor.reconcile_real_completed_human_decisions_v1(REPO)
    after = subject.reconcile_real_completed_human_decisions_with_g3h_v1(REPO)
    before_pending = (
        before.review_summary["unreviewed_event_count"]
        + before.review_summary["in_progress_event_count"]
    )
    after_pending = (
        after.review_summary["unreviewed_event_count"]
        + after.review_summary["in_progress_event_count"]
    )
    assert (
        after.review_summary["completed_positive_event_count"]
        - before.review_summary["completed_positive_event_count"]
        == 8
    )
    assert after_pending - before_pending == -8
    before_training = Counter(
        fact.training_disposition for fact in before.normalized_facts
    )
    after_training = Counter(
        fact.training_disposition for fact in after.normalized_facts
    )
    assert after_training[predecessor.TRAINING_EXCLUDE] - before_training[
        predecessor.TRAINING_EXCLUDE
    ] == 8
    assert after_training[predecessor.TRAINING_INCLUDE] - before_training[
        predecessor.TRAINING_INCLUDE
    ] == 0


def test_reconciliation_is_deterministic_and_source_order_independent() -> None:
    historical = predecessor.load_real_historical_reconciliation_v1(REPO)
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(REPO)
    first = predecessor.reconcile_completed_human_decisions_v1(historical, sources)
    second = predecessor.reconcile_completed_human_decisions_v1(
        historical, tuple(reversed(sources))
    )
    third = subject.reconcile_real_completed_human_decisions_with_g3h_v1(REPO)
    assert first == second == third


def test_cross_source_collision_continues_to_fail_in_predecessor() -> None:
    event_id = "SYNTHETIC_EVENT"
    unit_id = "SYNTHETIC_UNIT"
    rows = (_synthetic_row(event_id, unit_id),)
    first = _synthetic_source("synthetic/first.json", unit_id, event_id)
    second = _synthetic_source("synthetic/second.json", unit_id, event_id)
    with pytest.raises(GENERIC_ERROR, match="CROSS_SOURCE_EVENT_COLLISION"):
        predecessor.reconcile_completed_human_decisions_v1(rows, (first, second))


def test_incomplete_review_unit_coverage_continues_to_fail() -> None:
    historical = predecessor.load_real_historical_reconciliation_v1(REPO)
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(REPO)
    incomplete_g3h = replace(sources[-1], facts=sources[-1].facts[:-1])
    with pytest.raises(
        GENERIC_ERROR,
        match="SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH",
    ):
        predecessor.reconcile_completed_human_decisions_v1(
            historical, (*sources[:-1], incomplete_g3h)
        )


def test_prior_historical_status_not_unreviewed_continues_to_fail() -> None:
    rows = [
        dict(row) for row in predecessor.load_real_historical_reconciliation_v1(REPO)
    ]
    for row in rows:
        if row["raw_review_unit_id"] == subject._G3H_REVIEW_UNIT_ID:
            row["current_review_status"] = predecessor.CURRENTLY_IN_PROGRESS
            row["calibration_eligible"] = "false"
            row["calibration_exclusion_reason"] = predecessor.CURRENTLY_IN_PROGRESS
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(REPO)
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        predecessor.reconcile_completed_human_decisions_v1(rows, sources)


def test_duplicate_source_binding_continues_to_fail() -> None:
    historical = predecessor.load_real_historical_reconciliation_v1(REPO)
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(REPO)
    with pytest.raises(GENERIC_ERROR, match="SOURCE_BINDING_DUPLICATE"):
        predecessor.reconcile_completed_human_decisions_v1(
            historical, (*sources, sources[-1])
        )


def test_checker_runs_real_projector_loader_runner_and_exact4() -> None:
    result = checker.run_check_v1(REPO)
    assert result["candidate_file_count"] == 4
    assert result["source_binding_count"] == 3
    assert result["normalized_fact_count"] == 32
    assert result["g3h_prior_unreviewed_count"] == 8
    assert result["g3h_reconciled_positive_count"] == 8
    assert result["current_global_reconciliation_g3h_gap_closed"] is True
    assert result["current_global_readiness_census_complete"] is False
    assert result["training_admitted_count_created"] == 0
    assert result["model_work_performed"] is False


def test_checker_frozen_source_mismatch_fails_closed(tmp_path: Path) -> None:
    altered = tmp_path / "altered_source.py"
    altered.write_bytes(b"x\n")
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_file(
            altered,
            label="ALTERED_SOURCE",
            expected_byte_count=2,
            expected_sha256="0" * 64,
        )

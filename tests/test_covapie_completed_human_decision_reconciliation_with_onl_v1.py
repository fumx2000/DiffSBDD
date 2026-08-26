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
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_g3h_v1 as g3h_successor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_onl_v1 as subject,
)
from covalent_ext import (
    covapie_onl_completed_decision_ingestion_and_task_label_availability_v1
    as onl_ingestion_owner,
)


ERROR = subject.CompletedDecisionReconciliationWithONLError
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_onl_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_onl_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _historical() -> list[dict[str, str]]:
    return [
        dict(row) for row in generic.load_real_historical_reconciliation_v1(REPO)
    ]


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def _synthetic_row(event_id: str, unit_id: str) -> dict[str, str]:
    return {
        "raw_priority_rank": "1",
        "raw_review_unit_id": unit_id,
        "raw_unit_event_count": "1",
        "canonical_event_id": event_id,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "current_status_authority_sources_json": '["synthetic/history.csv"]',
        "calibration_eligible": "true",
        "calibration_exclusion_reason": "",
    }


def _synthetic_source(
    path: str, unit_id: str, event_id: str
) -> generic.NormalizedDecisionSource:
    payload = (path + unit_id).encode("utf-8")
    binding = generic.SourceBinding(
        source_path=path,
        path_namespace="synthetic",
        byte_count=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        schema_version="synthetic_completed_decision_v1",
        review_unit_id=unit_id,
    )
    fact = generic.NormalizedCompletedDecisionFact(
        canonical_event_id=event_id,
        review_unit_id=unit_id,
        human_review_completed=True,
        legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
        task_relevance_disposition=generic.TASK_RELEVANT,
        chemistry_disposition=generic.CHEMISTRY_POSITIVE,
        training_disposition=generic.TRAINING_INCLUDE,
        human_training_excluded=False,
        source_decision_schema=binding.schema_version,
        source_decision_sha256=binding.sha256,
        source_binding_path=binding.source_path,
    )
    return generic.NormalizedDecisionSource(binding=binding, facts=(fact,))


def test_public_api_is_minimal_and_adapter_is_private() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithONLError",
        "project_onl_completed_decision_v1",
        "load_real_completed_decision_sources_with_onl_v1",
        "reconcile_real_completed_human_decisions_with_onl_v1",
    )
    assert (
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
        not in subject.__all__
    )


def test_onl_projector_reuses_ingestion_owner_and_generic_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = onl_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.onl_ingestion_owner,
        "load_frozen_formal_decision_v1",
        wrapped,
    )
    source = subject.project_onl_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert len(source.facts) == 9
    assert tuple(fact.canonical_event_id for fact in source.facts) == (
        subject._ONL_EVENT_IDS
    )
    assert all(type(fact) is generic.NormalizedCompletedDecisionFact for fact in source.facts)


def test_onl_projection_exact9_semantics_and_formal_binding() -> None:
    source = subject.project_onl_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            subject._ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=28678,
        sha256="eb68b63046b561e857ae84640843914960c974ce7807be1ee18aba3f107581d5",
        schema_version="covapie_onl_exact9_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74",
    )
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status
        == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._ONL_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._ONL_FORMAL_DECISION_SHA256
        and fact.source_binding_path
        == subject._ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in source.facts
    )


def test_projector_does_not_use_role_pair_or_geometry_as_disposition() -> None:
    bound = onl_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    expected = subject._project_validated_onl_binding_v1(bound)
    altered = deepcopy(bound)
    altered["normalized"]["role"] = {"ignored": "changed"}
    for event in altered["normalized"]["events"]:
        event["D3_human_reactive_pair_decision"] = "IGNORED_PAIR_CHANGE"
        event["D4_human_role_partition_choice"] = "IGNORED_ROLE_CHANGE"
        event["POST_distance_angstrom"] = -999.0
        event["PRE_geometry_authority_available"] = True
    assert subject._project_validated_onl_binding_v1(altered) == expected


def test_projector_rejects_bound_identity_drift() -> None:
    bound = onl_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["formal_decision_binding"]["sha256"] = "0" * 64
    with pytest.raises(ERROR, match="ONL_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_onl_binding_v1(bound)


def test_projector_rejects_decision_semantics_drift() -> None:
    bound = onl_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["normalized"]["events"][0][
        "D5_human_training_use_disposition"
    ] = generic.TRAINING_INCLUDE
    with pytest.raises(ERROR, match="ONL_NORMALIZED_EVENT_DECISION_INVALID"):
        subject._project_validated_onl_binding_v1(bound)


def test_real_prior_is_exact9_in_progress_and_exact1_unit() -> None:
    rows = _historical()
    onl = [
        row
        for row in rows
        if row["canonical_event_id"] in set(subject._ONL_EVENT_IDS)
    ]
    in_progress = [
        row
        for row in rows
        if row["current_review_status"] == generic.CURRENTLY_IN_PROGRESS
    ]
    assert len(rows) == 338
    assert len({row["raw_review_unit_id"] for row in rows}) == 131
    assert len(onl) == len(in_progress) == 9
    assert {row["canonical_event_id"] for row in in_progress} == set(
        subject._ONL_EVENT_IDS
    )
    assert {row["raw_review_unit_id"] for row in in_progress} == {
        subject._ONL_REVIEW_UNIT_ID
    }
    assert all(
        row["current_review_status"] == generic.CURRENTLY_IN_PROGRESS
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"]
        == generic.CURRENTLY_IN_PROGRESS
        for row in onl
    )


def test_original_generic_direct_call_remains_fail_closed() -> None:
    historical = generic.load_real_historical_reconciliation_v1(REPO)
    sources = subject.load_real_completed_decision_sources_with_onl_v1(REPO)
    with pytest.raises(
        GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"
    ):
        generic.reconcile_completed_human_decisions_v1(historical, sources)


def test_adapter_is_exact9_private_copy_and_preserves_all_other_fields() -> None:
    original = generic.load_real_historical_reconciliation_v1(REPO)
    original_snapshot = deepcopy(original)
    adapted = subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        original
    )
    assert original == original_snapshot
    assert adapted is not original
    assert all(after is not before for before, after in zip(original, adapted, strict=True))
    changed_events: set[str] = set()
    for before, after in zip(original, adapted, strict=True):
        changed = {key for key in before if before[key] != after[key]}
        event_id = before["canonical_event_id"]
        if event_id in set(subject._ONL_EVENT_IDS):
            changed_events.add(event_id)
            assert changed == subject._ALLOWED_TRANSITION_FIELDS
            assert after["current_review_status"] == generic.CURRENTLY_UNREVIEWED
            assert after["calibration_eligible"] == "true"
            assert after["calibration_exclusion_reason"] == ""
            assert after["raw_priority_rank"] == before["raw_priority_rank"]
            assert after["raw_review_unit_id"] == before["raw_review_unit_id"]
            assert after["raw_unit_event_count"] == before["raw_unit_event_count"]
            assert after["canonical_event_id"] == before["canonical_event_id"]
            assert after["current_status_authority_sources_json"] == before[
                "current_status_authority_sources_json"
            ]
        else:
            assert changed == set()
    assert changed_events == set(subject._ONL_EVENT_IDS)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_UNREVIEWED, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_adapter_rejects_one_onl_prior_not_in_progress(status: str) -> None:
    rows = _historical()
    target = next(
        row for row in rows if row["canonical_event_id"] == subject._ONL_EVENT_IDS[0]
    )
    _set_status(target, status)
    with pytest.raises(ERROR, match="ONL_PRIOR_STATE_NOT_EXACT9_IN_PROGRESS"):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_adapter_rejects_one_missing_onl_event() -> None:
    rows = _historical()
    rows = [
        row
        for row in rows
        if row["canonical_event_id"] != subject._ONL_EVENT_IDS[0]
    ]
    with pytest.raises(ERROR, match="ONL_HISTORICAL_EVENT_MISSING"):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_adapter_rejects_duplicate_onl_event() -> None:
    rows = _historical()
    target = next(
        row for row in rows if row["canonical_event_id"] == subject._ONL_EVENT_IDS[0]
    )
    rows.append(dict(target))
    with pytest.raises(ERROR, match="ONL_HISTORICAL_EVENT_DUPLICATE"):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_adapter_rejects_extra_event_in_onl_review_unit() -> None:
    rows = _historical()
    extra = next(
        row
        for row in rows
        if row["raw_review_unit_id"] != subject._ONL_REVIEW_UNIT_ID
    )
    extra["raw_review_unit_id"] = subject._ONL_REVIEW_UNIT_ID
    with pytest.raises(ERROR, match="ONL_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT9"):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_adapter_rejects_onl_review_unit_id_drift() -> None:
    rows = _historical()
    target = next(
        row for row in rows if row["canonical_event_id"] == subject._ONL_EVENT_IDS[0]
    )
    target["raw_review_unit_id"] = "DRIFTED_ONL_REVIEW_UNIT"
    with pytest.raises(ERROR):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_adapter_rejects_non_onl_in_progress_event_and_wrong_global_count() -> None:
    rows = _historical()
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] not in set(subject._ONL_EVENT_IDS)
        and row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
    )
    _set_status(target, generic.CURRENTLY_IN_PROGRESS)
    with pytest.raises(
        ERROR, match="HISTORICAL_IN_PROGRESS_EVENT_COUNT_NOT_EXACT9"
    ):
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(rows)


def test_exact4_source_composition_is_collision_free() -> None:
    sources = subject.load_real_completed_decision_sources_with_onl_v1(REPO)
    assert [len(source.facts) for source in sources] == [8, 16, 8, 9]
    assert len({source.binding.review_unit_id for source in sources}) == 4
    assert len({source.binding.stable_identity for source in sources}) == 4
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    assert len(event_ids) == len(set(event_ids)) == 41


def test_real_successor_reconciliation_counts_training_and_onl_delta() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_onl_v1(REPO)
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 41,
        "completed_positive_unit_count": 4,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 65,
        "completed_total_unit_count": 8,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
    }
    assert len(result.source_bindings) == 4
    assert len(result.normalized_facts) == 41
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 12,
        generic.TRAINING_EXCLUDE: 29,
    }
    prior = g3h_successor.reconcile_real_completed_human_decisions_with_g3h_v1(
        REPO
    )
    assert (
        result.review_summary["completed_positive_event_count"]
        - prior.review_summary["completed_positive_event_count"]
        == 9
    )
    assert (
        result.review_summary["in_progress_event_count"]
        - prior.review_summary["in_progress_event_count"]
        == -9
    )
    result_pending = (
        result.review_summary["unreviewed_event_count"]
        + result.review_summary["in_progress_event_count"]
    )
    prior_pending = (
        prior.review_summary["unreviewed_event_count"]
        + prior.review_summary["in_progress_event_count"]
    )
    assert result_pending == 273
    assert result_pending - prior_pending == -9


def test_final_onl_rows_have_only_formal_authority_and_no_temporary_state() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_onl_v1(REPO)
    onl_path = subject._ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
    onl_rows = [
        row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in set(subject._ONL_EVENT_IDS)
    ]
    assert len(onl_rows) == 9
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and json.loads(row["current_status_authority_sources_json"]) == [onl_path]
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"]
        == generic.COMPLETED_HUMAN_POSITIVE
        for row in onl_rows
    )


def test_source_order_determinism_on_adapted_historical() -> None:
    historical = generic.load_real_historical_reconciliation_v1(REPO)
    adapted = subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    sources = subject.load_real_completed_decision_sources_with_onl_v1(REPO)
    normal = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_order = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    assert normal == reversed_order


def test_cross_source_collision_protection_remains_fail_closed() -> None:
    rows = (_synthetic_row("event-1", "unit-1"),)
    first = _synthetic_source("synthetic/first.json", "unit-1", "event-1")
    second = _synthetic_source("synthetic/second.json", "unit-1", "event-1")
    with pytest.raises(GENERIC_ERROR, match="CROSS_SOURCE_EVENT_COLLISION"):
        generic.reconcile_completed_human_decisions_v1(rows, (first, second))


def test_duplicate_source_binding_protection_remains_fail_closed() -> None:
    rows = (_synthetic_row("event-1", "unit-1"),)
    source = _synthetic_source("synthetic/source.json", "unit-1", "event-1")
    with pytest.raises(GENERIC_ERROR, match="SOURCE_BINDING_DUPLICATE"):
        generic.reconcile_completed_human_decisions_v1(rows, (source, source))


def test_incomplete_review_unit_coverage_remains_fail_closed() -> None:
    historical = generic.load_real_historical_reconciliation_v1(REPO)
    adapted = subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    sources = subject.load_real_completed_decision_sources_with_onl_v1(REPO)
    incomplete_onl = replace(sources[-1], facts=sources[-1].facts[:-1])
    with pytest.raises(GENERIC_ERROR, match="SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH"):
        generic.reconcile_completed_human_decisions_v1(
            adapted, (*sources[:-1], incomplete_onl)
        )


def test_source_event_outside_historical_universe_remains_fail_closed() -> None:
    rows = (_synthetic_row("event-1", "unit-1"),)
    source = _synthetic_source("synthetic/source.json", "unit-1", "event-2")
    with pytest.raises(GENERIC_ERROR, match="EVENT_NOT_IN_HISTORICAL_UNIVERSE"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_source_historical_review_unit_mismatch_remains_fail_closed() -> None:
    rows = (_synthetic_row("event-1", "historical-unit"),)
    source = _synthetic_source("synthetic/source.json", "source-unit", "event-1")
    with pytest.raises(
        GENERIC_ERROR, match="FACT_HISTORICAL_REVIEW_UNIT_MISMATCH"
    ):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_checker_runs_real_projector_adapter_generic_and_runner() -> None:
    result = checker.run_check_v1(REPO)
    assert result["candidate_file_count"] == 4
    assert result["source_binding_count"] == 4
    assert result["normalized_fact_count"] == 41
    assert result["onl_prior_in_progress_event_count"] == 9
    assert result["original_generic_failure"] == (
        "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"
    )
    assert result["completed_positive_event_count"] == 41
    assert result["completed_negative_event_count"] == 24
    assert result["completed_total_event_count"] == 65
    assert result["pending_event_count"] == 273
    assert result["training_include_count"] == 12
    assert result["training_excluded_count"] == 29
    assert result["global_census_updated"] is False
    assert result["published_global_positive_count"] == 49
    assert result["expected_next_global_positive_count"] == 58
    assert result["ready_for_training"] is False


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

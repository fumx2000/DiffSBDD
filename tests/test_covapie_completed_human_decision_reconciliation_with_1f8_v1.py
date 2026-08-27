from __future__ import annotations

import ast
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

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_2vs_v1 as two_vs_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_1f8_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1
    as one_f8_ingestion_owner,
)


ERROR = subject.CompletedDecisionReconciliationWith1F8Error
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_1f8_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_1f8_v1.py",
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


def _adapted_historical() -> tuple[dict[str, str], ...]:
    return onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        generic.load_real_historical_reconciliation_v1(REPO)
    )


def _synthetic_row(event_id: str, unit_id: str, count: int = 1) -> dict[str, str]:
    return {
        "raw_priority_rank": "1",
        "raw_review_unit_id": unit_id,
        "raw_unit_event_count": str(count),
        "canonical_event_id": event_id,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "current_status_authority_sources_json": '["synthetic/history.csv"]',
        "calibration_eligible": "true",
        "calibration_exclusion_reason": "",
    }


def _synthetic_source(
    path: str,
    unit_id: str,
    event_ids: tuple[str, ...],
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
    facts = tuple(
        generic.NormalizedCompletedDecisionFact(
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
        for event_id in event_ids
    )
    return generic.NormalizedDecisionSource(binding=binding, facts=facts)


def test_public_api_is_minimal_and_1f8_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWith1F8Error",
        "project_1f8_completed_decision_v1",
        "load_real_completed_decision_sources_with_1f8_v1",
        "reconcile_real_completed_human_decisions_with_1f8_v1",
    )
    assert subject.ONE_F8_TRANSITION_ADAPTER_CREATED is False
    module_path = REPO / "src/covalent_ext" / Path(subject.__file__).name
    tree = ast.parse(module_path.read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_1f8")
        or ("1f8" in name.lower() and "transition" in name.lower())
        for name in function_names
    )
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Subscript)
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in ast.walk(tree)
    )
    called = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert called.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) == 1
    assert called.count("reconcile_completed_human_decisions_v1") == 1
    assert "reconcile_real_completed_human_decisions_with_2vs_v1" not in called


def test_1f8_projector_reuses_ingestion_owner_and_generic_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = one_f8_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.one_f8_ingestion_owner,
        "load_frozen_formal_decision_v1",
        wrapped,
    )
    source = subject.project_1f8_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert len(source.facts) == 8
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )


def test_1f8_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise one_f8_ingestion_owner.OneF8IngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.one_f8_ingestion_owner,
        "load_frozen_formal_decision_v1",
        fail,
    )
    with pytest.raises(ERROR, match="1F8_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_1f8_completed_decision_v1(repo_root=REPO)


def test_1f8_projection_exact8_semantics_and_formal_binding() -> None:
    source = subject.project_1f8_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            subject._1F8_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        path_namespace="repository_parent_relative",
        byte_count=31063,
        sha256="6a73022e20e2562f95197b9f314b92b0ecead1cebbadf1c17d5ca292eee59e96",
        schema_version="covapie_1f8_exact8_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == (
        subject._1F8_EVENT_IDS
    )
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status
        == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._1F8_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._1F8_FORMAL_DECISION_SHA256
        and fact.source_binding_path
        == subject._1F8_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in source.facts
    )


def test_projector_does_not_reinterpret_pair_role_post_pre_or_context() -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    expected = subject._project_validated_1f8_binding_v1(bound)
    altered = deepcopy(bound)
    altered["normalized"]["role"] = {"ignored": "changed"}
    altered["normalized"]["scientific_context"] = {"ignored": "changed"}
    altered["normalized"]["observed_graph_pre_boundary"] = {"ignored": "changed"}
    for event in altered["normalized"]["events"]:
        event["D3_human_reactive_pair_decision"] = "IGNORED_PAIR_CHANGE"
        event["D4_human_role_partition_choice"] = "IGNORED_ROLE_CHANGE"
        event["POST_distance_angstrom"] = -999.0
        event["PRE_geometry_authority_available"] = True
        event["ligand_reactive_atom"] = "IGNORED_SD"
        event["ligand_reactive_atom_element"] = "IGNORED_S"
    assert subject._project_validated_1f8_binding_v1(altered) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/1f8.json"),
        ("byte_count", 31064),
        ("sha256", "0" * 64),
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
    ),
)
def test_projector_rejects_formal_binding_drift(
    field: str, value: object
) -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["formal_decision_binding"][field] = value
    with pytest.raises(ERROR, match="1F8_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_1f8_binding_v1(bound)


@pytest.mark.parametrize("new_count", (7, 9))
def test_projector_rejects_exact8_count_drift(new_count: int) -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    events = bound["normalized"]["events"]
    if new_count == 7:
        events.pop()
    else:
        events.append(deepcopy(events[-1]))
    with pytest.raises(ERROR, match="1F8_NORMALIZED_EVENT_COUNT_NOT_EXACT8"):
        subject._project_validated_1f8_binding_v1(bound)


def test_projector_rejects_missing_and_extra_event_identity() -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["normalized"]["events"][-1]["canonical_event_id"] = (
        "COVAPIE_CYS_SG_EVENT_V1:EXTRA:1F8:SD"
    )
    with pytest.raises(ERROR, match="1F8_NORMALIZED_EVENT_COVERAGE_NOT_EXACT8"):
        subject._project_validated_1f8_binding_v1(bound)


def test_projector_rejects_duplicate_event() -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["normalized"]["events"][-1]["canonical_event_id"] = bound[
        "normalized"
    ]["events"][0]["canonical_event_id"]
    with pytest.raises(ERROR, match="1F8_NORMALIZED_EVENT_ID_DUPLICATE"):
        subject._project_validated_1f8_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("D1_human_task_relevance_decision", "NOT_RELEVANT"),
        ("D2_human_chemistry_support_disposition", "NEGATIVE"),
        ("D5_human_training_use_disposition", "INCLUDE"),
        ("human_training_excluded", False),
        ("training_admitted", True),
        ("decision_finalized", False),
    ),
)
def test_projector_rejects_completed_decision_semantics_drift(
    field: str, value: object
) -> None:
    bound = one_f8_ingestion_owner.load_frozen_formal_decision_v1(REPO)
    bound["normalized"]["events"][0][field] = value
    with pytest.raises(ERROR, match="1F8_NORMALIZED_EVENT_DECISION_INVALID"):
        subject._project_validated_1f8_binding_v1(bound)


def test_original_historical_1f8_prior_is_exact8_unreviewed() -> None:
    rows = _historical()
    subject._prove_1f8_original_unreviewed_prior_v1(rows)
    one_f8_rows = [
        row
        for row in rows
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS)
    ]
    assert len(one_f8_rows) == 8
    assert {row["raw_review_unit_id"] for row in one_f8_rows} == {
        subject._1F8_REVIEW_UNIT_ID
    }
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in one_f8_rows
    )


def test_historical_proof_rejects_one_missing_1f8_event() -> None:
    rows = [
        row
        for row in _historical()
        if row["canonical_event_id"] != subject._1F8_EVENT_IDS[0]
    ]
    with pytest.raises(ERROR, match="1F8_HISTORICAL_EVENT_MISSING"):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_duplicate_1f8_event() -> None:
    rows = _historical()
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._1F8_EVENT_IDS[0]
    )
    rows.append(dict(target))
    with pytest.raises(ERROR, match="1F8_HISTORICAL_EVENT_DUPLICATE"):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_1f8_review_unit_drift() -> None:
    rows = _historical()
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._1F8_EVENT_IDS[0]
    )
    target["raw_review_unit_id"] = "DRIFTED_1F8_REVIEW_UNIT"
    with pytest.raises(ERROR, match="1F8_HISTORICAL_REVIEW_UNIT"):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_extra_event_in_1f8_unit() -> None:
    rows = _historical()
    extra = next(
        row
        for row in rows
        if row["raw_review_unit_id"] != subject._1F8_REVIEW_UNIT_ID
    )
    extra["raw_review_unit_id"] = subject._1F8_REVIEW_UNIT_ID
    with pytest.raises(
        ERROR, match="1F8_HISTORICAL_REVIEW_UNIT_EVENT_SET_NOT_EXACT8"
    ):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_one_non_unreviewed_1f8_prior(
    status: str,
) -> None:
    rows = _historical()
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == subject._1F8_EVENT_IDS[0]
    )
    _set_status(target, status)
    with pytest.raises(ERROR, match="1F8_PRIOR_STATE_NOT_EXACT8_UNREVIEWED"):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_whole_non_unreviewed_1f8_unit(
    status: str,
) -> None:
    rows = _historical()
    for row in rows:
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS):
            _set_status(row, status)
    with pytest.raises(ERROR, match="1F8_PRIOR_STATE_NOT_EXACT8_UNREVIEWED"):
        subject._prove_1f8_original_unreviewed_prior_v1(rows)


def test_onl_adapter_leaves_all_1f8_rows_field_equal() -> None:
    original = generic.load_real_historical_reconciliation_v1(REPO)
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        original
    )
    subject._prove_1f8_rows_unchanged_after_onl_normalization_v1(
        original, adapted
    )
    before = {
        row["canonical_event_id"]: row
        for row in original
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS)
    }
    after = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS)
    }
    assert before == after


def test_1f8_unchanged_proof_rejects_unexpected_onl_adapter_change() -> None:
    original = generic.load_real_historical_reconciliation_v1(REPO)
    adapted = [
        dict(row)
        for row in onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            original
        )
    ]
    target = next(
        row
        for row in adapted
        if row["canonical_event_id"] == subject._1F8_EVENT_IDS[0]
    )
    target["current_status_authority_sources_json"] = '["unexpected/adapter"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_1F8_ROW"):
        subject._prove_1f8_rows_unchanged_after_onl_normalization_v1(
            original, adapted
        )


def test_1f8_needs_no_adapter_and_passes_unchanged_generic() -> None:
    adapted = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    result = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    assert result.review_summary["completed_positive_event_count"] == 65


def test_one_1f8_prior_drift_fails_at_unit_consistency_gate() -> None:
    adapted = [dict(row) for row in _adapted_historical()]
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    target = next(
        row
        for row in adapted
        if row["canonical_event_id"] == subject._1F8_EVENT_IDS[0]
    )
    _set_status(target, generic.CURRENTLY_IN_PROGRESS)
    with pytest.raises(GENERIC_ERROR, match="HISTORICAL_REVIEW_UNIT_STATUS_MIXED"):
        generic.reconcile_completed_human_decisions_v1(adapted, sources)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_1f8_unit_prior_drift_reaches_generic_prior_status_protection(
    status: str,
) -> None:
    adapted = [dict(row) for row in _adapted_historical()]
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    for row in adapted:
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS):
            _set_status(row, status)
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(adapted, sources)


def test_original_historical_with_all_seven_sources_still_fails_for_onl() -> None:
    historical = generic.load_real_historical_reconciliation_v1(REPO)
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED") as caught:
        generic.reconcile_completed_human_decisions_v1(historical, sources)
    assert any(event_id in str(caught.value) for event_id in onl_successor._ONL_EVENT_IDS)


def test_exact7_source_composition_is_collision_free() -> None:
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    assert [len(source.facts) for source in sources] == [8, 16, 8, 9, 8, 8, 8]
    assert len({source.binding.review_unit_id for source in sources}) == 7
    assert len({source.binding.stable_identity for source in sources}) == 7
    event_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    assert len(event_ids) == len(set(event_ids)) == 65


def test_source_loader_rejects_1f8_collision_with_previous57(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = two_vs_successor.load_real_completed_decision_sources_with_2vs_v1(
        REPO
    )
    source = subject.project_1f8_completed_decision_v1(repo_root=REPO)
    collision = replace(
        source.facts[0], canonical_event_id=existing[0].facts[0].canonical_event_id
    )
    altered = replace(source, facts=(collision, *source.facts[1:]))
    monkeypatch.setattr(
        subject, "project_1f8_completed_decision_v1", lambda *, repo_root: altered
    )
    with pytest.raises(ERROR, match="REAL_NORMALIZED_FACT_EVENT_COLLISION"):
        subject.load_real_completed_decision_sources_with_1f8_v1(REPO)


def test_source_loader_rejects_1f8_review_unit_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = subject.project_1f8_completed_decision_v1(repo_root=REPO)
    altered = replace(
        source,
        binding=replace(source.binding, review_unit_id="WRONG_REVIEW_UNIT"),
    )
    monkeypatch.setattr(
        subject, "project_1f8_completed_decision_v1", lambda *, repo_root: altered
    )
    with pytest.raises(ERROR, match="1F8_SOURCE_REVIEW_UNIT_MISMATCH"):
        subject.load_real_completed_decision_sources_with_1f8_v1(REPO)


def test_generic_rejects_cross_source_collision() -> None:
    rows = [_synthetic_row("EVENT", "UNIT")]
    first = _synthetic_source("first.json", "UNIT", ("EVENT",))
    second = _synthetic_source("second.json", "UNIT", ("EVENT",))
    with pytest.raises(GENERIC_ERROR, match="CROSS_SOURCE_EVENT_COLLISION"):
        generic.reconcile_completed_human_decisions_v1(rows, (first, second))


def test_generic_rejects_duplicate_source_binding() -> None:
    rows = [_synthetic_row("EVENT", "UNIT")]
    source = _synthetic_source("source.json", "UNIT", ("EVENT",))
    with pytest.raises(GENERIC_ERROR, match="SOURCE_BINDING_DUPLICATE"):
        generic.reconcile_completed_human_decisions_v1(rows, (source, source))


def test_generic_rejects_incomplete_review_unit_coverage() -> None:
    rows = [
        _synthetic_row("EVENT1", "UNIT", 2),
        _synthetic_row("EVENT2", "UNIT", 2),
    ]
    source = _synthetic_source("source.json", "UNIT", ("EVENT1",))
    with pytest.raises(GENERIC_ERROR, match="SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_generic_rejects_source_event_outside_historical_universe() -> None:
    rows = [_synthetic_row("EVENT1", "UNIT")]
    source = _synthetic_source("source.json", "UNIT", ("EVENT2",))
    with pytest.raises(GENERIC_ERROR, match="EVENT_NOT_IN_HISTORICAL_UNIVERSE"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_generic_rejects_source_historical_review_unit_mismatch() -> None:
    rows = [_synthetic_row("EVENT", "UNIT1")]
    source = _synthetic_source("source.json", "UNIT2", ("EVENT",))
    with pytest.raises(GENERIC_ERROR, match="FACT_HISTORICAL_REVIEW_UNIT_MISMATCH"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_generic_rejects_non_unreviewed_prior() -> None:
    rows = [_synthetic_row("EVENT", "UNIT")]
    _set_status(rows[0], generic.COMPLETED_HUMAN_POSITIVE)
    source = _synthetic_source("source.json", "UNIT", ("EVENT",))
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_real_reconciliation_counts_training_and_final_1f8_authority() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_1f8_v1(REPO)
    assert result.review_summary == {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 65,
        "completed_positive_unit_count": 7,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 89,
        "completed_total_unit_count": 11,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 249,
        "unreviewed_unit_count": 120,
    }
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 12,
        generic.TRAINING_EXCLUDE: 53,
    }
    expected_authority = json.dumps(
        [subject._1F8_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()],
        separators=(",", ":"),
    )
    rows = [
        row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in set(subject._1F8_EVENT_IDS)
    ]
    assert len(rows) == 8
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["current_status_authority_sources_json"] == expected_authority
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"]
        == generic.COMPLETED_HUMAN_POSITIVE
        for row in rows
    )


def test_exact_1f8_delta_relative_to_published_2vs_chain() -> None:
    adapted = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    prior = generic.reconcile_completed_human_decisions_v1(adapted, sources[:-1])
    current = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    before = prior.review_summary
    after = current.review_summary
    assert after["completed_positive_event_count"] - before["completed_positive_event_count"] == 8
    assert after["completed_total_event_count"] - before["completed_total_event_count"] == 8
    assert after["unreviewed_event_count"] - before["unreviewed_event_count"] == -8
    assert after["unreviewed_unit_count"] - before["unreviewed_unit_count"] == -1
    prior_training = Counter(f.training_disposition for f in prior.normalized_facts)
    current_training = Counter(f.training_disposition for f in current.normalized_facts)
    assert current_training[generic.TRAINING_EXCLUDE] - prior_training[generic.TRAINING_EXCLUDE] == 8
    assert current_training[generic.TRAINING_INCLUDE] - prior_training[generic.TRAINING_INCLUDE] == 0


def test_source_order_is_deterministic() -> None:
    adapted = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_1f8_v1(REPO)
    assert generic.reconcile_completed_human_decisions_v1(
        adapted, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )


def test_production_pipeline_calls_onl_and_generic_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_onl = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = generic.reconcile_completed_human_decisions_v1
    calls = Counter()

    def wrapped_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl"] += 1
        return original_onl(rows)

    def wrapped_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic"] += 1
        return original_generic(rows, sources)

    monkeypatch.setattr(
        subject.onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        wrapped_onl,
    )
    monkeypatch.setattr(
        subject.generic,
        "reconcile_completed_human_decisions_v1",
        wrapped_generic,
    )
    subject.reconcile_real_completed_human_decisions_with_1f8_v1(REPO)
    assert calls == {"onl": 1, "generic": 1}


def test_checker_exact4_frozen_bindings_and_all_gates() -> None:
    result = checker.run_check_v1(REPO)
    assert result["candidate_file_count"] == 4
    assert result["source_binding_count"] == 7
    assert result["normalized_fact_count"] == 65
    assert result["one_f8_transition_adapter_created"] is False
    assert result["one_f8_rows_unchanged_by_onl_adapter"] is True
    assert result["published_global_positive_count"] == 74
    assert result["expected_next_global_positive_count"] == 82
    assert result["global_census_update"] == "NOT_DONE"
    assert result["canonical_task_count"] == 5
    assert result["scaffold_only_B3_present"] is True
    assert result["ready_for_training"] is False
    assert result["feature_semantics"] == "AUDIT_REQUIRED_LATER"


def test_checker_rejects_frozen_predecessor_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = checker.FROZEN_REPOSITORY_FILES
    first = original[0]
    monkeypatch.setattr(
        checker,
        "FROZEN_REPOSITORY_FILES",
        ((*first[:2], first[2] + 1, first[3]), *original[1:]),
    )
    with pytest.raises(ValueError, match="FROZEN_BYTE_COUNT_MISMATCH"):
        checker._verify_frozen_inputs(REPO)


def test_current_census_remains_published_74_and_expected_82_is_informational() -> None:
    result = checker.run_check_v1(REPO)
    assert result["published_global_positive_count"] == 74
    assert result["one_f8_reconciliation_local_positive_delta"] == 8
    assert result["expected_next_global_positive_count"] == 82
    assert result["expected_next_census_derivation_status"] == "INFORMATIONAL_ONLY"
    assert result["expected_next_pending_head"] == "YUN/EXACT7_INFORMATIONAL_ONLY"
    assert result["global_census_updated"] is False

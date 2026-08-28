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
    covapie_completed_human_decision_reconciliation_with_neq_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as neq_ingestion_owner,
)


ERROR = subject.CompletedDecisionReconciliationWithNEQError
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_neq_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_neq_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _historical() -> list[dict[str, str]]:
    return [
        dict(row) for row in generic.load_real_historical_reconciliation_v1(REPO)
    ]


def _adapted_historical() -> tuple[dict[str, str], ...]:
    return onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        generic.load_real_historical_reconciliation_v1(REPO)
    )


def _bound() -> dict[str, object]:
    return neq_ingestion_owner.load_frozen_formal_decision_v1(REPO)


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
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


def test_public_api_is_minimal_and_neq_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithNEQError",
        "project_neq_completed_decision_v1",
        "load_real_completed_decision_sources_with_neq_v1",
        "reconcile_real_completed_human_decisions_with_neq_v1",
    )
    assert subject.NEQ_TRANSITION_ADAPTER_CREATED is False
    module_path = REPO / "src/covalent_ext" / Path(subject.__file__).name
    tree = ast.parse(module_path.read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_neq")
        or ("neq" in name.lower() and "transition" in name.lower())
        for name in function_names
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
    assert called.count("load_real_completed_decision_sources_with_yun_v1") == 1
    assert "reconcile_real_completed_human_decisions_with_yun_v1" not in called


def test_neq_projector_reuses_ingestion_owner_and_generic_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = neq_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.neq_ingestion_owner,
        "load_frozen_formal_decision_v1",
        wrapped,
    )
    source = subject.project_neq_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert len(source.facts) == 6
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )


def test_neq_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise neq_ingestion_owner.NEQIngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.neq_ingestion_owner,
        "load_frozen_formal_decision_v1",
        fail,
    )
    with pytest.raises(ERROR, match="NEQ_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_neq_completed_decision_v1(repo_root=REPO)


def test_neq_projection_exact6_semantics_binding_and_dual_site_identity() -> None:
    source = subject.project_neq_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            "covapie-state/manual-review-aids/"
            "cumulative1000-high-yield-calibration-v1/"
            "NEQ_COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62/"
            "formal-human-decision-v1/neq_formal_human_decision_v1.json"
        ),
        path_namespace="repository_parent_relative",
        byte_count=33908,
        sha256="c5aa577f8b507b9bf6eb8d22207c8c11e3858ddd138c034d31d6f32d40b6c73c",
        schema_version="covapie_neq_exact6_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == (
        subject._NEQ_EVENT_IDS
    )
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status
        == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._NEQ_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._NEQ_FORMAL_DECISION_SHA256
        and fact.source_binding_path == source.binding.source_path
        for fact in source.facts
    )
    events = _bound()["normalized"]["events"]  # type: ignore[index]
    assert Counter(event["cys_residue_id"] for event in events) == {
        "CYS:22-": 3,
        "CYS:81-": 3,
    }


def test_projector_does_not_reinterpret_pair_role_topology_or_context() -> None:
    bound = _bound()
    expected = subject._project_validated_neq_binding_v1(bound)
    altered = deepcopy(bound)
    altered["normalized"]["role_partition"] = {"ignored": "changed"}  # type: ignore[index]
    altered["normalized"]["scientific_context"] = {"ignored": "changed"}  # type: ignore[index]
    for event in altered["normalized"]["events"]:  # type: ignore[index]
        event["D3_reactive_pair"] = "IGNORED_PAIR_CHANGE"
        event["D4_role_partition"] = "IGNORED_ROLE_CHANGE"
        event["POST_distance_angstrom"] = -999.0
        event["protein_reactive_atom"] = "IGNORED_ATOM"
        event["ligand_reactive_atom"] = "IGNORED_ATOM"
    assert subject._project_validated_neq_binding_v1(altered) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/neq.json"),
        ("byte_count", 33909),
        ("sha256", "0" * 64),
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
    ),
)
def test_projector_rejects_formal_binding_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["formal_decision_binding"][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="NEQ_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_neq_binding_v1(bound)


@pytest.mark.parametrize("new_count", (5, 7))
def test_projector_rejects_exact6_count_drift(new_count: int) -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    if new_count == 5:
        del events[-1]
    else:
        events.append(deepcopy(events[-1]))
    with pytest.raises(ERROR, match="EVENT_COUNT_NOT_EXACT6"):
        subject._project_validated_neq_binding_v1(bound)


def test_projector_rejects_missing_or_extra_event_identity() -> None:
    bound = _bound()
    bound["normalized"]["events"][0]["canonical_event_id"] = "EXTRA_EVENT"  # type: ignore[index]
    with pytest.raises(ERROR, match="EVENT_COVERAGE_NOT_EXACT6"):
        subject._project_validated_neq_binding_v1(bound)


def test_projector_rejects_duplicate_event_identity() -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    events[1] = deepcopy(events[0])
    with pytest.raises(ERROR, match="EVENT_ID_DUPLICATE"):
        subject._project_validated_neq_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("D1_task_relevance", "NOT_RELEVANT"),
        ("D2_chemistry_support", "NEGATIVE"),
        ("D5_training_use", "INCLUDE"),
        ("human_training_excluded", False),
        ("training_admitted", True),
        ("decision_finalized", False),
    ),
)
def test_projector_rejects_completed_decision_semantics_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="NEQ_NORMALIZED_EVENT_DECISION_INVALID"):
        subject._project_validated_neq_binding_v1(bound)


def test_projector_rejects_collapsed_cys22_cys81_identity() -> None:
    bound = _bound()
    for event in bound["normalized"]["events"]:  # type: ignore[index]
        event["cys_residue_id"] = "CYS:22-"
    with pytest.raises(ERROR, match="DUAL_SITE_IDENTITY"):
        subject._project_validated_neq_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("distinct_cys_residue_identities", ["CYS:22-"]),
        ("distinct_cys_residue_identity_count", 1),
        ("CYS22_event_count", 6),
        ("CYS81_event_count", 0),
    ),
)
def test_projector_rejects_site_inventory_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["normalized"]["site_inventory"][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="SITE_INVENTORY_IDENTITY_INVALID"):
        subject._project_validated_neq_binding_v1(bound)


def test_original_historical_neq_prior_is_exact6_unreviewed() -> None:
    rows = _historical()
    subject._prove_neq_original_unreviewed_prior_v1(rows)
    neq_rows = [
        row for row in rows if row["canonical_event_id"] in subject._NEQ_EVENT_IDS
    ]
    assert len(neq_rows) == 6
    assert {row["raw_review_unit_id"] for row in neq_rows} == {
        subject._NEQ_REVIEW_UNIT_ID
    }
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in neq_rows
    )


def test_historical_proof_rejects_one_missing_neq_event() -> None:
    rows = _historical()
    rows = [row for row in rows if row["canonical_event_id"] != subject._NEQ_EVENT_IDS[0]]
    with pytest.raises(ERROR, match="NEQ_HISTORICAL_EVENT_MISSING"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_duplicate_neq_event() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._NEQ_EVENT_IDS[0])
    rows.append(dict(row))
    with pytest.raises(ERROR, match="NEQ_HISTORICAL_EVENT_DUPLICATE"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_neq_review_unit_drift() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._NEQ_EVENT_IDS[0])
    row["raw_review_unit_id"] = "WRONG_UNIT"
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT6"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_extra_event_in_neq_unit() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] not in subject._NEQ_EVENT_IDS)
    row["raw_review_unit_id"] = subject._NEQ_REVIEW_UNIT_ID
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT6"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_one_non_unreviewed_neq_prior(status: str) -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._NEQ_EVENT_IDS[0])
    _set_status(row, status)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT6_UNREVIEWED"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_whole_non_unreviewed_neq_unit(status: str) -> None:
    rows = _historical()
    for row in rows:
        if row["canonical_event_id"] in subject._NEQ_EVENT_IDS:
            _set_status(row, status)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT6_UNREVIEWED"):
        subject._prove_neq_original_unreviewed_prior_v1(rows)


def test_onl_adapter_leaves_all_neq_rows_field_equal() -> None:
    original = tuple(_historical())
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(original)
    subject._prove_neq_rows_unchanged_after_onl_normalization_v1(original, adapted)
    neq_ids = set(subject._NEQ_EVENT_IDS)
    assert {
        row["canonical_event_id"]: row
        for row in original
        if row["canonical_event_id"] in neq_ids
    } == {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in neq_ids
    }


def test_neq_unchanged_proof_rejects_unexpected_onl_adapter_change() -> None:
    original = tuple(_historical())
    adapted = [dict(row) for row in original]
    row = next(row for row in adapted if row["canonical_event_id"] == subject._NEQ_EVENT_IDS[0])
    row["current_status_authority_sources_json"] = '["unexpected"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_NEQ_ROW"):
        subject._prove_neq_rows_unchanged_after_onl_normalization_v1(
            original, adapted
        )


def test_onl_adapted_historical_plus_exact9_sources_passes_generic() -> None:
    result = generic.reconcile_completed_human_decisions_v1(
        _adapted_historical(),
        subject.load_real_completed_decision_sources_with_neq_v1(REPO),
    )
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY


def test_one_neq_prior_drift_fails_at_unit_consistency_gate() -> None:
    rows = [dict(row) for row in _adapted_historical()]
    row = next(row for row in rows if row["canonical_event_id"] == subject._NEQ_EVENT_IDS[0])
    _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    with pytest.raises(GENERIC_ERROR, match="HISTORICAL_REVIEW_UNIT_STATUS_MIXED"):
        generic.reconcile_completed_human_decisions_v1(
            rows,
            subject.load_real_completed_decision_sources_with_neq_v1(REPO),
        )


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_whole_neq_prior_drift_reaches_generic_prior_protection(status: str) -> None:
    rows = [dict(row) for row in _adapted_historical()]
    for row in rows:
        if row["canonical_event_id"] in subject._NEQ_EVENT_IDS:
            _set_status(row, status)
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            rows,
            subject.load_real_completed_decision_sources_with_neq_v1(REPO),
        )


def test_original_historical_with_all_nine_sources_still_fails_for_onl() -> None:
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            generic.load_real_historical_reconciliation_v1(REPO),
            subject.load_real_completed_decision_sources_with_neq_v1(REPO),
        )


def test_exact9_source_composition_is_collision_free() -> None:
    sources = subject.load_real_completed_decision_sources_with_neq_v1(REPO)
    assert len(sources) == 9
    assert tuple(len(source.facts) for source in sources) == (8, 16, 8, 9, 8, 8, 8, 7, 6)
    assert len({source.binding.stable_identity for source in sources}) == 9
    assert len({source.binding.review_unit_id for source in sources}) == 9
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 78


def test_source_loader_rejects_neq_collision_with_previous72(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = subject.yun_successor.load_real_completed_decision_sources_with_yun_v1(REPO)
    neq = subject.project_neq_completed_decision_v1(repo_root=REPO)
    collision = replace(
        neq,
        facts=(
            replace(
                neq.facts[0],
                canonical_event_id=sources[0].facts[0].canonical_event_id,
            ),
            *neq.facts[1:],
        ),
    )
    monkeypatch.setattr(subject, "project_neq_completed_decision_v1", lambda *, repo_root: collision)
    with pytest.raises(ERROR, match="REAL_NORMALIZED_FACT_EVENT_COLLISION"):
        subject.load_real_completed_decision_sources_with_neq_v1(REPO)


def test_source_loader_rejects_neq_review_unit_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    neq = subject.project_neq_completed_decision_v1(repo_root=REPO)
    mismatch = replace(
        neq,
        binding=replace(neq.binding, review_unit_id="WRONG_UNIT"),
    )
    monkeypatch.setattr(subject, "project_neq_completed_decision_v1", lambda *, repo_root: mismatch)
    with pytest.raises(ERROR, match="NEQ_SOURCE_REVIEW_UNIT_MISMATCH"):
        subject.load_real_completed_decision_sources_with_neq_v1(REPO)


def test_generic_rejects_cross_source_collision() -> None:
    row = _synthetic_row("event-1", "unit-1")
    one = _synthetic_source("one.json", "unit-1", ("event-1",))
    two = _synthetic_source("two.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="CROSS_SOURCE_EVENT_COLLISION"):
        generic.reconcile_completed_human_decisions_v1((row,), (one, two))


def test_generic_rejects_duplicate_source_binding() -> None:
    row = _synthetic_row("event-1", "unit-1")
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="SOURCE_BINDING_DUPLICATE"):
        generic.reconcile_completed_human_decisions_v1((row,), (source, source))


def test_generic_rejects_incomplete_review_unit_coverage() -> None:
    rows = (
        _synthetic_row("event-1", "unit-1", 2),
        _synthetic_row("event-2", "unit-1", 2),
    )
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH"):
        generic.reconcile_completed_human_decisions_v1(rows, (source,))


def test_generic_rejects_source_event_outside_historical_universe() -> None:
    row = _synthetic_row("event-1", "unit-1")
    source = _synthetic_source("one.json", "unit-1", ("outside",))
    with pytest.raises(GENERIC_ERROR, match="EVENT_NOT_IN_HISTORICAL_UNIVERSE"):
        generic.reconcile_completed_human_decisions_v1((row,), (source,))


def test_generic_rejects_source_historical_review_unit_mismatch() -> None:
    row = _synthetic_row("event-1", "unit-other")
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="FACT_HISTORICAL_REVIEW_UNIT_MISMATCH"):
        generic.reconcile_completed_human_decisions_v1((row,), (source,))


def test_generic_rejects_non_unreviewed_prior() -> None:
    row = _synthetic_row("event-1", "unit-1")
    _set_status(row, generic.COMPLETED_HUMAN_POSITIVE)
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1((row,), (source,))


def test_real_reconciliation_counts_training_and_final_neq_authority() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_neq_v1(REPO)
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 19,
        generic.TRAINING_EXCLUDE: 59,
    }
    neq_source = subject.project_neq_completed_decision_v1(repo_root=REPO)
    expected_authority = json.dumps(
        [neq_source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    neq_rows = [
        row for row in result.reconciled_rows if row["canonical_event_id"] in subject._NEQ_EVENT_IDS
    ]
    assert len(neq_rows) == 6
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"]
        == generic.COMPLETED_HUMAN_POSITIVE
        and row["current_status_authority_sources_json"] == expected_authority
        for row in neq_rows
    )


def test_exact_neq_delta_relative_to_published_yun_chain() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_neq_v1(REPO)
    summary = result.review_summary
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    assert summary["completed_positive_event_count"] - 72 == 6
    assert summary["completed_total_event_count"] - 96 == 6
    assert summary["unreviewed_event_count"] - 242 == -6
    assert summary["unreviewed_unit_count"] - 119 == -1
    assert dispositions[generic.TRAINING_INCLUDE] - 19 == 0
    assert dispositions[generic.TRAINING_EXCLUDE] - 53 == 6


def test_source_order_is_deterministic() -> None:
    rows = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_neq_v1(REPO)
    assert generic.reconcile_completed_human_decisions_v1(
        rows, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        rows, tuple(reversed(sources))
    )


def test_production_pipeline_calls_onl_and_generic_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_onl = subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl"] += 1
        return original_onl(rows)  # type: ignore[arg-type]

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    monkeypatch.setattr(
        subject.onl_successor,
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        counted_onl,
    )
    monkeypatch.setattr(
        subject.generic,
        "reconcile_completed_human_decisions_v1",
        counted_generic,
    )
    subject.reconcile_real_completed_human_decisions_with_neq_v1(REPO)
    assert calls == {"onl": 1, "generic": 1}


def test_checker_exact4_frozen_bindings_and_all_gates() -> None:
    report = checker.run_check_v1(REPO)
    assert report["check"] == "PASS"
    assert report["exact4"]["count"] == 4
    assert report["frozen_bindings"]["count"] == 10
    assert report["delegate_runtime_calls"] == {
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert report["source_fact_counts"] == (8, 16, 8, 9, 8, 8, 8, 7, 6)
    assert report["global_census_update"] == "NOT_DONE"
    assert report["ready_for_training"] is False


def test_checker_rejects_frozen_predecessor_identity_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = checker.FROZEN_REPOSITORY_FILES[0]
    drifted = ((first[0], first[1], first[2], "0" * 64), *checker.FROZEN_REPOSITORY_FILES[1:])
    monkeypatch.setattr(checker, "FROZEN_REPOSITORY_FILES", drifted)
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)


def test_current_census_is_preserved_and_next_values_are_informational() -> None:
    published = checker._published_census_state(REPO)
    assert published["counts"] == {
        "positive": 89,
        "training_include": 36,
        "training_exclude": 53,
        "future_candidates": 19,
    }
    source = subject.project_neq_completed_decision_v1(repo_root=REPO)
    derived = checker._verify_next_census_derivation(source, published)
    assert derived["chemistry_positive"] == 95
    assert derived["training_include"] == 36
    assert derived["training_exclude"] == 59
    assert derived["future_training_candidates"] == 19
    assert derived["missing_tensor_composition"][-1] == "NEQ6"

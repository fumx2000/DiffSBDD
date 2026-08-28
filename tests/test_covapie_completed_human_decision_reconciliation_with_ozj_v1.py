from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from dataclasses import fields, replace
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
    covapie_completed_human_decision_reconciliation_with_ozj_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_ingestion_owner,
)


ERROR = subject.CompletedDecisionReconciliationWithOZJError
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_ozj_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
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
    return ozj_ingestion_owner.load_frozen_formal_decision_v1(REPO)


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
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
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
        ),
    )


def test_public_api_is_minimal_and_ozj_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithOZJError",
        "project_ozj_completed_decision_v1",
        "load_real_completed_decision_sources_with_ozj_v1",
        "reconcile_real_completed_human_decisions_with_ozj_v1",
    )
    assert subject.OZJ_TRANSITION_ADAPTER_CREATED is False
    tree = ast.parse(Path(subject.__file__).read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_ozj")
        or ("ozj" in name.lower() and "transition" in name.lower())
        for name in function_names
    )
    called = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert called.count("load_real_completed_decision_sources_with_cht_v1") == 1
    assert called.count("reconcile_real_completed_human_decisions_with_cht_v1") == 0
    assert called.count("load_frozen_formal_decision_v1") == 1
    assert called.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) == 1
    assert called.count("reconcile_completed_human_decisions_v1") == 1
    history_names = {
        "row", "rows", "historical", "historical_rows",
        "adapted_historical", "working",
    }
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id in history_names
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in ast.walk(tree)
    )


def test_successor_reuses_generic_types_without_implementation_duplication() -> None:
    source = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    assert type(source) is generic.NormalizedDecisionSource
    assert type(source.binding) is generic.SourceBinding
    assert all(
        type(fact) is generic.NormalizedCompletedDecisionFact
        for fact in source.facts
    )
    tree = ast.parse(Path(subject.__file__).read_bytes())
    classes = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    assert not classes & {
        "SourceBinding",
        "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource",
        "ReconciliationResult",
    }
    functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not functions & {
        "_validate_source_binding",
        "_validate_fact",
        "_review_summary",
    }


def test_ozj_projector_calls_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ozj_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.ozj_ingestion_owner, "load_frozen_formal_decision_v1", wrapped
    )
    subject.project_ozj_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]


def test_ozj_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise ozj_ingestion_owner.OZJIngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.ozj_ingestion_owner, "load_frozen_formal_decision_v1", fail
    )
    with pytest.raises(ERROR, match="OZJ_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_ozj_completed_decision_v1(repo_root=REPO)


def test_ozj_projection_exact4_binding_context_and_semantics() -> None:
    source = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            "covapie-state/manual-review-aids/"
            "cumulative1000-high-yield-calibration-v1/"
            "OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/"
            "formal-human-decision-v1/ozj_formal_human_decision_v1.json"
        ),
        path_namespace="repository_parent_relative",
        byte_count=28914,
        sha256="0b14271a4541e69d768e28b6433c87b8b22c21505f6e3bdf075bb94381c3c606",
        schema_version="covapie_ozj_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == tuple(
        sorted(subject._OZJ_EVENT_IDS)
    )
    assert len(source.facts) == 4
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_INCLUDE
        and fact.human_training_excluded is False
        and fact.source_decision_schema == subject._OZJ_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._OZJ_FORMAL_DECISION_SHA256
        and fact.source_binding_path == source.binding.source_path
        for fact in source.facts
    )
    events = _bound()["normalized"]["events"]  # type: ignore[index]
    assert Counter(event["pdb_id"] for event in events) == {"4CL8": 4}
    assert {event["cys_residue_id"] for event in events} == {"CYS:168-"}
    assert {
        (
            event["protein_chain_or_asym"],
            event["ligand_chain_or_asym"],
        )
        for event in events
    } == {("A", "E"), ("B", "I"), ("C", "L"), ("D", "O")}


def test_generic_fact_is_exact_thin_contract_without_future_or_admission() -> None:
    source = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    assert tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact)) == (
        checker.EXPECTED_GENERIC_FACT_FIELDS
    )
    for fact in source.facts:
        assert not hasattr(fact, "future_training_candidate")
        assert not hasattr(fact, "candidate_for_future_training_admission")
        assert not hasattr(fact, "future_training_admission_status")
        assert not hasattr(fact, "training_admitted")
        assert not hasattr(fact, "runtime")
        assert not hasattr(fact, "warhead")
        assert not hasattr(fact, "reaction_family")
    with pytest.raises(TypeError):
        generic.NormalizedCompletedDecisionFact(
            **{
                field: getattr(source.facts[0], field)
                for field in checker.EXPECTED_GENERIC_FACT_FIELDS
            },
            future_training_candidate=True,
        )


def test_projector_does_not_propagate_unrelated_ozj_fields() -> None:
    bound = _bound()
    expected = subject._project_validated_ozj_binding_v1(bound)
    altered = deepcopy(bound)
    altered["normalized"]["role"] = {"ignored": "changed"}  # type: ignore[index]
    altered["normalized"]["scientific_context"] = {"ignored": "changed"}  # type: ignore[index]
    altered["normalized"]["source_ccd_and_event_topology_boundary"] = {  # type: ignore[index]
        "ignored": "changed"
    }
    altered["normalized"]["geometry_boundary"] = {"ignored": "changed"}  # type: ignore[index]
    for event in altered["normalized"]["events"]:  # type: ignore[index]
        event["selected_role_candidate_index_0based"] = -999
        event["source_CAF_OAD_bond_order"] = "IGNORED"
        event["POST_distance_angstrom"] = -999.0
        event["reaction_family_target_available"] = "IGNORED"
        event["warhead_type_target_available"] = "IGNORED"
    assert subject._project_validated_ozj_binding_v1(altered) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/ozj.json"),
        ("byte_count", 28915),
        ("sha256", "0" * 64),
        ("schema_version", "wrong_schema"),
        ("review_unit_id", "WRONG_REVIEW_UNIT"),
        ("approved_at_utc", "2026-08-28T00:00:00Z"),
    ),
)
def test_projector_rejects_formal_binding_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["formal_decision_binding"][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="OZJ_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_ozj_binding_v1(bound)


@pytest.mark.parametrize("new_count", (3, 5))
def test_projector_rejects_exact4_count_drift(new_count: int) -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    if new_count == 3:
        del events[-1]
    else:
        events.append(deepcopy(events[-1]))
    with pytest.raises(ERROR, match="EVENT_COUNT_NOT_EXACT4"):
        subject._project_validated_ozj_binding_v1(bound)


def test_projector_rejects_duplicate_event_identity() -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    events[1] = deepcopy(events[0])
    with pytest.raises(ERROR, match="EVENT_ID_DUPLICATE"):
        subject._project_validated_ozj_binding_v1(bound)


def test_projector_rejects_missing_plus_extra_event_identity() -> None:
    bound = _bound()
    bound["normalized"]["events"][0]["canonical_event_id"] = "EXTRA_OZJ_EVENT"  # type: ignore[index]
    with pytest.raises(ERROR, match="EVENT_COVERAGE_NOT_EXACT4"):
        subject._project_validated_ozj_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("task_relevant", False),
        ("chemistry_known_positive", False),
        ("formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("human_training_excluded", True),
    ),
)
def test_projector_rejects_completed_decision_semantics_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="OZJ_NORMALIZED_EVENT_DECISION_INVALID"):
        subject._project_validated_ozj_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_for_future_training_admission", False),
        ("future_training_admission_status", "ADMITTED"),
        ("future_training_candidate_is_training_admission", True),
        ("training_admitted", True),
    ),
)
def test_projector_rejects_future_admission_boundary_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="FUTURE_ADMISSION_BOUNDARY_INVALID"):
        subject._project_validated_ozj_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("cys_residue_id", "CYS:169-", "CYS_RESIDUE_ID_INVALID"),
        ("pdb_id", "WRONG", "PDB_CONTEXT_COUNTS"),
        ("scaleup_rank", 999, "RANK_COVERAGE"),
        ("ligand_chain_or_asym", "WRONG", "DISTINCT_EVENT_CONTEXTS"),
    ),
)
def test_projector_rejects_context_identity_drift(
    field: str, value: object, token: str
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match=token):
        subject._project_validated_ozj_binding_v1(bound)


def test_projector_rejects_context_inventory_drift() -> None:
    bound = _bound()
    bound["normalized"]["event_context_inventory"][0]["ligand_asym"] = "WRONG"  # type: ignore[index]
    with pytest.raises(ERROR, match="EVENT_CONTEXT_INVENTORY_INVALID"):
        subject._project_validated_ozj_binding_v1(bound)


def test_original_historical_ozj_prior_is_exact4_unreviewed() -> None:
    rows = _historical()
    subject._prove_ozj_original_unreviewed_prior_v1(rows)
    ozj_rows = [row for row in rows if row["canonical_event_id"] in subject._OZJ_EVENT_IDS]
    assert len(ozj_rows) == 4
    assert {row["raw_review_unit_id"] for row in ozj_rows} == {subject._OZJ_REVIEW_UNIT_ID}
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in ozj_rows
    )


def test_historical_proof_rejects_one_missing_ozj_event() -> None:
    rows = [
        row for row in _historical()
        if row["canonical_event_id"] != subject._OZJ_EVENT_IDS[0]
    ]
    with pytest.raises(ERROR, match="OZJ_HISTORICAL_EVENT_MISSING"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_duplicate_ozj_event() -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._OZJ_EVENT_IDS[0]
    )
    rows.append(dict(row))
    with pytest.raises(ERROR, match="OZJ_HISTORICAL_EVENT_DUPLICATE"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_ozj_wrong_unit() -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._OZJ_EVENT_IDS[0]
    )
    row["raw_review_unit_id"] = "WRONG_UNIT"
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT4"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_extra_event_in_ozj_unit() -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] not in subject._OZJ_EVENT_IDS
    )
    row["raw_review_unit_id"] = subject._OZJ_REVIEW_UNIT_ID
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT4"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_non_unreviewed_ozj_prior(status: str) -> None:
    rows = _historical()
    for row in rows:
        if row["canonical_event_id"] in subject._OZJ_EVENT_IDS:
            _set_status(row, status)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_mixed_ozj_unit_status() -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._OZJ_EVENT_IDS[0]
    )
    _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (("calibration_eligible", "false"), ("calibration_exclusion_reason", "NONEMPTY")),
)
def test_historical_proof_rejects_calibration_prior_drift(
    field: str, value: str
) -> None:
    rows = _historical()
    row = next(
        row for row in rows
        if row["canonical_event_id"] == subject._OZJ_EVENT_IDS[0]
    )
    row[field] = value
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT4_UNREVIEWED"):
        subject._prove_ozj_original_unreviewed_prior_v1(rows)


def test_onl_adapter_leaves_all_ozj_rows_field_equal() -> None:
    original = tuple(_historical())
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(original)
    subject._prove_ozj_rows_unchanged_after_onl_normalization_v1(original, adapted)
    ozj_ids = set(subject._OZJ_EVENT_IDS)
    assert {
        row["canonical_event_id"]: row
        for row in original
        if row["canonical_event_id"] in ozj_ids
    } == {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in ozj_ids
    }


def test_ozj_unchanged_proof_rejects_onl_adapter_change() -> None:
    original = tuple(_historical())
    adapted = [dict(row) for row in original]
    row = next(
        row for row in adapted
        if row["canonical_event_id"] == subject._OZJ_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["unexpected"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_OZJ_ROW"):
        subject._prove_ozj_rows_unchanged_after_onl_normalization_v1(original, adapted)


def test_original_historical_with_exact11_sources_still_fails_for_onl() -> None:
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            generic.load_real_historical_reconciliation_v1(REPO),
            subject.load_real_completed_decision_sources_with_ozj_v1(REPO),
        )


def test_onl_adapted_historical_plus_exact11_sources_passes_generic() -> None:
    result = generic.reconcile_completed_human_decisions_v1(
        _adapted_historical(),
        subject.load_real_completed_decision_sources_with_ozj_v1(REPO),
    )
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY


def test_exact11_source_composition_is_collision_free() -> None:
    sources = subject.load_real_completed_decision_sources_with_ozj_v1(REPO)
    assert len(sources) == 11
    assert tuple(len(source.facts) for source in sources) == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert len({source.binding.stable_identity for source in sources}) == 11
    assert len({source.binding.review_unit_id for source in sources}) == 11
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 87


def test_source_loader_calls_cht_loader_once(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject.cht_successor.load_real_completed_decision_sources_with_cht_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.cht_successor,
        "load_real_completed_decision_sources_with_cht_v1",
        wrapped,
    )
    subject.load_real_completed_decision_sources_with_ozj_v1(REPO)
    assert calls == [REPO]


def test_source_loader_rejects_ozj_collision_with_predecessor83(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = subject.cht_successor.load_real_completed_decision_sources_with_cht_v1(REPO)
    ozj = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    collision = replace(
        ozj,
        facts=(
            replace(ozj.facts[0], canonical_event_id=existing[0].facts[0].canonical_event_id),
            *ozj.facts[1:],
        ),
    )
    monkeypatch.setattr(subject, "project_ozj_completed_decision_v1", lambda *, repo_root: collision)
    with pytest.raises(ERROR, match="OZJ_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_ozj_v1(REPO)


def test_source_loader_rejects_source_facts_not_exact4(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ozj = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    short = replace(ozj, facts=ozj.facts[:-1])
    monkeypatch.setattr(subject, "project_ozj_completed_decision_v1", lambda *, repo_root: short)
    with pytest.raises(ERROR, match="OZJ_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_ozj_v1(REPO)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("review_unit_id", "WRONG_UNIT"),
        ("task_relevance_disposition", generic.TASK_NOT_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_disposition", generic.TRAINING_EXCLUDE),
        ("human_training_excluded", True),
    ),
)
def test_source_loader_rejects_one_fact_semantics_drift(
    field: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    ozj = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    wrong = replace(
        ozj,
        facts=(replace(ozj.facts[0], **{field: value}), *ozj.facts[1:]),
    )
    monkeypatch.setattr(subject, "project_ozj_completed_decision_v1", lambda *, repo_root: wrong)
    with pytest.raises(ERROR, match="OZJ_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_ozj_v1(REPO)


def test_source_loader_rejects_malformed_generic_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subject,
        "project_ozj_completed_decision_v1",
        lambda *, repo_root: {"binding": "not-a-generic-source"},
    )
    with pytest.raises(ERROR, match="OZJ_SOURCE_PROJECTION_INVALID"):
        subject.load_real_completed_decision_sources_with_ozj_v1(REPO)


def test_generic_rejects_cross_source_collision() -> None:
    row = _synthetic_row("event-1", "unit-1")
    one = _synthetic_source("one.json", "unit-1", ("event-1",))
    two = _synthetic_source("two.json", "unit-1", ("event-1",))
    with pytest.raises(GENERIC_ERROR, match="CROSS_SOURCE_EVENT_COLLISION"):
        generic.reconcile_completed_human_decisions_v1((row,), (one, two))


def test_generic_rejects_duplicate_and_stable_identity_binding() -> None:
    row = _synthetic_row("event-1", "unit-1")
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    stable_collision = replace(source, binding=replace(source.binding))
    for duplicate in (source, stable_collision):
        with pytest.raises(GENERIC_ERROR, match="SOURCE_BINDING_DUPLICATE"):
            generic.reconcile_completed_human_decisions_v1((row,), (source, duplicate))


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


@pytest.mark.parametrize(
    ("mutation", "token"),
    (
        ("wrong_type", "NORMALIZED_SOURCE_TYPE_INVALID"),
        ("empty_facts", "SOURCE_FACTS_EMPTY"),
        ("human_incomplete", "HUMAN_REVIEW_NOT_COMPLETED"),
    ),
)
def test_generic_owner_rejects_malformed_source(mutation: str, token: str) -> None:
    row = _synthetic_row("event-1", "unit-1")
    source = _synthetic_source("one.json", "unit-1", ("event-1",))
    if mutation == "wrong_type":
        malformed: object = {"binding": source.binding, "facts": source.facts}
    elif mutation == "empty_facts":
        malformed = replace(source, facts=())
    else:
        malformed = replace(
            source,
            facts=(replace(source.facts[0], human_review_completed=False),),
        )
    with pytest.raises(GENERIC_ERROR, match=token):
        generic.reconcile_completed_human_decisions_v1((row,), (malformed,))  # type: ignore[arg-type]


def test_real_reconciliation_counts_training_and_final_ozj_authority() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_ozj_v1(REPO)
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 23,
        generic.TRAINING_EXCLUDE: 64,
    }
    ozj_source = subject.project_ozj_completed_decision_v1(repo_root=REPO)
    expected_authority = json.dumps(
        [ozj_source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    ozj_rows = [
        row for row in result.reconciled_rows
        if row["canonical_event_id"] in subject._OZJ_EVENT_IDS
    ]
    assert len(ozj_rows) == 4
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["current_status_authority_sources_json"] == expected_authority
        for row in ozj_rows
    )


def test_exact_ozj_delta_relative_to_published_cht_chain() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_ozj_v1(REPO)
    summary = result.review_summary
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    assert summary["completed_positive_event_count"] - 83 == 4
    assert summary["completed_positive_unit_count"] - 10 == 1
    assert summary["completed_total_event_count"] - 107 == 4
    assert summary["completed_total_unit_count"] - 14 == 1
    assert summary["unreviewed_event_count"] - 231 == -4
    assert summary["unreviewed_unit_count"] - 117 == -1
    assert summary["in_progress_event_count"] == 0
    assert dispositions[generic.TRAINING_INCLUDE] - 19 == 4
    assert dispositions[generic.TRAINING_EXCLUDE] - 64 == 0
    assert not hasattr(result, "future_training_candidate_count")
    assert not hasattr(result, "training_admitted_count")


def test_source_order_is_deterministic() -> None:
    rows = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_ozj_v1(REPO)
    assert generic.reconcile_completed_human_decisions_v1(
        rows, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        rows, tuple(reversed(sources))
    )


def test_production_pipeline_calls_all_delegates_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_cht = subject.cht_successor.load_real_completed_decision_sources_with_cht_v1
    original_ozj = subject.ozj_ingestion_owner.load_frozen_formal_decision_v1
    original_onl = subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()

    def counted_cht(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["cht"] += 1
        return original_cht(root)

    def counted_ozj(root: Path) -> dict[str, object]:
        calls["ozj"] += 1
        return original_ozj(root)

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl"] += 1
        return original_onl(rows)  # type: ignore[arg-type]

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    monkeypatch.setattr(subject.cht_successor, "load_real_completed_decision_sources_with_cht_v1", counted_cht)
    monkeypatch.setattr(subject.ozj_ingestion_owner, "load_frozen_formal_decision_v1", counted_ozj)
    monkeypatch.setattr(subject.onl_successor, "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1", counted_onl)
    monkeypatch.setattr(subject.generic, "reconcile_completed_human_decisions_v1", counted_generic)
    subject.reconcile_real_completed_human_decisions_with_ozj_v1(REPO)
    assert calls == {"cht": 1, "ozj": 1, "onl": 1, "generic": 1}


def test_current_census_stays_published_cht_and_future_is_informational() -> None:
    published = checker._published_census_state(REPO)
    assert published["counts"] == checker.EXPECTED_CURRENT_CENSUS
    derived = checker._verify_future_census_informational(
        subject.project_ozj_completed_decision_v1(repo_root=REPO),
        _bound(),
        published,
    )
    assert derived == checker.EXPECTED_FUTURE_CENSUS
    assert derived["warhead_only_A"] == 104
    assert derived["linker_plus_warhead_B"] == 48
    assert derived["scaffold_plus_warhead_B2"] == 48
    assert derived["scaffold_only_B3"] == 104
    assert derived["scaffold_plus_linker_plus_warhead_C"] == 104


def test_expected_next_pending_after_ozj_is_f24_informational() -> None:
    published = checker._published_census_state(REPO)
    pending = published["summary"]["top_pending_review_units_by_event_yield"]  # type: ignore[index]
    assert pending[0]["ligand_component_ids"] == ["OZJ"]
    assert pending[1] == {
        "ccd_complete_count": 4,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "event_count": 4,
        "exact_pair_count": 4,
        "full_coordinate_count": 4,
        "ligand_component_ids": ["F24"],
        "pdb_ids": ["3V4X"],
        "post_source_evidence_count": 4,
        "rank": 2,
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5",
    }


def test_checker_exact4_frozen_bindings_architecture_and_all_gates() -> None:
    report = checker.run_check_v1(REPO)
    assert report["check"] == "PASS"
    assert report["exact4"]["count"] == 4
    assert report["frozen_bindings"]["count"] == 10
    assert report["delegate_runtime_calls"] == {
        "cht_source_loader": 1,
        "ozj_ingestion_loader": 1,
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert report["source_fact_counts"] == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert report["event_collisions"] == 0
    assert report["generic_fact_thinness"]["future_candidate_propagated"] is False
    assert report["global_census_update"] == "NOT_DONE"
    assert report["ready_for_external_review"] is True
    assert report["ready_for_training"] is False
    assert report["feature_semantics"] == "AUDIT_REQUIRED_LATER"


def test_checker_accepts_future_tracked_clean_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checker, "_ordinary_untracked", lambda _root: ())
    report = checker.verify_candidate_exact4_v1(REPO)
    assert report["count"] == 4
    assert report["lifecycle"] == "TRACKED_CLEAN"


def test_checker_rejects_frozen_generic_owner_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = checker.FROZEN_REPOSITORY_FILES[0]
    drifted = (
        (first[0], first[1], first[2], "0" * 64),
        *checker.FROZEN_REPOSITORY_FILES[1:],
    )
    monkeypatch.setattr(checker, "FROZEN_REPOSITORY_FILES", drifted)
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)


def test_checker_rejects_frozen_ozj_formal_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checker, "OZJ_FORMAL_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)

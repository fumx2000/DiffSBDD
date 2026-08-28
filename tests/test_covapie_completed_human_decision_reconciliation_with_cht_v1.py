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
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v1
    as cht_ingestion_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_cht_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)


ERROR = subject.CompletedDecisionReconciliationWithCHTError
GENERIC_ERROR = generic.CompletedDecisionReconciliationError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_completed_human_decision_reconciliation_with_cht_v1",
    REPO
    / "scripts/check_covapie_completed_human_decision_reconciliation_with_cht_v1.py",
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
    return cht_ingestion_owner.load_frozen_formal_decision_v1(REPO)


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


def test_public_api_is_minimal_and_cht_transition_adapter_is_not_created() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithCHTError",
        "project_cht_completed_decision_v1",
        "load_real_completed_decision_sources_with_cht_v1",
        "reconcile_real_completed_human_decisions_with_cht_v1",
    )
    assert subject.CHT_TRANSITION_ADAPTER_CREATED is False
    tree = ast.parse(Path(subject.__file__).read_bytes())
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not any(
        name.lower().startswith("_adapt_cht")
        or ("cht" in name.lower() and "transition" in name.lower())
        for name in function_names
    )
    called = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert called.count("load_real_completed_decision_sources_with_neq_v1") == 1
    assert called.count("reconcile_real_completed_human_decisions_with_neq_v1") == 0
    assert called.count("load_frozen_formal_decision_v1") == 1
    assert called.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) == 1
    assert called.count("reconcile_completed_human_decisions_v1") == 1
    history_names = {
        "row",
        "rows",
        "historical",
        "historical_rows",
        "adapted_historical",
        "working",
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


def test_successor_reuses_generic_types_without_dataclass_duplication() -> None:
    source = subject.project_cht_completed_decision_v1(repo_root=REPO)
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


def test_cht_projector_calls_ingestion_owner_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = cht_ingestion_owner.load_frozen_formal_decision_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> dict[str, object]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.cht_ingestion_owner, "load_frozen_formal_decision_v1", wrapped
    )
    subject.project_cht_completed_decision_v1(repo_root=REPO)
    assert calls == [REPO]


def test_cht_projector_wraps_ingestion_owner_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_repo_root: Path) -> dict[str, object]:
        raise cht_ingestion_owner.CHTIngestionSafetyError("SOURCE_DRIFT")

    monkeypatch.setattr(
        subject.cht_ingestion_owner, "load_frozen_formal_decision_v1", fail
    )
    with pytest.raises(ERROR, match="CHT_INGESTION_OWNER_VALIDATION_FAILED"):
        subject.project_cht_completed_decision_v1(repo_root=REPO)


def test_cht_projection_exact5_binding_context_and_semantics() -> None:
    source = subject.project_cht_completed_decision_v1(repo_root=REPO)
    assert source.binding == generic.SourceBinding(
        source_path=(
            "covapie-state/manual-review-aids/"
            "cumulative1000-high-yield-calibration-v1/"
            "CHT_COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410/"
            "formal-human-decision-v1/cht_formal_human_decision_v1.json"
        ),
        path_namespace="repository_parent_relative",
        byte_count=33307,
        sha256="0f8b48d08a116aa6fa2b30a67d89a51ae2b730f68514b0ce2e0985189dd1ea2b",
        schema_version="covapie_cht_exact5_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410",
    )
    assert tuple(fact.canonical_event_id for fact in source.facts) == subject._CHT_EVENT_IDS
    assert len(source.facts) == 5
    assert all(
        fact.human_review_completed is True
        and fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_EXCLUDE
        and fact.human_training_excluded is True
        and fact.source_decision_schema == subject._CHT_FORMAL_DECISION_SCHEMA
        and fact.source_decision_sha256 == subject._CHT_FORMAL_DECISION_SHA256
        and fact.source_binding_path == source.binding.source_path
        for fact in source.facts
    )
    events = _bound()["normalized"]["events"]  # type: ignore[index]
    assert Counter(event["pdb_id"] for event in events) == {"4V3F": 3, "5A2D": 2}
    assert {event["cys_residue_id"] for event in events} == {"CYS:450-"}
    assert len(
        {
            (
                event["pdb_id"],
                event["protein_chain_or_asym"],
                event["ligand_chain_or_asym"],
            )
            for event in events
        }
    ) == 5


def test_projector_does_not_propagate_unrelated_cht_fields() -> None:
    bound = _bound()
    expected = subject._project_validated_cht_binding_v1(bound)
    altered = deepcopy(bound)
    altered["normalized"]["role"] = {"ignored": "changed"}  # type: ignore[index]
    altered["normalized"]["scientific_context"] = {"ignored": "changed"}  # type: ignore[index]
    altered["normalized"]["source_ccd_and_event_topology_boundary"] = {  # type: ignore[index]
        "ignored": "changed"
    }
    altered["normalized"]["geometry_boundary"] = {"ignored": "changed"}  # type: ignore[index]
    for event in altered["normalized"]["events"]:  # type: ignore[index]
        event["selected_role_candidate_index_0based"] = -999
        event["source_CCD_C4_O6_bond_order"] = "IGNORED"
        event["POST_distance_angstrom"] = -999.0
        event["reaction_family_target_available"] = "IGNORED"
        event["warhead_type_target_available"] = "IGNORED"
    assert subject._project_validated_cht_binding_v1(altered) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("path", "wrong/cht.json"),
        ("byte_count", 33308),
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
    with pytest.raises(ERROR, match="CHT_FORMAL_DECISION_BINDING_INVALID"):
        subject._project_validated_cht_binding_v1(bound)


@pytest.mark.parametrize("new_count", (4, 6))
def test_projector_rejects_exact5_count_drift(new_count: int) -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    if new_count == 4:
        del events[-1]
    else:
        events.append(deepcopy(events[-1]))
    with pytest.raises(ERROR, match="EVENT_COUNT_NOT_EXACT5"):
        subject._project_validated_cht_binding_v1(bound)


def test_projector_rejects_duplicate_event_identity() -> None:
    bound = _bound()
    events = bound["normalized"]["events"]  # type: ignore[index]
    events[1] = deepcopy(events[0])
    with pytest.raises(ERROR, match="EVENT_ID_DUPLICATE"):
        subject._project_validated_cht_binding_v1(bound)


def test_projector_rejects_missing_plus_extra_event_identity() -> None:
    bound = _bound()
    bound["normalized"]["events"][0]["canonical_event_id"] = "EXTRA_CHT_EVENT"  # type: ignore[index]
    with pytest.raises(ERROR, match="EVENT_COVERAGE_NOT_EXACT5"):
        subject._project_validated_cht_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("task_relevant", False),
        ("chemistry_known_positive", False),
        ("formal_event_training_use_decision", "INCLUDE"),
        ("human_training_excluded", False),
        ("training_admitted", True),
    ),
)
def test_projector_rejects_completed_decision_semantics_drift(
    field: str, value: object
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match="CHT_NORMALIZED_EVENT_DECISION_INVALID"):
        subject._project_validated_cht_binding_v1(bound)


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("cys_residue_id", "CYS:451-", "CYS_RESIDUE_ID_INVALID"),
        ("pdb_id", "WRONG", "PDB_CONTEXT_COUNTS"),
        ("scaleup_rank", 999, "RANK_COVERAGE"),
    ),
)
def test_projector_rejects_context_identity_drift(
    field: str, value: object, token: str
) -> None:
    bound = _bound()
    bound["normalized"]["events"][0][field] = value  # type: ignore[index]
    with pytest.raises(ERROR, match=token):
        subject._project_validated_cht_binding_v1(bound)


def test_projector_rejects_collapsed_context_inventory() -> None:
    bound = _bound()
    bound["normalized"]["event_context_inventory"]["contexts_collapsed"] = True  # type: ignore[index]
    with pytest.raises(ERROR, match="EVENT_CONTEXT_INVENTORY_INVALID"):
        subject._project_validated_cht_binding_v1(bound)


def test_original_historical_cht_prior_is_exact5_unreviewed() -> None:
    rows = _historical()
    subject._prove_cht_original_unreviewed_prior_v1(rows)
    cht_rows = [row for row in rows if row["canonical_event_id"] in subject._CHT_EVENT_IDS]
    assert len(cht_rows) == 5
    assert {row["raw_review_unit_id"] for row in cht_rows} == {subject._CHT_REVIEW_UNIT_ID}
    assert all(
        row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in cht_rows
    )


def test_historical_proof_rejects_one_missing_cht_event() -> None:
    rows = [row for row in _historical() if row["canonical_event_id"] != subject._CHT_EVENT_IDS[0]]
    with pytest.raises(ERROR, match="CHT_HISTORICAL_EVENT_MISSING"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_duplicate_cht_event() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._CHT_EVENT_IDS[0])
    rows.append(dict(row))
    with pytest.raises(ERROR, match="CHT_HISTORICAL_EVENT_DUPLICATE"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_cht_wrong_unit() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._CHT_EVENT_IDS[0])
    row["raw_review_unit_id"] = "WRONG_UNIT"
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT5"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_extra_event_in_cht_unit() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] not in subject._CHT_EVENT_IDS)
    row["raw_review_unit_id"] = subject._CHT_REVIEW_UNIT_ID
    with pytest.raises(ERROR, match="REVIEW_UNIT_EVENT_SET_NOT_EXACT5"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    "status",
    (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE),
)
def test_historical_proof_rejects_non_unreviewed_cht_prior(status: str) -> None:
    rows = _historical()
    for row in rows:
        if row["canonical_event_id"] in subject._CHT_EVENT_IDS:
            _set_status(row, status)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT5_UNREVIEWED"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


def test_historical_proof_rejects_mixed_cht_unit_status() -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._CHT_EVENT_IDS[0])
    _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT5_UNREVIEWED"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (("calibration_eligible", "false"), ("calibration_exclusion_reason", "NONEMPTY")),
)
def test_historical_proof_rejects_calibration_prior_drift(
    field: str, value: str
) -> None:
    rows = _historical()
    row = next(row for row in rows if row["canonical_event_id"] == subject._CHT_EVENT_IDS[0])
    row[field] = value
    with pytest.raises(ERROR, match="PRIOR_STATE_NOT_EXACT5_UNREVIEWED"):
        subject._prove_cht_original_unreviewed_prior_v1(rows)


def test_onl_adapter_leaves_all_cht_rows_field_equal() -> None:
    original = tuple(_historical())
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(original)
    subject._prove_cht_rows_unchanged_after_onl_normalization_v1(original, adapted)
    cht_ids = set(subject._CHT_EVENT_IDS)
    assert {
        row["canonical_event_id"]: row for row in original if row["canonical_event_id"] in cht_ids
    } == {
        row["canonical_event_id"]: row for row in adapted if row["canonical_event_id"] in cht_ids
    }


def test_cht_unchanged_proof_rejects_onl_adapter_change() -> None:
    original = tuple(_historical())
    adapted = [dict(row) for row in original]
    row = next(row for row in adapted if row["canonical_event_id"] == subject._CHT_EVENT_IDS[0])
    row["current_status_authority_sources_json"] = '["unexpected"]'
    with pytest.raises(ERROR, match="ONL_ADAPTER_CHANGED_CHT_ROW"):
        subject._prove_cht_rows_unchanged_after_onl_normalization_v1(original, adapted)


def test_original_historical_with_exact10_sources_still_fails_for_onl() -> None:
    with pytest.raises(GENERIC_ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"):
        generic.reconcile_completed_human_decisions_v1(
            generic.load_real_historical_reconciliation_v1(REPO),
            subject.load_real_completed_decision_sources_with_cht_v1(REPO),
        )


def test_onl_adapted_historical_plus_exact10_sources_passes_generic() -> None:
    result = generic.reconcile_completed_human_decisions_v1(
        _adapted_historical(),
        subject.load_real_completed_decision_sources_with_cht_v1(REPO),
    )
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY


def test_exact10_source_composition_is_collision_free() -> None:
    sources = subject.load_real_completed_decision_sources_with_cht_v1(REPO)
    assert len(sources) == 10
    assert tuple(len(source.facts) for source in sources) == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert len({source.binding.stable_identity for source in sources}) == 10
    assert len({source.binding.review_unit_id for source in sources}) == 10
    event_ids = [fact.canonical_event_id for source in sources for fact in source.facts]
    assert len(event_ids) == len(set(event_ids)) == 83


def test_source_loader_calls_neq_loader_once(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subject.neq_successor.load_real_completed_decision_sources_with_neq_v1
    calls: list[Path] = []

    def wrapped(repo_root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls.append(repo_root)
        return original(repo_root)

    monkeypatch.setattr(
        subject.neq_successor,
        "load_real_completed_decision_sources_with_neq_v1",
        wrapped,
    )
    subject.load_real_completed_decision_sources_with_cht_v1(REPO)
    assert calls == [REPO]


def test_source_loader_rejects_cht_collision_with_predecessor78(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = subject.neq_successor.load_real_completed_decision_sources_with_neq_v1(REPO)
    cht = subject.project_cht_completed_decision_v1(repo_root=REPO)
    collision = replace(
        cht,
        facts=(
            replace(cht.facts[0], canonical_event_id=existing[0].facts[0].canonical_event_id),
            *cht.facts[1:],
        ),
    )
    monkeypatch.setattr(subject, "project_cht_completed_decision_v1", lambda *, repo_root: collision)
    with pytest.raises(ERROR, match="REAL_NORMALIZED_FACT_EVENT_COLLISION"):
        subject.load_real_completed_decision_sources_with_cht_v1(REPO)


def test_source_loader_rejects_source_facts_not_exact5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cht = subject.project_cht_completed_decision_v1(repo_root=REPO)
    short = replace(cht, facts=cht.facts[:-1])
    monkeypatch.setattr(subject, "project_cht_completed_decision_v1", lambda *, repo_root: short)
    with pytest.raises(ERROR, match="FACT_COUNT_MISMATCH"):
        subject.load_real_completed_decision_sources_with_cht_v1(REPO)


def test_source_loader_rejects_one_fact_wrong_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cht = subject.project_cht_completed_decision_v1(repo_root=REPO)
    wrong = replace(
        cht,
        facts=(replace(cht.facts[0], review_unit_id="WRONG_UNIT"), *cht.facts[1:]),
    )
    monkeypatch.setattr(subject, "project_cht_completed_decision_v1", lambda *, repo_root: wrong)
    with pytest.raises(ERROR, match="REVIEW_UNIT_OR_FACT_COUNT_MISMATCH"):
        subject.load_real_completed_decision_sources_with_cht_v1(REPO)


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


def test_real_reconciliation_counts_training_and_final_cht_authority() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_cht_v1(REPO)
    assert result.review_summary == checker.EXPECTED_REVIEW_SUMMARY
    assert Counter(fact.training_disposition for fact in result.normalized_facts) == {
        generic.TRAINING_INCLUDE: 19,
        generic.TRAINING_EXCLUDE: 64,
    }
    cht_source = subject.project_cht_completed_decision_v1(repo_root=REPO)
    expected_authority = json.dumps(
        [cht_source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    cht_rows = [
        row for row in result.reconciled_rows if row["canonical_event_id"] in subject._CHT_EVENT_IDS
    ]
    assert len(cht_rows) == 5
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["current_status_authority_sources_json"] == expected_authority
        for row in cht_rows
    )


def test_exact_cht_delta_relative_to_published_neq_chain() -> None:
    result = subject.reconcile_real_completed_human_decisions_with_cht_v1(REPO)
    summary = result.review_summary
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    assert summary["completed_positive_event_count"] - 78 == 5
    assert summary["completed_positive_unit_count"] - 9 == 1
    assert summary["completed_total_event_count"] - 102 == 5
    assert summary["completed_total_unit_count"] - 13 == 1
    assert summary["unreviewed_event_count"] - 236 == -5
    assert summary["unreviewed_unit_count"] - 118 == -1
    assert summary["in_progress_event_count"] == 0
    assert dispositions[generic.TRAINING_INCLUDE] - 19 == 0
    assert dispositions[generic.TRAINING_EXCLUDE] - 59 == 5


def test_source_order_is_deterministic() -> None:
    rows = _adapted_historical()
    sources = subject.load_real_completed_decision_sources_with_cht_v1(REPO)
    assert generic.reconcile_completed_human_decisions_v1(
        rows, sources
    ) == generic.reconcile_completed_human_decisions_v1(
        rows, tuple(reversed(sources))
    )


def test_production_pipeline_calls_all_delegates_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_neq = subject.neq_successor.load_real_completed_decision_sources_with_neq_v1
    original_cht = subject.cht_ingestion_owner.load_frozen_formal_decision_v1
    original_onl = subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()

    def counted_neq(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["neq"] += 1
        return original_neq(root)

    def counted_cht(root: Path) -> dict[str, object]:
        calls["cht"] += 1
        return original_cht(root)

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl"] += 1
        return original_onl(rows)  # type: ignore[arg-type]

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    monkeypatch.setattr(subject.neq_successor, "load_real_completed_decision_sources_with_neq_v1", counted_neq)
    monkeypatch.setattr(subject.cht_ingestion_owner, "load_frozen_formal_decision_v1", counted_cht)
    monkeypatch.setattr(subject.onl_successor, "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1", counted_onl)
    monkeypatch.setattr(subject.generic, "reconcile_completed_human_decisions_v1", counted_generic)
    subject.reconcile_real_completed_human_decisions_with_cht_v1(REPO)
    assert calls == {"neq": 1, "cht": 1, "onl": 1, "generic": 1}


def test_current_census_stays_published_neq_and_future_is_informational() -> None:
    published = checker._published_census_state(REPO)
    assert published["counts"] == checker.EXPECTED_CURRENT_CENSUS
    derived = checker._verify_future_census_informational(
        subject.project_cht_completed_decision_v1(repo_root=REPO), published
    )
    assert derived == checker.EXPECTED_FUTURE_CENSUS
    assert derived["warhead_only_A"] == 100
    assert derived["linker_plus_warhead_B"] == 44
    assert derived["scaffold_plus_warhead_B2"] == 44
    assert derived["scaffold_only_B3"] == 100
    assert derived["scaffold_plus_linker_plus_warhead_C"] == 100


def test_expected_next_pending_after_cht_is_ozj_informational() -> None:
    published = checker._published_census_state(REPO)
    pending = published["summary"]["top_pending_review_units_by_event_yield"]  # type: ignore[index]
    assert pending[0]["ligand_component_ids"] == ["CHT"]
    assert pending[1] == {
        "ccd_complete_count": 4,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "event_count": 4,
        "exact_pair_count": 4,
        "full_coordinate_count": 4,
        "ligand_component_ids": ["OZJ"],
        "pdb_ids": ["4CL8"],
        "post_source_evidence_count": 4,
        "rank": 2,
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450",
    }


def test_checker_exact4_frozen_bindings_architecture_and_all_gates() -> None:
    report = checker.run_check_v1(REPO)
    assert report["check"] == "PASS"
    assert report["exact4"]["count"] == 4
    assert report["frozen_bindings"]["count"] == 10
    assert report["delegate_runtime_calls"] == {
        "neq_source_loader": 1,
        "cht_ingestion_loader": 1,
        "onl_adapter": 1,
        "generic_reconciler": 1,
    }
    assert report["source_fact_counts"] == checker.EXPECTED_SOURCE_FACT_COUNTS
    assert report["event_collisions"] == 0
    assert report["global_census_update"] == "NOT_DONE"
    assert report["ready_for_external_review"] is True
    assert report["ready_for_training"] is False
    assert report["feature_semantics"] == "AUDIT_REQUIRED_LATER"


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


def test_checker_rejects_frozen_cht_formal_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checker, "CHT_FORMAL_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="FROZEN_SHA256_MISMATCH"):
        checker._verify_frozen_inputs(REPO)

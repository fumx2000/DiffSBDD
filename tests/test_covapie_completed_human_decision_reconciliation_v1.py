from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
import hashlib
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as subject,
)


ERROR = subject.CompletedDecisionReconciliationError


def _binding(
    unit_id: str,
    *,
    schema: str = "synthetic_completed_decision_v1",
    path: str | None = None,
) -> subject.SourceBinding:
    source_path = path or f"synthetic/{unit_id}.json"
    payload = (source_path + schema + unit_id).encode("utf-8")
    return subject.SourceBinding(
        source_path=source_path,
        path_namespace="synthetic",
        byte_count=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        schema_version=schema,
        review_unit_id=unit_id,
    )


def _fact(
    event_id: str,
    binding: subject.SourceBinding,
    *,
    completed: bool = True,
    legacy_status: str = subject.COMPLETED_HUMAN_POSITIVE,
    task: str = subject.TASK_RELEVANT,
    chemistry: str = subject.CHEMISTRY_POSITIVE,
    training: str = subject.TRAINING_INCLUDE,
    excluded: bool = False,
) -> subject.NormalizedCompletedDecisionFact:
    return subject.NormalizedCompletedDecisionFact(
        canonical_event_id=event_id,
        review_unit_id=binding.review_unit_id,
        human_review_completed=completed,
        legacy_completed_review_status=legacy_status,
        task_relevance_disposition=task,
        chemistry_disposition=chemistry,
        training_disposition=training,
        human_training_excluded=excluded,
        source_decision_schema=binding.schema_version,
        source_decision_sha256=binding.sha256,
        source_binding_path=binding.source_path,
    )


def _source(
    binding: subject.SourceBinding,
    event_ids: tuple[str, ...],
    **fact_overrides: object,
) -> subject.NormalizedDecisionSource:
    return subject.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
            _fact(event_id, binding, **fact_overrides) for event_id in event_ids
        ),
    )


def _row(
    rank: int,
    unit_id: str,
    unit_count: int,
    event_id: str,
    status: str = subject.CURRENTLY_UNREVIEWED,
) -> dict[str, str]:
    eligible = status == subject.CURRENTLY_UNREVIEWED
    return {
        "raw_priority_rank": str(rank),
        "raw_review_unit_id": unit_id,
        "raw_unit_event_count": str(unit_count),
        "canonical_event_id": event_id,
        "current_review_status": status,
        "current_status_authority_sources_json": json.dumps(
            ["synthetic/historical_queue.csv"], separators=(",", ":")
        ),
        "calibration_eligible": str(eligible).lower(),
        "calibration_exclusion_reason": "" if eligible else status,
    }


def _historical_rows() -> tuple[dict[str, str], ...]:
    return (
        _row(1, "U_FFQ", 2, "E_FFQ_1"),
        _row(1, "U_FFQ", 2, "E_FFQ_2"),
        _row(2, "U_POA", 2, "E_POA_1"),
        _row(2, "U_POA", 2, "E_POA_2"),
        _row(3, "U_NEG", 1, "E_NEG", subject.COMPLETED_HUMAN_NEGATIVE),
        _row(4, "U_PROGRESS", 1, "E_PROGRESS", subject.CURRENTLY_IN_PROGRESS),
    )


def _ffq_binding() -> subject.SourceBinding:
    return _binding(
        subject.FFQ_REVIEW_UNIT_ID,
        schema=subject.FFQ_FORMAL_DECISION_SCHEMA,
        path="synthetic/ffq_formal.json",
    )


def _ffq_formal() -> dict[str, object]:
    events: list[dict[str, object]] = []
    for pdb_id in ("3VCY", "4R7U"):
        for index in range(4):
            event = {
                "canonical_event_id": (
                    "COVAPIE_CYS_SG_EVENT_V1:"
                    f"{pdb_id}:{index}:CYS:1-:SG:A:FFQ:C1"
                ),
                "pdb_id": pdb_id,
                "chemistry_identity": "COVALENT_CHEMISTRY_SUPPORTED",
                "event_training_use_decision": (
                    subject.TRAINING_INCLUDE
                    if pdb_id == "3VCY"
                    else subject.TRAINING_EXCLUDE
                ),
            }
            if pdb_id == "4R7U":
                event.update(
                    negative_chemistry=False,
                    task_domain_negative=False,
                )
            events.append(event)
    return {
        "schema_version": subject.FFQ_FORMAL_DECISION_SCHEMA,
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "review_unit_id": subject.FFQ_REVIEW_UNIT_ID,
        "ligand_component_id": "FFQ",
        "human_approval": {"approval_recorded": True},
        "unit_level_human_decisions": {
            "training_domain_relevance_decision": (
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            ),
            "chemistry_identity_decision": "COVALENT_CHEMISTRY_SUPPORTED",
            "chemistry_negative": False,
            "task_domain_negative": False,
        },
        "event_level_human_decisions": events,
    }


def _poa_binding() -> subject.SourceBinding:
    return _binding(
        subject.POA_REVIEW_UNIT_ID,
        schema=subject.POA_FORMAL_DECISION_SCHEMA,
        path="synthetic/poa_formal.json",
    )


def _poa_group(pdb_id: str) -> dict[str, object]:
    excluded = pdb_id == "4I3V"
    group: dict[str, object] = {
        "pdb_id": pdb_id,
        "CHEMISTRY_POSITIVE": True,
        "chemistry_identity": "COVALENT_CHEMISTRY_SUPPORTED",
        "negative_chemistry": False,
        "TASK_RELEVANT_COVALENT_EVENT": True,
        "task_domain_negative": False,
        "event_training_use_decision": (
            subject.TRAINING_EXCLUDE if excluded else subject.TRAINING_INCLUDE
        ),
        "human_training_excluded": excluded,
        "training_exclusion_scope": subject.TRAINING_EXCLUDE if excluded else "NONE",
        "ligand_component_id": "POA",
        "ligand_reactive_atom_id": "C2",
        "protein_component_id": "CYS",
        "protein_reactive_atom_id": "SG",
        "event_count": 8,
        "canonical_event_ids": [
            "COVAPIE_CYS_SG_EVENT_V1:"
            f"{pdb_id}:{index}:CYS:1-:SG:A:POA:C2"
            for index in range(8)
        ],
    }
    if excluded:
        group["training_exclusion_disposition"] = (
            "HUMAN_EXCLUDE_FROM_TRAINING_ONLY"
        )
    return group


def _poa_formal() -> dict[str, object]:
    return {
        "schema_version": subject.POA_FORMAL_DECISION_SCHEMA,
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "review_unit_id": subject.POA_REVIEW_UNIT_ID,
        "ligand_component_id": "POA",
        "human_approval": {"approval_recorded": True},
        "local_review_transition": {
            "prior_review_state": subject.CURRENTLY_UNREVIEWED,
            "materialized_review_state": "COMPLETED_HUMAN_REVIEW",
            "local_completed_human_review_delta": 16,
        },
        "unit_level_human_decisions": {
            "exact_event_count": 16,
            "completed_human_review_event_count": 16,
            "chemistry_positive_event_count": 16,
            "chemistry_negative_event_count": 0,
            "human_training_excluded_positive_event_count": 8,
            "subgroup_count": 2,
        },
        "subgroup_human_decisions": [_poa_group("4I3U"), _poa_group("4I3V")],
    }


def test_normalized_fact_exact_fields_and_current_enums() -> None:
    assert tuple(field.name for field in fields(subject.NormalizedCompletedDecisionFact)) == (
        "canonical_event_id",
        "review_unit_id",
        "human_review_completed",
        "legacy_completed_review_status",
        "task_relevance_disposition",
        "chemistry_disposition",
        "training_disposition",
        "human_training_excluded",
        "source_decision_schema",
        "source_decision_sha256",
        "source_binding_path",
    )
    assert {subject.TASK_RELEVANT, subject.TASK_NOT_RELEVANT} == {
        "RELEVANT",
        "NOT_RELEVANT",
    }
    assert {
        subject.CHEMISTRY_POSITIVE,
        subject.CHEMISTRY_NEGATIVE,
        subject.CHEMISTRY_NOT_ESTABLISHED,
    } == {"POSITIVE", "NEGATIVE", "NOT_ESTABLISHED"}
    assert {
        subject.TRAINING_INCLUDE,
        subject.TRAINING_EXCLUDE,
        subject.TRAINING_NOT_APPLICABLE,
    } == {"INCLUDE", "EXCLUDE_FROM_TRAINING_ONLY", "NOT_APPLICABLE"}


def test_ffq_projection_exact8_and_4r7u_stays_review_positive() -> None:
    source = subject._project_ffq_decision_mapping_v1(_ffq_formal(), _ffq_binding())
    assert len(source.facts) == 8
    assert {fact.chemistry_disposition for fact in source.facts} == {
        subject.CHEMISTRY_POSITIVE
    }
    included = [fact for fact in source.facts if ":3VCY:" in fact.canonical_event_id]
    excluded = [fact for fact in source.facts if ":4R7U:" in fact.canonical_event_id]
    assert len(included) == len(excluded) == 4
    assert all(fact.training_disposition == subject.TRAINING_INCLUDE for fact in included)
    assert all(not fact.human_training_excluded for fact in included)
    assert all(fact.training_disposition == subject.TRAINING_EXCLUDE for fact in excluded)
    assert all(fact.human_training_excluded for fact in excluded)
    assert all(
        fact.legacy_completed_review_status == subject.COMPLETED_HUMAN_POSITIVE
        for fact in excluded
    )


def test_poa_projection_exact16_and_g2_stays_review_positive() -> None:
    source = subject._project_poa_decision_mapping_v1(_poa_formal(), _poa_binding())
    assert len(source.facts) == 16
    g1 = [fact for fact in source.facts if ":4I3U:" in fact.canonical_event_id]
    g2 = [fact for fact in source.facts if ":4I3V:" in fact.canonical_event_id]
    assert len(g1) == len(g2) == 8
    assert all(fact.training_disposition == subject.TRAINING_INCLUDE for fact in g1)
    assert all(not fact.human_training_excluded for fact in g1)
    assert all(fact.training_disposition == subject.TRAINING_EXCLUDE for fact in g2)
    assert all(fact.human_training_excluded for fact in g2)
    assert all(fact.chemistry_disposition == subject.CHEMISTRY_POSITIVE for fact in g2)
    assert all(
        fact.legacy_completed_review_status == subject.COMPLETED_HUMAN_POSITIVE
        for fact in g2
    )


def test_generic_overlay_preserves_rows_and_updates_all_owned_fields() -> None:
    historical = _historical_rows()
    ffq_binding = _binding("U_FFQ")
    source = _source(ffq_binding, ("E_FFQ_1", "E_FFQ_2"))
    result = subject.reconcile_completed_human_decisions_v1(historical, (source,))
    before = {row["canonical_event_id"]: row for row in historical}
    after = {row["canonical_event_id"]: row for row in result.reconciled_rows}
    owned = {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
    for event_id in ("E_FFQ_1", "E_FFQ_2"):
        assert after[event_id]["current_review_status"] == (
            subject.COMPLETED_HUMAN_POSITIVE
        )
        assert json.loads(after[event_id]["current_status_authority_sources_json"]) == [
            ffq_binding.source_path
        ]
        assert after[event_id]["calibration_eligible"] == "false"
        assert after[event_id]["calibration_exclusion_reason"] == (
            subject.COMPLETED_HUMAN_POSITIVE
        )
        for field in subject.HISTORICAL_RECONCILIATION_HEADER:
            if field not in owned:
                assert after[event_id][field] == before[event_id][field]
    for event_id in set(before) - {"E_FFQ_1", "E_FFQ_2"}:
        assert after[event_id] == before[event_id]
    assert result.review_summary == {
        "universe_event_count": 6,
        "universe_review_unit_count": 4,
        "completed_positive_event_count": 2,
        "completed_positive_unit_count": 1,
        "completed_negative_event_count": 1,
        "completed_negative_unit_count": 1,
        "completed_total_event_count": 3,
        "completed_total_unit_count": 2,
        "in_progress_event_count": 1,
        "in_progress_unit_count": 1,
        "unreviewed_event_count": 2,
        "unreviewed_unit_count": 1,
    }


def test_task_not_relevant_with_chemistry_not_established_is_valid() -> None:
    historical = (_row(1, "U_TASK_NEG", 1, "E_TASK_NEG"),)
    binding = _binding("U_TASK_NEG")
    fact = _fact(
        "E_TASK_NEG",
        binding,
        legacy_status=subject.COMPLETED_HUMAN_NEGATIVE,
        task=subject.TASK_NOT_RELEVANT,
        chemistry=subject.CHEMISTRY_NOT_ESTABLISHED,
        training=subject.TRAINING_NOT_APPLICABLE,
    )
    source = subject.NormalizedDecisionSource(binding, (fact,))
    result = subject.reconcile_completed_human_decisions_v1(historical, (source,))
    assert result.normalized_facts[0].chemistry_disposition == (
        subject.CHEMISTRY_NOT_ESTABLISHED
    )
    assert result.reconciled_rows[0]["current_review_status"] == (
        subject.COMPLETED_HUMAN_NEGATIVE
    )


def test_reconciliation_is_deterministic_and_source_order_independent() -> None:
    historical = _historical_rows()
    ffq = _source(_binding("U_FFQ", path="synthetic/z_ffq.json"), ("E_FFQ_1", "E_FFQ_2"))
    poa = _source(_binding("U_POA", path="synthetic/a_poa.json"), ("E_POA_1", "E_POA_2"))
    first = subject.reconcile_completed_human_decisions_v1(historical, (ffq, poa))
    second = subject.reconcile_completed_human_decisions_v1(historical, (poa, ffq))
    third = subject.reconcile_completed_human_decisions_v1(historical, (ffq, poa))
    assert first == second == third
    assert [binding.source_path for binding in first.source_bindings] == [
        "synthetic/a_poa.json",
        "synthetic/z_ffq.json",
    ]


def test_portable_ffq_like_and_poa_like_reconciliation() -> None:
    historical = _historical_rows()
    ffq_binding = _binding("U_FFQ", path="synthetic/z_ffq.json")
    ffq = subject.NormalizedDecisionSource(
        ffq_binding,
        (
            _fact("E_FFQ_1", ffq_binding),
            _fact(
                "E_FFQ_2",
                ffq_binding,
                training=subject.TRAINING_EXCLUDE,
                excluded=True,
            ),
        ),
    )
    poa_binding = _binding("U_POA", path="synthetic/a_poa.json")
    poa = subject.NormalizedDecisionSource(
        poa_binding,
        (
            _fact("E_POA_1", poa_binding),
            _fact(
                "E_POA_2",
                poa_binding,
                training=subject.TRAINING_EXCLUDE,
                excluded=True,
            ),
        ),
    )
    result = subject.reconcile_completed_human_decisions_v1(
        historical, (ffq, poa)
    )
    assert result.review_summary == {
        "universe_event_count": 6,
        "universe_review_unit_count": 4,
        "completed_positive_event_count": 4,
        "completed_positive_unit_count": 2,
        "completed_negative_event_count": 1,
        "completed_negative_unit_count": 1,
        "completed_total_event_count": 5,
        "completed_total_unit_count": 3,
        "in_progress_event_count": 1,
        "in_progress_unit_count": 1,
        "unreviewed_event_count": 0,
        "unreviewed_unit_count": 0,
    }
    assert [binding.source_path for binding in result.source_bindings] == [
        "synthetic/a_poa.json",
        "synthetic/z_ffq.json",
    ]
    excluded = [fact for fact in result.normalized_facts if fact.human_training_excluded]
    assert len(excluded) == 2
    assert all(
        fact.chemistry_disposition == subject.CHEMISTRY_POSITIVE
        and fact.legacy_completed_review_status == subject.COMPLETED_HUMAN_POSITIVE
        for fact in excluded
    )


def test_source_sha_and_byte_count_drift_fail_closed() -> None:
    payload = b'{"review_unit_id":"U","schema_version":"synthetic_v1"}'
    expected_sha = hashlib.sha256(payload).hexdigest()
    binding, formal = subject._verified_source_binding(
        payload,
        source_path="synthetic/formal.json",
        path_namespace="synthetic",
        expected_byte_count=len(payload),
        expected_sha256=expected_sha,
        expected_schema="synthetic_v1",
        expected_review_unit_id="U",
        label="SYNTHETIC_FORMAL_DECISION",
    )
    assert binding.sha256 == expected_sha
    assert formal["review_unit_id"] == "U"
    changed = payload.replace(b'"U"', b'"V"')
    with pytest.raises(ERROR, match="SOURCE_SHA256_MISMATCH:SYNTHETIC_FORMAL_DECISION"):
        subject._verified_source_binding(
            changed,
            source_path="synthetic/formal.json",
            path_namespace="synthetic",
            expected_byte_count=len(payload),
            expected_sha256=expected_sha,
            expected_schema="synthetic_v1",
            expected_review_unit_id="U",
            label="SYNTHETIC_FORMAL_DECISION",
        )
    with pytest.raises(ERROR, match="SOURCE_BYTE_COUNT_MISMATCH:SYNTHETIC_FORMAL_DECISION"):
        subject._verified_source_binding(
            payload[:-1],
            source_path="synthetic/formal.json",
            path_namespace="synthetic",
            expected_byte_count=len(payload),
            expected_sha256=expected_sha,
            expected_schema="synthetic_v1",
            expected_review_unit_id="U",
            label="SYNTHETIC_FORMAL_DECISION",
        )


def test_source_schema_mismatch_fails_closed() -> None:
    formal = _ffq_formal()
    formal["schema_version"] = "drift"
    with pytest.raises(ERROR, match="FFQ_FORMAL_DECISION_IDENTITY_INVALID"):
        subject._project_ffq_decision_mapping_v1(formal, _ffq_binding())


@pytest.mark.parametrize("mode", ("duplicate", "missing"))
def test_ffq_expected_event_coverage_fails_closed(mode: str) -> None:
    formal = _ffq_formal()
    events = formal["event_level_human_decisions"]
    if mode == "duplicate":
        events[-1] = deepcopy(events[0])
    else:
        events.pop()
    with pytest.raises(ERROR):
        subject._project_ffq_decision_mapping_v1(formal, _ffq_binding())


def test_poa_g2_chemistry_negative_drift_fails_closed() -> None:
    formal = _poa_formal()
    g2 = next(
        group
        for group in formal["subgroup_human_decisions"]
        if group["pdb_id"] == "4I3V"
    )
    g2["CHEMISTRY_POSITIVE"] = False
    g2["negative_chemistry"] = True
    with pytest.raises(ERROR, match="POA_SUBGROUP_DISPOSITION_INVALID:4I3V"):
        subject._project_poa_decision_mapping_v1(formal, _poa_binding())


def test_duplicate_canonical_event_in_one_source_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    binding = _binding("U")
    fact = _fact("E", binding)
    source = subject.NormalizedDecisionSource(binding, (fact, fact))
    with pytest.raises(ERROR, match="SOURCE_CANONICAL_EVENT_DUPLICATE:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_same_source_supplied_twice_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    source = _source(_binding("U"), ("E",))
    with pytest.raises(ERROR, match="SOURCE_BINDING_DUPLICATE"):
        subject.reconcile_completed_human_decisions_v1(
            historical, (source, source)
        )


def test_cross_source_ffq_poa_event_collision_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    ffq = _source(_binding("U", path="synthetic/ffq.json"), ("E",))
    poa = _source(_binding("U", path="synthetic/poa.json"), ("E",))
    with pytest.raises(ERROR, match="CROSS_SOURCE_EVENT_COLLISION:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (ffq, poa))


def test_partial_review_unit_fails_closed() -> None:
    historical = (_row(1, "U", 2, "E1"), _row(1, "U", 2, "E2"))
    source = _source(_binding("U"), ("E1",))
    with pytest.raises(ERROR, match="SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH:U"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_extra_event_or_review_unit_mismatch_fails_closed() -> None:
    historical = (
        _row(1, "U1", 2, "E1"),
        _row(1, "U1", 2, "E2"),
        _row(2, "U2", 1, "E3"),
    )
    binding = _binding("U1")
    source = _source(binding, ("E1", "E2", "E3"))
    with pytest.raises(ERROR, match="FACT_HISTORICAL_REVIEW_UNIT_MISMATCH:E3"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_fact_source_review_unit_mismatch_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    binding = _binding("U")
    fact = replace(_fact("E", binding), review_unit_id="OTHER")
    source = subject.NormalizedDecisionSource(binding, (fact,))
    with pytest.raises(ERROR, match="FACT_SOURCE_REVIEW_UNIT_MISMATCH:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_unknown_event_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    source = _source(_binding("U"), ("UNKNOWN",))
    with pytest.raises(ERROR, match="EVENT_NOT_IN_HISTORICAL_UNIVERSE:UNKNOWN"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


@pytest.mark.parametrize(
    "prior_status",
    (
        subject.COMPLETED_HUMAN_POSITIVE,
        subject.COMPLETED_HUMAN_NEGATIVE,
        subject.CURRENTLY_IN_PROGRESS,
        subject.COMPLETED_PARTIAL_AUTHORITY,
        subject.CURRENT_RUNTIME_MODEL_USABLE,
        subject.PUBLISHED_EXACT_AUTO_NEGATIVE,
    ),
)
def test_prior_state_must_be_currently_unreviewed(prior_status: str) -> None:
    historical = (_row(1, "U", 1, "E", prior_status),)
    source = _source(_binding("U"), ("E",))
    with pytest.raises(ERROR, match="PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_unknown_historical_status_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E", "UNKNOWN_REVIEW_STATUS"),)
    with pytest.raises(ERROR, match="HISTORICAL_REVIEW_STATUS_INVALID:E"):
        subject.reconcile_completed_human_decisions_v1(historical, ())


def test_human_review_completed_false_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    source = _source(_binding("U"), ("E",), completed=False)
    with pytest.raises(ERROR, match="HUMAN_REVIEW_NOT_COMPLETED:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


@pytest.mark.parametrize(
    ("training", "excluded"),
    (
        (subject.TRAINING_EXCLUDE, False),
        (subject.TRAINING_INCLUDE, True),
        (subject.TRAINING_NOT_APPLICABLE, True),
    ),
)
def test_training_exclusion_inconsistency_fails_closed(
    training: str, excluded: bool
) -> None:
    historical = (_row(1, "U", 1, "E"),)
    source = _source(
        _binding("U"), ("E",), training=training, excluded=excluded
    )
    with pytest.raises(ERROR, match="TRAINING_EXCLUSION_INCONSISTENT:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


@pytest.mark.parametrize("kind", ("POA_G2", "FFQ_4R7U"))
def test_training_excluded_positive_cannot_be_legacy_negative(kind: str) -> None:
    if kind == "POA_G2":
        projected = subject._project_poa_decision_mapping_v1(
            _poa_formal(), _poa_binding()
        )
        original = next(
            fact for fact in projected.facts if ":4I3V:" in fact.canonical_event_id
        )
    else:
        projected = subject._project_ffq_decision_mapping_v1(
            _ffq_formal(), _ffq_binding()
        )
        original = next(
            fact for fact in projected.facts if ":4R7U:" in fact.canonical_event_id
        )
    binding = replace(projected.binding, review_unit_id="U")
    bad = replace(
        original,
        canonical_event_id="E",
        review_unit_id="U",
        legacy_completed_review_status=subject.COMPLETED_HUMAN_NEGATIVE,
    )
    source = subject.NormalizedDecisionSource(binding, (bad,))
    with pytest.raises(ERROR, match="POSITIVE_REVIEW_DISPOSITION_INVALID:E"):
        subject.reconcile_completed_human_decisions_v1(
            (_row(1, "U", 1, "E"),), (source,)
        )


def test_task_not_relevant_with_explicit_positive_chemistry_is_valid_and_not_conflated() -> None:
    historical = (_row(1, "U", 1, "E"),)
    source = _source(
        _binding("U"),
        ("E",),
        legacy_status=subject.COMPLETED_HUMAN_NEGATIVE,
        task=subject.TASK_NOT_RELEVANT,
        chemistry=subject.CHEMISTRY_POSITIVE,
        training=subject.TRAINING_NOT_APPLICABLE,
    )
    result = subject.reconcile_completed_human_decisions_v1(historical, (source,))
    assert result.normalized_facts[0].chemistry_disposition == (
        subject.CHEMISTRY_POSITIVE
    )
    assert result.reconciled_rows[0]["current_review_status"] == (
        subject.COMPLETED_HUMAN_NEGATIVE
    )


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("task_relevance_disposition", "UNKNOWN", "TASK_RELEVANCE_DISPOSITION_INVALID"),
        ("chemistry_disposition", "UNKNOWN", "CHEMISTRY_DISPOSITION_INVALID"),
        ("training_disposition", "UNKNOWN", "TRAINING_DISPOSITION_INVALID"),
        ("legacy_completed_review_status", "UNKNOWN", "LEGACY_COMPLETED_STATUS_INVALID"),
    ),
)
def test_unknown_enum_fails_closed(field: str, value: str, token: str) -> None:
    historical = (_row(1, "U", 1, "E"),)
    binding = _binding("U")
    fact = replace(_fact("E", binding), **{field: value})
    source = subject.NormalizedDecisionSource(binding, (fact,))
    with pytest.raises(ERROR, match=token + ":E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_malformed_authority_source_json_fails_closed() -> None:
    row = _row(1, "U", 1, "E")
    row["current_status_authority_sources_json"] = "[not-json"
    with pytest.raises(ERROR, match="AUTHORITY_SOURCE_JSON_MALFORMED:E"):
        subject.reconcile_completed_human_decisions_v1((row,), ())


def test_duplicate_historical_event_fails_closed() -> None:
    rows = (_row(1, "U1", 1, "E"), _row(2, "U2", 1, "E"))
    with pytest.raises(ERROR, match="HISTORICAL_CANONICAL_EVENT_DUPLICATE_OR_EMPTY"):
        subject.reconcile_completed_human_decisions_v1(rows, ())


def test_raw_unit_event_count_inconsistent_fails_closed() -> None:
    rows = (_row(1, "U", 3, "E1"), _row(1, "U", 3, "E2"))
    with pytest.raises(ERROR, match="RAW_UNIT_EVENT_COUNT_INCONSISTENT:U"):
        subject.reconcile_completed_human_decisions_v1(rows, ())


def test_fact_source_provenance_mismatch_fails_closed() -> None:
    historical = (_row(1, "U", 1, "E"),)
    binding = _binding("U")
    fact = replace(_fact("E", binding), source_decision_sha256="0" * 64)
    source = subject.NormalizedDecisionSource(binding, (fact,))
    with pytest.raises(ERROR, match="FACT_SOURCE_PROVENANCE_MISMATCH:E"):
        subject.reconcile_completed_human_decisions_v1(historical, (source,))


def test_production_owner_has_no_materialization_or_model_dependency() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "import torch",
        "tempfile",
        "os.replace",
        "_atomic_write",
        "materialize_v1",
        "Trainer.fit",
        "backward(",
        "optimizer.step",
    ):
        assert forbidden not in source

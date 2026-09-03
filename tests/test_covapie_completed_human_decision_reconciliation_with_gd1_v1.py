from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, replace
import hashlib
import importlib.util
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_4m5_v1
    as four_m5_predecessor,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_gd1_v1 as subject,
)
from covalent_ext import (
    covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1
    as gd1_ingestion_owner,
)


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_gd1_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_gd1_v1.py"
)
FORMAL_PATH = gd1_ingestion_owner.FORMAL_DECISION_RELATIVE.as_posix()
GENERIC_FIELDS = (
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
FORBIDDEN_RICH_FIELDS = (
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "role_profile",
    "selected_candidate",
    "warhead_atoms",
    "linker_atoms",
    "scaffold_atoms",
    "boundary_bonds",
    "canonical_mask_applicability",
    "PRE_geometry",
    "PRE_topology",
    "POST_geometry",
    "warhead_type",
    "reaction_family",
    "future_training_candidate",
    "training_admission",
    "tensor_target",
    "training_use_allowed",
    "training_materialization_allowed",
    "current_runtime_model_usable",
)
BEFORE_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 107,
    "completed_positive_unit_count": 16,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 135,
    "completed_total_unit_count": 21,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 203,
    "unreviewed_unit_count": 110,
}
AFTER_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 111,
    "completed_positive_unit_count": 17,
    "completed_negative_event_count": 28,
    "completed_negative_unit_count": 5,
    "completed_total_event_count": 139,
    "completed_total_unit_count": 22,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 199,
    "unreviewed_unit_count": 109,
}
ALLOWED_CHANGED_FIELDS = {
    "current_review_status",
    "current_status_authority_sources_json",
    "calibration_eligible",
    "calibration_exclusion_reason",
}


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return gd1_ingestion_owner.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def projection(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_gd1_binding_v1(bound)


@pytest.fixture(scope="module")
def source_chains() -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
]:
    before = four_m5_predecessor.load_real_completed_decision_sources_with_4m5_v1(
        ROOT
    )
    after = subject.load_real_completed_decision_sources_with_gd1_v1(ROOT)
    return before, after


@pytest.fixture(scope="module")
def reconciliations() -> tuple[
    generic.ReconciliationResult, generic.ReconciliationResult
]:
    before = (
        four_m5_predecessor.reconcile_real_completed_human_decisions_with_4m5_v1(
            ROOT
        )
    )
    after = subject.reconcile_real_completed_human_decisions_with_gd1_v1(ROOT)
    return before, after


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location(
        "gd1_reconciliation_checker", ROOT / CHECKER_RELATIVE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mutated_bound(
    bound: dict[str, object], section: str, key: str, value: object
) -> dict[str, object]:
    candidate = copy.deepcopy(bound)
    formal = candidate["formal"]
    assert isinstance(formal, dict)
    target = formal[section]
    assert isinstance(target, dict)
    target[key] = value
    return candidate


def _replace_source_fact(
    source: generic.NormalizedDecisionSource, **updates: object
) -> generic.NormalizedDecisionSource:
    facts = (replace(source.facts[0], **updates), *source.facts[1:])
    return replace(source, facts=facts)


def test_public_api_is_exact4() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithGD1Error",
        "project_gd1_completed_decision_v1",
        "load_real_completed_decision_sources_with_gd1_v1",
        "reconcile_real_completed_human_decisions_with_gd1_v1",
    )


def test_direct_predecessor_and_runtime_dependencies_are_exact() -> None:
    tree = ast.parse((ROOT / SUBJECT_RELATIVE).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name.startswith("covapie_")
    }
    assert imports == {
        "covapie_completed_human_decision_reconciliation_v1",
        "covapie_completed_human_decision_reconciliation_with_4m5_v1",
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1",
    }
    text = (ROOT / SUBJECT_RELATIVE).read_text(encoding="utf-8")
    assert "with_cer" not in text.lower()
    assert "with_1n0" not in text.lower()


def test_published_owner_identity_and_formal_validator_lifecycle(
    bound: dict[str, object],
) -> None:
    payload = (
        ROOT
        / "src/covalent_ext/"
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1.py"
    ).read_bytes()
    assert len(payload) == 95722
    assert hashlib.sha256(payload).hexdigest() == (
        "b9d87c844759ce5e6fd9b8aafb411854113fccb3ef00941b21f0eb79a4751670"
    )
    assert bound["formal_validator_provenance_identity_only"] is True
    assert bound["formal_validator_imported"] is False
    assert bound["formal_validator_executed"] is False
    assert bound.get("formal_validator_subprocess", False) is False


def test_rich_authority_preprojection_is_exact(
    bound: dict[str, object],
) -> None:
    events = subject._validate_rich_gd1_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    assert tuple(row["canonical_event_id"] for row in events) == (
        gd1_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert tuple(row["scaleup_rank"] for row in events) == (691, 692, 693, 694)
    assert formal["identity"]["contexts_collapsed"] is False
    assert formal["human_authorization"]["D1_task_relevance"] == "RELEVANT"
    assert formal["human_authorization"]["D2_chemistry"] == "POSITIVE"
    assert formal["human_authorization"]["D5_training_use"] == (
        "EXCLUDE_FROM_TRAINING_ONLY"
    )


def test_sg_c77_candidate0_roles_exact5_and_pre_post_are_proven(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_gd1_semantics_v1(bound)
    formal = bound["formal"]
    assert isinstance(formal, dict)
    pair = formal["reactive_pair_authority"]
    role = formal["selected_role_partition"]
    tasks = formal["canonical_Exact5_and_sample_applicability"]
    pre = formal["PRE_POST_boundary"]
    post = formal["POST_evidence_boundary"]
    assert (pair["protein_reactive_atom"], pair["ligand_reactive_atom"]) == (
        "SG",
        "C77",
    )
    assert role["human_selected"] is True
    assert role["machine_selected"] is False
    assert role["machine_recommended"] is False
    assert role["W_L_S_counts"] == [2, 0, 11]
    assert role["boundary_bonds"] == [dict(gd1_ingestion_owner.BOUNDARY_BONDS[0])]
    assert tasks["global_canonical_task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task_present"] is False
    assert tasks["sample_applicable_task_ids"] == [0, 3, 4]
    assert tasks["authoritative_task_labels_created"] is False
    assert tasks["event_task_label_rows_materialized"] is False
    assert pre["PRE_source_graph_count_per_event"] == 0
    assert pre["PRE_mapping_count_per_event"] == 0
    assert pre["PRE_mapping_status"] == "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert pre["POST_to_PRE_copy_performed"] is False
    assert pre["PRE_zero_fill_performed"] is False
    assert post["POST_source_evidence_count"] == 4
    assert post["observed_distances_angstrom"] == [
        1.873494,
        1.888634,
        1.881354,
        1.907766,
    ]


@pytest.mark.parametrize(
    ("section", "key", "value", "token"),
    (
        ("human_authorization", "D1_task_relevance", "NOT_RELEVANT", "GD1_D1_D5"),
        ("human_authorization", "D2_chemistry", "NEGATIVE", "GD1_D1_D5"),
        (
            "training_use_boundary",
            "training_use_disposition",
            "INCLUDE",
            "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "human_training_excluded",
            False,
            "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "future_training_admission_candidate",
            True,
            "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
        ),
        (
            "training_use_boundary",
            "current_runtime_model_usable",
            True,
            "GD1_RICH_TRAINING_EXCLUSION_BOUNDARY_INVALID",
        ),
    ),
)
def test_rich_semantic_and_training_positive_mutations_fail_closed(
    bound: dict[str, object],
    section: str,
    key: str,
    value: object,
    token: str,
) -> None:
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error, match=token
    ):
        subject._validate_rich_gd1_semantics_v1(
            _mutated_bound(bound, section, key, value)
        )


def test_exact4_missing_duplicate_and_extra_fail_closed(
    bound: dict[str, object],
) -> None:
    for operation in ("missing", "duplicate", "extra"):
        candidate = copy.deepcopy(bound)
        formal = candidate["formal"]
        assert isinstance(formal, dict)
        events = formal["event_level_formal_human_decisions"]
        assert isinstance(events, list)
        if operation == "missing":
            events.pop()
        elif operation == "duplicate":
            events[-1] = copy.deepcopy(events[0])
        else:
            events.append(copy.deepcopy(events[0]))
        with pytest.raises(subject.CompletedDecisionReconciliationWithGD1Error):
            subject._validate_rich_gd1_semantics_v1(candidate)


def test_generic_fact_schema_is_exact11_and_rich_fields_do_not_leak(
    projection: generic.NormalizedDecisionSource,
) -> None:
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == (
        GENERIC_FIELDS
    )
    subject._prove_generic_fact_schema_v1()
    for fact in projection.facts:
        assert tuple(fact.__dataclass_fields__) == GENERIC_FIELDS
        assert all(not hasattr(fact, field) for field in FORBIDDEN_RICH_FIELDS)


def test_future_training_field_schema_leak_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    @dataclass(frozen=True)
    class LeakedFact:
        canonical_event_id: str
        review_unit_id: str
        human_review_completed: bool
        legacy_completed_review_status: str
        task_relevance_disposition: str
        chemistry_disposition: str
        training_disposition: str
        human_training_excluded: bool
        source_decision_schema: str
        source_decision_sha256: str
        source_binding_path: str
        future_training_candidate: bool

    monkeypatch.setattr(generic, "NormalizedCompletedDecisionFact", LeakedFact)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11",
    ):
        subject._prove_generic_fact_schema_v1()


def test_gd1_generic_projection_provenance_and_positive_exclusion_are_exact(
    projection: generic.NormalizedDecisionSource,
) -> None:
    binding = projection.binding
    assert binding.source_path == FORMAL_PATH
    assert binding.path_namespace == "repository_parent_relative"
    assert binding.byte_count == 33315
    assert binding.sha256 == (
        "ffb8b0c237be2065908d2da6e041fdc57fb2706f19f91ce87d1524bd3aaa9068"
    )
    assert binding.schema_version == "covapie_gd1_exact4_formal_human_decision_v1"
    assert "snapshot" not in binding.source_path
    for fact in projection.facts:
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_EXCLUDE
        assert fact.human_training_excluded is True
        generic._validate_fact(fact, binding)


@pytest.mark.parametrize(
    "updates",
    (
        {"training_disposition": generic.TRAINING_INCLUDE},
        {"human_training_excluded": False},
        {"legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE},
    ),
)
def test_projection_disposition_mutations_fail_closed(
    projection: generic.NormalizedDecisionSource, updates: dict[str, object]
) -> None:
    mutated = _replace_source_fact(projection, **updates)
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GD1_SOURCE_PROJECTION_INVALID",
    ):
        subject._validate_projected_gd1_source_v1(mutated)


def test_ingestion_snapshot_cannot_replace_formal_generic_authority(
    projection: generic.NormalizedDecisionSource,
) -> None:
    snapshot = (
        "data/derived/covalent_small/"
        "covapie_gd1_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_gd1_completed_human_decision_snapshot_v1.json"
    )
    binding = replace(projection.binding, source_path=snapshot)
    facts = tuple(
        replace(fact, source_binding_path=snapshot) for fact in projection.facts
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GD1_SOURCE_PROJECTION_IDENTITY_INVALID",
    ):
        subject._validate_projected_gd1_source_v1(
            replace(projection, binding=binding, facts=facts)
        )


def test_source_chain_17_111_to_18_115_is_append_only(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, after = source_chains
    assert len(before) == 17
    assert sum(len(source.facts) for source in before) == 111
    assert len(after) == 18
    assert sum(len(source.facts) for source in after) == 115
    assert after[:-1] == before
    assert len({source.binding.review_unit_id for source in before}) == 17
    assert len({source.binding.review_unit_id for source in after}) == 18
    assert len({source.binding.stable_identity for source in before}) == 17
    assert len({source.binding.stable_identity for source in after}) == 18
    all_ids = [fact.canonical_event_id for source in after for fact in source.facts]
    assert len(all_ids) == len(set(all_ids)) == 115


def test_predecessor_source_count_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    before, _after = source_chains
    monkeypatch.setattr(
        four_m5_predecessor,
        "load_real_completed_decision_sources_with_4m5_v1",
        lambda _root: before[:-1],
    )
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="PREDECESSOR_WITH_4M5_SOURCE_COMPOSITION_INVALID",
    ):
        subject.load_real_completed_decision_sources_with_gd1_v1(ROOT)


def test_gd1_predecessor_historical_state_is_exact(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, _after = reconciliations
    subject._prove_gd1_predecessor_historical_state_v1(before.reconciled_rows)
    target = [
        row
        for row in before.reconciled_rows
        if row["raw_review_unit_id"] == gd1_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    ]
    assert len(target) == 4
    assert {row["canonical_event_id"] for row in target} == set(
        gd1_ingestion_owner.EXPECTED_EVENT_IDS
    )
    assert {row["raw_priority_rank"] for row in target} == {"21"}
    assert {row["raw_unit_event_count"] for row in target} == {"4"}
    assert {row["current_review_status"] for row in target} == {
        generic.CURRENTLY_UNREVIEWED
    }


def test_historical_prior_drift_and_fifth_unit_event_fail_closed(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, _after = reconciliations
    rows = [dict(row) for row in before.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == gd1_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["raw_priority_rank"] = "22"
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_gd1_predecessor_historical_state_v1(rows)

    rows = [dict(row) for row in before.reconciled_rows]
    rows[100]["raw_review_unit_id"] = gd1_ingestion_owner.EXPECTED_REVIEW_UNIT_ID
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GD1_PREDECESSOR_HISTORICAL_STATE_DRIFT",
    ):
        subject._prove_gd1_predecessor_historical_state_v1(rows)


def test_reconciliation_summary_and_exact_row_delta(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    assert before.review_summary == BEFORE_SUMMARY
    assert after.review_summary == AFTER_SUMMARY
    subject._validate_reconciliation_delta_v1(before, after)
    assert len(after.source_bindings) == 18
    assert len(after.normalized_facts) == 115


def test_only_gd1_exact4_rows_change_only_allowed_exact4_fields(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    target_ids = set(gd1_ingestion_owner.EXPECTED_EVENT_IDS)
    expected_authority = generic._canonical_json([FORMAL_PATH])
    changed = 0
    unchanged = 0
    for left, right in zip(
        before.reconciled_rows, after.reconciled_rows, strict=True
    ):
        assert tuple(left) == tuple(right) == generic.HISTORICAL_RECONCILIATION_HEADER
        assert left["canonical_event_id"] == right["canonical_event_id"]
        fields = {key for key in left if left[key] != right[key]}
        if left["canonical_event_id"] not in target_ids:
            assert fields == set()
            unchanged += 1
            continue
        assert fields == ALLOWED_CHANGED_FIELDS
        assert right["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        assert right["current_status_authority_sources_json"] == expected_authority
        assert right["calibration_eligible"] == "false"
        assert right["calibration_exclusion_reason"] == (
            generic.COMPLETED_HUMAN_POSITIVE
        )
        changed += 1
    assert changed == 4
    assert unchanged == 334


def test_training_exclusion_does_not_change_positive_historical_status(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    _before, after = reconciliations
    target_ids = set(gd1_ingestion_owner.EXPECTED_EVENT_IDS)
    facts = [
        fact
        for fact in after.normalized_facts
        if fact.canonical_event_id in target_ids
    ]
    rows = [
        row
        for row in after.reconciled_rows
        if row["canonical_event_id"] in target_ids
    ]
    assert len(facts) == len(rows) == 4
    assert all(fact.training_disposition == generic.TRAINING_EXCLUDE for fact in facts)
    assert all(fact.human_training_excluded is True for fact in facts)
    assert all(
        fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        for fact in facts
    )
    assert {row["current_review_status"] for row in rows} == {
        generic.COMPLETED_HUMAN_POSITIVE
    }


def test_fifth_reconciliation_row_field_change_fails_closed(
    reconciliations: tuple[generic.ReconciliationResult, generic.ReconciliationResult],
) -> None:
    before, after = reconciliations
    rows = [dict(row) for row in after.reconciled_rows]
    target = next(
        row
        for row in rows
        if row["canonical_event_id"] == gd1_ingestion_owner.EXPECTED_EVENT_IDS[0]
    )
    target["training_disposition"] = generic.TRAINING_EXCLUDE
    mutated = replace(after, reconciled_rows=tuple(rows))
    with pytest.raises(
        subject.CompletedDecisionReconciliationWithGD1Error,
        match="GD1_RECONCILIATION_ROW_ORDER_OR_SCHEMA_CHANGED",
    ):
        subject._validate_reconciliation_delta_v1(before, mutated)


def test_generic_reconciliation_is_deterministic(
    source_chains: tuple[
        tuple[generic.NormalizedDecisionSource, ...],
        tuple[generic.NormalizedDecisionSource, ...],
    ],
) -> None:
    _before, sources = source_chains
    historical = generic.load_real_historical_reconciliation_v1(ROOT)
    adapted = (
        four_m5_predecessor.onl_successor
        ._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    first = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    second = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    assert first == second


def test_candidate_and_future_tracked_lifecycle_profiles(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    assert checker.classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in checker.EXACT4_PATHS),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=checker.EXACT4_PATHS,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN


def test_future_tracked_lifecycle_allows_later_unrelated_commits(checker) -> None:
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=set(checker.EXACT4_PATHS),
        head="later-head",
        origin_main="intermediate-origin",
        ahead=3,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline={*checker.EXACT4_PATHS, "docs/later.md"},
    )


def test_candidate_inventory_is_exact4_without_materialized_outputs() -> None:
    expected = {
        SUBJECT_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        "tests/test_covapie_completed_human_decision_reconciliation_with_gd1_v1.py",
        "docs/covapie_completed_human_decision_reconciliation_with_gd1_v1_guide.md",
    }
    assert not any(
        path.startswith("data/derived/")
        for path in expected
    )
    assert len(expected) == 4

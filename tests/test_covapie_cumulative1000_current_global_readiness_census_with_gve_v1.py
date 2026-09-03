from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import importlib.util
import io
import json
from pathlib import Path

import pytest

from covalent_ext import covapie_completed_human_decision_reconciliation_with_gve_v1 as gve_reconciliation
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_gve_v1 as subject
from covalent_ext import covapie_gve_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


REPO_ROOT = Path(__file__).resolve().parents[1]
ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusWithGVEError
TARGET = set(ingestion.EXPECTED_EVENT_IDS)

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_with_gve", REPO_ROOT / subject.CHECKER_RELATIVE
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _parse(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as stream:
        return tuple(dict(row) for row in csv.DictReader(stream))


@pytest.fixture(scope="session")
def bundle():
    computation = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_gve_v1(
        REPO_ROOT
    )
    predecessor_rows = _parse(REPO_ROOT / subject.PREDECESSOR_CENSUS_RELATIVE)
    manifest = json.loads((REPO_ROOT / subject.PREDECESSOR_MANIFEST_RELATIVE).read_text())
    frozen = subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=predecessor_rows,
        summary={},
        semantic_source_bindings=tuple(manifest["semantic_source_bindings"]),
    )
    reconciliation = gve_reconciliation.reconcile_real_completed_human_decisions_with_gve_v1(
        REPO_ROOT
    )
    matrix = _parse(REPO_ROOT / subject.GVE_EVENT_MATRIX_RELATIVE)
    return {
        "computation": computation,
        "frozen": frozen,
        "reconciliation": reconciliation,
        "matrix": matrix,
    }


def _validate(bundle, computation) -> bool:
    return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_gve_v1(
        computation,
        predecessor_computation=bundle["frozen"],
        reconciliation_result=bundle["reconciliation"],
        matrix_rows=bundle["matrix"],
    )


def _mutate(bundle, event_id: str, **changes: str):
    rows = deepcopy(list(bundle["computation"].rows))
    row = next(row for row in rows if row["canonical_event_id"] == event_id)
    row.update(changes)
    return replace(bundle["computation"], rows=tuple(rows))


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "Cumulative1000CurrentGlobalReadinessCensusWithGVEError",
        "compute_covapie_cumulative1000_current_global_readiness_census_with_gve_v1",
        "validate_covapie_cumulative1000_current_global_readiness_census_with_gve_v1",
        "build_covapie_cumulative1000_current_global_readiness_artifacts_with_gve_v1",
        "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_gve_v1",
    )


def test_exact4_identity_and_matrix_authority(bundle) -> None:
    assert subject.GVE_EXACT4_EVENT_IDS_V1 == ingestion.EXPECTED_EVENT_IDS
    assert subject.GVE_EXACT4_RANKS_V1 == (295, 296, 480, 986)
    assert subject.GVE_REVIEW_UNIT_ID_V1 == "COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222"
    assert subject._validate_gve_matrix_rows_v1(bundle["matrix"]) == bundle["matrix"]


def test_schema_delta_and_overlay_sets_are_exact(bundle) -> None:
    after = {row["canonical_event_id"]: row for row in bundle["computation"].rows}
    before = {row["canonical_event_id"]: row for row in bundle["frozen"].rows}
    assert len(after) == 1000
    assert len(subject.CENSUS_COLUMNS_V1) == 47
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    assert changed == TARGET
    assert sum(before[event_id] == after[event_id] for event_id in set(before) - TARGET) == 996
    assert len(subject._AUTHORIZED_GVE_OVERLAY_FIELDS_V1) == 15
    assert len(subject._AUTHORIZED_BUT_UNCHANGED_GVE_FIELDS_V1) == 3
    assert len(subject._ACTUAL_CHANGED_GVE_FIELDS_V1) == 12
    for event_id in TARGET:
        actual = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        unchanged = {
            field for field in subject._AUTHORIZED_GVE_OVERLAY_FIELDS_V1
            if before[event_id][field] == after[event_id][field]
        }
        assert actual == subject._ACTUAL_CHANGED_GVE_FIELDS_V1
        assert unchanged == subject._AUTHORIZED_BUT_UNCHANGED_GVE_FIELDS_V1


def test_target_semantics_and_authority_sources(bundle) -> None:
    rows = [row for row in bundle["computation"].rows if row["canonical_event_id"] in TARGET]
    assert len(rows) == 4
    for row in rows:
        assert row["current_global_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert row["current_review_status"] == "COMPLETED_HUMAN_NEGATIVE"
        assert row["human_review_completed"] == "true"
        assert row["human_review_authority_source"] == subject.GVE_HUMAN_DECISION_SOURCE
        assert row["chemistry_disposition"] == "POSITIVE"
        assert row["chemistry_authority_source"] == subject.GVE_EVENT_MATRIX_SOURCE
        assert row["positive_authority_source"] == subject.GVE_EVENT_MATRIX_SOURCE
        assert row["task_relevance_disposition"] == "NOT_RELEVANT"
        assert row["task_relevance_authority_source"] == subject.GVE_EVENT_MATRIX_SOURCE
        assert row["training_use_disposition"] == "NOT_APPLICABLE"
        assert row["human_training_excluded"] == "false"
        assert row["training_use_include"] == "false"
        assert row["future_training_admission_candidate"] == "false"
        assert row["training_materialization_allowed_current_source"] == "false"
        assert row["reactive_pair_sample_authoritative"] == "true"
        assert row["role_partition_sample_authoritative"] == "false"
        assert row["role_profile"] == "NOT_ESTABLISHED"
        assert row["canonical_mask_structural_labels_available"] == "false"
        assert row["structurally_applicable_task_ids_json"] == "null"


def test_legacy_gve_and_rank322_are_unchanged(bundle) -> None:
    before = {row["canonical_event_id"]: row for row in bundle["frozen"].rows}
    after = {row["canonical_event_id"]: row for row in bundle["computation"].rows}
    # Build the legacy set without relying on ligand-wide selection in production.
    controls = {
        event_id for event_id in before if ":1XD3:" in event_id and ":GVE:" in event_id
    }
    controls.add(next(row["canonical_event_id"] for row in bundle["frozen"].rows if row["scaleup_rank"] == "322"))
    assert len(controls) == 3
    assert all(before[event_id] == after[event_id] for event_id in controls)


def test_cross_field_populations_are_exact90_plus_exact4(bundle) -> None:
    rows = bundle["computation"].rows
    legacy = {
        row["canonical_event_id"] for row in rows
        if (row["task_relevance_disposition"], row["chemistry_disposition"], row["training_use_disposition"])
        == ("NOT_RELEVANT", "NOT_ESTABLISHED", "NOT_APPLICABLE")
    }
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (row["task_relevance_disposition"], row["chemistry_disposition"], row["training_use_disposition"])
        == ("NOT_RELEVANT", "POSITIVE", "NOT_APPLICABLE")
    }
    assert len(legacy) == 90
    assert orthogonal == TARGET
    assert all(
        row["training_use_disposition"] == "NOT_APPLICABLE"
        for row in rows if row["task_relevance_disposition"] == "NOT_RELEVANT"
    )


def test_global_authority_exact5_and_geometry_counts(bundle) -> None:
    rows = bundle["computation"].rows
    assert Counter(row["chemistry_disposition"] for row in rows) == Counter(
        {"POSITIVE": 136, "NOT_ESTABLISHED": 90, "UNRESOLVED": 774}
    )
    assert Counter(row["task_relevance_disposition"] for row in rows) == Counter(
        {"RELEVANT": 133, "NOT_RELEVANT": 94, "UNRESOLVED": 773}
    )
    assert Counter(row["training_use_disposition"] for row in rows) == Counter(
        {"INCLUDE": 60, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 94, "UNRESOLVED": 774}
    )
    assert sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows) == 136
    assert sum(row["role_partition_sample_authoritative"] == "true" for row in rows) == 132
    assert sum(row["canonical_mask_structural_labels_available"] == "true" for row in rows) == 132
    applicability = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    assert applicability == Counter({0: 132, 1: 52, 2: 52, 3: 132, 4: 132})
    assert sum(row["post_geometry_source_evidence_available"] == "true" for row in rows) == 867
    assert sum(row["post_geometry_sample_authoritative"] == "true" for row in rows) == 21
    assert sum(row["post_geometry_training_target_available"] == "true" for row in rows) == 17
    assert sum(row["pre_geometry_authoritative"] == "true" for row in rows) == 0


def test_summary_uses_population_neutral_keys_and_source_counts(bundle) -> None:
    summary = bundle["computation"].summary
    checker._reject_stale_keys(summary)
    blockers = summary["blockers"]
    assert blockers["population_sizes"] == {
        "chemistry_positive_population_count": 136,
        "training_include_population_count": 60,
    }
    assert blockers["pair_authority_absent"] == {
        "all_1000": 864, "within_chemistry_positive": 0,
    }
    assert blockers["role_authority_absent"] == {
        "all_1000": 868, "within_chemistry_positive": 4,
    }
    assert blockers["missing_tensor_integration"]["within_chemistry_positive"] == 95
    assert blockers["missing_tensor_integration"]["within_training_include"] == 31
    assert blockers["missing_tensor_integration"]["missing_source_composition"]["GVE"] == 4
    assert summary["chemistry"]["positive_source_composition"]["GVE"] == 4
    assert "GVE" not in summary["training_stage"]["future_candidate_source_composition"]


def test_human_review_next_pending_and_boundaries(bundle) -> None:
    summary = bundle["computation"].summary
    assert summary["human_review"] == {
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 147,
        "completed_unit_count": 24,
        "completed_positive_event_count": 115,
        "completed_positive_unit_count": 18,
        "completed_negative_event_count": 32,
        "completed_negative_unit_count": 6,
        "unreviewed_event_count": 191,
        "unreviewed_unit_count": 107,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 191,
        "current_pending_review_unit_count": 107,
    }
    assert summary["top_pending_review_units_by_event_yield"][0]["raw_priority_rank"] == 24
    assert summary["top_pending_review_units_by_event_yield"][0]["review_unit_id"] == subject.NEXT_PENDING_REVIEW_UNIT_ID_V1
    assert summary["top_pending_review_units_by_event_yield"][0]["ligand_component_ids"] == ["LCY"]
    boundary = summary["authority_boundary"]
    assert boundary["GVE_REVIEW_COMPLETED"] is True
    assert boundary["READY_FOR_LCY_REVIEW_PREPARATION"] is True
    assert boundary["LCY_REVIEW_STARTED"] is False
    assert boundary["QUEUE_REFRESH"] is False
    assert boundary["TRAINING_STARTED"] is False


def test_semantic_lineage_exact150(bundle) -> None:
    bindings = bundle["computation"].semantic_source_bindings
    assert len(bindings) == 150
    assert len({(item["path_namespace"], item["path"]) for item in bindings}) == 150
    assert tuple(bindings[:144]) == bundle["frozen"].semantic_source_bindings
    assert [item["artifact_role"] for item in bindings[144:]] == [
        item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("chemistry_disposition", "NOT_ESTABLISHED"),
        ("chemistry_disposition", "NEGATIVE"),
        ("task_relevance_disposition", "RELEVANT"),
        ("training_use_disposition", "INCLUDE"),
        ("training_use_disposition", "EXCLUDE_FROM_TRAINING_ONLY"),
        ("reactive_pair_sample_authoritative", "false"),
        ("role_partition_sample_authoritative", "true"),
        ("role_profile", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        ("canonical_mask_structural_labels_available", "true"),
        ("structurally_applicable_task_ids_json", "[0,3,4]"),
        ("human_training_excluded", "true"),
        ("future_training_admission_candidate", "true"),
        ("post_geometry_training_target_available", "true"),
        ("pre_geometry_authoritative", "true"),
    ),
)
def test_gve_semantic_mutations_fail_closed(bundle, field: str, value: str) -> None:
    mutated = _mutate(bundle, next(iter(TARGET)), **{field: value})
    with pytest.raises(ERROR):
        _validate(bundle, mutated)


def test_non_target_and_outside_exact4_positive_fail_closed(bundle) -> None:
    legacy = next(
        row for row in bundle["computation"].rows
        if row["task_relevance_disposition"] == "NOT_RELEVANT"
        and row["canonical_event_id"] not in TARGET
    )
    mutated = _mutate(
        bundle,
        legacy["canonical_event_id"],
        chemistry_disposition="POSITIVE",
        positive_authority_source=subject.GVE_EVENT_MATRIX_SOURCE,
    )
    with pytest.raises(ERROR):
        _validate(bundle, mutated)


def test_stale_summary_key_fails_closed(bundle) -> None:
    summary = deepcopy(bundle["computation"].summary)
    summary["blockers"]["pair_authority_absent"]["within_positive_132"] = 0
    mutated = replace(bundle["computation"], summary=summary)
    with pytest.raises(ERROR):
        _validate(bundle, mutated)


def test_materialization_outside_authorized_root_fails(tmp_path: Path) -> None:
    with pytest.raises(ERROR, match="OUTPUT_DIRECTORY_NOT_AUTHORIZED"):
        subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_gve_v1(
            REPO_ROOT, output_directory=tmp_path
        )


def test_materialized_outputs_and_deterministic_rebuild(bundle) -> None:
    output = REPO_ROOT / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        name: (output / name).read_bytes()
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    built_once = subject._build_artifacts_from_computation_v1(
        REPO_ROOT, bundle["computation"]
    )
    built_twice = subject._build_artifacts_from_computation_v1(
        REPO_ROOT, bundle["computation"]
    )
    assert materialized == built_once == built_twice
    assert checker._sha(materialized[subject.CENSUS_FILE]) == checker.EXPECTED_CENSUS_SHA256
    assert checker._sha(materialized[subject.SUMMARY_FILE]) == checker.EXPECTED_SUMMARY_SHA256


def test_checker_lifecycle_simulations() -> None:
    assert all(checker.check_lifecycle_simulations_v1().values())

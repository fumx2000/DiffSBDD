from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import csv
import importlib.util
import io
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_v1 as subject,
)


ERROR = subject.Cumulative1000CurrentGlobalReadinessCensusError
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_cumulative1000_current_global_readiness_census_v1",
    REPO
    / "scripts/check_covapie_cumulative1000_current_global_readiness_census_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)

READINESS_SEMANTIC_BUNDLE = (
    "chemistry_disposition",
    "chemistry_authority_source",
    "task_relevance_disposition",
    "task_relevance_authority_source",
    "training_use_disposition",
    "human_training_excluded",
    "reactive_pair_sample_authoritative",
    "reactive_pair_training_target_available",
    "role_partition_sample_authoritative",
    "role_profile",
    "canonical_mask_structural_labels_available",
    "structurally_applicable_task_ids_json",
    "post_geometry_sample_authoritative",
    "post_geometry_training_target_available",
    "training_use_include",
    "future_training_admission_candidate",
    "formal_split_authoritative",
    "formal_split",
    "formal_training_admitted",
    "current_runtime_model_usable",
    "training_materialization_allowed_current_source",
    "positive_authority_source",
)
RUNTIME_POSITIVE_EVENT = (
    "COVAPIE_CYS_SG_EVENT_V1:1NFZ:A:CYS:67-:SG:E:EIP:C12"
)
UNRESOLVED_LEAKAGE_EVENT = (
    "COVAPIE_CYS_SG_EVENT_V1:1ATK:A:CYS:25-:SG:B:E64:C2"
)


@pytest.fixture(scope="session")
def computation() -> subject.Cumulative1000CurrentGlobalReadinessComputationV1:
    return subject.compute_covapie_cumulative1000_current_global_readiness_census_v1(
        REPO
    )


def _mutate_row(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
    predicate,
    **updates: str,
) -> subject.Cumulative1000CurrentGlobalReadinessComputationV1:
    rows = [dict(row) for row in computation.rows]
    index = next(index for index, row in enumerate(rows) if predicate(row))
    rows[index].update(updates)
    return replace(computation, rows=tuple(rows))


def _universe_payload(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _swapped_readiness_computation(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> subject.Cumulative1000CurrentGlobalReadinessComputationV1:
    rows = [dict(row) for row in computation.rows]
    by_event = {row["canonical_event_id"]: row for row in rows}
    runtime = by_event[RUNTIME_POSITIVE_EVENT]
    unresolved = by_event[UNRESOLVED_LEAKAGE_EVENT]
    for field in READINESS_SEMANTIC_BUNDLE:
        runtime[field], unresolved[field] = unresolved[field], runtime[field]
    summary = subject._build_summary(
        rows,
        deepcopy(computation.summary["top_pending_review_units_by_event_yield"]),
    )
    return replace(computation, rows=tuple(rows), summary=summary)


def test_real_happy_path_exact1000_and_readiness(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    assert subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
        computation
    )
    assert len(computation.rows) == 1000
    assert computation.summary["universe"] == {
        "event_count": 1000,
        "unique_canonical_event_id_count": 1000,
        "duplicate_canonical_event_id_count": 0,
        "missing_rank_count": 0,
        "rank_start": 1,
        "rank_end": 1000,
        "unique_pdb_count": 546,
        "unique_ligand_component_count": 416,
        "canonical_event_set_sha256": (
            "f74d4e568d97ac23e2bc2cba2e8473e6705b726daf92204868efb1afbe0453ce"
        ),
    }
    assert computation.summary["authority_boundary"][
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"
    ] is True
    assert computation.summary["authority_boundary"]["READY_FOR_FORMAL_TRAINING"] is False


def test_correct_real_computation_matches_all_exact_contract_digests(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    assert subject.EXPECTED_CENSUS_PROJECTION_SHA256_V1 == (
        "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9"
    )
    assert subject._sha256(subject._csv_bytes(computation.rows)) == (
        subject.EXPECTED_CENSUS_PROJECTION_SHA256_V1
    )
    assert subject.EXPECTED_SUMMARY_PAYLOAD_SHA256_V1 == (
        "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a"
    )
    assert subject._sha256(subject._json_bytes(computation.summary)) == (
        subject.EXPECTED_SUMMARY_PAYLOAD_SHA256_V1
    )
    assert subject.EXPECTED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 == (
        "d60abb26511d05f13f51656b9c8954794942b87babb514a8858262f13c54baaf"
    )
    assert subject._sha256(
        subject._canonical_json(list(computation.semantic_source_bindings)).encode(
            "utf-8"
        )
    ) == (
        subject.EXPECTED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1
    )


def test_coordinated_event_level_readiness_identity_swap_fails_exact_projection(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    mutated = _swapped_readiness_computation(computation)
    assert mutated.summary["chemistry"]["POSITIVE"]["event_set_sha256"] == (
        "0fefc1bf45c056b3675d3ebc140e78712e2666c8ec5fff6bda20cf911abddcda"
    )
    with pytest.raises(ERROR, match="CENSUS_EXACT_PROJECTION_SHA256_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_identity_swap_preserves_aggregates_but_changes_event_membership(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    mutated = _swapped_readiness_computation(computation)
    before = computation.rows
    after = mutated.rows
    for field in (
        "chemistry_disposition",
        "training_use_disposition",
        "role_profile",
        "current_runtime_model_usable",
        "formal_training_admitted",
    ):
        assert Counter(row[field] for row in before) == Counter(
            row[field] for row in after
        )
    before_positive = {
        row["canonical_event_id"]
        for row in before
        if row["chemistry_disposition"] == "POSITIVE"
    }
    after_positive = {
        row["canonical_event_id"]
        for row in after
        if row["chemistry_disposition"] == "POSITIVE"
    }
    assert len(before_positive) == len(after_positive) == 49
    assert RUNTIME_POSITIVE_EVENT in before_positive - after_positive
    assert UNRESOLVED_LEAKAGE_EVENT in after_positive - before_positive
    with pytest.raises(ERROR, match="CENSUS_EXACT_PROJECTION_SHA256_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_top_pending_metadata_drift_fails_exact_summary_payload(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    top_pending = deepcopy(
        computation.summary["top_pending_review_units_by_event_yield"]
    )
    assert top_pending[0]["event_count"] == 9
    top_pending[0]["event_count"] = 999
    summary = subject._build_summary(computation.rows, top_pending)
    mutated = replace(computation, summary=summary)
    with pytest.raises(ERROR, match="SUMMARY_EXACT_PAYLOAD_SHA256_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_split_derived_binding_role_drift_fails_exact_binding_inventory(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    target = next(
        binding
        for binding in bindings
        if binding["artifact_role"] == "BATCH001_FORMAL_FULL_COMPONENT_REGISTRY"
    )
    target["artifact_role"] = "WRONG_BUT_NONEMPTY_ROLE"
    mutated = replace(computation, semantic_source_bindings=tuple(bindings))
    with pytest.raises(
        ERROR, match="SEMANTIC_SOURCE_BINDINGS_EXACT_SHA256_INVALID"
    ):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_exact11_distribution_and_training_stage(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    assert computation.summary["global_status_distribution"]["counts"] == (
        subject.EXPECTED_GLOBAL_STATUS_COUNTS_V1
    )
    assert computation.summary["training_stage"]["future_training_admission_candidate_count"] == 12
    assert computation.summary["training_stage"]["current_runtime_model_usable_count"] == 17
    assert computation.summary["training_stage"]["formal_training_admitted_count"] == 5
    assert computation.summary["training_stage"]["ready_for_formal_training_event_count"] == 0


def test_pair_role_exact5_and_geometry_counts(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    summary = computation.summary
    assert summary["reactive_pair"]["raw_structural_pair_evidence_count"] == 865
    assert summary["reactive_pair"]["sample_level_authoritative_pair_count"] == 49
    assert summary["reactive_pair"]["published_model_bound_target_constructible_count"] == 41
    assert summary["role"]["role_profile_counts"] == {
        subject.STRICT_PROFILE: 31,
        subject.DIRECT_PROFILE: 18,
        "other": 0,
    }
    assert [
        row["structurally_applicable_authoritative_role_count"]
        for row in summary["canonical_exact5"]["tasks"]
    ] == [49, 31, 31, 49, 49]
    assert summary["geometry"]["POST_source_evidence_available_count"] == 867
    assert summary["geometry"]["POST_sample_authoritative_count"] == 21
    assert summary["geometry"]["POST_training_target_available_count"] == 17
    assert summary["geometry"]["PRE_sample_authoritative_count"] == 0


def test_source_bindings_are_real_and_sha_bound(
    computation: subject.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    assert len(computation.semantic_source_bindings) == 39
    for binding in computation.semantic_source_bindings:
        root = REPO if binding["path_namespace"] == "repository_relative" else REPO.parent
        payload = (root / binding["path"]).read_bytes()
        assert len(payload) == binding["byte_count"]
        assert subject._sha256(payload) == binding["sha256"]


def test_universe_event_missing_fails_closed() -> None:
    _header, rows = subject._parse_csv(
        (REPO / subject._UNIVERSE).read_bytes(), "TEST_UNIVERSE"
    )
    with pytest.raises(ERROR, match="UNIVERSE_EVENT_COUNT_INVALID"):
        subject._parse_universe(_universe_payload(rows[:-1]))


def test_universe_event_duplicate_fails_closed() -> None:
    _header, rows = subject._parse_csv(
        (REPO / subject._UNIVERSE).read_bytes(), "TEST_UNIVERSE"
    )
    rows[-1]["canonical_event_id"] = rows[0]["canonical_event_id"]
    with pytest.raises(ERROR, match="UNIVERSE_CANONICAL_EVENT_DUPLICATE"):
        subject._parse_universe(_universe_payload(rows))


def test_processing_source_sha_drift_fails_closed() -> None:
    spec = subject._DIRECT_SPEC_BY_PATH[subject._STRUCTURAL_501_1000]
    payload = bytearray((REPO / spec.path).read_bytes())
    payload[-2] = ord(" ") if payload[-2] != ord(" ") else ord("\t")
    with pytest.raises(ERROR, match="SOURCE_SHA256_MISMATCH"):
        subject._verify_source_payload(spec, bytes(payload))


def test_incompatible_authority_collision_fails_closed() -> None:
    records = {"EVENT": {"chemistry": "POSITIVE", "training": "INCLUDE"}}
    with pytest.raises(ERROR, match="INCOMPATIBLE_AUTHORITY_STATE_COLLISION"):
        subject._add_positive_record(
            records,
            "EVENT",
            {"chemistry": "POSITIVE", "training": "EXCLUDE_FROM_TRAINING_ONLY"},
        )


def test_positive_count_drift_fails_closed(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["chemistry_disposition"] == "POSITIVE",
        chemistry_disposition="UNRESOLVED",
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


@pytest.mark.parametrize(
    "status",
    ("COMPLETED_HUMAN_NEGATIVE", "PUBLISHED_EXACT_AUTO_NEGATIVE"),
)
def test_task_negative_cannot_be_mapped_to_chemistry_negative(
    computation, status: str
) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["current_global_status"] == status,
        chemistry_disposition="NEGATIVE",
    )
    with pytest.raises(ERROR, match="CHEMISTRY_DISPOSITION_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_exclude_from_training_only_cannot_be_mapped_negative(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["training_use_disposition"]
        == "EXCLUDE_FROM_TRAINING_ONLY",
        chemistry_disposition="NEGATIVE",
    )
    with pytest.raises(ERROR, match="CHEMISTRY_DISPOSITION_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_g3h_training_exclusion_lost_fails_closed(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["positive_authority_source"] == subject._G3H_EVENT,
        training_use_disposition="INCLUDE",
        training_use_include="true",
        human_training_excluded="false",
    )
    with pytest.raises(ERROR, match="G3H_TRAINING_EXCLUSION_OR_INTEGRATION_LOST"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_b3_omission_fails_closed() -> None:
    without_b3 = tuple(task for task in subject.CANONICAL_EXACT5_V1 if task[2] != "B3")
    with pytest.raises(ERROR, match="EXACT5_B3_OMITTED"):
        subject._validate_exact5_contract(without_b3)


def test_sixth_mask_fails_closed() -> None:
    sixth = (*subject.CANONICAL_EXACT5_V1, (5, "forbidden_sixth", "D"))
    with pytest.raises(ERROR, match="EXACT5_TASK_COUNT_INVALID"):
        subject._validate_exact5_contract(sixth)


def test_roleless_row_cannot_be_false_applicability(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["role_partition_sample_authoritative"] == "false",
        structurally_applicable_task_ids_json="[]",
    )
    with pytest.raises(ERROR, match="ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_post_evidence_cannot_promote_post_training_authority(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["post_geometry_source_evidence_available"] == "true"
        and row["post_geometry_sample_authoritative"] == "false",
        post_geometry_training_target_available="true",
    )
    with pytest.raises(ERROR, match="POST_EVIDENCE_PROMOTED_WITHOUT_AUTHORITY"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


@pytest.mark.parametrize(
    "field", ("pre_geometry_authoritative", "pre_geometry_training_target_available")
)
def test_post_to_pre_and_pre_zero_fill_fail_closed(computation, field: str) -> None:
    mutated = _mutate_row(computation, lambda _row: True, **{field: "true"})
    with pytest.raises(ERROR, match="POST_TO_PRE_OR_PRE_ZERO_FILL_DETECTED"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_runtime_usable_cannot_promote_training_admission(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["current_runtime_model_usable"] == "true"
        and row["formal_split"] != "train",
        formal_training_admitted="true",
    )
    with pytest.raises(ERROR, match="TRAINING_ADMISSION_PROMOTION_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_future_candidate_cannot_promote_training_admission(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["future_training_admission_candidate"] == "true",
        formal_training_admitted="true",
    )
    with pytest.raises(ERROR, match="TRAINING_ADMISSION_PROMOTION_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_training_materialization_not_computable_cannot_be_zero(computation) -> None:
    summary = deepcopy(computation.summary)
    summary["training_stage"]["training_materialization_allowed_global_status"] = 0
    mutated = replace(computation, summary=summary)
    with pytest.raises(ERROR, match="SUMMARY_NOT_DERIVED_FROM_CENSUS_ROWS"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_unknown_row_source_provenance_fails_closed(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: bool(row["positive_authority_source"]),
        positive_authority_source="unknown/not_published.csv",
    )
    with pytest.raises(ERROR, match="ROW_SOURCE_PROVENANCE_UNKNOWN"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_source_binding_unknown_field_fails_closed(computation) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    bindings[0]["unknown_field"] = "forbidden"
    mutated = replace(computation, semantic_source_bindings=tuple(bindings))
    with pytest.raises(ERROR, match="SEMANTIC_SOURCE_BINDING_SCHEMA_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_source_binding_wrong_path_fails_closed(computation) -> None:
    bindings = [dict(binding) for binding in computation.semantic_source_bindings]
    target = next(
        binding for binding in bindings if binding["path"] == subject._UNIVERSE
    )
    target["path"] = "wrong/path.csv"
    mutated = replace(computation, semantic_source_bindings=tuple(bindings))
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_output_row_count_not_1000_fails_closed(computation) -> None:
    mutated = replace(computation, rows=computation.rows[:-1])
    with pytest.raises(ERROR, match="CENSUS_EXACT1000_ROW_SCHEMA_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_rank_gap_fails_closed(computation) -> None:
    mutated = _mutate_row(
        computation, lambda row: row["scaleup_rank"] == "500", scaleup_rank="501"
    )
    with pytest.raises(ERROR, match="CENSUS_RANK_GAP_OR_ORDER_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_status_distribution_drift_fails_closed(computation) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row["current_global_status"] == "CURRENTLY_UNREVIEWED",
        current_global_status="CURRENTLY_IN_PROGRESS",
    )
    with pytest.raises(ERROR, match="CENSUS_EXACT11_STATUS_DISTRIBUTION_INVALID"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("training_use_disposition", "UNRESOLVED"),
        ("chemistry_disposition", "UNRESOLVED"),
        ("task_relevance_disposition", "UNRESOLVED"),
    ),
)
def test_disposition_total_drift_fails_closed(
    computation, field: str, value: str
) -> None:
    mutated = _mutate_row(
        computation,
        lambda row: row[field] not in {value, "NEGATIVE"},
        **{field: value},
    )
    with pytest.raises(ERROR):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_top_pending_review_ranking_drift_fails_closed(computation) -> None:
    summary = deepcopy(computation.summary)
    summary["top_pending_review_units_by_event_yield"][0], summary[
        "top_pending_review_units_by_event_yield"
    ][1] = (
        summary["top_pending_review_units_by_event_yield"][1],
        summary["top_pending_review_units_by_event_yield"][0],
    )
    mutated = replace(computation, summary=summary)
    with pytest.raises(ERROR, match="SUMMARY_TOP_PENDING_RANKING_DRIFT"):
        subject.validate_covapie_cumulative1000_current_global_readiness_census_v1(
            mutated
        )


def test_builder_is_byte_deterministic() -> None:
    first = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_v1(
        REPO
    )
    second = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_v1(
        REPO
    )
    assert first == second
    assert set(first) == {
        subject.CENSUS_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }


def test_materialized_outputs_match_fresh_builder() -> None:
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_v1(
        REPO
    )
    for filename, payload in built.items():
        assert (
            REPO / subject.OUTPUT_DIRECTORY_RELATIVE / filename
        ).read_bytes() == payload


def test_checker_passes() -> None:
    result = checker.run_check_v1(REPO)
    assert result["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is True
    assert result["READY_FOR_FORMAL_TRAINING"] is False
    assert result["deterministic_double_materialization"] is True

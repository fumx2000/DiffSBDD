from __future__ import annotations

import copy
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import covapie_completed_human_decision_reconciliation_with_6oa_v1 as predecessor
from covalent_ext import covapie_completed_human_decision_reconciliation_with_pyr_v1 as subject
from covalent_ext import covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


CHECKER = ROOT / subject.CHECKER_RELATIVE
ERROR = subject.CompletedDecisionReconciliationWithPYRError


@pytest.fixture(scope="session")
def checker():
    specification = importlib.util.spec_from_file_location(
        "check_pyr_reconciliation", CHECKER
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def bound() -> dict[str, object]:
    return ingestion.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="session")
def components():
    return subject._build_components_v1(ROOT)


@pytest.fixture(scope="session")
def predecessor_sources(components):
    return components[0]


@pytest.fixture(scope="session")
def sources(components):
    return components[1]


@pytest.fixture(scope="session")
def predecessor_result(components):
    return components[2]


@pytest.fixture(scope="session")
def reconciliation(components):
    return components[3]


@pytest.fixture(scope="session")
def artifact_mapping(sources, reconciliation) -> dict[str, object]:
    return subject._artifact_mapping_v1(sources, reconciliation)


def test_public_api_and_exact4_inventory_are_exact() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithPYRError",
        "project_pyr_completed_decision_v1",
        "load_real_completed_decision_sources_with_pyr_v1",
        "reconcile_real_completed_human_decisions_with_pyr_v1",
        "build_artifact_v1",
        "materialize_artifact_v1",
        "check_materialized_v1",
    )
    assert len(subject.EXACT4_PATHS) == len(set(subject.EXACT4_PATHS)) == 4
    assert all((ROOT / path).is_file() for path in subject.EXACT4_PATHS)


def test_rich_boundary_formal_binding_and_normalization_are_independently_validated(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_pyr_boundary_v1(bound)
    binding = subject._expected_binding_v1(bound)
    assert binding == generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=17975,
        sha256="58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
        schema_version="covapie_pyr_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4",
    )
    decisions = bound["formal_document"]["approved_D1_D6"]
    assert decisions["D2_task_generation_domain_relevance"]["decision"] == "IN_DOMAIN"
    assert decisions["D6_later_training_use_disposition"]["decision"] == "EXCLUDE"
    compatibility = bound["generic_Exact11_compatibility"]
    assert compatibility["normalized_task_relevance_disposition"] == "RELEVANT"
    assert compatibility["normalized_training_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"


def test_projection_is_generic_exact4_exact11_without_rich_fields(
    bound: dict[str, object],
) -> None:
    source = subject._project_bound_pyr_v1(bound)
    assert isinstance(source, generic.NormalizedDecisionSource)
    assert len(source.facts) == 4
    assert tuple(fact.canonical_event_id for fact in source.facts) == ingestion.EXPECTED_EVENT_IDS
    for fact in source.facts:
        row = asdict(fact)
        assert tuple(row) == subject._GENERIC_FACT_FIELDS
        assert len(row) == 11
        assert not subject._FORBIDDEN_RICH_FACT_FIELDS.intersection(row)
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_EXCLUDE
        assert fact.human_training_excluded is True


def test_exact5_and_false_authority_boundary_are_preserved(
    bound: dict[str, object],
) -> None:
    formal = bound["formal_document"]
    contract = formal["selected_task_ids"]["canonical_V1_contract"]
    assert contract["task_count"] == 5
    assert contract["B3_present"] is True
    assert contract["sixth_task"] is False
    assert [row["semantic_long_name"] for row in contract["tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    false_boundary = formal["non_created_authority"]
    for key in (
        "task_label_authority",
        "event_task_label_rows_materialized",
        "mask_tensor_targets_created",
        "formal_training_admitted",
        "training_materialization_allowed",
        "parameter_update_authorization",
    ):
        assert false_boundary[key] is False


def test_source_and_fact_chains_are_strict_prefix_append(
    predecessor_sources, sources, bound: dict[str, object]
) -> None:
    records = subject._projection_records_v1(bound)
    subject._validate_source_chain_v1(predecessor_sources, sources, records)
    assert len(predecessor_sources) == 26
    assert len(sources) == 27
    assert sources[:-1] == predecessor_sources
    before_facts = tuple(
        fact for source in predecessor_sources for fact in source.facts
    )
    after_facts = tuple(fact for source in sources for fact in source.facts)
    assert len(before_facts) == 147
    assert len(after_facts) == 151
    assert after_facts[:147] == before_facts
    assert after_facts[147:] == sources[-1].facts


def test_published_adapter_reproduces_with_6oa_predecessor(
    predecessor_sources, predecessor_result
) -> None:
    adapted = subject.historical_adapter_owner._adapt_historical_v1(ROOT)
    reproduced = generic.reconcile_completed_human_decisions_v1(
        adapted, predecessor_sources
    )
    published = predecessor.reconcile_real_completed_human_decisions_with_6oa_v1(
        ROOT
    )
    assert reproduced == published == predecessor_result


def test_historical_pyr_state_is_exactly_unreviewed(predecessor_result) -> None:
    subject._prove_pyr_predecessor_historical_state_v1(
        predecessor_result.reconciled_rows
    )
    targets = [
        row
        for row in predecessor_result.reconciled_rows
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS
    ]
    assert [row["raw_priority_rank"] for row in targets] == ["30"] * 4
    assert [row["raw_unit_event_count"] for row in targets] == ["4"] * 4
    assert [row["current_review_status"] for row in targets] == [
        generic.CURRENTLY_UNREVIEWED
    ] * 4
    assert [row["calibration_eligible"] for row in targets] == ["true"] * 4
    assert [row["calibration_exclusion_reason"] for row in targets] == [""] * 4


def test_reconciliation_changes_exact4_and_preserves_334(
    predecessor_result, reconciliation
) -> None:
    subject._validate_reconciliation_delta_v1(predecessor_result, reconciliation)
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(
        predecessor_result.reconciled_rows,
        reconciliation.reconciled_rows,
        strict=True,
    ):
        if old["canonical_event_id"] not in targets:
            changed_non_target += old != new
            continue
        assert {key for key in old if old[key] != new[key]} == subject._ALLOWED_RECONCILIATION_FIELDS
        assert new["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        assert new["current_status_authority_sources_json"] == generic._canonical_json(
            [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
        )
        assert new["calibration_eligible"] == "false"
        assert new["calibration_exclusion_reason"] == generic.COMPLETED_HUMAN_POSITIVE
        changed_target += old != new
    assert (changed_target, changed_non_target) == (4, 0)


def test_review_summary_is_computed_and_matches_expected_delta(
    predecessor_result, reconciliation, checker
) -> None:
    assert predecessor_result.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert reconciliation.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    computed = checker._review_summary(
        [dict(row) for row in reconciliation.reconciled_rows]
    )
    assert computed == reconciliation.review_summary
    assert computed["completed_positive_event_count"] == 127
    assert computed["completed_negative_event_count"] == 48
    assert computed["completed_total_event_count"] == 175
    assert computed["unreviewed_event_count"] == 163


def test_coverage_is_published_aggregate_plus_local_positive_delta(
    artifact_mapping, checker
) -> None:
    predecessor_artifact = json.loads(
        (ROOT / predecessor.OUTPUT_RELATIVE).read_text()
    )
    report = checker._verify_coverage_contract(
        predecessor_artifact["normalized_facts"],
        artifact_mapping["normalized_facts"],
    )
    assert report["predecessor"] == predecessor.SUCCESSOR_COVERAGE_SUMMARY
    assert report["successor"]["decision_category_distribution"] == {
        "chemistry_positive": 103,
        "chemistry_negative": 20,
        "task_domain_negative": 28,
        "task_domain_positive": 0,
    }
    assert report["successor"]["label_ready_event_count"] == 16
    assert report["successor"]["training_mask_target_count"] == 0
    assert report["successor"]["training_authority"] is False


def test_artifact_contract_prefix_and_materialized_bytes(
    predecessor_sources, sources, reconciliation, artifact_mapping
) -> None:
    subject._validate_artifact_mapping_v1(
        artifact_mapping,
        predecessor_sources=predecessor_sources,
        successor_sources=sources,
        reconciliation=reconciliation,
    )
    assert tuple(artifact_mapping) == subject._ARTIFACT_FIELDS
    assert len(artifact_mapping["source_bindings"]) == 27
    assert len(artifact_mapping["normalized_facts"]) == 151
    assert len(artifact_mapping["reconciled_rows"]) == 338
    assert (ROOT / subject.OUTPUT_RELATIVE).read_bytes() == subject.build_artifact_v1(
        ROOT
    )


def test_deterministic_double_build_and_materialized_check() -> None:
    first = subject.build_artifact_v1(ROOT)
    second = subject.build_artifact_v1(ROOT)
    assert first == second
    assert subject.check_materialized_v1(ROOT) == {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 27,
        "accepted_fact_count": 151,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }


def test_tamper_helper_accepts_only_prefixed_expected_valueerror(checker) -> None:
    assert (
        checker._expect_tamper(
            "expected", "EXPECTED_TOKEN", lambda: checker._fail("EXPECTED_TOKEN")
        )
        == "EXPECTED_TOKEN"
    )
    with pytest.raises(ValueError, match="DIFFERENT_TOKEN"):
        checker._expect_tamper(
            "wrong_token",
            "EXPECTED_TOKEN",
            lambda: checker._fail("DIFFERENT_TOKEN"),
        )
    with pytest.raises(ValueError, match="EXPECTED_TOKEN"):
        checker._expect_tamper(
            "wrong_prefix",
            "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(ValueError("EXPECTED_TOKEN")),
        )
    with pytest.raises(ValueError, match="MATERIALIZED_ARTIFACT_BYTES_MISMATCH"):
        checker._expect_tamper(
            "wrong_guard",
            "EXPECTED_TOKEN",
            lambda: checker._fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH"),
        )
    with pytest.raises(ValueError, match="TAMPER_PROBE_DID_NOT_FAIL"):
        checker._expect_tamper("callback_passed", "EXPECTED_TOKEN", lambda: None)


@pytest.mark.parametrize(
    "exception",
    [TypeError("boom"), KeyError("boom"), AssertionError("boom"), IndexError("boom")],
)
def test_tamper_helper_does_not_accept_arbitrary_exception_classes(
    checker, exception: Exception
) -> None:
    with pytest.raises(type(exception), match="boom"):
        checker._expect_tamper(
            "arbitrary_exception",
            "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(exception),
        )


def test_real_checker_and_all_required_negative_probes(checker) -> None:
    report = checker.check(ROOT)
    assert report["status"] == "PASS"
    assert report["repository"]["lifecycle"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    required = {
        "source_D2_wrong",
        "source_D2_missing",
        "source_D6_include",
        "source_D6_not_applicable",
        "source_D6_missing",
        "source_human_training_excluded_false",
        "legacy_status_negative",
        "missing_pyr_event",
        "duplicate_pyr_event",
        "fifth_pyr_event",
        "source_append_reordered",
        "fact_append_reordered",
        "duplicate_source_identity",
        "predecessor_fact_modified",
        "generic_schema_11_to_12",
        "wrong_authority_source",
        "pyr_still_unreviewed",
        "calibration_still_eligible",
        "wrong_exclusion_reason",
        "non_target_changed",
        "positive_count_not_plus4",
        "negative_count_wrong_plus4",
        "coverage_positive_not_plus4",
        "coverage_task_domain_negative_wrong_plus4",
        "label_ready_increased",
        "training_mask_target_created",
        "training_authority_forged",
        "task_label_authority_forged",
        "formal_training_admitted_forged",
        "census_refresh_forged",
        "queue_refresh_forged",
        "next_review_started_forged",
        "event_task_labels_forged",
        "training_started_forged",
        "B3_missing",
        "sixth_task_forged",
        "raw_byte_corruption",
        "unexpected_fifth_file",
        "filesystem_executable_bit",
        "tracked_executable_mode",
        "tracked_nonzero_stage",
    }
    assert required <= set(report["tamper_probes"])
    assert report["tamper_probes"]["raw_byte_corruption"] == "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
    assert report["tamper_probes"]["tracked_executable_mode"] == "TRACKED_GIT_INDEX_MODE_INVALID"
    if report["repository"]["lifecycle"] == checker.CANDIDATE_UNTRACKED:
        assert report["repository"]["git_index_mode_checked"] is False
        assert "git_index_modes" not in report["repository"]
    else:
        assert report["repository"]["git_index_mode_checked"] is True
        assert set(report["repository"]["git_index_modes"].values()) == {"100644"}


def test_checker_candidate_and_tracked_clean_profiles(checker) -> None:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    assert checker.classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in paths),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.CANDIDATE_UNTRACKED
    assert checker.classify_repository_profile(
        expected_paths=paths,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) == checker.TRACKED_CLEAN


def _valid_stage_lines() -> tuple[tuple[str, ...], set[str]]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    return tuple(f"100644 {'a' * 40} 0\t{path}" for path in paths), set(paths)


@pytest.mark.parametrize(
    "mutation",
    [
        "executable_100755",
        "symlink_120000",
        "missing_path",
        "duplicate_path",
        "nonzero_stage",
        "unexpected_fifth_path",
    ],
)
def test_tracked_index_mode_parser_rejects_nonpublication_state(
    checker, mutation: str
) -> None:
    stage_lines, expected = _valid_stage_lines()
    candidate = list(stage_lines)
    if mutation == "executable_100755":
        candidate[0] = candidate[0].replace("100644", "100755", 1)
    elif mutation == "symlink_120000":
        candidate[0] = candidate[0].replace("100644", "120000", 1)
    elif mutation == "missing_path":
        candidate.pop()
    elif mutation == "duplicate_path":
        candidate[-1] = candidate[0]
    elif mutation == "nonzero_stage":
        candidate[0] = candidate[0].replace(" 0\t", " 2\t", 1)
    elif mutation == "unexpected_fifth_path":
        candidate.append(f"100644 {'b' * 40} 0\tunexpected.txt")
    else:
        raise AssertionError("unknown test mutation")
    with pytest.raises(ValueError, match="TRACKED_GIT_INDEX_MODE_INVALID"):
        checker.validate_tracked_index_modes(tuple(candidate), expected)


@pytest.mark.parametrize(
    ("head", "origin", "ahead", "changed"),
    [
        ("successor", "baseline", 1, set()),
        ("successor", "successor", 0, set()),
        ("later", "successor", 1, {"docs/later.md"}),
    ],
)
def test_checker_tracked_clean_lifecycle_relations(
    checker, head: str, origin: str, ahead: int, changed: set[str]
) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    if origin == "baseline":
        origin = checker.BASELINE_COMMIT
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=expected,
        head=head,
        origin_main=origin,
        ahead=ahead,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected | changed,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("review_unit_id", "WRONG"),
        ("task_relevance_disposition", generic.TASK_NOT_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("legacy_completed_review_status", generic.COMPLETED_HUMAN_NEGATIVE),
        ("training_disposition", generic.TRAINING_INCLUDE),
        ("training_disposition", generic.TRAINING_NOT_APPLICABLE),
        ("human_training_excluded", False),
    ],
)
def test_projected_classification_tamper_fails_closed(
    bound: dict[str, object], field: str, value: object
) -> None:
    source = subject._project_bound_pyr_v1(bound)
    facts = list(source.facts)
    facts[-1] = replace(facts[-1], **{field: value})
    mutated = generic.NormalizedDecisionSource(
        binding=source.binding, facts=tuple(facts)
    )
    with pytest.raises(ERROR, match=subject.ERROR_PREFIX):
        subject._validate_projected_pyr_source_v1(
            mutated, subject._projection_records_v1(bound)
        )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("formal_document", "approved_D1_D6", "D2_task_generation_domain_relevance", "decision"), "OUT_OF_DOMAIN"),
        (("formal_document", "approved_D1_D6", "D6_later_training_use_disposition", "decision"), "INCLUDE"),
        (("formal_document", "approved_D1_D6", "D6_later_training_use_disposition", "human_training_excluded"), False),
        (("formal_document", "selected_task_ids", "canonical_V1_contract", "B3_present"), False),
        (("formal_document", "selected_task_ids", "canonical_V1_contract", "sixth_task"), True),
        (("formal_document", "non_created_authority", "task_label_authority"), True),
        (("formal_validator_binding", "validation_method"), "EXECUTED"),
    ],
)
def test_rich_identity_normalization_and_authority_tampers_fail_closed(
    bound: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    mutated = copy.deepcopy(bound)
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ERROR, match=subject.ERROR_PREFIX):
        subject._project_bound_pyr_v1(mutated)


def test_source_chain_missing_duplicate_and_reorder_fail_closed(
    predecessor_sources, sources, bound: dict[str, object]
) -> None:
    records = subject._projection_records_v1(bound)
    with pytest.raises(ERROR, match="SOURCE_CHAIN"):
        subject._validate_source_chain_v1(predecessor_sources, sources[:-1], records)
    duplicate = (*predecessor_sources, predecessor_sources[-1])
    with pytest.raises(ERROR, match=subject.ERROR_PREFIX):
        subject._validate_source_chain_v1(predecessor_sources, duplicate, records)
    reordered = (*sources[:-2], sources[-1], sources[-2])
    with pytest.raises(ERROR, match=subject.ERROR_PREFIX):
        subject._validate_source_chain_v1(predecessor_sources, reordered, records)

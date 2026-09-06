"""Targeted contract tests for the NWJ reconciliation Exact4."""

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
from covalent_ext import covapie_completed_human_decision_reconciliation_with_nwj_v1 as subject
from covalent_ext import covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


CHECKER = ROOT / subject.CHECKER_RELATIVE
ERROR = subject.CompletedDecisionReconciliationWithNWJError


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location("nwj_reconciliation_checker", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return ingestion.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def components():
    return subject._build_components_v1(ROOT)


@pytest.fixture(scope="module")
def predecessor_sources(components):
    return components[0]


@pytest.fixture(scope="module")
def sources(components):
    return components[1]


@pytest.fixture(scope="module")
def predecessor_result(components):
    return components[2]


@pytest.fixture(scope="module")
def reconciliation(components):
    return components[3]


@pytest.fixture(scope="module")
def artifact_mapping(sources, reconciliation) -> dict[str, object]:
    return subject._artifact_mapping_v1(sources, reconciliation)


@pytest.fixture(scope="module")
def checker_report(checker) -> dict[str, object]:
    return checker.check(ROOT)


def test_public_api_is_exact() -> None:
    assert subject.__all__ == (
        "CompletedDecisionReconciliationWithNWJError",
        "project_nwj_completed_decision_v1",
        "load_real_completed_decision_sources_with_nwj_v1",
        "reconcile_real_completed_human_decisions_with_nwj_v1",
        "build_artifact_v1",
        "materialize_artifact_v1",
        "check_materialized_v1",
    )


def test_rich_boundary_and_formal_binding_are_independently_validated(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_nwj_boundary_v1(bound)
    expected = generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=24265,
        sha256="1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        schema_version="covapie_nwj_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_DE7AFABE9D079CDF",
    )
    assert subject._expected_binding_v1(bound) == expected
    assert bound["formal_decision_binding"]["validation_method"] == (
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY"
    )
    assert bound["formal_validator_binding"]["validation_method"] == (
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
    )


def test_projection_is_generic_exact11_without_rich_fields(
    bound: dict[str, object],
) -> None:
    source = subject._project_bound_nwj_v1(bound)
    records = subject._projection_records_v1(bound)
    assert len(source.facts) == len(records) == 4
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == (
        subject._GENERIC_FACT_FIELDS
    )
    assert [asdict(fact) for fact in source.facts] == [dict(row) for row in records]
    assert all(tuple(row) == subject._GENERIC_FACT_FIELDS for row in records)
    assert all(len(row) == 11 for row in records)
    assert not any(subject._FORBIDDEN_RICH_FACT_FIELDS & set(row) for row in records)
    assert [fact.canonical_event_id for fact in source.facts] == list(
        ingestion.EXPECTED_EVENT_IDS
    )
    assert all(
        fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        and fact.task_relevance_disposition == generic.TASK_RELEVANT
        and fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        and fact.training_disposition == generic.TRAINING_INCLUDE
        and fact.human_training_excluded is False
        for fact in source.facts
    )


def test_rich_scientific_and_training_boundary_is_exact(
    bound: dict[str, object],
) -> None:
    formal = bound["formal_document"]
    identity = formal["sample_identity"]
    role = formal["selected_role_context"]
    tasks = formal["canonical_Exact5"]
    assert identity["PDB"] == "4CM5" and identity["ligand_component_id"] == "NWJ"
    assert identity["raw_priority_rank"] == 28
    assert identity["scaleup_event_ranks"] == [674, 675, 676, 677]
    assert role["candidate_id"] == "CANDIDATE_A_DIRECT_FORMYL"
    assert role["role_profile"] == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    assert role["warhead_atom_ids"] == ["CAV", "OAE"]
    assert role["linker_atom_ids"] == []
    assert role["minimal_seed"]["atom_ids"] == ["CAX", "CAI", "CAK"]
    assert role["minimal_seed"]["primary_scaffold_side_anchor"] == "CAX"
    assert tasks["task_count"] == 5
    assert tasks["B3_present"] is True and tasks["sixth_task"] is False
    assert tasks["selected_structural_applicability_task_ids"] == [0, 3, 4]
    assert tasks["task_label_authority"] is False
    assert tasks["event_task_label_rows_materialized"] is False
    assert tasks["mask_tensor_targets_created"] is False
    assert formal["PRE_boundary"]["PRE_source_mapping_status"] == (
        "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
    )
    assert formal["training_boundary"]["formal_training_admitted"] is False
    assert formal["training_boundary"]["READY_FOR_TRAINING"] is False
    assert formal["training_boundary"]["TRAINING_STARTED"] is False


def test_source_and_fact_chains_are_strict_prefix_append(
    bound, predecessor_sources, sources,
) -> None:
    records = subject._projection_records_v1(bound)
    subject._validate_source_chain_v1(predecessor_sources, sources, records)
    assert len(predecessor_sources) == 24 and len(sources) == 25
    assert sources[:-1] == predecessor_sources
    old_facts = tuple(
        fact for source in predecessor_sources for fact in source.facts
    )
    facts = tuple(fact for source in sources for fact in source.facts)
    assert len(old_facts) == 139 and len(facts) == 143
    assert facts[:139] == old_facts and facts[139:] == sources[-1].facts
    assert len({source.binding.stable_identity for source in sources}) == 25
    assert len({source.binding.review_unit_id for source in sources}) == 25
    assert all(
        source.binding.path_namespace == "repository_parent_relative"
        for source in sources
    )


def test_historical_nwj_state_is_exactly_unreviewed(
    predecessor_result,
) -> None:
    subject._prove_nwj_predecessor_historical_state_v1(
        predecessor_result.reconciled_rows
    )
    targets = [
        row
        for row in predecessor_result.reconciled_rows
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS
    ]
    assert len(targets) == 4
    assert all(
        row["raw_priority_rank"] == "28"
        and row["raw_review_unit_id"] == ingestion.EXPECTED_REVIEW_UNIT_ID
        and row["raw_unit_event_count"] == "4"
        and row["current_review_status"] == generic.CURRENTLY_UNREVIEWED
        and row["calibration_eligible"] == "true"
        and row["calibration_exclusion_reason"] == ""
        for row in targets
    )


def test_reconciliation_changes_exact4_and_preserves_334(
    predecessor_result, reconciliation,
) -> None:
    assert predecessor_result.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert reconciliation.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(
        predecessor_result.reconciled_rows,
        reconciliation.reconciled_rows,
        strict=True,
    ):
        if old["canonical_event_id"] in target_ids:
            changed_target += old != new
            assert {key for key in old if old[key] != new[key]} == (
                subject._ALLOWED_RECONCILIATION_FIELDS
            )
            assert new["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
            assert new["current_status_authority_sources_json"] == (
                generic._canonical_json(
                    [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
                )
            )
            assert new["calibration_eligible"] == "false"
            assert new["calibration_exclusion_reason"] == (
                generic.COMPLETED_HUMAN_POSITIVE
            )
        else:
            changed_non_target += old != new
    assert (changed_target, changed_non_target) == (4, 0)


def test_review_summary_is_computed_and_matches_expected_delta(
    checker, predecessor_result, reconciliation,
) -> None:
    before = checker._computed_review_summary(
        [dict(row) for row in predecessor_result.reconciled_rows]
    )
    after = checker._computed_review_summary(
        [dict(row) for row in reconciliation.reconciled_rows]
    )
    assert before == subject._PREDECESSOR_REVIEW_SUMMARY
    assert after == subject._SUCCESSOR_REVIEW_SUMMARY
    assert after["completed_positive_event_count"] - before[
        "completed_positive_event_count"
    ] == 4
    assert after["completed_positive_unit_count"] - before[
        "completed_positive_unit_count"
    ] == 1
    assert after["unreviewed_event_count"] - before["unreviewed_event_count"] == -4
    assert after["unreviewed_unit_count"] - before["unreviewed_unit_count"] == -1


def test_coverage_is_computed_and_matches_expected_delta(
    checker, artifact_mapping,
) -> None:
    old = json.loads((ROOT / subject.predecessor_owner.OUTPUT_RELATIVE).read_bytes())
    coverage = checker._verify_coverage_contract(
        old["normalized_facts"], artifact_mapping["normalized_facts"]
    )
    assert coverage["predecessor"] == subject.PREDECESSOR_COVERAGE_SUMMARY
    assert coverage["successor"] == subject.SUCCESSOR_COVERAGE_SUMMARY
    assert coverage["successor"]["decision_category_distribution"] == {
        "chemistry_positive": 99,
        "chemistry_negative": 20,
        "task_domain_negative": 24,
        "task_domain_positive": 0,
    }
    assert coverage["successor"]["label_ready_event_count"] == 16
    assert coverage["successor"]["training_mask_target_count"] == 0
    assert coverage["successor"]["training_authority"] is False


def test_artifact_contract_prefix_and_materialized_bytes(
    artifact_mapping, predecessor_sources, sources, reconciliation,
) -> None:
    subject._validate_artifact_mapping_v1(
        artifact_mapping,
        predecessor_sources=predecessor_sources,
        successor_sources=sources,
        reconciliation=reconciliation,
    )
    observed = (ROOT / subject.OUTPUT_RELATIVE).read_bytes()
    assert json.loads(observed) == artifact_mapping
    assert tuple(json.loads(observed)) == subject._ARTIFACT_FIELDS
    assert subject.check_materialized_v1(ROOT)["status"] == "PASS"


def test_deterministic_double_build() -> None:
    first = subject.build_artifact_v1(ROOT)
    second = subject.build_artifact_v1(ROOT)
    assert first == second == (ROOT / subject.OUTPUT_RELATIVE).read_bytes()


def test_real_checker_and_all_required_negative_probes(
    checker, checker_report,
) -> None:
    assert checker_report["status"] == "PASS"
    assert checker_report["repository"]["lifecycle"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    assert checker_report["artifact"] == {
        "source_count": 25,
        "accepted_fact_count": 143,
        "reconciled_row_count": 338,
        "generic_fact_field_count": 11,
        "rich_fields_leaked": False,
        "changed_target_rows": 4,
        "unchanged_rows": 334,
        "non_target_changed_rows": 0,
        "duplicate_count": 0,
    }
    required = {
        "wrong_review_unit",
        "missing_nwj_event",
        "duplicate_nwj_event",
        "formal_source_sha_drift",
        "generic_schema_11_to_12",
        "rich_pair_leak",
        "role_leak",
        "seed_leak",
        "task_id_leak",
        "legacy_positive_to_negative",
        "relevant_to_not_relevant",
        "chemistry_positive_to_negative",
        "training_include_drift",
        "human_training_excluded_true",
        "source_append_reordered",
        "duplicate_source_identity",
        "predecessor_fact_modified",
        "non_nwj_row_modified",
        "wrong_authority_source",
        "calibration_remains_eligible",
        "wrong_exclusion_reason",
        "fifth_row_changes",
        "training_authority_forged",
        "training_mask_target_count_positive",
        "census_refresh_forged",
        "queue_refresh_forged",
        "next_review_started_forged",
        "training_started_forged",
    }
    assert required <= checker_report["tamper_probes"].keys()
    assert all(checker_report["tamper_probes"].values())
    assert all(checker_report["lifecycle_simulations"].values())
    assert checker_report["materialized_equals_fresh_build"] is True
    assert checker_report["deterministic_double_build"] is True


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


def test_checker_committed_unpushed_profile(checker) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=expected,
        head="successor",
        origin_main=checker.BASELINE_COMMIT,
        ahead=1,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected,
    )


def test_checker_published_tracked_clean_profile(checker) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=expected,
        head="successor",
        origin_main="successor",
        ahead=0,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected,
    )


def test_checker_later_clean_descendant_profile(checker) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    checker.validate_repository_relation_values(
        profile=checker.TRACKED_CLEAN,
        expected_paths=expected,
        head="later",
        origin_main="successor",
        ahead=1,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline={*expected, "docs/later.md"},
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("legacy_completed_review_status", generic.COMPLETED_HUMAN_NEGATIVE),
        ("task_relevance_disposition", generic.TASK_NOT_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("training_disposition", "EXCLUDE"),
        ("human_training_excluded", True),
    ),
)
def test_projected_classification_tamper_fails_closed(
    bound, field: str, value: object,
) -> None:
    source = subject._project_bound_nwj_v1(bound)
    records = subject._projection_records_v1(bound)
    facts = list(source.facts)
    facts[0] = replace(facts[0], **{field: value})
    candidate = generic.NormalizedDecisionSource(
        binding=source.binding, facts=tuple(facts)
    )
    with pytest.raises(ERROR, match="NWJ_GENERIC_PROJECTION_CLASSIFICATION_INVALID"):
        subject._validate_projected_nwj_source_v1(candidate, records)


@pytest.mark.parametrize(
    "mutation",
    ("wrong_review_unit", "missing_event", "duplicate_event", "sha_drift"),
)
def test_rich_identity_and_binding_tampers_fail_closed(bound, mutation: str) -> None:
    candidate = copy.deepcopy(bound)
    if mutation == "wrong_review_unit":
        candidate["formal_document"]["sample_identity"]["review_unit_id"] = "WRONG"
    elif mutation == "missing_event":
        candidate["formal_document"]["sample_identity"]["canonical_event_ids"].pop()
    elif mutation == "duplicate_event":
        events = candidate["formal_document"]["sample_identity"]["canonical_event_ids"]
        events[-1] = events[0]
    else:
        candidate["formal_decision_binding"]["SHA256"] = "0" * 64
    with pytest.raises(ERROR):
        subject._validate_rich_nwj_boundary_v1(candidate)


def test_source_duplicate_event_missing_and_reorder_fail_closed(
    bound, predecessor_sources, sources,
) -> None:
    records = subject._projection_records_v1(bound)
    duplicate_source = (*predecessor_sources, predecessor_sources[-1])
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(
            predecessor_sources, duplicate_source, records
        )
    duplicate_fact_source = generic.NormalizedDecisionSource(
        binding=sources[-1].binding,
        facts=(sources[-1].facts[0], sources[-1].facts[0], *sources[-1].facts[2:]),
    )
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(
            predecessor_sources,
            (*predecessor_sources, duplicate_fact_source),
            records,
        )
    missing = generic.NormalizedDecisionSource(
        binding=sources[-1].binding, facts=sources[-1].facts[:-1]
    )
    with pytest.raises(ERROR, match="EXACT25_143"):
        subject._validate_source_chain_v1(
            predecessor_sources, (*predecessor_sources, missing), records
        )
    reordered = (*predecessor_sources[:-1], sources[-1], predecessor_sources[-1])
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(predecessor_sources, reordered, records)


def test_semantic_mutations_fail_before_byte_guard(
    checker, checker_report,
) -> None:
    assert all(checker_report["tamper_probes"].values())
    assert all(
        token != "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
        for name, token in checker_report["tamper_probes"].items()
        if name != "raw_byte_corruption"
    )


def test_destination_and_history_protection_fail_closed(checker) -> None:
    with pytest.raises(ERROR, match="ARTIFACT_DESTINATION_NOT_EXACT"):
        subject._validate_destination_v1(ROOT, ROOT / "unauthorized.json")
    for changed, token in (
        ({"data/raw/new.cif"}, "PROTECTED_PATH_CHANGED"),
        ({"equivariant_diffusion/new.py"}, "PROTECTED_PATH_CHANGED"),
        ({"dataset.py"}, "PROTECTED_PATH_CHANGED"),
        ({"docs/model.ckpt"}, "FORBIDDEN_SUFFIX_CHANGED"),
    ):
        with pytest.raises(ValueError, match=token):
            checker._validate_history_scope(changed)

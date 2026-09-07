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

from covalent_ext import covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import covapie_completed_human_decision_reconciliation_with_6oa_v1 as subject
from covalent_ext import covapie_completed_human_decision_reconciliation_with_nwj_v1 as predecessor


CHECKER = ROOT / subject.CHECKER_RELATIVE
ERROR = subject.CompletedDecisionReconciliationWith6OAError


@pytest.fixture(scope="session")
def checker():
    specification = importlib.util.spec_from_file_location("check_6oa_reconciliation", CHECKER)
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
        "CompletedDecisionReconciliationWith6OAError",
        "project_6oa_completed_decision_v1",
        "load_real_completed_decision_sources_with_6oa_v1",
        "reconcile_real_completed_human_decisions_with_6oa_v1",
        "build_artifact_v1",
        "materialize_artifact_v1",
        "check_materialized_v1",
    )
    assert len(subject.EXACT4_PATHS) == len(set(subject.EXACT4_PATHS)) == 4
    assert all((ROOT / path).is_file() for path in subject.EXACT4_PATHS)


def test_rich_boundary_formal_binding_and_normalization_are_independently_validated(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_6oa_boundary_v1(bound)
    binding = subject._expected_binding_v1(bound)
    assert binding == generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=33043,
        sha256="c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
        schema_version="covapie_6oa_exact4_formal_human_decision_v1",
        review_unit_id="COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72",
    )
    formal = bound["formal_document"]
    assert formal["formal_decisions"]["D2_task_generation_domain_relevance"]["decision"] == "OUT_OF_DOMAIN"
    compatibility = bound["generic_Exact11_compatibility"]
    assert compatibility["normalized_task_relevance_disposition"] == "NOT_RELEVANT"
    assert compatibility["source_formal_generation_domain_decision"] == "OUT_OF_DOMAIN"


def test_projection_is_generic_exact4_exact11_without_rich_fields(
    bound: dict[str, object],
) -> None:
    source = subject._project_bound_6oa_v1(bound)
    assert isinstance(source, generic.NormalizedDecisionSource)
    assert len(source.facts) == 4
    assert tuple(fact.canonical_event_id for fact in source.facts) == ingestion.EXPECTED_EVENT_IDS
    for fact in source.facts:
        row = asdict(fact)
        assert tuple(row) == subject._GENERIC_FACT_FIELDS
        assert len(row) == 11
        assert not subject._FORBIDDEN_RICH_FACT_FIELDS.intersection(row)
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_NEGATIVE
        assert fact.task_relevance_disposition == generic.TASK_NOT_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.training_disposition == generic.TRAINING_NOT_APPLICABLE
        assert fact.human_training_excluded is False


def test_rich_scientific_and_training_boundary_is_exact(bound: dict[str, object]) -> None:
    formal = bound["formal_document"]
    role = formal["selected_role_context"]
    assert role["warhead_atom_ids"] == ["C5", "O3"]
    assert role["linker_atom_ids"] == []
    assert role["scaffold_atom_ids"] == ["C", "C1", "C2", "C3", "C4", "O", "O1", "O2"]
    assert role["boundary"] == "C4--C5/SING"
    assert role["minimal_seed"]["atom_ids"] == ["C3", "C4"]
    assert role["minimal_seed"]["primary_scaffold_side_anchor"] == "C4"
    exact5 = formal["canonical_Exact5"]
    assert exact5["task_count"] == 5
    assert exact5["B3_present"] is True
    assert exact5["sixth_task"] is False
    assert exact5["selected_structural_applicability_task_ids"] == [0, 3, 4]
    geometry = formal["geometry_boundary"]
    assert [row["exact_POST_distance_angstrom"] for row in geometry["events"]] == [
        1.853206,
        1.674652,
        1.347977,
        1.677347,
    ]
    assert geometry["rank857_caveat"]["geometry_outlier"] is True
    assert formal["training_boundary"]["formal_training_admitted"] is False
    assert formal["readiness"]["READY_FOR_TRAINING"] is False


def test_source_and_fact_chains_are_strict_prefix_append(
    predecessor_sources, sources, bound: dict[str, object]
) -> None:
    records = subject._projection_records_v1(bound)
    subject._validate_source_chain_v1(predecessor_sources, sources, records)
    assert len(predecessor_sources) == 25
    assert len(sources) == 26
    assert sources[:-1] == predecessor_sources
    before_facts = tuple(fact for source in predecessor_sources for fact in source.facts)
    after_facts = tuple(fact for source in sources for fact in source.facts)
    assert len(before_facts) == 143
    assert len(after_facts) == 147
    assert after_facts[:143] == before_facts
    assert after_facts[143:] == sources[-1].facts


def test_published_adapter_reproduces_with_nwj_predecessor(
    predecessor_sources, predecessor_result
) -> None:
    adapted = subject.historical_adapter_owner._adapt_historical_v1(ROOT)
    reproduced = generic.reconcile_completed_human_decisions_v1(adapted, predecessor_sources)
    published = predecessor.reconcile_real_completed_human_decisions_with_nwj_v1(ROOT)
    assert reproduced == published == predecessor_result


def test_historical_6oa_state_is_exactly_unreviewed(predecessor_result) -> None:
    subject._prove_6oa_predecessor_historical_state_v1(predecessor_result.reconciled_rows)
    targets = [
        row
        for row in predecessor_result.reconciled_rows
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS
    ]
    assert [row["raw_priority_rank"] for row in targets] == ["29"] * 4
    assert [row["raw_unit_event_count"] for row in targets] == ["4"] * 4
    assert [row["current_review_status"] for row in targets] == [generic.CURRENTLY_UNREVIEWED] * 4
    assert [row["calibration_eligible"] for row in targets] == ["true"] * 4


def test_reconciliation_changes_exact4_and_preserves_334(
    predecessor_result, reconciliation
) -> None:
    subject._validate_reconciliation_delta_v1(predecessor_result, reconciliation)
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(predecessor_result.reconciled_rows, reconciliation.reconciled_rows, strict=True):
        if old["canonical_event_id"] not in targets:
            changed_non_target += old != new
            continue
        assert {key for key in old if old[key] != new[key]} == subject._ALLOWED_RECONCILIATION_FIELDS
        assert new["current_review_status"] == generic.COMPLETED_HUMAN_NEGATIVE
        assert new["current_status_authority_sources_json"] == generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
        assert new["calibration_eligible"] == "false"
        assert new["calibration_exclusion_reason"] == generic.COMPLETED_HUMAN_NEGATIVE
        changed_target += old != new
    assert (changed_target, changed_non_target) == (4, 0)


def test_review_summary_is_computed_and_matches_expected_delta(
    predecessor_result, reconciliation, checker
) -> None:
    assert predecessor_result.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert reconciliation.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    computed = checker._computed_review_summary([dict(row) for row in reconciliation.reconciled_rows])
    assert computed == reconciliation.review_summary
    assert computed["completed_positive_event_count"] == 123
    assert computed["completed_negative_event_count"] == 48
    assert computed["completed_total_event_count"] == 171
    assert computed["unreviewed_event_count"] == 167


def test_coverage_is_frozen_aggregate_plus_local_task_domain_delta(
    artifact_mapping, checker
) -> None:
    predecessor_artifact = json.loads((ROOT / predecessor.OUTPUT_RELATIVE).read_text())
    report = checker._verify_coverage_contract(
        predecessor_artifact["normalized_facts"], artifact_mapping["normalized_facts"]
    )
    assert report["predecessor"] == predecessor.SUCCESSOR_COVERAGE_SUMMARY
    assert report["successor"]["decision_category_distribution"] == {
        "chemistry_positive": 99,
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
    assert len(artifact_mapping["source_bindings"]) == 26
    assert len(artifact_mapping["normalized_facts"]) == 147
    assert len(artifact_mapping["reconciled_rows"]) == 338
    assert (ROOT / subject.OUTPUT_RELATIVE).read_bytes() == subject.build_artifact_v1(ROOT)


def test_deterministic_double_build_and_materialized_check() -> None:
    first = subject.build_artifact_v1(ROOT)
    second = subject.build_artifact_v1(ROOT)
    assert first == second
    assert subject.check_materialized_v1(ROOT) == {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 26,
        "accepted_fact_count": 147,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }


def test_tamper_helper_accepts_only_prefixed_expected_valueerror(checker) -> None:
    assert checker._expect_tamper(
        "expected",
        "EXPECTED_TOKEN",
        lambda: checker._fail("EXPECTED_TOKEN"),
    ) == "EXPECTED_TOKEN"
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
    with pytest.raises(ValueError, match="TAMPER_PROBE_DID_NOT_FAIL:callback_passed"):
        checker._expect_tamper("callback_passed", "EXPECTED_TOKEN", lambda: None)


@pytest.mark.parametrize("exception", [TypeError("boom"), KeyError("boom"), AssertionError("boom")])
def test_tamper_helper_does_not_accept_arbitrary_exception_classes(
    checker, exception: Exception
) -> None:
    with pytest.raises(type(exception), match="boom"):
        checker._expect_tamper(
            "arbitrary_exception",
            "EXPECTED_TOKEN",
            lambda: (_ for _ in ()).throw(exception),
        )


def test_review_summary_and_coverage_probe_mutations_are_distinct_and_semantic(
    checker, artifact_mapping, bound: dict[str, object]
) -> None:
    old = json.loads((ROOT / predecessor.OUTPUT_RELATIVE).read_text())
    projection = checker._independent_expected_projection(bound)
    positive = checker._review_summary_probe_candidate(
        artifact_mapping, "completed_positive_event_count", 127
    )
    negative = checker._review_summary_probe_candidate(
        artifact_mapping, "completed_negative_event_count", 44
    )
    assert artifact_mapping["review_summary"]["completed_positive_event_count"] == 123
    assert artifact_mapping["review_summary"]["completed_negative_event_count"] == 48
    assert positive["review_summary"]["completed_positive_event_count"] == 127
    assert positive["review_summary"]["completed_negative_event_count"] == 48
    assert negative["review_summary"]["completed_positive_event_count"] == 123
    assert negative["review_summary"]["completed_negative_event_count"] == 44
    for candidate in (positive, negative):
        with pytest.raises(ValueError, match="ARTIFACT_REVIEW_SUMMARY_INVALID"):
            checker._verify_full_semantics(
                candidate,
                predecessor_artifact=old,
                expected_projection=projection,
            )

    chemistry = checker._coverage_probe_candidate(
        "chemistry_positive", 103, decision_category=True
    )
    task_domain = checker._coverage_probe_candidate(
        "task_domain_negative", 27, decision_category=True
    )
    assert chemistry is not task_domain
    assert chemistry["decision_category_distribution"]["chemistry_positive"] == 103
    assert chemistry["decision_category_distribution"]["task_domain_negative"] == 28
    assert task_domain["decision_category_distribution"]["chemistry_positive"] == 99
    assert task_domain["decision_category_distribution"]["task_domain_negative"] == 27
    for coverage in (chemistry, task_domain):
        with pytest.raises(ValueError, match="SUCCESSOR_COVERAGE_DRIFT"):
            checker._verify_full_semantics(
                artifact_mapping,
                predecessor_artifact=old,
                expected_projection=projection,
                successor_coverage=coverage,
            )


def test_raw_byte_probe_reuses_actual_byte_comparator(checker, monkeypatch) -> None:
    calls: list[tuple[bytes, bytes]] = []

    def capture(expected: bytes, observed: bytes) -> None:
        calls.append((expected, observed))

    monkeypatch.setattr(checker, "_verify_byte_identity", capture)
    checker._raw_byte_corruption_probe(b"payload")
    assert calls == [(b"payload", b"payload ")]
    monkeypatch.undo()
    checker._verify_byte_identity(b"same", b"same")
    assert checker._expect_tamper(
        "raw_byte_corruption",
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
        lambda: checker._raw_byte_corruption_probe(b"payload"),
    ) == "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"


def test_real_checker_and_all_required_negative_probes(checker) -> None:
    report = checker.check(ROOT)
    assert report["status"] == "PASS"
    assert report["repository"]["lifecycle"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    required = {
        "wrong_review_unit",
        "missing_6oa_event",
        "duplicate_6oa_event",
        "wrong_raw_priority_rank",
        "formal_source_sha_drift",
        "OUT_OF_DOMAIN_source_value_lost",
        "normalized_relevant",
        "chemistry_negative",
        "legacy_positive",
        "training_include",
        "training_exclude_only",
        "human_training_excluded_true",
        "generic_schema_11_to_12",
        "pair_leak",
        "role_leak",
        "seed_leak",
        "task_id_leak",
        "geometry_outlier_leak",
        "PRE_leak",
        "source_append_reordered",
        "duplicate_source_identity",
        "predecessor_fact_modified",
        "predecessor_binding_modified",
        "6oa_row_remains_unreviewed",
        "wrong_authority_source",
        "calibration_remains_eligible",
        "wrong_exclusion_reason",
        "fifth_row_changes",
        "non_target_row_changes",
        "completed_positive_incorrectly_plus4",
        "completed_negative_not_plus4",
        "task_domain_negative_not_plus4",
        "chemistry_positive_coverage_plus4",
        "label_ready_count_changed",
        "training_mask_target_positive",
        "training_authority_forged",
        "census_refresh_forged",
        "queue_refresh_forged",
        "next_review_started_forged",
        "task_label_authority_forged",
        "training_started_forged",
        "raw_byte_corruption",
        "unexpected_fifth_file",
        "filesystem_executable_bit",
        "tracked_git_mode_not_100644",
        "sixth_task_drift",
        "B3_drift",
    }
    assert required <= set(report["tamper_probes"])
    assert "FAIL_CLOSED" not in set(report["tamper_probes"].values())
    assert report["tamper_probes"]["completed_positive_incorrectly_plus4"] == "ARTIFACT_REVIEW_SUMMARY_INVALID"
    assert report["tamper_probes"]["completed_negative_not_plus4"] == "ARTIFACT_REVIEW_SUMMARY_INVALID"
    assert report["tamper_probes"]["chemistry_positive_coverage_plus4"] == "SUCCESSOR_COVERAGE_DRIFT"
    assert report["tamper_probes"]["task_domain_negative_not_plus4"] == "SUCCESSOR_COVERAGE_DRIFT"
    assert report["tamper_probes"]["raw_byte_corruption"] == "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
    assert report["tamper_probes"]["tracked_git_mode_not_100644"] == "TRACKED_GIT_INDEX_MODE_INVALID"
    if report["repository"]["lifecycle"] == checker.CANDIDATE_UNTRACKED:
        assert report["repository"]["git_index_mode_checked"] is False
        assert "git_index_modes" not in report["repository"]
    else:
        assert report["repository"]["git_index_mode_checked"] is True
        modes = report["repository"]["git_index_modes"]
        assert type(modes) is dict
        assert set(modes) == {
            path.as_posix() for path in subject.EXACT4_PATHS
        }
        assert set(modes.values()) == {"100644"}
    assert report["repository"]["expected_git_publication_mode"] == "100644"
    assert all("git_mode" not in row for row in report["Exact4_files"])
    assert all(row["expected_git_publication_mode"] == "100644" for row in report["Exact4_files"])


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


def test_live_repository_git_index_mode_contract(checker) -> None:
    report = checker._verify_repository(ROOT)
    assert report["lifecycle"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    assert report["expected_git_publication_mode"] == "100644"
    if report["lifecycle"] == checker.CANDIDATE_UNTRACKED:
        assert report["git_index_mode_checked"] is False
        assert "git_index_modes" not in report
    else:
        assert report["git_index_mode_checked"] is True
        modes = report["git_index_modes"]
        assert type(modes) is dict
        assert set(modes) == {
            path.as_posix() for path in subject.EXACT4_PATHS
        }
        assert set(modes.values()) == {"100644"}


def test_tracked_index_mode_parser_accepts_exact4_100644(checker) -> None:
    stage_lines, expected = _valid_stage_lines()
    assert checker.validate_tracked_index_modes(stage_lines, expected) == {
        path: "100644" for path in expected
    }


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
        ("successor", subject.ERROR_PREFIX, 1, set()),
        ("successor", "successor", 0, set()),
        ("later", "successor", 1, {"docs/later.md"}),
    ],
)
def test_checker_tracked_clean_lifecycle_relations(
    checker, head: str, origin: str, ahead: int, changed: set[str]
) -> None:
    expected = {path.as_posix() for path in subject.EXACT4_PATHS}
    if origin == subject.ERROR_PREFIX:
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
        ("task_relevance_disposition", generic.TASK_RELEVANT),
        ("chemistry_disposition", generic.CHEMISTRY_NEGATIVE),
        ("legacy_completed_review_status", generic.COMPLETED_HUMAN_POSITIVE),
        ("training_disposition", generic.TRAINING_INCLUDE),
        ("training_disposition", generic.TRAINING_EXCLUDE),
        ("human_training_excluded", True),
    ],
)
def test_projected_classification_tamper_fails_closed(
    bound: dict[str, object], field: str, value: object
) -> None:
    source = subject._project_bound_6oa_v1(bound)
    facts = list(source.facts)
    facts[-1] = replace(facts[-1], **{field: value})
    mutated = generic.NormalizedDecisionSource(binding=source.binding, facts=tuple(facts))
    with pytest.raises(ERROR, match="COVAPIE_6OA_RECONCILIATION_V1_ERROR"):
        subject._validate_projected_6oa_source_v1(
            mutated, subject._projection_records_v1(bound)
        )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("formal_document", "sample_identity", "raw_priority_rank"), 30),
        (("formal_document", "formal_decisions", "D2_task_generation_domain_relevance", "decision"), "NOT_RELEVANT"),
        (("formal_document", "canonical_Exact5", "B3_present"), False),
        (("formal_document", "canonical_Exact5", "sixth_task"), True),
        (("formal_document", "geometry_boundary", "POST_geometry_training_authority"), True),
        (("formal_document", "PRE_boundary", "PRE_authority"), True),
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
    with pytest.raises(ERROR, match="COVAPIE_6OA_RECONCILIATION_V1_ERROR"):
        subject._project_bound_6oa_v1(mutated)


def test_source_missing_duplicate_reorder_and_predecessor_mutation_fail_closed(
    predecessor_sources, sources, bound: dict[str, object]
) -> None:
    records = subject._projection_records_v1(bound)
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(predecessor_sources, sources[:-1], records)
    duplicate = (*predecessor_sources, sources[-1], sources[-1])
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(predecessor_sources, duplicate, records)
    reordered = (*predecessor_sources[:-1], sources[-1], predecessor_sources[-1])
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(predecessor_sources, reordered, records)
    changed = list(predecessor_sources)
    changed[0] = generic.NormalizedDecisionSource(
        binding=changed[0].binding,
        facts=(replace(changed[0].facts[0], source_decision_sha256="0" * 64), *changed[0].facts[1:]),
    )
    with pytest.raises(ERROR):
        subject._validate_source_chain_v1(tuple(changed), sources, records)


def test_semantic_mutations_fail_before_any_byte_guard(
    checker, artifact_mapping, bound: dict[str, object]
) -> None:
    old = json.loads((ROOT / predecessor.OUTPUT_RELATIVE).read_text())
    projection = checker._independent_expected_projection(bound)
    for mutation in (
        ("normalized_facts", -1, "role_profile", "FORGED"),
        ("reconciled_rows", 0, "calibration_exclusion_reason", "FORGED"),
    ):
        candidate = copy.deepcopy(artifact_mapping)
        collection, index, key, value = mutation
        candidate[collection][index][key] = value
        with pytest.raises(ValueError) as caught:
            checker._verify_full_semantics(
                candidate,
                predecessor_artifact=old,
                expected_projection=projection,
            )
        assert "MATERIALIZED" not in str(caught.value)


def test_destination_and_output_inventory_protection_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ERROR, match="DESTINATION_NOT_EXACT"):
        subject._validate_destination_v1(ROOT, tmp_path / "wrong.json")
    root = tmp_path / "repo"
    output = root / subject.OUTPUT_RELATIVE
    output.parent.mkdir(parents=True)
    (output.parent / "unexpected.txt").write_text("unexpected\n")
    with pytest.raises(ERROR, match="CONTAINS_EXTRA_FILE"):
        subject._validate_destination_v1(root, output)

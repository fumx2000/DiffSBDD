from __future__ import annotations

import copy
from dataclasses import asdict, replace
import importlib.util
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1
    as ingestion,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_4lh_v1 as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / subject.CHECKER_RELATIVE
ERROR = subject.CompletedDecisionReconciliationWith4LHError
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWith4LHError",
    "project_4lh_completed_decision_v1",
    "load_real_completed_decision_sources_with_4lh_v1",
    "reconcile_real_completed_human_decisions_with_4lh_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)


@pytest.fixture(scope="module")
def bound() -> dict[str, object]:
    return ingestion.load_frozen_formal_decision_v1(ROOT)


@pytest.fixture(scope="module")
def projection(bound: dict[str, object]) -> generic.NormalizedDecisionSource:
    return subject._project_validated_4lh_binding_v1(bound)


@pytest.fixture(scope="module")
def sources() -> tuple[generic.NormalizedDecisionSource, ...]:
    return subject.load_real_completed_decision_sources_with_4lh_v1(ROOT)


@pytest.fixture(scope="module")
def reconciliation() -> generic.ReconciliationResult:
    return subject.reconcile_real_completed_human_decisions_with_4lh_v1(ROOT)


@pytest.fixture(scope="module")
def artifact_payload() -> bytes:
    return subject.build_artifact_v1(ROOT)


def _load_checker():
    spec = importlib.util.spec_from_file_location("four_lh_reconciliation_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


@pytest.fixture(scope="module")
def checker_report(checker):
    return checker.run_check_v1(ROOT)


def _artifact_mapping(
    sources: tuple[generic.NormalizedDecisionSource, ...],
    reconciliation: generic.ReconciliationResult,
) -> dict[str, object]:
    return {
        "reconciled_rows": [dict(row) for row in reconciliation.reconciled_rows],
        "source_bindings": [asdict(source.binding) for source in sources],
        "normalized_facts": [
            asdict(fact) for source in sources for fact in source.facts
        ],
        "review_summary": dict(reconciliation.review_summary),
    }


def test_public_api_exact4_paths_and_direct_architecture() -> None:
    assert subject.__all__ == EXPECTED_PUBLIC_API
    assert tuple(path.as_posix() for path in subject.EXACT4_PATHS) == (
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_4lh_v1.py",
        "scripts/check_covapie_completed_human_decision_reconciliation_with_4lh_v1.py",
        "tests/test_covapie_completed_human_decision_reconciliation_with_4lh_v1.py",
        "data/derived/covalent_small/covapie_completed_human_decision_reconciliation_with_4lh_v1/covapie_completed_human_decision_reconciliation_with_4lh_v1.json",
    )
    source = (ROOT / subject.SOURCE_RELATIVE).read_text(encoding="utf-8")
    assert "covapie_completed_human_decision_reconciliation_with_0d8_v1" in source
    assert "covapie_4lh_completed_decision_ingestion" in source
    assert "equivariant_diffusion" not in source
    assert "lightning_modules" not in source
    assert "optimizer.step" not in source
    assert "backward(" not in source


def test_projection_is_exact_ingestion_generic_exact11(
    bound: dict[str, object], projection: generic.NormalizedDecisionSource
) -> None:
    records = subject._projection_records_v1(bound)
    assert [asdict(fact) for fact in projection.facts] == list(records)
    assert tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) == tuple(
        subject._GENERIC_FACT_FIELDS
    )
    assert len(projection.facts) == 4
    assert projection.binding == subject._expected_binding_v1()
    assert projection.binding.path_namespace == "repository_parent_relative"
    assert not projection.binding.source_path.startswith("/")


def test_4lh_classification_boundary_and_no_rich_leakage(
    projection: generic.NormalizedDecisionSource,
) -> None:
    assert [fact.canonical_event_id for fact in projection.facts] == list(
        ingestion.EXPECTED_EVENT_IDS
    )
    for fact in projection.facts:
        assert fact.task_relevance_disposition == generic.TASK_RELEVANT
        assert fact.chemistry_disposition == generic.CHEMISTRY_POSITIVE
        assert fact.legacy_completed_review_status == generic.COMPLETED_HUMAN_POSITIVE
        assert fact.training_disposition == generic.TRAINING_INCLUDE
        assert fact.human_training_excluded is False
        assert set(asdict(fact)) == set(subject._GENERIC_FACT_FIELDS)
        assert not (subject._FORBIDDEN_RICH_FACT_FIELDS & set(asdict(fact)))
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["decision_category_distribution"] == {
        "chemistry_positive": 95,
        "chemistry_negative": 20,
        "task_domain_negative": 20,
        "task_domain_positive": 0,
    }


def test_upstream_pair_role_exact5_and_training_boundaries(
    bound: dict[str, object],
) -> None:
    subject._validate_rich_4lh_boundary_v1(bound)
    formal = bound["formal_document"]
    assert isinstance(formal, dict)
    decisions = formal["formal_human_decision"]
    pair = decisions["D3_reactive_pair"]
    role = formal["selected_role_partition"]
    tasks = formal["canonical_Exact5_task_applicability"]
    pre = formal["PRE_boundary"]
    post = formal["POST_boundary"]
    training = formal["training_boundary"]
    assert isinstance(pair, dict)
    assert isinstance(role, dict)
    assert isinstance(tasks, dict)
    assert isinstance(training, dict)
    assert (pair["protein_atom"], pair["ligand_atom"]) == ("SG", "CAP")
    assert pair["human_authority"] is True
    assert role["sample_level_human_role_authority"] is True
    assert (role["W"], role["L"], role["S"]) == (
        ["CAP", "CAQ", "CBE", "OAE", "NBA"],
        [],
        list(ingestion.SCAFFOLD_ATOMS),
    )
    assert [task["semantic_long_name"] for task in tasks["tasks"]] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert tasks["task_count"] == 5
    assert tasks["B3_present"] is True
    assert tasks["sixth_task"] is False
    assert tasks["applicable_task_ids"] == [0, 3, 4]
    assert tasks["event_task_label_rows_materialized"] is False
    assert (pre["per_event_mapping_count"], pre["PRE_source_mapping_status"]) == (
        2,
        "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS",
    )
    assert pre["PRE_status"] == "PRE_REACTION_UNRESOLVED"
    assert pre["PRE_authority"] is False
    assert post["explicit_event_count"] == 4
    assert post["POST_training_authority"] is False
    assert training["human_training_use_disposition"] == "INCLUDE"
    assert training["future_training_admission_candidate"] is True
    assert training["formal_training_admitted"] is False
    assert training["mask_targets_created"] is False
    assert training["training_materialization_allowed"] is False
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["training_mask_target_count"] == 0
    assert subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False


def test_source_chain_is_prefix_preserving_exact23_135(
    bound: dict[str, object], sources: tuple[generic.NormalizedDecisionSource, ...]
) -> None:
    predecessor = sources[:-1]
    records = subject._projection_records_v1(bound)
    subject._validate_source_chain_v1(predecessor, sources, records)
    assert len(predecessor) == 22
    assert len(sources) == 23
    assert sum(len(source.facts) for source in predecessor) == 131
    assert sum(len(source.facts) for source in sources) == 135
    assert tuple(len(source.facts) for source in sources) == (
        8, 16, 8, 9, 8, 8, 8, 7, 6, 5,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    )
    assert len({source.binding.review_unit_id for source in sources}) == 23
    assert len({source.binding.stable_identity for source in sources}) == 23


def test_reconciliation_changes_only_4lh_exact4(
    reconciliation: generic.ReconciliationResult,
) -> None:
    before = subject.predecessor_owner.reconcile_real_completed_human_decisions_with_0d8_v1(
        ROOT
    )
    assert before.review_summary == subject._PREDECESSOR_REVIEW_SUMMARY
    assert reconciliation.review_summary == subject._SUCCESSOR_REVIEW_SUMMARY
    assert len(reconciliation.normalized_facts) == 135
    changed_target = 0
    changed_non_target = 0
    for old, new in zip(before.reconciled_rows, reconciliation.reconciled_rows, strict=True):
        if old["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS:
            changed_target += old != new
        else:
            changed_non_target += old != new
    assert (changed_target, changed_non_target) == (4, 0)
    rows = {
        row["canonical_event_id"]: row
        for row in reconciliation.reconciled_rows
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS
    }
    assert tuple(rows) == ingestion.EXPECTED_EVENT_IDS
    assert all(
        row["current_review_status"] == generic.COMPLETED_HUMAN_POSITIVE
        and row["calibration_eligible"] == "false"
        and row["calibration_exclusion_reason"]
        == generic.COMPLETED_HUMAN_POSITIVE
        for row in rows.values()
    )


def test_artifact_is_existing_result_contract_prefix_stable_and_deterministic(
    artifact_payload: bytes,
    sources: tuple[generic.NormalizedDecisionSource, ...],
    reconciliation: generic.ReconciliationResult,
) -> None:
    assert artifact_payload == subject.build_artifact_v1(ROOT)
    artifact = json.loads(artifact_payload)
    assert tuple(artifact) == subject._ARTIFACT_FIELDS
    expected = _artifact_mapping(sources, reconciliation)
    assert artifact == expected
    assert artifact["normalized_facts"][:131] == expected["normalized_facts"][:131]
    assert artifact["normalized_facts"][-4:] == [
        asdict(fact) for fact in sources[-1].facts
    ]


def test_materialized_artifact_and_checker_pass(
    artifact_payload: bytes, checker, checker_report: dict[str, object]
) -> None:
    assert (ROOT / subject.OUTPUT_RELATIVE).read_bytes() == artifact_payload
    report = checker_report
    assert report["status"] == "PASS"
    assert report["artifact"]["accepted_fact_count"] == 135
    assert report["artifact"]["duplicate_count"] == 0
    assert report["coverage"]["predecessor"] == subject.PREDECESSOR_COVERAGE_SUMMARY
    assert report["coverage"]["successor"] == subject.SUCCESSOR_COVERAGE_SUMMARY
    assert report["4LH_boundary"]["pair"] == "SG-CAP"
    assert report["4LH_boundary"]["training_authority"] is False
    assert all(report["tamper_probes"].values())
    assert report["current_census_refresh"] is False
    assert report["queue_refresh"] is False
    assert report["training_started"] is False
    assert report["repository"]["lifecycle"] in {
        checker.CANDIDATE_UNTRACKED,
        checker.TRACKED_CLEAN,
    }
    assert report["repo_root_global_ROOT_dependency_removed"] is True
    assert report["lifecycle_simulations"] == {
        "candidate_untracked": True,
        "tracked_clean": True,
        "committed_unpushed": True,
        "pushed_successor": True,
        "later_clean_descendant": True,
    }
    assert report["tamper_probes"] == {
        "predecessor_order_tamper": "PREDECESSOR_FACT_PREFIX_INVALID",
        "4LH_fact_tamper": "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION",
        "duplicate_source_tamper": "ARTIFACT_SOURCE_IDENTITY_DUPLICATE",
        "count_tamper": "ARTIFACT_EXACT_COUNTS_INVALID",
        "decision_category_tamper": "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION",
        "formal_source_sha_tamper": "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION",
        "rich_field_leak_tamper": "ARTIFACT_GENERIC_FACT_NOT_EXACT11",
        "target_status_tamper": "4LH_RECONCILIATION_TRANSITION_INVALID",
        "non_target_row_tamper": "RECONCILIATION_DELTA_NOT_EXACT4_ONLY",
        "review_summary_tamper": "ARTIFACT_GENERIC_REVIEW_SUMMARY_INVALID",
        "artifact_bytes_tamper": "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
    }


def _lifecycle_inputs() -> tuple[tuple[str, ...], set[str]]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    return paths, set(paths)


def test_checker_lifecycle_candidate_untracked_and_tracked_clean_accepted(
    checker,
) -> None:
    paths, expected = _lifecycle_inputs()
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


def test_checker_tracked_clean_committed_unpushed_and_pushed_accepted(
    checker,
) -> None:
    _paths, expected = _lifecycle_inputs()
    common = {
        "profile": checker.TRACKED_CLEAN,
        "expected_paths": expected,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected,
    }
    checker.validate_repository_relation_values(
        **common,
        head="publication-head",
        origin_main=checker.BASELINE_COMMIT,
        ahead=1,
    )
    checker.validate_repository_relation_values(
        **common,
        head="pushed-head",
        origin_main="pushed-head",
        ahead=0,
    )
    checker.validate_repository_relation_values(
        **{**common, "changed_since_baseline": {*expected, "docs/later.md"}},
        head="later-head",
        origin_main="later-origin",
        ahead=2,
    )


def test_checker_lifecycle_mixed_tracking_dirty_and_staged_rejected(checker) -> None:
    paths, expected = _lifecycle_inputs()
    with pytest.raises(ValueError, match="MIXED_TRACKING_STATE"):
        checker.classify_repository_profile(
            expected_paths=paths,
            tracked_paths={paths[0]},
            ordinary_untracked=expected - {paths[0]},
            status_lines=tuple("?? " + path for path in paths[1:]),
            working_diff=set(),
            cached_diff=set(),
        )
    with pytest.raises(ValueError, match="TRACKED_WORKTREE_MODIFICATION_PRESENT"):
        checker.classify_repository_profile(
            expected_paths=paths,
            tracked_paths=expected,
            ordinary_untracked=set(),
            status_lines=(" M " + paths[0],),
            working_diff={paths[0]},
            cached_diff=set(),
        )
    with pytest.raises(ValueError, match="STAGED_INDEX_CHANGE_PRESENT"):
        checker.classify_repository_profile(
            expected_paths=paths,
            tracked_paths=expected,
            ordinary_untracked=set(),
            status_lines=("M  " + paths[0],),
            working_diff=set(),
            cached_diff={paths[0]},
        )


@pytest.mark.parametrize(
    ("overrides", "token"),
    (
        ({"behind": 1}, "TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID"),
        (
            {"baseline_is_ancestor_of_head": False},
            "TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID",
        ),
        (
            {"baseline_is_ancestor_of_origin": False},
            "TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID",
        ),
        (
            {"origin_is_ancestor_of_head": False},
            "TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID",
        ),
        (
            {"changed_since_baseline": {"docs/unrelated.md"}},
            "TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID",
        ),
    ),
)
def test_checker_tracked_clean_relation_failures_rejected(
    checker, overrides: dict[str, object], token: str
) -> None:
    _paths, expected = _lifecycle_inputs()
    values: dict[str, object] = {
        "profile": checker.TRACKED_CLEAN,
        "expected_paths": expected,
        "head": "publication-head",
        "origin_main": checker.BASELINE_COMMIT,
        "ahead": 1,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected,
    }
    values.update(overrides)
    with pytest.raises(ValueError, match=token):
        checker.validate_repository_relation_values(**values)


@pytest.mark.parametrize(
    ("changed", "token"),
    (
        ({"data/raw/new.cif"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"checkpoints/new.bin"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"equivariant_diffusion/new.py"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"lightning_modules.py"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"dataset.py"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"data/prepare_crossdocked.py"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"covapie-state/new.json"}, "PROTECTED_PATH_CHANGED_SINCE_BASELINE"),
        ({"docs/forbidden.ckpt"}, "FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE"),
    ),
)
def test_checker_tracked_history_protection_remains_fail_closed(
    checker, changed: set[str], token: str
) -> None:
    with pytest.raises(ValueError, match=token):
        checker._validate_history_scope(changed)


def test_checker_semantic_tampers_hit_semantic_tokens_not_byte_mismatch(
    checker,
    bound: dict[str, object],
    sources: tuple[generic.NormalizedDecisionSource, ...],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _artifact_mapping(sources, reconciliation)
    predecessor_artifact = json.loads(
        (ROOT / subject.predecessor_owner.OUTPUT_RELATIVE).read_bytes()
    )
    projection = checker._expected_projection_from_ingestion(bound)

    cases: list[tuple[dict[str, object], str]] = []
    reordered = copy.deepcopy(artifact)
    reordered["normalized_facts"][0], reordered["normalized_facts"][1] = (
        reordered["normalized_facts"][1],
        reordered["normalized_facts"][0],
    )
    cases.append((reordered, "PREDECESSOR_FACT_PREFIX_INVALID"))
    changed_fact = copy.deepcopy(artifact)
    changed_fact["normalized_facts"][-1]["chemistry_disposition"] = "NEGATIVE"
    cases.append((changed_fact, "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION"))
    duplicate = copy.deepcopy(artifact)
    duplicate["source_bindings"][-1] = copy.deepcopy(duplicate["source_bindings"][0])
    cases.append((duplicate, "ARTIFACT_SOURCE_IDENTITY_DUPLICATE"))
    missing = copy.deepcopy(artifact)
    missing["normalized_facts"].pop()
    cases.append((missing, "ARTIFACT_EXACT_COUNTS_INVALID"))
    classification = copy.deepcopy(artifact)
    classification["normalized_facts"][-1]["task_relevance_disposition"] = "NOT_RELEVANT"
    cases.append((classification, "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION"))

    for candidate, token in cases:
        with pytest.raises(ValueError, match=token) as caught:
            checker._verify_artifact_semantics(
                candidate,
                expected_predecessor_artifact=predecessor_artifact,
                expected_projection=projection,
            )
        assert "MATERIALIZED_ARTIFACT_BYTES_MISMATCH" not in str(caught.value)


def test_checker_raw_byte_tamper_remains_separate(checker, artifact_payload: bytes) -> None:
    with pytest.raises(ValueError, match="MATERIALIZED_ARTIFACT_BYTES_MISMATCH"):
        checker._verify_artifact_byte_identity(
            artifact_payload, artifact_payload + b" "
        )


def test_checker_semantic_verifier_has_no_module_root_repository_read(checker) -> None:
    checker_source = CHECKER.read_text(encoding="utf-8")
    semantic_source = checker_source.split("def _verify_artifact_semantics(", 1)[1].split(
        "\ndef _verify_coverage_contract", 1
    )[0]
    assert "ROOT" not in semantic_source
    assert "read_bytes" not in semantic_source


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("chemistry_disposition", "NEGATIVE"),
        ("task_relevance_disposition", "NOT_RELEVANT"),
        ("training_disposition", "NOT_APPLICABLE"),
        ("source_binding_path", "tampered/source.json"),
    ),
)
def test_one_4lh_projection_fact_tamper_fails_closed(
    bound: dict[str, object],
    projection: generic.NormalizedDecisionSource,
    field: str,
    value: object,
) -> None:
    records = subject._projection_records_v1(bound)
    facts = list(projection.facts)
    facts[0] = replace(facts[0], **{field: value})
    candidate = generic.NormalizedDecisionSource(
        binding=projection.binding, facts=tuple(facts)
    )
    with pytest.raises(ERROR, match="4LH_GENERIC_PROJECTION_NOT_EXACT_OWNER_PROJECTION"):
        subject._validate_projected_4lh_source_v1(candidate, records)


def test_predecessor_order_source_identity_and_count_tamper_fail_closed(
    bound: dict[str, object], sources: tuple[generic.NormalizedDecisionSource, ...]
) -> None:
    records = subject._projection_records_v1(bound)
    predecessor = list(sources[:-1])
    reordered = list(predecessor)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(ERROR, match="PREDECESSOR_WITH_0D8_SOURCE_CHAIN"):
        subject._validate_source_chain_v1(reordered, (*reordered, sources[-1]), records)

    duplicate = list(sources)
    duplicate[-1] = duplicate[-2]
    with pytest.raises(ERROR, match="4LH_SOURCE_PROJECTION_IDENTITY_INVALID"):
        subject._validate_source_chain_v1(predecessor, duplicate, records)

    missing = sources[:-1]
    with pytest.raises(ERROR, match="PREFIX_APPEND_EXACT23_135"):
        subject._validate_source_chain_v1(predecessor, missing, records)


def test_artifact_content_and_summary_tamper_fail_closed(
    sources: tuple[generic.NormalizedDecisionSource, ...],
    reconciliation: generic.ReconciliationResult,
) -> None:
    mapping = _artifact_mapping(sources, reconciliation)
    changed_fact = copy.deepcopy(mapping)
    changed_fact["normalized_facts"][-1]["chemistry_disposition"] = "NEGATIVE"
    with pytest.raises(ERROR, match="ARTIFACT_CONTENT_OR_PREFIX_INVALID"):
        subject._validate_artifact_mapping_v1(
            changed_fact,
            predecessor_sources=sources[:-1],
            successor_sources=sources,
            reconciliation=reconciliation,
        )

    changed_summary = copy.deepcopy(mapping)
    changed_summary["review_summary"]["completed_total_event_count"] = 154
    with pytest.raises(ERROR, match="ARTIFACT_CONTENT_OR_PREFIX_INVALID"):
        subject._validate_artifact_mapping_v1(
            changed_summary,
            predecessor_sources=sources[:-1],
            successor_sources=sources,
            reconciliation=reconciliation,
        )

    extra_rich = copy.deepcopy(mapping)
    extra_rich["normalized_facts"][-1]["role_profile"] = (
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
    )
    with pytest.raises(ERROR, match="ARTIFACT_CONTENT_OR_PREFIX_INVALID"):
        subject._validate_artifact_mapping_v1(
            extra_rich,
            predecessor_sources=sources[:-1],
            successor_sources=sources,
            reconciliation=reconciliation,
        )


def test_materialization_destination_is_exact() -> None:
    with pytest.raises(ERROR, match="ARTIFACT_DESTINATION_NOT_EXACT"):
        subject._validate_destination_v1(ROOT, ROOT / "unauthorized.json")

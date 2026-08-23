from __future__ import annotations

from collections import Counter
import copy
import csv
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1 as scaleup,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def product() -> dict[str, object]:
    artifacts = scaleup.build_artifacts_v1(repo_root=REPO_ROOT)
    return {
        "artifacts": artifacts,
        "census": list(csv.DictReader(io.StringIO(
            artifacts[scaleup.CENSUS].decode("utf-8")
        ))),
        "effective": json.loads(artifacts[scaleup.EFFECTIVE_N]),
        "summary": json.loads(artifacts[scaleup.SUMMARY]),
        "processing": json.loads(artifacts[scaleup.PROCESSING]),
        "queue": list(csv.DictReader(io.StringIO(
            artifacts[scaleup.QUEUE].decode("utf-8")
        ))),
    }


def test_independent_population_prefix_and_next500_oracles() -> None:
    canonical = json.loads((REPO_ROOT / scaleup.CANONICAL_RELATIVE).read_bytes())
    assert len(canonical["canonical_events"]) == 2387
    first = list(csv.DictReader((
        REPO_ROOT / "data/derived/covalent_small/"
        "covapie_bulk_500_new_event_scale_up_rehearsal_v1/"
        "covapie_bulk_500_new_event_cohort_v1.csv"
    ).open(newline="")))
    next_rows = list(csv.DictReader((
        REPO_ROOT / scaleup.OUTPUT_ROOT_RELATIVE / scaleup.COHORT
    ).open(newline="")))
    assert [int(row["scaleup_rank"]) for row in first] == list(range(1, 501))
    assert [int(row["scaleup_rank"]) for row in next_rows] == list(range(501, 1001))
    first_ids = [row["canonical_event_id"] for row in first]
    next_ids = [row["canonical_event_id"] for row in next_rows]
    assert len(set(next_ids)) == 500
    assert not set(first_ids) & set(next_ids)
    assert len(set(first_ids + next_ids)) == 1000
    assert 2360 == 1000 + 1360


def test_exact11_artifacts_and_no_network_replay_are_deterministic(
    product: dict[str, object],
) -> None:
    artifacts = product["artifacts"]
    assert tuple(artifacts) == scaleup.OUTPUT_FILENAMES
    assert len(scaleup.AUTHORIZED_PATHS) == 11
    for name, payload in artifacts.items():
        assert (REPO_ROOT / scaleup.OUTPUT_ROOT_RELATIVE / name).read_bytes() == payload
    replay = scaleup.replay_no_network_v1(repo_root=REPO_ROOT)
    assert replay["deterministic_no_network_replay_passed"] is True
    assert replay["network_performed"] is False


def test_global_authority_oracle_derives_all_current_lineages(
    product: dict[str, object],
) -> None:
    audit = product["summary"]["global_current_positive_authority_audit"]
    records = audit["records"]
    batch_count = len(list(csv.DictReader((REPO_ROOT / scaleup.BATCH13_INDEX).open())))
    current11_count = len(scaleup.mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1)
    k36_count = len(scaleup.mixed_tensorizer.K36_MEMBER_IDENTITIES_V1)
    approved_count = len(scaleup.APPROVED_EXPANSION_SAMPLE_FILES)
    human_count = sum(
        row["terminal_route"] == "HUMAN_RELEVANT_FINAL"
        for row in product["census"]
    )
    expected_runtime = batch_count + current11_count + k36_count
    expected_incomplete = approved_count + human_count
    counts = audit["counts"]
    assert audit["batch13_only_global_authority_assumption_removed"] is True
    assert counts["global_current_runtime_model_usable_sample_count"] == expected_runtime
    assert counts["global_current_runtime_model_usable_canonical_event_count"] == expected_runtime
    assert counts["global_current_positive_but_runtime_incomplete_count"] == expected_incomplete
    assert len(records) == expected_runtime + expected_incomplete
    assert len({row["sample_identity"] for row in records}) == len(records)
    assert len({row["canonical_event_id"] for row in records}) == len(records)
    assert all(row["authority_sources"] for row in records)
    assert all(row["canonical_event_id"].startswith("COVAPIE_CYS_SG_EVENT_V1:") for row in records)


def test_exact16_current11_k36_adjudication_is_explicit(
    product: dict[str, object],
) -> None:
    records = product["summary"]["global_current_positive_authority_audit"]["records"]
    exact16 = [row for row in records if row["lineage_id"].startswith("EXACT16_")]
    assert len(exact16) == (
        len(scaleup.mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1)
        + len(scaleup.mixed_tensorizer.K36_MEMBER_IDENTITIES_V1)
    )
    assert all(row["audit_status"] == "CURRENT_RUNTIME_MODEL_USABLE_CANONICAL_EVENT" for row in exact16)
    assert all(row["current_tensorizer_compatible"] for row in exact16)
    assert all(row["current_supervision_dataclass_compatible"] for row in exact16)
    assert all(row["current_model_input_available"] for row in exact16)
    current11 = [row for row in exact16 if "CURRENT11" in row["lineage_id"]]
    k36 = [row for row in exact16 if "K36" in row["lineage_id"]]
    assert Counter(row["formal_split"] for row in current11) == Counter({
        "train": 8, "validation": 2, "test": 1,
    })
    assert all(row["formal_split_authoritative"] is False for row in k36)
    assert all(row["formal_split"] == "" for row in k36)
    assert all(row["exclusion_reasons"] == [
        "CURRENT_FORMAL_LEAKAGE_SAFE_SPLIT_NOT_PUBLISHED"
    ] for row in k36)


def test_approved_expansion_is_positive_but_not_current_runtime_bound(
    product: dict[str, object],
) -> None:
    records = product["summary"]["global_current_positive_authority_audit"]["records"]
    approved = [
        row for row in records
        if row["lineage_id"] == "APPROVED_EXPANSION_EXACT3_SAMPLE_LINEAGE"
    ]
    assert {row["sample_identity"] for row in approved} == {
        identity for identity, _materialized, _tensorized
        in scaleup.APPROVED_EXPANSION_SAMPLE_FILES
    }
    assert all(row["positive_authority_exists"] for row in approved)
    assert all(row["role_label_authoritative"] for row in approved)
    assert all(row["current_runtime_model_usable"] is False for row in approved)
    assert all(row["current_supervision_dataclass_compatible"] is False for row in approved)
    assert all(row["exclusion_reasons"] for row in approved)


def test_five_human_relevant_rows_have_exact_evidence_based_status(
    product: dict[str, object],
) -> None:
    audit = product["summary"]["current_five_human_relevant_rows_adjudication"]
    assert audit["all_rows_adjudicated"] is True
    assert audit["event_count"] == 5
    statuses = Counter(row["audit_status"] for row in audit["records"])
    assert statuses == Counter({
        "PUBLISHED_POSITIVE_LABEL_RUNTIME_BINDING_INCOMPLETE": 4,
        "PUBLISHED_TASK_RELEVANCE_ONLY_EVENT_AUTHORITY_INCOMPLETE": 1,
    })
    task_only = next(
        row for row in audit["records"]
        if row["audit_status"]
        == "PUBLISHED_TASK_RELEVANCE_ONLY_EVENT_AUTHORITY_INCOMPLETE"
    )
    assert ":1BWC:" in task_only["canonical_event_id"]
    assert task_only["role_label_authoritative"] is False
    assert "EVENT_TRAINING_USE_DECISION_INCOMPLETE" in task_only["exclusion_reasons"]


def test_two_scope_effective_n_is_not_conflated(
    product: dict[str, object],
) -> None:
    effective = product["effective"]
    assert set(effective["scopes"]) == {
        "cumulative1000_ranked_new_scope",
        "global_current_runtime_authority_scope",
    }
    cumulative = effective["scopes"]["cumulative1000_ranked_new_scope"]
    global_scope = effective["scopes"]["global_current_runtime_authority_scope"]
    cumulative_pair = next(
        row for row in cumulative["actual_current_loss_heads"]
        if row["head_id"] == "covalent_pair_prediction"
    )
    global_pair = next(
        row for row in global_scope["actual_current_loss_heads"]
        if row["head_id"] == "covalent_pair_prediction"
    )
    assert cumulative_pair["raw_structural_label_available_count"] == 865
    assert cumulative_pair["authoritative_supervision_label_count"] == 17
    assert cumulative_pair["current_runtime_model_usable_count"] == 13
    assert cumulative_pair["formal_training_split_admitted_count"] == 5
    audit_counts = product["summary"]["global_current_positive_authority_audit"]["counts"]
    assert global_pair["current_runtime_model_usable_count"] == audit_counts[
        "global_current_runtime_model_usable_sample_count"
    ]
    assert global_pair["formal_training_split_admitted_count"] == audit_counts[
        "formal_training_split_admitted_positive_count"
    ]
    assert global_pair["current_runtime_model_usable_without_formal_split_count"] == 5
    assert effective["raw_label_N_distinguished_from_runtime_effective_N"] is True
    assert effective["runtime_effective_N_distinguished_from_formal_split_N"] is True


def test_exact_signature_chemistry_match_cannot_self_promote_runtime() -> None:
    state = scaleup.evaluate_runtime_authority_boundary_v1(
        chemistry_auto_admission_authorized=True,
        task_domain_positive_authority_source="EXISTING_EXACT_CHEMISTRY_AUTHORITY",
        role_label_authority_source="",
        runtime_role_materialization_source="",
        reactive_pair_label_authority_source="",
        POST_geometry_label_authority_source="",
        pair_raw_available=True,
        POST_raw_available=True,
        feature_compatible=True,
        formal_split_authoritative=False,
        formal_split="",
    )
    assert state["chemistry_auto_admission_authorized"] is True
    assert state["label_model_usable"] is False
    assert state["role_label_available"] is False
    assert state["training_split_admission_ready"] is False


def test_census_authority_and_partial_supervision_fail_closed(
    product: dict[str, object],
) -> None:
    census = product["census"]
    effective = product["effective"]
    positives = [row for row in census if row["label_model_usable"] == "true"]
    assert len(positives) == 13
    assert {row["formal_split_if_authoritative"] for row in positives} == {
        "train", "validation", "test"
    }
    assert all(row["role_label_authority_source"] for row in positives)
    assert all(row["reactive_pair_label_authority_source"] for row in positives)
    assert all(row["POST_geometry_label_authority_source"] for row in positives)
    assert all(row["experimental_PRE_available"] == "false" for row in positives)
    pre = next(
        row for row in effective["scopes"]["cumulative1000_ranked_new_scope"]
        ["geometry_component_breakdown"]
        if row["target_id"] == "PRE_geometry_component"
    )
    assert pre["authoritative_supervision_label_count"] == 0
    assert effective["partial_label_loss_mask_policy_preserved"] is True


def test_no_fuzzy_or_shadow_positive_promotion(product: dict[str, object]) -> None:
    census = product["census"]
    shadows = [row for row in census if row["shadow_exact_component_reuse_candidate"] == "true"]
    assert len(shadows) == 2
    assert all(row["label_model_usable"] == "false" for row in shadows)
    assert all(not row["positive_authority_source"] for row in shadows)
    summary = product["summary"]
    assert summary["safety"]["cross_signature_positive_propagation_performed"] is False
    assert summary["safety"]["human_decision_fuzzy_propagation_performed"] is False
    assert summary["safety"]["new_reaction_family_authority_created"] is False


def test_network_modes_and_authority_drift_fail_closed() -> None:
    with pytest.raises(scaleup.ScaleupSafetyError, match="NOT_AUTHORIZED"):
        scaleup.run_v1(
            repo_root=REPO_ROOT, mode=scaleup.CONTROLLED_NETWORK_EXECUTION,
            network_authorized=False,
        )
    with pytest.raises(scaleup.ScaleupSafetyError, match="INVALID_IN_REPLAY"):
        scaleup.run_v1(
            repo_root=REPO_ROOT, mode=scaleup.REPLAY_NO_NETWORK,
            network_authorized=True,
        )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("role_label_available", "false", "HARD_INPUT_OR_AUTHORITY"),
        ("runtime_role_materialization_available", "false", "HARD_INPUT_OR_AUTHORITY"),
        ("reactive_pair_label_authoritative", "false", "HARD_INPUT_OR_AUTHORITY"),
        ("POST_geometry_label_authoritative", "false", "HARD_INPUT_OR_AUTHORITY"),
        ("feature_status", "FAILED_CLOSED", "HARD_INPUT_OR_AUTHORITY"),
        ("task_domain_authority_status", "AUTHORITATIVE_NEGATIVE_EXACT_EVENT", "HARD_INPUT_OR_AUTHORITY"),
        ("shadow_exact_component_reuse_candidate", "true", "SHADOW_CANDIDATE"),
        ("derived_PRE_available", "true", "PRE_GEOMETRY_FABRICATED"),
        ("warhead_type_target_available", "true", "FAMILY_CLASS"),
        ("reaction_family_target_available", "true", "FAMILY_CLASS"),
    ),
)
def test_census_negative_authority_mutations_fail_closed(
    product: dict[str, object], field: str, value: str, reason: str,
) -> None:
    census = copy.deepcopy(product["census"])
    target = next(row for row in census if row["label_model_usable"] == "true")
    target[field] = value
    with pytest.raises(scaleup.ScaleupSafetyError, match=reason):
        scaleup.validate_census_rows_v1(census)


@pytest.mark.parametrize(
    ("available_field", "source_field", "reason"),
    (
        ("role_label_available", "role_label_authority_source", "ROLE_LABEL_SELF_CERTIFICATION"),
        ("reactive_pair_label_authoritative", "reactive_pair_label_authority_source", "PAIR_AUTHORITY_SELF_CERTIFICATION"),
        ("POST_geometry_label_authoritative", "POST_geometry_label_authority_source", "POST_AUTHORITY_SELF_CERTIFICATION"),
    ),
)
def test_label_authority_cannot_self_certify(
    product: dict[str, object], available_field: str, source_field: str, reason: str,
) -> None:
    census = copy.deepcopy(product["census"])
    target = next(
        row for row in census
        if row[available_field] == "true" and row["label_model_usable"] == "false"
    )
    target[source_field] = ""
    with pytest.raises(scaleup.ScaleupSafetyError, match=reason):
        scaleup.validate_census_rows_v1(census)


def test_new_component_cannot_be_called_train_without_formal_split(
    product: dict[str, object],
) -> None:
    census = copy.deepcopy(product["census"])
    target = next(row for row in census if not row["formal_split_if_authoritative"])
    target["training_split_admission_ready"] = "true"
    with pytest.raises(scaleup.ScaleupSafetyError, match="WITHOUT_FORMAL_SPLIT"):
        scaleup.validate_census_rows_v1(census)


def test_terminal_processing_and_review_queue_reconcile(
    product: dict[str, object],
) -> None:
    processing = product["processing"]
    queue = product["queue"]
    census = product["census"]
    assert processing["terminal_outcome_count"] == 500
    assert len(processing["events"]) == 500
    assert len({row["canonical_event_id"] for row in processing["events"]}) == 500
    queued_ids = {
        event_id for row in queue
        for event_id in json.loads(row["canonical_event_ids_json"])
    }
    unresolved = {
        row["canonical_event_id"] for row in census
        if row["terminal_route"] in {
            "HUMAN_REVIEW_REQUIRED", "HUMAN_REVIEW_REQUIRED_DEFERRED",
            "HUMAN_REVIEW_REQUIRED_GATE_INVALID",
        }
    }
    assert queued_ids == unresolved
    assert all(row["human_decision_created"] == "false" for row in queue)


def _synthetic_published_observation() -> dict[str, object]:
    return {
        "branch": "main", "HEAD": "f" * 40,
        "HEAD_parent": scaleup.BASELINE_HEAD,
        "head_parent_ids": [scaleup.BASELINE_HEAD],
        "HEAD_tree": "e" * 40,
        "HEAD_subject": scaleup.PUBLICATION_SUBJECT,
        "head_changed_entries": [
            {"status": "A", "path": path}
            for path in sorted(scaleup.AUTHORIZED_PATHS)
        ],
        "head_candidate_path_modes": {
            path: "100644" for path in scaleup.AUTHORIZED_PATHS
        },
        "origin_main": "f" * 40, "ahead_behind": "0\t0",
        "tracked_changes": [], "staged_changes": [], "untracked": [],
    }


def test_real_repository_profile_is_exact_candidate_or_real_successor() -> None:
    observation = scaleup.observe_repository_state_v1(REPO_ROOT)
    profile = scaleup.classify_repository_profile_v1(observation)
    if profile == "candidate_precommit_untracked":
        assert observation["HEAD"] == scaleup.BASELINE_HEAD
        assert set(observation["untracked"]) == set(scaleup.AUTHORIZED_PATHS)
        assert len(observation["untracked"]) == 11
    else:
        assert profile == "published_successor"
        assert observation["HEAD"] == observation["origin_main"]
        assert observation["head_parent_ids"] == [scaleup.BASELINE_HEAD]
        assert observation["head_candidate_path_modes"] == {
            path: "100644" for path in scaleup.AUTHORIZED_PATHS
        }


def test_candidate_profile_rejects_empty_untracked() -> None:
    observation = scaleup.observe_repository_state_v1(REPO_ROOT)
    if observation["HEAD"] != scaleup.BASELINE_HEAD:
        pytest.skip("real repository is already the published successor")
    observation["untracked"] = []
    with pytest.raises(scaleup.ScaleupSafetyError, match="PROFILE_MISMATCH"):
        scaleup.classify_repository_profile_v1(observation)


def test_published_successor_positive_profile_requires_exact11_a100644() -> None:
    assert scaleup.classify_repository_profile_v1(
        _synthetic_published_observation()
    ) == "published_successor"


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_parent", "wrong_subject", "extra_path", "missing_path",
        "modified_path", "executable_mode", "extra_untracked", "two_parents",
        "head_origin_mismatch", "ahead_behind_mismatch",
    ),
)
def test_published_successor_negative_profiles_fail_closed(mutation: str) -> None:
    observation = _synthetic_published_observation()
    entries = observation["head_changed_entries"]
    modes = observation["head_candidate_path_modes"]
    if mutation == "wrong_parent":
        observation["HEAD_parent"] = "1" * 40
        observation["head_parent_ids"] = ["1" * 40]
    elif mutation == "wrong_subject":
        observation["HEAD_subject"] = "wrong"
    elif mutation == "extra_path":
        entries.append({"status": "A", "path": "extra.txt"})
    elif mutation == "missing_path":
        removed = entries.pop()["path"]
        modes.pop(removed)
    elif mutation == "modified_path":
        entries[0]["status"] = "M"
    elif mutation == "executable_mode":
        python_path = next(path for path in modes if path.endswith(".py"))
        modes[python_path] = "100755"
    elif mutation == "extra_untracked":
        observation["untracked"] = ["extra.txt"]
    elif mutation == "two_parents":
        observation["HEAD_parent"] = ""
        observation["head_parent_ids"] = [scaleup.BASELINE_HEAD, "2" * 40]
    elif mutation == "head_origin_mismatch":
        observation["origin_main"] = "3" * 40
    elif mutation == "ahead_behind_mismatch":
        observation["ahead_behind"] = "1\t0"
    with pytest.raises(scaleup.ScaleupSafetyError, match="PROFILE_MISMATCH"):
        scaleup.classify_repository_profile_v1(observation)

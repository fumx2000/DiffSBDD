from __future__ import annotations

import ast
import copy
import csv
from dataclasses import replace
import hashlib
import inspect
import io
import json
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1
    as subject,
)
from scripts import (
    check_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1
    as checker,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPOSITORY_ROOT / checker.AUTHORIZED_CANDIDATE_FILES_V1[0]


@pytest.fixture(scope="module")
def computation():
    return subject.compute_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1()


@pytest.fixture(scope="module")
def artifacts():
    return subject.build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1()


def _replace_recovery_row(computation, index: int, **changes):
    rows = [dict(row) for row in computation.recovery_evidence_rows]
    rows[index].update(changes)
    return replace(computation, recovery_evidence_rows=tuple(rows))


def _replace_component(computation, **changes):
    components = [copy.deepcopy(dict(item)) for item in computation.recovered_components]
    components[0].update(changes)
    return replace(computation, recovered_components=tuple(components))


def _replace_event_row(computation, event_id: str, **changes):
    rows = []
    for row in computation.event_rows:
        value = dict(row)
        if value["canonical_event_id"] == event_id:
            value.update(changes)
        rows.append(value)
    return replace(computation, event_rows=tuple(rows))


def test_exact_target_readiness_and_pre_recovery_blocker(computation) -> None:
    assert computation.target_event_ids == tuple(sorted((
        "COVAPIE_CYS_SG_EVENT_V1:3B9H:A:CYS:146-:SG:D:NDU:C6",
        "COVAPIE_CYS_SG_EVENT_V1:3BHL:A:CYS:146-:SG:C:NDU:C6",
        "COVAPIE_CYS_SG_EVENT_V1:3BHL:B:CYS:146-:SG:G:NDU:C6",
        "COVAPIE_CYS_SG_EVENT_V1:3BHR:A:CYS:146-:SG:E:NDU:C6",
    )))
    assert computation.target_pdb_ligand_identities == (
        "3B9H/NDU", "3BHL/NDU", "3BHR/NDU",
    )
    assert computation.pre_recovery_blocker == "LEAKAGE_EVIDENCE_INCOMPLETE"
    assert computation.leakage_gap_root_cause == subject.ROOT_CAUSE_V1


def test_field_level_recovery_matrix_and_bound_cache_authority(computation) -> None:
    rows = computation.recovery_evidence_rows
    assert len(rows) == 15
    assert {
        row["evidence_axis"] for row in rows
    } == set(subject._CANONICAL_AXES_V1)
    assert all(row["used_for_component_linking"] == "true" for row in rows)
    sequence_rows = [
        row for row in rows
        if row["evidence_axis"] == "PROTEIN_SEQUENCE_IDENTITY_GE_0.5"
    ]
    assert len(sequence_rows) == 3
    assert all(row["pre_recovery_availability"] == "false" for row in sequence_rows)
    assert all(row["failure_reason"] == subject.ROOT_CAUSE_V1 for row in sequence_rows)
    assert {
        row["recovery_source_sha256"] for row in sequence_rows
    } == {
        "f907ac342928ec24708516f793f8306401521e6fa5a6b2d893160e65a734c31f",
        "9fd80c44497a6737d83c6f12150cb608e933d1823ca9c58a1e8013c1ceca5b7a",
        "b084d30d981db2fe4a630d1d4832d30a84f1b3752f994ffafa29703b9efb4c89",
    }
    assert {
        row["recovered_value"] for row in sequence_rows
    } == {
        "CANONICAL_SEQUENCE_SHA256:"
        "ca530340b80f99c2e9a083fdc60f66eefcced0e6dfc0bd5cefb8d5d6453c1162"
    }


def test_exact_527_context_and_complete_component_closure(computation) -> None:
    assert computation.context_counts == {
        "historical_frozen_outcome_count": 250,
        "known_control_outcome_count": 27,
        "incremental_attempt_outcome_count": 250,
        "full_predictor_population_count": 527,
        "frozen_reference_record_count": 14,
        "frozen_leakage_group_count": 7,
        "frozen_historical_group_count": 5,
        "frozen_cumulative_group_count": 2,
    }
    assert len(computation.recovered_components) == 1
    component = computation.recovered_components[0]
    assert component["classification"] == "HISTORICAL_BASELINE_COMPONENT"
    assert component["leakage_key"] == "COVAPIE_LEAKAGE_GROUP_000005"
    assert component["read_only_group_id"] == "COVAPIE_LEAKAGE_GROUP_000005"
    assert component["formal_group_id"] == "COVAPIE_LEAKAGE_GROUP_000005"
    assert component["read_only_split"] == component["formal_split"] == "test"
    assert component["group_existed_pre_recovery"] is True
    assert component["full_identity_count"] == 9
    assert component["full_event_count"] == 33
    assert component["batch001_target_event_count"] == 4
    assert component["non_target_component_event_count"] == 29
    assert component["full_member_pdb_ligand_identities"] == [
        "1B02/UFP", "1F28/UMP", "1JU6/UMP", "1JUJ/UMP", "2AAZ/UMP",
        "2BBQ/UMP", "3B9H/NDU", "3BHL/NDU", "3BHR/NDU",
    ]
    assert component["linking_axes"] == list(subject._CANONICAL_AXES_V1)
    assert component["cross_split_leakage_status"] == "PASSED_ZERO_VIOLATIONS"
    assert component["non_target_members_are_training_samples"] is False
    assert component["non_target_members_inherit_split_reservation_only"] is True


def test_independent_spanning_tree_proves_full_closure_without_name_grouping(computation) -> None:
    component = computation.recovered_components[0]
    events = set(component["full_member_canonical_event_ids"])
    parent = {event: event for event in events}

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    ndu_to_non_target = []
    for edge in component["connectivity_spanning_edges"]:
        left, right = edge["left_event_id"], edge["right_event_id"]
        assert left in events and right in events and edge["linking_axes"]
        left_root, right_root = find(left), find(right)
        assert left_root != right_root
        parent[right_root] = left_root
        if ("NDU" in left) != ("NDU" in right):
            ndu_to_non_target.append(edge)
    assert len({find(event) for event in events}) == 1
    assert ndu_to_non_target
    assert any(
        set(edge["linking_axes"])
        & {"PROTEIN_ACCESSION", "PROTEIN_EXACT_SEQUENCE", "PROTEIN_SEQUENCE_IDENTITY_GE_0.5"}
        for edge in ndu_to_non_target
    )
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert 'ligand_component_id"] == "NDU"' not in source
    assert "apply_leakage_predictions_read_only_v1" in source
    assert "_independent_complete_components_v1" in source


def test_frozen_group_inheritance_oracle_and_zero_cross_split_leakage(computation) -> None:
    oracle = computation.formal_split_oracle
    expected = [[
        "COVAPIE_LEAKAGE_GROUP_000005",
        "COVAPIE_LEAKAGE_GROUP_000005",
        "test",
    ]]
    assert oracle["mode"] == "INDEPENDENT_EXISTING_FROZEN_GROUP_INHERITANCE_ORACLE"
    assert oracle["candidate_assignment_count"] == 1
    assert oracle["policy_enumeration_required"] is False
    assert oracle["selected_assignment"] == expected
    assert oracle["independent_selected_assignment"] == expected
    assert oracle["production_owner_independent_oracle_parity"] is True
    assert computation.cross_split_leakage_violations == ()


def test_complete_13_event_successor_preserves_existing_rows_and_training_boundary(
    computation,
) -> None:
    assert len(computation.event_rows) == 13
    by_id = {row["canonical_event_id"]: row for row in computation.event_rows}
    assert all(
        by_id[event_id]["leakage_evidence_complete"] == "true"
        and by_id[event_id]["leakage_classification"] == "HISTORICAL_BASELINE_COMPONENT"
        and by_id[event_id]["formal_leakage_group_id"]
        == "COVAPIE_LEAKAGE_GROUP_000005"
        and by_id[event_id]["assigned_split"] == "test"
        and by_id[event_id]["split_admission_authoritative"] == "true"
        for event_id in computation.target_event_ids
    )
    assert all(row["sample_training_admitted"] == "false" for row in computation.event_rows)
    assert all(
        row["model_training_activation_authorized"] == "false"
        for row in computation.event_rows
    )
    assert computation.sample_training_admitted_count == 0
    assert computation.model_training_activation_authorized_count == 0
    assert computation.new_human_review_required_count == 0
    assert subject.validate_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
        computation
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "target_missing",
        "recovered_value_changed",
        "wrong_evidence_source_sha",
        "incomplete_527_context",
        "duplicate_event_identity",
        "component_omits_non_target",
        "component_manually_split",
        "existing_published_split_changed",
        "cross_split_component",
        "oracle_parity_missing",
        "training_admitted_true",
        "training_activation_true",
    ),
)
def test_required_negative_mutations_fail_closed(computation, mutation) -> None:
    candidate = computation
    if mutation == "target_missing":
        candidate = replace(candidate, target_event_ids=candidate.target_event_ids[:-1])
    elif mutation == "recovered_value_changed":
        candidate = _replace_recovery_row(candidate, 0, recovered_value="changed")
    elif mutation == "wrong_evidence_source_sha":
        candidate = _replace_recovery_row(
            candidate, 0, recovery_source_sha256="0" * 64,
        )
    elif mutation == "incomplete_527_context":
        counts = dict(candidate.context_counts)
        counts["full_predictor_population_count"] = 526
        candidate = replace(candidate, context_counts=counts)
    elif mutation == "duplicate_event_identity":
        component = copy.deepcopy(dict(candidate.recovered_components[0]))
        component["full_member_canonical_event_ids"].append(
            component["full_member_canonical_event_ids"][0]
        )
        candidate = replace(candidate, recovered_components=(component,))
    elif mutation == "component_omits_non_target":
        component = copy.deepcopy(dict(candidate.recovered_components[0]))
        omitted = component["non_target_component_event_ids"].pop()
        component["full_member_canonical_event_ids"].remove(omitted)
        component["full_event_count"] -= 1
        component["non_target_component_event_count"] -= 1
        candidate = replace(candidate, recovered_components=(component,))
    elif mutation == "component_manually_split":
        candidate = _replace_component(candidate, formal_group_id="MANUAL_GROUP")
    elif mutation == "existing_published_split_changed":
        event_id = candidate.published_existing_event_rows[0]["canonical_event_id"]
        candidate = _replace_event_row(candidate, event_id, assigned_split="test")
    elif mutation == "cross_split_component":
        candidate = replace(candidate, cross_split_leakage_violations=({"bad": True},))
    elif mutation == "oracle_parity_missing":
        oracle = dict(candidate.formal_split_oracle)
        oracle["production_owner_independent_oracle_parity"] = False
        candidate = replace(candidate, formal_split_oracle=oracle)
    elif mutation == "training_admitted_true":
        candidate = _replace_event_row(
            candidate, candidate.target_event_ids[0], sample_training_admitted="true",
        )
    elif mutation == "training_activation_true":
        candidate = _replace_event_row(
            candidate, candidate.target_event_ids[0],
            model_training_activation_authorized="true",
        )
    with pytest.raises(ValueError) as captured:
        subject.validate_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
            candidate
        )
    assert str(captured.value).startswith(subject.BATCH001_NDU4_LEAKAGE_RECOVERY_ERROR_V1)


def test_artifacts_are_deterministic_bound_and_audit_friendly(artifacts) -> None:
    repeated = subject.build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1()
    assert artifacts == repeated
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES_V1
    manifest = json.loads(artifacts[subject.MANIFEST_V1])
    assert manifest["recovery_success"] is True
    assert manifest["cross_split_leakage_violation_count"] == 0
    assert manifest["population_counts"] == {
        "batch001_positive_event_count": 13,
        "existing_authoritative_event_count": 9,
        "newly_authoritative_ndu_event_count": 4,
        "successor_split_authoritative_event_count": 13,
        "sample_training_admitted_count": 0,
        "model_training_activation_authorized_count": 0,
        "new_human_review_required_count": 0,
    }
    assert manifest["ndu_formal_splits"] == ["test"]
    assert subject.MANIFEST_V1 not in manifest["artifact_bindings"]
    for name, binding in manifest["artifact_bindings"].items():
        assert binding["sha256"] == hashlib.sha256(artifacts[name]).hexdigest()
    evidence = list(csv.DictReader(io.StringIO(
        artifacts[subject.RECOVERY_EVIDENCE_V1].decode("utf-8")
    )))
    assert len(evidence) == 15


def _candidate_snapshot() -> checker.RepositoryGitSnapshotV1:
    return checker.collect_repository_git_snapshot_v1(repository_root=REPOSITORY_ROOT)


def _valid_successor_snapshot() -> checker.RepositoryGitSnapshotV1:
    current = _candidate_snapshot()
    successor = "1" * 40
    return replace(
        current,
        head=successor,
        origin_main=successor,
        status_entries=(),
        head_parent_ids=(checker.EXPECTED_BASELINE_HEAD_V1,),
        head_subject=checker.PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="2" * 40,
        head_changed_entries=tuple(
            ("A", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644") for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def test_real_repository_dual_profile_and_valid_published_successor_simulation() -> None:
    snapshot = checker.collect_repository_git_snapshot_v1(
        repository_root=REPOSITORY_ROOT,
    )
    profile = checker.classify_repository_snapshot_v1(snapshot)
    assert profile in {
        checker.CANDIDATE_PRECOMMIT_PROFILE_V1,
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1,
    }
    if profile == checker.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert snapshot.branch == "main"
        assert snapshot.head == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.origin_main == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.ahead_behind == (0, 0)
        assert snapshot.tracked_modified_paths == ()
        assert snapshot.staged_modified_paths == ()
        assert tuple(sorted(snapshot.status_entries)) == tuple(sorted(
            ("??", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_PARENT_V1,)
        assert snapshot.head_subject == checker.EXPECTED_BASELINE_SUBJECT_V1
        assert snapshot.head_tree == checker.EXPECTED_BASELINE_TREE_V1
        assert snapshot.head_candidate_path_modes == ()
    else:
        assert snapshot.branch == "main"
        assert snapshot.head == snapshot.origin_main
        assert snapshot.head != checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.ahead_behind == (0, 0)
        assert snapshot.tracked_modified_paths == ()
        assert snapshot.staged_modified_paths == ()
        assert snapshot.status_entries == ()
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_HEAD_V1,)
        assert snapshot.head_subject == checker.PUBLISHED_SUCCESSOR_SUBJECT_V1
        assert tuple(sorted(snapshot.head_changed_entries)) == tuple(sorted(
            ("A", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
        assert tuple(sorted(snapshot.head_candidate_path_modes)) == tuple(sorted(
            (path, "100644") for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
    assert checker.classify_repository_snapshot_v1(_valid_successor_snapshot()) == (
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_parent", "wrong_subject", "extra_path", "missing_artifact",
        "wrong_change_type", "python_100755", "extra_untracked",
    ),
)
def test_invalid_published_successor_profiles_fail_closed(mutation) -> None:
    value = _valid_successor_snapshot()
    if mutation == "wrong_parent":
        value = replace(value, head_parent_ids=("3" * 40,))
    elif mutation == "wrong_subject":
        value = replace(value, head_subject="wrong")
    elif mutation == "extra_path":
        value = replace(
            value, head_changed_entries=value.head_changed_entries + (("A", "extra"),),
        )
    elif mutation == "missing_artifact":
        value = replace(
            value,
            head_changed_entries=value.head_changed_entries[:-1],
            head_candidate_path_modes=value.head_candidate_path_modes[:-1],
        )
    elif mutation == "wrong_change_type":
        value = replace(
            value,
            head_changed_entries=(
                ("M", checker.AUTHORIZED_CANDIDATE_FILES_V1[0]),
                *value.head_changed_entries[1:],
            ),
        )
    elif mutation == "python_100755":
        value = replace(
            value,
            head_candidate_path_modes=(
                (checker.AUTHORIZED_CANDIDATE_FILES_V1[0], "100755"),
                *value.head_candidate_path_modes[1:],
            ),
        )
    elif mutation == "extra_untracked":
        value = replace(value, status_entries=(("??", "extra"),))
    with pytest.raises(ValueError) as captured:
        checker.classify_repository_snapshot_v1(value)
    assert str(captured.value) == checker.CHECKER_ERROR_V1


def test_candidate_extra_untracked_and_tracked_modification_fail_closed() -> None:
    value = _candidate_snapshot()
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(value, status_entries=value.status_entries + (("??", "extra"),))
        )
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(value, tracked_modified_paths=("existing.py",))
        )


def test_source_boundary_and_checker_markers_are_static() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not ({"requests", "urllib", "torch", "pytorch_lightning"} & imports)
    source = inspect.getsource(checker.main)
    markers = (
        "ndu4_leakage_recovery_built",
        "ndu4_target_event_count",
        "ndu4_unique_pdb_ligand_identity_count",
        "ndu4_leakage_gap_root_cause",
        "controlled_leakage_context_event_count",
        "canonical_read_only_predictor_reused",
        "ndu4_recovered_component_count",
        "ndu4_full_component_identity_count",
        "ndu4_full_component_event_count",
        "ndu4_component_classification",
        "ndu4_formal_group_id",
        "ndu4_formal_split",
        "formal_split_policy_oracle_parity",
        "cross_split_leakage_violation_count",
        "deterministic_artifact_bytes",
        "candidate_precommit_profile_passed",
        "published_successor_profile_simulation_passed",
        "full_training_authorized",
        "ready_for_gpt_review",
    )
    assert all(marker in source for marker in markers)

from __future__ import annotations

from dataclasses import replace
import csv
import io
import json

import pytest

from covalent_ext import covapie_batch001_formal_split_leakage_admission_v1 as subject


@pytest.fixture(scope="module")
def computation():
    return subject.compute_covapie_batch001_formal_split_admission_v1()


@pytest.fixture(scope="module")
def artifacts():
    return subject.build_covapie_batch001_formal_split_admission_artifacts_v1()


def _replace_component(computation, component_name: str, **changes):
    components = tuple(
        replace(item, **changes) if item.component_name == component_name else item
        for item in computation.components
    )
    return replace(computation, components=components)


def _replace_event_row(computation, event_id: str, **changes):
    rows = tuple(
        {**row, **changes} if row["canonical_event_id"] == event_id else row
        for row in computation.event_rows
    )
    return replace(computation, event_rows=rows)


def test_exact_527_context_read_only_reproduction_and_source_bindings(computation) -> None:
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
    assert computation.read_only_prediction_reproduced_exactly is True
    assert computation.read_only_prediction_is_authority is False
    assert computation.read_only_prediction_copied_as_authority is False
    assert len(computation.source_bindings) == 30
    assert all(row["sha256_verified"] is True for row in computation.source_bindings)
    assert all(
        row["actual_sha256"] == row["expected_sha256"]
        for row in computation.source_bindings
    )


def test_exact_component_keys_memberships_and_non_target_boundary(computation) -> None:
    components = {item.component_name: item for item in computation.components}
    assert {
        name: item.leakage_key for name, item in components.items()
    } == {
        name: expected["leakage_key"]
        for name, expected in subject._EXPECTED_COMPONENTS_V1.items()
    }
    assert {name: len(item.full_member_canonical_event_ids) for name, item in components.items()} == {
        "DJK": 11, "LN5": 2, "PX5": 2, "PTG": 15,
    }
    assert {name: len(item.full_member_pdb_ligand_identities) for name, item in components.items()} == {
        "DJK": 5, "LN5": 1, "PX5": 1, "PTG": 9,
    }
    assert {name: len(item.batch001_target_event_ids) for name, item in components.items()} == {
        "DJK": 2, "LN5": 2, "PX5": 2, "PTG": 3,
    }
    assert {name: len(item.non_target_component_event_ids) for name, item in components.items()} == {
        "DJK": 9, "LN5": 0, "PX5": 0, "PTG": 12,
    }
    assert all(item.classification == "NEW_EXPANSION_COMPONENT" for item in components.values())
    assert all(item.linking_axes for item in components.values())


def test_formal_joint_divergence_is_accepted_with_group_parity(computation) -> None:
    observed = {
        item.component_name: (
            item.read_only_group_id,
            item.formal_group_id,
            item.read_only_split,
            item.formal_split,
            item.group_parity,
            item.split_parity,
        )
        for item in computation.components
    }
    assert observed == {
        "DJK": (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
            "train", "train", True, True,
        ),
        "LN5": (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95",
            "train", "validation", True, False,
        ),
        "PX5": (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
            "train", "validation", True, False,
        ),
        "PTG": (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
            "validation", "train", True, False,
        ),
    }
    assert subject.validate_covapie_batch001_formal_split_admission_v1(computation)


def test_independent_81_assignment_oracle_and_owner_parity(computation) -> None:
    oracle = computation.oracle
    assert oracle.candidate_assignment_count == 81
    assert oracle.valid_assignment_count == 46
    assert oracle.selected_full_signature == (2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 2)
    assert oracle.selected_sample_counts == (23, 4, 3)
    assert oracle.selected_group_counts == (5, 4, 2)
    assert oracle.selected_objective_fractions == ("4", "2", "27/5")
    assert oracle.best_pre_signature_objective == ("4", "2", "27/5")
    assert oracle.tie_count_before_signature == 3
    assert oracle.lexicographic_minimum_tie_break_applied is True
    assert computation.formal_owner_independent_oracle_parity is True
    assert computation.owner_assignment == oracle.selected_assignment


def test_input_order_frozen_groups_and_cross_component_integrity(computation) -> None:
    assert computation.formal_assignment_mode == "JOINT_ALL_FOUR_COMPONENTS"
    assert computation.input_order_case_count == 6
    assert computation.input_order_independence_verified is True
    assert len(computation.existing_groups_before) == 7
    assert computation.existing_groups_before == computation.existing_groups_after
    assert computation.cross_split_leakage_violations == ()
    assert computation.randomization_used is False
    assert computation.random_seed_used is False
    assert computation.manual_split_override is False


def test_exact_event_authority_counts_and_ndu_fail_closed(computation) -> None:
    rows = computation.event_rows
    admitted = [row for row in rows if row["split_admission_authoritative"] == "true"]
    ndu = [row for row in rows if row["ligand_component_id"] == "NDU"]
    assert len(rows) == 13
    assert len(admitted) == 9
    assert sum(row["assigned_split"] == "train" for row in admitted) == 5
    assert sum(row["assigned_split"] == "validation" for row in admitted) == 4
    assert not any(row["assigned_split"] == "test" for row in admitted)
    assert len(ndu) == 4
    for row in ndu:
        assert row["leakage_evidence_complete"] == "false"
        assert row["leakage_key"] == ""
        assert row["formal_leakage_group_id"] == ""
        assert row["assigned_split"] == ""
        assert row["split_admission_authoritative"] == "false"
        assert row["split_admission_status"] == "UNRESOLVED_FAIL_CLOSED"
        assert row["split_admission_reason"] == "LEAKAGE_EVIDENCE_INCOMPLETE"
    assert all(row["sample_training_admitted"] == "false" for row in rows)
    assert all(row["model_training_activation_authorized"] == "false" for row in rows)


def test_copying_read_only_split_directly_as_authority_is_rejected(computation) -> None:
    changed = _replace_component(computation, "LN5", formal_split="train", split_parity=True)
    with pytest.raises(ValueError, match="FORMAL_COMPONENT_CONTRACT_INVALID:LN5"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_sequential_formal_assignment_is_rejected(computation) -> None:
    changed = replace(computation, formal_assignment_mode="SEQUENTIAL_ONE_COMPONENT_AT_A_TIME")
    with pytest.raises(ValueError, match="FORMAL_VS_READ_ONLY_AUTHORITY_SEMANTICS_INVALID"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_formal_group_mismatch_is_rejected(computation) -> None:
    changed = _replace_component(computation, "DJK", formal_group_id="COVAPIE_EXPANSION_LEAKAGE_GROUP_BAD")
    with pytest.raises(ValueError, match="FORMAL_COMPONENT_CONTRACT_INVALID:DJK"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_formal_owner_oracle_mismatch_is_rejected(computation) -> None:
    changed = replace(computation, formal_owner_independent_oracle_parity=False)
    with pytest.raises(ValueError, match="FORMAL_OWNER_INDEPENDENT_ORACLE_MISMATCH"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_non_lexicographic_tied_winner_is_rejected(computation) -> None:
    changed_oracle = replace(
        computation.oracle,
        selected_full_signature=(2, 0, 0, 1, 0, 1, 0, 1, 1, 0, 2),
        lexicographic_minimum_tie_break_applied=False,
    )
    changed = replace(computation, oracle=changed_oracle)
    with pytest.raises(ValueError, match="INDEPENDENT_EXHAUSTIVE_ORACLE_CONTRACT_INVALID"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


@pytest.mark.parametrize("mutation", ("split", "member"))
def test_existing_frozen_group_mutation_is_rejected(computation, mutation) -> None:
    after = [dict(item) for item in computation.existing_groups_after]
    if mutation == "split":
        after[0]["assigned_split"] = "train" if after[0]["assigned_split"] != "train" else "test"
    else:
        after[0]["member_identities"] = after[0]["member_identities"][:-1]
        after[0]["member_count"] -= 1
    changed = replace(computation, existing_groups_after=tuple(after))
    with pytest.raises(ValueError, match="EXISTING_FROZEN_GROUP_MUTATION_DETECTED"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


@pytest.mark.parametrize("mutation", ("omit", "inject"))
def test_full_component_omission_or_injection_is_rejected(computation, mutation) -> None:
    djk = next(item for item in computation.components if item.component_name == "DJK")
    events = djk.full_member_canonical_event_ids
    changed_events = events[:-1] if mutation == "omit" else (*events, "COVAPIE_CYS_SG_EVENT_V1:FAKE")
    changed = _replace_component(
        computation, "DJK", full_member_canonical_event_ids=changed_events,
    )
    with pytest.raises(ValueError, match="FORMAL_COMPONENT_CONTRACT_INVALID:DJK"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_cross_group_must_link_edge_is_rejected(computation) -> None:
    changed = replace(computation, cross_split_leakage_violations=({
        "left": "A", "right": "B", "left_group": "G1", "right_group": "G2",
        "left_split": "train", "right_split": "validation", "linking_axes": ["LIGAND_GRAPH"],
    },))
    with pytest.raises(ValueError, match="CROSS_GROUP_MUST_LINK_EDGE_DETECTED"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_same_formal_group_assigned_two_splits_is_rejected(computation) -> None:
    djk_group = next(item.formal_group_id for item in computation.components if item.component_name == "DJK")
    changed = _replace_component(computation, "LN5", formal_group_id=djk_group)
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


@pytest.mark.parametrize(
    "changes",
    (
        {"formal_leakage_group_id": "COVAPIE_EXPANSION_LEAKAGE_GROUP_BAD"},
        {"assigned_split": "train"},
        {"split_admission_authoritative": "true"},
        {"model_training_activation_authorized": "true"},
    ),
)
def test_ndu_assignment_or_model_activation_is_rejected(computation, changes) -> None:
    event_id = subject._EXPECTED_NDU_EVENT_IDS_V1[0]
    changed = _replace_event_row(computation, event_id, **changes)
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_admitted_event_model_training_activation_is_rejected(computation) -> None:
    event_id = subject._EXPECTED_COMPONENTS_V1["DJK"]["target_event_ids"][0]
    changed = _replace_event_row(
        computation, event_id, model_training_activation_authorized="true",
    )
    with pytest.raises(ValueError, match="MODEL_ACTIVATION_OR_READ_ONLY_AUTHORITY_VIOLATION"):
        subject.validate_covapie_batch001_formal_split_admission_v1(changed)


def test_wrong_attempt_and_bridge_sha_are_rejected() -> None:
    repo = subject._DEFAULT_REPOSITORY_ROOT
    attempt = repo.parent / subject._ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1
    bridge = repo / subject._BRIDGE_READINESS
    with pytest.raises(subject._AdmissionInvariantError, match="ATTEMPT_TEST_SHA256_MISMATCH"):
        subject._verify_file_sha_v1(attempt, "0" * 64, "ATTEMPT_TEST")
    with pytest.raises(subject._AdmissionInvariantError, match="BRIDGE_TEST_SHA256_MISMATCH"):
        subject._verify_file_sha_v1(bridge, "0" * 64, "BRIDGE_TEST")


def test_wrong_full_context_count_and_input_order_change_are_rejected(computation) -> None:
    counts = dict(computation.context_counts)
    counts["full_predictor_population_count"] = 526
    with pytest.raises(ValueError, match="FULL_CONTEXT_COUNT_INVALID"):
        subject.validate_covapie_batch001_formal_split_admission_v1(
            replace(computation, context_counts=counts)
        )
    with pytest.raises(ValueError, match="FORMAL_INPUT_ORDER_INDEPENDENCE_INVALID"):
        subject.validate_covapie_batch001_formal_split_admission_v1(
            replace(computation, input_order_independence_verified=False)
        )


def test_exact_four_artifacts_are_deterministic_and_runtime_metadata_free(artifacts) -> None:
    repeated = subject.build_covapie_batch001_formal_split_admission_artifacts_v1()
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES_V1
    assert len(artifacts) == 4
    assert repeated == artifacts
    registry = json.loads(artifacts[subject.COMPONENT_REGISTRY_V1])
    manifest = json.loads(artifacts[subject.MANIFEST_V1])
    events = list(csv.DictReader(io.StringIO(
        artifacts[subject.EVENT_ADMISSION_V1].decode("utf-8")
    )))
    assert registry["component_count"] == 4
    assert len(events) == 13
    assert manifest["prediction_and_formal_assignment"]["read_only_split_superseded_event_count"] == 7
    assert manifest["formal_owner_independent_oracle_parity"] is True
    assert manifest["cross_component_leakage_audit"]["cross_split_leakage_violation_count"] == 0
    assert manifest["ready_for_admission_aware_cpu_model_smoke"] is True
    assert manifest["ready_for_training"] is False
    for payload in artifacts.values():
        text = payload.decode("utf-8")
        assert "timestamp" not in text.lower()
        assert "mtime" not in text.lower()
        assert str(subject._DEFAULT_REPOSITORY_ROOT) not in text

from __future__ import annotations

import copy
from dataclasses import fields
import hashlib
import json
from pathlib import Path

import pytest
import torch

from covalent_ext import covapie_existing_positive_runtime_and_split_closure_v1 as closure
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_EXACT7 = {
    "COVAPIE_CYS_SG_EVENT_V1:6OIM:A:CYS:12-:SG:D:MOV:C25",
    "COVAPIE_CYS_SG_EVENT_V1:6DI9:A:CYS:481-:SG:B:GJJ:C33",
    "COVAPIE_CYS_SG_EVENT_V1:5F2E:A:CYS:12-:SG:E:5UT:C15",
    "COVAPIE_CYS_SG_EVENT_V1:1NFZ:A:CYS:67-:SG:E:EIP:C12",
    "COVAPIE_CYS_SG_EVENT_V1:1NFZ:B:CYS:67-:SG:H:EIP:C12",
    "COVAPIE_CYS_SG_EVENT_V1:2AX0:A:CYS:366-:SG:F:5X:C1",
    "COVAPIE_CYS_SG_EVENT_V1:2AX0:B:CYS:366-:SG:K:5X:C1",
}
GJJ_EVENT_ID = "COVAPIE_CYS_SG_EVENT_V1:6DI9:A:CYS:481-:SG:B:GJJ:C33"


@pytest.fixture(scope="module")
def computation():
    return closure.compute_covapie_existing_positive_runtime_and_split_closure_v1(
        repository_root=REPO
    )


def _published_audit() -> dict[str, object]:
    path = REPO / closure.SCALEUP_SUMMARY_V1
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "e0e0c64c07b32f1e9f6b3d8ed4c9af6ec9b7db77eeb80345e2de7eab54e65561"
    )
    return json.loads(path.read_text())["global_current_positive_authority_audit"]


def _published_simulation(observation: dict[str, object]) -> dict[str, object]:
    simulated = copy.deepcopy(observation)
    simulated.update({
        "HEAD": "1" * 40,
        "HEAD_parent": closure.BASELINE_HEAD_V1,
        "head_parent_ids": [closure.BASELINE_HEAD_V1],
        "HEAD_tree": "2" * 40,
        "HEAD_subject": closure.PUBLICATION_SUBJECT_V1,
        "origin_main": "1" * 40,
        "untracked": [],
        "candidate_filesystem_modes": {},
        "head_changed_entries": [
            {"status": "A", "path": path}
            for path in sorted(closure.AUTHORIZED_PATHS_V1)
        ],
        "head_candidate_path_modes": {
            path: "100644" for path in closure.AUTHORIZED_PATHS_V1
        },
    })
    return simulated


def test_independent_published_37_event_authority_oracles():
    audit = _published_audit()
    records = audit["records"]
    full = [
        row for row in records
        if row["role_label_authoritative"]
        and row["reactive_pair_authoritative"]
        and row["POST_geometry_authoritative"]
    ]
    runtime = [row for row in records if row["current_runtime_model_usable"]]
    exact7 = {
        row["canonical_event_id"] for row in full
        if not row["current_runtime_model_usable"]
    }
    incomplete = [row for row in records if not row["role_label_authoritative"]]
    assert len(records) == 37
    assert len(full) == 36
    assert len(runtime) == 29
    assert exact7 == EXPECTED_EXACT7
    assert len(incomplete) == 1
    assert incomplete[0]["canonical_event_id"] == closure.AJ3_EVENT_ID_V1


def test_published_before_counts_are_frozen(computation):
    counts = computation.counts
    assert counts["published_positive_authority_event_count_before"] == 37
    assert counts["full_positive_supervision_event_count_before"] == 36
    assert counts["current_runtime_model_usable_event_count_before"] == 29
    assert counts["full_supervision_runtime_incomplete_event_count_before"] == 7
    assert counts["task_relevance_only_incomplete_event_count_before"] == 1


def test_exact7_runtime_closure_succeeds_without_predetermining_source_result(computation):
    assert len(computation.runtime_samples) == 7
    assert {sample.canonical_event_id for sample in computation.runtime_samples} == EXPECTED_EXACT7
    assert {
        row["runtime_binding_status"] for row in computation.runtime_binding_rows
    } == {"CURRENT_RUNTIME_BINDING_CLOSED"}


def test_exact7_role_profiles_are_mechanically_derived(computation):
    for sample in computation.runtime_samples:
        payload = sample.payload
        roles = payload["roles"]
        expected = closure._derive_profile(roles)
        assert payload["role_profile"] == expected
        assert tuple(payload["valid_task_ids"]) == (0, 1, 2, 3, 4)


def test_all_five_canonical_tasks_and_b3_are_runtime_valid(computation):
    split_by_event = {
        row["canonical_event_id"]: row for row in computation.leakage_split_rows
    }
    for sample in computation.runtime_samples:
        row = split_by_event[sample.canonical_event_id]
        training_admitted = bool(
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "true"
            and row["formal_split_after"] == "train"
        )
        observed = []
        for task_id in sample.payload["valid_task_ids"]:
            _batch, supervision = closure._model_batch_and_supervision(
                sample.payload,
                task_id=task_id,
                training_admitted=training_admitted,
            )
            observed.append(int(supervision.canonical_task_id.item()))
            assert bool(supervision.sample_training_admitted.item()) is training_admitted
        assert observed == [0, 1, 2, 3, 4]


def test_exact_37_field_dataclass_parity_for_every_runtime_target(computation):
    expected = tuple(field.name for field in fields(
        CovapieCurrent11TrainingSupervisionTensorsV1
    ))
    assert len(expected) == 37
    for sample in computation.runtime_samples:
        assert isinstance(sample.supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
        assert tuple(field.name for field in fields(sample.supervision)) == expected
        assert tuple(sample.payload["dataclass_field_names"]) == expected


def test_model_input_fields_and_source_parser_identity_are_complete(computation):
    for sample in computation.runtime_samples:
        payload = sample.payload
        assert set(closure._MODEL_INPUT_FIELDS_V1) <= set(sample.model_input_batch)
        assert payload["ligand_parser_local_indices"] == tuple(
            range(payload["ligand_atom_count"])
        )
        assert payload["pocket_parser_local_indices"] == tuple(
            range(payload["pocket_atom_count"])
        )
        assert len(set(payload["ligand_source_row_indices"])) == payload["ligand_atom_count"]
        assert len(set(payload["pocket_source_row_indices"])) == payload["pocket_atom_count"]


def test_reactive_pair_target_cys_sg_and_post_geometry_are_exact(computation):
    for sample in computation.runtime_samples:
        payload = sample.payload
        ligand_index, pocket_index = payload["positive_reactive_pair_indices"]
        assert payload["ligand_atom_ids"][ligand_index] == payload["ligand_reactive_atom_id"]
        assert pocket_index == payload["target_reactive_pocket_local_index"]
        assert pocket_index in payload["target_residue_member_indices"]
        observed = float(
            sample.supervision.observed_complex_pair_distance_angstrom.item()
        )
        assert observed == pytest.approx(payload["POST_distance_angstrom"], abs=0.0015)


def test_pre_remains_unavailable_and_never_loss_eligible(computation):
    for sample in computation.runtime_samples:
        payload = sample.payload
        supervision = sample.supervision
        assert payload["PRE_geometry_authoritative"] is False
        assert payload["PRE_loss_eligible"] is False
        assert payload["PRE_distance_angstrom"] is None
        assert torch.isnan(supervision.pre_post_geometry_target_angstrom[0, 0])
        assert not bool(supervision.pre_post_geometry_component_valid_mask[0, 0])
        assert not bool(supervision.pre_post_geometry_component_loss_mask[0, 0])
        assert bool(supervision.pre_post_geometry_component_valid_mask[0, 1])


def test_exact7_training_admission_independently_joins_final_formal_split(computation):
    split_by_event = {
        row["canonical_event_id"]: row for row in computation.leakage_split_rows
    }
    admitted_event_ids = set()
    for sample in computation.runtime_samples:
        row = split_by_event[sample.canonical_event_id]
        expected = bool(
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "true"
            and row["formal_split_after"] == "train"
        )
        observed = bool(sample.supervision.sample_training_admitted.item())
        assert observed is expected
        if observed:
            admitted_event_ids.add(sample.canonical_event_id)
    assert admitted_event_ids == {GJJ_EVENT_ID}


def test_six_heldout_exact7_samples_disable_losses_but_retain_labels(computation):
    heldout = [
        sample for sample in computation.runtime_samples
        if sample.canonical_event_id != GJJ_EVENT_ID
    ]
    assert len(heldout) == 6
    for sample in heldout:
        supervision = sample.supervision
        assert not bool(supervision.sample_training_admitted.item())
        assert int(supervision.ligand_active_diffusion_loss_mask.sum().item()) == 0
        assert int(supervision.pair_head_candidate_loss_mask.sum().item()) == 0
        assert not bool(supervision.pair_contrastive_sample_loss_mask.item())
        assert supervision.pre_post_geometry_component_loss_mask.tolist() == [
            [False, False]
        ]
        assert bool(supervision.canonical_task_valid.item())
        assert bool(supervision.ligand_role_valid.all().item())
        assert bool(supervision.target_residue_condition_valid.item())
        assert bool(supervision.pair_positive_candidate_valid.item())
        assert bool(supervision.observed_complex_pair_distance_valid.item())
        assert supervision.pre_post_geometry_component_valid_mask.tolist() == [
            [False, True]
        ]


def test_gjj_train_sample_activates_only_valid_training_components(computation):
    sample = next(
        sample for sample in computation.runtime_samples
        if sample.canonical_event_id == GJJ_EVENT_ID
    )
    supervision = sample.supervision
    assert bool(supervision.sample_training_admitted.item())
    assert int(supervision.ligand_active_diffusion_loss_mask.sum().item()) > 0
    assert int(supervision.pair_head_candidate_loss_mask.sum().item()) > 0
    assert bool(supervision.pair_head_candidate_loss_mask.all().item())
    assert bool(supervision.pair_contrastive_sample_loss_mask.item())
    assert supervision.pre_post_geometry_component_valid_mask.tolist() == [
        [False, True]
    ]
    assert supervision.pre_post_geometry_component_loss_mask.tolist() == [
        [False, True]
    ]


@pytest.mark.parametrize(
    "mutation",
    (
        "sample_training_admitted",
        "ligand_active_diffusion_loss_mask",
        "pair_head_candidate_loss_mask",
        "pair_contrastive_sample_loss_mask",
        "pre_post_geometry_component_loss_mask",
    ),
)
def test_heldout_training_activation_mutations_fail_closed(computation, mutation):
    sample = next(
        sample for sample in computation.runtime_samples
        if sample.canonical_event_id != GJJ_EVENT_ID
    )
    supervision = copy.deepcopy(sample.supervision)
    tensor = getattr(supervision, mutation)
    if mutation == "pre_post_geometry_component_loss_mask":
        tensor[0, 1] = True
    else:
        tensor.reshape(-1)[0] = True
    with pytest.raises(
        ValueError,
        match=closure.EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1,
    ):
        closure._validate_training_mask_activation_v1(
            supervision, training_admitted=False
        )


def test_k36_exact5_formal_split_closes_as_one_atomic_component(computation):
    rows = [
        row for row in computation.leakage_split_rows
        if row["canonical_event_id"] in closure.K36_EVENT_IDS_V1
    ]
    assert len(rows) == 5
    assert {row["leakage_classification"] for row in rows} == {"NEW_EXPANSION_COMPONENT"}
    assert len({row["leakage_group_id_after"] for row in rows}) == 1
    assert {row["formal_split_after"] for row in rows} == {"test"}
    assert {row["formal_split_authoritative_after"] for row in rows} == {"true"}


def test_eip_and_5x_new_components_receive_joint_additive_assignments(computation):
    rows = {row["canonical_event_id"]: row for row in computation.leakage_split_rows}
    eip = [rows[event_id] for event_id in closure.RUNTIME_TARGET_EVENT_IDS_V1[3:5]]
    five_x = [rows[event_id] for event_id in closure.RUNTIME_TARGET_EVENT_IDS_V1[5:7]]
    assert len({row["leakage_group_id_after"] for row in eip}) == 1
    assert {row["formal_split_after"] for row in eip} == {"test"}
    assert len({row["leakage_group_id_after"] for row in five_x}) == 1
    assert {row["formal_split_after"] for row in five_x} == {"validation"}


def test_exact3_frozen_formal_splits_become_effective_only_after_runtime_closure(computation):
    rows = {row["canonical_event_id"]: row for row in computation.leakage_split_rows}
    expected = {
        closure.RUNTIME_TARGET_EVENT_IDS_V1[0]: "test",
        closure.RUNTIME_TARGET_EVENT_IDS_V1[1]: "train",
        closure.RUNTIME_TARGET_EVENT_IDS_V1[2]: "test",
    }
    for event_id, split in expected.items():
        row = rows[event_id]
        assert row["current_runtime_model_usable_before"] == "false"
        assert row["current_runtime_model_usable_after"] == "true"
        assert row["formal_split_before"] == split
        assert row["formal_split_after"] == split


def test_existing_formal_split_assignments_are_byte_semantically_preserved(computation):
    assert computation.existing_split_assignments_changed is False
    for row in computation.leakage_split_rows:
        if row["formal_split_authoritative_before"] == "true":
            assert row["formal_split_authoritative_after"] == "true"
            assert row["formal_split_after"] == row["formal_split_before"]


def test_after_counts_and_no_runtime_usable_unsplit_gap(computation):
    counts = computation.counts
    assert counts["current_runtime_model_usable_event_count_after"] == 36
    assert counts["current_runtime_model_usable_without_formal_split_count_after"] == 0
    assert counts["formal_training_split_admitted_positive_count_after"] == 14
    assert counts["formal_validation_split_positive_count_after"] == 8
    assert counts["formal_test_split_positive_count_after"] == 14
    assert counts["remaining_positive_but_runtime_incomplete_count"] == 1


def test_training_admission_is_exact_three_way_conjunction(computation):
    for row in computation.leakage_split_rows:
        expected = (
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "true"
            and row["formal_split_after"] == "train"
        )
        assert (row["training_admission_readiness"] == "FORMAL_TRAIN_ADMITTED") is expected


def test_aj3_is_unchanged_and_not_runtime_or_split_promoted(computation):
    row = next(
        row for row in computation.leakage_split_rows
        if row["canonical_event_id"] == closure.AJ3_EVENT_ID_V1
    )
    assert row["current_runtime_model_usable_after"] == "false"
    assert row["formal_split_authoritative_after"] == "false"
    assert row["formal_split_after"] == ""
    assert row["training_admission_readiness"] == "RUNTIME_BINDING_INCOMPLETE"


@pytest.mark.parametrize("case", range(15))
def test_runtime_binding_negative_mutations_fail_closed(computation, case):
    payload = copy.deepcopy(computation.runtime_samples[0].payload)
    if case == 0:
        payload["expected_canonical_event_id"] = "MISMATCH"
    elif case == 1:
        payload["roles"]["scaffold_atom_ids"] = (
            *payload["roles"]["scaffold_atom_ids"], "MISSING_ROLE_ATOM"
        )
    elif case == 2:
        atom = payload["roles"]["scaffold_atom_ids"][0]
        payload["roles"]["linker_atom_ids"] = (
            *payload["roles"]["linker_atom_ids"], atom
        )
    elif case == 3:
        payload["roles"]["scaffold_atom_ids"] = payload["roles"]["scaffold_atom_ids"][1:]
    elif case == 4:
        payload["expected_ligand_reactive_atom_id"] = "WRONG"
    elif case == 5:
        payload["POST_geometry_authoritative"] = False
    elif case == 6:
        payload["feature_compatible"] = False
    elif case == 7:
        payload["dataclass_field_names"] = payload["dataclass_field_names"][:-1]
    elif case == 8:
        payload["role_profile"] = "UNSUPPORTED_PROFILE"
    elif case == 9:
        linker = payload["roles"]["linker_atom_ids"]
        payload["roles"]["scaffold_atom_ids"] = (
            *payload["roles"]["scaffold_atom_ids"], *linker
        )
        payload["roles"]["linker_atom_ids"] = ()
        payload["role_profile"] = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        payload["valid_task_ids"] = (0, 1, 2, 3, 4)
    elif case == 10:
        payload["PRE_geometry_authoritative"] = True
        payload["PRE_loss_eligible"] = True
        payload["PRE_distance_angstrom"] = 2.0
    elif case == 11:
        payload["source_bindings_verified"] = False
    elif case == 12:
        payload["canonical_event_id"] = closure.AJ3_EVENT_ID_V1
        payload["expected_canonical_event_id"] = closure.AJ3_EVENT_ID_V1
    elif case == 13:
        payload["mapping_method"] = "FUZZY_COMPONENT_MAPPING"
    else:
        payload["mapping_method"] = "CHEMISTRY_SIGNATURE_ONLY_RUNTIME_PROMOTION"
    with pytest.raises(ValueError, match=closure.EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1):
        closure.validate_runtime_adapter_payload_v1(payload)


@pytest.mark.parametrize("case", range(8))
def test_split_negative_mutations_fail_closed(computation, case):
    rows = copy.deepcopy(list(computation.leakage_split_rows))
    if case == 0:
        row = next(row for row in rows if row["formal_split_authoritative_before"] == "true")
        row["formal_split_after"] = "test" if row["formal_split_before"] != "test" else "train"
    elif case == 1:
        k36 = [row for row in rows if row["canonical_event_id"] in closure.K36_EVENT_IDS_V1]
        k36[0]["formal_split_after"] = "train"
        k36[0]["training_admission_readiness"] = "FORMAL_TRAIN_ADMITTED"
    elif case == 2:
        row = next(row for row in rows if row["canonical_event_id"] in closure.K36_EVENT_IDS_V1)
        row["formal_split_authoritative_after"] = "false"
        row["formal_split_after"] = "train"
    elif case == 3:
        row = next(row for row in rows if row["leakage_classification"] == "NEW_EXPANSION_COMPONENT")
        row["assignment_policy"] = "ARBITRARY_NEW_COMPONENT_ASSIGNMENT"
    elif case == 4:
        k36 = [row for row in rows if row["canonical_event_id"] in closure.K36_EVENT_IDS_V1]
        k36[0]["formal_split_after"] = "validation"
    elif case == 5:
        row = rows[0]
        row["split_membership_count"] = "2"
    elif case == 6:
        row = next(row for row in rows if row["canonical_event_id"] == closure.AJ3_EVENT_ID_V1)
        row["formal_split_authoritative_after"] = "true"
        row["formal_split_after"] = "test"
        row["split_membership_count"] = "1"
        row["leakage_group_id_after"] = "SYNTHETIC_GROUP"
    else:
        row = next(row for row in rows if row["canonical_event_id"] == closure.AJ3_EVENT_ID_V1)
        row["formal_split_authoritative_after"] = "true"
        row["formal_split_after"] = "train"
        row["split_membership_count"] = "1"
        row["leakage_group_id_after"] = "SYNTHETIC_GROUP"
        row["training_admission_readiness"] = "FORMAL_TRAIN_ADMITTED"
    with pytest.raises(ValueError, match=closure.EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1):
        closure.validate_leakage_split_rows_v1(rows)


def test_artifact_serialization_is_byte_deterministic_with_one_computation(computation):
    first = closure.build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
        repository_root=REPO, computation=computation
    )
    second = closure.build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
        repository_root=REPO, computation=computation
    )
    assert first == second
    assert tuple(first) == closure.OUTPUT_FILENAMES_V1


def test_materialized_artifacts_match_in_memory_product(computation):
    expected = closure.build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
        repository_root=REPO, computation=computation
    )
    root = REPO / closure.OUTPUT_ROOT_RELATIVE_V1
    assert {path.name for path in root.iterdir()} == set(closure.OUTPUT_FILENAMES_V1)
    for name, payload in expected.items():
        assert (root / name).read_bytes() == payload


def test_normal_code_has_no_cumulative1000_rebuild_or_replay_call():
    source = (REPO / closure.SOURCE_RELATIVE_V1).read_text()
    assert "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.build_artifacts_v1" not in source
    assert "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.replay_no_network_v1" not in source
    assert "CONTROLLED_NETWORK_EXECUTION" not in source


def test_real_lifecycle_profile_passes_without_postpublication_skip():
    observation = closure.observe_repository_state_v1(REPO)
    profile = closure.classify_repository_profile_v1(observation)
    assert profile in {"candidate_precommit_untracked", "published_successor"}


def test_published_successor_profile_simulation_passes():
    observation = closure.observe_repository_state_v1(REPO)
    assert closure.classify_repository_profile_v1(
        _published_simulation(observation)
    ) == "published_successor"


def test_candidate_precommit_checker_marker_is_lifecycle_aware():
    assert closure._candidate_precommit_profile_passed_v1(
        "candidate_precommit_untracked"
    ) is True
    assert closure._candidate_precommit_profile_passed_v1(
        "published_successor"
    ) is False


def test_candidate_only_negative_profile_uses_synthetic_observation():
    observation = closure.observe_repository_state_v1(REPO)
    if closure.classify_repository_profile_v1(observation) == "published_successor":
        observation = {
            **observation,
            "HEAD": closure.BASELINE_HEAD_V1,
            "HEAD_parent": closure.BASELINE_PARENT_V1,
            "HEAD_tree": closure.BASELINE_TREE_V1,
            "HEAD_subject": closure.BASELINE_SUBJECT_V1,
            "origin_main": closure.BASELINE_HEAD_V1,
            "head_parent_ids": [closure.BASELINE_PARENT_V1],
            "untracked": sorted(closure.AUTHORIZED_PATHS_V1),
            "candidate_filesystem_modes": {
                path: "0644" for path in closure.AUTHORIZED_PATHS_V1
            },
        }
    broken = copy.deepcopy(observation)
    broken["untracked"] = [*broken["untracked"], "ninth_file.txt"]
    with pytest.raises(ValueError, match=closure.EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1):
        closure.classify_repository_profile_v1(broken)

from __future__ import annotations

import csv
from dataclasses import fields
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as subject,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CACHE = STATE / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = subject.BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_ERROR_V1


def _assert_public_error(callable_object, reason: str) -> None:
    with pytest.raises(ValueError) as captured:
        callable_object()
    assert str(captured.value) == f"{ERROR}:{reason}"


@pytest.fixture(scope="module")
def authority() -> subject.CovapieBatch001Train5FormalAuthorityAuditV1:
    return subject.audit_covapie_batch001_train5_formal_authority_v1(
        repository_root=ROOT
    )


@pytest.fixture(scope="module")
def prepared():
    return subject._prepare_train5_batch(
        repository_root=ROOT,
        cache_root=CACHE,
        requested_sample_identities=None,
    )


@pytest.fixture(scope="module")
def real_smoke_result(
) -> subject.CovapieBatch001Train5CpuForwardLossSmokeResultV1:
    return subject.run_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1(
        repository_root=ROOT,
        state_root=STATE,
        cache_root=CACHE,
        checkpoint_path=CHECKPOINT,
    )


def test_exact_formal_train5_is_derived_and_exclusions_are_exact(
    authority,
) -> None:
    assert authority.formal_train_event_ids == subject.FORMAL_TRAIN_EVENT_IDS_V1
    assert authority.DJK_train_event_count == 2
    assert authority.PTG_train_event_count == 3
    assert len(authority.formal_validation_event_ids) == 4
    assert authority.LN5_validation_event_count == 2
    assert authority.PX5_validation_event_count == 2
    assert len(authority.formal_unresolved_event_ids) == 4
    assert authority.NDU_unresolved_event_count == 4
    assert len(authority.non_target_component_event_ids) == 21
    assert authority.cross_split_leakage_violation_count == 0
    assert not set(authority.formal_train_event_ids) & set(
        authority.formal_validation_event_ids
    )
    assert not set(authority.formal_train_event_ids) & set(
        authority.formal_unresolved_event_ids
    )


def test_published_authority_remains_preview_only_and_inactive() -> None:
    path = ROOT / subject.FORMAL_AUTHORITY_RELATIVE_PATH_V1
    with path.open(newline="", encoding="utf-8") as handle:
        rows = tuple(csv.DictReader(handle))
    assert len(rows) == 13
    assert all(row["sample_training_admitted"] == "false" for row in rows)
    assert all(
        row["model_training_activation_authorized"] == "false" for row in rows
    )


def test_formal_authority_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    corrupted = tmp_path / "formal.csv"
    corrupted.write_bytes(b"not-the-published-authority\n")
    _assert_public_error(
        lambda: subject.verify_covapie_batch001_train5_formal_authority_file_v1(
            formal_authority_path=corrupted
        ),
        "FORMAL_AUTHORITY_SHA256_MISMATCH",
    )


def test_checkpoint_sha_mismatch_fails_before_loading(tmp_path: Path) -> None:
    corrupted = tmp_path / "checkpoint.ckpt"
    corrupted.write_bytes(b"not-a-checkpoint")
    _assert_public_error(
        lambda: subject.verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=corrupted
        ),
        "CHECKPOINT_SHA256_MISMATCH",
    )


@pytest.mark.parametrize(
    "excluded_kind",
    (
        "LN5",
        "PX5",
        "NDU",
        "ONL",
        "TASK_DOMAIN_NEGATIVE",
        "UNKNOWN",
        "NON_TARGET_COMPONENT_MEMBER",
    ),
)
def test_only_exact_formally_admitted_train5_can_enter_smoke(
    authority, excluded_kind: str,
) -> None:
    replacement = {
        "LN5": authority.formal_validation_event_ids[0],
        "PX5": authority.formal_validation_event_ids[2],
        "NDU": authority.formal_unresolved_event_ids[0],
        "ONL": "COVAPIE_CYS_SG_EVENT_V1:XXXX:A:CYS:1-:SG:B:ONL:C1",
        "TASK_DOMAIN_NEGATIVE": "COVAPIE_CYS_SG_TASK_DOMAIN_NEGATIVE_V1:000001",
        "UNKNOWN": "COVAPIE_CYS_SG_EVENT_V1:XXXX:A:CYS:1-:SG:B:UNK:C1",
        "NON_TARGET_COMPONENT_MEMBER": authority.non_target_component_event_ids[0],
    }[excluded_kind]
    requested = (replacement,) + authority.formal_train_event_ids[1:]
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=CHECKPOINT,
            requested_sample_identities=requested,
        ),
        "ONLY_EXACT_FORMALLY_ADMITTED_TRAIN5_MAY_BE_SMOKE_ACTIVATED",
    )


def test_train5_structure_scheduler_and_static_five_mask_contract(prepared) -> None:
    assert prepared.sample_identities == subject.FORMAL_TRAIN_EVENT_IDS_V1
    assert prepared.scheduled_task_ids == (4, 4, 2, 0, 4)
    assert all(set(cycle) == set(range(5)) for cycle in prepared.five_epoch_task_schedule_audit)
    assert prepared.static_five_mask_audit_passed is True
    assert tuple(
        len(record.ligand_retained_heavy_atoms)
        for record in prepared.structural_records
    ) == (23, 23, 23, 23, 23)
    assert tuple(
        len(record.pocket_retained_heavy_atoms)
        for record in prepared.structural_records
    ) == (103, 118, 124, 110, 123)
    assert all(record.role_profile == "STRICT_LINKER_PRESENT_V1" for record in prepared.structural_records)
    assert all(record.applicable_canonical_task_ids == (0, 1, 2, 3, 4) for record in prepared.structural_records)


def test_ephemeral_admission_reuses_37_field_dataclass_without_mutating_preview(
    prepared,
) -> None:
    preview = prepared.preview_supervision
    admitted = prepared.supervision
    assert isinstance(admitted, CovapieCurrent11TrainingSupervisionTensorsV1)
    assert len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) == 37
    assert preview is not admitted
    assert preview.sample_training_admitted.tolist() == [False] * 5
    assert admitted.sample_training_admitted.tolist() == [True] * 5
    assert admitted.canonical_task_valid.tolist() == [True] * 5
    assert admitted.ligand_role_valid.tolist() == [True] * 115
    assert torch.equal(
        admitted.ligand_active_diffusion_loss_mask,
        admitted.ligand_base_generation_mask,
    )
    assert not bool(preview.ligand_active_diffusion_loss_mask.any().item())
    ligand_membership = prepared.model_input_batch["lig_mask"]
    assert all(
        bool(admitted.ligand_active_diffusion_loss_mask[:, 0][ligand_membership == sample].any().item())
        for sample in range(5)
    )


def test_minimal_seed_anchor_distance_and_exact_cys_sg_mapping(prepared) -> None:
    supervision = prepared.supervision
    assert supervision.ligand_minimal_seed_or_anchor_valid.tolist() == [False] * 5
    assert not bool(supervision.ligand_minimal_seed_or_anchor_mask.any().item())
    assert supervision.ligand_anchor_distance_valid.tolist() == [[True]] * 115
    assert bool(torch.isfinite(supervision.ligand_anchor_distance_angstrom).all().item())
    assert bool((supervision.ligand_anchor_distance_angstrom >= 0).all().item())
    assert supervision.target_residue_condition_valid.tolist() == [True] * 5
    assert int(supervision.target_residue_reactive_atom_mask.sum().item()) == 5
    assert all(record.protein_residue_name == "CYS" for record in prepared.structural_records)
    assert all(record.protein_reactive_atom_id == "SG" for record in prepared.structural_records)
    pocket_membership = prepared.model_input_batch["pocket_mask"]
    assert torch.equal(
        pocket_membership[supervision.target_residue_reactive_atom_flat_index],
        torch.arange(5),
    )


def test_pair_candidates_and_post_only_geometry_are_activated_exactly(prepared) -> None:
    supervision = prepared.supervision
    assert len(supervision.pair_candidate_batch_index) == 690
    assert int(supervision.pair_candidate_is_positive.sum().item()) == 5
    assert int(supervision.pair_candidate_is_negative.sum().item()) == 685
    assert supervision.pair_positive_candidate_index.tolist() == [83, 221, 395, 533, 671]
    assert bool((supervision.pair_negative_count > 0).all().item())
    assert bool(supervision.pair_head_candidate_loss_mask.all().item())
    assert bool(supervision.pair_contrastive_sample_loss_mask.all().item())
    ligand_membership = prepared.model_input_batch["lig_mask"]
    pocket_membership = prepared.model_input_batch["pocket_mask"]
    assert torch.equal(
        supervision.pair_candidate_batch_index,
        ligand_membership[supervision.pair_candidate_ligand_flat_index],
    )
    assert torch.equal(
        supervision.pair_candidate_batch_index,
        pocket_membership[supervision.pair_candidate_pocket_flat_index],
    )
    assert supervision.pre_post_geometry_component_valid_mask.tolist() == [[False, True]] * 5
    assert supervision.pre_post_geometry_component_loss_mask.tolist() == [[False, True]] * 5
    assert bool(torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0]).all().item())
    assert bool(torch.isfinite(supervision.pre_post_geometry_target_angstrom[:, 1]).all().item())
    assert bool((supervision.pre_post_geometry_target_angstrom[:, 1] > 0).all().item())


def test_real_checkpoint_cpu_forward_heads_and_all_losses(real_smoke_result) -> None:
    result = real_smoke_result
    assert result.implementation_status == "passed"
    assert result.formal_train_event_ids == subject.FORMAL_TRAIN_EVENT_IDS_V1
    assert not set(result.formal_validation_event_ids) & set(result.formal_train_event_ids)
    assert not set(result.formal_unresolved_event_ids) & set(result.formal_train_event_ids)
    assert result.ligand_node_count == 115
    assert result.pocket_node_count == 578
    assert result.pair_candidate_count == 690
    assert result.pair_positive_count == 5
    assert result.pair_negative_count == 685
    assert dict(result.tensor_shapes) == {
        "diffusion_epsilon_ligand": (115, 13),
        "denoised_ligand_xh": (115, 13),
        "ligand_hidden": (115, 32),
        "pocket_hidden": (578, 32),
        "role_hidden_delta": (115, 32),
        "pair_logits": (690,),
        "pair_embeddings": (690, 32),
        "geometry_predictions": (690, 2),
        "diffusion_timestep": (5,),
    }
    assert all(torch.isfinite(torch.tensor(value)) for value in dict(result.runtime_losses).values())
    assert result.base_diffusion_valid_sample_count == 5
    assert result.covalent_pair_prediction_valid_sample_count == 5
    assert result.pre_post_geometry_valid_sample_count == 5
    assert result.covalent_pair_contrastive_valid_sample_count == 5
    assert result.PRE_geometry_valid_sample_count == 0


def test_current_weights_geometry_graph_and_no_mutation_or_update(real_smoke_result) -> None:
    result = real_smoke_result
    assert dict(result.current_loss_weights) == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.1,
    }
    assert dict(result.runtime_losses)["loss_pre_post_geometry"] > 0.0
    assert result.geometry_contribution_to_loss_total == 0.0
    assert result.loss_total_requires_grad is True
    assert result.geometry_loss_requires_grad is True
    assert result.geometry_head_autograd_path_in_loss_total is True
    assert (
        result.geometry_head_nonzero_gradient_from_loss_total_in_future_backward
        is False
    )
    assert result.parameter_gradients_created is False
    assert result.model_state_modified_by_smoke is False
    assert result.checkpoint_modified is False
    assert result.optimizer_created is False
    assert result.optimizer_step_performed is False
    assert result.backward_performed is False
    assert result.Trainer_used is False
    assert result.training_performed is False
    assert result.CPU_only is True
    assert result.GPU_used is False
    assert result.architecture_modification_required_before_backward_smoke is False
    assert result.data_label_family_or_PRE_blocker_required_before_backward_smoke is False
    assert result.geometry_weight_policy_decision_required_before_backward_smoke is True
    assert result.ready_for_single_backward_optimizer_step_smoke is False


def test_real_checkpoint_migration_architecture_and_determinism(real_smoke_result) -> None:
    result = real_smoke_result
    assert result.checkpoint_sha256 == subject.CHECKPOINT_SHA256_V1
    assert dict(result.migration_counts) == {
        "checkpoint_key_count": 122,
        "target_model_key_count": 141,
        "shared_key_count": 122,
        "target_only_key_count": 19,
        "checkpoint_only_key_count": 0,
        "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": 122,
    }
    assert result.migration_missing_keys == ()
    assert result.migration_unexpected_keys == ()
    assert dict(result.architecture) == {
        "device": "cpu",
        "mode": "pocket_conditioning",
        "pocket_representation": "full-atom",
        "atom_nf": 10,
        "target_residue_atom_conditioning": True,
        "virtual_nodes": False,
        "loss_type": "l2",
        "joint_nf": 32,
        "hidden_nf": 128,
        "egnn_layers": 5,
    }
    assert result.diffusion_timesteps == (46, 279, 91, 52, 102)
    assert result.runtime_losses == result.repeated_runtime_losses
    assert result.maximum_repeated_loss_absolute_difference == 0.0
    assert result.repeat_count == 2


def test_product_source_has_no_backward_optimizer_trainer_or_persistent_output() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert ".backward(" not in source
    assert "configure_optimizers(" not in source
    assert "torch.optim" not in source
    assert "Trainer(" not in source
    assert "torch.no_grad" not in source
    assert ".save(" not in source
    assert "torch.save" not in source
    assert "numpy.save" not in source

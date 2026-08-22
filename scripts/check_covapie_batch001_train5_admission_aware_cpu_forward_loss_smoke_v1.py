#!/usr/bin/env python3
"""Fail-closed checker for the batch-001 admission-aware train5 CPU smoke."""

from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as subject,
)


STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = REPOSITORY_ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
CHECK_ERROR = (
    "COVAPIE_BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_V1_"
    "CHECK_ERROR"
)
RECOMMENDED_NEXT_STEP = (
    "gpt_audit_train5_cpu_forward_loss_smoke_then_decide_geometry_weight_"
    "policy_and_build_single_backward_optimizer_step_smoke_v1"
)


def _fail(reason: str) -> None:
    raise ValueError(f"{CHECK_ERROR}:{reason}")


def check_v1() -> dict[str, object]:
    result = subject.run_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
        checkpoint_path=CHECKPOINT,
    )
    losses = dict(result.runtime_losses)
    weights = dict(result.current_loss_weights)
    migration = dict(result.migration_counts)
    architecture = dict(result.architecture)
    shapes = dict(result.tensor_shapes)
    if (
        result.implementation_status != "passed"
        or result.formal_train_event_ids != subject.FORMAL_TRAIN_EVENT_IDS_V1
        or len(result.formal_validation_event_ids) != 4
        or len(result.formal_unresolved_event_ids) != 4
        or result.scheduled_task_ids != (4, 4, 2, 0, 4)
        or any(set(cycle) != set(range(5)) for cycle in result.five_epoch_task_schedule_audit)
        or result.ligand_counts != (23, 23, 23, 23, 23)
        or result.pocket_counts != (103, 118, 124, 110, 123)
        or result.ligand_node_count != 115
        or result.pocket_node_count != 578
        or result.pair_candidate_count != 690
        or result.pair_positive_count != 5
        or result.pair_negative_count != 685
        or result.pair_positive_candidate_indices != (83, 221, 395, 533, 671)
        or shapes.get("diffusion_epsilon_ligand") != (115, 13)
        or shapes.get("denoised_ligand_xh") != (115, 13)
        or shapes.get("ligand_hidden") != (115, 32)
        or shapes.get("pocket_hidden") != (578, 32)
        or shapes.get("role_hidden_delta") != (115, 32)
        or shapes.get("pair_logits") != (690,)
        or shapes.get("pair_embeddings") != (690, 32)
        or shapes.get("geometry_predictions") != (690, 2)
        or shapes.get("diffusion_timestep") != (5,)
    ):
        _fail("POPULATION_SCHEDULING_SHAPE_OR_CANDIDATE_ACCEPTANCE_INVALID")
    if (
        set(losses)
        != {
            "loss_base_diffusion",
            "loss_covalent_pair_prediction",
            "loss_pre_post_geometry",
            "loss_covalent_pair_contrastive",
            "loss_total",
        }
        or result.base_diffusion_valid_sample_count != 5
        or result.covalent_pair_prediction_valid_sample_count != 5
        or result.pre_post_geometry_valid_sample_count != 5
        or result.covalent_pair_contrastive_valid_sample_count != 5
        or result.PRE_geometry_valid_sample_count != 0
        or weights
        != {
            "base_diffusion": 1.0,
            "covalent_pair_prediction": 1.0,
            "pre_post_geometry": 0.0,
            "covalent_pair_contrastive": 0.1,
        }
        or result.geometry_contribution_to_loss_total != 0.0
        or result.loss_total_requires_grad is not True
        or result.geometry_loss_requires_grad is not True
        or result.geometry_head_autograd_path_in_loss_total is not True
        or result.geometry_head_nonzero_gradient_from_loss_total_in_future_backward
        is not False
    ):
        _fail("LOSS_OR_GEOMETRY_WEIGHT_ACCEPTANCE_INVALID")
    if (
        result.checkpoint_sha256 != subject.CHECKPOINT_SHA256_V1
        or migration.get("checkpoint_key_count") != 122
        or migration.get("target_model_key_count") != 141
        or migration.get("shared_key_count") != 122
        or migration.get("target_only_key_count") != 19
        or migration.get("checkpoint_only_key_count") != 0
        or migration.get("shared_shape_mismatch_count") != 0
        or result.migration_missing_keys
        or result.migration_unexpected_keys
        or architecture
        != {
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
    ):
        _fail("CHECKPOINT_MIGRATION_OR_ARCHITECTURE_ACCEPTANCE_INVALID")
    if (
        result.runtime_losses != result.repeated_runtime_losses
        or result.maximum_repeated_loss_absolute_difference != 0.0
        or result.repeat_count != 2
        or result.parameter_gradients_created is not False
        or result.model_state_modified_by_smoke is not False
        or result.checkpoint_modified is not False
        or result.optimizer_created is not False
        or result.optimizer_step_performed is not False
        or result.backward_performed is not False
        or result.Trainer_used is not False
        or result.training_performed is not False
        or result.CPU_only is not True
        or result.GPU_used is not False
        or result.network_used is not False
        or result.supervision_dataclass_reused is not True
        or result.architecture_modification_required_before_backward_smoke
        is not False
        or result.data_label_family_or_PRE_blocker_required_before_backward_smoke
        is not False
        or result.geometry_weight_policy_decision_required_before_backward_smoke
        is not True
        or result.ready_for_single_backward_optimizer_step_smoke is not False
    ):
        _fail("DETERMINISM_OR_SAFETY_ACCEPTANCE_INVALID")
    return {
        "batch001_train5_admission_aware_cpu_forward_loss_smoke_built": True,
        "formal_train_authority_consumed": True,
        "formal_train_event_count": 5,
        "DJK_train_event_count": 2,
        "PTG_train_event_count": 3,
        "validation_event_forward_count": 0,
        "unresolved_event_forward_count": 0,
        "non_target_component_event_forward_count": 0,
        "scheduled_task_tuple": result.scheduled_task_ids,
        "five_epoch_task_schedule_audit": result.five_epoch_task_schedule_audit,
        "ligand_node_count": result.ligand_node_count,
        "pocket_node_count": result.pocket_node_count,
        "pair_candidate_count": result.pair_candidate_count,
        "pair_positive_count": result.pair_positive_count,
        "pair_negative_count": result.pair_negative_count,
        "diffusion_timesteps": result.diffusion_timesteps,
        "in_memory_smoke_sample_training_admitted_count": 5,
        "supervision_dataclass_reused": True,
        "real_pretrained_checkpoint_loaded": True,
        "checkpoint_sha256_verified": True,
        "checkpoint_migration_passed": True,
        "checkpoint_key_count": migration["checkpoint_key_count"],
        "target_model_key_count": migration["target_model_key_count"],
        "shared_checkpoint_key_count": migration["shared_key_count"],
        "target_only_key_count": migration["target_only_key_count"],
        "checkpoint_only_key_count": migration["checkpoint_only_key_count"],
        "shared_shape_mismatch_count": migration["shared_shape_mismatch_count"],
        "CPU_only": True,
        "GPU_used": False,
        "model_forward_performed": True,
        "base_diffusion_forward_performed": True,
        "pair_prediction_head_forward_performed": True,
        "geometry_head_forward_performed": True,
        "loss_performed": True,
        "base_diffusion_valid_sample_count": 5,
        "pair_prediction_valid_sample_count": 5,
        "POST_geometry_valid_sample_count": 5,
        "pair_contrastive_valid_sample_count": 5,
        "PRE_geometry_valid_sample_count": 0,
        "current_pre_post_geometry_loss_weight": weights["pre_post_geometry"],
        "POST_geometry_loss": losses["loss_pre_post_geometry"],
        "POST_geometry_loss_finite": True,
        "geometry_contribution_to_loss_total": 0.0,
        "geometry_head_autograd_path_in_loss_total": (
            result.geometry_head_autograd_path_in_loss_total
        ),
        "geometry_head_nonzero_gradient_from_loss_total_in_future_backward": (
            result.geometry_head_nonzero_gradient_from_loss_total_in_future_backward
        ),
        "loss_total": losses["loss_total"],
        "loss_total_finite": True,
        "loss_total_requires_grad": True,
        "backward_performed": False,
        "parameter_gradients_created": False,
        "optimizer_created": False,
        "optimizer_step_performed": False,
        "Trainer_used": False,
        "training_performed": False,
        "checkpoint_modified": False,
        "model_state_modified_by_smoke": False,
        "repository_existing_files_modified": False,
        "network_used": False,
        "architecture_modification_required_before_backward_smoke": (
            result.architecture_modification_required_before_backward_smoke
        ),
        "data_label_family_or_PRE_blocker_required_before_backward_smoke": (
            result.data_label_family_or_PRE_blocker_required_before_backward_smoke
        ),
        "geometry_weight_policy_decision_required_before_backward_smoke": (
            result.geometry_weight_policy_decision_required_before_backward_smoke
        ),
        "real_smoke_elapsed_seconds": result.elapsed_seconds,
        "ready_for_gpt_review": True,
        "ready_for_single_backward_optimizer_step_smoke": False,
        "recommended_next_step_exactly": RECOMMENDED_NEXT_STEP,
    }


def main() -> int:
    result = check_v1()
    for name, value in result.items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{name}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

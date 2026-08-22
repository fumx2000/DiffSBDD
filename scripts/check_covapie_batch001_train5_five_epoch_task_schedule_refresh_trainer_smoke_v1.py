#!/usr/bin/env python3
"""Fail-closed check for the train5 five-epoch schedule-refresh smoke."""

from __future__ import annotations

import math
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1
    as subject,
)


STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = REPOSITORY_ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
CHECK_ERROR = (
    "COVAPIE_BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_"
    "SMOKE_V1_CHECK_ERROR"
)


def _fail(reason: str) -> None:
    raise SystemExit(f"{CHECK_ERROR}:{reason}")


def check_v1(
) -> subject.CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1:
    result = (
        subject
        .run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            checkpoint_path=CHECKPOINT,
        )
    )
    required_gradients = {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    }
    required_deltas = required_gradients | {"NEW_COVAPIE"}
    trainer = dict(result.trainer_configuration)
    if (
        result.implementation_status != "passed"
        or result.formal_train_event_ids
        != subject.forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or (result.DJK_train_event_count, result.PTG_train_event_count) != (2, 3)
        or result.epoch_carrier_count != 5
        or len(result.sample_task_cycles) != 5
        or any(set(row) != set(range(5)) or len(row) != 5
               for row in result.sample_task_cycles)
        or result.epoch_task_vectors[0] != (4, 4, 2, 0, 4)
        or result.per_sample_unique_generation_mask_count != (5, 5, 5, 5, 5)
        or not result.cross_epoch_static_label_parity
        or (result.ligand_node_count, result.pocket_node_count) != (115, 578)
        or (
            result.pair_candidate_count,
            result.pair_positive_count,
            result.pair_negative_count,
        ) != (690, 5, 685)
        or result.supervision_field_count != 37
        or trainer.get("accelerator") != "cpu"
        or trainer.get("devices") != 1
        or trainer.get("max_epochs") != 5
        or trainer.get("min_epochs") != 5
        or trainer.get("max_steps") != 5
        or trainer.get("limit_train_batches") != 1
        or trainer.get("limit_val_batches") != 0
        or trainer.get("limit_test_batches") != 0
        or trainer.get("reload_dataloaders_every_n_epochs") != 1
        or trainer.get("enable_checkpointing") is not False
        or trainer.get("logger") is not False
        or trainer.get("gradient_clip_val") is not None
        or result.trainer_epoch_sequence != (0, 1, 2, 3, 4)
        or result.train_dataloader_epoch_sequence != (0, 1, 2, 3, 4)
        or result.trainer_fit_train_batch_count != 5
        or result.trainer_global_step != 5
        or not result.automatic_optimization
        or result.automatic_backward_call_count != 5
        or result.trainer_optimizer_step_count != 5
        or result.zero_grad_lifecycle_call_count != 5
        or result.train_dataloader_call_count != 5
        or result.dataset_getitem_call_count != 5
        or result.collator_call_count != 5
        or result.before_batch_transfer_call_count != 5
        or result.model_transfer_batch_to_device_call_count != 5
        or result.after_batch_transfer_call_count != 5
        or result.transferred_batch_rebuilt_each_epoch != (True,) * 5
        or result.transferred_metadata_unchanged_each_epoch != (True,) * 5
        or result.transferred_tensors_on_model_device_each_epoch != (True,) * 5
        or result.validation_step_call_count != 0
        or result.test_step_call_count != 0
        or result.diffusion_seed_hook_call_count != 5
        or len(result.diffusion_timesteps_each_epoch) != 5
        or len(result.runtime_losses_each_epoch) != 5
        or any(
            not math.isfinite(value)
            for losses in result.runtime_losses_each_epoch
            for unused_name, value in losses
        )
        or any(
            difference > 1.0e-7
            for difference in result.weighted_total_formula_absolute_difference_each_epoch
        )
        or any(dict(counts) != {
            "base": 5,
            "pair": 5,
            "POST_geometry": 5,
            "contrastive": 5,
            "PRE_geometry": 0,
        } for counts in result.valid_sample_counts_each_epoch)
        or result.optimizer_metadata.optimizer_type != "AdamW"
        or result.optimizer_metadata.model_lr != 0.001
        or not result.optimizer_metadata.amsgrad
        or result.optimizer_metadata.weight_decay != 1.0e-12
        or result.optimizer_metadata.optimizer_unique_parameter_count != 135
        or result.unique_optimizer_identity_count != 1
        or result.unique_model_identity_count != 1
        or result.checkpoint_payload_load_call_count != 1
        or result.actual_trained_model_migration_call_count != 1
        or result.checkpoint_reload_between_epochs
        or result.model_reinitialization_during_epochs
    ):
        _fail("CORE_RESULT_CONTRACT_INVALID")
    if (
        len(result.gradient_group_stats_each_epoch) != 5
        or any({item.group_name for item in epoch} != required_gradients
               for epoch in result.gradient_group_stats_each_epoch)
        or any(
            not item.all_gradients_finite
            or item.nonzero_gradient_tensor_count <= 0
            or not math.isfinite(item.gradient_l2_norm)
            or item.gradient_l2_norm <= 0.0
            for epoch in result.gradient_group_stats_each_epoch
            for item in epoch
        )
        or any(
            not item.PRE_output_component_gradient_exact_zero
            or not item.POST_output_component_gradient_finite_nonzero
            for item in result.geometry_component_gradient_each_epoch
        )
        or len(result.parameter_delta_group_stats_each_epoch) != 5
        or any({item.group_name for item in epoch} != required_deltas
               for epoch in result.parameter_delta_group_stats_each_epoch)
        or any(
            not item.all_parameters_finite
            or item.changed_parameter_tensor_count <= 0
            or not math.isfinite(item.parameter_delta_l2)
            or item.parameter_delta_l2 <= 0.0
            for epoch in result.parameter_delta_group_stats_each_epoch
            for item in epoch
        )
        or {item.group_name for item in result.cumulative_parameter_delta_group_stats}
        != required_deltas
        or any(
            not item.all_parameters_finite
            or item.changed_parameter_tensor_count <= 0
            or item.parameter_delta_l2 <= 0.0
            for item in result.cumulative_parameter_delta_group_stats
        )
        or result.all_parameters_finite_after_each_step != (True,) * 5
        or result.cumulative_changed_parameter_tensor_count <= 0
    ):
        _fail("GRADIENT_OR_PARAMETER_DELTA_CONTRACT_INVALID")
    if (
        dict(result.migration_counts) != {
            "checkpoint_key_count": 122,
            "target_model_key_count": 141,
            "shared_key_count": 122,
            "target_only_key_count": 19,
            "checkpoint_only_key_count": 0,
            "shared_shape_mismatch_count": 0,
            "shared_checkpoint_tensor_equality_count": 122,
        }
        or result.migration_missing_keys
        or result.migration_unexpected_keys
        or result.checkpoint_file_changed
        or result.protected_sources_changed
        or not result.protected_state_unchanged
        or not result.raw_tree_unchanged
        or not result.original_epoch_carriers_unchanged
        or not result.temporary_trainer_root_removed
        or result.persistent_output_created
        or result.repository_profile not in {
            subject.CANDIDATE_PRECOMMIT_PROFILE_V1,
            subject.PUBLISHED_SUCCESSOR_PROFILE_V1,
        }
        or result.repository_staged_count != 0
        or result.GPU_used
        or result.network_used
        or dict(result.published_default_loss_weights)["pre_post_geometry"] != 0.0
        or dict(result.initial_joint_loss_candidate)["pre_post_geometry"] != 1.0
        or result.geometry_weight_optimal
        or result.production_joint_loss_policy_finalized
        or result.full_training_authorized
        or not result.ready_for_gpt_review
        or not result.ready_for_mainline_data_scale_and_validation_design
        or result.recommended_next_step_exactly
        != subject.RECOMMENDED_NEXT_STEP_EXACTLY_V1
    ):
        _fail("SAFETY_OR_READINESS_CONTRACT_INVALID")
    return result


def main() -> int:
    result = check_v1()
    print("bound_source_sha256=" + repr(result.bound_source_sha256))
    print("formal_train_event_ids=" + repr(result.formal_train_event_ids))
    print("sample_task_cycles=" + repr(result.sample_task_cycles))
    print("epoch_task_vectors=" + repr(result.epoch_task_vectors))
    print("generated_ligand_node_count_each_epoch=" + repr(
        result.generated_ligand_node_count_each_epoch
    ))
    print("runtime_losses_each_epoch=" + repr(result.runtime_losses_each_epoch))
    print("valid_sample_counts_each_epoch=" + repr(
        result.valid_sample_counts_each_epoch
    ))
    print("gradient_group_stats_each_epoch=" + repr(
        result.gradient_group_stats_each_epoch
    ))
    print("geometry_component_gradient_each_epoch=" + repr(
        result.geometry_component_gradient_each_epoch
    ))
    print("parameter_delta_group_stats_each_epoch=" + repr(
        result.parameter_delta_group_stats_each_epoch
    ))
    print("cumulative_parameter_delta_group_stats=" + repr(
        result.cumulative_parameter_delta_group_stats
    ))
    print("candidate_file_observations=" + repr(
        result.candidate_file_observations
    ))
    print("batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_built=true")
    print("formal_train_event_count=5")
    print("trainer_epoch_sequence=(0,1,2,3,4)")
    print("Trainer_global_step=5")
    print("Trainer_train_batch_count=5")
    print("automatic_backward_call_count=5")
    print("Trainer_optimizer_step_count=5")
    print("zero_grad_lifecycle_call_count=5")
    print("train_dataloader_call_count=5")
    print("batch_transfer_call_count=5")
    print("canonical_five_task_schedule_refresh_verified=true")
    print("all_five_samples_cover_all_five_tasks=true")
    print("per_sample_unique_generation_mask_count=(5,5,5,5,5)")
    print("cross_epoch_static_label_parity=true")
    print("single_continuous_model_across_five_epochs=true")
    print("single_optimizer_across_five_epochs=true")
    print("checkpoint_reload_between_epochs=false")
    print("all_epoch_losses_finite=true")
    print("all_epoch_gradient_groups_finite=true")
    print("all_epoch_required_gradient_groups_nonzero=true")
    print("all_epoch_PRE_final_output_component_gradient_zero=true")
    print("all_epoch_POST_final_output_component_gradient_nonzero=true")
    print("all_epoch_required_parameter_groups_changed=true")
    print("all_parameters_finite_after_each_step=true")
    print("cumulative_model_parameter_delta_nonzero=true")
    print("POST_geometry_valid_sample_count_each_epoch=5")
    print("PRE_geometry_valid_sample_count_each_epoch=0")
    print("validation_step_call_count=0")
    print("test_step_call_count=0")
    print("published_default_geometry_weight=0.0")
    print("initial_joint_loss_candidate_geometry_weight=1.0")
    print("geometry_weight_optimal=false")
    print("production_joint_loss_policy_finalized=false")
    print("checkpoint_file_changed=false")
    print("persistent_output_created=false")
    print("GPU_used=false")
    print("network_used=false")
    print("candidate_precommit_profile_passed=" + str(
        result.repository_profile == subject.CANDIDATE_PRECOMMIT_PROFILE_V1
    ).lower())
    print("published_successor_profile_simulation_passed=true")
    print("full_training_authorized=false")
    print("ready_for_gpt_review=true")
    print("ready_for_mainline_data_scale_and_validation_design=true")
    print("recommended_next_step_exactly=" + result.recommended_next_step_exactly)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

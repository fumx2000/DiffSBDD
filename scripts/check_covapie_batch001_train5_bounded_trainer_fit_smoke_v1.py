#!/usr/bin/env python3
"""Fail-closed executable check for the bounded batch001 train5 Trainer smoke."""

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
    covapie_batch001_train5_bounded_trainer_fit_smoke_v1 as subject,
)


STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = REPOSITORY_ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
CHECK_ERROR = (
    "COVAPIE_BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_V1_CHECK_ERROR"
)


def _fail(reason: str) -> None:
    raise SystemExit(f"{CHECK_ERROR}:{reason}")


def check_v1() -> subject.CovapieBatch001Train5BoundedTrainerFitSmokeResultV1:
    result = subject.run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
        checkpoint_path=CHECKPOINT,
    )
    gradients = {item.group_name: item for item in result.gradient_group_stats}
    deltas = {item.group_name: item for item in result.parameter_delta_group_stats}
    required_gradients = {
        "ALL_PARAMETERS", "SHARED_PRETRAINED", "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR", "PAIR_HEAD", "GEOMETRY_HEAD",
    }
    required_deltas = required_gradients | {"NEW_COVAPIE"}
    if (
        result.implementation_status != "passed"
        or result.formal_train_event_ids
        != subject.forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or result.DJK_train_event_count != 2
        or result.PTG_train_event_count != 3
        or result.scheduled_task_ids != (4, 4, 2, 0, 4)
        or (result.ligand_node_count, result.pocket_node_count) != (115, 578)
        or (result.pair_candidate_count, result.pair_positive_count, result.pair_negative_count)
        != (690, 5, 685)
        or result.supervision_field_count != 37
        or result.repository_profile not in {
            subject.CANDIDATE_PRECOMMIT_PROFILE_V1,
            subject.PUBLISHED_SUCCESSOR_PROFILE_V1,
        }
        or not result.parameter_delta_snapshot_captured_before_optimizer_step
        or result.parameter_delta_snapshot_optimizer_step_count_at_capture != 0
        or result.initial_joint_loss_candidate != (
            ("base_diffusion", 1.0),
            ("covalent_pair_prediction", 1.0),
            ("pre_post_geometry", 1.0),
            ("covalent_pair_contrastive", 0.1),
        )
        or dict(result.published_default_loss_weights)["pre_post_geometry"] != 0.0
        or result.published_default_modified
        or not result.trainer_fit_invoked
        or result.trainer_fit_train_batch_count != 1
        or result.trainer_global_step != 1
        or not result.automatic_optimization
        or result.automatic_backward_call_count != 1
        or result.trainer_optimizer_step_count != 1
        or result.zero_grad_lifecycle_call_count != 1
        or result.validation_step_call_count != 0
        or result.test_step_call_count != 0
        or result.diffusion_seed_hook_call_count != 1
        or result.max_abs_loss_difference > 1.0e-7
        or result.weighted_total_formula_absolute_difference > 1.0e-7
        or result.base_diffusion_valid_sample_count != 5
        or result.covalent_pair_prediction_valid_sample_count != 5
        or result.POST_geometry_valid_sample_count != 5
        or result.PRE_geometry_valid_sample_count != 0
        or result.covalent_pair_contrastive_valid_sample_count != 5
        or set(gradients) != required_gradients
        or any(
            not item.all_gradients_finite
            or item.nonzero_gradient_tensor_count <= 0
            or not math.isfinite(item.gradient_l2_norm)
            or item.gradient_l2_norm <= 0.0
            for item in gradients.values()
        )
        or set(deltas) != required_deltas
        or any(
            not item.all_parameters_finite
            or item.changed_parameter_tensor_count <= 0
            or not math.isfinite(item.parameter_delta_l2)
            or item.parameter_delta_l2 <= 0.0
            for item in deltas.values()
        )
        or not result.geometry_component_gradient.PRE_output_component_gradient_exact_zero
        or not result.geometry_component_gradient.POST_output_component_gradient_finite_nonzero
        or not result.all_parameters_finite_after_fit
        or result.checkpoint_file_changed
        or result.protected_sources_changed
        or not result.protected_state_unchanged
        or not result.raw_tree_unchanged
        or not result.original_batch_unchanged
        or not result.original_supervision_unchanged
        or not result.temporary_trainer_root_removed
        or result.persistent_output_created
        or result.GPU_used
        or result.network_used
        or not result.initial_joint_loss_candidate_validated_for_bounded_trainer_fit
        or result.geometry_weight_optimal
        or result.production_joint_loss_policy_finalized
        or result.full_training_authorized
        or not result.ready_for_gpt_review
        or not result.ready_for_five_epoch_train5_schedule_refresh_trainer_smoke
    ):
        _fail("RESULT_CONTRACT_INVALID")
    return result


def main() -> int:
    result = check_v1()
    gradient = {item.group_name: item for item in result.gradient_group_stats}
    delta = {item.group_name: item for item in result.parameter_delta_group_stats}
    print("batch001_train5_bounded_trainer_fit_smoke_built=true")
    print(f"repository_profile={result.repository_profile}")
    print(f"parameter_delta_snapshot_branch={result.parameter_delta_snapshot_branch}")
    print("parameter_delta_snapshot_captured_before_optimizer_step=true")
    print("formal_train_event_count=5")
    print(
        "initial_joint_loss_candidate_for_bounded_trainer_fit="
        "base1_pair1_postgeometry1_contrastive0.1"
    )
    print("initial_joint_loss_candidate_validated_for_bounded_trainer_fit=true")
    print("published_default_geometry_weight=0.0")
    print("published_default_modified=false")
    print("Trainer_fit_invoked=true")
    print("Trainer_fit_train_batch_count=1")
    print("Trainer_global_step=1")
    print("automatic_optimization=true")
    print("automatic_backward_call_count=1")
    print("Trainer_optimizer_step_count=1")
    print("zero_grad_lifecycle_call_count=1")
    print("DataLoader_executed=true")
    print("batch_transfer_pipeline_passed=true")
    print("validation_step_call_count=0")
    print("test_step_call_count=0")
    print(f"manual_trainer_max_abs_loss_difference={result.max_abs_loss_difference:.12g}")
    print(f"shared_pretrained_gradient_l2={gradient['SHARED_PRETRAINED'].gradient_l2_norm:.12g}")
    print(f"pair_head_gradient_l2={gradient['PAIR_HEAD'].gradient_l2_norm:.12g}")
    print(f"geometry_head_gradient_l2={gradient['GEOMETRY_HEAD'].gradient_l2_norm:.12g}")
    print(f"shared_pretrained_parameter_delta_l2={delta['SHARED_PRETRAINED'].parameter_delta_l2:.12g}")
    print(f"pair_head_parameter_delta_l2={delta['PAIR_HEAD'].parameter_delta_l2:.12g}")
    print(f"geometry_head_parameter_delta_l2={delta['GEOMETRY_HEAD'].parameter_delta_l2:.12g}")
    print("PRE_final_output_component_gradient_zero=true")
    print("POST_final_output_component_gradient_nonzero=true")
    print("checkpoint_file_changed=false")
    print("persistent_output_created=false")
    print("GPU_used=false")
    print("network_used=false")
    print("geometry_weight_optimal=false")
    print("production_joint_loss_policy_finalized=false")
    print("full_training_authorized=false")
    print("ready_for_gpt_review=true")
    print("ready_for_five_epoch_train5_schedule_refresh_trainer_smoke=true")
    print(
        "recommended_next_step_exactly="
        f"{result.recommended_next_step_exactly}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed checker for the formal train5 single backward/step smoke."""

from __future__ import annotations

import math
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as subject,
)


STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = REPOSITORY_ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
CHECK_ERROR = (
    "COVAPIE_BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_V1_"
    "CHECK_ERROR"
)


def _fail(reason: str) -> None:
    raise ValueError(f"{CHECK_ERROR}:{reason}")


def check_v1() -> dict[str, object]:
    result = subject.run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
        checkpoint_path=CHECKPOINT,
    )
    losses = dict(result.runtime_losses)
    published_weights = dict(result.published_default_loss_weights)
    smoke_weights = dict(result.smoke_only_loss_weights)
    migration = dict(result.migration_counts)
    architecture = dict(result.architecture)
    gradients = {item.group_name: item for item in result.gradient_group_stats}
    deltas = {
        item.group_name: item for item in result.parameter_delta_group_stats
    }
    optimizer = result.optimizer_metadata
    component = result.geometry_component_gradient
    if (
        result.implementation_status != "passed"
        or result.formal_train_event_ids
        != (
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
        )
        or result.DJK_train_event_count != 2
        or result.PTG_train_event_count != 3
        or result.validation_event_backward_count != 0
        or result.unresolved_event_backward_count != 0
        or result.non_target_component_event_backward_count != 0
        or result.scheduled_task_ids != (4, 4, 2, 0, 4)
        or result.ligand_node_count != 115
        or result.pocket_node_count != 578
        or result.pair_candidate_count != 690
        or result.pair_positive_count != 5
        or result.pair_negative_count != 685
        or result.diffusion_timesteps != (46, 279, 91, 52, 102)
    ):
        _fail("FORMAL_POPULATION_MODEL_INPUT_OR_FORWARD_INVALID")
    if (
        published_weights
        != {
            "base_diffusion": 1.0,
            "covalent_pair_prediction": 1.0,
            "pre_post_geometry": 0.0,
            "covalent_pair_contrastive": 0.1,
        }
        or smoke_weights
        != {
            "base_diffusion": 1.0,
            "covalent_pair_prediction": 1.0,
            "pre_post_geometry": 1.0,
            "covalent_pair_contrastive": 0.1,
        }
        or set(losses)
        != {
            "loss_base_diffusion",
            "loss_covalent_pair_prediction",
            "loss_pre_post_geometry",
            "loss_covalent_pair_contrastive",
            "loss_total",
        }
        or any(not math.isfinite(value) for value in losses.values())
        or result.base_diffusion_valid_sample_count != 5
        or result.covalent_pair_prediction_valid_sample_count != 5
        or result.pre_post_geometry_valid_sample_count != 5
        or result.covalent_pair_contrastive_valid_sample_count != 5
        or result.PRE_geometry_valid_sample_count != 0
        or result.geometry_contribution_to_smoke_total
        != losses["loss_pre_post_geometry"]
        or result.geometry_contribution_to_smoke_total <= 0.0
        or result.weighted_total_formula_absolute_difference > 1.0e-7
        or not math.isclose(
            losses["loss_total"],
            losses["loss_base_diffusion"]
            + losses["loss_covalent_pair_prediction"]
            + losses["loss_pre_post_geometry"]
            + 0.1 * losses["loss_covalent_pair_contrastive"],
            rel_tol=1.0e-7,
            abs_tol=1.0e-7,
        )
    ):
        _fail("SMOKE_WEIGHT_OR_LOSS_FORMULA_INVALID")
    if (
        result.checkpoint_sha256_before != subject.predecessor.CHECKPOINT_SHA256_V1
        or result.checkpoint_sha256_after != subject.predecessor.CHECKPOINT_SHA256_V1
        or result.bound_source_sha256 != subject.ALL_BOUND_SOURCE_SHA256_V1
        or migration
        != {
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
        _fail("BINDING_CHECKPOINT_MIGRATION_OR_ARCHITECTURE_INVALID")
    if (
        optimizer.optimizer_type != "AdamW"
        or optimizer.amsgrad is not True
        or optimizer.weight_decay != 1.0e-12
        or not math.isfinite(optimizer.model_lr)
        or optimizer.model_lr <= 0.0
        or optimizer.optimizer_param_group_lrs != (optimizer.model_lr,)
        or optimizer.model_parameter_tensor_count != 135
        or optimizer.optimizer_parameter_tensor_count != 135
        or optimizer.optimizer_unique_parameter_count != 135
        or optimizer.optimizer_parameter_set_exact is not True
        or result.backward_call_count != 1
        or result.optimizer_step_count != 1
    ):
        _fail("OPTIMIZER_OWNERSHIP_COVERAGE_OR_EXACTLY_ONCE_INVALID")
    if set(gradients) != {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    } or any(
        stats.gradient_tensor_count <= 0
        or stats.nonzero_gradient_tensor_count <= 0
        or stats.gradient_l2_norm <= 0.0
        or not math.isfinite(stats.gradient_l2_norm)
        or not math.isfinite(stats.gradient_max_abs)
        or stats.all_gradients_finite is not True
        for stats in gradients.values()
    ):
        _fail("GRADIENT_GROUP_ACCEPTANCE_INVALID")
    if (
        gradients["ALL_PARAMETERS"].parameter_tensor_count != 135
        or gradients["SHARED_PRETRAINED"].parameter_tensor_count != 116
        or gradients["TARGET_RESIDUE_CONDITIONING"].parameter_tensor_count != 1
        or component.final_weight_parameter_name
        != subject.GEOMETRY_FINAL_WEIGHT_NAME_V1
        or component.final_bias_parameter_name
        != subject.GEOMETRY_FINAL_BIAS_NAME_V1
        or component.PRE_weight_row_l2_norm != 0.0
        or component.PRE_bias_gradient_abs != 0.0
        or component.POST_weight_row_l2_norm <= 0.0
        or component.POST_bias_gradient_abs <= 0.0
        or component.PRE_output_component_gradient_exact_zero is not True
        or component.POST_output_component_gradient_finite_nonzero is not True
    ):
        _fail("POST_ONLY_GEOMETRY_COMPONENT_GRADIENT_INVALID")
    if set(deltas) != {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "NEW_COVAPIE",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    } or any(
        stats.changed_parameter_tensor_count <= 0
        or stats.parameter_delta_l2 <= 0.0
        or not math.isfinite(stats.parameter_delta_l2)
        or not math.isfinite(stats.parameter_delta_max_abs)
        or stats.all_parameters_finite is not True
        for stats in deltas.values()
    ):
        _fail("PARAMETER_DELTA_GROUP_ACCEPTANCE_INVALID")
    for group_name in (
        "SHARED_PRETRAINED",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    ):
        if (
            deltas[group_name].relative_delta_l2 is None
            or deltas[group_name].relative_delta_l2 <= 0.0
        ):
            _fail("RELATIVE_PARAMETER_DELTA_DIAGNOSTIC_INVALID")
    if (
        len(result.parameter_snapshots) != 135
        or len({item.name for item in result.parameter_snapshots}) != 135
        or any(not item.initial_finite for item in result.parameter_snapshots)
        or result.gradient_clipping_performed is not False
        or result.scheduler_step_performed is not False
        or result.all_parameters_finite_after_step is not True
        or result.in_memory_model_parameters_changed is not True
        or result.checkpoint_file_changed is not False
        or result.repository_predecessor_files_changed is not False
        or result.published_default_modified is not False
        or result.persistent_output_written is not False
        or result.checkpoint_saved is not False
        or result.model_saved is not False
        or result.Trainer_used is not False
        or result.GPU_used is not False
        or result.supervision_dataclass_reused is not True
    ):
        _fail("POST_STEP_OR_FILESYSTEM_SAFETY_INVALID")
    if (
        result.result_interpretation
        != "geometry_weight_candidate_validated_for_single_step_smoke"
        or result.geometry_weight_candidate_validated_for_single_step_smoke
        is not True
        or result.geometry_weight_optimal is not False
        or result.production_geometry_weight_finalized is not False
        or result.ready_for_bounded_batch001_train5_trainer_fit_smoke is not True
        or result.ready_for_full_training is not False
    ):
        _fail("READINESS_OR_INTERPRETATION_INVALID")
    report: dict[str, object] = {
        "batch001_train5_single_backward_optimizer_step_smoke_built": True,
        "formal_train_event_count": len(result.formal_train_event_ids),
        "DJK_train_event_count": result.DJK_train_event_count,
        "PTG_train_event_count": result.PTG_train_event_count,
        "validation_event_backward_count": result.validation_event_backward_count,
        "unresolved_event_backward_count": result.unresolved_event_backward_count,
        "non_target_component_event_backward_count": (
            result.non_target_component_event_backward_count
        ),
        "scheduled_task_tuple": result.scheduled_task_ids,
        "ligand_node_count": result.ligand_node_count,
        "pocket_node_count": result.pocket_node_count,
        "pair_candidate_count": result.pair_candidate_count,
        "pair_positive_count": result.pair_positive_count,
        "pair_negative_count": result.pair_negative_count,
        "checkpoint_sha256": result.checkpoint_sha256_before,
        "checkpoint_key_count": migration["checkpoint_key_count"],
        "target_model_key_count": migration["target_model_key_count"],
        "shared_checkpoint_key_count": migration["shared_key_count"],
        "target_only_key_count": migration["target_only_key_count"],
        "checkpoint_only_key_count": migration["checkpoint_only_key_count"],
        "shared_shape_mismatch_count": migration["shared_shape_mismatch_count"],
        "published_default_geometry_weight": published_weights["pre_post_geometry"],
        "smoke_geometry_weight": smoke_weights["pre_post_geometry"],
        **losses,
        "geometry_contribution_to_smoke_total": (
            result.geometry_contribution_to_smoke_total
        ),
        "base_diffusion_valid_sample_count": 5,
        "pair_prediction_valid_sample_count": 5,
        "POST_geometry_valid_sample_count": 5,
        "pair_contrastive_valid_sample_count": 5,
        "PRE_geometry_valid_sample_count": 0,
        "optimizer_type": optimizer.optimizer_type,
        "model_lr": optimizer.model_lr,
        "optimizer_param_group_lrs": optimizer.optimizer_param_group_lrs,
        "model_parameter_tensor_count": optimizer.model_parameter_tensor_count,
        "optimizer_parameter_tensor_count": optimizer.optimizer_parameter_tensor_count,
        "optimizer_unique_parameter_count": optimizer.optimizer_unique_parameter_count,
        "backward_call_count": result.backward_call_count,
        "optimizer_step_count": result.optimizer_step_count,
        "PRE_output_component_gradient_exact_zero": (
            component.PRE_output_component_gradient_exact_zero
        ),
        "POST_output_component_gradient_finite_nonzero": (
            component.POST_output_component_gradient_finite_nonzero
        ),
        "POST_final_weight_row_gradient_l2": component.POST_weight_row_l2_norm,
        "POST_final_bias_gradient_abs": component.POST_bias_gradient_abs,
    }
    for group_name, stats in gradients.items():
        prefix = group_name.lower()
        report[f"{prefix}_gradient_tensor_count"] = stats.gradient_tensor_count
        report[f"{prefix}_nonzero_gradient_tensor_count"] = (
            stats.nonzero_gradient_tensor_count
        )
        report[f"{prefix}_gradient_l2_norm"] = stats.gradient_l2_norm
        report[f"{prefix}_gradient_max_abs"] = stats.gradient_max_abs
    for group_name, stats in deltas.items():
        prefix = group_name.lower()
        report[f"{prefix}_changed_parameter_tensor_count"] = (
            stats.changed_parameter_tensor_count
        )
        report[f"{prefix}_parameter_delta_l2"] = stats.parameter_delta_l2
        report[f"{prefix}_parameter_delta_max_abs"] = stats.parameter_delta_max_abs
        report[f"{prefix}_relative_delta_l2"] = stats.relative_delta_l2
    report.update({
        "all_parameters_finite_after_step": True,
        "gradient_clipping_performed": False,
        "checkpoint_file_changed": False,
        "repository_predecessor_files_changed": False,
        "published_default_modified": False,
        "persistent_output_written": False,
        "Trainer_used": False,
        "GPU_used": False,
        "geometry_weight_candidate_validated_for_single_step_smoke": True,
        "geometry_weight_optimal": False,
        "production_geometry_weight_finalized": False,
        "ready_for_bounded_batch001_train5_trainer_fit_smoke": True,
        "ready_for_full_training": False,
        "real_smoke_elapsed_seconds": result.elapsed_seconds,
    })
    return report


def main() -> int:
    result = check_v1()
    for name, value in result.items():
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{name}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

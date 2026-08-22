"""One real backward and optimizer step on the formal batch-001 train5.

This bounded CPU smoke consumes the published admission-aware forward/loss
predecessor and the existing Current11 model, loss, migration, and optimizer
owners.  It performs one fresh-model forward, exactly one total-loss backward,
and exactly one optimizer step.  It never persists model state.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import math
from pathlib import Path
import time
from typing import Mapping, NoReturn, Sequence

import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as predecessor,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossOutputV1,
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_ERROR_V1",
    "SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1",
    "CovapieBatch001Train5GradientGroupStatsV1",
    "CovapieBatch001Train5ParameterDeltaGroupStatsV1",
    "CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1",
    "verify_covapie_batch001_train5_single_backward_predecessor_source_v1",
    "run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1",
)


BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_ERROR_V1 = (
    "COVAPIE_BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_V1_ERROR"
)
SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1 = CovapieCurrent11LossWeightsV1(
    base_diffusion=1.0,
    covalent_pair_prediction=1.0,
    pre_post_geometry=1.0,
    covalent_pair_contrastive=0.1,
)

PREDECESSOR_SOURCE_RELATIVE_PATH_V1 = Path(
    "src/covalent_ext/"
    "covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py"
)
PREDECESSOR_SOURCE_SHA256_V1 = (
    "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21"
)
PREDECESSOR_CHECKER_RELATIVE_PATH_V1 = Path(
    "scripts/"
    "check_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py"
)
PREDECESSOR_CHECKER_SHA256_V1 = (
    "2e4f4c07c399adeb5c8e570b0a475367094ffda1102abd5f085a767bbf971ab2"
)
PREDECESSOR_TEST_RELATIVE_PATH_V1 = Path(
    "tests/"
    "test_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py"
)
PREDECESSOR_TEST_SHA256_V1 = (
    "9b830ecd2a6351dd5a3735f3f105680e1e27eb651f88eac0f38b58afd5c8771f"
)
BOUND_OWNER_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "d3d21b920785f791652cb456465a8bb375a09cdf0e24e5e84415b01f82cd6485",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "5bf91b3af56ec0e5c2dec3ebb13e56695ca74c17bbbbb65f35e8d9249d6fc60f",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
    ),
)
BOUND_PREDECESSOR_SHA256_V1 = (
    (str(PREDECESSOR_SOURCE_RELATIVE_PATH_V1), PREDECESSOR_SOURCE_SHA256_V1),
    (str(PREDECESSOR_CHECKER_RELATIVE_PATH_V1), PREDECESSOR_CHECKER_SHA256_V1),
    (str(PREDECESSOR_TEST_RELATIVE_PATH_V1), PREDECESSOR_TEST_SHA256_V1),
)
ALL_BOUND_SOURCE_SHA256_V1 = BOUND_PREDECESSOR_SHA256_V1 + BOUND_OWNER_SHA256_V1

TARGET_RESIDUE_PARAMETER_NAME_V1 = (
    "ddpm.dynamics.target_residue_atom_condition_embedding"
)
ROLE_TASK_MASK_ANCHOR_PREFIXES_V1 = (
    "covapie_current11_auxiliary_model_v1.role_embedding.",
    "covapie_current11_auxiliary_model_v1.task_embedding.",
    "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
    "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
)
PAIR_HEAD_PREFIXES_V1 = (
    "covapie_current11_auxiliary_model_v1.pair_embedding.",
    "covapie_current11_auxiliary_model_v1.pair_logit.",
)
GEOMETRY_HEAD_PREFIX_V1 = (
    "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
)
GEOMETRY_FINAL_WEIGHT_NAME_V1 = GEOMETRY_HEAD_PREFIX_V1 + "2.weight"
GEOMETRY_FINAL_BIAS_NAME_V1 = GEOMETRY_HEAD_PREFIX_V1 + "2.bias"

LOSS_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
LOSS_RELATIVE_TOLERANCE_V1 = 1.0e-7

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001Train5ParameterSnapshotV1:
    name: str
    shape: tuple[int, ...]
    requires_grad: bool
    initial_finite: bool
    initial_l2_norm: float


@dataclass(frozen=True)
class CovapieBatch001Train5GradientGroupStatsV1:
    group_name: str
    parameter_tensor_count: int
    gradient_tensor_count: int
    nonzero_gradient_tensor_count: int
    gradient_l2_norm: float
    gradient_max_abs: float
    all_gradients_finite: bool


@dataclass(frozen=True)
class CovapieBatch001Train5ParameterDeltaGroupStatsV1:
    group_name: str
    parameter_tensor_count: int
    changed_parameter_tensor_count: int
    pre_step_parameter_l2: float
    parameter_delta_l2: float
    parameter_delta_max_abs: float
    relative_delta_l2: float | None
    all_parameters_finite: bool


@dataclass(frozen=True)
class CovapieBatch001Train5GeometryComponentGradientV1:
    final_weight_parameter_name: str
    final_bias_parameter_name: str
    PRE_weight_row_l2_norm: float
    POST_weight_row_l2_norm: float
    PRE_bias_gradient_abs: float
    POST_bias_gradient_abs: float
    PRE_output_component_gradient_exact_zero: bool
    POST_output_component_gradient_finite_nonzero: bool


@dataclass(frozen=True)
class CovapieBatch001Train5OptimizerMetadataV1:
    optimizer_type: str
    amsgrad: bool
    weight_decay: float
    model_lr: float
    optimizer_param_group_lrs: tuple[float, ...]
    model_parameter_tensor_count: int
    optimizer_parameter_tensor_count: int
    optimizer_unique_parameter_count: int
    optimizer_parameter_set_exact: bool


@dataclass(frozen=True)
class CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1:
    implementation_status: str
    result_interpretation: str
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_unresolved_event_ids: tuple[str, ...]
    non_target_component_event_ids: tuple[str, ...]
    DJK_train_event_count: int
    PTG_train_event_count: int
    validation_event_backward_count: int
    unresolved_event_backward_count: int
    non_target_component_event_backward_count: int
    scheduled_task_ids: tuple[int, ...]
    ligand_node_count: int
    pocket_node_count: int
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    diffusion_timesteps: tuple[int, ...]
    published_default_loss_weights: tuple[tuple[str, float], ...]
    smoke_only_loss_weights: tuple[tuple[str, float], ...]
    runtime_losses: tuple[tuple[str, float], ...]
    weighted_total_formula_value: float
    weighted_total_formula_absolute_difference: float
    geometry_contribution_to_smoke_total: float
    base_diffusion_valid_sample_count: int
    covalent_pair_prediction_valid_sample_count: int
    pre_post_geometry_valid_sample_count: int
    covalent_pair_contrastive_valid_sample_count: int
    PRE_geometry_valid_sample_count: int
    parameter_snapshots: tuple[CovapieBatch001Train5ParameterSnapshotV1, ...]
    gradient_group_stats: tuple[CovapieBatch001Train5GradientGroupStatsV1, ...]
    parameter_delta_group_stats: tuple[
        CovapieBatch001Train5ParameterDeltaGroupStatsV1, ...
    ]
    geometry_component_gradient: CovapieBatch001Train5GeometryComponentGradientV1
    optimizer_metadata: CovapieBatch001Train5OptimizerMetadataV1
    migration_counts: tuple[tuple[str, int], ...]
    migration_missing_keys: tuple[str, ...]
    migration_unexpected_keys: tuple[str, ...]
    architecture: tuple[tuple[str, object], ...]
    bound_source_sha256: tuple[tuple[str, str], ...]
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    backward_call_count: int
    optimizer_step_count: int
    gradient_clipping_performed: bool
    scheduler_step_performed: bool
    all_parameters_finite_after_step: bool
    in_memory_model_parameters_changed: bool
    checkpoint_file_changed: bool
    repository_predecessor_files_changed: bool
    published_default_modified: bool
    persistent_output_written: bool
    checkpoint_saved: bool
    model_saved: bool
    Trainer_used: bool
    GPU_used: bool
    supervision_dataclass_reused: bool
    elapsed_seconds: float
    geometry_weight_candidate_validated_for_single_step_smoke: bool
    geometry_weight_optimal: bool
    production_geometry_weight_finalized: bool
    ready_for_bounded_batch001_train5_trainer_fit_smoke: bool
    ready_for_full_training: bool


class _SmokeInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class _ExactlyOnceExecutionGuard:
    def __init__(self) -> None:
        self.backward_call_count = 0
        self.optimizer_step_count = 0

    def claim_backward(self) -> None:
        if self.backward_call_count != 0:
            _fail("SECOND_BACKWARD_ATTEMPT_REJECTED")
        self.backward_call_count = 1

    def claim_optimizer_step(self) -> None:
        if self.optimizer_step_count != 0:
            _fail("SECOND_OPTIMIZER_STEP_ATTEMPT_REJECTED")
        self.optimizer_step_count = 1


def _fail(reason: str) -> NoReturn:
    raise _SmokeInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_ERROR_V1
    ):
        raise error
    if isinstance(error, (_SmokeInvariantError, predecessor._SmokeInvariantError)):
        reason = error.reason
    else:
        reason = "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_ERROR_V1}:"
        f"{reason}"
    ) from error


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if (
        type(path) is not _PATH_TYPE
        or not path.is_absolute()
        or not path.is_dir()
        or path.is_symlink()
    ):
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    if (
        type(path) is not _PATH_TYPE
        or not path.is_absolute()
        or not path.is_file()
        or path.is_symlink()
    ):
        _fail("BOUND_FILE_NOT_SAFE_REGULAR_FILE")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_sha(path: Path, expected: str, reason: str) -> str:
    actual = _sha256_file(path)
    if actual != expected:
        _fail(reason)
    return actual


def _require_unchanged_evidence(before: object, after: object, reason: str) -> None:
    if before != after:
        _fail(reason)


def verify_covapie_batch001_train5_single_backward_predecessor_source_v1(
    *, predecessor_source_path: Path,
) -> str:
    """Verify the exact published train5 forward/loss predecessor source."""

    try:
        return _verify_sha(
            predecessor_source_path,
            PREDECESSOR_SOURCE_SHA256_V1,
            "PREDECESSOR_SOURCE_SHA256_MISMATCH",
        )
    except BaseException as error:
        _public_error(error)


def _verify_bound_sources(repository_root: Path) -> tuple[tuple[str, str], ...]:
    verified = tuple(
        (
            relative,
            _verify_sha(
                repository_root / relative,
                expected,
                "BOUND_SOURCE_SHA256_MISMATCH",
            ),
        )
        for relative, expected in ALL_BOUND_SOURCE_SHA256_V1
    )
    if verified != ALL_BOUND_SOURCE_SHA256_V1:
        _fail("BOUND_SOURCE_SET_INVALID")
    predecessor._verify_bound_owners(repository_root)
    return verified


def _loss_weights_tuple(
    weights: CovapieCurrent11LossWeightsV1,
) -> tuple[tuple[str, float], ...]:
    return (
        ("base_diffusion", float(weights.base_diffusion)),
        ("covalent_pair_prediction", float(weights.covalent_pair_prediction)),
        ("pre_post_geometry", float(weights.pre_post_geometry)),
        ("covalent_pair_contrastive", float(weights.covalent_pair_contrastive)),
    )


def _validate_loss_weight_policy(
    smoke_loss_weights: object,
    *,
    published_default: CovapieCurrent11LossWeightsV1 | None = None,
) -> tuple[CovapieCurrent11LossWeightsV1, CovapieCurrent11LossWeightsV1]:
    default = CovapieCurrent11LossWeightsV1() if published_default is None else published_default
    expected_default = CovapieCurrent11LossWeightsV1(
        base_diffusion=1.0,
        covalent_pair_prediction=1.0,
        pre_post_geometry=0.0,
        covalent_pair_contrastive=0.1,
    )
    candidate = (
        SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
        if smoke_loss_weights is None
        else smoke_loss_weights
    )
    if default != expected_default:
        _fail("PUBLISHED_DEFAULT_LOSS_WEIGHTS_MUTATED")
    if (
        not isinstance(candidate, CovapieCurrent11LossWeightsV1)
        or candidate != SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
    ):
        _fail("SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_INVALID")
    return default, candidate


def _validate_finite_loss_contract(
    losses: CovapieCurrent11LossOutputV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    weights: CovapieCurrent11LossWeightsV1,
) -> tuple[tuple[tuple[str, float], ...], float, float]:
    loss_tensors = (
        ("loss_base_diffusion", losses.loss_base_diffusion),
        ("loss_covalent_pair_prediction", losses.loss_covalent_pair_prediction),
        ("loss_pre_post_geometry", losses.loss_pre_post_geometry),
        ("loss_covalent_pair_contrastive", losses.loss_covalent_pair_contrastive),
        ("loss_total", losses.loss_total),
    )
    if any(
        value.ndim != 0 or not bool(torch.isfinite(value).item())
        for unused, value in loss_tensors
    ):
        _fail("NON_FINITE_OR_NON_SCALAR_LOSS")
    if (
        losses.base_diffusion_valid_sample_count != 5
        or losses.covalent_pair_prediction_valid_sample_count != 5
        or losses.pre_post_geometry_valid_sample_count != 5
        or losses.covalent_pair_contrastive_valid_sample_count != 5
        or int(supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()) != 0
        or int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()) != 5
    ):
        _fail("LOSS_VALID_SAMPLE_COUNTS_INVALID")
    formula = (
        float(weights.base_diffusion) * losses.loss_base_diffusion
        + float(weights.covalent_pair_prediction)
        * losses.loss_covalent_pair_prediction
        + float(weights.pre_post_geometry) * losses.loss_pre_post_geometry
        + float(weights.covalent_pair_contrastive)
        * losses.loss_covalent_pair_contrastive
    )
    difference = float(torch.abs(losses.loss_total - formula).detach().item())
    if not bool(
        torch.isclose(
            losses.loss_total,
            formula,
            atol=LOSS_ABSOLUTE_TOLERANCE_V1,
            rtol=LOSS_RELATIVE_TOLERANCE_V1,
        ).item()
    ):
        _fail("WEIGHTED_TOTAL_LOSS_FORMULA_MISMATCH")
    geometry_contribution = float(
        (float(weights.pre_post_geometry) * losses.loss_pre_post_geometry)
        .detach()
        .item()
    )
    geometry_loss = float(losses.loss_pre_post_geometry.detach().item())
    if geometry_contribution != geometry_loss or geometry_contribution <= 0.0:
        _fail("GEOMETRY_CONTRIBUTION_TO_SMOKE_TOTAL_INVALID")
    return (
        tuple((name, float(value.detach().item())) for name, value in loss_tensors),
        float(formula.detach().item()),
        difference,
    )


def _parameter_snapshot(
    named_parameters: Mapping[str, nn.Parameter],
) -> tuple[
    dict[str, torch.Tensor],
    tuple[CovapieBatch001Train5ParameterSnapshotV1, ...],
]:
    if not named_parameters:
        _fail("MODEL_PARAMETER_SET_EMPTY")
    tensors: dict[str, torch.Tensor] = {}
    observations: list[CovapieBatch001Train5ParameterSnapshotV1] = []
    for name, parameter in named_parameters.items():
        finite = bool(torch.isfinite(parameter.detach()).all().item())
        norm = float(torch.linalg.vector_norm(parameter.detach().double()).item())
        if not finite or not math.isfinite(norm):
            _fail("NON_FINITE_INITIAL_PARAMETER")
        tensors[name] = parameter.detach().clone()
        observations.append(CovapieBatch001Train5ParameterSnapshotV1(
            name=name,
            shape=tuple(parameter.shape),
            requires_grad=parameter.requires_grad,
            initial_finite=finite,
            initial_l2_norm=norm,
        ))
    return tensors, tuple(observations)


def _validate_optimizer_parameter_coverage(
    model: nn.Module,
    optimizer: object,
) -> CovapieBatch001Train5OptimizerMetadataV1:
    model_parameters = list(model.parameters())
    model_ids = [id(parameter) for parameter in model_parameters]
    if not isinstance(optimizer, torch.optim.AdamW):
        _fail("OPTIMIZER_TYPE_INVALID")
    optimizer_parameters = [
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    optimizer_ids = [id(parameter) for parameter in optimizer_parameters]
    unique_ids = set(optimizer_ids)
    exact = (
        len(model_ids) == len(set(model_ids))
        and len(optimizer_ids) == len(unique_ids)
        and unique_ids == set(model_ids)
    )
    if not exact:
        _fail("OPTIMIZER_PARAMETER_SET_NOT_EXACT")
    lrs = tuple(float(group["lr"]) for group in optimizer.param_groups)
    amsgrad_values = tuple(group.get("amsgrad") for group in optimizer.param_groups)
    weight_decays = tuple(float(group["weight_decay"]) for group in optimizer.param_groups)
    model_lr = getattr(model, "lr", None)
    if (
        type(model_lr) not in (int, float)
        or type(model_lr) is bool
        or not math.isfinite(float(model_lr))
        or float(model_lr) <= 0.0
        or not lrs
        or any(not math.isfinite(value) or value <= 0.0 for value in lrs)
        or any(value != float(model_lr) for value in lrs)
        or any(value is not True for value in amsgrad_values)
        or any(value != 1.0e-12 for value in weight_decays)
    ):
        _fail("OPTIMIZER_HYPERPARAMETER_OWNERSHIP_INVALID")
    return CovapieBatch001Train5OptimizerMetadataV1(
        optimizer_type=type(optimizer).__name__,
        amsgrad=True,
        weight_decay=1.0e-12,
        model_lr=float(model_lr),
        optimizer_param_group_lrs=lrs,
        model_parameter_tensor_count=len(model_parameters),
        optimizer_parameter_tensor_count=len(optimizer_parameters),
        optimizer_unique_parameter_count=len(unique_ids),
        optimizer_parameter_set_exact=True,
    )


def _names_with_prefixes(
    named_parameters: Mapping[str, nn.Parameter],
    prefixes: str | tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        name for name in named_parameters if name.startswith(prefixes)
    )


def _gradient_group_stats(
    *,
    group_name: str,
    named_parameters: Mapping[str, nn.Parameter],
    parameter_names: Sequence[str],
) -> CovapieBatch001Train5GradientGroupStatsV1:
    names = tuple(parameter_names)
    if not names or len(names) != len(set(names)) or any(
        name not in named_parameters for name in names
    ):
        _fail("GRADIENT_GROUP_PARAMETER_SET_INVALID")
    gradients = [named_parameters[name].grad for name in names]
    existing = [gradient for gradient in gradients if gradient is not None]
    finite = all(bool(torch.isfinite(gradient).all().item()) for gradient in existing)
    nonzero = [
        gradient for gradient in existing
        if bool(torch.count_nonzero(gradient).item())
    ]
    squared_norm = sum(
        float(torch.sum(gradient.detach().double().square()).item())
        for gradient in existing
    )
    maximum = max(
        (float(gradient.detach().abs().max().item()) for gradient in existing),
        default=0.0,
    )
    return CovapieBatch001Train5GradientGroupStatsV1(
        group_name=group_name,
        parameter_tensor_count=len(names),
        gradient_tensor_count=len(existing),
        nonzero_gradient_tensor_count=len(nonzero),
        gradient_l2_norm=math.sqrt(squared_norm),
        gradient_max_abs=maximum,
        all_gradients_finite=finite,
    )


def _require_gradient_gate(
    stats: CovapieBatch001Train5GradientGroupStatsV1,
    *,
    reason: str,
) -> None:
    if (
        stats.gradient_tensor_count <= 0
        or stats.nonzero_gradient_tensor_count <= 0
        or not stats.all_gradients_finite
        or not math.isfinite(stats.gradient_l2_norm)
        or stats.gradient_l2_norm <= 0.0
        or not math.isfinite(stats.gradient_max_abs)
    ):
        _fail(reason)


def _geometry_component_gradient(
    named_parameters: Mapping[str, nn.Parameter],
) -> CovapieBatch001Train5GeometryComponentGradientV1:
    weight = named_parameters.get(GEOMETRY_FINAL_WEIGHT_NAME_V1)
    bias = named_parameters.get(GEOMETRY_FINAL_BIAS_NAME_V1)
    if (
        weight is None
        or bias is None
        or weight.shape[0] != 2
        or bias.shape != (2,)
        or weight.grad is None
        or bias.grad is None
        or weight.grad.shape != weight.shape
        or bias.grad.shape != bias.shape
    ):
        _fail("GEOMETRY_FINAL_LINEAR_COMPONENT_STRUCTURE_INVALID")
    gradients = (weight.grad, bias.grad)
    if any(not bool(torch.isfinite(value).all().item()) for value in gradients):
        _fail("GEOMETRY_FINAL_LINEAR_COMPONENT_GRADIENT_NON_FINITE")
    pre_zero = (
        int(torch.count_nonzero(weight.grad[0]).item()) == 0
        and int(torch.count_nonzero(bias.grad[0]).item()) == 0
    )
    post_nonzero = (
        int(torch.count_nonzero(weight.grad[1]).item()) > 0
        and int(torch.count_nonzero(bias.grad[1]).item()) > 0
    )
    if not pre_zero:
        _fail("PRE_OUTPUT_COMPONENT_GRADIENT_NOT_EXACT_ZERO")
    if not post_nonzero:
        _fail("POST_OUTPUT_COMPONENT_GRADIENT_NOT_NONZERO")
    return CovapieBatch001Train5GeometryComponentGradientV1(
        final_weight_parameter_name=GEOMETRY_FINAL_WEIGHT_NAME_V1,
        final_bias_parameter_name=GEOMETRY_FINAL_BIAS_NAME_V1,
        PRE_weight_row_l2_norm=float(
            torch.linalg.vector_norm(weight.grad[0].detach().double()).item()
        ),
        POST_weight_row_l2_norm=float(
            torch.linalg.vector_norm(weight.grad[1].detach().double()).item()
        ),
        PRE_bias_gradient_abs=float(bias.grad[0].detach().abs().item()),
        POST_bias_gradient_abs=float(bias.grad[1].detach().abs().item()),
        PRE_output_component_gradient_exact_zero=True,
        POST_output_component_gradient_finite_nonzero=True,
    )


def _parameter_delta_group_stats(
    *,
    group_name: str,
    named_parameters: Mapping[str, nn.Parameter],
    parameter_names: Sequence[str],
    before: Mapping[str, torch.Tensor],
) -> CovapieBatch001Train5ParameterDeltaGroupStatsV1:
    names = tuple(parameter_names)
    if not names or len(names) != len(set(names)) or any(
        name not in named_parameters or name not in before for name in names
    ):
        _fail("PARAMETER_DELTA_GROUP_SET_INVALID")
    changed = 0
    parameter_squared = 0.0
    delta_squared = 0.0
    delta_maximum = 0.0
    all_finite = True
    for name in names:
        after = named_parameters[name].detach()
        initial = before[name]
        all_finite = all_finite and bool(torch.isfinite(after).all().item())
        delta = after - initial
        if not torch.equal(after, initial):
            changed += 1
        parameter_squared += float(torch.sum(initial.double().square()).item())
        delta_squared += float(torch.sum(delta.double().square()).item())
        if delta.numel():
            delta_maximum = max(delta_maximum, float(delta.abs().max().item()))
    parameter_l2 = math.sqrt(parameter_squared)
    delta_l2 = math.sqrt(delta_squared)
    relative = delta_l2 / parameter_l2 if parameter_l2 > 0.0 else None
    return CovapieBatch001Train5ParameterDeltaGroupStatsV1(
        group_name=group_name,
        parameter_tensor_count=len(names),
        changed_parameter_tensor_count=changed,
        pre_step_parameter_l2=parameter_l2,
        parameter_delta_l2=delta_l2,
        parameter_delta_max_abs=delta_maximum,
        relative_delta_l2=relative,
        all_parameters_finite=all_finite,
    )


def _require_delta_gate(
    stats: CovapieBatch001Train5ParameterDeltaGroupStatsV1,
    *,
    reason: str,
) -> None:
    if (
        stats.changed_parameter_tensor_count <= 0
        or not stats.all_parameters_finite
        or not math.isfinite(stats.parameter_delta_l2)
        or stats.parameter_delta_l2 <= 0.0
        or not math.isfinite(stats.parameter_delta_max_abs)
    ):
        _fail(reason)


def _assert_cpu_tensors(value: object) -> None:
    if isinstance(value, torch.Tensor):
        if value.device.type != "cpu":
            _fail("NON_CPU_TENSOR_DETECTED")
    elif type(value) is dict:
        for item in value.values():
            _assert_cpu_tensors(item)
    elif isinstance(value, CovapieCurrent11TrainingSupervisionTensorsV1):
        for field in fields(value):
            _assert_cpu_tensors(getattr(value, field.name))


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.shape != right.shape or left.dtype != right.dtype:
        return False
    if left.is_floating_point() or left.is_complex():
        return bool(torch.equal(torch.isnan(left), torch.isnan(right))) and bool(
            torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
        )
    return bool(torch.equal(left, right))


def _run_single_step_impl(
    *,
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
    checkpoint_path: Path,
    requested_sample_identities: object,
    smoke_loss_weights: object,
) -> CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1:
    started = time.perf_counter()
    bound_before = _verify_bound_sources(repository_root)
    checkpoint_before = predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
        checkpoint_path=checkpoint_path
    )
    published_default, candidate_weights = _validate_loss_weight_policy(
        smoke_loss_weights
    )
    prepared = predecessor._prepare_train5_batch(
        repository_root=repository_root,
        cache_root=cache_root,
        requested_sample_identities=requested_sample_identities,
    )
    if (
        prepared.sample_identities != predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or prepared.authority.DJK_train_event_count != 2
        or prepared.authority.PTG_train_event_count != 3
        or prepared.scheduled_task_ids != (4, 4, 2, 0, 4)
        or not prepared.static_five_mask_audit_passed
    ):
        _fail("FORMAL_TRAIN5_POPULATION_OR_SCHEDULE_INVALID")
    ligand_counts = tuple(
        len(record.ligand_retained_heavy_atoms)
        for record in prepared.structural_records
    )
    pocket_counts = tuple(
        len(record.pocket_retained_heavy_atoms)
        for record in prepared.structural_records
    )
    supervision = prepared.supervision
    if (
        ligand_counts != predecessor.EXPECTED_LIGAND_COUNTS_V1
        or pocket_counts != predecessor.EXPECTED_POCKET_COUNTS_V1
        or sum(ligand_counts) != 115
        or sum(pocket_counts) != 578
        or len(supervision.pair_candidate_batch_index) != 690
        or int(supervision.pair_candidate_is_positive.sum().item()) != 5
        or int(supervision.pair_candidate_is_negative.sum().item()) != 685
        or len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or not bool(supervision.sample_training_admitted.all().item())
    ):
        _fail("MODEL_INPUT_POPULATION_OR_SUPERVISION_INVALID")
    _assert_cpu_tensors(prepared.model_input_batch)
    _assert_cpu_tensors(supervision)
    supervision_before = {
        field.name: getattr(supervision, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    model_input_before = {
        name: value.clone()
        for name, value in prepared.model_input_batch.items()
        if isinstance(value, torch.Tensor)
    }

    with predecessor._repository_import_path(repository_root):
        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_checkpoint_migration_v1 as checkpoint_owner,
        )
        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
            as instantiation_owner,
        )
        from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: PLC0415
            run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
        )

    checkpoint_payload = checkpoint_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    checkpoint_state = checkpoint_payload.get("state_dict")
    guard = _ExactlyOnceExecutionGuard()
    with predecessor._deterministic_cpu_context():
        torch.random.default_generator.manual_seed(
            predecessor.MODEL_INITIALIZATION_SEED_V1
        )
        model = instantiation_owner._instantiate_current11_model_v1(
            repo_root=repository_root,
            state_root=state_root,
            device="cpu",
        )
        migration = checkpoint_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model,
            checkpoint_state_dict=checkpoint_state,
        )
        migration_names = (
            "checkpoint_key_count",
            "target_model_key_count",
            "shared_key_count",
            "target_only_key_count",
            "checkpoint_only_key_count",
            "shared_shape_mismatch_count",
            "shared_checkpoint_tensor_equality_count",
        )
        migration_counts = tuple(
            (name, int(migration[name])) for name in migration_names
        )
        if dict(migration_counts) != {
            "checkpoint_key_count": 122,
            "target_model_key_count": 141,
            "shared_key_count": 122,
            "target_only_key_count": 19,
            "checkpoint_only_key_count": 0,
            "shared_shape_mismatch_count": 0,
            "shared_checkpoint_tensor_equality_count": 122,
        } or migration["migration_missing_keys"] or migration["migration_unexpected_keys"]:
            _fail("CHECKPOINT_MIGRATION_COUNTS_OR_STRICTNESS_INVALID")
        dynamics = model.ddpm.dynamics
        architecture = (
            ("device", "cpu"),
            ("mode", model.mode),
            ("pocket_representation", model.pocket_representation),
            ("atom_nf", model.atom_nf),
            ("target_residue_atom_conditioning", dynamics.target_residue_atom_conditioning),
            ("virtual_nodes", model.virtual_nodes),
            ("loss_type", model.ddpm.loss_type),
            ("joint_nf", model.covapie_current11_auxiliary_model_v1.joint_nf),
            ("hidden_nf", dynamics.egnn.hidden_nf),
            ("egnn_layers", dynamics.egnn.n_layers),
        )
        if dict(architecture) != {
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
        } or any(parameter.device.type != "cpu" for parameter in model.parameters()):
            _fail("REAL_CPU_ARCHITECTURE_INVALID")
        if model.covapie_current11_loss_weights != published_default:
            _fail("MODEL_PUBLISHED_DEFAULT_LOSS_WEIGHTS_MUTATED")
        model.train()
        ligand, pocket = model.get_ligand_and_pocket(prepared.model_input_batch)
        indicator = supervision.target_residue_reactive_atom_mask[:, 0]
        role_delta = model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=ligand["mask"],
        )
        torch.random.default_generator.manual_seed(
            predecessor.DIFFUSION_FORWARD_SEED_V1
        )
        trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
            ddpm=model.ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
            pocket_target_residue_atom_condition_indicator=indicator,
        )
        model_output = model.covapie_current11_auxiliary_model_v1(
            diffusion_trace=trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )
        forward_tensors = (
            model_output.diffusion_epsilon_prediction_ligand,
            model_output.denoised_ligand_xh,
            model_output.ligand_node_hidden,
            model_output.pocket_node_hidden,
            model_output.role_mask_anchor_hidden_delta,
            model_output.pair_logits,
            model_output.pair_embeddings,
            model_output.pre_post_geometry_predictions_angstrom,
        )
        if (
            tuple(model_output.diffusion_timestep_int.tolist())
            != (46, 279, 91, 52, 102)
            or tuple(model_output.pair_logits.shape) != (690,)
            or tuple(model_output.pre_post_geometry_predictions_angstrom.shape)
            != (690, 2)
            or any(not bool(value.isfinite().all().item()) for value in forward_tensors)
        ):
            _fail("REAL_FORWARD_OUTPUT_INVALID")
        losses = compute_covapie_current11_training_losses_v1(
            model_output=model_output,
            supervision=supervision,
            diffusion_trace=trace,
            loss_weights=candidate_weights,
            pair_contrastive_temperature=1.0,
            geometry_smooth_l1_beta=1.0,
        )
        runtime_losses, formula_value, formula_difference = _validate_finite_loss_contract(
            losses,
            supervision,
            candidate_weights,
        )
        named_parameters = dict(model.named_parameters())
        before_parameters, parameter_snapshots = _parameter_snapshot(named_parameters)
        shared_names = tuple(name for name in named_parameters if name in checkpoint_state)
        new_names = tuple(sorted(
            set(migration["target_only_exact_keys"])
            | set(migration["target_only_auxiliary_keys"])
        ))
        target_names = (TARGET_RESIDUE_PARAMETER_NAME_V1,)
        conditioner_names = _names_with_prefixes(
            named_parameters, ROLE_TASK_MASK_ANCHOR_PREFIXES_V1
        )
        pair_names = _names_with_prefixes(named_parameters, PAIR_HEAD_PREFIXES_V1)
        geometry_names = _names_with_prefixes(named_parameters, GEOMETRY_HEAD_PREFIX_V1)
        all_names = tuple(named_parameters)
        if (
            len(shared_names) != 116
            or len(new_names) != 19
            or set(shared_names) & set(new_names)
            or set(shared_names) | set(new_names) != set(all_names)
            or TARGET_RESIDUE_PARAMETER_NAME_V1 not in new_names
            or not conditioner_names
            or not pair_names
            or not geometry_names
            or GEOMETRY_FINAL_WEIGHT_NAME_V1 not in geometry_names
            or GEOMETRY_FINAL_BIAS_NAME_V1 not in geometry_names
        ):
            _fail("PARAMETER_GROUP_IDENTITY_INVALID")
        optimizer = model.configure_optimizers()
        optimizer_metadata = _validate_optimizer_parameter_coverage(model, optimizer)
        optimizer.zero_grad(set_to_none=True)
        if any(parameter.grad is not None for parameter in model.parameters()):
            _fail("GRADIENT_RESET_TO_NONE_FAILED")
        guard.claim_backward()
        losses.loss_total.backward()
        gradient_specs = (
            ("ALL_PARAMETERS", all_names, "GLOBAL_GRADIENT_GATE_FAILED"),
            ("SHARED_PRETRAINED", shared_names, "SHARED_PRETRAINED_GRADIENT_GATE_FAILED"),
            ("TARGET_RESIDUE_CONDITIONING", target_names, "TARGET_RESIDUE_GRADIENT_GATE_FAILED"),
            ("ROLE_TASK_MASK_ANCHOR", conditioner_names, "CONDITIONER_GRADIENT_GATE_FAILED"),
            ("PAIR_HEAD", pair_names, "PAIR_HEAD_GRADIENT_GATE_FAILED"),
            ("GEOMETRY_HEAD", geometry_names, "GEOMETRY_HEAD_GRADIENT_GATE_FAILED"),
        )
        gradient_stats_list: list[CovapieBatch001Train5GradientGroupStatsV1] = []
        for group_name, names, reason in gradient_specs:
            stats = _gradient_group_stats(
                group_name=group_name,
                named_parameters=named_parameters,
                parameter_names=names,
            )
            _require_gradient_gate(stats, reason=reason)
            gradient_stats_list.append(stats)
        gradient_stats = tuple(gradient_stats_list)
        component_gradient = _geometry_component_gradient(named_parameters)
        guard.claim_optimizer_step()
        optimizer.step()
        delta_specs = (
            ("ALL_PARAMETERS", all_names, "GLOBAL_PARAMETER_DELTA_GATE_FAILED"),
            ("SHARED_PRETRAINED", shared_names, "SHARED_PRETRAINED_DELTA_GATE_FAILED"),
            ("NEW_COVAPIE", new_names, "NEW_COVAPIE_DELTA_GATE_FAILED"),
            ("TARGET_RESIDUE_CONDITIONING", target_names, "TARGET_RESIDUE_DELTA_GATE_FAILED"),
            ("ROLE_TASK_MASK_ANCHOR", conditioner_names, "CONDITIONER_DELTA_GATE_FAILED"),
            ("PAIR_HEAD", pair_names, "PAIR_HEAD_DELTA_GATE_FAILED"),
            ("GEOMETRY_HEAD", geometry_names, "GEOMETRY_HEAD_DELTA_GATE_FAILED"),
        )
        delta_stats_list: list[CovapieBatch001Train5ParameterDeltaGroupStatsV1] = []
        for group_name, names, reason in delta_specs:
            stats = _parameter_delta_group_stats(
                group_name=group_name,
                named_parameters=named_parameters,
                parameter_names=names,
                before=before_parameters,
            )
            _require_delta_gate(stats, reason=reason)
            delta_stats_list.append(stats)
        delta_stats = tuple(delta_stats_list)
        all_parameters_finite = all(
            bool(torch.isfinite(parameter).all().item())
            for parameter in model.parameters()
        )
        if not all_parameters_finite:
            _fail("NON_FINITE_PARAMETER_AFTER_OPTIMIZER_STEP")
        if model.covapie_current11_loss_weights != published_default:
            _fail("PUBLISHED_DEFAULT_MODIFIED_DURING_SMOKE")

    if any(
        not _same_tensor(supervision_before[field.name], getattr(supervision, field.name))
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    ) or any(
        not _same_tensor(value, prepared.model_input_batch[name])
        for name, value in model_input_before.items()
    ):
        _fail("TRAIN5_INPUT_OR_SUPERVISION_MUTATED")
    checkpoint_after = predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
        checkpoint_path=checkpoint_path
    )
    bound_after = _verify_bound_sources(repository_root)
    predecessor.audit_covapie_batch001_train5_formal_authority_v1(
        repository_root=repository_root
    )
    _require_unchanged_evidence(
        checkpoint_before, checkpoint_after, "CHECKPOINT_CHANGED"
    )
    _require_unchanged_evidence(
        bound_before, bound_after, "PUBLISHED_PREDECESSOR_OR_OWNER_CHANGED"
    )
    if guard.backward_call_count != 1 or guard.optimizer_step_count != 1:
        _fail("EXACTLY_ONCE_EXECUTION_COUNTS_INVALID")
    geometry_loss = dict(runtime_losses)["loss_pre_post_geometry"]
    return CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1(
        implementation_status="passed",
        result_interpretation="geometry_weight_candidate_validated_for_single_step_smoke",
        formal_train_event_ids=prepared.authority.formal_train_event_ids,
        formal_validation_event_ids=prepared.authority.formal_validation_event_ids,
        formal_unresolved_event_ids=prepared.authority.formal_unresolved_event_ids,
        non_target_component_event_ids=prepared.authority.non_target_component_event_ids,
        DJK_train_event_count=prepared.authority.DJK_train_event_count,
        PTG_train_event_count=prepared.authority.PTG_train_event_count,
        validation_event_backward_count=0,
        unresolved_event_backward_count=0,
        non_target_component_event_backward_count=0,
        scheduled_task_ids=prepared.scheduled_task_ids,
        ligand_node_count=sum(ligand_counts),
        pocket_node_count=sum(pocket_counts),
        pair_candidate_count=len(supervision.pair_candidate_batch_index),
        pair_positive_count=int(supervision.pair_candidate_is_positive.sum().item()),
        pair_negative_count=int(supervision.pair_candidate_is_negative.sum().item()),
        diffusion_timesteps=tuple(model_output.diffusion_timestep_int.tolist()),
        published_default_loss_weights=_loss_weights_tuple(published_default),
        smoke_only_loss_weights=_loss_weights_tuple(candidate_weights),
        runtime_losses=runtime_losses,
        weighted_total_formula_value=formula_value,
        weighted_total_formula_absolute_difference=formula_difference,
        geometry_contribution_to_smoke_total=geometry_loss,
        base_diffusion_valid_sample_count=losses.base_diffusion_valid_sample_count,
        covalent_pair_prediction_valid_sample_count=losses.covalent_pair_prediction_valid_sample_count,
        pre_post_geometry_valid_sample_count=losses.pre_post_geometry_valid_sample_count,
        covalent_pair_contrastive_valid_sample_count=losses.covalent_pair_contrastive_valid_sample_count,
        PRE_geometry_valid_sample_count=0,
        parameter_snapshots=parameter_snapshots,
        gradient_group_stats=gradient_stats,
        parameter_delta_group_stats=delta_stats,
        geometry_component_gradient=component_gradient,
        optimizer_metadata=optimizer_metadata,
        migration_counts=migration_counts,
        migration_missing_keys=tuple(migration["migration_missing_keys"]),
        migration_unexpected_keys=tuple(migration["migration_unexpected_keys"]),
        architecture=architecture,
        bound_source_sha256=bound_before,
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        backward_call_count=guard.backward_call_count,
        optimizer_step_count=guard.optimizer_step_count,
        gradient_clipping_performed=False,
        scheduler_step_performed=False,
        all_parameters_finite_after_step=True,
        in_memory_model_parameters_changed=True,
        checkpoint_file_changed=False,
        repository_predecessor_files_changed=False,
        published_default_modified=False,
        persistent_output_written=False,
        checkpoint_saved=False,
        model_saved=False,
        Trainer_used=False,
        GPU_used=False,
        supervision_dataclass_reused=True,
        elapsed_seconds=time.perf_counter() - started,
        geometry_weight_candidate_validated_for_single_step_smoke=True,
        geometry_weight_optimal=False,
        production_geometry_weight_finalized=False,
        ready_for_bounded_batch001_train5_trainer_fit_smoke=True,
        ready_for_full_training=False,
    )


def run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
    *,
    repository_root: Path | None = None,
    state_root: Path | None = None,
    cache_root: Path | None = None,
    checkpoint_path: Path | None = None,
    requested_sample_identities: object = None,
    smoke_loss_weights: CovapieCurrent11LossWeightsV1 | None = None,
    persistent_output_path: Path | None = None,
) -> CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1:
    """Execute the bounded formal-train5 single-step CPU smoke."""

    try:
        if persistent_output_path is not None:
            _fail("PERSISTENT_MODEL_OUTPUT_PATH_FORBIDDEN")
        repository = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_directory(
            state_root,
            default=_DEFAULT_STATE_ROOT,
            reason="STATE_ROOT_INVALID",
        )
        cache = _require_directory(
            cache_root,
            default=_DEFAULT_CACHE_ROOT,
            reason="CACHE_ROOT_INVALID",
        )
        checkpoint = (
            repository / predecessor.CHECKPOINT_RELATIVE_PATH_V1
            if checkpoint_path is None
            else checkpoint_path
        )
        if (
            type(checkpoint) is not _PATH_TYPE
            or checkpoint != repository / predecessor.CHECKPOINT_RELATIVE_PATH_V1
        ):
            _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
        return _run_single_step_impl(
            repository_root=repository,
            state_root=state,
            cache_root=cache,
            checkpoint_path=checkpoint,
            requested_sample_identities=requested_sample_identities,
            smoke_loss_weights=smoke_loss_weights,
        )
    except BaseException as error:
        _public_error(error)

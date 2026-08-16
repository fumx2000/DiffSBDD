"""Deterministic, CPU-only Current11 Exact5 learning-signal probe V1.

The probe composes the published tensorizer, diffusion bridge, auxiliary model,
and loss owner.  It is diagnostic-only: it never creates an optimizer, runs a
backward pass, or updates model state.
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import torch
from torch import nn

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    tensorize_covapie_current11_training_supervision_v1,
)


__all__ = (
    "BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1",
    "BOUNDED_LEARNING_SIGNAL_PROBE_ERROR_V1",
    "BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1",
    "BOUNDED_LEARNING_SIGNAL_PROBE_DEFAULT_SEED_V1",
    "BOUNDED_LEARNING_SIGNAL_OUTCOMES_V1",
    "CovapieCurrent11PairRankingDiagnosticsV1",
    "CovapieCurrent11ProbeEpochResultV1",
    "CovapieCurrent11DeterministicExact5ProbeResultV1",
    "CovapieCurrent11ProbeRepeatabilityResultV1",
    "CovapieCurrent11LearningSignalDecisionV1",
    "CovapieCurrent11BoundedLearningSignalExperimentResultV1",
    "run_covapie_current11_deterministic_exact5_probe_v1",
    "validate_covapie_current11_preprobe_repeatability_v1",
    "compare_covapie_current11_learning_signal_v1",
    "run_covapie_current11_bounded_learning_signal_experiment_v1",
)


BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1 = (
    "covapie_current11_bounded_learning_signal_probe_v1"
)
BOUNDED_LEARNING_SIGNAL_PROBE_ERROR_V1 = (
    "COVAPIE_CURRENT11_BOUNDED_LEARNING_SIGNAL_PROBE_V1_ERROR"
)
BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1 = (0, 1, 2, 3, 4)
BOUNDED_LEARNING_SIGNAL_PROBE_DEFAULT_SEED_V1 = 20_260_816
BOUNDED_LEARNING_SIGNAL_OUTCOMES_V1 = (
    "LEARNING_SIGNAL_PASS",
    "LEARNING_SIGNAL_WEAK",
    "NO_LEARNING_SIGNAL",
    "PROBE_NONDETERMINISTIC",
    "TRAINING_FAILED",
)

_PROBE_SEED_DOMAIN_V1 = (
    b"COVAPIE_CURRENT11_BOUNDED_LEARNING_SIGNAL_PROBE_V1\0"
)
_EXPECTED_TASK_VECTORS_V1 = (
    (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1),
    (4, 3, 4, 1, 3, 0, 1, 1, 0, 0, 2),
    (0, 4, 0, 2, 4, 1, 2, 2, 1, 1, 3),
    (1, 0, 1, 3, 0, 2, 3, 3, 2, 2, 4),
    (2, 1, 2, 4, 1, 3, 4, 4, 3, 3, 0),
)
_EXPECTED_LOSS_WEIGHTS_V1 = {
    "base_diffusion": 1.0,
    "covalent_pair_prediction": 1.0,
    "pre_post_geometry": 0.0,
    "covalent_pair_contrastive": 0.1,
}
_EPS32_V1 = 1.1920928955078125e-7
_FLOAT_METRIC_FIELDS_V1 = (
    "probe_base",
    "probe_pair",
    "probe_geometry",
    "probe_contrastive",
    "probe_total",
    "pair_positive_logit",
    "pair_negative_logit",
    "pair_margin",
    "pair_rank",
    "pair_top1",
)
_LEARNING_METRICS_V1 = (
    "probe_total",
    "probe_base",
    "probe_pair",
    "probe_contrastive",
    "pair_margin",
)


@dataclass(frozen=True)
class CovapieCurrent11PairRankingDiagnosticsV1:
    positive_logits: tuple[float, ...]
    negative_logit_means: tuple[float, ...]
    margins: tuple[float, ...]
    ranks: tuple[int, ...]
    top1: tuple[bool, ...]
    positive_logit_mean: float
    negative_logit_mean: float
    margin_mean: float
    rank_mean: float
    top1_accuracy: float


@dataclass(frozen=True)
class CovapieCurrent11ProbeEpochResultV1:
    schema_version: str
    probe_epoch: int
    derived_epoch_seed: int
    canonical_task_ids: tuple[int, ...]
    diffusion_timesteps: tuple[int, ...]
    effective_sampled_epsilon_sha256: str
    loss_base_diffusion: float
    loss_covalent_pair_prediction: float
    loss_pre_post_geometry: float
    loss_covalent_pair_contrastive: float
    loss_total: float
    base_diffusion_valid_sample_count: int
    covalent_pair_prediction_valid_sample_count: int
    pre_post_geometry_valid_sample_count: int
    covalent_pair_contrastive_valid_sample_count: int
    geometry_head_forward: bool
    geometry_predictions_finite: bool
    geometry_formal_weight: float
    target_pair_consistency: bool
    pair_candidate_consistency: bool
    pair_positive_logit_mean: float
    pair_negative_logit_mean: float
    pair_margin_mean: float
    pair_rank_mean: float
    pair_top1_accuracy: float
    pair_rank_by_sample: tuple[int, ...]
    pair_top1_by_sample: tuple[bool, ...]


@dataclass(frozen=True)
class CovapieCurrent11DeterministicExact5ProbeResultV1:
    schema_version: str
    probe_seed: int
    derived_epoch_seeds: tuple[int, ...]
    epoch_results: tuple[CovapieCurrent11ProbeEpochResultV1, ...]
    sample_task_evaluation_count: int
    input_configuration_fingerprint_before: str
    input_configuration_fingerprint_after: str
    probe_base_mean: float
    probe_pair_mean: float
    probe_geometry_mean: float
    probe_contrastive_mean: float
    probe_total_mean: float
    pair_positive_logit_mean: float
    pair_negative_logit_mean: float
    pair_margin_mean: float
    pair_rank_mean: float
    pair_top1_accuracy: float
    parameter_digest_before: str
    parameter_digest_after: str
    buffer_digest_before: str
    buffer_digest_after: str
    gradient_digest_before: str
    gradient_digest_after: str
    mode_digest_before: str
    mode_digest_after: str
    batch_tensor_digest_before: str
    batch_tensor_digest_after: str
    trainer_counter_digest_before: str
    trainer_counter_digest_after: str
    parameter_unchanged: bool
    buffer_unchanged: bool
    gradient_state_unchanged: bool
    mode_flags_restored: bool
    batch_unchanged: bool
    trainer_counters_unchanged: bool
    torch_cpu_rng_digest_before: str
    torch_cpu_rng_digest_after: str
    probe_rng_used_domains: tuple[str, ...]
    cpu_rng_state_restored: bool
    all_probe_rng_domains_restored: bool
    global_rng_restored: bool
    probe_model_mode: str
    no_grad_used: bool
    optimizer_created: bool
    backward_called: bool
    optimizer_step_called: bool
    stateful_train_mode_layer_blocker_found: bool


@dataclass(frozen=True)
class CovapieCurrent11ProbeRepeatabilityResultV1:
    schema_version: str
    repeatable: bool
    outcome: str
    exact_evidence_equal: bool
    maximum_absolute_discrepancies: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class CovapieCurrent11LearningSignalDecisionV1:
    schema_version: str
    outcome: str
    tolerances: tuple[tuple[str, float], ...]
    improvements: tuple[tuple[str, float], ...]
    total_criterion_passed: bool
    covalent_criterion_passed: bool
    geometry_in_acceptance: bool


@dataclass(frozen=True)
class CovapieCurrent11BoundedLearningSignalExperimentResultV1:
    schema_version: str
    outcome: str
    pre1: CovapieCurrent11DeterministicExact5ProbeResultV1 | None
    pre2: CovapieCurrent11DeterministicExact5ProbeResultV1 | None
    repeatability: CovapieCurrent11ProbeRepeatabilityResultV1 | None
    post: CovapieCurrent11DeterministicExact5ProbeResultV1 | None
    decision: CovapieCurrent11LearningSignalDecisionV1 | None
    fit_call_count: int
    fit_ckpt_path_was_none: bool
    training_completed: bool
    failure_stage: str | None


class _ProbeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _ProbeInvariantError()


def _public_error(error: BaseException) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error) == BOUNDED_LEARNING_SIGNAL_PROBE_ERROR_V1
    ):
        raise error
    raise ValueError(BOUNDED_LEARNING_SIGNAL_PROBE_ERROR_V1) from error


def _require_probe_seed_v1(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        _fail()
    return value


def _require_probe_epoch_v1(value: object) -> int:
    if type(value) is not int or value not in BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1:
        _fail()
    return value


def _derive_covapie_current11_probe_epoch_seed_v1(
    *, probe_seed: object, probe_epoch: object,
) -> int:
    try:
        base_seed = _require_probe_seed_v1(probe_seed)
        epoch = _require_probe_epoch_v1(probe_epoch)
        payload = (
            _PROBE_SEED_DOMAIN_V1
            + b"schema="
            + BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1.encode("ascii")
            + b"\0base_seed="
            + str(base_seed).encode("ascii")
            + b"\0probe_epoch="
            + str(epoch).encode("ascii")
        )
        return int.from_bytes(
            hashlib.sha256(payload).digest()[:8], "big", signed=False
        ) & ((1 << 63) - 1)
    except BaseException as error:
        _public_error(error)


def _tensor_bytes_v1(value: torch.Tensor) -> bytes:
    tensor = value.detach().cpu().contiguous()
    return tensor.reshape(-1).view(torch.uint8).numpy().tobytes()


def _update_tensor_hash_v1(
    digest: "hashlib._Hash", *, name: str, value: torch.Tensor,
) -> None:
    tensor = value.detach().cpu().contiguous()
    shape = ",".join(str(item) for item in tensor.shape)
    digest.update(b"tensor\0name=")
    digest.update(name.encode("utf-8"))
    digest.update(b"\0dtype=")
    digest.update(str(tensor.dtype).encode("ascii"))
    digest.update(b"\0shape=")
    digest.update(shape.encode("ascii"))
    digest.update(b"\0bytes=")
    digest.update(_tensor_bytes_v1(tensor))
    digest.update(b"\0")


def _canonical_tensor_sha256_v1(*, name: str, value: torch.Tensor) -> str:
    if type(name) is not str or not name or not isinstance(value, torch.Tensor):
        _fail()
    digest = hashlib.sha256()
    _update_tensor_hash_v1(digest, name=name, value=value)
    return digest.hexdigest()


def _named_tensor_digest_v1(
    values: tuple[tuple[str, torch.Tensor], ...],
) -> str:
    digest = hashlib.sha256()
    for name, value in values:
        _update_tensor_hash_v1(digest, name=name, value=value)
    return digest.hexdigest()


def _gradient_digest_v1(
    values: tuple[tuple[str, torch.Tensor | None], ...],
) -> str:
    digest = hashlib.sha256()
    for name, value in values:
        digest.update(name.encode("utf-8") + b"\0")
        if value is None:
            digest.update(b"none\0")
        else:
            _update_tensor_hash_v1(digest, name=name, value=value)
    return digest.hexdigest()


def _mode_digest_v1(values: tuple[tuple[str, bool], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in values:
        digest.update(name.encode("utf-8") + b"=" + str(int(value)).encode("ascii") + b"\0")
    return digest.hexdigest()


def _normalize_numpy_scalar_v1(value: object) -> object:
    value_type = type(value)
    if value_type.__module__.split(".")[0] != "numpy":
        return value
    item = getattr(value, "item", None)
    if not callable(item):
        _fail()
    normalized = item()
    if normalized is value:
        _fail()
    return normalized


def _update_value_hash_v1(
    digest: "hashlib._Hash", value: object, *, path: str,
) -> None:
    value = _normalize_numpy_scalar_v1(value)
    if isinstance(value, torch.Tensor):
        _update_tensor_hash_v1(digest, name=path, value=value)
    elif value is None:
        digest.update(b"none\0")
    elif type(value) is bool:
        digest.update(b"bool=" + str(int(value)).encode("ascii") + b"\0")
    elif type(value) is int:
        digest.update(b"int=" + str(value).encode("ascii") + b"\0")
    elif type(value) is float:
        digest.update(b"float64=")
        digest.update(struct.pack(">d", value))
        digest.update(b"\0")
    elif type(value) is str:
        encoded = value.encode("utf-8")
        digest.update(b"str=" + str(len(encoded)).encode("ascii") + b":" + encoded + b"\0")
    elif type(value) is bytes:
        digest.update(b"bytes=" + str(len(value)).encode("ascii") + b":" + value + b"\0")
    elif type(value) is Path:
        _update_value_hash_v1(digest, str(value), path=path)
    elif type(value) is dict:
        if any(type(key) is not str for key in value):
            _fail()
        digest.update(b"dict\0")
        for key in sorted(value):
            _update_value_hash_v1(digest, key, path=f"{path}.key")
            _update_value_hash_v1(digest, value[key], path=f"{path}.{key}")
        digest.update(b"enddict\0")
    elif type(value) in (list, tuple):
        digest.update(("list" if type(value) is list else "tuple").encode("ascii") + b"\0")
        for index, item in enumerate(value):
            _update_value_hash_v1(digest, item, path=f"{path}[{index}]")
        digest.update(b"endsequence\0")
    else:
        _fail()


def _value_digest_v1(value: object, *, root_name: str) -> str:
    digest = hashlib.sha256()
    _update_value_hash_v1(digest, value, path=root_name)
    return digest.hexdigest()


def _iter_batch_tensors_v1(
    value: object, *, path: str,
) -> tuple[tuple[str, torch.Tensor], ...]:
    result: list[tuple[str, torch.Tensor]] = []

    def visit(item: object, item_path: str) -> None:
        if isinstance(item, torch.Tensor):
            result.append((item_path, item))
        elif type(item) is dict:
            if any(type(key) is not str for key in item):
                _fail()
            for key in sorted(item):
                visit(item[key], f"{item_path}.{key}")
        elif type(item) in (list, tuple):
            for index, child in enumerate(item):
                visit(child, f"{item_path}[{index}]")

    visit(value, path)
    return tuple(result)


def _trainer_counters_v1(model: nn.Module) -> tuple[tuple[str, int], ...]:
    trainer = getattr(model, "_trainer", None)
    if trainer is None:
        return ()
    counters: list[tuple[str, int]] = []
    for name in ("current_epoch", "global_step"):
        value = getattr(trainer, name, None)
        if type(value) is not int or value < 0:
            _fail()
        counters.append((name, value))
    return tuple(counters)


def _counter_digest_v1(values: tuple[tuple[str, int], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in values:
        digest.update(name.encode("ascii") + b"=" + str(value).encode("ascii") + b"\0")
    return digest.hexdigest()


def _snapshot_parameters_v1(
    model: nn.Module,
) -> tuple[tuple[str, torch.Tensor], ...]:
    return tuple(
        (name, parameter.detach().clone())
        for name, parameter in model.named_parameters()
    )


def _snapshot_buffers_v1(
    model: nn.Module,
) -> tuple[tuple[str, torch.Tensor], ...]:
    return tuple(
        (name, buffer.detach().clone()) for name, buffer in model.named_buffers()
    )


def _snapshot_gradients_v1(
    model: nn.Module,
) -> tuple[tuple[str, torch.Tensor | None], ...]:
    return tuple(
        (
            name,
            None if parameter.grad is None else parameter.grad.detach().clone(),
        )
        for name, parameter in model.named_parameters()
    )


def _snapshots_equal_v1(
    first: tuple[tuple[str, torch.Tensor], ...],
    second: tuple[tuple[str, torch.Tensor], ...],
) -> bool:
    return (
        tuple(name for name, unused in first)
        == tuple(name for name, unused in second)
        and all(
            torch.equal(left, right)
            for (unused_name, left), (unused_name_2, right) in zip(
                first, second, strict=True
            )
        )
    )


def _gradient_snapshots_equal_v1(
    first: tuple[tuple[str, torch.Tensor | None], ...],
    second: tuple[tuple[str, torch.Tensor | None], ...],
) -> bool:
    if tuple(name for name, unused in first) != tuple(name for name, unused in second):
        return False
    for (unused_name, left), (unused_name_2, right) in zip(
        first, second, strict=True
    ):
        if (left is None) != (right is None):
            return False
        if left is not None and right is not None and not torch.equal(left, right):
            return False
    return True


def _restore_mode_map_v1(
    model: nn.Module, modes: tuple[tuple[str, bool], ...],
) -> None:
    current = tuple(model.named_modules())
    if tuple(name for name, unused in current) != tuple(name for name, unused in modes):
        _fail()
    for (unused_name, module), (unused_name_2, training) in zip(
        current, modes, strict=True
    ):
        module.training = training


def _reject_stateful_train_mode_layers_v1(model: nn.Module) -> None:
    forbidden = (
        nn.modules.batchnorm._BatchNorm,
        nn.SyncBatchNorm,
        nn.modules.instancenorm._InstanceNorm,
        nn.GroupNorm,
        nn.LayerNorm,
        nn.Dropout,
        nn.Dropout1d,
        nn.Dropout2d,
        nn.Dropout3d,
        nn.AlphaDropout,
        nn.FeatureAlphaDropout,
    )
    for module in model.modules():
        class_name = type(module).__name__.lower()
        if (
            isinstance(module, forbidden)
            or "stochasticdepth" in class_name
            or "droppath" in class_name
            or (
                isinstance(module, nn.RNNBase)
                and float(getattr(module, "dropout", 0.0)) != 0.0
            )
            or (
                isinstance(module, nn.MultiheadAttention)
                and float(getattr(module, "dropout", 0.0)) != 0.0
            )
        ):
            _fail()


def _validate_probe_model_and_batch_v1(
    *, model: object, attached_batch: object,
) -> CovapieCurrent11TrainingLigandPocketDDPM:
    if (
        not isinstance(model, CovapieCurrent11TrainingLigandPocketDDPM)
        or type(attached_batch) is not dict
        or getattr(model, "covapie_current11_training_enabled", None) is not True
        or getattr(model, "covapie_current11_task_schedule_seed", None) != 0
        or getattr(model, "covapie_current11_pair_contrastive_temperature", None)
        != 1.0
        or getattr(model, "covapie_current11_authoritative_supervision_batch_field", None)
        not in attached_batch
        or "covapie_current11_task2_runtime_result_v1" not in attached_batch
    ):
        _fail()
    weights = getattr(model, "covapie_current11_loss_weights", None)
    if (
        not isinstance(weights, CovapieCurrent11LossWeightsV1)
        or vars(weights) != _EXPECTED_LOSS_WEIGHTS_V1
    ):
        _fail()
    if any(parameter.device.type != "cpu" for parameter in model.parameters()):
        _fail()
    if any(buffer.device.type != "cpu" for buffer in model.buffers()):
        _fail()
    # Querying this flag does not initialize CUDA.  If another caller already
    # initialized that RNG domain, V1 refuses to make a CPU-global claim.
    if torch.cuda.is_initialized():
        _fail()
    batch_tensors = _iter_batch_tensors_v1(attached_batch, path="attached_batch")
    if any(tensor.device.type != "cpu" for unused, tensor in batch_tensors):
        _fail()
    _reject_stateful_train_mode_layers_v1(model)
    return model


def _input_configuration_fingerprint_v1(
    *, model: CovapieCurrent11TrainingLigandPocketDDPM, attached_batch: dict[str, object],
) -> str:
    weights = model.covapie_current11_loss_weights
    configuration = {
        "schema_version": BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
        "model_class": f"{type(model).__module__}.{type(model).__qualname__}",
        "ddpm_timesteps": int(model.ddpm.T),
        "ligand_feature_count": int(model.ddpm.atom_nf),
        "pocket_feature_count": int(model.ddpm.residue_nf),
        "task_schedule_seed": model.covapie_current11_task_schedule_seed,
        "pair_contrastive_temperature": (
            model.covapie_current11_pair_contrastive_temperature
        ),
        "loss_weights": dict(vars(weights)),
        "attached_batch": attached_batch,
    }
    return _value_digest_v1(configuration, root_name="probe_configuration")


def _run_covapie_current11_probe_epoch_forward_v1(
    *,
    model: CovapieCurrent11TrainingLigandPocketDDPM,
    attached_batch: dict[str, object],
    probe_epoch: object,
) -> CovapieCurrent11TrainingForwardOutputV1:
    epoch = _require_probe_epoch_v1(probe_epoch)
    if model.training is not True or model.ddpm.training is not True:
        _fail()
    ligand, pocket = model.get_ligand_and_pocket(attached_batch)
    runtime_result = attached_batch["covapie_current11_task2_runtime_result_v1"]
    authoritative_supervision = attached_batch[
        model.covapie_current11_authoritative_supervision_batch_field
    ]
    supervision = tensorize_covapie_current11_training_supervision_v1(
        batch=attached_batch,
        runtime_result=runtime_result,
        authoritative_supervision=authoritative_supervision,
        device=ligand["x"].device,
        epoch=epoch,
        task_schedule_seed=0,
    )
    canonical_indicator = supervision.target_residue_reactive_atom_mask
    if (
        canonical_indicator.dtype != torch.bool
        or canonical_indicator.ndim != 2
        or canonical_indicator.shape != (len(pocket["x"]), 1)
    ):
        _fail()
    role_delta = model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
        supervision=supervision,
        ligand_batch_index=ligand["mask"],
    )
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=model.ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=canonical_indicator[:, 0],
    )
    model_output = model.covapie_current11_auxiliary_model_v1(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    loss_output = compute_covapie_current11_training_losses_v1(
        model_output=model_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=model.covapie_current11_loss_weights,
        pair_contrastive_temperature=1.0,
        geometry_smooth_l1_beta=1.0,
    )
    return CovapieCurrent11TrainingForwardOutputV1(
        model_output=model_output,
        loss_output=loss_output,
        supervision=supervision,
        diffusion_trace=trace,
    )


def _compute_pair_ranking_diagnostics_v1(
    *,
    pair_logits: torch.Tensor,
    pair_candidate_offsets: torch.Tensor,
    pair_positive_candidate_index: torch.Tensor,
    pair_positive_candidate_valid: torch.Tensor,
    pair_candidate_is_negative: torch.Tensor,
    pair_head_candidate_loss_mask: torch.Tensor,
) -> CovapieCurrent11PairRankingDiagnosticsV1:
    try:
        tensors = (
            pair_logits,
            pair_candidate_offsets,
            pair_positive_candidate_index,
            pair_positive_candidate_valid,
            pair_candidate_is_negative,
            pair_head_candidate_loss_mask,
        )
        if any(not isinstance(value, torch.Tensor) for value in tensors):
            _fail()
        batch_size = len(pair_positive_candidate_index)
        if (
            pair_logits.ndim != 1
            or pair_candidate_offsets.dtype != torch.long
            or pair_candidate_offsets.ndim != 1
            or len(pair_candidate_offsets) != batch_size + 1
            or pair_positive_candidate_index.dtype != torch.long
            or pair_positive_candidate_index.ndim != 1
            or pair_positive_candidate_valid.dtype != torch.bool
            or pair_positive_candidate_valid.shape != pair_positive_candidate_index.shape
            or pair_candidate_is_negative.dtype != torch.bool
            or pair_candidate_is_negative.shape != pair_logits.shape
            or pair_head_candidate_loss_mask.dtype != torch.bool
            or pair_head_candidate_loss_mask.shape != pair_logits.shape
            or not bool(pair_positive_candidate_valid.all().item())
        ):
            _fail()
        positives: list[float] = []
        negative_means: list[float] = []
        margins: list[float] = []
        ranks: list[int] = []
        top1: list[bool] = []
        for sample in range(batch_size):
            start = int(pair_candidate_offsets[sample].item())
            end = int(pair_candidate_offsets[sample + 1].item())
            positive_index = int(pair_positive_candidate_index[sample].item())
            if not 0 <= start <= positive_index < end <= len(pair_logits):
                _fail()
            negative_mask = (
                pair_candidate_is_negative[start:end]
                & pair_head_candidate_loss_mask[start:end]
            )
            negative_logits = pair_logits[start:end][negative_mask]
            positive_logit = pair_logits[positive_index]
            if (
                len(negative_logits) == 0
                or not bool(pair_head_candidate_loss_mask[positive_index].item())
                or not bool(torch.isfinite(positive_logit).item())
                or not bool(torch.isfinite(negative_logits).all().item())
            ):
                _fail()
            negative_mean = negative_logits.mean()
            margin = positive_logit - negative_mean
            rank = 1 + int((negative_logits >= positive_logit).sum().item())
            positives.append(float(positive_logit.detach().cpu().item()))
            negative_means.append(float(negative_mean.detach().cpu().item()))
            margins.append(float(margin.detach().cpu().item()))
            ranks.append(rank)
            top1.append(rank == 1)
        if batch_size != 11:
            _fail()
        return CovapieCurrent11PairRankingDiagnosticsV1(
            positive_logits=tuple(positives),
            negative_logit_means=tuple(negative_means),
            margins=tuple(margins),
            ranks=tuple(ranks),
            top1=tuple(top1),
            positive_logit_mean=sum(positives) / batch_size,
            negative_logit_mean=sum(negative_means) / batch_size,
            margin_mean=sum(margins) / batch_size,
            rank_mean=sum(ranks) / batch_size,
            top1_accuracy=sum(top1) / batch_size,
        )
    except BaseException as error:
        _public_error(error)


def _finite_scalar_v1(value: torch.Tensor) -> float:
    if not isinstance(value, torch.Tensor) or value.numel() != 1:
        _fail()
    result = float(value.detach().cpu().item())
    if not math.isfinite(result):
        _fail()
    return result


def _extract_epoch_result_v1(
    *, output: CovapieCurrent11TrainingForwardOutputV1, probe_epoch: int, epoch_seed: int,
) -> CovapieCurrent11ProbeEpochResultV1:
    if not isinstance(output, CovapieCurrent11TrainingForwardOutputV1):
        _fail()
    supervision = output.supervision
    trace = output.diffusion_trace
    model_output = output.model_output
    losses = output.loss_output
    task_ids = tuple(int(value) for value in supervision.canonical_task_id.tolist())
    timesteps = tuple(int(value) for value in trace.diffusion_timestep_int.tolist())
    if (
        task_ids != _EXPECTED_TASK_VECTORS_V1[probe_epoch]
        or len(timesteps) != 11
        or not bool(supervision.canonical_task_valid.all().item())
    ):
        _fail()
    candidate_fields_equal = all(
        torch.equal(getattr(model_output, name), getattr(supervision, name))
        for name in (
            "pair_candidate_offsets",
            "pair_candidate_batch_index",
            "pair_candidate_ligand_local_index",
            "pair_candidate_residue_local_index",
            "pair_candidate_ligand_flat_index",
            "pair_candidate_pocket_flat_index",
        )
    )
    target_consistency = bool(
        model_output.target_pair_consistency[
            supervision.pair_positive_candidate_valid
        ].all().item()
    )
    ranking = _compute_pair_ranking_diagnostics_v1(
        pair_logits=model_output.pair_logits,
        pair_candidate_offsets=supervision.pair_candidate_offsets,
        pair_positive_candidate_index=supervision.pair_positive_candidate_index,
        pair_positive_candidate_valid=supervision.pair_positive_candidate_valid,
        pair_candidate_is_negative=supervision.pair_candidate_is_negative,
        pair_head_candidate_loss_mask=supervision.pair_head_candidate_loss_mask,
    )
    geometry_finite = bool(
        torch.isfinite(model_output.pre_post_geometry_predictions_angstrom).all().item()
    )
    loss_geometry = _finite_scalar_v1(losses.loss_pre_post_geometry)
    if (
        losses.base_diffusion_valid_sample_count != 11
        or losses.covalent_pair_prediction_valid_sample_count != 11
        or losses.pre_post_geometry_valid_sample_count != 0
        or losses.covalent_pair_contrastive_valid_sample_count != 11
        or loss_geometry != 0.0
        or not geometry_finite
        or not target_consistency
        or not candidate_fields_equal
    ):
        _fail()
    return CovapieCurrent11ProbeEpochResultV1(
        schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
        probe_epoch=probe_epoch,
        derived_epoch_seed=epoch_seed,
        canonical_task_ids=task_ids,
        diffusion_timesteps=timesteps,
        effective_sampled_epsilon_sha256=_canonical_tensor_sha256_v1(
            name="effective_sampled_epsilon_ligand",
            value=trace.sampled_epsilon_ligand,
        ),
        loss_base_diffusion=_finite_scalar_v1(losses.loss_base_diffusion),
        loss_covalent_pair_prediction=_finite_scalar_v1(
            losses.loss_covalent_pair_prediction
        ),
        loss_pre_post_geometry=loss_geometry,
        loss_covalent_pair_contrastive=_finite_scalar_v1(
            losses.loss_covalent_pair_contrastive
        ),
        loss_total=_finite_scalar_v1(losses.loss_total),
        base_diffusion_valid_sample_count=losses.base_diffusion_valid_sample_count,
        covalent_pair_prediction_valid_sample_count=(
            losses.covalent_pair_prediction_valid_sample_count
        ),
        pre_post_geometry_valid_sample_count=(
            losses.pre_post_geometry_valid_sample_count
        ),
        covalent_pair_contrastive_valid_sample_count=(
            losses.covalent_pair_contrastive_valid_sample_count
        ),
        geometry_head_forward=True,
        geometry_predictions_finite=geometry_finite,
        geometry_formal_weight=0.0,
        target_pair_consistency=target_consistency,
        pair_candidate_consistency=candidate_fields_equal,
        pair_positive_logit_mean=ranking.positive_logit_mean,
        pair_negative_logit_mean=ranking.negative_logit_mean,
        pair_margin_mean=ranking.margin_mean,
        pair_rank_mean=ranking.rank_mean,
        pair_top1_accuracy=ranking.top1_accuracy,
        pair_rank_by_sample=ranking.ranks,
        pair_top1_by_sample=ranking.top1,
    )


def _mean_epoch_field_v1(
    epochs: tuple[CovapieCurrent11ProbeEpochResultV1, ...], field: str,
) -> float:
    return sum(float(getattr(epoch, field)) for epoch in epochs) / len(epochs)


def run_covapie_current11_deterministic_exact5_probe_v1(
    *,
    model: object,
    attached_batch: object,
    probe_seed: int = BOUNDED_LEARNING_SIGNAL_PROBE_DEFAULT_SEED_V1,
) -> CovapieCurrent11DeterministicExact5ProbeResultV1:
    """Run five explicit no-grad epochs while preserving every used state."""

    try:
        base_seed = _require_probe_seed_v1(probe_seed)
        validated_model = _validate_probe_model_and_batch_v1(
            model=model, attached_batch=attached_batch
        )
        batch = attached_batch
        epoch_seeds = tuple(
            _derive_covapie_current11_probe_epoch_seed_v1(
                probe_seed=base_seed, probe_epoch=epoch
            )
            for epoch in BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1
        )
        if (
            len(epoch_seeds) != 5
            or len(set(epoch_seeds)) != 5
            or any(not 0 <= seed <= 2**63 - 1 for seed in epoch_seeds)
        ):
            _fail()

        parameters_before = _snapshot_parameters_v1(validated_model)
        buffers_before = _snapshot_buffers_v1(validated_model)
        gradients_before = _snapshot_gradients_v1(validated_model)
        modes_before = tuple(
            (name, module.training)
            for name, module in validated_model.named_modules()
        )
        batch_tensors_before = tuple(
            (name, tensor.detach().clone())
            for name, tensor in _iter_batch_tensors_v1(
                batch, path="attached_batch"
            )
        )
        trainer_before = _trainer_counters_v1(validated_model)
        fingerprint_before = _input_configuration_fingerprint_v1(
            model=validated_model, attached_batch=batch
        )
        rng_before = torch.random.get_rng_state().clone()
        rng_digest_before = _canonical_tensor_sha256_v1(
            name="torch_cpu_rng_state", value=rng_before
        )

        epoch_results: list[CovapieCurrent11ProbeEpochResultV1] = []
        try:
            validated_model.train()
            for epoch, epoch_seed in zip(
                BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1,
                epoch_seeds,
                strict=True,
            ):
                with torch.random.fork_rng(devices=[], enabled=True):
                    torch.manual_seed(epoch_seed)
                    with torch.no_grad():
                        output = _run_covapie_current11_probe_epoch_forward_v1(
                            model=validated_model,
                            attached_batch=batch,
                            probe_epoch=epoch,
                        )
                epoch_results.append(
                    _extract_epoch_result_v1(
                        output=output,
                        probe_epoch=epoch,
                        epoch_seed=epoch_seed,
                    )
                )
        finally:
            _restore_mode_map_v1(validated_model, modes_before)

        parameters_after = _snapshot_parameters_v1(validated_model)
        buffers_after = _snapshot_buffers_v1(validated_model)
        gradients_after = _snapshot_gradients_v1(validated_model)
        modes_after = tuple(
            (name, module.training)
            for name, module in validated_model.named_modules()
        )
        batch_tensors_after = tuple(
            (name, tensor.detach().clone())
            for name, tensor in _iter_batch_tensors_v1(
                batch, path="attached_batch"
            )
        )
        trainer_after = _trainer_counters_v1(validated_model)
        fingerprint_after = _input_configuration_fingerprint_v1(
            model=validated_model, attached_batch=batch
        )
        rng_after = torch.random.get_rng_state().clone()
        rng_digest_after = _canonical_tensor_sha256_v1(
            name="torch_cpu_rng_state", value=rng_after
        )
        parameter_unchanged = _snapshots_equal_v1(
            parameters_before, parameters_after
        )
        buffer_unchanged = _snapshots_equal_v1(buffers_before, buffers_after)
        gradient_unchanged = _gradient_snapshots_equal_v1(
            gradients_before, gradients_after
        )
        mode_restored = modes_before == modes_after
        batch_unchanged = _snapshots_equal_v1(
            batch_tensors_before, batch_tensors_after
        ) and fingerprint_before == fingerprint_after
        trainer_unchanged = trainer_before == trainer_after
        rng_restored = torch.equal(rng_before, rng_after)
        epochs = tuple(epoch_results)
        coverage = tuple(
            {epoch.canonical_task_ids[sample] for epoch in epochs}
            for sample in range(11)
        )
        if (
            len(epochs) != 5
            or any(tasks != {0, 1, 2, 3, 4} for tasks in coverage)
            or not all((
                parameter_unchanged,
                buffer_unchanged,
                gradient_unchanged,
                mode_restored,
                batch_unchanged,
                trainer_unchanged,
                rng_restored,
            ))
        ):
            _fail()
        return CovapieCurrent11DeterministicExact5ProbeResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            probe_seed=base_seed,
            derived_epoch_seeds=epoch_seeds,
            epoch_results=epochs,
            sample_task_evaluation_count=55,
            input_configuration_fingerprint_before=fingerprint_before,
            input_configuration_fingerprint_after=fingerprint_after,
            probe_base_mean=_mean_epoch_field_v1(epochs, "loss_base_diffusion"),
            probe_pair_mean=_mean_epoch_field_v1(
                epochs, "loss_covalent_pair_prediction"
            ),
            probe_geometry_mean=_mean_epoch_field_v1(
                epochs, "loss_pre_post_geometry"
            ),
            probe_contrastive_mean=_mean_epoch_field_v1(
                epochs, "loss_covalent_pair_contrastive"
            ),
            probe_total_mean=_mean_epoch_field_v1(epochs, "loss_total"),
            pair_positive_logit_mean=_mean_epoch_field_v1(
                epochs, "pair_positive_logit_mean"
            ),
            pair_negative_logit_mean=_mean_epoch_field_v1(
                epochs, "pair_negative_logit_mean"
            ),
            pair_margin_mean=_mean_epoch_field_v1(epochs, "pair_margin_mean"),
            pair_rank_mean=_mean_epoch_field_v1(epochs, "pair_rank_mean"),
            pair_top1_accuracy=_mean_epoch_field_v1(
                epochs, "pair_top1_accuracy"
            ),
            parameter_digest_before=_named_tensor_digest_v1(parameters_before),
            parameter_digest_after=_named_tensor_digest_v1(parameters_after),
            buffer_digest_before=_named_tensor_digest_v1(buffers_before),
            buffer_digest_after=_named_tensor_digest_v1(buffers_after),
            gradient_digest_before=_gradient_digest_v1(gradients_before),
            gradient_digest_after=_gradient_digest_v1(gradients_after),
            mode_digest_before=_mode_digest_v1(modes_before),
            mode_digest_after=_mode_digest_v1(modes_after),
            batch_tensor_digest_before=_named_tensor_digest_v1(
                batch_tensors_before
            ),
            batch_tensor_digest_after=_named_tensor_digest_v1(
                batch_tensors_after
            ),
            trainer_counter_digest_before=_counter_digest_v1(trainer_before),
            trainer_counter_digest_after=_counter_digest_v1(trainer_after),
            parameter_unchanged=parameter_unchanged,
            buffer_unchanged=buffer_unchanged,
            gradient_state_unchanged=gradient_unchanged,
            mode_flags_restored=mode_restored,
            batch_unchanged=batch_unchanged,
            trainer_counters_unchanged=trainer_unchanged,
            torch_cpu_rng_digest_before=rng_digest_before,
            torch_cpu_rng_digest_after=rng_digest_after,
            probe_rng_used_domains=("torch_cpu",),
            cpu_rng_state_restored=rng_restored,
            all_probe_rng_domains_restored=rng_restored,
            global_rng_restored=rng_restored,
            probe_model_mode="train",
            no_grad_used=True,
            optimizer_created=False,
            backward_called=False,
            optimizer_step_called=False,
            stateful_train_mode_layer_blocker_found=False,
        )
    except BaseException as error:
        _public_error(error)


def _probe_float_series_v1(
    result: CovapieCurrent11DeterministicExact5ProbeResultV1,
) -> dict[str, tuple[float, ...]]:
    epochs = result.epoch_results
    return {
        "probe_base": tuple(epoch.loss_base_diffusion for epoch in epochs)
        + (result.probe_base_mean,),
        "probe_pair": tuple(
            epoch.loss_covalent_pair_prediction for epoch in epochs
        ) + (result.probe_pair_mean,),
        "probe_geometry": tuple(
            epoch.loss_pre_post_geometry for epoch in epochs
        ) + (result.probe_geometry_mean,),
        "probe_contrastive": tuple(
            epoch.loss_covalent_pair_contrastive for epoch in epochs
        ) + (result.probe_contrastive_mean,),
        "probe_total": tuple(epoch.loss_total for epoch in epochs)
        + (result.probe_total_mean,),
        "pair_positive_logit": tuple(
            epoch.pair_positive_logit_mean for epoch in epochs
        ) + (result.pair_positive_logit_mean,),
        "pair_negative_logit": tuple(
            epoch.pair_negative_logit_mean for epoch in epochs
        ) + (result.pair_negative_logit_mean,),
        "pair_margin": tuple(epoch.pair_margin_mean for epoch in epochs)
        + (result.pair_margin_mean,),
        "pair_rank": tuple(epoch.pair_rank_mean for epoch in epochs)
        + (result.pair_rank_mean,),
        "pair_top1": tuple(epoch.pair_top1_accuracy for epoch in epochs)
        + (result.pair_top1_accuracy,),
    }


def _result_integrity_v1(
    result: object,
) -> bool:
    if not isinstance(result, CovapieCurrent11DeterministicExact5ProbeResultV1):
        return False
    epochs = result.epoch_results
    float_series = _probe_float_series_v1(result)
    macro_matches = all((
        result.probe_base_mean
        == _mean_epoch_field_v1(epochs, "loss_base_diffusion"),
        result.probe_pair_mean
        == _mean_epoch_field_v1(epochs, "loss_covalent_pair_prediction"),
        result.probe_geometry_mean
        == _mean_epoch_field_v1(epochs, "loss_pre_post_geometry"),
        result.probe_contrastive_mean
        == _mean_epoch_field_v1(epochs, "loss_covalent_pair_contrastive"),
        result.probe_total_mean == _mean_epoch_field_v1(epochs, "loss_total"),
        result.pair_positive_logit_mean
        == _mean_epoch_field_v1(epochs, "pair_positive_logit_mean"),
        result.pair_negative_logit_mean
        == _mean_epoch_field_v1(epochs, "pair_negative_logit_mean"),
        result.pair_margin_mean == _mean_epoch_field_v1(epochs, "pair_margin_mean"),
        result.pair_rank_mean == _mean_epoch_field_v1(epochs, "pair_rank_mean"),
        result.pair_top1_accuracy
        == _mean_epoch_field_v1(epochs, "pair_top1_accuracy"),
    ))
    return (
        result.schema_version == BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1
        and len(epochs) == 5
        and result.sample_task_evaluation_count == 55
        and result.probe_seed >= 0
        and len(set(result.derived_epoch_seeds)) == 5
        and all(0 <= seed <= 2**63 - 1 for seed in result.derived_epoch_seeds)
        and result.derived_epoch_seeds
        == tuple(epoch.derived_epoch_seed for epoch in epochs)
        and tuple(epoch.probe_epoch for epoch in epochs)
        == BOUNDED_LEARNING_SIGNAL_PROBE_EPOCHS_V1
        and all(epoch.schema_version == result.schema_version for epoch in epochs)
        and all(epoch.canonical_task_ids == _EXPECTED_TASK_VECTORS_V1[index]
                for index, epoch in enumerate(epochs))
        and all(len(epoch.diffusion_timesteps) == 11 for epoch in epochs)
        and all(epoch.geometry_head_forward for epoch in epochs)
        and all(epoch.geometry_predictions_finite for epoch in epochs)
        and all(epoch.geometry_formal_weight == 0.0 for epoch in epochs)
        and all(epoch.loss_pre_post_geometry == 0.0 for epoch in epochs)
        and all(epoch.pre_post_geometry_valid_sample_count == 0 for epoch in epochs)
        and result.probe_geometry_mean == 0.0
        and macro_matches
        and all(
            math.isfinite(value)
            for series in float_series.values()
            for value in series
        )
        and all((
            result.parameter_unchanged,
            result.buffer_unchanged,
            result.gradient_state_unchanged,
            result.mode_flags_restored,
            result.batch_unchanged,
            result.trainer_counters_unchanged,
            result.cpu_rng_state_restored,
            result.all_probe_rng_domains_restored,
            result.global_rng_restored,
            result.no_grad_used,
        ))
        and result.probe_rng_used_domains == ("torch_cpu",)
        and result.probe_model_mode == "train"
        and not any((
            result.optimizer_created,
            result.backward_called,
            result.optimizer_step_called,
            result.stateful_train_mode_layer_blocker_found,
        ))
    )


def _exact_repeatability_evidence_v1(
    first: CovapieCurrent11DeterministicExact5ProbeResultV1,
    second: CovapieCurrent11DeterministicExact5ProbeResultV1,
) -> bool:
    top_level = (
        first.schema_version == second.schema_version,
        first.probe_seed == second.probe_seed,
        first.derived_epoch_seeds == second.derived_epoch_seeds,
        first.sample_task_evaluation_count == second.sample_task_evaluation_count,
        first.input_configuration_fingerprint_before
        == second.input_configuration_fingerprint_before,
        first.input_configuration_fingerprint_after
        == second.input_configuration_fingerprint_after,
        first.parameter_digest_before == second.parameter_digest_before,
        first.buffer_digest_before == second.buffer_digest_before,
        first.gradient_digest_before == second.gradient_digest_before,
        first.mode_digest_before == second.mode_digest_before,
        first.batch_tensor_digest_before == second.batch_tensor_digest_before,
        first.trainer_counter_digest_before
        == second.trainer_counter_digest_before,
        first.probe_rng_used_domains == second.probe_rng_used_domains,
    )
    epoch_equal = all(
        (
            left.schema_version,
            left.probe_epoch,
            left.derived_epoch_seed,
            left.canonical_task_ids,
            left.diffusion_timesteps,
            left.effective_sampled_epsilon_sha256,
            left.base_diffusion_valid_sample_count,
            left.covalent_pair_prediction_valid_sample_count,
            left.pre_post_geometry_valid_sample_count,
            left.covalent_pair_contrastive_valid_sample_count,
            left.geometry_head_forward,
            left.geometry_predictions_finite,
            left.geometry_formal_weight,
            left.target_pair_consistency,
            left.pair_candidate_consistency,
            left.pair_rank_by_sample,
            left.pair_top1_by_sample,
        )
        == (
            right.schema_version,
            right.probe_epoch,
            right.derived_epoch_seed,
            right.canonical_task_ids,
            right.diffusion_timesteps,
            right.effective_sampled_epsilon_sha256,
            right.base_diffusion_valid_sample_count,
            right.covalent_pair_prediction_valid_sample_count,
            right.pre_post_geometry_valid_sample_count,
            right.covalent_pair_contrastive_valid_sample_count,
            right.geometry_head_forward,
            right.geometry_predictions_finite,
            right.geometry_formal_weight,
            right.target_pair_consistency,
            right.pair_candidate_consistency,
            right.pair_rank_by_sample,
            right.pair_top1_by_sample,
        )
        for left, right in zip(first.epoch_results, second.epoch_results, strict=True)
    )
    return all(top_level) and epoch_equal


def validate_covapie_current11_preprobe_repeatability_v1(
    *,
    first: CovapieCurrent11DeterministicExact5ProbeResultV1,
    second: CovapieCurrent11DeterministicExact5ProbeResultV1,
) -> CovapieCurrent11ProbeRepeatabilityResultV1:
    """Validate exact discrete evidence and bounded float32 repeatability."""

    try:
        integrity = _result_integrity_v1(first) and _result_integrity_v1(second)
        exact = integrity and _exact_repeatability_evidence_v1(first, second)
        discrepancies: list[tuple[str, float]] = []
        within_limits = True
        if integrity:
            first_series = _probe_float_series_v1(first)
            second_series = _probe_float_series_v1(second)
            for metric in _FLOAT_METRIC_FIELDS_V1:
                pairs = tuple(
                    zip(first_series[metric], second_series[metric], strict=True)
                )
                if any(not math.isfinite(value) for pair in pairs for value in pair):
                    maximum = float("inf")
                    within_limits = False
                else:
                    maximum = max(abs(left - right) for left, right in pairs)
                    within_limits = within_limits and all(
                        abs(left - right)
                        <= 8 * _EPS32_V1 * max(1.0, abs(left), abs(right))
                        for left, right in pairs
                    )
                discrepancies.append((metric, maximum))
        else:
            discrepancies = [
                (metric, float("inf")) for metric in _FLOAT_METRIC_FIELDS_V1
            ]
            within_limits = False
        repeatable = exact and within_limits
        return CovapieCurrent11ProbeRepeatabilityResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            repeatable=repeatable,
            outcome=(
                "LEARNING_SIGNAL_PASS" if repeatable else "PROBE_NONDETERMINISTIC"
            ),
            exact_evidence_equal=exact,
            maximum_absolute_discrepancies=tuple(discrepancies),
        )
    except BaseException as error:
        _public_error(error)


def _same_fixed_probe_evidence_v1(
    before: CovapieCurrent11DeterministicExact5ProbeResultV1,
    after: CovapieCurrent11DeterministicExact5ProbeResultV1,
) -> bool:
    if (
        before.schema_version != after.schema_version
        or before.probe_seed != after.probe_seed
        or before.derived_epoch_seeds != after.derived_epoch_seeds
        or before.input_configuration_fingerprint_before
        != after.input_configuration_fingerprint_before
        or before.buffer_digest_before != after.buffer_digest_before
        or before.batch_tensor_digest_before != after.batch_tensor_digest_before
    ):
        return False
    return all(
        (
            left.probe_epoch,
            left.derived_epoch_seed,
            left.canonical_task_ids,
            left.diffusion_timesteps,
            left.effective_sampled_epsilon_sha256,
            left.base_diffusion_valid_sample_count,
            left.covalent_pair_prediction_valid_sample_count,
            left.pre_post_geometry_valid_sample_count,
            left.covalent_pair_contrastive_valid_sample_count,
            left.geometry_head_forward,
            left.geometry_predictions_finite,
            left.geometry_formal_weight,
            left.target_pair_consistency,
            left.pair_candidate_consistency,
        )
        == (
            right.probe_epoch,
            right.derived_epoch_seed,
            right.canonical_task_ids,
            right.diffusion_timesteps,
            right.effective_sampled_epsilon_sha256,
            right.base_diffusion_valid_sample_count,
            right.covalent_pair_prediction_valid_sample_count,
            right.pre_post_geometry_valid_sample_count,
            right.covalent_pair_contrastive_valid_sample_count,
            right.geometry_head_forward,
            right.geometry_predictions_finite,
            right.geometry_formal_weight,
            right.target_pair_consistency,
            right.pair_candidate_consistency,
        )
        for left, right in zip(before.epoch_results, after.epoch_results, strict=True)
    )


def compare_covapie_current11_learning_signal_v1(
    *,
    before: CovapieCurrent11DeterministicExact5ProbeResultV1,
    repeated_before: CovapieCurrent11DeterministicExact5ProbeResultV1,
    after: CovapieCurrent11DeterministicExact5ProbeResultV1,
) -> CovapieCurrent11LearningSignalDecisionV1:
    """Apply frozen V1 tolerances and the exact five-outcome vocabulary."""

    try:
        repeatability = validate_covapie_current11_preprobe_repeatability_v1(
            first=before, second=repeated_before
        )
        empty = CovapieCurrent11LearningSignalDecisionV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="PROBE_NONDETERMINISTIC",
            tolerances=(),
            improvements=(),
            total_criterion_passed=False,
            covalent_criterion_passed=False,
            geometry_in_acceptance=False,
        )
        if not repeatability.repeatable:
            return empty
        if isinstance(after, CovapieCurrent11DeterministicExact5ProbeResultV1):
            after_scalars = tuple(
                value
                for series in _probe_float_series_v1(after).values()
                for value in series
            )
            if any(not math.isfinite(value) for value in after_scalars):
                return CovapieCurrent11LearningSignalDecisionV1(
                    schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
                    outcome="TRAINING_FAILED",
                    tolerances=(),
                    improvements=(),
                    total_criterion_passed=False,
                    covalent_criterion_passed=False,
                    geometry_in_acceptance=False,
                )
        if (
            not _result_integrity_v1(after)
            or not _same_fixed_probe_evidence_v1(before, after)
        ):
            return empty
        macro = {
            "probe_total": (before.probe_total_mean, after.probe_total_mean),
            "probe_base": (before.probe_base_mean, after.probe_base_mean),
            "probe_pair": (before.probe_pair_mean, after.probe_pair_mean),
            "probe_contrastive": (
                before.probe_contrastive_mean,
                after.probe_contrastive_mean,
            ),
            "pair_margin": (before.pair_margin_mean, after.pair_margin_mean),
        }
        if any(not math.isfinite(value) for pair in macro.values() for value in pair):
            return CovapieCurrent11LearningSignalDecisionV1(
                schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
                outcome="TRAINING_FAILED",
                tolerances=(),
                improvements=(),
                total_criterion_passed=False,
                covalent_criterion_passed=False,
                geometry_in_acceptance=False,
            )
        repeat_discrepancies = dict(repeatability.maximum_absolute_discrepancies)
        tolerances = {
            metric: max(
                10 * repeat_discrepancies[metric],
                1e-6 + 1e-5 * abs(macro[metric][0]),
            )
            for metric in _LEARNING_METRICS_V1
        }
        improvements = {
            metric: (
                macro[metric][1] - macro[metric][0]
                if metric == "pair_margin"
                else macro[metric][0] - macro[metric][1]
            )
            for metric in _LEARNING_METRICS_V1
        }
        passed = {
            metric: (
                macro[metric][1] > macro[metric][0] + tolerances[metric]
                if metric == "pair_margin"
                else macro[metric][1] < macro[metric][0] - tolerances[metric]
            )
            for metric in _LEARNING_METRICS_V1
        }
        total_passed = passed["probe_total"]
        covalent_passed = any((
            passed["probe_pair"],
            passed["probe_contrastive"],
            passed["pair_margin"],
        ))
        if total_passed and covalent_passed:
            outcome = "LEARNING_SIGNAL_PASS"
        elif any(passed.values()):
            outcome = "LEARNING_SIGNAL_WEAK"
        else:
            outcome = "NO_LEARNING_SIGNAL"
        return CovapieCurrent11LearningSignalDecisionV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome=outcome,
            tolerances=tuple((metric, tolerances[metric]) for metric in _LEARNING_METRICS_V1),
            improvements=tuple((metric, improvements[metric]) for metric in _LEARNING_METRICS_V1),
            total_criterion_passed=total_passed,
            covalent_criterion_passed=covalent_passed,
            geometry_in_acceptance=False,
        )
    except BaseException as error:
        _public_error(error)


def _build_formal_probe_session_and_batch_v1(
    *, repository_root: Path, state_root: Path, legacy_init_checkpoint: Path,
) -> tuple[object, dict[str, object]]:
    from covalent_ext.covapie_current11_formal_trainer_v1 import (
        build_covapie_current11_formal_train_only_session_v1,
    )

    session = build_covapie_current11_formal_train_only_session_v1(
        repository_root=repository_root,
        state_root=state_root,
        legacy_init_checkpoint=legacy_init_checkpoint,
    )
    session.model.setup("fit")
    raw_batch = next(iter(session.model.train_dataloader()))
    attached_batch = session.model.on_before_batch_transfer(raw_batch, 0)
    if type(attached_batch) is not dict:
        _fail()
    return session, attached_batch


def _validate_formal_fit_postconditions_v1(session: object) -> None:
    trainer = getattr(session, "trainer", None)
    model = getattr(session, "model", None)
    if (
        trainer is None
        or not isinstance(model, nn.Module)
        or getattr(trainer, "current_epoch", None) != 5
        or getattr(trainer, "global_step", None) != 5
        or any(not bool(torch.isfinite(parameter).all().item())
               for parameter in model.parameters())
    ):
        _fail()


def run_covapie_current11_bounded_learning_signal_experiment_v1(
    *,
    repository_root: Path,
    state_root: Path,
    legacy_init_checkpoint: Path,
    probe_seed: int = BOUNDED_LEARNING_SIGNAL_PROBE_DEFAULT_SEED_V1,
) -> CovapieCurrent11BoundedLearningSignalExperimentResultV1:
    """Orchestrate the one-fit experiment; callers must explicitly invoke it."""

    base_seed = _require_probe_seed_v1(probe_seed)
    pre1 = None
    pre2 = None
    repeatability = None
    fit_count = 0
    fit_ckpt_none = False
    try:
        session, attached_batch = _build_formal_probe_session_and_batch_v1(
            repository_root=repository_root,
            state_root=state_root,
            legacy_init_checkpoint=legacy_init_checkpoint,
        )
        pre1 = run_covapie_current11_deterministic_exact5_probe_v1(
            model=session.model,
            attached_batch=attached_batch,
            probe_seed=base_seed,
        )
        pre2 = run_covapie_current11_deterministic_exact5_probe_v1(
            model=session.model,
            attached_batch=attached_batch,
            probe_seed=base_seed,
        )
        repeatability = validate_covapie_current11_preprobe_repeatability_v1(
            first=pre1, second=pre2
        )
        if not repeatability.repeatable:
            return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
                schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
                outcome="PROBE_NONDETERMINISTIC",
                pre1=pre1,
                pre2=pre2,
                repeatability=repeatability,
                post=None,
                decision=None,
                fit_call_count=0,
                fit_ckpt_path_was_none=False,
                training_completed=False,
                failure_stage="preprobe_repeatability",
            )
    except BaseException:
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="PROBE_NONDETERMINISTIC",
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=None,
            decision=None,
            fit_call_count=0,
            fit_ckpt_path_was_none=False,
            training_completed=False,
            failure_stage="preprobe",
        )

    fit_count += 1
    fit_ckpt_none = True
    try:
        session.trainer.fit(model=session.model, ckpt_path=None)
    except BaseException:
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="TRAINING_FAILED",
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=None,
            decision=None,
            fit_call_count=fit_count,
            fit_ckpt_path_was_none=fit_ckpt_none,
            training_completed=False,
            failure_stage="trainer_fit",
        )

    try:
        _validate_formal_fit_postconditions_v1(session)
    except BaseException:
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="TRAINING_FAILED",
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=None,
            decision=None,
            fit_call_count=fit_count,
            fit_ckpt_path_was_none=fit_ckpt_none,
            training_completed=False,
            failure_stage="formal_fit_postconditions",
        )

    try:
        post = run_covapie_current11_deterministic_exact5_probe_v1(
            model=session.model,
            attached_batch=attached_batch,
            probe_seed=base_seed,
        )
    except BaseException:
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="TRAINING_FAILED",
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=None,
            decision=None,
            fit_call_count=fit_count,
            fit_ckpt_path_was_none=fit_ckpt_none,
            training_completed=True,
            failure_stage="postprobe",
        )

    try:
        decision = compare_covapie_current11_learning_signal_v1(
            before=pre1,
            repeated_before=pre2,
            after=post,
        )
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome=decision.outcome,
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=post,
            decision=decision,
            fit_call_count=fit_count,
            fit_ckpt_path_was_none=fit_ckpt_none,
            training_completed=True,
            failure_stage=None,
        )
    except BaseException:
        return CovapieCurrent11BoundedLearningSignalExperimentResultV1(
            schema_version=BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1,
            outcome="TRAINING_FAILED",
            pre1=pre1,
            pre2=pre2,
            repeatability=repeatability,
            post=post,
            decision=None,
            fit_call_count=fit_count,
            fit_ckpt_path_was_none=fit_ckpt_none,
            training_completed=True,
            failure_stage="comparison",
        )

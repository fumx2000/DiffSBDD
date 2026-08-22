"""Current-state Lightning lifecycle integration for formal validation4 V1.

The published evaluator owns every scientific equation and reducer.  This
module only supplies a fail-closed Lightning request lifecycle and copies the
current Lightning state to an ephemeral CPU shadow before calling those bound
semantic helpers.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
import hashlib
import io
import math
from pathlib import Path
import stat
import time
from typing import Mapping, NoReturn

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, SequentialSampler

import constants
from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as instantiation_owner,
)
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as published_evaluator,
)
from covalent_ext.checkpoint_compatible_model_instantiation import (
    BEST_CONFIG_CANDIDATE_PATH,
    CONFIG_PREVIEW_PATH,
    _constructor_config_from_compatible_config,
    _temporary_10d_dataset_info,
    build_checkpoint_compatible_config_v0,
    load_config_preview_v0,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.diffsbdd_model_instantiation import _constructor_kwargs


__all__ = (
    "FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1",
    "VALIDATION_MODEL_WEIGHT_SOURCE_V1",
    "PRIMARY_LIGHTNING_MONITOR_KEY_V1",
    "LIGHTNING_METRIC_KEYS_V1",
    "FormalValidation4RequestSentinelV1",
    "FORMAL_VALIDATION4_REQUEST_SENTINEL_V1",
    "CurrentStateCpuShadowCopyV1",
    "CovapieCurrent11CurrentModelFormalValidation4ResultV1",
    "CovapieCurrent11FormalValidation4LigandPocketDDPMV1",
    "build_covapie_current11_cpu_shadow_from_current_state_v1",
    "instantiate_covapie_current11_formal_validation4_lightning_model_v1",
)


FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1 = (
    "COVAPIE_CURRENT11_FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_V1_ERROR"
)
VALIDATION_MODEL_WEIGHT_SOURCE_V1 = "CURRENT_LIGHTNING_MODEL_STATE"
PRIMARY_LIGHTNING_MONITOR_KEY_V1 = (
    "val/formal_validation4_event_macro_masked_conditional_vlb_nll"
)
MICRO_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_micro_masked_conditional_vlb_nll"
)
PROFILE_BALANCED_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_profile_balanced_masked_conditional_vlb_nll"
)
PAIR_BCE_LIGHTNING_METRIC_KEY_V1 = "val/formal_validation4_pair_BCE"
POST_GEOMETRY_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_POST_geometry_loss"
)
PAIR_CONTRASTIVE_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_pair_contrastive_loss"
)
POST_PREDICTION_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_POST_prediction_angstrom"
)
POST_TARGET_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_POST_target_angstrom"
)
TASK4_JOINT_LIGHTNING_METRIC_KEY_V1 = (
    "val/formal_validation4_task4_historical_joint_nll_diagnostic"
)
LIGHTNING_METRIC_KEYS_V1 = (
    PRIMARY_LIGHTNING_MONITOR_KEY_V1,
    MICRO_LIGHTNING_METRIC_KEY_V1,
    PROFILE_BALANCED_LIGHTNING_METRIC_KEY_V1,
    PAIR_BCE_LIGHTNING_METRIC_KEY_V1,
    POST_GEOMETRY_LIGHTNING_METRIC_KEY_V1,
    PAIR_CONTRASTIVE_LIGHTNING_METRIC_KEY_V1,
    POST_PREDICTION_LIGHTNING_METRIC_KEY_V1,
    POST_TARGET_LIGHTNING_METRIC_KEY_V1,
    TASK4_JOINT_LIGHTNING_METRIC_KEY_V1,
)

EXPECTED_BASELINE_HEAD_V1 = "4b60900fad41d0719b054986e94620e35e39b2ce"
EXPECTED_CURRENT_STATE_KEY_COUNT_V1 = 141
FORMAL_VALIDATION_POPULATION_IDENTITY_V1 = "FORMAL_VALIDATION4_LN5X2_PX5X2_V1"
FORMAL_VALIDATION_SENTINEL_VERSION_V1 = (
    "covapie_current11_formal_validation4_request_sentinel_v1"
)
CURRENT_ARCHITECTURE_DATASET_NAME_V1 = (
    "covapie_current11_real_one_batch_train_path_smoke_v1_10d"
)

BOUND_CURRENT_OWNER_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "3f53e1bb668dfe5751f154793ba0d4e1f1001e9619f7a8613b7df31b522be755",
    ),
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "d3d21b920785f791652cb456465a8bb375a09cdf0e24e5e84415b01f82cd6485",
    ),
    (
        "src/covalent_ext/covapie_current11_task2_lightning_module_v1.py",
        "38ed7a2b272520720935021782547f01d1d2cf36b636ce7319e6751fb54dcd98",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
    ),
    (
        "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024",
    ),
    (
        "src/covalent_ext/diffsbdd_model_instantiation.py",
        "5bc98bad19bad27a4260ce01d68194fbfe46096bd3955b7ff5e5efa4c70d5613",
    ),
    (
        "lightning_modules.py",
        "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())


class _IntegrationInvariantError(Exception):
    pass


def _fail(reason: str) -> NoReturn:
    raise _IntegrationInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error) == FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1
    ):
        raise error
    raise ValueError(FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1) from error


def _require_root(value: object, *, reason: str) -> Path:
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        _fail(reason)
    try:
        if value.resolve(strict=True) != value or not value.is_dir():
            _fail(reason)
    except OSError as error:
        raise _IntegrationInvariantError(reason) from error
    return value


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_FILE_NOT_REGULAR")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise _IntegrationInvariantError("BOUND_FILE_READ_FAILED") from error


def _verify_current_owner_bindings_v1(
    repository_root: Path,
) -> tuple[tuple[str, str], ...]:
    actual: list[tuple[str, str]] = []
    for relative, expected in BOUND_CURRENT_OWNER_SHA256_V1:
        digest = _sha256_file(repository_root / relative)
        if digest != expected:
            _fail("CURRENT_OWNER_SHA256_MISMATCH:" + relative)
        actual.append((relative, digest))
    published_evaluator._verify_bound_sources(repository_root)
    return tuple(actual)


@dataclass(frozen=True)
class FormalValidation4RequestSentinelV1:
    version: str
    formal_validation_population_identity: str
    formal_validation_event_ids: tuple[str, ...]
    primary_metric_identity: str


FORMAL_VALIDATION4_REQUEST_SENTINEL_V1 = FormalValidation4RequestSentinelV1(
    version=FORMAL_VALIDATION_SENTINEL_VERSION_V1,
    formal_validation_population_identity=FORMAL_VALIDATION_POPULATION_IDENTITY_V1,
    formal_validation_event_ids=published_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1,
    primary_metric_identity=published_evaluator.PRIMARY_METRIC_NAME_V1,
)


def _validate_formal_validation_sentinel_v1(value: object) -> None:
    if (
        type(value) is not FormalValidation4RequestSentinelV1
        or value != FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    ):
        _fail("FORMAL_VALIDATION_SENTINEL_INVALID")


class _FormalValidation4RequestDatasetV1(Dataset):
    def __init__(self) -> None:
        self.getitem_call_count = 0

    def __len__(self) -> int:
        return 1

    def __getitem__(self, index: int) -> FormalValidation4RequestSentinelV1:
        if (
            type(index) is not int
            or index != 0
            or type(self.getitem_call_count) is not int
            or self.getitem_call_count < 0
        ):
            _fail("FORMAL_VALIDATION_DATASET_ACCESS_INVALID")
        self.getitem_call_count += 1
        return FORMAL_VALIDATION4_REQUEST_SENTINEL_V1


class _FormalValidation4RequestCollatorV1:
    def __init__(self) -> None:
        self.call_count = 0

    def __call__(
        self, items: list[FormalValidation4RequestSentinelV1],
    ) -> FormalValidation4RequestSentinelV1:
        if (
            type(self.call_count) is not int
            or self.call_count < 0
            or type(items) is not list
            or len(items) != 1
        ):
            _fail("FORMAL_VALIDATION_COLLATION_INVALID")
        _validate_formal_validation_sentinel_v1(items[0])
        self.call_count += 1
        return items[0]


@dataclass(frozen=True)
class CurrentStateCpuShadowCopyV1:
    shadow_model: CovapieCurrent11TrainingLigandPocketDDPM
    current_state_key_count: int
    shadow_state_key_count: int
    missing_keys: tuple[str, ...]
    unexpected_keys: tuple[str, ...]
    shape_mismatch_count: int
    post_load_tensor_equality: bool
    current_state_copied_to_cpu: bool
    source_state_device_types: tuple[str, ...]


@dataclass(frozen=True)
class CovapieCurrent11CurrentModelFormalValidation4ResultV1:
    implementation_status: str
    primary_metric_name: str
    primary_lightning_monitor_key: str
    formal_validation_event_ids: tuple[str, ...]
    root_validation_seeds: tuple[int, ...]
    formal_validation_event_count: int
    formal_validation_task_event_count: int
    formal_validation_estimate_count: int
    formal_validation_task_slice_evaluation_count: int
    main_dynamics_task_slice_call_count: int
    t0_dynamics_task_slice_call_count: int
    total_dynamics_task_slice_call_count: int
    per_estimate_rows: tuple[published_evaluator.FormalValidationEstimateV1, ...]
    per_event_task_seed_means: tuple[
        published_evaluator.FormalValidationEventTaskMeanV1, ...
    ]
    per_event_means: tuple[published_evaluator.FormalValidationEventMeanV1, ...]
    event_macro_masked_conditional_vlb_nll: float
    micro_masked_conditional_vlb_nll: float
    profile_means: tuple[tuple[str, float], ...]
    profile_balanced_masked_conditional_vlb_nll: float
    mean_pair_BCE: float
    mean_POST_geometry_loss: float
    mean_POST_geometry_prediction_angstrom: float
    mean_POST_geometry_target_angstrom: float
    mean_pair_contrastive_loss: float
    mean_task4_historical_joint_nll_with_node_prior_diagnostic: float
    PRE_geometry_valid_count: int
    POST_geometry_valid_count: int
    primary_node_prior_included: bool
    all_applicable_primary_metrics_finite: bool
    all_applicable_auxiliary_metrics_finite: bool
    current_source_model_identity: str
    source_model_device: str
    CPU_shadow_identity: str
    validation_model_weight_source: str
    current_state_key_count: int
    shadow_state_key_count: int
    shadow_missing_keys: tuple[str, ...]
    shadow_unexpected_keys: tuple[str, ...]
    shadow_shape_mismatch_count: int
    shadow_strict_state_copy_parity: bool
    current_state_copied_to_cpu_shadow: bool
    active_model_parameters_unchanged: bool
    active_model_buffers_unchanged: bool
    active_model_gradient_states_unchanged: bool
    active_model_training_flags_unchanged: bool
    active_model_current_epoch_unchanged: bool
    active_model_optimizer_independent_state_unchanged: bool
    active_model_size_distribution_unchanged: bool
    active_model_registered_modules_unchanged: bool
    active_model_registered_parameters_unchanged: bool
    active_model_registered_buffers_unchanged: bool
    shadow_not_registered_on_active_model: bool
    shadow_eval_mode_verified: bool
    shadow_gradient_recording_disabled: bool
    metric_tensors_require_grad: bool
    historical_node_prior_source: str
    historical_node_histogram_shape: tuple[int, int]
    synthetic_node_histogram_used: bool
    checkpoint_metadata_read_count: int
    checkpoint_weight_migration_call_count_inside_validation: int
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    checkpoint_unchanged: bool
    standalone_public_wrapper_called_inside_validation: bool
    published_evaluator_helpers_reused: tuple[str, ...]
    source_bindings: tuple[tuple[str, str], ...]
    cpu_shadow_validation_architecture_supports_non_cpu_source_state: bool
    real_gpu_validation_runtime_verified: bool
    optimizer_created_during_validation: bool
    backward_performed: bool
    training_performed: bool
    runtime_elapsed_seconds: float


def _snapshot_named_tensors_cpu(
    values: Mapping[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone() for name, tensor in values.items()
    }


def _snapshot_grads_cpu(model: nn.Module) -> dict[str, torch.Tensor | None]:
    return {
        name: (
            None if parameter.grad is None
            else parameter.grad.detach().cpu().clone()
        )
        for name, parameter in model.named_parameters()
    }


def _same_named_tensor_snapshot(
    before: Mapping[str, torch.Tensor], values: Mapping[str, torch.Tensor],
) -> bool:
    return before.keys() == values.keys() and all(
        torch.equal(before[name], values[name].detach().cpu()) for name in before
    )


def _same_grad_snapshot(
    before: Mapping[str, torch.Tensor | None], model: nn.Module,
) -> bool:
    current = dict(model.named_parameters())
    if before.keys() != current.keys():
        return False
    for name, expected in before.items():
        actual = current[name].grad
        if expected is None:
            if actual is not None:
                return False
        elif actual is None or not torch.equal(expected, actual.detach().cpu()):
            return False
    return True


def _model_identity(model: nn.Module) -> str:
    return type(model).__module__ + "." + type(model).__qualname__


def _single_model_device(model: nn.Module) -> str:
    devices = {
        str(value.device)
        for value in tuple(model.parameters()) + tuple(model.buffers())
    }
    if len(devices) != 1:
        _fail("SOURCE_MODEL_DEVICE_DOMAIN_INVALID")
    return next(iter(devices))


def build_covapie_current11_cpu_shadow_from_current_state_v1(
    *,
    source_model: nn.Module,
    repository_root: Path,
    state_root: Path,
) -> CurrentStateCpuShadowCopyV1:
    """Strict-copy every current state tensor to a fresh unregistered CPU model."""

    try:
        repository = _require_root(repository_root, reason="REPOSITORY_ROOT_INVALID")
        state = _require_root(state_root, reason="STATE_ROOT_INVALID")
        if not isinstance(source_model, nn.Module):
            _fail("SOURCE_MODEL_INVALID")
        current_state = source_model.state_dict()
        if (
            type(current_state) is not dict
            and type(current_state).__name__ != "OrderedDict"
        ):
            _fail("CURRENT_STATE_DICT_INVALID")
        source_devices = tuple(sorted({value.device.type for value in current_state.values()}))
        if (
            len(current_state) != EXPECTED_CURRENT_STATE_KEY_COUNT_V1
            or any(not isinstance(value, torch.Tensor) for value in current_state.values())
        ):
            _fail("CURRENT_STATE_KEY_COUNT_OR_VALUE_INVALID")
        copied_state = {
            key: value.detach().cpu().clone() for key, value in current_state.items()
        }
        shadow = instantiation_owner._instantiate_current11_model_v1(
            repo_root=repository, state_root=state, device="cpu",
        )
        shadow_target = shadow.state_dict()
        if len(shadow_target) != EXPECTED_CURRENT_STATE_KEY_COUNT_V1:
            _fail("SHADOW_STATE_KEY_COUNT_INVALID")
        missing = tuple(sorted(set(shadow_target) - set(copied_state)))
        unexpected = tuple(sorted(set(copied_state) - set(shadow_target)))
        shared = set(copied_state) & set(shadow_target)
        shape_mismatch = sum(
            int(copied_state[key].shape != shadow_target[key].shape)
            for key in shared
        )
        if missing or unexpected or shape_mismatch:
            _fail("CURRENT_SHADOW_STATE_DOMAIN_MISMATCH")
        incompatible = shadow.load_state_dict(copied_state, strict=True)
        load_missing = tuple(incompatible.missing_keys)
        load_unexpected = tuple(incompatible.unexpected_keys)
        loaded_state = shadow.state_dict()
        parity = (
            not load_missing
            and not load_unexpected
            and tuple(loaded_state) == tuple(copied_state)
            and all(torch.equal(loaded_state[key], copied_state[key]) for key in copied_state)
        )
        if not parity:
            _fail("CURRENT_SHADOW_STRICT_LOAD_PARITY_INVALID")
        return CurrentStateCpuShadowCopyV1(
            shadow_model=shadow,
            current_state_key_count=len(copied_state),
            shadow_state_key_count=len(loaded_state),
            missing_keys=load_missing,
            unexpected_keys=load_unexpected,
            shape_mismatch_count=shape_mismatch,
            post_load_tensor_equality=True,
            current_state_copied_to_cpu=all(
                value.device.type == "cpu" for value in copied_state.values()
            ),
            source_state_device_types=source_devices,
        )
    except Exception as error:
        _public_error(error)


def _historical_node_histogram_from_checkpoint_v1(
    checkpoint_path: Path,
) -> tuple[list[list[float]], str]:
    payload = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path,
    )
    constructor = payload.get("legacy_constructor")
    histogram = (
        constructor.get("node_histogram") if type(constructor) is dict else None
    )
    if (
        type(histogram) is not list
        or len(histogram) != 107
        or any(type(row) is not list or len(row) != 1671 for row in histogram)
        or constructor.get("node_histogram_source")
        != "exact_legacy_checkpoint_hyperparameters"
        or constructor.get("synthetic_node_histogram_used") is not False
    ):
        _fail("HISTORICAL_NODE_HISTOGRAM_AUTHORITY_INVALID")
    return histogram, str(payload["checkpoint_sha256"])


def _prepare_published_formal_population_v1(
    *, repository_root: Path, cache_root: Path,
) -> tuple[object, dict[str, object], tuple[tuple[int, object], ...]]:
    authority = published_evaluator._audit_formal_authority(repository_root)
    records_all = published_evaluator.structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=repository_root, cache_root=cache_root,
    )
    by_event = {record.canonical_event_id: record for record in records_all}
    if len(records_all) != 13 or len(by_event) != 13:
        _fail("STRUCTURAL_OWNER_POPULATION_INVALID")
    records = tuple(
        by_event[event_id]
        for event_id in published_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
    )
    expected_domains = {
        "LN5": (13, 5, 3, 5, (0, 1, 2, 3, 4)),
        "PX5": (17, 9, 0, 8, (0, 3, 4)),
    }
    for record in records:
        published_evaluator.structural_owner.validate_covapie_batch001_positive_structural_record_v1(
            record
        )
        actual = (
            len(record.ligand_retained_heavy_atoms),
            len(record.scaffold_retained_local_indices),
            len(record.linker_retained_local_indices),
            len(record.warhead_retained_local_indices),
            record.applicable_canonical_task_ids,
        )
        if actual != expected_domains[record.ligand_component_id] or record.sample_training_admitted:
            _fail("VALIDATION_PROFILE_ROLE_OR_LABEL_DOMAIN_INVALID")
    return authority, by_event, published_evaluator._task_batches(records)


def _evaluate_current_model_on_cpu_shadow_v1(
    *,
    source_model: nn.Module,
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
    checkpoint_path: Path,
) -> CovapieCurrent11CurrentModelFormalValidation4ResultV1:
    started = time.perf_counter()
    bindings = _verify_current_owner_bindings_v1(repository_root)
    if checkpoint_path != repository_root / published_evaluator.CHECKPOINT_RELATIVE_PATH_V1:
        _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
    checkpoint_before = _sha256_file(checkpoint_path)
    if checkpoint_before != published_evaluator.CHECKPOINT_SHA256_V1:
        _fail("CHECKPOINT_SHA256_MISMATCH")
    if not isinstance(source_model, CovapieCurrent11FormalValidation4LigandPocketDDPMV1):
        _fail("CURRENT_LIGHTNING_MODEL_CLASS_INVALID")

    parameter_before = _snapshot_named_tensors_cpu(dict(source_model.named_parameters()))
    buffer_before = _snapshot_named_tensors_cpu(dict(source_model.named_buffers()))
    grad_before = _snapshot_grads_cpu(source_model)
    module_names_before = tuple(name for name, unused in source_model.named_modules())
    parameter_names_before = tuple(name for name, unused in source_model.named_parameters())
    buffer_names_before = tuple(name for name, unused in source_model.named_buffers())
    training_flags_before = tuple(
        (name, module.training) for name, module in source_model.named_modules()
    )
    current_epoch_before = int(source_model.current_epoch)
    optimizer_independent_state_before = (
        source_model.covapie_current11_training_enabled,
        source_model.covapie_current11_task_schedule_seed,
        source_model.covapie_current11_pair_contrastive_temperature,
        source_model.covapie_current11_authoritative_supervision_batch_field,
        id(source_model.covapie_current11_loss_weights),
        tuple(sorted(vars(source_model.covapie_current11_loss_weights).items())),
    )
    active_size_distribution = source_model.ddpm.size_distribution
    source_device = _single_model_device(source_model)
    source_identity = _model_identity(source_model)

    authority, record_by_event, batches = _prepare_published_formal_population_v1(
        repository_root=repository_root, cache_root=cache_root,
    )
    histogram, checkpoint_metadata_sha = _historical_node_histogram_from_checkpoint_v1(
        checkpoint_path
    )
    if checkpoint_metadata_sha != checkpoint_before:
        _fail("CHECKPOINT_METADATA_IDENTITY_MISMATCH")

    with published_evaluator._deterministic_cpu_context():
        torch.random.default_generator.manual_seed(
            published_evaluator.MODEL_INITIALIZATION_SEED_V1
        )
        shadow_copy = build_covapie_current11_cpu_shadow_from_current_state_v1(
            source_model=source_model,
            repository_root=repository_root,
            state_root=state_root,
        )
        shadow = shadow_copy.shadow_model
        with contextlib.redirect_stdout(io.StringIO()):
            shadow.ddpm.size_distribution = type(shadow.ddpm.size_distribution)(
                histogram
            )
        shadow.eval()
        published_evaluator.validate_formal_evaluation_module_state_v1(model=shadow)
        shadow_parameter_before = published_evaluator._snapshot_parameters(shadow)
        shadow_buffer_before = published_evaluator._snapshot_buffers(shadow)
        shadow_grad_before = published_evaluator._snapshot_grads(shadow)
        leakage_by_event = {
            event: group
            for event, unused, group in authority.validation_rows
        }
        estimates: list[published_evaluator.FormalValidationEstimateV1] = []
        main_calls = 0
        t0_calls = 0
        fixed_clean = True
        indicator_reused = True
        tensors_require_grad = False
        grad_disabled_inside = True
        with torch.inference_mode():
            grad_disabled_inside = grad_disabled_inside and not torch.is_grad_enabled()
            for root_seed in published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1:
                for task_id, preview in batches:
                    output = published_evaluator._evaluate_slice(
                        model=shadow,
                        preview=preview,
                        task_id=task_id,
                        root_seed=root_seed,
                        leakage_by_event=leakage_by_event,
                        record_by_event=record_by_event,
                    )
                    estimates.extend(output.estimates)
                    main_calls += output.main_calls
                    t0_calls += output.t0_calls
                    fixed_clean = fixed_clean and output.fixed_clean
                    indicator_reused = indicator_reused and output.indicator_reused
                    tensors_require_grad = (
                        tensors_require_grad or output.tensors_require_grad
                    )
        shadow_unchanged = (
            published_evaluator._same_snapshot(
                shadow_parameter_before,
                published_evaluator._snapshot_parameters(shadow),
            )
            and published_evaluator._same_snapshot(
                shadow_buffer_before,
                published_evaluator._snapshot_buffers(shadow),
            )
            and published_evaluator._same_grads(shadow_grad_before, shadow)
        )
        shadow_identity = _model_identity(shadow)
        shadow_eval = (
            not shadow.training
            and not shadow.ddpm.training
            and not shadow.covapie_current11_auxiliary_model_v1.training
            and not shadow.ddpm.dynamics.training
        )

    estimate_rows = tuple(estimates)
    if len(estimate_rows) != 64 or main_calls != 20 or t0_calls != 20:
        _fail("FORMAL_EXECUTION_COUNT_INVALID")
    (
        event_task_means,
        event_means,
        event_macro,
        micro,
        profile_means,
        profile_balanced,
    ) = published_evaluator._aggregate(estimate_rows)
    pair_bce = published_evaluator._means(tuple(row.pair_BCE for row in estimate_rows))
    post_geometry = published_evaluator._means(
        tuple(row.POST_geometry_loss for row in estimate_rows)
    )
    post_prediction = published_evaluator._means(
        tuple(row.POST_geometry_prediction_angstrom for row in estimate_rows)
    )
    post_target = published_evaluator._means(
        tuple(row.POST_geometry_target_angstrom for row in estimate_rows)
    )
    contrastive = published_evaluator._means(
        tuple(row.pair_contrastive_loss for row in estimate_rows)
    )
    task4_joint = published_evaluator._means(tuple(
        float(row.task4_historical_joint_nll_with_node_prior_diagnostic)
        for row in estimate_rows
        if row.task4_historical_joint_nll_with_node_prior_diagnostic is not None
    ))
    primary_values = tuple(row.masked_conditional_vlb_nll for row in estimate_rows)
    auxiliary_values = tuple(
        value
        for row in estimate_rows
        for value in (row.pair_BCE, row.POST_geometry_loss, row.pair_contrastive_loss)
    )
    partial_rows = tuple(row for row in estimate_rows if row.canonical_task_id != 4)
    task4_rows = tuple(row for row in estimate_rows if row.canonical_task_id == 4)

    parameters_unchanged = _same_named_tensor_snapshot(
        parameter_before, dict(source_model.named_parameters())
    )
    buffers_unchanged = _same_named_tensor_snapshot(
        buffer_before, dict(source_model.named_buffers())
    )
    grads_unchanged = _same_grad_snapshot(grad_before, source_model)
    modules_unchanged = module_names_before == tuple(
        name for name, unused in source_model.named_modules()
    )
    parameter_registry_unchanged = parameter_names_before == tuple(
        name for name, unused in source_model.named_parameters()
    )
    buffer_registry_unchanged = buffer_names_before == tuple(
        name for name, unused in source_model.named_buffers()
    )
    training_flags_unchanged = training_flags_before == tuple(
        (name, module.training) for name, module in source_model.named_modules()
    )
    current_epoch_unchanged = current_epoch_before == int(source_model.current_epoch)
    optimizer_independent_state_unchanged = optimizer_independent_state_before == (
        source_model.covapie_current11_training_enabled,
        source_model.covapie_current11_task_schedule_seed,
        source_model.covapie_current11_pair_contrastive_temperature,
        source_model.covapie_current11_authoritative_supervision_batch_field,
        id(source_model.covapie_current11_loss_weights),
        tuple(sorted(vars(source_model.covapie_current11_loss_weights).items())),
    )
    size_distribution_unchanged = source_model.ddpm.size_distribution is active_size_distribution
    checkpoint_after = _sha256_file(checkpoint_path)
    finite_values = (
        event_macro,
        micro,
        profile_balanced,
        pair_bce,
        post_geometry,
        post_prediction,
        post_target,
        contrastive,
        task4_joint,
    )
    partial_dimensions_exact = all(
        row.coordinate_dimension == 3 * row.generated_atom_count
        for row in partial_rows
    )
    task4_dimensions_exact = all(
        row.coordinate_dimension == 3 * (row.generated_atom_count - 1)
        for row in task4_rows
    )
    readiness = (
        shadow_copy.current_state_key_count == EXPECTED_CURRENT_STATE_KEY_COUNT_V1
        and shadow_copy.shadow_state_key_count == EXPECTED_CURRENT_STATE_KEY_COUNT_V1
        and not shadow_copy.missing_keys
        and not shadow_copy.unexpected_keys
        and shadow_copy.shape_mismatch_count == 0
        and shadow_copy.post_load_tensor_equality
        and shadow_copy.current_state_copied_to_cpu
        and parameters_unchanged
        and buffers_unchanged
        and grads_unchanged
        and modules_unchanged
        and parameter_registry_unchanged
        and buffer_registry_unchanged
        and training_flags_unchanged
        and current_epoch_unchanged
        and optimizer_independent_state_unchanged
        and size_distribution_unchanged
        and shadow_unchanged
        and shadow_eval
        and grad_disabled_inside
        and not tensors_require_grad
        and fixed_clean
        and indicator_reused
        and partial_dimensions_exact
        and task4_dimensions_exact
        and all(1 <= row.main_timestep_int <= 500 for row in estimate_rows)
        and sum(int(row.PRE_geometry_valid) for row in estimate_rows) == 0
        and all(math.isfinite(value) for value in finite_values + primary_values + auxiliary_values)
        and checkpoint_after == checkpoint_before
    )
    if not readiness:
        _fail("CURRENT_MODEL_FORMAL_VALIDATION_READINESS_INVALID")

    return CovapieCurrent11CurrentModelFormalValidation4ResultV1(
        implementation_status="passed",
        primary_metric_name=published_evaluator.PRIMARY_METRIC_NAME_V1,
        primary_lightning_monitor_key=PRIMARY_LIGHTNING_MONITOR_KEY_V1,
        formal_validation_event_ids=published_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1,
        root_validation_seeds=published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1,
        formal_validation_event_count=4,
        formal_validation_task_event_count=16,
        formal_validation_estimate_count=64,
        formal_validation_task_slice_evaluation_count=20,
        main_dynamics_task_slice_call_count=main_calls,
        t0_dynamics_task_slice_call_count=t0_calls,
        total_dynamics_task_slice_call_count=main_calls + t0_calls,
        per_estimate_rows=estimate_rows,
        per_event_task_seed_means=event_task_means,
        per_event_means=event_means,
        event_macro_masked_conditional_vlb_nll=event_macro,
        micro_masked_conditional_vlb_nll=micro,
        profile_means=profile_means,
        profile_balanced_masked_conditional_vlb_nll=profile_balanced,
        mean_pair_BCE=pair_bce,
        mean_POST_geometry_loss=post_geometry,
        mean_POST_geometry_prediction_angstrom=post_prediction,
        mean_POST_geometry_target_angstrom=post_target,
        mean_pair_contrastive_loss=contrastive,
        mean_task4_historical_joint_nll_with_node_prior_diagnostic=task4_joint,
        PRE_geometry_valid_count=0,
        POST_geometry_valid_count=64,
        primary_node_prior_included=False,
        all_applicable_primary_metrics_finite=True,
        all_applicable_auxiliary_metrics_finite=True,
        current_source_model_identity=source_identity,
        source_model_device=source_device,
        CPU_shadow_identity=shadow_identity,
        validation_model_weight_source=VALIDATION_MODEL_WEIGHT_SOURCE_V1,
        current_state_key_count=shadow_copy.current_state_key_count,
        shadow_state_key_count=shadow_copy.shadow_state_key_count,
        shadow_missing_keys=shadow_copy.missing_keys,
        shadow_unexpected_keys=shadow_copy.unexpected_keys,
        shadow_shape_mismatch_count=shadow_copy.shape_mismatch_count,
        shadow_strict_state_copy_parity=shadow_copy.post_load_tensor_equality,
        current_state_copied_to_cpu_shadow=shadow_copy.current_state_copied_to_cpu,
        active_model_parameters_unchanged=parameters_unchanged,
        active_model_buffers_unchanged=buffers_unchanged,
        active_model_gradient_states_unchanged=grads_unchanged,
        active_model_training_flags_unchanged=training_flags_unchanged,
        active_model_current_epoch_unchanged=current_epoch_unchanged,
        active_model_optimizer_independent_state_unchanged=(
            optimizer_independent_state_unchanged
        ),
        active_model_size_distribution_unchanged=size_distribution_unchanged,
        active_model_registered_modules_unchanged=modules_unchanged,
        active_model_registered_parameters_unchanged=parameter_registry_unchanged,
        active_model_registered_buffers_unchanged=buffer_registry_unchanged,
        shadow_not_registered_on_active_model=modules_unchanged,
        shadow_eval_mode_verified=shadow_eval,
        shadow_gradient_recording_disabled=grad_disabled_inside,
        metric_tensors_require_grad=tensors_require_grad,
        historical_node_prior_source="exact_legacy_checkpoint_hyperparameters",
        historical_node_histogram_shape=(107, 1671),
        synthetic_node_histogram_used=False,
        checkpoint_metadata_read_count=1,
        checkpoint_weight_migration_call_count_inside_validation=0,
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        checkpoint_unchanged=True,
        standalone_public_wrapper_called_inside_validation=False,
        published_evaluator_helpers_reused=(
            "_audit_formal_authority",
            "_task_batches",
            "_evaluate_slice",
            "_aggregate",
        ),
        source_bindings=bindings,
        cpu_shadow_validation_architecture_supports_non_cpu_source_state=True,
        real_gpu_validation_runtime_verified=False,
        optimizer_created_during_validation=False,
        backward_performed=False,
        training_performed=False,
        runtime_elapsed_seconds=time.perf_counter() - started,
    )


class CovapieCurrent11FormalValidation4LigandPocketDDPMV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Add only the formal validation4 lifecycle to the Current11 model."""

    validation_epoch_end = None

    def __init__(
        self,
        *args: object,
        covapie_current11_formal_validation4_cache_root: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        repository = Path(self.covapie_repository_root)
        state = Path(self.covapie_state_root)
        cache = (
            state / "bulk-multisource-cys-sg-v1/rcsb"
            if covapie_current11_formal_validation4_cache_root is None
            else Path(covapie_current11_formal_validation4_cache_root)
        )
        self._covapie_formal_validation4_repository_root_v1 = repository
        self._covapie_formal_validation4_state_root_v1 = state
        self._covapie_formal_validation4_cache_root_v1 = cache
        self._covapie_formal_validation4_checkpoint_path_v1 = (
            repository / published_evaluator.CHECKPOINT_RELATIVE_PATH_V1
        )
        self._covapie_formal_validation4_last_result_v1 = None
        self._covapie_formal_validation4_request_dataset_v1 = None
        self._covapie_formal_validation4_request_collator_v1 = None
        self._covapie_formal_validation4_lifecycle_counts_v1 = {
            "setup_validate": 0,
            "validation_dataloader": 0,
            "validation_step": 0,
            "training_step": 0,
            "test_step": 0,
            "sentinel_before_transfer": 0,
            "sentinel_transfer_to_device": 0,
        }
        self._covapie_formal_validation4_validation_run_active_v1 = False
        self._covapie_formal_validation4_validation_run_count_v1 = 0
        self._covapie_formal_validation4_current_run_step_count_v1 = 0
        self._covapie_formal_validation4_completed_run_step_counts_v1 = []
        if len(self.state_dict()) != EXPECTED_CURRENT_STATE_KEY_COUNT_V1:
            raise ValueError(FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1)

    def _prepare_formal_validation4_lifecycle_v1(self) -> None:
        repository = _require_root(
            self._covapie_formal_validation4_repository_root_v1,
            reason="REPOSITORY_ROOT_INVALID",
        )
        _require_root(
            self._covapie_formal_validation4_state_root_v1,
            reason="STATE_ROOT_INVALID",
        )
        _require_root(
            self._covapie_formal_validation4_cache_root_v1,
            reason="CACHE_ROOT_INVALID",
        )
        _verify_current_owner_bindings_v1(repository)
        dataset = self._covapie_formal_validation4_request_dataset_v1
        collator = self._covapie_formal_validation4_request_collator_v1
        if dataset is None and collator is None:
            self._covapie_formal_validation4_request_dataset_v1 = (
                _FormalValidation4RequestDatasetV1()
            )
            self._covapie_formal_validation4_request_collator_v1 = (
                _FormalValidation4RequestCollatorV1()
            )
            return
        if (
            type(dataset) is not _FormalValidation4RequestDatasetV1
            or type(collator) is not _FormalValidation4RequestCollatorV1
            or type(dataset.getitem_call_count) is not int
            or dataset.getitem_call_count < 0
            or type(collator.call_count) is not int
            or collator.call_count < 0
        ):
            _fail("FORMAL_VALIDATION_LIFECYCLE_PREPARATION_STATE_INVALID")

    def setup(self, stage: str | None = None) -> None:
        try:
            if stage == "validate":
                self._prepare_formal_validation4_lifecycle_v1()
                self._covapie_formal_validation4_lifecycle_counts_v1[
                    "setup_validate"
                ] += 1
                if (
                    self.train_dataset is not None
                    or self.val_dataset is not None
                    or self.test_dataset is not None
                ):
                    _fail("VALIDATE_SETUP_CREATED_MOLECULAR_DATASET")
                return None
            result = super().setup(stage)
            if stage == "fit":
                self._prepare_formal_validation4_lifecycle_v1()
            return result
        except Exception as error:
            _public_error(error)

    def val_dataloader(self) -> DataLoader:
        try:
            dataset = self._covapie_formal_validation4_request_dataset_v1
            collator = self._covapie_formal_validation4_request_collator_v1
            counts = self._covapie_formal_validation4_lifecycle_counts_v1
            if (
                type(dataset) is not _FormalValidation4RequestDatasetV1
                or type(collator) is not _FormalValidation4RequestCollatorV1
                or type(counts["validation_dataloader"]) is not int
                or counts["validation_dataloader"] < 0
            ):
                _fail("VALIDATION_DATALOADER_STATE_INVALID")
            counts["validation_dataloader"] += 1
            loader = DataLoader(
                dataset,
                batch_size=1,
                shuffle=False,
                num_workers=0,
                collate_fn=collator,
                pin_memory=False,
                drop_last=False,
                persistent_workers=False,
            )
            if (
                len(dataset) != 1
                or len(loader) != 1
                or loader.batch_size != 1
                or loader.num_workers != 0
                or loader.drop_last is not False
                or loader.pin_memory is not False
                or loader.persistent_workers is not False
                or type(loader.sampler) is not SequentialSampler
            ):
                _fail("VALIDATION_DATALOADER_CONTRACT_INVALID")
            return loader
        except Exception as error:
            _public_error(error)

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int,
    ) -> object:
        if type(batch) is FormalValidation4RequestSentinelV1:
            try:
                _validate_formal_validation_sentinel_v1(batch)
                if type(dataloader_idx) is not int or dataloader_idx != 0:
                    _fail("SENTINEL_DATALOADER_INDEX_INVALID")
                self._covapie_formal_validation4_lifecycle_counts_v1[
                    "sentinel_before_transfer"
                ] += 1
                return batch
            except Exception as error:
                _public_error(error)
        return super().on_before_batch_transfer(batch, dataloader_idx)

    def transfer_batch_to_device(
        self, batch: object, device: torch.device, dataloader_idx: int,
    ) -> object:
        if type(batch) is FormalValidation4RequestSentinelV1:
            try:
                _validate_formal_validation_sentinel_v1(batch)
                if (
                    not isinstance(device, torch.device)
                    or type(dataloader_idx) is not int
                    or dataloader_idx != 0
                ):
                    _fail("SENTINEL_DEVICE_TRANSFER_ARGUMENT_INVALID")
                self._covapie_formal_validation4_lifecycle_counts_v1[
                    "sentinel_transfer_to_device"
                ] += 1
                return batch
            except Exception as error:
                _public_error(error)
        return super().transfer_batch_to_device(batch, device, dataloader_idx)

    def on_validation_epoch_start(self) -> None:
        try:
            active = self._covapie_formal_validation4_validation_run_active_v1
            run_count = self._covapie_formal_validation4_validation_run_count_v1
            current_steps = (
                self._covapie_formal_validation4_current_run_step_count_v1
            )
            completed = (
                self._covapie_formal_validation4_completed_run_step_counts_v1
            )
            if (
                type(active) is not bool
                or active
                or type(run_count) is not int
                or run_count < 0
                or type(current_steps) is not int
                or current_steps < 0
                or type(completed) is not list
                or len(completed) != run_count
                or any(type(value) is not int or value != 1 for value in completed)
            ):
                _fail("VALIDATION_RUN_START_STATE_INVALID")
            self._covapie_formal_validation4_validation_run_active_v1 = True
            self._covapie_formal_validation4_validation_run_count_v1 += 1
            self._covapie_formal_validation4_current_run_step_count_v1 = 0
        except Exception as error:
            _public_error(error)

    def on_validation_epoch_end(self) -> None:
        try:
            active = self._covapie_formal_validation4_validation_run_active_v1
            current_steps = (
                self._covapie_formal_validation4_current_run_step_count_v1
            )
            completed = (
                self._covapie_formal_validation4_completed_run_step_counts_v1
            )
            run_count = self._covapie_formal_validation4_validation_run_count_v1
            if (
                active is not True
                or type(current_steps) is not int
                or current_steps != 1
                or type(completed) is not list
                or len(completed) != run_count - 1
            ):
                _fail("VALIDATION_RUN_END_STATE_INVALID")
            completed.append(current_steps)
            self._covapie_formal_validation4_validation_run_active_v1 = False
        except Exception as error:
            _public_error(error)

    def validation_step(
        self,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> dict[str, torch.Tensor]:
        try:
            _validate_formal_validation_sentinel_v1(batch)
            counts = self._covapie_formal_validation4_lifecycle_counts_v1
            if (
                type(batch_idx) is not int
                or batch_idx != 0
                or type(dataloader_idx) is not int
                or dataloader_idx != 0
                or self._covapie_formal_validation4_validation_run_active_v1
                is not True
                or type(
                    self._covapie_formal_validation4_current_run_step_count_v1
                ) is not int
                or self._covapie_formal_validation4_current_run_step_count_v1
                != 0
                or self.training is not False
                or torch.is_grad_enabled()
            ):
                _fail("FORMAL_VALIDATION_STEP_CONTEXT_INVALID")
            self._covapie_formal_validation4_current_run_step_count_v1 += 1
            counts["validation_step"] += 1
            result = _evaluate_current_model_on_cpu_shadow_v1(
                source_model=self,
                repository_root=self._covapie_formal_validation4_repository_root_v1,
                state_root=self._covapie_formal_validation4_state_root_v1,
                cache_root=self._covapie_formal_validation4_cache_root_v1,
                checkpoint_path=self._covapie_formal_validation4_checkpoint_path_v1,
            )
            values = (
                result.event_macro_masked_conditional_vlb_nll,
                result.micro_masked_conditional_vlb_nll,
                result.profile_balanced_masked_conditional_vlb_nll,
                result.mean_pair_BCE,
                result.mean_POST_geometry_loss,
                result.mean_pair_contrastive_loss,
                result.mean_POST_geometry_prediction_angstrom,
                result.mean_POST_geometry_target_angstrom,
                result.mean_task4_historical_joint_nll_with_node_prior_diagnostic,
            )
            if any(not math.isfinite(value) for value in values):
                _fail("LIGHTNING_METRIC_NONFINITE")
            metric_tensors = {
                key: torch.tensor(value, dtype=torch.float64, device=self.device)
                for key, value in zip(LIGHTNING_METRIC_KEYS_V1, values, strict=True)
            }
            module_names_before_log = tuple(
                name for name, unused in self.named_modules()
            )
            parameter_names_before_log = tuple(
                name for name, unused in self.named_parameters()
            )
            buffer_names_before_log = tuple(
                name for name, unused in self.named_buffers()
            )
            for key, value in metric_tensors.items():
                self.log(
                    key,
                    value,
                    on_step=False,
                    on_epoch=True,
                    sync_dist=False,
                    batch_size=4,
                )
            if (
                module_names_before_log
                != tuple(name for name, unused in self.named_modules())
                or parameter_names_before_log
                != tuple(name for name, unused in self.named_parameters())
                or buffer_names_before_log
                != tuple(name for name, unused in self.named_buffers())
            ):
                _fail("LIGHTNING_LOGGING_MUTATED_MODEL_REGISTRY")
            self._covapie_formal_validation4_last_result_v1 = result
            return metric_tensors
        except Exception as error:
            _public_error(error)


def instantiate_covapie_current11_formal_validation4_lightning_model_v1(
    *, repository_root: Path, state_root: Path, cache_root: Path,
) -> CovapieCurrent11FormalValidation4LigandPocketDDPMV1:
    """Instantiate the exact current architecture as the additive subclass."""

    try:
        repository = _require_root(repository_root, reason="REPOSITORY_ROOT_INVALID")
        state = _require_root(state_root, reason="STATE_ROOT_INVALID")
        cache = _require_root(cache_root, reason="CACHE_ROOT_INVALID")
        _verify_current_owner_bindings_v1(repository)
        preview_result = load_config_preview_v0(repository / CONFIG_PREVIEW_PATH)
        if preview_result.get("config_preview_loaded") is not True:
            _fail("CONFIG_PREVIEW_INVALID")
        compatible = build_checkpoint_compatible_config_v0(
            preview_result["preview"], repository / BEST_CONFIG_CANDIDATE_PATH
        )
        relevant = compatible.get("compatible_config_flattened_relevant_fields")
        if (
            compatible.get("compatible_config_built") is not True
            or type(relevant) is not dict
            or relevant.get("mode") != "pocket_conditioning"
            or relevant.get("pocket_representation") != "full-atom"
            or relevant.get("virtual_nodes") is not False
            or relevant.get("egnn_params.joint_nf") != 32
            or relevant.get("egnn_params.hidden_nf") != 128
            or relevant.get("egnn_params.n_layers") != 5
        ):
            _fail("CURRENT_ARCHITECTURE_CONFIG_INVALID")
        config = _constructor_config_from_compatible_config(
            compatible, CURRENT_ARCHITECTURE_DATASET_NAME_V1, "cpu"
        )
        config["batch_size"] = 11
        kwargs = _constructor_kwargs(config)
        kwargs.update({
            "target_residue_atom_conditioning": True,
            "covapie_current11_task2_runtime_enabled": True,
            "covapie_repository_root": str(repository),
            "covapie_state_root": str(state),
            "covapie_current11_formal_validation4_cache_root": str(cache),
        })
        previous = constants.dataset_params.get(CURRENT_ARCHITECTURE_DATASET_NAME_V1)
        constants.dataset_params[CURRENT_ARCHITECTURE_DATASET_NAME_V1] = (
            _temporary_10d_dataset_info()
        )
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                model = CovapieCurrent11FormalValidation4LigandPocketDDPMV1(
                    **kwargs
                )
        finally:
            if previous is None:
                constants.dataset_params.pop(CURRENT_ARCHITECTURE_DATASET_NAME_V1, None)
            else:
                constants.dataset_params[CURRENT_ARCHITECTURE_DATASET_NAME_V1] = previous
        model = model.to(torch.device("cpu"))
        if (
            model.mode != "pocket_conditioning"
            or model.pocket_representation != "full-atom"
            or model.atom_nf != 10
            or model.aa_nf != 10
            or model.virtual_nodes is not False
            or model.auxiliary_loss is not False
            or model.target_residue_atom_conditioning is not True
            or model.covapie_current11_task2_runtime_enabled is not True
            or len(model.state_dict()) != EXPECTED_CURRENT_STATE_KEY_COUNT_V1
        ):
            _fail("INTEGRATION_MODEL_ARCHITECTURE_INVALID")
        return model
    except Exception as error:
        _public_error(error)

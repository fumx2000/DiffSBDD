"""Bounded real train5 -> current-state formal validation4 integration V1.

This additive integration consumes the published batch001 activation boundary
for its train population, reuses the bounded Current11 train carrier adapter,
and reuses the published formal-validation sentinel and scientific evaluator.
It performs no test inference and persists no runtime result.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, fields
import hashlib
import inspect
import io
import math
from pathlib import Path
import platform
import signal
import stat
import tempfile
import time
from typing import Mapping, NoReturn, Sequence

import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

import pytorch_lightning as pl  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as forward_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_bounded_trainer_fit_smoke_v1 as bounded_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1
    as schedule_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as single_step_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as migration_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_formal_validation4_lightning_integration_v1
    as formal_validation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_formal_validation4_masked_vlb_nll_v1
    as formal_evaluator,
)
from covalent_ext import (  # noqa: E402
    covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1
    as trainer_reference,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_FORMAL_TRAIN_VALIDATION_INTEGRATION_ERROR_V1",
    "FORMAL_TRAIN_EPOCH_V1",
    "FORMAL_TASK_SCHEDULE_SEED_V1",
    "INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1",
    "CovapieBatch001FormalTrainingDataModuleV1",
    "CovapieBatch001FormalTrainValidationLigandPocketDDPMV1",
    "CovapieBatch001FormalTrainValidationIntegrationResultV1",
    "verify_covapie_batch001_formal_train_validation_source_bindings_v1",
    "build_covapie_batch001_formal_training_datamodule_v1",
    "instantiate_covapie_batch001_train_validation_model_v1",
    "run_covapie_batch001_bounded_train_validation_integration_v1",
)


BATCH001_FORMAL_TRAIN_VALIDATION_INTEGRATION_ERROR_V1 = (
    "COVAPIE_BATCH001_FORMAL_TRAINING_DATAMODULE_AND_TRAIN_VALIDATION_"
    "INTEGRATION_V1_ERROR"
)
FORMAL_TRAIN_EPOCH_V1 = 0
FORMAL_TASK_SCHEDULE_SEED_V1 = 0
RESULT_INTERPRETATION_V1 = (
    "BOUNDED_REAL_TRAIN_VALIDATION_LIFECYCLE_INTEGRATION_NOT_SCIENTIFIC_TRAINING"
)
INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1 = (
    bounded_predecessor.INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
)
CHECKPOINT_RELATIVE_PATH_V1 = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
ACTIVATION_SOURCE_SHA256_V1 = (
    "e57d2b8d75cf53cb37992a33e8e41a4075dbf94422243ad6686197722d1b48f7"
)
ACTIVATION_ARTIFACT_SHA256_V1 = (
    (
        "covapie_batch001_13event_model_usable_split_index_v1.csv",
        "f22064a20000126b0792a22e241f3cf9d912bc804da7c5f58eb2f5669157faf3",
    ),
    (
        "covapie_batch001_model_usable_split_registry_v1.json",
        "bb40624fbb88356e31d2b69d685055f6ed8ec785155a7d5ba877cc1e6cfb1540",
    ),
    (
        "covapie_batch001_model_usable_source_binding_inventory_v1.csv",
        "8cdd0572e47ff97afb407423aa221365173c6acd7a1302f7dc3fb72a1e9b1f4a",
    ),
    (
        "covapie_batch001_13event_model_usable_split_materialization_and_"
        "activation_boundary_manifest_v1.json",
        "ec92d99183810bcd98ff835b4c361ffc8a720af39286d2ff97f4c3f8ae791598",
    ),
)
BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_13event_model_usable_split_"
        "materialization_and_activation_boundary_v1.py",
        ACTIVATION_SOURCE_SHA256_V1,
    ),
    (
        "src/covalent_ext/covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
        "ab4659abeed0a93a442dae68cc339a389c6fbee10e3747f36735117cb89a54c7",
    ),
    (
        "src/covalent_ext/covapie_batch001_train5_five_epoch_task_schedule_"
        "refresh_trainer_smoke_v1.py",
        "18dd460ae7ef9aeb368ca9ede1c56b91e02d81e679b3618632b370387779f05b",
    ),
    (
        "src/covalent_ext/covapie_batch001_train5_admission_aware_cpu_"
        "forward_loss_smoke_v1.py",
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
    ),
    (
        "src/covalent_ext/covapie_batch001_train5_single_backward_optimizer_"
        "step_smoke_v1.py",
        "7ab327d86df87b5b20e5758906d34f60e21426cc6a9e35376b78b5c97b086cdc",
    ),
    (
        "src/covalent_ext/covapie_current11_formal_validation4_masked_vlb_"
        "nll_v1.py",
        "3f53e1bb668dfe5751f154793ba0d4e1f1001e9619f7a8613b7df31b522be755",
    ),
    (
        "src/covalent_ext/covapie_current11_formal_validation4_lightning_"
        "integration_v1.py",
        "48ab4378d47af747c828517df0a153b1feb1042872a891233b0c11b14f999ca1",
    ),
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
        "src/covalent_ext/covapie_current11_checkpoint_migration_and_real_"
        "one_batch_train_path_smoke_v1.py",
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
    ),
    (
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
    ),
)
EXPECTED_METRIC_KEYS_V1 = frozenset((
    "loss",
    "loss_base_diffusion",
    "loss_covalent_pair_prediction",
    "loss_pre_post_geometry",
    "loss_covalent_pair_contrastive",
))
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001FormalTrainValidationIntegrationResultV1:
    implementation_status: str
    result_interpretation: str
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_test_event_ids: tuple[str, ...]
    runtime_train_event_ids: tuple[str, ...]
    runtime_validation_event_ids: tuple[str, ...]
    runtime_test_event_ids: tuple[str, ...]
    train_runtime_matches_published_activation_authority: bool
    validation_runtime_matches_published_formal_validation_authority: bool
    formal_test_runtime_intersection_count: int
    formal_leakage_group_cross_split_violation_count: int
    train_sample_training_admitted_count: int
    validation_sample_training_admitted_count: int
    test_sample_training_admitted_count: int
    train_model_training_activation_authorized_count: int
    train_optimizer_population_eligible_count: int
    train_pair_candidate_count: int
    train_pair_positive_count: int
    train_pair_negative_count: int
    PRE_geometry_train_active_count: int
    POST_geometry_train_active_count: int
    supervision_field_count: int
    formal_train_epoch: int
    task_schedule_seed: int
    scheduled_task_ids: tuple[int, ...]
    five_epoch_task_vectors: tuple[tuple[int, ...], ...]
    five_epoch_task_cycles_complete: bool
    datamodule_setup_fit_call_count: int
    train_dataloader_call_count: int
    validation_dataloader_call_count: int
    train_dataset_getitem_count: int
    train_collator_call_count: int
    validation_dataset_getitem_count: int
    validation_collator_call_count: int
    test_dataset_getitem_count: int
    train_dataloader_length: int
    validation_dataloader_length: int
    train_dataloader_sequential_sampler: bool
    validation_dataloader_sequential_sampler: bool
    dataloader_batch_size: int
    dataloader_num_workers: int
    dataloader_drop_last: bool
    dataloader_pin_memory: bool
    dataloader_persistent_workers: bool
    trainer_configuration: tuple[tuple[str, object], ...]
    trainer_api_family: str
    active_python_version: str
    active_torch_version: str
    active_lightning_version: str
    real_trainer_fit_invoked: bool
    trainer_fit_call_count: int
    train_batch_start_count: int
    train_batch_end_count: int
    automatic_backward_call_count: int
    optimizer_step_count: int
    zero_grad_lifecycle_call_count: int
    trainer_global_step: int
    formal_validation_run_count: int
    formal_validation_step_count: int
    test_step_call_count: int
    Trainer_test_invoked: bool
    lifecycle_order: tuple[str, ...]
    training_step_metrics: tuple[tuple[str, float], ...]
    runtime_losses: tuple[tuple[str, float], ...]
    optimizer_metadata: single_step_predecessor.CovapieBatch001Train5OptimizerMetadataV1
    gradient_group_stats: tuple[
        single_step_predecessor.CovapieBatch001Train5GradientGroupStatsV1, ...
    ]
    geometry_component_gradient: single_step_predecessor.CovapieBatch001Train5GeometryComponentGradientV1
    parameter_delta_group_stats: tuple[
        single_step_predecessor.CovapieBatch001Train5ParameterDeltaGroupStatsV1, ...
    ]
    changed_parameter_tensor_count: int
    all_model_parameters_finite: bool
    pre_fit_state_fingerprint: str
    post_optimizer_state_fingerprint: str
    validation_entry_state_fingerprint: str
    validation_exit_state_fingerprint: str
    post_optimizer_state_differs_from_pre_fit_state: bool
    validation_entry_uses_post_optimizer_current_state: bool
    active_state_unchanged_across_validation: bool
    formal_validation_result: formal_validation_owner.CovapieCurrent11CurrentModelFormalValidation4ResultV1
    validation_task_domains: tuple[tuple[str, tuple[int, ...]], ...]
    validation_model_weight_source: str
    validation_checkpoint_weight_migration_count: int
    checkpoint_initialization_migration_count: int
    migration_counts: tuple[tuple[str, int], ...]
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    checkpoint_unchanged: bool
    bound_source_sha256: tuple[tuple[str, str], ...]
    activation_artifact_sha256: tuple[tuple[str, str], ...]
    integration_candidate_loss_weights: tuple[tuple[str, float], ...]
    integration_candidate_loss_weights_reused: bool
    production_geometry_weight_finalized: bool
    production_joint_loss_policy_finalized: bool
    active_model_parameters_unchanged_across_validation: bool
    active_model_buffers_unchanged_across_validation: bool
    active_model_gradient_states_unchanged_across_validation: bool
    active_model_registered_modules_unchanged_across_validation: bool
    active_model_registered_parameters_unchanged_across_validation: bool
    active_model_registered_buffers_unchanged_across_validation: bool
    formal_validation_estimate_count: int
    formal_validation_PRE_valid_count: int
    formal_validation_POST_valid_count: int
    all_formal_validation_metrics_finite: bool
    current_state_key_count: int
    shadow_state_key_count: int
    shadow_strict_state_copy_parity: bool
    original_train_batch_unchanged: bool
    protected_sources_changed: bool
    protected_state_unchanged: bool
    raw_tree_unchanged: bool
    temporary_trainer_root_removed: bool
    persistent_output_created: bool
    training_performed: bool
    scientific_training_claimed: bool
    CPU_only: bool
    GPU_used: bool
    network_used: bool
    full_training_authorized: bool
    elapsed_seconds: float
    ready_for_gpt_review: bool
    ready_for_publication: bool
    ready_to_pivot_to_bulk_data_scale_after_publication: bool
    recommended_next_step_exactly: str


class _IntegrationInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _IntegrationInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_FORMAL_TRAIN_VALIDATION_INTEGRATION_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _IntegrationInvariantError) else "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_FORMAL_TRAIN_VALIDATION_INTEGRATION_ERROR_V1}:{reason}"
    ) from error


def _require_root(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _IntegrationInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_FILE_NOT_SAFE_REGULAR_FILE")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise _IntegrationInvariantError("BOUND_FILE_READ_FAILED") from error


def verify_covapie_batch001_formal_train_validation_source_bindings_v1(
    *, repository_root: object = None,
) -> tuple[tuple[str, str], ...]:
    """Verify the current activation, train, validation, and migration owners."""

    try:
        repository = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        observed: list[tuple[str, str]] = []
        for relative, expected in BOUND_SOURCE_SHA256_V1:
            actual = _sha256_file(repository / relative)
            if actual != expected:
                _fail("BOUND_SOURCE_SHA256_MISMATCH:" + relative)
            observed.append((relative, actual))
        artifact_root = repository / activation_owner.OUTPUT_ROOT_RELATIVE_V1
        for name, expected in ACTIVATION_ARTIFACT_SHA256_V1:
            actual = _sha256_file(artifact_root / name)
            if actual != expected:
                _fail("ACTIVATION_ARTIFACT_SHA256_MISMATCH:" + name)
        if (
            INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1
            is not bounded_predecessor.INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
            or INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1
            is not single_step_predecessor.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
        ):
            _fail("INTEGRATION_CANDIDATE_NOT_EXACT_PUBLISHED_ALIAS")
        return tuple(observed)
    except BaseException as error:
        _public_error(error)


def _loss_weights_tuple(
    weights: CovapieCurrent11LossWeightsV1,
) -> tuple[tuple[str, float], ...]:
    return single_step_predecessor._loss_weights_tuple(weights)


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    return single_step_predecessor._same_tensor(left, right)


def _same_supervision(
    left: CovapieCurrent11TrainingSupervisionTensorsV1,
    right: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> bool:
    return all(
        _same_tensor(getattr(left, item.name), getattr(right, item.name))
        for item in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )


def _same_model_input(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    return activation_owner._same_model_input(left, right)


def _all_nested_tensors(value: object) -> tuple[torch.Tensor, ...]:
    return bounded_predecessor._all_nested_tensors(value)


def _tensor_snapshot(value: object) -> tuple[torch.Tensor, ...]:
    return tuple(tensor.detach().cpu().clone() for tensor in _all_nested_tensors(value))


def _tensor_snapshot_unchanged(
    before: Sequence[torch.Tensor], value: object,
) -> bool:
    after = _all_nested_tensors(value)
    return len(before) == len(after) and all(
        _same_tensor(left, right.detach().cpu()) for left, right in zip(before, after)
    )


def _state_snapshot(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def _same_state_snapshot(
    before: Mapping[str, torch.Tensor], after: Mapping[str, torch.Tensor]
) -> bool:
    return tuple(before) == tuple(after) and all(
        _same_tensor(before[name], after[name]) for name in before
    )


def _state_fingerprint_from_snapshot(
    snapshot: Mapping[str, torch.Tensor],
) -> str:
    digest = hashlib.sha256()
    for name, value in snapshot.items():
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _state_fingerprint(model: torch.nn.Module) -> str:
    return _state_fingerprint_from_snapshot(_state_snapshot(model))


def _validate_current_authority(
    authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1,
) -> None:
    activation_owner.validate_covapie_batch001_formal_split_authority_v1(authority)
    train = set(authority.train_event_ids)
    validation = set(authority.validation_event_ids)
    test = set(authority.test_event_ids)
    if (
        len(train) != 5
        or len(validation) != 4
        or len(test) != 4
        or train & validation
        or train & test
        or validation & test
        or authority.formal_leakage_group_cross_split_violation_count != 0
    ):
        _fail("CURRENT_FORMAL_5_4_4_AUTHORITY_INVALID")
    sentinel_ids = (
        formal_validation_owner.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
        .formal_validation_event_ids
    )
    if (
        sentinel_ids != authority.validation_event_ids
        or formal_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
        != authority.validation_event_ids
    ):
        _fail("FORMAL_VALIDATION_OWNER_IDENTITY_MISMATCH")


def _carrier_from_activation_batch(
    batch: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1:
    return bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1(
        model_input_batch=batch.model_input_batch,
        supervision=batch.supervision,
        sample_identities=batch.sample_identities,
        scheduled_task_ids=tuple(int(value) for value in batch.training_scheduled_task_ids),
        epoch=batch.epoch,
        task_schedule_seed=batch.task_schedule_seed,
    )


def _validate_train_batch_and_carrier(
    batch: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    carrier: bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1,
    authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1,
) -> None:
    activation_owner.validate_covapie_batch001_model_usable_split_batch_v1(
        batch, authority=authority
    )
    supervision = carrier.supervision
    if (
        batch.formal_split != "train"
        or carrier.sample_identities != authority.train_event_ids
        or carrier.sample_identities != batch.sample_identities
        or carrier.scheduled_task_ids
        != tuple(int(value) for value in batch.training_scheduled_task_ids)
        or carrier.epoch != batch.epoch
        or carrier.task_schedule_seed != batch.task_schedule_seed
        or carrier.model_input_batch is not batch.model_input_batch
        or carrier.supervision is not batch.supervision
        or batch.sample_training_admitted != (True,) * 5
        or batch.model_training_activation_authorized != (True,) * 5
        or batch.optimizer_population_eligible != (True,) * 5
        or len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or len(supervision.pair_candidate_batch_index) != 690
        or int(supervision.pair_candidate_is_positive.sum().item()) != 5
        or int(supervision.pair_candidate_is_negative.sum().item()) != 685
        or int(supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()) != 0
        or int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()) != 5
    ):
        _fail("CURRENT_ACTIVATION_TRAIN5_CARRIER_INVALID")


class _SingleFormalTrainCarrierDatasetV1(
    Dataset[bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1]
):
    def __init__(
        self,
        carrier: bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1,
    ) -> None:
        self.carrier = carrier
        self.getitem_call_count = 0

    def __len__(self) -> int:
        return 1

    def __getitem__(
        self, index: int,
    ) -> bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        self.getitem_call_count += 1
        if self.getitem_call_count > 1:
            _fail("SECOND_TRAIN_DATASET_ITEM_REJECTED")
        return self.carrier


class _SingleFormalTrainCarrierCollatorV1:
    def __init__(
        self,
        carrier: bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1,
    ) -> None:
        self.carrier = carrier
        self.call_count = 0

    def __call__(
        self,
        rows: list[bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1],
    ) -> bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1:
        self.call_count += 1
        if self.call_count > 1 or len(rows) != 1 or rows[0] is not self.carrier:
            _fail("FORMAL_TRAIN_COLLATOR_CONTRACT_INVALID")
        return rows[0]


class CovapieBatch001FormalTrainingDataModuleV1(pl.LightningDataModule):
    """Exact train5 carrier plus one published formal-validation request."""

    def __init__(
        self,
        *,
        authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1,
        train_batch: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    ) -> None:
        super().__init__()
        _validate_current_authority(authority)
        carrier = _carrier_from_activation_batch(train_batch)
        _validate_train_batch_and_carrier(train_batch, carrier, authority)
        self.authority = authority
        self.train_split_batch = train_batch
        self.train_carrier = carrier
        self.train_dataset = _SingleFormalTrainCarrierDatasetV1(carrier)
        self.train_collator = _SingleFormalTrainCarrierCollatorV1(carrier)
        self.validation_dataset = (
            formal_validation_owner._FormalValidation4RequestDatasetV1()
        )
        self.validation_collator = (
            formal_validation_owner._FormalValidation4RequestCollatorV1()
        )
        self.train_loader: DataLoader | None = None
        self.validation_loader: DataLoader | None = None
        self.setup_fit_call_count = 0
        self.train_dataloader_call_count = 0
        self.validation_dataloader_call_count = 0
        self.test_dataloader_call_count = 0
        self.test_dataset_getitem_count = 0
        self.before_train_batch_transfer_call_count = 0
        self.after_train_batch_transfer_call_count = 0
        self.before_validation_batch_transfer_call_count = 0
        self.after_validation_batch_transfer_call_count = 0
        self.transferred_train_batch_rebuilt = False
        self.transferred_train_metadata_unchanged = False
        self.transferred_train_tensors_on_cpu = False

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("DATAMODULE_SETUP_STAGE_INVALID")
        self.setup_fit_call_count += 1
        if self.setup_fit_call_count > 1:
            _fail("DATAMODULE_SETUP_FIT_CALLED_MORE_THAN_ONCE")

    @staticmethod
    def _validate_loader(loader: DataLoader, *, reason: str) -> None:
        if (
            len(loader) != 1
            or loader.batch_size != 1
            or type(loader.sampler) is not SequentialSampler
            or loader.num_workers != 0
            or loader.drop_last is not False
            or loader.pin_memory is not False
            or loader.persistent_workers is not False
        ):
            _fail(reason)

    def train_dataloader(self) -> DataLoader:
        self.train_dataloader_call_count += 1
        if self.train_dataloader_call_count > 1:
            _fail("TRAIN_DATALOADER_CALLED_MORE_THAN_ONCE")
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=self.train_collator,
        )
        self._validate_loader(
            self.train_loader, reason="TRAIN_DATALOADER_CONFIGURATION_INVALID"
        )
        return self.train_loader

    def val_dataloader(self) -> DataLoader:
        self.validation_dataloader_call_count += 1
        if self.validation_dataloader_call_count > 1:
            _fail("VALIDATION_DATALOADER_CALLED_MORE_THAN_ONCE")
        self.validation_loader = DataLoader(
            self.validation_dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=self.validation_collator,
        )
        self._validate_loader(
            self.validation_loader,
            reason="VALIDATION_DATALOADER_CONFIGURATION_INVALID",
        )
        return self.validation_loader

    def test_dataloader(self) -> NoReturn:
        try:
            self.test_dataloader_call_count += 1
            _fail("FORMAL_TEST_DATALOADER_ACCESS_FORBIDDEN")
        except BaseException as error:
            _public_error(error)

    def on_before_batch_transfer(self, batch: object, dataloader_idx: int) -> object:
        if type(batch) is bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1:
            self.before_train_batch_transfer_call_count += 1
            if (
                self.before_train_batch_transfer_call_count > 1
                or batch is not self.train_carrier
                or dataloader_idx != 0
            ):
                _fail("TRAIN_BEFORE_BATCH_TRANSFER_INVALID")
            return batch
        formal_validation_owner._validate_formal_validation_sentinel_v1(batch)
        self.before_validation_batch_transfer_call_count += 1
        if self.before_validation_batch_transfer_call_count > 1 or dataloader_idx != 0:
            _fail("VALIDATION_BEFORE_BATCH_TRANSFER_INVALID")
        return batch

    def on_after_batch_transfer(self, batch: object, dataloader_idx: int) -> object:
        if type(batch) is bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1:
            self.after_train_batch_transfer_call_count += 1
            self.transferred_train_batch_rebuilt = (
                batch is not self.train_carrier
                and batch.model_input_batch is not self.train_carrier.model_input_batch
                and batch.supervision is not self.train_carrier.supervision
            )
            self.transferred_train_metadata_unchanged = (
                batch.sample_identities is self.train_carrier.sample_identities
                and batch.scheduled_task_ids is self.train_carrier.scheduled_task_ids
                and batch.epoch == self.train_carrier.epoch
                and batch.task_schedule_seed == self.train_carrier.task_schedule_seed
            )
            tensors = _all_nested_tensors(batch)
            self.transferred_train_tensors_on_cpu = bool(tensors) and all(
                tensor.device.type == "cpu" for tensor in tensors
            )
            if (
                self.after_train_batch_transfer_call_count > 1
                or dataloader_idx != 0
                or not self.transferred_train_batch_rebuilt
                or not self.transferred_train_metadata_unchanged
                or not self.transferred_train_tensors_on_cpu
            ):
                _fail("TRAIN_AFTER_BATCH_TRANSFER_INVALID")
            return batch
        formal_validation_owner._validate_formal_validation_sentinel_v1(batch)
        self.after_validation_batch_transfer_call_count += 1
        if self.after_validation_batch_transfer_call_count > 1 or dataloader_idx != 0:
            _fail("VALIDATION_AFTER_BATCH_TRANSFER_INVALID")
        return batch


def build_covapie_batch001_formal_training_datamodule_v1(
    *,
    epoch: object = FORMAL_TRAIN_EPOCH_V1,
    task_schedule_seed: object = FORMAL_TASK_SCHEDULE_SEED_V1,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001FormalTrainingDataModuleV1:
    """Build from current activation authority; no identity override exists."""

    try:
        if (
            type(epoch) is not int
            or epoch < 0
            or type(task_schedule_seed) is not int
            or not 0 <= task_schedule_seed <= 2**63 - 1
        ):
            _fail("DATAMODULE_BUILD_ARGUMENT_INVALID")
        repository = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_root(
            cache_root,
            default=_DEFAULT_CACHE_ROOT,
            reason="CACHE_ROOT_INVALID",
        )
        verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=repository
        )
        authority = activation_owner.load_covapie_batch001_formal_split_authority_v1(
            repository_root=repository
        )
        _validate_current_authority(authority)
        train_batch = activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
            split="train",
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
            repository_root=repository,
            cache_root=cache,
        )
        return CovapieBatch001FormalTrainingDataModuleV1(
            authority=authority, train_batch=train_batch
        )
    except BaseException as error:
        _public_error(error)


class CovapieBatch001FormalTrainValidationLigandPocketDDPMV1(
    formal_validation_owner.CovapieCurrent11FormalValidation4LigandPocketDDPMV1,
    bounded_predecessor._Train5BoundedTrainerCompatibilityAdapterV1,
):
    """Current11 bounded train adapter plus unchanged formal validation owner."""

    validation_epoch_end = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._covapie_batch001_model_setup_fit_call_count_v1 = 0
        self._covapie_batch001_validation_entry_state_snapshot_v1 = None
        self._covapie_batch001_validation_exit_state_snapshot_v1 = None
        self._covapie_batch001_test_step_call_count_v1 = 0

    def setup(self, stage: str | None = None) -> None:
        """Prepare only the sentinel lifecycle; the DataModule owns fit data."""

        try:
            if stage != "fit":
                _fail("MODEL_SETUP_STAGE_INVALID")
            self._covapie_batch001_model_setup_fit_call_count_v1 += 1
            if self._covapie_batch001_model_setup_fit_call_count_v1 > 1:
                _fail("MODEL_SETUP_FIT_CALLED_MORE_THAN_ONCE")
            self._prepare_formal_validation4_lifecycle_v1()
            if (
                self.train_dataset is not None
                or self.val_dataset is not None
                or self.test_dataset is not None
            ):
                _fail("MODEL_SETUP_CREATED_LEGACY_MOLECULAR_DATASET")
            return None
        except BaseException as error:
            _public_error(error)

    def on_validation_epoch_start(self) -> None:
        try:
            if self._covapie_batch001_validation_entry_state_snapshot_v1 is not None:
                _fail("SECOND_VALIDATION_ENTRY_REJECTED")
            self._covapie_batch001_validation_entry_state_snapshot_v1 = (
                _state_snapshot(self)
            )
            return super().on_validation_epoch_start()
        except BaseException as error:
            _public_error(error)

    def on_validation_epoch_end(self) -> None:
        try:
            super().on_validation_epoch_end()
            self._covapie_batch001_validation_exit_state_snapshot_v1 = (
                _state_snapshot(self)
            )
            if not _same_state_snapshot(
                self._covapie_batch001_validation_entry_state_snapshot_v1,
                self._covapie_batch001_validation_exit_state_snapshot_v1,
            ):
                _fail("ACTIVE_STATE_MUTATED_ACROSS_VALIDATION")
        except BaseException as error:
            _public_error(error)

    def test_step(self, data: object, *unused: object) -> NoReturn:
        del data, unused
        self._covapie_batch001_test_step_call_count_v1 += 1
        _fail("FORMAL_TEST_STEP_FORBIDDEN")


def instantiate_covapie_batch001_train_validation_model_v1(
    *,
    runtime_root: object,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
    loss_weights: object = None,
) -> CovapieBatch001FormalTrainValidationLigandPocketDDPMV1:
    """Instantiate the exact additive model in a caller-owned temporary root."""

    try:
        repository = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_root(
            state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID"
        )
        cache = _require_root(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
        )
        runtime = _require_root(
            runtime_root, default=Path("/__no_default__"), reason="RUNTIME_ROOT_INVALID"
        )
        verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=repository
        )
        try:
            unused_default, candidate = bounded_predecessor._validate_loss_policy(
                loss_weights
            )
        except bounded_predecessor._SmokeInvariantError as error:
            _fail(error.reason)
        del unused_default
        if candidate is not INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1:
            _fail("INTEGRATION_CANDIDATE_LOSS_POLICY_INVALID")
        legacy_setup = runtime / "legacy_setup_data"
        legacy_setup.mkdir(mode=0o700)
        model = bounded_predecessor._instantiate_model(
            owner=CovapieBatch001FormalTrainValidationLigandPocketDDPMV1,
            repository_root=repository,
            state_root=state,
            legacy_setup_data_root=legacy_setup,
            output_root=runtime / "model_output",
            loss_weights=candidate,
        )
        model._covapie_formal_validation4_cache_root_v1 = cache
        if (
            type(model) is not CovapieBatch001FormalTrainValidationLigandPocketDDPMV1
            or not isinstance(
                model,
                formal_validation_owner.CovapieCurrent11FormalValidation4LigandPocketDDPMV1,
            )
            or not isinstance(model, bounded_predecessor._Train5BoundedTrainerAdapterV1)
            or len(model.state_dict()) != 141
            or model.covapie_current11_loss_weights is not candidate
            or model._covapie_formal_validation4_cache_root_v1 != cache
            or getattr(type(model), "forward")
            is not bounded_predecessor._Train5BoundedTrainerAdapterV1.forward
            or getattr(type(model), "training_step")
            is not CovapieCurrent11TrainingLigandPocketDDPM.training_step
            or getattr(type(model), "configure_optimizers")
            is not CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
        ):
            _fail("TRAIN_VALIDATION_MODEL_ADAPTER_INVALID")
        return model
    except BaseException as error:
        _public_error(error)


class _TrainValidationLifecycleObserverV1(bounded_predecessor._TrainerObserverV1):
    def __init__(
        self,
        *,
        original_carrier: bounded_predecessor.CovapieBatch001Train5TrainerBatchCarrierV1,
        checkpoint_state: Mapping[str, torch.Tensor],
        pre_fit_state_snapshot: Mapping[str, torch.Tensor],
        formal_test_event_ids: tuple[str, ...],
    ) -> None:
        super().__init__(
            original_carrier=original_carrier, checkpoint_state=checkpoint_state
        )
        self.pre_fit_state_snapshot = dict(pre_fit_state_snapshot)
        self.formal_test_event_ids = formal_test_event_ids
        self.post_optimizer_state_snapshot: dict[str, torch.Tensor] | None = None
        self.validation_entry_state_snapshot: dict[str, torch.Tensor] | None = None
        self.validation_exit_state_snapshot: dict[str, torch.Tensor] | None = None
        self.formal_validation_epoch_start_count = 0
        self.formal_validation_epoch_end_count = 0
        self.formal_validation_step_count = 0
        self.runtime_train_event_ids: tuple[str, ...] = ()
        self.runtime_validation_event_ids: tuple[str, ...] = ()
        self.runtime_test_event_ids: tuple[str, ...] = ()
        self.lifecycle_order: list[str] = []

    def on_train_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
    ) -> None:
        super().on_train_batch_start(trainer, pl_module, batch, batch_idx)
        carrier = bounded_predecessor._validate_carrier(batch)
        self.runtime_train_event_ids = carrier.sample_identities
        if set(carrier.sample_identities) & set(self.formal_test_event_ids):
            _fail("FORMAL_TEST_ID_IN_TRAIN_RUNTIME")
        self.lifecycle_order.append("train_batch_start")

    def on_before_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule, loss: torch.Tensor
    ) -> None:
        super().on_before_backward(trainer, pl_module, loss)
        self.lifecycle_order.append("before_backward")

    def on_after_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        super().on_after_backward(trainer, pl_module)
        self.lifecycle_order.append("after_backward")

    def on_before_optimizer_step(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
        optimizer_idx: int | None = None,
    ) -> None:
        super().on_before_optimizer_step(
            trainer, pl_module, optimizer, optimizer_idx
        )
        self.lifecycle_order.append("before_optimizer_step")

    def on_train_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: object,
        batch: object,
        batch_idx: int,
    ) -> None:
        super().on_train_batch_end(
            trainer, pl_module, outputs, batch, batch_idx
        )
        if self.before_optimizer_step_count != 1:
            _fail("TRAIN_BATCH_ENDED_WITHOUT_EXACT_OPTIMIZER_STEP")
        self.post_optimizer_state_snapshot = _state_snapshot(pl_module)
        if _same_state_snapshot(
            self.pre_fit_state_snapshot, self.post_optimizer_state_snapshot
        ):
            _fail("OPTIMIZER_STEP_DID_NOT_CHANGE_MODEL_STATE")
        self.lifecycle_order.append("train_batch_end_after_optimizer_step")

    def on_validation_epoch_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer
        self.formal_validation_epoch_start_count += 1
        if (
            self.formal_validation_epoch_start_count > 1
            or self.before_optimizer_step_count != 1
            or self.train_batch_end_count != 1
            or self.post_optimizer_state_snapshot is None
        ):
            _fail("VALIDATION_BEFORE_EXACT_OPTIMIZER_LIFECYCLE")
        self.validation_entry_state_snapshot = _state_snapshot(pl_module)
        if not _same_state_snapshot(
            self.post_optimizer_state_snapshot,
            self.validation_entry_state_snapshot,
        ):
            _fail("VALIDATION_ENTRY_NOT_POST_OPTIMIZER_STATE")
        self.lifecycle_order.append("validation_epoch_start")

    def on_validation_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> None:
        del trainer, pl_module
        formal_validation_owner._validate_formal_validation_sentinel_v1(batch)
        self.validation_batch_count += 1
        self.formal_validation_step_count += 1
        self.runtime_validation_event_ids = batch.formal_validation_event_ids
        if (
            self.validation_batch_count > 1
            or self.formal_validation_step_count > 1
            or batch_idx != 0
            or dataloader_idx != 0
            or set(self.runtime_validation_event_ids) & set(self.formal_test_event_ids)
        ):
            _fail("FORMAL_VALIDATION_BATCH_LIFECYCLE_INVALID")
        self.lifecycle_order.append("validation_step_start")

    def on_validation_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: object,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> None:
        del trainer, batch
        if (
            batch_idx != 0
            or dataloader_idx != 0
            or type(outputs) is not dict
            or tuple(outputs) != formal_validation_owner.LIGHTNING_METRIC_KEYS_V1
            or any(
                not isinstance(value, torch.Tensor)
                or not bool(torch.isfinite(value).all().item())
                for value in outputs.values()
            )
        ):
            _fail("FORMAL_VALIDATION_LOGGED_METRICS_INVALID")
        self.validation_exit_state_snapshot = _state_snapshot(pl_module)
        if not _same_state_snapshot(
            self.validation_entry_state_snapshot,
            self.validation_exit_state_snapshot,
        ):
            _fail("ACTIVE_STATE_MUTATED_DURING_VALIDATION_STEP")
        self.lifecycle_order.append("validation_step_end")

    def on_validation_epoch_end(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer, pl_module
        self.formal_validation_epoch_end_count += 1
        if (
            self.formal_validation_epoch_end_count > 1
            or self.formal_validation_step_count != 1
        ):
            _fail("FORMAL_VALIDATION_EPOCH_END_INVALID")
        self.lifecycle_order.append("validation_epoch_end")

    def on_test_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> NoReturn:
        del trainer, pl_module, batch, batch_idx, dataloader_idx
        self.test_batch_count += 1
        _fail("FORMAL_TEST_RUNTIME_ACCESS_FORBIDDEN")


@dataclass
class _FitRuntimeV1:
    trainer: pl.Trainer
    datamodule: CovapieBatch001FormalTrainingDataModuleV1
    observer: _TrainValidationLifecycleObserverV1
    trainer_api_family: str
    sampler_control_parameter: str
    precision_argument: object
    trainer_kwargs: dict[str, object]
    fit_call_count: int = 0


def _trainer_configuration_for_signature(
    *, signature: inspect.Signature, callbacks: list[pl.Callback], root: Path
) -> tuple[dict[str, object], dict[str, object]]:
    parameters = set(signature.parameters) - {"self"}
    required = {
        "accelerator",
        "devices",
        "num_nodes",
        "precision",
        "max_epochs",
        "min_epochs",
        "max_steps",
        "limit_train_batches",
        "limit_val_batches",
        "limit_test_batches",
        "num_sanity_val_steps",
        "check_val_every_n_epoch",
        "val_check_interval",
        "enable_checkpointing",
        "callbacks",
        "logger",
        "gradient_clip_val",
        "accumulate_grad_batches",
        "deterministic",
        "enable_progress_bar",
        "default_root_dir",
    }
    if not required <= parameters:
        _fail("TRAINER_SIGNATURE_REQUIRED_CAPABILITY_MISSING")
    if "use_distributed_sampler" in parameters:
        family = "lightning-2.x"
        sampler = "use_distributed_sampler"
        precision: object = "32-true"
    elif "replace_sampler_ddp" in parameters:
        family = "lightning-1.x"
        sampler = "replace_sampler_ddp"
        precision = 32
    else:
        _fail("TRAINER_SAMPLER_CONTROL_MISSING")
    kwargs: dict[str, object] = {
        "accelerator": "cpu",
        "devices": 1,
        "num_nodes": 1,
        "precision": precision,
        "max_epochs": 1,
        "min_epochs": 1,
        "max_steps": -1,
        "limit_train_batches": 1,
        "limit_val_batches": 1,
        "limit_test_batches": 0,
        "num_sanity_val_steps": 0,
        "check_val_every_n_epoch": 1,
        "val_check_interval": 1.0,
        "enable_checkpointing": False,
        "callbacks": callbacks,
        "logger": False,
        "gradient_clip_val": None,
        "accumulate_grad_batches": 1,
        "deterministic": True,
        "enable_progress_bar": False,
        "default_root_dir": root,
        sampler: False,
    }
    optional = {
        "gradient_clip_algorithm": None,
        "benchmark": False,
        "reload_dataloaders_every_n_epochs": 0,
        "sync_batchnorm": False,
        "enable_model_summary": False,
        "log_every_n_steps": 1,
        "profiler": None,
    }
    kwargs.update({name: value for name, value in optional.items() if name in parameters})
    return kwargs, {
        "trainer_api_family": family,
        "sampler_control_parameter": sampler,
        "precision_argument": precision,
    }


def _validate_trainer_kwargs(kwargs: Mapping[str, object]) -> None:
    sampler_values = tuple(
        kwargs[name]
        for name in ("use_distributed_sampler", "replace_sampler_ddp")
        if name in kwargs
    )
    expected = {
        "accelerator": "cpu",
        "devices": 1,
        "num_nodes": 1,
        "max_epochs": 1,
        "min_epochs": 1,
        "max_steps": -1,
        "limit_train_batches": 1,
        "limit_val_batches": 1,
        "limit_test_batches": 0,
        "num_sanity_val_steps": 0,
        "check_val_every_n_epoch": 1,
        "val_check_interval": 1.0,
        "enable_checkpointing": False,
        "logger": False,
        "gradient_clip_val": None,
        "accumulate_grad_batches": 1,
        "deterministic": True,
        "enable_progress_bar": False,
    }
    if (
        any(kwargs.get(name) != value for name, value in expected.items())
        or sampler_values != (False,)
        or kwargs.get("profiler", None) is not None
    ):
        _fail("TRAINER_CONFIGURATION_NOT_EXACT_BOUNDED_CPU")


def _build_fit_runtime(
    *,
    datamodule: CovapieBatch001FormalTrainingDataModuleV1,
    checkpoint_state: Mapping[str, torch.Tensor],
    pre_fit_state_snapshot: Mapping[str, torch.Tensor],
    root: Path,
) -> _FitRuntimeV1:
    observer = _TrainValidationLifecycleObserverV1(
        original_carrier=datamodule.train_carrier,
        checkpoint_state=checkpoint_state,
        pre_fit_state_snapshot=pre_fit_state_snapshot,
        formal_test_event_ids=datamodule.authority.test_event_ids,
    )
    kwargs, compatibility = _trainer_configuration_for_signature(
        signature=inspect.signature(pl.Trainer.__init__),
        callbacks=[observer],
        root=root,
    )
    _validate_trainer_kwargs(kwargs)
    fit_parameters = set(inspect.signature(pl.Trainer.fit).parameters)
    if not {"model", "datamodule", "ckpt_path"} <= fit_parameters:
        _fail("TRAINER_FIT_SIGNATURE_INVALID")
    trainer = pl.Trainer(**kwargs)
    if (
        trainer.num_devices != 1
        or trainer.max_epochs != 1
        or trainer.max_steps != -1
        or trainer.limit_train_batches != 1
        or trainer.limit_val_batches != 1
        or trainer.limit_test_batches != 0
        or trainer.num_sanity_val_steps != 0
        or trainer.checkpoint_callback is not None
        or trainer.logger is not None
    ):
        _fail("EFFECTIVE_TRAINER_CONFIGURATION_INVALID")
    return _FitRuntimeV1(
        trainer=trainer,
        datamodule=datamodule,
        observer=observer,
        trainer_api_family=str(compatibility["trainer_api_family"]),
        sampler_control_parameter=str(compatibility["sampler_control_parameter"]),
        precision_argument=compatibility["precision_argument"],
        trainer_kwargs=kwargs,
    )


def _invoke_fit(
    model: pl.LightningModule, runtime: _FitRuntimeV1,
) -> None:
    runtime.fit_call_count += 1
    if runtime.fit_call_count != 1:
        _fail("TRAINER_FIT_MUST_BE_INVOKED_EXACTLY_ONCE")
    previous_handler = signal.getsignal(signal.SIGINT)
    try:
        runtime.trainer.fit(
            model=model, datamodule=runtime.datamodule, ckpt_path=None
        )
    except SystemExit:
        if isinstance(runtime.observer.process_control_exception, KeyboardInterrupt):
            raise runtime.observer.process_control_exception
        raise
    finally:
        if signal.getsignal(signal.SIGINT) is not previous_handler:
            signal.signal(signal.SIGINT, previous_handler)


def _validation_task_domains(
    result: formal_validation_owner.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    domains: dict[str, set[int]] = {}
    for row in result.per_estimate_rows:
        domains.setdefault(row.canonical_event_id, set()).add(row.canonical_task_id)
    ordered = tuple(
        (event_id, tuple(sorted(domains.get(event_id, set()))))
        for event_id in result.formal_validation_event_ids
    )
    expected = tuple(
        (
            event_id,
            (0, 3, 4) if event_id.split(":")[-2] == "PX5" else (0, 1, 2, 3, 4),
        )
        for event_id in result.formal_validation_event_ids
    )
    if ordered != expected:
        _fail("FORMAL_VALIDATION_TASK_DOMAIN_DRIFT")
    return ordered


def _validate_formal_result(
    result: object,
    *,
    authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1,
) -> formal_validation_owner.CovapieCurrent11CurrentModelFormalValidation4ResultV1:
    if not isinstance(
        result,
        formal_validation_owner.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
    ):
        _fail("FORMAL_VALIDATION_RESULT_MISSING")
    finite_values = (
        result.event_macro_masked_conditional_vlb_nll,
        result.micro_masked_conditional_vlb_nll,
        result.profile_balanced_masked_conditional_vlb_nll,
        result.mean_pair_BCE,
        result.mean_POST_geometry_loss,
        result.mean_POST_geometry_prediction_angstrom,
        result.mean_POST_geometry_target_angstrom,
        result.mean_pair_contrastive_loss,
        result.mean_task4_historical_joint_nll_with_node_prior_diagnostic,
    )
    if (
        result.formal_validation_event_ids != authority.validation_event_ids
        or result.formal_validation_event_count != 4
        or result.formal_validation_task_event_count != 16
        or result.formal_validation_estimate_count != 64
        or result.PRE_geometry_valid_count != 0
        or result.POST_geometry_valid_count != 64
        or not result.all_applicable_primary_metrics_finite
        or not result.all_applicable_auxiliary_metrics_finite
        or not all(math.isfinite(value) for value in finite_values)
        or result.validation_model_weight_source
        != formal_validation_owner.VALIDATION_MODEL_WEIGHT_SOURCE_V1
        or result.current_state_key_count != 141
        or result.shadow_state_key_count != 141
        or not result.shadow_strict_state_copy_parity
        or result.checkpoint_weight_migration_call_count_inside_validation != 0
        or not result.active_model_parameters_unchanged
        or not result.active_model_buffers_unchanged
        or not result.active_model_gradient_states_unchanged
        or not result.active_model_registered_modules_unchanged
        or not result.active_model_registered_parameters_unchanged
        or not result.active_model_registered_buffers_unchanged
        or result.optimizer_created_during_validation
        or result.backward_performed
        or result.training_performed
    ):
        _fail("FORMAL_CURRENT_STATE_VALIDATION_GATE_FAILED")
    _validation_task_domains(result)
    return result


def _five_epoch_datamodule_vectors(
    *, repository_root: Path, cache_root: Path,
) -> tuple[tuple[int, ...], ...]:
    vectors = []
    for epoch in range(5):
        datamodule = build_covapie_batch001_formal_training_datamodule_v1(
            epoch=epoch,
            task_schedule_seed=FORMAL_TASK_SCHEDULE_SEED_V1,
            repository_root=repository_root,
            cache_root=cache_root,
        )
        vectors.append(datamodule.train_carrier.scheduled_task_ids)
    result = tuple(vectors)
    if (
        len(result) != 5
        or any(len(vector) != 5 for vector in result)
        or any(
            set(result[epoch][sample_index] for epoch in range(5)) != set(range(5))
            for sample_index in range(5)
        )
    ):
        _fail("FIVE_EPOCH_CURRENT_ACTIVATION_TASK_CYCLE_INVALID")
    return result


def _validate_state_transition_snapshots(
    *,
    pre_fit: Mapping[str, torch.Tensor],
    post_optimizer: Mapping[str, torch.Tensor],
    validation_entry: Mapping[str, torch.Tensor],
    validation_exit: Mapping[str, torch.Tensor],
    final_state: Mapping[str, torch.Tensor],
) -> tuple[bool, bool, bool]:
    post_changed = not _same_state_snapshot(pre_fit, post_optimizer)
    validation_uses_post = _same_state_snapshot(post_optimizer, validation_entry)
    validation_unchanged = (
        _same_state_snapshot(validation_entry, validation_exit)
        and _same_state_snapshot(validation_exit, final_state)
    )
    if not post_changed:
        _fail("VALIDATION_SOURCE_STATE_EQUALS_PRE_FIT_STATE")
    if not validation_uses_post:
        _fail("VALIDATION_ENTRY_NOT_POST_OPTIMIZER_CURRENT_STATE")
    if not validation_unchanged:
        _fail("VALIDATION_MUTATED_ACTIVE_MODEL_STATE")
    return post_changed, validation_uses_post, validation_unchanged


def _run_impl(
    *,
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
    checkpoint_path: Path,
    loss_weights: object,
) -> CovapieBatch001FormalTrainValidationIntegrationResultV1:
    started = time.perf_counter()
    bound_before = (
        verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=repository_root
        )
    )
    artifact_before = tuple(
        (
            name,
            _sha256_file(
                repository_root / activation_owner.OUTPUT_ROOT_RELATIVE_V1 / name
            ),
        )
        for name, unused in ACTIVATION_ARTIFACT_SHA256_V1
    )
    authority = activation_owner.load_covapie_batch001_formal_split_authority_v1(
        repository_root=repository_root
    )
    _validate_current_authority(authority)
    if checkpoint_path != repository_root / CHECKPOINT_RELATIVE_PATH_V1:
        _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
    checkpoint_before = _sha256_file(checkpoint_path)
    if checkpoint_before != CHECKPOINT_SHA256_V1:
        _fail("CHECKPOINT_SHA256_MISMATCH")
    raw_before = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    state_before = trainer_reference._state_integrity_snapshot_v1(state_root)

    try:
        published_default, candidate = bounded_predecessor._validate_loss_policy(
            loss_weights
        )
    except bounded_predecessor._SmokeInvariantError as error:
        _fail(error.reason)
    if (
        candidate is not INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1
        or candidate is not single_step_predecessor.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
        or published_default != CovapieCurrent11LossWeightsV1()
    ):
        _fail("INTEGRATION_CANDIDATE_LOSS_POLICY_INVALID")

    datamodule = build_covapie_batch001_formal_training_datamodule_v1(
        epoch=FORMAL_TRAIN_EPOCH_V1,
        task_schedule_seed=FORMAL_TASK_SCHEDULE_SEED_V1,
        repository_root=repository_root,
        cache_root=cache_root,
    )
    independent_train_batch = (
        activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
            split="train",
            epoch=FORMAL_TRAIN_EPOCH_V1,
            task_schedule_seed=FORMAL_TASK_SCHEDULE_SEED_V1,
            repository_root=repository_root,
            cache_root=cache_root,
        )
    )
    if (
        datamodule.train_split_batch.sample_identities
        != independent_train_batch.sample_identities
        or datamodule.train_split_batch.training_scheduled_task_ids
        != independent_train_batch.training_scheduled_task_ids
        or not _same_model_input(
            datamodule.train_split_batch.model_input_batch,
            independent_train_batch.model_input_batch,
        )
        or not _same_supervision(
            datamodule.train_split_batch.supervision,
            independent_train_batch.supervision,
        )
    ):
        _fail("DATAMODULE_TRAIN_RUNTIME_CURRENT_ACTIVATION_PARITY_FAILED")
    five_epoch_vectors = _five_epoch_datamodule_vectors(
        repository_root=repository_root, cache_root=cache_root
    )
    carrier_model_input_before = _tensor_snapshot(
        datamodule.train_carrier.model_input_batch
    )
    carrier_supervision_before = _tensor_snapshot(
        datamodule.train_carrier.supervision
    )

    checkpoint_payload = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    checkpoint_state = checkpoint_payload.get("state_dict")
    if not isinstance(checkpoint_state, Mapping) or len(checkpoint_state) != 122:
        _fail("CHECKPOINT_STATE_DOMAIN_INVALID")

    temporary_path: Path | None = None
    with tempfile.TemporaryDirectory(
        prefix="covapie_batch001_formal_train_validation_integration_"
    ) as temporary:
        temporary_path = Path(temporary)
        with forward_predecessor._deterministic_cpu_context():
            model = instantiate_covapie_batch001_train_validation_model_v1(
                runtime_root=temporary_path,
                repository_root=repository_root,
                state_root=state_root,
                cache_root=cache_root,
                loss_weights=candidate,
            )
            migration, architecture = bounded_predecessor._migration_and_architecture(
                model=model, checkpoint_state=checkpoint_state
            )
            del architecture
            pre_fit_state_snapshot = _state_snapshot(model)
            pre_fit_state_fingerprint = _state_fingerprint_from_snapshot(
                pre_fit_state_snapshot
            )
            pre_fit_parameter_snapshot = {
                name: pre_fit_state_snapshot[name]
                for name, unused in model.named_parameters()
            }
            runtime = _build_fit_runtime(
                datamodule=datamodule,
                checkpoint_state=checkpoint_state,
                pre_fit_state_snapshot=pre_fit_state_snapshot,
                root=temporary_path / "trainer_root",
            )
            _invoke_fit(model, runtime)
            final_state_snapshot = _state_snapshot(model)
            final_state_fingerprint = _state_fingerprint_from_snapshot(
                final_state_snapshot
            )
            named_parameters = dict(model.named_parameters())
            groups = bounded_predecessor._parameter_groups(
                model, checkpoint_state, migration
            )
            delta_observations = []
            for group_name, names, reason in groups:
                stats = single_step_predecessor._parameter_delta_group_stats(
                    group_name=group_name,
                    named_parameters=named_parameters,
                    parameter_names=names,
                    before=pre_fit_parameter_snapshot,
                )
                single_step_predecessor._require_delta_gate(stats, reason=reason)
                delta_observations.append(stats)
            delta_stats = tuple(delta_observations)
            changed_count = sum(
                not torch.equal(parameter.detach().cpu(), pre_fit_parameter_snapshot[name])
                for name, parameter in named_parameters.items()
            )
            all_parameters_finite = all(
                bool(torch.isfinite(parameter).all().item())
                for parameter in named_parameters.values()
            )

    temporary_removed = temporary_path is not None and not temporary_path.exists()
    if not temporary_removed:
        _fail("TEMPORARY_TRAINER_ROOT_NOT_REMOVED")
    original_batch_unchanged = (
        _tensor_snapshot_unchanged(
            carrier_model_input_before, datamodule.train_carrier.model_input_batch
        )
        and _tensor_snapshot_unchanged(
            carrier_supervision_before, datamodule.train_carrier.supervision
        )
    )
    if not original_batch_unchanged:
        _fail("ORIGINAL_TRAIN_CARRIER_MUTATED")

    observer = runtime.observer
    trainer = runtime.trainer
    formal_result = _validate_formal_result(
        model._covapie_formal_validation4_last_result_v1,
        authority=authority,
    )
    validation_domains = _validation_task_domains(formal_result)
    model_counts = model._covapie_formal_validation4_lifecycle_counts_v1
    model_entry = model._covapie_batch001_validation_entry_state_snapshot_v1
    model_exit = model._covapie_batch001_validation_exit_state_snapshot_v1
    if (
        observer.post_optimizer_state_snapshot is None
        or observer.validation_entry_state_snapshot is None
        or observer.validation_exit_state_snapshot is None
        or model_entry is None
        or model_exit is None
    ):
        _fail("TRAIN_VALIDATION_STATE_SNAPSHOT_MISSING")
    post_optimizer_fingerprint = _state_fingerprint_from_snapshot(
        observer.post_optimizer_state_snapshot
    )
    validation_entry_fingerprint = _state_fingerprint_from_snapshot(model_entry)
    validation_exit_fingerprint = _state_fingerprint_from_snapshot(model_exit)
    post_changed, validation_uses_post, validation_unchanged = (
        _validate_state_transition_snapshots(
            pre_fit=pre_fit_state_snapshot,
            post_optimizer=observer.post_optimizer_state_snapshot,
            validation_entry=model_entry,
            validation_exit=model_exit,
            final_state=final_state_snapshot,
        )
    )

    expected_order = (
        "train_batch_start",
        "before_backward",
        "after_backward",
        "before_optimizer_step",
        "train_batch_end_after_optimizer_step",
        "validation_epoch_start",
        "validation_step_start",
        "validation_step_end",
        "validation_epoch_end",
    )
    if (
        tuple(observer.lifecycle_order) != expected_order
        or runtime.fit_call_count != 1
        or observer.fit_start_count != 1
        or observer.train_batch_start_count != 1
        or observer.train_batch_end_count != 1
        or observer.before_backward_count != 1
        or observer.after_backward_count != 1
        or observer.before_optimizer_step_count != 1
        or observer.before_zero_grad_count != 1
        or observer.formal_validation_epoch_start_count != 1
        or observer.formal_validation_epoch_end_count != 1
        or observer.formal_validation_step_count != 1
        or observer.test_batch_count != 0
        or trainer.global_step != 1
        or datamodule.setup_fit_call_count != 1
        or datamodule.train_dataloader_call_count != 1
        or datamodule.validation_dataloader_call_count != 1
        or datamodule.test_dataloader_call_count != 0
        or datamodule.train_dataset.getitem_call_count != 1
        or datamodule.train_collator.call_count != 1
        or datamodule.validation_dataset.getitem_call_count != 1
        or datamodule.validation_collator.call_count != 1
        or datamodule.test_dataset_getitem_count != 0
        or datamodule.before_train_batch_transfer_call_count != 1
        or datamodule.after_train_batch_transfer_call_count != 1
        or datamodule.before_validation_batch_transfer_call_count != 1
        or datamodule.after_validation_batch_transfer_call_count != 1
        or model.transfer_batch_to_device_call_count != 1
        or model_counts["sentinel_transfer_to_device"] != 1
        or model_counts["validation_dataloader"] != 0
        or model_counts["validation_step"] != 1
        or model._covapie_formal_validation4_validation_run_count_v1 != 1
        or model._covapie_batch001_test_step_call_count_v1 != 0
        or not post_changed
        or not validation_uses_post
        or not validation_unchanged
        or changed_count <= 0
        or not all_parameters_finite
    ):
        _fail("EXACT_TRAIN_VALIDATION_LIFECYCLE_GATE_FAILED")

    runtime_train_ids = observer.runtime_train_event_ids
    runtime_validation_ids = observer.runtime_validation_event_ids
    runtime_test_ids = observer.runtime_test_event_ids
    runtime_all = set(runtime_train_ids + runtime_validation_ids + runtime_test_ids)
    test_intersection = len(runtime_all & set(authority.test_event_ids))
    if (
        runtime_train_ids != authority.train_event_ids
        or runtime_validation_ids != authority.validation_event_ids
        or runtime_test_ids
        or test_intersection != 0
    ):
        _fail("RUNTIME_SPLIT_IDENTITY_OR_TEST_EXCLUSION_FAILED")

    raw_after = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    state_after = trainer_reference._state_integrity_snapshot_v1(state_root)
    trainer_reference._assert_protected_state_unchanged_v1(
        state_before["protected_state_fingerprint"],
        state_after["protected_state_fingerprint"],
    )
    trainer_reference._assert_external_state_ownership_stable_v1(
        state_before, state_after
    )
    checkpoint_after = _sha256_file(checkpoint_path)
    bound_after = (
        verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=repository_root
        )
    )
    artifact_after = tuple(
        (
            name,
            _sha256_file(
                repository_root / activation_owner.OUTPUT_ROOT_RELATIVE_V1 / name
            ),
        )
        for name, unused in ACTIVATION_ARTIFACT_SHA256_V1
    )
    if (
        raw_before != raw_after
        or checkpoint_before != checkpoint_after
        or bound_before != bound_after
        or artifact_before != artifact_after
    ):
        _fail("CHECKPOINT_RAW_OR_BOUND_SOURCE_STATE_CHANGED")

    supervision = datamodule.train_carrier.supervision
    migration_names = (
        "checkpoint_key_count",
        "target_model_key_count",
        "shared_key_count",
        "target_only_key_count",
        "checkpoint_only_key_count",
        "shared_shape_mismatch_count",
        "shared_checkpoint_tensor_equality_count",
    )
    trainer_config = tuple(
        (name, value)
        for name, value in runtime.trainer_kwargs.items()
        if name != "callbacks"
    )
    return CovapieBatch001FormalTrainValidationIntegrationResultV1(
        implementation_status="passed",
        result_interpretation=RESULT_INTERPRETATION_V1,
        formal_train_event_ids=authority.train_event_ids,
        formal_validation_event_ids=authority.validation_event_ids,
        formal_test_event_ids=authority.test_event_ids,
        runtime_train_event_ids=runtime_train_ids,
        runtime_validation_event_ids=runtime_validation_ids,
        runtime_test_event_ids=runtime_test_ids,
        train_runtime_matches_published_activation_authority=True,
        validation_runtime_matches_published_formal_validation_authority=True,
        formal_test_runtime_intersection_count=test_intersection,
        formal_leakage_group_cross_split_violation_count=0,
        train_sample_training_admitted_count=sum(
            datamodule.train_split_batch.sample_training_admitted
        ),
        validation_sample_training_admitted_count=0,
        test_sample_training_admitted_count=0,
        train_model_training_activation_authorized_count=sum(
            datamodule.train_split_batch.model_training_activation_authorized
        ),
        train_optimizer_population_eligible_count=sum(
            datamodule.train_split_batch.optimizer_population_eligible
        ),
        train_pair_candidate_count=len(supervision.pair_candidate_batch_index),
        train_pair_positive_count=int(
            supervision.pair_candidate_is_positive.sum().item()
        ),
        train_pair_negative_count=int(
            supervision.pair_candidate_is_negative.sum().item()
        ),
        PRE_geometry_train_active_count=int(
            supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()
        ),
        POST_geometry_train_active_count=int(
            supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()
        ),
        supervision_field_count=len(
            fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        ),
        formal_train_epoch=FORMAL_TRAIN_EPOCH_V1,
        task_schedule_seed=FORMAL_TASK_SCHEDULE_SEED_V1,
        scheduled_task_ids=datamodule.train_carrier.scheduled_task_ids,
        five_epoch_task_vectors=five_epoch_vectors,
        five_epoch_task_cycles_complete=True,
        datamodule_setup_fit_call_count=datamodule.setup_fit_call_count,
        train_dataloader_call_count=datamodule.train_dataloader_call_count,
        validation_dataloader_call_count=datamodule.validation_dataloader_call_count,
        train_dataset_getitem_count=datamodule.train_dataset.getitem_call_count,
        train_collator_call_count=datamodule.train_collator.call_count,
        validation_dataset_getitem_count=datamodule.validation_dataset.getitem_call_count,
        validation_collator_call_count=datamodule.validation_collator.call_count,
        test_dataset_getitem_count=datamodule.test_dataset_getitem_count,
        train_dataloader_length=len(datamodule.train_loader),
        validation_dataloader_length=len(datamodule.validation_loader),
        train_dataloader_sequential_sampler=(
            type(datamodule.train_loader.sampler) is SequentialSampler
        ),
        validation_dataloader_sequential_sampler=(
            type(datamodule.validation_loader.sampler) is SequentialSampler
        ),
        dataloader_batch_size=1,
        dataloader_num_workers=0,
        dataloader_drop_last=False,
        dataloader_pin_memory=False,
        dataloader_persistent_workers=False,
        trainer_configuration=trainer_config,
        trainer_api_family=runtime.trainer_api_family,
        active_python_version=platform.python_version(),
        active_torch_version=str(torch.__version__),
        active_lightning_version=str(pl.__version__),
        real_trainer_fit_invoked=True,
        trainer_fit_call_count=runtime.fit_call_count,
        train_batch_start_count=observer.train_batch_start_count,
        train_batch_end_count=observer.train_batch_end_count,
        automatic_backward_call_count=observer.after_backward_count,
        optimizer_step_count=observer.before_optimizer_step_count,
        zero_grad_lifecycle_call_count=observer.before_zero_grad_count,
        trainer_global_step=int(trainer.global_step),
        formal_validation_run_count=(
            model._covapie_formal_validation4_validation_run_count_v1
        ),
        formal_validation_step_count=observer.formal_validation_step_count,
        test_step_call_count=(
            observer.test_batch_count
            + model._covapie_batch001_test_step_call_count_v1
        ),
        Trainer_test_invoked=False,
        lifecycle_order=tuple(observer.lifecycle_order),
        training_step_metrics=observer.metrics,
        runtime_losses=observer.runtime_losses,
        optimizer_metadata=observer.optimizer_metadata,
        gradient_group_stats=observer.gradient_group_stats,
        geometry_component_gradient=observer.geometry_component_gradient,
        parameter_delta_group_stats=delta_stats,
        changed_parameter_tensor_count=changed_count,
        all_model_parameters_finite=True,
        pre_fit_state_fingerprint=pre_fit_state_fingerprint,
        post_optimizer_state_fingerprint=post_optimizer_fingerprint,
        validation_entry_state_fingerprint=validation_entry_fingerprint,
        validation_exit_state_fingerprint=validation_exit_fingerprint,
        post_optimizer_state_differs_from_pre_fit_state=True,
        validation_entry_uses_post_optimizer_current_state=True,
        active_state_unchanged_across_validation=True,
        formal_validation_result=formal_result,
        validation_task_domains=validation_domains,
        validation_model_weight_source=formal_result.validation_model_weight_source,
        validation_checkpoint_weight_migration_count=(
            formal_result.checkpoint_weight_migration_call_count_inside_validation
        ),
        checkpoint_initialization_migration_count=1,
        migration_counts=tuple(
            (name, int(migration[name])) for name in migration_names
        ),
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        checkpoint_unchanged=True,
        bound_source_sha256=bound_before,
        activation_artifact_sha256=artifact_before,
        integration_candidate_loss_weights=_loss_weights_tuple(candidate),
        integration_candidate_loss_weights_reused=True,
        production_geometry_weight_finalized=False,
        production_joint_loss_policy_finalized=False,
        active_model_parameters_unchanged_across_validation=(
            formal_result.active_model_parameters_unchanged
        ),
        active_model_buffers_unchanged_across_validation=(
            formal_result.active_model_buffers_unchanged
        ),
        active_model_gradient_states_unchanged_across_validation=(
            formal_result.active_model_gradient_states_unchanged
        ),
        active_model_registered_modules_unchanged_across_validation=(
            formal_result.active_model_registered_modules_unchanged
        ),
        active_model_registered_parameters_unchanged_across_validation=(
            formal_result.active_model_registered_parameters_unchanged
        ),
        active_model_registered_buffers_unchanged_across_validation=(
            formal_result.active_model_registered_buffers_unchanged
        ),
        formal_validation_estimate_count=formal_result.formal_validation_estimate_count,
        formal_validation_PRE_valid_count=formal_result.PRE_geometry_valid_count,
        formal_validation_POST_valid_count=formal_result.POST_geometry_valid_count,
        all_formal_validation_metrics_finite=True,
        current_state_key_count=formal_result.current_state_key_count,
        shadow_state_key_count=formal_result.shadow_state_key_count,
        shadow_strict_state_copy_parity=formal_result.shadow_strict_state_copy_parity,
        original_train_batch_unchanged=True,
        protected_sources_changed=False,
        protected_state_unchanged=True,
        raw_tree_unchanged=True,
        temporary_trainer_root_removed=True,
        persistent_output_created=False,
        training_performed=True,
        scientific_training_claimed=False,
        CPU_only=True,
        GPU_used=False,
        network_used=False,
        full_training_authorized=False,
        elapsed_seconds=time.perf_counter() - started,
        ready_for_gpt_review=True,
        ready_for_publication=True,
        ready_to_pivot_to_bulk_data_scale_after_publication=True,
        recommended_next_step_exactly=(
            "gpt_audit_batch001_formal_training_datamodule_and_train_validation_"
            "integration_then_publish_if_pass"
        ),
    )


def run_covapie_batch001_bounded_train_validation_integration_v1(
    *,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
    checkpoint_path: object = None,
    integration_loss_weights: object = None,
) -> CovapieBatch001FormalTrainValidationIntegrationResultV1:
    """Run one real CPU train batch/step and end-of-epoch formal validation4."""

    try:
        repository = _require_root(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_root(
            state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID"
        )
        cache = _require_root(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
        )
        checkpoint = (
            repository / CHECKPOINT_RELATIVE_PATH_V1
            if checkpoint_path is None
            else checkpoint_path
        )
        if type(checkpoint) is not _PATH_TYPE:
            _fail("CHECKPOINT_PATH_INVALID")
        return _run_impl(
            repository_root=repository,
            state_root=state,
            cache_root=cache,
            checkpoint_path=checkpoint,
            loss_weights=integration_loss_weights,
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as error:
        _public_error(error)

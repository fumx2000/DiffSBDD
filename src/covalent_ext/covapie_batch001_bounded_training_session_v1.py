"""Default-off bounded Batch001 train5 training-session assembly V1.

The prepare path builds and audits five real CPU train5 carriers and verifies
the identity of the sole bound checkpoint without deserializing it.  Model,
optimizer, and Trainer construction live behind an explicit future execution
authorization argument.  This module has no validation or test evaluator.
"""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import asdict, dataclass, fields, replace
import hashlib
import inspect
import io
import json
from pathlib import Path
import stat
from typing import Mapping, NoReturn, Sequence

import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


# This compatibility patch must precede imports of the real model owner.
patch_biopython_polypeptide_three_to_one()

import pytorch_lightning as pl  # noqa: E402
from covalent_ext import (  # noqa: E402
    checkpoint_compatible_model_instantiation as compatible_config_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_hidden_post_forward_adapter_v1 as forward_adapter_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as migration_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.diffsbdd_model_instantiation import (  # noqa: E402
    _constructor_kwargs,
)


__all__ = (
    "COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_ERROR_V1",
    "TASK_ID_V1",
    "EXACT_EPOCHS_V1",
    "TASK_SCHEDULE_SEED_V1",
    "CHECKPOINT_RELATIVE_PATH_V1",
    "CHECKPOINT_SIZE_BYTES_V1",
    "CHECKPOINT_SHA256_V1",
    "CANONICAL_MASK_CONTRACT_V1",
    "DEFAULT_LOSS_WEIGHTS_V1",
    "CovapieBatch001BoundedTrainingSessionConfigV1",
    "CovapieBatch001BoundedTrainingEpochSummaryV1",
    "CovapieBatch001BoundedTrainingSessionSummaryV1",
    "CovapieBatch001PreparedBoundedTrainingSessionV1",
    "CovapieBatch001BoundedTrainingDataModuleV1",
    "CovapieBatch001BoundedTrainingLigandPocketDDPMV1",
    "CovapieBatch001BoundedTrainingRuntimeV1",
    "verify_covapie_batch001_bounded_training_session_sources_v1",
    "verify_covapie_batch001_bounded_training_checkpoint_identity_v1",
    "validate_covapie_batch001_train5_epoch_carrier_v1",
    "transfer_covapie_batch001_train5_carrier_to_cpu_v1",
    "build_covapie_batch001_bounded_trainer_kwargs_v1",
    "prepare_covapie_batch001_bounded_training_session_v1",
    "build_covapie_batch001_bounded_training_runtime_v1",
    "execute_covapie_batch001_bounded_training_session_v1",
    "serialize_covapie_batch001_bounded_training_session_summary_v1",
    "main",
)


COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_ERROR_V1 = (
    "COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_V1_ERROR"
)
TASK_ID_V1 = "implement_covapie_batch001_bounded_training_session_v1"
EXACT_EPOCHS_V1 = (0, 1, 2, 3, 4)
TASK_SCHEDULE_SEED_V1 = 0
CHECKPOINT_RELATIVE_PATH_V1 = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)

# Semantic long names are authoritative.  Display aliases are secondary.
CANONICAL_MASK_CONTRACT_V1 = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
DEFAULT_LOSS_WEIGHTS_V1 = CovapieCurrent11LossWeightsV1(
    base_diffusion=1.0,
    covalent_pair_prediction=1.0,
    pre_post_geometry=0.0,
    covalent_pair_contrastive=0.1,
)

# Fixed identities published by the current no-update checkpoint/adapter
# evidence.  Values are expectations, never populated from the live tree.
DIRECT_BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_hidden_post_forward_adapter_v1.py",
        "a1830928e1784214980ae0c8bdad761802dd46c055c7335be0e7ee31005cd971",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
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
        "configs/crossdock_fullatom_joint.yml",
        "155ac1b9dba8af71946e1f4e17ca9176bd05acba0a6132e50b6929f2dbf3b0ea",
    ),
    (
        "data/derived/covalent_small/"
        "checkpoint_original_config_instantiation_design_v0/"
        "checkpoint_original_config_preview.json",
        "6960de3ebb1fa408b6188dac5fdade5e2b1fc1505408ca9142b1748e305d7f4a",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_DATASET_NAME_V1 = "crossdock_checkpoint_10d_fullatom_shape_smoke"
_MODEL_INITIALIZATION_SEED_V1 = 20260821
_PATH_TYPE = type(Path())
_TASK_DEPENDENT_SUPERVISION_FIELDS_V1 = frozenset((
    "canonical_task_id",
    "ligand_base_generation_mask",
    "ligand_base_fixed_mask",
    "ligand_base_target_mask",
    "ligand_base_context_mask",
    "ligand_active_diffusion_loss_mask",
))


@dataclass(frozen=True)
class CovapieBatch001BoundedTrainingSessionConfigV1:
    formal_split: str = "train"
    epochs: tuple[int, ...] = EXACT_EPOCHS_V1
    task_schedule_seed: int = TASK_SCHEDULE_SEED_V1
    accelerator: str = "cpu"
    devices: int = 1
    max_epochs: int = 5
    max_steps: int = 5
    limit_train_batches: int = 1
    accumulate_grad_batches: int = 1
    reload_dataloaders_every_n_epochs: int = 1
    train_loader_batch_size: int = 1
    train_loader_shuffle: bool = False
    train_loader_num_workers: int = 0
    validation_enabled: bool = False
    formal_validation_runtime_integrated: bool = False
    test_evaluation_enabled: bool = False


@dataclass(frozen=True)
class CovapieBatch001BoundedTrainingSourceBindingV1:
    relative_path: str
    expected_sha256: str
    observed_sha256: str
    sha256_verified: bool


@dataclass(frozen=True)
class CovapieBatch001BoundedTrainingEpochSummaryV1:
    epoch: int
    sample_identities: tuple[str, ...]
    applicable_task_ids: tuple[tuple[int, ...], ...]
    scheduled_task_ids: tuple[int, ...]
    generated_atom_counts: tuple[int, ...]
    fixed_atom_counts: tuple[int, ...]
    hidden_post_eligible_count: int
    carrier_fingerprint: str


@dataclass(frozen=True)
class CovapieBatch001BoundedTrainingSessionSummaryV1:
    schema_version: str
    task_id: str
    implementation_status: str
    source_bindings: tuple[CovapieBatch001BoundedTrainingSourceBindingV1, ...]
    checkpoint_relative_path: str
    checkpoint_size_bytes: int
    checkpoint_sha256: str
    checkpoint_identity_verified: bool
    canonical_mask_semantic_names: tuple[str, ...]
    canonical_mask_display_aliases: tuple[str, ...]
    epochs: tuple[int, ...]
    task_schedule_seed: int
    epoch_summaries: tuple[CovapieBatch001BoundedTrainingEpochSummaryV1, ...]
    trainer_configuration: tuple[tuple[str, object], ...]
    validation_enabled: bool
    formal_validation_runtime_integrated: bool
    test_evaluation_enabled: bool
    default_prepare_only: bool
    checkpoint_loaded: bool
    real_model_instantiated: bool
    real_forward_executed: bool
    production_loss_executed: bool
    backward_executed: bool
    optimizer_created: bool
    optimizer_step_executed: bool
    parameter_update_performed: bool
    trainer_created: bool
    trainer_fit_executed: bool
    trainer_runtime_integration_validated: bool
    formal_scientific_training_started: bool
    ready_for_training: bool
    geometry_training_gradient_accepted: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool
    prior_single_step_authorization_consumed: bool


@dataclass(frozen=True)
class CovapieBatch001PreparedBoundedTrainingSessionV1:
    config: CovapieBatch001BoundedTrainingSessionConfigV1
    authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1
    carriers: tuple[
        activation_owner.CovapieBatch001ModelUsableSplitBatchV1, ...
    ]
    summary: CovapieBatch001BoundedTrainingSessionSummaryV1


@dataclass
class CovapieBatch001BoundedTrainingRuntimeV1:
    model: pl.LightningModule
    datamodule: "CovapieBatch001BoundedTrainingDataModuleV1"
    trainer: pl.Trainer
    checkpoint_metadata: Mapping[str, object]
    migration_metadata: Mapping[str, object]
    trainer_kwargs: Mapping[str, object]
    fit_call_count: int = 0


def _fail(reason: str) -> NoReturn:
    raise ValueError(
        f"{COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_ERROR_V1}:{reason}"
    )


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    result = default if value is None else value
    if (
        type(result) is not _PATH_TYPE
        or not result.is_absolute()
        or not result.is_dir()
    ):
        _fail(reason)
    return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        _fail("BOUND_FILE_UNREADABLE")
    return digest.hexdigest()


def _safe_regular_file_identity(path: Path) -> tuple[int, str]:
    try:
        metadata = path.lstat()
    except OSError:
        _fail("BOUND_FILE_UNREADABLE")
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        _fail("BOUND_FILE_NOT_REGULAR")
    return metadata.st_size, _sha256_file(path)


def _validate_config(
    config: object,
) -> CovapieBatch001BoundedTrainingSessionConfigV1:
    if type(config) is not CovapieBatch001BoundedTrainingSessionConfigV1:
        _fail("SESSION_CONFIG_TYPE_INVALID")
    expected = CovapieBatch001BoundedTrainingSessionConfigV1()
    if config != expected:
        _fail("SESSION_CONFIG_OUTSIDE_EXACT_BOUNDED_TRAIN5_POLICY")
    return config


def verify_covapie_batch001_bounded_training_session_sources_v1(
    *, repository_root: object = None
) -> tuple[CovapieBatch001BoundedTrainingSourceBindingV1, ...]:
    """Fail closed on current adapter, migration, and constructor source pins."""

    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    observed = []
    for relative, expected in DIRECT_BOUND_SOURCE_SHA256_V1:
        size, digest = _safe_regular_file_identity(repository / relative)
        if size <= 0 or digest != expected:
            _fail("DIRECT_BOUND_SOURCE_SHA256_MISMATCH:" + relative)
        observed.append(CovapieBatch001BoundedTrainingSourceBindingV1(
            relative_path=relative,
            expected_sha256=expected,
            observed_sha256=digest,
            sha256_verified=True,
        ))
    try:
        forward_adapter_owner.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
            repository_root=repository
        )
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_ERROR_V1}:"
            "CURRENT_HIDDEN_POST_ADAPTER_SOURCE_BINDING_REJECTED"
        ) from error
    return tuple(observed)


def verify_covapie_batch001_bounded_training_checkpoint_identity_v1(
    *, repository_root: object = None
) -> tuple[int, str]:
    """Hash the bound checkpoint without calling ``torch.load``."""

    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    size, digest = _safe_regular_file_identity(
        repository / CHECKPOINT_RELATIVE_PATH_V1
    )
    if size != CHECKPOINT_SIZE_BYTES_V1 or digest != CHECKPOINT_SHA256_V1:
        _fail("CHECKPOINT_IDENTITY_MISMATCH")
    if (
        size != migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
        or digest
        != migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
    ):
        _fail("CHECKPOINT_MIGRATION_OWNER_IDENTITY_MISMATCH")
    return size, digest


def _validate_canonical_mask_contract_v1() -> None:
    observed = tuple((row[0], row[1], row[2]) for row in CANONICAL_TASKS_V1)
    if observed != CANONICAL_MASK_CONTRACT_V1 or len(observed) != 5:
        _fail("CANONICAL_EXACT5_MASK_CONTRACT_DRIFT")


def _all_carrier_tensors(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> tuple[torch.Tensor, ...]:
    model_tensors = tuple(
        value
        for value in carrier.model_input_batch.values()
        if isinstance(value, torch.Tensor)
    )
    if not isinstance(
        carrier.supervision, CovapieCurrent11TrainingSupervisionTensorsV1
    ):
        _fail("CARRIER_SUPERVISION_TYPE_INVALID")
    return model_tensors + tuple(
        getattr(carrier.supervision, field.name)
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )


def _carrier_audit(
    carrier: object,
    *,
    expected_epoch: object,
    task_schedule_seed: object,
) -> tuple[str, tuple[preflight_owner.CovapieBatch001HiddenPostEligibilityRowV1, ...]]:
    if type(carrier) is not activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        _fail("CARRIER_TYPE_INVALID")
    if (
        type(expected_epoch) is not int
        or expected_epoch not in EXACT_EPOCHS_V1
        or carrier.epoch != expected_epoch
    ):
        _fail("CARRIER_EPOCH_MISMATCH")
    if (
        type(task_schedule_seed) is not int
        or task_schedule_seed != TASK_SCHEDULE_SEED_V1
        or carrier.task_schedule_seed != task_schedule_seed
    ):
        _fail("CARRIER_TASK_SCHEDULE_SEED_MISMATCH")
    scheduled = carrier.training_scheduled_task_ids
    tensors = _all_carrier_tensors(carrier)
    if (
        carrier.formal_split != "train"
        or carrier.sample_identities != activation_owner.FORMAL_TRAIN_EVENT_IDS_V1
        or len(carrier.sample_identities) != 5
        or any(type(value) is not int for value in scheduled)
        or tuple(scheduled) != carrier.preview_tensorization_task_ids
        or carrier.supervision.canonical_task_id.tolist() != list(scheduled)
        or any(
            task not in applicable
            for task, applicable in zip(scheduled, carrier.applicable_task_ids)
        )
        or carrier.sample_training_admitted != (True,) * 5
        or carrier.model_training_activation_authorized != (True,) * 5
        or carrier.optimizer_population_eligible != (True,) * 5
        or carrier.training_scheduler_eligible != (True,) * 5
        or carrier.formal_validation_population_member != (False,) * 5
        or carrier.formal_test_population_member != (False,) * 5
        or not tensors
        or any(
            tensor.device.type != "cpu" or tensor.requires_grad
            for tensor in tensors
        )
    ):
        _fail("EXACT_TRAIN5_CARRIER_CONTRACT_INVALID")
    try:
        activation_owner.validate_covapie_batch001_training_activation_population_v1(
            sample_identities=carrier.sample_identities,
            formal_splits=(carrier.formal_split,) * 5,
        )
        return preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
            carrier
        )
    except ValueError as error:
        raise ValueError(
            f"{COVAPIE_BATCH001_BOUNDED_TRAINING_SESSION_ERROR_V1}:"
            "PUBLISHED_CARRIER_AUDIT_REJECTED"
        ) from error


def validate_covapie_batch001_train5_epoch_carrier_v1(
    carrier: object,
    *,
    expected_epoch: object,
    task_schedule_seed: object = TASK_SCHEDULE_SEED_V1,
) -> bool:
    """Validate one current real train5 carrier without mutation."""

    _carrier_audit(
        carrier,
        expected_epoch=expected_epoch,
        task_schedule_seed=task_schedule_seed,
    )
    return True


def _epoch_summary(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> CovapieBatch001BoundedTrainingEpochSummaryV1:
    fingerprint, rows = _carrier_audit(
        carrier,
        expected_epoch=carrier.epoch,
        task_schedule_seed=carrier.task_schedule_seed,
    )
    membership = carrier.model_input_batch.get("lig_mask")
    if not isinstance(membership, torch.Tensor):
        _fail("CARRIER_LIGAND_MEMBERSHIP_INVALID")
    generation = carrier.supervision.ligand_base_generation_mask[:, 0]
    fixed = carrier.supervision.ligand_base_fixed_mask[:, 0]
    generated_counts = tuple(
        int(generation[membership == sample].sum().item()) for sample in range(5)
    )
    fixed_counts = tuple(
        int(fixed[membership == sample].sum().item()) for sample in range(5)
    )
    if any(left <= 0 or right < 0 for left, right in zip(generated_counts, fixed_counts)):
        _fail("GENERATION_OR_FIXED_MASK_COUNT_INVALID")
    return CovapieBatch001BoundedTrainingEpochSummaryV1(
        epoch=carrier.epoch,
        sample_identities=carrier.sample_identities,
        applicable_task_ids=carrier.applicable_task_ids,
        scheduled_task_ids=tuple(int(value) for value in carrier.training_scheduled_task_ids),
        generated_atom_counts=generated_counts,
        fixed_atom_counts=fixed_counts,
        hidden_post_eligible_count=sum(
            row.preflight_effective_hidden_post_eligible for row in rows
        ),
        carrier_fingerprint=fingerprint,
    )


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        if left.dtype != right.dtype or left.shape != right.shape:
            return False
        if left.is_floating_point():
            return bool(torch.allclose(left, right, rtol=0, atol=0, equal_nan=True))
        return torch.equal(left, right)
    return type(left) is type(right) and bool(left == right)


def _validate_cross_epoch_static_parity(
    carriers: Sequence[
        activation_owner.CovapieBatch001ModelUsableSplitBatchV1
    ],
) -> None:
    values = tuple(carriers)
    if len(values) != 5:
        _fail("CROSS_EPOCH_CARRIER_DOMAIN_INVALID")
    baseline = values[0]
    static_supervision_fields = tuple(
        field.name
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        if field.name not in _TASK_DEPENDENT_SUPERVISION_FIELDS_V1
    )
    for carrier in values[1:]:
        if (
            carrier.sample_identities != baseline.sample_identities
            or carrier.role_profiles != baseline.role_profiles
            or carrier.applicable_task_ids != baseline.applicable_task_ids
            or carrier.structural_records != baseline.structural_records
            or carrier.source_authority_bindings != baseline.source_authority_bindings
            or tuple(carrier.model_input_batch) != tuple(baseline.model_input_batch)
            or any(
                not _same_value(
                    baseline.model_input_batch[name],
                    carrier.model_input_batch[name],
                )
                for name in baseline.model_input_batch
            )
            or any(
                not _same_value(
                    getattr(baseline.supervision, name),
                    getattr(carrier.supervision, name),
                )
                for name in static_supervision_fields
            )
        ):
            _fail("CROSS_EPOCH_STATIC_CHEMISTRY_OR_LABEL_DRIFT")


def _move_tensor_to_cpu(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.to(device=torch.device("cpu"))
    return value


def transfer_covapie_batch001_train5_carrier_to_cpu_v1(
    carrier: object,
    *,
    current_epoch: object,
    task_schedule_seed: object = TASK_SCHEDULE_SEED_V1,
) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
    """Rebuild the carrier around CPU tensors while preserving all metadata."""

    _carrier_audit(
        carrier,
        expected_epoch=current_epoch,
        task_schedule_seed=task_schedule_seed,
    )
    model_input = {
        name: _move_tensor_to_cpu(value)
        for name, value in carrier.model_input_batch.items()
    }
    supervision_values = {
        field.name: _move_tensor_to_cpu(getattr(carrier.supervision, field.name))
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    transferred = replace(
        carrier,
        model_input_batch=model_input,
        supervision=CovapieCurrent11TrainingSupervisionTensorsV1(
            **supervision_values
        ),
    )
    _carrier_audit(
        transferred,
        expected_epoch=current_epoch,
        task_schedule_seed=task_schedule_seed,
    )
    return transferred


class _SingleTrain5CarrierDatasetV1(
    Dataset[activation_owner.CovapieBatch001ModelUsableSplitBatchV1]
):
    def __init__(
        self,
        carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    ) -> None:
        self.carrier = carrier

    def __len__(self) -> int:
        return 1

    def __getitem__(
        self, index: int
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        return self.carrier


class _SingleTrain5CarrierCollatorV1:
    def __init__(
        self,
        carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    ) -> None:
        self.carrier = carrier

    def __call__(
        self,
        rows: list[activation_owner.CovapieBatch001ModelUsableSplitBatchV1],
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        if len(rows) != 1 or rows[0] is not self.carrier:
            _fail("TRAIN_LOADER_COLLATE_CONTRACT_INVALID")
        return rows[0]


class CovapieBatch001BoundedTrainingDataModuleV1(pl.LightningDataModule):
    """Epoch-aware exact train5 DataModule with no held-out loader."""

    def __init__(
        self,
        *,
        carriers: Sequence[
            activation_owner.CovapieBatch001ModelUsableSplitBatchV1
        ],
        config: CovapieBatch001BoundedTrainingSessionConfigV1,
    ) -> None:
        super().__init__()
        self.config = _validate_config(config)
        self.carriers = tuple(carriers)
        if (
            len(self.carriers) != 5
            or tuple(carrier.epoch for carrier in self.carriers) != EXACT_EPOCHS_V1
        ):
            _fail("DATAMODULE_CARRIER_EPOCH_DOMAIN_INVALID")
        for epoch, carrier in zip(EXACT_EPOCHS_V1, self.carriers):
            _carrier_audit(
                carrier,
                expected_epoch=epoch,
                task_schedule_seed=self.config.task_schedule_seed,
            )

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("DATAMODULE_SETUP_FIT_ONLY")

    def _carrier_for_epoch(
        self, epoch: object
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        if type(epoch) is not int or epoch not in EXACT_EPOCHS_V1:
            _fail("DATAMODULE_CURRENT_EPOCH_INVALID")
        carrier = self.carriers[epoch]
        _carrier_audit(
            carrier,
            expected_epoch=epoch,
            task_schedule_seed=self.config.task_schedule_seed,
        )
        return carrier

    def build_train_dataloader_for_epoch_v1(self, epoch: object) -> DataLoader:
        """Pure epoch selector used by ``train_dataloader`` and no-update QA."""

        carrier = self._carrier_for_epoch(epoch)
        dataset = _SingleTrain5CarrierDatasetV1(carrier)
        loader = DataLoader(
            dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=_SingleTrain5CarrierCollatorV1(carrier),
        )
        if (
            len(loader) != 1
            or loader.batch_size != 1
            or type(loader.sampler) is not SequentialSampler
            or loader.num_workers != 0
            or loader.drop_last is not False
            or loader.pin_memory is not False
            or loader.persistent_workers is not False
        ):
            _fail("DATAMODULE_TRAIN_LOADER_CONFIGURATION_INVALID")
        return loader

    def _trainer_current_epoch(self) -> int:
        trainer = getattr(self, "trainer", None)
        epoch = getattr(trainer, "current_epoch", None)
        if type(epoch) is not int or epoch not in EXACT_EPOCHS_V1:
            _fail("DATAMODULE_REAL_TRAINER_CURRENT_EPOCH_REQUIRED")
        return epoch

    def train_dataloader(self) -> DataLoader:
        return self.build_train_dataloader_for_epoch_v1(
            self._trainer_current_epoch()
        )

    def val_dataloader(self) -> NoReturn:
        _fail("FORMAL_VALIDATION_DATALOADER_NOT_INTEGRATED")

    def test_dataloader(self) -> NoReturn:
        _fail("FORMAL_TEST_DATALOADER_ACCESS_FORBIDDEN")

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        epoch = self._trainer_current_epoch()
        if dataloader_idx != 0 or batch is not self.carriers[epoch]:
            _fail("DATAMODULE_BEFORE_TRANSFER_EPOCH_OR_IDENTITY_MISMATCH")
        _carrier_audit(
            batch,
            expected_epoch=epoch,
            task_schedule_seed=self.config.task_schedule_seed,
        )
        return batch

    def on_after_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        epoch = self._trainer_current_epoch()
        if dataloader_idx != 0:
            _fail("DATAMODULE_AFTER_TRANSFER_DATALOADER_INDEX_INVALID")
        _carrier_audit(
            batch,
            expected_epoch=epoch,
            task_schedule_seed=self.config.task_schedule_seed,
        )
        return batch


class CovapieBatch001BoundedTrainingLigandPocketDDPMV1(
    forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
):
    """Thin Trainer-lifecycle adapter; model math and optimizer are inherited."""

    # Lightning 2 rejects the legacy epoch-end hook inherited from DiffSBDD.
    validation_epoch_end = None

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("MODEL_SETUP_FIT_ONLY")
        trainer = getattr(self, "trainer", None)
        datamodule = getattr(trainer, "datamodule", None)
        if type(datamodule) is not CovapieBatch001BoundedTrainingDataModuleV1:
            _fail("MODEL_SETUP_BOUNDED_DATAMODULE_REQUIRED")
        if any(
            getattr(self, name, None) is not None
            for name in ("train_dataset", "val_dataset", "test_dataset")
        ):
            _fail("MODEL_SETUP_LEGACY_DATASET_PRESENT")
        return None

    def transfer_batch_to_device(
        self,
        batch: object,
        device: torch.device,
        dataloader_idx: int,
    ) -> activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
        if device != torch.device("cpu") or dataloader_idx != 0:
            _fail("MODEL_TRANSFER_EXACT_CPU_TRAIN_LOADER_REQUIRED")
        return transfer_covapie_batch001_train5_carrier_to_cpu_v1(
            batch,
            current_epoch=int(self.current_epoch),
            task_schedule_seed=self.covapie_current11_task_schedule_seed,
        )

    def configure_gradient_clipping(
        self,
        optimizer: torch.optim.Optimizer,
        gradient_clip_val: float | int | None = None,
        gradient_clip_algorithm: str | None = None,
    ) -> None:
        del optimizer
        if gradient_clip_val is not None or gradient_clip_algorithm is not None:
            _fail("GRADIENT_CLIPPING_MUST_REMAIN_DISABLED")


def _validate_model_routing_v1() -> None:
    owner = CovapieBatch001BoundedTrainingLigandPocketDDPMV1
    if (
        owner.__mro__[1]
        is not forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
        or getattr(owner, "forward")
        is not forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1.forward
        or getattr(owner, "training_step")
        is not CovapieCurrent11TrainingLigandPocketDDPM.training_step
        or getattr(owner, "configure_optimizers")
        is not CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
        or "__init__" in owner.__dict__
        or any(
            isinstance(value, (torch.nn.Parameter, torch.nn.Module))
            for value in owner.__dict__.values()
        )
    ):
        _fail("CURRENT_FORWARD_TRAINING_STEP_OR_OPTIMIZER_ROUTING_INVALID")


def _trainer_signature_configuration(
    *, signature: inspect.Signature, default_root_dir: Path
) -> dict[str, object]:
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
        "enable_checkpointing",
        "callbacks",
        "logger",
        "gradient_clip_val",
        "accumulate_grad_batches",
        "deterministic",
        "enable_progress_bar",
        "default_root_dir",
        "reload_dataloaders_every_n_epochs",
    }
    if not required <= parameters:
        _fail("TRAINER_SIGNATURE_REQUIRED_CAPABILITY_MISSING")
    if "use_distributed_sampler" in parameters:
        sampler = "use_distributed_sampler"
        precision: object = "32-true"
    elif "replace_sampler_ddp" in parameters:
        sampler = "replace_sampler_ddp"
        precision = 32
    else:
        _fail("TRAINER_SAMPLER_CONTROL_MISSING")
    kwargs: dict[str, object] = {
        "accelerator": "cpu",
        "devices": 1,
        "num_nodes": 1,
        "precision": precision,
        "max_epochs": 5,
        "min_epochs": 5,
        "max_steps": 5,
        "limit_train_batches": 1,
        "limit_val_batches": 0,
        "limit_test_batches": 0,
        "num_sanity_val_steps": 0,
        "enable_checkpointing": False,
        "callbacks": [],
        "logger": False,
        "gradient_clip_val": None,
        "accumulate_grad_batches": 1,
        "deterministic": True,
        "enable_progress_bar": False,
        "reload_dataloaders_every_n_epochs": 1,
        "default_root_dir": str(default_root_dir),
        sampler: False,
    }
    optional = {
        "check_val_every_n_epoch": 1,
        "val_check_interval": 1.0,
        "gradient_clip_algorithm": None,
        "benchmark": False,
        "sync_batchnorm": False,
        "enable_model_summary": False,
        "log_every_n_steps": 1,
        "profiler": None,
    }
    kwargs.update(
        {name: value for name, value in optional.items() if name in parameters}
    )
    return kwargs


def _validate_trainer_kwargs(kwargs: Mapping[str, object]) -> None:
    sampler_names = tuple(
        name
        for name in ("use_distributed_sampler", "replace_sampler_ddp")
        if name in kwargs
    )
    required_exact = {
        "accelerator": "cpu",
        "devices": 1,
        "num_nodes": 1,
        "max_epochs": 5,
        "min_epochs": 5,
        "max_steps": 5,
        "limit_train_batches": 1,
        "limit_val_batches": 0,
        "limit_test_batches": 0,
        "num_sanity_val_steps": 0,
        "enable_checkpointing": False,
        "logger": False,
        "gradient_clip_val": None,
        "accumulate_grad_batches": 1,
        "deterministic": True,
        "enable_progress_bar": False,
        "reload_dataloaders_every_n_epochs": 1,
    }
    exact_int_fields = (
        "devices",
        "num_nodes",
        "max_epochs",
        "min_epochs",
        "max_steps",
        "limit_train_batches",
        "limit_val_batches",
        "limit_test_batches",
        "num_sanity_val_steps",
        "accumulate_grad_batches",
        "reload_dataloaders_every_n_epochs",
    )
    callbacks = kwargs.get("callbacks")
    expected_precision: object = (
        "32-true" if sampler_names == ("use_distributed_sampler",) else 32
    )
    if (
        any(kwargs.get(name) != value for name, value in required_exact.items())
        or any(type(kwargs.get(name)) is not int for name in exact_int_fields)
        or len(sampler_names) != 1
        or kwargs[sampler_names[0]] is not False
        or type(callbacks) is not list
        or callbacks
        or kwargs.get("profiler", None) is not None
        or kwargs.get("gradient_clip_algorithm", None) is not None
        or kwargs.get("enable_model_summary", False) is not False
        or kwargs.get("default_root_dir") is None
        or kwargs.get("precision") != expected_precision
    ):
        _fail("TRAINER_CONFIGURATION_OUTSIDE_EXACT_BOUNDED_CPU_POLICY")


def build_covapie_batch001_bounded_trainer_kwargs_v1(
    *,
    default_root_dir: object,
    overrides: Mapping[str, object] | None = None,
    trainer_signature: inspect.Signature | None = None,
) -> dict[str, object]:
    """Build an exact Trainer plan without constructing ``pl.Trainer``."""

    root = _require_directory(
        default_root_dir,
        default=Path("/__no_default__"),
        reason="TRAINER_DEFAULT_ROOT_INVALID",
    )
    signature = (
        inspect.signature(pl.Trainer.__init__)
        if trainer_signature is None
        else trainer_signature
    )
    if not isinstance(signature, inspect.Signature):
        _fail("TRAINER_SIGNATURE_INVALID")
    kwargs = _trainer_signature_configuration(
        signature=signature, default_root_dir=root
    )
    if overrides is not None:
        if type(overrides) is not dict or any(name not in kwargs for name in overrides):
            _fail("TRAINER_OVERRIDE_KEY_INVALID")
        kwargs.update(overrides)
    _validate_trainer_kwargs(kwargs)
    return kwargs


def _trainer_configuration_summary(
    kwargs: Mapping[str, object]
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (name, value)
        for name, value in sorted(kwargs.items())
        if name not in {"callbacks", "default_root_dir"}
    ) + (("callbacks", ()),)


def prepare_covapie_batch001_bounded_training_session_v1(
    *,
    config: CovapieBatch001BoundedTrainingSessionConfigV1 | None = None,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001PreparedBoundedTrainingSessionV1:
    """Prepare and audit five carriers; never build a model, optimizer, or Trainer."""

    selected_config = _validate_config(
        CovapieBatch001BoundedTrainingSessionConfigV1()
        if config is None
        else config
    )
    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    cache = _require_directory(
        cache_root,
        default=_DEFAULT_CACHE_ROOT,
        reason="CACHE_ROOT_INVALID",
    )
    bindings = verify_covapie_batch001_bounded_training_session_sources_v1(
        repository_root=repository
    )
    checkpoint_size, checkpoint_sha = (
        verify_covapie_batch001_bounded_training_checkpoint_identity_v1(
            repository_root=repository
        )
    )
    _validate_canonical_mask_contract_v1()
    _validate_model_routing_v1()
    authority = activation_owner.load_covapie_batch001_formal_split_authority_v1(
        repository_root=repository
    )
    if (
        authority.train_event_ids != activation_owner.FORMAL_TRAIN_EVENT_IDS_V1
        or len(authority.validation_event_ids) != 4
        or len(authority.test_event_ids) != 4
        or authority.formal_leakage_group_cross_split_violation_count != 0
    ):
        _fail("FORMAL_SPLIT_AUTHORITY_INVALID")
    carriers = []
    for epoch in selected_config.epochs:
        carrier = activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
            split=selected_config.formal_split,
            epoch=epoch,
            task_schedule_seed=selected_config.task_schedule_seed,
            repository_root=repository,
            cache_root=cache,
        )
        activation_owner.validate_covapie_batch001_model_usable_split_batch_v1(
            carrier, authority=authority
        )
        _carrier_audit(
            carrier,
            expected_epoch=epoch,
            task_schedule_seed=selected_config.task_schedule_seed,
        )
        carriers.append(carrier)
    carrier_tuple = tuple(carriers)
    _validate_cross_epoch_static_parity(carrier_tuple)
    if any(
        {
            carrier_tuple[epoch].training_scheduled_task_ids[sample]
            for epoch in EXACT_EPOCHS_V1
        }
        != set(range(5))
        for sample in range(5)
    ):
        _fail("TRAIN5_FIVE_EPOCH_TASK_REFRESH_INCOMPLETE")
    # Constructing this DataModule is metadata/tensor assembly only.  No
    # Trainer is attached and no lifecycle method is called here.
    CovapieBatch001BoundedTrainingDataModuleV1(
        carriers=carrier_tuple, config=selected_config
    )
    trainer_kwargs = build_covapie_batch001_bounded_trainer_kwargs_v1(
        default_root_dir=repository
    )
    epoch_summaries = tuple(_epoch_summary(carrier) for carrier in carrier_tuple)
    summary = CovapieBatch001BoundedTrainingSessionSummaryV1(
        schema_version="covapie_batch001_bounded_training_session_v1",
        task_id=TASK_ID_V1,
        implementation_status="PREPARED_NOT_EXECUTED",
        source_bindings=bindings,
        checkpoint_relative_path=CHECKPOINT_RELATIVE_PATH_V1.as_posix(),
        checkpoint_size_bytes=checkpoint_size,
        checkpoint_sha256=checkpoint_sha,
        checkpoint_identity_verified=True,
        canonical_mask_semantic_names=tuple(
            row[1] for row in CANONICAL_MASK_CONTRACT_V1
        ),
        canonical_mask_display_aliases=tuple(
            row[2] for row in CANONICAL_MASK_CONTRACT_V1
        ),
        epochs=selected_config.epochs,
        task_schedule_seed=selected_config.task_schedule_seed,
        epoch_summaries=epoch_summaries,
        trainer_configuration=_trainer_configuration_summary(trainer_kwargs),
        validation_enabled=False,
        formal_validation_runtime_integrated=False,
        test_evaluation_enabled=False,
        default_prepare_only=True,
        checkpoint_loaded=False,
        real_model_instantiated=False,
        real_forward_executed=False,
        production_loss_executed=False,
        backward_executed=False,
        optimizer_created=False,
        optimizer_step_executed=False,
        parameter_update_performed=False,
        trainer_created=False,
        trainer_fit_executed=False,
        trainer_runtime_integration_validated=False,
        formal_scientific_training_started=False,
        ready_for_training=False,
        geometry_training_gradient_accepted=False,
        feature_semantics_audit_required_later=True,
        step12d_is_only_smoke_legality_check=True,
        prior_single_step_authorization_consumed=True,
    )
    return CovapieBatch001PreparedBoundedTrainingSessionV1(
        config=selected_config,
        authority=authority,
        carriers=carrier_tuple,
        summary=summary,
    )


def _instantiate_authorized_model_v1(
    *,
    checkpoint: Mapping[str, object],
    repository_root: Path,
    state_root: Path,
    runtime_root: Path,
) -> CovapieBatch001BoundedTrainingLigandPocketDDPMV1:
    """Future-only real construction using published config helpers."""

    legacy = checkpoint.get("legacy_constructor")
    if type(legacy) is not dict:
        _fail("VALIDATED_LEGACY_CONSTRUCTOR_MISSING")
    preview = compatible_config_owner.load_config_preview_v0(
        repository_root / compatible_config_owner.CONFIG_PREVIEW_PATH
    )
    if preview.get("config_preview_loaded") is not True:
        _fail("CHECKPOINT_CONFIG_PREVIEW_REJECTED")
    compatible = compatible_config_owner.build_checkpoint_compatible_config_v0(
        preview["preview"],
        repository_root / compatible_config_owner.BEST_CONFIG_CANDIDATE_PATH,
    )
    if compatible.get("compatible_config_built") is not True:
        _fail("CHECKPOINT_COMPATIBLE_CONFIG_REJECTED")
    config = compatible_config_owner._constructor_config_from_compatible_config(
        compatible,
        _DATASET_NAME_V1,
        "cpu",
        node_histogram=legacy["node_histogram"],
    )
    if (
        config["egnn_params"] != dict(legacy["egnn_params"], device="cpu")
        or config["diffusion_params"] != legacy["diffusion_params"]
        or config["eval_params"] != legacy["eval_params"]
        or config["loss_params"] != legacy["loss_params"]
        or config["node_histogram"] != legacy["node_histogram"]
        or config["lr"] != 0.001
        or config["clip_grad"] is not False
        or config["mode"] != "pocket_conditioning"
        or config["pocket_representation"] != "full-atom"
        or config["virtual_nodes"] is not False
    ):
        _fail("CHECKPOINT_CONSTRUCTOR_CONFIG_DRIFT")
    legacy_setup = runtime_root / "legacy_setup_data"
    legacy_setup.mkdir(mode=0o700)
    config.update({
        "outdir": runtime_root / "model_output_disabled",
        "datadir": str(legacy_setup),
        "batch_size": 5,
    })
    kwargs = _constructor_kwargs(config)
    kwargs.update({
        "target_residue_atom_conditioning": True,
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(repository_root),
        "covapie_state_root": str(state_root),
        "covapie_current11_training_enabled": True,
        "covapie_current11_task_schedule_seed": TASK_SCHEDULE_SEED_V1,
        "covapie_current11_pair_contrastive_temperature": 1.0,
        "covapie_current11_loss_weights": DEFAULT_LOSS_WEIGHTS_V1,
        "covapie_batch001_hidden_post_forward_enabled": True,
    })
    import constants  # noqa: PLC0415

    torch.random.default_generator.manual_seed(_MODEL_INITIALIZATION_SEED_V1)
    previous = constants.dataset_params.get(_DATASET_NAME_V1)
    constants.dataset_params[_DATASET_NAME_V1] = (
        compatible_config_owner._temporary_10d_dataset_info()
    )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = CovapieBatch001BoundedTrainingLigandPocketDDPMV1(**kwargs)
    finally:
        if previous is None:
            constants.dataset_params.pop(_DATASET_NAME_V1, None)
        else:
            constants.dataset_params[_DATASET_NAME_V1] = previous
    model = model.to(torch.device("cpu"))
    if (
        type(model) is not CovapieBatch001BoundedTrainingLigandPocketDDPMV1
        or len(model.state_dict()) != 141
        or model.device != torch.device("cpu")
        or model.batch_size != 5
        or model.automatic_optimization is not True
        or model.covapie_current11_loss_weights != DEFAULT_LOSS_WEIGHTS_V1
        or model.mode != "pocket_conditioning"
        or model.pocket_representation != "full-atom"
        or model.atom_nf != 10
        or model.aa_nf != 10
        or model.virtual_nodes is not False
        or model.target_residue_atom_conditioning is not True
        or model.ddpm.loss_type != "l2"
    ):
        _fail("REAL_MODEL_CONFIGURATION_INVALID")
    return model


def build_covapie_batch001_bounded_training_runtime_v1(
    *,
    execution_authorized: object = False,
    prepared: object,
    runtime_root: object,
    repository_root: object = None,
    state_root: object = None,
) -> CovapieBatch001BoundedTrainingRuntimeV1:
    """Future-only runtime builder; callers must have separate user authority."""

    if execution_authorized is not True:
        _fail("EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    if type(prepared) is not CovapieBatch001PreparedBoundedTrainingSessionV1:
        _fail("PREPARED_SESSION_TYPE_INVALID")
    _validate_config(prepared.config)
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
    runtime = _require_directory(
        runtime_root,
        default=Path("/__no_default__"),
        reason="RUNTIME_ROOT_INVALID",
    )
    if any(runtime.iterdir()):
        _fail("RUNTIME_ROOT_MUST_BE_EMPTY")
    verify_covapie_batch001_bounded_training_session_sources_v1(
        repository_root=repository
    )
    verify_covapie_batch001_bounded_training_checkpoint_identity_v1(
        repository_root=repository
    )
    checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=repository / CHECKPOINT_RELATIVE_PATH_V1
    )
    model = _instantiate_authorized_model_v1(
        checkpoint=checkpoint,
        repository_root=repository,
        state_root=state,
        runtime_root=runtime,
    )
    migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=checkpoint["state_dict"],
    )
    if migration.get("full_target_strict_load") is not True:
        _fail("STRICT_CHECKPOINT_MIGRATION_NOT_PROVEN")
    datamodule = CovapieBatch001BoundedTrainingDataModuleV1(
        carriers=prepared.carriers, config=prepared.config
    )
    trainer_kwargs = build_covapie_batch001_bounded_trainer_kwargs_v1(
        default_root_dir=runtime
    )
    fit_parameters = set(inspect.signature(pl.Trainer.fit).parameters)
    if not {"model", "datamodule", "ckpt_path"} <= fit_parameters:
        _fail("TRAINER_FIT_SIGNATURE_INVALID")
    trainer = pl.Trainer(**trainer_kwargs)
    if (
        trainer.num_devices != 1
        or trainer.max_epochs != 5
        or trainer.max_steps != 5
        or trainer.limit_train_batches != 1
        or trainer.limit_val_batches != 0
        or trainer.limit_test_batches != 0
        or trainer.num_sanity_val_steps != 0
        or trainer.reload_dataloaders_every_n_epochs != 1
        or trainer.checkpoint_callback is not None
        or trainer.logger is not None
    ):
        _fail("EFFECTIVE_TRAINER_CONFIGURATION_INVALID")
    return CovapieBatch001BoundedTrainingRuntimeV1(
        model=model,
        datamodule=datamodule,
        trainer=trainer,
        checkpoint_metadata=checkpoint,
        migration_metadata=migration,
        trainer_kwargs=trainer_kwargs,
    )


def _invoke_fit_once_v1(runtime: CovapieBatch001BoundedTrainingRuntimeV1) -> None:
    if type(runtime) is not CovapieBatch001BoundedTrainingRuntimeV1:
        _fail("RUNTIME_TYPE_INVALID")
    if runtime.fit_call_count != 0:
        _fail("TRAINER_FIT_RETRY_FORBIDDEN")
    runtime.fit_call_count += 1
    runtime.trainer.fit(
        model=runtime.model,
        datamodule=runtime.datamodule,
        ckpt_path=None,
    )


def execute_covapie_batch001_bounded_training_session_v1(
    *,
    execution_authorized: object = False,
    runtime_root: object,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001BoundedTrainingRuntimeV1:
    """Run one bounded fit only after explicit, separately obtained authority."""

    if execution_authorized is not True:
        _fail("EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    prepared = prepare_covapie_batch001_bounded_training_session_v1(
        repository_root=repository_root,
        cache_root=cache_root,
    )
    runtime = build_covapie_batch001_bounded_training_runtime_v1(
        execution_authorized=True,
        prepared=prepared,
        runtime_root=runtime_root,
        repository_root=repository_root,
        state_root=state_root,
    )
    _invoke_fit_once_v1(runtime)
    return runtime


def serialize_covapie_batch001_bounded_training_session_summary_v1(
    summary: object,
) -> bytes:
    if type(summary) is not CovapieBatch001BoundedTrainingSessionSummaryV1:
        _fail("SESSION_SUMMARY_TYPE_INVALID")
    return (
        json.dumps(
            asdict(summary),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Prepare-only module entry point; no execute option is exposed."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--cache-root", type=Path)
    arguments = parser.parse_args(argv)
    prepared = prepare_covapie_batch001_bounded_training_session_v1(
        repository_root=arguments.repository_root,
        cache_root=arguments.cache_root,
    )
    print(
        serialize_covapie_batch001_bounded_training_session_summary_v1(
            prepared.summary
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

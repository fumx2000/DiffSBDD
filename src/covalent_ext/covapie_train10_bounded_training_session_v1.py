"""Default-off train10 five-epoch session assembly; prepare is data-only.

The build and execute interfaces require separate, new user authority before
their execution_authorized=True branch is used. Import and prepare do not
inspect the checkpoint or create a training runtime, model, optimizer or Trainer.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
import hashlib
import inspect
import io
from pathlib import Path
import stat
from typing import Mapping, NoReturn

from covalent_ext.biopython_compat import patch_biopython_polypeptide_three_to_one

# Keep the published model-owner import order even in a fresh interpreter.
patch_biopython_polypeptide_three_to_one()

import pytorch_lightning as pl  # noqa: E402
import torch  # noqa: E402
from covalent_ext import (  # noqa: E402
    checkpoint_compatible_model_instantiation as config_owner,
    covapie_batch001_bounded_training_session_v1 as bounded_owner,
    covapie_current11_checkpoint_migration_v1 as migration_owner,
    covapie_train10_cpu_batch_composer_v1 as composer_owner,
    covapie_train10_epoch_datamodule_v1 as data_owner,
    covapie_train10_hidden_post_forward_adapter_v1 as forward_owner,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CANONICAL_TASKS_V1,
)
from covalent_ext.diffsbdd_model_instantiation import _constructor_kwargs  # noqa: E402


ERROR_V1 = "COVAPIE_TRAIN10_BOUNDED_TRAINING_SESSION_V1_ERROR"
TASK_ID_V1 = "implement_covapie_train10_bounded_training_session_v1"
EXACT_EPOCHS_V1 = (0, 1, 2, 3, 4)
TASK_SCHEDULE_SEED_V1 = 0
CHECKPOINT_RELATIVE_PATH_V1 = bounded_owner.CHECKPOINT_RELATIVE_PATH_V1
CHECKPOINT_SIZE_BYTES_V1 = 17_861_341  # expectation, NOT verified in prepare
CHECKPOINT_SHA256_V1 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
CANONICAL_MASK_CONTRACT_V1 = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
# Fixed published expectations, not computed from arbitrary live source bytes.
DIRECT_SOURCE_PINS_V1 = (
    ("src/covalent_ext/covapie_train10_epoch_datamodule_v1.py", "84ea24ddfaa442be6a2b3ef9e29363d6e62f2d1aa3d5b847d5f6247c01548eda"),
    ("src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py", "5beaa700e2e5af87265c022a919dddfe1c8054114a45415adc416e5fe25fa40d"),
    ("src/covalent_ext/covapie_batch001_bounded_training_session_v1.py", "f38c3f88822723e44fb55b31a60d0ec1a34236553c71b7e87ecdadd9f7ce3620"),
    *bounded_owner.DIRECT_BOUND_SOURCE_SHA256_V1[1:],
)
_PUBLISHED_REPOSITORY_ROOT_V1 = Path(data_owner.__file__).resolve(strict=True).parents[2]
_DATASET_NAME_V1 = "crossdock_checkpoint_10d_fullatom_shape_smoke"
_MODEL_INITIALIZATION_SEED_V1 = 20260821


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{ERROR_V1}:{reason}")


def _directory(value: object, expected: Path, reason: str) -> Path:
    if type(value) is not type(Path()) or not value.is_absolute():
        _fail(reason)
    try:
        if value.resolve(strict=True) != value or not value.is_dir() or value != expected:
            _fail(reason)
    except OSError as error:
        raise ValueError(f"{ERROR_V1}:{reason}") from error
    return value


def _roots(repository_root: object, state_root: object, cache_root: object) -> tuple[Path, Path, Path]:
    repository = _directory(repository_root, _PUBLISHED_REPOSITORY_ROOT_V1, "CANONICAL_REPOSITORY_ROOT_REQUIRED")
    state = _directory(state_root, repository.parent / "covapie-state", "CANONICAL_STATE_ROOT_REQUIRED")
    cache = _directory(cache_root, state / "bulk-multisource-cys-sg-v1/rcsb", "CANONICAL_CACHE_ROOT_REQUIRED")
    return repository, state, cache


def verify_covapie_train10_bounded_training_sources_v1(repository_root: Path) -> tuple[tuple[str, str], ...]:
    """Pin direct owners; their published validators bind the predecessor chain."""
    _directory(repository_root, _PUBLISHED_REPOSITORY_ROOT_V1, "CANONICAL_REPOSITORY_ROOT_REQUIRED")
    observed = []
    for relative, expected in DIRECT_SOURCE_PINS_V1:
        path = repository_root / relative
        try:
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
                _fail("DIRECT_SOURCE_NOT_REGULAR:" + relative)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(f"{ERROR_V1}:DIRECT_SOURCE_UNREADABLE:{relative}") from error
        if digest != expected:
            _fail("DIRECT_SOURCE_PIN_DRIFT:" + relative)
        observed.append((relative, digest))
    if (
        type(bounded_owner.CHECKPOINT_RELATIVE_PATH_V1) is not type(Path())
        or CHECKPOINT_RELATIVE_PATH_V1 != config_owner.CHECKPOINT_PATH
        or CHECKPOINT_SIZE_BYTES_V1 != migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
        or CHECKPOINT_SHA256_V1 != migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
        or bounded_owner.DEFAULT_LOSS_WEIGHTS_V1.pre_post_geometry != 0.0
        or bounded_owner.DEFAULT_LOSS_WEIGHTS_V1 != bounded_owner.DEFAULT_LOSS_WEIGHTS_V1.__class__()
    ):
        _fail("PUBLISHED_CHECKPOINT_OR_LOSS_EXPECTATION_DRIFT")
    try:
        forward_owner.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(repository_root=repository_root)
    except ValueError as error:
        raise ValueError(f"{ERROR_V1}:PUBLISHED_FORWARD_SOURCE_CHAIN_REJECTED") from error
    return tuple(observed)


class CovapieTrain10BoundedTrainingLigandPocketDDPMV1(
    forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
):
    """Only the necessary fit lifecycle changes; forward/loss/optimizer remain owned."""

    validation_epoch_end = None  # Lightning 2 compatibility, not validation opt-in.

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("MODEL_SETUP_FIT_ONLY")
        datamodule = getattr(getattr(self, "_trainer", None), "datamodule", None)
        if type(datamodule) is not data_owner.CovapieTrain10EpochDataModuleV1:
            _fail("PUBLISHED_TRAIN10_DATAMODULE_REQUIRED")
        if any(getattr(self, name, None) is not None for name in ("train_dataset", "val_dataset", "test_dataset")):
            _fail("LEGACY_MODEL_DATASET_PRESENT")

    def configure_gradient_clipping(
        self, optimizer: torch.optim.Optimizer,
        gradient_clip_val: float | int | None = None,
        gradient_clip_algorithm: str | None = None,
    ) -> None:
        del optimizer
        if gradient_clip_val is not None or gradient_clip_algorithm is not None:
            _fail("GRADIENT_CLIPPING_DISABLED")


def _model_route() -> None:
    owner = CovapieTrain10BoundedTrainingLigandPocketDDPMV1
    if (
        owner.__mro__[1] is not forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
        or owner.forward is not forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward
        or owner.training_step is not CovapieCurrent11TrainingLigandPocketDDPM.training_step
        or owner.configure_optimizers is not CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
        or "__init__" in owner.__dict__
        or any(isinstance(value, (torch.nn.Parameter, torch.nn.Module)) for value in owner.__dict__.values())
    ):
        _fail("PUBLISHED_MODEL_ROUTE_DRIFT")


def _trainer_kwargs(root: Path) -> dict[str, object]:
    if set(inspect.signature(bounded_owner.build_covapie_batch001_bounded_trainer_kwargs_v1).parameters) != {
        "default_root_dir", "overrides", "trainer_signature"
    }:
        _fail("PUBLISHED_PURE_TRAINER_HELPER_SIGNATURE_DRIFT")
    try:
        kwargs = bounded_owner.build_covapie_batch001_bounded_trainer_kwargs_v1(default_root_dir=root)
    except ValueError as error:
        raise ValueError(f"{ERROR_V1}:PUBLISHED_TRAINER_POLICY_REJECTED") from error
    if kwargs.get("default_root_dir") != str(root) or kwargs.get("max_steps") != 5:
        _fail("EXACT_TRAINER_POLICY_DRIFT")
    return kwargs


@dataclass(frozen=True)
class CovapieTrain10BoundedTrainingPlanV1:
    source_bindings: tuple[tuple[str, str], ...]
    checkpoint_relative_path_expected: str
    checkpoint_size_bytes_expected: int
    checkpoint_sha256_expected: str
    checkpoint_identity_verified_this_prepare: bool
    epochs: tuple[int, ...]
    seed: int
    canonical_masks: tuple[tuple[int, str, str], ...]
    event_count: int
    leakage_group_count: int
    event_epoch_rows: int
    exact5_task_counts: tuple[int, ...]
    carrier_seals: tuple[str, ...]
    trainer_configuration: tuple[tuple[str, object], ...]
    build_status: str = "NOT_RUN"
    execute_status: str = "NOT_RUN"
    trainer_runtime_validated: bool = False
    ready_for_training: bool = False
    feature_semantics_audit_required_later: bool = True
    step12d_is_only_smoke_legality_check: bool = True


@dataclass(frozen=True)
class CovapieTrain10PreparedBoundedTrainingSessionV1:
    repository_root: Path
    state_root: Path
    cache_root: Path
    datamodule: data_owner.CovapieTrain10EpochDataModuleV1
    carriers: tuple[composer_owner.CovapieTrain10CpuEpochBatchV1, ...]
    plan: CovapieTrain10BoundedTrainingPlanV1


@dataclass
class CovapieTrain10BoundedTrainingRuntimeV1:
    prepared: CovapieTrain10PreparedBoundedTrainingSessionV1
    model: pl.LightningModule
    datamodule: data_owner.CovapieTrain10EpochDataModuleV1
    trainer: pl.Trainer
    runtime_root: Path
    checkpoint_metadata: Mapping[str, object]
    migration_metadata: Mapping[str, object]
    trainer_kwargs: Mapping[str, object]
    fit_request_count: int = 0
    trainer_runtime_validated: bool = False


def _audit_prepared(prepared: object) -> CovapieTrain10PreparedBoundedTrainingSessionV1:
    if type(prepared) is not CovapieTrain10PreparedBoundedTrainingSessionV1:
        _fail("PREPARED_TYPE_REQUIRED")
    module = prepared.datamodule
    if (
        type(module) is not data_owner.CovapieTrain10EpochDataModuleV1
        or prepared.carriers is not module.carriers
        or type(prepared.carriers) is not tuple
        or len(prepared.carriers) != 5
        or type(module.prepared) is not composer_owner.CovapieTrain10CpuBatchPreparedV1
        or (module.prepared.repository_root, module.prepared.state_root, module.prepared.cache_root)
        != (prepared.repository_root, prepared.state_root, prepared.cache_root)
    ):
        _fail("PUBLISHED_DATAMODULE_OR_CARRIER_IDENTITY_REQUIRED")
    _roots(prepared.repository_root, prepared.state_root, prepared.cache_root)
    for epoch, carrier in enumerate(prepared.carriers):
        if module.carriers[epoch] is not carrier:
            _fail("CURRENT_CARRIER_IDENTITY_REQUIRED")
        data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(
            carrier, current_epoch=epoch, task_schedule_seed=0
        )
        if (
            carrier.training_session_active is not False
            or carrier.trainer_integrated is not False
            or carrier.legacy_post_overlay_applied is not False
        ):
            _fail("PUBLISHED_CARRIER_UNMODIFIED_REQUIRED")
    return prepared


def prepare_covapie_train10_bounded_training_session_v1(
    *, repository_root: Path, state_root: Path, cache_root: Path
) -> CovapieTrain10PreparedBoundedTrainingSessionV1:
    """One published real CPU prepare and five carrier builds, zero training."""
    repository, state, cache = _roots(repository_root, state_root, cache_root)
    sources = verify_covapie_train10_bounded_training_sources_v1(repository)
    _model_route()
    if tuple(row[:3] for row in CANONICAL_TASKS_V1) != CANONICAL_MASK_CONTRACT_V1:
        _fail("CANONICAL_EXACT5_B3_DRIFT")
    # Existing external state directory is solely a pure plan-validation input.
    # It is NOT a newly created training runtime; build must rebind its own root.
    trainer_kwargs = _trainer_kwargs(state)
    module = data_owner.prepare_covapie_train10_epoch_datamodule_v1(
        repository_root=repository, state_root=state, cache_root=cache
    )
    carriers = module.carriers
    if (
        len(module.prepared.sample_identities) != 10
        or len(module.prepared.canonical_event_ids) != 10
        or module.prepared.formal_splits != ("train",) * 10
        or module.prepared.verified_distinct_leakage_group_count != 3
    ):
        _fail("EXACT_TRAIN10_FORMAL_POPULATION_REQUIRED")
    counts = [0] * 5
    for epoch, carrier in enumerate(carriers):
        data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(carrier, current_epoch=epoch)
        if (
            carrier.sample_identities != module.prepared.sample_identities
            or carrier.canonical_event_ids != module.prepared.canonical_event_ids
            or carrier.leakage_group_ids != module.prepared.leakage_group_ids
            or carrier.formal_splits != module.prepared.formal_splits
            or carrier.batch_positions != tuple(range(10))
            or carrier.scheduled_task_ids != tuple(carrier.supervision.canonical_task_id.tolist())
        ):
            _fail("EPOCH_MEMBERSHIP_OR_SUPERVISION_DRIFT")
        for task in carrier.scheduled_task_ids:
            if type(task) is not int or task not in range(5):
                _fail("NONCANONICAL_TASK_ID")
            counts[task] += 1
    if tuple(counts) != (10,) * 5:
        _fail("EXACT5_PER_TASK_TEN_ROWS_REQUIRED")
    configuration = tuple(
        (name, () if name == "callbacks" else value)
        for name, value in sorted(trainer_kwargs.items())
        if name != "default_root_dir"
    )
    plan = CovapieTrain10BoundedTrainingPlanV1(
        source_bindings=sources,
        checkpoint_relative_path_expected=CHECKPOINT_RELATIVE_PATH_V1.as_posix(),
        checkpoint_size_bytes_expected=CHECKPOINT_SIZE_BYTES_V1,
        checkpoint_sha256_expected=CHECKPOINT_SHA256_V1,
        checkpoint_identity_verified_this_prepare=False,
        epochs=EXACT_EPOCHS_V1, seed=0, canonical_masks=CANONICAL_MASK_CONTRACT_V1,
        event_count=10, leakage_group_count=3, event_epoch_rows=50,
        exact5_task_counts=tuple(counts),
        carrier_seals=tuple(carrier.payload_sha256 for carrier in carriers),
        trainer_configuration=configuration,
    )
    result = CovapieTrain10PreparedBoundedTrainingSessionV1(
        repository_root=repository, state_root=state, cache_root=cache,
        datamodule=module, carriers=carriers, plan=plan,
    )
    _audit_prepared(result)
    return result


def _runtime_directory(value: object, prepared: CovapieTrain10PreparedBoundedTrainingSessionV1) -> Path:
    if type(value) is not type(Path()) or not value.is_absolute():
        _fail("EXPLICIT_RUNTIME_ROOT_REQUIRED")
    try:
        if value.resolve(strict=True) != value or not value.is_dir() or any(value.iterdir()):
            _fail("NEW_EMPTY_RUNTIME_ROOT_REQUIRED")
    except OSError as error:
        raise ValueError(f"{ERROR_V1}:NEW_EMPTY_RUNTIME_ROOT_REQUIRED") from error
    if value == prepared.state_root or value == prepared.cache_root or value.is_relative_to(prepared.repository_root):
        _fail("EXTERNAL_RUNTIME_ROOT_REQUIRED")
    return value


def _instantiate_train10_model(
    *, checkpoint: Mapping[str, object], prepared: CovapieTrain10PreparedBoundedTrainingSessionV1,
    runtime_root: Path,
) -> CovapieTrain10BoundedTrainingLigandPocketDDPMV1:
    legacy = checkpoint.get("legacy_constructor")
    if type(legacy) is not dict:
        _fail("VALIDATED_LEGACY_CONSTRUCTOR_REQUIRED")
    preview = config_owner.load_config_preview_v0(prepared.repository_root / config_owner.CONFIG_PREVIEW_PATH)
    if preview.get("config_preview_loaded") is not True:
        _fail("PUBLISHED_CONFIG_PREVIEW_REJECTED")
    compatible = config_owner.build_checkpoint_compatible_config_v0(
        preview["preview"], prepared.repository_root / config_owner.BEST_CONFIG_CANDIDATE_PATH
    )
    if compatible.get("compatible_config_built") is not True:
        _fail("PUBLISHED_COMPATIBLE_CONFIG_REJECTED")
    config = config_owner._constructor_config_from_compatible_config(
        compatible, _DATASET_NAME_V1, "cpu", node_histogram=legacy["node_histogram"]
    )
    if (
        config["egnn_params"] != dict(legacy["egnn_params"], device="cpu")
        or config["diffusion_params"] != legacy["diffusion_params"]
        or config["eval_params"] != legacy["eval_params"]
        or config["loss_params"] != legacy["loss_params"]
        or config["node_histogram"] != legacy["node_histogram"]
        or type(config["lr"]) is not float or config["lr"] != 0.001
        or config["diffusion_params"].get("diffusion_steps") != 500
        or config["clip_grad"] is not False
        or config["mode"] != "pocket_conditioning"
        or config["pocket_representation"] != "full-atom"
        or config["virtual_nodes"] is not False
    ):
        _fail("CHECKPOINT_CONSTRUCTOR_CONFIG_DRIFT")
    legacy_setup = runtime_root / "legacy_setup_data"
    legacy_setup.mkdir(mode=0o700)
    config.update({"outdir": runtime_root / "model_output_disabled", "datadir": str(legacy_setup), "batch_size": 10})
    kwargs = _constructor_kwargs(config)
    kwargs.update({
        "target_residue_atom_conditioning": True,
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(prepared.repository_root),
        "covapie_state_root": str(prepared.state_root),
        "covapie_current11_training_enabled": True,
        "covapie_current11_task_schedule_seed": 0,
        "covapie_current11_pair_contrastive_temperature": 1.0,
        "covapie_current11_loss_weights": bounded_owner.DEFAULT_LOSS_WEIGHTS_V1,
        "covapie_train10_hidden_post_forward_enabled": True,
    })
    import constants  # noqa: PLC0415; future authorized branch only

    saved_rng = torch.random.get_rng_state()
    previous = constants.dataset_params.get(_DATASET_NAME_V1)
    try:
        torch.random.default_generator.manual_seed(_MODEL_INITIALIZATION_SEED_V1)
        constants.dataset_params[_DATASET_NAME_V1] = config_owner._temporary_10d_dataset_info()
        with contextlib.redirect_stdout(io.StringIO()):
            model = CovapieTrain10BoundedTrainingLigandPocketDDPMV1(**kwargs)
    finally:
        if previous is None:
            constants.dataset_params.pop(_DATASET_NAME_V1, None)
        else:
            constants.dataset_params[_DATASET_NAME_V1] = previous
        torch.random.set_rng_state(saved_rng)
    model = model.to(torch.device("cpu"))
    if (
        type(model) is not CovapieTrain10BoundedTrainingLigandPocketDDPMV1
        or len(model.state_dict()) != 141
        or model.device != torch.device("cpu")
        or model.batch_size != 10
        or model.automatic_optimization is not True
        or model.covapie_current11_loss_weights != bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
        or model.mode != "pocket_conditioning"
        or model.pocket_representation != "full-atom"
        or model.atom_nf != 10 or model.aa_nf != 10
        or model.virtual_nodes is not False
        or model.target_residue_atom_conditioning is not True
        or model.ddpm.loss_type != "l2"
    ):
        _fail("REAL_MODEL_CONFIGURATION_INVALID")
    return model


def build_covapie_train10_bounded_training_runtime_v1(
    *, prepared: object, runtime_root: object,
    repository_root: object = None, state_root: object = None, cache_root: object = None,
    execution_authorized: object = False,
) -> CovapieTrain10BoundedTrainingRuntimeV1:
    """Future-only: one checkpoint load, one model and one strict migration."""
    if execution_authorized is not True:
        _fail("NEW_EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    selected = _audit_prepared(prepared)
    if _roots(repository_root, state_root, cache_root) != (
        selected.repository_root, selected.state_root, selected.cache_root
    ):
        _fail("PREPARED_ROOT_CONTEXT_DRIFT")
    runtime = _runtime_directory(runtime_root, selected)
    verify_covapie_train10_bounded_training_sources_v1(selected.repository_root)
    _model_route()
    trainer_kwargs = _trainer_kwargs(runtime)
    if not {"model", "datamodule", "ckpt_path"} <= set(inspect.signature(pl.Trainer.fit).parameters):
        _fail("TRAINER_FIT_SIGNATURE_DRIFT")
    # This published loader validates content identity, then deserializes ONCE.
    checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=selected.repository_root / CHECKPOINT_RELATIVE_PATH_V1
    )
    model = _instantiate_train10_model(checkpoint=checkpoint, prepared=selected, runtime_root=runtime)
    migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model, checkpoint_state_dict=checkpoint["state_dict"]
    )
    if migration.get("full_target_strict_load") is not True:
        _fail("STRICT_MIGRATION_REQUIRED")
    trainer = pl.Trainer(**trainer_kwargs)
    if (
        trainer.num_devices != 1 or trainer.max_epochs != 5 or trainer.max_steps != 5
        or trainer.limit_train_batches != 1 or trainer.limit_val_batches != 0
        or trainer.limit_test_batches != 0 or trainer.num_sanity_val_steps != 0
        or trainer.reload_dataloaders_every_n_epochs != 1
        or trainer.checkpoint_callback is not None or trainer.logger is not None
    ):
        _fail("EFFECTIVE_TRAINER_CONFIGURATION_DRIFT")
    return CovapieTrain10BoundedTrainingRuntimeV1(
        prepared=selected, model=model, datamodule=selected.datamodule, trainer=trainer,
        runtime_root=runtime, checkpoint_metadata=checkpoint,
        migration_metadata=migration, trainer_kwargs=trainer_kwargs,
    )


def execute_covapie_train10_bounded_training_session_v1(
    *, runtime: object, execution_authorized: object = False
) -> CovapieTrain10BoundedTrainingRuntimeV1:
    """Consume an already-built runtime, never re-prepare or auto-resume."""
    if execution_authorized is not True:
        _fail("NEW_EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    if type(runtime) is not CovapieTrain10BoundedTrainingRuntimeV1:
        _fail("RUNTIME_TYPE_REQUIRED")
    if type(runtime.fit_request_count) is not int or runtime.fit_request_count != 0:
        _fail("SINGLE_FIT_REQUEST_ONLY")
    selected = _audit_prepared(runtime.prepared)
    if runtime.datamodule is not selected.datamodule or runtime.model is None or runtime.trainer is None:
        _fail("RUNTIME_OBJECT_IDENTITY_REQUIRED")
    bounded_owner._validate_trainer_kwargs(runtime.trainer_kwargs)
    if runtime.trainer_kwargs.get("default_root_dir") != str(runtime.runtime_root):
        _fail("RUNTIME_TRAINER_ROOT_DRIFT")
    verify_covapie_train10_bounded_training_sources_v1(selected.repository_root)
    runtime.fit_request_count = 1  # before the request: failure also forbids retry
    runtime.trainer.fit(model=runtime.model, datamodule=runtime.datamodule, ckpt_path=None)
    for carrier in selected.carriers:
        data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(
            carrier, current_epoch=carrier.epoch
        )
    # No claim of effective epoch-refresh or trainer runtime validation here.
    return runtime

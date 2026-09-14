"""Default-off Batch001 bounded-fit and validation4 lifecycle V1.

Preparation composes the published train5 session and current-state
validation4 adapter without constructing a model or Trainer.  The future
execution path is deliberately explicit and sequential: build one runtime,
evaluate its initial model, invoke the owner's bounded fit once, and evaluate
the same current model again.  No Lightning validation hook is installed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Callable, Mapping, NoReturn, Sequence

import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_bounded_training_session_v1 as bounded_owner,
)
from covalent_ext import (
    covapie_batch001_current_state_validation4_adapter_v1 as validation_owner,
)


__all__ = (
    "COVAPIE_BATCH001_TRAIN_VALIDATION_LIFECYCLE_ERROR_V1",
    "TASK_ID_V1",
    "EXPLICIT_LR_DIAGNOSTIC_OPTION_TASK_ID_V1",
    "LEGACY_CONSTRUCTOR_LEARNING_RATE_V1",
    "CANDIDATE_LEARNING_RATE_V1",
    "ALLOWED_RUN_LEARNING_RATES_V1",
    "DIRECT_BOUND_SOURCE_SHA256_V1",
    "CANONICAL_MASK_CONTRACT_V1",
    "CovapieBatch001TrainValidationSourceBindingV1",
    "CovapieBatch001TrainValidationLifecyclePrepareSummaryV1",
    "CovapieBatch001PreparedTrainValidationLifecycleV1",
    "CovapieBatch001PairedEstimateDeltaV1",
    "CovapieBatch001PairedEventTaskDeltaV1",
    "CovapieBatch001PairedEventDeltaV1",
    "CovapieBatch001PairedMetricComparisonV1",
    "CovapieBatch001TrainValidationLifecycleRunV1",
    "CovapieBatch001TrainValidationLifecycleExecutionErrorV1",
    "verify_covapie_batch001_train_validation_lifecycle_sources_v1",
    "prepare_covapie_batch001_train_validation_lifecycle_v1",
    "create_covapie_batch001_train_validation_lifecycle_run_v1",
    "execute_covapie_batch001_train_validation_lifecycle_v1",
    "serialize_covapie_batch001_train_validation_lifecycle_prepare_v1",
    "main",
)


COVAPIE_BATCH001_TRAIN_VALIDATION_LIFECYCLE_ERROR_V1 = (
    "COVAPIE_BATCH001_TRAIN_VALIDATION_LIFECYCLE_V1_ERROR"
)
TASK_ID_V1 = "implement_covapie_batch001_train_validation_lifecycle_v1"
EXPLICIT_LR_DIAGNOSTIC_OPTION_TASK_ID_V1 = (
    "implement_covapie_batch001_explicit_lr_diagnostic_option_v1"
)
LEGACY_CONSTRUCTOR_LEARNING_RATE_V1 = 1.0e-3
CANDIDATE_LEARNING_RATE_V1 = 1.0e-4
ALLOWED_RUN_LEARNING_RATES_V1 = (
    LEGACY_CONSTRUCTOR_LEARNING_RATE_V1,
    CANDIDATE_LEARNING_RATE_V1,
)
PRE_FIT_MODEL_STAGE_V1 = "PRE_FIT_INITIAL_MODEL"
POST_FIT_MODEL_STAGE_V1 = "POST_FIT_CURRENT_MODEL"
LEARNING_RATE_APPLICATION_STAGE_V1 = "POST_RUNTIME_BUILD_PRE_A0"
NOT_OBSERVED_V1 = "NOT_OBSERVED"
CANONICAL_MASK_CONTRACT_V1 = bounded_owner.CANONICAL_MASK_CONTRACT_V1
DIRECT_BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_bounded_training_session_v1.py",
        "f38c3f88822723e44fb55b31a60d0ec1a34236553c71b7e87ecdadd9f7ce3620",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_current_state_validation4_adapter_v1.py",
        "5300e7599453b92684e3dd12f0ae728e0b37ce410f29b5c82eb969edbe943099",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())
_SNAPSHOT_PARITY_NAMES_V1 = (
    "parameters_unchanged",
    "buffers_unchanged",
    "gradients_unchanged",
    "requires_grad_unchanged",
    "parameter_identities_unchanged",
    "buffer_identities_unchanged",
    "module_identities_unchanged",
    "state_keys_unchanged",
    "configuration_unchanged",
    "node_distribution_unchanged",
    "training_flags_restored",
    "state_mapping_unchanged",
)
_PAIRED_ROW_METADATA_FIELDS_V1 = (
    "canonical_event_id",
    "pdb_id",
    "ligand_component_id",
    "formal_split",
    "leakage_group",
    "profile",
    "canonical_task_id",
    "canonical_task_name",
    "canonical_task_alias",
    "root_validation_seed",
    "main_timestep_int",
    "generated_atom_count",
    "fixed_atom_count",
    "coordinate_dimension",
    "PRE_geometry_valid",
    "target_cys_sg_indicator_count",
    "pair_candidate_count",
    "fixed_ligand_clean_main",
    "fixed_ligand_clean_t0",
)


@dataclass(frozen=True)
class CovapieBatch001TrainValidationSourceBindingV1:
    relative_path: str
    expected_sha256: str
    observed_sha256: str
    sha256_verified: bool


@dataclass(frozen=True)
class CovapieBatch001TrainValidationLifecyclePrepareSummaryV1:
    schema_version: str
    task_id: str
    implementation_status: str
    learning_rate_diagnostic_option_task_id: str
    legacy_constructor_learning_rate: float
    requested_run_learning_rate: float
    requested_run_learning_rate_differs_from_legacy_reference: bool
    model_learning_rate_before_application: str
    model_learning_rate_after_application: str
    constructor_hparams_learning_rate_after_application: str
    learning_rate_application_stage: str
    actual_optimizer_param_group_learning_rates: str
    source_bindings: tuple[CovapieBatch001TrainValidationSourceBindingV1, ...]
    bounded_training_owner_task_id: str
    validation4_owner_task_id: str
    canonical_mask_semantic_names: tuple[str, ...]
    canonical_mask_display_aliases: tuple[str, ...]
    training_epochs: tuple[int, ...]
    training_task_schedule_seed: int
    training_carrier_fingerprints: tuple[str, ...]
    training_scheduled_task_ids: tuple[tuple[int, ...], ...]
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_test_event_ids: tuple[str, ...]
    validation_root_seeds: tuple[int, ...]
    validation_context_seed: int
    validation_profile_task_matrix: tuple[tuple[str, tuple[int, ...]], ...]
    primary_metric_name: str
    checkpoint_relative_path: str
    checkpoint_size_bytes: int
    checkpoint_sha256: str
    checkpoint_identity_verified: bool
    exact_train_validation_test_identity_verified: bool
    event_identity_intersections_zero: bool
    leakage_group_cross_split_violation_count: int
    validation_training_admission_closed: bool
    validation_training_loss_masks_closed: bool
    validation_labels_retained_for_evaluation: bool
    test_model_input_constructed: bool
    planned_checkpoint_load_count: int
    planned_model_construction_count: int
    planned_trainer_construction_count: int
    planned_optimizer_construction_count: int
    planned_fit_call_count: int
    planned_training_forward_count: int
    planned_max_optimizer_step_count: int
    planned_validation4_call_count: int
    planned_validation_event_count_per_call: int
    planned_validation_event_task_count_per_call: int
    planned_validation_estimate_count_per_call: int
    planned_validation_task_seed_slice_count_per_call: int
    planned_validation_main_dynamics_count_per_call: int
    planned_validation_t0_dynamics_count_per_call: int
    planned_validation_estimate_count_total: int
    planned_validation_dynamics_count_total: int
    actual_checkpoint_load_count: int
    actual_model_construction_count: int
    actual_trainer_construction_count: int
    actual_optimizer_construction_count: int
    actual_fit_call_count: int
    actual_validation4_call_count: int
    actual_validation_dynamics_count: int
    actual_backward_count: int
    actual_optimizer_step_count: int
    parameter_update_performed: bool
    default_prepare_only: bool
    execution_opt_in_required: bool
    same_model_required_for_all_stages: bool
    validation_runs_outside_fit: bool
    lightning_in_fit_validation_hook_integrated: bool
    train_validation_lifecycle_runtime_validated: bool
    formal_scientific_training_started: bool
    ready_for_training: bool
    geometry_training_gradient_accepted: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool


@dataclass(frozen=True)
class CovapieBatch001PreparedTrainValidationLifecycleV1:
    training: bounded_owner.CovapieBatch001PreparedBoundedTrainingSessionV1
    validation: validation_owner.CovapieBatch001PreparedCurrentStateValidation4V1
    summary: CovapieBatch001TrainValidationLifecyclePrepareSummaryV1


@dataclass(frozen=True)
class CovapieBatch001PairedEstimateDeltaV1:
    canonical_event_id: str
    canonical_task_id: int
    root_validation_seed: int
    masked_conditional_vlb_nll_post_minus_pre: float
    pair_BCE_post_minus_pre: float
    POST_geometry_loss_post_minus_pre: float
    pair_contrastive_loss_post_minus_pre: float


@dataclass(frozen=True)
class CovapieBatch001PairedEventTaskDeltaV1:
    canonical_event_id: str
    canonical_task_id: int
    seed_count: int
    masked_conditional_vlb_nll_pre: float
    masked_conditional_vlb_nll_post: float
    masked_conditional_vlb_nll_post_minus_pre: float
    pair_BCE_post_minus_pre: float
    POST_geometry_loss_post_minus_pre: float
    pair_contrastive_loss_post_minus_pre: float


@dataclass(frozen=True)
class CovapieBatch001PairedEventDeltaV1:
    canonical_event_id: str
    applicable_task_count: int
    masked_conditional_vlb_nll_pre: float
    masked_conditional_vlb_nll_post: float
    masked_conditional_vlb_nll_post_minus_pre: float


@dataclass(frozen=True)
class CovapieBatch001PairedMetricComparisonV1:
    comparison_direction: str
    primary_metric_name: str
    paired_estimate_count: int
    paired_event_task_count: int
    paired_event_count: int
    event_macro_pre: float
    event_macro_post: float
    event_macro_post_minus_pre: float
    micro_pre: float
    micro_post: float
    micro_post_minus_pre: float
    profile_balanced_pre: float
    profile_balanced_post: float
    profile_balanced_post_minus_pre: float
    mean_pair_BCE_post_minus_pre: float
    mean_POST_geometry_loss_post_minus_pre: float
    mean_pair_contrastive_loss_post_minus_pre: float
    mean_task4_historical_joint_nll_post_minus_pre: float
    per_estimate: tuple[CovapieBatch001PairedEstimateDeltaV1, ...]
    per_event_task: tuple[CovapieBatch001PairedEventTaskDeltaV1, ...]
    per_event: tuple[CovapieBatch001PairedEventDeltaV1, ...]


@dataclass(frozen=True)
class _OptimizerSnapshotV1:
    optimizer_identity: int
    parameter_identities: tuple[int, ...]
    state_sha256: str


@dataclass
class CovapieBatch001TrainValidationLifecycleRunV1:
    prepared: CovapieBatch001PreparedTrainValidationLifecycleV1
    legacy_constructor_learning_rate: float = LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
    requested_run_learning_rate: float = LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
    requested_run_learning_rate_differs_from_legacy_reference: bool = False
    model_learning_rate_before_application: float | str = NOT_OBSERVED_V1
    model_learning_rate_after_application: float | str = NOT_OBSERVED_V1
    constructor_hparams_learning_rate_after_application: float | str = (
        NOT_OBSERVED_V1
    )
    learning_rate_application_stage: str = "NOT_APPLIED"
    actual_optimizer_param_group_learning_rates: tuple[float, ...] | str = (
        NOT_OBSERVED_V1
    )
    phase: str = "READY_NOT_EXECUTED"
    terminal_status: str = "NOT_REACHED"
    stage_history: list[str] = field(default_factory=lambda: ["READY_NOT_EXECUTED"])
    execution_consumed: bool = False
    runtime_build_request_count: int = 0
    runtime_build_completion_count: int = 0
    validation_request_count: int = 0
    validation_completion_count: int = 0
    fit_request_count: int = 0
    fit_completion_count: int = 0
    runtime: object | None = None
    model: nn.Module | None = None
    model_object_identity: int | None = None
    parameter_object_identities: tuple[int, ...] | None = None
    optimizer_object_identity: int | None = None
    A0: object | None = None
    A1: object | None = None
    B0: object | None = None
    B1: object | None = None
    fit_failure_state: object | None = None
    pre_fit_validation_result: object | None = None
    post_fit_validation_result: object | None = None
    paired_comparison: CovapieBatch001PairedMetricComparisonV1 | None = None
    actual_global_step: int | None = None
    actual_final_epoch: int | None = None
    fit_returned: bool | None = None
    parameter_update_observed: bool | None = None
    pre_fit_state_isolation_pass: bool | None = None
    post_fit_state_isolation_pass: bool | None = None
    post_fit_optimizer_isolation_pass: bool | None = None
    pre_fit_public_API_rng_isolation_pass: bool | None = None
    post_fit_public_API_rng_isolation_pass: bool | None = None
    same_model_and_parameter_objects_pass: bool | None = None
    source_and_carrier_identity_final_pass: bool | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None
    failure_cause_type: str | None = None


class CovapieBatch001TrainValidationLifecycleExecutionErrorV1(ValueError):
    """Terminal lifecycle failure retaining the consumed in-memory run."""

    def __init__(
        self,
        reason: str,
        *,
        run: CovapieBatch001TrainValidationLifecycleRunV1 | None = None,
    ) -> None:
        self.reason = reason
        self.run = run
        super().__init__(
            f"{COVAPIE_BATCH001_TRAIN_VALIDATION_LIFECYCLE_ERROR_V1}:{reason}"
        )


def _fail(
    reason: str,
    *,
    run: CovapieBatch001TrainValidationLifecycleRunV1 | None = None,
) -> NoReturn:
    raise CovapieBatch001TrainValidationLifecycleExecutionErrorV1(
        reason, run=run
    )


def _validate_requested_run_learning_rate_v1(value: object) -> float:
    if (
        type(value) is not float
        or not math.isfinite(value)
        or value not in ALLOWED_RUN_LEARNING_RATES_V1
    ):
        _fail("RUN_LEARNING_RATE_NOT_EXPLICITLY_ALLOWED")
    return value


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CovapieBatch001TrainValidationLifecycleExecutionErrorV1(
            reason
        ) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_SOURCE_NOT_SAFE_REGULAR_FILE")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise CovapieBatch001TrainValidationLifecycleExecutionErrorV1(
            "BOUND_SOURCE_READ_FAILED"
        ) from error


def verify_covapie_batch001_train_validation_lifecycle_sources_v1(
    *, repository_root: object = None
) -> tuple[CovapieBatch001TrainValidationSourceBindingV1, ...]:
    """Bind the two direct owners and reuse each owner's transitive gate."""

    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    bindings = []
    for relative, expected in DIRECT_BOUND_SOURCE_SHA256_V1:
        actual = _sha256_file(repository / relative)
        if actual != expected:
            _fail("DIRECT_BOUND_SOURCE_SHA256_MISMATCH:" + relative)
        bindings.append(CovapieBatch001TrainValidationSourceBindingV1(
            relative_path=relative,
            expected_sha256=expected,
            observed_sha256=actual,
            sha256_verified=True,
        ))
    try:
        bounded_owner.verify_covapie_batch001_bounded_training_session_sources_v1(
            repository_root=repository
        )
        validation_owner.verify_covapie_batch001_current_state_validation4_sources_v1(
            repository_root=repository
        )
    except ValueError as error:
        raise CovapieBatch001TrainValidationLifecycleExecutionErrorV1(
            "OWNER_TRANSITIVE_SOURCE_BINDING_REJECTED"
        ) from error
    return tuple(bindings)


def _validate_prepared_components_v1(
    *,
    training: object,
    validation: object,
) -> None:
    if (
        type(training)
        is not bounded_owner.CovapieBatch001PreparedBoundedTrainingSessionV1
        or type(validation)
        is not validation_owner.CovapieBatch001PreparedCurrentStateValidation4V1
    ):
        _fail("PREPARED_OWNER_COMPONENT_TYPE_INVALID")
    train_summary = training.summary
    validation_summary = validation.summary
    train_authority = training.authority
    validation_authority = validation.authority
    expected_masks = (
        (0, "warhead_only", "A"),
        (1, "linker_plus_warhead", "B"),
        (2, "scaffold_plus_warhead", "B2"),
        (3, "scaffold_only", "B3"),
        (4, "scaffold_plus_linker_plus_warhead", "C"),
    )
    if (
        CANONICAL_MASK_CONTRACT_V1 != expected_masks
        or validation_owner.CANONICAL_MASK_CONTRACT_V1 != expected_masks
        or tuple(train_summary.canonical_mask_semantic_names)
        != tuple(row[1] for row in expected_masks)
        or tuple(train_summary.canonical_mask_display_aliases)
        != tuple(row[2] for row in expected_masks)
    ):
        _fail("CANONICAL_EXACT5_MASK_CONTRACT_DRIFT")
    if (
        train_summary.epochs != bounded_owner.EXACT_EPOCHS_V1
        or train_summary.task_schedule_seed
        != bounded_owner.TASK_SCHEDULE_SEED_V1
        or len(training.carriers) != 5
        or tuple(carrier.epoch for carrier in training.carriers)
        != bounded_owner.EXACT_EPOCHS_V1
        or any(carrier.formal_split != "train" for carrier in training.carriers)
        or any(
            carrier.sample_identities != train_authority.train_event_ids
            for carrier in training.carriers
        )
    ):
        _fail("TRAIN5_IDENTITY_OR_SCHEDULE_INVALID")
    if (
        train_authority.train_event_ids != validation_authority.train_event_ids
        or train_authority.validation_event_ids
        != validation_authority.validation_event_ids
        or train_authority.test_event_ids != validation_authority.test_event_ids
        or validation_summary.formal_train_event_ids
        != train_authority.train_event_ids
        or validation_summary.formal_validation_event_ids
        != train_authority.validation_event_ids
        or validation_summary.formal_test_event_ids
        != train_authority.test_event_ids
        or validation.validation_carrier.sample_identities
        != train_authority.validation_event_ids
        or validation.validation_carrier.formal_split != "validation"
    ):
        _fail("TRAIN_VALIDATION_TEST_IDENTITY_MISMATCH")
    train_ids = set(train_authority.train_event_ids)
    validation_ids = set(train_authority.validation_event_ids)
    test_ids = set(train_authority.test_event_ids)
    if (
        train_ids & validation_ids
        or train_ids & test_ids
        or validation_ids & test_ids
        or train_authority.event_identity_intersection_counts
        != (("train_validation", 0), ("train_test", 0), ("validation_test", 0))
        or validation_authority.event_identity_intersection_counts
        != train_authority.event_identity_intersection_counts
        or train_authority.formal_leakage_group_cross_split_violation_count != 0
        or validation_authority.formal_leakage_group_cross_split_violation_count
        != 0
    ):
        _fail("TRAIN_VALIDATION_TEST_LEAKAGE_BOUNDARY_INVALID")
    trainer_configuration = dict(train_summary.trainer_configuration)
    if (
        trainer_configuration.get("limit_val_batches") != 0
        or trainer_configuration.get("limit_test_batches") != 0
        or trainer_configuration.get("num_sanity_val_steps") != 0
        or train_summary.validation_enabled
        or train_summary.formal_validation_runtime_integrated
        or train_summary.test_evaluation_enabled
    ):
        _fail("BOUNDED_TRAINER_HELD_OUT_HOOK_MUST_REMAIN_DISABLED")
    if (
        not validation_summary.exact_validation4_identity_verified
        or not validation_summary.train_validation_test_event_intersections_zero
        or validation_summary.formal_leakage_group_cross_split_violation_count
        != 0
        or not validation_summary.validation_training_admission_closed
        or not validation_summary.validation_training_loss_masks_closed
        or not validation_summary.labels_retained_for_evaluation
        or validation_summary.test_model_input_constructed
        or validation_summary.primary_metric_name
        != validation_owner.PRIMARY_METRIC_NAME_V1
        or validation_summary.planned_event_count != 4
        or validation_summary.planned_event_task_combination_count != 16
        or validation_summary.planned_event_task_seed_estimate_count != 64
        or validation_summary.planned_task_seed_slice_count != 20
        or validation_summary.planned_main_dynamics_call_count != 20
        or validation_summary.planned_t0_dynamics_call_count != 20
    ):
        _fail("VALIDATION4_PREPARED_CONTRACT_INVALID")


def prepare_covapie_batch001_train_validation_lifecycle_v1(
    *,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
    learning_rate: object = LEGACY_CONSTRUCTOR_LEARNING_RATE_V1,
) -> CovapieBatch001PreparedTrainValidationLifecycleV1:
    """Prepare real train5/validation4 carriers with zero model execution."""

    requested_run_learning_rate = _validate_requested_run_learning_rate_v1(
        learning_rate
    )
    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    # Validate for path identity only.  Preparation never reads runtime state.
    _require_directory(
        state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID"
    )
    cache = _require_directory(
        cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
    )
    bindings = verify_covapie_batch001_train_validation_lifecycle_sources_v1(
        repository_root=repository
    )
    training = bounded_owner.prepare_covapie_batch001_bounded_training_session_v1(
        repository_root=repository,
        cache_root=cache,
    )
    validation = (
        validation_owner.prepare_covapie_batch001_current_state_validation4_v1(
            repository_root=repository,
            cache_root=cache,
        )
    )
    _validate_prepared_components_v1(training=training, validation=validation)
    train_summary = training.summary
    validation_summary = validation.summary
    summary = CovapieBatch001TrainValidationLifecyclePrepareSummaryV1(
        schema_version="covapie_batch001_train_validation_lifecycle_v1",
        task_id=TASK_ID_V1,
        implementation_status="PREPARED_NOT_EXECUTED",
        learning_rate_diagnostic_option_task_id=(
            EXPLICIT_LR_DIAGNOSTIC_OPTION_TASK_ID_V1
        ),
        legacy_constructor_learning_rate=(
            LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        ),
        requested_run_learning_rate=requested_run_learning_rate,
        requested_run_learning_rate_differs_from_legacy_reference=(
            requested_run_learning_rate
            != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        ),
        model_learning_rate_before_application=NOT_OBSERVED_V1,
        model_learning_rate_after_application=NOT_OBSERVED_V1,
        constructor_hparams_learning_rate_after_application=NOT_OBSERVED_V1,
        learning_rate_application_stage="NOT_APPLIED_PREPARE_ONLY",
        actual_optimizer_param_group_learning_rates=NOT_OBSERVED_V1,
        source_bindings=bindings,
        bounded_training_owner_task_id=bounded_owner.TASK_ID_V1,
        validation4_owner_task_id=validation_owner.TASK_ID_V1,
        canonical_mask_semantic_names=tuple(
            row[1] for row in CANONICAL_MASK_CONTRACT_V1
        ),
        canonical_mask_display_aliases=tuple(
            row[2] for row in CANONICAL_MASK_CONTRACT_V1
        ),
        training_epochs=train_summary.epochs,
        training_task_schedule_seed=train_summary.task_schedule_seed,
        training_carrier_fingerprints=tuple(
            row.carrier_fingerprint for row in train_summary.epoch_summaries
        ),
        training_scheduled_task_ids=tuple(
            row.scheduled_task_ids for row in train_summary.epoch_summaries
        ),
        formal_train_event_ids=training.authority.train_event_ids,
        formal_validation_event_ids=training.authority.validation_event_ids,
        formal_test_event_ids=training.authority.test_event_ids,
        validation_root_seeds=validation_summary.root_validation_seeds,
        validation_context_seed=validation_owner.VALIDATION_CONTEXT_SEED_V1,
        validation_profile_task_matrix=validation_summary.profile_task_matrix,
        primary_metric_name=validation_summary.primary_metric_name,
        checkpoint_relative_path=train_summary.checkpoint_relative_path,
        checkpoint_size_bytes=train_summary.checkpoint_size_bytes,
        checkpoint_sha256=train_summary.checkpoint_sha256,
        checkpoint_identity_verified=True,
        exact_train_validation_test_identity_verified=True,
        event_identity_intersections_zero=True,
        leakage_group_cross_split_violation_count=0,
        validation_training_admission_closed=True,
        validation_training_loss_masks_closed=True,
        validation_labels_retained_for_evaluation=True,
        test_model_input_constructed=False,
        planned_checkpoint_load_count=1,
        planned_model_construction_count=1,
        planned_trainer_construction_count=1,
        planned_optimizer_construction_count=1,
        planned_fit_call_count=1,
        planned_training_forward_count=5,
        planned_max_optimizer_step_count=5,
        planned_validation4_call_count=2,
        planned_validation_event_count_per_call=4,
        planned_validation_event_task_count_per_call=16,
        planned_validation_estimate_count_per_call=64,
        planned_validation_task_seed_slice_count_per_call=20,
        planned_validation_main_dynamics_count_per_call=20,
        planned_validation_t0_dynamics_count_per_call=20,
        planned_validation_estimate_count_total=128,
        planned_validation_dynamics_count_total=80,
        actual_checkpoint_load_count=0,
        actual_model_construction_count=0,
        actual_trainer_construction_count=0,
        actual_optimizer_construction_count=0,
        actual_fit_call_count=0,
        actual_validation4_call_count=0,
        actual_validation_dynamics_count=0,
        actual_backward_count=0,
        actual_optimizer_step_count=0,
        parameter_update_performed=False,
        default_prepare_only=True,
        execution_opt_in_required=True,
        same_model_required_for_all_stages=True,
        validation_runs_outside_fit=True,
        lightning_in_fit_validation_hook_integrated=False,
        train_validation_lifecycle_runtime_validated=False,
        formal_scientific_training_started=False,
        ready_for_training=False,
        geometry_training_gradient_accepted=False,
        feature_semantics_audit_required_later=True,
        step12d_is_only_smoke_legality_check=True,
    )
    return CovapieBatch001PreparedTrainValidationLifecycleV1(
        training=training,
        validation=validation,
        summary=summary,
    )


def _validate_prepared_lifecycle_v1(prepared: object) -> float:
    if type(prepared) is not CovapieBatch001PreparedTrainValidationLifecycleV1:
        _fail("PREPARED_LIFECYCLE_TYPE_INVALID")
    _validate_prepared_components_v1(
        training=prepared.training, validation=prepared.validation
    )
    summary = prepared.summary
    if type(summary) is not CovapieBatch001TrainValidationLifecyclePrepareSummaryV1:
        _fail("PREPARED_LIFECYCLE_SUMMARY_TYPE_INVALID")
    requested = _validate_requested_run_learning_rate_v1(
        summary.requested_run_learning_rate
    )
    if (
        summary.learning_rate_diagnostic_option_task_id
        != EXPLICIT_LR_DIAGNOSTIC_OPTION_TASK_ID_V1
        or summary.legacy_constructor_learning_rate
        != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        or summary.requested_run_learning_rate_differs_from_legacy_reference
        is not (requested != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1)
        or summary.model_learning_rate_before_application != NOT_OBSERVED_V1
        or summary.model_learning_rate_after_application != NOT_OBSERVED_V1
        or summary.constructor_hparams_learning_rate_after_application
        != NOT_OBSERVED_V1
        or summary.learning_rate_application_stage
        != "NOT_APPLIED_PREPARE_ONLY"
        or summary.actual_optimizer_param_group_learning_rates
        != NOT_OBSERVED_V1
        or summary.actual_checkpoint_load_count != 0
        or summary.actual_model_construction_count != 0
        or summary.actual_trainer_construction_count != 0
        or summary.actual_optimizer_construction_count != 0
        or summary.actual_fit_call_count != 0
        or summary.actual_validation4_call_count != 0
        or summary.actual_backward_count != 0
        or summary.actual_optimizer_step_count != 0
        or summary.parameter_update_performed
    ):
        _fail("PREPARED_LEARNING_RATE_DIAGNOSTIC_CONTRACT_INVALID")
    return requested


def create_covapie_batch001_train_validation_lifecycle_run_v1(
    *, prepared: object
) -> CovapieBatch001TrainValidationLifecycleRunV1:
    requested_run_learning_rate = _validate_prepared_lifecycle_v1(prepared)
    return CovapieBatch001TrainValidationLifecycleRunV1(
        prepared=prepared,
        requested_run_learning_rate=requested_run_learning_rate,
        requested_run_learning_rate_differs_from_legacy_reference=(
            requested_run_learning_rate
            != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        ),
    )


def _set_phase_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1, phase: str
) -> None:
    run.phase = phase
    run.stage_history.append(phase)


def _mark_terminal_failure_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    *,
    stage: str,
    reason: str,
    cause: BaseException,
) -> NoReturn:
    run.failure_stage = stage
    run.failure_reason = reason
    run.failure_cause_type = type(cause).__module__ + "." + type(cause).__qualname__
    run.terminal_status = "FAILED"
    _set_phase_v1(run, "FAILED")
    raise CovapieBatch001TrainValidationLifecycleExecutionErrorV1(
        reason, run=run
    ) from cause


def _request_operation_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1, operation: str
) -> None:
    if operation == "BUILD":
        if run.runtime_build_request_count != 0:
            _fail("SECOND_RUNTIME_BUILD_REQUEST_FORBIDDEN", run=run)
        run.runtime_build_request_count += 1
        return
    if operation == "FIT":
        if run.fit_request_count != 0:
            _fail("SECOND_FIT_REQUEST_FORBIDDEN", run=run)
        run.fit_request_count += 1
        return
    if operation == "VALIDATION":
        if run.validation_request_count >= 2:
            _fail("THIRD_VALIDATION_REQUEST_FORBIDDEN", run=run)
        run.validation_request_count += 1
        return
    _fail("OPERATION_REQUEST_KIND_INVALID", run=run)


def _runtime_model_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    *,
    synthetic_fixture_mode: bool,
) -> nn.Module:
    runtime = run.runtime
    if runtime is None:
        _fail("RUNTIME_NOT_AVAILABLE", run=run)
    if (
        not synthetic_fixture_mode
        and type(runtime) is not bounded_owner.CovapieBatch001BoundedTrainingRuntimeV1
    ):
        _fail("BOUNDED_RUNTIME_EXACT_TYPE_REQUIRED", run=run)
    model = getattr(runtime, "model", None)
    if not isinstance(model, nn.Module):
        _fail("RUNTIME_MODEL_NN_MODULE_REQUIRED", run=run)
    if run.model is not None and model is not run.model:
        _fail("RUNTIME_MODEL_OBJECT_REPLACED", run=run)
    return model


def _validate_unexecuted_run_learning_rate_contract_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
) -> None:
    requested = _validate_prepared_lifecycle_v1(run.prepared)
    if (
        run.legacy_constructor_learning_rate
        != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        or run.requested_run_learning_rate != requested
        or run.requested_run_learning_rate_differs_from_legacy_reference
        is not (requested != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1)
        or run.model_learning_rate_before_application != NOT_OBSERVED_V1
        or run.model_learning_rate_after_application != NOT_OBSERVED_V1
        or run.constructor_hparams_learning_rate_after_application
        != NOT_OBSERVED_V1
        or run.learning_rate_application_stage != "NOT_APPLIED"
        or run.actual_optimizer_param_group_learning_rates
        != NOT_OBSERVED_V1
    ):
        _fail("RUN_LEARNING_RATE_DIAGNOSTIC_CONTRACT_INVALID", run=run)


def _model_learning_rate_v1(
    model: nn.Module,
    *,
    reason: str,
    run: CovapieBatch001TrainValidationLifecycleRunV1,
) -> float:
    value = getattr(model, "lr", None)
    if type(value) is not float or not math.isfinite(value):
        _fail(reason, run=run)
    return value


def _apply_pre_fit_learning_rate_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    *,
    synthetic_fixture_mode: bool,
) -> None:
    """Apply the prepared choice after build and before the first A0 snapshot."""

    if run.learning_rate_application_stage != "NOT_APPLIED":
        _fail("RUN_LEARNING_RATE_ALREADY_APPLIED", run=run)
    model = _runtime_model_v1(
        run, synthetic_fixture_mode=synthetic_fixture_mode
    )
    runtime = run.runtime
    trainer = getattr(runtime, "trainer", None)
    optimizers = getattr(trainer, "optimizers", None)
    if validation_owner._trainer_running(model):
        _fail("RUNNING_TRAINER_MODEL_VALIDATION_FORBIDDEN", run=run)
    if (
        run.runtime_build_request_count != 1
        or run.runtime_build_completion_count != 1
        or run.A0 is not None
        or run.A1 is not None
        or run.B0 is not None
        or run.B1 is not None
        or run.validation_request_count != 0
        or run.validation_completion_count != 0
        or run.fit_request_count != 0
        or run.fit_completion_count != 0
        or getattr(runtime, "fit_call_count", None) != 0
        or getattr(trainer, "global_step", None) != 0
    ):
        _fail("RUN_LEARNING_RATE_APPLICATION_TOO_LATE", run=run)
    if type(optimizers) not in (tuple, list) or len(optimizers) != 0:
        _fail("OPTIMIZER_MUST_NOT_EXIST_BEFORE_LEARNING_RATE_APPLICATION", run=run)
    before = _model_learning_rate_v1(
        model,
        reason="LEGACY_CONSTRUCTOR_MODEL_LEARNING_RATE_INVALID",
        run=run,
    )
    if before != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1:
        _fail("LEGACY_CONSTRUCTOR_MODEL_LEARNING_RATE_DRIFT", run=run)
    requested = run.requested_run_learning_rate
    _validate_requested_run_learning_rate_v1(requested)
    run.model_learning_rate_before_application = before
    if before != requested:
        model.lr = requested
    after = _model_learning_rate_v1(
        model,
        reason="EFFECTIVE_MODEL_LEARNING_RATE_INVALID_AFTER_APPLICATION",
        run=run,
    )
    if after != requested:
        _fail("EFFECTIVE_MODEL_LEARNING_RATE_APPLICATION_FAILED", run=run)
    constructor_hparams_lr = validation_owner._hparam_value(model, "lr")
    if constructor_hparams_lr is None:
        observed_hparams_lr: float | str = NOT_OBSERVED_V1
    else:
        if (
            type(constructor_hparams_lr) is not float
            or not math.isfinite(constructor_hparams_lr)
            or constructor_hparams_lr
            != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        ):
            _fail("LEGACY_CONSTRUCTOR_HPARAMS_LEARNING_RATE_DRIFT", run=run)
        observed_hparams_lr = constructor_hparams_lr
    run.model_learning_rate_after_application = after
    run.constructor_hparams_learning_rate_after_application = (
        observed_hparams_lr
    )
    run.learning_rate_application_stage = LEARNING_RATE_APPLICATION_STAGE_V1


def _require_effective_run_learning_rate_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
) -> None:
    model = run.model
    if not isinstance(model, nn.Module):
        _fail("RUN_MODEL_NOT_AVAILABLE_FOR_LEARNING_RATE_CHECK", run=run)
    current = _model_learning_rate_v1(
        model,
        reason="EFFECTIVE_MODEL_LEARNING_RATE_INVALID",
        run=run,
    )
    if (
        run.learning_rate_application_stage
        != LEARNING_RATE_APPLICATION_STAGE_V1
        or run.model_learning_rate_before_application
        != LEGACY_CONSTRUCTOR_LEARNING_RATE_V1
        or run.model_learning_rate_after_application
        != run.requested_run_learning_rate
        or current != run.requested_run_learning_rate
    ):
        _fail("EFFECTIVE_MODEL_LEARNING_RATE_DRIFT", run=run)


def _snapshot_parity_v1(before: object, after: object) -> Mapping[str, bool]:
    values = validation_owner._state_parity(before, after)
    return dict(zip(_SNAPSHOT_PARITY_NAMES_V1, values, strict=True))


def _parameter_ids_v1(snapshot: object) -> tuple[int, ...]:
    return tuple(entry[1] for entry in snapshot.parameter_entries)


def _cross_fit_object_parity_v1(before: object, after: object) -> bool:
    return (
        tuple((row[0], row[1]) for row in before.parameter_entries)
        == tuple((row[0], row[1]) for row in after.parameter_entries)
        and tuple((row[0], row[1]) for row in before.buffer_entries)
        == tuple((row[0], row[1]) for row in after.buffer_entries)
        and before.module_entries == after.module_entries
        and before.state_keys == after.state_keys
        and tuple((row[0], row[2]) for row in before.parameter_entries)
        == tuple((row[0], row[2]) for row in after.parameter_entries)
        and before.configuration_sha256 == after.configuration_sha256
        and before.node_distribution_identity == after.node_distribution_identity
    )


def _parameter_values_changed_v1(before: object, after: object) -> bool:
    left = tuple((row[0], row[3]) for row in before.parameter_entries)
    right = tuple((row[0], row[3]) for row in after.parameter_entries)
    return left != right


def _cpu_environment_snapshot_v1() -> tuple[torch.Tensor, int, bool, bool]:
    return (
        torch.random.get_rng_state().clone(),
        torch.get_num_threads(),
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )


def _cpu_environment_unchanged_v1(
    before: tuple[torch.Tensor, int, bool, bool]
) -> bool:
    return (
        torch.equal(before[0], torch.random.get_rng_state())
        and before[1:]
        == (
            torch.get_num_threads(),
            torch.are_deterministic_algorithms_enabled(),
            torch.is_deterministic_algorithms_warn_only_enabled(),
        )
    )


def _float_equal_v1(left: object, right: object) -> bool:
    return (
        type(left) in (float, int)
        and type(right) in (float, int)
        and math.isfinite(float(left))
        and math.isfinite(float(right))
        and math.isclose(float(left), float(right), rel_tol=1.0e-12, abs_tol=1.0e-12)
    )


def _validate_validation_result_v1(
    *,
    result: object,
    prepared: validation_owner.CovapieBatch001PreparedCurrentStateValidation4V1,
    expected_stage: str,
    expected_stage_evidence: str,
    expected_snapshot: object,
    synthetic_fixture_mode: bool,
) -> tuple[
    tuple[object, ...],
    tuple[object, ...],
    tuple[object, ...],
]:
    if (
        not synthetic_fixture_mode
        and type(result)
        is not validation_owner.CovapieBatch001CurrentStateValidation4ResultV1
    ):
        _fail("PUBLIC_VALIDATION4_RESULT_EXACT_TYPE_REQUIRED")
    required_equal = {
        "implementation_status": "EXECUTED",
        "primary_metric_name": validation_owner.PRIMARY_METRIC_NAME_V1,
        "validation_model_weight_source": (
            validation_owner.VALIDATION_MODEL_WEIGHT_SOURCE_V1
        ),
        "caller_model_stage": expected_stage,
        "caller_stage_evidence": expected_stage_evidence,
        "caller_quiescence_asserted": True,
        "historical_output644_model_state_recovered": False,
        "formal_validation_event_ids": prepared.summary.formal_validation_event_ids,
        "root_validation_seeds": prepared.summary.root_validation_seeds,
        "formal_validation_event_count": 4,
        "formal_validation_task_event_count": 16,
        "formal_validation_estimate_count": 64,
        "formal_validation_task_slice_evaluation_count": 20,
        "main_dynamics_task_slice_call_count": 20,
        "t0_dynamics_task_slice_call_count": 20,
        "total_dynamics_task_slice_call_count": 40,
        "primary_node_prior_included": False,
        "source_parameters_unchanged": True,
        "source_buffers_unchanged": True,
        "source_gradients_unchanged": True,
        "source_requires_grad_unchanged": True,
        "source_parameter_identities_unchanged": True,
        "source_buffer_identities_unchanged": True,
        "source_module_identities_unchanged": True,
        "source_state_keys_unchanged": True,
        "source_configuration_unchanged": True,
        "evaluation_carriers_unchanged": True,
        "source_training_flags_restored": True,
        "CPU_rng_restored": True,
        "CPU_determinism_settings_restored": True,
        "no_new_parameter_module_or_state_key": True,
        "metric_tensors_require_grad": False,
        "all_validation_rows_finite": True,
        "checkpoint_loaded_inside_validation": False,
        "shadow_model_constructed": False,
        "optimizer_created": False,
        "Trainer_used": False,
        "backward_performed": False,
        "parameter_update_performed": False,
    }
    if any(getattr(result, name, None) != value for name, value in required_equal.items()):
        _fail("VALIDATION4_RESULT_CONTRACT_INVALID")
    if (
        getattr(result, "source_model_state_sha256_before", None)
        != expected_snapshot.model_state_sha256
        or getattr(result, "source_model_state_sha256_after", None)
        != expected_snapshot.model_state_sha256
        or getattr(result, "model_training_provenance_status", None)
        != validation_owner.MODEL_STATE_TRAINING_PROVENANCE_V1
    ):
        _fail("VALIDATION4_RESULT_MODEL_STATE_EVIDENCE_INVALID")
    rows = getattr(result, "per_estimate_rows", None)
    if type(rows) is not tuple:
        _fail("VALIDATION4_RESULT_ROWS_TYPE_INVALID")
    aggregates = validation_owner._validate_and_aggregate_rows_v1(
        estimates=rows, prepared=prepared
    )
    task_means, event_means, event_macro, micro, profile_means, profile_balanced = (
        aggregates
    )
    if (
        getattr(result, "per_event_task_seed_means", None) != task_means
        or getattr(result, "per_event_means", None) != event_means
        or getattr(result, "profile_means", None) != profile_means
        or not _float_equal_v1(
            getattr(result, "event_macro_masked_conditional_vlb_nll", None),
            event_macro,
        )
        or not _float_equal_v1(
            getattr(result, "micro_masked_conditional_vlb_nll", None), micro
        )
        or not _float_equal_v1(
            getattr(
                result,
                "profile_balanced_masked_conditional_vlb_nll",
                None,
            ),
            profile_balanced,
        )
    ):
        _fail("VALIDATION4_PUBLISHED_AGGREGATION_MISMATCH")
    auxiliary = (
        "mean_pair_BCE",
        "mean_POST_geometry_loss",
        "mean_POST_geometry_prediction_angstrom",
        "mean_POST_geometry_target_angstrom",
        "mean_pair_contrastive_loss",
        "mean_task4_historical_joint_nll_with_node_prior_diagnostic",
    )
    if any(
        not isinstance(getattr(result, name, None), (int, float))
        or not math.isfinite(float(getattr(result, name)))
        for name in auxiliary
    ):
        _fail("VALIDATION4_AUXILIARY_METRIC_NONFINITE")
    task4_joint = tuple(
        float(row.task4_historical_joint_nll_with_node_prior_diagnostic)
        for row in rows
        if row.task4_historical_joint_nll_with_node_prior_diagnostic is not None
    )
    expected_auxiliary = {
        "mean_pair_BCE": math.fsum(row.pair_BCE for row in rows) / len(rows),
        "mean_POST_geometry_loss": (
            math.fsum(row.POST_geometry_loss for row in rows) / len(rows)
        ),
        "mean_POST_geometry_prediction_angstrom": (
            math.fsum(row.POST_geometry_prediction_angstrom for row in rows)
            / len(rows)
        ),
        "mean_POST_geometry_target_angstrom": (
            math.fsum(row.POST_geometry_target_angstrom for row in rows)
            / len(rows)
        ),
        "mean_pair_contrastive_loss": (
            math.fsum(row.pair_contrastive_loss for row in rows) / len(rows)
        ),
        "mean_task4_historical_joint_nll_with_node_prior_diagnostic": (
            math.fsum(task4_joint) / len(task4_joint)
        ),
    }
    if any(
        not _float_equal_v1(getattr(result, name), expected)
        for name, expected in expected_auxiliary.items()
    ):
        _fail("VALIDATION4_AUXILIARY_AGGREGATION_MISMATCH")
    return rows, task_means, event_means


def _row_key_v1(row: object) -> tuple[str, int, int]:
    return (
        row.canonical_event_id,
        row.canonical_task_id,
        row.root_validation_seed,
    )


def _finite_delta_v1(post: float, pre: float) -> float:
    value = float(post) - float(pre)
    if not math.isfinite(value):
        _fail("PAIRED_METRIC_DELTA_NONFINITE")
    return value


def _build_paired_comparison_v1(
    *,
    pre_result: object,
    post_result: object,
    prepared: validation_owner.CovapieBatch001PreparedCurrentStateValidation4V1,
    pre_snapshot: object,
    post_snapshot: object,
    pre_stage_evidence: str,
    post_stage_evidence: str,
    synthetic_fixture_mode: bool,
) -> CovapieBatch001PairedMetricComparisonV1:
    pre_rows, pre_tasks, pre_events = _validate_validation_result_v1(
        result=pre_result,
        prepared=prepared,
        expected_stage=PRE_FIT_MODEL_STAGE_V1,
        expected_stage_evidence=pre_stage_evidence,
        expected_snapshot=pre_snapshot,
        synthetic_fixture_mode=synthetic_fixture_mode,
    )
    post_rows, post_tasks, post_events = _validate_validation_result_v1(
        result=post_result,
        prepared=prepared,
        expected_stage=POST_FIT_MODEL_STAGE_V1,
        expected_stage_evidence=post_stage_evidence,
        expected_snapshot=post_snapshot,
        synthetic_fixture_mode=synthetic_fixture_mode,
    )
    pre_by_key = {_row_key_v1(row): row for row in pre_rows}
    post_by_key = {_row_key_v1(row): row for row in post_rows}
    if (
        len(pre_by_key) != 64
        or len(post_by_key) != 64
        or pre_by_key.keys() != post_by_key.keys()
    ):
        _fail("PAIRED_ESTIMATE_KEY_DOMAIN_INVALID")
    estimate_deltas = []
    for key in sorted(pre_by_key):
        pre = pre_by_key[key]
        post = post_by_key[key]
        if any(
            getattr(pre, name) != getattr(post, name)
            for name in _PAIRED_ROW_METADATA_FIELDS_V1
        ):
            _fail("PAIRED_ESTIMATE_METADATA_MISMATCH")
        estimate_deltas.append(CovapieBatch001PairedEstimateDeltaV1(
            canonical_event_id=key[0],
            canonical_task_id=key[1],
            root_validation_seed=key[2],
            masked_conditional_vlb_nll_post_minus_pre=_finite_delta_v1(
                post.masked_conditional_vlb_nll,
                pre.masked_conditional_vlb_nll,
            ),
            pair_BCE_post_minus_pre=_finite_delta_v1(
                post.pair_BCE, pre.pair_BCE
            ),
            POST_geometry_loss_post_minus_pre=_finite_delta_v1(
                post.POST_geometry_loss, pre.POST_geometry_loss
            ),
            pair_contrastive_loss_post_minus_pre=_finite_delta_v1(
                post.pair_contrastive_loss, pre.pair_contrastive_loss
            ),
        ))
    pre_task_by_key = {
        (row.canonical_event_id, row.canonical_task_id): row for row in pre_tasks
    }
    post_task_by_key = {
        (row.canonical_event_id, row.canonical_task_id): row for row in post_tasks
    }
    if (
        len(pre_task_by_key) != 16
        or len(post_task_by_key) != 16
        or pre_task_by_key.keys() != post_task_by_key.keys()
    ):
        _fail("PAIRED_EVENT_TASK_DOMAIN_INVALID")
    task_deltas = []
    for key in sorted(pre_task_by_key):
        pre = pre_task_by_key[key]
        post = post_task_by_key[key]
        if pre.profile != post.profile or pre.seed_count != post.seed_count:
            _fail("PAIRED_EVENT_TASK_METADATA_MISMATCH")
        task_deltas.append(CovapieBatch001PairedEventTaskDeltaV1(
            canonical_event_id=key[0],
            canonical_task_id=key[1],
            seed_count=pre.seed_count,
            masked_conditional_vlb_nll_pre=pre.masked_conditional_vlb_nll,
            masked_conditional_vlb_nll_post=post.masked_conditional_vlb_nll,
            masked_conditional_vlb_nll_post_minus_pre=_finite_delta_v1(
                post.masked_conditional_vlb_nll,
                pre.masked_conditional_vlb_nll,
            ),
            pair_BCE_post_minus_pre=_finite_delta_v1(
                post.pair_BCE, pre.pair_BCE
            ),
            POST_geometry_loss_post_minus_pre=_finite_delta_v1(
                post.POST_geometry_loss, pre.POST_geometry_loss
            ),
            pair_contrastive_loss_post_minus_pre=_finite_delta_v1(
                post.pair_contrastive_loss, pre.pair_contrastive_loss
            ),
        ))
    pre_event_by_key = {row.canonical_event_id: row for row in pre_events}
    post_event_by_key = {row.canonical_event_id: row for row in post_events}
    if (
        len(pre_event_by_key) != 4
        or len(post_event_by_key) != 4
        or pre_event_by_key.keys() != post_event_by_key.keys()
    ):
        _fail("PAIRED_EVENT_DOMAIN_INVALID")
    event_deltas = []
    for key in sorted(pre_event_by_key):
        pre = pre_event_by_key[key]
        post = post_event_by_key[key]
        if (
            pre.profile != post.profile
            or pre.applicable_task_count != post.applicable_task_count
        ):
            _fail("PAIRED_EVENT_METADATA_MISMATCH")
        event_deltas.append(CovapieBatch001PairedEventDeltaV1(
            canonical_event_id=key,
            applicable_task_count=pre.applicable_task_count,
            masked_conditional_vlb_nll_pre=pre.masked_conditional_vlb_nll,
            masked_conditional_vlb_nll_post=post.masked_conditional_vlb_nll,
            masked_conditional_vlb_nll_post_minus_pre=_finite_delta_v1(
                post.masked_conditional_vlb_nll,
                pre.masked_conditional_vlb_nll,
            ),
        ))
    return CovapieBatch001PairedMetricComparisonV1(
        comparison_direction="post_minus_pre",
        primary_metric_name=validation_owner.PRIMARY_METRIC_NAME_V1,
        paired_estimate_count=64,
        paired_event_task_count=16,
        paired_event_count=4,
        event_macro_pre=pre_result.event_macro_masked_conditional_vlb_nll,
        event_macro_post=post_result.event_macro_masked_conditional_vlb_nll,
        event_macro_post_minus_pre=_finite_delta_v1(
            post_result.event_macro_masked_conditional_vlb_nll,
            pre_result.event_macro_masked_conditional_vlb_nll,
        ),
        micro_pre=pre_result.micro_masked_conditional_vlb_nll,
        micro_post=post_result.micro_masked_conditional_vlb_nll,
        micro_post_minus_pre=_finite_delta_v1(
            post_result.micro_masked_conditional_vlb_nll,
            pre_result.micro_masked_conditional_vlb_nll,
        ),
        profile_balanced_pre=(
            pre_result.profile_balanced_masked_conditional_vlb_nll
        ),
        profile_balanced_post=(
            post_result.profile_balanced_masked_conditional_vlb_nll
        ),
        profile_balanced_post_minus_pre=_finite_delta_v1(
            post_result.profile_balanced_masked_conditional_vlb_nll,
            pre_result.profile_balanced_masked_conditional_vlb_nll,
        ),
        mean_pair_BCE_post_minus_pre=_finite_delta_v1(
            post_result.mean_pair_BCE, pre_result.mean_pair_BCE
        ),
        mean_POST_geometry_loss_post_minus_pre=_finite_delta_v1(
            post_result.mean_POST_geometry_loss,
            pre_result.mean_POST_geometry_loss,
        ),
        mean_pair_contrastive_loss_post_minus_pre=_finite_delta_v1(
            post_result.mean_pair_contrastive_loss,
            pre_result.mean_pair_contrastive_loss,
        ),
        mean_task4_historical_joint_nll_post_minus_pre=_finite_delta_v1(
            post_result.mean_task4_historical_joint_nll_with_node_prior_diagnostic,
            pre_result.mean_task4_historical_joint_nll_with_node_prior_diagnostic,
        ),
        per_estimate=tuple(estimate_deltas),
        per_event_task=tuple(task_deltas),
        per_event=tuple(event_deltas),
    )


def _sole_optimizer_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    *,
    synthetic_fixture_mode: bool,
) -> object:
    trainer = getattr(run.runtime, "trainer", None)
    optimizers = getattr(trainer, "optimizers", None)
    if type(optimizers) not in (tuple, list) or len(optimizers) != 1:
        _fail("EXACTLY_ONE_PRODUCTION_OPTIMIZER_REQUIRED", run=run)
    optimizer = optimizers[0]
    if (
        not synthetic_fixture_mode
        and not isinstance(optimizer, torch.optim.Optimizer)
    ):
        _fail("PRODUCTION_OPTIMIZER_TYPE_INVALID", run=run)
    if not callable(getattr(optimizer, "state_dict", None)):
        _fail("OPTIMIZER_STATE_INTERFACE_INVALID", run=run)
    parameter_groups = getattr(optimizer, "param_groups", None)
    if type(parameter_groups) is not list or not parameter_groups:
        _fail("OPTIMIZER_PARAMETER_GROUPS_INVALID", run=run)
    optimizer_parameter_ids = tuple(
        id(parameter)
        for group in parameter_groups
        if type(group) is dict
        for parameter in group.get("params", ())
    )
    model_parameter_ids = tuple(id(parameter) for parameter in run.model.parameters())
    if (
        not optimizer_parameter_ids
        or len(optimizer_parameter_ids) != len(set(optimizer_parameter_ids))
        or set(optimizer_parameter_ids) != set(model_parameter_ids)
    ):
        _fail("OPTIMIZER_MODEL_PARAMETER_DOMAIN_INVALID", run=run)
    return optimizer


def _observe_optimizer_learning_rates_v1(
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    optimizer: object,
) -> tuple[float, ...]:
    if run.actual_optimizer_param_group_learning_rates != NOT_OBSERVED_V1:
        _fail("OPTIMIZER_LEARNING_RATE_ALREADY_OBSERVED", run=run)
    groups = getattr(optimizer, "param_groups", None)
    if type(groups) is not list or not groups:
        _fail("OPTIMIZER_PARAMETER_GROUPS_INVALID", run=run)
    learning_rates = []
    for group in groups:
        if type(group) is not dict:
            _fail("OPTIMIZER_PARAMETER_GROUP_INVALID", run=run)
        value = group.get("lr")
        if type(value) is not float or not math.isfinite(value):
            _fail("OPTIMIZER_PARAMETER_GROUP_LEARNING_RATE_INVALID", run=run)
        learning_rates.append(value)
    observed = tuple(learning_rates)
    run.actual_optimizer_param_group_learning_rates = observed
    if any(value != run.requested_run_learning_rate for value in observed):
        _fail("OPTIMIZER_LEARNING_RATE_MISMATCH", run=run)
    return observed


def _optimizer_snapshot_v1(optimizer: object) -> _OptimizerSnapshotV1:
    parameter_ids = tuple(
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    )
    state = optimizer.state_dict()
    return _OptimizerSnapshotV1(
        optimizer_identity=id(optimizer),
        parameter_identities=parameter_ids,
        state_sha256=validation_owner._value_sha256(
            _normalize_scalar_tensors_for_owner_digest_v1(state)
        ),
    )


def _normalize_scalar_tensors_for_owner_digest_v1(value: object) -> object:
    """Give the reused owner digest a byte-viewable shape for scalar state."""

    if isinstance(value, torch.Tensor):
        return value.reshape(1) if value.ndim == 0 else value
    if isinstance(value, Mapping):
        return {
            key: _normalize_scalar_tensors_for_owner_digest_v1(item)
            for key, item in value.items()
        }
    if type(value) is tuple:
        return tuple(
            _normalize_scalar_tensors_for_owner_digest_v1(item) for item in value
        )
    if type(value) is list:
        return [
            _normalize_scalar_tensors_for_owner_digest_v1(item) for item in value
        ]
    return value


def _training_carrier_fingerprints_v1(
    prepared: CovapieBatch001PreparedTrainValidationLifecycleV1,
) -> tuple[str, ...]:
    return tuple(
        bounded_owner._epoch_summary(carrier).carrier_fingerprint
        for carrier in prepared.training.carriers
    )


def _validation_carrier_fingerprint_v1(
    prepared: CovapieBatch001PreparedTrainValidationLifecycleV1,
) -> str:
    return validation_owner._carrier_fingerprint(prepared.validation)


def _perform_validation_stage_v1(
    *,
    run: CovapieBatch001TrainValidationLifecycleRunV1,
    evaluator: Callable[..., object],
    stage: str,
    stage_evidence: str,
    repository_root: Path,
    cache_root: Path,
    synthetic_fixture_mode: bool,
) -> tuple[object, object]:
    is_pre = stage == PRE_FIT_MODEL_STAGE_V1
    try:
        model = _runtime_model_v1(
            run, synthetic_fixture_mode=synthetic_fixture_mode
        )
        if validation_owner._trainer_running(model):
            _fail("RUNNING_TRAINER_MODEL_VALIDATION_FORBIDDEN", run=run)
        _require_effective_run_learning_rate_v1(run)
    except BaseException as error:
        reason = (
            error.reason
            if isinstance(
                error,
                CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
            )
            else (
                "PRE_FIT_VALIDATION_GATE_REJECTED"
                if is_pre
                else "POST_FIT_VALIDATION_GATE_REJECTED_AFTER_TRAINING_UPDATE"
            )
        )
        _mark_terminal_failure_v1(
            run, stage=stage, reason=reason, cause=error
        )
    before = validation_owner._snapshot_model_state_v1(model)
    environment_before = _cpu_environment_snapshot_v1()
    _request_operation_v1(run, "VALIDATION")
    _set_phase_v1(
        run,
        "PRE_FIT_VALIDATION_REQUESTED" if is_pre else "POST_FIT_VALIDATION_REQUESTED",
    )
    try:
        result = evaluator(
            source_model=model,
            execution_opt_in=True,
            caller_model_stage=stage,
            caller_stage_evidence=stage_evidence,
            caller_confirms_model_is_quiescent=True,
            repository_root=repository_root,
            cache_root=cache_root,
        )
        _require_effective_run_learning_rate_v1(run)
    except BaseException as error:
        after = validation_owner._snapshot_model_state_v1(model)
        if is_pre:
            run.A0, run.A1 = before, after
            run.pre_fit_state_isolation_pass = all(
                _snapshot_parity_v1(before, after).values()
            )
            run.pre_fit_public_API_rng_isolation_pass = (
                _cpu_environment_unchanged_v1(environment_before)
            )
        else:
            run.B0, run.B1 = before, after
            run.post_fit_state_isolation_pass = all(
                _snapshot_parity_v1(before, after).values()
            )
            run.post_fit_public_API_rng_isolation_pass = (
                _cpu_environment_unchanged_v1(environment_before)
            )
        _mark_terminal_failure_v1(
            run,
            stage=stage,
            reason=(
                "PRE_FIT_VALIDATION_FAILED"
                if is_pre
                else "POST_FIT_VALIDATION_FAILED_AFTER_TRAINING_UPDATE"
            ),
            cause=error,
        )
    after = validation_owner._snapshot_model_state_v1(model)
    parity = _snapshot_parity_v1(before, after)
    rng_pass = _cpu_environment_unchanged_v1(environment_before)
    if is_pre:
        run.A0, run.A1 = before, after
        run.pre_fit_state_isolation_pass = all(parity.values())
        run.pre_fit_public_API_rng_isolation_pass = rng_pass
    else:
        run.B0, run.B1 = before, after
        run.post_fit_state_isolation_pass = all(parity.values())
        run.post_fit_public_API_rng_isolation_pass = rng_pass
    try:
        if _runtime_model_v1(
            run, synthetic_fixture_mode=synthetic_fixture_mode
        ) is not model:
            _fail("VALIDATION_MODEL_OBJECT_REPLACED", run=run)
        if not all(parity.values()):
            _fail("PUBLIC_VALIDATION4_MODEL_STATE_ISOLATION_FAILED", run=run)
        if not rng_pass:
            _fail("PUBLIC_VALIDATION4_CPU_RNG_ISOLATION_FAILED", run=run)
        _validate_validation_result_v1(
            result=result,
            prepared=run.prepared.validation,
            expected_stage=stage,
            expected_stage_evidence=stage_evidence,
            expected_snapshot=before,
            synthetic_fixture_mode=synthetic_fixture_mode,
        )
    except BaseException as error:
        _mark_terminal_failure_v1(
            run,
            stage=stage,
            reason=(
                "PRE_FIT_VALIDATION_RESULT_OR_ISOLATION_REJECTED"
                if is_pre
                else "POST_FIT_VALIDATION_RESULT_OR_ISOLATION_REJECTED_AFTER_TRAINING_UPDATE"
            ),
            cause=error,
        )
    run.validation_completion_count += 1
    if is_pre:
        run.pre_fit_validation_result = result
        _set_phase_v1(run, "PRE_FIT_VALIDATION_COMPLETED_A1")
    else:
        run.post_fit_validation_result = result
        _set_phase_v1(run, "POST_FIT_VALIDATION_COMPLETED_B1")
    return result, after


def _execute_lifecycle_with_callbacks_v1(
    *,
    run: object,
    execution_opt_in: object = False,
    runtime_root: object,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
    runtime_builder: Callable[..., object] | None = None,
    evaluator: Callable[..., object] | None = None,
    fit_invoker: Callable[[object], object] | None = None,
    synthetic_fixture_mode: object = False,
    feature_semantics_use_audit_confirmed: object = False,
) -> CovapieBatch001TrainValidationLifecycleRunV1:
    if execution_opt_in is not True:
        _fail("EXPLICIT_LIFECYCLE_EXECUTION_OPT_IN_REQUIRED")
    if type(run) is not CovapieBatch001TrainValidationLifecycleRunV1:
        _fail("LIFECYCLE_RUN_TYPE_INVALID")
    if run.execution_consumed:
        _fail("LIFECYCLE_ALREADY_CONSUMED_NO_RETRY_OR_RESUME", run=run)
    _validate_unexecuted_run_learning_rate_contract_v1(run)
    callbacks = (runtime_builder, evaluator, fit_invoker)
    if synthetic_fixture_mode is True:
        if not all(callable(callback) for callback in callbacks):
            _fail("SYNTHETIC_FIXTURE_CALLBACK_SET_INCOMPLETE", run=run)
    elif synthetic_fixture_mode is False:
        if any(callback is not None for callback in callbacks):
            _fail("PRODUCTION_CALLBACK_INJECTION_FORBIDDEN", run=run)
        if feature_semantics_use_audit_confirmed is not True:
            _fail(
                "FEATURE_SEMANTICS_USE_AUDIT_CONFIRMATION_REQUIRED",
                run=run,
            )
        runtime_builder = bounded_owner.build_covapie_batch001_bounded_training_runtime_v1
        evaluator = validation_owner.evaluate_covapie_batch001_current_state_validation4_v1
        fit_invoker = bounded_owner._invoke_fit_once_v1
    else:
        _fail("SYNTHETIC_FIXTURE_MODE_BOOLEAN_REQUIRED", run=run)
    repository = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    state = _require_directory(
        state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID"
    )
    cache = _require_directory(
        cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
    )
    runtime_path = _require_directory(
        runtime_root,
        default=Path("/__no_default__"),
        reason="RUNTIME_ROOT_INVALID",
    )
    _validate_prepared_lifecycle_v1(run.prepared)
    verify_covapie_batch001_train_validation_lifecycle_sources_v1(
        repository_root=repository
    )
    initial_train_fingerprints = _training_carrier_fingerprints_v1(run.prepared)
    initial_validation_fingerprint = _validation_carrier_fingerprint_v1(
        run.prepared
    )
    if (
        initial_train_fingerprints
        != run.prepared.summary.training_carrier_fingerprints
    ):
        _fail("PRE_EXECUTION_TRAIN_CARRIER_IDENTITY_DRIFT", run=run)
    run.execution_consumed = True
    run.terminal_status = "RUNNING"
    _request_operation_v1(run, "BUILD")
    _set_phase_v1(run, "RUNTIME_BUILD_REQUESTED")
    try:
        runtime = runtime_builder(
            execution_authorized=True,
            prepared=run.prepared.training,
            runtime_root=runtime_path,
            repository_root=repository,
            state_root=state,
        )
    except BaseException as error:
        _mark_terminal_failure_v1(
            run,
            stage="RUNTIME_BUILD",
            reason="RUNTIME_BUILD_FAILED",
            cause=error,
        )
    run.runtime = runtime
    run.runtime_build_completion_count += 1
    try:
        model = _runtime_model_v1(
            run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
        )
        run.model = model
        run.model_object_identity = id(model)
        if not validation_owner._trainer_running(model):
            _apply_pre_fit_learning_rate_v1(
                run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
            )
        run.A0 = validation_owner._snapshot_model_state_v1(model)
        run.parameter_object_identities = _parameter_ids_v1(run.A0)
    except BaseException as error:
        _mark_terminal_failure_v1(
            run,
            stage="RUNTIME_BUILD",
            reason="BUILT_RUNTIME_MODEL_REJECTED",
            cause=error,
        )
    _set_phase_v1(run, "RUNTIME_BUILT_A0")
    pre_evidence = (
        f"{TASK_ID_V1}:same_process_runtime_model:{run.model_object_identity}:A0"
    )
    pre_result, _unused_A1 = _perform_validation_stage_v1(
        run=run,
        evaluator=evaluator,
        stage=PRE_FIT_MODEL_STAGE_V1,
        stage_evidence=pre_evidence,
        repository_root=repository,
        cache_root=cache,
        synthetic_fixture_mode=bool(synthetic_fixture_mode),
    )
    if run.A0 is None or run.A1 is None:
        _fail("PRE_FIT_STATE_CHECKPOINTS_MISSING", run=run)
    if not _cross_fit_object_parity_v1(run.A0, run.A1):
        _fail("PRE_FIT_MODEL_OBJECT_PARITY_INVALID", run=run)
    _require_effective_run_learning_rate_v1(run)
    _request_operation_v1(run, "FIT")
    _set_phase_v1(run, "FIT_REQUESTED")
    try:
        fit_invoker(runtime)
    except BaseException as error:
        run.fit_returned = False
        try:
            failed_model = _runtime_model_v1(
                run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
            )
            run.fit_failure_state = validation_owner._snapshot_model_state_v1(
                failed_model
            )
            run.parameter_update_observed = _parameter_values_changed_v1(
                run.A1, run.fit_failure_state
            )
            trainer = getattr(runtime, "trainer", None)
            run.actual_global_step = getattr(trainer, "global_step", None)
            run.actual_final_epoch = getattr(trainer, "current_epoch", None)
        except BaseException:
            pass
        _mark_terminal_failure_v1(
            run,
            stage="BOUNDED_FIT",
            reason="BOUNDED_FIT_FAILED_NO_RETRY_POST_VALIDATION_NOT_REACHED",
            cause=error,
        )
    run.fit_returned = True
    run.fit_completion_count += 1
    try:
        model_after_fit = _runtime_model_v1(
            run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
        )
        _require_effective_run_learning_rate_v1(run)
        trainer = getattr(runtime, "trainer", None)
        run.actual_global_step = getattr(trainer, "global_step", None)
        run.actual_final_epoch = getattr(trainer, "current_epoch", None)
        run.B0 = validation_owner._snapshot_model_state_v1(model_after_fit)
        run.parameter_update_observed = _parameter_values_changed_v1(
            run.A1, run.B0
        )
        run.same_model_and_parameter_objects_pass = (
            model_after_fit is run.model
            and _cross_fit_object_parity_v1(run.A1, run.B0)
        )
        if (
            getattr(runtime, "fit_call_count", None) != 1
            or run.actual_global_step != 5
            or run.actual_final_epoch != 5
            or validation_owner._trainer_running(model_after_fit)
            or not run.parameter_update_observed
            or not run.same_model_and_parameter_objects_pass
        ):
            _fail("BOUNDED_FIT_COMPLETION_CONTRACT_INVALID", run=run)
        optimizer = _sole_optimizer_v1(
            run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
        )
        _observe_optimizer_learning_rates_v1(run, optimizer)
        optimizer_before = _optimizer_snapshot_v1(optimizer)
        run.optimizer_object_identity = id(optimizer)
    except BaseException as error:
        _mark_terminal_failure_v1(
            run,
            stage="BOUNDED_FIT",
            reason="BOUNDED_FIT_COMPLETION_STATE_REJECTED",
            cause=error,
        )
    _set_phase_v1(run, "FIT_COMPLETED_B0")
    post_evidence = (
        f"{TASK_ID_V1}:same_process_fit_returned_model:"
        f"{run.model_object_identity}:global_step_5:B0"
    )
    post_result, _unused_B1 = _perform_validation_stage_v1(
        run=run,
        evaluator=evaluator,
        stage=POST_FIT_MODEL_STAGE_V1,
        stage_evidence=post_evidence,
        repository_root=repository,
        cache_root=cache,
        synthetic_fixture_mode=bool(synthetic_fixture_mode),
    )
    try:
        optimizer_after = _sole_optimizer_v1(
            run, synthetic_fixture_mode=bool(synthetic_fixture_mode)
        )
        optimizer_after_snapshot = _optimizer_snapshot_v1(optimizer_after)
        run.post_fit_optimizer_isolation_pass = (
            optimizer_after_snapshot == optimizer_before
        )
        if not run.post_fit_optimizer_isolation_pass:
            _fail("POST_FIT_VALIDATION_MUTATED_OPTIMIZER_STATE", run=run)
        if run.B0 is None or run.B1 is None:
            _fail("POST_FIT_STATE_CHECKPOINTS_MISSING", run=run)
        run.same_model_and_parameter_objects_pass = bool(
            run.same_model_and_parameter_objects_pass
            and _cross_fit_object_parity_v1(run.B0, run.B1)
            and _parameter_ids_v1(run.A0)
            == _parameter_ids_v1(run.A1)
            == _parameter_ids_v1(run.B0)
            == _parameter_ids_v1(run.B1)
        )
        if not run.same_model_and_parameter_objects_pass:
            _fail("FOUR_STAGE_MODEL_OR_PARAMETER_IDENTITY_MISMATCH", run=run)
        final_bindings = (
            verify_covapie_batch001_train_validation_lifecycle_sources_v1(
                repository_root=repository
            )
        )
        checkpoint_size, checkpoint_sha = (
            bounded_owner.verify_covapie_batch001_bounded_training_checkpoint_identity_v1(
                repository_root=repository
            )
        )
        final_train_fingerprints = _training_carrier_fingerprints_v1(
            run.prepared
        )
        final_validation_fingerprint = _validation_carrier_fingerprint_v1(
            run.prepared
        )
        run.source_and_carrier_identity_final_pass = (
            final_bindings == run.prepared.summary.source_bindings
            and checkpoint_size == run.prepared.summary.checkpoint_size_bytes
            and checkpoint_sha == run.prepared.summary.checkpoint_sha256
            and final_train_fingerprints == initial_train_fingerprints
            and final_validation_fingerprint == initial_validation_fingerprint
        )
        if not run.source_and_carrier_identity_final_pass:
            _fail("FINAL_SOURCE_CHECKPOINT_OR_CARRIER_IDENTITY_DRIFT", run=run)
        run.paired_comparison = _build_paired_comparison_v1(
            pre_result=pre_result,
            post_result=post_result,
            prepared=run.prepared.validation,
            pre_snapshot=run.A0,
            post_snapshot=run.B0,
            pre_stage_evidence=pre_evidence,
            post_stage_evidence=post_evidence,
            synthetic_fixture_mode=bool(synthetic_fixture_mode),
        )
    except BaseException as error:
        _mark_terminal_failure_v1(
            run,
            stage="POST_FIT_FINALIZATION",
            reason="POST_FIT_STATE_OR_PAIRED_COMPARISON_REJECTED",
            cause=error,
        )
    run.terminal_status = "COMPLETED"
    _set_phase_v1(run, "COMPLETED")
    return run


def execute_covapie_batch001_train_validation_lifecycle_v1(
    *,
    run: object,
    execution_opt_in: object = False,
    runtime_root: object,
    repository_root: object = None,
    state_root: object = None,
    cache_root: object = None,
    feature_semantics_use_audit_confirmed: object = False,
) -> CovapieBatch001TrainValidationLifecycleRunV1:
    """Future production execution after separate user authority and audit.

    Boolean arguments are fail-closed technical gates; they are not themselves
    authority to train or evaluate without a later explicit user request.
    """

    return _execute_lifecycle_with_callbacks_v1(
        run=run,
        execution_opt_in=execution_opt_in,
        runtime_root=runtime_root,
        repository_root=repository_root,
        state_root=state_root,
        cache_root=cache_root,
        feature_semantics_use_audit_confirmed=(
            feature_semantics_use_audit_confirmed
        ),
    )


def serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
    prepared: object,
) -> bytes:
    _validate_prepared_lifecycle_v1(prepared)
    return (
        json.dumps(
            asdict(prepared.summary),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Prepare-only CLI; execution and training options do not exist."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument(
        "--learning-rate",
        type=float,
        choices=ALLOWED_RUN_LEARNING_RATES_V1,
        default=LEGACY_CONSTRUCTOR_LEARNING_RATE_V1,
    )
    arguments = parser.parse_args(argv)
    prepared = prepare_covapie_batch001_train_validation_lifecycle_v1(
        repository_root=arguments.repository_root,
        state_root=arguments.state_root,
        cache_root=arguments.cache_root,
        learning_rate=arguments.learning_rate,
    )
    print(
        serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
            prepared
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

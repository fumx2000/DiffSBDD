"""One ordinary bounded ``Trainer.fit`` step on formal batch-001 train5.

This smoke is deliberately local orchestration.  Formal selection and
structural/supervision preparation come from the published train5 predecessor;
model, loss, migration, training-step, and optimizer ownership remain with the
published Current11 owners.  No report, checkpoint, or tensor is persisted.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import math
from pathlib import Path
import platform
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, fields
from typing import Mapping, NoReturn, Sequence

import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

import pytorch_lightning as pl  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as forward_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as single_step_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as instantiation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as migration_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1
    as trainer_reference,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_ERROR_V1",
    "INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1",
    "CovapieBatch001Train5TrainerBatchCarrierV1",
    "CovapieBatch001Train5BoundedTrainerFitSmokeResultV1",
    "verify_covapie_batch001_train5_bounded_trainer_predecessor_source_v1",
    "run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1",
)


BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_ERROR_V1 = (
    "COVAPIE_BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_V1_ERROR"
)
INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1 = (
    single_step_predecessor.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
)

EXPECTED_HEAD_V1 = "7d23b07c29ab8f58e16e639123fe13a9f9de5793"
EXPECTED_HEAD_SUBJECT_V1 = (
    "add CovaPIE batch001 train5 single backward optimizer step smoke v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE batch001 train5 bounded Trainer.fit smoke v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
IMMEDIATE_PREDECESSOR_SHA256_V1 = (
    (
        "src/covalent_ext/"
        "covapie_batch001_train5_single_backward_optimizer_step_smoke_v1.py",
        "7ab327d86df87b5b20e5758906d34f60e21426cc6a9e35376b78b5c97b086cdc",
    ),
    (
        "scripts/"
        "check_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1.py",
        "4cffee820b3f24ed0b5f86f8d63f35ac55774eb901fa615065f3ff0086611b55",
    ),
    (
        "tests/"
        "test_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1.py",
        "a2acd066e5f6a85ea128898152a05446cb1c2c459d0d9c8a0e647fc6c4295a62",
    ),
)
TRAINER_REFERENCE_RELATIVE_PATH_V1 = (
    "src/covalent_ext/"
    "covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py"
)
TRAINER_REFERENCE_SHA256_V1 = (
    "d0c50939eb182a9cc4047b4a99843c7da5a78d6e70a96773afeedd43c4fca653"
)
CANDIDATE_RELATIVE_PATHS_V1 = frozenset((
    "src/covalent_ext/covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
    "scripts/check_covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
    "tests/test_covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
))
EXPECTED_METRIC_KEYS_V1 = frozenset((
    "loss",
    "loss_base_diffusion",
    "loss_covalent_pair_prediction",
    "loss_pre_post_geometry",
    "loss_covalent_pair_contrastive",
))
LOSS_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
LOSS_RELATIVE_TOLERANCE_V1 = 1.0e-7
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001Train5TrainerBatchCarrierV1:
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    sample_identities: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int


@dataclass(frozen=True)
class CovapieBatch001Train5BoundedTrainerFitSmokeResultV1:
    implementation_status: str
    result_interpretation: str
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_unresolved_event_ids: tuple[str, ...]
    non_target_component_event_ids: tuple[str, ...]
    DJK_train_event_count: int
    PTG_train_event_count: int
    scheduled_task_ids: tuple[int, ...]
    ligand_node_count: int
    pocket_node_count: int
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    supervision_field_count: int
    trainer_configuration: tuple[tuple[str, object], ...]
    trainer_api_family: str
    trainer_init_signature: str
    trainer_fit_signature: str
    sampler_control_parameter: str
    precision_argument: object
    active_python_version: str
    active_torch_version: str
    active_lightning_version: str
    direct_probe_rejection_message: str | None
    legacy_validation_epoch_end_compatibility_used: bool
    direct_probe_global_step: int
    direct_probe_dataset_getitem_count: int
    direct_probe_train_batch_start_count: int
    direct_probe_parameters_unchanged: bool
    parameter_delta_snapshot_branch: str
    parameter_delta_snapshot_optimizer_step_count_at_capture: int
    parameter_delta_snapshot_captured_before_optimizer_step: bool
    training_step_method_identity_exact: bool
    configure_optimizers_method_identity_exact: bool
    trainer_fit_invoked: bool
    trainer_fit_train_batch_count: int
    trainer_global_step: int
    automatic_optimization: bool
    automatic_backward_call_count: int
    trainer_optimizer_step_count: int
    zero_grad_lifecycle_call_count: int
    datamodule_setup_fit_call_count: int
    train_dataloader_call_count: int
    dataset_getitem_call_count: int
    collator_call_count: int
    before_batch_transfer_call_count: int
    model_transfer_batch_to_device_call_count: int
    after_batch_transfer_call_count: int
    transferred_batch_rebuilt: bool
    transferred_metadata_unchanged: bool
    transferred_tensors_on_model_device: bool
    dataloader_batch_size: int
    dataloader_sequential_sampler: bool
    dataloader_num_workers: int
    dataloader_drop_last: bool
    dataloader_pin_memory: bool
    dataloader_persistent_workers: bool
    validation_step_call_count: int
    test_step_call_count: int
    diffusion_seed: int
    diffusion_seed_hook: str
    diffusion_seed_hook_call_count: int
    diffusion_timesteps: tuple[int, ...]
    training_step_metrics: tuple[tuple[str, float], ...]
    runtime_losses: tuple[tuple[str, float], ...]
    weighted_total_formula_value: float
    weighted_total_formula_absolute_difference: float
    manual_reference_loss_tuple: tuple[tuple[str, float], ...]
    trainer_loss_tuple: tuple[tuple[str, float], ...]
    max_abs_loss_difference: float
    base_diffusion_valid_sample_count: int
    covalent_pair_prediction_valid_sample_count: int
    POST_geometry_valid_sample_count: int
    PRE_geometry_valid_sample_count: int
    covalent_pair_contrastive_valid_sample_count: int
    published_default_loss_weights: tuple[tuple[str, float], ...]
    initial_joint_loss_candidate: tuple[tuple[str, float], ...]
    optimizer_metadata: single_step_predecessor.CovapieBatch001Train5OptimizerMetadataV1
    gradient_group_stats: tuple[
        single_step_predecessor.CovapieBatch001Train5GradientGroupStatsV1, ...
    ]
    geometry_component_gradient: single_step_predecessor.CovapieBatch001Train5GeometryComponentGradientV1
    parameter_delta_group_stats: tuple[
        single_step_predecessor.CovapieBatch001Train5ParameterDeltaGroupStatsV1,
        ...,
    ]
    changed_parameter_tensor_count: int
    all_parameters_finite_after_fit: bool
    migration_counts: tuple[tuple[str, int], ...]
    migration_missing_keys: tuple[str, ...]
    migration_unexpected_keys: tuple[str, ...]
    architecture: tuple[tuple[str, object], ...]
    bound_source_sha256: tuple[tuple[str, str], ...]
    trainer_reference_source_sha256: str
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    checkpoint_file_changed: bool
    protected_sources_changed: bool
    protected_state_unchanged: bool
    raw_tree_unchanged: bool
    original_batch_unchanged: bool
    original_supervision_unchanged: bool
    temporary_trainer_root_removed: bool
    persistent_output_created: bool
    repository_profile: str
    repository_branch: str
    repository_HEAD: str
    repository_origin_main: str
    repository_ahead: int
    repository_behind: int
    repository_staged_count: int
    repository_untracked_paths: tuple[str, ...]
    published_default_modified: bool
    GPU_used: bool
    network_used: bool
    elapsed_seconds: float
    initial_joint_loss_candidate_validated_for_bounded_trainer_fit: bool
    geometry_weight_optimal: bool
    production_joint_loss_policy_finalized: bool
    full_training_authorized: bool
    ready_for_gpt_review: bool
    ready_for_five_epoch_train5_schedule_refresh_trainer_smoke: bool
    recommended_next_step_exactly: str


@dataclass(frozen=True)
class _RepositoryObservationV1:
    branch: str
    head: str
    subject: str
    origin_main: str
    ahead: int
    behind: int
    tracked_status: tuple[str, ...]
    staged_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    head_parents: tuple[str, ...]
    head_changed_paths: tuple[tuple[str, str], ...]
    head_tree_modes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class _PreOptimizerStepParameterSnapshotV1:
    branch: str
    model_identity: int
    trainer_global_step_at_capture: int
    optimizer_step_count_at_capture: int
    tensors: dict[str, torch.Tensor]


class _SmokeInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _SmokeInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_ERROR_V1
    ):
        raise error
    if isinstance(error, (
        _SmokeInvariantError,
        single_step_predecessor._SmokeInvariantError,
        forward_predecessor._SmokeInvariantError,
    )):
        reason = error.reason
    else:
        reason = "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_ERROR_V1}:{reason}"
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


def _git(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or completed.stderr:
        _fail("GIT_COMMAND_FAILED")
    return completed.stdout.strip()


def _classify_repository_profile_v1(
    observation: _RepositoryObservationV1,
) -> str:
    if (
        type(observation) is not _RepositoryObservationV1
        or observation.branch != "main"
        or observation.ahead != 0
        or observation.behind != 0
        or observation.tracked_status
        or observation.staged_paths
    ):
        _fail("REPOSITORY_PROFILE_INVALID")
    if (
        observation.head == EXPECTED_HEAD_V1
        and observation.subject == EXPECTED_HEAD_SUBJECT_V1
        and observation.origin_main == EXPECTED_HEAD_V1
        and frozenset(observation.untracked_paths) == CANDIDATE_RELATIVE_PATHS_V1
        and len(observation.untracked_paths) == 3
    ):
        return CANDIDATE_PRECOMMIT_PROFILE_V1
    expected_changed = tuple(
        sorted(("A", path) for path in CANDIDATE_RELATIVE_PATHS_V1)
    )
    expected_modes = tuple(
        sorted(("100644", path) for path in CANDIDATE_RELATIVE_PATHS_V1)
    )
    if (
        observation.head != EXPECTED_HEAD_V1
        and observation.origin_main == observation.head
        and observation.subject == PUBLISHED_SUCCESSOR_SUBJECT_V1
        and not observation.untracked_paths
        and observation.head_parents == (EXPECTED_HEAD_V1,)
        and tuple(sorted(observation.head_changed_paths)) == expected_changed
        and tuple(sorted(observation.head_tree_modes)) == expected_modes
    ):
        return PUBLISHED_SUCCESSOR_PROFILE_V1
    _fail("REPOSITORY_PROFILE_INVALID")


def _git_snapshot(repository_root: Path) -> dict[str, object]:
    branch = _git(repository_root, "branch", "--show-current")
    head = _git(repository_root, "rev-parse", "HEAD")
    subject = _git(repository_root, "log", "-1", "--format=%s")
    origin = _git(repository_root, "rev-parse", "origin/main")
    divergence = _git(
        repository_root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    status_lines = tuple(filter(None, _git(
        repository_root, "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines()))
    untracked = tuple(sorted(
        line[3:] for line in status_lines if line.startswith("?? ")
    ))
    tracked_status = tuple(line for line in status_lines if not line.startswith("?? "))
    staged = tuple(filter(None, _git(
        repository_root, "diff", "--cached", "--name-only"
    ).splitlines()))
    parent_line = _git(repository_root, "rev-list", "--parents", "-n", "1", "HEAD").split()
    if not parent_line or parent_line[0] != head:
        _fail("GIT_HEAD_PARENT_OBSERVATION_INVALID")
    parents = tuple(parent_line[1:])
    changed: list[tuple[str, str]] = []
    for line in filter(None, _git(
        repository_root, "diff-tree", "--root", "--no-commit-id",
        "--name-status", "-r", "HEAD",
    ).splitlines()):
        parts = line.split("\t")
        if len(parts) != 2:
            _fail("GIT_HEAD_CHANGED_PATH_OBSERVATION_INVALID")
        changed.append((parts[0], parts[1]))
    modes: list[tuple[str, str]] = []
    tree_output = _git(
        repository_root, "ls-tree", "-r", "--full-tree", "HEAD", "--",
        *sorted(CANDIDATE_RELATIVE_PATHS_V1),
    )
    for line in filter(None, tree_output.splitlines()):
        metadata, separator, path = line.partition("\t")
        metadata_parts = metadata.split()
        if not separator or len(metadata_parts) != 3 or not path:
            _fail("GIT_HEAD_TREE_MODE_OBSERVATION_INVALID")
        modes.append((metadata_parts[0], path))
    if len(divergence) != 2:
        _fail("GIT_DIVERGENCE_OBSERVATION_INVALID")
    try:
        ahead, behind = (int(value) for value in divergence)
    except ValueError as error:
        raise _SmokeInvariantError("GIT_DIVERGENCE_OBSERVATION_INVALID") from error
    observation = _RepositoryObservationV1(
        branch=branch,
        head=head,
        subject=subject,
        origin_main=origin,
        ahead=ahead,
        behind=behind,
        tracked_status=tracked_status,
        staged_paths=staged,
        untracked_paths=untracked,
        head_parents=parents,
        head_changed_paths=tuple(changed),
        head_tree_modes=tuple(modes),
    )
    profile = _classify_repository_profile_v1(observation)
    return {
        "profile": profile,
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "staged": len(staged),
        "untracked": untracked,
    }


def _verify_bound_sources(repository_root: Path) -> tuple[tuple[str, str], ...]:
    bindings = (
        IMMEDIATE_PREDECESSOR_SHA256_V1
        + single_step_predecessor.ALL_BOUND_SOURCE_SHA256_V1
        + ((TRAINER_REFERENCE_RELATIVE_PATH_V1, TRAINER_REFERENCE_SHA256_V1),)
    )
    observed: list[tuple[str, str]] = []
    seen: set[str] = set()
    for relative, expected in bindings:
        if relative in seen:
            continue
        seen.add(relative)
        actual = single_step_predecessor._sha256_file(repository_root / relative)
        if actual != expected:
            _fail("BOUND_SOURCE_SHA256_MISMATCH")
        observed.append((relative, actual))
    single_step_predecessor._verify_bound_sources(repository_root)
    return tuple(observed)


def verify_covapie_batch001_train5_bounded_trainer_predecessor_source_v1(
    *, predecessor_source_path: Path
) -> str:
    """Verify the exact immediate single-step predecessor source."""

    try:
        actual = single_step_predecessor._sha256_file(predecessor_source_path)
        expected = IMMEDIATE_PREDECESSOR_SHA256_V1[0][1]
        if actual != expected:
            _fail("PREDECESSOR_SOURCE_SHA256_MISMATCH")
        return actual
    except BaseException as error:
        _public_error(error)


def _formal_artifact_paths(repository_root: Path) -> tuple[Path, ...]:
    authority = repository_root / forward_predecessor.FORMAL_AUTHORITY_RELATIVE_PATH_V1
    return (
        authority,
        authority.parent / forward_predecessor.FORMAL_COMPONENT_REGISTRY_FILENAME_V1,
        authority.parent / forward_predecessor.FORMAL_SOURCE_INVENTORY_FILENAME_V1,
        authority.parent / forward_predecessor.FORMAL_MANIFEST_FILENAME_V1,
    )


def _protected_file_snapshot(
    repository_root: Path, checkpoint_path: Path
) -> tuple[tuple[str, str], ...]:
    relative_paths = tuple(relative for relative, unused in _verify_bound_sources(repository_root))
    paths = tuple(repository_root / relative for relative in relative_paths)
    paths += _formal_artifact_paths(repository_root) + (checkpoint_path,)
    observations = tuple(
        (str(path.relative_to(repository_root)), single_step_predecessor._sha256_file(path))
        for path in paths
    )
    if len(observations) != len(set(name for name, unused in observations)):
        _fail("PROTECTED_FILE_SET_DUPLICATED")
    return observations


def _loss_weights_tuple(
    weights: CovapieCurrent11LossWeightsV1,
) -> tuple[tuple[str, float], ...]:
    return single_step_predecessor._loss_weights_tuple(weights)


def _validate_loss_policy(
    requested: object,
    *,
    published_default: CovapieCurrent11LossWeightsV1 | None = None,
) -> tuple[CovapieCurrent11LossWeightsV1, CovapieCurrent11LossWeightsV1]:
    try:
        published, candidate = single_step_predecessor._validate_loss_weight_policy(
            requested, published_default=published_default
        )
    except single_step_predecessor._SmokeInvariantError as error:
        _fail(error.reason)
    if candidate is not INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1:
        _fail("TRAINER_CANDIDATE_NOT_EXACT_PREDECESSOR_ALIAS")
    return published, candidate


def _validate_carrier(
    carrier: object,
) -> CovapieBatch001Train5TrainerBatchCarrierV1:
    if type(carrier) is not CovapieBatch001Train5TrainerBatchCarrierV1:
        _fail("TRAIN5_CARRIER_TYPE_INVALID")
    supervision = carrier.supervision
    if (
        type(carrier.model_input_batch) is not dict
        or not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
        or carrier.sample_identities != forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or carrier.scheduled_task_ids != (4, 4, 2, 0, 4)
        or carrier.epoch != forward_predecessor.TASK_SCHEDULE_EPOCH_V1
        or carrier.task_schedule_seed != forward_predecessor.TASK_SCHEDULE_SEED_V1
        or len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or len(supervision.sample_training_admitted) != 5
        or not bool(supervision.sample_training_admitted.all().item())
        or len(supervision.pair_candidate_batch_index) != 690
        or int(supervision.pair_candidate_is_positive.sum().item()) != 5
        or int(supervision.pair_candidate_is_negative.sum().item()) != 685
        or int(supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()) != 0
        or int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()) != 5
    ):
        _fail("TRAIN5_CARRIER_CONTRACT_INVALID")
    ligand_mask = carrier.model_input_batch.get("lig_mask")
    pocket_mask = carrier.model_input_batch.get("pocket_mask")
    if (
        not isinstance(ligand_mask, torch.Tensor)
        or not isinstance(pocket_mask, torch.Tensor)
        or len(ligand_mask) != 115
        or len(pocket_mask) != 578
    ):
        _fail("TRAIN5_CARRIER_MODEL_INPUT_INVALID")
    return carrier


def _carrier_from_prepared(
    prepared: forward_predecessor._PreparedTrain5BatchV1,
) -> CovapieBatch001Train5TrainerBatchCarrierV1:
    carrier = CovapieBatch001Train5TrainerBatchCarrierV1(
        model_input_batch=prepared.model_input_batch,
        supervision=prepared.supervision,
        sample_identities=prepared.sample_identities,
        scheduled_task_ids=prepared.scheduled_task_ids,
        epoch=forward_predecessor.TASK_SCHEDULE_EPOCH_V1,
        task_schedule_seed=forward_predecessor.TASK_SCHEDULE_SEED_V1,
    )
    return _validate_carrier(carrier)


def _all_nested_tensors(value: object) -> tuple[torch.Tensor, ...]:
    tensors: list[torch.Tensor] = []
    if isinstance(value, torch.Tensor):
        tensors.append(value)
    elif type(value) is dict:
        for item in value.values():
            tensors.extend(_all_nested_tensors(item))
    elif isinstance(value, CovapieCurrent11TrainingSupervisionTensorsV1):
        for field in fields(value):
            tensors.extend(_all_nested_tensors(getattr(value, field.name)))
    elif isinstance(value, CovapieBatch001Train5TrainerBatchCarrierV1):
        tensors.extend(_all_nested_tensors(value.model_input_batch))
        tensors.extend(_all_nested_tensors(value.supervision))
    return tuple(tensors)


def _tensor_snapshot(value: object) -> tuple[torch.Tensor, ...]:
    return tuple(tensor.detach().clone() for tensor in _all_nested_tensors(value))


def _tensor_snapshot_unchanged(
    before: Sequence[torch.Tensor], value: object
) -> bool:
    after = _all_nested_tensors(value)
    return len(before) == len(after) and all(
        single_step_predecessor._same_tensor(left, right)
        for left, right in zip(before, after)
    )


class _Train5BoundedTrainerAdapterV1(CovapieCurrent11TrainingLigandPocketDDPM):
    """Smoke-local carrier adapter; training-step and optimizer stay inherited."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.transfer_batch_to_device_call_count = 0
        self._bounded_last_forward_output: CovapieCurrent11TrainingForwardOutputV1 | None = None

    def transfer_batch_to_device(
        self, batch: object, device: torch.device, dataloader_idx: int
    ) -> CovapieBatch001Train5TrainerBatchCarrierV1:
        original = _validate_carrier(batch)
        if dataloader_idx != 0 or device.type != "cpu":
            _fail("TRAINER_TRANSFER_DEVICE_OR_INDEX_INVALID")
        self.transfer_batch_to_device_call_count += 1
        parent_transfer = super().transfer_batch_to_device
        model_input = parent_transfer(original.model_input_batch, device, dataloader_idx)
        if type(model_input) is not dict:
            _fail("MODEL_INPUT_TRANSFER_RESULT_INVALID")
        model_input = dict(model_input)
        values: dict[str, torch.Tensor] = {}
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
            transferred = parent_transfer(
                getattr(original.supervision, field.name), device, dataloader_idx
            )
            if not isinstance(transferred, torch.Tensor):
                _fail("SUPERVISION_TRANSFER_RESULT_INVALID")
            values[field.name] = transferred
        transferred_carrier = CovapieBatch001Train5TrainerBatchCarrierV1(
            model_input_batch=model_input,
            supervision=CovapieCurrent11TrainingSupervisionTensorsV1(**values),
            sample_identities=original.sample_identities,
            scheduled_task_ids=original.scheduled_task_ids,
            epoch=original.epoch,
            task_schedule_seed=original.task_schedule_seed,
        )
        return _validate_carrier(transferred_carrier)

    def forward(self, data: object) -> CovapieCurrent11TrainingForwardOutputV1:
        carrier = _validate_carrier(data)
        if (
            self.training is not True
            or carrier.epoch != int(self.current_epoch)
            or carrier.task_schedule_seed != self.covapie_current11_task_schedule_seed
        ):
            _fail("TRAIN5_FORWARD_LIFECYCLE_INVALID")
        ligand, pocket = self.get_ligand_and_pocket(carrier.model_input_batch)
        supervision = carrier.supervision
        indicator = supervision.target_residue_reactive_atom_mask
        if indicator.shape != (len(pocket["x"]), 1) or indicator.dtype != torch.bool:
            _fail("TARGET_RESIDUE_INDICATOR_INVALID")
        role_delta = self.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=ligand["mask"],
        )
        trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
            ddpm=self.ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
            pocket_target_residue_atom_condition_indicator=indicator[:, 0],
        )
        model_output = self.covapie_current11_auxiliary_model_v1(
            diffusion_trace=trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )
        losses = compute_covapie_current11_training_losses_v1(
            model_output=model_output,
            supervision=supervision,
            diffusion_trace=trace,
            loss_weights=self.covapie_current11_loss_weights,
            pair_contrastive_temperature=self.covapie_current11_pair_contrastive_temperature,
            geometry_smooth_l1_beta=1.0,
        )
        result = CovapieCurrent11TrainingForwardOutputV1(
            model_output=model_output,
            loss_output=losses,
            supervision=supervision,
            diffusion_trace=trace,
        )
        self._bounded_last_forward_output = result
        return result


class _Train5BoundedTrainerCompatibilityAdapterV1(_Train5BoundedTrainerAdapterV1):
    """Only active-Lightning legacy-hook compatibility; math is unchanged."""

    validation_epoch_end = None

    def configure_gradient_clipping(
        self, optimizer: torch.optim.Optimizer, *args: object, **kwargs: object
    ) -> None:
        del optimizer
        if set(kwargs) - {
            "optimizer_idx", "gradient_clip_val", "gradient_clip_algorithm"
        }:
            _fail("GRADIENT_CLIPPING_COMPATIBILITY_SIGNATURE_INVALID")
        optimizer_idx_supplied = "optimizer_idx" in kwargs
        optimizer_idx = kwargs.get("optimizer_idx")
        clip_value = kwargs.get("gradient_clip_val")
        clip_algorithm = kwargs.get("gradient_clip_algorithm")
        if len(args) == 2 and not kwargs:
            clip_value, clip_algorithm = args
        elif len(args) == 3 and not kwargs:
            optimizer_idx, clip_value, clip_algorithm = args
            optimizer_idx_supplied = True
        elif len(args) == 1 and type(args[0]) is int and not kwargs:
            optimizer_idx = args[0]
            optimizer_idx_supplied = True
        elif args:
            _fail("GRADIENT_CLIPPING_COMPATIBILITY_SIGNATURE_INVALID")
        if (
            optimizer_idx_supplied
            and (type(optimizer_idx) is not int or optimizer_idx != 0)
        ):
            _fail("GRADIENT_CLIPPING_OPTIMIZER_INDEX_INVALID")
        if clip_value is not None or clip_algorithm is not None:
            _fail("GRADIENT_CLIPPING_MUST_REMAIN_DISABLED")


def _instantiate_model(
    *,
    owner: type[_Train5BoundedTrainerAdapterV1],
    repository_root: Path,
    state_root: Path,
    legacy_setup_data_root: Path,
    output_root: Path,
    loss_weights: CovapieCurrent11LossWeightsV1,
) -> _Train5BoundedTrainerAdapterV1:
    preview = instantiation_owner.load_config_preview_v0(
        repository_root / instantiation_owner.CONFIG_PREVIEW_PATH
    )
    compatible = instantiation_owner.build_checkpoint_compatible_config_v0(
        preview["preview"], repository_root / instantiation_owner.BEST_CONFIG_CANDIDATE_PATH
    )
    config = instantiation_owner._constructor_config_from_compatible_config(
        compatible, instantiation_owner._DATASET_NAME_V1, "cpu"
    )
    config["batch_size"] = 5
    kwargs = instantiation_owner._constructor_kwargs(config)
    kwargs.update({
        "outdir": output_root,
        "datadir": str(legacy_setup_data_root),
        "target_residue_atom_conditioning": True,
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(repository_root),
        "covapie_state_root": str(state_root),
        "covapie_current11_training_enabled": True,
        "covapie_current11_task_schedule_seed": 0,
        "covapie_current11_pair_contrastive_temperature": 1.0,
        "covapie_current11_loss_weights": loss_weights,
    })
    torch.random.default_generator.manual_seed(
        forward_predecessor.MODEL_INITIALIZATION_SEED_V1
    )
    previous = instantiation_owner.constants.dataset_params.get(
        instantiation_owner._DATASET_NAME_V1
    )
    instantiation_owner.constants.dataset_params[
        instantiation_owner._DATASET_NAME_V1
    ] = instantiation_owner._temporary_10d_dataset_info()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = owner(**kwargs)
    finally:
        if previous is None:
            instantiation_owner.constants.dataset_params.pop(
                instantiation_owner._DATASET_NAME_V1, None
            )
        else:
            instantiation_owner.constants.dataset_params[
                instantiation_owner._DATASET_NAME_V1
            ] = previous
    model = model.to(torch.device("cpu"))
    dynamics = model.ddpm.dynamics
    if (
        type(model) is not owner
        or model.batch_size != 5
        or model.automatic_optimization is not True
        or len(model.state_dict()) != 141
        or model.covapie_current11_loss_weights != loss_weights
        or model.mode != "pocket_conditioning"
        or model.pocket_representation != "full-atom"
        or model.atom_nf != 10
        or dynamics.target_residue_atom_conditioning is not True
        or model.virtual_nodes is not False
        or model.ddpm.loss_type != "l2"
        or model.covapie_current11_auxiliary_model_v1.joint_nf != 32
        or dynamics.egnn.hidden_nf != 128
        or dynamics.egnn.n_layers != 5
    ):
        _fail("REAL_MODEL_CONFIGURATION_INVALID")
    return model


class _SingleTrain5DatasetV1(Dataset[CovapieBatch001Train5TrainerBatchCarrierV1]):
    def __init__(self, carrier: CovapieBatch001Train5TrainerBatchCarrierV1) -> None:
        self.carrier = _validate_carrier(carrier)
        self.getitem_call_count = 0

    def __len__(self) -> int:
        return 1

    def __getitem__(self, index: int) -> CovapieBatch001Train5TrainerBatchCarrierV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        self.getitem_call_count += 1
        if self.getitem_call_count > 1:
            _fail("SECOND_DATASET_ITEM_REQUESTED")
        return self.carrier


class _SingleTrain5CollatorV1:
    def __init__(self, carrier: CovapieBatch001Train5TrainerBatchCarrierV1) -> None:
        self.carrier = carrier
        self.call_count = 0

    def __call__(
        self, rows: list[CovapieBatch001Train5TrainerBatchCarrierV1]
    ) -> CovapieBatch001Train5TrainerBatchCarrierV1:
        self.call_count += 1
        if self.call_count > 1 or len(rows) != 1 or rows[0] is not self.carrier:
            _fail("COLLATOR_EXACT_SINGLE_CARRIER_INVALID")
        return _validate_carrier(rows[0])


class _Train5DataModuleV1(pl.LightningDataModule):
    def __init__(self, carrier: CovapieBatch001Train5TrainerBatchCarrierV1) -> None:
        super().__init__()
        self.carrier = carrier
        self.dataset = _SingleTrain5DatasetV1(carrier)
        self.collator = _SingleTrain5CollatorV1(carrier)
        self.loader: DataLoader | None = None
        self.setup_fit_call_count = 0
        self.train_dataloader_call_count = 0
        self.before_batch_transfer_call_count = 0
        self.after_batch_transfer_call_count = 0
        self.transferred_batch_rebuilt = False
        self.transferred_metadata_unchanged = False
        self.transferred_tensors_on_cpu = False

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("DATAMODULE_SETUP_STAGE_INVALID")
        self.setup_fit_call_count += 1
        if self.setup_fit_call_count > 1:
            _fail("DATAMODULE_SETUP_FIT_CALLED_MORE_THAN_ONCE")

    def train_dataloader(self) -> DataLoader:
        self.train_dataloader_call_count += 1
        if self.train_dataloader_call_count > 1:
            _fail("TRAIN_DATALOADER_CALLED_MORE_THAN_ONCE")
        self.loader = DataLoader(
            self.dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=self.collator,
        )
        if (
            len(self.loader) != 1
            or self.loader.batch_size != 1
            or type(self.loader.sampler) is not SequentialSampler
            or self.loader.num_workers != 0
            or self.loader.drop_last is not False
            or self.loader.pin_memory is not False
            or self.loader.persistent_workers is not False
        ):
            _fail("DATALOADER_CONFIGURATION_INVALID")
        return self.loader

    def val_dataloader(self) -> None:
        return None

    def test_dataloader(self) -> None:
        return None

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> CovapieBatch001Train5TrainerBatchCarrierV1:
        self.before_batch_transfer_call_count += 1
        if (
            self.before_batch_transfer_call_count > 1
            or batch is not self.carrier
            or dataloader_idx != 0
        ):
            _fail("BEFORE_BATCH_TRANSFER_CONTRACT_INVALID")
        return _validate_carrier(batch)

    def on_after_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> CovapieBatch001Train5TrainerBatchCarrierV1:
        self.after_batch_transfer_call_count += 1
        transferred = _validate_carrier(batch)
        self.transferred_batch_rebuilt = (
            transferred is not self.carrier
            and transferred.model_input_batch is not self.carrier.model_input_batch
            and transferred.supervision is not self.carrier.supervision
        )
        self.transferred_metadata_unchanged = (
            transferred.sample_identities is self.carrier.sample_identities
            and transferred.scheduled_task_ids is self.carrier.scheduled_task_ids
            and transferred.epoch == self.carrier.epoch
            and transferred.task_schedule_seed == self.carrier.task_schedule_seed
        )
        tensors = _all_nested_tensors(transferred)
        self.transferred_tensors_on_cpu = bool(tensors) and all(
            tensor.device.type == "cpu" for tensor in tensors
        )
        if (
            self.after_batch_transfer_call_count > 1
            or dataloader_idx != 0
            or not self.transferred_batch_rebuilt
            or not self.transferred_metadata_unchanged
            or not self.transferred_tensors_on_cpu
        ):
            _fail("AFTER_BATCH_TRANSFER_CONTRACT_INVALID")
        return transferred


class _TrainerObserverV1(pl.Callback):
    def __init__(
        self,
        *,
        original_carrier: CovapieBatch001Train5TrainerBatchCarrierV1,
        checkpoint_state: Mapping[str, torch.Tensor],
    ) -> None:
        super().__init__()
        self.original_carrier = original_carrier
        self.checkpoint_state = checkpoint_state
        self.fit_start_count = 0
        self.train_batch_start_count = 0
        self.train_batch_end_count = 0
        self.before_backward_count = 0
        self.after_backward_count = 0
        self.before_optimizer_step_count = 0
        self.before_zero_grad_count = 0
        self.validation_batch_count = 0
        self.test_batch_count = 0
        self.diffusion_seed_hook_call_count = 0
        self.metrics: tuple[tuple[str, float], ...] | None = None
        self.runtime_losses: tuple[tuple[str, float], ...] | None = None
        self.weighted_formula = 0.0
        self.weighted_formula_difference = 0.0
        self.diffusion_timesteps: tuple[int, ...] = ()
        self.optimizer_metadata = None
        self.gradient_group_stats = ()
        self.geometry_component_gradient = None
        self.process_control_exception: BaseException | None = None

    def on_fit_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        del trainer, pl_module
        self.fit_start_count += 1

    def on_train_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
    ) -> None:
        del trainer
        self.train_batch_start_count += 1
        if self.train_batch_start_count > 1:
            _fail("SECOND_TRAIN_BATCH_REJECTED")
        carrier = _validate_carrier(batch)
        model_device = next(pl_module.parameters()).device
        if (
            batch_idx != 0
            or pl_module.training is not True
            or int(pl_module.current_epoch) != 0
            or carrier is self.original_carrier
            or any(tensor.device != model_device for tensor in _all_nested_tensors(carrier))
        ):
            _fail("TRAIN_BATCH_START_CONTRACT_INVALID")
        torch.random.default_generator.manual_seed(
            forward_predecessor.DIFFUSION_FORWARD_SEED_V1
        )
        self.diffusion_seed_hook_call_count += 1

    def on_before_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule, loss: torch.Tensor
    ) -> None:
        del trainer, pl_module
        self.before_backward_count += 1
        if (
            self.before_backward_count > 1
            or loss.ndim != 0
            or not loss.requires_grad
            or not bool(torch.isfinite(loss).item())
        ):
            _fail("AUTOMATIC_BACKWARD_INPUT_INVALID")

    def on_after_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer, pl_module
        self.after_backward_count += 1
        if self.after_backward_count > 1:
            _fail("SECOND_AUTOMATIC_BACKWARD_REJECTED")

    def on_before_optimizer_step(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
        optimizer_idx: int | None = None,
    ) -> None:
        del trainer
        self.before_optimizer_step_count += 1
        if (
            self.before_optimizer_step_count > 1
            or (optimizer_idx is not None and optimizer_idx != 0)
        ):
            _fail("SECOND_OR_INVALID_OPTIMIZER_STEP_REJECTED")
        self.optimizer_metadata = single_step_predecessor._validate_optimizer_parameter_coverage(
            pl_module, optimizer
        )
        named = dict(pl_module.named_parameters())
        shared_names = tuple(name for name in named if name in self.checkpoint_state)
        target_names = (single_step_predecessor.TARGET_RESIDUE_PARAMETER_NAME_V1,)
        role_names = single_step_predecessor._names_with_prefixes(
            named, single_step_predecessor.ROLE_TASK_MASK_ANCHOR_PREFIXES_V1
        )
        pair_names = single_step_predecessor._names_with_prefixes(
            named, single_step_predecessor.PAIR_HEAD_PREFIXES_V1
        )
        geometry_names = single_step_predecessor._names_with_prefixes(
            named, single_step_predecessor.GEOMETRY_HEAD_PREFIX_V1
        )
        specifications = (
            ("ALL_PARAMETERS", tuple(named), "GLOBAL_GRADIENT_GATE_FAILED"),
            ("SHARED_PRETRAINED", shared_names, "SHARED_GRADIENT_GATE_FAILED"),
            ("TARGET_RESIDUE_CONDITIONING", target_names, "TARGET_GRADIENT_GATE_FAILED"),
            ("ROLE_TASK_MASK_ANCHOR", role_names, "ROLE_GRADIENT_GATE_FAILED"),
            ("PAIR_HEAD", pair_names, "PAIR_GRADIENT_GATE_FAILED"),
            ("GEOMETRY_HEAD", geometry_names, "GEOMETRY_GRADIENT_GATE_FAILED"),
        )
        observations = []
        for group, names, reason in specifications:
            stats = single_step_predecessor._gradient_group_stats(
                group_name=group, named_parameters=named, parameter_names=names
            )
            single_step_predecessor._require_gradient_gate(stats, reason=reason)
            observations.append(stats)
        self.gradient_group_stats = tuple(observations)
        self.geometry_component_gradient = single_step_predecessor._geometry_component_gradient(
            named
        )

    def on_before_zero_grad(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
    ) -> None:
        del trainer, pl_module, optimizer
        self.before_zero_grad_count += 1
        if self.before_zero_grad_count > 1:
            _fail("SECOND_ZERO_GRAD_LIFECYCLE_REJECTED")

    def on_train_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: object,
        batch: object,
        batch_idx: int,
    ) -> None:
        del trainer, batch
        self.train_batch_end_count += 1
        if (
            self.train_batch_end_count > 1
            or batch_idx != 0
            or type(outputs) is not dict
            or frozenset(outputs) != EXPECTED_METRIC_KEYS_V1
            or any(
                not isinstance(value, torch.Tensor)
                or not bool(torch.isfinite(value).all().item())
                for value in outputs.values()
            )
        ):
            _fail("TRAINING_STEP_METRICS_INVALID")
        self.metrics = tuple(
            (name, float(outputs[name].detach().item()))
            for name in (
                "loss", "loss_base_diffusion", "loss_covalent_pair_prediction",
                "loss_pre_post_geometry", "loss_covalent_pair_contrastive",
            )
        )
        forward = getattr(pl_module, "_bounded_last_forward_output", None)
        if not isinstance(forward, CovapieCurrent11TrainingForwardOutputV1):
            _fail("TRAINING_FORWARD_OBSERVATION_MISSING")
        losses, formula, difference = single_step_predecessor._validate_finite_loss_contract(
            forward.loss_output,
            forward.supervision,
            pl_module.covapie_current11_loss_weights,
        )
        self.runtime_losses = losses
        self.weighted_formula = formula
        self.weighted_formula_difference = difference
        self.diffusion_timesteps = tuple(
            forward.model_output.diffusion_timestep_int.tolist()
        )

    def on_validation_batch_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule,
        batch: object, batch_idx: int, dataloader_idx: int = 0,
    ) -> None:
        del trainer, pl_module, batch, batch_idx, dataloader_idx
        self.validation_batch_count += 1
        _fail("VALIDATION_MUST_REMAIN_DISABLED")

    def on_test_batch_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule,
        batch: object, batch_idx: int, dataloader_idx: int = 0,
    ) -> None:
        del trainer, pl_module, batch, batch_idx, dataloader_idx
        self.test_batch_count += 1
        _fail("TEST_MUST_REMAIN_DISABLED")

    def on_exception(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule,
        exception: BaseException,
    ) -> None:
        del trainer, pl_module
        if isinstance(exception, (KeyboardInterrupt, SystemExit)):
            self.process_control_exception = exception


@dataclass(frozen=True)
class _FitRuntimeV1:
    trainer: pl.Trainer
    datamodule: _Train5DataModuleV1
    observer: _TrainerObserverV1
    trainer_api_family: str
    sampler_control_parameter: str
    precision_argument: object
    trainer_kwargs: dict[str, object]


def _trainer_configuration_for_signature(
    *, signature: inspect.Signature, callbacks: list[pl.Callback], root: Path
) -> tuple[dict[str, object], dict[str, object]]:
    parameters = set(signature.parameters) - {"self"}
    required = {
        "accelerator", "devices", "num_nodes", "precision", "max_epochs",
        "min_epochs", "max_steps", "limit_train_batches", "limit_val_batches",
        "limit_test_batches", "num_sanity_val_steps", "enable_checkpointing",
        "callbacks", "logger", "gradient_clip_val", "accumulate_grad_batches",
        "deterministic", "enable_progress_bar", "default_root_dir",
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
        "accelerator": "cpu", "devices": 1, "num_nodes": 1,
        "precision": precision, "max_epochs": 1, "min_epochs": 1,
        "max_steps": 1, "limit_train_batches": 1, "limit_val_batches": 0,
        "limit_test_batches": 0, "num_sanity_val_steps": 0,
        "enable_checkpointing": False, "callbacks": callbacks, "logger": False,
        "gradient_clip_val": None, "accumulate_grad_batches": 1,
        "deterministic": True, "enable_progress_bar": False,
        "default_root_dir": root, sampler: False,
    }
    optional = {
        "check_val_every_n_epoch": 1, "val_check_interval": 1.0,
        "gradient_clip_algorithm": None, "benchmark": False,
        "reload_dataloaders_every_n_epochs": 0, "sync_batchnorm": False,
        "enable_model_summary": False, "log_every_n_steps": 1,
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
        kwargs[name] for name in ("use_distributed_sampler", "replace_sampler_ddp")
        if name in kwargs
    )
    if (
        kwargs.get("accelerator") != "cpu"
        or kwargs.get("devices") != 1
        or kwargs.get("num_nodes") != 1
        or kwargs.get("max_epochs") != 1
        or kwargs.get("min_epochs") != 1
        or kwargs.get("max_steps") != 1
        or kwargs.get("limit_train_batches") != 1
        or kwargs.get("limit_val_batches") != 0
        or kwargs.get("limit_test_batches") != 0
        or kwargs.get("num_sanity_val_steps") != 0
        or kwargs.get("enable_checkpointing") is not False
        or kwargs.get("logger") is not False
        or kwargs.get("gradient_clip_val") is not None
        or kwargs.get("accumulate_grad_batches") != 1
        or kwargs.get("deterministic") is not True
        or kwargs.get("enable_progress_bar") is not False
        or sampler_values != (False,)
        or kwargs.get("profiler", None) is not None
    ):
        _fail("TRAINER_CONFIGURATION_NOT_EXACT_BOUNDED_CPU")


def _build_fit_runtime(
    *, carrier: CovapieBatch001Train5TrainerBatchCarrierV1,
    checkpoint_state: Mapping[str, torch.Tensor], root: Path,
) -> _FitRuntimeV1:
    observer = _TrainerObserverV1(
        original_carrier=carrier, checkpoint_state=checkpoint_state
    )
    datamodule = _Train5DataModuleV1(carrier)
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
        or trainer.max_steps != 1
        or trainer.limit_train_batches != 1
        or trainer.limit_val_batches != 0
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


def _invoke_fit(model: pl.LightningModule, runtime: _FitRuntimeV1) -> None:
    previous_handler = signal.getsignal(signal.SIGINT)
    try:
        runtime.trainer.fit(model=model, datamodule=runtime.datamodule, ckpt_path=None)
    except SystemExit:
        if isinstance(runtime.observer.process_control_exception, KeyboardInterrupt):
            raise runtime.observer.process_control_exception
        raise
    finally:
        if signal.getsignal(signal.SIGINT) is not previous_handler:
            signal.signal(signal.SIGINT, previous_handler)


def _migration_and_architecture(
    *, model: _Train5BoundedTrainerAdapterV1,
    checkpoint_state: Mapping[str, torch.Tensor],
) -> tuple[dict[str, object], tuple[tuple[str, object], ...]]:
    migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model, checkpoint_state_dict=checkpoint_state
    )
    expected = {
        "checkpoint_key_count": 122, "target_model_key_count": 141,
        "shared_key_count": 122, "target_only_key_count": 19,
        "checkpoint_only_key_count": 0, "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": 122,
    }
    if (
        any(int(migration[name]) != value for name, value in expected.items())
        or migration["full_target_strict_load"] is not True
        or migration["migration_missing_keys"] != ()
        or migration["migration_unexpected_keys"] != ()
    ):
        _fail("CHECKPOINT_MIGRATION_CONTRACT_INVALID")
    dynamics = model.ddpm.dynamics
    architecture = (
        ("device", "cpu"), ("mode", model.mode),
        ("pocket_representation", model.pocket_representation),
        ("atom_nf", model.atom_nf),
        ("target_residue_atom_conditioning", dynamics.target_residue_atom_conditioning),
        ("virtual_nodes", model.virtual_nodes), ("loss_type", model.ddpm.loss_type),
        ("joint_nf", model.covapie_current11_auxiliary_model_v1.joint_nf),
        ("hidden_nf", dynamics.egnn.hidden_nf), ("egnn_layers", dynamics.egnn.n_layers),
    )
    if dict(architecture) != {
        "device": "cpu", "mode": "pocket_conditioning",
        "pocket_representation": "full-atom", "atom_nf": 10,
        "target_residue_atom_conditioning": True, "virtual_nodes": False,
        "loss_type": "l2", "joint_nf": 32, "hidden_nf": 128, "egnn_layers": 5,
    }:
        _fail("ARCHITECTURE_CONTRACT_INVALID")
    return migration, architecture


def _parameter_groups(
    model: torch.nn.Module,
    checkpoint_state: Mapping[str, torch.Tensor],
    migration: Mapping[str, object],
) -> tuple[tuple[str, tuple[str, ...], str], ...]:
    named = dict(model.named_parameters())
    shared = tuple(name for name in named if name in checkpoint_state)
    new = tuple(sorted(
        set(migration["target_only_exact_keys"])
        | set(migration["target_only_auxiliary_keys"])
    ))
    target = (single_step_predecessor.TARGET_RESIDUE_PARAMETER_NAME_V1,)
    role = single_step_predecessor._names_with_prefixes(
        named, single_step_predecessor.ROLE_TASK_MASK_ANCHOR_PREFIXES_V1
    )
    pair = single_step_predecessor._names_with_prefixes(
        named, single_step_predecessor.PAIR_HEAD_PREFIXES_V1
    )
    geometry = single_step_predecessor._names_with_prefixes(
        named, single_step_predecessor.GEOMETRY_HEAD_PREFIX_V1
    )
    if (
        len(named) != 135 or len(shared) != 116 or len(new) != 19
        or set(shared) & set(new) or set(shared) | set(new) != set(named)
    ):
        _fail("PARAMETER_GROUP_DOMAIN_INVALID")
    return (
        ("ALL_PARAMETERS", tuple(named), "GLOBAL_PARAMETER_DELTA_GATE_FAILED"),
        ("SHARED_PRETRAINED", shared, "SHARED_PARAMETER_DELTA_GATE_FAILED"),
        ("NEW_COVAPIE", new, "NEW_PARAMETER_DELTA_GATE_FAILED"),
        ("TARGET_RESIDUE_CONDITIONING", target, "TARGET_PARAMETER_DELTA_GATE_FAILED"),
        ("ROLE_TASK_MASK_ANCHOR", role, "ROLE_PARAMETER_DELTA_GATE_FAILED"),
        ("PAIR_HEAD", pair, "PAIR_PARAMETER_DELTA_GATE_FAILED"),
        ("GEOMETRY_HEAD", geometry, "GEOMETRY_PARAMETER_DELTA_GATE_FAILED"),
    )


def _capture_pre_optimizer_step_parameter_snapshot_v1(
    model: torch.nn.Module,
    *,
    branch: str,
    trainer_global_step: int,
    optimizer_step_count: int,
) -> _PreOptimizerStepParameterSnapshotV1:
    if (
        branch not in ("direct_success", "compatibility_fallback")
        or trainer_global_step != 0
        or optimizer_step_count != 0
    ):
        _fail("PARAMETER_SNAPSHOT_NOT_CAPTURED_BEFORE_OPTIMIZER_STEP")
    tensors, unused_metadata = single_step_predecessor._parameter_snapshot(
        dict(model.named_parameters())
    )
    del unused_metadata
    return _PreOptimizerStepParameterSnapshotV1(
        branch=branch,
        model_identity=id(model),
        trainer_global_step_at_capture=trainer_global_step,
        optimizer_step_count_at_capture=optimizer_step_count,
        tensors=tensors,
    )


def _parameter_before_from_pre_optimizer_step_snapshot_v1(
    snapshot: object,
    *,
    trained_model: torch.nn.Module,
    expected_branch: str,
) -> dict[str, torch.Tensor]:
    named = dict(trained_model.named_parameters())
    if (
        type(snapshot) is not _PreOptimizerStepParameterSnapshotV1
        or snapshot.branch != expected_branch
        or snapshot.model_identity != id(trained_model)
        or snapshot.trainer_global_step_at_capture != 0
        or snapshot.optimizer_step_count_at_capture != 0
        or tuple(snapshot.tensors) != tuple(named)
    ):
        _fail("PARAMETER_DELTA_PRE_STEP_SNAPSHOT_INVALID")
    return snapshot.tensors


def _select_trained_pre_optimizer_step_snapshot_v1(
    *,
    compatibility_used: bool,
    direct_snapshot: _PreOptimizerStepParameterSnapshotV1,
    compatibility_snapshot: _PreOptimizerStepParameterSnapshotV1 | None,
) -> _PreOptimizerStepParameterSnapshotV1:
    if type(compatibility_used) is not bool:
        _fail("PARAMETER_DELTA_SNAPSHOT_BRANCH_INVALID")
    selected = compatibility_snapshot if compatibility_used else direct_snapshot
    expected_branch = (
        "compatibility_fallback" if compatibility_used else "direct_success"
    )
    if (
        type(selected) is not _PreOptimizerStepParameterSnapshotV1
        or selected.branch != expected_branch
    ):
        _fail("PARAMETER_DELTA_SNAPSHOT_BRANCH_INVALID")
    return selected


def _run_impl(
    *, repository_root: Path, state_root: Path, cache_root: Path,
    checkpoint_path: Path, loss_weights: object,
) -> CovapieBatch001Train5BoundedTrainerFitSmokeResultV1:
    started = time.perf_counter()
    git_before = _git_snapshot(repository_root)
    bound_before = _verify_bound_sources(repository_root)
    checkpoint_before = forward_predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
        checkpoint_path=checkpoint_path
    )
    protected_before = _protected_file_snapshot(repository_root, checkpoint_path)
    state_before = trainer_reference._state_integrity_snapshot_v1(state_root)
    raw_before = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    published_default, candidate = _validate_loss_policy(loss_weights)

    prepared = forward_predecessor._prepare_train5_batch(
        repository_root=repository_root,
        cache_root=cache_root,
        requested_sample_identities=None,
    )
    carrier = _carrier_from_prepared(prepared)
    model_input_before = _tensor_snapshot(carrier.model_input_batch)
    supervision_before = _tensor_snapshot(carrier.supervision)
    manual_reference = (
        single_step_predecessor
        .run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
            repository_root=repository_root,
            state_root=state_root,
            cache_root=cache_root,
            checkpoint_path=checkpoint_path,
            smoke_loss_weights=candidate,
        )
    )
    checkpoint_payload = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    checkpoint_state = checkpoint_payload["state_dict"]
    if not isinstance(checkpoint_state, Mapping) or len(checkpoint_state) != 122:
        _fail("CHECKPOINT_STATE_DOMAIN_INVALID")

    temporary_path: Path | None = None
    direct_rejection: str | None = None
    compatibility_used = False
    direct_global_step = 0
    direct_getitem_count = 0
    direct_train_start_count = 0
    direct_parameters_unchanged = True
    with tempfile.TemporaryDirectory(
        prefix="covapie_batch001_train5_bounded_trainer_fit_smoke_"
    ) as temporary:
        temporary_path = Path(temporary)
        normalized_repository = temporary_path / "normalized_repository"
        trainer_reference.mixed_scheduler._clone_head_v1(
            repository_root, normalized_repository
        )
        legacy_setup_data = temporary_path / "legacy_setup_data"
        legacy_setup_data.mkdir(mode=0o700)
        formal_carrier = state_root / instantiation_owner._FORMAL_CARRIER_RELATIVE_PATH_V1
        for split in ("train", "val"):
            (legacy_setup_data / f"{split}.npz").symlink_to(formal_carrier)
        with forward_predecessor._deterministic_cpu_context():
            direct_model = _instantiate_model(
                owner=_Train5BoundedTrainerAdapterV1,
                repository_root=normalized_repository,
                state_root=state_root,
                legacy_setup_data_root=legacy_setup_data,
                output_root=temporary_path / "direct_model_output",
                loss_weights=candidate,
            )
            direct_migration, direct_architecture = _migration_and_architecture(
                model=direct_model, checkpoint_state=checkpoint_state
            )
            direct_runtime = _build_fit_runtime(
                carrier=carrier,
                checkpoint_state=checkpoint_state,
                root=temporary_path / "direct_probe",
            )
            direct_pre_step_snapshot = (
                _capture_pre_optimizer_step_parameter_snapshot_v1(
                    direct_model,
                    branch="direct_success",
                    trainer_global_step=int(direct_runtime.trainer.global_step),
                    optimizer_step_count=(
                        direct_runtime.observer.before_optimizer_step_count
                    ),
                )
            )
            compatibility_pre_step_snapshot = None
            try:
                _invoke_fit(direct_model, direct_runtime)
            except NotImplementedError as error:
                if "validation_epoch_end" not in str(error):
                    raise
                compatibility_used = True
                direct_rejection = str(error)
                direct_global_step = int(direct_runtime.trainer.global_step)
                direct_getitem_count = direct_runtime.datamodule.dataset.getitem_call_count
                direct_train_start_count = direct_runtime.observer.train_batch_start_count
                direct_parameters_unchanged = all(
                    torch.equal(
                        parameter.detach(), direct_pre_step_snapshot.tensors[name]
                    )
                    for name, parameter in direct_model.named_parameters()
                )
                if (
                    direct_global_step != 0
                    or direct_getitem_count != 0
                    or direct_train_start_count != 0
                    or not direct_parameters_unchanged
                ):
                    _fail("DIRECT_COMPATIBILITY_REJECTION_NOT_PRE_TRAIN")

            if compatibility_used:
                model = _instantiate_model(
                    owner=_Train5BoundedTrainerCompatibilityAdapterV1,
                    repository_root=normalized_repository,
                    state_root=state_root,
                    legacy_setup_data_root=legacy_setup_data,
                    output_root=temporary_path / "compatibility_model_output",
                    loss_weights=candidate,
                )
                migration, architecture = _migration_and_architecture(
                    model=model, checkpoint_state=checkpoint_state
                )
                direct_state = direct_model.state_dict()
                compatibility_state = model.state_dict()
                if tuple(direct_state) != tuple(compatibility_state) or any(
                    not torch.equal(direct_state[name], compatibility_state[name])
                    for name in direct_state
                ):
                    _fail("COMPATIBILITY_MODEL_STATE_PARITY_FAILED")
                runtime = _build_fit_runtime(
                    carrier=carrier,
                    checkpoint_state=checkpoint_state,
                    root=temporary_path / "actual_fit",
                )
                compatibility_pre_step_snapshot = (
                    _capture_pre_optimizer_step_parameter_snapshot_v1(
                        model,
                        branch="compatibility_fallback",
                        trainer_global_step=int(runtime.trainer.global_step),
                        optimizer_step_count=(
                            runtime.observer.before_optimizer_step_count
                        ),
                    )
                )
                _invoke_fit(model, runtime)
            else:
                model = direct_model
                migration = direct_migration
                architecture = direct_architecture
                runtime = direct_runtime

            trained_pre_step_snapshot = (
                _select_trained_pre_optimizer_step_snapshot_v1(
                    compatibility_used=compatibility_used,
                    direct_snapshot=direct_pre_step_snapshot,
                    compatibility_snapshot=compatibility_pre_step_snapshot,
                )
            )

            named = dict(model.named_parameters())
            snapshot_branch = (
                "compatibility_fallback" if compatibility_used else "direct_success"
            )
            parameter_before = (
                _parameter_before_from_pre_optimizer_step_snapshot_v1(
                    trained_pre_step_snapshot,
                    trained_model=model,
                    expected_branch=snapshot_branch,
                )
            )
            groups = _parameter_groups(model, checkpoint_state, migration)

            observer = runtime.observer
            datamodule = runtime.datamodule
            trainer = runtime.trainer
            delta_observations = []
            for group_name, names, reason in groups:
                stats = single_step_predecessor._parameter_delta_group_stats(
                    group_name=group_name,
                    named_parameters=named,
                    parameter_names=names,
                    before=parameter_before,
                )
                single_step_predecessor._require_delta_gate(stats, reason=reason)
                delta_observations.append(stats)
            delta_stats = tuple(delta_observations)
            all_parameters_finite = all(
                bool(torch.isfinite(parameter).all().item())
                for parameter in named.values()
            )
            changed_count = sum(
                not torch.equal(parameter.detach(), parameter_before[name])
                for name, parameter in named.items()
            )

    if temporary_path is None or temporary_path.exists():
        _fail("TEMPORARY_TRAINER_ROOT_NOT_REMOVED")
    if not _tensor_snapshot_unchanged(model_input_before, carrier.model_input_batch):
        _fail("ORIGINAL_MODEL_INPUT_MUTATED")
    if not _tensor_snapshot_unchanged(supervision_before, carrier.supervision):
        _fail("ORIGINAL_SUPERVISION_MUTATED")
    protected_after = _protected_file_snapshot(repository_root, checkpoint_path)
    state_after = trainer_reference._state_integrity_snapshot_v1(state_root)
    raw_after = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    checkpoint_after = forward_predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
        checkpoint_path=checkpoint_path
    )
    git_after = _git_snapshot(repository_root)
    trainer_reference._assert_protected_state_unchanged_v1(
        state_before["protected_state_fingerprint"],
        state_after["protected_state_fingerprint"],
    )
    trainer_reference._assert_external_state_ownership_stable_v1(state_before, state_after)
    if (
        bound_before != _verify_bound_sources(repository_root)
        or protected_before != protected_after
        or raw_before != raw_after
        or checkpoint_before != checkpoint_after
        or git_before != git_after
    ):
        _fail("CHECKPOINT_PROTECTED_RAW_OR_GIT_STATE_CHANGED")
    if (
        model.covapie_current11_loss_weights != candidate
        or CovapieCurrent11LossWeightsV1() != published_default
    ):
        _fail("PUBLISHED_DEFAULT_OR_INSTANCE_CANDIDATE_CHANGED")
    if (
        observer.fit_start_count != 1
        or observer.train_batch_start_count != 1
        or observer.train_batch_end_count != 1
        or observer.before_backward_count != 1
        or observer.after_backward_count != 1
        or observer.before_optimizer_step_count != 1
        or observer.before_zero_grad_count != 1
        or observer.diffusion_seed_hook_call_count != 1
        or trainer.global_step != 1
        or model.automatic_optimization is not True
        or datamodule.setup_fit_call_count != 1
        or datamodule.train_dataloader_call_count != 1
        or datamodule.dataset.getitem_call_count != 1
        or datamodule.collator.call_count != 1
        or datamodule.before_batch_transfer_call_count != 1
        or model.transfer_batch_to_device_call_count != 1
        or datamodule.after_batch_transfer_call_count != 1
        or observer.validation_batch_count != 0
        or observer.test_batch_count != 0
        or observer.metrics is None
        or observer.runtime_losses is None
        or observer.optimizer_metadata is None
        or observer.geometry_component_gradient is None
        or not all_parameters_finite
        or changed_count <= 0
    ):
        _fail("BOUNDED_TRAINER_LIFECYCLE_GATE_FAILED")
    manual_losses = manual_reference.runtime_losses
    trainer_losses = observer.runtime_losses
    if tuple(name for name, unused in manual_losses) != tuple(
        name for name, unused in trainer_losses
    ):
        _fail("MANUAL_TRAINER_LOSS_DOMAIN_MISMATCH")
    maximum_loss_difference = max(
        abs(left - right)
        for (unused, left), (unused2, right) in zip(manual_losses, trainer_losses)
    )
    if maximum_loss_difference > LOSS_ABSOLUTE_TOLERANCE_V1:
        _fail("MANUAL_TRAINER_LOSS_PARITY_FAILED")
    loss_output = model._bounded_last_forward_output.loss_output
    if (
        loss_output.base_diffusion_valid_sample_count != 5
        or loss_output.covalent_pair_prediction_valid_sample_count != 5
        or loss_output.pre_post_geometry_valid_sample_count != 5
        or loss_output.covalent_pair_contrastive_valid_sample_count != 5
        or dict(observer.runtime_losses)["loss_pre_post_geometry"] <= 0.0
    ):
        _fail("LOSS_VALID_COUNTS_OR_GEOMETRY_INVALID")
    training_step_identity = (
        getattr(type(model), "training_step")
        is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    )
    optimizer_identity = (
        getattr(type(model), "configure_optimizers")
        is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    if not training_step_identity or not optimizer_identity:
        _fail("TRAINING_STEP_OR_OPTIMIZER_OWNER_IDENTITY_CHANGED")
    migration_names = (
        "checkpoint_key_count", "target_model_key_count", "shared_key_count",
        "target_only_key_count", "checkpoint_only_key_count",
        "shared_shape_mismatch_count", "shared_checkpoint_tensor_equality_count",
    )
    trainer_config = tuple(
        (name, value) for name, value in runtime.trainer_kwargs.items()
        if name != "callbacks"
    )
    return CovapieBatch001Train5BoundedTrainerFitSmokeResultV1(
        implementation_status="passed",
        result_interpretation="initial_joint_loss_candidate_validated_for_bounded_trainer_fit",
        formal_train_event_ids=prepared.authority.formal_train_event_ids,
        formal_validation_event_ids=prepared.authority.formal_validation_event_ids,
        formal_unresolved_event_ids=prepared.authority.formal_unresolved_event_ids,
        non_target_component_event_ids=prepared.authority.non_target_component_event_ids,
        DJK_train_event_count=prepared.authority.DJK_train_event_count,
        PTG_train_event_count=prepared.authority.PTG_train_event_count,
        scheduled_task_ids=carrier.scheduled_task_ids,
        ligand_node_count=115, pocket_node_count=578,
        pair_candidate_count=690, pair_positive_count=5, pair_negative_count=685,
        supervision_field_count=37,
        trainer_configuration=trainer_config,
        trainer_api_family=runtime.trainer_api_family,
        trainer_init_signature=str(inspect.signature(pl.Trainer.__init__)),
        trainer_fit_signature=str(inspect.signature(pl.Trainer.fit)),
        sampler_control_parameter=runtime.sampler_control_parameter,
        precision_argument=runtime.precision_argument,
        active_python_version=platform.python_version(),
        active_torch_version=str(torch.__version__),
        active_lightning_version=str(pl.__version__),
        direct_probe_rejection_message=direct_rejection,
        legacy_validation_epoch_end_compatibility_used=compatibility_used,
        direct_probe_global_step=direct_global_step,
        direct_probe_dataset_getitem_count=direct_getitem_count,
        direct_probe_train_batch_start_count=direct_train_start_count,
        direct_probe_parameters_unchanged=direct_parameters_unchanged,
        parameter_delta_snapshot_branch=snapshot_branch,
        parameter_delta_snapshot_optimizer_step_count_at_capture=(
            trained_pre_step_snapshot.optimizer_step_count_at_capture
        ),
        parameter_delta_snapshot_captured_before_optimizer_step=True,
        training_step_method_identity_exact=training_step_identity,
        configure_optimizers_method_identity_exact=optimizer_identity,
        trainer_fit_invoked=True,
        trainer_fit_train_batch_count=observer.train_batch_end_count,
        trainer_global_step=int(trainer.global_step),
        automatic_optimization=bool(model.automatic_optimization),
        automatic_backward_call_count=observer.after_backward_count,
        trainer_optimizer_step_count=observer.before_optimizer_step_count,
        zero_grad_lifecycle_call_count=observer.before_zero_grad_count,
        datamodule_setup_fit_call_count=datamodule.setup_fit_call_count,
        train_dataloader_call_count=datamodule.train_dataloader_call_count,
        dataset_getitem_call_count=datamodule.dataset.getitem_call_count,
        collator_call_count=datamodule.collator.call_count,
        before_batch_transfer_call_count=datamodule.before_batch_transfer_call_count,
        model_transfer_batch_to_device_call_count=model.transfer_batch_to_device_call_count,
        after_batch_transfer_call_count=datamodule.after_batch_transfer_call_count,
        transferred_batch_rebuilt=datamodule.transferred_batch_rebuilt,
        transferred_metadata_unchanged=datamodule.transferred_metadata_unchanged,
        transferred_tensors_on_model_device=datamodule.transferred_tensors_on_cpu,
        dataloader_batch_size=datamodule.loader.batch_size,
        dataloader_sequential_sampler=type(datamodule.loader.sampler) is SequentialSampler,
        dataloader_num_workers=datamodule.loader.num_workers,
        dataloader_drop_last=datamodule.loader.drop_last,
        dataloader_pin_memory=datamodule.loader.pin_memory,
        dataloader_persistent_workers=datamodule.loader.persistent_workers,
        validation_step_call_count=observer.validation_batch_count,
        test_step_call_count=observer.test_batch_count,
        diffusion_seed=forward_predecessor.DIFFUSION_FORWARD_SEED_V1,
        diffusion_seed_hook="Callback.on_train_batch_start_before_inherited_training_step",
        diffusion_seed_hook_call_count=observer.diffusion_seed_hook_call_count,
        diffusion_timesteps=observer.diffusion_timesteps,
        training_step_metrics=observer.metrics,
        runtime_losses=observer.runtime_losses,
        weighted_total_formula_value=observer.weighted_formula,
        weighted_total_formula_absolute_difference=observer.weighted_formula_difference,
        manual_reference_loss_tuple=manual_losses,
        trainer_loss_tuple=trainer_losses,
        max_abs_loss_difference=maximum_loss_difference,
        base_diffusion_valid_sample_count=loss_output.base_diffusion_valid_sample_count,
        covalent_pair_prediction_valid_sample_count=loss_output.covalent_pair_prediction_valid_sample_count,
        POST_geometry_valid_sample_count=loss_output.pre_post_geometry_valid_sample_count,
        PRE_geometry_valid_sample_count=0,
        covalent_pair_contrastive_valid_sample_count=loss_output.covalent_pair_contrastive_valid_sample_count,
        published_default_loss_weights=_loss_weights_tuple(published_default),
        initial_joint_loss_candidate=_loss_weights_tuple(candidate),
        optimizer_metadata=observer.optimizer_metadata,
        gradient_group_stats=observer.gradient_group_stats,
        geometry_component_gradient=observer.geometry_component_gradient,
        parameter_delta_group_stats=delta_stats,
        changed_parameter_tensor_count=changed_count,
        all_parameters_finite_after_fit=True,
        migration_counts=tuple((name, int(migration[name])) for name in migration_names),
        migration_missing_keys=tuple(migration["migration_missing_keys"]),
        migration_unexpected_keys=tuple(migration["migration_unexpected_keys"]),
        architecture=architecture,
        bound_source_sha256=bound_before,
        trainer_reference_source_sha256=TRAINER_REFERENCE_SHA256_V1,
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        checkpoint_file_changed=False,
        protected_sources_changed=False,
        protected_state_unchanged=True,
        raw_tree_unchanged=True,
        original_batch_unchanged=True,
        original_supervision_unchanged=True,
        temporary_trainer_root_removed=True,
        persistent_output_created=False,
        repository_profile=str(git_after["profile"]),
        repository_branch=str(git_after["branch"]),
        repository_HEAD=str(git_after["HEAD"]),
        repository_origin_main=str(git_after["origin_main"]),
        repository_ahead=int(git_after["ahead"]),
        repository_behind=int(git_after["behind"]),
        repository_staged_count=int(git_after["staged"]),
        repository_untracked_paths=tuple(git_after["untracked"]),
        published_default_modified=False,
        GPU_used=False,
        network_used=False,
        elapsed_seconds=time.perf_counter() - started,
        initial_joint_loss_candidate_validated_for_bounded_trainer_fit=True,
        geometry_weight_optimal=False,
        production_joint_loss_policy_finalized=False,
        full_training_authorized=False,
        ready_for_gpt_review=True,
        ready_for_five_epoch_train5_schedule_refresh_trainer_smoke=True,
        recommended_next_step_exactly=(
            "gpt_reaudit_repaired_bounded_train5_trainer_fit_then_publish_if_pass"
        ),
    )


def run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
    *,
    repository_root: Path | None = None,
    state_root: Path | None = None,
    cache_root: Path | None = None,
    checkpoint_path: Path | None = None,
    device: str = "cpu",
    initial_joint_loss_candidate: CovapieCurrent11LossWeightsV1 | None = None,
    persistent_output_path: Path | None = None,
) -> CovapieBatch001Train5BoundedTrainerFitSmokeResultV1:
    """Execute one real automatic-optimization Trainer step and stop."""

    try:
        if device != "cpu":
            _fail("NON_CPU_TRAINER_REJECTED")
        if persistent_output_path is not None:
            _fail("PERSISTENT_OUTPUT_PATH_FORBIDDEN")
        repository = _require_directory(
            repository_root, default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_directory(
            state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID"
        )
        cache = _require_directory(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID"
        )
        checkpoint = (
            repository / forward_predecessor.CHECKPOINT_RELATIVE_PATH_V1
            if checkpoint_path is None else checkpoint_path
        )
        if (
            type(checkpoint) is not _PATH_TYPE
            or checkpoint != repository / forward_predecessor.CHECKPOINT_RELATIVE_PATH_V1
        ):
            _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
        return _run_impl(
            repository_root=repository,
            state_root=state,
            cache_root=cache,
            checkpoint_path=checkpoint,
            loss_weights=initial_joint_loss_candidate,
        )
    except BaseException as error:
        _public_error(error)

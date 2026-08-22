"""Five ordinary Trainer epochs with canonical task refresh on formal train5.

This is a bounded CPU smoke, not formal training.  Formal population and
structural preparation stay owned by the published train5 predecessor; the
Current11 model, diffusion path, auxiliary heads, losses, training step, and
optimizer remain inherited from their published owners.  Nothing is persisted.
"""

from __future__ import annotations

import inspect
import math
from pathlib import Path
import platform
import signal
import stat
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
    covapie_batch001_train5_bounded_trainer_fit_smoke_v1
    as bounded_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as forward_predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
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


single_step_predecessor = bounded_predecessor.single_step_predecessor
instantiation_owner = bounded_predecessor.instantiation_owner
migration_owner = bounded_predecessor.migration_owner
trainer_reference = bounded_predecessor.trainer_reference

__all__ = (
    "BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_SMOKE_ERROR_V1",
    "INITIAL_FIVE_EPOCH_JOINT_LOSS_CANDIDATE_V1",
    "CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1",
    "CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1",
    "verify_covapie_batch001_train5_five_epoch_predecessor_source_v1",
    "run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1",
)


BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_SMOKE_ERROR_V1 = (
    "COVAPIE_BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_"
    "SMOKE_V1_ERROR"
)
INITIAL_FIVE_EPOCH_JOINT_LOSS_CANDIDATE_V1 = (
    bounded_predecessor.INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
)
EXPECTED_HEAD_V1 = "efe5aec019bfc878f780cf23240c9f9d2661cae9"
EXPECTED_HEAD_SUBJECT_V1 = (
    "add CovaPIE batch001 train5 bounded Trainer.fit smoke v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE batch001 train5 five-epoch task schedule refresh Trainer smoke v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
EXACT_EPOCHS_V1 = (0, 1, 2, 3, 4)
EXPECTED_EPOCH0_TASK_VECTOR_V1 = (4, 4, 2, 0, 4)
EXPECTED_METRIC_KEYS_V1 = bounded_predecessor.EXPECTED_METRIC_KEYS_V1
LOSS_ABSOLUTE_TOLERANCE_V1 = bounded_predecessor.LOSS_ABSOLUTE_TOLERANCE_V1
LOSS_RELATIVE_TOLERANCE_V1 = bounded_predecessor.LOSS_RELATIVE_TOLERANCE_V1
RECOMMENDED_NEXT_STEP_EXACTLY_V1 = (
    "gpt_audit_five_epoch_schedule_refresh_then_pivot_to_formal_dataset_scale_"
    "and_validation_mainline_v1"
)
IMMEDIATE_PREDECESSOR_SHA256_V1 = (
    (
        "src/covalent_ext/"
        "covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
        "ab4659abeed0a93a442dae68cc339a389c6fbee10e3747f36735117cb89a54c7",
    ),
    (
        "scripts/check_covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
        "eb680dbe5d5cccb573f1735fb2bef0cd706642e9e8c84d12cc0e16e6671c3e8e",
    ),
    (
        "tests/test_covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py",
        "3e602d89a43ceb82be593b9fe89f719907b2b45d2b00f0b9efba21cb9f38a667",
    ),
)
CANDIDATE_RELATIVE_PATHS_V1 = frozenset((
    "src/covalent_ext/"
    "covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1.py",
    "scripts/"
    "check_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1.py",
    "tests/"
    "test_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1.py",
))
_TASK_DEPENDENT_SUPERVISION_FIELDS_V1 = frozenset((
    "canonical_task_id",
    "ligand_base_generation_mask",
    "ligand_base_fixed_mask",
    "ligand_base_target_mask",
    "ligand_base_context_mask",
    "ligand_active_diffusion_loss_mask",
))
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    sample_identities: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int


@dataclass(frozen=True)
class _PreparedFiveEpochCarriersV1:
    prepared_train5: forward_predecessor._PreparedTrain5BatchV1
    carriers: tuple[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1, ...]
    sample_task_cycles: tuple[tuple[int, ...], ...]
    epoch_task_vectors: tuple[tuple[int, ...], ...]
    per_sample_unique_generation_mask_count: tuple[int, ...]
    cross_epoch_static_label_parity: bool


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
class CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1:
    implementation_status: str
    result_interpretation: str
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_unresolved_event_ids: tuple[str, ...]
    non_target_component_event_ids: tuple[str, ...]
    DJK_train_event_count: int
    PTG_train_event_count: int
    sample_task_cycles: tuple[tuple[int, ...], ...]
    epoch_task_vectors: tuple[tuple[int, ...], ...]
    per_sample_unique_generation_mask_count: tuple[int, ...]
    cross_epoch_static_label_parity: bool
    epoch_carrier_count: int
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
    direct_probe_optimizer_step_count: int
    direct_probe_parameters_unchanged: bool
    parameter_delta_snapshot_branch: str
    parameter_delta_snapshot_model_identity_exact: bool
    parameter_delta_snapshot_trainer_global_step_at_capture: int
    parameter_delta_snapshot_optimizer_step_count_at_capture: int
    training_step_method_identity_exact: bool
    configure_optimizers_method_identity_exact: bool
    trainer_fit_invoked: bool
    trainer_fit_train_batch_count: int
    trainer_epoch_sequence: tuple[int, ...]
    trainer_global_step: int
    automatic_optimization: bool
    automatic_backward_call_count: int
    trainer_optimizer_step_count: int
    zero_grad_lifecycle_call_count: int
    datamodule_setup_fit_call_count: int
    train_dataloader_call_count: int
    train_dataloader_epoch_sequence: tuple[int, ...]
    dataset_getitem_call_count: int
    collator_call_count: int
    before_batch_transfer_call_count: int
    model_transfer_batch_to_device_call_count: int
    after_batch_transfer_call_count: int
    transferred_batch_rebuilt_each_epoch: tuple[bool, ...]
    transferred_metadata_unchanged_each_epoch: tuple[bool, ...]
    transferred_tensors_on_model_device_each_epoch: tuple[bool, ...]
    dataloader_contract_each_epoch: tuple[tuple[tuple[str, object], ...], ...]
    validation_step_call_count: int
    test_step_call_count: int
    diffusion_seed: int
    diffusion_seed_hook_call_count: int
    diffusion_timesteps_each_epoch: tuple[tuple[int, ...], ...]
    generated_ligand_node_count_each_epoch: tuple[int, ...]
    runtime_losses_each_epoch: tuple[tuple[tuple[str, float], ...], ...]
    weighted_total_formula_each_epoch: tuple[float, ...]
    weighted_total_formula_absolute_difference_each_epoch: tuple[float, ...]
    valid_sample_counts_each_epoch: tuple[tuple[tuple[str, int], ...], ...]
    published_default_loss_weights: tuple[tuple[str, float], ...]
    initial_joint_loss_candidate: tuple[tuple[str, float], ...]
    optimizer_metadata: single_step_predecessor.CovapieBatch001Train5OptimizerMetadataV1
    optimizer_object_identities: tuple[int, ...]
    unique_optimizer_identity_count: int
    gradient_group_stats_each_epoch: tuple[
        tuple[single_step_predecessor.CovapieBatch001Train5GradientGroupStatsV1, ...],
        ...,
    ]
    geometry_component_gradient_each_epoch: tuple[
        single_step_predecessor.CovapieBatch001Train5GeometryComponentGradientV1,
        ...,
    ]
    parameter_delta_group_stats_each_epoch: tuple[
        tuple[
            single_step_predecessor.CovapieBatch001Train5ParameterDeltaGroupStatsV1,
            ...,
        ],
        ...,
    ]
    cumulative_parameter_delta_group_stats: tuple[
        single_step_predecessor.CovapieBatch001Train5ParameterDeltaGroupStatsV1,
        ...,
    ]
    cumulative_changed_parameter_tensor_count: int
    all_parameters_finite_after_each_step: tuple[bool, ...]
    model_object_identities: tuple[int, ...]
    unique_model_identity_count: int
    checkpoint_payload_load_call_count: int
    actual_trained_model_migration_call_count: int
    checkpoint_reload_between_epochs: bool
    model_reinitialization_during_epochs: bool
    migration_counts: tuple[tuple[str, int], ...]
    migration_missing_keys: tuple[str, ...]
    migration_unexpected_keys: tuple[str, ...]
    architecture: tuple[tuple[str, object], ...]
    bound_source_sha256: tuple[tuple[str, str], ...]
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    checkpoint_file_changed: bool
    protected_sources_changed: bool
    protected_state_unchanged: bool
    raw_tree_unchanged: bool
    original_epoch_carriers_unchanged: bool
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
    candidate_file_observations: tuple[tuple[str, int, str, str], ...]
    published_default_modified: bool
    GPU_used: bool
    network_used: bool
    elapsed_seconds: float
    canonical_five_task_schedule_refresh_verified: bool
    all_five_samples_cover_all_five_tasks: bool
    single_continuous_model_across_five_epochs: bool
    single_optimizer_across_five_epochs: bool
    all_epoch_losses_finite: bool
    all_epoch_gradient_groups_finite: bool
    all_epoch_required_gradient_groups_nonzero: bool
    all_epoch_PRE_final_output_component_gradient_zero: bool
    all_epoch_POST_final_output_component_gradient_nonzero: bool
    all_epoch_required_parameter_groups_changed: bool
    cumulative_model_parameter_delta_nonzero: bool
    geometry_weight_optimal: bool
    production_joint_loss_policy_finalized: bool
    full_training_authorized: bool
    ready_for_gpt_review: bool
    ready_for_mainline_data_scale_and_validation_design: bool
    recommended_next_step_exactly: str


class _SmokeInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _SmokeInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_SMOKE_ERROR_V1
    ):
        raise error
    if isinstance(error, (
        _SmokeInvariantError,
        bounded_predecessor._SmokeInvariantError,
        single_step_predecessor._SmokeInvariantError,
        forward_predecessor._SmokeInvariantError,
    )):
        reason = error.reason
    else:
        reason = "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_SMOKE_ERROR_V1}:"
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


def _classify_repository_profile_v1(observation: _RepositoryObservationV1) -> str:
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
    expected_changed = tuple(sorted(
        ("A", path) for path in CANDIDATE_RELATIVE_PATHS_V1
    ))
    expected_modes = tuple(sorted(
        ("100644", path) for path in CANDIDATE_RELATIVE_PATHS_V1
    ))
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
        repository_root, "rev-list", "--left-right", "--count",
        "HEAD...origin/main",
    ).split()
    status_lines = tuple(filter(None, _git(
        repository_root, "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines()))
    untracked = tuple(sorted(
        line[3:] for line in status_lines if line.startswith("?? ")
    ))
    tracked = tuple(line for line in status_lines if not line.startswith("?? "))
    staged = tuple(filter(None, _git(
        repository_root, "diff", "--cached", "--name-only"
    ).splitlines()))
    parent_line = _git(
        repository_root, "rev-list", "--parents", "-n", "1", "HEAD"
    ).split()
    if not parent_line or parent_line[0] != head:
        _fail("GIT_HEAD_PARENT_OBSERVATION_INVALID")
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
        tracked_status=tracked,
        staged_paths=staged,
        untracked_paths=untracked,
        head_parents=tuple(parent_line[1:]),
        head_changed_paths=tuple(changed),
        head_tree_modes=tuple(modes),
    )
    return {
        "profile": _classify_repository_profile_v1(observation),
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
        + bounded_predecessor.IMMEDIATE_PREDECESSOR_SHA256_V1
        + single_step_predecessor.ALL_BOUND_SOURCE_SHA256_V1
        + forward_predecessor.BOUND_OWNER_SHA256_V1
        + ((
            bounded_predecessor.TRAINER_REFERENCE_RELATIVE_PATH_V1,
            bounded_predecessor.TRAINER_REFERENCE_SHA256_V1,
        ),)
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
    bounded_predecessor._verify_bound_sources(repository_root)
    return tuple(observed)


def verify_covapie_batch001_train5_five_epoch_predecessor_source_v1(
    *, predecessor_source_path: Path,
) -> str:
    """Verify the exact bounded-Trainer immediate predecessor source."""

    try:
        actual = single_step_predecessor._sha256_file(predecessor_source_path)
        if actual != IMMEDIATE_PREDECESSOR_SHA256_V1[0][1]:
            _fail("PREDECESSOR_SOURCE_SHA256_MISMATCH")
        return actual
    except BaseException as error:
        _public_error(error)


def _protected_file_snapshot(
    repository_root: Path, checkpoint_path: Path,
) -> tuple[tuple[str, str], ...]:
    relative_paths = tuple(relative for relative, unused in _verify_bound_sources(
        repository_root
    ))
    paths = tuple(repository_root / relative for relative in relative_paths)
    paths += bounded_predecessor._formal_artifact_paths(repository_root)
    paths += (checkpoint_path,)
    observations = tuple(
        (str(path.relative_to(repository_root)), single_step_predecessor._sha256_file(path))
        for path in paths
    )
    if len(observations) != len(set(name for name, unused in observations)):
        _fail("PROTECTED_FILE_SET_DUPLICATED")
    return observations


def _candidate_file_observations(
    repository_root: Path,
) -> tuple[tuple[str, int, str, str], ...]:
    observations: list[tuple[str, int, str, str]] = []
    for relative in sorted(CANDIDATE_RELATIVE_PATHS_V1):
        path = repository_root / relative
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or mode & 0o111
        ):
            _fail("CANDIDATE_FILE_MODE_INVALID")
        observations.append((
            relative,
            metadata.st_size,
            single_step_predecessor._sha256_file(path),
            f"{mode:04o}",
        ))
    return tuple(observations)


def _validate_loss_policy(
    requested: object,
    *, published_default: CovapieCurrent11LossWeightsV1 | None = None,
) -> tuple[CovapieCurrent11LossWeightsV1, CovapieCurrent11LossWeightsV1]:
    published, candidate = bounded_predecessor._validate_loss_policy(
        requested, published_default=published_default
    )
    if candidate is not INITIAL_FIVE_EPOCH_JOINT_LOSS_CANDIDATE_V1:
        _fail("FIVE_EPOCH_CANDIDATE_NOT_EXACT_PREDECESSOR_ALIAS")
    return published, candidate


def _canonical_epoch_task_vector(epoch: int) -> tuple[int, ...]:
    if type(epoch) is not int or epoch not in EXACT_EPOCHS_V1:
        _fail("EPOCH_OUTSIDE_EXACT_FIVE_EPOCH_DOMAIN")
    return tuple(
        preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identity,
            epoch=epoch,
            task_schedule_seed=forward_predecessor.TASK_SCHEDULE_SEED_V1,
        )
        for identity in forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
    )


def _validate_carrier(
    carrier: object,
) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
    if type(carrier) is not CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        _fail("TRAIN5_FIVE_EPOCH_CARRIER_TYPE_INVALID")
    supervision = carrier.supervision
    expected_tasks = _canonical_epoch_task_vector(carrier.epoch)
    if (
        type(carrier.model_input_batch) is not dict
        or not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
        or carrier.sample_identities != forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or carrier.scheduled_task_ids != expected_tasks
        or carrier.task_schedule_seed != forward_predecessor.TASK_SCHEDULE_SEED_V1
        or len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or supervision.canonical_task_id.tolist() != list(expected_tasks)
        or not bool(supervision.canonical_task_valid.all().item())
        or len(supervision.sample_training_admitted) != 5
        or not bool(supervision.sample_training_admitted.all().item())
        or len(supervision.pair_candidate_batch_index) != 690
        or int(supervision.pair_candidate_is_positive.sum().item()) != 5
        or int(supervision.pair_candidate_is_negative.sum().item()) != 685
        or int(supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()) != 0
        or int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()) != 5
        or not bool(torch.isnan(
            supervision.pre_post_geometry_target_angstrom[:, 0]
        ).all().item())
        or not bool(torch.isfinite(
            supervision.pre_post_geometry_target_angstrom[:, 1]
        ).all().item())
    ):
        _fail("TRAIN5_FIVE_EPOCH_CARRIER_CONTRACT_INVALID")
    ligand_mask = carrier.model_input_batch.get("lig_mask")
    pocket_mask = carrier.model_input_batch.get("pocket_mask")
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask
    if (
        not isinstance(ligand_mask, torch.Tensor)
        or not isinstance(pocket_mask, torch.Tensor)
        or len(ligand_mask) != 115
        or len(pocket_mask) != 578
        or generation.shape != (115, 1)
        or fixed.shape != (115, 1)
        or generation.dtype != torch.bool
        or fixed.dtype != torch.bool
        or not bool((generation ^ fixed).all().item())
        or bool((generation & fixed).any().item())
        or not torch.equal(
            supervision.ligand_active_diffusion_loss_mask, generation
        )
    ):
        _fail("TRAIN5_FIVE_EPOCH_CARRIER_MODEL_OR_MASK_INVALID")
    for sample in range(5):
        if not bool(generation[:, 0][ligand_mask == sample].any().item()):
            _fail("TRAIN5_FIVE_EPOCH_GENERATED_ATOM_SET_EMPTY")
    return carrier


def _values_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return single_step_predecessor._same_tensor(left, right)
    return type(left) is type(right) and left == right


def _validate_static_label_parity(
    carriers: Sequence[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1],
) -> bool:
    carrier_tuple = tuple(carriers)
    if len(carrier_tuple) != 5:
        _fail("STATIC_LABEL_CARRIER_DOMAIN_INVALID")
    baseline = carrier_tuple[0]
    supervision_fields = tuple(
        field.name for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        if field.name not in _TASK_DEPENDENT_SUPERVISION_FIELDS_V1
    )
    for carrier in carrier_tuple[1:]:
        if (
            carrier.sample_identities != baseline.sample_identities
            or tuple(carrier.model_input_batch) != tuple(baseline.model_input_batch)
            or any(
                not _values_equal(
                    baseline.model_input_batch[name],
                    carrier.model_input_batch[name],
                )
                for name in baseline.model_input_batch
            )
            or any(
                not _values_equal(
                    getattr(baseline.supervision, name),
                    getattr(carrier.supervision, name),
                )
                for name in supervision_fields
            )
        ):
            _fail("CROSS_EPOCH_STATIC_CHEMISTRY_LABEL_DRIFT")
    return True


def _generation_mask_unique_counts(
    carriers: Sequence[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1],
) -> tuple[int, ...]:
    carrier_tuple = tuple(_validate_carrier(carrier) for carrier in carriers)
    if (
        len(carrier_tuple) != 5
        or tuple(carrier.epoch for carrier in carrier_tuple) != EXACT_EPOCHS_V1
    ):
        _fail("GENERATION_MASK_CARRIER_DOMAIN_INVALID")
    pattern_counts: list[int] = []
    for sample in range(5):
        patterns: set[tuple[bool, ...]] = set()
        for carrier in carrier_tuple:
            membership = carrier.model_input_batch["lig_mask"]
            if not isinstance(membership, torch.Tensor):
                _fail("EPOCH_LIGAND_MEMBERSHIP_INVALID")
            pattern = tuple(bool(value) for value in (
                carrier.supervision.ligand_base_generation_mask[:, 0][
                    membership == sample
                ].tolist()
            ))
            if not pattern or not any(pattern):
                _fail("GENERATION_MASK_PATTERN_EMPTY")
            patterns.add(pattern)
        pattern_counts.append(len(patterns))
    counts = tuple(pattern_counts)
    if counts != (5, 5, 5, 5, 5):
        _fail("GENERATION_MASK_NOT_REFRESHED_ACROSS_FIVE_TASKS")
    return counts


def _build_five_epoch_carriers(
    prepared: forward_predecessor._PreparedTrain5BatchV1,
) -> _PreparedFiveEpochCarriersV1:
    if (
        type(prepared) is not forward_predecessor._PreparedTrain5BatchV1
        or prepared.sample_identities != forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
        or len(prepared.structural_records) != 5
    ):
        _fail("PREPARED_TRAIN5_INPUT_INVALID")
    cycles = tuple(tuple(row) for row in prepared.five_epoch_task_schedule_audit)
    if (
        len(cycles) != 5
        or any(len(cycle) != 5 or set(cycle) != set(EXACT_EPOCHS_V1) for cycle in cycles)
    ):
        _fail("SAMPLE_TASK_CYCLE_NOT_EXACT_FIVE_TASK_PERMUTATION")
    epoch_vectors = tuple(
        tuple(cycles[sample][epoch] for sample in range(5))
        for epoch in EXACT_EPOCHS_V1
    )
    if epoch_vectors[0] != EXPECTED_EPOCH0_TASK_VECTOR_V1:
        _fail("EPOCH0_TASK_VECTOR_CONTINUITY_FAILED")
    if any(
        vector != _canonical_epoch_task_vector(epoch)
        for epoch, vector in zip(EXACT_EPOCHS_V1, epoch_vectors)
    ):
        _fail("CANONICAL_SCHEDULER_ORACLE_PARITY_FAILED")

    carriers: list[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1] = []
    for epoch, task_vector in zip(EXACT_EPOCHS_V1, epoch_vectors):
        preview = preview_owner._tensorize_records_v1(
            records=prepared.structural_records,
            task_ids=task_vector,
            epoch=epoch,
            task_schedule_seed=forward_predecessor.TASK_SCHEDULE_SEED_V1,
        )
        if not preview_owner.validate_covapie_batch001_preview_batch_v1(preview):
            _fail("EPOCH_PREVIEW_VALIDATION_FAILED")
        ligand_mask = preview.model_input_batch.get("lig_mask")
        if not isinstance(ligand_mask, torch.Tensor):
            _fail("EPOCH_LIGAND_MEMBERSHIP_INVALID")
        admitted = forward_predecessor._clone_admitted_supervision(
            preview.supervision, ligand_mask
        )
        carriers.append(_validate_carrier(
            CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1(
                model_input_batch=preview.model_input_batch,
                supervision=admitted,
                sample_identities=prepared.sample_identities,
                scheduled_task_ids=task_vector,
                epoch=epoch,
                task_schedule_seed=forward_predecessor.TASK_SCHEDULE_SEED_V1,
            )
        ))

    unique_counts = _generation_mask_unique_counts(carriers)
    static_parity = _validate_static_label_parity(carriers)
    return _PreparedFiveEpochCarriersV1(
        prepared_train5=prepared,
        carriers=tuple(carriers),
        sample_task_cycles=cycles,
        epoch_task_vectors=epoch_vectors,
        per_sample_unique_generation_mask_count=unique_counts,
        cross_epoch_static_label_parity=static_parity,
    )


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
    elif isinstance(value, CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1):
        tensors.extend(_all_nested_tensors(value.model_input_batch))
        tensors.extend(_all_nested_tensors(value.supervision))
    return tuple(tensors)


def _tensor_snapshot(value: object) -> tuple[torch.Tensor, ...]:
    return tuple(tensor.detach().clone() for tensor in _all_nested_tensors(value))


def _tensor_snapshot_unchanged(
    before: Sequence[torch.Tensor], value: object,
) -> bool:
    after = _all_nested_tensors(value)
    return len(before) == len(after) and all(
        single_step_predecessor._same_tensor(left, right)
        for left, right in zip(before, after)
    )


class _Train5FiveEpochTrainerAdapterV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Smoke-local refreshed-carrier adapter; training ownership is inherited."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.transfer_batch_to_device_call_count = 0
        self._five_epoch_last_forward_output: (
            CovapieCurrent11TrainingForwardOutputV1 | None
        ) = None

    def transfer_batch_to_device(
        self, batch: object, device: torch.device, dataloader_idx: int,
    ) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        original = _validate_carrier(batch)
        if (
            dataloader_idx != 0
            or device.type != "cpu"
            or self.transfer_batch_to_device_call_count >= 5
        ):
            _fail("TRAINER_TRANSFER_DEVICE_INDEX_OR_COUNT_INVALID")
        self.transfer_batch_to_device_call_count += 1
        parent_transfer = super().transfer_batch_to_device
        model_input = parent_transfer(
            original.model_input_batch, device, dataloader_idx
        )
        if type(model_input) is not dict:
            _fail("MODEL_INPUT_TRANSFER_RESULT_INVALID")
        values: dict[str, torch.Tensor] = {}
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
            transferred = parent_transfer(
                getattr(original.supervision, field.name), device, dataloader_idx
            )
            if not isinstance(transferred, torch.Tensor):
                _fail("SUPERVISION_TRANSFER_RESULT_INVALID")
            values[field.name] = transferred
        return _validate_carrier(
            CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1(
                model_input_batch=dict(model_input),
                supervision=CovapieCurrent11TrainingSupervisionTensorsV1(**values),
                sample_identities=original.sample_identities,
                scheduled_task_ids=original.scheduled_task_ids,
                epoch=original.epoch,
                task_schedule_seed=original.task_schedule_seed,
            )
        )

    def forward(self, data: object) -> CovapieCurrent11TrainingForwardOutputV1:
        carrier = _validate_carrier(data)
        if (
            self.training is not True
            or carrier.epoch != int(self.current_epoch)
            or carrier.task_schedule_seed
            != self.covapie_current11_task_schedule_seed
        ):
            _fail("TRAIN5_FIVE_EPOCH_FORWARD_LIFECYCLE_INVALID")
        ligand, pocket = self.get_ligand_and_pocket(carrier.model_input_batch)
        supervision = carrier.supervision
        indicator = supervision.target_residue_reactive_atom_mask
        if indicator.shape != (len(pocket["x"]), 1) or indicator.dtype != torch.bool:
            _fail("TARGET_RESIDUE_INDICATOR_INVALID")
        role_delta = (
            self.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
                supervision=supervision,
                ligand_batch_index=ligand["mask"],
            )
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
            pair_contrastive_temperature=(
                self.covapie_current11_pair_contrastive_temperature
            ),
            geometry_smooth_l1_beta=1.0,
        )
        result = CovapieCurrent11TrainingForwardOutputV1(
            model_output=model_output,
            loss_output=losses,
            supervision=supervision,
            diffusion_trace=trace,
        )
        self._five_epoch_last_forward_output = result
        return result


class _Train5FiveEpochTrainerCompatibilityAdapterV1(
    _Train5FiveEpochTrainerAdapterV1
):
    """Only the previously accepted active-Lightning hook compatibility."""

    validation_epoch_end = None
    configure_gradient_clipping = (
        bounded_predecessor._Train5BoundedTrainerCompatibilityAdapterV1
        .configure_gradient_clipping
    )


def _instantiate_model(
    *,
    owner: type[_Train5FiveEpochTrainerAdapterV1],
    repository_root: Path,
    state_root: Path,
    legacy_setup_data_root: Path,
    output_root: Path,
    loss_weights: CovapieCurrent11LossWeightsV1,
) -> _Train5FiveEpochTrainerAdapterV1:
    model = bounded_predecessor._instantiate_model(
        owner=owner,
        repository_root=repository_root,
        state_root=state_root,
        legacy_setup_data_root=legacy_setup_data_root,
        output_root=output_root,
        loss_weights=loss_weights,
    )
    if type(model) is not owner:
        _fail("FIVE_EPOCH_MODEL_OWNER_TYPE_INVALID")
    return model


class _SingleEpochCarrierDatasetV1(
    Dataset[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1]
):
    def __init__(
        self, carrier: CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1,
    ) -> None:
        self.carrier = _validate_carrier(carrier)
        self.getitem_call_count = 0

    def __len__(self) -> int:
        return 1

    def __getitem__(
        self, index: int,
    ) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        self.getitem_call_count += 1
        if self.getitem_call_count > 1:
            _fail("SECOND_TRAIN_BATCH_IN_EPOCH_REJECTED")
        return self.carrier


class _SingleEpochCarrierCollatorV1:
    def __init__(
        self, carrier: CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1,
    ) -> None:
        self.carrier = carrier
        self.call_count = 0

    def __call__(
        self,
        rows: list[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1],
    ) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        self.call_count += 1
        if (
            self.call_count > 1
            or len(rows) != 1
            or rows[0] is not self.carrier
        ):
            _fail("COLLATOR_EXACT_SINGLE_EPOCH_CARRIER_INVALID")
        return _validate_carrier(rows[0])


class _FiveEpochRefreshDataModuleV1(pl.LightningDataModule):
    def __init__(
        self,
        carriers: Sequence[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1],
    ) -> None:
        super().__init__()
        self.carriers = tuple(_validate_carrier(carrier) for carrier in carriers)
        if tuple(carrier.epoch for carrier in self.carriers) != EXACT_EPOCHS_V1:
            _fail("DATAMODULE_CARRIER_EPOCH_DOMAIN_INVALID")
        self.datasets: list[_SingleEpochCarrierDatasetV1] = []
        self.collators: list[_SingleEpochCarrierCollatorV1] = []
        self.loaders: list[DataLoader] = []
        self.setup_fit_call_count = 0
        self.train_dataloader_call_count = 0
        self.train_dataloader_epoch_sequence: list[int] = []
        self.before_batch_transfer_call_count = 0
        self.after_batch_transfer_call_count = 0
        self.transferred_batch_rebuilt_each_epoch: list[bool] = []
        self.transferred_metadata_unchanged_each_epoch: list[bool] = []
        self.transferred_tensors_on_cpu_each_epoch: list[bool] = []
        self.dataloader_contract_each_epoch: list[tuple[tuple[str, object], ...]] = []

    @property
    def dataset_getitem_call_count(self) -> int:
        return sum(dataset.getitem_call_count for dataset in self.datasets)

    @property
    def collator_call_count(self) -> int:
        return sum(collator.call_count for collator in self.collators)

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("DATAMODULE_SETUP_STAGE_INVALID")
        self.setup_fit_call_count += 1
        if self.setup_fit_call_count > 1:
            _fail("DATAMODULE_SETUP_FIT_CALLED_MORE_THAN_ONCE")

    def train_dataloader(self) -> DataLoader:
        epoch = int(self.trainer.current_epoch)
        expected_epoch = self.train_dataloader_call_count
        if (
            self.train_dataloader_call_count >= 5
            or epoch not in EXACT_EPOCHS_V1
            or epoch != expected_epoch
        ):
            _fail("TRAIN_DATALOADER_EPOCH_REFRESH_SEQUENCE_INVALID")
        carrier = self.carriers[epoch]
        if carrier.epoch != epoch:
            _fail("STALE_EPOCH0_CARRIER_REUSED")
        dataset = _SingleEpochCarrierDatasetV1(carrier)
        collator = _SingleEpochCarrierCollatorV1(carrier)
        loader = DataLoader(
            dataset,
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=collator,
        )
        contract = (
            ("dataset_length", len(dataset)),
            ("loader_length", len(loader)),
            ("batch_size", loader.batch_size),
            ("sequential_sampler", type(loader.sampler) is SequentialSampler),
            ("num_workers", loader.num_workers),
            ("drop_last", loader.drop_last),
            ("pin_memory", loader.pin_memory),
            ("persistent_workers", loader.persistent_workers),
        )
        if dict(contract) != {
            "dataset_length": 1,
            "loader_length": 1,
            "batch_size": 1,
            "sequential_sampler": True,
            "num_workers": 0,
            "drop_last": False,
            "pin_memory": False,
            "persistent_workers": False,
        }:
            _fail("DATALOADER_CONFIGURATION_INVALID")
        self.datasets.append(dataset)
        self.collators.append(collator)
        self.loaders.append(loader)
        self.dataloader_contract_each_epoch.append(contract)
        self.train_dataloader_epoch_sequence.append(epoch)
        self.train_dataloader_call_count += 1
        return loader

    def val_dataloader(self) -> None:
        return None

    def test_dataloader(self) -> None:
        return None

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int,
    ) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        carrier = _validate_carrier(batch)
        epoch = int(self.trainer.current_epoch)
        self.before_batch_transfer_call_count += 1
        if (
            self.before_batch_transfer_call_count > 5
            or dataloader_idx != 0
            or carrier is not self.carriers[epoch]
            or carrier.epoch != epoch
        ):
            _fail("BEFORE_BATCH_TRANSFER_CONTRACT_INVALID")
        return carrier

    def on_after_batch_transfer(
        self, batch: object, dataloader_idx: int,
    ) -> CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1:
        transferred = _validate_carrier(batch)
        epoch = int(self.trainer.current_epoch)
        original = self.carriers[epoch]
        rebuilt = (
            transferred is not original
            and transferred.model_input_batch is not original.model_input_batch
            and transferred.supervision is not original.supervision
        )
        metadata = (
            transferred.sample_identities is original.sample_identities
            and transferred.scheduled_task_ids is original.scheduled_task_ids
            and transferred.epoch == original.epoch
            and transferred.task_schedule_seed == original.task_schedule_seed
        )
        tensors = _all_nested_tensors(transferred)
        on_cpu = bool(tensors) and all(tensor.device.type == "cpu" for tensor in tensors)
        self.after_batch_transfer_call_count += 1
        if (
            self.after_batch_transfer_call_count > 5
            or dataloader_idx != 0
            or transferred.epoch != epoch
            or not rebuilt
            or not metadata
            or not on_cpu
        ):
            _fail("AFTER_BATCH_TRANSFER_CONTRACT_INVALID")
        self.transferred_batch_rebuilt_each_epoch.append(rebuilt)
        self.transferred_metadata_unchanged_each_epoch.append(metadata)
        self.transferred_tensors_on_cpu_each_epoch.append(on_cpu)
        return transferred


class _FiveEpochTrainerObserverV1(pl.Callback):
    def __init__(
        self,
        *,
        original_carriers: Sequence[
            CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1
        ],
        checkpoint_state: Mapping[str, torch.Tensor],
        parameter_groups: tuple[tuple[str, tuple[str, ...], str], ...],
    ) -> None:
        super().__init__()
        self.original_carriers = tuple(original_carriers)
        self.checkpoint_state = checkpoint_state
        self.parameter_groups = parameter_groups
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
        self.epoch_sequence: list[int] = []
        self.model_object_identities: list[int] = []
        self.optimizer_object_identities: list[int] = []
        self.optimizer_metadata_each_epoch: list[
            single_step_predecessor.CovapieBatch001Train5OptimizerMetadataV1
        ] = []
        self.runtime_losses_each_epoch: list[tuple[tuple[str, float], ...]] = []
        self.weighted_total_formula_each_epoch: list[float] = []
        self.weighted_difference_each_epoch: list[float] = []
        self.valid_counts_each_epoch: list[tuple[tuple[str, int], ...]] = []
        self.diffusion_timesteps_each_epoch: list[tuple[int, ...]] = []
        self.generated_node_counts_each_epoch: list[int] = []
        self.gradient_stats_each_epoch: list[tuple[
            single_step_predecessor.CovapieBatch001Train5GradientGroupStatsV1,
            ...,
        ]] = []
        self.geometry_gradient_each_epoch: list[
            single_step_predecessor.CovapieBatch001Train5GeometryComponentGradientV1
        ] = []
        self.parameter_delta_each_epoch: list[tuple[
            single_step_predecessor.CovapieBatch001Train5ParameterDeltaGroupStatsV1,
            ...,
        ]] = []
        self.all_parameters_finite_after_each_step: list[bool] = []
        self._model_identity: int | None = None
        self._pre_batch_parameters: dict[int, dict[str, torch.Tensor]] = {}
        self.process_control_exception: BaseException | None = None

    def on_fit_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule,
    ) -> None:
        self.fit_start_count += 1
        self._model_identity = id(pl_module)
        if (
            self.fit_start_count != 1
            or int(trainer.global_step) != 0
            or self.before_optimizer_step_count != 0
        ):
            _fail("FIT_START_SNAPSHOT_ORDER_INVALID")

    def on_train_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
    ) -> None:
        carrier = _validate_carrier(batch)
        epoch = int(trainer.current_epoch)
        expected_epoch = self.train_batch_start_count
        model_device = next(pl_module.parameters()).device
        if (
            self.train_batch_start_count >= 5
            or batch_idx != 0
            or epoch != expected_epoch
            or carrier.epoch != epoch
            or carrier.scheduled_task_ids != _canonical_epoch_task_vector(epoch)
            or carrier is self.original_carriers[epoch]
            or pl_module.training is not True
            or id(pl_module) != self._model_identity
            or any(tensor.device != model_device for tensor in _all_nested_tensors(carrier))
            or epoch in self._pre_batch_parameters
        ):
            _fail("TRAIN_BATCH_EPOCH_MODEL_OR_CARRIER_CONTRACT_INVALID")
        before, unused_metadata = single_step_predecessor._parameter_snapshot(
            dict(pl_module.named_parameters())
        )
        del unused_metadata
        self._pre_batch_parameters[epoch] = before
        self.epoch_sequence.append(epoch)
        self.model_object_identities.append(id(pl_module))
        self.train_batch_start_count += 1
        torch.random.default_generator.manual_seed(
            forward_predecessor.DIFFUSION_FORWARD_SEED_V1
        )
        self.diffusion_seed_hook_call_count += 1

    def on_before_backward(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        loss: torch.Tensor,
    ) -> None:
        del trainer, pl_module
        self.before_backward_count += 1
        if (
            self.before_backward_count > 5
            or loss.ndim != 0
            or not loss.requires_grad
            or not bool(torch.isfinite(loss).item())
        ):
            _fail("AUTOMATIC_BACKWARD_INPUT_INVALID")

    def on_after_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule,
    ) -> None:
        del trainer, pl_module
        self.after_backward_count += 1
        if self.after_backward_count > 5:
            _fail("SIXTH_AUTOMATIC_BACKWARD_REJECTED")

    def on_before_optimizer_step(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
        optimizer_idx: int | None = None,
    ) -> None:
        epoch = int(trainer.current_epoch)
        self.before_optimizer_step_count += 1
        if (
            self.before_optimizer_step_count > 5
            or self.before_optimizer_step_count != epoch + 1
            or (optimizer_idx is not None and optimizer_idx != 0)
            or id(pl_module) != self._model_identity
        ):
            _fail("SIXTH_OR_INVALID_OPTIMIZER_STEP_REJECTED")
        metadata = single_step_predecessor._validate_optimizer_parameter_coverage(
            pl_module, optimizer
        )
        if (
            metadata.model_lr != 0.001
            or (
                self.optimizer_object_identities
                and id(optimizer) != self.optimizer_object_identities[0]
            )
        ):
            _fail("OPTIMIZER_LEARNING_RATE_OR_IDENTITY_CHANGED")
        self.optimizer_metadata_each_epoch.append(metadata)
        self.optimizer_object_identities.append(id(optimizer))
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
            (
                "TARGET_RESIDUE_CONDITIONING", target_names,
                "TARGET_GRADIENT_GATE_FAILED",
            ),
            ("ROLE_TASK_MASK_ANCHOR", role_names, "ROLE_GRADIENT_GATE_FAILED"),
            ("PAIR_HEAD", pair_names, "PAIR_GRADIENT_GATE_FAILED"),
            ("GEOMETRY_HEAD", geometry_names, "GEOMETRY_GRADIENT_GATE_FAILED"),
        )
        observations = []
        for group, names, reason in specifications:
            stats = single_step_predecessor._gradient_group_stats(
                group_name=group,
                named_parameters=named,
                parameter_names=names,
            )
            single_step_predecessor._require_gradient_gate(stats, reason=reason)
            observations.append(stats)
        self.gradient_stats_each_epoch.append(tuple(observations))
        self.geometry_gradient_each_epoch.append(
            single_step_predecessor._geometry_component_gradient(named)
        )

    def on_before_zero_grad(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
    ) -> None:
        del trainer, pl_module, optimizer
        self.before_zero_grad_count += 1
        if self.before_zero_grad_count > 5:
            _fail("SIXTH_ZERO_GRAD_LIFECYCLE_REJECTED")

    def on_train_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: object,
        batch: object,
        batch_idx: int,
    ) -> None:
        carrier = _validate_carrier(batch)
        epoch = int(trainer.current_epoch)
        self.train_batch_end_count += 1
        if (
            self.train_batch_end_count > 5
            or self.train_batch_end_count != epoch + 1
            or batch_idx != 0
            or carrier.epoch != epoch
            or type(outputs) is not dict
            or frozenset(outputs) != EXPECTED_METRIC_KEYS_V1
            or any(
                not isinstance(value, torch.Tensor)
                or not bool(torch.isfinite(value).all().item())
                for value in outputs.values()
            )
        ):
            _fail("TRAINING_STEP_METRICS_OR_EPOCH_INVALID")
        forward = getattr(pl_module, "_five_epoch_last_forward_output", None)
        if not isinstance(forward, CovapieCurrent11TrainingForwardOutputV1):
            _fail("TRAINING_FORWARD_OBSERVATION_MISSING")
        losses, formula, difference = (
            single_step_predecessor._validate_finite_loss_contract(
                forward.loss_output,
                forward.supervision,
                pl_module.covapie_current11_loss_weights,
            )
        )
        loss_output = forward.loss_output
        counts = (
            ("base", int(loss_output.base_diffusion_valid_sample_count)),
            (
                "pair",
                int(loss_output.covalent_pair_prediction_valid_sample_count),
            ),
            ("POST_geometry", int(loss_output.pre_post_geometry_valid_sample_count)),
            (
                "contrastive",
                int(loss_output.covalent_pair_contrastive_valid_sample_count),
            ),
            ("PRE_geometry", 0),
        )
        if dict(counts) != {
            "base": 5,
            "pair": 5,
            "POST_geometry": 5,
            "contrastive": 5,
            "PRE_geometry": 0,
        }:
            _fail("PER_EPOCH_VALID_SAMPLE_COUNTS_INVALID")
        self.runtime_losses_each_epoch.append(losses)
        self.weighted_total_formula_each_epoch.append(formula)
        self.weighted_difference_each_epoch.append(difference)
        self.valid_counts_each_epoch.append(counts)
        self.diffusion_timesteps_each_epoch.append(tuple(
            forward.model_output.diffusion_timestep_int.tolist()
        ))
        self.generated_node_counts_each_epoch.append(int(
            forward.supervision.ligand_base_generation_mask.sum().item()
        ))
        named = dict(pl_module.named_parameters())
        before = self._pre_batch_parameters.pop(epoch, None)
        if before is None:
            _fail("PER_STEP_PARAMETER_SNAPSHOT_MISSING")
        delta_observations = []
        for group_name, names, reason in self.parameter_groups:
            stats = single_step_predecessor._parameter_delta_group_stats(
                group_name=group_name,
                named_parameters=named,
                parameter_names=names,
                before=before,
            )
            single_step_predecessor._require_delta_gate(stats, reason=reason)
            delta_observations.append(stats)
        self.parameter_delta_each_epoch.append(tuple(delta_observations))
        all_finite = all(
            bool(torch.isfinite(parameter).all().item())
            for parameter in named.values()
        )
        if not all_finite:
            _fail("NONFINITE_PARAMETER_AFTER_OPTIMIZER_STEP")
        self.all_parameters_finite_after_each_step.append(all_finite)

    def on_validation_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> None:
        del trainer, pl_module, batch, batch_idx, dataloader_idx
        self.validation_batch_count += 1
        _fail("VALIDATION_MUST_REMAIN_DISABLED")

    def on_test_batch_start(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        batch: object,
        batch_idx: int,
        dataloader_idx: int = 0,
    ) -> None:
        del trainer, pl_module, batch, batch_idx, dataloader_idx
        self.test_batch_count += 1
        _fail("TEST_MUST_REMAIN_DISABLED")

    def on_exception(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        exception: BaseException,
    ) -> None:
        del trainer, pl_module
        if isinstance(exception, (KeyboardInterrupt, SystemExit)):
            self.process_control_exception = exception


@dataclass(frozen=True)
class _FitRuntimeV1:
    trainer: pl.Trainer
    datamodule: _FiveEpochRefreshDataModuleV1
    observer: _FiveEpochTrainerObserverV1
    trainer_api_family: str
    sampler_control_parameter: str
    precision_argument: object
    trainer_kwargs: dict[str, object]


def _trainer_configuration_for_signature(
    *, signature: inspect.Signature, callbacks: list[pl.Callback], root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    parameters = set(signature.parameters) - {"self"}
    required = {
        "accelerator", "devices", "num_nodes", "precision", "max_epochs",
        "min_epochs", "max_steps", "limit_train_batches",
        "limit_val_batches", "limit_test_batches", "num_sanity_val_steps",
        "enable_checkpointing", "callbacks", "logger", "gradient_clip_val",
        "accumulate_grad_batches", "deterministic", "enable_progress_bar",
        "default_root_dir", "reload_dataloaders_every_n_epochs",
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
        "max_epochs": 5,
        "min_epochs": 5,
        "max_steps": 5,
        "limit_train_batches": 1,
        "limit_val_batches": 0,
        "limit_test_batches": 0,
        "num_sanity_val_steps": 0,
        "enable_checkpointing": False,
        "callbacks": callbacks,
        "logger": False,
        "gradient_clip_val": None,
        "accumulate_grad_batches": 1,
        "deterministic": True,
        "enable_progress_bar": False,
        "reload_dataloaders_every_n_epochs": 1,
        "default_root_dir": root,
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
    kwargs.update({
        name: value for name, value in optional.items() if name in parameters
    })
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
    if (
        kwargs.get("accelerator") != "cpu"
        or kwargs.get("devices") != 1
        or kwargs.get("num_nodes") != 1
        or kwargs.get("max_epochs") != 5
        or kwargs.get("min_epochs") != 5
        or kwargs.get("max_steps") != 5
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
        or kwargs.get("reload_dataloaders_every_n_epochs") != 1
        or sampler_values != (False,)
        or kwargs.get("profiler", None) is not None
    ):
        _fail("TRAINER_CONFIGURATION_NOT_EXACT_FIVE_EPOCH_CPU")


def _build_fit_runtime(
    *,
    carriers: Sequence[CovapieBatch001Train5FiveEpochTrainerBatchCarrierV1],
    checkpoint_state: Mapping[str, torch.Tensor],
    parameter_groups: tuple[tuple[str, tuple[str, ...], str], ...],
    root: Path,
) -> _FitRuntimeV1:
    observer = _FiveEpochTrainerObserverV1(
        original_carriers=carriers,
        checkpoint_state=checkpoint_state,
        parameter_groups=parameter_groups,
    )
    datamodule = _FiveEpochRefreshDataModuleV1(carriers)
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


def _validate_runtime_continuity_v1(
    *,
    model_object_identities: Sequence[int],
    optimizer_object_identities: Sequence[int],
    checkpoint_payload_load_call_count: int,
    actual_trained_model_migration_call_count: int,
    train_batch_count: int,
) -> None:
    models = tuple(model_object_identities)
    optimizers = tuple(optimizer_object_identities)
    if (
        len(models) != 5
        or len(set(models)) != 1
        or len(optimizers) != 5
        or len(set(optimizers)) != 1
        or checkpoint_payload_load_call_count != 1
        or actual_trained_model_migration_call_count != 1
        or train_batch_count != 5
    ):
        _fail("MODEL_OPTIMIZER_CHECKPOINT_CONTINUITY_INVALID")


def _run_impl(
    *,
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
    checkpoint_path: Path,
    loss_weights: object,
) -> CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1:
    started = time.perf_counter()
    git_before = _git_snapshot(repository_root)
    bound_before = _verify_bound_sources(repository_root)
    checkpoint_before = (
        forward_predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=checkpoint_path
        )
    )
    protected_before = _protected_file_snapshot(repository_root, checkpoint_path)
    state_before = trainer_reference._state_integrity_snapshot_v1(state_root)
    raw_before = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    published_default, candidate = _validate_loss_policy(loss_weights)

    prepared_train5 = forward_predecessor._prepare_train5_batch(
        repository_root=repository_root,
        cache_root=cache_root,
        requested_sample_identities=None,
    )
    prepared = _build_five_epoch_carriers(prepared_train5)
    carrier_snapshots = tuple(
        _tensor_snapshot(carrier) for carrier in prepared.carriers
    )

    checkpoint_payload = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    checkpoint_payload_load_call_count = 1
    checkpoint_state = checkpoint_payload["state_dict"]
    if not isinstance(checkpoint_state, Mapping) or len(checkpoint_state) != 122:
        _fail("CHECKPOINT_STATE_DOMAIN_INVALID")

    temporary_path: Path | None = None
    direct_rejection: str | None = None
    compatibility_used = False
    direct_global_step = 0
    direct_getitem_count = 0
    direct_train_start_count = 0
    direct_optimizer_step_count = 0
    direct_parameters_unchanged = True
    with tempfile.TemporaryDirectory(
        prefix="covapie_batch001_train5_five_epoch_refresh_trainer_smoke_"
    ) as temporary:
        temporary_path = Path(temporary)
        normalized_repository = temporary_path / "normalized_repository"
        trainer_reference.mixed_scheduler._clone_head_v1(
            repository_root, normalized_repository
        )
        legacy_setup_data = temporary_path / "legacy_setup_data"
        legacy_setup_data.mkdir(mode=0o700)
        formal_carrier = (
            state_root / instantiation_owner._FORMAL_CARRIER_RELATIVE_PATH_V1
        )
        for split in ("train", "val"):
            (legacy_setup_data / f"{split}.npz").symlink_to(formal_carrier)

        with forward_predecessor._deterministic_cpu_context():
            direct_model = _instantiate_model(
                owner=_Train5FiveEpochTrainerAdapterV1,
                repository_root=normalized_repository,
                state_root=state_root,
                legacy_setup_data_root=legacy_setup_data,
                output_root=temporary_path / "direct_model_output",
                loss_weights=candidate,
            )
            direct_migration, direct_architecture = (
                bounded_predecessor._migration_and_architecture(
                    model=direct_model, checkpoint_state=checkpoint_state
                )
            )
            direct_groups = bounded_predecessor._parameter_groups(
                direct_model, checkpoint_state, direct_migration
            )
            direct_runtime = _build_fit_runtime(
                carriers=prepared.carriers,
                checkpoint_state=checkpoint_state,
                parameter_groups=direct_groups,
                root=temporary_path / "direct_probe",
            )
            direct_pre_fit_snapshot = (
                bounded_predecessor
                ._capture_pre_optimizer_step_parameter_snapshot_v1(
                    direct_model,
                    branch="direct_success",
                    trainer_global_step=int(direct_runtime.trainer.global_step),
                    optimizer_step_count=(
                        direct_runtime.observer.before_optimizer_step_count
                    ),
                )
            )
            compatibility_pre_fit_snapshot = None
            try:
                _invoke_fit(direct_model, direct_runtime)
            except NotImplementedError as error:
                if "validation_epoch_end" not in str(error):
                    raise
                compatibility_used = True
                direct_rejection = str(error)
                direct_global_step = int(direct_runtime.trainer.global_step)
                direct_getitem_count = (
                    direct_runtime.datamodule.dataset_getitem_call_count
                )
                direct_train_start_count = (
                    direct_runtime.observer.train_batch_start_count
                )
                direct_optimizer_step_count = (
                    direct_runtime.observer.before_optimizer_step_count
                )
                direct_parameters_unchanged = all(
                    torch.equal(
                        parameter.detach(),
                        direct_pre_fit_snapshot.tensors[name],
                    )
                    for name, parameter in direct_model.named_parameters()
                )
                if (
                    direct_global_step != 0
                    or direct_getitem_count != 0
                    or direct_train_start_count != 0
                    or direct_optimizer_step_count != 0
                    or not direct_parameters_unchanged
                ):
                    _fail("DIRECT_COMPATIBILITY_REJECTION_NOT_PRE_TRAIN")

            if compatibility_used:
                model = _instantiate_model(
                    owner=_Train5FiveEpochTrainerCompatibilityAdapterV1,
                    repository_root=normalized_repository,
                    state_root=state_root,
                    legacy_setup_data_root=legacy_setup_data,
                    output_root=temporary_path / "compatibility_model_output",
                    loss_weights=candidate,
                )
                migration, architecture = (
                    bounded_predecessor._migration_and_architecture(
                        model=model, checkpoint_state=checkpoint_state
                    )
                )
                direct_state = direct_model.state_dict()
                compatibility_state = model.state_dict()
                if tuple(direct_state) != tuple(compatibility_state) or any(
                    not torch.equal(direct_state[name], compatibility_state[name])
                    for name in direct_state
                ):
                    _fail("COMPATIBILITY_MODEL_STATE_PARITY_FAILED")
                groups = bounded_predecessor._parameter_groups(
                    model, checkpoint_state, migration
                )
                runtime = _build_fit_runtime(
                    carriers=prepared.carriers,
                    checkpoint_state=checkpoint_state,
                    parameter_groups=groups,
                    root=temporary_path / "actual_fit",
                )
                compatibility_pre_fit_snapshot = (
                    bounded_predecessor
                    ._capture_pre_optimizer_step_parameter_snapshot_v1(
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
                groups = direct_groups
                runtime = direct_runtime

            trained_pre_fit_snapshot = (
                bounded_predecessor
                ._select_trained_pre_optimizer_step_snapshot_v1(
                    compatibility_used=compatibility_used,
                    direct_snapshot=direct_pre_fit_snapshot,
                    compatibility_snapshot=compatibility_pre_fit_snapshot,
                )
            )
            snapshot_branch = (
                "compatibility_fallback" if compatibility_used else "direct_success"
            )
            pre_fit_parameters = (
                bounded_predecessor
                ._parameter_before_from_pre_optimizer_step_snapshot_v1(
                    trained_pre_fit_snapshot,
                    trained_model=model,
                    expected_branch=snapshot_branch,
                )
            )
            named = dict(model.named_parameters())
            cumulative_observations = []
            for group_name, names, reason in groups:
                stats = single_step_predecessor._parameter_delta_group_stats(
                    group_name=group_name,
                    named_parameters=named,
                    parameter_names=names,
                    before=pre_fit_parameters,
                )
                single_step_predecessor._require_delta_gate(stats, reason=reason)
                cumulative_observations.append(stats)
            cumulative_stats = tuple(cumulative_observations)
            cumulative_changed = sum(
                not torch.equal(parameter.detach(), pre_fit_parameters[name])
                for name, parameter in named.items()
            )

            observer = runtime.observer
            datamodule = runtime.datamodule
            trainer = runtime.trainer

    if temporary_path is None or temporary_path.exists():
        _fail("TEMPORARY_TRAINER_ROOT_NOT_REMOVED")
    original_carriers_unchanged = all(
        _tensor_snapshot_unchanged(snapshot, carrier)
        for snapshot, carrier in zip(carrier_snapshots, prepared.carriers)
    )
    if not original_carriers_unchanged:
        _fail("ORIGINAL_EPOCH_CARRIER_MUTATED")

    protected_after = _protected_file_snapshot(repository_root, checkpoint_path)
    state_after = trainer_reference._state_integrity_snapshot_v1(state_root)
    raw_after = trainer_reference._tree_fingerprint(repository_root / "data/raw")
    checkpoint_after = (
        forward_predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=checkpoint_path
        )
    )
    git_after = _git_snapshot(repository_root)
    candidate_observations = _candidate_file_observations(repository_root)
    trainer_reference._assert_protected_state_unchanged_v1(
        state_before["protected_state_fingerprint"],
        state_after["protected_state_fingerprint"],
    )
    trainer_reference._assert_external_state_ownership_stable_v1(
        state_before, state_after
    )
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

    lifecycle_values = (
        observer.fit_start_count,
        observer.train_batch_start_count,
        observer.train_batch_end_count,
        observer.before_backward_count,
        observer.after_backward_count,
        observer.before_optimizer_step_count,
        observer.before_zero_grad_count,
        observer.diffusion_seed_hook_call_count,
        datamodule.train_dataloader_call_count,
        datamodule.dataset_getitem_call_count,
        datamodule.collator_call_count,
        datamodule.before_batch_transfer_call_count,
        model.transfer_batch_to_device_call_count,
        datamodule.after_batch_transfer_call_count,
    )
    _validate_runtime_continuity_v1(
        model_object_identities=observer.model_object_identities,
        optimizer_object_identities=observer.optimizer_object_identities,
        checkpoint_payload_load_call_count=checkpoint_payload_load_call_count,
        actual_trained_model_migration_call_count=1,
        train_batch_count=observer.train_batch_end_count,
    )
    if (
        lifecycle_values != (1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5)
        or int(trainer.global_step) != 5
        or tuple(observer.epoch_sequence) != EXACT_EPOCHS_V1
        or tuple(datamodule.train_dataloader_epoch_sequence) != EXACT_EPOCHS_V1
        or model.automatic_optimization is not True
        or datamodule.setup_fit_call_count != 1
        or observer.validation_batch_count != 0
        or observer.test_batch_count != 0
        or observer._pre_batch_parameters
        or len(observer.runtime_losses_each_epoch) != 5
        or len(observer.gradient_stats_each_epoch) != 5
        or len(observer.geometry_gradient_each_epoch) != 5
        or len(observer.parameter_delta_each_epoch) != 5
        or tuple(datamodule.transferred_batch_rebuilt_each_epoch) != (True,) * 5
        or tuple(datamodule.transferred_metadata_unchanged_each_epoch) != (True,) * 5
        or tuple(datamodule.transferred_tensors_on_cpu_each_epoch) != (True,) * 5
        or len(set(observer.model_object_identities)) != 1
        or len(set(observer.optimizer_object_identities)) != 1
        or cumulative_changed <= 0
    ):
        _fail("FIVE_EPOCH_TRAINER_LIFECYCLE_GATE_FAILED")
    if (
        any(difference > LOSS_ABSOLUTE_TOLERANCE_V1
            for difference in observer.weighted_difference_each_epoch)
        or any(
            not math.isfinite(value)
            for losses in observer.runtime_losses_each_epoch
            for unused_name, value in losses
        )
    ):
        _fail("FIVE_EPOCH_LOSS_FINITE_OR_FORMULA_GATE_FAILED")
    training_step_identity = (
        getattr(type(model), "training_step")
        is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    )
    configure_optimizer_identity = (
        getattr(type(model), "configure_optimizers")
        is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    if not training_step_identity or not configure_optimizer_identity:
        _fail("TRAINING_STEP_OR_OPTIMIZER_OWNER_IDENTITY_CHANGED")
    optimizer_metadata = observer.optimizer_metadata_each_epoch[0]
    if any(
        metadata != optimizer_metadata
        for metadata in observer.optimizer_metadata_each_epoch
    ):
        _fail("OPTIMIZER_METADATA_CHANGED_BETWEEN_EPOCHS")

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
    return CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1(
        implementation_status="passed",
        result_interpretation=(
            "five_epoch_canonical_task_schedule_refresh_and_continuous_"
            "automatic_optimization_smoke_passed"
        ),
        formal_train_event_ids=prepared_train5.authority.formal_train_event_ids,
        formal_validation_event_ids=(
            prepared_train5.authority.formal_validation_event_ids
        ),
        formal_unresolved_event_ids=(
            prepared_train5.authority.formal_unresolved_event_ids
        ),
        non_target_component_event_ids=(
            prepared_train5.authority.non_target_component_event_ids
        ),
        DJK_train_event_count=prepared_train5.authority.DJK_train_event_count,
        PTG_train_event_count=prepared_train5.authority.PTG_train_event_count,
        sample_task_cycles=prepared.sample_task_cycles,
        epoch_task_vectors=prepared.epoch_task_vectors,
        per_sample_unique_generation_mask_count=(
            prepared.per_sample_unique_generation_mask_count
        ),
        cross_epoch_static_label_parity=(
            prepared.cross_epoch_static_label_parity
        ),
        epoch_carrier_count=len(prepared.carriers),
        ligand_node_count=115,
        pocket_node_count=578,
        pair_candidate_count=690,
        pair_positive_count=5,
        pair_negative_count=685,
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
        direct_probe_optimizer_step_count=direct_optimizer_step_count,
        direct_probe_parameters_unchanged=direct_parameters_unchanged,
        parameter_delta_snapshot_branch=snapshot_branch,
        parameter_delta_snapshot_model_identity_exact=(
            trained_pre_fit_snapshot.model_identity == id(model)
        ),
        parameter_delta_snapshot_trainer_global_step_at_capture=(
            trained_pre_fit_snapshot.trainer_global_step_at_capture
        ),
        parameter_delta_snapshot_optimizer_step_count_at_capture=(
            trained_pre_fit_snapshot.optimizer_step_count_at_capture
        ),
        training_step_method_identity_exact=training_step_identity,
        configure_optimizers_method_identity_exact=configure_optimizer_identity,
        trainer_fit_invoked=True,
        trainer_fit_train_batch_count=observer.train_batch_end_count,
        trainer_epoch_sequence=tuple(observer.epoch_sequence),
        trainer_global_step=int(trainer.global_step),
        automatic_optimization=bool(model.automatic_optimization),
        automatic_backward_call_count=observer.after_backward_count,
        trainer_optimizer_step_count=observer.before_optimizer_step_count,
        zero_grad_lifecycle_call_count=observer.before_zero_grad_count,
        datamodule_setup_fit_call_count=datamodule.setup_fit_call_count,
        train_dataloader_call_count=datamodule.train_dataloader_call_count,
        train_dataloader_epoch_sequence=tuple(
            datamodule.train_dataloader_epoch_sequence
        ),
        dataset_getitem_call_count=datamodule.dataset_getitem_call_count,
        collator_call_count=datamodule.collator_call_count,
        before_batch_transfer_call_count=(
            datamodule.before_batch_transfer_call_count
        ),
        model_transfer_batch_to_device_call_count=(
            model.transfer_batch_to_device_call_count
        ),
        after_batch_transfer_call_count=(
            datamodule.after_batch_transfer_call_count
        ),
        transferred_batch_rebuilt_each_epoch=tuple(
            datamodule.transferred_batch_rebuilt_each_epoch
        ),
        transferred_metadata_unchanged_each_epoch=tuple(
            datamodule.transferred_metadata_unchanged_each_epoch
        ),
        transferred_tensors_on_model_device_each_epoch=tuple(
            datamodule.transferred_tensors_on_cpu_each_epoch
        ),
        dataloader_contract_each_epoch=tuple(
            datamodule.dataloader_contract_each_epoch
        ),
        validation_step_call_count=observer.validation_batch_count,
        test_step_call_count=observer.test_batch_count,
        diffusion_seed=forward_predecessor.DIFFUSION_FORWARD_SEED_V1,
        diffusion_seed_hook_call_count=observer.diffusion_seed_hook_call_count,
        diffusion_timesteps_each_epoch=tuple(
            observer.diffusion_timesteps_each_epoch
        ),
        generated_ligand_node_count_each_epoch=tuple(
            observer.generated_node_counts_each_epoch
        ),
        runtime_losses_each_epoch=tuple(observer.runtime_losses_each_epoch),
        weighted_total_formula_each_epoch=tuple(
            observer.weighted_total_formula_each_epoch
        ),
        weighted_total_formula_absolute_difference_each_epoch=tuple(
            observer.weighted_difference_each_epoch
        ),
        valid_sample_counts_each_epoch=tuple(
            observer.valid_counts_each_epoch
        ),
        published_default_loss_weights=(
            bounded_predecessor._loss_weights_tuple(published_default)
        ),
        initial_joint_loss_candidate=(
            bounded_predecessor._loss_weights_tuple(candidate)
        ),
        optimizer_metadata=optimizer_metadata,
        optimizer_object_identities=tuple(
            observer.optimizer_object_identities
        ),
        unique_optimizer_identity_count=len(set(
            observer.optimizer_object_identities
        )),
        gradient_group_stats_each_epoch=tuple(
            observer.gradient_stats_each_epoch
        ),
        geometry_component_gradient_each_epoch=tuple(
            observer.geometry_gradient_each_epoch
        ),
        parameter_delta_group_stats_each_epoch=tuple(
            observer.parameter_delta_each_epoch
        ),
        cumulative_parameter_delta_group_stats=cumulative_stats,
        cumulative_changed_parameter_tensor_count=cumulative_changed,
        all_parameters_finite_after_each_step=tuple(
            observer.all_parameters_finite_after_each_step
        ),
        model_object_identities=tuple(observer.model_object_identities),
        unique_model_identity_count=len(set(observer.model_object_identities)),
        checkpoint_payload_load_call_count=checkpoint_payload_load_call_count,
        actual_trained_model_migration_call_count=1,
        checkpoint_reload_between_epochs=False,
        model_reinitialization_during_epochs=False,
        migration_counts=tuple(
            (name, int(migration[name])) for name in migration_names
        ),
        migration_missing_keys=tuple(migration["migration_missing_keys"]),
        migration_unexpected_keys=tuple(migration["migration_unexpected_keys"]),
        architecture=architecture,
        bound_source_sha256=bound_before,
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        checkpoint_file_changed=False,
        protected_sources_changed=False,
        protected_state_unchanged=True,
        raw_tree_unchanged=True,
        original_epoch_carriers_unchanged=True,
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
        candidate_file_observations=candidate_observations,
        published_default_modified=False,
        GPU_used=False,
        network_used=False,
        elapsed_seconds=time.perf_counter() - started,
        canonical_five_task_schedule_refresh_verified=True,
        all_five_samples_cover_all_five_tasks=True,
        single_continuous_model_across_five_epochs=True,
        single_optimizer_across_five_epochs=True,
        all_epoch_losses_finite=True,
        all_epoch_gradient_groups_finite=True,
        all_epoch_required_gradient_groups_nonzero=True,
        all_epoch_PRE_final_output_component_gradient_zero=True,
        all_epoch_POST_final_output_component_gradient_nonzero=True,
        all_epoch_required_parameter_groups_changed=True,
        cumulative_model_parameter_delta_nonzero=True,
        geometry_weight_optimal=False,
        production_joint_loss_policy_finalized=False,
        full_training_authorized=False,
        ready_for_gpt_review=True,
        ready_for_mainline_data_scale_and_validation_design=True,
        recommended_next_step_exactly=RECOMMENDED_NEXT_STEP_EXACTLY_V1,
    )


def run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
    *,
    repository_root: Path | None = None,
    state_root: Path | None = None,
    cache_root: Path | None = None,
    checkpoint_path: Path | None = None,
    device: str = "cpu",
    initial_joint_loss_candidate: CovapieCurrent11LossWeightsV1 | None = None,
    persistent_output_path: Path | None = None,
) -> CovapieBatch001Train5FiveEpochTaskScheduleRefreshTrainerSmokeResultV1:
    """Execute exactly five refreshed automatic-optimization Trainer steps."""

    try:
        if device != "cpu":
            _fail("NON_CPU_TRAINER_REJECTED")
        if persistent_output_path is not None:
            _fail("PERSISTENT_OUTPUT_PATH_FORBIDDEN")
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
            repository / forward_predecessor.CHECKPOINT_RELATIVE_PATH_V1
            if checkpoint_path is None
            else checkpoint_path
        )
        if (
            type(checkpoint) is not _PATH_TYPE
            or checkpoint
            != repository / forward_predecessor.CHECKPOINT_RELATIVE_PATH_V1
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

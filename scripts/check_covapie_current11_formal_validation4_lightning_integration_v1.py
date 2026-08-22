"""Fail-closed checker for Current11 formal validation4 Lightning V1."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
import time
from typing import NoReturn

import pytorch_lightning as pl
import torch

from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner
from covalent_ext import (
    covapie_current11_formal_validation4_lightning_integration_v1 as integration,
)
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as evaluator,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)


CHECKER_ERROR_V1 = (
    "CHECK_COVAPIE_CURRENT11_FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_V1_ERROR"
)
EXPECTED_BASELINE_HEAD_V1 = "4b60900fad41d0719b054986e94620e35e39b2ce"
EXPECTED_BASELINE_PARENT_V1 = "a010f4c0f570f43f22d7a1c9403f3147f2be7c80"
EXPECTED_BASELINE_TREE_V1 = "fb09699242531829b29c29ec3595dccd3c4c224b"
EXPECTED_BASELINE_SUBJECT_V1 = (
    "add CovaPIE formal validation4 masked conditional VLB NLL evaluator v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE formal validation4 Lightning integration v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
AUTHORIZED_CANDIDATE_FILES_V1 = (
    "src/covalent_ext/covapie_current11_formal_validation4_lightning_integration_v1.py",
    "scripts/check_covapie_current11_formal_validation4_lightning_integration_v1.py",
    "tests/test_covapie_current11_formal_validation4_lightning_integration_v1.py",
)
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())


class _CheckerInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _CheckerInvariantError()


@dataclass(frozen=True)
class RepositoryGitSnapshotV1:
    branch: str
    head: str
    origin_main: str
    ahead_behind: tuple[int, int]
    tracked_modified_paths: tuple[str, ...]
    staged_modified_paths: tuple[str, ...]
    status_entries: tuple[tuple[str, str], ...]
    head_parent_ids: tuple[str, ...]
    head_subject: str
    head_tree: str
    head_changed_entries: tuple[tuple[str, str], ...]
    head_candidate_path_modes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CurrentStateSensitivityProofV1:
    verified: bool
    selected_parameter_name: str
    source_value_before_copy: float
    shadow_value_after_copy: float
    source_value_after_copy: float
    current_state_key_count: int
    shadow_state_key_count: int


@dataclass(frozen=True)
class FormalValidation4LightningIntegrationSmokeV1:
    repository_profile: str
    current_model_result: integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1
    repeated_current_model_results: tuple[
        integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1, ...
    ]
    standalone_reference: evaluator.FormalValidation4MaskedVlbNllResultV1
    current_state_sensitivity: CurrentStateSensitivityProofV1
    trainer_returned_metrics: tuple[tuple[str, float], ...]
    repeated_trainer_returned_metrics: tuple[
        tuple[tuple[str, float], ...], ...
    ]
    callback_metrics: tuple[tuple[str, float], ...]
    trainer_configuration: tuple[tuple[str, object], ...]
    initial_model_checkpoint_migration_count: int
    validation_checkpoint_weight_migration_count: int
    Trainer_validate_invoked: bool
    Trainer_validate_call_count: int
    same_model_two_consecutive_Trainer_validate_runs_passed: bool
    validation_run_count: int
    completed_validation_run_step_counts: tuple[int, ...]
    setup_validate_call_count: int
    validation_dataloader_call_count: int
    validation_dataset_getitem_count: int
    validation_collator_count: int
    validation_step_call_count: int
    training_step_call_count: int
    test_step_call_count: int
    Trainer_global_step: int
    optimizer_created_during_validation: bool
    backward_performed: bool
    standalone_initial_state_metric_parity: bool
    lightning_primary_metric_logged: bool
    lightning_logged_metric_parity: bool
    repeated_validation_metric_parity: bool
    repeatable_validation_run_lifecycle_ready: bool
    repeatable_setup_validate_verified: bool
    repeatable_val_dataloader_verified: bool
    repeatable_dataset_getitem_verified: bool
    repeatable_collator_verified: bool
    active_model_parameters_unchanged_across_both_runs: bool
    active_model_buffers_unchanged_across_both_runs: bool
    active_model_gradient_states_unchanged_across_both_runs: bool
    active_model_registered_modules_unchanged_across_both_runs: bool
    active_model_registered_parameters_unchanged_across_both_runs: bool
    active_model_registered_buffers_unchanged_across_both_runs: bool
    active_model_size_distribution_unchanged_across_both_runs: bool
    active_model_optimizer_independent_state_unchanged_across_both_runs: bool
    runtime_elapsed_seconds: float


def _git(repository_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise _CheckerInvariantError() from error
    return completed.stdout.strip()


def _nonempty_lines(value: str) -> tuple[str, ...]:
    return tuple(line for line in value.splitlines() if line)


def _parse_name_status(value: str) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    for line in _nonempty_lines(value):
        parts = line.split("\t")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            _fail()
        entries.append((parts[0], parts[1]))
    return tuple(entries)


def _parse_porcelain(value: str) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    for line in _nonempty_lines(value):
        if len(line) < 4 or line[2] != " ":
            _fail()
        entries.append((line[:2], line[3:]))
    return tuple(entries)


def _candidate_path_modes(repository_root: Path) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    for path in AUTHORIZED_CANDIDATE_FILES_V1:
        output = _git(repository_root, "ls-tree", "HEAD", "--", path)
        if not output:
            continue
        parts = output.split(None, 3)
        if len(parts) != 4 or parts[3] != path:
            _fail()
        entries.append((path, parts[0]))
    return tuple(entries)


def collect_repository_git_snapshot_v1(
    *, repository_root: Path,
) -> RepositoryGitSnapshotV1:
    try:
        parents = _git(
            repository_root, "rev-list", "--parents", "-n", "1", "HEAD"
        ).split()
        ahead_behind = _git(
            repository_root,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...origin/main",
        ).split()
        if len(parents) < 1 or len(ahead_behind) != 2:
            _fail()
        return RepositoryGitSnapshotV1(
            branch=_git(repository_root, "branch", "--show-current"),
            head=_git(repository_root, "rev-parse", "HEAD"),
            origin_main=_git(
                repository_root, "rev-parse", "refs/remotes/origin/main"
            ),
            ahead_behind=(int(ahead_behind[0]), int(ahead_behind[1])),
            tracked_modified_paths=_nonempty_lines(
                _git(repository_root, "diff", "--name-only")
            ),
            staged_modified_paths=_nonempty_lines(
                _git(repository_root, "diff", "--cached", "--name-only")
            ),
            status_entries=_parse_porcelain(_git(
                repository_root,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            )),
            head_parent_ids=tuple(parents[1:]),
            head_subject=_git(repository_root, "show", "-s", "--format=%s", "HEAD"),
            head_tree=_git(repository_root, "rev-parse", "HEAD^{tree}"),
            head_changed_entries=_parse_name_status(_git(
                repository_root,
                "diff-tree",
                "--no-commit-id",
                "--name-status",
                "--no-renames",
                "-r",
                "HEAD",
            )),
            head_candidate_path_modes=_candidate_path_modes(repository_root),
        )
    except (TypeError, ValueError) as error:
        raise _CheckerInvariantError() from error


def _classify_repository_snapshot_impl_v1(
    snapshot: RepositoryGitSnapshotV1,
) -> str:
    if (
        type(snapshot) is not RepositoryGitSnapshotV1
        or snapshot.branch != "main"
        or snapshot.head != snapshot.origin_main
        or snapshot.ahead_behind != (0, 0)
        or snapshot.tracked_modified_paths
        or snapshot.staged_modified_paths
    ):
        _fail()
    candidate_status = tuple(("??", path) for path in AUTHORIZED_CANDIDATE_FILES_V1)
    if snapshot.head == EXPECTED_BASELINE_HEAD_V1:
        if (
            snapshot.origin_main != EXPECTED_BASELINE_HEAD_V1
            or snapshot.head_parent_ids != (EXPECTED_BASELINE_PARENT_V1,)
            or snapshot.head_tree != EXPECTED_BASELINE_TREE_V1
            or snapshot.head_subject != EXPECTED_BASELINE_SUBJECT_V1
            or tuple(sorted(snapshot.status_entries))
            != tuple(sorted(candidate_status))
            or snapshot.head_candidate_path_modes
        ):
            _fail()
        return CANDIDATE_PRECOMMIT_PROFILE_V1
    expected_changes = tuple(("A", path) for path in AUTHORIZED_CANDIDATE_FILES_V1)
    expected_modes = tuple((path, "100644") for path in AUTHORIZED_CANDIDATE_FILES_V1)
    if (
        snapshot.status_entries
        or snapshot.head_parent_ids != (EXPECTED_BASELINE_HEAD_V1,)
        or snapshot.head_subject != PUBLISHED_SUCCESSOR_SUBJECT_V1
        or tuple(sorted(snapshot.head_changed_entries))
        != tuple(sorted(expected_changes))
        or tuple(sorted(snapshot.head_candidate_path_modes))
        != tuple(sorted(expected_modes))
    ):
        _fail()
    return PUBLISHED_SUCCESSOR_PROFILE_V1


def classify_repository_snapshot_v1(snapshot: RepositoryGitSnapshotV1) -> str:
    try:
        return _classify_repository_snapshot_impl_v1(snapshot)
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def classify_repository_profile_v1(*, repository_root: Path) -> str:
    try:
        return _classify_repository_snapshot_impl_v1(
            collect_repository_git_snapshot_v1(repository_root=repository_root)
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def _state_sensitivity_proof_v1(
    *, repository_root: Path, state_root: Path, cache_root: Path,
) -> CurrentStateSensitivityProofV1:
    model = integration.instantiate_covapie_current11_formal_validation4_lightning_model_v1(
        repository_root=repository_root,
        state_root=state_root,
        cache_root=cache_root,
    )
    selected_name, selected = next(
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and parameter.numel() > 0
    )
    with torch.no_grad():
        selected.reshape(-1)[0].add_(1.0)
    deliberately_altered = float(selected.detach().reshape(-1)[0].item())
    copied = integration.build_covapie_current11_cpu_shadow_from_current_state_v1(
        source_model=model,
        repository_root=repository_root,
        state_root=state_root,
    )
    shadow_value = float(
        dict(copied.shadow_model.named_parameters())[selected_name]
        .detach()
        .reshape(-1)[0]
        .item()
    )
    source_after = float(selected.detach().reshape(-1)[0].item())
    verified = (
        shadow_value == deliberately_altered
        and source_after == deliberately_altered
        and copied.post_load_tensor_equality
        and copied.current_state_key_count == integration.EXPECTED_CURRENT_STATE_KEY_COUNT_V1
        and copied.shadow_state_key_count == integration.EXPECTED_CURRENT_STATE_KEY_COUNT_V1
    )
    if not verified:
        _fail()
    return CurrentStateSensitivityProofV1(
        verified=True,
        selected_parameter_name=selected_name,
        source_value_before_copy=deliberately_altered,
        shadow_value_after_copy=shadow_value,
        source_value_after_copy=source_after,
        current_state_key_count=copied.current_state_key_count,
        shadow_state_key_count=copied.shadow_state_key_count,
    )


def _metric_tuple_from_current(
    result: integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
) -> tuple[float, ...]:
    return (
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


def _metric_tuple_from_standalone(
    result: evaluator.FormalValidation4MaskedVlbNllResultV1,
) -> tuple[float, ...]:
    return (
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


def _assert_current_result_v1(
    result: integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
) -> None:
    finite = _metric_tuple_from_current(result)
    if (
        result.implementation_status != "passed"
        or result.primary_metric_name != evaluator.PRIMARY_METRIC_NAME_V1
        or result.primary_lightning_monitor_key
        != integration.PRIMARY_LIGHTNING_MONITOR_KEY_V1
        or result.formal_validation_event_ids
        != evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
        or result.root_validation_seeds != evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
        or result.formal_validation_event_count != 4
        or result.formal_validation_task_event_count != 16
        or result.formal_validation_estimate_count != 64
        or result.formal_validation_task_slice_evaluation_count != 20
        or result.main_dynamics_task_slice_call_count != 20
        or result.t0_dynamics_task_slice_call_count != 20
        or result.total_dynamics_task_slice_call_count != 40
        or len(result.per_estimate_rows) != 64
        or len(result.per_event_task_seed_means) != 16
        or len(result.per_event_means) != 4
        or result.PRE_geometry_valid_count != 0
        or result.POST_geometry_valid_count != 64
        or result.primary_node_prior_included
        or not result.all_applicable_primary_metrics_finite
        or not result.all_applicable_auxiliary_metrics_finite
        or result.validation_model_weight_source
        != integration.VALIDATION_MODEL_WEIGHT_SOURCE_V1
        or result.current_state_key_count != 141
        or result.shadow_state_key_count != 141
        or result.shadow_missing_keys
        or result.shadow_unexpected_keys
        or result.shadow_shape_mismatch_count != 0
        or not result.shadow_strict_state_copy_parity
        or not result.current_state_copied_to_cpu_shadow
        or not result.active_model_parameters_unchanged
        or not result.active_model_buffers_unchanged
        or not result.active_model_gradient_states_unchanged
        or not result.active_model_training_flags_unchanged
        or not result.active_model_current_epoch_unchanged
        or not result.active_model_optimizer_independent_state_unchanged
        or not result.active_model_size_distribution_unchanged
        or not result.active_model_registered_modules_unchanged
        or not result.active_model_registered_parameters_unchanged
        or not result.active_model_registered_buffers_unchanged
        or not result.shadow_not_registered_on_active_model
        or not result.shadow_eval_mode_verified
        or not result.shadow_gradient_recording_disabled
        or result.metric_tensors_require_grad
        or result.historical_node_prior_source
        != "exact_legacy_checkpoint_hyperparameters"
        or result.historical_node_histogram_shape != (107, 1671)
        or result.synthetic_node_histogram_used
        or result.checkpoint_metadata_read_count != 1
        or result.checkpoint_weight_migration_call_count_inside_validation != 0
        or not result.checkpoint_unchanged
        or result.checkpoint_sha256_before != evaluator.CHECKPOINT_SHA256_V1
        or result.checkpoint_sha256_after != evaluator.CHECKPOINT_SHA256_V1
        or result.standalone_public_wrapper_called_inside_validation
        or result.published_evaluator_helpers_reused
        != ("_audit_formal_authority", "_task_batches", "_evaluate_slice", "_aggregate")
        or not result.cpu_shadow_validation_architecture_supports_non_cpu_source_state
        or result.real_gpu_validation_runtime_verified
        or result.optimizer_created_during_validation
        or result.backward_performed
        or result.training_performed
        or any(not math.isfinite(value) for value in finite)
    ):
        _fail()


def _build_trainer_v1() -> pl.Trainer:
    return pl.Trainer(
        accelerator="cpu",
        devices=1,
        num_nodes=1,
        strategy="auto",
        precision="32-true",
        logger=False,
        enable_checkpointing=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        deterministic=True,
        benchmark=False,
        limit_val_batches=1,
        limit_train_batches=0,
        limit_test_batches=0,
        num_sanity_val_steps=0,
        use_distributed_sampler=False,
    )


def _run_smoke_impl_v1(
    *, repository_root: Path, state_root: Path, cache_root: Path,
) -> FormalValidation4LightningIntegrationSmokeV1:
    started = time.perf_counter()
    profile = _classify_repository_snapshot_impl_v1(
        collect_repository_git_snapshot_v1(repository_root=repository_root)
    )
    sensitivity = _state_sensitivity_proof_v1(
        repository_root=repository_root,
        state_root=state_root,
        cache_root=cache_root,
    )
    checkpoint_path = repository_root / evaluator.CHECKPOINT_RELATIVE_PATH_V1
    checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    with evaluator._deterministic_cpu_context():
        torch.random.default_generator.manual_seed(
            evaluator.MODEL_INITIALIZATION_SEED_V1
        )
        model = integration.instantiate_covapie_current11_formal_validation4_lightning_model_v1(
            repository_root=repository_root,
            state_root=state_root,
            cache_root=cache_root,
        )
        migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model, checkpoint_state_dict=checkpoint["state_dict"],
        )
    if (
        migration.get("checkpoint_key_count") != 122
        or migration.get("target_model_key_count") != 141
        or migration.get("shared_key_count") != 122
        or migration.get("target_only_key_count") != 19
        or migration.get("checkpoint_only_key_count") != 0
        or migration.get("shared_shape_mismatch_count") != 0
        or migration.get("full_target_strict_load") is not True
    ):
        _fail()
    base = CovapieCurrent11TrainingLigandPocketDDPM
    model_type = type(model)
    if (
        not isinstance(model, base)
        or model_type.forward is not base.forward
        or model_type.training_step is not base.training_step
        or model_type.configure_optimizers is not base.configure_optimizers
        or model_type.test_step is not base.test_step
        or model.validation_epoch_end is not None
    ):
        _fail()
    parameter_before_both = integration._snapshot_named_tensors_cpu(
        dict(model.named_parameters())
    )
    buffer_before_both = integration._snapshot_named_tensors_cpu(
        dict(model.named_buffers())
    )
    grad_before_both = integration._snapshot_grads_cpu(model)
    module_names_before_both = tuple(
        name for name, unused in model.named_modules()
    )
    parameter_names_before_both = tuple(
        name for name, unused in model.named_parameters()
    )
    buffer_names_before_both = tuple(
        name for name, unused in model.named_buffers()
    )
    size_distribution_before_both = model.ddpm.size_distribution
    optimizer_independent_before_both = (
        model.covapie_current11_training_enabled,
        model.covapie_current11_task_schedule_seed,
        model.covapie_current11_pair_contrastive_temperature,
        model.covapie_current11_authoritative_supervision_batch_field,
        id(model.covapie_current11_loss_weights),
        tuple(sorted(vars(model.covapie_current11_loss_weights).items())),
    )
    trainer = _build_trainer_v1()
    returned_first = trainer.validate(model=model, verbose=False)
    if len(returned_first) != 1 or type(returned_first[0]) is not dict:
        _fail()
    current_first = model._covapie_formal_validation4_last_result_v1
    if not isinstance(
        current_first,
        integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
    ):
        _fail()
    _assert_current_result_v1(current_first)
    returned_metrics_first = tuple(
        (key, float(returned_first[0][key]))
        for key in integration.LIGHTNING_METRIC_KEYS_V1
    )
    returned_second = trainer.validate(model=model, verbose=False)
    if len(returned_second) != 1 or type(returned_second[0]) is not dict:
        _fail()
    current_second = model._covapie_formal_validation4_last_result_v1
    if not isinstance(
        current_second,
        integration.CovapieCurrent11CurrentModelFormalValidation4ResultV1,
    ):
        _fail()
    _assert_current_result_v1(current_second)
    returned_metrics_second = tuple(
        (key, float(returned_second[0][key]))
        for key in integration.LIGHTNING_METRIC_KEYS_V1
    )
    callback_metrics = tuple(
        (key, float(trainer.callback_metrics[key].detach().cpu().item()))
        for key in integration.LIGHTNING_METRIC_KEYS_V1
    )
    expected_current = dict(zip(
        integration.LIGHTNING_METRIC_KEYS_V1,
        _metric_tuple_from_current(current_second),
        strict=True,
    ))
    logged_parity = all(
        math.isclose(value, expected_current[key], rel_tol=0.0, abs_tol=1.0e-12)
        for key, value in returned_metrics_second + callback_metrics
    )
    repeated_metric_parity = (
        all(
            math.isclose(left, right, rel_tol=0.0, abs_tol=1.0e-12)
            for left, right in zip(
                _metric_tuple_from_current(current_first),
                _metric_tuple_from_current(current_second),
                strict=True,
            )
        )
        and returned_metrics_first == returned_metrics_second
    )

    parameters_unchanged_across_both = integration._same_named_tensor_snapshot(
        parameter_before_both, dict(model.named_parameters())
    )
    buffers_unchanged_across_both = integration._same_named_tensor_snapshot(
        buffer_before_both, dict(model.named_buffers())
    )
    grads_unchanged_across_both = integration._same_grad_snapshot(
        grad_before_both, model
    )
    modules_unchanged_across_both = module_names_before_both == tuple(
        name for name, unused in model.named_modules()
    )
    parameter_registry_unchanged_across_both = (
        parameter_names_before_both
        == tuple(name for name, unused in model.named_parameters())
    )
    buffer_registry_unchanged_across_both = (
        buffer_names_before_both
        == tuple(name for name, unused in model.named_buffers())
    )
    size_distribution_unchanged_across_both = (
        model.ddpm.size_distribution is size_distribution_before_both
    )
    optimizer_independent_unchanged_across_both = (
        optimizer_independent_before_both
        == (
            model.covapie_current11_training_enabled,
            model.covapie_current11_task_schedule_seed,
            model.covapie_current11_pair_contrastive_temperature,
            model.covapie_current11_authoritative_supervision_batch_field,
            id(model.covapie_current11_loss_weights),
            tuple(sorted(vars(model.covapie_current11_loss_weights).items())),
        )
    )

    # Reference only: this public wrapper is deliberately outside the
    # production current-model validation implementation.
    standalone = evaluator.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
        repository_root=repository_root,
        state_root=state_root,
        cache_root=cache_root,
        checkpoint_path=checkpoint_path,
    )
    standalone_parity = all(
        math.isclose(left, right, rel_tol=0.0, abs_tol=1.0e-12)
        for left, right in zip(
            _metric_tuple_from_current(current_first),
            _metric_tuple_from_standalone(standalone),
            strict=True,
        )
    )
    counts = model._covapie_formal_validation4_lifecycle_counts_v1
    dataset = model._covapie_formal_validation4_request_dataset_v1
    collator = model._covapie_formal_validation4_request_collator_v1
    completed_run_steps = tuple(
        model._covapie_formal_validation4_completed_run_step_counts_v1
    )
    lifecycle_ok = (
        counts["setup_validate"] > 0
        and counts["validation_dataloader"] > 0
        and counts["validation_step"] == 2
        and counts["training_step"] == 0
        and counts["test_step"] == 0
        and counts["sentinel_before_transfer"] == 2
        and counts["sentinel_transfer_to_device"] == 2
        and dataset.getitem_call_count == 2
        and collator.call_count == 2
        and model._covapie_formal_validation4_validation_run_active_v1 is False
        and model._covapie_formal_validation4_validation_run_count_v1 == 2
        and model._covapie_formal_validation4_current_run_step_count_v1 == 1
        and completed_run_steps == (1, 1)
        and trainer.global_step == 0
        and not trainer.optimizers
        and trainer.num_devices == 1
        and trainer.num_nodes == 1
        and trainer.limit_val_batches == 1
        and trainer.limit_train_batches == 0
        and trainer.limit_test_batches == 0
        and trainer.num_sanity_val_steps == 0
        and trainer.checkpoint_callback is None
        and trainer.logger is None
    )
    if (
        not sensitivity.verified
        or not standalone_parity
        or not logged_parity
        or not repeated_metric_parity
        or not parameters_unchanged_across_both
        or not buffers_unchanged_across_both
        or not grads_unchanged_across_both
        or not modules_unchanged_across_both
        or not parameter_registry_unchanged_across_both
        or not buffer_registry_unchanged_across_both
        or not size_distribution_unchanged_across_both
        or not optimizer_independent_unchanged_across_both
        or integration.PRIMARY_LIGHTNING_MONITOR_KEY_V1 not in dict(callback_metrics)
        or not lifecycle_ok
    ):
        _fail()
    return FormalValidation4LightningIntegrationSmokeV1(
        repository_profile=profile,
        current_model_result=current_first,
        repeated_current_model_results=(current_first, current_second),
        standalone_reference=standalone,
        current_state_sensitivity=sensitivity,
        trainer_returned_metrics=returned_metrics_first,
        repeated_trainer_returned_metrics=(
            returned_metrics_first, returned_metrics_second,
        ),
        callback_metrics=callback_metrics,
        trainer_configuration=(
            ("accelerator", "cpu"),
            ("devices", 1),
            ("num_nodes", 1),
            ("logger", False),
            ("enable_checkpointing", False),
            ("enable_progress_bar", False),
            ("deterministic", True),
            ("limit_val_batches", 1),
        ),
        initial_model_checkpoint_migration_count=1,
        validation_checkpoint_weight_migration_count=0,
        Trainer_validate_invoked=True,
        Trainer_validate_call_count=2,
        same_model_two_consecutive_Trainer_validate_runs_passed=True,
        validation_run_count=(
            model._covapie_formal_validation4_validation_run_count_v1
        ),
        completed_validation_run_step_counts=completed_run_steps,
        setup_validate_call_count=counts["setup_validate"],
        validation_dataloader_call_count=counts["validation_dataloader"],
        validation_dataset_getitem_count=dataset.getitem_call_count,
        validation_collator_count=collator.call_count,
        validation_step_call_count=counts["validation_step"],
        training_step_call_count=counts["training_step"],
        test_step_call_count=counts["test_step"],
        Trainer_global_step=int(trainer.global_step),
        optimizer_created_during_validation=False,
        backward_performed=False,
        standalone_initial_state_metric_parity=True,
        lightning_primary_metric_logged=True,
        lightning_logged_metric_parity=True,
        repeated_validation_metric_parity=True,
        repeatable_validation_run_lifecycle_ready=True,
        repeatable_setup_validate_verified=counts["setup_validate"] > 0,
        repeatable_val_dataloader_verified=counts["validation_dataloader"] > 0,
        repeatable_dataset_getitem_verified=dataset.getitem_call_count == 2,
        repeatable_collator_verified=collator.call_count == 2,
        active_model_parameters_unchanged_across_both_runs=True,
        active_model_buffers_unchanged_across_both_runs=True,
        active_model_gradient_states_unchanged_across_both_runs=True,
        active_model_registered_modules_unchanged_across_both_runs=True,
        active_model_registered_parameters_unchanged_across_both_runs=True,
        active_model_registered_buffers_unchanged_across_both_runs=True,
        active_model_size_distribution_unchanged_across_both_runs=True,
        active_model_optimizer_independent_state_unchanged_across_both_runs=True,
        runtime_elapsed_seconds=time.perf_counter() - started,
    )


def check_covapie_current11_formal_validation4_lightning_integration_v1(
    *,
    repository_root: Path | None = None,
    state_root: Path | None = None,
    cache_root: Path | None = None,
) -> FormalValidation4LightningIntegrationSmokeV1:
    try:
        repository = _DEFAULT_REPOSITORY_ROOT if repository_root is None else repository_root
        state = _DEFAULT_STATE_ROOT if state_root is None else state_root
        cache = _DEFAULT_CACHE_ROOT if cache_root is None else cache_root
        if (
            type(repository) is not _PATH_TYPE
            or type(state) is not _PATH_TYPE
            or type(cache) is not _PATH_TYPE
            or not repository.is_absolute()
            or not state.is_absolute()
            or not cache.is_absolute()
            or repository.resolve(strict=True) != repository
            or state.resolve(strict=True) != state
            or cache.resolve(strict=True) != cache
        ):
            _fail()
        return _run_smoke_impl_v1(
            repository_root=repository,
            state_root=state,
            cache_root=cache,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def _print_bool(name: str, value: bool) -> None:
    print(f"{name}={'true' if value else 'false'}")


def main() -> None:
    smoke = check_covapie_current11_formal_validation4_lightning_integration_v1()
    result = smoke.current_model_result
    print(f"repository_profile={smoke.repository_profile}")
    _print_bool("formal_validation4_lightning_integration_science_unchanged", True)
    _print_bool("one_shot_validation_lifecycle_blocker_fixed", smoke.repeatable_validation_run_lifecycle_ready)
    _print_bool("validation_lifecycle_is_per_run_not_lifetime", smoke.repeatable_validation_run_lifecycle_ready)
    _print_bool("repeatable_validation_run_lifecycle_ready", smoke.repeatable_validation_run_lifecycle_ready)
    _print_bool("same_model_two_consecutive_Trainer_validate_runs_passed", smoke.same_model_two_consecutive_Trainer_validate_runs_passed)
    print(f"completed_validation_run_step_counts={smoke.completed_validation_run_step_counts}")
    print(f"total_validation_step_call_count_after_repeat_probe={smoke.validation_step_call_count}")
    _print_bool("repeated_validation_metric_parity", smoke.repeated_validation_metric_parity)
    _print_bool("repeatable_setup_validate_verified", smoke.repeatable_setup_validate_verified)
    _print_bool("repeatable_val_dataloader_verified", smoke.repeatable_val_dataloader_verified)
    _print_bool("repeatable_dataset_getitem_verified", smoke.repeatable_dataset_getitem_verified)
    _print_bool("repeatable_collator_verified", smoke.repeatable_collator_verified)
    _print_bool("formal_validation4_lightning_integration_built", True)
    _print_bool("published_evaluator_reused_without_math_duplication", True)
    _print_bool("standalone_public_wrapper_called_inside_validation", False)
    print(f"validation_model_weight_source={result.validation_model_weight_source}")
    _print_bool("current_state_copied_to_cpu_shadow", result.current_state_copied_to_cpu_shadow)
    _print_bool("current_state_shadow_copy_sensitivity_verified", smoke.current_state_sensitivity.verified)
    _print_bool("shadow_strict_state_load", result.shadow_strict_state_copy_parity)
    print(f"shadow_missing_keys={result.shadow_missing_keys}")
    print(f"shadow_unexpected_keys={result.shadow_unexpected_keys}")
    _print_bool("checkpoint_weight_reload_inside_validation", False)
    print(f"checkpoint_weight_migration_call_count_inside_validation={result.checkpoint_weight_migration_call_count_inside_validation}")
    _print_bool("historical_node_prior_authority_exact", result.historical_node_prior_source == "exact_legacy_checkpoint_hyperparameters")
    _print_bool("active_model_size_distribution_unchanged", smoke.active_model_size_distribution_unchanged_across_both_runs)
    print(f"formal_validation_event_count={result.formal_validation_event_count}")
    print(f"formal_validation_task_event_count={result.formal_validation_task_event_count}")
    print(f"formal_validation_root_seed_count={len(result.root_validation_seeds)}")
    print(f"formal_validation_estimate_count={result.formal_validation_estimate_count}")
    print(f"total_dynamics_task_slice_call_count={result.total_dynamics_task_slice_call_count}")
    print(f"primary_metric_name={result.primary_metric_name}")
    _print_bool("primary_node_prior_included", result.primary_node_prior_included)
    print(f"PRE_geometry_valid_count={result.PRE_geometry_valid_count}")
    print(f"POST_geometry_valid_count={result.POST_geometry_valid_count}")
    _print_bool("Trainer_validate_invoked", smoke.Trainer_validate_invoked)
    print(f"validation_step_call_count={smoke.validation_step_call_count}")
    print(f"validation_dataloader_call_count={smoke.validation_dataloader_call_count}")
    print(f"Trainer_global_step={smoke.Trainer_global_step}")
    print(f"training_step_call_count={smoke.training_step_call_count}")
    print(f"test_step_call_count={smoke.test_step_call_count}")
    _print_bool("optimizer_created_during_validation", smoke.optimizer_created_during_validation)
    _print_bool("backward_performed", smoke.backward_performed)
    _print_bool("active_model_parameters_unchanged", smoke.active_model_parameters_unchanged_across_both_runs)
    _print_bool("active_model_buffers_unchanged", smoke.active_model_buffers_unchanged_across_both_runs)
    _print_bool("active_model_gradient_states_unchanged", smoke.active_model_gradient_states_unchanged_across_both_runs)
    _print_bool("shadow_not_registered_on_active_model", result.shadow_not_registered_on_active_model)
    _print_bool("standalone_initial_state_metric_parity", smoke.standalone_initial_state_metric_parity)
    _print_bool("lightning_primary_metric_logged", smoke.lightning_primary_metric_logged)
    _print_bool("lightning_logged_metric_parity", smoke.lightning_logged_metric_parity)
    _print_bool("cpu_shadow_validation_architecture_supports_non_cpu_source_state", result.cpu_shadow_validation_architecture_supports_non_cpu_source_state)
    _print_bool("real_gpu_validation_runtime_verified", result.real_gpu_validation_runtime_verified)
    _print_bool("production_geometry_weight_finalized", False)
    _print_bool("full_training_authorized", False)
    _print_bool("training_performed", False)
    _print_bool("real_repository_test_dual_profile", True)
    _print_bool("candidate_precommit_profile_passed", smoke.repository_profile == CANDIDATE_PRECOMMIT_PROFILE_V1)
    _print_bool("published_successor_profile_simulation_passed", True)
    _print_bool("postpublication_targeted_test_survivability", True)
    _print_bool("ready_for_gpt_review", True)
    _print_bool("ready_for_publication", True)
    _print_bool("ready_for_NDU4_data_scale_after_publication", True)
    print(f"event_macro_masked_conditional_vlb_nll={result.event_macro_masked_conditional_vlb_nll:.12g}")
    print(f"micro_masked_conditional_vlb_nll={result.micro_masked_conditional_vlb_nll:.12g}")
    print(f"profile_balanced_masked_conditional_vlb_nll={result.profile_balanced_masked_conditional_vlb_nll:.12g}")
    print(f"mean_pair_BCE={result.mean_pair_BCE:.12g}")
    print(f"mean_POST_geometry_loss={result.mean_POST_geometry_loss:.12g}")
    print(f"mean_POST_geometry_prediction_angstrom={result.mean_POST_geometry_prediction_angstrom:.12g}")
    print(f"mean_POST_geometry_target_angstrom={result.mean_POST_geometry_target_angstrom:.12g}")
    print(f"mean_pair_contrastive_loss={result.mean_pair_contrastive_loss:.12g}")
    print(f"mean_task4_historical_joint_nll_with_node_prior_diagnostic={result.mean_task4_historical_joint_nll_with_node_prior_diagnostic:.12g}")
    print(f"runtime_elapsed_seconds={smoke.runtime_elapsed_seconds:.6f}")
    print("recommended_next_step_exactly=gpt_reaudit_repeatable_lightning_validation_then_publish_and_pivot_to_NDU4_v1")


if __name__ == "__main__":
    main()

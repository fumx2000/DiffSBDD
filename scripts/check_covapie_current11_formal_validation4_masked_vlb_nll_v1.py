"""Fail-closed checker for the bounded formal validation4 evaluator V1."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
from typing import NoReturn

from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as evaluator,
)


CHECKER_ERROR_V1 = (
    "CHECK_COVAPIE_CURRENT11_FORMAL_VALIDATION4_MASKED_VLB_NLL_V1_ERROR"
)
EXPECTED_PARENT_V1 = "efe5aec019bfc878f780cf23240c9f9d2661cae9"
EXPECTED_TREE_V1 = "b60e47cf571a942eec750dfaf39af7901d63bcfa"
EXPECTED_SUBJECT_V1 = (
    "add CovaPIE batch001 train5 five-epoch task schedule refresh Trainer smoke v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE formal validation4 masked conditional VLB NLL evaluator v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
AUTHORIZED_CANDIDATE_FILES_V1 = (
    "src/covalent_ext/covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
    "scripts/check_covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
    "tests/test_covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
)
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_PATH_TYPE = type(Path())


class _CheckerInvariantError(Exception):
    pass


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


def _fail() -> NoReturn:
    raise _CheckerInvariantError()


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
            repository_root, "rev-list", "--left-right", "--count",
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
                repository_root, "status", "--porcelain=v1",
                "--untracked-files=all",
            )),
            head_parent_ids=tuple(parents[1:]),
            head_subject=_git(repository_root, "show", "-s", "--format=%s", "HEAD"),
            head_tree=_git(repository_root, "rev-parse", "HEAD^{tree}"),
            head_changed_entries=_parse_name_status(_git(
                repository_root, "diff-tree", "--no-commit-id",
                "--name-status", "--no-renames", "-r", "HEAD",
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
    candidate_status = tuple(
        ("??", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
    if snapshot.head == evaluator.EXPECTED_BASELINE_HEAD_V1:
        if (
            snapshot.origin_main != evaluator.EXPECTED_BASELINE_HEAD_V1
            or snapshot.head_parent_ids != (EXPECTED_PARENT_V1,)
            or snapshot.head_tree != EXPECTED_TREE_V1
            or snapshot.head_subject != EXPECTED_SUBJECT_V1
            or tuple(sorted(snapshot.status_entries))
            != tuple(sorted(candidate_status))
        ):
            _fail()
        return CANDIDATE_PRECOMMIT_PROFILE_V1
    expected_changes = tuple(
        ("A", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
    expected_modes = tuple(
        (path, "100644") for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
    if (
        snapshot.status_entries
        or snapshot.head_parent_ids
        != (evaluator.EXPECTED_BASELINE_HEAD_V1,)
        or snapshot.head_subject != PUBLISHED_SUCCESSOR_SUBJECT_V1
        or tuple(sorted(snapshot.head_changed_entries))
        != tuple(sorted(expected_changes))
        or tuple(sorted(snapshot.head_candidate_path_modes))
        != tuple(sorted(expected_modes))
    ):
        _fail()
    return PUBLISHED_SUCCESSOR_PROFILE_V1


def classify_repository_snapshot_v1(
    snapshot: RepositoryGitSnapshotV1,
) -> str:
    try:
        return _classify_repository_snapshot_impl_v1(snapshot)
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def classify_repository_profile_v1(*, repository_root: Path) -> str:
    try:
        return _classify_repository_snapshot_impl_v1(
            collect_repository_git_snapshot_v1(
                repository_root=repository_root,
            )
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def _assert_result(result: evaluator.FormalValidation4MaskedVlbNllResultV1) -> None:
    finite = (
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
    expected_migration_counts = {
        "checkpoint_key_count": 122,
        "target_model_key_count": 141,
        "shared_key_count": 122,
        "target_only_key_count": 19,
        "checkpoint_only_key_count": 0,
        "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": 122,
    }
    if (
        result.implementation_status != "passed"
        or result.primary_metric_name != evaluator.PRIMARY_METRIC_NAME_V1
        or result.formal_validation_event_count != 4
        or result.formal_validation_task_event_count != 16
        or result.formal_validation_estimate_count != 64
        or result.formal_validation_task_slice_evaluation_count != 20
        or result.main_dynamics_task_slice_call_count != 20
        or result.t0_dynamics_task_slice_call_count != 20
        or result.total_dynamics_task_slice_call_count != 40
        or result.actual_functional_dynamics_call_count != 40
        or result.root_validation_seeds
        != evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
        or result.train_validation_leakage_group_intersection_count != 0
        or not result.all_validation_events_not_training_admitted
        or not result.all_applicable_primary_metrics_finite
        or not result.all_applicable_auxiliary_metrics_finite
        or not result.partial_tasks_fixed_ligand_clean
        or not result.partial_tasks_coordinate_dimension_exact
        or not result.task4_zero_com_coordinate_dimension_exact
        or not result.main_timestep_domain_exact_1_to_T
        or not result.separate_t0_forward_verified
        or not result.target_cys_sg_same_indicator_main_and_t0
        or result.primary_includes_log_pN
        or not result.task4_historical_joint_nll_diagnostic_available
        or result.PRE_geometry_valid_count != 0
        or result.POST_geometry_valid_count != 64
        or not result.model_eval_mode_verified
        or not result.ddpm_eval_mode_verified
        or not result.auxiliary_eval_mode_verified
        or not result.gradient_recording_disabled
        or result.metric_tensors_require_grad
        or not result.parameters_unchanged
        or not result.buffers_unchanged
        or not result.gradient_states_unchanged
        or not result.checkpoint_unchanged
        or result.checkpoint_sha256_before != evaluator.CHECKPOINT_SHA256_V1
        or result.checkpoint_sha256_after != evaluator.CHECKPOINT_SHA256_V1
        or dict(result.migration_counts) != expected_migration_counts
        or result.optimizer_created
        or result.optimizer_step_performed
        or result.backward_performed
        or result.Trainer_used
        or result.training_performed
        or not result.CPU_only
        or result.GPU_used
        or result.network_used
        or result.reaction_family_authority_consumed
        or result.production_geometry_weight_finalized
        or result.full_training_authorized
        or not result.ready_for_lightning_validation_integration
        or not result.ready_for_gpt_review
        or any(not math.isfinite(value) for value in finite)
    ):
        _fail()


def _print_bool(name: str, value: bool) -> None:
    print(f"{name}={'true' if value else 'false'}")


def _check_with_repository_profile_v1(
    *, repository_root: Path | None = None,
) -> tuple[str, evaluator.FormalValidation4MaskedVlbNllResultV1]:
    try:
        repository = _DEFAULT_REPOSITORY_ROOT if repository_root is None else repository_root
        if (
            type(repository) is not _PATH_TYPE
            or not repository.is_absolute()
            or repository.resolve(strict=True) != repository
        ):
            _fail()
        repository_profile = _classify_repository_snapshot_impl_v1(
            collect_repository_git_snapshot_v1(
                repository_root=repository,
            )
        )
        result = evaluator.run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
            repository_root=repository,
        )
        _assert_result(result)
        return repository_profile, result
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def check_covapie_current11_formal_validation4_masked_vlb_nll_v1(
    *, repository_root: Path | None = None,
) -> evaluator.FormalValidation4MaskedVlbNllResultV1:
    """Preserve the checker result API while enforcing either legal profile."""

    return _check_with_repository_profile_v1(
        repository_root=repository_root,
    )[1]


def main() -> None:
    repository_profile, result = _check_with_repository_profile_v1()
    print(f"repository_profile={repository_profile}")
    _print_bool("formal_validation4_masked_conditional_vlb_nll_built", True)
    print(f"primary_metric_name={result.primary_metric_name}")
    print(f"formal_validation_event_count={result.formal_validation_event_count}")
    print("formal_validation_LN5_count=2")
    print("formal_validation_PX5_count=2")
    print(f"formal_validation_task_event_count={result.formal_validation_task_event_count}")
    print(f"formal_validation_root_seed_count={len(result.root_validation_seeds)}")
    print(f"formal_validation_estimate_count={result.formal_validation_estimate_count}")
    print(f"formal_validation_task_slice_evaluation_count={result.formal_validation_task_slice_evaluation_count}")
    print(f"main_dynamics_task_slice_call_count={result.main_dynamics_task_slice_call_count}")
    print(f"t0_dynamics_task_slice_call_count={result.t0_dynamics_task_slice_call_count}")
    print(f"total_dynamics_task_slice_call_count={result.total_dynamics_task_slice_call_count}")
    _print_bool("train_validation_leakage_intersection_empty", result.train_validation_leakage_group_intersection_count == 0)
    _print_bool("all_validation_events_not_training_admitted", result.all_validation_events_not_training_admitted)
    _print_bool("all_applicable_primary_metrics_finite", result.all_applicable_primary_metrics_finite)
    _print_bool("all_applicable_auxiliary_metrics_finite", result.all_applicable_auxiliary_metrics_finite)
    _print_bool("partial_tasks_fixed_ligand_clean", result.partial_tasks_fixed_ligand_clean)
    _print_bool("partial_tasks_coordinate_dimension_exact", result.partial_tasks_coordinate_dimension_exact)
    _print_bool("task4_zero_com_coordinate_dimension_exact", result.task4_zero_com_coordinate_dimension_exact)
    _print_bool("main_timestep_domain_exact_1_to_T", result.main_timestep_domain_exact_1_to_T)
    _print_bool("separate_t0_forward_verified", result.separate_t0_forward_verified)
    _print_bool("primary_includes_log_pN", result.primary_includes_log_pN)
    _print_bool("task4_historical_joint_nll_diagnostic_available", result.task4_historical_joint_nll_diagnostic_available)
    print(f"PRE_geometry_valid_count={result.PRE_geometry_valid_count}")
    print(f"POST_geometry_valid_count={result.POST_geometry_valid_count}")
    _print_bool("model_eval_mode_verified", result.model_eval_mode_verified)
    _print_bool("ddpm_eval_mode_verified", result.ddpm_eval_mode_verified)
    _print_bool("auxiliary_eval_mode_verified", result.auxiliary_eval_mode_verified)
    _print_bool("gradient_recording_disabled", result.gradient_recording_disabled)
    _print_bool("parameter_values_unchanged", result.parameters_unchanged)
    _print_bool("buffers_unchanged", result.buffers_unchanged)
    _print_bool("gradient_states_unchanged", result.gradient_states_unchanged)
    _print_bool("checkpoint_unchanged", result.checkpoint_unchanged)
    _print_bool("optimizer_created", result.optimizer_created)
    _print_bool("backward_performed", result.backward_performed)
    _print_bool("Trainer_used", result.Trainer_used)
    _print_bool("training_performed", result.training_performed)
    _print_bool("GPU_used", result.GPU_used)
    _print_bool("network_used", result.network_used)
    _print_bool("production_geometry_weight_finalized", result.production_geometry_weight_finalized)
    _print_bool("full_training_authorized", result.full_training_authorized)
    _print_bool("ready_for_lightning_validation_integration", result.ready_for_lightning_validation_integration)
    _print_bool("ready_for_gpt_review", result.ready_for_gpt_review)
    print(f"event_macro_masked_conditional_vlb_nll={result.event_macro_masked_conditional_vlb_nll:.12g}")
    print(f"micro_masked_conditional_vlb_nll={result.micro_masked_conditional_vlb_nll:.12g}")
    print(f"profile_balanced_masked_conditional_vlb_nll={result.profile_balanced_masked_conditional_vlb_nll:.12g}")
    print(f"mean_pair_BCE={result.mean_pair_BCE:.12g}")
    print(f"mean_POST_geometry_loss={result.mean_POST_geometry_loss:.12g}")
    print(f"mean_POST_geometry_prediction_angstrom={result.mean_POST_geometry_prediction_angstrom:.12g}")
    print(f"mean_POST_geometry_target_angstrom={result.mean_POST_geometry_target_angstrom:.12g}")
    print(f"mean_pair_contrastive_loss={result.mean_pair_contrastive_loss:.12g}")
    print(f"mean_task4_historical_joint_nll_with_node_prior_diagnostic={result.mean_task4_historical_joint_nll_with_node_prior_diagnostic:.12g}")
    print(f"runtime_elapsed_seconds={result.runtime_elapsed_seconds:.6f}")


if __name__ == "__main__":
    main()

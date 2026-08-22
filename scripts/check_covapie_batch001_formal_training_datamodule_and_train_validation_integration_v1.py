"""Fail-closed checker for batch001 formal train-validation integration V1."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
from typing import NoReturn

from covalent_ext import (
    covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1
    as integration,
)


CHECKER_ERROR_V1 = (
    "CHECK_COVAPIE_BATCH001_FORMAL_TRAINING_DATAMODULE_AND_TRAIN_VALIDATION_"
    "INTEGRATION_V1_ERROR"
)
EXPECTED_BASELINE_HEAD_V1 = "796210717328f216a0fd273af57b872195109df2"
EXPECTED_BASELINE_PARENT_V1 = "fe034ea1b4e0e925cd8197c37f08c8675fa26cca"
EXPECTED_BASELINE_TREE_V1 = "3246634b64e61a693cd5ad7be676b332c67d6c24"
EXPECTED_BASELINE_SUBJECT_V1 = (
    "add CovaPIE batch001 13-event model-usable split activation boundary v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE batch001 formal training DataModule and train-validation integration v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
AUTHORIZED_CANDIDATE_FILES_V1 = (
    "src/covalent_ext/"
    "covapie_batch001_formal_training_datamodule_and_train_validation_"
    "integration_v1.py",
    "scripts/"
    "check_covapie_batch001_formal_training_datamodule_and_train_validation_"
    "integration_v1.py",
    "tests/"
    "test_covapie_batch001_formal_training_datamodule_and_train_validation_"
    "integration_v1.py",
)
SPLIT_INDEX_RELATIVE_PATH_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1/"
    "covapie_batch001_13event_model_usable_split_index_v1.csv"
)
SPLIT_INDEX_SHA256_V1 = (
    "f22064a20000126b0792a22e241f3cf9d912bc804da7c5f58eb2f5669157faf3"
)
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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
class FormalTrainValidationCheckerResultV1:
    repository_profile: str
    oracle_train_event_ids: tuple[str, ...]
    oracle_validation_event_ids: tuple[str, ...]
    oracle_test_event_ids: tuple[str, ...]
    split_index_sha256: str
    runtime: integration.CovapieBatch001FormalTrainValidationIntegrationResultV1
    candidate_precommit_profile_passed: bool
    published_successor_profile_simulation_passed: bool
    ready_for_gpt_review: bool
    ready_for_publication: bool


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


def _lines(value: str) -> tuple[str, ...]:
    return tuple(line for line in value.splitlines() if line)


def _porcelain(value: str) -> tuple[tuple[str, str], ...]:
    result = []
    for line in _lines(value):
        if len(line) < 4 or line[2] != " ":
            _fail()
        result.append((line[:2], line[3:]))
    return tuple(result)


def _name_status(value: str) -> tuple[tuple[str, str], ...]:
    result = []
    for line in _lines(value):
        parts = line.split("\t")
        if len(parts) != 2:
            _fail()
        result.append((parts[0], parts[1]))
    return tuple(result)


def _candidate_modes(repository_root: Path) -> tuple[tuple[str, str], ...]:
    result = []
    for path in AUTHORIZED_CANDIDATE_FILES_V1:
        line = _git(repository_root, "ls-tree", "HEAD", "--", path)
        if not line:
            continue
        parts = line.split(None, 3)
        if len(parts) != 4 or parts[3] != path:
            _fail()
        result.append((path, parts[0]))
    return tuple(result)


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
            "HEAD...refs/remotes/origin/main",
        ).split()
        if not parents or len(ahead_behind) != 2:
            _fail()
        return RepositoryGitSnapshotV1(
            branch=_git(repository_root, "branch", "--show-current"),
            head=_git(repository_root, "rev-parse", "HEAD"),
            origin_main=_git(
                repository_root, "rev-parse", "refs/remotes/origin/main"
            ),
            ahead_behind=(int(ahead_behind[0]), int(ahead_behind[1])),
            tracked_modified_paths=_lines(
                _git(repository_root, "diff", "--name-only")
            ),
            staged_modified_paths=_lines(
                _git(repository_root, "diff", "--cached", "--name-only")
            ),
            status_entries=_porcelain(
                _git(
                    repository_root,
                    "status",
                    "--porcelain=v1",
                    "--untracked-files=all",
                )
            ),
            head_parent_ids=tuple(parents[1:]),
            head_subject=_git(
                repository_root, "show", "-s", "--format=%s", "HEAD"
            ),
            head_tree=_git(repository_root, "rev-parse", "HEAD^{tree}"),
            head_changed_entries=_name_status(
                _git(
                    repository_root,
                    "diff-tree",
                    "--no-commit-id",
                    "--name-status",
                    "--no-renames",
                    "-r",
                    "HEAD",
                )
            ),
            head_candidate_path_modes=_candidate_modes(repository_root),
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
            snapshot.head_parent_ids != (EXPECTED_BASELINE_PARENT_V1,)
            or snapshot.head_subject != EXPECTED_BASELINE_SUBJECT_V1
            or snapshot.head_tree != EXPECTED_BASELINE_TREE_V1
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


def classify_repository_snapshot_v1(snapshot: object) -> str:
    try:
        if type(snapshot) is not RepositoryGitSnapshotV1:
            _fail()
        return _classify_repository_snapshot_impl_v1(snapshot)
    except _CheckerInvariantError as error:
        raise ValueError(CHECKER_ERROR_V1) from error


def classify_repository_profile_v1(*, repository_root: Path) -> str:
    return classify_repository_snapshot_v1(
        collect_repository_git_snapshot_v1(repository_root=repository_root)
    )


def valid_published_successor_simulation_v1() -> RepositoryGitSnapshotV1:
    return RepositoryGitSnapshotV1(
        branch="main",
        head="f" * 40,
        origin_main="f" * 40,
        ahead_behind=(0, 0),
        tracked_modified_paths=(),
        staged_modified_paths=(),
        status_entries=(),
        head_parent_ids=(EXPECTED_BASELINE_HEAD_V1,),
        head_subject=PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="e" * 40,
        head_changed_entries=tuple(
            ("A", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644") for path in AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def _independent_split_index_oracle(
    repository_root: Path,
) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    path = repository_root / SPLIT_INDEX_RELATIVE_PATH_V1
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SPLIT_INDEX_SHA256_V1:
        _fail()
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = tuple(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as error:
        raise _CheckerInvariantError() from error
    if len(rows) != 13:
        _fail()
    populations = tuple(
        tuple(
            row["canonical_event_id"]
            for row in rows
            if row["formal_split"] == split
        )
        for split in ("train", "validation", "test")
    )
    if tuple(map(len, populations)) != (5, 4, 4):
        _fail()
    return digest, populations[0], populations[1], populations[2]


def check_covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1(
    *, repository_root: Path = _DEFAULT_REPOSITORY_ROOT,
) -> FormalTrainValidationCheckerResultV1:
    try:
        profile = classify_repository_profile_v1(repository_root=repository_root)
        if (
            classify_repository_snapshot_v1(
                valid_published_successor_simulation_v1()
            )
            != PUBLISHED_SUCCESSOR_PROFILE_V1
        ):
            _fail()
        digest, train_ids, validation_ids, test_ids = (
            _independent_split_index_oracle(repository_root)
        )
        runtime = (
            integration.run_covapie_batch001_bounded_train_validation_integration_v1(
                repository_root=repository_root
            )
        )
        if (
            runtime.formal_train_event_ids != train_ids
            or runtime.formal_validation_event_ids != validation_ids
            or runtime.formal_test_event_ids != test_ids
            or runtime.runtime_train_event_ids != train_ids
            or runtime.runtime_validation_event_ids != validation_ids
            or runtime.runtime_test_event_ids
            or runtime.formal_test_runtime_intersection_count != 0
            or runtime.trainer_fit_call_count != 1
            or runtime.automatic_backward_call_count != 1
            or runtime.optimizer_step_count != 1
            or runtime.changed_parameter_tensor_count <= 0
            or runtime.formal_validation_run_count != 1
            or runtime.formal_validation_step_count != 1
            or runtime.formal_validation_estimate_count != 64
            or runtime.formal_validation_PRE_valid_count != 0
            or runtime.formal_validation_POST_valid_count != 64
            or runtime.validation_checkpoint_weight_migration_count != 0
            or runtime.test_step_call_count != 0
            or runtime.Trainer_test_invoked
            or runtime.GPU_used
            or runtime.network_used
            or runtime.persistent_output_created
            or runtime.production_geometry_weight_finalized
            or runtime.full_training_authorized
        ):
            _fail()
        return FormalTrainValidationCheckerResultV1(
            repository_profile=profile,
            oracle_train_event_ids=train_ids,
            oracle_validation_event_ids=validation_ids,
            oracle_test_event_ids=test_ids,
            split_index_sha256=digest,
            runtime=runtime,
            candidate_precommit_profile_passed=(
                profile == CANDIDATE_PRECOMMIT_PROFILE_V1
            ),
            published_successor_profile_simulation_passed=True,
            ready_for_gpt_review=True,
            ready_for_publication=True,
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except (OSError, _CheckerInvariantError, ValueError) as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def _print_bool(name: str, value: bool) -> None:
    print(f"{name}={str(value).lower()}")


def main() -> None:
    checked = (
        check_covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1()
    )
    result = checked.runtime
    _print_bool("batch001_formal_training_datamodule_built", True)
    _print_bool("real_trainer_fit_invoked", result.real_trainer_fit_invoked)
    print(f"trainer_fit_call_count={result.trainer_fit_call_count}")
    print(f"formal_train_event_count={len(result.formal_train_event_ids)}")
    print(f"formal_validation_event_count={len(result.formal_validation_event_ids)}")
    print(f"formal_test_event_count={len(result.formal_test_event_ids)}")
    print(f"runtime_train_event_count={len(result.runtime_train_event_ids)}")
    print(f"runtime_validation_event_count={len(result.runtime_validation_event_ids)}")
    print(f"runtime_test_event_count={len(result.runtime_test_event_ids)}")
    _print_bool(
        "train_runtime_matches_published_activation_authority",
        result.train_runtime_matches_published_activation_authority,
    )
    _print_bool(
        "validation_runtime_matches_published_formal_validation_authority",
        result.validation_runtime_matches_published_formal_validation_authority,
    )
    print(
        "formal_test_runtime_intersection_count="
        f"{result.formal_test_runtime_intersection_count}"
    )
    print(
        "train_sample_training_admitted_count="
        f"{result.train_sample_training_admitted_count}"
    )
    print(
        "validation_sample_training_admitted_count="
        f"{result.validation_sample_training_admitted_count}"
    )
    print(
        "test_sample_training_admitted_count="
        f"{result.test_sample_training_admitted_count}"
    )
    print(f"train_pair_candidate_count={result.train_pair_candidate_count}")
    print(f"PRE_geometry_train_active_count={result.PRE_geometry_train_active_count}")
    print(f"POST_geometry_train_active_count={result.POST_geometry_train_active_count}")
    print(f"automatic_backward_call_count={result.automatic_backward_call_count}")
    print(f"optimizer_step_count={result.optimizer_step_count}")
    print(f"changed_parameter_tensor_count={result.changed_parameter_tensor_count}")
    _print_bool(
        "post_optimizer_state_differs_from_pre_fit_state",
        result.post_optimizer_state_differs_from_pre_fit_state,
    )
    _print_bool(
        "validation_entry_uses_post_optimizer_current_state",
        result.validation_entry_uses_post_optimizer_current_state,
    )
    print(f"formal_validation_run_count={result.formal_validation_run_count}")
    print(f"formal_validation_step_count={result.formal_validation_step_count}")
    print(
        f"formal_validation_estimate_count={result.formal_validation_estimate_count}"
    )
    print(
        "formal_validation_PRE_valid_count="
        f"{result.formal_validation_PRE_valid_count}"
    )
    print(
        "formal_validation_POST_valid_count="
        f"{result.formal_validation_POST_valid_count}"
    )
    print(f"validation_model_weight_source={result.validation_model_weight_source}")
    print(
        "validation_checkpoint_weight_migration_count="
        f"{result.validation_checkpoint_weight_migration_count}"
    )
    _print_bool(
        "active_model_parameters_unchanged_across_validation",
        result.active_model_parameters_unchanged_across_validation,
    )
    _print_bool(
        "active_model_buffers_unchanged_across_validation",
        result.active_model_buffers_unchanged_across_validation,
    )
    _print_bool(
        "active_model_gradient_states_unchanged_across_validation",
        result.active_model_gradient_states_unchanged_across_validation,
    )
    print(f"test_step_call_count={result.test_step_call_count}")
    _print_bool("Trainer_test_invoked", result.Trainer_test_invoked)
    _print_bool(
        "integration_candidate_loss_weights_reused",
        result.integration_candidate_loss_weights_reused,
    )
    _print_bool(
        "production_geometry_weight_finalized",
        result.production_geometry_weight_finalized,
    )
    _print_bool("checkpoint_unchanged", result.checkpoint_unchanged)
    _print_bool("persistent_output_created", result.persistent_output_created)
    _print_bool("training_performed", result.training_performed)
    _print_bool("scientific_training_claimed", result.scientific_training_claimed)
    _print_bool("CPU_only", result.CPU_only)
    _print_bool("GPU_used", result.GPU_used)
    _print_bool("network_used", result.network_used)
    _print_bool("full_training_authorized", result.full_training_authorized)
    _print_bool(
        "candidate_precommit_profile_passed",
        checked.candidate_precommit_profile_passed,
    )
    _print_bool(
        "published_successor_profile_simulation_passed",
        checked.published_successor_profile_simulation_passed,
    )
    _print_bool("ready_for_gpt_review", checked.ready_for_gpt_review)
    _print_bool("ready_for_publication", checked.ready_for_publication)
    _print_bool(
        "ready_to_pivot_to_bulk_data_scale_after_publication",
        result.ready_to_pivot_to_bulk_data_scale_after_publication,
    )
    print(f"recommended_next_step_exactly={result.recommended_next_step_exactly}")


if __name__ == "__main__":
    main()

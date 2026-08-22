"""Fail-closed checker for the batch001 exact13 model-usable boundary V1."""

from __future__ import annotations

from dataclasses import dataclass, fields
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as boundary,
)
from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as train5_predecessor,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


CHECKER_ERROR_V1 = (
    "CHECK_COVAPIE_BATCH001_13EVENT_MODEL_USABLE_SPLIT_MATERIALIZATION_AND_"
    "ACTIVATION_BOUNDARY_V1_ERROR"
)
EXPECTED_BASELINE_HEAD_V1 = "fe034ea1b4e0e925cd8197c37f08c8675fa26cca"
EXPECTED_BASELINE_PARENT_V1 = "8fcaea02805eb27fb370e3f4b8d5915e52aa8240"
EXPECTED_BASELINE_TREE_V1 = "72129d1af1584234e5356ddf4599cd878cd7fc73"
EXPECTED_BASELINE_SUBJECT_V1 = (
    "add CovaPIE batch001 NDU4 leakage recovery and formal split admission v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE batch001 13-event model-usable split activation boundary v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
AUTHORIZED_CANDIDATE_FILES_V1 = (
    "src/covalent_ext/"
    "covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1.py",
    "scripts/"
    "check_covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1.py",
    "tests/"
    "test_covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1.py",
    (boundary.OUTPUT_ROOT_RELATIVE_V1 / boundary.SPLIT_INDEX_V1).as_posix(),
    (boundary.OUTPUT_ROOT_RELATIVE_V1 / boundary.SPLIT_REGISTRY_V1).as_posix(),
    (
        boundary.OUTPUT_ROOT_RELATIVE_V1
        / boundary.SOURCE_BINDING_INVENTORY_V1
    ).as_posix(),
    (boundary.OUTPUT_ROOT_RELATIVE_V1 / boundary.MANIFEST_V1).as_posix(),
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
class ModelUsableSplitCheckerResultV1:
    repository_profile: str
    authority: boundary.CovapieBatch001FormalSplitAuthorityV1
    batches: tuple[boundary.CovapieBatch001ModelUsableSplitBatchV1, ...]
    artifact_sha256: tuple[tuple[str, str], ...]
    deterministic_artifact_bytes: bool
    materialized_artifacts_match_recomputation: bool
    source_state_unchanged: bool
    cache_input_state_unchanged: bool
    train_activation_matches_independent_split_oracle: bool
    train_supervision_matches_published_train5_activation_semantics: bool
    validation_supervision_training_inactive: bool
    test_supervision_training_inactive: bool
    validation_preview_tensor_parity: bool
    test_preview_tensor_parity: bool
    model_input_tensor_parity: bool
    preview_source_unchanged: bool
    train5_schedule_complete: bool
    candidate_precommit_profile_passed: bool
    published_successor_profile_simulation_passed: bool


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
    *, repository_root: Path
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
    candidate_status = tuple(
        ("??", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
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
    expected_changes = tuple(
        ("A", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
    expected_modes = tuple(
        (path, "100644") for path in AUTHORIZED_CANDIDATE_FILES_V1
    )
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


def _valid_published_successor_simulation() -> RepositoryGitSnapshotV1:
    successor = "1" * 40
    return RepositoryGitSnapshotV1(
        branch="main",
        head=successor,
        origin_main=successor,
        ahead_behind=(0, 0),
        tracked_modified_paths=(),
        staged_modified_paths=(),
        status_entries=(),
        head_parent_ids=(EXPECTED_BASELINE_HEAD_V1,),
        head_subject=PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="2" * 40,
        head_changed_entries=tuple(
            ("A", path) for path in AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644") for path in AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.dtype != right.dtype or left.shape != right.shape:
        return False
    if left.dtype.is_floating_point:
        return bool(
            torch.equal(torch.isnan(left), torch.isnan(right))
            and torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
        )
    return bool(torch.equal(left, right))


def _same_supervision(
    left: CovapieCurrent11TrainingSupervisionTensorsV1,
    right: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> bool:
    return all(
        _same_tensor(getattr(left, field.name), getattr(right, field.name))
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )


def _clone_supervision(
    value: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    return CovapieCurrent11TrainingSupervisionTensorsV1(**{
        field.name: getattr(value, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    })


def _same_model_input(
    left: Mapping[str, object], right: Mapping[str, object]
) -> bool:
    if tuple(left) != tuple(right):
        return False
    for name in left:
        left_value, right_value = left[name], right[name]
        if isinstance(left_value, torch.Tensor):
            if not isinstance(right_value, torch.Tensor) or not _same_tensor(
                left_value, right_value
            ):
                return False
        elif left_value != right_value:
            return False
    return True


def _independent_previews(
    *, repository_root: Path, cache_root: Path
) -> tuple[
    tuple[preview_owner.CovapieBatch001ExistingSupervisionPreviewBatchV1, ...],
    tuple[CovapieCurrent11TrainingSupervisionTensorsV1, ...],
]:
    records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=repository_root, cache_root=cache_root
    )
    by_id = {record.sample_identity: record for record in records}
    previews = []
    snapshots = []
    for event_ids in (
        boundary.FORMAL_TRAIN_EVENT_IDS_V1,
        boundary.FORMAL_VALIDATION_EVENT_IDS_V1,
        boundary.FORMAL_TEST_EVENT_IDS_V1,
    ):
        tasks = tuple(
            preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=event_id,
                epoch=0,
                task_schedule_seed=0,
            )
            for event_id in event_ids
        )
        preview = preview_owner._tensorize_records_v1(
            records=tuple(by_id[event_id] for event_id in event_ids),
            task_ids=tasks,
            epoch=0,
            task_schedule_seed=0,
        )
        previews.append(preview)
        snapshots.append(_clone_supervision(preview.supervision))
    return tuple(previews), tuple(snapshots)


def _independent_activation_oracle(
    repository_root: Path,
) -> dict[str, bool]:
    path = repository_root / boundary._FORMAL_EVENT_PATH_V1
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as error:
        raise _CheckerInvariantError() from error
    if len(rows) != 13:
        _fail()
    return {
        row["canonical_event_id"]: (
            row["assigned_split"] == "train"
            and row["split_admission_authoritative"] == "true"
        )
        for row in rows
    }


def _snapshot(paths: Sequence[Path]) -> tuple[tuple[str, str], ...]:
    try:
        return tuple(sorted(
            (path.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
            for path in paths
        ))
    except OSError as error:
        raise _CheckerInvariantError() from error


def _write_isolated(root: Path, artifacts: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True, exist_ok=False)
    for name in boundary.OUTPUT_FILENAMES_V1:
        (root / name).write_bytes(artifacts[name])


def check_covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1(
    *, repository_root: Path = _DEFAULT_REPOSITORY_ROOT
) -> ModelUsableSplitCheckerResultV1:
    try:
        repository_root = repository_root.resolve(strict=True)
        cache_root = (
            repository_root.parent
            / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
        ).resolve(strict=True)
        git_before = collect_repository_git_snapshot_v1(
            repository_root=repository_root
        )
        profile = _classify_repository_snapshot_impl_v1(git_before)
        bound_paths = tuple(
            repository_root / relative
            for _, relative, _, _ in boundary._SOURCE_BINDING_SPECS_V1
        )
        cache_input_paths = (
            cache_root.parent / "cache_manifest_v1.json",
            *tuple(
                cache_root / "structures" / f"{pdb_id}.cif.gz"
                for pdb_id in structural_owner.BATCH001_STRUCTURE_SHA256_BY_PDB_V1
            ),
            *tuple(
                cache_root / "ccd" / f"{component}.cif"
                for component in structural_owner.BATCH001_CCD_SHA256_BY_COMPONENT_V1
            ),
            repository_root.parent
            / "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
            "incremental_processing_outcomes_v1.json",
        )
        source_before = _snapshot(bound_paths)
        cache_input_before = _snapshot(cache_input_paths)
        first = boundary.build_covapie_batch001_model_usable_split_artifacts_v1(
            repository_root=repository_root, cache_root=cache_root
        )
        second = boundary.build_covapie_batch001_model_usable_split_artifacts_v1(
            repository_root=repository_root, cache_root=cache_root
        )
        if first != second or tuple(first) != boundary.OUTPUT_FILENAMES_V1:
            _fail()
        with tempfile.TemporaryDirectory(prefix="covapie_batch001_split_check_") as temporary:
            first_root = Path(temporary) / "run1"
            second_root = Path(temporary) / "run2"
            _write_isolated(first_root, first)
            _write_isolated(second_root, second)
            if any(
                (first_root / name).read_bytes()
                != (second_root / name).read_bytes()
                for name in boundary.OUTPUT_FILENAMES_V1
            ):
                _fail()
        output_root = repository_root / boundary.OUTPUT_ROOT_RELATIVE_V1
        if (
            not output_root.is_dir()
            or {path.name for path in output_root.iterdir()}
            != set(boundary.OUTPUT_FILENAMES_V1)
            or any(
                (output_root / name).read_bytes() != first[name]
                for name in boundary.OUTPUT_FILENAMES_V1
            )
        ):
            _fail()
        authority = boundary.load_covapie_batch001_formal_split_authority_v1(
            repository_root=repository_root
        )
        if not boundary.validate_covapie_batch001_model_usable_split_artifacts_v1(
            first, authority=authority
        ):
            _fail()
        context = boundary._build_context(
            repository_root=repository_root, cache_root=cache_root
        )
        batches = tuple(
            boundary._build_split_from_context(
                context=context,
                split=split,
                epoch=0,
                task_schedule_seed=0,
            )
            for split in ("train", "validation", "test")
        )
        previews, preview_snapshots = _independent_previews(
            repository_root=repository_root, cache_root=cache_root
        )
        train_expected = train5_predecessor._clone_admitted_supervision(
            previews[0].supervision,
            previews[0].model_input_batch["lig_mask"],
        )
        train_parity = _same_supervision(batches[0].supervision, train_expected)
        validation_parity = _same_supervision(
            batches[1].supervision, previews[1].supervision
        )
        test_parity = _same_supervision(
            batches[2].supervision, previews[2].supervision
        )
        preview_unchanged = all(
            _same_supervision(preview.supervision, snapshot)
            for preview, snapshot in zip(previews, preview_snapshots)
        )
        model_parity = all(
            _same_model_input(batch.model_input_batch, preview.model_input_batch)
            for batch, preview in zip(batches, previews)
        )
        independent_oracle = _independent_activation_oracle(repository_root)
        index_rows = list(csv.DictReader(io.StringIO(
            first[boundary.SPLIT_INDEX_V1].decode("utf-8"), newline=""
        )))
        oracle_parity = len(index_rows) == 13 and all(
            (row["sample_training_admitted"] == "true")
            == independent_oracle[row["canonical_event_id"]]
            and (row["model_training_activation_authorized"] == "true")
            == independent_oracle[row["canonical_event_id"]]
            and batch.sample_training_admitted[index]
            == independent_oracle[event_id]
            for batch in batches
            for index, event_id in enumerate(batch.sample_identities)
            for row in index_rows
            if row["canonical_event_id"] == event_id
        )
        train5_schedule_complete = all(
            {
                preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                    sample_identity=event_id,
                    epoch=epoch,
                    task_schedule_seed=0,
                )
                for epoch in range(5)
            }
            == set(range(5))
            for event_id in boundary.FORMAL_TRAIN_EVENT_IDS_V1
        )
        validation_inactive = not any((
            bool(batches[1].supervision.sample_training_admitted.any().item()),
            bool(batches[1].supervision.ligand_active_diffusion_loss_mask.any().item()),
            bool(batches[1].supervision.pair_head_candidate_loss_mask.any().item()),
            bool(batches[1].supervision.pair_contrastive_sample_loss_mask.any().item()),
            bool(batches[1].supervision.pre_post_geometry_component_loss_mask.any().item()),
        ))
        test_inactive = not any((
            bool(batches[2].supervision.sample_training_admitted.any().item()),
            bool(batches[2].supervision.ligand_active_diffusion_loss_mask.any().item()),
            bool(batches[2].supervision.pair_head_candidate_loss_mask.any().item()),
            bool(batches[2].supervision.pair_contrastive_sample_loss_mask.any().item()),
            bool(batches[2].supervision.pre_post_geometry_component_loss_mask.any().item()),
        ))
        manifest = json.loads(first[boundary.MANIFEST_V1])
        if (
            not all((
                train_parity,
                validation_parity,
                test_parity,
                preview_unchanged,
                model_parity,
                oracle_parity,
                train5_schedule_complete,
                validation_inactive,
                test_inactive,
            ))
            or manifest.get("ready_for_gpt_review") is not True
            or manifest.get("ready_for_publication") is not True
            or manifest.get("full_training_authorized") is not False
            or manifest.get("training_performed") is not False
        ):
            _fail()
        source_after = _snapshot(bound_paths)
        cache_input_after = _snapshot(cache_input_paths)
        git_after = collect_repository_git_snapshot_v1(
            repository_root=repository_root
        )
        if (
            source_before != source_after
            or cache_input_before != cache_input_after
            or git_before != git_after
        ):
            _fail()
        published_simulation = _valid_published_successor_simulation()
        if (
            _classify_repository_snapshot_impl_v1(published_simulation)
            != PUBLISHED_SUCCESSOR_PROFILE_V1
        ):
            _fail()
        if (
            any(repository_root.rglob("*.pyc"))
            or any(repository_root.rglob("*.tmp"))
            or any(repository_root.rglob("*.part"))
        ):
            _fail()
        return ModelUsableSplitCheckerResultV1(
            repository_profile=profile,
            authority=authority,
            batches=batches,
            artifact_sha256=tuple(
                (name, hashlib.sha256(first[name]).hexdigest())
                for name in boundary.OUTPUT_FILENAMES_V1
            ),
            deterministic_artifact_bytes=True,
            materialized_artifacts_match_recomputation=True,
            source_state_unchanged=source_before == source_after,
            cache_input_state_unchanged=cache_input_before == cache_input_after,
            train_activation_matches_independent_split_oracle=True,
            train_supervision_matches_published_train5_activation_semantics=True,
            validation_supervision_training_inactive=True,
            test_supervision_training_inactive=True,
            validation_preview_tensor_parity=True,
            test_preview_tensor_parity=True,
            model_input_tensor_parity=True,
            preview_source_unchanged=True,
            train5_schedule_complete=True,
            candidate_precommit_profile_passed=(
                profile == CANDIDATE_PRECOMMIT_PROFILE_V1
            ),
            published_successor_profile_simulation_passed=True,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == CHECKER_ERROR_V1:
            raise
        raise ValueError(CHECKER_ERROR_V1) from error


def _print_bool(name: str, value: bool) -> None:
    print(name + "=" + str(value).lower())


def main() -> None:
    result = check_covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1()
    train, validation, test = result.batches
    _print_bool("batch001_model_usable_split_materialization_built", True)
    print("formal_positive_event_count=13")
    print("formal_train_event_count=" + str(len(train.sample_identities)))
    print("formal_validation_event_count=" + str(len(validation.sample_identities)))
    print("formal_test_event_count=" + str(len(test.sample_identities)))
    print("model_usable_event_count=" + str(sum(
        sum(batch.model_usable) for batch in result.batches
    )))
    print("sample_training_admitted_event_count=" + str(sum(
        sum(batch.sample_training_admitted) for batch in result.batches
    )))
    print("model_training_activation_authorized_event_count=" + str(sum(
        sum(batch.model_training_activation_authorized) for batch in result.batches
    )))
    print("optimizer_population_eligible_event_count=" + str(sum(
        sum(batch.optimizer_population_eligible) for batch in result.batches
    )))
    print("validation_training_admitted_event_count=" + str(sum(
        validation.sample_training_admitted
    )))
    print("test_training_admitted_event_count=" + str(sum(
        test.sample_training_admitted
    )))
    _print_bool("train5_exact_identity_match", train.sample_identities == boundary.FORMAL_TRAIN_EVENT_IDS_V1)
    _print_bool("validation4_exact_identity_match", validation.sample_identities == boundary.FORMAL_VALIDATION_EVENT_IDS_V1)
    _print_bool("test4_exact_identity_match", test.sample_identities == boundary.FORMAL_TEST_EVENT_IDS_V1)
    intersections = dict(result.authority.event_identity_intersection_counts)
    print("train_validation_intersection_count=" + str(intersections["train_validation"]))
    print("train_test_intersection_count=" + str(intersections["train_test"]))
    print("validation_test_intersection_count=" + str(intersections["validation_test"]))
    _print_bool("all_split_intersections_empty", all(value == 0 for value in intersections.values()))
    _print_bool("formal_leakage_groups_do_not_cross_split", result.authority.formal_leakage_group_cross_split_violation_count == 0)
    _print_bool("train_activation_matches_independent_split_oracle", result.train_activation_matches_independent_split_oracle)
    _print_bool("train_supervision_matches_published_train5_activation_semantics", result.train_supervision_matches_published_train5_activation_semantics)
    _print_bool("validation_supervision_training_inactive", result.validation_supervision_training_inactive)
    _print_bool("test_supervision_training_inactive", result.test_supervision_training_inactive)
    _print_bool("validation_preview_tensor_parity", result.validation_preview_tensor_parity)
    _print_bool("test_preview_tensor_parity", result.test_preview_tensor_parity)
    _print_bool("model_input_tensor_parity", result.model_input_tensor_parity)
    _print_bool("preview_source_unchanged", result.preview_source_unchanged)
    _print_bool("cache_inputs_unchanged", result.cache_input_state_unchanged)
    print("train_pair_candidate_count=" + str(len(train.supervision.pair_candidate_batch_index)))
    print("PRE_geometry_training_active_count=" + str(sum(
        int(batch.supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item())
        for batch in result.batches
    )))
    print("POST_geometry_train_active_count=" + str(int(
        train.supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()
    )))
    print("NDU4_optimizer_eligible_count=" + str(sum(test.optimizer_population_eligible)))
    print("NDU4_training_admitted_count=" + str(sum(test.sample_training_admitted)))
    print("NDU4_formal_split=" + test.formal_split)
    _print_bool("production_geometry_weight_finalized", False)
    _print_bool("training_performed", False)
    _print_bool("Trainer_used", False)
    _print_bool("backward_performed", False)
    _print_bool("optimizer_created", False)
    _print_bool("full_training_authorized", False)
    _print_bool("deterministic_artifact_bytes", result.deterministic_artifact_bytes)
    _print_bool("candidate_precommit_profile_passed", result.candidate_precommit_profile_passed)
    _print_bool("published_successor_profile_simulation_passed", result.published_successor_profile_simulation_passed)
    _print_bool("ready_for_gpt_review", True)
    _print_bool("ready_for_publication", True)
    _print_bool("ready_for_training_datamodule_integration", True)
    print("recommended_next_step_exactly=gpt_audit_batch001_13event_model_usable_split_activation_then_publish_if_pass")


if __name__ == "__main__":
    main()

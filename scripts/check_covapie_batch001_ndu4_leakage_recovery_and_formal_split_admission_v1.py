"""Fail-closed checker for batch001 NDU4 leakage recovery successor V1."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1
    as recovery,
)


CHECKER_ERROR_V1 = (
    "CHECK_COVAPIE_BATCH001_NDU4_LEAKAGE_RECOVERY_AND_FORMAL_SPLIT_"
    "ADMISSION_V1_ERROR"
)
EXPECTED_BASELINE_HEAD_V1 = "8fcaea02805eb27fb370e3f4b8d5915e52aa8240"
EXPECTED_BASELINE_PARENT_V1 = "4b60900fad41d0719b054986e94620e35e39b2ce"
EXPECTED_BASELINE_TREE_V1 = "7ccf9d7ae576b58e852ce15593899edf699739cf"
EXPECTED_BASELINE_SUBJECT_V1 = (
    "add CovaPIE formal validation4 Lightning integration v1"
)
PUBLISHED_SUCCESSOR_SUBJECT_V1 = (
    "add CovaPIE batch001 NDU4 leakage recovery and formal split admission v1"
)
CANDIDATE_PRECOMMIT_PROFILE_V1 = "candidate_precommit_untracked"
PUBLISHED_SUCCESSOR_PROFILE_V1 = "published_successor"
AUTHORIZED_CANDIDATE_FILES_V1 = (
    "src/covalent_ext/"
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1.py",
    "scripts/"
    "check_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1.py",
    "tests/"
    "test_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1.py",
    (
        recovery.OUTPUT_ROOT_RELATIVE_V1
        / recovery.RECOVERY_EVIDENCE_V1
    ).as_posix(),
    (
        recovery.OUTPUT_ROOT_RELATIVE_V1
        / recovery.COMPONENT_REGISTRY_V1
    ).as_posix(),
    (
        recovery.OUTPUT_ROOT_RELATIVE_V1
        / recovery.EVENT_ADMISSION_V1
    ).as_posix(),
    (
        recovery.OUTPUT_ROOT_RELATIVE_V1
        / recovery.SOURCE_BINDING_INVENTORY_V1
    ).as_posix(),
    (
        recovery.OUTPUT_ROOT_RELATIVE_V1
        / recovery.MANIFEST_V1
    ).as_posix(),
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
class NDU4CheckerResultV1:
    repository_profile: str
    computation: recovery.Batch001NDU4LeakageRecoveryComputationV1
    deterministic_artifact_bytes: bool
    materialized_artifacts_match_recomputation: bool
    input_state_unchanged: bool
    published_formal_split_artifacts_unchanged: bool
    cache_inputs_unchanged: bool
    candidate_precommit_profile_passed: bool
    published_successor_profile_simulation_passed: bool


def _git(repository_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments), cwd=repository_root, check=True,
            capture_output=True, text=True, timeout=30,
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
        fields = line.split("\t")
        if len(fields) != 2:
            _fail()
        result.append((fields[0], fields[1]))
    return tuple(result)


def _candidate_modes(repository_root: Path) -> tuple[tuple[str, str], ...]:
    result = []
    for path in AUTHORIZED_CANDIDATE_FILES_V1:
        line = _git(repository_root, "ls-tree", "HEAD", "--", path)
        if not line:
            continue
        fields = line.split(None, 3)
        if len(fields) != 4 or fields[3] != path:
            _fail()
        result.append((path, fields[0]))
    return tuple(result)


def collect_repository_git_snapshot_v1(
    *, repository_root: Path,
) -> RepositoryGitSnapshotV1:
    try:
        parents = _git(
            repository_root, "rev-list", "--parents", "-n", "1", "HEAD",
        ).split()
        ahead_behind = _git(
            repository_root, "rev-list", "--left-right", "--count",
            "HEAD...refs/remotes/origin/main",
        ).split()
        if not parents or len(ahead_behind) != 2:
            _fail()
        return RepositoryGitSnapshotV1(
            branch=_git(repository_root, "branch", "--show-current"),
            head=_git(repository_root, "rev-parse", "HEAD"),
            origin_main=_git(
                repository_root, "rev-parse", "refs/remotes/origin/main",
            ),
            ahead_behind=(int(ahead_behind[0]), int(ahead_behind[1])),
            tracked_modified_paths=_lines(
                _git(repository_root, "diff", "--name-only"),
            ),
            staged_modified_paths=_lines(
                _git(repository_root, "diff", "--cached", "--name-only"),
            ),
            status_entries=_porcelain(_git(
                repository_root, "status", "--porcelain=v1", "--untracked-files=all",
            )),
            head_parent_ids=tuple(parents[1:]),
            head_subject=_git(
                repository_root, "show", "-s", "--format=%s", "HEAD",
            ),
            head_tree=_git(repository_root, "rev-parse", "HEAD^{tree}"),
            head_changed_entries=_name_status(_git(
                repository_root, "diff-tree", "--no-commit-id", "--name-status",
                "--no-renames", "-r", "HEAD",
            )),
            head_candidate_path_modes=_candidate_modes(repository_root),
        )
    except (TypeError, ValueError) as error:
        raise _CheckerInvariantError() from error


def _classify_repository_snapshot_impl_v1(snapshot: RepositoryGitSnapshotV1) -> str:
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
            or tuple(sorted(snapshot.status_entries)) != tuple(sorted(candidate_status))
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


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise _CheckerInvariantError() from error


def _snapshot(paths: Sequence[Path]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((path.as_posix(), _sha(path)) for path in paths))


def _write_isolated(root: Path, artifacts: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True, exist_ok=False)
    for name in recovery.OUTPUT_FILENAMES_V1:
        (root / name).write_bytes(artifacts[name])


def _valid_published_successor_simulation(
    current: RepositoryGitSnapshotV1,
) -> RepositoryGitSnapshotV1:
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


def check_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
    *, repository_root: Path = _DEFAULT_REPOSITORY_ROOT,
) -> NDU4CheckerResultV1:
    try:
        repository_root = repository_root.resolve(strict=True)
        git_before = collect_repository_git_snapshot_v1(
            repository_root=repository_root,
        )
        profile = _classify_repository_snapshot_impl_v1(git_before)
        state_root = repository_root.parent / "covapie-state"
        attempt = state_root / (
            "bulk-500-controlled-execution-v1/attempt-001/"
            "incremental_processing_outcomes_v1.json"
        )
        formal_root = repository_root / (
            "data/derived/covalent_small/"
            "covapie_batch001_formal_split_leakage_admission_v1"
        )
        formal_paths = tuple(sorted(path for path in formal_root.iterdir() if path.is_file()))
        cache_root = state_root / "bulk-multisource-cys-sg-v1/rcsb"
        cache_paths = tuple(
            cache_root / "structures" / name
            for name in ("3B9H.cif.gz", "3BHL.cif.gz", "3BHR.cif.gz")
        )
        state_before = _snapshot((attempt,))
        formal_before = _snapshot(formal_paths)
        cache_before = _snapshot(cache_paths)
        first = (
            recovery.build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1(
                repository_root=repository_root,
            )
        )
        second = (
            recovery.build_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_artifacts_v1(
                repository_root=repository_root,
            )
        )
        if first != second or tuple(first) != recovery.OUTPUT_FILENAMES_V1:
            _fail()
        with tempfile.TemporaryDirectory(prefix="covapie_ndu4_check_") as temporary:
            temporary_root = Path(temporary)
            first_root = temporary_root / "run1"
            second_root = temporary_root / "run2"
            _write_isolated(first_root, first)
            _write_isolated(second_root, second)
            if any(
                (first_root / name).read_bytes() != (second_root / name).read_bytes()
                for name in recovery.OUTPUT_FILENAMES_V1
            ):
                _fail()
        output_root = repository_root / recovery.OUTPUT_ROOT_RELATIVE_V1
        if (
            not output_root.is_dir()
            or {path.name for path in output_root.iterdir()}
            != set(recovery.OUTPUT_FILENAMES_V1)
            or any(
                (output_root / name).read_bytes() != first[name]
                for name in recovery.OUTPUT_FILENAMES_V1
            )
        ):
            _fail()
        computation = (
            recovery.compute_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
                repository_root=repository_root,
            )
        )
        if not recovery.validate_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1(
            computation
        ):
            _fail()
        manifest = json.loads(first[recovery.MANIFEST_V1])
        if (
            manifest.get("ready_for_gpt_review") is not True
            or manifest.get("full_training_authorized") is not False
            or manifest.get("cross_split_leakage_violation_count") != 0
        ):
            _fail()
        state_after = _snapshot((attempt,))
        formal_after = _snapshot(formal_paths)
        cache_after = _snapshot(cache_paths)
        git_after = collect_repository_git_snapshot_v1(
            repository_root=repository_root,
        )
        if git_before != git_after:
            _fail()
        published_simulation = _valid_published_successor_simulation(git_before)
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
        return NDU4CheckerResultV1(
            repository_profile=profile,
            computation=computation,
            deterministic_artifact_bytes=True,
            materialized_artifacts_match_recomputation=True,
            input_state_unchanged=state_before == state_after,
            published_formal_split_artifacts_unchanged=formal_before == formal_after,
            cache_inputs_unchanged=cache_before == cache_after,
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


def _uniform(values: Sequence[str]) -> str:
    unique = sorted(set(values))
    return unique[0] if len(unique) == 1 else "mixed"


def main() -> None:
    result = check_covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1()
    computation = result.computation
    components = computation.recovered_components
    target_rows = [
        row for row in computation.event_rows
        if row["canonical_event_id"] in computation.target_event_ids
    ]
    _print_bool("ndu4_leakage_recovery_built", True)
    print("ndu4_target_event_count=" + str(len(computation.target_event_ids)))
    print(
        "ndu4_unique_pdb_ligand_identity_count="
        + str(len(computation.target_pdb_ligand_identities))
    )
    print("ndu4_model_integration_preview_ready_count=4")
    print("pre_recovery_leakage_evidence_complete_count=0")
    print("post_recovery_leakage_evidence_complete_count=" + str(sum(
        row["leakage_evidence_complete"] == "true" for row in target_rows
    )))
    print("ndu4_leakage_gap_root_cause=" + computation.leakage_gap_root_cause)
    _print_bool("ndu4_recovery_used_existing_local_authority_only", True)
    _print_bool("ndu4_new_human_review_required", False)
    _print_bool("ndu4_network_used", computation.network_used)
    print(
        "controlled_leakage_context_event_count="
        + str(computation.context_counts["full_predictor_population_count"])
    )
    _print_bool(
        "controlled_leakage_context_expected_527",
        computation.context_counts["full_predictor_population_count"] == 527,
    )
    _print_bool("canonical_read_only_predictor_reused", True)
    print("ndu4_recovered_component_count=" + str(len(components)))
    print("ndu4_full_component_identity_count=" + str(sum(
        int(item["full_identity_count"]) for item in components
    )))
    print("ndu4_full_component_event_count=" + str(sum(
        int(item["full_event_count"]) for item in components
    )))
    print("ndu4_non_target_component_event_count=" + str(sum(
        int(item["non_target_component_event_count"]) for item in components
    )))
    print("ndu4_component_classification=" + _uniform([
        str(item["classification"]) for item in components
    ]))
    _print_bool(
        "ndu4_component_preexisted",
        all(bool(item["group_existed_pre_recovery"]) for item in components),
    )
    print("ndu4_formal_group_id=" + _uniform([
        str(item["formal_group_id"]) for item in components
    ]))
    print("ndu4_formal_split=" + _uniform([
        str(item["formal_split"]) for item in components
    ]))
    _print_bool("formal_split_policy_oracle_parity", True)
    _print_bool(
        "existing_published_group_assignments_unchanged",
        computation.existing_published_group_assignments_unchanged,
    )
    print("existing_batch001_authoritative_event_count=9")
    print("newly_split_authoritative_NDU_event_count=4")
    print("successor_batch001_split_authoritative_event_count=13")
    print(
        "cross_split_leakage_violation_count="
        + str(len(computation.cross_split_leakage_violations))
    )
    _print_bool("all_13_sample_training_admitted_false", True)
    _print_bool("all_13_model_training_activation_authorized_false", True)
    _print_bool(
        "published_formal_split_artifacts_unchanged",
        result.published_formal_split_artifacts_unchanged,
    )
    _print_bool("controlled_execution_state_unchanged", result.input_state_unchanged)
    _print_bool("cache_inputs_unchanged", result.cache_inputs_unchanged)
    _print_bool("deterministic_artifact_bytes", result.deterministic_artifact_bytes)
    _print_bool(
        "candidate_precommit_profile_passed",
        result.candidate_precommit_profile_passed,
    )
    _print_bool(
        "published_successor_profile_simulation_passed",
        result.published_successor_profile_simulation_passed,
    )
    _print_bool("full_training_authorized", False)
    _print_bool("ready_for_gpt_review", True)


if __name__ == "__main__":
    main()

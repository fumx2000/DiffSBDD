"""One real Exact16 mixed-profile batch driven by ``Trainer.fit``.

This is a bounded CPU-only integration smoke.  It reuses the published mixed
batch, mixed Lightning bridge, checkpoint migration, model/loss, and optimizer
owners.  Lightning receives one immutable in-memory batch and performs its
ordinary automatic-optimization lifecycle.  Nothing is persisted.
"""

from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import math
import os
import platform
import signal
import stat
import subprocess
import tempfile
from argparse import Namespace
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import NoReturn

import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

import pytorch_lightning as pl  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as current11_smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as checkpoint_migration,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_formal_trainer_v1 as formal_trainer,
)
from covalent_ext import (  # noqa: E402
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as mixed_scheduler,
)
from covalent_ext import (  # noqa: E402
    covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1
    as mixed_bridge,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (  # noqa: E402
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR",
    "run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1",
)


COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR"
)

_EXPECTED_HEAD_V1 = "ad009ef5274b8bd2fb8c9cc56276b34a16a27db3"
_EXPECTED_PUBLICATION_SUBJECT_V1 = (
    "add CovaPIE expanded Cys-SG mixed-profile single-batch Trainer.fit smoke v1"
)
_EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_EXPECTED_BRIDGE_SHA256_V1 = (
    "cabb479e35df0cd86c72cdca11903deaf03cf3c134d95d1c067e4b671e2b3fb2"
)
_EXPECTED_BRIDGE_TEST_SHA256_V1 = (
    "fe19777936cd50243986e67e134e5216d8c5ab87ec44ef80c693e027c09b51f4"
)
_EXPECTED_TASKS_V1 = (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1, 3, 0, 0, 0, 0)
_EXPECTED_K36_INDICES_V1 = (11, 12, 13, 14, 15)
_EXPECTED_K36_TASKS_V1 = (3, 0, 0, 0, 0)
_MODEL_INITIALIZATION_SEED_V1 = 20_260_818
_TRAINER_FIT_SEED_V1 = 20_260_819
_PATH_TYPE = type(Path())
_CANDIDATE_RELATIVE_PATHS_V1 = frozenset((
    "src/covalent_ext/"
    "covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py",
    "tests/"
    "test_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py",
))
_EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1 = (
    "local-tools",
    "gpu_steady_30pct_20h_v4",
    "runs",
)
_EXTERNAL_CURRENT_RUN_PARTS_V1 = (
    "local-tools",
    "gpu_steady_30pct_20h_v4",
    "current_run.json",
)
_EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1 = (
    "heartbeat.json",
    "control_summary.json",
    "launch_acceptance_checks.jsonl",
)
_EXTERNAL_RUN_ID_GRAMMAR_V1 = (
    "YYYYMMDDTHHMMSSZ_<8 lowercase hexadecimal digits>"
)
_EXTERNAL_OWNERSHIP_RULE_SOURCE_V1 = (
    "covapie-state/local-tools/gpu_steady_30pct_20h_v4/start_formal.sh:"
    "RUN_ID=date-UTC-%Y%m%dT%H%M%SZ plus '_' plus od-4-byte-lowercase-hex; "
    "start_formal.sh creates launch_acceptance_checks.jsonl; "
    "gpu_steady_load.py RunState creates heartbeat.json and control_summary.json"
)
_STATE_MODIFIED_SEMANTICS_V1 = (
    "CovaPIE-protected state excluding explicitly declared externally-owned "
    "volatile runtime files was unchanged."
)
_EXPECTED_METRIC_KEYS_V1 = frozenset((
    "loss",
    "loss_base_diffusion",
    "loss_covalent_pair_prediction",
    "loss_pre_post_geometry",
    "loss_covalent_pair_contrastive",
))


class _TrainerFitSmokeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _TrainerFitSmokeInvariantError()


def _public_error(error: Exception) -> NoReturn:
    if (
        type(error) is ValueError
        and str(error)
        == COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR
    ):
        raise error
    raise ValueError(
        COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_SINGLE_BATCH_TRAINER_FIT_SMOKE_V1_ERROR
    ) from error


def _require_root(value: object) -> Path:
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        _fail()
    try:
        metadata = value.lstat()
        resolved = value.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _TrainerFitSmokeInvariantError() from error
    if (
        resolved != value
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return value


def _file_fingerprint(path: Path) -> tuple[int, int, str]:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail()
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _TrainerFitSmokeInvariantError() from error
    return metadata.st_size, stat.S_IMODE(metadata.st_mode), digest.hexdigest()


def _tree_fingerprint_excluding_exact_paths_v1(
    root: Path,
    exact_excluded_relative_paths: frozenset[str],
) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    seen_exclusions: set[str] = set()
    try:
        paths = sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix())
        for path in paths:
            relative_text = path.relative_to(root).as_posix()
            metadata = path.lstat()
            if relative_text in exact_excluded_relative_paths:
                if (
                    stat.S_ISLNK(metadata.st_mode)
                    or not stat.S_ISREG(metadata.st_mode)
                ):
                    _fail()
                seen_exclusions.add(relative_text)
                continue
            relative = relative_text.encode("utf-8")
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISLNK(metadata.st_mode):
                kind = b"L"
                payload = os.readlink(path).encode("utf-8")
            elif stat.S_ISDIR(metadata.st_mode):
                kind = b"D"
                payload = b""
            elif stat.S_ISREG(metadata.st_mode):
                kind = b"F"
                file_digest = hashlib.sha256()
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        file_digest.update(chunk)
                payload = file_digest.digest()
            else:
                _fail()
            digest.update(kind)
            digest.update(relative)
            digest.update(b"\0")
            digest.update(str(mode).encode("ascii"))
            digest.update(b"\0")
            digest.update(str(metadata.st_size).encode("ascii"))
            digest.update(b"\0")
            digest.update(payload)
            count += 1
    except (OSError, RuntimeError, UnicodeError) as error:
        raise _TrainerFitSmokeInvariantError() from error
    if seen_exclusions != set(exact_excluded_relative_paths):
        _fail()
    return count, digest.hexdigest()


def _tree_fingerprint(root: Path) -> tuple[int, str]:
    return _tree_fingerprint_excluding_exact_paths_v1(root, frozenset())


def _valid_external_run_id_v1(value: object) -> bool:
    if (
        type(value) is not str
        or len(value) != 25
        or value[8] != "T"
        or value[15:17] != "Z_"
        or not value[:8].isdigit()
        or not value[9:15].isdigit()
        or any(character not in "0123456789abcdef" for character in value[17:])
    ):
        return False
    try:
        datetime(
            int(value[0:4]),
            int(value[4:6]),
            int(value[6:8]),
            int(value[9:11]),
            int(value[11:13]),
            int(value[13:15]),
        )
    except ValueError:
        return False
    return True


def _real_directory_at_parts_v1(
    state: Path,
    parts: tuple[str, ...],
) -> Path | None:
    current = state
    for part in parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            return None
    return current


def _validated_external_volatile_state_paths_v1(
    state_root: Path,
) -> tuple[tuple[str, Path], ...]:
    state = _require_root(state_root)
    runs = _real_directory_at_parts_v1(
        state,
        _EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1,
    )
    if runs is None:
        return ()
    try:
        children = sorted(runs.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise _TrainerFitSmokeInvariantError() from error
    validated: list[tuple[str, Path]] = []
    for run_directory in children:
        try:
            run_metadata = run_directory.lstat()
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        if (
            not _valid_external_run_id_v1(run_directory.name)
            or stat.S_ISLNK(run_metadata.st_mode)
            or not stat.S_ISDIR(run_metadata.st_mode)
        ):
            continue
        for leaf_name in _EXTERNAL_VOLATILE_STATE_LEAF_NAMES_V1:
            path = run_directory / leaf_name
            try:
                metadata = path.lstat()
            except FileNotFoundError:
                continue
            except OSError as error:
                raise _TrainerFitSmokeInvariantError() from error
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                _fail()
            try:
                if not path.resolve(strict=True).is_relative_to(state):
                    _fail()
            except (OSError, RuntimeError) as error:
                raise _TrainerFitSmokeInvariantError() from error
            validated.append((path.relative_to(state).as_posix(), path))
    return tuple(validated)


def _external_volatile_file_observation_v1(
    relative: str,
    path: Path,
) -> dict[str, object]:
    for _unused in range(32):
        try:
            before = path.lstat()
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                _fail()
            payload = path.read_bytes()
            after = path.lstat()
            if stat.S_ISLNK(after.st_mode) or not stat.S_ISREG(after.st_mode):
                _fail()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after or len(payload) != before.st_size:
            continue
        return {
            "relative_path": relative,
            "file_type": "regular",
            "mode": stat.S_IMODE(before.st_mode),
            "bytes": before.st_size,
            "mtime_ns": before.st_mtime_ns,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    _fail()


def _optional_external_gpu_writer_authority_v1(
    state_root: Path,
) -> dict[str, object]:
    state = _require_root(state_root)
    owner = _real_directory_at_parts_v1(
        state,
        _EXTERNAL_CURRENT_RUN_PARTS_V1[:-1],
    )
    if owner is None:
        return {
            "external_gpu_writer_detected": False,
            "external_active_run_id": None,
        }
    current = owner / _EXTERNAL_CURRENT_RUN_PARTS_V1[-1]
    for _unused in range(32):
        try:
            before = current.lstat()
        except FileNotFoundError:
            return {
                "external_gpu_writer_detected": False,
                "external_active_run_id": None,
            }
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            _fail()
        try:
            payload = current.read_bytes()
            after = current.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before == identity_after and len(payload) == before.st_size:
            break
    else:
        _fail()
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _TrainerFitSmokeInvariantError() from error
    if type(document) is not dict:
        _fail()
    run_id = document.get("run_id")
    run_directory = (
        state.joinpath(*_EXTERNAL_VOLATILE_STATE_RUNS_PARTS_V1) / str(run_id)
    )
    try:
        run_metadata = run_directory.lstat()
    except OSError as error:
        raise _TrainerFitSmokeInvariantError() from error
    if (
        document.get("schema_version")
        != "covapie_gpu_steady_load_current_run_v4"
        or not _valid_external_run_id_v1(run_id)
        or document.get("run_directory") != str(run_directory)
        or document.get("run_mode") != "formal_20h"
        or type(document.get("ready")) is not bool
        or type(document.get("pid")) is not int
        or document["pid"] <= 0
        or stat.S_ISLNK(run_metadata.st_mode)
        or not stat.S_ISDIR(run_metadata.st_mode)
    ):
        _fail()
    return {
        "external_gpu_writer_detected": True,
        "external_active_run_id": run_id,
    }


def _state_integrity_snapshot_v1(state_root: Path) -> dict[str, object]:
    validated = _validated_external_volatile_state_paths_v1(state_root)
    external = tuple(
        _external_volatile_file_observation_v1(relative, path)
        for relative, path in validated
    )
    protected = _tree_fingerprint_excluding_exact_paths_v1(
        state_root,
        frozenset(relative for relative, _path in validated),
    )
    writer = _optional_external_gpu_writer_authority_v1(state_root)
    return {
        "protected_state_fingerprint": protected,
        "external_volatile_state_observation": external,
        **writer,
    }


def _assert_protected_state_unchanged_v1(
    before: object,
    after: object,
) -> None:
    for value in (before, after):
        if (
            type(value) is not tuple
            or len(value) != 2
            or type(value[0]) is not int
            or value[0] < 0
            or type(value[1]) is not str
            or len(value[1]) != 64
        ):
            _fail()
    if before != after:
        _fail()


def _assert_external_state_ownership_stable_v1(
    before: dict[str, object],
    after: dict[str, object],
) -> None:
    before_paths = tuple(
        item["relative_path"]
        for item in before["external_volatile_state_observation"]
    )
    after_paths = tuple(
        item["relative_path"]
        for item in after["external_volatile_state_observation"]
    )
    if (
        before_paths != after_paths
        or before["external_gpu_writer_detected"]
        != after["external_gpu_writer_detected"]
        or before["external_active_run_id"] != after["external_active_run_id"]
    ):
        _fail()


def _git_process(
    repository_root: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            ("git", "-C", str(repository_root), *arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise _TrainerFitSmokeInvariantError() from error
    return completed


def _git_command(repository_root: Path, *arguments: str) -> str:
    completed = _git_process(repository_root, *arguments)
    if completed.returncode != 0:
        _fail()
    return completed.stdout


def _git_is_ancestor(
    repository_root: Path, ancestor: str, descendant: str
) -> bool:
    completed = _git_process(
        repository_root, "merge-base", "--is-ancestor", ancestor, descendant
    )
    if completed.returncode not in (0, 1):
        _fail()
    return completed.returncode == 0


def _publication_commit_contract_v1(
    repository_root: Path, commit: str
) -> dict[str, object] | None:
    parents = _git_command(
        repository_root, "show", "-s", "--format=%P", commit
    ).strip().split()
    subject = _git_command(
        repository_root, "show", "-s", "--format=%s", commit
    ).strip()
    if parents != [_EXPECTED_HEAD_V1] or subject != _EXPECTED_PUBLICATION_SUBJECT_V1:
        return None
    changed = tuple(
        tuple(line.split("\t", 1))
        for line in _git_command(
            repository_root,
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            commit,
        ).splitlines()
        if line
    )
    if changed != tuple(("A", path) for path in sorted(_CANDIDATE_RELATIVE_PATHS_V1)):
        return None
    tree_rows = tuple(
        line.split(maxsplit=3)
        for line in _git_command(
            repository_root,
            "ls-tree",
            commit,
            "--",
            *sorted(_CANDIDATE_RELATIVE_PATHS_V1),
        ).splitlines()
        if line
    )
    if (
        len(tree_rows) != 2
        or {row[3] for row in tree_rows} != set(_CANDIDATE_RELATIVE_PATHS_V1)
        or any(row[0] != "100644" or row[1] != "blob" for row in tree_rows)
    ):
        return None
    blobs = {row[3]: row[2] for row in tree_rows}
    return {
        "commit": commit,
        "parent": _EXPECTED_HEAD_V1,
        "subject": subject,
        "changed_paths": tuple(path for _status, path in changed),
        "changed_statuses": tuple(status for status, _path in changed),
        "git_modes": {path: "100644" for path in blobs},
        "blobs": blobs,
    }


def _working_bytes_match_commit_v1(
    repository_root: Path, commit: str
) -> bool:
    for relative in _CANDIDATE_RELATIVE_PATHS_V1:
        path = repository_root / relative
        try:
            metadata = path.lstat()
            working = path.read_bytes()
        except OSError as error:
            raise _TrainerFitSmokeInvariantError() from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            return False
        blob = _git_process(repository_root, "show", f"{commit}:{relative}")
        if blob.returncode != 0 or blob.stdout.encode("utf-8") != working:
            return False
    return True


def _git_snapshot(repository_root: Path) -> dict[str, object]:
    branch = _git_command(repository_root, "branch", "--show-current").strip()
    head = _git_command(repository_root, "rev-parse", "HEAD").strip()
    origin = _git_command(repository_root, "rev-parse", "origin/main").strip()
    divergence = _git_command(
        repository_root,
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...origin/main",
    ).strip().split()
    status = tuple(
        line
        for line in _git_command(
            repository_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if line
    )
    staged = tuple(
        line
        for line in _git_command(
            repository_root, "diff", "--cached", "--name-status"
        ).splitlines()
        if line
    )
    if branch != "main" or len(divergence) != 2 or staged:
        _fail()
    try:
        ahead, behind = (int(value) for value in divergence)
    except ValueError as error:
        raise _TrainerFitSmokeInvariantError() from error

    lifecycle: str
    publication: dict[str, object] | None
    if head == _EXPECTED_HEAD_V1:
        if origin != _EXPECTED_HEAD_V1 or (ahead, behind) != (0, 0):
            _fail()
        expected_status = tuple(
            f"?? {path}" for path in sorted(_CANDIDATE_RELATIVE_PATHS_V1)
        )
        if status != expected_status:
            _fail()
        for relative in _CANDIDATE_RELATIVE_PATHS_V1:
            if (
                _git_process(
                    repository_root, "cat-file", "-e", f"HEAD:{relative}"
                ).returncode
                == 0
                or _git_process(
                    repository_root, "ls-files", "--error-unmatch", relative
                ).returncode
                == 0
            ):
                _fail()
        lifecycle = "precommit-untracked"
        publication = None
    else:
        if status or not _git_is_ancestor(repository_root, _EXPECTED_HEAD_V1, head):
            _fail()
        touching_commits = tuple(
            line
            for line in _git_command(
                repository_root,
                "rev-list",
                head,
                "--",
                *sorted(_CANDIDATE_RELATIVE_PATHS_V1),
            ).splitlines()
            if line
        )
        candidates = tuple(
            contract
            for commit in touching_commits
            if (contract := _publication_commit_contract_v1(repository_root, commit))
            is not None
        )
        if len(candidates) != 1:
            _fail()
        publication = candidates[0]
        publication_commit = str(publication["commit"])
        if (
            not _git_is_ancestor(repository_root, publication_commit, head)
            or not _working_bytes_match_commit_v1(
                repository_root, publication_commit
            )
            or _git_command(
                repository_root,
                "rev-list",
                f"{publication_commit}..{head}",
                "--",
                *sorted(_CANDIDATE_RELATIVE_PATHS_V1),
            ).strip()
        ):
            _fail()
        if head == publication_commit:
            if (
                origin == _EXPECTED_HEAD_V1
                and (ahead, behind) == (1, 0)
            ):
                lifecycle = "committed-unpushed"
            elif origin == publication_commit and (ahead, behind) == (0, 0):
                lifecycle = "published-successor"
            else:
                _fail()
        else:
            if (
                behind != 0
                or not _git_is_ancestor(repository_root, publication_commit, origin)
                or not _git_is_ancestor(repository_root, origin, head)
            ):
                _fail()
            lifecycle = "published-descendant"
    return {
        "lifecycle": lifecycle,
        "baseline_HEAD": _EXPECTED_HEAD_V1,
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "status": status,
        "staged": staged,
        "publication_commit": (
            None if publication is None else publication["commit"]
        ),
        "publication_contract": publication,
    }


def _protected_file_paths(
    *, repository_root: Path, state_root: Path, checkpoint_path: Path
) -> dict[str, Path]:
    scheduler_paths = mixed_scheduler._protected_sources_v1(
        repository_root=repository_root,
        state_root=state_root,
        checkpoint_path=checkpoint_path,
    )
    return {
        **scheduler_paths,
        "published_mixed_bridge": repository_root
        / "src/covalent_ext/"
        "covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1.py",
        "published_mixed_bridge_tests": repository_root
        / "tests/test_covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1.py",
        "published_mixed_scheduler": repository_root
        / "src/covalent_ext/"
        "covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1.py",
        "published_mixed_tensorizer": repository_root
        / "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py",
        "published_current11_lightning": repository_root
        / "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "published_current11_formal_trainer": repository_root
        / "src/covalent_ext/covapie_current11_formal_trainer_v1.py",
    }


def _protected_file_snapshot(paths: dict[str, Path]) -> dict[str, tuple[int, int, str]]:
    snapshot = {name: _file_fingerprint(path) for name, path in paths.items()}
    if (
        snapshot["legacy_checkpoint"][2] != _EXPECTED_CHECKPOINT_SHA256_V1
        or snapshot["published_mixed_bridge"][2] != _EXPECTED_BRIDGE_SHA256_V1
        or snapshot["published_mixed_bridge_tests"][2]
        != _EXPECTED_BRIDGE_TEST_SHA256_V1
    ):
        _fail()
    return snapshot


def _build_real_exact16_batch_v1(
    *, normalized_repository_root: Path, repository_root: Path, state_root: Path
) -> mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
    real = current11_smoke._build_real_current11_batch_v1(
        repo_root=normalized_repository_root,
        state_root=state_root,
    )
    schedule_dataset = mixed_scheduler._Exact16ScheduleDatasetV1(
        epoch=0, task_schedule_seed=0
    )
    build_loader = DataLoader(
        schedule_dataset,
        batch_size=16,
        shuffle=False,
        num_workers=0,
        drop_last=False,
        pin_memory=False,
        persistent_workers=False,
        collate_fn=mixed_scheduler._Exact16DataLoaderCollatorV1(
            current11_batch=real["model_batch"],
            current11_runtime_result=real["runtime"],
            current11_authoritative_supervision=real["authoritative_supervision"],
            repository_root=repository_root,
            state_root=state_root,
        ),
    )
    iterator = iter(build_loader)
    mixed_batch = next(iterator)
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        _fail()
    mixed_scheduler.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
        mixed_batch
    )
    if (
        type(mixed_batch) is not mixed_scheduler.CovapieExpandedCysSgMixedBatchV1
        or mixed_batch.scheduled_task_ids != _EXPECTED_TASKS_V1
        or mixed_batch.k36_batch_indices != _EXPECTED_K36_INDICES_V1
        or tuple(
            mixed_batch.scheduled_task_ids[index]
            for index in mixed_batch.k36_batch_indices
        )
        != _EXPECTED_K36_TASKS_V1
        or len(mixed_batch.model_input_batch["lig_coords"]) != 468
        or len(mixed_batch.model_input_batch["pocket_coords"]) != 3335
        or len(mixed_batch.supervision.pair_candidate_batch_index) != 2808
        or int(mixed_batch.supervision.pair_candidate_is_positive.sum().item()) != 16
    ):
        _fail()
    return mixed_batch


class _PrivateMixedTrainerFitCompatibilityModel(
    mixed_bridge.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
):
    """Active-Lightning hook compatibility; no model computation changes."""

    validation_epoch_end = None

    def configure_gradient_clipping(
        self,
        optimizer: torch.optim.Optimizer,
        *args: object,
        **kwargs: object,
    ) -> None:
        del optimizer
        if set(kwargs) - {
            "optimizer_idx", "gradient_clip_val", "gradient_clip_algorithm"
        }:
            _fail()
        optimizer_idx_supplied = "optimizer_idx" in kwargs
        optimizer_idx = kwargs.get("optimizer_idx")
        gradient_clip_val = kwargs.get("gradient_clip_val")
        gradient_clip_algorithm = kwargs.get("gradient_clip_algorithm")
        if len(args) == 2 and not kwargs:
            gradient_clip_val, gradient_clip_algorithm = args
        elif len(args) == 3 and not kwargs:
            optimizer_idx, gradient_clip_val, gradient_clip_algorithm = args
            optimizer_idx_supplied = True
        elif (
            len(args) == 1
            and type(args[0]) is int
            and "optimizer_idx" not in kwargs
        ):
            optimizer_idx = args[0]
            optimizer_idx_supplied = True
        elif (
            len(args) == 2
            and type(args[0]) is int
            and "optimizer_idx" not in kwargs
            and "gradient_clip_val" not in kwargs
        ):
            optimizer_idx, gradient_clip_val = args
            optimizer_idx_supplied = True
        elif args:
            _fail()
        if (
            optimizer_idx_supplied
            and (type(optimizer_idx) is not int or optimizer_idx != 0)
        ):
            _fail()
        if gradient_clip_val is not None or gradient_clip_algorithm is not None:
            _fail()


def _instantiate_mixed_model_v1(
    *,
    owner: type[mixed_bridge.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1],
    constructor: dict[str, object],
    normalized_repository_root: Path,
    state_root: Path,
    legacy_setup_data_root: Path,
    output_root: Path,
) -> mixed_bridge.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1:
    validated = formal_trainer._validate_legacy_constructor_envelope_v1(constructor)
    egnn_params = dict(validated["egnn_params"])
    egnn_params["device"] = "cpu"
    loss_weights = {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.1,
    }
    torch.manual_seed(_MODEL_INITIALIZATION_SEED_V1)
    with contextlib.redirect_stdout(io.StringIO()):
        model = owner(
            outdir=output_root,
            dataset="crossdock",
            datadir=str(legacy_setup_data_root),
            batch_size=16,
            lr=validated["lr"],
            egnn_params=Namespace(**egnn_params),
            diffusion_params=Namespace(**validated["diffusion_params"]),
            num_workers=0,
            augment_noise=validated["augment_noise"],
            augment_rotation=validated["augment_rotation"],
            clip_grad=False,
            eval_epochs=validated["eval_epochs"],
            eval_params=Namespace(**validated["eval_params"]),
            visualize_sample_epoch=validated["visualize_sample_epoch"],
            visualize_chain_epoch=validated["visualize_chain_epoch"],
            auxiliary_loss=False,
            loss_params=Namespace(**validated["loss_params"]),
            mode="pocket_conditioning",
            node_histogram=validated["node_histogram"],
            pocket_representation="full-atom",
            virtual_nodes=False,
            target_residue_atom_conditioning=True,
            covapie_current11_task2_runtime_enabled=True,
            covapie_repository_root=str(normalized_repository_root),
            covapie_state_root=str(state_root),
            covapie_current11_training_enabled=True,
            covapie_current11_task_schedule_seed=0,
            covapie_current11_pair_contrastive_temperature=1.0,
            covapie_current11_loss_weights=loss_weights,
            covapie_current11_authoritative_supervision_batch_field=(
                AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1
            ),
        )
    if (
        type(model) is not owner
        or model.batch_size != 16
        or model.num_workers != 0
        or model.clip_grad is not False
        or model.automatic_optimization is not True
        or len(model.state_dict()) != 141
    ):
        _fail()
    return model


class _SingleExact16MixedBatchDatasetV1(
    Dataset[mixed_scheduler.CovapieExpandedCysSgMixedBatchV1]
):
    def __init__(
        self, batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1
    ) -> None:
        if type(batch) is not mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
            _fail()
        self._batch = batch
        self.getitem_call_count = 0

    def __len__(self) -> int:
        return 1

    def __getitem__(
        self, index: int
    ) -> mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        self.getitem_call_count += 1
        return self._batch


class _SingleExact16MixedBatchCollatorV1:
    def __init__(
        self,
        batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1,
        *,
        validate_batch: bool,
    ) -> None:
        self._batch = batch
        self._validate_batch = validate_batch
        self.call_count = 0

    def __call__(
        self, rows: list[mixed_scheduler.CovapieExpandedCysSgMixedBatchV1]
    ) -> mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
        self.call_count += 1
        if len(rows) != 1 or rows[0] is not self._batch:
            _fail()
        if self._validate_batch:
            mixed_scheduler.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
                rows[0]
            )
        return rows[0]


class _Exact16MixedTrainerFitDataModuleV1(pl.LightningDataModule):
    """One loader plus a neutral pre-transfer owner for the frozen dataclass."""

    def __init__(
        self,
        batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1,
        *,
        validate_collated_batch: bool = True,
    ) -> None:
        super().__init__()
        self.batch = batch
        self.dataset = _SingleExact16MixedBatchDatasetV1(batch)
        self.collator = _SingleExact16MixedBatchCollatorV1(
            batch, validate_batch=validate_collated_batch
        )
        self.loader: DataLoader | None = None
        self.setup_call_count = 0
        self.train_dataloader_call_count = 0
        self.before_batch_transfer_call_count = 0
        self.after_batch_transfer_call_count = 0
        self.transferred_batch_exact_type = False
        self.transferred_batch_rebuilt = False
        self.transferred_metadata_unchanged = False
        self.transferred_tensors_on_cpu = False

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail()
        self.setup_call_count += 1

    def train_dataloader(self) -> DataLoader:
        self.train_dataloader_call_count += 1
        if self.loader is None:
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
            or self.loader.num_workers != 0
            or self.loader.drop_last is not False
            or self.loader.pin_memory is not False
            or self.loader.persistent_workers is not False
            or type(self.loader.sampler) is not SequentialSampler
        ):
            _fail()
        return self.loader

    def val_dataloader(self) -> None:
        return None

    def test_dataloader(self) -> None:
        return None

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
        self.before_batch_transfer_call_count += 1
        if (
            type(batch) is not mixed_scheduler.CovapieExpandedCysSgMixedBatchV1
            or batch is not self.batch
            or dataloader_idx != 0
        ):
            _fail()
        return batch

    def on_after_batch_transfer(
        self, batch: object, dataloader_idx: int
    ) -> mixed_scheduler.CovapieExpandedCysSgMixedBatchV1:
        self.after_batch_transfer_call_count += 1
        if (
            type(batch) is not mixed_scheduler.CovapieExpandedCysSgMixedBatchV1
            or dataloader_idx != 0
        ):
            _fail()
        self.transferred_batch_exact_type = True
        self.transferred_batch_rebuilt = (
            batch is not self.batch
            and batch.model_input_batch is not self.batch.model_input_batch
            and batch.supervision is not self.batch.supervision
        )
        self.transferred_metadata_unchanged = all(
            getattr(batch, name) is getattr(self.batch, name)
            for name in (
                "sample_identities",
                "role_profiles",
                "scheduled_task_ids",
                "current11_batch_indices",
                "k36_batch_indices",
            )
        )
        tensors = [
            value
            for value in batch.model_input_batch.values()
            if isinstance(value, torch.Tensor)
        ] + [
            getattr(batch.supervision, field.name)
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        ]
        self.transferred_tensors_on_cpu = bool(tensors) and all(
            tensor.device.type == "cpu" for tensor in tensors
        )
        if (
            not self.transferred_batch_rebuilt
            or not self.transferred_metadata_unchanged
            or not self.transferred_tensors_on_cpu
        ):
            _fail()
        return batch


def _nonzero_finite_gradient(parameter: torch.Tensor) -> bool:
    gradient = parameter.grad
    return bool(
        gradient is not None
        and torch.isfinite(gradient).all().item()
        and torch.count_nonzero(gradient).item() > 0
    )


class _TrainerFitObserverV1(pl.Callback):
    """Strictly observational in-memory lifecycle and objective evidence."""

    def __init__(
        self,
        *,
        original_batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1,
        checkpoint_state: dict[str, torch.Tensor],
        enforce_expected_schedule: bool = True,
    ) -> None:
        super().__init__()
        self.original_batch = original_batch
        self.checkpoint_state = checkpoint_state
        self.enforce_expected_schedule = enforce_expected_schedule
        self.fit_start_count = 0
        self.train_batch_start_count = 0
        self.train_batch_end_count = 0
        self.before_backward_count = 0
        self.after_backward_count = 0
        self.before_optimizer_step_count = 0
        self.before_zero_grad_count = 0
        self.validation_start_count = 0
        self.validation_batch_count = 0
        self.test_start_count = 0
        self.test_batch_count = 0
        self.current_epoch_during_batch: int | None = None
        self.transferred_batch_exact_type = False
        self.transferred_batch_rebuilt = False
        self.transferred_metadata_unchanged = False
        self.nested_tensors_on_model_device = False
        self.optimizer_type: str | None = None
        self.optimizer_parameter_unique = False
        self.optimizer_parameter_set_exact = False
        self.all_existing_gradients_finite = False
        self.shared_pretrained_nonzero_gradient = False
        self.target_residue_embedding_nonzero_gradient = False
        self.role_mask_anchor_group_nonzero_gradient = False
        self.pair_head_nonzero_gradient = False
        self.geometry_head_nonzero_gradient = False
        self.metrics: dict[str, float] | None = None
        self.loss_evidence: dict[str, object] | None = None
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
        if (
            batch_idx != 0
            or type(batch) is not mixed_scheduler.CovapieExpandedCysSgMixedBatchV1
            or pl_module.training is not True
            or int(pl_module.current_epoch) != 0
            or len(batch.sample_identities) != 16
            or (
                self.enforce_expected_schedule
                and (batch.epoch != 0 or batch.task_schedule_seed != 0)
            )
        ):
            _fail()
        if self.enforce_expected_schedule:
            mixed_scheduler.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
                batch
            )
        self.current_epoch_during_batch = int(pl_module.current_epoch)
        self.transferred_batch_exact_type = True
        self.transferred_batch_rebuilt = (
            batch is not self.original_batch
            and batch.model_input_batch is not self.original_batch.model_input_batch
            and batch.supervision is not self.original_batch.supervision
        )
        self.transferred_metadata_unchanged = all(
            getattr(batch, name) is getattr(self.original_batch, name)
            for name in (
                "sample_identities",
                "role_profiles",
                "scheduled_task_ids",
                "current11_batch_indices",
                "k36_batch_indices",
            )
        )
        model_device = next(pl_module.parameters()).device
        tensors = [
            value
            for value in batch.model_input_batch.values()
            if isinstance(value, torch.Tensor)
        ] + [
            getattr(batch.supervision, field.name)
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        ]
        self.nested_tensors_on_model_device = bool(tensors) and all(
            tensor.device == model_device for tensor in tensors
        )
        if (
            not self.transferred_batch_rebuilt
            or not self.transferred_metadata_unchanged
            or not self.nested_tensors_on_model_device
        ):
            _fail()

    def on_before_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule, loss: torch.Tensor
    ) -> None:
        del trainer, pl_module
        self.before_backward_count += 1
        if loss.ndim != 0 or not loss.requires_grad or not bool(torch.isfinite(loss).item()):
            _fail()

    def on_after_backward(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer, pl_module
        self.after_backward_count += 1

    def on_before_optimizer_step(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
        optimizer_idx: int | None = None,
    ) -> None:
        del trainer
        if optimizer_idx is not None and (
            type(optimizer_idx) is not int or optimizer_idx != 0
        ):
            _fail()
        self.before_optimizer_step_count += 1
        named_parameters = dict(pl_module.named_parameters())
        model_parameters = list(named_parameters.values())
        optimizer_parameters = [
            parameter
            for group in optimizer.param_groups
            for parameter in group["params"]
        ]
        model_ids = [id(parameter) for parameter in model_parameters]
        optimizer_ids = [id(parameter) for parameter in optimizer_parameters]
        self.optimizer_type = type(optimizer).__name__
        self.optimizer_parameter_unique = (
            len(optimizer_ids) == len(set(optimizer_ids))
        )
        self.optimizer_parameter_set_exact = set(optimizer_ids) == set(model_ids)
        gradients = [
            parameter.grad
            for parameter in model_parameters
            if parameter.grad is not None
        ]
        self.all_existing_gradients_finite = bool(gradients) and all(
            bool(torch.isfinite(gradient).all().item()) for gradient in gradients
        )
        shared = set(named_parameters) & set(self.checkpoint_state)
        target = checkpoint_migration.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
        role = {
            name
            for name in named_parameters
            if name.startswith((
                "covapie_current11_auxiliary_model_v1.role_embedding.",
                "covapie_current11_auxiliary_model_v1.task_embedding.",
                "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
                "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
                "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
            ))
        }
        pair = {
            name
            for name in named_parameters
            if name.startswith((
                "covapie_current11_auxiliary_model_v1.pair_embedding.",
                "covapie_current11_auxiliary_model_v1.pair_logit.",
            ))
        }
        geometry = {
            name
            for name in named_parameters
            if name.startswith(
                "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
            )
        }
        self.shared_pretrained_nonzero_gradient = any(
            _nonzero_finite_gradient(named_parameters[name]) for name in shared
        )
        self.target_residue_embedding_nonzero_gradient = _nonzero_finite_gradient(
            named_parameters[target]
        )
        self.role_mask_anchor_group_nonzero_gradient = any(
            _nonzero_finite_gradient(named_parameters[name]) for name in role
        )
        self.pair_head_nonzero_gradient = any(
            _nonzero_finite_gradient(named_parameters[name]) for name in pair
        )
        self.geometry_head_nonzero_gradient = any(
            _nonzero_finite_gradient(named_parameters[name]) for name in geometry
        )
        if (
            not isinstance(optimizer, torch.optim.AdamW)
            or len(model_ids) != len(set(model_ids))
            or not self.optimizer_parameter_unique
            or not self.optimizer_parameter_set_exact
            or not self.all_existing_gradients_finite
            or not self.shared_pretrained_nonzero_gradient
            or not self.target_residue_embedding_nonzero_gradient
            or not self.role_mask_anchor_group_nonzero_gradient
            or not self.pair_head_nonzero_gradient
            or self.geometry_head_nonzero_gradient
        ):
            _fail()

    def on_before_zero_grad(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        optimizer: torch.optim.Optimizer,
    ) -> None:
        del trainer, pl_module, optimizer
        self.before_zero_grad_count += 1

    def on_train_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: object,
        batch: object,
        batch_idx: int,
    ) -> None:
        del trainer, pl_module, batch
        self.train_batch_end_count += 1
        if (
            batch_idx != 0
            or type(outputs) is not dict
            or set(outputs) != _EXPECTED_METRIC_KEYS_V1
            or any(
                not isinstance(value, torch.Tensor)
                or not bool(torch.isfinite(value).all().item())
                for value in outputs.values()
            )
        ):
            _fail()
        self.metrics = {
            name: float(value.detach().item()) for name, value in outputs.items()
        }
        supervision = self.original_batch.supervision
        geometry_valid_count = int(
            supervision.pre_post_geometry_component_loss_mask.any(dim=1).sum().item()
        )
        if (
            self.metrics["loss_pre_post_geometry"] != 0.0
            or geometry_valid_count != 0
            or not bool(supervision.sample_training_admitted.all().item())
            or not bool(supervision.pair_positive_candidate_valid.all().item())
            or not bool(
                supervision.pair_contrastive_sample_loss_mask.all().item()
            )
        ):
            _fail()
        self.loss_evidence = {
            "total_loss": self.metrics["loss"],
            "base_loss": self.metrics["loss_base_diffusion"],
            "pair_prediction_loss": self.metrics[
                "loss_covalent_pair_prediction"
            ],
            "geometry_loss": self.metrics["loss_pre_post_geometry"],
            "contrastive_loss": self.metrics[
                "loss_covalent_pair_contrastive"
            ],
            "base_valid_sample_count": 16,
            "pair_valid_sample_count": 16,
            "geometry_valid_sample_count": geometry_valid_count,
            "contrastive_valid_sample_count": 16,
            "trainer_training_step_exposes_per_sample_contributions": False,
        }

    def on_validation_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer, pl_module
        self.validation_start_count += 1

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

    def on_test_start(
        self, trainer: pl.Trainer, pl_module: pl.LightningModule
    ) -> None:
        del trainer, pl_module
        self.test_start_count += 1

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
    datamodule: _Exact16MixedTrainerFitDataModuleV1
    observer: _TrainerFitObserverV1
    trainer_api_family: str
    sampler_control_parameter: str
    precision_argument: object
    trainer_kwargs: dict[str, object]
    trainer_fit_signature_parameters: tuple[str, ...]


def _trainer_configuration_for_signature_v1(
    *,
    signature: inspect.Signature,
    callbacks: list[pl.Callback],
    default_root_dir: Path,
) -> tuple[dict[str, object], dict[str, object]]:
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
    }
    if not required <= parameters:
        _fail()
    if "use_distributed_sampler" in parameters:
        trainer_api_family = "lightning-2.x"
        sampler_parameter = "use_distributed_sampler"
        precision_argument: object = "32-true"
    elif "replace_sampler_ddp" in parameters:
        trainer_api_family = "lightning-1.x"
        sampler_parameter = "replace_sampler_ddp"
        precision_argument = 32
    else:
        _fail()
    required_values: dict[str, object] = {
        "accelerator": "cpu",
        "devices": 1,
        "num_nodes": 1,
        "precision": precision_argument,
        "max_epochs": 1,
        "min_epochs": 1,
        "max_steps": 1,
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
        "default_root_dir": default_root_dir,
        sampler_parameter: False,
    }
    optional_values: dict[str, object] = {
        "check_val_every_n_epoch": 1,
        "val_check_interval": 1.0,
        "gradient_clip_algorithm": None,
        "benchmark": False,
        "reload_dataloaders_every_n_epochs": 0,
        "sync_batchnorm": False,
        "enable_model_summary": False,
        "log_every_n_steps": 1,
        "profiler": None,
    }
    kwargs = dict(required_values)
    kwargs.update({
        name: value
        for name, value in optional_values.items()
        if name in parameters
    })
    if not set(kwargs) <= parameters:
        _fail()
    return kwargs, {
        "trainer_api_family": trainer_api_family,
        "sampler_control_parameter": sampler_parameter,
        "precision_argument": precision_argument,
    }


def _trainer_fit_signature_parameters_v1(
    signature: inspect.Signature,
) -> tuple[str, ...]:
    parameters = tuple(signature.parameters)
    if not {"model", "datamodule", "ckpt_path"} <= set(parameters):
        _fail()
    return parameters


def _build_fit_runtime_v1(
    *,
    batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1,
    checkpoint_state: dict[str, torch.Tensor],
    default_root_dir: Path,
    validate_collated_batch: bool = True,
    enforce_expected_schedule_observation: bool = True,
) -> _FitRuntimeV1:
    observer = _TrainerFitObserverV1(
        original_batch=batch,
        checkpoint_state=checkpoint_state,
        enforce_expected_schedule=enforce_expected_schedule_observation,
    )
    datamodule = _Exact16MixedTrainerFitDataModuleV1(
        batch, validate_collated_batch=validate_collated_batch
    )
    trainer_signature = inspect.signature(pl.Trainer.__init__)
    trainer_kwargs, compatibility = _trainer_configuration_for_signature_v1(
        signature=trainer_signature,
        callbacks=[observer],
        default_root_dir=default_root_dir,
    )
    fit_parameters = _trainer_fit_signature_parameters_v1(
        inspect.signature(pl.Trainer.fit)
    )
    trainer = pl.Trainer(**trainer_kwargs)
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
        _fail()
    return _FitRuntimeV1(
        trainer=trainer,
        datamodule=datamodule,
        observer=observer,
        trainer_api_family=str(compatibility["trainer_api_family"]),
        sampler_control_parameter=str(
            compatibility["sampler_control_parameter"]
        ),
        precision_argument=compatibility["precision_argument"],
        trainer_kwargs=trainer_kwargs,
        trainer_fit_signature_parameters=fit_parameters,
    )


def _invoke_trainer_fit_v1(
    *, model: pl.LightningModule, runtime: _FitRuntimeV1
) -> None:
    previous_sigint_handler = signal.getsignal(signal.SIGINT)
    try:
        runtime.trainer.fit(
            model=model,
            datamodule=runtime.datamodule,
            ckpt_path=None,
        )
    except SystemExit:
        if isinstance(runtime.observer.process_control_exception, KeyboardInterrupt):
            raise runtime.observer.process_control_exception
        raise
    finally:
        if signal.getsignal(signal.SIGINT) is not previous_sigint_handler:
            signal.signal(signal.SIGINT, previous_sigint_handler)


def _state_parameter_buffer_parity(
    *, published_model: pl.LightningModule, compatibility_model: pl.LightningModule
) -> tuple[bool, bool, bool]:
    published_state = published_model.state_dict()
    compatibility_state = compatibility_model.state_dict()
    state_parity = tuple(published_state) == tuple(compatibility_state) and all(
        torch.equal(published_state[name], compatibility_state[name])
        for name in published_state
    )
    published_parameters = dict(published_model.named_parameters())
    compatibility_parameters = dict(compatibility_model.named_parameters())
    parameter_parity = (
        tuple(published_parameters) == tuple(compatibility_parameters)
        and all(
            torch.equal(
                published_parameters[name].detach(),
                compatibility_parameters[name].detach(),
            )
            for name in published_parameters
        )
    )
    published_buffers = dict(published_model.named_buffers())
    compatibility_buffers = dict(compatibility_model.named_buffers())
    buffer_parity = tuple(published_buffers) == tuple(compatibility_buffers) and all(
        torch.equal(published_buffers[name], compatibility_buffers[name])
        for name in published_buffers
    )
    return state_parity, parameter_parity, buffer_parity


def _validate_k36_participation(
    batch: mixed_scheduler.CovapieExpandedCysSgMixedBatchV1,
) -> None:
    supervision = batch.supervision
    for index in batch.k36_batch_indices:
        ligand_rows = batch.model_input_batch["lig_mask"] == index
        if (
            not bool(supervision.sample_training_admitted[index])
            or not bool(supervision.canonical_task_valid[index])
            or int(supervision.canonical_task_id[index].item()) not in (0, 3, 4)
            or not bool(
                supervision.ligand_active_diffusion_loss_mask[
                    ligand_rows, 0
                ].any().item()
            )
            or not bool(supervision.pair_positive_candidate_valid[index])
            or int(supervision.pair_negative_count[index].item()) <= 0
        ):
            _fail()


def _run_impl(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str,
) -> dict[str, object]:
    repository = _require_root(repository_root)
    state = _require_root(state_root)
    if type(device) is not str or device != "cpu":
        _fail()
    if type(checkpoint_path) is not _PATH_TYPE or not checkpoint_path.is_absolute():
        _fail()

    git_before = _git_snapshot(repository)
    checkpoint = checkpoint_migration.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path
    )
    if checkpoint["checkpoint_sha256"] != _EXPECTED_CHECKPOINT_SHA256_V1:
        _fail()
    checkpoint_state = checkpoint["state_dict"]
    if not isinstance(checkpoint_state, dict):
        _fail()
    protected_paths = _protected_file_paths(
        repository_root=repository,
        state_root=state,
        checkpoint_path=checkpoint_path,
    )
    protected_before = _protected_file_snapshot(protected_paths)
    state_before = _state_integrity_snapshot_v1(state)
    raw_before = _tree_fingerprint(repository / "data/raw")

    temporary_path: Path | None = None
    fit_result: dict[str, object]
    with tempfile.TemporaryDirectory(
        prefix="covapie_exact16_trainer_fit_smoke_"
    ) as temporary:
        temporary_path = Path(temporary)
        normalized_repository = temporary_path / "normalized_repository"
        mixed_scheduler._clone_head_v1(repository, normalized_repository)
        mixed_batch = _build_real_exact16_batch_v1(
            normalized_repository_root=normalized_repository,
            repository_root=repository,
            state_root=state,
        )
        _validate_k36_participation(mixed_batch)

        legacy_setup_data = temporary_path / "legacy_setup_data"
        legacy_setup_data.mkdir(mode=0o700)
        formal_carrier = state / formal_trainer.FORMAL_CARRIER_RELATIVE_PATH_V1
        for split in ("train", "val"):
            (legacy_setup_data / f"{split}.npz").symlink_to(formal_carrier)

        published_model = _instantiate_mixed_model_v1(
            owner=(
                mixed_bridge
                .CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
            ),
            constructor=checkpoint["legacy_constructor"],
            normalized_repository_root=normalized_repository,
            state_root=state,
            legacy_setup_data_root=legacy_setup_data,
            output_root=temporary_path / "published_model_output",
        )
        published_migration = (
            checkpoint_migration
            .migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=published_model,
                checkpoint_state_dict=checkpoint_state,
            )
        )
        published_before_probe = {
            name: parameter.detach().clone()
            for name, parameter in published_model.named_parameters()
        }
        direct_runtime = _build_fit_runtime_v1(
            batch=mixed_batch,
            checkpoint_state=checkpoint_state,
            default_root_dir=temporary_path / "direct_bridge_probe",
        )
        torch.manual_seed(_TRAINER_FIT_SEED_V1)
        legacy_validation_epoch_end_compat_shim_used = False
        direct_rejection_message: str | None = None
        try:
            _invoke_trainer_fit_v1(model=published_model, runtime=direct_runtime)
        except NotImplementedError as error:
            if "validation_epoch_end" not in str(error):
                raise
            direct_rejection_message = str(error)
            legacy_validation_epoch_end_compat_shim_used = True
            if (
                direct_runtime.trainer.global_step != 0
                or direct_runtime.datamodule.dataset.getitem_call_count != 0
                or direct_runtime.observer.train_batch_start_count != 0
                or any(
                    not torch.equal(parameter.detach(), published_before_probe[name])
                    for name, parameter in published_model.named_parameters()
                )
            ):
                _fail()

        if legacy_validation_epoch_end_compat_shim_used:
            fit_model = _instantiate_mixed_model_v1(
                owner=_PrivateMixedTrainerFitCompatibilityModel,
                constructor=checkpoint["legacy_constructor"],
                normalized_repository_root=normalized_repository,
                state_root=state,
                legacy_setup_data_root=legacy_setup_data,
                output_root=temporary_path / "compatibility_model_output",
            )
            migration = (
                checkpoint_migration
                .migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                    model=fit_model,
                    checkpoint_state_dict=checkpoint_state,
                )
            )
            state_parity, parameter_parity, buffer_parity = (
                _state_parameter_buffer_parity(
                    published_model=published_model,
                    compatibility_model=fit_model,
                )
            )
            if not state_parity or not parameter_parity or not buffer_parity:
                _fail()
            runtime = _build_fit_runtime_v1(
                batch=mixed_batch,
                checkpoint_state=checkpoint_state,
                default_root_dir=temporary_path / "actual_fit",
            )
            torch.manual_seed(_TRAINER_FIT_SEED_V1)
            parameter_before = {
                name: parameter.detach().clone()
                for name, parameter in fit_model.named_parameters()
            }
            _invoke_trainer_fit_v1(model=fit_model, runtime=runtime)
        else:
            fit_model = published_model
            migration = published_migration
            state_parity = True
            parameter_parity = True
            buffer_parity = True
            runtime = direct_runtime
            parameter_before = published_before_probe

        observer = runtime.observer
        datamodule = runtime.datamodule
        trainer = runtime.trainer
        named_parameters = dict(fit_model.named_parameters())
        changed_names = {
            name
            for name, parameter in named_parameters.items()
            if not torch.equal(parameter.detach(), parameter_before[name])
        }
        shared_names = set(named_parameters) & set(checkpoint_state)
        auxiliary_names = {
            name
            for name in named_parameters
            if name.startswith("covapie_current11_auxiliary_model_v1.")
        }
        target_name = checkpoint_migration.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
        shared_changed = bool(changed_names & shared_names)
        auxiliary_changed = bool(changed_names & auxiliary_names)
        target_changed = target_name in changed_names
        all_parameters_finite = all(
            bool(torch.isfinite(parameter).all().item())
            for parameter in named_parameters.values()
        )

        if (
            migration["checkpoint_key_count"] != 122
            or migration["target_model_key_count"] != 141
            or migration["shared_key_count"] != 122
            or migration["checkpoint_only_key_count"] != 0
            or migration["shared_shape_mismatch_count"] != 0
            or migration["full_target_strict_load"] is not True
            or migration["migration_missing_keys"] != ()
            or migration["migration_unexpected_keys"] != ()
            or trainer.global_step != 1
            or observer.fit_start_count != 1
            or observer.train_batch_start_count != 1
            or observer.train_batch_end_count != 1
            or observer.before_backward_count != 1
            or observer.after_backward_count != 1
            or observer.before_optimizer_step_count != 1
            or observer.before_zero_grad_count != 1
            or observer.validation_start_count != 0
            or observer.validation_batch_count != 0
            or observer.test_start_count != 0
            or observer.test_batch_count != 0
            or datamodule.dataset.getitem_call_count != 1
            or datamodule.collator.call_count != 1
            or datamodule.before_batch_transfer_call_count != 1
            or datamodule.after_batch_transfer_call_count != 1
            or not datamodule.transferred_batch_exact_type
            or not datamodule.transferred_batch_rebuilt
            or not datamodule.transferred_metadata_unchanged
            or not datamodule.transferred_tensors_on_cpu
            or observer.metrics is None
            or observer.loss_evidence is None
            or not shared_changed
            or not auxiliary_changed
            or not target_changed
            or not all_parameters_finite
        ):
            _fail()

        product_owner = (
            mixed_bridge
            .CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
        )
        published_transfer_method_identity_exact = (
            getattr(type(fit_model), "transfer_batch_to_device")
            is product_owner.transfer_batch_to_device
        )
        if (
            getattr(type(fit_model), "forward") is not product_owner.forward
            or getattr(type(fit_model), "training_step")
            is not product_owner.training_step
            or not published_transfer_method_identity_exact
            or getattr(type(fit_model), "configure_optimizers")
            is not product_owner.configure_optimizers
        ):
            _fail()

        fit_result = {
            "implementation_status": "passed",
            "active_python_version": platform.python_version(),
            "active_torch_version": str(torch.__version__),
            "active_lightning_version": str(pl.__version__),
            "declared_python_version": "3.10.4",
            "declared_torch_version": "2.0.1+cu118",
            "declared_lightning_version": "1.8.4",
            "active_environment_matches_repository_declared": (
                platform.python_version() == "3.10.4"
                and str(torch.__version__) == "2.0.1+cu118"
                and str(pl.__version__) == "1.8.4"
            ),
            "trainer_fit_signature": str(inspect.signature(pl.Trainer.fit)),
            "trainer_init_signature": str(inspect.signature(pl.Trainer.__init__)),
            "trainer_fit_signature_parameters": (
                runtime.trainer_fit_signature_parameters
            ),
            "trainer_api_family": runtime.trainer_api_family,
            "trainer_sampler_control_parameter": (
                runtime.sampler_control_parameter
            ),
            "trainer_precision_argument": runtime.precision_argument,
            "trainer_configuration_selected": {
                key: value
                for key, value in runtime.trainer_kwargs.items()
                if key != "callbacks"
            },
            "Trainer_fit": True,
            "single_batch_single_epoch_trainer_fit_smoke": True,
            "trainer_fit_train_batch_count": observer.train_batch_end_count,
            "trainer_fit_optimizer_step_count": observer.before_optimizer_step_count,
            "trainer_global_step": trainer.global_step,
            "trainer_fit_current_epoch_during_batch": (
                observer.current_epoch_during_batch
            ),
            "before_batch_transfer_call_count": (
                datamodule.before_batch_transfer_call_count
            ),
            "after_batch_transfer_call_count": (
                datamodule.after_batch_transfer_call_count
            ),
            "published_transfer_method_identity_exact": (
                published_transfer_method_identity_exact
            ),
            "trainer_fit_device_transfer_pipeline_pass": True,
            "trainer_fit_training_step_executed": True,
            "training_step_call_count": observer.train_batch_end_count,
            "trainer_fit_automatic_backward_executed": True,
            "automatic_backward_call_count": observer.after_backward_count,
            "trainer_fit_optimizer_step_executed": True,
            "zero_grad_lifecycle_call_count": observer.before_zero_grad_count,
            "automatic_optimization": fit_model.automatic_optimization,
            "trainer_fit_model_is_exact_published_bridge": (
                type(fit_model) is product_owner
            ),
            "legacy_validation_epoch_end_compat_shim_used": (
                legacy_validation_epoch_end_compat_shim_used
            ),
            "direct_published_bridge_rejection_message": direct_rejection_message,
            "smoke_only_legacy_hook_compatibility_subclass": (
                legacy_validation_epoch_end_compat_shim_used
            ),
            "compatibility_subclass_parent_exact_published_bridge": (
                not legacy_validation_epoch_end_compat_shim_used
                or _PrivateMixedTrainerFitCompatibilityModel.__bases__
                == (product_owner,)
            ),
            "compatibility_subclass_overridden_members": (
                ("validation_epoch_end", "configure_gradient_clipping")
                if legacy_validation_epoch_end_compat_shim_used
                else ()
            ),
            "compatibility_state_dict_exact_parity": state_parity,
            "compatibility_named_parameter_exact_parity": parameter_parity,
            "compatibility_named_buffer_exact_parity": buffer_parity,
            "model_state_dict_key_count": len(fit_model.state_dict()),
            "checkpoint_key_count": migration["checkpoint_key_count"],
            "target_model_key_count": migration["target_model_key_count"],
            "shared_exact_key_count": migration["shared_key_count"],
            "checkpoint_only_key_count": migration["checkpoint_only_key_count"],
            "shape_mismatch_count": migration["shared_shape_mismatch_count"],
            "full_target_strict_load": migration["full_target_strict_load"],
            "migration_missing_keys": migration["migration_missing_keys"],
            "migration_unexpected_keys": migration["migration_unexpected_keys"],
            "mixed_batch_sample_count": 16,
            "mixed_batch_current11_count": 11,
            "mixed_batch_k36_count": 5,
            "mixed_batch_ligand_node_count": 468,
            "mixed_batch_pocket_node_count": 3335,
            "mixed_batch_pair_candidate_count": 2808,
            "mixed_batch_positive_pair_count": 16,
            "mixed_batch_task_vector": mixed_batch.scheduled_task_ids,
            "mixed_batch_epoch": mixed_batch.epoch,
            "mixed_batch_task_schedule_seed": mixed_batch.task_schedule_seed,
            "k36_actual_batch_indices": mixed_batch.k36_batch_indices,
            "k36_scheduled_task_ids": _EXPECTED_K36_TASKS_V1,
            "K36_participated_in_actual_trainer_fit_objective": True,
            "DataLoader_executed": True,
            "DataLoader_dataset_length": len(datamodule.dataset),
            "DataLoader_batch_count": datamodule.collator.call_count,
            "DataLoader_batch_exact_type": datamodule.transferred_batch_exact_type,
            "DataLoader_num_workers": datamodule.loader.num_workers,
            "DataLoader_batch_size": datamodule.loader.batch_size,
            "DataLoader_sequential_sampler": (
                type(datamodule.loader.sampler) is SequentialSampler
            ),
            "DataLoader_drop_last": datamodule.loader.drop_last,
            "DataLoader_pin_memory": datamodule.loader.pin_memory,
            "DataLoader_persistent_workers": datamodule.loader.persistent_workers,
            "transferred_batch_rebuilt": datamodule.transferred_batch_rebuilt,
            "transferred_metadata_unchanged": (
                datamodule.transferred_metadata_unchanged
            ),
            "nested_tensors_on_model_device": observer.nested_tensors_on_model_device,
            "trainer_accelerator": type(trainer.accelerator).__name__,
            "trainer_strategy": type(trainer.strategy).__name__,
            "trainer_num_devices": trainer.num_devices,
            "trainer_max_epochs": trainer.max_epochs,
            "trainer_max_steps": trainer.max_steps,
            "trainer_limit_train_batches": trainer.limit_train_batches,
            "trainer_limit_val_batches": trainer.limit_val_batches,
            "trainer_limit_test_batches": trainer.limit_test_batches,
            "trainer_num_sanity_val_steps": trainer.num_sanity_val_steps,
            "trainer_accumulate_grad_batches": trainer.accumulate_grad_batches,
            "trainer_deterministic": True,
            "trainer_checkpointing_enabled": trainer.checkpoint_callback is not None,
            "logger_enabled": trainer.logger is not None,
            "validation_step_call_count": observer.validation_batch_count,
            "test_step_call_count": observer.test_batch_count,
            "optimizer_type": observer.optimizer_type,
            "optimizer_parameter_unique": observer.optimizer_parameter_unique,
            "optimizer_parameter_set_exact": observer.optimizer_parameter_set_exact,
            "all_existing_gradients_finite": (
                observer.all_existing_gradients_finite
            ),
            "shared_pretrained_nonzero_gradient": (
                observer.shared_pretrained_nonzero_gradient
            ),
            "target_residue_embedding_nonzero_gradient": (
                observer.target_residue_embedding_nonzero_gradient
            ),
            "role_mask_anchor_group_nonzero_gradient": (
                observer.role_mask_anchor_group_nonzero_gradient
            ),
            "pair_head_nonzero_gradient": observer.pair_head_nonzero_gradient,
            "geometry_head_nonzero_gradient": observer.geometry_head_nonzero_gradient,
            "shared_pretrained_parameter_changed": shared_changed,
            "new_covapie_parameter_changed": auxiliary_changed,
            "target_residue_parameter_changed": target_changed,
            "all_parameters_finite_after_fit": all_parameters_finite,
            **observer.loss_evidence,
            "training_step_metrics": observer.metrics,
            "all_enabled_losses_finite": True,
            "PRE_geometry_supervision_authority_complete": False,
            "checkpoint_saved": False,
            "state_modified": False,
            "persistent_output_created": False,
            "ready_for_single_batch_trainer_fit": True,
            "single_batch_trainer_fit_pass": True,
            "ready_for_multi_epoch_schedule_refresh_design": True,
            "ready_for_training": False,
            "EXPANDED_MIXED_PROFILE_TRAINER_FIT_SMOKE_ABSENT": False,
            "MULTI_EPOCH_MIXED_BATCH_SCHEDULE_REFRESH_NOT_YET_VALIDATED": True,
            "HISTORICAL_PAYLOAD_BUILDER_PHYSICAL_MODE_PORTABILITY": (
                "OPEN_NONBLOCKING"
            ),
            "remaining_blockers": (
                "PRE_GEOMETRY_SUPERVISION_AUTHORITY_NOT_ESTABLISHED",
                "MULTI_EPOCH_MIXED_BATCH_SCHEDULE_REFRESH_NOT_YET_VALIDATED",
            ),
            "recommended_next_step_exactly": (
                "review_and_publish_covapie_expanded_cys_sg_mixed_profile_"
                "single_batch_trainer_fit_smoke_v1"
            ),
        }

    if temporary_path is None or temporary_path.exists():
        _fail()
    protected_after = _protected_file_snapshot(protected_paths)
    state_after = _state_integrity_snapshot_v1(state)
    raw_after = _tree_fingerprint(repository / "data/raw")
    git_after = _git_snapshot(repository)
    protected_state_before = state_before["protected_state_fingerprint"]
    protected_state_after = state_after["protected_state_fingerprint"]
    _assert_protected_state_unchanged_v1(
        protected_state_before,
        protected_state_after,
    )
    _assert_external_state_ownership_stable_v1(state_before, state_after)
    if (
        protected_after != protected_before
        or raw_after != raw_before
        or git_after != git_before
    ):
        _fail()
    fit_result.update({
        "legacy_checkpoint_SHA256_before": protected_before["legacy_checkpoint"][2],
        "legacy_checkpoint_SHA256_after": protected_after["legacy_checkpoint"][2],
        "checkpoint_byte_unchanged": True,
        "published_protected_sources_byte_unchanged": True,
        "whole_state_fingerprint_replaced": True,
        "protected_state_entry_count": protected_state_before[0],
        "protected_state_SHA256_before": protected_state_before[1],
        "protected_state_SHA256_after": protected_state_after[1],
        "protected_state_unchanged": True,
        "external_volatile_state_paths": tuple(
            observation["relative_path"]
            for observation in state_before[
                "external_volatile_state_observation"
            ]
        ),
        "external_volatile_state_before": (
            state_before["external_volatile_state_observation"]
        ),
        "external_volatile_state_after": (
            state_after["external_volatile_state_observation"]
        ),
        "external_volatile_state_changed_during_smoke": (
            state_before["external_volatile_state_observation"]
            != state_after["external_volatile_state_observation"]
        ),
        "external_volatile_state_exclusion_exact": True,
        "basename_or_glob_ignore_used": False,
        "whole_gpu_directory_ignored": False,
        "external_gpu_writer_detected": (
            state_before["external_gpu_writer_detected"]
        ),
        "external_active_run_id": state_before["external_active_run_id"],
        "external_ownership_rule_source": _EXTERNAL_OWNERSHIP_RULE_SOURCE_V1,
        "external_run_id_grammar": _EXTERNAL_RUN_ID_GRAMMAR_V1,
        "zero_external_run_supported": True,
        "future_run_id_supported_without_code_change": True,
        "multiple_retained_runs_supported": True,
        "state_modified_semantics": _STATE_MODIFIED_SEMANTICS_V1,
        "raw_tree_entry_count": raw_before[0],
        "raw_tree_SHA256_before": raw_before[1],
        "raw_tree_SHA256_after": raw_after[1],
        "raw_diff_zero": True,
        "persistent_generated_file_count": 0,
        "temporary_trainer_root_removed": True,
        "repository_branch": git_after["branch"],
        "repository_lifecycle": git_after["lifecycle"],
        "baseline_HEAD": git_after["baseline_HEAD"],
        "repository_HEAD": git_after["HEAD"],
        "repository_origin_main": git_after["origin_main"],
        "repository_ahead": git_after["ahead"],
        "repository_behind": git_after["behind"],
        "repository_staged": git_after["staged"],
        "repository_status": git_after["status"],
        "candidate_publication_commit": git_after["publication_commit"],
        "commit_created": False,
        "push_performed": False,
        "ready_for_gpt_review": True,
    })
    return fit_result


def run_covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str = "cpu",
) -> dict[str, object]:
    """Run exactly one real mixed train batch and optimizer step on CPU."""

    try:
        return _run_impl(
            repository_root=repository_root,
            state_root=state_root,
            checkpoint_path=checkpoint_path,
            device=device,
        )
    except Exception as error:
        _public_error(error)

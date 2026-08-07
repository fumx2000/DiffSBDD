#!/usr/bin/env python3
"""Check the Current11 runtime batch observation extractor V1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence


sys.dont_write_bytecode = True

from covalent_ext.covapie_current11_runtime_batch_observation_extractor_v1 import (  # noqa: E402
    extract_covapie_current11_runtime_batch_observation_v1,
)


_ERROR = "COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR"
_STATUS = "PASS_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_ONLY"
_BASE_COMMIT = "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
_DATASET_BLOB = "5cd1531e9beeca2f53c17b705949676bf457a967"
_CARRIER_RELATIVE = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
)
_ROUTING_RELATIVE = Path(
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_BINDING = "current11_runtime_sample_and_role_order_carrier_binding_report.json"
_CARRIER_AGGREGATE = "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
_NPZ_SHA256 = "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
_ROUTING_SNAPSHOT = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_ROUTING_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
_FIELDS = (
    "schema_version",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "batch_sample_keys",
    "ligand_lengths",
    "pocket_lengths",
    "ligand_membership",
    "pocket_membership",
    "joint_layout_descriptor",
    "virtual_node_policy",
    "receptors",
    "consistency_buffer_lengths",
    "debug_coordinates",
    "debug_rank_metadata",
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ValueError(_ERROR)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if completed.returncode != 0 or completed.stderr:
        raise ValueError(_ERROR)
    return completed.stdout


def _validate_repository_lineage(repo: Path) -> None:
    if _run_git(repo, ("branch", "--show-current")).strip() != "main":
        raise ValueError(_ERROR)
    _run_git(repo, ("cat-file", "-e", f"{_BASE_COMMIT}^{{commit}}"))
    _run_git(repo, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))


def _root(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError(_ERROR)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(_ERROR) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise ValueError(_ERROR)
    return path


def _tree_snapshot(path: Path) -> str:
    digest = hashlib.sha256(b"COVAPIE_RUNTIME_EXTRACTOR_CHECKER_SNAPSHOT_V1\0")
    pending = [path]
    while pending:
        current = pending.pop()
        metadata = current.lstat()
        relative = str(current.relative_to(path.parent)).encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(metadata.st_mode.to_bytes(8, "big"))
        digest.update(metadata.st_size.to_bytes(8, "big"))
        digest.update(metadata.st_mtime_ns.to_bytes(8, "big"))
        digest.update(metadata.st_ino.to_bytes(8, "big"))
        if current.is_symlink():
            target = os.readlink(current).encode("utf-8")
            digest.update(target)
            pending.append(current.parent / os.readlink(current))
        elif current.is_dir():
            pending.extend(sorted(current.iterdir(), reverse=True))
        elif current.is_file():
            digest.update(current.read_bytes())
        else:
            raise ValueError(_ERROR)
    return digest.hexdigest()


def _repo_snapshot(repo: Path) -> tuple[str, ...]:
    return (
        _run_git(repo, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo, ("diff", "--name-status")),
        _run_git(repo, ("diff", "--cached", "--name-status")),
        _run_git(repo, ("rev-parse", "HEAD")),
        _run_git(repo, ("rev-parse", "origin/main")),
    )


def _validate_dataset(repo: Path) -> None:
    path = repo / "dataset.py"
    metadata = path.lstat()
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _run_git(repo, ("rev-parse", "HEAD:dataset.py")).strip()
        != _DATASET_BLOB
        or _run_git(repo, ("hash-object", "dataset.py")).strip()
        != _DATASET_BLOB
    ):
        raise ValueError(_ERROR)


def _validate_formal(state: Path) -> tuple[Path, tuple[str, str]]:
    carrier = state / _CARRIER_RELATIVE
    routing = state / _ROUTING_RELATIVE
    if (
        not carrier.is_symlink()
        or _CARRIER_AGGREGATE not in os.readlink(carrier)
        or not routing.is_symlink()
        or _ROUTING_AGGREGATE not in os.readlink(routing)
    ):
        raise ValueError(_ERROR)
    npz = carrier / _NPZ
    if _sha(npz) != _NPZ_SHA256:
        raise ValueError(_ERROR)
    try:
        binding = json.loads((carrier / _BINDING).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if (
        type(binding) is not dict
        or binding.get("runtime_npz_sha256") != _NPZ_SHA256
        or binding.get("formal_routing_sidecar_snapshot_sha256")
        != _ROUTING_SNAPSHOT
        or binding.get("formal_routing_sidecar_aggregate_sha256")
        != _ROUTING_AGGREGATE
        or binding.get("virtual_nodes_present") is not False
    ):
        raise ValueError(_ERROR)
    return npz, (_tree_snapshot(carrier), _tree_snapshot(routing))


def _load_dataset(repo: Path):
    specification = importlib.util.spec_from_file_location(
        "covapie_runtime_extractor_checker_dataset", repo / "dataset.py"
    )
    if specification is None or specification.loader is None:
        raise ValueError(_ERROR)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    dataset = getattr(module, "ProcessedLigandPocketDataset", None)
    if not isinstance(dataset, type):
        raise ValueError(_ERROR)
    return dataset


def _expanded(lengths: list[int]) -> list[int]:
    return [
        ordinal
        for ordinal, length in enumerate(lengths)
        for _ in range(length)
    ]


def _assert_observation(
    observation: object, *, names: list[str], ligand: list[int], pocket: list[int],
) -> None:
    if type(observation) is not dict or tuple(observation) != _FIELDS:
        raise ValueError(_ERROR)
    if (
        observation["batch_sample_keys"] != names
        or observation["ligand_lengths"] != ligand
        or observation["pocket_lengths"] != pocket
        or observation["ligand_membership"] != _expanded(ligand)
        or observation["pocket_membership"] != _expanded(pocket)
        or observation["joint_layout_descriptor"] is not None
        or observation["virtual_node_policy"] != "no_virtual_nodes_v1"
        or any(
            type(value) is not int
            for value in observation["ligand_membership"]
            + observation["pocket_membership"]
        )
        or observation["consistency_buffer_lengths"]
        != {
            "ligand_coords": sum(ligand),
            "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket),
            "pocket_one_hot": sum(pocket),
        }
    ):
        raise ValueError(_ERROR)
    encoded = json.dumps(
        observation,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    if not encoded or "torch" in encoded or "numpy" in encoded:
        raise ValueError(_ERROR)


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    repo = _root(namespace.repo_root)
    state = _root(namespace.state_root)
    _validate_repository_lineage(repo)
    _validate_dataset(repo)
    repo_before = _repo_snapshot(repo)
    npz, formal_before = _validate_formal(state)
    dataset_type = _load_dataset(repo)
    dataset = dataset_type(npz, center=False)
    cases = (
        (
            list(range(11)),
            [f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)],
            [13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21],
            [66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228],
        ),
        (
            [10, 4, 0],
            [
                "CYS_SG_SAMPLE_INDEX_000011",
                "CYS_SG_SAMPLE_INDEX_000005",
                "CYS_SG_SAMPLE_INDEX_000001",
            ],
            [21, 28, 13],
            [228, 188, 66],
        ),
        (
            [10],
            ["CYS_SG_SAMPLE_INDEX_000011"],
            [21],
            [228],
        ),
    )
    observations: list[dict[str, object]] = []
    batches: list[dict[str, object]] = []
    for order, names, ligand, pocket in cases:
        batch = dataset_type.collate_fn([dataset[index] for index in order])
        observation = extract_covapie_current11_runtime_batch_observation_v1(
            batch=batch
        )
        _assert_observation(
            observation, names=names, ligand=ligand, pocket=pocket,
        )
        batches.append(batch)
        observations.append(observation)
    malformed = dict(batches[1])
    malformed["lig_mask"] = batches[1]["lig_mask"].clone()
    malformed["lig_mask"][0] = 1.0
    try:
        extract_covapie_current11_runtime_batch_observation_v1(batch=malformed)
    except ValueError as error:
        if (
            str(error) != _ERROR
            or error.args != (_ERROR,)
            or getattr(error, "reason", None) != "invalid_membership"
        ):
            raise ValueError(_ERROR) from error
    else:
        raise ValueError(_ERROR)
    _npz_after, formal_after = _validate_formal(state)
    if (
        formal_after != formal_before
        or _repo_snapshot(repo) != repo_before
        or _npz_after != npz
    ):
        raise ValueError(_ERROR)
    summary = {
        "actual_case_count": len(observations),
        "canonical_batch_size": 11,
        "exact14_field_count": len(_FIELDS),
        "formal_state_unchanged": True,
        "joint_layout_descriptor": None,
        "malformed_membership_reason": "invalid_membership",
        "repository_unchanged": True,
        "status": _STATUS,
        "subset_batch_size": 3,
        "singleton_batch_size": 1,
    }
    sys.stdout.write(
        json.dumps(
            summary,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
    return 0


def main() -> int:
    try:
        return _main(sys.argv[1:])
    except BaseException:
        sys.stderr.write(_ERROR + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

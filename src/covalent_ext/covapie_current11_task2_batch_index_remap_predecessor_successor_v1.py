"""Reconstruct the Current11 Task2 remap predecessor successor V1 in memory."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_contract_gate_v1 as _remap_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    as _b2,
)
from covalent_ext import (
    covapie_current11_tensor_projection_instance_builder_v1 as _instance_owner,
)
from covalent_ext import (
    covapie_current11_tensor_projection_payload_builder_v1 as _payload_owner,
)


__all__ = (
    "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
)

ERROR_TOKEN = (
    "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_PREDECESSOR_SUCCESSOR_V1_ERROR"
)
BASE_COMMIT = "3c9c13f1d3a17ee32d7ac9f6583a91dd8e780c8c"
BRANCH = "main"

MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_index_remap_predecessor_successor_v1.py"
)
SCRIPT_PATH = (
    "scripts/"
    "check_covapie_current11_task2_batch_index_remap_predecessor_successor_v1.py"
)
TEST_PATH = (
    "tests/"
    "test_covapie_current11_task2_batch_index_remap_predecessor_successor_v1.py"
)
GUIDE_PATH = (
    "docs/"
    "covapie_current11_task2_batch_index_remap_predecessor_successor_v1_guide.md"
)
REPOSITORY_EXACT4 = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)

HISTORICAL_REPORT_NAME = (
    "current11_task2_batch_index_remap_contract_gate_report.json"
)
SUCCESSOR_REPORT_NAME = (
    "current11_task2_batch_index_remap_predecessor_successor_report.json"
)
STABLE_ARTIFACT_NAMES = (
    "current11_task2_batch_index_remap_contract_manifest.json",
    "current11_task2_batch_index_remap_input_schema.json",
    "current11_task2_batch_index_remap_output_schema.json",
    "current11_task2_batch_index_remap_status_vocabulary.csv",
    "current11_task2_batch_index_remap_reference_vectors.json",
)
ARTIFACT_NAMES = (*STABLE_ARTIFACT_NAMES, SUCCESSOR_REPORT_NAME)
REPORT_SCHEMA = (
    "covapie_current11_task2_batch_index_remap_predecessor_successor_report_v1"
)
SUCCESSOR_STATUS = "PASS_REMAP_PREDECESSOR_SUCCESSOR_ONLY"

B2_STABLE_DIGEST = (
    "d39d40b634a3cdd38c43c3636dda57ffb5540ae3a9c9a4b30dfaca70e56b4cb1"
)
PAYLOAD_STABLE7_DIGEST = (
    "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
)
PROJECTION_INSTANCE_DIGEST = (
    "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
)
REMAP_STABLE5_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)

B2_MODULE_SPEC = {
    "path": (
        "src/covalent_ext/"
        "covapie_current11_task2_batch_index_remap_state_mount_device_"
        "transition_contract_gate_v1.py"
    ),
    "bytes": 54756,
    "LF": 1464,
    "sha256": "cca947353675255518e3c6c14d95ed0f864d37495d163d94a7e128853cfd1ade",
    "git_blob": "f8b17a86969e41eb8a4a1bde9c65368e3cb2bd05",
    "commit": BASE_COMMIT,
    "parent": "83beddbcd468caeb38a6b8a86c15f31dfd430d79",
    "subject": (
        "add CovaPIE Current11 Task2 remap state mount-device transition "
        "contract v1"
    ),
}

HELPER_OWNER_SPECS = {
    "payload": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_tensor_projection_payload_builder_v1.py"
        ),
        "bytes": 74187,
        "LF": 1876,
        "sha256": "c6229dce93afb82766ef1b6aacf5c547e32145f334d51ebbd6ac1d7ea5a4e197",
        "git_blob": "8ff02292ec86333ae73d109c327492673e06a9e6",
        "commit": "bc927ef679a6605339d8879559f69fc5ab3002a7",
        "parent": "df9aa9d0b2a91df577b4182e0afdcf4cdfc3bbce",
        "subject": "add CovaPIE Current11 tensor projection payload builder v1",
    },
    "instance": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_tensor_projection_instance_builder_v1.py"
        ),
        "bytes": 40923,
        "LF": 1032,
        "sha256": "39132d2f020ffd3a399c4203d10e534114bd370b8c3a288a9fbde101801022b8",
        "git_blob": "72f9f61563fe83d50f95cf1fdebca622f7c4b0fa",
        "commit": "124543d39ab8f2bc27e748ad2e2c57387730ba47",
        "parent": "bc927ef679a6605339d8879559f69fc5ab3002a7",
        "subject": "add CovaPIE Current11 tensor projection instance builder v1",
    },
    "remap": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
        ),
        "bytes": 70077,
        "LF": 926,
        "sha256": "e9f7d83a17d08eda338ce4d64ab60241887e488c6139ee70af7f210b82bc6eec",
        "git_blob": "6d5f495bac770ef4a87f641ae340fd39947122f4",
        "commit": "6502321ca56ce8895adb3ee20587c383dfbda767",
        "parent": "124543d39ab8f2bc27e748ad2e2c57387730ba47",
        "subject": "add CovaPIE Current11 Task 2 batch index remap contract gate v1",
    },
}

PAYLOAD_STABLE7_IDENTITIES = {
    "current11_tensor_projection_payload_bundle_manifest.json": (
        17038,
        341,
        "d4a1fac58d869a97a73b3f645344aeabf300df604b7ddadfcc55bcb23380df3c",
    ),
    "current11_tensor_projection_payload_sample_identity.json": (
        6645,
        554,
        "bbe2426593ca5d8df59604ec5ef91fdefb0d6e34abba4eea57b1c7abd65748e8",
    ),
    "current11_tensor_projection_payload_explicit_covalent_event.json": (
        6744,
        229,
        "ca55e53f43c2b7743da9b2445b649d66a6e4bfbbd4f1ea5f52ccd2000b939688",
    ),
    "current11_tensor_projection_payload_ligand_residue_atom_pair.json": (
        6381,
        302,
        "fc73c3ed9113ad5183da0bfbc211113e524430ee5546d1c1acbabe6a1a4bf692",
    ),
    "current11_tensor_projection_payload_warhead_boundary.json": (
        12830,
        1007,
        "77a489114b9b74e7f50bdcc09f33da2a005bc7472f78ccd64bbd4adafa7942c5",
    ),
    "current11_tensor_projection_payload_observed_complex_geometry.json": (
        2444,
        98,
        "d59d1ceeed3b8626d4bd91c2a058d81884e23635cdcf0a4ea980da7155a7fb4e",
    ),
    "current11_tensor_projection_payload_provenance.json": (
        119508,
        2798,
        "4bd1d06af9c763eeed75cad0b93b4d0699d9da93014c940658a4f065dc16abe9",
    ),
}
PAYLOAD_HISTORICAL_REPORT_NAME = (
    "current11_tensor_projection_payload_builder_report.json"
)
PROJECTION_HISTORICAL_REPORT_NAME = (
    "current11_tensor_projection_instance_builder_report.json"
)
PROJECTION_INSTANCE_IDENTITY = (
    251433,
    10468,
    "ac191d0fa8b6855fd01247c4c93cce2901c91f5862de923f66855315655cf23b",
)
REMAP_STABLE5_IDENTITIES = {
    STABLE_ARTIFACT_NAMES[0]: (
        50797,
        1254,
        "f887cd6069101c42209a243770714194f76507484e4c264fe68376c610838bfa",
    ),
    STABLE_ARTIFACT_NAMES[1]: (
        13673,
        449,
        "d2a8501218ff4a865c3d583f0ffee76bbc3cfc04e5d8acf08028c9daad396bd5",
    ),
    STABLE_ARTIFACT_NAMES[2]: (
        9395,
        322,
        "772f6e92e43dbb665f66061c3625795c25426f0d75cb79de0693d613b502fbd8",
    ),
    STABLE_ARTIFACT_NAMES[3]: (
        2214,
        19,
        "41ac8e635d9dbb4d8c6b5235239ac5bb8a6e088daaa798000a0fa3e2a876a46a",
    ),
    STABLE_ARTIFACT_NAMES[4]: (
        78673,
        2934,
        "8fb4c78ffc21aa2425a19a72c3159999e01a9f47b6e17ec451011e9a3c096556",
    ),
}

_PAYLOAD_SIGNATURES = {
    "_read_formal": "(canonical: 'Path') -> 'dict[str, bytes]'",
    "_validate_routing": "(formal: 'Mapping[str, bytes]') -> 'dict[str, object]'",
    "_resolve_sources": (
        "(repo_root: 'Path', state_root: 'Path', routing: "
        "'Mapping[str, object]') -> 'dict[str, dict[str, object]]'"
    ),
    "_parse_primary_sources": (
        "(repo_root: 'Path', sources: 'Mapping[str, Mapping[str, object]]') "
        "-> 'dict[str, object]'"
    ),
    "_parse_boundaries": "(source: 'Mapping[str, object]') -> 'dict[str, object]'",
    "_stable_build": (
        "(sources: 'Mapping[str, Mapping[str, object]]', routing: "
        "'Mapping[str, object]', parsed: 'Mapping[str, object]', boundaries: "
        "'Mapping[str, object]') -> 'dict[str, bytes]'"
    ),
    "_stable_digest": "(artifacts: 'Mapping[str, bytes]') -> 'str'",
    "_strict_json": "(payload: 'bytes') -> 'dict[str, object]'",
    "_canonical_json": "(value: 'object') -> 'bytes'",
    "_report": (
        "(stable: 'Mapping[str, bytes]', digest: 'str', formal_snapshot: "
        "'Mapping[str, object]') -> 'dict[str, object]'"
    ),
}
_INSTANCE_SIGNATURES = {
    "_routing": (
        "(formal: 'Mapping[str, bytes]', contract_manifest: "
        "'Mapping[str, object] | None' = None) -> 'dict[str, object]'"
    ),
    "_assemble": (
        "(routing: 'Mapping[str, object]', decoded: 'Mapping[str, object]') "
        "-> 'dict[str, object]'"
    ),
    "_stable_digest": "(payload: 'bytes') -> 'str'",
    "_canonical_json": "(value: 'object') -> 'bytes'",
    "_strict_json": "(payload: 'bytes') -> 'dict[str, object]'",
}
_REMAP_SIGNATURES = {
    "_runtime_inventory": "(repo: 'Path') -> 'list[dict[str, object]]'",
    "_source_contract": (
        "(instance: 'Mapping[str, object]') -> 'dict[str, object]'"
    ),
    "_projection_records": (
        "(repo: 'Path', instance: 'Mapping[str, object]') -> "
        "'tuple[list[dict[str, object]], list[dict[str, object]]]'"
    ),
    "_reference_input": (
        "(order: 'Sequence[int]', tables: 'Sequence[Mapping[str, object]]', "
        "*, joint: 'str | None' = 'ligand_segment_then_pocket_segment_v1') "
        "-> 'dict[str, object]'"
    ),
    "_evaluate_reference_case": (
        "(case: 'Mapping[str, object]', *, authoritative_tables: "
        "'Sequence[Mapping[str, object]]') -> 'dict[str, object]'"
    ),
    "_batch_contract": "(case: 'Mapping[str, object]') -> 'dict[str, object]'",
    "_synthetic_case": "() -> 'dict[str, object]'",
    "_synthetic_authority": "() -> 'list[dict[str, object]]'",
    "_input_schema_artifact": "() -> 'dict[str, object]'",
    "_output_schema_artifact": "() -> 'dict[str, object]'",
    "_status_csv": "() -> 'bytes'",
    "_manifest": (
        "(runtime: 'list[dict[str, object]]', source: 'dict[str, object]', "
        "projection_records: 'list[dict[str, object]]') -> 'dict[str, object]'"
    ),
    "_stable_digest": "(artifacts: 'Mapping[str, bytes]') -> 'str'",
    "_json": "(value: 'object') -> 'bytes'",
}
FROZEN_HELPER_SIGNATURE_COUNT = (
    len(_PAYLOAD_SIGNATURES) + len(_INSTANCE_SIGNATURES) + len(_REMAP_SIGNATURES)
)

_PATH_TYPE = type(Path())
_B2_STABLE_NAMES = tuple(_b2.STABLE_ARTIFACT_NAMES)
_B2_ARTIFACT_NAMES = tuple(_b2.ARTIFACT_NAMES)
_B2_DOMAIN = bytes(_b2.CONTRACT_DIGEST_DOMAIN)
_PAYLOAD_DOMAIN = b"COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUNDLE_V1\0"
_REMAP_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0"


class _HistoricalHelperContractError(Exception):
    pass


class _ReconstructionInvariantError(Exception):
    pass


def _helper_fail() -> NoReturn:
    raise _HistoricalHelperContractError()


def _reconstruction_fail() -> NoReturn:
    raise _ReconstructionInvariantError()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        payload = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _ReconstructionInvariantError() from error
    _validate_payload_bytes(payload)
    return payload


def _strict_json_value(payload: bytes) -> object:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=lambda unused: _reconstruction_fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _ReconstructionInvariantError() from error
    if _canonical_json(value) != payload:
        _reconstruction_fail()
    return value


def _strict_json(payload: bytes) -> dict[str, object]:
    value = _strict_json_value(payload)
    if type(value) is not dict:
        _reconstruction_fail()
    return value


def _validate_payload_bytes(payload: object) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _reconstruction_fail()


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _reconstruction_fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _ReconstructionInvariantError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _reconstruction_fail()
    return path


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise _ReconstructionInvariantError() from error
    if completed.returncode != 0 or completed.stderr:
        _reconstruction_fail()
    return completed.stdout


def _validate_repository_lineage(repo_root: Path) -> None:
    if _run_git(repo_root, ("branch", "--show-current")).strip() != BRANCH:
        _reconstruction_fail()
    _run_git(repo_root, ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"))


def _safe_candidate_files(repo_root: Path) -> None:
    for relative in REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise _ReconstructionInvariantError() from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _reconstruction_fail()
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise _ReconstructionInvariantError() from error


def _repository_lifecycle(repo_root: Path) -> str:
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *REPOSITORY_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(REPOSITORY_EXACT4):
        if index:
            _reconstruction_fail()
        _safe_candidate_files(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(REPOSITORY_EXACT4):
        _reconstruction_fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise _ReconstructionInvariantError() from error
        if (
            relative not in REPOSITORY_EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _reconstruction_fail()
        seen.add(relative)
    if seen != set(REPOSITORY_EXACT4):
        _reconstruction_fail()
    _safe_candidate_files(repo_root)
    return "clean-tracked-successor"


def _direct_path_item(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _repository_snapshot(repo_root: Path) -> tuple[object, ...]:
    paths = (
        *REPOSITORY_EXACT4,
        str(B2_MODULE_SPEC["path"]),
        *(str(spec["path"]) for spec in HELPER_OWNER_SPECS.values()),
    )
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _direct_path_item(repo_root / relative)) for relative in paths),
    )


def _formal_snapshot(state_root: Path) -> tuple[object, ...]:
    canonical = state_root / _payload_owner._FORMAL_RELATIVE
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        parent_inventory = tuple(sorted(os.listdir(parent)))
        object_inventory = tuple(sorted(os.listdir(object_path)))
        return (
            _direct_path_item(parent),
            parent_inventory,
            _direct_path_item(canonical),
            link,
            _direct_path_item(object_path),
            object_inventory,
            tuple(
                (name, _direct_path_item(object_path / name))
                for name in object_inventory
            ),
        )
    except OSError as error:
        raise _ReconstructionInvariantError() from error


def _verify_owner_identity(
    repo_root: Path,
    owner_name: str,
    spec: Mapping[str, object],
) -> dict[str, object]:
    relative = str(spec["path"])
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise _HistoricalHelperContractError() from error
    tree = _run_git(repo_root, ("ls-tree", "HEAD", "--", relative)).strip()
    try:
        tree_metadata, listed = tree.split("\t", 1)
        tree_mode, tree_kind, tree_blob = tree_metadata.split()
    except ValueError as error:
        raise _HistoricalHelperContractError() from error
    commit = str(spec["commit"])
    try:
        if (
            listed != relative
            or tree_mode != "100644"
            or tree_kind != "blob"
            or tree_blob != spec["git_blob"]
            or stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) != spec["bytes"]
            or payload.count(b"\n") != spec["LF"]
            or _sha256(payload) != spec["sha256"]
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != spec["git_blob"]
            or _run_git(repo_root, ("rev-parse", f"{commit}:{relative}")).strip()
            != spec["git_blob"]
        ):
            _helper_fail()
        _run_git(repo_root, ("cat-file", "-e", f"{commit}^{{commit}}"))
        _run_git(repo_root, ("merge-base", "--is-ancestor", commit, "HEAD"))
        if (
            _run_git(repo_root, ("show", "-s", "--format=%P", commit)).strip()
            != spec["parent"]
            or _run_git(
                repo_root, ("show", "-s", "--format=%s", commit)
            ).strip()
            != spec["subject"]
            or _run_git(
                repo_root,
                (
                    "diff-tree",
                    "--no-commit-id",
                    "--name-status",
                    "-r",
                    commit,
                    "--",
                    relative,
                ),
            ).strip()
            != f"A\t{relative}"
        ):
            _helper_fail()
    except _ReconstructionInvariantError as error:
        raise _HistoricalHelperContractError() from error
    return {
        "owner_name": owner_name,
        "relative_path": relative,
        "bytes": spec["bytes"],
        "LF": spec["LF"],
        "sha256": spec["sha256"],
        "git_blob": spec["git_blob"],
        "git_mode": "100644",
        "introduction_commit": commit,
        "head_and_worktree_exact": True,
    }


def _validate_b2_owner(repo_root: Path) -> dict[str, object]:
    row = _verify_owner_identity(repo_root, "B2_transition_authority", B2_MODULE_SPEC)
    api_name = (
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_"
        "transition_contract_gate_v1"
    )
    function = getattr(_b2, api_name, None)
    if (
        _b2.__all__ != (api_name,)
        or not callable(function)
        or str(inspect.signature(function))
        != "(*, repo_root: 'Path', state_root: 'Path') -> 'dict[str, bytes]'"
    ):
        _helper_fail()
    return row


def _validate_helper_owners(repo_root: Path) -> list[dict[str, object]]:
    return [
        _verify_owner_identity(repo_root, name, spec)
        for name, spec in HELPER_OWNER_SPECS.items()
    ]


def _validate_helper_signatures() -> list[dict[str, object]]:
    groups = (
        ("payload", _payload_owner, _PAYLOAD_SIGNATURES),
        ("instance", _instance_owner, _INSTANCE_SIGNATURES),
        ("remap", _remap_owner, _REMAP_SIGNATURES),
    )
    rows: list[dict[str, object]] = []
    for owner_name, module, expected in groups:
        for helper_name, expected_signature in expected.items():
            function = getattr(module, helper_name, None)
            if not callable(function):
                _helper_fail()
            try:
                observed = str(inspect.signature(function))
            except (TypeError, ValueError) as error:
                raise _HistoricalHelperContractError() from error
            if observed != expected_signature:
                _helper_fail()
            rows.append(
                {
                    "owner_name": owner_name,
                    "helper_name": helper_name,
                    "signature": observed,
                }
            )
    if len(rows) != FROZEN_HELPER_SIGNATURE_COUNT or len(rows) != 29:
        _helper_fail()
    return rows


def _manual_framed_digest(
    domain: bytes,
    names: Sequence[str],
    artifacts: Mapping[str, bytes],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    for name in names:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        if type(payload) is not bytes:
            _reconstruction_fail()
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_identity_table(
    artifacts: Mapping[str, bytes],
    identities: Mapping[str, tuple[int, int, str]],
) -> None:
    if type(artifacts) is not dict or tuple(artifacts) != tuple(identities):
        _reconstruction_fail()
    for name, (size, lines, digest) in identities.items():
        payload = artifacts.get(name)
        _validate_payload_bytes(payload)
        if (
            len(payload) != size
            or payload.count(b"\n") != lines
            or _sha256(payload) != digest
        ):
            _reconstruction_fail()


def _validate_b2_artifacts(artifacts: object) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != _B2_ARTIFACT_NAMES:
        _reconstruction_fail()
    parsed: dict[str, object] = {}
    for name, payload in artifacts.items():
        _validate_payload_bytes(payload)
        parsed[name] = _strict_json_value(payload)
    stable = {name: artifacts[name] for name in _B2_STABLE_NAMES}
    digest = _manual_framed_digest(_B2_DOMAIN, _B2_STABLE_NAMES, stable)
    transitions = parsed[_B2_ARTIFACT_NAMES[1]]
    report = parsed[_B2_ARTIFACT_NAMES[4]]
    if (
        digest != B2_STABLE_DIGEST
        or type(transitions) is not list
        or len(transitions) != 3
        or [row.get("object_id") for row in transitions]
        != ["unit_000001_dossier", "routing_canonical", "routing_object"]
        or [row.get("historical_identity", {}).get("st_dev") for row in transitions]
        != [49, 49, 49]
        or [
            row.get("authorized_current_identity", {}).get("st_dev")
            for row in transitions
        ]
        != [50, 50, 50]
        or any(row.get("transition_authorized") is not True for row in transitions)
        or type(report) is not dict
        or report.get("gate_status")
        != "PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY"
        or report.get("contract_digest") != B2_STABLE_DIGEST
        or report.get("historical_public_gates_called") is not False
        or report.get("heavy_remap_contract_chain_called") is not False
        or report.get("remap_adapter_private_contract_called") is not False
    ):
        _reconstruction_fail()
    readiness = report.get("readiness")
    if (
        type(readiness) is not dict
        or readiness.get("ready_for_remap_predecessor_successor_integration")
        is not True
        or readiness.get(
            "ready_for_public_remap_adapter_hot_loop_contract_implementation"
        )
        is not False
        or readiness.get("compiler_context_rebuild_device_identity_risk")
        is not True
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("ready_for_model_integration") is not False
        or readiness.get("ready_for_loss_integration") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        _reconstruction_fail()
    return {
        "stable_digest": digest,
        "transitions": transitions,
        "readiness": readiness,
    }


def _identity_rows(
    identities: Mapping[str, tuple[int, int, str]],
) -> list[dict[str, object]]:
    return [
        {
            "artifact_index": index,
            "artifact_name": name,
            "bytes": identity[0],
            "LF": identity[1],
            "sha256": identity[2],
        }
        for index, (name, identity) in enumerate(identities.items())
    ]


def _reconstruct_stable(
    repo_root: Path,
    state_root: Path,
) -> tuple[dict[str, bytes], dict[str, object]]:
    canonical = state_root / _payload_owner._FORMAL_RELATIVE
    formal = _payload_owner._read_formal(canonical)
    routing = _payload_owner._validate_routing(formal)
    sources = _payload_owner._resolve_sources(repo_root, state_root, routing)
    parsed = _payload_owner._parse_primary_sources(repo_root, sources)
    boundaries = _payload_owner._parse_boundaries(
        sources["unified_boundary_authority"]
    )
    boundary_records = boundaries.get("records")
    ligand_atom_names = parsed.get("ligand_atom_names")
    if (
        type(boundary_records) is not list
        or type(ligand_atom_names) is not list
        or "F1" not in boundary_records[4]["warhead"]
        or "F1" in ligand_atom_names[4]
    ):
        _reconstruction_fail()
    stable7 = _payload_owner._stable_build(sources, routing, parsed, boundaries)
    _validate_identity_table(stable7, PAYLOAD_STABLE7_IDENTITIES)
    payload_digest = _payload_owner._stable_digest(stable7)
    if (
        payload_digest != PAYLOAD_STABLE7_DIGEST
        or _manual_framed_digest(
            _PAYLOAD_DOMAIN, tuple(PAYLOAD_STABLE7_IDENTITIES), stable7
        )
        != PAYLOAD_STABLE7_DIGEST
        or PAYLOAD_HISTORICAL_REPORT_NAME in stable7
    ):
        _reconstruction_fail()

    decoded = {
        name: _payload_owner._strict_json(stable7[name]) for name in stable7
    }
    if PAYLOAD_HISTORICAL_REPORT_NAME in decoded:
        _reconstruction_fail()
    instance_routing = _instance_owner._routing(formal, None)
    instance_value = _instance_owner._assemble(instance_routing, decoded)
    instance_bytes = _instance_owner._canonical_json(instance_value)
    instance_size, instance_lines, instance_sha = PROJECTION_INSTANCE_IDENTITY
    if (
        len(instance_bytes) != instance_size
        or instance_bytes.count(b"\n") != instance_lines
        or _sha256(instance_bytes) != instance_sha
        or _instance_owner._stable_digest(instance_bytes)
        != PROJECTION_INSTANCE_DIGEST
        or PROJECTION_HISTORICAL_REPORT_NAME in decoded
    ):
        _reconstruction_fail()

    runtime = _remap_owner._runtime_inventory(repo_root)
    source = _remap_owner._source_contract(instance_value)
    projection_records, evaluator_tables = _remap_owner._projection_records(
        repo_root, instance_value
    )
    canonical_input = _remap_owner._reference_input(
        list(range(11)), evaluator_tables
    )
    reverse_input = _remap_owner._reference_input(
        list(reversed(range(11))), evaluator_tables
    )
    mixed_input = _remap_owner._reference_input(
        [10, 4, 0, 7, 2], evaluator_tables
    )
    subset_input = _remap_owner._reference_input([10, 4, 0], evaluator_tables)
    no_joint_input = _remap_owner._reference_input(
        list(range(11)), evaluator_tables, joint=None
    )
    synthetic_input = _remap_owner._synthetic_case()
    synthetic_authority = _remap_owner._synthetic_authority()
    canonical_output = _remap_owner._evaluate_reference_case(
        canonical_input, authoritative_tables=evaluator_tables
    )
    reverse_output = _remap_owner._evaluate_reference_case(
        reverse_input, authoritative_tables=evaluator_tables
    )
    mixed_output = _remap_owner._evaluate_reference_case(
        mixed_input, authoritative_tables=evaluator_tables
    )
    subset_output = _remap_owner._evaluate_reference_case(
        subset_input, authoritative_tables=evaluator_tables
    )
    no_joint_output = _remap_owner._evaluate_reference_case(
        no_joint_input, authoritative_tables=evaluator_tables
    )
    synthetic_output = _remap_owner._evaluate_reference_case(
        synthetic_input, authoritative_tables=synthetic_authority
    )
    outputs = (
        canonical_output,
        reverse_output,
        mixed_output,
        subset_output,
        no_joint_output,
        synthetic_output,
    )
    if (
        any(output.get("remap_status") != "REMAPPED_EXACT" for output in outputs)
        or no_joint_output.get("pair_values_joint_global_indices") is not None
        or no_joint_output.get("provenance", {}).get("joint_index_status")
        != "JOINT_INDEX_SPACE_UNAVAILABLE"
        or synthetic_output.get("sample_pair_offsets") != [0, 1, 3, 3]
    ):
        _reconstruction_fail()
    vectors = {
        "schema_version": _remap_owner._REFERENCE_SCHEMA,
        "source_contract": source,
        "exact22_source_to_local": projection_records,
        "canonical_exact11_batch_reference": {
            "batch_contract": _remap_owner._batch_contract(canonical_input),
            "output": canonical_output,
        },
        "permutation_reference_cases": [
            {
                "case_name": "reversed_exact11",
                "source_sample_indices": list(reversed(range(11))),
                "batch_contract": _remap_owner._batch_contract(reverse_input),
                "output": reverse_output,
            },
            {
                "case_name": "mixed_permutation",
                "source_sample_indices": [10, 4, 0, 7, 2],
                "batch_contract": _remap_owner._batch_contract(mixed_input),
                "output": mixed_output,
            },
        ],
        "subset_reference_cases": [
            {
                "case_name": "subset_10_4_0",
                "source_sample_indices": [10, 4, 0],
                "batch_contract": _remap_owner._batch_contract(subset_input),
                "output": subset_output,
            }
        ],
        "no_joint_layout_reference_case": {
            "joint_layout_descriptor": None,
            "batch_contract": _remap_owner._batch_contract(no_joint_input),
            "output": no_joint_output,
        },
        "synthetic_future_p_gt_1_reference_case": {
            "source_pair_counts_by_sample": [2, 0, 1],
            "source_sample_offsets_int64": [0, 2, 2, 3],
            "batch_source_sample_order": [2, 0, 1],
            "batch_contract": _remap_owner._batch_contract(synthetic_input),
            "output": synthetic_output,
        },
        "reference_case_semantics": {
            "canonical_exact11_batch_reference_only": True,
            "future_batch_values_must_be_recomputed": True,
            "hardcode_as_runtime_output_forbidden": True,
            "reference_contract_evaluator_only": True,
            "public_adapter_implemented": False,
            "model_integration_authorized": False,
            "loss_authorized": False,
        },
    }
    stable_values = (
        _remap_owner._manifest(runtime, source, projection_records),
        _remap_owner._input_schema_artifact(),
        _remap_owner._output_schema_artifact(),
        None,
        vectors,
    )
    stable5: dict[str, bytes] = {}
    for name, value in zip(STABLE_ARTIFACT_NAMES, stable_values, strict=True):
        stable5[name] = (
            _remap_owner._status_csv()
            if name == STABLE_ARTIFACT_NAMES[3]
            else _remap_owner._json(value)
        )
    _validate_identity_table(stable5, REMAP_STABLE5_IDENTITIES)
    remap_digest = _remap_owner._stable_digest(stable5)
    if (
        remap_digest != REMAP_STABLE5_DIGEST
        or _manual_framed_digest(_REMAP_DOMAIN, STABLE_ARTIFACT_NAMES, stable5)
        != REMAP_STABLE5_DIGEST
    ):
        _reconstruction_fail()
    return stable5, {
        "payload_stable7": stable7,
        "payload_digest": payload_digest,
        "instance_bytes": instance_bytes,
        "instance_value": instance_value,
        "instance_digest": PROJECTION_INSTANCE_DIGEST,
        "remap_digest": remap_digest,
        "reference_outputs": outputs,
        "no_joint_output": no_joint_output,
        "synthetic_output": synthetic_output,
    }


def _successor_report(
    *,
    lifecycle: str,
    b2_evidence: Mapping[str, object],
    b2_owner: Mapping[str, object],
    helper_owners: Sequence[Mapping[str, object]],
    signature_rows: Sequence[Mapping[str, object]],
    reconstruction: Mapping[str, object],
) -> dict[str, object]:
    clean_live = lifecycle == "clean-tracked-successor"
    return {
        "schema_version": REPORT_SCHEMA,
        "successor_status": SUCCESSOR_STATUS,
        "artifact_file_count": 6,
        "artifact_names": list(ARTIFACT_NAMES),
        "repository_lifecycle": lifecycle,
        "historical_stable5_digest": REMAP_STABLE5_DIGEST,
        "historical_stable5_identities": _identity_rows(REMAP_STABLE5_IDENTITIES),
        "stable_semantic_artifact_parity": True,
        "historical_stable_manifest_bytes_preserved": True,
        "historical_manifest_report_name_is_current_output": False,
        "historical_manifest_report_name": HISTORICAL_REPORT_NAME,
        "successor_returned_report_name": SUCCESSOR_REPORT_NAME,
        "historical_report_byte_parity_required": False,
        "B2_transition_contract_called": True,
        "B2_transition_contract_passed": True,
        "B2_transition_contract_call_count": 1,
        "B2_stable_digest": b2_evidence["stable_digest"],
        "B2_owner_identity": dict(b2_owner),
        "historical_device": 49,
        "current_device": 50,
        "transition_object_count": 3,
        "transition_object_ids": [
            "unit_000001_dossier",
            "routing_canonical",
            "routing_object",
        ],
        "transition_authorized_count": 3,
        "historical_public_gate_called": False,
        "historical_payload_public_builder_called": False,
        "historical_projection_instance_public_builder_called": False,
        "historical_remap_contract_public_gate_called": False,
        "public_remap_adapter_called": False,
        "production_monkeypatch_used": False,
        "state_or_repository_write_performed": False,
        "payload_stable7_parity": True,
        "payload_stable7_digest": reconstruction["payload_digest"],
        "payload_stable7_identities": _identity_rows(PAYLOAD_STABLE7_IDENTITIES),
        "payload_historical_report_emitted": False,
        "projection_instance_stable_parity": True,
        "projection_instance_bytes": PROJECTION_INSTANCE_IDENTITY[0],
        "projection_instance_LF": PROJECTION_INSTANCE_IDENTITY[1],
        "projection_instance_SHA256": PROJECTION_INSTANCE_IDENTITY[2],
        "projection_instance_digest": reconstruction["instance_digest"],
        "projection_historical_report_emitted": False,
        "remap_stable5_parity": True,
        "remap_stable5_digest": reconstruction["remap_digest"],
        "reference_case_success_count": 6,
        "no_joint_pair_values_joint_global_indices_is_null": True,
        "synthetic_sample_pair_offsets": [0, 1, 3, 3],
        "historical_payload_report_sha_embedded_as_lineage_only": True,
        "historical_projection_instance_report_sha_embedded_as_lineage_only": True,
        "historical_embedded_report_sha_does_not_mean_report_emitted_in_successor": True,
        "owner_identity_validation_passed": True,
        "helper_owner_identities": [dict(row) for row in helper_owners],
        "helper_signature_validation_passed": True,
        "helper_signature_frozen_count": len(signature_rows),
        "fresh_B2_per_build": True,
        "fresh_formal_and_source_reads_per_build": True,
        "cache_used": False,
        "repository_snapshot_unchanged": True,
        "formal_snapshot_unchanged": True,
        "clean_successor_live_validation_pending": not clean_live,
        "ready_for_commit_review": True,
        "ready_for_one_heavy_parity_timing_probe": clean_live,
        "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
        "current_adapter_directly_accepts_successor_exact6": False,
        "current_compiler_context_uses_successor_authority": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "commit_created": False,
        "push_performed": False,
    }


def _validate_successor_artifacts(artifacts: object) -> None:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES:
        _reconstruction_fail()
    stable5 = {name: artifacts[name] for name in STABLE_ARTIFACT_NAMES}
    _validate_identity_table(stable5, REMAP_STABLE5_IDENTITIES)
    if (
        _manual_framed_digest(_REMAP_DOMAIN, STABLE_ARTIFACT_NAMES, stable5)
        != REMAP_STABLE5_DIGEST
        or HISTORICAL_REPORT_NAME in artifacts
    ):
        _reconstruction_fail()
    report_payload = artifacts[SUCCESSOR_REPORT_NAME]
    _validate_payload_bytes(report_payload)
    report = _strict_json(report_payload)
    if (
        report.get("schema_version") != REPORT_SCHEMA
        or report.get("successor_status") != SUCCESSOR_STATUS
        or report.get("artifact_names") != list(ARTIFACT_NAMES)
        or report.get("historical_stable5_digest") != REMAP_STABLE5_DIGEST
        or report.get("stable_semantic_artifact_parity") is not True
        or report.get("production_monkeypatch_used") is not False
        or report.get("ready_for_training") is not False
    ):
        _reconstruction_fail()


def _build_after_b2(
    *,
    repo_root: Path,
    state_root: Path,
    lifecycle: str,
    b2_artifacts: object,
    b2_owner: Mapping[str, object],
    before_repository: tuple[object, ...],
    before_formal: tuple[object, ...],
) -> dict[str, bytes]:
    b2_evidence = _validate_b2_artifacts(b2_artifacts)
    helper_owners = _validate_helper_owners(repo_root)
    signature_rows = _validate_helper_signatures()
    stable5, reconstruction = _reconstruct_stable(repo_root, state_root)
    if (
        _repository_snapshot(repo_root) != before_repository
        or _formal_snapshot(state_root) != before_formal
    ):
        _reconstruction_fail()
    report = _successor_report(
        lifecycle=lifecycle,
        b2_evidence=b2_evidence,
        b2_owner=b2_owner,
        helper_owners=helper_owners,
        signature_rows=signature_rows,
        reconstruction=reconstruction,
    )
    artifacts = dict(stable5)
    artifacts[SUCCESSOR_REPORT_NAME] = _canonical_json(report)
    _validate_successor_artifacts(artifacts)
    if (
        _repository_snapshot(repo_root) != before_repository
        or _formal_snapshot(state_root) != before_formal
    ):
        _reconstruction_fail()
    return artifacts


def _build_fixture_only(
    *,
    repo_root: Path,
    state_root: Path,
    b2_artifacts: object,
) -> dict[str, bytes]:
    """Candidate-checker fixture path; it is not the public production API."""

    repository = _require_root(repo_root)
    state = _require_root(state_root)
    before_repository = _repository_snapshot(repository)
    before_formal = _formal_snapshot(state)
    _validate_repository_lineage(repository)
    lifecycle = _repository_lifecycle(repository)
    b2_owner = _validate_b2_owner(repository)
    return _build_after_b2(
        repo_root=repository,
        state_root=state,
        lifecycle=lifecycle,
        b2_artifacts=b2_artifacts,
        b2_owner=b2_owner,
        before_repository=before_repository,
        before_formal=before_formal,
    )


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    before_repository = _repository_snapshot(repository)
    before_formal = _formal_snapshot(state)
    _validate_repository_lineage(repository)
    lifecycle = _repository_lifecycle(repository)
    if lifecycle != "clean-tracked-successor":
        _reconstruction_fail()
    b2_owner = _validate_b2_owner(repository)
    b2_artifacts = _b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=repository,
        state_root=state,
    )
    return _build_after_b2(
        repo_root=repository,
        state_root=state,
        lifecycle=lifecycle,
        b2_artifacts=b2_artifacts,
        b2_owner=b2_owner,
        before_repository=before_repository,
        before_formal=before_formal,
    )


def build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return historical remap stable5 plus one truthful successor report."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error

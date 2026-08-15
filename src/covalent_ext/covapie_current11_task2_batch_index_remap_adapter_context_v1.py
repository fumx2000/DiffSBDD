"""Opaque successor-backed context and no-I/O Task2 remap fast path V1."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1
    as _hot_loop_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as _adapter_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    as _reconciliation_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_predecessor_successor_v1
    as _successor_owner,
)


__all__ = (
    "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
    "remap_covapie_current11_task2_batch_index_with_context_v1",
)

ERROR_TOKEN = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_CONTEXT_V1_ERROR"
BASE_COMMIT = "68cf69574d3f97c57f2c3873c77bc8250f5cbad0"
BRANCH = "main"
ARCHITECTURE_NAME = (
    "explicit_successor_authority_context_plus_output17_only_no_io_fast_path_v1"
)
CONTEXT_SCHEMA_VERSION = (
    "covapie_current11_task2_batch_index_remap_adapter_context_v1"
)
CONTEXT_CONTRACT_VERSION = (
    "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
)
RUNTIME_TARGET = "current_public_adapter_output17_v1"
RECONCILIATION_DIGEST = (
    "9250ff7948d353222f7a2c5b34fdfceee92ae03b73be802af80a214db004203f"
)
SUCCESSOR_STABLE5_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)
PROJECTION_INSTANCE_DIGEST = (
    "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
)
PAYLOAD_BUNDLE_DIGEST = (
    "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
)
PROJECTION_CONTRACT_DIGEST = (
    "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
)
CONTEXT_FRESHNESS_MODEL = "explicit_rebuild_by_owner"
_SEAL_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_CONTEXT_V1\0"
_PATH_TYPE = type(Path())

MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_task2_batch_index_remap_adapter_context_v1_guide.md"
)
REPOSITORY_EXACT4 = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)

_LOGICAL_FIELD_ORDER = (
    "context_schema_version",
    "context_contract_version",
    "runtime_output17_target",
    "reconciliation_contract_digest",
    "successor_stable5_digest",
    "remap_contract_digest",
    "projection_instance_digest",
    "payload_bundle_digest",
    "projection_contract_digest",
    "join_contract",
    "index_space_order",
    "input_field_order",
    "input_required_fields",
    "input_optional_fields",
    "output17_field_order",
    "source_contract",
    "authority_tables",
    "formal_authority_identity",
    "context_freshness_model",
    "construction_seal",
)

_OWNER_SPECS = {
    "published_hot_loop_contract_gate": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "contract_gate_v1.py"
        ),
        "bytes": 58101,
        "LF": 1482,
        "sha256": (
            "5acc793c40d1a899371fd08a02713cd8f1d6105cce04d177317bf03bbdb3cd29"
        ),
        "git_blob": "8ba056493e5db83c34e342f3424179ecfe729d77",
        "commit": BASE_COMMIT,
        "subject": (
            "add CovaPIE Current11 Task2 remap adapter hot-loop contract v1"
        ),
    },
    "published_output17_reconciliation_gate": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_output17_semantic_"
            "reconciliation_contract_gate_v1.py"
        ),
        "bytes": 67867,
        "LF": 1793,
        "sha256": (
            "15f639ef955a975cbfbeebce9bde452ee65d4acdf67b2feec56871786603e1de"
        ),
        "git_blob": "edac625388b8c58539c3c29a5dd470d6ccec6e6e",
        "commit": "03e9a238d0c910257e4f43a78c69998dc62dd162",
        "subject": (
            "add CovaPIE Current11 Task2 Output17 semantic reconciliation "
            "contract v1"
        ),
    },
    "published_remap_predecessor_successor": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_predecessor_successor_v1.py"
        ),
        "bytes": 43997,
        "LF": 1203,
        "sha256": (
            "c1e4b207a6432b6495d85fb799a196cb2370edd41402000fbfcbfcf3514acb05"
        ),
        "git_blob": "0e0ebdca4db0abbfaec921ea34253dcefbb29410",
        "commit": "cd392246fc424de609db9c5110d805fbe3d9a555",
        "subject": (
            "add CovaPIE Current11 Task2 remap predecessor successor v1"
        ),
    },
    "current_public_runtime_adapter": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_v1.py"
        ),
        "bytes": 56510,
        "LF": 1368,
        "sha256": (
            "d09bd5648a3c47851efd933fa8c0523c4ab7c67f8cce765b08fb8423a4e57dd2"
        ),
        "git_blob": "11573d4e0857cf69dceb22c3b1ec4f319faa6d08",
        "commit": "b3c76bd4321da5aece08711a4d6f2d421cb8b54b",
        "subject": (
            "add CovaPIE Current11 Task 2 batch index remap adapter v1"
        ),
    },
}

_RECONCILIATION_ARTIFACT_NAMES = (
    "current11_task2_batch_index_remap_output17_semantic_reconciliation_manifest.json",
    "current11_task2_batch_index_remap_output17_field_partition.json",
    "current11_task2_batch_index_remap_output17_producer_metadata_contract.json",
    "current11_task2_batch_index_remap_output17_success_failure_parity_contract.json",
    "current11_task2_batch_index_remap_output17_negative_matrix.json",
    "current11_task2_batch_index_remap_output17_semantic_reconciliation_gate_report.json",
)
_RECONCILIATION_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
    b"RECONCILIATION_CONTRACT_GATE_V1\0"
)
_SELECTED_RECONCILIATION_MODEL = (
    "B_plus_E_success_plus_runtime_whole_failure_exact_plus_historical_"
    "failure_self_validation"
)

_STABLE5_NAMES = (
    "current11_task2_batch_index_remap_contract_manifest.json",
    "current11_task2_batch_index_remap_input_schema.json",
    "current11_task2_batch_index_remap_output_schema.json",
    "current11_task2_batch_index_remap_status_vocabulary.csv",
    "current11_task2_batch_index_remap_reference_vectors.json",
)
_SUCCESSOR_REPORT_NAME = (
    "current11_task2_batch_index_remap_predecessor_successor_report.json"
)
_HISTORICAL_REPORT_NAME = (
    "current11_task2_batch_index_remap_contract_gate_report.json"
)
_SUCCESSOR_ARTIFACT_NAMES = (*_STABLE5_NAMES, _SUCCESSOR_REPORT_NAME)
_STABLE5_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0"
_STABLE5_IDENTITIES = {
    _STABLE5_NAMES[0]: (
        50797,
        1254,
        "f887cd6069101c42209a243770714194f76507484e4c264fe68376c610838bfa",
    ),
    _STABLE5_NAMES[1]: (
        13673,
        449,
        "d2a8501218ff4a865c3d583f0ffee76bbc3cfc04e5d8acf08028c9daad396bd5",
    ),
    _STABLE5_NAMES[2]: (
        9395,
        322,
        "772f6e92e43dbb665f66061c3625795c25426f0d75cb79de0693d613b502fbd8",
    ),
    _STABLE5_NAMES[3]: (
        2214,
        19,
        "41ac8e635d9dbb4d8c6b5235239ac5bb8a6e088daaa798000a0fa3e2a876a46a",
    ),
    _STABLE5_NAMES[4]: (
        78673,
        2934,
        "8fb4c78ffc21aa2425a19a72c3159999e01a9f47b6e17ec451011e9a3c096556",
    ),
}


class _ContextInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _ContextInvariantError()


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
        raise _ContextInvariantError() from error
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail()
    return payload


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=lambda unused: _fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _ContextInvariantError() from error
    if type(value) is not dict or _canonical_json(value) != payload:
        _fail()
    return value


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _ContextInvariantError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
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
        raise _ContextInvariantError() from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _validate_repository_lineage(repo_root: Path) -> None:
    if _run_git(repo_root, ("branch", "--show-current")).strip() != BRANCH:
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"))


def _safe_exact4(repo_root: Path) -> None:
    for relative in REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
            payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise _ContextInvariantError() from error
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
            _fail()


def _repository_lifecycle(repo_root: Path) -> str:
    _validate_repository_lineage(repo_root)
    status = _run_git(
        repo_root,
        ("status", "--porcelain=v1", "--untracked-files=all"),
    ).splitlines()
    index = _run_git(
        repo_root,
        ("ls-files", "--stage", "--", *REPOSITORY_EXACT4),
    ).splitlines()
    expected = {f"?? {relative}" for relative in REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(REPOSITORY_EXACT4):
        if index:
            _fail()
        _safe_exact4(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(REPOSITORY_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise _ContextInvariantError() from error
        if (
            relative not in REPOSITORY_EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo_root,
                ("hash-object", "--no-filters", "--", relative),
            ).strip()
            != blob
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _fail()
        seen.add(relative)
    if seen != set(REPOSITORY_EXACT4):
        _fail()
    _safe_exact4(repo_root)
    return "clean-tracked-successor"


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
        tree = _run_git(repo_root, ("ls-tree", "HEAD", "--", relative)).strip()
        tree_metadata, listed = tree.split("\t", 1)
        tree_mode, tree_kind, tree_blob = tree_metadata.split()
    except (OSError, ValueError) as error:
        raise _ContextInvariantError() from error
    commit = str(spec["commit"])
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
            repo_root,
            ("hash-object", "--no-filters", "--", relative),
        ).strip()
        != spec["git_blob"]
        or _run_git(repo_root, ("rev-parse", f"{commit}:{relative}")).strip()
        != spec["git_blob"]
    ):
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{commit}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", commit, "HEAD"))
    if (
        _run_git(repo_root, ("show", "-s", "--format=%s", commit)).strip()
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
        _fail()
    return {
        "owner_name": owner_name,
        "relative_path": relative,
        "bytes": spec["bytes"],
        "LF": spec["LF"],
        "sha256": spec["sha256"],
        "git_blob": spec["git_blob"],
        "git_mode": "100644",
        "worktree_mode": "0644",
        "introduction_or_published_commit": commit,
        "subject": spec["subject"],
        "head_and_worktree_exact": True,
    }


def _verify_owner_identities(repo_root: Path) -> list[dict[str, object]]:
    return [
        _verify_owner_identity(repo_root, name, spec)
        for name, spec in _OWNER_SPECS.items()
    ]


def _signature_rows(
    expected: Mapping[str, str],
    *,
    purpose: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for helper_name, signature in expected.items():
        helper = getattr(_adapter_owner, helper_name, None)
        if not callable(helper):
            _fail()
        try:
            observed = str(inspect.signature(helper))
        except (TypeError, ValueError) as error:
            raise _ContextInvariantError() from error
        if observed != signature:
            _fail()
        rows.append(
            {
                "helper_name": helper_name,
                "signature": observed,
                "purpose": purpose,
            }
        )
    return rows


def _validate_frozen_adapter_contract() -> dict[str, object]:
    pure = _signature_rows(
        _hot_loop_owner.ADAPTER_PURE_HELPER_SIGNATURES,
        purpose="fast_output17_orchestration",
    )
    parser = _signature_rows(
        _hot_loop_owner.SUCCESSOR_PARSE_HELPER_SIGNATURES,
        purpose="successor_stable5_parse",
    )
    formal = {
        "canonical_relative_path": _adapter_owner._FORMAL_RELATIVE,
        "canonical_readlink": _adapter_owner._FORMAL_READLINK,
        "formal_aggregate_sha256": _adapter_owner._FORMAL_AGGREGATE,
        "formal_snapshot_sha256": _adapter_owner._FORMAL_SNAPSHOT_SHA256,
        "formal_exact4_sha256": copy.deepcopy(_adapter_owner._FORMAL_FILES),
    }
    status_order = getattr(_adapter_owner, "_STATUS_ORDER", None)
    hard_failures = getattr(_adapter_owner, "_HARD_FAILURES", None)
    if (
        len(pure) != 6
        or len(parser) != 5
        or tuple(_adapter_owner._INPUT_FIELD_ORDER)
        != tuple(_hot_loop_owner.INPUT_FIELD_ORDER)
        or frozenset(_adapter_owner._INPUT_REQUIRED)
        != frozenset(_hot_loop_owner.INPUT_REQUIRED_FIELDS)
        or frozenset(_adapter_owner._INPUT_OPTIONAL)
        != frozenset(_hot_loop_owner.INPUT_OPTIONAL_FIELDS)
        or tuple(sorted(_adapter_owner._LEGACY_ALIASES))
        != tuple(_hot_loop_owner.LEGACY_INPUT_ALIASES)
        or tuple(_adapter_owner._OUTPUT_FIELD_ORDER)
        != tuple(_hot_loop_owner.OUTPUT17_FIELD_ORDER)
        or type(status_order) is not tuple
        or len(status_order) != 18
        or type(hard_failures) is not frozenset
        or hard_failures
        != frozenset(status_order[2:16] + (status_order[17],))
        or _adapter_owner._INPUT_SCHEMA
        != "covapie_current11_task2_batch_index_remap_adapter_input_v1"
        or _adapter_owner._OUTPUT_SCHEMA
        != "covapie_current11_task2_batch_index_remap_adapter_output_v1"
        or _adapter_owner._PARSER_SCHEMA
        != "order_preserving_checkpoint_heavy_projection_v1"
        or _adapter_owner._COLLATE_SCHEMA
        != "processed_ligand_pocket_dataset_collate_fn_v1"
        or _adapter_owner._JOIN
        != "exact_source_table_row_identity_to_order_preserving_parser_node_v1"
        or tuple(_adapter_owner._INDEX_SPACES)
        != (
            "source_atom_table_data_row_index",
            "parser_sample_local_index",
            "collated_batch_segment_index",
            "dynamics_joint_global_node_index",
        )
        or formal != _hot_loop_owner.FORMAL_AUTHORITY_IDENTITY
    ):
        _fail()
    return {
        "pure_helper_rows": pure,
        "parser_helper_rows": parser,
        "formal_authority_identity": formal,
    }


def _framed_digest(
    domain: bytes,
    names: Sequence[str],
    artifacts: Mapping[str, bytes],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    for name in names:
        payload = artifacts.get(name)
        if type(payload) is not bytes:
            _fail()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_reconciliation_artifacts(
    artifacts: object,
) -> dict[str, object]:
    if (
        type(artifacts) is not dict
        or tuple(artifacts) != _RECONCILIATION_ARTIFACT_NAMES
        or len(artifacts) != 6
    ):
        _fail()
    parsed: dict[str, dict[str, object]] = {}
    for name, payload in artifacts.items():
        if type(payload) is not bytes:
            _fail()
        parsed[name] = _strict_json(payload)
    digest = _framed_digest(
        _RECONCILIATION_DOMAIN,
        _RECONCILIATION_ARTIFACT_NAMES[:5],
        artifacts,
    )
    manifest = parsed[_RECONCILIATION_ARTIFACT_NAMES[0]]
    fields = parsed[_RECONCILIATION_ARTIFACT_NAMES[1]]
    parity = parsed[_RECONCILIATION_ARTIFACT_NAMES[3]]
    report = parsed[_RECONCILIATION_ARTIFACT_NAMES[5]]
    runtime_fast = parity.get("runtime_fast_path")
    historical_failure = parity.get("historical_private_failure")
    if (
        digest != RECONCILIATION_DIGEST
        or manifest.get("selected_reconciliation_model")
        != _SELECTED_RECONCILIATION_MODEL
        or manifest.get("runtime_fast_path_output17_target") != RUNTIME_TARGET
        or fields.get("exact17_field_order")
        != list(_adapter_owner._OUTPUT_FIELD_ORDER)
        or fields.get("successful_cross_producer_core15_field_order")
        != list(_adapter_owner._OUTPUT_FIELD_ORDER[:15])
        or fields.get("producer_metadata_fields")
        != list(_adapter_owner._OUTPUT_FIELD_ORDER[15:])
        or type(runtime_fast) is not dict
        or runtime_fast.get("runtime_target") != RUNTIME_TARGET
        or runtime_fast.get("runtime_whole_output17_exact_required") is not True
        or runtime_fast.get("success") is not True
        or runtime_fast.get("failure") is not True
        or runtime_fast.get("old_adapter_report_authoritative") is not False
        or type(historical_failure) is not dict
        or historical_failure.get("historical_failure_runtime_golden") is not False
        or historical_failure.get("normalization_forbidden") is not True
        or report.get("gate_status")
        != "PASS_OUTPUT17_SEMANTIC_RECONCILIATION_CONTRACT_ONLY"
        or report.get("stable_contract_digest") != RECONCILIATION_DIGEST
        or report.get("selected_reconciliation_model")
        != _SELECTED_RECONCILIATION_MODEL
        or report.get("runtime_fast_path_output17_target") != RUNTIME_TARGET
        or report.get("runtime_success_whole_output17_target_exact") is not True
        or report.get("runtime_failure_whole_output17_target_exact") is not True
        or report.get("historical_failure_cross_producer_core15_exact") is not False
    ):
        _fail()
    return {
        "stable_contract_digest": digest,
        "selected_reconciliation_model": _SELECTED_RECONCILIATION_MODEL,
        "runtime_target": RUNTIME_TARGET,
        "exact17_field_order": list(_adapter_owner._OUTPUT_FIELD_ORDER),
        "runtime_success_whole_exact": True,
        "runtime_failure_whole_exact": True,
        "historical_failure_runtime_golden": False,
        "failure_normalization_forbidden": True,
    }


def _validate_successor_artifacts(artifacts: object) -> dict[str, object]:
    if (
        type(artifacts) is not dict
        or tuple(artifacts) != _SUCCESSOR_ARTIFACT_NAMES
        or len(artifacts) != 6
        or _HISTORICAL_REPORT_NAME in artifacts
    ):
        _fail()
    for name, (size, lines, digest) in _STABLE5_IDENTITIES.items():
        payload = artifacts.get(name)
        if (
            type(payload) is not bytes
            or len(payload) != size
            or payload.count(b"\n") != lines
            or _sha256(payload) != digest
        ):
            _fail()
    digest = _framed_digest(_STABLE5_DOMAIN, _STABLE5_NAMES, artifacts)
    report_payload = artifacts.get(_SUCCESSOR_REPORT_NAME)
    if type(report_payload) is not bytes:
        _fail()
    report = _strict_json(report_payload)
    if (
        digest != SUCCESSOR_STABLE5_DIGEST
        or report.get("successor_status")
        != "PASS_REMAP_PREDECESSOR_SUCCESSOR_ONLY"
        or report.get("artifact_names") != list(_SUCCESSOR_ARTIFACT_NAMES)
        or report.get("historical_stable5_digest")
        != SUCCESSOR_STABLE5_DIGEST
        or report.get("stable_semantic_artifact_parity") is not True
        or report.get("historical_manifest_report_name_is_current_output")
        is not False
        or report.get("successor_returned_report_name")
        != _SUCCESSOR_REPORT_NAME
        or report.get("historical_report_byte_parity_required") is not False
        or report.get("B2_transition_contract_called") is not True
        or report.get("B2_transition_contract_passed") is not True
        or report.get("B2_transition_contract_call_count") != 1
        or report.get("production_monkeypatch_used") is not False
        or report.get("ready_for_one_heavy_parity_timing_probe") is not True
    ):
        _fail()
    return {
        "stable5_digest": digest,
        "successor_status": report["successor_status"],
        "stable_semantic_artifact_parity": True,
        "B2_transition_consumed_and_passed": True,
        "historical_report_present": False,
        "production_monkeypatch_used": False,
    }


def _parse_successor_stable5_v1(
    artifacts: Mapping[str, bytes],
) -> dict[str, object]:
    manifest = _adapter_owner._strict_json(artifacts[_STABLE5_NAMES[0]])
    input_schema = _adapter_owner._strict_json(artifacts[_STABLE5_NAMES[1]])
    output_schema = _adapter_owner._strict_json(artifacts[_STABLE5_NAMES[2]])
    vectors = _adapter_owner._strict_json(artifacts[_STABLE5_NAMES[4]])
    csv_header, statuses = _adapter_owner._csv_rows(artifacts[_STABLE5_NAMES[3]])
    expected_header = (
        "status_code",
        "status",
        "scope",
        "is_success",
        "is_nonmember",
        "is_hard_failure",
        "numeric_output_allowed",
        "overall_status_allowed",
        "description",
    )
    status_order = tuple(row.get("status") for row in statuses)
    hard = frozenset(
        row["status"]
        for row in statuses
        if row.get("is_hard_failure") == "true"
    )
    if (
        csv_header != expected_header
        or status_order != tuple(_adapter_owner._STATUS_ORDER)
        or tuple(row.get("status_code") for row in statuses)
        != tuple(str(index) for index in range(18))
        or hard != frozenset(_adapter_owner._HARD_FAILURES)
        or manifest.get("schema_version") != _adapter_owner._CONTRACT_SCHEMA
        or input_schema.get("schema_version") != _adapter_owner._INPUT_SCHEMA
        or tuple(input_schema.get("field_order", ()))
        != tuple(_adapter_owner._INPUT_FIELD_ORDER)
        or tuple(input_schema.get("required_fields", ()))
        != tuple(_adapter_owner._INPUT_FIELD_ORDER[:15])
        or tuple(input_schema.get("optional_fields", ()))
        != tuple(_adapter_owner._INPUT_FIELD_ORDER[15:])
        or output_schema.get("schema_version") != _adapter_owner._OUTPUT_SCHEMA
        or tuple(output_schema.get("field_order", ()))
        != tuple(_adapter_owner._OUTPUT_FIELD_ORDER)
        or vectors.get("schema_version") != _adapter_owner._REFERENCE_SCHEMA
    ):
        _fail()
    join = manifest.get("join_contract")
    spaces = manifest.get("index_space_definitions")
    placeholder = output_schema.get("numeric_placeholder_semantics")
    if (
        type(join) is not dict
        or join.get("name") != _adapter_owner._JOIN
        or type(spaces) is not list
        or tuple(
            row.get("name") for row in spaces if type(row) is dict
        )
        != tuple(_adapter_owner._INDEX_SPACES)
        or placeholder
        != {
            "sentinel_placeholder_usage_forbidden": True,
            "valid_zero_index_allowed": True,
            "negative_index_allowed": False,
            "missing_numeric_entry_is_omitted": True,
            "joint_unavailable_representation": None,
        }
    ):
        _fail()
    lineage = manifest.get("source_lineage")
    if (
        type(lineage) is not dict
        or lineage.get("projection_instance_builder", {}).get(
            "projection_digest"
        )
        != PROJECTION_INSTANCE_DIGEST
        or lineage.get("payload_builder", {}).get("payload_digest")
        != PAYLOAD_BUNDLE_DIGEST
        or lineage.get("projection_contract_gate", {}).get("contract_digest")
        != PROJECTION_CONTRACT_DIGEST
        or lineage.get("formal_routing_sidecar", {}).get("snapshot_SHA256")
        != _adapter_owner._FORMAL_SNAPSHOT_SHA256
        or lineage.get("formal_routing_sidecar", {}).get("aggregate")
        != _adapter_owner._FORMAL_AGGREGATE
    ):
        _fail()
    source = vectors.get("source_contract")
    records = vectors.get("exact22_source_to_local")
    if type(source) is not dict or type(records) is not list or len(records) != 11:
        _fail()
    expected_pairs = [list(pair) for pair in _adapter_owner._SOURCE_PAIRS]
    if (
        source.get("pair_values_source_row_indices") != expected_pairs
        or source.get("sample_pair_offsets") != list(range(12))
        or source.get("entry_validity") != [True] * 11
        or source.get("sample_validity") != [True] * 11
        or source.get("pair_count") != 11
        or source.get("column_semantics")
        != [
            "pocket_atom_table_row_index_0based",
            "ligand_atom_table_row_index_0based",
        ]
    ):
        _fail()
    sample_order = source.get("sample_order")
    if type(sample_order) is not list or len(sample_order) != 11:
        _fail()
    authority: list[dict[str, object]] = []
    role_count = 0
    for index, (sample, record) in enumerate(zip(sample_order, records)):
        if (
            not _adapter_owner._identity_complete(sample)
            or type(sample.get("source_sample_index")) is not int
            or sample.get("source_sample_index") != index
            or type(record) is not dict
            or record.get("source_sample_index") != index
            or record.get("sample_identity") != sample
        ):
            _fail()
        roles_list = record.get("roles")
        if type(roles_list) is not list or len(roles_list) != 2:
            _fail()
        roles: dict[str, object] = {}
        for expected_role, role_record in zip(
            ("pocket", "ligand"), roles_list, strict=True
        ):
            role_count += 1
            if (
                type(role_record) is not dict
                or role_record.get("role") != expected_role
            ):
                _fail()
            derived = _adapter_owner._derive_role_authority(role_record)
            atom = derived.get("selected_atom_identity")
            source_row = derived.get("selected_source_row_index_0based")
            local = derived.get("selected_parser_local_index")
            row_count = derived.get("row_count")
            parser_count = derived.get("parser_output_atom_count")
            if (
                type(atom) is not dict
                or tuple(sorted(atom))
                != tuple(sorted(_adapter_owner._ATOM_IDENTITY_FIELDS))
                or any(
                    type(atom.get(field)) is not str
                    for field in _adapter_owner._ATOM_IDENTITY_FIELDS
                )
                or type(source_row) is not int
                or type(local) is not int
                or type(row_count) is not int
                or type(parser_count) is not int
                or not 0 <= source_row < row_count
                or not 0 <= local < parser_count
                or derived.get("source_to_parser_local")
                != {str(source_row): local}
            ):
                _fail()
            roles[expected_role] = derived
        authority.append(
            {
                "sample_identity": copy.deepcopy(sample),
                "roles": roles,
            }
        )
    canonical = vectors.get("canonical_exact11_batch_reference")
    if (
        role_count != 22
        or type(canonical) is not dict
        or type(canonical.get("batch_contract")) is not dict
        or type(canonical.get("output")) is not dict
        or canonical["output"].get("batch_sample_order") != sample_order
    ):
        _fail()
    for sample, table in zip(sample_order, authority, strict=True):
        if _adapter_owner._identity_key(sample) != _adapter_owner._identity_key(
            table["sample_identity"]
        ):
            _fail()
    return {
        "source_contract": copy.deepcopy(source),
        "authority_tables": authority,
        "source_sample_count": len(sample_order),
        "authority_table_count": len(authority),
        "authority_role_count": role_count,
        "selected_atom_identity_field_count": len(
            _adapter_owner._ATOM_IDENTITY_FIELDS
        ),
    }


@dataclass(frozen=True, slots=True)
class _FrozenDictionary:
    _items: tuple[tuple[str, object], ...]


@dataclass(frozen=True, slots=True)
class _FrozenList:
    _values: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class _AdapterContext:
    _semantic: _FrozenDictionary
    _seal: str


def _deep_freeze(value: object) -> object:
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            _fail()
        return _FrozenDictionary(
            tuple((key, _deep_freeze(item)) for key, item in value.items())
        )
    if type(value) is list:
        return _FrozenList(tuple(_deep_freeze(item) for item in value))
    if type(value) in (str, int, bool) or value is None:
        return value
    _fail()


def _deep_thaw(value: object) -> object:
    if type(value) is _FrozenDictionary:
        return {key: _deep_thaw(item) for key, item in value._items}
    if type(value) is _FrozenList:
        return [_deep_thaw(item) for item in value._values]
    if type(value) in (str, int, bool) or value is None:
        return value
    _fail()


def _construction_seal(semantic: Mapping[str, object]) -> str:
    return _sha256(_SEAL_DOMAIN + _canonical_json(dict(semantic)))


def _formal_authority_identity() -> dict[str, object]:
    return {
        "canonical_relative_path": _adapter_owner._FORMAL_RELATIVE,
        "canonical_readlink": _adapter_owner._FORMAL_READLINK,
        "formal_aggregate_sha256": _adapter_owner._FORMAL_AGGREGATE,
        "formal_snapshot_sha256": _adapter_owner._FORMAL_SNAPSHOT_SHA256,
        "formal_exact4_sha256": copy.deepcopy(_adapter_owner._FORMAL_FILES),
    }


def _logical_context_semantic_payload(
    *,
    parsed: Mapping[str, object],
) -> dict[str, object]:
    semantic = {
        "context_schema_version": CONTEXT_SCHEMA_VERSION,
        "context_contract_version": CONTEXT_CONTRACT_VERSION,
        "runtime_output17_target": RUNTIME_TARGET,
        "reconciliation_contract_digest": RECONCILIATION_DIGEST,
        "successor_stable5_digest": SUCCESSOR_STABLE5_DIGEST,
        "remap_contract_digest": SUCCESSOR_STABLE5_DIGEST,
        "projection_instance_digest": PROJECTION_INSTANCE_DIGEST,
        "payload_bundle_digest": PAYLOAD_BUNDLE_DIGEST,
        "projection_contract_digest": PROJECTION_CONTRACT_DIGEST,
        "join_contract": _adapter_owner._JOIN,
        "index_space_order": list(_adapter_owner._INDEX_SPACES),
        "input_field_order": list(_adapter_owner._INPUT_FIELD_ORDER),
        "input_required_fields": list(_adapter_owner._INPUT_FIELD_ORDER[:15]),
        "input_optional_fields": list(_adapter_owner._INPUT_FIELD_ORDER[15:]),
        "output17_field_order": list(_adapter_owner._OUTPUT_FIELD_ORDER),
        "source_contract": copy.deepcopy(parsed["source_contract"]),
        "authority_tables": copy.deepcopy(parsed["authority_tables"]),
        "formal_authority_identity": _formal_authority_identity(),
        "context_freshness_model": CONTEXT_FRESHNESS_MODEL,
    }
    if tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]:
        _fail()
    return semantic


def _construct_context(
    *,
    semantic: Mapping[str, object],
) -> _AdapterContext:
    if type(semantic) is not dict or tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]:
        _fail()
    seal = _construction_seal(semantic)
    frozen = _deep_freeze(dict(semantic))
    if type(frozen) is not _FrozenDictionary:
        _fail()
    return _AdapterContext(frozen, seal)


def _validate_context_and_materialize(
    context: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    if (
        type(context) is not _AdapterContext
        or type(context._semantic) is not _FrozenDictionary
        or type(context._seal) is not str
        or len(context._seal) != 64
    ):
        _fail()
    semantic = _deep_thaw(context._semantic)
    if (
        type(semantic) is not dict
        or tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]
        or semantic.get("context_schema_version") != CONTEXT_SCHEMA_VERSION
        or semantic.get("context_contract_version") != CONTEXT_CONTRACT_VERSION
        or semantic.get("runtime_output17_target") != RUNTIME_TARGET
        or semantic.get("reconciliation_contract_digest")
        != RECONCILIATION_DIGEST
        or semantic.get("successor_stable5_digest")
        != SUCCESSOR_STABLE5_DIGEST
        or semantic.get("remap_contract_digest") != SUCCESSOR_STABLE5_DIGEST
        or semantic.get("projection_instance_digest")
        != PROJECTION_INSTANCE_DIGEST
        or semantic.get("payload_bundle_digest") != PAYLOAD_BUNDLE_DIGEST
        or semantic.get("projection_contract_digest")
        != PROJECTION_CONTRACT_DIGEST
        or semantic.get("join_contract") != _adapter_owner._JOIN
        or semantic.get("index_space_order")
        != list(_adapter_owner._INDEX_SPACES)
        or semantic.get("input_field_order")
        != list(_adapter_owner._INPUT_FIELD_ORDER)
        or semantic.get("input_required_fields")
        != list(_adapter_owner._INPUT_FIELD_ORDER[:15])
        or semantic.get("input_optional_fields")
        != list(_adapter_owner._INPUT_FIELD_ORDER[15:])
        or semantic.get("output17_field_order")
        != list(_adapter_owner._OUTPUT_FIELD_ORDER)
        or semantic.get("formal_authority_identity")
        != _formal_authority_identity()
        or semantic.get("context_freshness_model")
        != CONTEXT_FRESHNESS_MODEL
        or _construction_seal(semantic) != context._seal
    ):
        _fail()
    source = semantic.get("source_contract")
    authority = semantic.get("authority_tables")
    if type(source) is not dict or type(authority) is not list:
        _fail()
    if any(type(table) is not dict for table in authority):
        _fail()
    return source, authority, semantic


def _logical_context_value(context: object) -> dict[str, object]:
    unused_source, unused_authority, semantic = _validate_context_and_materialize(
        context
    )
    logical = dict(semantic)
    logical["construction_seal"] = context._seal
    if tuple(logical) != _LOGICAL_FIELD_ORDER:
        _fail()
    return logical


def _build_context_kernel(
    *,
    repo_root: Path,
    state_root: Path,
    reconciliation_artifacts: object | None,
    successor_artifacts: object | None,
) -> _AdapterContext:
    _validate_repository_lineage(repo_root)
    _verify_owner_identities(repo_root)
    _validate_frozen_adapter_contract()
    canonical = state_root / _adapter_owner._FORMAL_RELATIVE
    formal_before = _adapter_owner._validate_formal(canonical)
    if reconciliation_artifacts is None and successor_artifacts is None:
        reconciliation_artifacts = _reconciliation_owner.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
        _validate_reconciliation_artifacts(reconciliation_artifacts)
        successor_artifacts = _successor_owner.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    elif reconciliation_artifacts is None or successor_artifacts is None:
        _fail()
    else:
        _validate_reconciliation_artifacts(reconciliation_artifacts)
    _validate_successor_artifacts(successor_artifacts)
    parsed = _parse_successor_stable5_v1(successor_artifacts)
    semantic = _logical_context_semantic_payload(parsed=parsed)
    formal_after = _adapter_owner._validate_formal(canonical)
    if formal_before != formal_after:
        _fail()
    return _construct_context(semantic=semantic)


def _build_context_from_verified_predecessor_artifacts_v1(
    *,
    repo_root: Path,
    state_root: Path,
    reconciliation_artifacts: dict[str, bytes],
    successor_artifacts: dict[str, bytes],
) -> object:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    return _build_context_kernel(
        repo_root=repository,
        state_root=state,
        reconciliation_artifacts=reconciliation_artifacts,
        successor_artifacts=successor_artifacts,
    )


def _build_public_context_impl(*, repo_root: Path, state_root: Path) -> object:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    if _repository_lifecycle(repository) != "clean-tracked-successor":
        _fail()
    return _build_context_kernel(
        repo_root=repository,
        state_root=state,
        reconciliation_artifacts=None,
        successor_artifacts=None,
    )


def build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> object:
    """Build one opaque context from clean published successor authority."""

    try:
        return _build_public_context_impl(
            repo_root=repo_root,
            state_root=state_root,
        )
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _remap_with_context_impl(
    *,
    context: object,
    adapter_input: dict[str, object],
) -> dict[str, object]:
    source, authority, unused_semantic = _validate_context_and_materialize(context)
    if type(adapter_input) is not dict:
        _fail()
    try:
        copied = copy.deepcopy(adapter_input)
    except BaseException as error:
        raise _ContextInvariantError() from error
    if type(copied) is not dict:
        _fail()
    _adapter_owner._json(copied)
    keys = set(copied)
    schema_rejected = (
        not _adapter_owner._INPUT_REQUIRED.issubset(keys)
        or not keys.issubset(
            _adapter_owner._INPUT_REQUIRED | _adapter_owner._INPUT_OPTIONAL
        )
        or bool(keys & _adapter_owner._LEGACY_ALIASES)
        or any(
            field in copied
            and copied[field] is not None
            and type(copied[field]) is not dict
            for field in ("debug_coordinates", "debug_rank_metadata")
        )
    )
    try:
        if schema_rejected:
            raise _adapter_owner._InputFailure("SCHEMA_VERSION_MISMATCH", 0)
        _adapter_owner._validate_source_contract(copied, source, authority)
        output = _adapter_owner._remap_engine(
            copied,
            authoritative_tables=authority,
        )
    except _adapter_owner._InputFailure as error:
        pairs = source.get("pair_values_source_row_indices")
        if type(pairs) is not list:
            _fail()
        output = _adapter_owner._failure_output(
            copied,
            error.status,
            len(pairs),
            error.entry_index,
        )
    _adapter_owner._validate_output(output)
    return output


def remap_covapie_current11_task2_batch_index_with_context_v1(
    *,
    context: object,
    adapter_input: dict[str, object],
) -> dict[str, object]:
    """Return the current adapter's built-in Output17 with zero runtime I/O."""

    try:
        return _remap_with_context_impl(
            context=context,
            adapter_input=adapter_input,
        )
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error

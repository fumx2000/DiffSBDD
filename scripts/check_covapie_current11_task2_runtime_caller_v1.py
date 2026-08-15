#!/usr/bin/env python3
"""Check the stateless Current11 Task 2 runtime caller V1."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Mapping, NoReturn, Sequence


sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
import torch  # noqa: E402

from dataset import ProcessedLigandPocketDataset  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_current11_runtime_batch_observation_extractor_v1 as extractor,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as remap_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_runtime_caller_contract_gate_v1 as gate,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_runtime_caller_v1 as caller,
)
from scripts import (  # noqa: E402
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)


_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_CHECK_ERROR"
_BASE_COMMIT = "b1dd9e44ba2877a46d9622b2a24612e523f1a100"
_BASE_SUBJECT = "add CovaPIE Current11 Task2 runtime caller contract gate v1"
_BRANCH = "main"
_CONTRACT_DIGEST = (
    "098c66343e2e924ea75ce6619cac7aa9b46baabd7f0143e80e652764660a1c20"
)
_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_runtime_caller_v1.py",
    "scripts/check_covapie_current11_task2_runtime_caller_v1.py",
    "tests/test_covapie_current11_task2_runtime_caller_v1.py",
    "docs/covapie_current11_task2_runtime_caller_v1_guide.md",
)
_FORMAL_CARRIER = (
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
_SOURCE_SPECS = (
    {
        "owner": "runtime_caller_contract_gate_v1",
        "path": gate._MODULE_PATH,
        "mode": "0644",
        "bytes": 43266,
        "LF": 1141,
        "sha256": (
            "ca70cb6a4ba56974b2ccf1940e74c0375e1e64bca5d960988fe94d5a74c3b9d5"
        ),
        "git_blob": "536ec00a8d17145002d2326e2e59a6a9d358a545",
    },
    {
        "owner": "runtime_observation_extractor_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_runtime_batch_observation_extractor_v1.py"
        ),
        "mode": "0644",
        "bytes": 9229,
        "LF": 287,
        "sha256": (
            "aa129304b350e1089411803c90890c638526e6e3db79bd55a9460b7a1960c5b9"
        ),
        "git_blob": "1f7b978eaa111c7cdd296d256c8cfc6d18242802",
    },
    {
        "owner": "compiler_context_from_remap_context_v1",
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_descriptor_"
            "compiler_context_from_remap_context_v1.py"
        ),
        "mode": "0644",
        "bytes": 22556,
        "LF": 683,
        "sha256": (
            "af9c80a1b46839872b64d2be4005e855b91fa26e761c0cd2c1f146a8e8177b35"
        ),
        "git_blob": "0ac10bf21db93273a1e9b0cd49b5b23e33261b44",
    },
    {
        "owner": "remap_adapter_context_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
        ),
        "mode": "0644",
        "bytes": 43578,
        "LF": 1211,
        "sha256": (
            "1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6"
        ),
        "git_blob": "b4a68ff8193666a3d22f777b111c3ae01178ef8d",
    },
    {
        "owner": "formal_collate_dataset_transport",
        "path": "dataset.py",
        "mode": "0644",
        "bytes": 2693,
        "LF": 70,
        "sha256": (
            "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"
        ),
        "git_blob": "5cd1531e9beeca2f53c17b705949676bf457a967",
    },
)
_SUCCESS_CASES = (
    ("canonical", tuple(range(11))),
    ("reversed", tuple(reversed(range(11)))),
    ("subset_10_4_0", (10, 4, 0)),
    ("singleton_10", (10,)),
)


class _CheckError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise _CheckError()


def _fail() -> NoReturn:
    raise _CheckError()


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    return parser


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
        raise _CheckError() from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _CheckError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _safe_file(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise _CheckError() from error
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
    return {
        "mode": "0644",
        "bytes": len(payload),
        "LF": payload.count(b"\n"),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _repository_lifecycle(repo_root: Path) -> tuple[str, dict[str, object]]:
    branch = _run_git(repo_root, ("branch", "--show-current")).strip()
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "origin/main")).strip()
    relation = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...origin/main")
    ).strip()
    subject = _run_git(repo_root, ("log", "-1", "--format=%s", "HEAD")).strip()
    if branch != _BRANCH or relation.count("\t") != 1:
        _fail()
    ahead_text, behind_text = relation.split("\t")
    if not ahead_text.isdigit() or not behind_text.isdigit():
        _fail()
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in _EXACT4}
    if set(status) == expected and len(status) == len(_EXACT4):
        if (
            index
            or head != _BASE_COMMIT
            or origin != _BASE_COMMIT
            or ahead_text != "0"
            or behind_text != "0"
            or subject != _BASE_SUBJECT
        ):
            _fail()
        lifecycle = "precommit-untracked"
    elif not status and len(index) == len(_EXACT4):
        if head != origin or ahead_text != "0" or behind_text != "0":
            _fail()
        _run_git(repo_root, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))
        seen: set[str] = set()
        for row in index:
            try:
                metadata, relative = row.split("\t", 1)
                mode, blob, stage = metadata.split()
            except ValueError as error:
                raise _CheckError() from error
            if (
                relative not in _EXACT4
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
                _fail()
            seen.add(relative)
        if seen != set(_EXACT4):
            _fail()
        lifecycle = "clean-tracked-successor"
    else:
        _fail()
    return lifecycle, {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "head_subject": subject,
    }


def _validate_source_identities(repo_root: Path) -> list[dict[str, object]]:
    identities: list[dict[str, object]] = []
    for spec in _SOURCE_SPECS:
        relative = str(spec["path"])
        identity = _safe_file(repo_root / relative)
        expected = {
            key: spec[key] for key in ("mode", "bytes", "LF", "sha256")
        }
        if (
            identity != expected
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != spec["git_blob"]
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != spec["git_blob"]
            or _run_git(
                repo_root, ("rev-parse", f"{_BASE_COMMIT}:{relative}")
            ).strip()
            != spec["git_blob"]
        ):
            _fail()
        identities.append({"owner": spec["owner"], "path": relative, **identity})
    _run_git(repo_root, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))
    return identities


def _literal_assignment(path: Path, name: str) -> object:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as error:
        raise _CheckError() from error
    matches = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        )
    ]
    if len(matches) != 1:
        _fail()
    try:
        return ast.literal_eval(matches[0])
    except (ValueError, TypeError, SyntaxError) as error:
        raise _CheckError() from error


def _validate_product_contract(repo_root: Path) -> None:
    product_path = repo_root / _EXACT4[0]
    try:
        source = product_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        signature = str(
            inspect.signature(
                caller.run_covapie_current11_task2_runtime_caller_v1
            )
        )
    except (OSError, UnicodeError, SyntaxError, TypeError, ValueError) as error:
        raise _CheckError() from error
    imports: list[tuple[str | None, tuple[str, ...]]] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.append((None, tuple(alias.name for alias in node.names)))
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module, tuple(alias.name for alias in node.names)))
    expected_imports = [
        ("__future__", ("annotations",)),
        ("typing", ("NoReturn",)),
        (
            "covalent_ext",
            ("covapie_current11_runtime_batch_observation_extractor_v1",),
        ),
        (
            "covalent_ext",
            (
                "covapie_current11_task2_batch_descriptor_compiler_context_"
                "from_remap_context_v1",
            ),
        ),
        (
            "covalent_ext",
            ("covapie_current11_task2_batch_index_remap_adapter_context_v1",),
        ),
    ]
    provenance = dict(caller._PROVENANCE_ITEMS)
    readiness = dict(caller._READINESS_ITEMS)
    if (
        imports != expected_imports
        or caller.__all__
        != ("run_covapie_current11_task2_runtime_caller_v1",)
        or signature
        != (
            "(*, batch: 'dict[str, object]', remap_context: 'object', "
            "compiler_context: 'object') -> 'dict[str, object]'"
        )
        or caller._ERROR != gate._CALLER_ERROR
        or caller._RESULT_FIELDS != gate._RESULT_FIELDS
        or caller._EXACT14_FIELDS != gate._EXACT14_FIELDS
        or caller._OUTPUT10_FIELDS != gate._COMPILER_OUTPUT_FIELDS
        or caller._EXACT18_FIELDS != gate._EXACT18_FIELDS
        or caller._OUTPUT17_FIELDS != gate._REMAP_OUTPUT_FIELDS
        or caller._EXTRACTOR_REASONS != gate._EXTRACTOR_REASONS
        or caller._COMPILER_SUCCESS != gate._COMPILER_OVERALL_SUCCESS_STATUS
        or caller._COMPILER_STRUCTURED_FAILURES
        != gate._COMPILER_STRUCTURED_FAILURE_STATUSES
        or caller._REMAP_SUCCESS != gate._REMAP_OVERALL_SUCCESS_STATUS
        or caller._REMAP_STRUCTURED_FAILURES
        != gate._REMAP_STRUCTURED_FAILURE_STATUSES
        or provenance.get("selected_architecture") != gate._ARCHITECTURE
        or provenance.get("runtime_caller_contract_commit") != _BASE_COMMIT
        or provenance.get("runtime_caller_contract_digest") != _CONTRACT_DIGEST
        or provenance.get("runtime_caller_implemented") is not True
        or readiness
        != {
            "runtime_caller_contract_gate_implemented": True,
            "runtime_caller_contract_gate_passed": True,
            "runtime_caller_implemented": True,
            "ready_for_runtime_caller_implementation": False,
            "ready_for_dataloader_integration": False,
            "ready_for_model_integration": False,
            "ready_for_loss_integration": False,
            "feature_semantics_reaudit_required_before_training": True,
            "step12d_smoke_is_final_training_feature_contract": False,
            "ready_for_training": False,
        }
        or any(type(value) is not bool for value in readiness.values())
        or _literal_assignment(product_path, "__all__") != caller.__all__
    ):
        _fail()


def _path_identity(path: Path) -> tuple[object, ...]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    except OSError as error:
        raise _CheckError() from error
    return (
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_ino),
        int(metadata.st_mtime_ns),
        None if payload is None else hashlib.sha256(payload).hexdigest(),
    )


def _snapshot(repo_root: Path, state_root: Path) -> tuple[object, ...]:
    return (
        _run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple(
            (relative, _path_identity(repo_root / relative))
            for relative in (
                *_EXACT4,
                *(str(spec["path"]) for spec in _SOURCE_SPECS),
            )
        ),
        bridge_checker._adapter_checker._state_snapshot(state_root),
    )


def _batch_fingerprint(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return (
            "tensor",
            id(value),
            str(value.dtype),
            str(value.device),
            tuple(value.shape),
            int(value._version),
            value.detach().cpu().clone(),
        )
    if type(value) is dict:
        return (
            "dict",
            id(value),
            tuple((key, _batch_fingerprint(item)) for key, item in value.items()),
        )
    if type(value) is list:
        return ("list", id(value), tuple(_batch_fingerprint(item) for item in value))
    if type(value) is tuple:
        return ("tuple", id(value), tuple(_batch_fingerprint(item) for item in value))
    return ("scalar", type(value).__name__, value)


def _fingerprint_equal(left: object, right: object) -> bool:
    if type(left) is tuple and type(right) is tuple:
        if len(left) != len(right):
            return False
        if left and left[0] == "tensor" and right[0] == "tensor":
            return left[:-1] == right[:-1] and torch.equal(left[-1], right[-1])
        return all(_fingerprint_equal(a, b) for a, b in zip(left, right))
    return left == right


def _profiled_call(
    *,
    batch: dict[str, object],
    remap_context: object,
    compiler_context: object,
) -> tuple[dict[str, object], dict[str, int]]:
    targets = {
        extractor.extract_covapie_current11_runtime_batch_observation_v1.__code__: (
            "extractor"
        ),
        bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1.__code__: (
            "compiler"
        ),
        remap_owner.remap_covapie_current11_task2_batch_index_with_context_v1.__code__: (
            "remap"
        ),
    }
    counts = {"extractor": 0, "compiler": 0, "remap": 0}
    previous = sys.getprofile()

    def profile(frame: object, event: str, unused_arg: object) -> None:
        del unused_arg
        if event == "call":
            name = targets.get(frame.f_code)
            if name is not None:
                counts[name] += 1

    try:
        sys.setprofile(profile)
        result = caller.run_covapie_current11_task2_runtime_caller_v1(
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
    finally:
        sys.setprofile(previous)
    return result, counts


def _validate_result(value: object) -> dict[str, object]:
    if (
        type(value) is not dict
        or tuple(value) != caller._RESULT_FIELDS
        or value.get("schema_version") != caller._RESULT_SCHEMA
        or type(value.get("provenance")) is not dict
        or value.get("provenance") != dict(caller._PROVENANCE_ITEMS)
        or type(value.get("readiness")) is not dict
        or value.get("readiness") != dict(caller._READINESS_ITEMS)
        or any(type(item) is not bool for item in value["readiness"].values())
    ):
        _fail()
    try:
        json.dumps(value, ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _CheckError() from error
    return value


def _collate(
    dataset: ProcessedLigandPocketDataset,
    indices: Sequence[int],
) -> dict[str, object]:
    return dataset.collate_fn([dataset[index] for index in indices])


def _runtime_reference(
    *,
    lifecycle: str,
    repo_root: Path,
    state_root: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    remap_context, acquisition = bridge_checker._acquire_remap_context(
        lifecycle=lifecycle,
        repo_root=repo_root,
        state_root=state_root,
    )
    compiler_context = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context,
        )
    )
    expected_profile = {
        "precommit-untracked": (True, False),
        "clean-tracked-successor": (False, True),
    }[lifecycle]
    if (
        acquisition.get("test_harness_only") is not expected_profile[0]
        or acquisition.get("real_public_remap_context_build_performed")
        is not expected_profile[1]
        or acquisition.get("predecessor_public_call_counts")
        != {"reconciliation": 1, "successor": 1, "B2": 1}
        or acquisition.get("formal_before_after_call_count") != 2
        or acquisition.get("production_monkeypatch_used") is not False
    ):
        _fail()
    dataset = ProcessedLigandPocketDataset(state_root / _FORMAL_CARRIER, center=False)
    cases: list[dict[str, object]] = []
    for case_id, indices in _SUCCESS_CASES:
        batch = _collate(dataset, indices)
        before = _batch_fingerprint(batch)
        result, counts = _profiled_call(
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
        result = _validate_result(result)
        output17 = result["remap_output17_or_none"]
        if (
            result["runtime_status"] != "full_success"
            or result["failure_stage"] != "none"
            or result["failure_reason"] != "NONE"
            or result["compiler_status"] != "COMPILED_EXACT"
            or result["remap_status"] != "REMAPPED_EXACT"
            or result["compiler_failure_output10_or_none"] is not None
            or type(output17) is not dict
            or tuple(output17) != caller._OUTPUT17_FIELDS
            or output17.get("pair_values_joint_global_indices") is not None
            or output17.get("provenance", {}).get("joint_index_status")
            != "JOINT_INDEX_SPACE_UNAVAILABLE"
            or counts != {"extractor": 1, "compiler": 1, "remap": 1}
            or not _fingerprint_equal(before, _batch_fingerprint(batch))
        ):
            _fail()
        cases.append(
            {
                "case_id": case_id,
                "runtime_status": result["runtime_status"],
                "compiler_status": result["compiler_status"],
                "remap_status": result["remap_status"],
                "call_vector": counts,
                "raw_batch_mutation": 0,
            }
        )

    extractor_batch = _collate(dataset, (10,))
    extractor_batch["lig_mask"] = extractor_batch["lig_mask"].clone()
    extractor_batch["lig_mask"][0] = 1
    extractor_result, extractor_counts = _profiled_call(
        batch=extractor_batch,
        remap_context=object(),
        compiler_context=object(),
    )
    extractor_result = _validate_result(extractor_result)
    if (
        extractor_result["runtime_status"] != "extractor_failure"
        or extractor_result["failure_reason"] != "invalid_membership"
        or extractor_counts != {"extractor": 1, "compiler": 0, "remap": 0}
    ):
        _fail()
    compiler_batch = _collate(dataset, (10,))
    compiler_batch["names"] = [np.str_("not-a-current11-sample")]
    compiler_result, compiler_counts = _profiled_call(
        batch=compiler_batch,
        remap_context=object(),
        compiler_context=compiler_context,
    )
    compiler_result = _validate_result(compiler_result)
    if (
        compiler_result["runtime_status"] != "compiler_failure"
        or compiler_result["compiler_status"] != "BATCH_SAMPLE_KEY_UNKNOWN"
        or compiler_result["remap_status"] is not None
        or type(compiler_result["compiler_failure_output10_or_none"])
        is not dict
        or compiler_result["remap_output17_or_none"] is not None
        or compiler_counts != {"extractor": 1, "compiler": 1, "remap": 0}
    ):
        _fail()
    return cases, {
        "extractor_failure": {
            "runtime_status": extractor_result["runtime_status"],
            "failure_reason": extractor_result["failure_reason"],
            "call_vector": extractor_counts,
        },
        "compiler_failure": {
            "runtime_status": compiler_result["runtime_status"],
            "compiler_status": compiler_result["compiler_status"],
            "call_vector": compiler_counts,
        },
        "context_acquisition": {
            "test_harness_only": acquisition["test_harness_only"],
            "real_public_remap_context_build_performed": acquisition[
                "real_public_remap_context_build_performed"
            ],
            "predecessor_public_call_counts": acquisition[
                "predecessor_public_call_counts"
            ],
            "formal_before_after_call_count": acquisition[
                "formal_before_after_call_count"
            ],
            "production_monkeypatch_used": acquisition[
                "production_monkeypatch_used"
            ],
        },
    }


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repo_root = _require_root(arguments.repo_root)
    state_root = _require_root(arguments.state_root)
    lifecycle, repository = _repository_lifecycle(repo_root)
    before = _snapshot(repo_root, state_root)
    exact4 = [
        {"path": relative, **_safe_file(repo_root / relative)}
        for relative in _EXACT4
    ]
    source_identities = _validate_source_identities(repo_root)
    _validate_product_contract(repo_root)
    cases, runtime = _runtime_reference(
        lifecycle=lifecycle,
        repo_root=repo_root,
        state_root=state_root,
    )
    after = _snapshot(repo_root, state_root)
    if before != after:
        _fail()
    readiness = dict(caller._READINESS_ITEMS)
    if (
        readiness["runtime_caller_contract_gate_implemented"] is not True
        or readiness["runtime_caller_contract_gate_passed"] is not True
        or readiness["runtime_caller_implemented"] is not True
        or readiness["ready_for_runtime_caller_implementation"] is not False
        or readiness["ready_for_training"] is not False
    ):
        _fail()
    result = {
        "status": "PASS_CURRENT11_TASK2_RUNTIME_CALLER_V1",
        "repository_lifecycle": lifecycle,
        "repository": repository,
        "contract_commit_binding": _BASE_COMMIT,
        "contract_digest_binding": _CONTRACT_DIGEST,
        "caller_error_token": caller._ERROR,
        "runtime_result_schema": caller._RESULT_SCHEMA,
        "runtime_result_exact_field_count": len(caller._RESULT_FIELDS),
        "repository_exact4_identities": exact4,
        "published_source_identities": source_identities,
        "success_cases": cases,
        **runtime,
        "per_batch_context_build_count": 0,
        "per_batch_filesystem_calls": 0,
        "per_batch_filesystem_mutations": 0,
        "per_batch_Git_calls": 0,
        "per_batch_subprocess_calls": 0,
        **readiness,
        "persistent_artifacts_written": 0,
    }
    sys.stdout.buffer.write(
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1)

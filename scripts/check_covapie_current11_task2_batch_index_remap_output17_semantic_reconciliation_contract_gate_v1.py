#!/usr/bin/env python3
"""Check the Current11 Task2 Output17 semantic reconciliation gate V1."""

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
from typing import NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    as gate,
)


_ERROR = gate.ERROR_TOKEN


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def _root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
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
        raise ValueError(_ERROR) from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _safe_exact4(repo_root: Path) -> None:
    for relative in gate.REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(_ERROR) from error
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
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(_ERROR) from error


def _repository_lifecycle(repo_root: Path) -> str:
    if _run_git(repo_root, ("branch", "--show-current")).strip() != gate.BRANCH:
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{gate.BASE_COMMIT}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", gate.BASE_COMMIT, "HEAD"))
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *gate.REPOSITORY_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in gate.REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(gate.REPOSITORY_EXACT4):
        if index:
            _fail()
        _safe_exact4(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(gate.REPOSITORY_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise ValueError(_ERROR) from error
        if (
            relative not in gate.REPOSITORY_EXACT4
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
    if seen != set(gate.REPOSITORY_EXACT4):
        _fail()
    _safe_exact4(repo_root)
    return "clean-tracked-successor"


def _path_item(path: Path) -> tuple[object, ...]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    except OSError as error:
        raise ValueError(_ERROR) from error
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else hashlib.sha256(payload).hexdigest(),
    )


def _snapshot(repo_root: Path, state_root: Path) -> tuple[object, ...]:
    repository_paths = (
        *gate.REPOSITORY_EXACT4,
        *(str(spec["path"]) for spec in gate.OWNER_SPECS.values()),
    )
    evidence_paths = tuple(
        str(spec["relative_path"])
        for spec in gate.REVIEWED_EVIDENCE_SPECS.values()
    )
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple(
            (relative, _path_item(repo_root / relative))
            for relative in repository_paths
        ),
        tuple(
            (relative, _path_item(state_root / relative))
            for relative in evidence_paths
        ),
    )


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _target_name(node.value)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _static_product_validation(repo_root: Path) -> None:
    try:
        source = (repo_root / gate.MODULE_PATH).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    function = (
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    )
    signature = inspect.signature(function)
    if (
        gate.__all__ != (function.__name__,)
        or tuple(signature.parameters) != ("repo_root", "state_root")
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in signature.parameters.values()
        )
    ):
        _fail()
    forbidden_calls = {
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        "_contract_exact6",
        "setattr",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            called = _target_name(node.func)
            leaf = None if called is None else called.rsplit(".", 1)[-1]
            if leaf in forbidden_calls:
                _fail()
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Attribute) for target in targets):
                _fail()


def _canonical_object(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if canonical != payload:
        _fail()
    return value


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(gate.STABLE_DIGEST_DOMAIN)
    for name in gate.STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _verify_artifacts(
    artifacts: object,
    *,
    lifecycle: str,
) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != gate.ARTIFACT_NAMES:
        _fail()
    parsed: dict[str, dict[str, object]] = {}
    for name, payload in artifacts.items():
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
        ):
            _fail()
        parsed[name] = _canonical_object(payload)
    digest = _manual_digest(artifacts)
    manifest = parsed[gate.MANIFEST_NAME]
    fields = parsed[gate.FIELD_PARTITION_NAME]
    metadata = parsed[gate.METADATA_CONTRACT_NAME]
    parity = parsed[gate.PARITY_CONTRACT_NAME]
    negative = parsed[gate.NEGATIVE_MATRIX_NAME]
    report = parsed[gate.REPORT_NAME]
    success_rows = report.get("pure_success_evidence")
    failure_rows = report.get("pure_failure_evidence")
    readiness = report.get("readiness")
    validators = metadata.get("validators")
    if (
        manifest.get("artifact_names") != list(gate.ARTIFACT_NAMES)
        or manifest.get("stable_artifact_names")
        != list(gate.STABLE_ARTIFACT_NAMES)
        or manifest.get("report_self_excluded_from_stable_digest") is not True
        or manifest.get("canonical_mask_semantics")
        != [
            {"semantic_name": semantic, "display_alias": alias}
            for semantic, alias in gate.CANONICAL_MASKS
        ]
        or fields.get("exact17_field_order") != list(gate.EXACT17_FIELD_ORDER)
        or fields.get("successful_cross_producer_core15_field_order")
        != list(gate.CORE15_FIELD_ORDER)
        or fields.get("producer_metadata_fields")
        != list(gate.PRODUCER_METADATA_FIELDS)
        or fields.get("universal_failure_core15_cross_producer_authority")
        is not False
        or type(validators) is not dict
        or set(validators)
        != {
            "reference_success_metadata_v1",
            "reference_failure_metadata_v1",
            "runtime_success_metadata_v1",
            "runtime_failure_metadata_v1",
        }
        or validators["reference_success_metadata_v1"].get(
            "provenance_exact_key_order"
        )
        != list(gate.REFERENCE_SUCCESS_PROVENANCE_KEYS)
        or validators["reference_failure_metadata_v1"].get(
            "provenance_exact_key_order"
        )
        != list(gate.REFERENCE_FAILURE_PROVENANCE_KEYS)
        or validators["runtime_success_metadata_v1"].get(
            "provenance_exact_key_order"
        )
        != list(gate.RUNTIME_PROVENANCE_KEYS)
        or validators["runtime_failure_metadata_v1"].get(
            "readiness_exact_key_order"
        )
        != list(gate.RUNTIME_READINESS_KEYS)
        or parity.get("selected_reconciliation_model")
        != gate.SELECTED_RECONCILIATION_MODEL
        or parity.get("runtime_fast_path", {}).get("runtime_target")
        != gate.RUNTIME_TARGET
        or parity.get("runtime_fast_path", {}).get("success") is not True
        or parity.get("runtime_fast_path", {}).get("failure") is not True
        or parity.get("historical_private_failure", {}).get(
            "historical_failure_self_validation"
        )
        is not True
        or parity.get("historical_private_failure", {}).get(
            "cross_producer_core15_exact_required"
        )
        is not False
        or parity.get("historical_private_failure", {}).get(
            "normalization_forbidden"
        )
        is not True
        or negative.get("case_count") != len(gate.NEGATIVE_CASES)
        or [row.get("case_id") for row in negative.get("cases", [])]
        != [case_id for case_id, unused in gate.NEGATIVE_CASES]
        or negative.get("all_cases_fail_closed") is not True
        or report.get("gate_status") != gate.GATE_STATUS
        or report.get("stable_contract_digest") != digest
        or report.get("repository_lifecycle") != lifecycle
        or report.get("frozen_helper_signature_count")
        != gate.FROZEN_HELPER_SIGNATURE_COUNT
        or report.get("pure_success_case_count") != 3
        or type(success_rows) is not list
        or len(success_rows) != 3
        or any(row.get("core15_exact") is not True for row in success_rows)
        or any(
            row.get("shared_provenance2_exact") is not True
            for row in success_rows
        )
        or any(row.get("whole_output17_exact") is not False for row in success_rows)
        or success_rows[2].get("not_in_batch_source_outcome_count", 0) < 1
        or report.get("pure_failure_case_count") != 2
        or type(failure_rows) is not list
        or len(failure_rows) != 2
        or failure_rows[0].get("core15_difference_fields")
        != ["sample_pair_offsets", "sample_validity"]
        or failure_rows[0].get("historical_sample_pair_offsets") != [0]
        or failure_rows[0].get("historical_sample_validity") != []
        or failure_rows[1].get("historical_hard_failure_entry_index") != 0
        or failure_rows[1].get("runtime_hard_failure_entry_index") != 2
        or report.get("universal_failure_core15_cross_producer_parity")
        is not False
        or report.get("runtime_success_whole_output17_target_exact") is not True
        or report.get("runtime_failure_whole_output17_target_exact") is not True
        or report.get("negative_matrix_case_count") != len(gate.NEGATIVE_CASES)
        or report.get("negative_matrix_all_rejected") is not True
        or type(readiness) is not dict
        or readiness.get("ready_for_output17_lightweight_semantic_parity_probe")
        is not True
        or readiness.get("ready_for_remap_hot_loop_contract_gate") is not False
        or readiness.get("current_adapter_directly_accepts_successor_exact6")
        is not False
        or readiness.get("current_compiler_context_uses_successor_authority")
        is not False
        or readiness.get("compiler_context_rebuild_device_identity_risk")
        is not True
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        _fail()
    return report


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    repository = _root(arguments.repo_root)
    state = _root(arguments.state_root)
    _static_product_validation(repository)
    lifecycle = _repository_lifecycle(repository)
    before = _snapshot(repository, state)
    first = gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
        repo_root=repository,
        state_root=state,
    )
    second = gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
        repo_root=repository,
        state_root=state,
    )
    if first != second:
        _fail()
    report = _verify_artifacts(first, lifecycle=lifecycle)
    if _snapshot(repository, state) != before:
        _fail()
    readiness = report["readiness"]
    summary = {
        "status": gate.GATE_STATUS,
        "repository_lifecycle": lifecycle,
        "artifact_file_count": len(gate.ARTIFACT_NAMES),
        "stable_contract_digest": _manual_digest(first),
        "public_gate_build_count": 2,
        "double_build_byte_identical": True,
        "reviewed_evidence_identity_count": len(gate.REVIEWED_EVIDENCE_SPECS),
        "production_owner_identity_count": len(gate.OWNER_SPECS),
        "frozen_helper_signature_count": gate.FROZEN_HELPER_SIGNATURE_COUNT,
        "pure_success_case_count": report["pure_success_case_count"],
        "pure_failure_case_count": report["pure_failure_case_count"],
        "negative_matrix_case_count": report["negative_matrix_case_count"],
        "repository_and_reviewed_evidence_unchanged": True,
        "ready_for_output17_lightweight_semantic_parity_probe": readiness[
            "ready_for_output17_lightweight_semantic_parity_probe"
        ],
        "ready_for_remap_hot_loop_contract_gate": readiness[
            "ready_for_remap_hot_loop_contract_gate"
        ],
        "feature_semantics_reaudit_required_before_training": readiness[
            "feature_semantics_reaudit_required_before_training"
        ],
        "ready_for_training": readiness["ready_for_training"],
    }
    if (
        summary["ready_for_output17_lightweight_semantic_parity_probe"] is not True
        or summary["ready_for_remap_hot_loop_contract_gate"] is not False
        or summary["feature_semantics_reaudit_required_before_training"] is not True
        or summary["ready_for_training"] is not False
    ):
        _fail()
    print(
        json.dumps(
            summary,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _main(argv)
    except Exception:
        print(_ERROR, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

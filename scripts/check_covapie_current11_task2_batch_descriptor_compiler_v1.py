#!/usr/bin/env python3
"""Check the pure in-memory Current11 Task 2 batch descriptor compiler V1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NoReturn, Sequence

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as gate
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter
from covalent_ext.covapie_current11_task2_batch_descriptor_compiler_v1 import (
    compile_covapie_current11_task2_batch_descriptor_v1,
)


_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR"
_CONTRACT_COMMIT = "3b390cec784ed73a72f522145b6f26e3d8af704d"
_CONTRACT_DIGEST = "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
_VECTORS = "current11_task2_batch_descriptor_compiler_reference_vectors.json"
_OUTPUT = "current11_task2_batch_index_remap_output.json"
_REPORT = "current11_task2_batch_index_remap_adapter_report.json"
_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_v1_guide.md",
)
_FORMAL_PATHS = (
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1",
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1",
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _json(payload: bytes) -> dict[str, object]:
    value = json.loads(
        payload.decode("utf-8"),
        parse_constant=lambda _value: (_ for _ in ()).throw(ValueError(_ERROR)),
    )
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(base: dict[str, object], order: Sequence[int], joint: str | None) -> dict[str, object]:
    ligand = [base["ligand_lengths"][index] for index in order]
    pocket = [base["pocket_lengths"][index] for index in order]
    return {
        "schema_version": base["schema_version"],
        "runtime_batch_schema_version": base["runtime_batch_schema_version"],
        "sample_key_schema_version": base["sample_key_schema_version"],
        "batch_sample_keys": [base["batch_sample_keys"][index] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": base["virtual_node_policy"],
        "receptors": [base["receptors"][index] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand), "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket), "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


@contextmanager
def _gate_compatibility() -> Iterator[None]:
    owner = gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            allowed = {f"?? {path}" for path in _EXACT4}
            lines = output.splitlines()
            if any(len(line) >= 4 and line[3:] in _EXACT4 and line not in allowed for line in lines):
                raise ValueError(_ERROR)
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


@contextmanager
def _adapter_compatibility() -> Iterator[None]:
    owner = adapter._projection_contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in _EXACT4}
            lines = output.splitlines()
            if any(len(line) >= 4 and line[3:] in _EXACT4 and line not in allowed for line in lines):
                raise ValueError(_ERROR)
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        text=True, encoding="utf-8", errors="strict",
    )
    if completed.returncode != 0 or completed.stderr:
        raise ValueError(_ERROR)
    return completed.stdout


def _tree_snapshot(path: Path) -> str:
    digest = hashlib.sha256(b"COVAPIE_COMPILER_CHECKER_TREE_SNAPSHOT_V1\0")
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


def _normalize_expected(output: dict[str, object]) -> dict[str, object]:
    output_fields = (
        "schema_version", "compiler_status", "failure_reason", "adapter_input_exact18",
        "batch_sample_key_outcomes", "source_contract_digest", "identity_provider_digest",
        "runtime_schema_binding", "provenance", "readiness",
    )
    exact18_fields = (
        "schema_version", "source_projection_digest", "source_payload_digest",
        "parser_schema_version", "collate_schema_version", "source_sample_order",
        "source_pair_values_int64", "source_sample_offsets_int64",
        "source_entry_validity_bool", "source_sample_validity_bool", "batch_sample_order",
        "batch_sample_atom_identity_tables", "batch_role_lengths", "batch_role_offsets",
        "batch_membership_masks", "joint_layout_descriptor", "debug_coordinates",
        "debug_rank_metadata",
    )
    normalized = {field: copy.deepcopy(output[field]) for field in output_fields}
    if type(normalized["adapter_input_exact18"]) is dict:
        raw_exact18 = normalized["adapter_input_exact18"]
        normalized["adapter_input_exact18"] = {
            field: raw_exact18[field] for field in exact18_fields
        }
    normalized["provenance"] = {
        "contract_evaluator_only": False,
        "compiler_implemented": True,
        "runtime_extractor_implemented": False,
        "remap_executed_by_compiler": False,
        "compiler_contract_commit": _CONTRACT_COMMIT,
        "compiler_contract_digest": _CONTRACT_DIGEST,
    }
    normalized["readiness"]["task2_batch_descriptor_compiler_implemented"] = True
    normalized["readiness"]["ready_for_task2_batch_descriptor_compiler_implementation"] = False
    return normalized


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    repo = namespace.repo_root
    state = namespace.state_root

    git_before = (
        _run_git(repo, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo, ("diff", "--cached", "--name-status")),
        _run_git(repo, ("rev-parse", "HEAD")),
        _run_git(repo, ("rev-parse", "origin/main")),
    )
    formal_before = tuple(_tree_snapshot(state / relative) for relative in _FORMAL_PATHS)
    with _gate_compatibility():
        exact6 = gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
            repo_root=repo, state_root=state,
        )
    vectors = _json(exact6[_VECTORS])
    cases = vectors.get("reference_cases")
    base = vectors.get("canonical_runtime_observation")
    if type(cases) is not list or len(cases) != 35 or type(base) is not dict:
        raise ValueError(_ERROR)
    by_id = {row.get("case_id"): row for row in cases if type(row) is dict}

    success_specs = (
        ("canonical_exact11", list(range(11)), "ligand_segment_then_pocket_segment_v1"),
        ("reversed_exact11", list(reversed(range(11))), "ligand_segment_then_pocket_segment_v1"),
        ("mixed_10_4_0_7_2", [10, 4, 0, 7, 2], "ligand_segment_then_pocket_segment_v1"),
        ("subset_10_4_0", [10, 4, 0], "ligand_segment_then_pocket_segment_v1"),
        ("no_joint", list(range(11)), None),
        ("empty_batch", [], "ligand_segment_then_pocket_segment_v1"),
    )
    compiled: dict[str, dict[str, object]] = {}
    parity_checked = 0
    for case_id, order, joint in success_specs:
        output = compile_covapie_current11_task2_batch_descriptor_v1(
            repo_root=repo, state_root=state, observation=_observation(base, order, joint),
        )
        expected = by_id[case_id]["compiler_output"]
        if list(output.items()) != list(_normalize_expected(expected).items()):
            raise ValueError(_ERROR)
        compiled[case_id] = output
        parity_checked += 1

    wrong = _observation(base, [10, 4, 0], "ligand_segment_then_pocket_segment_v1")
    wrong["ligand_lengths"] = [22, 28, 13]
    duplicate = _observation(base, [10, 4, 0], "ligand_segment_then_pocket_segment_v1")
    duplicate["batch_sample_keys"] = [base["batch_sample_keys"][10]] * 3
    for case_id, observation in (("wrong_ligand_length", wrong), ("duplicate_runtime_key", duplicate)):
        output = compile_covapie_current11_task2_batch_descriptor_v1(
            repo_root=repo, state_root=state, observation=observation,
        )
        if list(output.items()) != list(_normalize_expected(by_id[case_id]["compiler_output"]).items()):
            raise ValueError(_ERROR)
        parity_checked += 1

    composition_count = 0
    empty_compatible = False
    no_joint_compatible = False
    for case_id, _order, _joint in success_specs:
        with _adapter_compatibility():
            exact2 = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
                repo_root=repo, state_root=state,
                adapter_input=copy.deepcopy(compiled[case_id]["adapter_input_exact18"]),
            )
        remap = _json(exact2[_OUTPUT])
        adapter_report = _json(exact2[_REPORT])
        if (
            remap.get("remap_status") != "REMAPPED_EXACT"
            or remap.get("failure_reason") != "NONE"
            or adapter_report.get("adapter_status") != "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
        ):
            raise ValueError(_ERROR)
        composition_count += 1
        if case_id == "empty_batch":
            empty_compatible = remap.get("pair_values_batch_indices") == []
        if case_id == "no_joint":
            no_joint_compatible = remap.get("pair_values_joint_global_indices") is None

    git_after = (
        _run_git(repo, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo, ("diff", "--cached", "--name-status")),
        _run_git(repo, ("rev-parse", "HEAD")),
        _run_git(repo, ("rev-parse", "origin/main")),
    )
    formal_after = tuple(_tree_snapshot(state / relative) for relative in _FORMAL_PATHS)
    readiness = compiled["canonical_exact11"].get("readiness")
    result = {
        "status": "PASS_IN_MEMORY_TASK2_BATCH_DESCRIPTOR_COMPILER_ONLY",
        "compiler_contract_commit": _CONTRACT_COMMIT,
        "compiler_contract_digest": _CONTRACT_DIGEST,
        "reference_parity": {
            "published_reference_count": 35,
            "direct_runtime_cases_checked": parity_checked,
            "direct_runtime_cases_matched": parity_checked,
        },
        "success_cases_checked": 6,
        "hard_failure_cases_checked": 2,
        "adapter_composition": {"checked": composition_count, "passed": composition_count},
        "empty_batch_adapter_compatible": empty_compatible,
        "no_joint_adapter_compatible": no_joint_compatible,
        "compiler_does_not_execute_remap": True,
        "formal_state_unchanged": formal_after == formal_before,
        "repository_unchanged": git_after == git_before,
        "readiness": readiness,
    }
    if (
        composition_count != 6 or not empty_compatible or not no_joint_compatible
        or result["formal_state_unchanged"] is not True
        or result["repository_unchanged"] is not True
        or type(readiness) is not dict
        or readiness.get("task2_batch_descriptor_compiler_implemented") is not True
        or readiness.get("runtime_batch_observation_extractor_implemented") is not False
        or readiness.get("ready_for_training") is not False
    ):
        raise ValueError(_ERROR)
    sys.stdout.write(json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit and type(error.code) is int and error.code == 0:
            raise
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1) from None

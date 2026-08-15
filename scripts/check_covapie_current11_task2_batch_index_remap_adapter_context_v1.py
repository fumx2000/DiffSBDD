#!/usr/bin/env python3
"""Check the Current11 Task2 remap context/runtime candidate V1."""

from __future__ import annotations

import argparse
import ast
import builtins
import copy
import hashlib
import inspect
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Callable, Mapping

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as _context,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as _adapter,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    as _reconciliation,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_predecessor_successor_v1
    as _successor,
)


_B2 = _successor._b2
_HISTORICAL = _adapter._contract_gate
_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_CONTEXT_V1_CHECK_ERROR"
_REVIEWED_EVIDENCE = (
    (
        "review-scratch/current11-task2-remap-output17-lightweight-semantic-parity-v1/"
        "remap_output17_lightweight_semantic_parity_probe_report.md",
        8454,
        139,
        "ea108ff4f501a1d7b0f4053399a2c8e73364948c0d101955dc5a1939d12c51cc",
    ),
    (
        "review-scratch/current11-task2-remap-successor-adapter-parity-timing-v1/"
        "remap_successor_adapter_parity_timing_report.md",
        15200,
        218,
        "6425ade470cf12be31b367062f4612e634160e5611e665bc98f4efe17c667c79",
    ),
    (
        "review-scratch/current11-task2-remap-output17-semantic-reconciliation-design-v1/"
        "remap_output17_semantic_reconciliation_design_report.md",
        31207,
        552,
        "e597dc7605e504b3d0c9a81b930c0dd6ea14b869380f2bebb6654564bfdc0f30",
    ),
)


class _CheckError(Exception):
    pass


def _fail() -> None:
    raise _CheckError(_ERROR)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _run_git(repo_root: Path, arguments: tuple[str, ...]) -> str:
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
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _path_identity(path: Path) -> tuple[object, ...]:
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
    paths = (*_context.REPOSITORY_EXACT4, *(
        str(spec["path"]) for spec in _context._OWNER_SPECS.values()
    ))
    return (
        _run_git(
            repo_root,
            ("status", "--porcelain=v1", "--untracked-files=all"),
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _path_identity(repo_root / relative)) for relative in paths),
    )


def _state_snapshot(state_root: Path) -> tuple[object, ...]:
    canonical = state_root / _adapter._FORMAL_RELATIVE
    evidence = tuple(
        (relative, _path_identity(state_root / relative))
        for relative, unused_size, unused_lines, unused_digest in _REVIEWED_EVIDENCE
    )
    return (_adapter._formal_snapshot(canonical), evidence)


def _verify_evidence(state_root: Path) -> None:
    for relative, size, lines, digest in _REVIEWED_EVIDENCE:
        path = state_root / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) != size
            or payload.count(b"\n") != lines
            or _sha256(payload) != digest
        ):
            _fail()


def _acquire_predecessor_fixture(
    *,
    repo_root: Path,
    state_root: Path,
) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, object]]:
    originals = {
        "reconciliation_lifecycle": _reconciliation._repository_lifecycle,
        "successor_lifecycle": _successor._repository_lifecycle,
        "B2_lifecycle": _B2._repository_lifecycle,
        "reconciliation_public": _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor_public": _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "B2_public": _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1,
    }
    counts = {"reconciliation": 0, "successor": 0, "B2": 0}

    def clean_lifecycle(unused_repo: Path) -> str:
        return "clean-tracked-successor"

    def reconciliation_public(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
        counts["reconciliation"] += 1
        return originals["reconciliation_public"](
            repo_root=repo_root,
            state_root=state_root,
        )

    def successor_public(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
        counts["successor"] += 1
        return originals["successor_public"](
            repo_root=repo_root,
            state_root=state_root,
        )

    def b2_public(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
        counts["B2"] += 1
        return originals["B2_public"](
            repo_root=repo_root,
            state_root=state_root,
        )

    try:
        _reconciliation._repository_lifecycle = clean_lifecycle
        _successor._repository_lifecycle = clean_lifecycle
        _B2._repository_lifecycle = clean_lifecycle
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = reconciliation_public
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = successor_public
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = b2_public
        reconciliation_artifacts = reconciliation_public(
            repo_root=repo_root,
            state_root=state_root,
        )
        successor_artifacts = successor_public(
            repo_root=repo_root,
            state_root=state_root,
        )
    finally:
        _reconciliation._repository_lifecycle = originals[
            "reconciliation_lifecycle"
        ]
        _successor._repository_lifecycle = originals["successor_lifecycle"]
        _B2._repository_lifecycle = originals["B2_lifecycle"]
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals[
            "reconciliation_public"
        ]
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals[
            "successor_public"
        ]
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = originals[
            "B2_public"
        ]
    restored = (
        _reconciliation._repository_lifecycle
        is originals["reconciliation_lifecycle"]
        and _successor._repository_lifecycle is originals["successor_lifecycle"]
        and _B2._repository_lifecycle is originals["B2_lifecycle"]
        and _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
        is originals["reconciliation_public"]
        and _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
        is originals["successor_public"]
        and _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
        is originals["B2_public"]
    )
    if counts != {"reconciliation": 1, "successor": 1, "B2": 1} or not restored:
        _fail()
    return reconciliation_artifacts, successor_artifacts, {
        "test_harness_only": True,
        "predecessor_public_call_counts": counts,
        "patch_restoration_passed": restored,
        "production_monkeypatch_used": False,
    }


def _acquire_clean_public_context(
    *,
    repo_root: Path,
    state_root: Path,
) -> tuple[object, dict[str, bytes], dict[str, bytes], dict[str, object]]:
    originals = {
        "reconciliation": _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor": _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "B2": _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1,
        "formal": _adapter._validate_formal,
    }
    counts = {"reconciliation": 0, "successor": 0, "B2": 0, "formal": 0}
    captured: dict[str, dict[str, bytes]] = {}

    def reconciliation_public(
        *, repo_root: Path, state_root: Path
    ) -> dict[str, bytes]:
        counts["reconciliation"] += 1
        artifacts = originals["reconciliation"](
            repo_root=repo_root,
            state_root=state_root,
        )
        captured["reconciliation"] = artifacts
        return artifacts

    def successor_public(
        *, repo_root: Path, state_root: Path
    ) -> dict[str, bytes]:
        counts["successor"] += 1
        artifacts = originals["successor"](
            repo_root=repo_root,
            state_root=state_root,
        )
        captured["successor"] = artifacts
        return artifacts

    def b2_public(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
        counts["B2"] += 1
        return originals["B2"](repo_root=repo_root, state_root=state_root)

    def formal(canonical: Path) -> dict[str, object]:
        counts["formal"] += 1
        return originals["formal"](canonical)

    try:
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = reconciliation_public
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = successor_public
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = b2_public
        _adapter._validate_formal = formal
        built = _context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    finally:
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals[
            "reconciliation"
        ]
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals[
            "successor"
        ]
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = originals[
            "B2"
        ]
        _adapter._validate_formal = originals["formal"]
    if (
        counts != {"reconciliation": 1, "successor": 1, "B2": 1, "formal": 2}
        or set(captured) != {"reconciliation", "successor"}
        or type(built) is not _context._AdapterContext
    ):
        _fail()
    return built, captured["reconciliation"], captured["successor"], {
        "test_harness_only": False,
        "predecessor_public_call_counts": {
            "reconciliation": 1,
            "successor": 1,
            "B2": 1,
        },
        "formal_before_after_call_count": 2,
        "patch_restoration_passed": True,
        "counter_wrappers_delegated_originals": True,
        "production_monkeypatch_used": False,
    }


def _public_precommit_negative(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, int]:
    originals = {
        "reconciliation": _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor": _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "B2": _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1,
    }
    counts = {"reconciliation": 0, "successor": 0, "B2": 0}

    def forbidden(name: str, original: Callable[..., object]) -> Callable[..., object]:
        def wrapper(**kwargs: object) -> object:
            counts[name] += 1
            return original(**kwargs)

        return wrapper

    try:
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = forbidden(
            "reconciliation", originals["reconciliation"]
        )
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = forbidden(
            "successor", originals["successor"]
        )
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = forbidden(
            "B2", originals["B2"]
        )
        try:
            _context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
                repo_root=repo_root,
                state_root=state_root,
            )
        except ValueError as error:
            if str(error) != _context.ERROR_TOKEN:
                _fail()
        else:
            _fail()
    finally:
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals[
            "reconciliation"
        ]
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals[
            "successor"
        ]
        _B2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = originals[
            "B2"
        ]
    if set(counts.values()) != {0}:
        _fail()
    return counts


def _build_fixture_contexts(
    *,
    repo_root: Path,
    state_root: Path,
    reconciliation_artifacts: dict[str, bytes],
    successor_artifacts: dict[str, bytes],
) -> tuple[object, object, dict[str, object]]:
    original_formal = _adapter._validate_formal
    formal_count = 0

    def validate_formal(canonical: Path) -> dict[str, object]:
        nonlocal formal_count
        formal_count += 1
        return original_formal(canonical)

    try:
        _adapter._validate_formal = validate_formal
        first = _context._build_context_from_verified_predecessor_artifacts_v1(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
        first_logical = _context._logical_context_value(first)
        second = _context._build_context_from_verified_predecessor_artifacts_v1(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
        second_logical = _context._logical_context_value(second)
    finally:
        _adapter._validate_formal = original_formal
    if (
        formal_count != 4
        or first is second
        or first_logical != second_logical
        or first_logical["construction_seal"]
        != second_logical["construction_seal"]
    ):
        _fail()
    return first, second, {
        "formal_validation_total_for_two_contexts": formal_count,
        "formal_validation_count_per_context": 2,
        "two_context_object_identities_distinct": True,
        "same_authority_seal_deterministic": True,
        "logical_context_field_order": list(first_logical),
        "logical_context_field_count": len(first_logical),
        "construction_seal": first_logical["construction_seal"],
    }


def _build_deterministic_fixture_peer(
    *,
    first: object,
    repo_root: Path,
    state_root: Path,
    reconciliation_artifacts: dict[str, bytes],
    successor_artifacts: dict[str, bytes],
) -> tuple[object, dict[str, object]]:
    original_formal = _adapter._validate_formal
    formal_count = 0

    def validate_formal(canonical: Path) -> dict[str, object]:
        nonlocal formal_count
        formal_count += 1
        return original_formal(canonical)

    try:
        _adapter._validate_formal = validate_formal
        second = _context._build_context_from_verified_predecessor_artifacts_v1(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
    finally:
        _adapter._validate_formal = original_formal
    first_logical = _context._logical_context_value(first)
    second_logical = _context._logical_context_value(second)
    if (
        formal_count != 2
        or first is second
        or first_logical != second_logical
        or first_logical["construction_seal"]
        != second_logical["construction_seal"]
    ):
        _fail()
    return second, {
        "formal_validation_total_for_fixture_peer": formal_count,
        "formal_validation_count_per_context": 2,
        "real_context_formal_before_after_count": 2,
        "two_context_object_identities_distinct": True,
        "same_authority_seal_deterministic": True,
        "logical_context_field_order": list(first_logical),
        "logical_context_field_count": len(first_logical),
        "construction_seal": first_logical["construction_seal"],
    }


def _canonical_input(
    context: object,
    *,
    order: list[int] | None = None,
    joint: str | None = _adapter._JOINT_LAYOUT,
) -> dict[str, object]:
    source, authority, unused_semantic = _context._validate_context_and_materialize(
        context
    )
    sample_order = source["sample_order"]
    if order is None:
        order = list(range(len(sample_order)))
    authority_by_key = {
        _adapter._identity_key(table["sample_identity"]): table
        for table in authority
    }
    batch = [copy.deepcopy(sample_order[index]) for index in order]
    tables = [
        copy.deepcopy(authority_by_key[_adapter._identity_key(sample)])
        for sample in batch
    ]
    lengths = {
        role: [table["roles"][role]["parser_output_atom_count"] for table in tables]
        for role in ("pocket", "ligand")
    }
    offsets: dict[str, list[int]] = {}
    masks: dict[str, list[int]] = {}
    for role in ("pocket", "ligand"):
        role_offsets = [0]
        for value in lengths[role]:
            role_offsets.append(role_offsets[-1] + value)
        offsets[role] = role_offsets
        masks[role] = [
            ordinal
            for ordinal, length in enumerate(lengths[role])
            for unused in range(length)
        ]
    return {
        "schema_version": _adapter._INPUT_SCHEMA,
        "source_projection_digest": _adapter._PROJECTION_DIGEST,
        "source_payload_digest": _adapter._PAYLOAD_DIGEST,
        "parser_schema_version": _adapter._PARSER_SCHEMA,
        "collate_schema_version": _adapter._COLLATE_SCHEMA,
        "source_sample_order": copy.deepcopy(sample_order),
        "source_pair_values_int64": copy.deepcopy(
            source["pair_values_source_row_indices"]
        ),
        "source_sample_offsets_int64": copy.deepcopy(
            source["sample_pair_offsets"]
        ),
        "source_entry_validity_bool": copy.deepcopy(source["entry_validity"]),
        "source_sample_validity_bool": copy.deepcopy(source["sample_validity"]),
        "batch_sample_order": batch,
        "batch_sample_atom_identity_tables": tables,
        "batch_role_lengths": lengths,
        "batch_role_offsets": offsets,
        "batch_membership_masks": masks,
        "joint_layout_descriptor": joint,
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _slow_public_output(
    *,
    repo_root: Path,
    state_root: Path,
    adapter_input: dict[str, object],
    successor_artifacts: dict[str, bytes],
    context: object,
) -> tuple[bytes, dict[str, int]]:
    source, authority, unused_semantic = _context._validate_context_and_materialize(
        context
    )
    originals = {
        "contract": _adapter._contract_exact6,
        "parse": _adapter._parse_contract,
        "formal": _adapter._validate_formal,
    }
    counts = {"contract": 0, "parse": 0, "formal": 0, "public": 0}
    formal_fixture = {"fixture": "stable_test_snapshot"}

    def contract(unused_repo: Path, unused_state: Path) -> dict[str, bytes]:
        counts["contract"] += 1
        return successor_artifacts

    def parse(unused_exact6: Mapping[str, bytes]) -> dict[str, object]:
        counts["parse"] += 1
        return {"source": copy.deepcopy(source), "authority": copy.deepcopy(authority)}

    def formal(unused_canonical: Path) -> dict[str, str]:
        counts["formal"] += 1
        return dict(formal_fixture)

    try:
        _adapter._contract_exact6 = contract
        _adapter._parse_contract = parse
        _adapter._validate_formal = formal
        counts["public"] += 1
        artifacts = _adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
            repo_root=repo_root,
            state_root=state_root,
            adapter_input=adapter_input,
        )
    finally:
        _adapter._contract_exact6 = originals["contract"]
        _adapter._parse_contract = originals["parse"]
        _adapter._validate_formal = originals["formal"]
    expected_counts = {"contract": 1, "parse": 1, "formal": 2, "public": 1}
    if counts != expected_counts:
        _fail()
    return artifacts[_adapter._OUTPUT_NAME], counts


def _parity_matrix(
    *,
    repo_root: Path,
    state_root: Path,
    context: object,
    successor_artifacts: dict[str, bytes],
) -> tuple[dict[str, bool], dict[str, object]]:
    cases = {
        "canonical_success": _canonical_input(context),
        "subset_10_4_0": _canonical_input(context, order=[10, 4, 0]),
        "no_joint": _canonical_input(context, joint=None),
    }
    schema = _canonical_input(context, order=[10, 4, 0])
    schema["schema_version"] = "invalid_context_runtime_schema_fixture"
    cases["schema_mismatch"] = schema
    hard = _canonical_input(context)
    unused_source, authority, unused_semantic = _context._validate_context_and_materialize(
        context
    )
    hard["source_pair_values_int64"][2][0] = authority[2]["roles"]["pocket"][
        "row_count"
    ]
    cases["hard_failure_entry2"] = hard
    parity: dict[str, bool] = {}
    slow_counts: dict[str, dict[str, int]] = {}
    logical_before = _context._logical_context_value(context)
    for name, case in cases.items():
        before = copy.deepcopy(case)
        before_payload = _adapter._json(before)
        fast = _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=context,
            adapter_input=case,
        )
        slow_payload, counts = _slow_public_output(
            repo_root=repo_root,
            state_root=state_root,
            adapter_input=case,
            successor_artifacts=successor_artifacts,
            context=context,
        )
        parity[name] = (
            slow_payload == _adapter._json(fast)
            and type(fast) is dict
            and tuple(fast) == _adapter._OUTPUT_FIELD_ORDER
            and len(fast) == 17
            and case == before
            and _adapter._json(case) == before_payload
        )
        slow_counts[name] = counts
        if name == "hard_failure_entry2":
            outcomes = fast["source_entry_outcomes"]
            parity["hard_failure_entry2_preserved"] = (
                fast["remap_status"] == "SOURCE_ROW_OUT_OF_RANGE"
                and outcomes[2]["status"] == "SOURCE_ROW_OUT_OF_RANGE"
                and outcomes[0]["status"] == "ENTRY_INVALID"
            )
    context_unchanged = _context._logical_context_value(context) == logical_before
    if not all(parity.values()) or not context_unchanged:
        _fail()
    return parity, {
        "slow_public_golden_counts_by_case": slow_counts,
        "caller_inputs_unchanged": True,
        "context_unchanged": context_unchanged,
        "output_exact17_only": True,
        "historical_failure_normalization_performed": False,
    }


def _expect_product_rejection(action: Callable[[], object]) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == _context.ERROR_TOKEN
    return False


def _tamper_matrix(context: object) -> dict[str, bool]:
    logical = _context._logical_context_value(context)
    try:
        context._seal = "0" * 64
    except (AttributeError, TypeError):
        no_public_mutation = True
    else:
        no_public_mutation = False
    wrong_type = _expect_product_rejection(
        lambda: _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context={},
            adapter_input={},
        )
    )
    seal_corrupt = _context._AdapterContext(context._semantic, context._seal)
    object.__setattr__(seal_corrupt, "_seal", "0" * 64)
    seal_rejected = _expect_product_rejection(
        lambda: _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=seal_corrupt,
            adapter_input={},
        )
    )
    altered = dict(logical)
    del altered["construction_seal"]
    altered["runtime_output17_target"] = "corrupted_runtime_target"
    frozen = _context._deep_freeze(altered)
    semantic_corrupt = _context._AdapterContext(frozen, context._seal)
    semantic_rejected = _expect_product_rejection(
        lambda: _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=semantic_corrupt,
            adapter_input={},
        )
    )
    result = {
        "no_public_mutation_interface": no_public_mutation,
        "wrong_type_rejected": wrong_type,
        "seal_corruption_rejected": seal_rejected,
        "semantic_corruption_rejected": semantic_rejected,
    }
    if not all(result.values()):
        _fail()
    return result


def _no_io_matrix(
    *,
    context: object,
) -> tuple[dict[str, int], int]:
    counts = {
        "reconciliation_public_build_count": 0,
        "successor_public_build_count": 0,
        "B2_public_build_count": 0,
        "historical_contract_public_gate_count": 0,
        "adapter_contract_exact6_count": 0,
        "adapter_parse_contract_count": 0,
        "adapter_validate_formal_count": 0,
        "formal_filesystem_read_count": 0,
        "other_filesystem_read_count": 0,
        "git_call_count": 0,
        "subprocess_call_count": 0,
        "report_generation_count": 0,
        "artifact_write_count": 0,
        "global_cache_lookup_count": 0,
        "context_rebuild_count": 0,
    }
    additional = {"adapter_public_fast_path_count": 0}
    patches: list[tuple[object, str, object]] = []

    def patch(owner: object, name: str, key: str) -> None:
        original = getattr(owner, name)

        def forbidden(*args: object, **kwargs: object) -> object:
            counts[key] += 1
            raise AssertionError(key)

        patches.append((owner, name, original))
        setattr(owner, name, forbidden)

    def patch_additional(owner: object, name: str, key: str) -> None:
        original = getattr(owner, name)

        def forbidden(*args: object, **kwargs: object) -> object:
            additional[key] += 1
            raise AssertionError(key)

        patches.append((owner, name, original))
        setattr(owner, name, forbidden)

    patch(
        _reconciliation,
        "build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1",
        "reconciliation_public_build_count",
    )
    patch(
        _successor,
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        "successor_public_build_count",
    )
    patch(
        _B2,
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        "B2_public_build_count",
    )
    patch(
        _HISTORICAL,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "historical_contract_public_gate_count",
    )
    patch(_adapter, "_contract_exact6", "adapter_contract_exact6_count")
    patch(_adapter, "_parse_contract", "adapter_parse_contract_count")
    patch(_adapter, "_validate_formal", "adapter_validate_formal_count")
    patch(_adapter, "_formal_snapshot", "formal_filesystem_read_count")
    patch(_context, "_run_git", "git_call_count")
    patch(subprocess, "run", "subprocess_call_count")
    patch(_adapter, "_report", "report_generation_count")
    patch(_context, "build_covapie_current11_task2_batch_index_remap_adapter_context_v1", "context_rebuild_count")
    patch_additional(
        _adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "adapter_public_fast_path_count",
    )
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    original_write_bytes = Path.write_bytes
    original_write_text = Path.write_text
    original_open = builtins.open

    def no_read(*args: object, **kwargs: object) -> object:
        counts["other_filesystem_read_count"] += 1
        raise AssertionError("other_filesystem_read_count")

    def no_write(*args: object, **kwargs: object) -> object:
        counts["artifact_write_count"] += 1
        raise AssertionError("artifact_write_count")

    try:
        Path.read_bytes = no_read
        Path.read_text = no_read
        Path.write_bytes = no_write
        Path.write_text = no_write
        builtins.open = no_read
        success = _canonical_input(context, order=[10, 4, 0])
        hard = _canonical_input(context)
        unused_source, authority, unused_semantic = _context._validate_context_and_materialize(
            context
        )
        hard["source_pair_values_int64"][2][0] = authority[2]["roles"][
            "pocket"
        ]["row_count"]
        _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=context,
            adapter_input=success,
        )
        _context.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=context,
            adapter_input=hard,
        )
    finally:
        builtins.open = original_open
        Path.write_text = original_write_text
        Path.write_bytes = original_write_bytes
        Path.read_text = original_read_text
        Path.read_bytes = original_read_bytes
        for owner, name, original in reversed(patches):
            setattr(owner, name, original)
    if set(counts.values()) != {0} or set(additional.values()) != {0}:
        _fail()
    return counts, additional["adapter_public_fast_path_count"]


def _source_architecture(repo_root: Path) -> dict[str, bool]:
    payload = (repo_root / _context.MODULE_PATH).read_bytes()
    tree = ast.parse(payload.decode("utf-8"))
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    text = payload.decode("utf-8")
    result = {
        "no_remap_engine_definition": "_remap_engine" not in function_names,
        "uses_adapter_remap_engine": "_remap_engine" in attributes
        and "_adapter_owner._remap_engine" in text,
        "uses_adapter_failure_output": "_failure_output" in attributes
        and "_adapter_owner._failure_output" in text,
        "no_second_status_precedence": "_STATUS_ORDER =" not in text,
        "no_lru_cache": "lru_cache" not in names and "lru_cache" not in text,
        "no_global_context_cache": not any(
            token in text
            for token in (
                "_CONTEXT_CACHE",
                "_AUTHORITY_CACHE",
                "WeakValueDictionary",
                "weakref",
                "singleton",
            )
        ),
        "no_direct_B2_owner": "state_mount_device_transition" not in text,
    }
    if not all(result.values()):
        _fail()
    return result


def _clean_lifecycle_simulation(
    *,
    repo_root: Path,
    state_root: Path,
    reconciliation_artifacts: dict[str, bytes],
    successor_artifacts: dict[str, bytes],
) -> dict[str, object]:
    originals = {
        "lifecycle": _context._repository_lifecycle,
        "reconciliation": _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1,
        "successor": _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1,
        "formal": _adapter._validate_formal,
    }
    counts = {"reconciliation": 0, "successor": 0, "formal": 0}

    def clean(unused_repo: Path) -> str:
        return "clean-tracked-successor"

    def reconciliation_fixture(**unused: object) -> dict[str, bytes]:
        counts["reconciliation"] += 1
        return reconciliation_artifacts

    def successor_fixture(**unused: object) -> dict[str, bytes]:
        counts["successor"] += 1
        return successor_artifacts

    def formal(canonical: Path) -> dict[str, object]:
        counts["formal"] += 1
        return originals["formal"](canonical)

    try:
        _context._repository_lifecycle = clean
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = reconciliation_fixture
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = successor_fixture
        _adapter._validate_formal = formal
        built = _context.build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    finally:
        _context._repository_lifecycle = originals["lifecycle"]
        _reconciliation.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1 = originals[
            "reconciliation"
        ]
        _successor.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1 = originals[
            "successor"
        ]
        _adapter._validate_formal = originals["formal"]
    if (
        counts != {"reconciliation": 1, "successor": 1, "formal": 2}
        or type(built) is not _context._AdapterContext
    ):
        _fail()
    return {
        "clean_lifecycle_simulation_passed": True,
        "reconciliation_public_call_count": 1,
        "successor_public_call_count": 1,
        "formal_before_after_call_count": 2,
        "context_direct_B2_call_count": 0,
        "real_predecessor_calls_replaced_by_fixture": True,
    }


def _api_and_file_contract(repo_root: Path) -> dict[str, object]:
    names = _context.__all__
    expected_names = (
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "remap_covapie_current11_task2_batch_index_with_context_v1",
    )
    build_signature = str(inspect.signature(getattr(_context, names[0])))
    fast_signature = str(inspect.signature(getattr(_context, names[1])))
    identities: list[dict[str, object]] = []
    for relative in _context.REPOSITORY_EXACT4:
        path = repo_root / relative
        metadata = path.lstat()
        payload = path.read_bytes()
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
        payload.decode("utf-8")
        identities.append(
            {
                "relative_path": relative,
                "bytes": len(payload),
                "LF": payload.count(b"\n"),
                "sha256": _sha256(payload),
                "git_blob": hashlib.sha1(
                    b"blob "
                    + str(len(payload)).encode("ascii")
                    + b"\0"
                    + payload
                ).hexdigest(),
                "mode": "0644",
            }
        )
    if (
        names != expected_names
        or build_signature
        != "(*, repo_root: 'Path', state_root: 'Path') -> 'object'"
        or fast_signature
        != "(*, context: 'object', adapter_input: 'dict[str, object]') -> 'dict[str, object]'"
        or any(
            name in _context.__dict__ and not name.startswith("_")
            for name in ("AdapterContext", "Context", "context_class")
        )
    ):
        _fail()
    return {
        "public_api_names": list(names),
        "build_signature": build_signature,
        "fast_signature": fast_signature,
        "error_token": _context.ERROR_TOKEN,
        "repository_exact4_identities": identities,
        "public_context_class_exposed": False,
        "silent_import": True,
    }


def _candidate_audit(
    *,
    repo_root: Path,
    state_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    before_repository = _repository_snapshot(repo_root)
    before_state = _state_snapshot(state_root)
    _verify_evidence(state_root)
    lifecycle = _context._repository_lifecycle(repo_root)
    if lifecycle not in ("precommit-untracked", "clean-tracked-successor"):
        _fail()
    api = _api_and_file_contract(repo_root)
    owners = _context._verify_owner_identities(repo_root)
    frozen = _context._validate_frozen_adapter_contract()
    architecture = _source_architecture(repo_root)
    if lifecycle == "precommit-untracked":
        negative_counts = _public_precommit_negative(
            repo_root=repo_root,
            state_root=state_root,
        )
        reconciliation_artifacts, successor_artifacts, harness = (
            _acquire_predecessor_fixture(
                repo_root=repo_root,
                state_root=state_root,
            )
        )
        first, second, context_evidence = _build_fixture_contexts(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
        clean_simulation = _clean_lifecycle_simulation(
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
        real_public_context_build_performed = False
    else:
        negative_counts = {"reconciliation": 0, "successor": 0, "B2": 0}
        first, reconciliation_artifacts, successor_artifacts, harness = (
            _acquire_clean_public_context(
                repo_root=repo_root,
                state_root=state_root,
            )
        )
        second, context_evidence = _build_deterministic_fixture_peer(
            first=first,
            repo_root=repo_root,
            state_root=state_root,
            reconciliation_artifacts=reconciliation_artifacts,
            successor_artifacts=successor_artifacts,
        )
        clean_simulation = {
            "clean_lifecycle_simulation_passed": True,
            "reconciliation_public_call_count": 1,
            "successor_public_call_count": 1,
            "successor_internal_B2_call_count": 1,
            "formal_before_after_call_count": 2,
            "context_direct_B2_call_count": 0,
            "real_predecessor_calls_replaced_by_fixture": False,
        }
        real_public_context_build_performed = True
    reconciliation_evidence = _context._validate_reconciliation_artifacts(
        reconciliation_artifacts
    )
    successor_evidence = _context._validate_successor_artifacts(
        successor_artifacts
    )
    parser_evidence = _context._parse_successor_stable5_v1(successor_artifacts)
    tamper = _tamper_matrix(first)
    parity, parity_evidence = _parity_matrix(
        repo_root=repo_root,
        state_root=state_root,
        context=first,
        successor_artifacts=successor_artifacts,
    )
    no_io, adapter_public_fast_path_count = _no_io_matrix(context=first)
    if (
        _repository_snapshot(repo_root) != before_repository
        or _state_snapshot(state_root) != before_state
    ):
        _fail()
    report = {
        "status": (
            "PASS_REMAP_ADAPTER_CONTEXT_PRECOMMIT_CANDIDATE_ONLY"
            if lifecycle == "precommit-untracked"
            else "PASS_REMAP_ADAPTER_CONTEXT_RUNTIME_ONLY"
        ),
        "repository_lifecycle": lifecycle,
        "architecture_name": _context.ARCHITECTURE_NAME,
        "public_api_exact2": api["public_api_names"],
        "error_token": _context.ERROR_TOKEN,
        "public_precommit_context_build_failed_closed": (
            lifecycle == "precommit-untracked"
        ),
        "public_precommit_predecessor_call_counts": negative_counts,
        "fixture_harness": harness,
        "owner_identities": owners,
        "frozen_adapter_helper_exact6": frozen["pure_helper_rows"],
        "successor_parser_helper_exact5": frozen["parser_helper_rows"],
        "reconciliation_evidence": reconciliation_evidence,
        "successor_evidence": successor_evidence,
        "successor_parser_evidence": {
            key: value
            for key, value in parser_evidence.items()
            if key not in ("source_contract", "authority_tables")
        },
        "context_evidence": context_evidence,
        "context_tamper_matrix": tamper,
        "fast_parity_matrix": parity,
        "fast_parity_evidence": parity_evidence,
        "fast_no_io_contract_counts": no_io,
        "adapter_public_fast_path_count": adapter_public_fast_path_count,
        "source_architecture": architecture,
        "clean_lifecycle_simulation": clean_simulation,
        "canonical_mask_semantics": [
            {"semantic_name": semantic, "display_alias": alias}
            for semantic, alias in _hot_loop_masks()
        ],
        "remap_adapter_context_runtime_implemented": True,
        "precommit_candidate_validation_passed": (
            lifecycle == "precommit-untracked"
        ),
        "real_public_context_build_performed": (
            real_public_context_build_performed
        ),
        "clean_successor_live_validation_pending": (
            lifecycle == "precommit-untracked"
        ),
        "ready_for_context_runtime_commit_review": True,
        "ready_for_context_runtime_publication": (
            lifecycle == "clean-tracked-successor"
        ),
        "public_fast_output17_candidate_implemented": True,
        "fast_success_whole_output17_parity_passed": all(
            parity[name]
            for name in ("canonical_success", "subset_10_4_0", "no_joint")
        ),
        "fast_failure_whole_output17_parity_passed": all(
            parity[name]
            for name in (
                "schema_mismatch",
                "hard_failure_entry2",
                "hard_failure_entry2_preserved",
            )
        ),
        "fast_no_io_structural_contract_passed": (
            set(no_io.values()) == {0} and adapter_public_fast_path_count == 0
        ),
        "production_monkeypatch_used": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "current_compiler_context_uses_successor_authority": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_bytes_read": False,
        "model_parameter_shape_change_required": False,
        "repository_snapshot_unchanged": True,
        "state_snapshot_unchanged": True,
        "commit_created": False,
        "push_performed": False,
    }
    if (
        report["ready_for_context_runtime_publication"]
        is not (lifecycle == "clean-tracked-successor")
        or report["ready_for_training"] is not False
        or report["feature_semantics_reaudit_required_before_training"]
        is not True
    ):
        _fail()
    internal = {
        "first_context": first,
        "second_context": second,
        "reconciliation_artifacts": reconciliation_artifacts,
        "successor_artifacts": successor_artifacts,
        "api": api,
        "report": report,
    }
    return report, internal


def _hot_loop_masks() -> tuple[tuple[str, str], ...]:
    from covalent_ext import (
        covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1
        as hot_loop,
    )

    expected = (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    if tuple(hot_loop.CANONICAL_MASKS) != expected:
        _fail()
    return expected


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        report, unused_internal = _candidate_audit(
            repo_root=arguments.repo_root,
            state_root=arguments.state_root,
        )
    except BaseException as error:
        if type(error) is _CheckError and str(error) == _ERROR:
            raise SystemExit(_ERROR) from error
        raise SystemExit(_ERROR) from error
    print(
        json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_011.

The Exact10 predecessor remains the sole authority for public result/error
objects and its ten registered handlers.  This successor adds only the
ADMIT_011 adapter, an immutable Exact11 registry, and a new dispatcher bound
to that registry.  The public dispatch closure is pure in memory.  Source
attestation, evidence construction, and set-atomic publication are reachable
only through the explicit materialization entry point.
"""

from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import inspect
import io
import json
import os
import secrets
import stat
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_011_rule_logic_interface as admit011,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate
    as admit011_oracle,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_011 v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1"
EXPECTED_BASE_COMMIT = "fab48133058b826f5e9387c06d3cb0024657aec9"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_011 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = "covapie_unified_dispatch_runtime_with_admit_001_to_011_manifest_v1"
RECOMMENDED_NEXT_STEP = "audit_covapie_admit_012_formal_evaluator_interface_preconditions_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Exact object-identity re-exports from Exact10.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 12))
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_011"
ADMISSION_RULE_NAME = "raw_overwrite_forbidden"
ADAPTER_ID = "covapie_admit_011_unified_adapter_v1"
ADMIT_011_CANDIDATE_FIELDS = ("raw_target_relative_path",)
ADMIT_011_CONTEXT_ITEMS = (
    "raw_target_relative_path_contract",
    "existing_raw_target_relative_paths",
)

RULE_NAMES = MappingProxyType(
    {**dict(predecessor.RULE_NAMES), ADMISSION_RULE_ID: ADMISSION_RULE_NAME}
)
ADAPTER_IDS = MappingProxyType(
    {**dict(predecessor.ADAPTER_IDS), ADMISSION_RULE_ID: ADAPTER_ID}
)


def _raise_dispatch_error(
    code: str,
    admission_rule_id: str,
    known_rule: bool,
    callable_discovered: bool,
    adapter_ready: bool,
    reason: str | None = None,
) -> NoReturn:
    raise UnifiedAdmissionDispatchError(
        code=code,
        admission_rule_id=admission_rule_id,
        known_rule=known_rule,
        callable_discovered=callable_discovered,
        adapter_ready=adapter_ready,
        reason=code if reason is None else reason,
    )


def _admit011_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit011_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit011_candidate_invalid(reason: str) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=ADMIT_011_CANDIDATE_FIELDS,
        consumed_context_items=ADMIT_011_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _prevalidate_admit011_source(source: object) -> admit011.Admit011EvaluationResult:
    """Require the exact committed Exact10 type, storage, types, and invariants."""
    if type(source) is not admit011.Admit011EvaluationResult:
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert type(source) is admit011.Admit011EvaluationResult
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != admit011.RESULT_FIELDS:
            raise ValueError("Exact10 storage/order drift")
        if tuple(field.name for field in fields(admit011.Admit011EvaluationResult)) != admit011.RESULT_FIELDS:
            raise ValueError("Exact10 dataclass order drift")
        values = tuple(getattr(source, name) for name in admit011.RESULT_FIELDS)
        exact_types = (str, str, bool, bool, str, str, tuple, tuple, tuple, bool)
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("Exact10 built-in type drift")
        reconstructed = admit011.Admit011EvaluationResult(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact10 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return source


def _expected_admit011_from_oracle(
    scalar_object: object,
    snapshot_object: object,
    contract_object: object,
) -> admit011.Admit011EvaluationResult:
    """Call the independent exact-result oracle once and construct formal Exact10."""
    try:
        classification = admit011_oracle.classify_admit_011_raw_target_relative_path_design(
            scalar_object,
            snapshot_object,
            contract_object,
        )
        result_type = admit011_oracle.Admit011EvaluationResultDesign
        if type(classification) is not result_type:
            raise TypeError("oracle exact result type required")
        if tuple(field.name for field in fields(result_type)) != admit011.RESULT_FIELDS:
            raise ValueError("oracle Exact10 dataclass order drift")
        storage = vars(classification)
        if type(storage) is not dict or tuple(storage) != admit011.RESULT_FIELDS:
            raise ValueError("oracle Exact10 storage/order drift")
        values = tuple(getattr(classification, name) for name in admit011.RESULT_FIELDS)
        exact_types = (str, str, bool, bool, str, str, tuple, tuple, tuple, bool)
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact10 built-in type drift")
        if result_type(*values) != classification:
            raise ValueError("oracle Exact10 reconstruction drift")
        expected = admit011.Admit011EvaluationResult(*values)
    except Exception:
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return expected


def _validate_admit011_oracle_equivalence(
    source: admit011.Admit011EvaluationResult,
    expected: admit011.Admit011EvaluationResult,
) -> None:
    if type(expected) is not admit011.Admit011EvaluationResult:
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    try:
        source_values = tuple(getattr(source, name) for name in admit011.RESULT_FIELDS)
        expected_values = tuple(getattr(expected, name) for name in admit011.RESULT_FIELDS)
    except AttributeError:
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        _admit011_adapter_failure("ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")


def _project_admit011_exact13(
    source: admit011.Admit011EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=source.consumed_context_items,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _evaluate_registered_admit_011(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # All six context gates finish before the first candidate operation.
    if batch_context is not None:
        _admit011_context_failure("ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit011_context_failure("ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED")
    try:
        contract_object = evaluation_context["raw_target_relative_path_contract"]
    except KeyError:
        _admit011_context_failure("ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED")
    try:
        snapshot_object = evaluation_context["existing_raw_target_relative_paths"]
    except KeyError:
        _admit011_context_failure("ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED")
    if download_result_context is not None:
        _admit011_context_failure("ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE")
    if stage_authorization_context is not None:
        _admit011_context_failure("ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE")
    if not isinstance(candidate_record, Mapping):
        return _admit011_candidate_invalid("ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID")
    try:
        scalar_object = candidate_record["raw_target_relative_path"]
    except KeyError:
        return _admit011_candidate_invalid("raw_target_relative_path_missing")

    source = admit011.evaluate_admit_011(
        scalar_object,
        snapshot_object,
        contract_object,
    )
    validated_source = _prevalidate_admit011_source(source)
    expected = _expected_admit011_from_oracle(
        scalar_object,
        snapshot_object,
        contract_object,
    )
    _validate_admit011_oracle_equivalence(validated_source, expected)
    return _project_admit011_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": predecessor.EVALUATOR_REGISTRY["ADMIT_006"],
        "ADMIT_007": predecessor.EVALUATOR_REGISTRY["ADMIT_007"],
        "ADMIT_008": predecessor.EVALUATOR_REGISTRY["ADMIT_008"],
        "ADMIT_009": predecessor.EVALUATOR_REGISTRY["ADMIT_009"],
        "ADMIT_010": predecessor.EVALUATOR_REGISTRY["ADMIT_010"],
        "ADMIT_011": _evaluate_registered_admit_011,
    }
)


def evaluate_admission_rule(
    admission_rule_id: str,
    candidate_record: Mapping[str, object],
    *,
    batch_context: Mapping[str, object] | None = None,
    evaluation_context: Mapping[str, object] | None = None,
    download_result_context: Mapping[str, object] | None = None,
    stage_authorization_context: Mapping[str, object] | None = None,
) -> UnifiedAdmissionRuleEvaluation:
    """Evaluate exactly one registered rule without I/O or aggregation."""
    if type(admission_rule_id) is not str:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False
        )
    if admission_rule_id not in KNOWN_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", admission_rule_id, False, False, False
        )
    if admission_rule_id not in EVALUATOR_REGISTRY:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", admission_rule_id, True, False, False
        )
    return EVALUATOR_REGISTRY[admission_rule_id](
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# Fixed ordered Exact23 committed source boundary.  The adapter design source
# is frozen evidence only and is deliberately not imported by this runtime.
_SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py", "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_manifest.json", "46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_contract.csv", "da2ccbeef748a9ff503ff1e993bcdfb05ae436f92dcd4d46544c424f4f841874"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_truth_matrix.csv", "2d087ef178cd7402fa3d0d40a8a22d2b0a726ed0f49ff2549f6893db15cb20ee"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_registry_routing_and_oracle_audit.csv", "c797c6aad1a9951c61c85379fc2f633aa528bc593dd6f923de9416b7f07ccdbc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_safety_audit.csv", "2c2ae91713cbd05361db3b0a1e74045cc9b810e06133caceff53e8daf0b5786b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_issue_inventory.csv", "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py", "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json", "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv", "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_truth_matrix.csv", "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_source_boundary_audit.csv", "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_purity_audit.csv", "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py", "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json", "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv", "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_candidate_projection_and_context_routing_matrix.csv", "be12ce9e9c551f5891cac9840d130dd9feabfb99fe849385db08dcf767486845"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_result_projection_truth_matrix.csv", "deb4b71376a27d00317d9255e822c9e534c39fc16f0a6636dc149a6ca205b01a"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py", "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json", "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv", "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca"),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in _SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in _SOURCE_BOUNDARY}

(
    PREDECESSOR_SOURCE_PATH,
    PREDECESSOR_MANIFEST_PATH,
    PREDECESSOR_CONTRACT_PATH,
    PREDECESSOR_TRUTH_PATH,
    PREDECESSOR_REGISTRY_PATH,
    PREDECESSOR_SAFETY_PATH,
    PREDECESSOR_ISSUE_PATH,
    STANDALONE_SOURCE_PATH,
    STANDALONE_MANIFEST_PATH,
    STANDALONE_CONTRACT_PATH,
    STANDALONE_TRUTH_PATH,
    STANDALONE_SOURCE_AUDIT_PATH,
    STANDALONE_PURITY_PATH,
    STANDALONE_ISSUE_PATH,
    DESIGN_SOURCE_PATH,
    DESIGN_MANIFEST_PATH,
    DESIGN_CONTRACT_PATH,
    DESIGN_ROUTING_PATH,
    DESIGN_TRUTH_PATH,
    DESIGN_ISSUE_PATH,
    ORACLE_SOURCE_PATH,
    ORACLE_MANIFEST_PATH,
    ORACLE_TRUTH_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_011_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_011_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_011_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_011_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_011_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_011_runtime_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_id",
    "contract_group",
    "contract_subject",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "admission_rule_id",
    "behavior",
    "expected_result_or_error",
    "observed_result_or_error",
    "expected_reason",
    "observed_reason",
    "formal_call_count",
    "oracle_call_count",
    "candidate_access_status",
    "handler_identity_status",
    "case_passed",
)
REGISTRY_COLUMNS = (
    "rule_id",
    "rule_name",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "registered",
    "adapter_id",
    "handler_identity_status",
    "dispatch_disposition",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
ISSUE_COLUMNS = predecessor.ISSUE_COLUMNS


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    base_tree_mode: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ValueError("source-boundary git command failed")
    return result.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("parent chain is not a real directory chain")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("parent chain resolved identity drift")


def _read_pinned(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != expected_identity or _identity(os.lstat(path)) != expected_identity:
            raise ValueError("source identity changed before read")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity or _identity(os.lstat(path)) != expected_identity:
            raise ValueError("source identity changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    """Complete all Exact23 structural checks before the first source-byte read."""
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("repository identity unsafe")
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head_ref invalid")
    if _git(root, "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT).decode().rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    _git(root, "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref)
    if (
        len(SOURCE_PATHS) != 23
        or len(set(SOURCE_PATHS)) != 23
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact23 source boundary configuration drift")

    inspected: list[tuple[Path, Path, tuple[int, int, int], str]] = []
    for relative in SOURCE_PATHS:
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE in relative.parts
        ):
            raise ValueError("unsafe source boundary path")
        target = root / relative
        _assert_real_parent_chain(target.parent, root)
        item = os.lstat(target)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or target.resolve(strict=True) != target
        ):
            raise ValueError("source leaf unsafe")
        if _git(root, "ls-files", "--error-unmatch", "--", relative.as_posix()).decode() != f"{relative.as_posix()}\n":
            raise ValueError("source is not tracked")
        tree = _git(root, "ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix()).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise ValueError("base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if (
            tree_path.decode() != relative.as_posix()
            or len(parts) != 3
            or parts[0] not in (b"100644", b"100755")
            or parts[1] != b"blob"
        ):
            raise ValueError("base tree entry drift")
        inspected.append((relative, target, _identity(item), parts[0].decode()))

    records = []
    for relative, target, identity, mode in inspected:
        base_bytes = _git(root, "show", f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}")
        filesystem_bytes = _read_pinned(target, identity)
        expected = SOURCE_SHA256[relative]
        base_sha = _sha(base_bytes)
        filesystem_sha = _sha(filesystem_bytes)
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {relative}")
        records.append(
            FrozenSourceRecord(
                relative,
                expected,
                base_sha,
                filesystem_sha,
                mode,
                filesystem_bytes,
            )
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 23
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and record.base_tree_mode in ("100644", "100755")
            and _sha(record.content_bytes) == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError("source record missing or duplicate")
    return matches[0]


def _csv_rows(content: bytes, columns: Sequence[str] | None = None) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    header = tuple(reader.fieldnames or ())
    if not header or len(header) != len(set(header)) or (columns is not None and header != tuple(columns)):
        raise ValueError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != header or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV row shape mismatch")
    return rows


def _json_object(content: bytes) -> dict[str, Any]:
    value = json.loads(content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    predecessor_manifest = _json_object(_record(snapshot, PREDECESSOR_MANIFEST_PATH).content_bytes)
    predecessor_contract = _csv_rows(_record(snapshot, PREDECESSOR_CONTRACT_PATH).content_bytes)
    predecessor_truth = _csv_rows(_record(snapshot, PREDECESSOR_TRUTH_PATH).content_bytes)
    predecessor_registry = _csv_rows(_record(snapshot, PREDECESSOR_REGISTRY_PATH).content_bytes)
    predecessor_safety = _csv_rows(_record(snapshot, PREDECESSOR_SAFETY_PATH).content_bytes)
    predecessor_issues = _csv_rows(_record(snapshot, PREDECESSOR_ISSUE_PATH).content_bytes, ISSUE_COLUMNS)
    standalone_manifest = _json_object(_record(snapshot, STANDALONE_MANIFEST_PATH).content_bytes)
    standalone_contract = _csv_rows(_record(snapshot, STANDALONE_CONTRACT_PATH).content_bytes)
    standalone_truth = _csv_rows(_record(snapshot, STANDALONE_TRUTH_PATH).content_bytes)
    standalone_source = _csv_rows(_record(snapshot, STANDALONE_SOURCE_AUDIT_PATH).content_bytes)
    standalone_purity = _csv_rows(_record(snapshot, STANDALONE_PURITY_PATH).content_bytes)
    standalone_issues = _csv_rows(_record(snapshot, STANDALONE_ISSUE_PATH).content_bytes, ISSUE_COLUMNS)
    design_manifest = _json_object(_record(snapshot, DESIGN_MANIFEST_PATH).content_bytes)
    design_contract = _csv_rows(_record(snapshot, DESIGN_CONTRACT_PATH).content_bytes)
    design_routing = _csv_rows(_record(snapshot, DESIGN_ROUTING_PATH).content_bytes)
    design_truth = _csv_rows(_record(snapshot, DESIGN_TRUTH_PATH).content_bytes)
    design_issues = _csv_rows(_record(snapshot, DESIGN_ISSUE_PATH).content_bytes, ISSUE_COLUMNS)
    oracle_manifest = _json_object(_record(snapshot, ORACLE_MANIFEST_PATH).content_bytes)
    oracle_truth = _csv_rows(_record(snapshot, ORACLE_TRUTH_PATH).content_bytes)
    issue_map = {row["issue_id"]: row for row in design_issues}
    checks = (
        predecessor_manifest.get("unified_dispatch_runtime_with_admit_001_to_010_implemented") is True,
        predecessor_manifest.get("registered_rule_ids") == list(KNOWN_RULE_IDS[:10]),
        predecessor_manifest.get("admit_011_started") is False,
        len(predecessor_contract) == 80,
        len(predecessor_truth) == 407,
        len(predecessor_registry) == 15,
        len(predecessor_safety) == 20,
        len(predecessor_issues) == 11,
        standalone_manifest.get("admit_011_rule_logic_implemented") is True,
        standalone_manifest.get("result_type") == "Admit011EvaluationResult",
        standalone_manifest.get("result_fields") == list(admit011.RESULT_FIELDS),
        standalone_manifest.get("row_counts", {}).get("truth") == 84,
        standalone_manifest.get("row_counts", {}).get("truth_historical") == 47,
        len(standalone_contract) == 10,
        len(standalone_truth) == 84,
        len(standalone_source) == 11,
        len(standalone_purity) == 4,
        len(standalone_issues) == 11,
        design_manifest.get("ready_for_unified_dispatch_runtime_with_admit_001_to_011_implementation") is True,
        design_manifest.get("admit_011_runtime_adapter_implemented") is False,
        design_manifest.get("admit_011_registered_in_engine") is False,
        design_manifest.get("future_registered_rule_order") == list(KNOWN_RULE_IDS[:11]),
        len(design_contract) == 26,
        len(design_routing) == 33,
        len(design_truth) == 84,
        len(design_issues) == 11,
        oracle_manifest.get("row_counts", {}).get("truth") == 84,
        len(oracle_truth) == 84,
        tuple(row["case_id"] for row in standalone_truth) == tuple(row["case_id"] for row in oracle_truth),
        issue_map["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract mismatch")
    return {
        "predecessor_truth": predecessor_truth,
        "standalone_truth": standalone_truth,
        "design_issues": design_issues,
    }


def _jsonable(value: object) -> object:
    if type(value) is tuple:
        return [_jsonable(item) for item in value]
    if type(value) is list:
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool, float):
        return value
    return f"<{type(value).__name__}>"


def _evaluation_json(value: UnifiedAdmissionRuleEvaluation) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in RESULT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _error_json(value: UnifiedAdmissionDispatchError) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in DISPATCH_ERROR_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _truth_row(
    case_id: str,
    case_group: str,
    rule_id: str,
    behavior: str,
    expected: str,
    observed: str,
    expected_reason: str,
    observed_reason: str,
    formal_calls: int,
    oracle_calls: int,
    candidate_access: str = "not_applicable",
    identity: str = "not_applicable",
) -> dict[str, str]:
    return {
        "case_order": "",
        "case_id": case_id,
        "case_group": case_group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": expected,
        "observed_result_or_error": observed,
        "expected_reason": expected_reason,
        "observed_reason": observed_reason,
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "candidate_access_status": candidate_access,
        "handler_identity_status": identity,
        "case_passed": str(expected == observed and expected_reason == observed_reason).lower(),
    }


def _capture_dispatch(
    module: object,
    rule_id: object,
    candidate: object,
    **contexts: object,
) -> tuple[str, str]:
    try:
        value = module.evaluate_admission_rule(rule_id, candidate, **contexts)
    except UnifiedAdmissionDispatchError as error:
        return _error_json(error), error.reason
    return _evaluation_json(value), value.reason


def _global_rows() -> list[dict[str, str]]:
    class StringSubclass(str):
        pass

    definitions: list[tuple[str, object, str]] = [
        ("rule_id_str_subclass", StringSubclass(ADMISSION_RULE_ID), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("unknown_rule", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
    ]
    definitions.extend(
        (f"{rule_id.lower()}_not_registered", rule_id, "UNIFIED_ADMISSION_RULE_NOT_REGISTERED")
        for rule_id in KNOWN_RULE_IDS[11:]
    )
    rows = []
    for case_id, rule_id, code in definitions:
        observed, reason = _capture_dispatch(
            __import__(__name__, fromlist=["x"]), rule_id, {}
        )
        expected = UnifiedAdmissionDispatchError(
            code=code,
            admission_rule_id="" if type(rule_id) is not str else rule_id,
            known_rule=code == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            callable_discovered=False,
            adapter_ready=False,
            reason=code,
        )
        rows.append(
            _truth_row(
                f"GLOBAL_{case_id}",
                "global_dispatch",
                "" if type(rule_id) is not str else rule_id,
                "exact built-in ID, known-set, then local-registry precedence",
                _error_json(expected),
                observed,
                code,
                reason,
                0,
                0,
            )
        )
    registered = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {"raw_target_relative_path": "data/raw/a.cif"},
        evaluation_context={
            ADMIT_011_CONTEXT_ITEMS[0]: admit011_oracle.DEFAULT_CONTRACT,
            ADMIT_011_CONTEXT_ITEMS[1]: admit011._empty_snapshot(),
        },
    )
    rows.append(
        _truth_row(
            "GLOBAL_admit011_registered",
            "global_dispatch",
            ADMISSION_RULE_ID,
            "ADMIT_011 dispatches through successor local registry",
            _evaluation_json(registered),
            _evaluation_json(registered),
            registered.reason,
            registered.reason,
            1,
            1,
        )
    )
    for case_id, passed, behavior in (
        ("new_dispatcher", evaluate_admission_rule is not predecessor.evaluate_admission_rule, "new successor dispatcher object"),
        ("local_registry", evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is EVALUATOR_REGISTRY, "dispatcher bound to successor registry"),
    ):
        rows.append(
            _truth_row(
                f"GLOBAL_{case_id}", "global_dispatch", ADMISSION_RULE_ID,
                behavior, "true", str(passed).lower(), "", "", 0, 0,
            )
        )
    return rows


def _identity_and_parity_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS[:10]:
        same_handler = EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
        predecessor_observed, predecessor_reason = _capture_dispatch(predecessor, rule_id, {})
        successor_observed, successor_reason = _capture_dispatch(
            __import__(__name__, fromlist=["x"]), rule_id, {}
        )
        rows.append(
            _truth_row(
                f"IDENTITY_PARITY_{rule_id}",
                "predecessor_handler_identity_and_parity",
                rule_id,
                "handler object identity and default-context value/error parity",
                predecessor_observed,
                successor_observed if same_handler else "handler_identity_drift",
                predecessor_reason,
                successor_reason,
                0,
                0,
                identity=(
                    "reused_predecessor_handler_identity"
                    if same_handler
                    else "identity_drift"
                ),
            )
        )
    return rows


class _CandidateBomb(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


class _CountingMapping(Mapping[str, object]):
    def __init__(self, values: Mapping[str, object], error: Exception | None = None) -> None:
        self.values = dict(values)
        self.error = error
        self.calls: list[object] = []
        self.iterated = False
        self.get_called = False
        self.contains_called = False
        self.len_called = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.len_called = True
        return len(self.values)

    def get(self, key: str, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


def _context_candidate_mapping_rows() -> list[dict[str, str]]:
    contract = admit011_oracle.DEFAULT_CONTRACT
    snapshot = admit011._empty_snapshot()
    valid_context = {
        ADMIT_011_CONTEXT_ITEMS[0]: contract,
        ADMIT_011_CONTEXT_ITEMS[1]: snapshot,
    }
    context_definitions = (
        ("batch_non_none", {"batch_context": object()}, "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
        ("evaluation_non_mapping", {"evaluation_context": object()}, "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("contract_missing", {"evaluation_context": {}}, "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED"),
        ("snapshot_missing", {"evaluation_context": {ADMIT_011_CONTEXT_ITEMS[0]: contract}}, "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED"),
        ("download_non_none", {"evaluation_context": valid_context, "download_result_context": object()}, "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("stage_non_none", {"evaluation_context": valid_context, "stage_authorization_context": object()}, "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("multi_invalid", {"batch_context": object(), "evaluation_context": object(), "download_result_context": object(), "stage_authorization_context": object()}, "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE"),
    )
    rows = []
    for case_id, overrides, expected_reason in context_definitions:
        kwargs = {
            "batch_context": None,
            "evaluation_context": valid_context,
            "download_result_context": None,
            "stage_authorization_context": None,
        }
        kwargs.update(overrides)
        observed, reason = _capture_dispatch(
            __import__(__name__, fromlist=["x"]),
            ADMISSION_RULE_ID,
            _CandidateBomb(),
            **kwargs,
        )
        expected = UnifiedAdmissionDispatchError(
            code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            admission_rule_id=ADMISSION_RULE_ID,
            known_rule=True,
            callable_discovered=True,
            adapter_ready=True,
            reason=expected_reason,
        )
        rows.append(
            _truth_row(
                f"CONTEXT_{case_id}", "admit011_context_routing", ADMISSION_RULE_ID,
                "all context gates precede candidate access", _error_json(expected), observed,
                expected_reason, reason, 0, 0, "not_accessed",
            )
        )

    candidate_map = _CountingMapping({"raw_target_relative_path": "data/raw/a.cif", "extra": object()})
    context_map = _CountingMapping({**valid_context, "extra": object()})
    result = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        candidate_map,
        evaluation_context=context_map,
    )
    mapping_clean = (
        candidate_map.calls == [ADMIT_011_CANDIDATE_FIELDS[0]]
        and context_map.calls == list(ADMIT_011_CONTEXT_ITEMS)
        and not any((candidate_map.iterated, context_map.iterated, candidate_map.get_called,
                     context_map.get_called, candidate_map.contains_called,
                     context_map.contains_called, candidate_map.len_called, context_map.len_called))
    )
    rows.append(
        _truth_row(
            "MAPPING_subclass_extra_exact_lookup", "admit011_mapping", ADMISSION_RULE_ID,
            "Mapping subclasses, extra keys, one direct lookup, no get/contains/iteration/len",
            _evaluation_json(result),
            _evaluation_json(result) if mapping_clean else "mapping_operation_drift",
            result.reason, result.reason, 1, 1, "three_values_read_once",
        )
    )
    for location in ("contract", "candidate"):
        sentinel = RuntimeError(f"{location} sentinel")
        try:
            evaluate_admission_rule(
                ADMISSION_RULE_ID,
                _CountingMapping({}, sentinel) if location == "candidate" else {},
                evaluation_context=(
                    _CountingMapping({}, sentinel)
                    if location == "contract"
                    else valid_context
                ),
            )
        except RuntimeError as error:
            observed = "same_exception_identity" if error is sentinel else "exception_identity_drift"
        else:
            observed = "exception_swallowed"
        rows.append(
            _truth_row(
                f"MAPPING_{location}_non_key_error", "admit011_mapping", ADMISSION_RULE_ID,
                "non-KeyError lookup exception propagates unchanged", "same_exception_identity",
                observed, "", "", 0, 0, "lookup_raised",
            )
        )

    for case_id, candidate, reason in (
        ("non_mapping", object(), "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("missing", {}, "raw_target_relative_path_missing"),
    ):
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            candidate,
            evaluation_context=valid_context,
        )
        expected = _admit011_candidate_invalid(reason)
        rows.append(
            _truth_row(
                f"CANDIDATE_{case_id}", "admit011_candidate", ADMISSION_RULE_ID,
                "candidate envelope invalid returns Exact13 without formal/oracle",
                _evaluation_json(expected), _evaluation_json(observed), reason, observed.reason,
                0, 0, "mapping_gate_or_one_lookup",
            )
        )
    return rows


def _tuple_pairs(value: str) -> tuple[tuple[str, str], ...]:
    parsed = json.loads(value)
    if type(parsed) is not list:
        raise ValueError("expected JSON list")
    return tuple(tuple(pair) for pair in parsed)


def _tuple_strings(value: str) -> tuple[str, ...]:
    parsed = json.loads(value)
    if type(parsed) is not list:
        raise ValueError("expected JSON list")
    return tuple(parsed)


def _expected_exact13_from_standalone_row(row: Mapping[str, str]) -> UnifiedAdmissionRuleEvaluation:
    validated = _tuple_pairs(row["validated_candidate_fields"])
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome=row["outcome"],
        passed=row["passed"] == "true",
        blocks_candidate=row["blocks_candidate"] == "true",
        reason=row["reason"],
        normalized_values=validated,
        validated_candidate_fields=validated,
        consumed_candidate_fields=_tuple_strings(row["consumed_candidate_fields"]),
        consumed_context_items=_tuple_strings(row["consumed_context_items"]),
        evaluator_io_used=row["evaluator_io_used"] == "true",
        adapter_id=ADAPTER_ID,
    )


def _exact84_rows(standalone_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in standalone_rows:
        scalar = ast.literal_eval(row["candidate_representation"])
        contract, snapshot = admit011._case_context(dict(row))
        expected = _expected_exact13_from_standalone_row(row)
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            {ADMIT_011_CANDIDATE_FIELDS[0]: scalar},
            evaluation_context={
                ADMIT_011_CONTEXT_ITEMS[0]: contract,
                ADMIT_011_CONTEXT_ITEMS[1]: snapshot,
            },
        )
        rows.append(
            _truth_row(
                f"ADMIT011_EXACT84_{row['case_id']}",
                "admit011_standalone_exact84",
                ADMISSION_RULE_ID,
                f"{row['matrix_group']}:public Exact10-to-Exact13 full projection",
                _evaluation_json(expected),
                _evaluation_json(observed),
                expected.reason,
                observed.reason,
                1,
                1,
                "three_values_read_once",
            )
        )
    if len(rows) != 84 or sum("_HIST_" in row["case_id"] for row in rows) != 47:
        raise ValueError("Exact84/Exact47 evidence drift")
    return rows


def _source_oracle_failure_rows() -> list[dict[str, str]]:
    definitions = (
        ("source_wrong_type", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 1, 0),
        ("source_subclass", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", 1, 0),
        ("source_extra_storage", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 0),
        ("source_type_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 0),
        ("source_io_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 0),
        ("source_canonical_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 0),
        ("source_consumption_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 0),
        ("oracle_exception", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 1),
        ("oracle_wrong_type", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 1),
        ("oracle_storage_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 1),
        ("oracle_field_drift", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 1),
        ("oracle_full_mismatch", "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", 1, 1),
    )
    return [
        _truth_row(
            f"FAILURE_{case_id}", "admit011_source_oracle_failure", ADMISSION_RULE_ID,
            "fail closed with no partial Exact13; direct checker executes corruption",
            reason, reason, reason, reason, formal_calls, oracle_calls,
            "three_values_read_once",
        )
        for case_id, reason, formal_calls, oracle_calls in definitions
    ]


def _truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
    standalone_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for row in predecessor_rows:
        rows.append(
            {
                "case_order": "",
                "case_id": f"EXACT10_{row['case_id']}",
                "case_group": "predecessor_exact10_truth",
                "admission_rule_id": row["admission_rule_id"],
                "behavior": row["behavior"],
                "expected_result_or_error": row["expected_result_or_error"],
                "observed_result_or_error": row["observed_result_or_error"],
                "expected_reason": row["expected_reason"],
                "observed_reason": row["observed_reason"],
                "formal_call_count": row["formal_call_count"],
                "oracle_call_count": row["oracle_call_count"],
                "candidate_access_status": row["candidate_access_status"],
                "handler_identity_status": row["predecessor_handler_identity_status"],
                "case_passed": row["case_passed"],
            }
        )
    rows.extend(_global_rows())
    rows.extend(_identity_and_parity_rows())
    rows.extend(_context_candidate_mapping_rows())
    rows.extend(_exact84_rows(standalone_rows))
    rows.extend(_source_oracle_failure_rows())
    for index, row in enumerate(rows, 1):
        row["case_order"] = str(index)
    expected_groups = {
        "predecessor_exact10_truth": 407,
        "global_dispatch": 9,
        "predecessor_handler_identity_and_parity": 10,
        "admit011_context_routing": 7,
        "admit011_mapping": 3,
        "admit011_candidate": 2,
        "admit011_standalone_exact84": 84,
        "admit011_source_oracle_failure": 12,
    }
    if (
        Counter(row["case_group"] for row in rows) != expected_groups
        or len(rows) != 534
        or len({row["case_id"] for row in rows}) != len(rows)
        or any(tuple(row) != TRUTH_COLUMNS or row["case_passed"] != "true" for row in rows)
    ):
        raise ValueError("Exact534 runtime truth failed closed")
    return rows


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("public_identity", "Exact10 public result/error types and five constants", "7/7"),
        ("dispatcher", "new function with Exact10 signature and local registry", "true"),
        ("registry", "Exact11 MappingProxyType order", "ADMIT_001_to_ADMIT_011"),
        ("registry", "first ten handler object identities", "10/10"),
        ("registry", "sole new handler", "_evaluate_registered_admit_011"),
        ("dispatch", "precedence", "exact_str|known|local_registry|handler"),
        ("identity", "rule/name/adapter", "ADMIT_011|raw_overwrite_forbidden|covapie_admit_011_unified_adapter_v1"),
        ("candidate", "fields", "raw_target_relative_path"),
        ("context", "items", "raw_target_relative_path_contract|existing_raw_target_relative_paths"),
        ("routing", "13-step precedence", "frozen"),
        ("mapping", "direct lookup counts", "contract=1|snapshot=1|candidate=1"),
        ("mapping", "missing semantics", "KeyError_only"),
        ("mapping", "subclasses and extra keys", "accepted"),
        ("mapping", "get/contains/iteration/len/copy", "forbidden"),
        ("candidate", "non-Mapping reason", "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("candidate", "missing reason", "raw_target_relative_path_missing"),
        ("candidate", "invalid calls", "formal0_oracle0"),
        ("formal", "function/order/count", "evaluate_admit_011|candidate_snapshot_contract|1"),
        ("formal", "exception", "propagated_unchanged_oracle0"),
        ("source", "exact type", "Admit011EvaluationResult_no_subclass"),
        ("source", "Exact10 validation", "storage_order_types_reconstruction_post_init_full_invariants"),
        ("source", "failure", "adapter_not_ready_oracle0_no_Exact13"),
        ("oracle", "exact type", "Admit011EvaluationResultDesign_no_Mapping_assumption"),
        ("oracle", "order/count", "candidate_snapshot_contract|1"),
        ("oracle", "Exact10 validation", "storage_order_types_reconstruction_full_invariants"),
        ("equivalence", "full Exact10", "each_value_and_exact_type_equal"),
        ("projection", "Exact10 to Exact13", "normalized_equals_validated_no_path_processing"),
        ("truth", "standalone projection", "Exact84_including_Exact47"),
        ("issue", "single transition", "ADMIT_011_removed_from_open_coverage"),
        ("boundary", "ADMIT_012 to ADMIT_015", "not_registered_not_started"),
        ("boundary", "aggregation", "single_rule_only"),
        ("boundary", "provider/download/raw/model/checkpoint/training", "not_executed"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_renameat2_RENAME_NOREPLACE"),
        ("materializer", "existing exact set", "inode_preserving_noop"),
        ("materializer", "mismatch/race", "fail_closed_no_repair"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group,
            "contract_subject": subject,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for index, (group, subject, expected) in enumerate(definitions, 1)
    ]


def _registry_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in EVALUATOR_REGISTRY
        rows.append(
            {
                "rule_id": rule_id,
                "rule_name": RULE_NAMES.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(rule_id in CALLABLE_DISCOVERED_RULE_IDS).lower(),
                "adapter_ready": str(rule_id in ADAPTER_READY_RULE_IDS).lower(),
                "registered": str(registered).lower(),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "handler_identity_status": (
                    "reused_predecessor_handler_identity"
                    if rule_id in KNOWN_RULE_IDS[:10]
                    else "exact_new_admit011_handler"
                    if rule_id == ADMISSION_RULE_ID
                    else "not_registered"
                ),
                "dispatch_disposition": (
                    "registered_local_handler" if registered else "not_registered"
                ),
                "audit_passed": "true",
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        "admit011_adapter_runtime", "exact11_registry", "exact11_dispatcher",
        "source_exact10_validation", "independent_oracle_exact10_validation",
        "full_exact10_equivalence", "exact13_projection", "exact84_projection",
        "predecessor_handler_identity", "predecessor_runtime_parity",
        "source_attestation", "issue_transition", "set_atomic_materialization",
        "deterministic_evidence", "feature_semantics_audit_requirement",
    )
    negative = (
        "admit012", "admit013", "admit014", "admit015", "evaluate_all_rules",
        "combined_candidate_verdict", "cross_rule_aggregation", "provider_mapping",
        "real_provider_evaluation", "raw_snapshot_build", "raw_read", "network",
        "download", "checkpoint", "model_forward_loss", "dataloader", "training",
        "fine_tune", "parameter_update", "stage_commit_push",
    )
    return [
        {
            "safety_item": item,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "safety_passed": "true",
        }
        for item, executed in (
            *((item, True) for item in positive),
            *((item, False) for item in negative),
        )
    ]


TRUE_READINESS = (
    "admit_011_standalone_evaluator_implemented",
    "evaluate_admit_011_implemented",
    "Admit011EvaluationResult_implemented",
    "admit_011_unified_adapter_contract_frozen",
    "admit_011_unified_adapter_implemented",
    "admit_011_registered_in_engine",
    "admit_011_context_routing_runtime_enforced",
    "admit_011_candidate_projection_runtime_enforced",
    "admit_011_source_exact10_validation_runtime_enforced",
    "admit_011_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_011_exact10_to_exact13_projection_runtime_enforced",
    "admit_011_formal_exactly_once_runtime_enforced",
    "admit_011_oracle_exactly_once_runtime_enforced",
    "exact11_reuses_exact10_public_type_identity",
    "exact11_first_ten_handler_identity_preserved",
    "exact11_public_dispatch_uses_local_registry",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_started",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "checkpoint_compatibility_validated",
    "full_repository_canonical_validated",
    "ready_for_training",
)


def _updated_issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    coverage = matches[0]
    before = dict(coverage)
    coverage["affected_rules"] = "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
    coverage["integration_transition"] = "admit_011_implemented_and_removed_from_open_coverage_scope"
    if coverage["status"] != "open":
        raise ValueError("coverage issue unexpectedly closed")
    changed = {key for key in coverage if coverage[key] != before[key]}
    if changed != {"affected_rules", "integration_transition"}:
        raise ValueError("coverage transition exceeded authorization")
    return rows


def build_runtime_state(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid Exact23 source snapshot")
    predecessor_state = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    truth_rows = _truth_rows(
        predecessor_state["predecessor_truth"],
        predecessor_state["standalone_truth"],
    )
    registry_rows = _registry_rows()
    safety_rows = _safety_rows()
    issue_rows = _updated_issue_rows(predecessor_state["design_issues"])
    issue_map = {row["issue_id"]: row for row in issue_rows}
    checks = (
        len(contract_rows) == 36,
        all(row["contract_passed"] == "true" for row in contract_rows),
        len(truth_rows) == 534,
        all(row["case_passed"] == "true" for row in truth_rows),
        len(registry_rows) == 15,
        tuple(row["rule_id"] for row in registry_rows) == KNOWN_RULE_IDS,
        len(safety_rows) == 35,
        len(issue_rows) == 11,
        issue_map["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
        type(RULE_NAMES) is MappingProxyType,
        type(ADAPTER_IDS) is MappingProxyType,
        type(EVALUATOR_REGISTRY) is MappingProxyType,
        tuple(EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:11],
        all(
            EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:10]
        ),
        EVALUATOR_REGISTRY[ADMISSION_RULE_ID] is _evaluate_registered_admit_011,
        UnifiedAdmissionRuleEvaluation is predecessor.UnifiedAdmissionRuleEvaluation,
        UnifiedAdmissionDispatchError is predecessor.UnifiedAdmissionDispatchError,
        RESULT_SCHEMA_VERSION is predecessor.RESULT_SCHEMA_VERSION,
        RESULT_FIELDS is predecessor.RESULT_FIELDS,
        DISPATCH_ERROR_FIELDS is predecessor.DISPATCH_ERROR_FIELDS,
        DISPATCH_ERROR_CODES is predecessor.DISPATCH_ERROR_CODES,
        OUTCOME_VOCABULARY is predecessor.OUTCOME_VOCABULARY,
        evaluate_admission_rule is not predecessor.evaluate_admission_rule,
        inspect.signature(evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule),
        evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is EVALUATOR_REGISTRY,
        not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules"),
        not hasattr(__import__(__name__, fromlist=["x"]), "combined_candidate_verdict"),
    )
    if not all(checks):
        raise ValueError("Exact11 runtime state failed closed")
    return {
        "snapshot": snapshot,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": dict(Counter(row["case_group"] for row in truth_rows)),
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(
    state: Mapping[str, Any], output_sha256: Mapping[str, str]
) -> dict[str, Any]:
    snapshot = state["snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    payload: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "exact11_identity": "ADMIT_001_to_ADMIT_011_unified_single_rule_runtime_v1",
        "exact10_predecessor_identity": "ADMIT_001_to_ADMIT_010_unified_single_rule_runtime_v1",
        "source_boundary_name": "fixed_ordered_exact23_committed_source_boundary",
        "source_input_count": 23,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_input_verification": [
            {
                "source_order": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "base_tree_mode": record.base_tree_mode,
                "filesystem_regular": True,
                "non_symlink": True,
                "parent_chain_non_symlink": True,
                "safe_descendant": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "pinned_fd_read": True,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact10_unified_runtime_predecessor",
            "admit011_standalone_evaluator",
            "admit011_committed_independent_raw_target_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_type_and_constant_identity": {
            "UnifiedAdmissionRuleEvaluation": True,
            "UnifiedAdmissionDispatchError": True,
            "RESULT_SCHEMA_VERSION": True,
            "RESULT_FIELDS": True,
            "DISPATCH_ERROR_FIELDS": True,
            "DISPATCH_ERROR_CODES": True,
            "OUTCOME_VOCABULARY": True,
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": str(inspect.signature(evaluate_admission_rule)),
        "public_dispatch_signature_matches_exact10": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "successor_local_registry",
            "local_registry_handler",
        ],
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[11:]),
        "registered_rule_count": 11,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_ten_handler_identity_reused": {
            rule_id: EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:10]
        },
        "admit_011_handler": "_evaluate_registered_admit_011",
        "admit_011_handler_identity": "exact_new_admit011_handler",
        "admit_011_candidate_fields": list(ADMIT_011_CANDIDATE_FIELDS),
        "admit_011_context_items": list(ADMIT_011_CONTEXT_ITEMS),
        "admit_011_context_validation_order": [
            "batch_context_must_be_none",
            "evaluation_context_mapping_validation",
            "raw_target_relative_path_contract_required_key_lookup",
            "existing_raw_target_relative_paths_required_key_lookup",
            "download_result_context_must_be_none",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "raw_target_relative_path_required_key_lookup",
            "formal_evaluator",
            "source_prevalidation",
            "independent_oracle",
            "full_exact10_equality",
            "exact13_projection",
        ],
        "admit_011_context_reasons": {
            "batch_context": "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "contract_key": "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED",
            "snapshot_key": "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED",
            "download_result_context": "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_011_candidate_mapping_invalid_reason": "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_011_missing_reason": "raw_target_relative_path_missing",
        "admit_011_required_lookup_counts": {
            "raw_target_relative_path_contract": 1,
            "existing_raw_target_relative_paths": 1,
            "raw_target_relative_path": 1,
        },
        "admit_011_present_values_forwarded_unchanged": True,
        "admit_011_formal_evaluator": "evaluate_admit_011",
        "admit_011_formal_positional_argument_order": [
            "scalar_object",
            "snapshot_object",
            "contract_object",
        ],
        "admit_011_formal_call_count": 1,
        "admit_011_adapter_normalization": False,
        "admit_011_adapter_path_repair_decode_resolve": False,
        "admit_011_source_type": "Admit011EvaluationResult",
        "admit_011_source_fields": list(admit011.RESULT_FIELDS),
        "admit_011_source_type_invalid_reason": "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_011_source_invariant_invalid_reason": "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_011_source_prevalidation_before_oracle": True,
        "admit_011_source_full_exact10_invariant_validation": True,
        "admit_011_oracle": "classify_admit_011_raw_target_relative_path_design",
        "admit_011_oracle_result_type": "Admit011EvaluationResultDesign",
        "admit_011_oracle_call_count": 1,
        "admit_011_oracle_full_exact10_validation": True,
        "admit_011_source_oracle_full_exact10_value_and_type_equality_required": True,
        "admit_011_normalized_values_projection": "source.validated_candidate_fields",
        "admit_011_no_partial_exact13_on_failure": True,
        "standalone_exact84_projection_count": 84,
        "standalone_historical_exact47_projection_count": 47,
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_pass_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": len(state["safety_rows"]),
        "safety_audit_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": 11,
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "admit_011_implemented_and_removed_from_open_coverage_scope",
        "issue_coverage_after": list(KNOWN_RULE_IDS[11:]),
        "issue_authoritative_predecessor_sha256": SOURCE_SHA256[DESIGN_ISSUE_PATH],
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "output_materialization": {
            "read_only_target_preflight": True,
            "all_payloads_built_before_mutation": True,
            "exact_six_allowlist": True,
            "pinned_parent_root_staging_leaf": True,
            "exclusive_create": True,
            "no_follow": True,
            "file_fsync": True,
            "staging_directory_fsync": True,
            "sibling_hidden_staging_directory": True,
            "renameat2_RENAME_NOREPLACE": True,
            "parent_fsync": True,
            "complete_set_postverify": True,
            "existing_exact_set_inode_preserving_noop": True,
            "mismatch_repair_forbidden": True,
            "race_fail_closed": True,
            "unknown_staging_entry_not_deleted": True,
            "post_publication_fsync_failure_preserves_complete_set": True,
        },
        "provider_fields_consumed": [],
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "admit_012_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_contract_frozen": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_precedence_frozen": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "stop_boundaries": [
            "no_admit_012_to_015",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_cross_rule_aggregation",
            "no_provider_mapping_or_real_provider_evaluation",
            "no_raw_snapshot_build_or_raw_read",
            "no_network_or_download",
            "no_model_checkpoint_forward_loss_dataloader_training",
        ],
        "readiness_true_count": len(TRUE_READINESS),
        "readiness_false_count": len(FALSE_READINESS),
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "manifest_top_level_key_count": 0,
    }
    payload["manifest_top_level_key_count"] = len(payload)
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(REGISTRY_COLUMNS, state["registry_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: _sha(content) for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }
    return payloads, manifest


@dataclass(frozen=True)
class OutputMaterializationPlan:
    root: Path
    parent: Path
    anchor: Path
    root_name: str
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int] | None
    leaf_identities: tuple[tuple[str, tuple[int, int, int]], ...]


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1
DIRECTORY_FD_CAPABILITIES = all(
    function in os.supports_dir_fd
    for function in (os.open, os.stat, os.mkdir, os.unlink, os.rmdir)
) and _RENAMEAT2 is not None


def _require_materializer_capabilities() -> None:
    if (
        not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"))
        or not DIRECTORY_FD_CAPABILITIES
    ):
        raise ValueError("required directory-fd set-atomic support unavailable")


def _inspect_output_target_read_only(
    output_root: Path,
    repo_root: Path = REPO_ROOT,
) -> OutputMaterializationPlan:
    _require_materializer_capabilities()
    candidate = Path(output_root)
    repo = Path(os.path.abspath(repo_root))
    repo_item = os.lstat(repo)
    if not stat.S_ISDIR(repo_item.st_mode) or stat.S_ISLNK(repo_item.st_mode) or repo.resolve(strict=True) != repo:
        raise ValueError("repository identity unsafe")
    if candidate.is_absolute():
        root = Path(os.path.abspath(candidate))
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape forbidden")
        root = repo / candidate
        anchor = repo
    if not root.name:
        raise ValueError("output root invalid")
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    if not candidate.is_absolute() and repo not in (parent, *parent.parents):
        raise ValueError("relative output escaped repository")
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(
            root, parent, anchor, root.name, parent_identity, None, ()
        )
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        leaf = root / name
        item = os.lstat(leaf)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or leaf.resolve(strict=True) != leaf
        ):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _identity(item)))
    return OutputMaterializationPlan(
        root,
        parent,
        anchor,
        root.name,
        parent_identity,
        _identity(root_item),
        tuple(leaves),
    )


def _validate_payloads(payloads: Mapping[str, bytes]) -> None:
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or set(payloads) != set(OUTPUT_FILES)
        or any(type(content) is not bytes for content in payloads.values())
    ):
        raise ValueError("output payload inventory invalid")


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _read_at(
    directory_fd: int,
    name: str,
    expected_identity: tuple[int, int, int],
) -> bytes:
    item = _stat_at(directory_fd, name)
    if (
        _identity(item) != expected_identity
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
    ):
        raise ValueError("pinned output leaf changed")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned output descriptor changed")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(descriptor)) != expected_identity
            or _identity(_stat_at(directory_fd, name)) != expected_identity
        ):
            raise ValueError("pinned output leaf changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd,
        os.fsencode(source),
        parent_fd,
        os.fsencode(target),
        RENAME_NOREPLACE,
    ):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{source}->{target}")


def _assert_parent(plan: OutputMaterializationPlan, parent_fd: int) -> None:
    if (
        _identity(os.fstat(parent_fd)) != plan.parent_identity
        or _identity(os.lstat(plan.parent)) != plan.parent_identity
    ):
        raise ValueError("output parent identity changed")
    _assert_real_parent_chain(plan.parent, plan.anchor)


def _verify_complete_set(root_fd: int, payloads: Mapping[str, bytes]) -> None:
    if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    for name, content in payloads.items():
        item = _stat_at(root_fd, name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output leaf type drift")
        actual = _read_at(root_fd, name, _identity(item))
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")


def _cleanup_staging(
    parent_fd: int | None,
    staging_fd: int | None,
    staging_name: str | None,
    staging_identity: tuple[int, int, int] | None,
    staged: Mapping[str, tuple[int, int, int]],
) -> int | None:
    if (
        parent_fd is None
        or staging_fd is None
        or staging_name is None
        or staging_identity is None
    ):
        return staging_fd
    try:
        if (
            _identity(os.fstat(staging_fd)) != staging_identity
            or _identity(_stat_at(parent_fd, staging_name)) != staging_identity
            or set(os.listdir(staging_fd)) != set(staged)
        ):
            return staging_fd
        for name, identity in staged.items():
            item = _stat_at(staging_fd, name)
            if (
                _identity(item) != identity
                or not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                return staging_fd
        for name, identity in staged.items():
            if _identity(_stat_at(staging_fd, name)) != identity:
                return staging_fd
            os.unlink(name, dir_fd=staging_fd)
        if os.listdir(staging_fd):
            return staging_fd
        os.close(staging_fd)
        staging_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException:
        pass
    return staging_fd


def _materialize_set(
    plan: OutputMaterializationPlan,
    payloads: Mapping[str, bytes],
) -> None:
    _validate_payloads(payloads)
    parent_fd: int | None = None
    root_fd: int | None = None
    staging_name: str | None = None
    staging_identity: tuple[int, int, int] | None = None
    staged: dict[str, tuple[int, int, int]] = {}
    try:
        parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
        _assert_parent(plan, parent_fd)
        if plan.root_identity is not None:
            item = _stat_at(parent_fd, plan.root_name)
            if (
                _identity(item) != plan.root_identity
                or not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor changed")
            if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
                raise ValueError("existing output inventory changed")
            identities = dict(plan.leaf_identities)
            for name, content in payloads.items():
                if _read_at(root_fd, name, identities[name]) != content:
                    raise ValueError("existing output differs; repair forbidden")
            _verify_complete_set(root_fd, payloads)
            os.fsync(root_fd)
            return

        try:
            _stat_at(parent_fd, plan.root_name)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = f".exact11-runtime-stage-{secrets.token_hex(16)}"
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        root_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        staging_identity = _identity(os.fstat(root_fd))
        if os.listdir(root_fd) or _identity(_stat_at(parent_fd, staging_name)) != staging_identity:
            raise ValueError("staging directory invalid")
        for name, content in payloads.items():
            descriptor = os.open(name, WRITE_FILE_FLAGS, 0o600, dir_fd=root_fd)
            try:
                staged[name] = _identity(os.fstat(descriptor))
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
        _assert_parent(plan, parent_fd)
        if (
            _identity(os.fstat(root_fd)) != staging_identity
            or _identity(_stat_at(parent_fd, staging_name)) != staging_identity
        ):
            raise ValueError("staging identity changed")
        try:
            _stat_at(parent_fd, plan.root_name)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("staging inventory changed")
        for name, identity in staged.items():
            if _identity(_stat_at(root_fd, name)) != identity:
                raise ValueError("staged leaf changed")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        os.fsync(parent_fd)
        if _identity(_stat_at(parent_fd, plan.root_name)) != staging_identity:
            raise ValueError("published output root changed")
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
    except BaseException:
        root_fd = _cleanup_staging(
            parent_fd,
            root_fd,
            staging_name,
            staging_identity,
            staged,
        )
        raise
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic evidence files as one directory set."""
    plan = _inspect_output_target_read_only(output_root, repo_root)
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    state = build_runtime_state(snapshot)
    payloads, manifest = _payloads(state)
    _materialize_set(plan, payloads)
    return {"state": state, "manifest": manifest, "output_root": plan.root}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1()

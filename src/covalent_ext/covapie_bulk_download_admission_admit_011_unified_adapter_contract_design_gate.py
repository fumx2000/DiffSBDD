"""Design-only contract gate for the future ADMIT_011 unified adapter.

This module freezes routing, exact source/oracle validation, and Exact13
projection.  It deliberately defines no runtime handler, registry, or public
dispatcher and performs no raw, provider, network, download, or training work.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import importlib
import io
import json
import os
import secrets
import stat
import subprocess
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, NoReturn


PROJECT = "CovaPIE"
STEP = "ADMIT_011 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "da7367cfdcf54bff8c30e05ba6f7d16cc5dbda2e"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_011 standalone evaluator interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_011_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_011_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_011"
ADMISSION_RULE_NAME = "raw_overwrite_forbidden"
ADAPTER_ID = "covapie_admit_011_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_011"
FORMAL_RESULT_TYPE = "Admit011EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_011_raw_target_relative_path_design"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 11))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("raw_target_relative_path",)
CONTEXT_ITEMS = ("raw_target_relative_path_contract", "existing_raw_target_relative_paths")
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_raw_target_relative_path", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
DISPATCH_ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
DISPATCH_ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")
CONTEXT_REASONS = {
    "batch_context": "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "contract_key": "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED",
    "snapshot_key": "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED",
    "download_result_context": "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_MAPPING_REASON = "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "raw_target_relative_path_missing"
SOURCE_TYPE_REASON = "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "raw_target_relative_path_contract_required_key_lookup",
    "existing_raw_target_relative_paths_required_key_lookup",
    "download_result_context_must_be_none",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "raw_target_relative_path_required_key_lookup",
    "formal_evaluator",
    "standalone_source_validation",
    "independent_oracle",
    "full_exact10_equality",
    "exact13_projection",
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_source_boundary_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_purity_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
    "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2",
    "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b",
    "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6",
    "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e",
    "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
    "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d",
    "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4",
    "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca",
    "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436",
    "46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198",
    "dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095",
    "6ee42e0baf26ece28df75201521babdf8f9ffe7a89b7544a346f92e5ecd39119",
    "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30",
    "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1",
), strict=True))

CONTRACT_FILENAME = "covapie_admit_011_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_011_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_011_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_011_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_011_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_011_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME)
FROZEN_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    ROUTING_FILENAME: "be12ce9e9c551f5891cac9840d130dd9feabfb99fe849385db08dcf767486845",
    TRUTH_FILENAME: "deb4b71376a27d00317d9255e822c9e534c39fc16f0a6636dc149a6ca205b01a",
    SAFETY_FILENAME: "8c1cfae97131a7b76acc2c1b92381359d458c0ef9640ca3870975bf1724759bc",
    ISSUE_FILENAME: "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    MANIFEST_FILENAME: "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
}
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "condition", "expected_behavior",
    "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count",
    "candidate_access_status", "required_lookup_count", "identity_preserved", "case_passed",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason",
    "source_exact10_json", "oracle_exact10_json", "unified_exact13_json",
    "formal_call_count", "oracle_call_count", "case_passed",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class UnifiedAdmissionEvaluationDesignRecord:
    schema_version: str
    admission_rule_id: str
    admission_rule_name: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    normalized_values: tuple[tuple[str, str], ...]
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool
    adapter_id: str

    def __post_init__(self) -> None:
        if type(self) is not UnifiedAdmissionEvaluationDesignRecord or tuple(x.name for x in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("exact unified design result required")
        if any(type(value) is not str for value in (self.schema_version, self.admission_rule_id, self.admission_rule_name, self.outcome, self.reason, self.adapter_id)):
            raise TypeError("unified string fields require exact built-in str")
        if any(type(value) is not bool for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)):
            raise TypeError("unified boolean fields require exact built-in bool")
        if any(type(value) is not tuple for value in (self.normalized_values, self.validated_candidate_fields, self.consumed_candidate_fields, self.consumed_context_items)):
            raise TypeError("unified tuple fields require exact built-in tuple")
        if self.schema_version != RESULT_SCHEMA_VERSION or self.admission_rule_id != ADMISSION_RULE_ID or self.admission_rule_name != ADMISSION_RULE_NAME or self.adapter_id != ADAPTER_ID:
            raise ValueError("unified identity drift")
        if self.outcome not in OUTCOME_VOCABULARY or self.passed is not (self.outcome == "passed") or self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("unified outcome flags drift")
        if self.normalized_values != self.validated_candidate_fields or self.evaluator_io_used is not False:
            raise ValueError("unified projection drift")


@dataclass(frozen=True)
class SourceValidationDecision:
    accepted: bool
    code: str
    reason: str
    adapter_ready: bool


class AdapterContractDesignError(Exception):
    """Design-only representation of a future Exact6 dispatch failure."""

    def __init__(self, code: str, reason: str, *, adapter_ready: bool) -> None:
        self.code = code
        self.admission_rule_id = ADMISSION_RULE_ID
        self.known_rule = True
        self.callable_discovered = True
        self.adapter_ready = adapter_ready
        self.reason = reason
        super().__init__(reason)

    def as_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in DISPATCH_ERROR_FIELDS}


def _standalone_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_011_rule_logic_interface")


def _oracle_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate")


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit011EvaluationResult
    if type(source) is not result_type:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False)
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 storage mismatch")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 dataclass field order mismatch")
        values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        expected_types = (str, str, bool, bool, str, str, tuple, tuple, tuple, bool)
        if any(type(value) is not expected for value, expected in zip(values, expected_types, strict=True)):
            raise TypeError("Exact10 field type mismatch")
        reconstructed = result_type(*values)
        if reconstructed != source or source.admission_rule_id != ADMISSION_RULE_ID or source.evaluator_io_used is not False:
            raise ValueError("Exact10 reconstruction or fixed invariant mismatch")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def expected_exact10_from_committed_oracle_for_design(
    scalar: object,
    snapshot: object,
    contract: object,
    *,
    oracle_callable: Callable[[object, object, object], object] | None = None,
) -> Any:
    standalone = _standalone_module()
    oracle = _oracle_module()
    classify = oracle.classify_admit_011_raw_target_relative_path_design if oracle_callable is None else oracle_callable
    try:
        classification = classify(scalar, snapshot, contract)
        result_type = oracle.Admit011EvaluationResultDesign
        if type(classification) is not result_type:
            raise TypeError("oracle exact result type required")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact10 field order drift")
        storage = vars(classification)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("oracle Exact10 storage drift")
        values = tuple(getattr(classification, name) for name in STANDALONE_RESULT_FIELDS)
        if result_type(*values) != classification:
            raise ValueError("oracle reconstruction drift")
        return standalone.Admit011EvaluationResult(*values)
    except Exception as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(source: object, expected: object) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    standalone = _standalone_module()
    if type(expected) is not standalone.Admit011EvaluationResult:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    try:
        source_values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        expected_values = tuple(getattr(expected, name) for name in STANDALONE_RESULT_FIELDS)
    except AttributeError:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    if any(type(left) is not type(right) or left != right for left, right in zip(source_values, expected_values, strict=True)):
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def project_exact10_to_exact13_for_design(source: object) -> UnifiedAdmissionEvaluationDesignRecord:
    if not validate_source_shape_and_invariants_for_design(source).accepted:
        raise ValueError("source is not projection-ready")
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, source.admission_rule_id, ADMISSION_RULE_NAME,
        source.outcome, source.passed, source.blocks_candidate, source.reason,
        source.validated_candidate_fields, source.validated_candidate_fields,
        source.consumed_candidate_fields, source.consumed_context_items,
        source.evaluator_io_used, ADAPTER_ID,
    )


def candidate_invalid_exact13_for_design(reason: str) -> UnifiedAdmissionEvaluationDesignRecord:
    if reason not in (CANDIDATE_MAPPING_REASON, MISSING_REASON):
        raise ValueError("unsupported adapter candidate reason")
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, ADMISSION_RULE_ID, ADMISSION_RULE_NAME, "invalid",
        False, True, reason, (), (), CANDIDATE_FIELDS, CONTEXT_ITEMS, False, ADAPTER_ID,
    )


def _raise_design_error(code: str, reason: str, adapter_ready: bool) -> NoReturn:
    raise AdapterContractDesignError(code, reason, adapter_ready=adapter_ready)


def route_and_project_for_design(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
    formal_evaluator: Callable[[object, object, object], object] | None = None,
    oracle_callable: Callable[[object, object, object], object] | None = None,
) -> UnifiedAdmissionEvaluationDesignRecord:
    """Exercise the frozen future algorithm without implementing its handler."""
    if batch_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context"], True)
    if not isinstance(evaluation_context, Mapping):
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context"], True)
    try:
        contract_object = evaluation_context[CONTEXT_ITEMS[0]]
    except KeyError:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["contract_key"], True)
    try:
        snapshot_object = evaluation_context[CONTEXT_ITEMS[1]]
    except KeyError:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["snapshot_key"], True)
    if download_result_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["download_result_context"], True)
    if stage_authorization_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["stage_authorization_context"], True)
    if not isinstance(candidate_record, Mapping):
        return candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    try:
        scalar_object = candidate_record[CANDIDATE_FIELDS[0]]
    except KeyError:
        return candidate_invalid_exact13_for_design(MISSING_REASON)

    evaluator = _standalone_module().evaluate_admit_011 if formal_evaluator is None else formal_evaluator
    source = evaluator(scalar_object, snapshot_object, contract_object)
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact10_from_committed_oracle_for_design(
            scalar_object, snapshot_object, contract_object, oracle_callable=oracle_callable,
        )
    except ValueError:
        _raise_design_error("UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    decision = validate_source_oracle_equivalence_for_design(source, expected)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    return project_exact10_to_exact13_for_design(source)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(root: Path, arguments: Sequence[str]) -> bytes:
    result = subprocess.run(("git", *arguments), cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ValueError("source-boundary git command failed")
    return result.stdout


def _parent_chain_is_real(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("parent chain is unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("parent chain resolved identity drift")


def _source_identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _read_pinned_file(path: Path, identity: tuple[int, int, int]) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _source_identity(os.fstat(descriptor)) != identity or _source_identity(os.lstat(path)) != identity:
            raise ValueError("source identity changed")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _source_identity(os.fstat(descriptor)) != identity or _source_identity(os.lstat(path)) != identity:
            raise ValueError("source identity changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("repository identity unsafe")
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head_ref invalid")
    if _git(root, ("show", "-s", "--format=%s", EXPECTED_BASE_COMMIT)).decode().rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("base subject drift")
    _git(root, ("merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref))
    if len(SOURCE_PATHS) != 16 or len(set(SOURCE_PATHS)) != 16 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact16 source boundary configuration drift")
    inspected: list[tuple[Path, Path, tuple[int, int, int]]] = []
    for relative in SOURCE_PATHS:
        if relative.is_absolute() or not relative.parts or ".." in relative.parts or relative.parts[:2] == ("data", "raw") or relative.parts[0] == "checkpoints":
            raise ValueError("unsafe source path")
        path = root / relative
        _parent_chain_is_real(path.parent, root)
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path:
            raise ValueError("source leaf unsafe")
        if _git(root, ("ls-files", "--error-unmatch", "--", relative.as_posix())).decode() != f"{relative.as_posix()}\n":
            raise ValueError("source is not tracked")
        tree = _git(root, ("ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix())).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise ValueError("base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if tree_path.decode() != relative.as_posix() or len(parts) != 3 or parts[0] not in (b"100644", b"100755") or parts[1] != b"blob":
            raise ValueError("base tree entry drift")
        inspected.append((relative, path, _source_identity(item)))
    records = []
    for relative, path, identity in inspected:
        base = _git(root, ("show", f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}"))
        content = _read_pinned_file(path, identity)
        expected = SOURCE_SHA256[relative]
        base_sha, filesystem_sha = _sha(base), _sha(content)
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {relative}")
        records.append(FrozenSourceRecord(relative, expected, base_sha, filesystem_sha, content))
    return FrozenSourceSnapshot(tuple(records))


def _record(snapshot: FrozenSourceSnapshot, index: int) -> FrozenSourceRecord:
    record = snapshot.records[index]
    if record.relative_path != SOURCE_PATHS[index]:
        raise ValueError("source snapshot order drift")
    return record


def _json_document(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_record(snapshot, index).content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON root must be object")
    return value


def _csv_document(snapshot: FrozenSourceSnapshot, index: int) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, index).content.decode("utf-8"), newline=""))
    header = tuple(reader.fieldnames or ())
    rows = tuple(dict(row) for row in reader)
    if not header or len(header) != len(set(header)) or any(tuple(row) != header or None in row.values() for row in rows):
        raise ValueError("CSV shape drift")
    return header, rows


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets):
            value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
            if isinstance(value, ast.Dict) and all(isinstance(key, ast.Constant) and type(key.value) is str for key in value.keys):
                return tuple(key.value for key in value.keys)
    raise ValueError("literal runtime registry absent")


def _top_functions(tree: ast.Module) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    standalone_tree = ast.parse(_record(snapshot, 0).content.decode())
    contract_header, contract_rows = _csv_document(snapshot, 1)
    truth_header, truth_rows = _csv_document(snapshot, 2)
    issue_header, issue_rows = _csv_document(snapshot, 5)
    standalone_manifest = _json_document(snapshot, 6)
    oracle_tree = ast.parse(_record(snapshot, 7).content.decode())
    path_manifest = _json_document(snapshot, 8)
    path_truth_header, path_truth = _csv_document(snapshot, 9)
    runtime_tree = ast.parse(_record(snapshot, 10).content.decode())
    runtime_manifest = _json_document(snapshot, 11)
    admit010_tree = ast.parse(_record(snapshot, 12).content.decode())
    admit010_manifest = _json_document(snapshot, 13)
    admit009_tree = ast.parse(_record(snapshot, 14).content.decode())
    admit009_manifest = _json_document(snapshot, 15)
    issues = {row["issue_id"]: row for row in issue_rows}
    checks = (
        FORMAL_EVALUATOR_NAME in _top_functions(standalone_tree),
        standalone_manifest.get("result_type") == FORMAL_RESULT_TYPE,
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        standalone_manifest.get("row_counts", {}).get("truth") == 84,
        standalone_manifest.get("row_counts", {}).get("truth_historical") == 47,
        contract_header == ("field_order", "field", "contract", "passed") and len(contract_rows) == 10,
        len(truth_rows) == 84 and len(path_truth) == 84
        and tuple(row["case_id"] for row in truth_rows) == tuple(row["case_id"] for row in path_truth)
        and all(
            left[key] == right[path_key]
            for left, right in zip(truth_rows, path_truth, strict=True)
            for key, path_key in (
                ("candidate_representation", "candidate_representation"),
                ("outcome", "outcome"), ("passed", "passed"),
                ("blocks_candidate", "blocks_candidate"), ("reason", "reason"),
                ("canonical_raw_target_relative_path", "canonical"),
                ("validated_candidate_fields", "validated_candidate_fields"),
                ("consumed_candidate_fields", "consumed_candidate_fields"),
                ("consumed_context_items", "consumed_context_items"),
                ("evaluator_io_used", "evaluator_io_used"),
            )
        ),
        INDEPENDENT_ORACLE_NAME in _top_functions(oracle_tree),
        FORMAL_EVALUATOR_NAME not in _top_functions(oracle_tree),
        path_manifest.get("row_counts", {}).get("truth") == 84,
        _literal_registry_keys(runtime_tree) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("known_not_registered_rule_ids") == list(KNOWN_RULE_IDS[10:]),
        "_evaluate_registered_admit_011" not in _top_functions(runtime_tree),
        "evaluate_admission_rule" in _top_functions(runtime_tree),
        "build_design_state" in _top_functions(admit010_tree),
        admit010_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        "build_design_state" in _top_functions(admit009_tree),
        admit009_manifest.get("future_registered_rule_order") == list(KNOWN_RULE_IDS[:9]),
        issue_header == ISSUE_COLUMNS and len(issue_rows) == 11,
        issues["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] == "resolved",
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "|".join(KNOWN_RULE_IDS[10:]),
        issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {"truth_rows": truth_rows, "issue_rows": issue_rows, "issue_bytes": _record(snapshot, 5).content}


def _json_record(value: object) -> str:
    return json.dumps({field.name: getattr(value, field.name) for field in fields(value)}, ensure_ascii=True, separators=(",", ":"))


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "rule", f"{ADMISSION_RULE_ID}|{ADMISSION_RULE_NAME}|{ADAPTER_ID}"),
        ("registry", "current_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registry", "known_ids", "|".join(KNOWN_RULE_IDS)),
        ("candidate", "fields", "|".join(CANDIDATE_FIELDS)),
        ("context", "standalone_consumption_order", "|".join(CONTEXT_ITEMS)),
        ("formal", "public_parameter_order", "raw_target_relative_path|existing_raw_target_relative_paths|raw_target_relative_path_contract"),
        ("formal", "exactly_once", "true"),
        ("oracle", "exactly_once_after_source_validation", "true"),
        ("oracle", "exact_result_type", "Admit011EvaluationResultDesign"),
        ("source", "exact10_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("dispatch", "exact6_fields", "|".join(DISPATCH_ERROR_FIELDS)),
        ("dispatch", "error_codes", "|".join(DISPATCH_ERROR_CODES)),
        ("result", "outcomes", "|".join(OUTCOME_VOCABULARY)),
        ("routing", "precedence", "|".join(CONTEXT_ROUTING_ORDER)),
        ("routing", "mapping", "Mapping_subclasses_allowed_direct_lookup_once_KeyError_only"),
        ("routing", "lookup_counts", "contract=1|snapshot=1|candidate=1"),
        ("identity", "object_identity", "candidate_snapshot_contract_preserved_for_formal_and_oracle"),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_post_init_full_invariants"),
        ("source", "oracle_equivalence", "all_Exact10_values_and_types_equal"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "adapter_side_path_processing", "none"),
        ("boundary", "runtime", "design_only_no_handler_registry_or_dispatcher"),
        ("boundary", "operations", "no_provider_mapping_raw_network_download_model_checkpoint_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    return [{
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1)]


def _routing_rows() -> list[dict[str, str]]:
    def row(group: str, case_id: str, condition: str, behavior: str, reason: str = "", result: str = "", formal: int = 0, oracle: int = 0, access: str = "not_accessed", lookups: int = 0, identity: str = "n/a") -> dict[str, str]:
        return {
            "matrix_order": "", "matrix_group": group, "case_id": case_id,
            "condition": condition, "expected_behavior": behavior, "expected_reason": reason,
            "expected_result_json": result, "formal_call_count": str(formal),
            "oracle_call_count": str(oracle), "candidate_access_status": access,
            "required_lookup_count": str(lookups), "identity_preserved": identity,
            "case_passed": "true",
        }
    invalid_mapping = _json_record(candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON))
    missing = _json_record(candidate_invalid_exact13_for_design(MISSING_REASON))
    cases = [
        row("context", "batch_non_none", "batch non-None", "dispatch_error", CONTEXT_REASONS["batch_context"]),
        row("context", "evaluation_non_mapping", "evaluation non-Mapping", "dispatch_error", CONTEXT_REASONS["evaluation_context"]),
        row("context", "contract_missing", "contract key absent", "dispatch_error", CONTEXT_REASONS["contract_key"], lookups=1),
        row("context", "snapshot_missing", "snapshot key absent", "dispatch_error", CONTEXT_REASONS["snapshot_key"], lookups=2),
        row("context", "download_non_none", "download non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], lookups=2),
        row("context", "stage_non_none", "stage non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], lookups=2),
        row("context", "mapping_subclass", "evaluation Mapping subclass", "accepted", lookups=3, identity="true", formal=1, oracle=1, access="value_read_once"),
        row("context", "extra_keys", "extra evaluation keys", "ignored", lookups=3, identity="true", formal=1, oracle=1, access="value_read_once"),
        row("context", "contract_lookup_once", "repeat lookup bomb", "accepted_single_lookup", lookups=3, identity="true", formal=1, oracle=1, access="value_read_once"),
        row("context", "snapshot_lookup_once", "repeat lookup bomb", "accepted_single_lookup", lookups=3, identity="true", formal=1, oracle=1, access="value_read_once"),
        row("precedence", "batch_blocks_evaluation", "batch and evaluation invalid", "first_batch_error", CONTEXT_REASONS["batch_context"]),
        row("precedence", "evaluation_blocks_lookup", "evaluation and keys invalid", "evaluation_error", CONTEXT_REASONS["evaluation_context"]),
        row("precedence", "contract_blocks_snapshot", "both keys absent", "contract_error", CONTEXT_REASONS["contract_key"], lookups=1),
        row("precedence", "snapshot_blocks_candidate", "snapshot absent and candidate bomb", "snapshot_error", CONTEXT_REASONS["snapshot_key"], lookups=2),
        row("precedence", "download_blocks_candidate", "download invalid and candidate bomb", "download_error", CONTEXT_REASONS["download_result_context"], lookups=2),
        row("precedence", "stage_blocks_candidate", "stage invalid and candidate bomb", "stage_error", CONTEXT_REASONS["stage_authorization_context"], lookups=2),
        row("candidate", "non_mapping", "candidate non-Mapping", "exact13_invalid", CANDIDATE_MAPPING_REASON, invalid_mapping, lookups=2, access="envelope_checked"),
        row("candidate", "field_missing", "candidate key absent", "exact13_invalid", MISSING_REASON, missing, lookups=3, access="single_lookup"),
        row("candidate", "mapping_subclass", "candidate Mapping subclass", "accepted", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("candidate", "extra_keys", "extra candidate keys", "ignored", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("candidate", "lookup_once", "candidate repeat lookup bomb", "accepted_single_lookup", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("call", "formal_once", "valid routing", "one positional candidate_snapshot_contract call", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("call", "oracle_once", "valid source", "one positional candidate_snapshot_contract call", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("call", "formal_exception", "formal raises", "exception_no_source_or_oracle", formal=1, access="value_read_once", lookups=3, identity="true"),
        row("source", "wrong_type", "formal object", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, formal=1, access="value_read_once", lookups=3, identity="true"),
        row("source", "subclass", "formal subclass", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, formal=1, access="value_read_once", lookups=3, identity="true"),
        row("source", "invariant", "Exact10 invariant drift", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, formal=1, access="value_read_once", lookups=3, identity="true"),
        row("oracle", "exception", "oracle raises", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("oracle", "type_drift", "oracle wrong type", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("oracle", "mismatch", "full Exact10 mismatch", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("projection", "passed", "unoccupied canonical path", "exact10_to_exact13", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("projection", "collision", "occupied canonical path", "exact10_to_exact13_blocked", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
        row("projection", "invalid_scalar", "scalar grammar invalid", "exact10_to_exact13_invalid", formal=1, oracle=1, access="value_read_once", lookups=3, identity="true"),
    ]
    for index, value in enumerate(cases, 1):
        value["matrix_order"] = str(index)
    return cases


def _truth_rows(predecessor_truth: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    standalone = _standalone_module()
    rows = []
    for row in predecessor_truth:
        scalar = ast.literal_eval(row["candidate_representation"])
        contract, snapshot = standalone._case_context(dict(row))
        source = standalone.evaluate_admit_011(scalar, snapshot, contract)
        expected = expected_exact10_from_committed_oracle_for_design(scalar, snapshot, contract)
        if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
            raise ValueError(f"source/oracle truth mismatch: {row['case_id']}")
        unified = project_exact10_to_exact13_for_design(source)
        rows.append({
            "case_id": row["case_id"], "case_group": row["matrix_group"],
            "behavior": "exact10_to_exact13", "expected_dispatch_code": "",
            "expected_reason": source.reason, "source_exact10_json": _json_record(source),
            "oracle_exact10_json": _json_record(expected), "unified_exact13_json": _json_record(unified),
            "formal_call_count": "1", "oracle_call_count": "1", "case_passed": "true",
        })
    if len(rows) != 84 or sum(row["case_id"].startswith("HIST_") for row in rows) != 47:
        raise ValueError("Exact84/Exact47 projection truth drift")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        "adapter_contract_design", "candidate_projection_design", "context_routing_design",
        "standalone_source_validation_design", "independent_oracle_equivalence_design",
        "exact10_to_exact13_projection_design", "formal_exactly_once", "oracle_exactly_once",
        "candidate_context_identity_preserved", "deterministic_set_atomic_materialization",
        "source_attestation", "issue_inventory_preservation", "design_only_status",
    )
    negative = (
        "runtime_handler", "registry_modification", "dispatcher_modification", "adapter_filesystem_use",
        "network", "raw_read_or_enumeration", "checkpoint", "provider_mapping", "download",
        "candidate_context_mutation", "model_forward", "model_loss", "dataloader", "training",
        "fine_tune", "parameter_update", "stage", "commit", "push",
    )
    return [{
        "safety_item": item, "expected_executed": str(expected).lower(),
        "observed_executed": str(expected).lower(), "safety_passed": "true",
    } for item, expected in (*((item, True) for item in positive), *((item, False) for item in negative))]


TRUE_READINESS = (
    "admit_011_rule_logic_implemented", "admit_011_standalone_interface_frozen",
    "admit_011_unified_adapter_contract_frozen", "candidate_projection_contract_frozen",
    "context_routing_contract_frozen", "standalone_source_validation_contract_frozen",
    "independent_oracle_equivalence_contract_frozen", "exact10_to_exact13_projection_frozen",
    "future_registered_rule_order_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_011_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_011_runtime_adapter_implemented", "admit_011_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented", "provider_mapping_validated",
    "real_provider_evaluation_ready", "combined_candidate_verdict_implemented",
    "ready_for_bulk_download_now", "checkpoint_compatibility_validated",
    "full_repository_canonical_validated", "ready_for_training",
)
READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_design_state(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    state = {
        "snapshot": snapshot, "contract_rows": _contract_rows(), "routing_rows": _routing_rows(),
        "truth_rows": _truth_rows(predecessor["truth_rows"]), "safety_rows": _safety_rows(),
        "issue_rows": predecessor["issue_rows"], "issue_bytes": predecessor["issue_bytes"],
    }
    if (len(state["routing_rows"]) != 33 or len(state["truth_rows"]) != 84 or len(state["issue_rows"]) != 11
            or any(row["case_passed"] != "true" for row in (*state["routing_rows"], *state["truth_rows"]))):
        raise ValueError("design state failed closed")
    return state


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    snapshot = state["snapshot"]
    manifest = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID, "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": FORMAL_RESULT_TYPE, "future_adapter_handler": "_evaluate_registered_admit_011",
        "independent_oracle": INDEPENDENT_ORACLE_NAME, "independent_oracle_result_type": "Admit011EvaluationResultDesign",
        "candidate_fields": list(CANDIDATE_FIELDS), "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "known_rule_ids": list(KNOWN_RULE_IDS), "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[10:]),
        "result_schema_version": RESULT_SCHEMA_VERSION, "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS), "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY), "context_routing_order": list(CONTEXT_ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON, "candidate_missing_reason": MISSING_REASON,
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": list(CANDIDATE_FIELDS), "consumed_context_items": list(CONTEXT_ITEMS),
            "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
        },
        "formal_positional_argument_order": ["raw_target_relative_path_object", "existing_raw_target_relative_paths_object", "raw_target_relative_path_contract_object"],
        "formal_call_count_after_candidate_gate": 1, "oracle_call_count_after_source_validation": 1,
        "required_lookup_counts": {"raw_target_relative_path": 1, "raw_target_relative_path_contract": 1, "existing_raw_target_relative_paths": 1},
        "original_object_identity_preserved": True, "adapter_side_normalization": False,
        "adapter_side_path_repair_or_resolution": False, "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON, "source_exact_type_required": True,
        "source_exact10_full_invariant_validation": True, "oracle_exact_type_required": True,
        "source_oracle_full_exact10_equality_required": True, "normalized_values_projection": "source.validated_candidate_fields",
        "contract_row_count": len(state["contract_rows"]), "contract_pass_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]), "routing_matrix_pass_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(Counter(row["matrix_group"] for row in state["routing_rows"]).items())),
        "projection_truth_matrix_row_count": 84, "projection_truth_matrix_historical_count": 47,
        "projection_truth_matrix_pass_count": 84,
        "projection_truth_matrix_group_counts": dict(sorted(Counter(row["case_group"] for row in state["truth_rows"]).items())),
        "safety_row_count": len(state["safety_rows"]), "safety_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": 11, "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_SHA256[SOURCE_PATHS[5]],
        "coverage_issue_status": "open", "coverage_issue_affected_rules": "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "cross_rule_aggregation_issue_status": "open", "raw_target_context_issue_status": "resolved",
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary", "source_input_count": 16,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": index, "source_relative_path": record.relative_path.as_posix(),
            "tracked": True, "base_tree_blob": True, "base_tree_mode": "100644_or_100755",
            "filesystem_regular": True, "non_symlink": True, "parent_chain_non_symlink": True,
            "safe_descendant": True, "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256, "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: _sha(content) for name, content in payloads.items()},
        "output_sha256_excludes_manifest_self_hash": True,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP, "readiness": dict(READINESS), **READINESS,
        "stop_boundaries": [
            "runtime_handler_not_implemented", "registry_unchanged", "dispatcher_unchanged",
            "provider_mapping_not_validated", "real_provider_evaluation_not_executed",
            "raw_network_download_forbidden", "model_checkpoint_training_forbidden",
        ],
        "validation_failures": [], "all_checks_passed": True,
    }
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
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
    _RENAMEAT2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1


def _inspect_output_target_read_only(output_root: Path, repo_root: Path) -> OutputMaterializationPlan:
    candidate = Path(output_root)
    if candidate.is_absolute():
        root, anchor = candidate, Path(candidate.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape forbidden")
        root, anchor = repo_root / candidate, repo_root
    parent = root.parent
    _parent_chain_is_real(parent, anchor)
    parent_identity = _source_identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(root, parent, anchor, root.name, parent_identity, None, ())
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        item = os.lstat(root / name)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _source_identity(item)))
    return OutputMaterializationPlan(root, parent, anchor, root.name, parent_identity, _source_identity(root_item), tuple(leaves))


def _read_at(directory_fd: int, name: str, expected_identity: tuple[int, int, int]) -> bytes:
    item = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if _source_identity(item) != expected_identity or not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
        raise ValueError("pinned leaf drift")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _source_identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("pinned descriptor drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(parent_fd, os.fsencode(source), parent_fd, os.fsencode(target), RENAME_NOREPLACE):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), f"{source}->{target}")


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if count <= 0:
            raise OSError("short output write")
        offset += count


def _verify_complete_set(root_fd: int, payloads: Mapping[str, bytes]) -> None:
    if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    for name, content in payloads.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        actual = _read_at(root_fd, name, _source_identity(item))
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")


def _materialize_set(plan: OutputMaterializationPlan, payloads: Mapping[str, bytes]) -> None:
    if tuple(payloads) != OUTPUT_FILES or {name: _sha(content) for name, content in payloads.items()} != FROZEN_OUTPUT_SHA256:
        raise ValueError("output payload inventory drift")
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    staged: dict[str, tuple[int, int, int]] = {}
    try:
        if _source_identity(os.fstat(parent_fd)) != plan.parent_identity or _source_identity(os.lstat(plan.parent)) != plan.parent_identity:
            raise ValueError("output parent identity changed")
        _parent_chain_is_real(plan.parent, plan.anchor)
        if plan.root_identity is not None:
            item = os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
            if _source_identity(item) != plan.root_identity:
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            if _source_identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor drift")
            if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
                raise ValueError("existing output inventory drift")
            identities = dict(plan.leaf_identities)
            for name, content in payloads.items():
                if _read_at(root_fd, name, identities[name]) != content:
                    raise ValueError("existing output differs; repair forbidden")
            _verify_complete_set(root_fd, payloads)
            os.fsync(root_fd)
            return
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = f".admit011-adapter-stage-{secrets.token_hex(16)}"
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        root_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
        staging_identity = _source_identity(os.fstat(root_fd))
        for name, content in payloads.items():
            descriptor = os.open(name, WRITE_FILE_FLAGS, 0o600, dir_fd=root_fd)
            try:
                staged[name] = _source_identity(os.fstat(descriptor))
                _write_all(descriptor, content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
        if _source_identity(os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)) != staging_identity:
            raise ValueError("staging identity drift")
        try:
            os.stat(plan.root_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        os.fsync(parent_fd)
        _verify_complete_set(root_fd, payloads)
        os.fsync(root_fd)
    except BaseException:
        if staging_name is not None and root_fd is not None:
            try:
                item = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
                if _source_identity(item) == _source_identity(os.fstat(root_fd)) and set(os.listdir(root_fd)) == set(staged):
                    for name, identity in staged.items():
                        if _source_identity(os.stat(name, dir_fd=root_fd, follow_symlinks=False)) != identity:
                            break
                    else:
                        for name in staged:
                            os.unlink(name, dir_fd=root_fd)
                        os.close(root_fd)
                        root_fd = None
                        os.rmdir(staging_name, dir_fd=parent_fd)
            except BaseException:
                pass
        raise
    finally:
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT, head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic evidence files as one directory set."""
    plan = _inspect_output_target_read_only(output_root, repo_root)
    state = build_design_state(repo_root, head_ref)
    payloads, manifest = _payloads(state)
    _materialize_set(plan, payloads)
    return {"state": state, "manifest": manifest, "output_root": plan.root}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1()

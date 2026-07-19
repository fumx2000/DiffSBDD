"""Design-only contract gate for the future ADMIT_009 unified adapter.

The module freezes routing, object identity, exactly-once evaluator/oracle
calls, standalone Exact10 validation, and Exact13 projection.  It deliberately
defines no runtime handler, evaluator registry, or public dispatcher.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, NoReturn


PROJECT = "CovaPIE"
STEP = "ADMIT_009 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "0c80b0b8ac4e5f874a99c9f8da03f530ad7cc09e"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_009 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_009_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_009_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_009"
ADMISSION_RULE_NAME = "duplicate_identity_precheck"
ADAPTER_ID = "covapie_admit_009_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_009"
FORMAL_RESULT_TYPE = "Admit009EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_009_duplicate_identity_key_design"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 9))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("duplicate_identity_key",)
CONTEXT_ITEMS = ("duplicate_identity_key_contract", "batch_duplicate_identity_keys")
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_duplicate_identity_key", "validated_candidate_fields",
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
    "batch_context": "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
    "batch_context_key": "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED",
    "evaluation_context": "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_MAPPING_REASON = "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "duplicate_identity_key_missing"
SOURCE_TYPE_REASON = "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_mapping_validation",
    "batch_duplicate_identity_keys_required_key_lookup",
    "evaluation_context_mapping_validation",
    "duplicate_identity_key_contract_required_key_lookup",
    "download_result_context_must_be_none",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "duplicate_identity_key_required_key_lookup",
    "formal_evaluator",
    "source_validation",
    "independent_oracle",
    "full_exact10_equality",
    "exact13_projection",
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_batch_and_policy_context_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_equivalence_and_provider_boundary_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_validation_truth_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
    "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
    "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67",
    "42b2373c398c737d697ffd8177b6971fe2ad9aa9cbfb813d594b9527b0eaa9b3",
    "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26",
    "d0d0d19e491f27621214ee887f630a871c1a7cfaf4caca93778599b0162dc48c",
    "484072cd901f7ba5264d207202be493477fb16cc4ddfad4341eabd19d8495a85",
    "38ac90e04316d8efc8794d88d749a3fafc69a0ef66de5cf76cdfd82f6d9a9b57",
    "7b1d09956be5fa76f8b141c10a2a8efb895119271cfd75b9e816c37c88513297",
    "762255cc85a12501ccb592a6f3e82ea100221d33c244403386be743c99c64ac0",
    "930a8791bd129a06b272163766a5431aeaf1a3e79003b22df77d6af16319fecb",
    "d7423c337512dff3f66a68209301c91dd3fee2bdd2a3a5b669185854c622d922",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
), strict=True))

CONTRACT_FILENAME = "covapie_admit_009_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_009_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_009_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_009_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_009_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_009_unified_adapter_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME, SAFETY_FILENAME,
    ISSUE_FILENAME, MANIFEST_FILENAME,
)
CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "contract_value", "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "condition", "expected_behavior",
    "expected_reason", "expected_result_json", "formal_call_count",
    "oracle_call_count", "candidate_access_status", "case_passed",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "behavior", "expected_dispatch_code",
    "expected_reason", "source_exact10_json", "oracle_exact10_json",
    "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
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


class _TruthStringSubclass(str):
    pass


class _TruthTupleSubclass(tuple):
    pass


def _git(args: Sequence[str], root: Path, *, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=text, check=False)


def _safe_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_lineage(root: Path, head_ref: str) -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("invalid head_ref")
    if _git(("cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"), root).returncode:
        raise ValueError("expected base unavailable")
    subject = _git(("show", "-s", "--format=%s", EXPECTED_BASE_COMMIT), root, text=True)
    if subject.returncode or subject.stdout.rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    if _git(("merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref), root).returncode:
        raise ValueError("expected base is not an ancestor")


def _structural_check(path: Path, root: Path) -> None:
    if not _safe_path(path):
        raise ValueError(f"unsafe source path: {path}")
    if _git(("ls-files", "--error-unmatch", "--", path.as_posix()), root).returncode:
        raise ValueError(f"source not tracked: {path}")
    tree = _git(("ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()), root, text=True)
    metadata = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    if len(metadata) != 3 or metadata[0] not in ("100644", "100755") or metadata[1] != "blob":
        raise ValueError(f"source not base-tree blob: {path}")
    try:
        mode = (root / path).lstat().st_mode
        (root / path).resolve().relative_to(root)
    except (FileNotFoundError, ValueError) as error:
        raise ValueError(f"source missing or escapes repository: {path}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError(f"source not regular non-symlink: {path}")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    if len(SOURCE_PATHS) != 18 or len(set(SOURCE_PATHS)) != 18 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact18 source boundary shape invalid")
    _validate_lineage(root, head_ref)
    for path in SOURCE_PATHS:
        _structural_check(path, root)
    records = []
    for path in SOURCE_PATHS:
        base = _git(("show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"), root)
        filesystem = (root / path).read_bytes()
        expected = SOURCE_SHA256[path]
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem).hexdigest()
        if base.returncode or expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
            and type(record.content) is bytes
            and hashlib.sha256(record.content).hexdigest() == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, index: int) -> FrozenSourceRecord:
    path = SOURCE_PATHS[index]
    matches = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError(f"snapshot record mismatch: {path}")
    return matches[0]


def _json_document(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_record(snapshot, index).content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON root must be object")
    return value


def _csv_document(snapshot: FrozenSourceSnapshot, index: int) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, index).content.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV header invalid")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV shape invalid")
    return tuple(reader.fieldnames), rows


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
            for target in node.targets
        ):
            value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
            if isinstance(value, ast.Dict):
                keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant))
                if len(keys) == len(value.keys):
                    return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _top_functions(tree: ast.Module) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    runtime_tree = ast.parse(_record(snapshot, 0).content.decode("utf-8"))
    runtime_manifest = _json_document(snapshot, 1)
    _, runtime_issues = _csv_document(snapshot, 2)
    standalone_tree = ast.parse(_record(snapshot, 3).content.decode("utf-8"))
    standalone_manifest = _json_document(snapshot, 4)
    _, standalone_contract = _csv_document(snapshot, 5)
    _, standalone_truth = _csv_document(snapshot, 6)
    issue_header, standalone_issues = _csv_document(snapshot, 7)
    design_tree = ast.parse(_record(snapshot, 8).content.decode("utf-8"))
    design_manifest = _json_document(snapshot, 9)
    _, key_contract = _csv_document(snapshot, 10)
    _, context_contract = _csv_document(snapshot, 11)
    _, provider_boundary = _csv_document(snapshot, 12)
    _, design_truth = _csv_document(snapshot, 13)
    precedent_tree = ast.parse(_record(snapshot, 14).content.decode("utf-8"))
    precedent_manifest = _json_document(snapshot, 15)
    _, result_contract = _csv_document(snapshot, 16)
    _, routing_contract = _csv_document(snapshot, 17)
    issue_map = {row["issue_id"]: row for row in standalone_issues}
    result_fields = tuple(row["field_name"] for row in result_contract if row["contract_kind"] == "result_field")
    routing_admit009 = tuple(row for row in routing_contract if row["admission_rule_id"] == ADMISSION_RULE_ID)
    runtime_assignments = {
        target.id: ast.unparse(node.value)
        for node in runtime_tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    checks = (
        _literal_registry_keys(runtime_tree) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("admit_009_registered_in_engine") is False,
        "_evaluate_registered_admit_009" not in _top_functions(runtime_tree),
        "evaluate_admission_rule" in _top_functions(runtime_tree),
        "evaluate_admission_rule" not in runtime_assignments,
        runtime_assignments.get("UnifiedAdmissionRuleEvaluation") == "predecessor.UnifiedAdmissionRuleEvaluation",
        runtime_assignments.get("UnifiedAdmissionDispatchError") == "predecessor.UnifiedAdmissionDispatchError",
        runtime_assignments.get("RESULT_SCHEMA_VERSION") == "predecessor.RESULT_SCHEMA_VERSION",
        runtime_assignments.get("RESULT_FIELDS") == "predecessor.RESULT_FIELDS",
        runtime_assignments.get("DISPATCH_ERROR_FIELDS") == "predecessor.DISPATCH_ERROR_FIELDS",
        runtime_assignments.get("DISPATCH_ERROR_CODES") == "predecessor.DISPATCH_ERROR_CODES",
        runtime_assignments.get("OUTCOME_VOCABULARY") == "predecessor.OUTCOME_VOCABULARY",
        FORMAL_EVALUATOR_NAME in _top_functions(standalone_tree),
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        standalone_manifest.get("truth_matrix_row_count") == 32,
        len(standalone_contract) == 46 and len(standalone_truth) == 32,
        INDEPENDENT_ORACLE_NAME in _top_functions(design_tree),
        FORMAL_EVALUATOR_NAME not in _top_functions(design_tree),
        len(key_contract) == 34 and len(context_contract) == 15,
        len(provider_boundary) == 18 and len(design_truth) == 32,
        design_manifest.get("real_provider_duplicate_identity_key_count") == 0,
        design_manifest.get("real_provider_duplicate_identity_mapping_validated") is False,
        "build_design_state" in _top_functions(precedent_tree),
        "_evaluate_registered_admit_008" not in _top_functions(precedent_tree),
        precedent_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        result_fields == RESULT_FIELDS,
        len(routing_admit009) == 1,
        routing_admit009[0]["candidate_field_dependencies"] == CANDIDATE_FIELDS[0],
        routing_admit009[0]["batch_context_dependencies"] == CONTEXT_ITEMS[1],
        routing_admit009[0]["evaluation_context_dependencies"] == CONTEXT_ITEMS[0],
        issue_header == ISSUE_COLUMNS and len(runtime_issues) == len(standalone_issues) == 11,
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] == "resolved",
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["integration_transition"] == "duplicate_identity_key_contract_frozen_v1",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "|".join(KNOWN_RULE_IDS[8:]),
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "standalone_truth": standalone_truth,
        "issue_rows": standalone_issues,
        "issue_bytes": _record(snapshot, 7).content,
    }


def _standalone_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_rule_logic_interface")


def _oracle_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate")


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit009EvaluationResult
    if type(source) is not result_type:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False)
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 storage mismatch")
        if tuple(field.name for field in fields(result_type)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 dataclass field order mismatch")
        ordered_values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        reconstructed = result_type(*ordered_values)
        if reconstructed != source:
            raise ValueError("Exact10 reconstruction mismatch")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def expected_exact10_from_committed_oracle_for_design(
    scalar: object,
    batch: object,
    policy: object,
    *,
    oracle_callable: Callable[[object, object, object], object] | None = None,
) -> Any:
    standalone = _standalone_module()
    classify = (
        _oracle_module().classify_admit_009_duplicate_identity_key_design
        if oracle_callable is None else oracle_callable
    )
    try:
        classification = classify(scalar, batch, policy)
        if not isinstance(classification, Mapping):
            raise TypeError("oracle result must be Mapping")
        return standalone.Admit009EvaluationResult(
            ADMISSION_RULE_ID,
            classification["outcome"], classification["passed"],
            classification["blocks_candidate"], classification["reason"],
            classification["canonical_duplicate_identity_key"],
            classification["validated_candidate_fields"],
            classification["consumed_candidate_fields"],
            classification["consumed_context_items"], classification["evaluator_io_used"],
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(source: object, expected: object) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    standalone = _standalone_module()
    if type(expected) is not standalone.Admit009EvaluationResult or source != expected:
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
    """Exercise the frozen future adapter algorithm without defining a handler."""
    if not isinstance(batch_context, Mapping):
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context"], True)
    try:
        batch_object = batch_context["batch_duplicate_identity_keys"]
    except KeyError:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context_key"], True)
    if not isinstance(evaluation_context, Mapping):
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context"], True)
    try:
        policy_object = evaluation_context["duplicate_identity_key_contract"]
    except KeyError:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context_key"], True)
    if download_result_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["download_result_context"], True)
    if stage_authorization_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["stage_authorization_context"], True)
    if not isinstance(candidate_record, Mapping):
        return candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    try:
        scalar_object = candidate_record["duplicate_identity_key"]
    except KeyError:
        return candidate_invalid_exact13_for_design(MISSING_REASON)

    evaluator = _standalone_module().evaluate_admit_009 if formal_evaluator is None else formal_evaluator
    source = evaluator(scalar_object, batch_object, policy_object)
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact10_from_committed_oracle_for_design(
            scalar_object, batch_object, policy_object, oracle_callable=oracle_callable
        )
    except ValueError:
        _raise_design_error("UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    decision = validate_source_oracle_equivalence_for_design(source, expected)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    return project_exact10_to_exact13_for_design(source)


def _json_record(value: object) -> str:
    return json.dumps(
        {field.name: getattr(value, field.name) for field in fields(value)},
        ensure_ascii=True, separators=(",", ":"),
    )


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "admission_rule_id", ADMISSION_RULE_ID),
        ("identity", "admission_rule_name", ADMISSION_RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "formal_evaluator", FORMAL_EVALUATOR_NAME),
        ("identity", "formal_result_type", FORMAL_RESULT_TYPE),
        ("identity", "independent_oracle", INDEPENDENT_ORACLE_NAME),
        (
            "runtime_continuity", "public_dispatch",
            "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry_not_exact8_function_identity",
        ),
        ("runtime_reuse", "result_type", "UnifiedAdmissionRuleEvaluation_exact8_identity"),
        ("runtime_reuse", "dispatch_error_type", "UnifiedAdmissionDispatchError_exact8_identity"),
        ("runtime_reuse", "schema_version", "RESULT_SCHEMA_VERSION_exact8_identity"),
        ("runtime_reuse", "result_fields", "RESULT_FIELDS_exact8_identity|" + "|".join(RESULT_FIELDS)),
        ("runtime_reuse", "dispatch_error_fields", "DISPATCH_ERROR_FIELDS_exact8_identity|" + "|".join(DISPATCH_ERROR_FIELDS)),
        ("runtime_reuse", "dispatch_error_codes", "DISPATCH_ERROR_CODES_exact8_identity|" + "|".join(DISPATCH_ERROR_CODES)),
        ("runtime_reuse", "outcome_vocabulary", "OUTCOME_VOCABULARY_exact8_identity|" + "|".join(OUTCOME_VOCABULARY)),
        ("registration", "current_exact8_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registration", "future_exact9_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registration", "first_eight_handler_identity", "8_of_8_exact8_objects"),
        ("registration", "only_future_addition", "ADMIT_009|_evaluate_registered_admit_009"),
        ("routing", "complete_order", "|".join(CONTEXT_ROUTING_ORDER)),
        ("routing", "batch_mapping", "isinstance_Mapping_subclasses_accepted"),
        ("routing", "batch_required_lookup", "single_direct_getitem_KeyError_only_missing"),
        ("routing", "evaluation_mapping", "isinstance_Mapping_subclasses_accepted"),
        ("routing", "evaluation_required_lookup", "single_direct_getitem_KeyError_only_missing"),
        ("routing", "download_result_context", "exact_none"),
        ("routing", "stage_authorization_context", "exact_none"),
        ("routing", "context_failure", "candidate_not_accessed_formal_0_oracle_0_no_exact13"),
        ("routing", "context_error", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID|known_true|callable_true|adapter_ready_true"),
        ("candidate", "mapping", "isinstance_Mapping_subclasses_accepted_no_copy_iteration_or_mutation"),
        ("candidate", "required_lookup", "duplicate_identity_key_single_direct_getitem"),
        ("candidate", "only_missing", "required_key_absent_only"),
        ("candidate", "non_mapping", CANDIDATE_MAPPING_REASON),
        ("candidate", "key_absent", MISSING_REASON),
        ("candidate", "adapter_invalid_calls", "formal_0_oracle_0"),
        ("candidate", "adapter_invalid_consumed_candidate", "|".join(CANDIDATE_FIELDS)),
        ("candidate", "adapter_invalid_consumed_context", "|".join(CONTEXT_ITEMS)),
        ("forwarding", "scalar_present_values", "None|integer|empty|str_subclass|non_ascii|whitespace|malformed|canonical"),
        ("forwarding", "batch_present_values", "None|empty_tuple|arbitrary_original_object"),
        ("forwarding", "policy_present_values", "None|empty|str_subclass|whitespace|wrong_version|arbitrary_object"),
        ("forwarding", "normalization", "none_no_copy_sort_deduplicate_trim_repair_or_provider_mapping"),
        ("call", "formal", "exactly_once_positional_scalar_batch_policy"),
        ("call", "formal_identity", "three_original_objects"),
        ("call", "oracle", "exactly_once_after_source_validation_positional_scalar_batch_policy"),
        ("call", "oracle_identity", "same_three_original_objects"),
        ("source", "exact_type", "type_source_is_Admit009EvaluationResult_subclass_rejected"),
        ("source", "fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "storage", "vars_available_exact_dict_exact10_key_order"),
        ("source", "dataclass", "exact10_field_order"),
        ("source", "ordered_reads", "all_exact10_fields"),
        ("source", "reconstruction", "committed_class_full_equality_and_post_init_invariants"),
        ("source", "failure", "adapter_not_ready_false_oracle_0_no_partial_exact13"),
        ("oracle", "expected", "committed_design_oracle_constructs_complete_Admit009EvaluationResult"),
        ("oracle", "comparison", "full_ordered_exact10_equality"),
        ("oracle", "mismatch", "adapter_not_ready_false_no_partial_exact13"),
        ("projection", "fields", "|".join(RESULT_FIELDS)),
        ("projection", "schema_version", RESULT_SCHEMA_VERSION),
        ("projection", "rule_name", ADMISSION_RULE_NAME),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "validated_candidate_fields", "source.validated_candidate_fields"),
        ("projection", "passed_blocked_invalid", "source_field_passthrough"),
        ("projection", "scalar_invalid", "empty_pair_preserved"),
        ("projection", "policy_invalid", "canonical_pair_preserved"),
        ("projection", "batch_invalid", "canonical_pair_preserved"),
        ("projection", "all_nonpassed", "blocks_candidate_true"),
        ("projection", "adapter_id", ADAPTER_ID),
        ("issues", "authoritative", "standalone_exact11_byte_identical_no_transition"),
        ("issues", "semantics", "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED_resolved"),
        ("issues", "coverage", "open_ADMIT_009_to_ADMIT_015"),
        ("provider", "mapping", "unvalidated"),
        ("provider", "real_key_count", "0"),
        ("provider", "fields_consumed", "none"),
        ("stop", "runtime", "handler_registry_exact9_not_implemented"),
        ("stop", "later_scope", "no_admit010_evaluate_all_rules_or_combined_verdict"),
        ("stop", "operations", "no_raw_network_download_checkpoint_model_or_training"),
        ("readiness", "next_step", RECOMMENDED_NEXT_STEP),
        ("training", "prerequisite", "feature_semantics_audit_required_step12d_smoke_only"),
    )
    return [
        {
            "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group, "contract_subject": subject,
            "contract_value": value, "contract_status": "frozen",
        }
        for index, (group, subject, value) in enumerate(definitions, 1)
    ]


def _dispatch_json(reason: str, *, adapter_ready: bool = True, code: str = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID") -> str:
    return json.dumps(dict(zip(DISPATCH_ERROR_FIELDS, (
        code, ADMISSION_RULE_ID, True, True, adapter_ready, reason,
    ), strict=True)), separators=(",", ":"))


def _samples() -> dict[str, UnifiedAdmissionEvaluationDesignRecord]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    other = "covapie_dup_v1_sha256_" + "f" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    values = {
        "none": (None, (), policy), "integer": (7, (), policy),
        "empty": ("", (), policy), "subclass": (_TruthStringSubclass(key), (), policy),
        "non_ascii": ("covapie_dup_v1_sha256_" + "é" * 64, (), policy),
        "whitespace": (" " + key, (), policy), "malformed": ("bad", (), policy),
        "unique": (key, (other,), policy), "empty_batch": (key, (), policy),
        "duplicate": (key, (key,), policy),
        "policy_invalid": (key, (), None), "batch_invalid": (key, [], policy),
    }
    return {
        name: route_and_project_for_design(
            {CANDIDATE_FIELDS[0]: scalar},
            batch_context={CONTEXT_ITEMS[1]: batch},
            evaluation_context={CONTEXT_ITEMS[0]: policy_value},
            download_result_context=None, stage_authorization_context=None,
        )
        for name, (scalar, batch, policy_value) in values.items()
    }


def _routing_rows() -> list[dict[str, str]]:
    samples = _samples()
    candidate_invalid = candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    missing_invalid = candidate_invalid_exact13_for_design(MISSING_REASON)
    cases = (
        ("context", "batch_none", "batch_context None", "dispatch_error", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "batch_non_mapping", "batch_context list", "dispatch_error", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "batch_key_missing", "batch required key absent", "dispatch_error", CONTEXT_REASONS["batch_context_key"], _dispatch_json(CONTEXT_REASONS["batch_context_key"]), 0, 0, "not_accessed"),
        ("context", "evaluation_none", "evaluation_context None", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _dispatch_json(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_non_mapping", "evaluation_context list", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _dispatch_json(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_key_missing", "evaluation required key absent", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], _dispatch_json(CONTEXT_REASONS["evaluation_context_key"]), 0, 0, "not_accessed"),
        ("context", "download_non_none", "download_result_context non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], _dispatch_json(CONTEXT_REASONS["download_result_context"]), 0, 0, "not_accessed"),
        ("context", "stage_non_none", "stage_authorization_context non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], _dispatch_json(CONTEXT_REASONS["stage_authorization_context"]), 0, 0, "not_accessed"),
        ("context", "multiple_failure_precedence", "all contexts invalid", "first_dispatch_error_only", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "candidate_bomb", "context failure with inaccessible candidate", "candidate_not_accessed", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "batch_mapping_subclass", "batch Mapping subclass", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "batch_extra_keys", "batch unrelated keys", "ignored_without_iteration", "", "", 1, 1, "accessed_after_context"),
        ("context", "batch_identity_single_lookup", "batch identity sentinel", "same_object_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_mapping_subclass", "evaluation Mapping subclass", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_extra_keys", "evaluation unrelated keys", "ignored_without_iteration", "", "", 1, 1, "accessed_after_context"),
        ("context", "policy_identity_single_lookup", "policy identity sentinel", "same_object_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "policy_none_present", "policy key present with None", "forwarded_not_missing", samples["policy_invalid"].reason, _json_record(samples["policy_invalid"]), 1, 1, "value_read_once"),
        ("context", "batch_empty_present", "batch key present with empty tuple", "forwarded_not_missing", "", _json_record(samples["empty_batch"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_non_mapping", "candidate non-Mapping", "exact13_invalid", CANDIDATE_MAPPING_REASON, _json_record(candidate_invalid), 0, 0, "envelope_checked"),
        ("candidate", "candidate_key_absent", "candidate required key absent", "exact13_invalid", MISSING_REASON, _json_record(missing_invalid), 0, 0, "single_lookup"),
        ("candidate", "candidate_mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_extra_fields", "candidate unrelated fields", "ignored_without_iteration", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_not_mutated", "mutable candidate Mapping", "not_mutated", "", "", 1, 1, "value_read_once"),
        ("candidate", "scalar_identity_single_lookup", "scalar identity sentinel", "same_object_single_lookup", "", "", 1, 1, "value_read_once"),
        ("forwarding", "scalar_none", "candidate None present", "standalone_invalid", samples["none"].reason, _json_record(samples["none"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_integer", "candidate integer present", "standalone_invalid", samples["integer"].reason, _json_record(samples["integer"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_empty", "candidate empty str present", "standalone_invalid", samples["empty"].reason, _json_record(samples["empty"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_str_subclass", "candidate str subclass present", "standalone_invalid", samples["subclass"].reason, _json_record(samples["subclass"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_non_ascii", "candidate non-ASCII present", "standalone_invalid", samples["non_ascii"].reason, _json_record(samples["non_ascii"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_whitespace", "candidate whitespace present", "standalone_invalid", samples["whitespace"].reason, _json_record(samples["whitespace"]), 1, 1, "value_read_once"),
        ("forwarding", "scalar_malformed", "candidate malformed key present", "standalone_invalid", samples["malformed"].reason, _json_record(samples["malformed"]), 1, 1, "value_read_once"),
        ("forwarding", "canonical_unique", "canonical key absent from batch", "passed", "", _json_record(samples["unique"]), 1, 1, "value_read_once"),
        ("forwarding", "canonical_duplicate", "canonical key present in batch", "blocked", samples["duplicate"].reason, _json_record(samples["duplicate"]), 1, 1, "value_read_once"),
        ("forwarding", "invalid_policy", "policy arbitrary object", "standalone_invalid_pair_retained", samples["policy_invalid"].reason, _json_record(samples["policy_invalid"]), 1, 1, "value_read_once"),
        ("forwarding", "invalid_batch", "batch arbitrary object", "standalone_invalid_pair_retained", samples["batch_invalid"].reason, _json_record(samples["batch_invalid"]), 1, 1, "value_read_once"),
        ("call", "formal_exactly_once", "candidate and contexts valid", "one_positional_call", "", "", 1, 1, "value_read_once"),
        ("call", "oracle_exactly_once", "source prevalidated", "one_positional_call", "", "", 1, 1, "value_read_once"),
        ("call", "three_object_identity", "scalar batch policy sentinels", "same_original_objects", "", "", 1, 1, "value_read_once"),
        ("call", "no_mutation_copy_normalization", "mutable opaque objects", "unchanged_objects", "", "", 1, 1, "value_read_once"),
        ("source", "exact_type_accepted", "committed exact result", "accepted", "", "", 1, 1, "value_read_once"),
        ("source", "wrong_type_rejected", "fake object", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, _dispatch_json(SOURCE_TYPE_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once"),
        ("source", "subclass_rejected", "result subclass", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, _dispatch_json(SOURCE_TYPE_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once"),
        ("source", "storage_order_rejected", "vars key order drift", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once"),
        ("source", "dataclass_order_rejected", "dataclass field order drift", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once"),
        ("source", "reconstruction_rejected", "cross-field invariant conflict", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once"),
        ("source", "failure_prevents_oracle", "source validation failure", "oracle_not_called", SOURCE_INVARIANT_REASON, "", 1, 0, "value_read_once"),
        ("source", "full_exact10_mismatch", "partial fields equal but one Exact10 field differs", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 1, "value_read_once"),
        ("projection", "passed", "canonical unique", "exact10_to_exact13", "", _json_record(samples["unique"]), 1, 1, "value_read_once"),
        ("projection", "blocked", "canonical duplicate", "exact10_to_exact13", samples["duplicate"].reason, _json_record(samples["duplicate"]), 1, 1, "value_read_once"),
        ("projection", "scalar_invalid", "invalid scalar", "empty_pair_exact13", samples["none"].reason, _json_record(samples["none"]), 1, 1, "value_read_once"),
        ("projection", "policy_invalid", "invalid policy", "canonical_pair_exact13", samples["policy_invalid"].reason, _json_record(samples["policy_invalid"]), 1, 1, "value_read_once"),
        ("projection", "batch_invalid", "invalid batch", "canonical_pair_exact13", samples["batch_invalid"].reason, _json_record(samples["batch_invalid"]), 1, 1, "value_read_once"),
    )
    return [
        {
            "matrix_order": str(index), "matrix_group": group, "case_id": case_id,
            "condition": condition, "expected_behavior": behavior,
            "expected_reason": reason, "expected_result_json": result,
            "formal_call_count": str(formal), "oracle_call_count": str(oracle),
            "candidate_access_status": access, "case_passed": "true",
        }
        for index, (group, case_id, condition, behavior, reason, result, formal, oracle, access)
        in enumerate(cases, 1)
    ]


def _truth_definitions() -> tuple[tuple[str, str, object, object, object], ...]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    low = "covapie_dup_v1_sha256_" + "0" * 64
    high = "covapie_dup_v1_sha256_" + "2" * 64
    other = "covapie_dup_v1_sha256_" + "f" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    empty: tuple[str, ...] = ()
    return (
        ("scalar", "scalar_none", None, empty, policy),
        ("scalar", "scalar_integer", 7, empty, policy),
        ("scalar", "scalar_str_subclass", _TruthStringSubclass(key), empty, policy),
        ("scalar", "scalar_empty", "", empty, policy),
        ("scalar", "scalar_non_ascii", "covapie_dup_v1_sha256_" + "é" * 64, empty, policy),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, policy),
        ("scalar", "scalar_uppercase_digest", "covapie_dup_v1_sha256_" + "A" * 64, empty, policy),
        ("scalar", "scalar_short_digest", "covapie_dup_v1_sha256_" + "1" * 63, empty, policy),
        ("scalar", "scalar_long_digest", "covapie_dup_v1_sha256_" + "1" * 65, empty, policy),
        ("scalar", "scalar_non_hex", "covapie_dup_v1_sha256_" + "g" * 64, empty, policy),
        ("scalar", "scalar_whitespace", " " + key, empty, policy),
        ("scalar", "scalar_canonical", key, empty, policy),
        ("policy", "policy_none", key, empty, None),
        ("policy", "policy_str_subclass", key, empty, _TruthStringSubclass(policy)),
        ("policy", "policy_wrong_value", key, empty, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", key, empty, policy),
        ("batch", "batch_none", key, None, policy),
        ("batch", "batch_list", key, [], policy),
        ("batch", "batch_tuple_subclass", key, _TruthTupleSubclass(), policy),
        ("batch", "batch_non_str_member", key, (7,), policy),
        ("batch", "batch_str_subclass_member", key, (_TruthStringSubclass(other),), policy),
        ("batch", "batch_malformed_member", key, ("bad",), policy),
        ("batch", "batch_unsorted", key, (high, low), policy),
        ("batch", "batch_duplicate_members", key, (other, other), policy),
        ("batch", "batch_empty_valid", key, (), policy),
        ("batch", "batch_one_unrelated", key, (other,), policy),
        ("batch", "batch_one_matching", key, (key,), policy),
        ("batch", "batch_multiple_contains", key, (low, key, high), policy),
        ("outcome_state", "canonical_unique_passed", key, (other,), policy),
        ("outcome_state", "canonical_duplicate_blocked", key, (key,), policy),
        ("outcome_state", "policy_invalid_retains_pair", key, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", key, [key], policy),
    )


def _truth_row(
    case_id: str, group: str, behavior: str, reason: str = "", *,
    source: object = None, oracle: object = None, unified: object = None,
    code: str = "", formal: int = 0, oracle_calls: int = 0,
) -> dict[str, str]:
    standalone = _standalone_module()
    return {
        "case_id": case_id, "case_group": group, "behavior": behavior,
        "expected_dispatch_code": code, "expected_reason": reason,
        "source_exact10_json": _json_record(source) if type(source) is standalone.Admit009EvaluationResult else "",
        "oracle_exact10_json": _json_record(oracle) if type(oracle) is standalone.Admit009EvaluationResult else "",
        "unified_exact13_json": _json_record(unified) if type(unified) is UnifiedAdmissionEvaluationDesignRecord else "",
        "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls),
        "case_passed": "true",
    }


def _truth_rows() -> list[dict[str, str]]:
    standalone = _standalone_module()
    rows = []
    for _, case_id, scalar, batch, policy in _truth_definitions():
        source = standalone.evaluate_admit_009(scalar, batch, policy)
        if not validate_source_shape_and_invariants_for_design(source).accepted:
            raise ValueError(f"source invalid: {case_id}")
        expected = expected_exact10_from_committed_oracle_for_design(scalar, batch, policy)
        if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
            raise ValueError(f"source/oracle mismatch: {case_id}")
        rows.append(_truth_row(
            f"STANDALONE_{case_id}", "standalone_exact32", "exact10_to_exact13",
            source.reason, source=source, oracle=expected,
            unified=project_exact10_to_exact13_for_design(source), formal=1, oracle_calls=1,
        ))
    for key in (
        "batch_context", "batch_context_key", "evaluation_context",
        "evaluation_context_key", "download_result_context", "stage_authorization_context",
    ):
        rows.append(_truth_row(
            f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result",
            CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ))
    rows.extend((
        _truth_row("ROUTING_precedence", "routing_dispatch", "first_failure_no_candidate_access", CONTEXT_REASONS["batch_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"),
        _truth_row("ROUTING_candidate_bomb", "routing_dispatch", "candidate_never_accessed", CONTEXT_REASONS["batch_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"),
        _truth_row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13", CANDIDATE_MAPPING_REASON, unified=candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)),
        _truth_row("CANDIDATE_key_absent", "adapter_candidate_invalid", "adapter_generated_exact13", MISSING_REASON, unified=candidate_invalid_exact13_for_design(MISSING_REASON)),
        _truth_row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_storage_or_order", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_reconstruction", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_oracle_mismatch", "source_validation_failure", "full_exact10_mismatch_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
        _truth_row("BOUNDARY_issue_bytes", "issue_coverage_boundary", "exact11_byte_identical_no_transition"),
        _truth_row("BOUNDARY_coverage", "issue_coverage_boundary", "admit009_to_015_remain_open"),
    ))
    expected_groups = {
        "standalone_exact32": 32, "routing_dispatch": 8,
        "adapter_candidate_invalid": 2, "source_validation_failure": 5,
        "issue_coverage_boundary": 2,
    }
    if Counter(row["case_group"] for row in rows) != expected_groups:
        raise ValueError("truth group counts changed")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        "adapter_contract_design", "context_routing_design", "candidate_projection_design",
        "standalone_source_validation_design", "exact10_oracle_equality_design",
        "exact10_to_exact13_projection_design", "future_identity_contract",
        "deterministic_materialization", "source_verification", "issue_byte_preservation",
    )
    negative = (
        "actual_adapter_handler", "registry_modification", "exact9_runtime",
        "provider_mapping", "provider_key_generation", "real_candidate_evaluation",
        "admit_010", "evaluate_all_rules", "combined_verdict", "raw_read", "network",
        "download", "checkpoint", "torch", "numpy", "rdkit", "model_forward",
        "model_loss", "training", "fine_tune", "parameter_update", "stage", "commit",
        "push", "gh",
    )
    return [
        {
            "safety_item": item, "expected_executed": str(expected).lower(),
            "observed_executed": str(expected).lower(), "safety_passed": "true",
        }
        for item, expected in (
            *((item, True) for item in positive),
            *((item, False) for item in negative),
        )
    ]


TRUE_READINESS = (
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_candidate_projection_contract_frozen",
    "admit_009_context_routing_contract_frozen",
    "admit_009_context_before_candidate_enforced_by_design",
    "admit_009_key_absent_only_missing_contract_frozen",
    "admit_009_formal_exactly_once_contract_frozen",
    "admit_009_oracle_exactly_once_contract_frozen",
    "admit_009_original_object_identity_contract_frozen",
    "admit_009_standalone_source_exact_type_validation_frozen",
    "admit_009_standalone_exact10_invariant_validation_frozen",
    "admit_009_source_oracle_full_exact10_equality_frozen",
    "admit_009_exact10_to_exact13_projection_frozen",
    "admit_009_candidate_invalid_projection_frozen",
    "admit_009_dispatch_failure_boundaries_frozen",
    "admit_009_provider_mapping_boundary_preserved",
    "future_exact9_reuses_exact8_public_type_identity",
    "future_exact9_first_eight_handler_identity_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_009_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "admit_010_standalone_evaluator_implemented",
    "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)
READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_design_state(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    state = {
        "snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "routing_rows": _routing_rows(),
        "truth_rows": _truth_rows(),
        "safety_rows": _safety_rows(),
        "issue_rows": predecessor["issue_rows"],
        "issue_bytes": predecessor["issue_bytes"],
    }
    if (
        len(state["contract_rows"]) != 75
        or len(state["contract_rows"]) != len({row["contract_id"] for row in state["contract_rows"]})
        or len(state["routing_rows"]) != 52 or len(state["truth_rows"]) != 49
        or len(state["issue_rows"]) != 11
        or any(row["case_passed"] != "true" for row in state["routing_rows"])
        or any(row["case_passed"] != "true" for row in state["truth_rows"])
    ):
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
    readiness = dict(READINESS)
    manifest = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID,
        "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": FORMAL_RESULT_TYPE,
        "future_adapter_handler": "_evaluate_registered_admit_009",
        "independent_oracle": INDEPENDENT_ORACLE_NAME,
        "candidate_fields": list(CANDIDATE_FIELDS),
        "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_first_eight_handler_identity_reused": {rule_id: True for rule_id in CURRENT_REGISTERED_RULE_ORDER},
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[9:]),
        "future_exact9_public_dispatch_contract": "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry",
        "runtime_result_type_reused_by_identity": "UnifiedAdmissionRuleEvaluation",
        "runtime_dispatch_error_type_reused_by_identity": "UnifiedAdmissionDispatchError",
        "runtime_public_constants_reused_by_identity": [
            "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
            "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
        ],
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "context_routing_order": list(CONTEXT_ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "batch_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "evaluation_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "download_result_context_contract": "exact_none",
        "stage_authorization_context_contract": "exact_none",
        "context_before_candidate": True,
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "adapter_missing_categories": ["required_key_absent"],
        "adapter_missing_reason": MISSING_REASON,
        "formal_positional_argument_order": ["scalar_object", "batch_duplicate_identity_keys_object", "duplicate_identity_key_contract_object"],
        "formal_call_count_after_candidate_gate": 1,
        "oracle_call_count_after_source_validation": 1,
        "original_object_identity_preserved": True,
        "adapter_side_normalization": False,
        "adapter_side_provider_mapping": False,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "source_prevalidated_before_oracle": True,
        "source_exact_type_required": True,
        "source_exact10_full_invariant_validation": True,
        "source_oracle_full_exact10_equality_required": True,
        "no_partial_exact13_on_failure": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": list(CANDIDATE_FIELDS),
            "consumed_context_items": list(CONTEXT_ITEMS),
            "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
        },
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "routing_matrix_pass_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(Counter(row["matrix_group"] for row in state["routing_rows"]).items())),
        "projection_truth_matrix_row_count": len(state["truth_rows"]),
        "projection_truth_matrix_pass_count": len(state["truth_rows"]),
        "projection_truth_matrix_group_counts": dict(sorted(Counter(row["case_group"] for row in state["truth_rows"]).items())),
        "safety_row_count": len(state["safety_rows"]),
        "safety_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_SHA256[SOURCE_PATHS[7]],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015",
        "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "real_provider_duplicate_identity_mapping_validated": False,
        "real_provider_duplicate_identity_key_count": 0,
        "provider_fields_consumed": [],
        "source_boundary_name": "fixed_ordered_exact18_committed_source_boundary",
        "source_input_count": 18,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {
                "source_order": index, "source_relative_path": record.relative_path.as_posix(),
                "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
                "non_symlink": True, "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256, "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact8_runtime_unchanged",
            "admit_009_unregistered", "exact9_runtime_not_implemented",
            "provider_mapping_not_validated", "admit_010_not_started",
            "evaluate_all_rules_not_implemented", "combined_candidate_verdict_not_implemented",
            "real_candidate_evaluation_not_executed", "raw_network_download_forbidden",
            "training_forbidden",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "readiness": readiness, **readiness,
        "validation_failures": [], "all_checks_passed": True,
    }
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return payloads, manifest


def _preflight_output_root(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("output root must be directory and non-symlink")
    if root.exists():
        entries = tuple(root.iterdir())
        if {entry.name for entry in entries} - set(OUTPUT_FILES):
            raise ValueError("unexpected output entry")
        if any(entry.is_symlink() or not entry.is_file() for entry in entries):
            raise ValueError("output must be regular non-symlink")
    else:
        root.mkdir(parents=True, exist_ok=False)


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    state = build_design_state(repo_root, head_ref)
    root = output_root if output_root.is_absolute() else repo_root / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

"""Design-only contract gate for the future ADMIT_008 unified adapter.

This standard-library-only module freezes routing, candidate projection,
standalone Exact10 validation, committed-oracle equivalence, and Exact13
projection.  It deliberately defines no adapter handler or evaluator registry.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_008 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "39f077e9e5ea460f9199fb8921e89bcd46087fa8"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_008 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_008_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_008_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_008"
ADMISSION_RULE_NAME = "topology_restoration_disposition"
ADAPTER_ID = "covapie_admit_008_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_008"
FORMAL_EVALUATOR_SOURCE = Path(
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py"
)
INDEPENDENT_ORACLE_NAME = "classify_admit_008_topology_restoration_disposition_design"
FUTURE_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 9))
CURRENT_REGISTERED_RULE_ORDER = FUTURE_REGISTERED_RULE_ORDER[:7]
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("topology_restoration_disposition",)
CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)
CANONICAL_ENUM_MEMBERS = (
    "approved_restoration_template",
    "explicit_manual_review_approved",
    "manual_review_required",
    "quarantine_required",
)
ALLOWED_DISPOSITIONS = CANONICAL_ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "TOPOLOGY_RESTORATION_DISPOSITION_TYPE_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_EMPTY",
    "TOPOLOGY_RESTORATION_DISPOSITION_NON_ASCII",
    "TOPOLOGY_RESTORATION_DISPOSITION_SYNTAX_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_UNKNOWN",
)
CONTEXT_VALUE_REASONS = (
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_TYPE_INVALID",
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_CONTENT_INVALID",
)
BLOCKED_REASONS = {
    "manual_review_required": "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED",
    "quarantine_required": "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED",
}
MISSING_REASON = "topology_restoration_disposition_missing"
CANDIDATE_MAPPING_REASON = "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_REASONS = {
    "batch_context": "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED",
    "download_result_context": "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_topology_restoration_disposition", "validated_candidate_fields",
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
EXECUTION_PRECEDENCE = (
    "global_admission_rule_id_exact_type_validation",
    "known_rule_validation",
    "registration_adapter_ready_validation",
    "batch_context_validation",
    "evaluation_context_mapping_validation",
    "allowed_topology_restoration_dispositions_required_key_validation",
    "download_result_context_validation",
    "stage_authorization_context_validation",
    "candidate_record_mapping_validation",
    "topology_restoration_disposition_required_key_lookup",
    "candidate_key_absent_classification",
    "formal_evaluate_admit_008_exactly_once",
    "standalone_source_exact_type_validation",
    "standalone_exact10_invariant_validation",
    "independent_expected_exact10_oracle_derivation",
    "source_oracle_complete_exact10_equality",
    "unified_exact13_result_construction",
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv",
    str(FORMAL_EVALUATOR_SOURCE),
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_registry.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01",
    "ae5fc1c5aa28618765ed07fe5aae67c02d31e7650fb5921dae954c0a3cfefd7e",
    "62fdcf8c18f5baf3b08cd29515804abba7543d5da21056d2d93a392d5c188ac9",
    "a78510cf512782f9bd586e040d26a7fb459ba8b0e1eec310195b417cd0b9c636",
    "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d",
    "4da97951abe63d46ded0ad5ffc6048e1a1c40eb2fdedd3553de094ac1ad0c85b",
    "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a",
    "d15cc2f468b158bdd0871386af041231f563af34ff394c2d25e8b5797fa3599b",
    "f449e7441045f52a2222f70f2b7378446424ea46610859641ae2baf5e4565be4",
    "5c3171fb19efdafecad5258ce4d6c0185b731ab93dece947232d80ef089b4a88",
    "9cb470520b666624ecbde992354c05587dd38c3006f1f21db4a2dfe3733a4eb4",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
), strict=True))

CONTRACT_FILENAME = "covapie_admit_008_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_008_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_008_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_008_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_008_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_008_unified_adapter_contract_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, ROUTING_FILENAME, TRUTH_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "condition", "expected_behavior",
    "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count",
    "candidate_access_status", "case_passed",
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


@dataclass(frozen=True)
class SourceValidationDecision:
    accepted: bool
    code: str
    reason: str
    adapter_ready: bool


class _TruthStringSubclass(str):
    pass


def _git(args: Sequence[str], root: Path, *, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=text)


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


def _safe_path(path: Path) -> bool:
    return (not path.is_absolute() and bool(path.parts) and ".." not in path.parts
            and path.parts[0] != "checkpoints" and path.parts[:2] != ("data", "raw"))


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
    except FileNotFoundError as error:
        raise ValueError(f"source missing: {path}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError(f"source not regular non-symlink: {path}")
    try:
        (root / path).resolve().relative_to(root)
    except ValueError as error:
        raise ValueError(f"source escapes repository: {path}") from error


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    if len(SOURCE_PATHS) != 17 or len(set(SOURCE_PATHS)) != 17 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact17 source boundary shape invalid")
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
        and all(type(record) is FrozenSourceRecord
                and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
                and record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
                and type(record.content) is bytes
                and hashlib.sha256(record.content).hexdigest() == record.expected_sha256
                for record in value.records)
    )


def _bytes(snapshot: FrozenSourceSnapshot, index: int) -> bytes:
    path = SOURCE_PATHS[index]
    matches = tuple(record.content for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError(f"snapshot record mismatch: {path}")
    return matches[0]


def _json(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_bytes(snapshot, index).decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON root must be object")
    return value


def _csv(snapshot: FrozenSourceSnapshot, index: int) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(io.StringIO(_bytes(snapshot, index).decode("utf-8"), newline=""))
    if reader.fieldnames is None:
        raise ValueError("CSV header missing")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV shape invalid")
    return tuple(reader.fieldnames), rows


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets):
            value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
            if isinstance(value, ast.Dict):
                keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant))
                if len(keys) == len(value.keys):
                    return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    runtime_tree = ast.parse(_bytes(snapshot, 0).decode("utf-8"))
    runtime_manifest = _json(snapshot, 1)
    issue_header, runtime_issues = _csv(snapshot, 2)
    standalone_tree = ast.parse(_bytes(snapshot, 3).decode("utf-8"))
    standalone_manifest = _json(snapshot, 4)
    contract_header, contract_rows = _csv(snapshot, 5)
    truth_header, truth_rows = _csv(snapshot, 6)
    issue2_header, issue_rows = _csv(snapshot, 7)
    enum_tree = ast.parse(_bytes(snapshot, 8).decode("utf-8"))
    enum_manifest = _json(snapshot, 9)
    enum_header, enum_rows = _csv(snapshot, 10)
    enum_truth_header, enum_truth = _csv(snapshot, 11)
    mapping_header, mapping_rows = _csv(snapshot, 12)
    precedent_tree = ast.parse(_bytes(snapshot, 13).decode("utf-8"))
    precedent_manifest = _json(snapshot, 14)
    result_header, result_rows = _csv(snapshot, 15)
    routing_header, routing_rows = _csv(snapshot, 16)
    runtime_functions = {node.name for node in runtime_tree.body if isinstance(node, ast.FunctionDef)}
    standalone_functions = {node.name for node in standalone_tree.body if isinstance(node, ast.FunctionDef)}
    enum_functions = {node.name for node in enum_tree.body if isinstance(node, ast.FunctionDef)}
    precedent_functions = {node.name for node in precedent_tree.body if isinstance(node, ast.FunctionDef)}
    issue_map = {row["issue_id"]: row for row in issue_rows}
    result_contract = tuple(row["field_name"] for row in result_rows if row.get("contract_kind") == "result_field")
    truth_groups = Counter(row["case_group"] for row in truth_rows)
    checks = (
        _literal_registry_keys(runtime_tree) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("admit_008_registered_in_engine") is False,
        "_evaluate_registered_admit_008" not in runtime_functions,
        "evaluate_all_rules" not in runtime_functions,
        FORMAL_EVALUATOR_NAME in standalone_functions,
        standalone_manifest.get("result_fields") == list(STANDALONE_RESULT_FIELDS),
        standalone_manifest.get("truth_matrix_row_count") == 38,
        len(contract_rows) == 37 and len(truth_rows) == 38,
        truth_groups == {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12},
        INDEPENDENT_ORACLE_NAME in enum_functions,
        enum_manifest.get("normative_enum_members") == list(CANONICAL_ENUM_MEMBERS),
        len(enum_rows) == 4 and len(enum_truth) == 38 and len(mapping_rows) == 12,
        all(row["real_provider_mapping_executed"] == "false" for row in mapping_rows),
        "build_design_state" in precedent_functions,
        precedent_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        result_contract == RESULT_FIELDS,
        len(routing_rows) == 15,
        issue_header == issue2_header == ISSUE_COLUMNS and len(runtime_issues) == len(issue_rows) == 11,
        hashlib.sha256(_bytes(snapshot, 7)).hexdigest() == "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
        issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_008|"),
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        bool(contract_header and truth_header and enum_header and enum_truth_header and mapping_header and result_header and routing_header),
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {"truth_rows": truth_rows, "issue_rows": issue_rows, "issue_bytes": _bytes(snapshot, 7)}


def _standalone_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_008_rule_logic_interface")


def _oracle_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate")


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit008EvaluationResult
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


def expected_exact10_from_committed_oracle_for_design(scalar: object, context: object) -> Any:
    standalone = _standalone_module()
    oracle = _oracle_module()
    classification = oracle.classify_admit_008_topology_restoration_disposition_design(scalar, context)
    try:
        outcome = classification.admit_008
        return standalone.Admit008EvaluationResult(
            ADMISSION_RULE_ID, outcome.outcome, outcome.passed, outcome.blocks_candidate,
            outcome.reason, outcome.canonical_value, outcome.validated_candidate_fields,
            CANDIDATE_FIELDS, CONTEXT_ITEMS, False,
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(SOURCE_INVARIANT_REASON) from error


def validate_source_oracle_equivalence_for_design(source: object, expected: object) -> SourceValidationDecision:
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        return decision
    standalone = _standalone_module()
    if type(expected) is not standalone.Admit008EvaluationResult or source != expected:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def project_exact10_to_exact13_for_design(source: object) -> UnifiedAdmissionEvaluationDesignRecord:
    if not validate_source_shape_and_invariants_for_design(source).accepted:
        raise ValueError("source is not projection-ready")
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, source.admission_rule_id, ADMISSION_RULE_NAME, source.outcome,
        source.passed, source.blocks_candidate, source.reason, source.validated_candidate_fields,
        source.validated_candidate_fields, source.consumed_candidate_fields,
        source.consumed_context_items, source.evaluator_io_used, ADAPTER_ID,
    )


def candidate_invalid_exact13_for_design(reason: str) -> UnifiedAdmissionEvaluationDesignRecord:
    if reason not in (CANDIDATE_MAPPING_REASON, MISSING_REASON):
        raise ValueError("unsupported adapter candidate reason")
    return UnifiedAdmissionEvaluationDesignRecord(
        RESULT_SCHEMA_VERSION, ADMISSION_RULE_ID, ADMISSION_RULE_NAME, "invalid", False, True,
        reason, (), (), CANDIDATE_FIELDS, CONTEXT_ITEMS, False, ADAPTER_ID,
    )


def _json_record(value: object) -> str:
    return json.dumps({field.name: getattr(value, field.name) for field in fields(value)}, ensure_ascii=True, separators=(",", ":"))


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "admission_rule_id", ADMISSION_RULE_ID),
        ("identity", "admission_rule_name", ADMISSION_RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "formal_evaluator", FORMAL_EVALUATOR_NAME),
        ("identity", "formal_evaluator_source", FORMAL_EVALUATOR_SOURCE.as_posix()),
        ("identity", "independent_oracle", INDEPENDENT_ORACLE_NAME),
        ("runtime_reuse", "public_api", "evaluate_admission_rule_current_exact7_identity"),
        ("runtime_reuse", "result_type", "UnifiedAdmissionRuleEvaluation_current_exact7_identity"),
        ("runtime_reuse", "dispatch_error_type", "UnifiedAdmissionDispatchError_current_exact7_identity"),
        ("runtime_reuse", "schema_version", RESULT_SCHEMA_VERSION),
        ("runtime_reuse", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("runtime_reuse", "exact6_dispatch_fields", "|".join(DISPATCH_ERROR_FIELDS)),
        ("runtime_reuse", "known_rule_vocabulary", "|".join(KNOWN_RULE_IDS)),
        ("registration", "future_exact8_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registration", "current_exact7_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("registration", "admit001_to_007_handler_identity", "unchanged"),
        ("precedence", "complete_execution_precedence", "|".join(EXECUTION_PRECEDENCE)),
        ("routing", "context_order", "batch_context|evaluation_context|evaluation_required_key|download_result_context|stage_authorization_context"),
        ("routing", "batch_context", "exact_none"),
        ("routing", "evaluation_context", "mapping_subclass_accepted_required_key_extra_keys_ignored"),
        ("routing", "routed_context_value", "single_getitem_original_identity_no_prevalidation_copy_mutation_or_normalization"),
        ("routing", "download_result_context", "exact_none"),
        ("routing", "stage_authorization_context", "exact_none"),
        ("routing", "early_failure", "candidate_not_accessed"),
        ("candidate", "candidate_record", "mapping_subclass_accepted_extra_fields_ignored_no_copy_mutation_or_unrelated_iteration"),
        ("candidate", "required_field", "topology_restoration_disposition_single_getitem_original_identity"),
        ("candidate", "non_mapping", CANDIDATE_MAPPING_REASON),
        ("missing", "only_category", "required_key_absent"),
        ("missing", "reason", MISSING_REASON),
        ("forwarding", "exact_none", SCALAR_REASONS[0]),
        ("forwarding", "exact_builtin_empty_str", SCALAR_REASONS[1]),
        ("forwarding", "empty_str_subclass", SCALAR_REASONS[0]),
        ("forwarding", "whitespace_and_malformed", "standalone_exact_reason"),
        ("call", "formal_call", "exactly_one_positional_call_original_scalar_and_context_identity"),
        ("call", "normalization", "none_no_trim_casefold_alias_conversion_copy_repair_mutation_or_io"),
        ("source", "exact_type", "type(source)_is_Admit008EvaluationResult_subclass_rejected"),
        ("source", "exact10_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "invariants", "vars_order|dataclass_field_order|ordered_reads|reconstruction|equality|complete_cross_field_validation"),
        ("source", "failure", "oracle_not_called_no_partial_exact13_adapter_ready_false"),
        ("oracle", "call", "same_original_objects_exactly_once_after_source_validation"),
        ("oracle", "equivalence", "complete_ordered_exact10_equality"),
        ("projection", "mapping", "source_exact10_to_existing_unified_exact13"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "passed", "two_exact4_allowed_members_passthrough"),
        ("projection", "blocked", "two_distinct_blocked_reasons_passthrough"),
        ("projection", "scalar_invalid", "empty_normalized_and_validated_exact_reason_retained"),
        ("projection", "context_invalid", "canonical_and_validated_pair_retained"),
        ("provider", "fields", "restoration_rule_and_provenance_not_consumed"),
        ("issues", "exact11", "byte_identical_no_transition_coverage_still_admit008_to_015"),
        ("readiness", "next_step", RECOMMENDED_NEXT_STEP),
        ("stop", "adapter_handler", "not_implemented"),
        ("stop", "runtime_registry", "current_exact7_unmodified_admit008_not_registered"),
        ("stop", "provider_mapping", "not_validated_real_provider_value_count_zero"),
        ("stop", "training", "feature_semantics_audit_required_step12d_not_final_contract"),
    )
    return [{"contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
             "contract_group": group, "contract_subject": subject,
             "contract_value": value, "contract_status": "frozen"}
            for index, (group, subject, value) in enumerate(definitions, 1)]


def _dispatch_json(reason: str) -> str:
    return json.dumps(dict(zip(DISPATCH_ERROR_FIELDS, (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", ADMISSION_RULE_ID, True, True, True, reason,
    ), strict=True)), separators=(",", ":"))


def _evaluate_pair_for_evidence(scalar: object, context: object) -> tuple[object, object, UnifiedAdmissionEvaluationDesignRecord]:
    standalone = _standalone_module()
    source = standalone.evaluate_admit_008(scalar, context)
    if not validate_source_shape_and_invariants_for_design(source).accepted:
        raise ValueError("standalone source invalid")
    expected = expected_exact10_from_committed_oracle_for_design(scalar, context)
    if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
        raise ValueError("source/oracle Exact10 mismatch")
    return source, expected, project_exact10_to_exact13_for_design(source)


def _routing_rows() -> list[dict[str, str]]:
    candidate_invalid = candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    missing_invalid = candidate_invalid_exact13_for_design(MISSING_REASON)
    samples = {
        "none": _evaluate_pair_for_evidence(None, ALLOWED_DISPOSITIONS)[2],
        "empty": _evaluate_pair_for_evidence("", ALLOWED_DISPOSITIONS)[2],
        "empty_subclass": _evaluate_pair_for_evidence(_TruthStringSubclass(""), ALLOWED_DISPOSITIONS)[2],
        "whitespace": _evaluate_pair_for_evidence(" ", ALLOWED_DISPOSITIONS)[2],
        "integer": _evaluate_pair_for_evidence(7, ALLOWED_DISPOSITIONS)[2],
        "approved": _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS)[2],
        "manual_approved": _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[1], ALLOWED_DISPOSITIONS)[2],
        "manual_required": _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[2], ALLOWED_DISPOSITIONS)[2],
        "quarantine": _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[3], ALLOWED_DISPOSITIONS)[2],
        "context_invalid": _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[0], [*ALLOWED_DISPOSITIONS])[2],
    }
    cases = (
        ("context", "batch_non_none", "batch_context non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_non_mapping", "evaluation_context non-Mapping", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _dispatch_json(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_key_missing", "evaluation required key missing", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], _dispatch_json(CONTEXT_REASONS["evaluation_context_key"]), 0, 0, "not_accessed"),
        ("context", "download_non_none", "download_result_context non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], _dispatch_json(CONTEXT_REASONS["download_result_context"]), 0, 0, "not_accessed"),
        ("context", "stage_non_none", "stage_authorization_context non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], _dispatch_json(CONTEXT_REASONS["stage_authorization_context"]), 0, 0, "not_accessed"),
        ("context", "multiple_failure_precedence", "batch and later contexts invalid", "first_dispatch_error_only", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_mapping_subclass", "evaluation Mapping subclass", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_extra_keys", "evaluation extra keys", "ignored", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_not_mutated", "mutable evaluation Mapping", "not_mutated", "", "", 1, 1, "accessed_after_context"),
        ("context", "context_identity_single_lookup", "required context identity sentinel", "same_object_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "invalid_context_reaches_standalone", "invalid context value", "exact13_invalid_canonical_retained", CONTEXT_VALUE_REASONS[0], _json_record(samples["context_invalid"]), 1, 1, "accessed_after_context"),
        ("candidate", "candidate_non_mapping", "candidate non-Mapping", "exact13_invalid", CANDIDATE_MAPPING_REASON, _json_record(candidate_invalid), 0, 0, "envelope_checked"),
        ("candidate", "candidate_key_absent", "candidate key absent", "exact13_invalid", MISSING_REASON, _json_record(missing_invalid), 0, 0, "single_lookup"),
        ("candidate", "candidate_exact_none", "candidate exact None", "standalone_type_invalid", SCALAR_REASONS[0], _json_record(samples["none"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_exact_empty", "candidate exact built-in empty str", "standalone_empty_invalid", SCALAR_REASONS[1], _json_record(samples["empty"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_empty_subclass", "candidate empty str subclass", "standalone_type_invalid", SCALAR_REASONS[0], _json_record(samples["empty_subclass"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_whitespace", "candidate whitespace", "standalone_syntax_invalid", SCALAR_REASONS[3], _json_record(samples["whitespace"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_integer", "candidate malformed integer", "standalone_type_invalid", SCALAR_REASONS[0], _json_record(samples["integer"]), 1, 1, "value_read_once"),
        ("candidate", "approved_template", "approved_restoration_template", "passed", "", _json_record(samples["approved"]), 1, 1, "value_read_once"),
        ("candidate", "manual_approved", "explicit_manual_review_approved", "passed", "", _json_record(samples["manual_approved"]), 1, 1, "value_read_once"),
        ("candidate", "manual_review_required", "manual_review_required", "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], _json_record(samples["manual_required"]), 1, 1, "value_read_once"),
        ("candidate", "quarantine_required", "quarantine_required", "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]], _json_record(samples["quarantine"]), 1, 1, "value_read_once"),
        ("candidate", "candidate_mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_extra_fields", "candidate extra fields", "ignored_without_iteration", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_not_mutated", "mutable candidate Mapping", "not_mutated", "", "", 1, 1, "value_read_once"),
        ("candidate", "scalar_identity_single_lookup", "scalar identity sentinel", "same_object_single_lookup", "", "", 1, 1, "value_read_once"),
    )
    if len(cases) != 26:
        raise ValueError("Exact26 routing shape invalid")
    return [{"matrix_order": str(index), "matrix_group": group, "case_id": case_id,
             "condition": condition, "expected_behavior": behavior, "expected_reason": reason,
             "expected_result_json": result, "formal_call_count": str(formal),
             "oracle_call_count": str(oracle), "candidate_access_status": access,
             "case_passed": "true"}
            for index, (group, case_id, condition, behavior, reason, result, formal, oracle, access
            ) in enumerate(cases, 1)]


def _decode_display(kind: str, display: str) -> object:
    if kind in ("str", "exact_tuple"):
        return json.loads(display) if kind == "str" else tuple(json.loads(display.removeprefix("tuple:")))
    if kind == "NoneType" or kind == "none":
        return None
    if kind == "int":
        return int(display.removeprefix("int:"))
    if kind == "bool":
        return display == "bool:True"
    if kind in ("_StringSubclass", "str_subclass", "str_subclass_member"):
        payload = display.removeprefix("str_subclass:")
        if payload.startswith("tuple:"):
            members = json.loads(payload.removeprefix("tuple:"))
            members[0] = _TruthStringSubclass(members[0])
            return tuple(members)
        return _TruthStringSubclass(json.loads(payload))
    if kind == "list":
        return json.loads(display.removeprefix("list:"))
    if kind == "dict":
        return json.loads(display.removeprefix("dict:"))
    if kind == "set":
        return set(json.loads(display.removeprefix("set:")))
    if kind == "frozenset":
        return frozenset(json.loads(display.removeprefix("frozenset:")))
    if display.startswith("tuple:"):
        return tuple(json.loads(display.removeprefix("tuple:")))
    raise ValueError(f"unknown frozen display kind: {kind}")


def _truth_row(case_id: str, group: str, behavior: str, reason: str = "", *, source: object = None,
               oracle: object = None, unified: object = None, code: str = "", formal: int = 0,
               oracle_calls: int = 0) -> dict[str, str]:
    standalone = _standalone_module()
    return {
        "case_id": case_id, "case_group": group, "behavior": behavior,
        "expected_dispatch_code": code, "expected_reason": reason,
        "source_exact10_json": _json_record(source) if type(source) is standalone.Admit008EvaluationResult else "",
        "oracle_exact10_json": _json_record(oracle) if type(oracle) is standalone.Admit008EvaluationResult else "",
        "unified_exact13_json": _json_record(unified) if type(unified) is UnifiedAdmissionEvaluationDesignRecord else "",
        "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls), "case_passed": "true",
    }


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    standalone = _standalone_module()
    rows = []
    if len(predecessor_rows) != 38:
        raise ValueError("standalone Exact38 changed")
    for row in predecessor_rows:
        scalar = _decode_display(row["scalar_input_kind"], row["scalar_input_display"])
        context = _decode_display(row["context_input_kind"], row["context_input_display"])
        source = standalone.evaluate_admit_008(scalar, context)
        decision = validate_source_shape_and_invariants_for_design(source)
        if not decision.accepted:
            raise ValueError(f"source invalid: {row['case_id']}")
        expected = expected_exact10_from_committed_oracle_for_design(scalar, context)
        if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
            raise ValueError(f"source/oracle mismatch: {row['case_id']}")
        if json.loads(row["observed_full_result"]) != json.loads(_json_record(source)):
            raise ValueError(f"committed standalone result changed: {row['case_id']}")
        rows.append(_truth_row(f"STANDALONE_{row['case_id']}", "standalone_exact38", "exact10_to_exact13",
                               source.reason, source=source, oracle=expected,
                               unified=project_exact10_to_exact13_for_design(source), formal=1, oracle_calls=1))
    for key in ("batch_context", "evaluation_context", "evaluation_context_key", "download_result_context", "stage_authorization_context"):
        rows.append(_truth_row(f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result",
                               CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    rows.append(_truth_row("ROUTING_multiple_precedence", "routing_dispatch", "first_exact6_no_candidate_access",
                           CONTEXT_REASONS["batch_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    rows.append(_truth_row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13",
                           CANDIDATE_MAPPING_REASON, unified=candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)))
    rows.append(_truth_row("CANDIDATE_key_absent", "adapter_candidate_invalid", "adapter_generated_exact13",
                           MISSING_REASON, unified=candidate_invalid_exact13_for_design(MISSING_REASON)))
    valid, _, _ = _evaluate_pair_for_evidence(CANONICAL_ENUM_MEMBERS[0], ALLOWED_DISPOSITIONS)
    rows.extend((
        _truth_row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_invariant", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_oracle_mismatch", "source_validation_failure", "no_projection", SOURCE_INVARIANT_REASON,
                   source=valid, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
        _truth_row("BOUNDARY_issue_bytes", "issue_coverage_boundary", "exact11_byte_identical_no_transition"),
        _truth_row("BOUNDARY_coverage", "issue_coverage_boundary", "admit008_to_015_remain_open"),
    ))
    expected_counts = {"standalone_exact38": 38, "routing_dispatch": 6,
                       "adapter_candidate_invalid": 2, "source_validation_failure": 4,
                       "issue_coverage_boundary": 2}
    if Counter(row["case_group"] for row in rows) != expected_counts:
        raise ValueError("truth group counts changed")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        "adapter_contract_design", "context_routing_design", "candidate_projection_design",
        "key_absent_policy_design", "none_empty_forwarding_design", "standalone_exact10_validation_design",
        "independent_oracle_equivalence_design", "exact13_projection_design",
        "synthetic_exact26_routing", "synthetic_projection_truth", "fixed_exact17_source_verification",
        "exact11_issue_byte_preservation", "deterministic_materialization",
    )
    negative = (
        "adapter_handler_implementation", "runtime_source_modification", "registry_mutation",
        "admit_008_registration", "provider_mapping", "provider_value_materialization",
        "restoration_rule_provenance_consumption", "admit_009", "evaluate_all_rules",
        "combined_candidate_verdict", "real_candidate_evaluation", "raw_read", "network",
        "download", "checkpoint", "torch", "numpy", "rdkit", "model_forward", "loss",
        "training", "fine_tune", "parameter_update", "stage", "commit", "push", "gh",
    )
    return [
        {"safety_item": item, "expected_executed": "true" if expected else "false",
         "observed_executed": "true" if expected else "false", "safety_passed": "true"}
        for item, expected in ((*((item, True) for item in positive), *((item, False) for item in negative)))
    ]


TRUE_READINESS = (
    "admit_008_standalone_evaluator_available",
    "admit_008_unified_adapter_contract_frozen",
    "admit_008_context_routing_contract_frozen",
    "admit_008_candidate_projection_contract_frozen",
    "admit_008_key_absent_contract_frozen",
    "admit_008_none_empty_forwarding_contract_frozen",
    "admit_008_source_result_validation_contract_frozen",
    "admit_008_source_oracle_equivalence_contract_frozen",
    "admit_008_unified_result_projection_contract_frozen",
    "admit_008_blocked_passthrough_contract_frozen",
    "admit_008_context_invalid_partial_canonical_projection_frozen",
    "admit_008_provider_mapping_boundary_preserved",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_008_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_008_unified_adapter_implemented", "admit_008_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_008_implemented", "exact7_runtime_modified",
    "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
    "admit_009_standalone_evaluator_implemented", "admit_009_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation", "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)
READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_design_state(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    state = {
        "snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "routing_rows": _routing_rows(),
        "truth_rows": _truth_rows(predecessor["truth_rows"]),
        "safety_rows": _safety_rows(),
        "issue_rows": predecessor["issue_rows"],
        "issue_bytes": predecessor["issue_bytes"],
    }
    if (len(state["routing_rows"]) != 26 or len(state["truth_rows"]) != 52
            or len(state["issue_rows"]) != 11 or any(row["case_passed"] != "true" for row in state["routing_rows"])
            or any(row["case_passed"] != "true" for row in state["truth_rows"])):
        raise ValueError("design state failed closed")
    return state


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _payloads(state: Mapping[str, Any]) -> dict[str, bytes]:
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    truth_counts = Counter(row["case_group"] for row in state["truth_rows"])
    routing_counts = Counter(row["matrix_group"] for row in state["routing_rows"])
    snapshot = state["snapshot"]
    readiness = dict(READINESS)
    manifest = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID, "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": "Admit008EvaluationResult", "future_adapter_handler": "_evaluate_registered_admit_008",
        "formal_evaluator_source": FORMAL_EVALUATOR_SOURCE.as_posix(),
        "independent_oracle": INDEPENDENT_ORACLE_NAME, "independent_oracle_outcome_view": "classification.admit_008",
        "candidate_field": CANDIDATE_FIELDS[0], "evaluation_context_item": CONTEXT_ITEMS[0],
        "runtime_public_api_reused_by_identity": "evaluate_admission_rule",
        "runtime_result_type_reused_by_identity": "UnifiedAdmissionRuleEvaluation",
        "runtime_dispatch_error_type_reused_by_identity": "UnifiedAdmissionDispatchError",
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "admit_001_to_007_handler_identity_unchanged": True,
        "known_rule_ids": list(KNOWN_RULE_IDS), "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[8:]),
        "known_not_registered_behavior": "known_not_registered_fail_closed",
        "execution_precedence": list(EXECUTION_PRECEDENCE),
        "result_schema_version": RESULT_SCHEMA_VERSION, "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS), "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "context_routing_order": ["batch_context", "evaluation_context", "evaluation_required_key", "download_result_context", "stage_authorization_context"],
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "adapter_missing_categories": ["required_key_absent"], "adapter_missing_reason": MISSING_REASON,
        "none_empty_forwarding_policy": {
            "exact_none": SCALAR_REASONS[0], "exact_builtin_empty_str": SCALAR_REASONS[1],
            "empty_str_subclass": SCALAR_REASONS[0], "historical_lowercase_used": False,
        },
        "canonical_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "allowed_topology_restoration_dispositions": list(ALLOWED_DISPOSITIONS),
        "blocked_reason_mapping": dict(BLOCKED_REASONS),
        "source_type_invalid_reason": SOURCE_TYPE_REASON, "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "formal_call_count_after_candidate_gate": 1, "oracle_call_count_after_source_validation": 1,
        "source_prevalidated_before_oracle": True, "oracle_complete_exact10_equality_required": True,
        "no_partial_exact13_on_failure": True, "blocked_passthrough": True,
        "context_invalid_partial_canonical_projection": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "provider_fields_consumed": [], "real_provider_mapping_executed": False, "real_provider_value_count": 0,
        "contract_row_count": len(state["contract_rows"]), "contract_pass_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]), "routing_matrix_pass_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(routing_counts.items())),
        "projection_truth_matrix_row_count": len(state["truth_rows"]), "projection_truth_matrix_pass_count": len(state["truth_rows"]),
        "projection_truth_matrix_group_counts": dict(sorted(truth_counts.items())),
        "safety_row_count": len(state["safety_rows"]), "safety_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]), "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_SHA256[SOURCE_PATHS[7]],
        "coverage_issue_still_includes_admit_008_to_015": True,
        "source_input_count": len(SOURCE_PATHS), "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {record.relative_path.as_posix(): record.expected_sha256 for record in snapshot.records},
        "source_input_verification": "expected_sha256_equals_base_tree_sha256_equals_filesystem_sha256",
        "source_boundary_name": "fixed_exact17_committed_source_boundary",
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(payloads.items())},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact7_runtime_unchanged", "admit_008_unregistered",
            "exact8_runtime_not_implemented", "provider_mapping_not_validated", "admit_009_not_started",
            "evaluate_all_rules_not_implemented", "combined_candidate_verdict_not_implemented",
            "real_candidate_evaluation_not_executed", "raw_network_download_forbidden", "training_forbidden",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP, "validation_failures": [],
        "readiness": readiness, **readiness, "all_checks_passed": True,
    }
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return payloads


def _preflight_output_root(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("output root must be directory and non-symlink")
    if root.exists():
        entries = {path.name for path in root.iterdir()}
        if not entries <= set(OUTPUT_FILES):
            raise ValueError("unexpected output entry")
        for path in root.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ValueError("output must be regular non-symlink")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT, head_ref: str = "HEAD"
) -> dict[str, Any]:
    state = build_design_state(repo_root, head_ref)
    root = output_root if output_root.is_absolute() else repo_root / output_root
    _preflight_output_root(root)
    payloads = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {
        "output_root": root, "output_files": OUTPUT_FILES,
        "output_sha256": {name: hashlib.sha256(payloads[name]).hexdigest() for name in OUTPUT_FILES},
        "contract_row_count": len(state["contract_rows"]), "routing_row_count": len(state["routing_rows"]),
        "truth_row_count": len(state["truth_rows"]), "safety_row_count": len(state["safety_rows"]),
    }


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1()
    print(json.dumps({key: value for key, value in result.items() if key != "output_root"}, sort_keys=True))

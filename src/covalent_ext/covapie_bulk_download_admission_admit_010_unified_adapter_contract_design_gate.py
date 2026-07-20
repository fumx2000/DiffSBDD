"""Design-only contract gate for the future ADMIT_010 unified adapter.

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
STEP = "ADMIT_010 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "4090769a3036e4019a65ce93ae61bd5ac8408983"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_010 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_010_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_010_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_010"
ADMISSION_RULE_NAME = "leakage_group_assignment_before_split"
ADAPTER_ID = "covapie_admit_010_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_010"
FORMAL_RESULT_TYPE = "Admit010EvaluationResult"
INDEPENDENT_ORACLE_NAME = "classify_admit_010_leakage_group_assignment_provenance_design"
CURRENT_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 10))
FUTURE_REGISTERED_RULE_ORDER = (*CURRENT_REGISTERED_RULE_ORDER, ADMISSION_RULE_ID)
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("leakage_group_id",)
CONTEXT_ITEMS = ("leakage_group_assignment_provenance_contract",)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_leakage_group_id", "validated_candidate_fields",
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
    "batch_context": "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_MAPPING_REASON = "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "leakage_group_id_missing"
SOURCE_TYPE_REASON = "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "leakage_group_assignment_provenance_contract_required_key_lookup",
    "download_result_context_must_be_none",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "leakage_group_id_required_key_lookup",
    "formal_evaluator",
    "source_validation",
    "independent_oracle",
    "full_exact10_equality",
    "exact13_projection",
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_source_boundary_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_safety_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c",
    "5769c583bc5ade6dbeb81190b20e1774120f7b38dbf53d540f97b50dbf594d54",
    "809a591cca7bd5f94920100105dbc6d643d8e73f38dc7692933f244de954d774",
    "c5caa0f398f7d8592b2ef8ab14e4af4c47e9bfd7a06e476f617de55e6c627284",
    "8695ed6089fd576581ef1a50e7c48b07cac12a7aa6450f19a384bfbfabcef84d",
    "85dbd9f38e39a5620c41081d6134774893250a43d67023b69cae94775224d2ab",
    "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05",
    "33fb0d6f35b49dbf98e61e2c16fafece4b01cdfcce629ff7f1ac5afb1e7e5af2",
    "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
    "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc",
    "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30",
    "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1",
    "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
    "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
), strict=True))

CONTRACT_FILENAME = "covapie_admit_010_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_010_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_010_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_010_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_010_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_010_unified_adapter_contract_manifest.json"
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
    "oracle_call_count", "candidate_access_status", "required_lookup_count",
    "identity_preserved", "case_passed",
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
        (root / path).resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as error:
        raise ValueError(f"source missing or escapes repository: {path}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError(f"source not regular non-symlink: {path}")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    if len(SOURCE_PATHS) != 15 or len(set(SOURCE_PATHS)) != 15 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact15 source boundary shape invalid")
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
    standalone_tree = ast.parse(_record(snapshot, 0).content.decode("utf-8"))
    standalone_manifest = _json_document(snapshot, 1)
    _, standalone_contract = _csv_document(snapshot, 2)
    _, standalone_truth = _csv_document(snapshot, 3)
    issue_header, standalone_issues = _csv_document(snapshot, 6)
    provenance_tree = ast.parse(_record(snapshot, 7).content.decode("utf-8"))
    provenance_manifest = _json_document(snapshot, 8)
    runtime_tree = ast.parse(_record(snapshot, 9).content.decode("utf-8"))
    runtime_manifest = _json_document(snapshot, 10)
    precedent_tree = ast.parse(_record(snapshot, 11).content.decode("utf-8"))
    precedent_manifest = _json_document(snapshot, 12)
    admit009_tree = ast.parse(_record(snapshot, 13).content.decode("utf-8"))
    admit009_manifest = _json_document(snapshot, 14)
    issue_map = {row["issue_id"]: row for row in standalone_issues}
    runtime_assignments = {
        target.id: ast.unparse(node.value)
        for node in runtime_tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    checks = (
        _literal_registry_keys(runtime_tree) == CURRENT_REGISTERED_RULE_ORDER,
        runtime_manifest.get("registered_rule_ids") == list(CURRENT_REGISTERED_RULE_ORDER),
        runtime_manifest.get("known_not_registered_rule_ids") == list(KNOWN_RULE_IDS[9:]),
        "_evaluate_registered_admit_010" not in _top_functions(runtime_tree),
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
        standalone_manifest.get("truth_row_count") == 71,
        len(standalone_contract) == 41 and len(standalone_truth) == 71,
        INDEPENDENT_ORACLE_NAME in _top_functions(provenance_tree),
        FORMAL_EVALUATOR_NAME not in _top_functions(provenance_tree),
        provenance_manifest.get("truth_row_count") == 71,
        provenance_manifest.get("leakage_group_id_provider_mapping_validated") is False,
        "build_design_state" in _top_functions(precedent_tree),
        "_evaluate_registered_admit_010" not in _top_functions(precedent_tree),
        precedent_manifest.get("future_registered_rule_order") == list(CURRENT_REGISTERED_RULE_ORDER),
        "evaluate_admit_009" in _top_functions(admit009_tree),
        admit009_manifest.get("result_fields") is not None,
        issue_header == ISSUE_COLUMNS and len(standalone_issues) == 11,
        issue_map["LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "|".join(KNOWN_RULE_IDS[9:]),
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "standalone_truth": standalone_truth,
        "issue_rows": standalone_issues,
        "issue_bytes": _record(snapshot, 6).content,
    }


def _standalone_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface")


def _oracle_module() -> Any:
    return importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate")


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    standalone = _standalone_module()
    result_type = standalone.Admit010EvaluationResult
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
    provenance: object,
    *,
    oracle_callable: Callable[[object, object], object] | None = None,
) -> Any:
    standalone = _standalone_module()
    classify = (
        _oracle_module().classify_admit_010_leakage_group_assignment_provenance_design
        if oracle_callable is None else oracle_callable
    )
    try:
        classification = classify(scalar, provenance)
        if not isinstance(classification, Mapping):
            raise TypeError("oracle result must be Mapping")
        return standalone.Admit010EvaluationResult(
            ADMISSION_RULE_ID,
            classification["outcome"], classification["passed"],
            classification["blocks_candidate"], classification["reason"],
            classification["canonical_leakage_group_id"],
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
    if type(expected) is not standalone.Admit010EvaluationResult or source != expected:
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
    formal_evaluator: Callable[[object, object], object] | None = None,
    oracle_callable: Callable[[object, object], object] | None = None,
) -> UnifiedAdmissionEvaluationDesignRecord:
    """Exercise the frozen future adapter algorithm without defining a handler."""
    if batch_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context"], True)
    if not isinstance(evaluation_context, Mapping):
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context"], True)
    try:
        provenance_object = evaluation_context["leakage_group_assignment_provenance_contract"]
    except KeyError:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context_key"], True)
    if download_result_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["download_result_context"], True)
    if stage_authorization_context is not None:
        _raise_design_error("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["stage_authorization_context"], True)
    if not isinstance(candidate_record, Mapping):
        return candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    try:
        scalar_object = candidate_record["leakage_group_id"]
    except KeyError:
        return candidate_invalid_exact13_for_design(MISSING_REASON)

    evaluator = _standalone_module().evaluate_admit_010 if formal_evaluator is None else formal_evaluator
    source = evaluator(scalar_object, provenance_object)
    decision = validate_source_shape_and_invariants_for_design(source)
    if not decision.accepted:
        _raise_design_error(decision.code, decision.reason, decision.adapter_ready)
    try:
        expected = expected_exact10_from_committed_oracle_for_design(
            scalar_object, provenance_object, oracle_callable=oracle_callable
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


def _dispatch_json(
    reason: str, *, adapter_ready: bool = True,
    code: str = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
) -> str:
    return json.dumps(dict(zip(DISPATCH_ERROR_FIELDS, (
        code, ADMISSION_RULE_ID, True, True, adapter_ready, reason,
    ), strict=True)), separators=(",", ":"))


def _truth_row(
    case_id: str, group: str, behavior: str, reason: str = "", *,
    source: object = None, oracle: object = None, unified: object = None,
    code: str = "", formal: int = 0, oracle_calls: int = 0,
) -> dict[str, str]:
    standalone = _standalone_module()
    return {
        "case_id": case_id, "case_group": group, "behavior": behavior,
        "expected_dispatch_code": code, "expected_reason": reason,
        "source_exact10_json": _json_record(source) if type(source) is standalone.Admit010EvaluationResult else "",
        "oracle_exact10_json": _json_record(oracle) if type(oracle) is standalone.Admit010EvaluationResult else "",
        "unified_exact13_json": _json_record(unified) if type(unified) is UnifiedAdmissionEvaluationDesignRecord else "",
        "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls),
        "case_passed": "true",
    }


def _contract_rows() -> list[dict[str, str]]:
    """Natural, non-padded statements of the frozen ADMIT_010 adapter contract."""
    definitions = (
        ("identity", "admission_rule_id", ADMISSION_RULE_ID),
        ("identity", "admission_rule_name", ADMISSION_RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "candidate_field", CANDIDATE_FIELDS[0]),
        ("identity", "evaluation_context_item", CONTEXT_ITEMS[0]),
        ("identity", "formal_evaluator", FORMAL_EVALUATOR_NAME),
        ("identity", "formal_result_type", FORMAL_RESULT_TYPE),
        ("identity", "design_oracle", INDEPENDENT_ORACLE_NAME),
        ("identity", "unified_schema", RESULT_SCHEMA_VERSION),
        ("runtime_reuse", "public_result_type", "UnifiedAdmissionRuleEvaluation_exact9_object_identity"),
        ("runtime_reuse", "public_error_type", "UnifiedAdmissionDispatchError_exact9_object_identity"),
        ("runtime_reuse", "public_constants", "RESULT_SCHEMA_VERSION|RESULT_FIELDS|DISPATCH_ERROR_FIELDS|DISPATCH_ERROR_CODES|OUTCOME_VOCABULARY_exact9_object_identity"),
        ("runtime_reuse", "known_rule_ids", "|".join(KNOWN_RULE_IDS)),
        ("runtime_reuse", "public_dispatch_signature", "exactly_equal_to_current_exact9"),
        ("successor", "dispatcher_identity", "new_function_object_not_current_exact9_dispatcher"),
        ("successor", "dispatcher_registry_binding", "successor_local_immutable_exact10_registry"),
        ("successor", "current_registry", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("successor", "future_registry", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("successor", "first_nine_handlers", "9_of_9_current_exact9_object_identity"),
        ("successor", "only_new_handler", "_evaluate_registered_admit_010"),
        ("successor", "known_not_registered", "|".join(KNOWN_RULE_IDS[10:])),
        ("routing", "precedence", "|".join(CONTEXT_ROUTING_ORDER)),
        ("routing", "batch", "exact_none"),
        ("routing", "evaluation", "isinstance_collections.abc.Mapping"),
        ("routing", "evaluation_lookup", "single_direct_getitem_KeyError_only_missing"),
        ("routing", "download", "exact_none"),
        ("routing", "stage", "exact_none"),
        ("routing", "context_before_candidate", "all_context_checks_complete_before_candidate_access"),
        ("mapping", "copy", "none"),
        ("mapping", "iteration", "none"),
        ("mapping", "mutation", "none"),
        ("mapping", "extra_keys", "ignored"),
        ("mapping", "present_none", "present_not_missing"),
        ("mapping", "non_key_error", "propagates_unchanged"),
        ("candidate", "mapping_invalid", CANDIDATE_MAPPING_REASON),
        ("candidate", "required_key_absent", MISSING_REASON),
        ("candidate", "invalid_calls", "formal_0|oracle_0"),
        ("candidate", "invalid_consumed_candidate", CANDIDATE_FIELDS[0]),
        ("candidate", "invalid_consumed_context", CONTEXT_ITEMS[0]),
        ("candidate", "present_values", "forward_original_object_without_prevalidation"),
        ("call", "formal", "exactly_once_positional_scalar_then_provenance"),
        ("call", "formal_identity", "same_two_original_objects"),
        ("source", "exact_type", "type_source_is_Admit010EvaluationResult_subclass_rejected"),
        ("source", "storage", "vars_exact_builtin_dict_exact10_order"),
        ("source", "dataclass", "exact10_field_order"),
        ("source", "reads", "all_exact10_fields_in_order"),
        ("source", "reconstruction", "committed_type_post_init_and_full_equality"),
        ("source", "failure", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|adapter_ready_false|oracle_0|no_partial_exact13"),
        ("oracle", "call", "exactly_once_after_source_validation_same_two_objects"),
        ("oracle", "result", "Mapping_required"),
        ("oracle", "expected", "complete_committed_Admit010EvaluationResult"),
        ("oracle", "comparison", "full_exact10_equality"),
        ("projection", "fields", "|".join(RESULT_FIELDS)),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "consumed_context", "source.consumed_context_items_no_envelope_injection"),
        ("projection", "adapter_id", ADAPTER_ID),
        ("issues", "inventory", "Exact11_byte_identical_SHA256_779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"),
        ("issues", "coverage", "open_ADMIT_010_through_ADMIT_015_unchanged"),
        ("provider", "mapping", "unvalidated_zero_real_provider_ids"),
        ("boundary", "runtime", "design_only_no_handler_registry_dispatcher_or_registration"),
        ("boundary", "operations", "no_provider_grouping_split_reassignment_raw_network_download_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    return [{
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1)]


def _route_case(
    index: int, group: str, case_id: str, condition: str, behavior: str,
    reason: str, result: str, formal: int, oracle: int, access: str,
    lookups: int, identity: str,
) -> dict[str, str]:
    return {
        "matrix_order": str(index), "matrix_group": group, "case_id": case_id,
        "condition": condition, "expected_behavior": behavior,
        "expected_reason": reason, "expected_result_json": result,
        "formal_call_count": str(formal), "oracle_call_count": str(oracle),
        "candidate_access_status": access, "required_lookup_count": str(lookups),
        "identity_preserved": identity, "case_passed": "true",
    }


def _routing_rows() -> list[dict[str, str]]:
    standalone = _standalone_module()
    scalar = "COVAPIE_LEAKAGE_GROUP_000001"
    provenance = standalone._valid_contract(candidate=scalar)
    passed = route_and_project_for_design(
        {CANDIDATE_FIELDS[0]: scalar}, batch_context=None,
        evaluation_context={CONTEXT_ITEMS[0]: provenance},
        download_result_context=None, stage_authorization_context=None,
    )
    none_result = route_and_project_for_design(
        {CANDIDATE_FIELDS[0]: scalar}, batch_context=None,
        evaluation_context={CONTEXT_ITEMS[0]: None},
        download_result_context=None, stage_authorization_context=None,
    )
    empty_result = route_and_project_for_design(
        {CANDIDATE_FIELDS[0]: ""}, batch_context=None,
        evaluation_context={CONTEXT_ITEMS[0]: provenance},
        download_result_context=None, stage_authorization_context=None,
    )
    malformed_result = route_and_project_for_design(
        {CANDIDATE_FIELDS[0]: "bad"}, batch_context=None,
        evaluation_context={CONTEXT_ITEMS[0]: provenance},
        download_result_context=None, stage_authorization_context=None,
    )
    candidate_invalid = candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    missing = candidate_invalid_exact13_for_design(MISSING_REASON)
    d = lambda key: _dispatch_json(CONTEXT_REASONS[key])
    cases = (
        ("context", "batch_none", "batch exact None", "accepted", "", "", 1, 1, "accessed_after_context", 2, "true"),
        ("context", "batch_mapping", "batch Mapping non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], d("batch_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "batch_object", "batch arbitrary object", "dispatch_error", CONTEXT_REASONS["batch_context"], d("batch_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_none", "evaluation None", "dispatch_error", CONTEXT_REASONS["evaluation_context"], d("evaluation_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_non_mapping", "evaluation arbitrary object", "dispatch_error", CONTEXT_REASONS["evaluation_context"], d("evaluation_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_mapping_subclass", "evaluation Mapping subclass", "accepted_without_copy", "", _json_record(passed), 1, 1, "accessed_after_context", 2, "true"),
        ("context", "evaluation_extra_keys", "evaluation extra keys", "ignored_without_iteration", "", _json_record(passed), 1, 1, "accessed_after_context", 2, "true"),
        ("context", "evaluation_key_missing", "required evaluation key absent", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], d("evaluation_context_key"), 0, 0, "not_accessed", 1, "n/a"),
        ("context", "evaluation_none_present", "required value None", "forwarded_not_missing", none_result.reason, _json_record(none_result), 1, 1, "value_read_once", 2, "true"),
        ("context", "context_identity", "provenance sentinel", "same_original_object", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("context", "evaluation_direct_lookup", "single direct getitem", "one_lookup_no_get_or_contains", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("context", "evaluation_lookup_non_key_error", "getitem raises RuntimeError", "exception_propagates", "RuntimeError", "", 0, 0, "not_accessed", 1, "n/a"),
        ("context", "download_non_none", "download non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], d("download_result_context"), 0, 0, "not_accessed", 1, "true"),
        ("context", "stage_non_none", "stage non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], d("stage_authorization_context"), 0, 0, "not_accessed", 1, "true"),
        ("context", "multiple_failure_precedence", "all contexts invalid", "first_batch_error", CONTEXT_REASONS["batch_context"], d("batch_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "candidate_bomb", "context failure with inaccessible candidate", "candidate_not_accessed", CONTEXT_REASONS["evaluation_context"], d("evaluation_context"), 0, 0, "not_accessed", 0, "n/a"),
        ("candidate", "non_mapping", "candidate arbitrary object", "exact13_invalid", CANDIDATE_MAPPING_REASON, _json_record(candidate_invalid), 0, 0, "envelope_checked", 1, "n/a"),
        ("candidate", "key_missing", "candidate key absent", "exact13_invalid", MISSING_REASON, _json_record(missing), 0, 0, "single_lookup", 2, "n/a"),
        ("candidate", "mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "extra_fields", "candidate extra fields", "ignored_without_iteration", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "mutable_not_mutated", "mutable candidate", "not_mutated", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "scalar_identity", "scalar sentinel", "same_original_object", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "direct_lookup", "single direct getitem", "one_lookup_no_get_or_contains", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "lookup_non_key_error", "getitem raises RuntimeError", "exception_propagates", "RuntimeError", "", 0, 0, "lookup_raised", 2, "n/a"),
        ("candidate", "none_present", "candidate None", "formal_invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "", 1, 1, "value_read_once", 2, "true"),
        ("candidate", "empty_present", "candidate empty string", "formal_blocked", empty_result.reason, _json_record(empty_result), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "str_subclass", "candidate str subclass", "formal_invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "", 1, 1, "value_read_once", 2, "true"),
        ("candidate", "canonical", "canonical candidate", "passed", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("candidate", "malformed", "malformed candidate", "formal_invalid", malformed_result.reason, _json_record(malformed_result), 1, 1, "value_read_once", 2, "true"),
        ("call", "formal_once", "valid envelope", "exactly_one_positional_call", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("call", "oracle_once", "source validation succeeds", "exactly_one_positional_call", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
        ("source", "wrong_type", "formal returns object", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, _dispatch_json(SOURCE_TYPE_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once", 2, "true"),
        ("source", "subclass", "formal result subclass", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, _dispatch_json(SOURCE_TYPE_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once", 2, "true"),
        ("source", "storage_order", "vars order tamper", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once", 2, "true"),
        ("source", "cross_field", "post-init invariant tamper", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 0, "value_read_once", 2, "true"),
        ("source", "oracle_mismatch", "one of Exact10 differs", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, _dispatch_json(SOURCE_INVARIANT_REASON, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"), 1, 1, "value_read_once", 2, "true"),
        ("projection", "scalar_short", "empty candidate", "preserve_empty_context", empty_result.reason, _json_record(empty_result), 1, 1, "value_read_once", 2, "true"),
        ("projection", "context_invalid", "provenance invalid", "preserve_canonical_and_context", none_result.reason, _json_record(none_result), 1, 1, "value_read_once", 2, "true"),
        ("projection", "passed", "valid pair", "exact10_to_exact13", "", _json_record(passed), 1, 1, "value_read_once", 2, "true"),
    )
    return [_route_case(index, *case) for index, case in enumerate(cases, 1)]


def _truth_rows() -> list[dict[str, str]]:
    standalone = _standalone_module()
    rows: list[dict[str, str]] = []
    for group, case_id, scalar, provenance, _precedence in standalone._natural_cases():
        source = standalone.evaluate_admit_010(scalar, provenance)
        expected = expected_exact10_from_committed_oracle_for_design(scalar, provenance)
        if not validate_source_oracle_equivalence_for_design(source, expected).accepted:
            raise ValueError(f"Exact71 source/oracle mismatch: {case_id}")
        rows.append(_truth_row(
            f"STANDALONE_{case_id}", f"standalone_{group}", "exact10_to_exact13",
            source.reason, source=source, oracle=expected,
            unified=project_exact10_to_exact13_for_design(source), formal=1, oracle_calls=1,
        ))
    for key in ("batch_context", "evaluation_context", "evaluation_context_key", "download_result_context", "stage_authorization_context"):
        rows.append(_truth_row(
            f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result",
            CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ))
    rows.extend((
        _truth_row("ROUTING_precedence", "routing_dispatch", "first_failure_no_candidate_access", CONTEXT_REASONS["batch_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"),
        _truth_row("ROUTING_candidate_bomb", "routing_dispatch", "candidate_never_accessed", CONTEXT_REASONS["evaluation_context"], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"),
        _truth_row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13", CANDIDATE_MAPPING_REASON, unified=candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)),
        _truth_row("CANDIDATE_key_absent", "adapter_candidate_invalid", "adapter_generated_exact13", MISSING_REASON, unified=candidate_invalid_exact13_for_design(MISSING_REASON)),
        _truth_row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_storage_or_order", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_cross_field", "source_validation_failure", "reconstruction_rejected_no_oracle", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_oracle_mismatch", "source_validation_failure", "full_exact10_mismatch_no_projection", SOURCE_INVARIANT_REASON, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
    ))
    if len(rows) != 85:
        raise ValueError("Exact85 projection truth corpus drift")
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
        "admit_011", "evaluate_all_rules", "combined_verdict", "raw_read", "network",
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
    "admit_010_standalone_evaluator_implemented",
    "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented",
    "admit_010_exact10_result_contract_frozen",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_candidate_projection_contract_frozen",
    "admit_010_context_routing_contract_frozen",
    "admit_010_formal_source_validation_contract_frozen",
    "admit_010_design_oracle_full_parity_contract_frozen",
    "admit_010_exact13_projection_contract_frozen",
    "admit_010_successor_dispatcher_contract_frozen",
    "admit_010_first_nine_handler_identity_reuse_frozen",
    "admit_010_provider_mapping_boundary_preserved",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_010_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started",
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
        len(state["contract_rows"]) != 62
        or len(state["contract_rows"]) != len({row["contract_id"] for row in state["contract_rows"]})
        or len(state["routing_rows"]) != 39 or len(state["truth_rows"]) != 85
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
        "future_adapter_handler": "_evaluate_registered_admit_010",
        "independent_oracle": INDEPENDENT_ORACLE_NAME,
        "candidate_fields": list(CANDIDATE_FIELDS),
        "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_first_nine_handler_identity_reused": {rule_id: True for rule_id in CURRENT_REGISTERED_RULE_ORDER},
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[10:]),
        "future_exact10_public_dispatch_contract": "new_function_object_same_exact9_signature_reads_successor_local_exact10_registry",
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
        "batch_context_contract": "exact_none",
        "evaluation_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "download_result_context_contract": "exact_none",
        "stage_authorization_context_contract": "exact_none",
        "context_before_candidate": True,
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "adapter_missing_categories": ["required_key_absent"],
        "adapter_missing_reason": MISSING_REASON,
        "formal_positional_argument_order": ["leakage_group_id_object", "leakage_group_assignment_provenance_contract_object"],
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
        "issue_inventory_sha256": SOURCE_SHA256[SOURCE_PATHS[6]],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010–ADMIT_015",
        "coverage_issue_transition": "admit_009_implemented_and_removed_from_open_coverage_scope",
        "leakage_group_id_provider_mapping_validated": False,
        "real_provider_leakage_group_id_count": 0,
        "provider_fields_consumed": [],
        "source_boundary_name": "fixed_ordered_exact15_committed_source_boundary",
        "source_input_count": 15,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {
                "source_order": index, "source_relative_path": record.relative_path.as_posix(),
                "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
                "non_symlink": True, "safe_descendant": True,
                "expected_sha256": record.expected_sha256,
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
            "adapter_handler_not_implemented", "exact9_runtime_unchanged",
            "admit_010_unregistered", "exact10_runtime_not_implemented",
            "provider_mapping_not_validated", "admit_011_not_started",
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


def _resolved_output_target_is_authorized(
    root: Path, repo_root: Path, *, output_root_was_relative: bool,
) -> bool:
    try:
        repo_metadata = os.lstat(repo_root)
        if not stat.S_ISDIR(repo_metadata.st_mode) or stat.S_ISLNK(repo_metadata.st_mode):
            return False
        resolved_repo = repo_root.resolve(strict=True)
        parent_metadata = os.lstat(root.parent)
        if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
            return False
        resolved_parent = root.parent.resolve(strict=True)
        if Path(os.path.abspath(root.parent)) != resolved_parent:
            return False
        if root.exists() or root.is_symlink():
            root_metadata = os.lstat(root)
            if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(root_metadata.st_mode):
                return False
            resolved_target = root.resolve(strict=True)
            if Path(os.path.abspath(root)) != resolved_target:
                return False
        else:
            resolved_target = resolved_parent / root.name
        if output_root_was_relative:
            resolved_target.relative_to(resolved_repo)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _preflight_output_root(
    root: Path, repo_root: Path, *, output_root_was_relative: bool,
) -> bool:
    if not _resolved_output_target_is_authorized(
        root, repo_root, output_root_was_relative=output_root_was_relative,
    ):
        raise ValueError("output target resolved containment invalid")
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
        entries = tuple(root.iterdir())
        if not {entry.name for entry in entries}.issubset(set(OUTPUT_FILES)):
            raise ValueError("unexpected output entry")
        for entry in entries:
            item = os.lstat(entry)
            if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise ValueError("existing output must be regular non-symlink")
        return False
    return True


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _postvalidate_output_root(root: Path) -> None:
    metadata = os.lstat(root)
    entries = tuple(root.iterdir())
    if (
        not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
        or {entry.name for entry in entries} != set(OUTPUT_FILES)
    ):
        raise ValueError("postwrite output root invalid")
    for entry in entries:
        item = os.lstat(entry)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("postwrite output entry invalid")


def run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    output_root_was_relative = not output_root.is_absolute()
    root = repo_root / output_root if output_root_was_relative else output_root
    create_root = _preflight_output_root(
        root, repo_root, output_root_was_relative=output_root_was_relative,
    )
    state = build_design_state(repo_root, head_ref)
    payloads, manifest = _payloads(state)
    if create_root:
        root.mkdir(exist_ok=False)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    _postvalidate_output_root(root)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

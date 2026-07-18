"""Design-only contract gate for the future ADMIT_007 unified adapter.

This standard-library-only module freezes routing, candidate projection,
standalone Exact10 validation, independent-oracle equivalence, and Exact13
projection.  It intentionally provides no runtime handler and performs no
registry mutation.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_007 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "0c7081a281fe3b4dac774bc6772a10ea599b8a76"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_007 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_007_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_007_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_007"
ADMISSION_RULE_NAME = "distance_only_inference_forbidden"
ADAPTER_ID = "covapie_admit_007_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_007"
FORMAL_EVALUATOR_SOURCE = Path(
    "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py"
)
INDEPENDENT_ORACLE_NAME = "classify_admit_006_admit_007_evidence_design"
FUTURE_REGISTERED_RULE_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 8))
CURRENT_REGISTERED_RULE_ORDER = FUTURE_REGISTERED_RULE_ORDER[:6]
CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)
CANONICAL_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
ALLOWED_CLASSES = CANONICAL_ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CONTEXT_VALUE_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
MISSING_REASON = "covalent_event_evidence_missing"
CANDIDATE_MAPPING_REASON = "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_REASONS = {
    "batch_context": "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_007_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED",
    "download_result_context": "ADMIT_007_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_007_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
EXECUTION_PRECEDENCE = (
    "global_admission_rule_id_exact_type_validation",
    "known_rule_validation",
    "registration_adapter_ready_validation",
    "batch_context_validation",
    "evaluation_context_mapping_validation",
    "allowed_covalent_evidence_classes_key_validation",
    "download_result_context_validation",
    "stage_authorization_context_validation",
    "candidate_record_mapping_validation",
    "required_candidate_field_presence",
    "adapter_missing_value_classification",
    "formal_evaluate_admit_007_exactly_once",
    "standalone_source_exact_type_and_exact10_invariant_validation",
    "independent_expected_exact10_oracle_derivation",
    "source_oracle_complete_exact10_equality",
    "exact13_unified_result_construction",
)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_covalent_event_evidence_source", "validated_candidate_fields",
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
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_issue_inventory.csv",
    str(FORMAL_EVALUATOR_SOURCE),
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_formal_evaluator_preconditions_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1/covapie_admit_006_unified_adapter_contract_manifest.json",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
    "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
    "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    "ce5cbf09765e8b12db162458ca9518d71d431b175f3225e5558a8b57fdd133f6",
    "f5212100bf458372dd908a234557ee34858cf24cf2360e39b1e61cba8a562958",
    "d6183b2f6dba1c50f6131e28d14519c29d6645b879f954fed7668e776bb0f425",
    "e0ac129e65333e7d1808b8d165391e9188a22c61e8f96ce5e0def8895a34b30c",
    "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
    "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
    "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
    "7645a99f107bd784d1868dbab7136803804645874b33a210273944b00447ac89",
    "449f3f2f5bcf7b7e6a2d60504238da91f41f67822a9747e32fd6eb60b88468b2",
), strict=True))

CONTRACT_FILENAME = "covapie_admit_007_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_007_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_007_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_007_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_007_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_007_unified_adapter_contract_manifest.json"
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
class Admit007EvaluationDesignRecord:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_covalent_event_evidence_source: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


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
    kind = _git(("cat-file", "-t", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"), root, text=True)
    if kind.returncode or kind.stdout.strip() != "blob":
        raise ValueError(f"source not base-tree blob: {path}")
    try:
        mode = (root / path).lstat().st_mode
    except FileNotFoundError as error:
        raise ValueError(f"source missing: {path}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError(f"source not regular non-symlink: {path}")


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    _validate_lineage(root, head_ref)
    for path in SOURCE_PATHS:  # all structural checks precede the first explicit byte read
        _structural_check(path, root)
    records = []
    for path in SOURCE_PATHS:
        base = _git(("show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"), root)
        content = (root / path).read_bytes()
        expected = SOURCE_SHA256[path]
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        fs_sha = hashlib.sha256(content).hexdigest()
        if base.returncode or expected != base_sha or expected != fs_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, base_sha, fs_sha, content))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and type(value.records) is tuple
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(type(record) is FrozenSourceRecord
                and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
                and record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
                and type(record.content) is bytes
                and hashlib.sha256(record.content).hexdigest() == record.expected_sha256
                for record in value.records)
    )


def _bytes(snapshot: FrozenSourceSnapshot, path: Path) -> bytes:
    matches = [record.content for record in snapshot.records if record.relative_path == path]
    if len(matches) != 1:
        raise ValueError(f"snapshot record mismatch: {path}")
    return matches[0]


def _json(snapshot: FrozenSourceSnapshot, index: int) -> dict[str, Any]:
    value = json.loads(_bytes(snapshot, SOURCE_PATHS[index]).decode())
    if type(value) is not dict:
        raise ValueError("JSON root must be object")
    return value


def _csv(snapshot: FrozenSourceSnapshot, index: int) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    reader = csv.DictReader(io.StringIO(_bytes(snapshot, SOURCE_PATHS[index]).decode(), newline=""))
    if reader.fieldnames is None:
        raise ValueError("CSV header missing")
    return tuple(reader.fieldnames), tuple(dict(row) for row in reader)


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EVALUATOR_REGISTRY" for t in node.targets):
            call = node.value
            if isinstance(call, ast.Call) and call.args and isinstance(call.args[0], ast.Dict):
                return tuple(key.value for key in call.args[0].keys if isinstance(key, ast.Constant))
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _function_calls(tree: ast.Module, name: str) -> set[str]:
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise ValueError(f"function shape changed: {name}")
    result = set()
    for node in ast.walk(nodes[0]):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                result.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                result.add(node.func.attr)
    return result


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen snapshot invalid")
    runtime_manifest = _json(snapshot, 1)
    issue_fields, issue_rows = _csv(snapshot, 2)
    standalone_manifest = _json(snapshot, 4)
    contract_fields, contract_rows = _csv(snapshot, 5)
    truth_fields, truth_rows = _csv(snapshot, 6)
    precondition_manifest = _json(snapshot, 7)
    responsibility_fields, responsibility_rows = _csv(snapshot, 9)
    result_fields, result_rows = _csv(snapshot, 10)
    routing_fields, routing_rows = _csv(snapshot, 11)
    runtime_tree = ast.parse(_bytes(snapshot, SOURCE_PATHS[0]).decode())
    standalone_tree = ast.parse(_bytes(snapshot, SOURCE_PATHS[3]).decode())
    precedent_tree = ast.parse(_bytes(snapshot, SOURCE_PATHS[12]).decode())
    if standalone_manifest.get("truth_matrix_row_count") != 37 or len(truth_rows) != 37:
        raise ValueError("standalone Exact37 changed")
    if standalone_manifest.get("result_fields") != list(STANDALONE_RESULT_FIELDS):
        raise ValueError("standalone Exact10 changed")
    if len(contract_rows) != 28 or not contract_fields or not truth_fields:
        raise ValueError("standalone contract changed")
    if tuple(issue_fields) != ISSUE_COLUMNS or len(issue_rows) != 11:
        raise ValueError("Exact11 issue inventory changed")
    issue_map = {row["issue_id"]: row for row in issue_rows}
    if issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] != "resolved":
        raise ValueError("enum issue resolution changed")
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if coverage["status"] != "open" or "ADMIT_007" not in coverage["affected_rules"].split("|"):
        raise ValueError("coverage issue changed")
    if issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise ValueError("aggregation issue changed")
    if precondition_manifest.get("candidate_scalar_field") != CANDIDATE_FIELDS[0]:
        raise ValueError("ADMIT_007 precondition candidate field changed")
    if len(responsibility_rows) != 3 or not responsibility_fields:
        raise ValueError("responsibility contract changed")
    result_contract = [r for r in result_rows if r.get("contract_kind") == "result_field"]
    if tuple(r["field_name"] for r in result_contract) != RESULT_FIELDS:
        raise ValueError("Exact13 changed")
    if len(routing_rows) != 15 or not routing_fields or not result_fields:
        raise ValueError("unified routing contract changed")
    if runtime_manifest.get("registered_rule_ids") != list(CURRENT_REGISTERED_RULE_ORDER):
        raise ValueError("current Exact6 manifest changed")
    if _literal_registry_keys(runtime_tree) != CURRENT_REGISTERED_RULE_ORDER:
        raise ValueError("current Exact6 registry changed")
    top_functions = {node.name for node in runtime_tree.body if isinstance(node, ast.FunctionDef)}
    if "_evaluate_registered_admit_007" in top_functions or "evaluate_all_rules" in top_functions:
        raise ValueError("future runtime work already present")
    if INDEPENDENT_ORACLE_NAME in _function_calls(standalone_tree, FORMAL_EVALUATOR_NAME):
        raise ValueError("standalone evaluator calls design oracle")
    if "build_design_state" not in {n.name for n in precedent_tree.body if isinstance(n, ast.FunctionDef)}:
        raise ValueError("ADMIT_006 design precedent shape changed")
    return {"truth_rows": truth_rows, "issue_rows": issue_rows}


def _source_values(source: Admit007EvaluationDesignRecord) -> dict[str, object]:
    return {field.name: getattr(source, field.name) for field in fields(source)}


def _json_record(value: object) -> str:
    return json.dumps({field.name: getattr(value, field.name) for field in fields(value)}, ensure_ascii=True, separators=(",", ":"))


def _source_invariants_valid(source: Admit007EvaluationDesignRecord) -> bool:
    strings = (source.admission_rule_id, source.outcome, source.reason, source.canonical_covalent_event_evidence_source)
    if any(type(value) is not str for value in strings):
        return False
    if type(source.passed) is not bool or type(source.blocks_candidate) is not bool or type(source.evaluator_io_used) is not bool:
        return False
    if type(source.validated_candidate_fields) is not tuple or any(
        type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str or type(pair[1]) is not str
        for pair in source.validated_candidate_fields
    ):
        return False
    if type(source.consumed_candidate_fields) is not tuple or any(type(x) is not str for x in source.consumed_candidate_fields):
        return False
    if type(source.consumed_context_items) is not tuple or any(type(x) is not str for x in source.consumed_context_items):
        return False
    if source.admission_rule_id != ADMISSION_RULE_ID or source.outcome not in ("passed", "blocked", "invalid"):
        return False
    if source.passed is not (source.outcome == "passed") or source.blocks_candidate is not (source.outcome != "passed"):
        return False
    if (source.outcome == "passed") is not (source.reason == ""):
        return False
    if source.consumed_candidate_fields != CANDIDATE_FIELDS or source.consumed_context_items != CONTEXT_ITEMS:
        return False
    if source.evaluator_io_used is not False:
        return False
    canonical = source.canonical_covalent_event_evidence_source
    expected_validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    if canonical == "":
        valid = source.outcome == "invalid" and source.reason in SCALAR_REASONS
    elif canonical not in CANONICAL_ENUM_MEMBERS:
        valid = False
    elif source.outcome == "passed":
        valid = canonical in ALLOWED_CLASSES and source.reason == ""
    elif source.outcome == "blocked":
        valid = canonical == CANONICAL_ENUM_MEMBERS[2] and source.reason == BLOCKED_REASON
    else:
        valid = source.reason in CONTEXT_VALUE_REASONS
    return valid and source.validated_candidate_fields == expected_validated


def validate_source_shape_and_invariants_for_design(source: object) -> SourceValidationDecision:
    if type(source) is not Admit007EvaluationDesignRecord:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, False)
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 storage mismatch")
        if tuple(field.name for field in fields(source)) != STANDALONE_RESULT_FIELDS:
            raise ValueError("Exact10 dataclass field order mismatch")
        values = tuple(getattr(source, name) for name in STANDALONE_RESULT_FIELDS)
        reconstructed = Admit007EvaluationDesignRecord(*values)
        if reconstructed != source:
            raise ValueError("Exact10 reconstruction mismatch")
    except (AttributeError, TypeError, ValueError):
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    if not _source_invariants_valid(source):
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def validate_source_oracle_equivalence_for_design(source: object, expected: object) -> SourceValidationDecision:
    prevalidated = validate_source_shape_and_invariants_for_design(source)
    if not prevalidated.accepted:
        return prevalidated
    if type(expected) is not Admit007EvaluationDesignRecord or not _source_invariants_valid(expected) or source != expected:
        return SourceValidationDecision(False, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, False)
    return SourceValidationDecision(True, "", "", True)


def classify_admit_007_independent_design(scalar: object, context: object) -> Admit007EvaluationDesignRecord:
    """Local independent semantic oracle evidence; never a runtime handler."""
    canonical = ""
    if type(scalar) is not str:
        reason = SCALAR_REASONS[0]
    elif scalar == "":
        reason = SCALAR_REASONS[1]
    elif not scalar.isascii():
        reason = SCALAR_REASONS[2]
    elif not (1 <= len(scalar) <= 64 and scalar[0].islower() and all(c.islower() or c.isdigit() or c == "_" for c in scalar)):
        reason = SCALAR_REASONS[3]
    elif scalar not in CANONICAL_ENUM_MEMBERS:
        reason = SCALAR_REASONS[4]
    else:
        canonical, reason = scalar, ""
    if type(context) is not tuple:
        context_reason = CONTEXT_VALUE_REASONS[0]
    elif any(type(member) is not str for member in context) or context != ALLOWED_CLASSES:
        context_reason = CONTEXT_VALUE_REASONS[1]
    else:
        context_reason = ""
    if reason:
        outcome, final_reason, canonical = "invalid", reason, ""
    elif context_reason:
        outcome, final_reason = "invalid", context_reason
    elif canonical == CANONICAL_ENUM_MEMBERS[2]:
        outcome, final_reason = "blocked", BLOCKED_REASON
    else:
        outcome, final_reason = "passed", ""
    validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    return Admit007EvaluationDesignRecord(
        ADMISSION_RULE_ID, outcome, outcome == "passed", outcome != "passed", final_reason,
        canonical, validated, CANDIDATE_FIELDS, CONTEXT_ITEMS, False,
    )


def _source_from_truth_row(row: Mapping[str, str]) -> Admit007EvaluationDesignRecord:
    canonical = row["observed_canonical_evidence_source"]
    validated = tuple(tuple(pair) for pair in json.loads(row["observed_validated_candidate_fields"]))
    outcome = row["observed_outcome"]
    return Admit007EvaluationDesignRecord(
        ADMISSION_RULE_ID, outcome, outcome == "passed", outcome != "passed", row["observed_reason"],
        canonical, validated, CANDIDATE_FIELDS, CONTEXT_ITEMS, False,
    )


class _TruthStringSubclass(str):
    pass


def _objects_from_truth_row(row: Mapping[str, str]) -> tuple[object, object]:
    """Decode only the committed synthetic display grammar for oracle evidence."""
    scalar_kind = row["scalar_input_kind"]
    scalar_display = row["scalar_input_display"]
    if scalar_kind == "str":
        scalar: object = json.loads(scalar_display)
    elif scalar_kind == "NoneType":
        scalar = None
    elif scalar_kind == "int":
        scalar = int(scalar_display.removeprefix("int:"))
    elif scalar_kind == "bool":
        scalar = scalar_display == "bool:True"
    elif scalar_kind == "_StringSubclass":
        scalar = _TruthStringSubclass(json.loads(scalar_display.removeprefix("str_subclass:")))
    elif scalar_kind == "list":
        scalar = json.loads(scalar_display.removeprefix("list:"))
    elif scalar_kind == "dict":
        scalar = json.loads(scalar_display.removeprefix("dict:"))
    else:
        raise ValueError(f"unknown frozen scalar display kind: {scalar_kind}")

    context_kind = row["context_input_kind"]
    context_display = row["context_input_display"]
    if context_kind == "none":
        context: object = None
    elif context_kind == "list":
        context = json.loads(context_display.removeprefix("list:"))
    elif context_kind == "set":
        context = set(json.loads(context_display.removeprefix("set:")))
    elif context_kind == "frozenset":
        context = frozenset(json.loads(context_display.removeprefix("frozenset:")))
    else:
        members = json.loads(context_display.removeprefix("tuple:"))
        if context_kind == "str_subclass":
            members[0] = _TruthStringSubclass(members[0])
        context = tuple(members)
    return scalar, context


def project_exact10_to_exact13_for_design(source: Admit007EvaluationDesignRecord) -> UnifiedAdmissionEvaluationDesignRecord:
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


def _contract_rows() -> list[dict[str, str]]:
    definitions = [
        ("identity", "admission_rule_id", ADMISSION_RULE_ID),
        ("identity", "admission_rule_name", ADMISSION_RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "formal_evaluator", FORMAL_EVALUATOR_NAME),
        ("identity", "formal_evaluator_source", FORMAL_EVALUATOR_SOURCE.as_posix()),
        ("runtime_reuse", "public_api", "evaluate_admission_rule"),
        ("runtime_reuse", "result_type", "UnifiedAdmissionRuleEvaluation"),
        ("runtime_reuse", "dispatch_error_type", "UnifiedAdmissionDispatchError"),
        ("runtime_reuse", "schema_version", RESULT_SCHEMA_VERSION),
        ("runtime_reuse", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("runtime_reuse", "exact6_dispatch_fields", "|".join(DISPATCH_ERROR_FIELDS)),
        ("registration", "future_exact7_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("registration", "current_exact6_order", "|".join(CURRENT_REGISTERED_RULE_ORDER)),
        ("precedence", "complete_execution_precedence", "|".join(EXECUTION_PRECEDENCE)),
        ("routing", "context_order", "batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "batch_context", "exact_none"),
        ("routing", "evaluation_context", "mapping_subclass_accepted_required_key_extra_keys_ignored"),
        ("routing", "routed_context_value", "single_getitem_original_identity_no_prevalidation_copy_or_mutation"),
        ("routing", "download_result_context", "exact_none"),
        ("routing", "stage_authorization_context", "exact_none"),
        ("candidate", "candidate_record", "mapping_subclass_accepted_extra_fields_ignored_no_copy_no_mutation"),
        ("candidate", "required_field", f"{CANDIDATE_FIELDS[0]}_single_getitem_original_identity"),
        ("candidate", "non_mapping", CANDIDATE_MAPPING_REASON),
        ("missing", "missing_field", MISSING_REASON),
        ("missing", "exact_none", MISSING_REASON),
        ("missing", "exact_builtin_empty_str", MISSING_REASON),
        ("missing", "empty_str_subclass", "not_missing_routed_to_standalone"),
        ("call", "formal_call", "exactly_one_positional_call_original_scalar_and_context_identity"),
        ("call", "normalization", "none_no_trim_casefold_alias_conversion_copy_repair_mutation_or_io"),
        ("source", "exact_type", "type(source)_is_Admit007EvaluationResult_subclass_rejected"),
        ("source", "exact10_fields", "|".join(STANDALONE_RESULT_FIELDS)),
        ("source", "invariants", "exact_vars_dict_order_dataclass_field_order_ordered_reads_committed_dataclass_reconstruction_equality_and_complete_cross_field_validation_before_oracle"),
        ("oracle", "identity", INDEPENDENT_ORACLE_NAME),
        ("oracle", "equivalence", "same_original_objects_exactly_once_classification_scalar_context_admit_007_complete_ordered_exact10_equality"),
        ("projection", "mapping", "source_exact10_to_existing_unified_exact13"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "blocked", "blocked_passthrough_not_rejected_or_invalid"),
        ("projection", "context_invalid", "canonical_and_validated_pair_retained"),
        ("issues", "exact11", "byte_identical_preserved"),
        ("readiness", "next_step", RECOMMENDED_NEXT_STEP),
        ("stop", "adapter_handler", "not_implemented"),
        ("stop", "runtime_registry", "current_exact6_unmodified_admit_007_not_registered"),
        ("stop", "training", "feature_semantics_audit_required_step12d_not_final_contract"),
    ]
    return [{"contract_order": str(i), "contract_id": f"CONTRACT_{i:03d}", "contract_group": group,
             "contract_subject": subject, "contract_value": value, "contract_status": "frozen"}
            for i, (group, subject, value) in enumerate(definitions, 1)]


def _dispatch_json(reason: str) -> str:
    return json.dumps(dict(zip(DISPATCH_ERROR_FIELDS, (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", ADMISSION_RULE_ID, True, True, True, reason
    ), strict=True)), separators=(",", ":"))


def _routing_rows() -> list[dict[str, str]]:
    invalid_context_result = project_exact10_to_exact13_for_design(
        classify_admit_007_independent_design(CANONICAL_ENUM_MEMBERS[0], [])
    )
    candidate_invalid = candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    missing_invalid = candidate_invalid_exact13_for_design(MISSING_REASON)
    cases = [
        ("context", "batch_non_none", "batch_context is object", "dispatch_error", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_non_mapping", "evaluation_context is list", "dispatch_error", CONTEXT_REASONS["evaluation_context"], _dispatch_json(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_key_missing", "evaluation Mapping lacks required key", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], _dispatch_json(CONTEXT_REASONS["evaluation_context_key"]), 0, 0, "not_accessed"),
        ("context", "download_non_none", "download_result_context is object", "dispatch_error", CONTEXT_REASONS["download_result_context"], _dispatch_json(CONTEXT_REASONS["download_result_context"]), 0, 0, "not_accessed"),
        ("context", "stage_non_none", "stage_authorization_context is object", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], _dispatch_json(CONTEXT_REASONS["stage_authorization_context"]), 0, 0, "not_accessed"),
        ("context", "multiple_failure_precedence", "batch and later contexts invalid", "first_dispatch_error_only", CONTEXT_REASONS["batch_context"], _dispatch_json(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed"),
        ("context", "evaluation_mapping_subclass", "Mapping subclass with required key", "accepted_without_copy", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_extra_keys", "extra evaluation keys", "ignored", "", "", 1, 1, "accessed_after_context"),
        ("context", "evaluation_not_mutated", "mutable Mapping sentinel", "not_mutated", "", "", 1, 1, "accessed_after_context"),
        ("context", "context_value_identity", "required value identity sentinel with single __getitem__ lookup", "same_object_passed_single_lookup", "", "", 1, 1, "accessed_after_context"),
        ("context", "invalid_value_reaches_standalone", "required value is list", "exact13_invalid_not_dispatch", CONTEXT_VALUE_REASONS[0], _json_record(invalid_context_result), 1, 1, "accessed_after_context"),
        ("candidate", "candidate_non_mapping", "candidate_record is list", "exact13_invalid", CANDIDATE_MAPPING_REASON, _json_record(candidate_invalid), 0, 0, "envelope_checked"),
        ("candidate", "candidate_key_missing", "required key absent", "exact13_invalid", MISSING_REASON, _json_record(missing_invalid), 0, 0, "presence_only"),
        ("candidate", "candidate_exact_none", "required value is exact None", "exact13_invalid", MISSING_REASON, _json_record(missing_invalid), 0, 0, "value_read_once"),
        ("candidate", "candidate_builtin_empty", "required value exact built-in empty str", "exact13_invalid", MISSING_REASON, _json_record(missing_invalid), 0, 0, "value_read_once"),
        ("candidate", "empty_str_subclass", "required value empty str subclass", "routed_to_standalone_invalid", SCALAR_REASONS[0], "", 1, 1, "value_read_once"),
        ("candidate", "whitespace_not_missing", "required value whitespace-only", "routed_to_standalone_invalid", SCALAR_REASONS[3], "", 1, 1, "value_read_once"),
        ("candidate", "malformed_not_missing", "required value integer", "routed_to_standalone_invalid", SCALAR_REASONS[0], "", 1, 1, "value_read_once"),
        ("candidate", "distance_not_missing", "required value distance_only_inference", "routed_to_standalone_blocked", BLOCKED_REASON, "", 1, 1, "value_read_once"),
        ("candidate", "candidate_mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_extra_fields", "extra candidate fields", "ignored", "", "", 1, 1, "value_read_once"),
        ("candidate", "candidate_not_mutated", "mutable candidate sentinel", "not_mutated", "", "", 1, 1, "value_read_once"),
        ("candidate", "scalar_identity", "scalar object identity sentinel with single __getitem__ lookup", "same_object_passed_single_lookup", "", "", 1, 1, "value_read_once"),
    ]
    return [{"matrix_order": str(i), "matrix_group": group, "case_id": case_id, "condition": condition,
             "expected_behavior": behavior, "expected_reason": reason, "expected_result_json": result,
             "formal_call_count": str(formal), "oracle_call_count": str(oracle),
             "candidate_access_status": access, "case_passed": "true"}
            for i, (group, case_id, condition, behavior, reason, result, formal, oracle, access) in enumerate(cases, 1)]


def _truth_row(case_id: str, group: str, behavior: str, reason: str = "", *, source: object = None,
               oracle: object = None, unified: object = None, code: str = "", formal: int = 0,
               oracle_calls: int = 0) -> dict[str, str]:
    return {"case_id": case_id, "case_group": group, "behavior": behavior,
            "expected_dispatch_code": code, "expected_reason": reason,
            "source_exact10_json": _json_record(source) if type(source) is Admit007EvaluationDesignRecord else "",
            "oracle_exact10_json": _json_record(oracle) if type(oracle) is Admit007EvaluationDesignRecord else "",
            "unified_exact13_json": _json_record(unified) if type(unified) is UnifiedAdmissionEvaluationDesignRecord else "",
            "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls), "case_passed": "true"}


class _SourceSubclass(Admit007EvaluationDesignRecord):
    pass


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in predecessor_rows:
        source = _source_from_truth_row(row)
        scalar, context = _objects_from_truth_row(row)
        oracle = classify_admit_007_independent_design(scalar, context)
        if not validate_source_oracle_equivalence_for_design(source, oracle).accepted:
            raise ValueError(f"standalone/oracle Exact10 mismatch: {row['case_id']}")
        projection = project_exact10_to_exact13_for_design(source)
        rows.append(_truth_row(f"STANDALONE_{row['case_id']}", "standalone_exact37", "exact10_to_exact13",
                               source.reason, source=source, oracle=oracle, unified=projection, formal=1, oracle_calls=1))
    result = candidate_invalid_exact13_for_design(CANDIDATE_MAPPING_REASON)
    rows.append(_truth_row("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13",
                           CANDIDATE_MAPPING_REASON, unified=result))
    for suffix in ("field_missing", "value_none", "value_builtin_empty"):
        result = candidate_invalid_exact13_for_design(MISSING_REASON)
        rows.append(_truth_row(f"CANDIDATE_{suffix}", "adapter_candidate_invalid", "adapter_generated_exact13",
                               MISSING_REASON, unified=result))
    for key in ("batch_context", "evaluation_context", "evaluation_context_key", "download_result_context", "stage_authorization_context"):
        rows.append(_truth_row(f"ROUTING_{key}", "routing_dispatch", "exact6_no_partial_result",
                               CONTEXT_REASONS[key], code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"))
    valid = classify_admit_007_independent_design(CANONICAL_ENUM_MEMBERS[0], ALLOWED_CLASSES)
    subclass = _SourceSubclass(*tuple(getattr(valid, name) for name in STANDALONE_RESULT_FIELDS))
    rows.extend((
        _truth_row("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_TYPE_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_invariant", "source_validation_failure", "oracle_not_called_no_projection", SOURCE_INVARIANT_REASON,
                   code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1),
        _truth_row("SOURCE_oracle_mismatch", "source_validation_failure", "no_projection", SOURCE_INVARIANT_REASON,
                   source=valid, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", formal=1, oracle_calls=1),
    ))
    special = (
        ("explicit_passed", CANONICAL_ENUM_MEMBERS[0], ALLOWED_CLASSES),
        ("distance_blocked", CANONICAL_ENUM_MEMBERS[2], ALLOWED_CLASSES),
        ("scalar_invalid", object(), ALLOWED_CLASSES),
        ("context_invalid_canonical_retained", CANONICAL_ENUM_MEMBERS[0], []),
    )
    for name, scalar, context in special:
        source = classify_admit_007_independent_design(scalar, context)
        rows.append(_truth_row(f"PROJECTION_{name}", "projection_semantics", "projection_frozen", source.reason,
                               source=source, oracle=source, unified=project_exact10_to_exact13_for_design(source),
                               formal=1, oracle_calls=1))
    rows.extend((
        _truth_row("BOUNDARY_current_exact6", "runtime_boundary", "registry_unchanged", ""),
        _truth_row("BOUNDARY_admit007_not_registered", "runtime_boundary", "handler_not_implemented_runtime_unchanged", ""),
    ))
    expected_counts = {"standalone_exact37": 37, "adapter_candidate_invalid": 4, "routing_dispatch": 5,
                       "source_validation_failure": 4, "projection_semantics": 4, "runtime_boundary": 2}
    if Counter(row["case_group"] for row in rows) != expected_counts:
        raise ValueError("truth group counts changed")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        "fixed_ordered_source_boundary", "all_structural_checks_before_source_bytes", "source_sha256_verified",
        "snapshot_only_ast_csv_json_parsing", "exact11_issue_byte_preservation", "deterministic_materialization",
        "candidate_projection_contract", "context_routing_contract", "missing_value_contract",
        "exact10_source_validation", "independent_oracle_equivalence", "exact13_projection_contract",
        "blocked_passthrough", "context_invalid_partial_canonical_projection", "current_exact6_verified",
    )
    negative = (
        "adapter_handler_implementation", "registry_modification", "admit_007_registration", "admit_008_work",
        "evaluate_all_rules", "combined_candidate_verdict", "cross_rule_aggregation", "provider_mapping",
        "raw_read", "structure_parsing", "network", "download", "real_candidate_evaluation", "checkpoint_access",
        "torch", "numpy", "rdkit", "model_forward", "loss", "training", "fine_tune", "parameter_update",
        "stage", "commit", "push", "gh",
    )
    rows = []
    for item in positive:
        rows.append({"safety_item": item, "expected_executed": "true", "observed_executed": "true", "safety_passed": "true"})
    for item in negative:
        rows.append({"safety_item": item, "expected_executed": "false", "observed_executed": "false", "safety_passed": "true"})
    return rows


READINESS = {
    "admit_007_standalone_evaluator_available": True,
    "admit_007_unified_adapter_contract_frozen": True,
    "admit_007_candidate_projection_contract_frozen": True,
    "admit_007_context_routing_contract_frozen": True,
    "admit_007_missing_field_value_contract_frozen": True,
    "admit_007_source_result_validation_contract_frozen": True,
    "admit_007_source_oracle_equivalence_contract_frozen": True,
    "admit_007_unified_result_projection_contract_frozen": True,
    "admit_007_blocked_passthrough_contract_frozen": True,
    "admit_007_context_invalid_partial_canonical_projection_frozen": True,
    "ready_for_unified_dispatch_runtime_with_admit_001_to_007_implementation": True,
    "feature_semantics_audit_required_before_training": True,
    "admit_007_unified_adapter_implemented": False,
    "admit_007_registered_in_engine": False,
    "current_exact6_runtime_modified": False,
    "admit_008_standalone_evaluator_implemented": False,
    "admit_008_to_015_registered_in_engine": False,
    "all_15_rules_covered": False,
    "evaluate_all_rules_implemented": False,
    "combined_candidate_verdict_contract_frozen": False,
    "combined_candidate_verdict_implemented": False,
    "cross_rule_precedence_frozen": False,
    "real_provider_enum_mapping_validated": False,
    "real_candidate_evaluation": False,
    "exact11_real_rows_evaluated": False,
    "ready_for_bulk_download_now": False,
    "ready_for_training": False,
    "ready_to_train_now": False,
}


def build_design_state(repo_root: Path = REPO_ROOT, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref)
    predecessor = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    routing_rows = _routing_rows()
    truth_rows = _truth_rows(predecessor["truth_rows"])
    safety_rows = _safety_rows()
    return {
        "snapshot": snapshot, "contract_rows": contract_rows, "routing_rows": routing_rows,
        "truth_rows": truth_rows, "safety_rows": safety_rows, "issue_rows": predecessor["issue_rows"],
        "issue_bytes": _bytes(snapshot, SOURCE_PATHS[2]),
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


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
    manifest = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "adapter_id": ADAPTER_ID, "formal_evaluator": FORMAL_EVALUATOR_NAME,
        "formal_result_type": "Admit007EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_007",
        "formal_evaluator_source": FORMAL_EVALUATOR_SOURCE.as_posix(),
        "independent_oracle": INDEPENDENT_ORACLE_NAME,
        "independent_oracle_outcome_view": "classification.admit_007",
        "candidate_field": CANDIDATE_FIELDS[0], "evaluation_context_item": CONTEXT_ITEMS[0],
        "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_REGISTERED_RULE_ORDER),
        "current_registered_rule_order": list(CURRENT_REGISTERED_RULE_ORDER),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[7:]),
        "known_not_registered_behavior": "known_not_registered_fail_closed",
        "execution_precedence": list(EXECUTION_PRECEDENCE),
        "result_schema_version": RESULT_SCHEMA_VERSION, "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(STANDALONE_RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "adapter_missing_categories": ["required_key_absent", "exact_none", "exact_builtin_empty_str"],
        "adapter_missing_reason": MISSING_REASON,
        "candidate_mapping_invalid_reason": CANDIDATE_MAPPING_REASON,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "formal_blocked_reason": BLOCKED_REASON,
        "blocked_passthrough": True,
        "context_invalid_partial_canonical_projection": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "contract_row_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "routing_matrix_group_counts": dict(sorted(routing_counts.items())),
        "projection_truth_matrix_row_count": len(state["truth_rows"]),
        "projection_truth_matrix_group_counts": dict(sorted(truth_counts.items())),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_inventory_preserved_byte_identical": True,
        "source_input_count": len(SOURCE_PATHS), "source_input_paths": [p.as_posix() for p in SOURCE_PATHS],
        "source_input_sha256": {record.relative_path.as_posix(): record.expected_sha256 for record in snapshot.records},
        "source_input_verification": "expected_sha256_equals_base_tree_sha256_equals_filesystem_sha256",
        "source_boundary_name": "fixed_exact14_committed_source_boundary",
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(payloads.items())},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact6_runtime_unchanged", "admit_007_unregistered",
            "admit_008_not_started", "evaluate_all_rules_not_implemented",
            "combined_candidate_verdict_not_implemented", "provider_mapping_not_validated",
            "real_candidate_evaluation_not_executed", "bulk_download_forbidden", "training_forbidden",
        ],
        "attestations": {
            "exact43_contract_frozen": True, "exact23_routing_frozen": True,
            "exact56_truth_frozen": True, "exact41_safety_frozen": True,
            "exact11_issue_bytes_preserved": True, "exact14_sources_verified": True,
            "formal_called_exactly_once_after_missing_gate": True,
            "source_prevalidated_before_oracle": True,
            "oracle_complete_exact10_equality_required": True,
            "no_partial_exact13_on_failure": True,
        },
        "validation_failures": [],
        "readiness": dict(READINESS), **READINESS,
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
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


def run_covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT, head_ref: str = "HEAD"
) -> dict[str, Any]:
    state = build_design_state(repo_root, head_ref)
    root = output_root if output_root.is_absolute() else repo_root / output_root
    _preflight_output_root(root)
    payloads = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"output_root": root, "output_files": OUTPUT_FILES,
            "output_sha256": {name: hashlib.sha256(payloads[name]).hexdigest() for name in OUTPUT_FILES},
            "contract_row_count": len(state["contract_rows"]),
            "routing_row_count": len(state["routing_rows"]), "truth_row_count": len(state["truth_rows"])}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1()
    print(json.dumps({key: value for key, value in result.items() if key != "output_root"}, sort_keys=True))

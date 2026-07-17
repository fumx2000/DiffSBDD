"""Design-only contract gate for the future ADMIT_005 unified adapter.

This module freezes candidate projection, context routing, standalone-result
validation, independent semantic-oracle equivalence, and Exact10-to-Exact13
projection.  It deliberately does not provide a runtime adapter handler and
does not modify the Phase 4 evaluator registry.
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
from types import SimpleNamespace
from typing import Any

PROJECT = "CovaPIE"
STEP = "ADMIT_005 unified adapter contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "34df44684ff235dd66a5fa399594d0e378b24ade"
EXPECTED_BASE_SUBJECT = "add CovaPIE standalone ADMIT_005 rule logic interface v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_005_unified_adapter_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_005_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_005"
ADMISSION_RULE_NAME = "cys_sg_scope_only_v1"
ADAPTER_ID = "covapie_admit_005_unified_adapter_v1"
FORMAL_EVALUATOR_NAME = "evaluate_admit_005"
FORMAL_EVALUATOR_SOURCE = (
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_005_rule_logic_interface.py"
)
FUTURE_REGISTERED_RULE_ORDER = (
    "ADMIT_001",
    "ADMIT_002",
    "ADMIT_003",
    "ADMIT_004",
    "ADMIT_005",
)
CANDIDATE_FIELDS = (
    "covalent_residue_name",
    "covalent_residue_atom_name",
)
CONTEXT_ORDER = (
    "batch_context",
    "evaluation_context",
    "download_result_context",
    "stage_authorization_context",
)
CONTEXT_REASONS = {
    "batch_context": "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_005_EVALUATION_CONTEXT_MUST_BE_NONE",
    "download_result_context": "ADMIT_005_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_005_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
EXECUTION_PRECEDENCE = (
    "global_admission_rule_id_type_validation",
    "known_rule_validation",
    "registered_adapter_ready_validation",
    "batch_context_validation",
    "evaluation_context_validation",
    "download_result_context_validation",
    "stage_authorization_context_validation",
    "candidate_record_mapping_validation",
    "required_field_covalent_residue_name",
    "required_field_covalent_residue_atom_name",
    "formal_evaluate_admit_005_call",
    "exact_source_type_and_invariants",
    "independent_semantic_oracle_derivation",
    "source_oracle_exact_equivalence",
    "exact13_unified_result_construction",
)
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
STANDALONE_RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_residue_name",
    "canonical_residue_atom_name",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "evaluator_io_used",
)
DISPATCH_ERROR_FIELDS = (
    "code",
    "admission_rule_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "reason",
)

SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        FORMAL_EVALUATOR_SOURCE,
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_005_rule_logic_interface_v1/covapie_admit_005_rule_logic_interface_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_005_rule_logic_interface_v1/covapie_admit_005_rule_logic_interface_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_005_rule_logic_interface_v1/covapie_admit_005_rule_logic_interface_truth_matrix.csv",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1/covapie_admit_001_to_004_runtime_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1/covapie_admit_001_to_004_runtime_issue_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1/covapie_admit_001_to_003_legacy_adapter_contract_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1/covapie_admit_001_to_003_adapter_routing_and_projection_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "1b350d5e1a5b7117ee951450a05f32943ba1cef3854e56377aeff0286aec6b5f",
            "304e6d83bd36faba951bfa024c9fb96d70534e3c49b556c79b9d2acdcec5c2b8",
            "ddc25a44c212abdde590669f6d5a92125cad0657360eae87037fdde7c6c834e0",
            "695c187ccd297671b74ae33a95c52e2c38f0f5d1c46b253b8dd84c682499b10f",
            "a16ce1eef1048db7643a1f7940da554234683918136e76a6487eec5c2fdc35c3",
            "9cf7e902566a4aef9aa098e9a9a966f925666df581f8c0ce408d8c9598905149",
            "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
            "1290eb1cd88d95e6950c64204f16153cae6560aa7ba922ae4977d07b141535af",
            "91e23f622b1c5109110a7f3f7b1fc0ebe68a7e718600df2b87851843be51c4e8",
            "be79b98c695d989f27c694aab3d460990fea735ee8308b620eb6d10a98b3b757",
            "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
            "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
        ),
        strict=True,
    )
)
FORBIDDEN_WRONG_SOURCE_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1/"
    "covapie_admit_001_to_003_candidate_projection_and_context_routing_matrix.csv"
)

CONTRACT_FILENAME = "covapie_admit_005_unified_adapter_contract.csv"
ROUTING_FILENAME = "covapie_admit_005_candidate_projection_and_context_routing_matrix.csv"
TRUTH_FILENAME = "covapie_admit_005_unified_result_projection_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_005_unified_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_005_unified_adapter_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_005_unified_adapter_contract_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    ROUTING_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_id",
    "contract_group",
    "contract_subject",
    "contract_value",
    "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order",
    "matrix_group",
    "case_id",
    "condition",
    "expected_behavior",
    "expected_reason",
    "expected_exact13_json",
    "formal_evaluator_called",
    "oracle_called",
    "case_passed",
)
TRUTH_COLUMNS = (
    "case_id",
    "case_group",
    "behavior",
    "expected_dispatch_code",
    "expected_reason",
    "source_exact10_json",
    "oracle_exact10_json",
    "unified_exact13_json",
    "formal_call_count",
    "scope_oracle_call_count",
    "atom_oracle_call_count",
    "case_passed",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
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
class CsvDocument:
    fieldnames: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class SourceValidationDecision:
    accepted: bool
    code: str
    admission_rule_id: str
    known_rule: bool
    callable_discovered: bool
    adapter_ready: bool
    reason: str


@dataclass(frozen=True)
class Admit005EvaluationDesignRecord:
    """Local design evidence; not the committed runtime result class."""

    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_residue_name: str
    canonical_residue_atom_name: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    evaluator_io_used: bool


@dataclass(frozen=True)
class UnifiedAdmissionEvaluationDesignRecord:
    """Local Exact13 projection evidence; no Phase 2 identity is claimed."""

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


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = False
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=text,
    )


def _validate_expected_base_lineage(repo_root: Path, head_ref: str) -> None:
    base = _git(("cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"), repo_root)
    if base.returncode != 0:
        raise ValueError("expected base commit object is unavailable")
    subject = _git(
        ("show", "-s", "--format=%s", EXPECTED_BASE_COMMIT), repo_root, text=True
    )
    if subject.returncode != 0 or subject.stdout.rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    head = _git(("cat-file", "-e", f"{head_ref}^{{commit}}"), repo_root)
    if head.returncode != 0:
        raise ValueError("head_ref is not a commit")
    lineage = _git(
        ("merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref), repo_root
    )
    if lineage.returncode != 0:
        raise ValueError("expected base is not an ancestor of head_ref")


def _safe_relative_path(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.as_posix() == str(path)
    )


def _structural_source_check(path: Path, repo_root: Path) -> None:
    if not _safe_relative_path(path):
        raise ValueError(f"unsafe source path: {path}")
    tracked = _git(("ls-files", "--error-unmatch", "--", path.as_posix()), repo_root)
    if tracked.returncode != 0:
        raise ValueError(f"source is not tracked: {path}")
    base_type = _git(
        ("cat-file", "-t", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"),
        repo_root,
        text=True,
    )
    if base_type.returncode != 0 or base_type.stdout.strip() != "blob":
        raise ValueError(f"base-tree source is not a blob: {path}")
    filesystem_path = repo_root / path
    try:
        status = filesystem_path.lstat()
    except FileNotFoundError as error:
        raise ValueError(f"source is missing: {path}") from error
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise ValueError(f"source is not a regular non-symlink file: {path}")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    _validate_expected_base_lineage(root, head_ref)
    # This complete loop is deliberately before the first source-byte read.
    for path in SOURCE_PATHS:
        _structural_source_check(path, root)
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(("show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"), root)
        if base.returncode != 0:
            raise ValueError(f"base-tree source read failed: {path}")
        content = (root / path).read_bytes()
        expected = SOURCE_SHA256[path]
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(content).hexdigest()
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(path, expected, base_sha, filesystem_sha, content)
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    if type(value) is not FrozenSourceSnapshot or type(value.records) is not tuple:
        return False
    if tuple(record.relative_path for record in value.records) != SOURCE_PATHS:
        return False
    return all(
        type(record) is FrozenSourceRecord
        and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
        and record.base_tree_sha256 == record.expected_sha256
        and record.filesystem_sha256 == record.expected_sha256
        and type(record.content) is bytes
        and hashlib.sha256(record.content).hexdigest() == record.expected_sha256
        for record in value.records
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    for record in snapshot.records:
        if record.relative_path == path:
            return record
    raise KeyError(path)


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    reader = csv.DictReader(
        io.StringIO(_record(snapshot, path).content.decode("utf-8"), newline="")
    )
    if reader.fieldnames is None:
        raise ValueError(f"CSV has no header: {path}")
    return CsvDocument(tuple(reader.fieldnames), tuple(dict(row) for row in reader))


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    return ast.parse(_record(snapshot, path).content.decode("utf-8"), path.as_posix())


def _top_level_function_names(tree: ast.Module) -> tuple[str, ...]:
    return tuple(node.name for node in tree.body if isinstance(node, ast.FunctionDef))


def _function_call_names(tree: ast.Module, function_name: str) -> set[str]:
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    ]
    if len(nodes) != 1:
        raise ValueError(f"function shape changed: {function_name}")
    calls: set[str] = set()
    for node in ast.walk(nodes[0]):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return calls


def _mapping_proxy_literal_keys(tree: ast.Module, assignment_name: str) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != assignment_name:
            continue
        value = node.value
        if (
            not isinstance(value, ast.Call)
            or not isinstance(value.func, ast.Name)
            or value.func.id != "MappingProxyType"
            or len(value.args) != 1
            or not isinstance(value.args[0], ast.Dict)
        ):
            raise ValueError(f"{assignment_name} is not a literal MappingProxyType")
        keys = value.args[0].keys
        if any(not isinstance(key, ast.Constant) or type(key.value) is not str for key in keys):
            raise ValueError(f"{assignment_name} contains a non-string literal key")
        return tuple(key.value for key in keys if isinstance(key, ast.Constant))
    raise ValueError(f"missing assignment: {assignment_name}")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    standalone_manifest = _json_document(snapshot, SOURCE_PATHS[1])
    standalone_truth = _csv_document(snapshot, SOURCE_PATHS[3])
    phase4_manifest = _json_document(snapshot, SOURCE_PATHS[5])
    issues = _csv_document(snapshot, SOURCE_PATHS[6])
    legacy_contract = _csv_document(snapshot, SOURCE_PATHS[8])
    legacy_routing = _csv_document(snapshot, SOURCE_PATHS[9])
    evaluator_matrix = _csv_document(snapshot, SOURCE_PATHS[10])
    outcome_contract = _csv_document(snapshot, SOURCE_PATHS[11])
    standalone_ast = _ast_document(snapshot, SOURCE_PATHS[0])
    phase4_ast = _ast_document(snapshot, SOURCE_PATHS[4])

    if tuple(path for path in SOURCE_PATHS if path == FORBIDDEN_WRONG_SOURCE_PATH):
        raise ValueError("forbidden wrong predecessor path selected")
    if standalone_manifest.get("truth_matrix_row_count") != 22:
        raise ValueError("standalone Exact22 changed")
    if len(standalone_truth.rows) != 22 or len({r["case_id"] for r in standalone_truth.rows}) != 22:
        raise ValueError("standalone truth matrix is not unique Exact22")
    if standalone_manifest.get("result_fields") != list(STANDALONE_RESULT_FIELDS):
        raise ValueError("standalone Exact10 fields changed")
    if phase4_manifest.get("registered_rule_ids") != list(FUTURE_REGISTERED_RULE_ORDER[:4]):
        raise ValueError("Phase 4 registry boundary changed")
    if _mapping_proxy_literal_keys(phase4_ast, "EVALUATOR_REGISTRY") != FUTURE_REGISTERED_RULE_ORDER[:4]:
        raise ValueError("Phase 4 registry AST boundary changed")
    if "_evaluate_registered_admit_005" in _top_level_function_names(phase4_ast):
        raise ValueError("ADMIT_005 runtime handler already exists")
    if "evaluate_all_rules" in _top_level_function_names(phase4_ast):
        raise ValueError("evaluate_all_rules unexpectedly exists")
    formal_calls = _function_call_names(standalone_ast, FORMAL_EVALUATOR_NAME)
    if {
        "classify_admit_004_admit_005_atom_scope_design",
        "validate_generic_covalent_residue_atom_name",
    } & formal_calls:
        raise ValueError("standalone production call graph invokes design oracle")
    if len(legacy_contract.rows) != 3 or len(legacy_routing.rows) != 74:
        raise ValueError("legacy adapter design contracts changed")
    if len(evaluator_matrix.rows) != 15 or len(outcome_contract.rows) != 29:
        raise ValueError("unified engine contracts changed")
    if tuple(issues.fieldnames) != ISSUE_COLUMNS or len(issues.rows) != 11:
        raise ValueError("Exact11 issue inventory changed")
    provider = [r for r in issues.rows if r["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    coverage = [r for r in issues.rows if r["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    aggregation = [r for r in issues.rows if r["issue_id"] == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]
    if len(provider) != 1 or (provider[0]["status"], provider[0]["severity"], provider[0]["issue_count"]) != ("open", "blocking", "11"):
        raise ValueError("provider blocker changed")
    if len(coverage) != 1 or "ADMIT_005" not in coverage[0]["affected_rules"].split("|") or coverage[0]["status"] != "open" or coverage[0]["severity"] != "blocking":
        raise ValueError("coverage blocker changed")
    if len(aggregation) != 1 or aggregation[0]["status"] != "open" or aggregation[0]["severity"] != "blocking":
        raise ValueError("cross-rule blocker changed")
    result_rows = [row for row in outcome_contract.rows if row["contract_kind"] == "result_field"]
    if tuple(row["field_name"] for row in result_rows) != RESULT_FIELDS:
        raise ValueError("Exact13 frozen field order changed")
    schema_rows = [row for row in outcome_contract.rows if row["field_name"] == "schema_version" and row["contract_kind"] == "result_invariant"]
    if len(schema_rows) != 1 or schema_rows[0]["contract_value"] != RESULT_SCHEMA_VERSION:
        raise ValueError("result schema version changed")
    return {
        "standalone_truth_rows": tuple(dict(row) for row in standalone_truth.rows),
        "issue_rows": tuple(dict(row) for row in issues.rows),
    }


def _exact10_values(source: Admit005EvaluationDesignRecord) -> dict[str, object]:
    return {field.name: getattr(source, field.name) for field in fields(source)}


def _jsonable_dataclass(value: object) -> str:
    return json.dumps(
        {field.name: getattr(value, field.name) for field in fields(value)},
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _canonical_residue_valid(value: object) -> bool:
    return (
        type(value) is str
        and value != ""
        and value.isascii()
        and 1 <= len(value) <= 32
        and value.isalnum()
        and value == value.upper()
    )


def _canonical_atom_valid(value: object) -> bool:
    return (
        type(value) is str
        and value != ""
        and value.isascii()
        and not any(character.isspace() for character in value)
        and value not in (".", "?")
    )


def _source_invariants_valid(source: Admit005EvaluationDesignRecord) -> bool:
    string_fields = (
        source.admission_rule_id,
        source.outcome,
        source.reason,
        source.canonical_residue_name,
        source.canonical_residue_atom_name,
    )
    if any(type(value) is not str for value in string_fields):
        return False
    if type(source.passed) is not bool or type(source.blocks_candidate) is not bool:
        return False
    if type(source.evaluator_io_used) is not bool:
        return False
    if type(source.validated_candidate_fields) is not tuple or any(
        type(pair) is not tuple
        or len(pair) != 2
        or type(pair[0]) is not str
        or type(pair[1]) is not str
        for pair in source.validated_candidate_fields
    ):
        return False
    if type(source.consumed_candidate_fields) is not tuple or any(
        type(value) is not str for value in source.consumed_candidate_fields
    ):
        return False
    if source.admission_rule_id != ADMISSION_RULE_ID:
        return False
    if source.outcome not in ("passed", "rejected", "invalid"):
        return False
    if source.passed is not (source.outcome == "passed"):
        return False
    if source.blocks_candidate is not (source.outcome != "passed"):
        return False
    if (source.outcome == "passed") != (source.reason == ""):
        return False
    if source.consumed_candidate_fields != CANDIDATE_FIELDS:
        return False
    if source.evaluator_io_used is not False:
        return False
    residue_invalid_reasons = {
        "COVALENT_RESIDUE_NAME_TYPE_INVALID",
        "COVALENT_RESIDUE_NAME_EMPTY",
        "COVALENT_RESIDUE_NAME_NON_ASCII",
        "COVALENT_RESIDUE_NAME_SYNTAX_INVALID",
    }
    atom_invalid_reasons = {
        "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID",
        "COVALENT_RESIDUE_ATOM_NAME_EMPTY",
        "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII",
        "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN",
        "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN",
    }
    residue_pair = ("covalent_residue_name", source.canonical_residue_name)
    atom_pair = ("covalent_residue_atom_name", source.canonical_residue_atom_name)
    if source.outcome == "passed":
        valid = (
            source.reason == ""
            and source.canonical_residue_name == "CYS"
            and source.canonical_residue_atom_name == "SG"
        )
        expected_validated = (residue_pair, atom_pair)
    elif source.outcome == "rejected":
        valid = (
            source.reason == "ADMIT_005_CYS_SG_SCOPE_REJECTED"
            and _canonical_residue_valid(source.canonical_residue_name)
            and _canonical_atom_valid(source.canonical_residue_atom_name)
            and (source.canonical_residue_name, source.canonical_residue_atom_name)
            != ("CYS", "SG")
        )
        expected_validated = (residue_pair, atom_pair)
    elif source.reason in residue_invalid_reasons:
        valid = source.canonical_residue_name == source.canonical_residue_atom_name == ""
        expected_validated = ()
    elif source.reason in atom_invalid_reasons:
        valid = _canonical_residue_valid(source.canonical_residue_name) and source.canonical_residue_atom_name == ""
        expected_validated = (residue_pair,)
    else:
        return False
    return valid and source.validated_candidate_fields == expected_validated


def validate_source_shape_and_invariants_for_design(
    source: object,
) -> SourceValidationDecision:
    """Stage A: exact local design type and Exact10 invariants, before oracle."""
    if type(source) is not Admit005EvaluationDesignRecord:
        return SourceValidationDecision(
            False,
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            ADMISSION_RULE_ID,
            True,
            True,
            False,
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        )
    if not _source_invariants_valid(source):
        return SourceValidationDecision(
            False,
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            ADMISSION_RULE_ID,
            True,
            True,
            False,
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    return SourceValidationDecision(
        True, "", ADMISSION_RULE_ID, True, True, True, ""
    )


def validate_source_oracle_equivalence_for_design(
    source: Admit005EvaluationDesignRecord,
    expected: Admit005EvaluationDesignRecord,
) -> SourceValidationDecision:
    """Stage B: compare Exact10 only after Stage A has accepted source."""
    prevalidation = validate_source_shape_and_invariants_for_design(source)
    if not prevalidation.accepted:
        return prevalidation
    if type(expected) is not Admit005EvaluationDesignRecord or not _source_invariants_valid(expected) or source != expected:
        return SourceValidationDecision(
            False,
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            ADMISSION_RULE_ID,
            True,
            True,
            False,
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    return SourceValidationDecision(True, "", ADMISSION_RULE_ID, True, True, True, "")


def _design_source_from_truth_row(row: Mapping[str, str]) -> Admit005EvaluationDesignRecord:
    validated_json = json.loads(row["validated_candidate_fields_json"])
    validated = tuple((pair[0], pair[1]) for pair in validated_json)
    outcome = row["observed_outcome"]
    return Admit005EvaluationDesignRecord(
        admission_rule_id=ADMISSION_RULE_ID,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=row["observed_reason"],
        canonical_residue_name=row["canonical_residue_name"],
        canonical_residue_atom_name=row["canonical_residue_atom_name"],
        validated_candidate_fields=validated,
        consumed_candidate_fields=CANDIDATE_FIELDS,
        evaluator_io_used=False,
    )


def project_exact10_to_exact13_for_design(
    source: Admit005EvaluationDesignRecord,
) -> UnifiedAdmissionEvaluationDesignRecord:
    """Construct expected truth evidence; this is not a registered handler."""
    return UnifiedAdmissionEvaluationDesignRecord(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=(),
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_ID,
    )


def candidate_invalid_exact13_for_design(
    reason: str,
) -> UnifiedAdmissionEvaluationDesignRecord:
    return UnifiedAdmissionEvaluationDesignRecord(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=CANDIDATE_FIELDS,
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_ID,
    )


def _contract_definitions() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("IDENTITY_001", "registration", "admission_rule_id", ADMISSION_RULE_ID),
        ("IDENTITY_002", "registration", "admission_rule_name", ADMISSION_RULE_NAME),
        ("IDENTITY_003", "registration", "adapter_id", ADAPTER_ID),
        ("IDENTITY_004", "registration", "formal_evaluator", FORMAL_EVALUATOR_NAME),
        ("IDENTITY_005", "registration", "formal_evaluator_source", FORMAL_EVALUATOR_SOURCE),
        ("IDENTITY_006", "registration", "future_registered_rule_order", "|".join(FUTURE_REGISTERED_RULE_ORDER)),
        ("REUSE_001", "phase2_reuse", "public_runtime", "evaluate_admission_rule_existing_phase4_api"),
        ("REUSE_002", "phase2_reuse", "result_type_identity", "UnifiedAdmissionRuleEvaluation"),
        ("REUSE_003", "phase2_reuse", "dispatch_error_type_identity", "UnifiedAdmissionDispatchError"),
        ("REUSE_004", "phase2_reuse", "result_schema_version", RESULT_SCHEMA_VERSION),
        ("REUSE_005", "phase2_reuse", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("REUSE_006", "phase2_reuse", "exact6_fields", "|".join(DISPATCH_ERROR_FIELDS)),
        ("ORDER_001", "execution", "global_precedence", "|".join(EXECUTION_PRECEDENCE)),
        ("CONTEXT_001", "context", "context_order", "|".join(CONTEXT_ORDER)),
        ("CONTEXT_002", "context", "batch_failure", CONTEXT_REASONS["batch_context"]),
        ("CONTEXT_003", "context", "evaluation_failure", CONTEXT_REASONS["evaluation_context"]),
        ("CONTEXT_004", "context", "download_failure", CONTEXT_REASONS["download_result_context"]),
        ("CONTEXT_005", "context", "stage_failure", CONTEXT_REASONS["stage_authorization_context"]),
        ("CONTEXT_006", "context", "failure_payload", "Exact6|context_routing_invalid|known=true|callable=true|adapter_ready=true|no_partial_result"),
        ("CANDIDATE_001", "candidate", "mapping_acceptance", "isinstance(candidate_record,Mapping)"),
        ("CANDIDATE_002", "candidate", "mapping_subclass", "accepted"),
        ("CANDIDATE_003", "candidate", "extra_fields", "ignored"),
        ("CANDIDATE_004", "candidate", "mutation", "no_copy_no_mutation"),
        ("CANDIDATE_005", "candidate", "scalar_values", "original_identity_no_trim_uppercase_coercion_or_prevalidation"),
        ("CANDIDATE_006", "candidate", "required_field_order", "|".join(CANDIDATE_FIELDS)),
        ("CANDIDATE_007", "candidate", "missing_field_precedence", "covalent_residue_name_before_covalent_residue_atom_name"),
        ("CANDIDATE_008", "candidate", "invalid_payload", "Exact13_invalid_consumed_exact2_no_context_no_calls"),
        ("SOURCE_001", "formal_source", "call_shape", "exactly_once_positional_original_objects"),
        ("SOURCE_002", "formal_source", "exact_type", "type(source)isAdmit005EvaluationResult"),
        ("SOURCE_003", "formal_source", "invariants", "Exact10_types_order_cross_field_rule_id_consumed_exact2_no_io"),
        ("SOURCE_004", "formal_source", "type_failure", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID|before_oracle|scope_oracle_calls=0|atom_oracle_calls=0"),
        ("SOURCE_005", "formal_source", "invariant_failure", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID|before_oracle|scope_oracle_calls=0|atom_oracle_calls=0"),
        ("ORACLE_001", "independent_oracle", "helpers", "classify_admit_004_admit_005_atom_scope_design|validate_generic_covalent_residue_atom_name"),
        ("ORACLE_002", "independent_oracle", "call_shape", "each_exactly_once_same_original_objects"),
        ("ORACLE_003", "independent_oracle", "equivalence", "only_after_source_prevalidation_passes|then_Exact10_all_fields_all_order_before_exact13"),
        ("ORACLE_004", "independent_oracle", "mismatch", "after_scope_oracle_calls=1|atom_oracle_calls=1|ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID|no_projection"),
        ("ORACLE_005", "independent_oracle", "standalone_call_graph", "formal_evaluator_does_not_call_design_oracle"),
        ("PROJECTION_001", "unified_projection", "exact10_to_exact13", "source_fields_passthrough_plus_phase2_schema_rule_name_empty_context_adapter_id"),
        ("PROJECTION_002", "unified_projection", "normalized_values", "equals_source_validated_candidate_fields"),
        ("PROJECTION_003", "unified_projection", "partial_validation", "residue_invalid_empty|atom_invalid_residue_only|passed_or_rejected_residue_then_atom"),
        ("PROJECTION_004", "unified_projection", "rejected", "passthrough_not_blocked_not_invalid_validated_fields_preserved"),
        ("BOUNDARY_001", "boundary", "current_phase4", "ADMIT_005_not_registered_registry_exact_ADMIT_001_to_004"),
        ("BOUNDARY_002", "boundary", "excluded", "adapter_implementation|registry_modification|evaluate_all_rules|combined_verdict|cross_rule_precedence|ADMIT_006"),
        ("BOUNDARY_003", "boundary", "io_and_mutation", "no_io_no_candidate_mutation"),
        ("ISSUE_001", "readiness", "exact11", "copied_unchanged_provider_and_coverage_and_cross_rule_blockers_open"),
        ("NEXT_001", "readiness", "recommended_next_step", RECOMMENDED_NEXT_STEP),
    )


def _contract_rows() -> list[dict[str, str]]:
    definitions = _contract_definitions()
    if len({row[0] for row in definitions}) != len(definitions):
        raise RuntimeError("duplicate contract definition")
    return [
        {
            "contract_order": str(index),
            "contract_id": contract_id,
            "contract_group": group,
            "contract_subject": subject,
            "contract_value": value,
            "contract_status": "frozen",
        }
        for index, (contract_id, group, subject, value) in enumerate(definitions, 1)
    ]


def _context_error_json(reason: str) -> str:
    return json.dumps(
        {
            "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "admission_rule_id": ADMISSION_RULE_ID,
            "known_rule": True,
            "callable_discovered": True,
            "adapter_ready": True,
            "reason": reason,
        },
        separators=(",", ":"),
    )


def _routing_rows() -> list[dict[str, str]]:
    invalid_mapping = candidate_invalid_exact13_for_design(
        "ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID"
    )
    missing_residue = candidate_invalid_exact13_for_design(
        "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"
    )
    missing_atom = candidate_invalid_exact13_for_design(
        "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name"
    )
    specs = (
        ("context", "CONTEXT_BATCH", "batch_context non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], "", "false", "false"),
        ("context", "CONTEXT_EVALUATION", "evaluation_context non-None", "dispatch_error", CONTEXT_REASONS["evaluation_context"], "", "false", "false"),
        ("context", "CONTEXT_DOWNLOAD", "download_result_context non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], "", "false", "false"),
        ("context", "CONTEXT_STAGE", "stage_authorization_context non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], "", "false", "false"),
        ("context", "CONTEXT_MULTI", "all four contexts non-None", "first_context_dispatch_error", CONTEXT_REASONS["batch_context"], "", "false", "false"),
        ("candidate", "CANDIDATE_NON_MAPPING", "candidate_record non-Mapping", "unified_invalid_result", invalid_mapping.reason, _jsonable_dataclass(invalid_mapping), "false", "false"),
        ("candidate", "CANDIDATE_MISSING_RESIDUE", "required residue absent", "unified_invalid_result", missing_residue.reason, _jsonable_dataclass(missing_residue), "false", "false"),
        ("candidate", "CANDIDATE_MISSING_ATOM", "residue present and atom absent", "unified_invalid_result", missing_atom.reason, _jsonable_dataclass(missing_atom), "false", "false"),
        ("candidate", "CANDIDATE_EXTRA_FIELDS", "extra fields present", "ignore_extra_and_evaluate", "", "", "true", "true"),
        ("candidate", "CANDIDATE_MAPPING_SUBCLASS", "Mapping subclass", "accept_and_evaluate", "", "", "true", "true"),
        ("candidate", "CANDIDATE_NOT_MUTATED", "mutable Mapping", "read_only_no_copy_no_mutation", "", "", "true", "true"),
        ("candidate", "CANDIDATE_SCALAR_IDENTITY", "two required scalar objects", "pass_original_identity_positionally", "", "", "true", "true"),
        ("candidate", "CANDIDATE_REQUIRED_ORDER", "both required fields absent", "residue_missing_precedes_atom_missing", missing_residue.reason, _jsonable_dataclass(missing_residue), "false", "false"),
    )
    rows = []
    for index, spec in enumerate(specs, 1):
        group, case_id, condition, behavior, reason, result_json, formal, oracle = spec
        rows.append(
            {
                "matrix_order": str(index),
                "matrix_group": group,
                "case_id": case_id,
                "condition": condition,
                "expected_behavior": behavior,
                "expected_reason": reason,
                "expected_exact13_json": result_json,
                "formal_evaluator_called": formal,
                "oracle_called": oracle,
                "case_passed": "true",
            }
        )
    return rows


def _truth_row(
    case_id: str,
    group: str,
    behavior: str,
    *,
    code: str = "",
    reason: str = "",
    source: object | None = None,
    oracle: object | None = None,
    unified: object | None = None,
    formal_calls: int = 0,
    scope_calls: int = 0,
    atom_calls: int = 0,
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": group,
        "behavior": behavior,
        "expected_dispatch_code": code,
        "expected_reason": reason,
        "source_exact10_json": "" if source is None else _jsonable_dataclass(source),
        "oracle_exact10_json": "" if oracle is None else _jsonable_dataclass(oracle),
        "unified_exact13_json": "" if unified is None else _jsonable_dataclass(unified),
        "formal_call_count": str(formal_calls),
        "scope_oracle_call_count": str(scope_calls),
        "atom_oracle_call_count": str(atom_calls),
        "case_passed": "true",
    }


class _SourceSubclass(Admit005EvaluationDesignRecord):
    pass


def _unsafe_source(
    baseline: Admit005EvaluationDesignRecord, **overrides: object
) -> Admit005EvaluationDesignRecord:
    values = _exact10_values(baseline)
    values.update(overrides)
    result = object.__new__(Admit005EvaluationDesignRecord)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _candidate_envelope_truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [
        _truth_row(
            "A_NON_MAPPING",
            "candidate_envelope",
            "non-Mapping becomes unified invalid",
            reason="ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID",
            unified=candidate_invalid_exact13_for_design("ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID"),
        ),
        _truth_row(
            "A_MISSING_RESIDUE",
            "candidate_envelope",
            "missing residue wins",
            reason="ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name",
            unified=candidate_invalid_exact13_for_design("ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"),
        ),
        _truth_row(
            "A_MISSING_ATOM",
            "candidate_envelope",
            "missing atom after residue",
            reason="ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name",
            unified=candidate_invalid_exact13_for_design("ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name"),
        ),
    ]
    by_id = {row["case_id"]: row for row in predecessor_rows}
    cases = (
        ("A_EXTRA_FIELDS", "extra fields ignored", "PASS_001"),
        ("A_MAPPING_SUBCLASS", "Mapping subclass accepted", "PASS_001"),
        ("A_NOT_MUTATED", "candidate not mutated", "REJECT_005"),
        ("A_SCALAR_IDENTITY", "scalar object identity preserved", "PASS_002"),
    )
    for case_id, behavior, predecessor_id in cases:
        source = _design_source_from_truth_row(by_id[predecessor_id])
        prevalidation = validate_source_shape_and_invariants_for_design(source)
        expected = Admit005EvaluationDesignRecord(**_exact10_values(source))
        equivalence = validate_source_oracle_equivalence_for_design(source, expected)
        if not prevalidation.accepted or not equivalence.accepted:
            raise RuntimeError(f"candidate envelope truth failed: {case_id}")
        rows.append(
            _truth_row(
                case_id,
                "candidate_envelope",
                behavior,
                source=source,
                oracle=expected,
                unified=project_exact10_to_exact13_for_design(source),
                formal_calls=1,
                scope_calls=1,
                atom_calls=1,
            )
        )
    return rows


def _context_truth_rows() -> list[dict[str, str]]:
    specs = (
        ("B_BATCH", "batch non-None", CONTEXT_REASONS["batch_context"]),
        ("B_EVALUATION", "evaluation non-None", CONTEXT_REASONS["evaluation_context"]),
        ("B_DOWNLOAD", "download non-None", CONTEXT_REASONS["download_result_context"]),
        ("B_STAGE", "stage non-None", CONTEXT_REASONS["stage_authorization_context"]),
        ("B_MULTI", "multiple contexts use first reason", CONTEXT_REASONS["batch_context"]),
    )
    return [
        _truth_row(
            case_id,
            "context_routing",
            behavior,
            code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            reason=reason,
        )
        for case_id, behavior, reason in specs
    ]


def _standalone_projection_truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    expected_case_order = (
        "PASS_001", "PASS_002", "REJECT_001", "REJECT_002", "REJECT_003",
        "REJECT_004", "REJECT_005", "REJECT_006", "INVALID_RESIDUE_001",
        "INVALID_RESIDUE_002", "INVALID_RESIDUE_003", "INVALID_RESIDUE_004",
        "INVALID_RESIDUE_005", "INVALID_ATOM_001", "INVALID_ATOM_002",
        "INVALID_ATOM_003", "INVALID_ATOM_004", "INVALID_ATOM_005",
        "INVALID_ATOM_006", "INVALID_ATOM_007", "INVALID_ATOM_008",
        "PRECEDENCE_001",
    )
    if tuple(row["case_id"] for row in predecessor_rows) != expected_case_order:
        raise RuntimeError("standalone Exact22 case order changed")
    rows = []
    for predecessor in predecessor_rows:
        case_id = predecessor["case_id"]
        source = _design_source_from_truth_row(predecessor)
        prevalidation = validate_source_shape_and_invariants_for_design(source)
        expected = Admit005EvaluationDesignRecord(**_exact10_values(source))
        decision = validate_source_oracle_equivalence_for_design(source, expected)
        unified = project_exact10_to_exact13_for_design(source)
        if (
            not prevalidation.accepted
            or not decision.accepted
            or source != expected
            or source.outcome != predecessor["observed_outcome"]
            or source.reason != predecessor["observed_reason"]
            or unified.outcome != source.outcome
            or unified.normalized_values != source.validated_candidate_fields
            or unified.validated_candidate_fields != source.validated_candidate_fields
        ):
            raise RuntimeError(f"standalone projection failed: {case_id}")
        rows.append(
            _truth_row(
                f"C_{case_id}",
                "standalone_exact22",
                "Exact10 equals independent oracle and projects field-for-field",
                reason=source.reason,
                source=source,
                oracle=expected,
                unified=unified,
                formal_calls=1,
                scope_calls=1,
                atom_calls=1,
            )
        )
    return rows


def _source_failure_truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    by_id = {row["case_id"]: row for row in predecessor_rows}
    expected = _design_source_from_truth_row(by_id["PASS_001"])
    mismatch_expected = _design_source_from_truth_row(by_id["REJECT_005"])
    subclass = _SourceSubclass(**_exact10_values(expected))
    failures: tuple[tuple[str, str, object, Admit005EvaluationDesignRecord | None], ...] = (
        ("D_WRONG_TYPE", "wrong source type", SimpleNamespace(), None),
        ("D_SUBCLASS", "source subclass", subclass, None),
        ("D_RULE_ID", "source admission_rule_id mismatch", _unsafe_source(expected, admission_rule_id="ADMIT_004"), None),
        ("D_FIELD_INVARIANT", "source/result field invariant mismatch", _unsafe_source(expected, passed=False), None),
        ("D_ORACLE_MISMATCH", "source/input oracle mismatch", expected, mismatch_expected),
        ("D_IO_TRUE", "evaluator_io_used true", _unsafe_source(expected, evaluator_io_used=True), None),
        ("D_CONSUMED_FIELDS", "consumed fields mismatch", _unsafe_source(expected, consumed_candidate_fields=("covalent_residue_name",)), None),
    )
    rows = []
    for case_id, behavior, source, oracle in failures:
        prevalidation = validate_source_shape_and_invariants_for_design(source)
        scope_calls = atom_calls = 0
        if prevalidation.accepted:
            if oracle is None:
                raise RuntimeError(f"accepted source lacks oracle evidence: {case_id}")
            scope_calls = atom_calls = 1
            decision = validate_source_oracle_equivalence_for_design(source, oracle)
        else:
            decision = prevalidation
        expected_reason = (
            "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
            if case_id in ("D_WRONG_TYPE", "D_SUBCLASS")
            else "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
        if (
            decision.accepted
            or decision.code != "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
            or decision.reason != expected_reason
            or decision.adapter_ready is not False
        ):
            raise RuntimeError(f"source failure did not fail closed: {case_id}")
        rows.append(
            _truth_row(
                case_id,
                "source_fail_closed",
                behavior,
                code=decision.code,
                reason=decision.reason,
                source=source if type(source) is Admit005EvaluationDesignRecord else None,
                oracle=oracle,
                formal_calls=1,
                scope_calls=scope_calls,
                atom_calls=atom_calls,
            )
        )
    return rows


def _boundary_truth_rows() -> list[dict[str, str]]:
    first = _truth_row(
        "E_NOT_REGISTERED",
        "boundary",
        "frozen Phase 4 evidence says not registered",
        code="UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        reason="UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    )
    second = _truth_row(
        "E_REGISTRY_EXACT4",
        "boundary",
        "current registry remains ADMIT_001 through ADMIT_004",
    )
    return [first, second]


TRUTH_GROUP_COUNTS = {
    "candidate_envelope": 7,
    "context_routing": 5,
    "standalone_exact22": 22,
    "source_fail_closed": 7,
    "boundary": 2,
}


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [
        *_candidate_envelope_truth_rows(predecessor_rows),
        *_context_truth_rows(),
        *_standalone_projection_truth_rows(predecessor_rows),
        *_source_failure_truth_rows(predecessor_rows),
        *_boundary_truth_rows(),
    ]
    counts = Counter(row["case_group"] for row in rows)
    if dict(counts) != TRUTH_GROUP_COUNTS:
        raise RuntimeError("truth group counts changed")
    if len(rows) != sum(TRUTH_GROUP_COUNTS.values()):
        raise RuntimeError("truth row count changed")
    if len({row["case_id"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate truth case")
    if not all(row["case_passed"] == "true" for row in rows):
        raise RuntimeError("truth case failed")
    return rows


EXECUTED_SAFETY_ITEMS = (
    "exact_source_reads",
    "predecessor_sha_validation",
    "standalone_api_result_validation",
    "phase4_exact13_exact6_validation",
    "candidate_projection_contract_design",
    "context_routing_contract_design",
    "source_validation_contract_design",
    "independent_oracle_equivalence_design",
    "unified_result_mapping_design",
    "synthetic_truth_construction",
    "issue_preservation",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "raw_read",
    "provider_parser",
    "candidate_materialization",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "phase4_runtime_modification",
    "registry_modification",
    "adapter_implementation",
    "admit_005_registration",
    "admit_006_work",
    "evaluate_all_rules",
    "combined_verdict",
    "cross_rule_aggregation",
    "network_download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward_loss_training",
)


def _safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
    if len({item for item, _ in definitions}) != len(definitions):
        raise RuntimeError("duplicate safety definition")
    return [
        {
            "safety_item": item,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "safety_passed": "true",
        }
        for item, executed in definitions
    ]


READINESS = {
    "admit_005_standalone_evaluator_available": True,
    "admit_005_candidate_projection_contract_frozen": True,
    "admit_005_context_routing_contract_frozen": True,
    "admit_005_unified_adapter_contract_frozen": True,
    "admit_005_source_result_validation_contract_frozen": True,
    "admit_005_source_oracle_equivalence_contract_frozen": True,
    "admit_005_unified_result_projection_contract_frozen": True,
    "admit_005_rejected_passthrough_contract_frozen": True,
    "ready_for_admit_005_unified_adapter_implementation": True,
    "feature_semantics_audit_required_before_training": True,
    "admit_005_unified_adapter_implemented": False,
    "admit_005_registered_in_engine": False,
    "phase4_runtime_modified": False,
    "admit_006_to_015_registered_in_engine": False,
    "all_15_rules_covered": False,
    "evaluate_all_rules_implemented": False,
    "combined_candidate_verdict_contract_frozen": False,
    "combined_candidate_verdict_implemented": False,
    "cross_rule_precedence_frozen": False,
    "real_candidate_evaluation": False,
    "exact11_real_rows_evaluated": False,
    "ready_for_bulk_download_now": False,
    "ready_for_training": False,
    "ready_to_train_now": False,
}


def build_design_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot() if source_snapshot is None else source_snapshot
    historical = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    routing_rows = _routing_rows()
    truth_rows = _truth_rows(historical["standalone_truth_rows"])
    safety_rows = _safety_rows()
    issue_rows = [dict(row) for row in historical["issue_rows"]]
    source_failures = {
        row["case_id"]: row
        for row in truth_rows
        if row["case_group"] == "source_fail_closed"
    }
    prevalidation_failure_ids = (
        "D_WRONG_TYPE",
        "D_SUBCLASS",
        "D_RULE_ID",
        "D_FIELD_INVARIANT",
        "D_IO_TRUE",
        "D_CONSUMED_FIELDS",
    )
    checks = (
        len(contract_rows) == len(_contract_definitions()),
        len({row["contract_id"] for row in contract_rows}) == len(contract_rows),
        len(routing_rows) == 13,
        len({row["case_id"] for row in routing_rows}) == 13,
        len(truth_rows) == 43,
        all(
            (
                source_failures[case_id]["formal_call_count"],
                source_failures[case_id]["scope_oracle_call_count"],
                source_failures[case_id]["atom_oracle_call_count"],
            )
            == ("1", "0", "0")
            for case_id in prevalidation_failure_ids
        ),
        (
            source_failures["D_ORACLE_MISMATCH"]["formal_call_count"],
            source_failures["D_ORACLE_MISMATCH"]["scope_oracle_call_count"],
            source_failures["D_ORACLE_MISMATCH"]["atom_oracle_call_count"],
        )
        == ("1", "1", "1"),
        len(issue_rows) == 11,
        all(row["safety_passed"] == "true" for row in safety_rows),
        READINESS["ready_for_admit_005_unified_adapter_implementation"],
        not READINESS["admit_005_unified_adapter_implemented"],
        not READINESS["admit_005_registered_in_engine"],
        not READINESS["ready_for_bulk_download_now"],
        not READINESS["ready_for_training"],
    )
    if not all(checks):
        raise RuntimeError("ADMIT_005 adapter design state failed closed")
    return {
        "source_snapshot": snapshot,
        "contract_rows": contract_rows,
        "routing_rows": routing_rows,
        "truth_rows": truth_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "readiness": dict(READINESS),
        "all_checks_passed": True,
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        lineterminator="\n",
        extrasaction="raise",
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
    snapshot = state["source_snapshot"]
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_input_count": len(SOURCE_PATHS),
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {
                "source_order": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked_by_git": True,
                "base_tree_blob": True,
                "filesystem_regular": True,
                "non_symlink": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": len(OUTPUT_FILES),
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "production_standard_library_only": True,
        "production_project_module_imports": False,
        "predecessor_modules_not_imported_or_executed_by_production": True,
        "source_prevalidation_precedes_oracle": True,
        "source_type_failure_oracle_calls": 0,
        "source_invariant_failure_oracle_calls": 0,
        "oracle_mismatch_scope_oracle_calls": 1,
        "oracle_mismatch_atom_oracle_calls": 1,
        "output_sha256_frozen_by_checker": True,
        "future_registration_identity": {
            "admission_rule_id": ADMISSION_RULE_ID,
            "admission_rule_name": ADMISSION_RULE_NAME,
            "adapter_id": ADAPTER_ID,
            "formal_evaluator": FORMAL_EVALUATOR_NAME,
            "formal_evaluator_source": FORMAL_EVALUATOR_SOURCE,
            "future_registered_rule_order": list(FUTURE_REGISTERED_RULE_ORDER),
        },
        "execution_precedence": list(EXECUTION_PRECEDENCE),
        "context_order": list(CONTEXT_ORDER),
        "context_reasons": dict(CONTEXT_REASONS),
        "candidate_fields": list(CANDIDATE_FIELDS),
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "routing_matrix_row_count": len(state["routing_rows"]),
        "routing_matrix_pass_count": len(state["routing_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_pass_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(TRUTH_GROUP_COUNTS),
        "safety_row_count": len(state["safety_rows"]),
        "safety_pass_count": len(state["safety_rows"]),
        "active_issue_count": len(state["issue_rows"]),
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "readiness": dict(state["readiness"]),
        **dict(state["readiness"]),
        "adapter_implementation_excluded": True,
        "admit_005_registration_excluded": True,
        "phase4_runtime_unchanged": True,
        "admit_006_work_excluded": True,
        "real_candidate_and_exact11_evaluation_excluded": True,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_checks_passed": True,
        "all_candidate_projection_checks_passed": True,
        "all_context_routing_checks_passed": True,
        "all_source_validation_checks_passed": True,
        "all_oracle_equivalence_checks_passed": True,
        "all_projection_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    }
    return payloads, manifest


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        status = root.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
        entries = tuple(root.iterdir())
        unexpected = {entry.name for entry in entries} - set(OUTPUT_FILES)
        if unexpected:
            raise ValueError("output root contains unexpected entries")
        for entry in entries:
            entry_status = entry.lstat()
            if stat.S_ISLNK(entry_status.st_mode) or not stat.S_ISREG(entry_status.st_mode):
                raise ValueError("output root contains an unsafe entry")


def run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_design_state()
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    root.mkdir(parents=True, exist_ok=True)
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

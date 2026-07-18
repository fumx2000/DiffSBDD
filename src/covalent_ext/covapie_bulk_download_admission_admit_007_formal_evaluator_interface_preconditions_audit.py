"""Read-only ADMIT_007 formal-evaluator interface preconditions audit v1.

This metadata-only gate inventories committed contracts.  It does not implement
an evaluator, adapter, registry entry, provider mapping, or candidate run.
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_007 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "afed6395fa254db664aeaf05b343a6d9eeb41ae8"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_006 v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_007_formal_evaluator_preconditions_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_007_standalone_evaluator_interface_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1"
)
ENUM_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
ENGINE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1"
)
ADMIT006_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_006_rule_logic_interface_v1"
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_006_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_006_runtime_issue_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
    str(ENUM_ROOT / "covapie_covalent_event_evidence_source_enum_contract_manifest.json"),
    str(ENUM_ROOT / "covapie_covalent_event_evidence_source_enum_registry.csv"),
    str(ENUM_ROOT / "covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv"),
    str(ENUM_ROOT / "covapie_admit_006_admit_007_evidence_responsibility_matrix.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(ENGINE_ROOT / "covapie_unified_admission_result_schema_and_outcome_contract.csv"),
    str(ENGINE_ROOT / "covapie_unified_admission_evaluator_and_context_routing_matrix.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit.py",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py",
    str(ADMIT006_ROOT / "covapie_admit_006_rule_logic_interface_manifest.json"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
    "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
    "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
    "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
    "7a4c3e2b7be8a097be521d98cd3a9d8003c766cc95a1d41a4b68198f6e6729a7",
    "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
    "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
    "fabac801a86d3b5e31298e3ad29e2e51d72a3cef46cfb28e5a25a5c3c8d6f3d3",
    "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "921356eaa15f40fed925d11d73a6fbb868b4c881828c358fb35fde168b8c33f8",
), strict=True))

(
    RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH,
    ENUM_SOURCE_PATH, ENUM_MANIFEST_PATH, ENUM_REGISTRY_PATH, ENUM_TRUTH_PATH,
    RESPONSIBILITY_PATH, RULE_REGISTRY_PATH, RESULT_CONTRACT_PATH,
    ROUTING_CONTRACT_PATH, ADMIT006_AUDIT_SOURCE_PATH, ADMIT006_SOURCE_PATH,
    ADMIT006_MANIFEST_PATH,
) = SOURCE_PATHS

CANONICAL_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
ALLOWED_COVALENT_EVIDENCE_CLASSES = CANONICAL_ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CONTEXT_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
FORMAL_BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
HISTORICAL_REGISTRY_REASON = "distance_only_inference_not_admissible"
INDEPENDENT_ORACLE = "classify_admit_006_admit_007_evidence_design"

MATCH_TERMS = (
    "ADMIT_007", "distance_only_inference_forbidden",
    HISTORICAL_REGISTRY_REASON, FORMAL_BLOCKED_REASON,
    "covalent_event_evidence_source", "allowed_covalent_evidence_classes",
    "distance_only_inference", "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation", INDEPENDENT_ORACLE,
)

SOURCE_BOUNDARY_FILENAME = "covapie_admit_007_source_boundary_audit.csv"
OCCURRENCE_FILENAME = "covapie_admit_007_field_occurrence_inventory.csv"
VALUE_FILENAME = "covapie_admit_007_observed_evidence_value_inventory.csv"
PRECONDITION_FILENAME = "covapie_admit_007_evaluator_precondition_matrix.csv"
ISSUE_FILENAME = "covapie_admit_007_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_007_formal_evaluator_preconditions_manifest.json"
CSV_OUTPUTS = (
    PRECONDITION_FILENAME, OCCURRENCE_FILENAME, VALUE_FILENAME,
    SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
OCCURRENCE_COLUMNS = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "contains_concrete_value", "concrete_value",
    "authoritative_for_runtime_semantics", "occurrence_passed",
)
VALUE_COLUMNS = (
    "value_order", "observed_value", "source_relative_path", "source_row_or_symbol",
    "source_role", "exact_string", "occurrence_count", "evidence_interpretation",
    "real_provider_value", "enum_membership_frozen", "safe_for_admit_007_pass",
    "value_inventory_passed",
)
PRECONDITION_COLUMNS = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_007_candidate_field_contract_available",
    "admit_007_scalar_validation_contract_available",
    "admit_007_context_contract_available",
    "admit_007_enum_contract_available",
    "admit_007_reason_outcome_contract_available",
    "admit_007_canonical_state_contract_available",
    "admit_007_independent_semantic_oracle_available",
    "admit_007_shared_enum_dependency_resolved",
    "admit_007_standalone_evaluator_preconditions_complete",
    "ready_for_admit_007_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_007_standalone_evaluator_implemented",
    "admit_007_unified_adapter_contract_frozen",
    "admit_007_unified_adapter_implemented",
    "admit_007_registered_in_engine",
    "current_exact6_runtime_modified",
    "admit_008_standalone_evaluator_implemented",
    "admit_008_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_provider_enum_mapping_validated",
    "real_candidate_evaluation", "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False
    )


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_expected_base_lineage(repo_root: Path, *, head_ref: str = "HEAD") -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root)
    if base.returncode != 0:
        raise ValueError("expected base commit object is missing")
    if subject.returncode != 0 or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base commit subject mismatch")
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Metadata-only preflight; source content is not read here."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(fields) == 3
        and fields[0] in ("100644", "100755") and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Finish all structural checks before the first explicit byte read."""
    if len(SOURCE_PATHS) != 14 or len(set(SOURCE_PATHS)) != 14 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact14 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 14
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(item for item in snapshot.records if item.relative_path == path)
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    return ast.parse(
        _record(snapshot, path).content_bytes.decode("utf-8", errors="strict"),
        filename=path.as_posix(),
    )


def _row(document: CsvDocument, key: str, value: str) -> dict[str, str]:
    matches = tuple(row for row in document.rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _top_level_functions(tree: ast.Module) -> tuple[str, ...]:
    return tuple(node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    runtime_manifest = _json_document(snapshot, RUNTIME_MANIFEST_PATH)
    runtime_issues = _csv_document(snapshot, RUNTIME_ISSUE_PATH)
    enum_manifest = _json_document(snapshot, ENUM_MANIFEST_PATH)
    enum_registry = _csv_document(snapshot, ENUM_REGISTRY_PATH)
    truth = _csv_document(snapshot, ENUM_TRUTH_PATH)
    responsibility = _csv_document(snapshot, RESPONSIBILITY_PATH)
    design_rules = _csv_document(snapshot, RULE_REGISTRY_PATH)
    routing = _csv_document(snapshot, ROUTING_CONTRACT_PATH)
    result_contract = _csv_document(snapshot, RESULT_CONTRACT_PATH)
    admit006_manifest = _json_document(snapshot, ADMIT006_MANIFEST_PATH)
    runtime_tree = _ast_document(snapshot, RUNTIME_SOURCE_PATH)
    enum_tree = _ast_document(snapshot, ENUM_SOURCE_PATH)
    admit006_tree = _ast_document(snapshot, ADMIT006_SOURCE_PATH)
    enum_values = tuple(row["canonical_value"] for row in enum_registry.rows)
    allowed = tuple(row["canonical_value"] for row in enum_registry.rows if row["included_in_allowed_covalent_evidence_classes"] == "true")
    admit006 = _row(responsibility, "rule_id", "ADMIT_006")
    admit007 = _row(responsibility, "rule_id", "ADMIT_007")
    historical = _row(design_rules, "admission_rule_id", "ADMIT_007")
    route007 = _row(routing, "admission_rule_id", "ADMIT_007")
    enum_issue = _row(runtime_issues, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    coverage = _row(runtime_issues, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    aggregation = _row(runtime_issues, "issue_id", "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED")
    provider = _row(runtime_issues, "issue_id", "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    enum_functions = _top_level_functions(enum_tree)
    runtime_functions = _top_level_functions(runtime_tree)
    admit006_functions = _top_level_functions(admit006_tree)
    exact37 = len(truth.rows) == 37 and all(row.get("case_passed") == "true" for row in truth.rows)
    reason_fields = tuple(row["field_name"] for row in result_contract.rows if row.get("field_name") in ("outcome", "passed", "blocks_candidate", "reason", "canonical_candidate_values", "validated_candidate_fields"))
    if not (
        enum_values == CANONICAL_ENUM_MEMBERS and allowed == ALLOWED_COVALENT_EVIDENCE_CLASSES
        and enum_manifest.get("normative_enum_members") == list(CANONICAL_ENUM_MEMBERS)
        and enum_manifest.get("allowed_covalent_evidence_classes") == list(ALLOWED_COVALENT_EVIDENCE_CLASSES)
        and enum_manifest.get("covalent_event_evidence_source_scalar_validation_contract_frozen") is True
        and enum_manifest.get("allowed_covalent_evidence_classes_context_contract_frozen") is True
        and enum_manifest.get("admit_007_reason_outcome_contract_frozen") is True
        and enum_manifest.get("covalent_event_evidence_source_design_oracle_available") is True
        and exact37 and INDEPENDENT_ORACLE in enum_functions
        and admit007["rule_name"] == "distance_only_inference_forbidden"
        and admit007["consumed_candidate_fields"] == "covalent_event_evidence_source"
        and admit007["consumed_context_items"] == "allowed_covalent_evidence_classes"
        and admit007["passed_enum_members"] == "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES)
        and admit007["blocked_enum_members"] == "distance_only_inference"
        and admit007["passed_outcome"] == "passed" and admit007["blocked_outcome"] == "blocked"
        and admit007["blocked_reason"] == FORMAL_BLOCKED_REASON
        and admit007["invalid_outcome"] == "invalid"
        and admit006["blocked_reason"] == "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"
        and historical["admission_rule_name"] == "distance_only_inference_forbidden"
        and historical["blocking_reason"] == HISTORICAL_REGISTRY_REASON
        and route007["candidate_field_dependencies"] == "covalent_event_evidence_source"
        and route007["evaluation_context_dependencies"] == "allowed_covalent_evidence_classes"
        and route007["callable_discovered"] == "false" and route007["engine_registration_status"] == "unsupported"
        and {"outcome", "passed", "blocks_candidate", "reason"}.issubset(reason_fields)
        and len(runtime_issues.rows) == 11 and enum_issue["status"] == "resolved"
        and coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(7, 16))
        and coverage["status"] == "open" and aggregation["status"] == "open"
        and provider["status"] == "open" and provider["issue_count"] == "11"
        and runtime_manifest.get("registered_rule_ids") == [f"ADMIT_{index:03d}" for index in range(1, 7)]
        and runtime_manifest.get("admit_007_registered_in_engine") is False
        and runtime_manifest.get("admit_007_standalone_evaluator_implemented") is False
        and runtime_manifest.get("evaluate_all_rules_implemented") is False
        and "evaluate_admit_007" not in runtime_functions and "evaluate_all_rules" not in runtime_functions
        and "evaluate_admit_006" in admit006_functions
        and admit006_manifest.get("admit_006_standalone_evaluator_implemented") is True
        and admit006_manifest.get("admit_006_independent_semantic_oracle_attested") is True
    ):
        raise ValueError("committed predecessor semantics mismatch")
    return {
        "runtime_issue_rows": tuple(dict(row) for row in runtime_issues.rows),
        "runtime_issue_bytes": _record(snapshot, RUNTIME_ISSUE_PATH).content_bytes,
        "enum_truth_row_count": len(truth.rows),
    }


def _source_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "source_code"
    if "issue" in path.name:
        return "authoritative_issue_inventory"
    if path.suffix == ".json":
        return "manifest"
    if path in (ENUM_REGISTRY_PATH, RESPONSIBILITY_PATH, RULE_REGISTRY_PATH, RESULT_CONTRACT_PATH, ROUTING_CONTRACT_PATH):
        return "normative_contract"
    if path == ENUM_TRUTH_PATH:
        return "normative_truth_matrix"
    return "metadata"


def _boundary_necessity(path: Path) -> str:
    if path in (RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH):
        return "current_exact6_runtime_boundary"
    if path in (ENUM_SOURCE_PATH, ENUM_MANIFEST_PATH, ENUM_REGISTRY_PATH, ENUM_TRUTH_PATH, RESPONSIBILITY_PATH):
        return "current_normative_enum_reason_oracle_contract"
    if path == RULE_REGISTRY_PATH:
        return "historical_rule_identity_and_lowercase_reason_declaration"
    if path in (RESULT_CONTRACT_PATH, ROUTING_CONTRACT_PATH):
        return "unified_result_and_context_routing_contract"
    if path == ADMIT006_AUDIT_SOURCE_PATH:
        return "admit006_precondition_audit_structural_precedent"
    return "admit006_standalone_interface_shape_precedent"


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": _source_kind(record.relative_path),
        "boundary_necessity": _boundary_necessity(record.relative_path),
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "expected_sha256": record.expected_sha256,
        "base_tree_sha256": record.base_tree_sha256, "filesystem_sha256": record.filesystem_sha256,
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _csv_row_identity(text: str, line_number: int) -> str:
    lines = text.splitlines()
    if line_number <= 1 or line_number > len(lines):
        return f"line:{line_number}"
    header = next(csv.reader([lines[0]]), [])
    row = next(csv.reader([lines[line_number - 1]]), [])
    return f"{header[0]}={row[0]}" if header and row else f"line:{line_number}"


def _occurrence_statement(path: Path, term: str) -> str:
    if path == RULE_REGISTRY_PATH and term == HISTORICAL_REGISTRY_REASON:
        return "historical lowercase registry blocking-reason declaration; not a formal evaluator reason"
    if path in (RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH):
        return "current Exact6 runtime boundary keeps ADMIT_007 known but unregistered"
    if path in (ENUM_SOURCE_PATH, ENUM_MANIFEST_PATH, ENUM_REGISTRY_PATH, ENUM_TRUTH_PATH, RESPONSIBILITY_PATH):
        return "current normative enum validation reason outcome or independent-oracle contract"
    if path in (ADMIT006_SOURCE_PATH, ADMIT006_MANIFEST_PATH):
        return "ADMIT_006 standalone interface shape precedent; distinct rule responsibility"
    if path == ADMIT006_AUDIT_SOURCE_PATH:
        return "historical precondition-audit structure precedent"
    return "unified rule identity result or context-routing contract"


def _occurrence_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    concrete_terms = set(CANONICAL_ENUM_MEMBERS) | {FORMAL_BLOCKED_REASON, HISTORICAL_REGISTRY_REASON}
    authoritative = {
        RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH,
        ENUM_SOURCE_PATH, ENUM_MANIFEST_PATH, ENUM_REGISTRY_PATH, ENUM_TRUTH_PATH,
        RESPONSIBILITY_PATH, RULE_REGISTRY_PATH, RESULT_CONTRACT_PATH, ROUTING_CONTRACT_PATH,
    }
    for record in snapshot.records:
        text = record.content_bytes.decode("utf-8", errors="strict")
        for line_number, line in enumerate(text.splitlines(), 1):
            for term in MATCH_TERMS:
                if term not in line:
                    continue
                role = (
                    "candidate_scalar" if term == "covalent_event_evidence_source"
                    else "evaluation_context" if term == "allowed_covalent_evidence_classes"
                    else "independent_oracle" if term == INDEPENDENT_ORACLE
                    else "rule_identity" if term in ("ADMIT_007", "distance_only_inference_forbidden")
                    else "reason_contract" if term in (FORMAL_BLOCKED_REASON, HISTORICAL_REGISTRY_REASON)
                    else "evidence_enum_member"
                )
                rows.append({
                    "occurrence_order": str(len(rows) + 1),
                    "source_relative_path": record.relative_path.as_posix(),
                    "source_sha256": record.expected_sha256,
                    "source_kind": _source_kind(record.relative_path),
                    "symbol_or_row_id": _csv_row_identity(text, line_number) if record.relative_path.suffix == ".csv" else f"line:{line_number}",
                    "matched_term": term, "field_role": role,
                    "rule_scope": "ADMIT_006|ADMIT_007" if ("ADMIT_006" in line and "ADMIT_007" in line) else ("ADMIT_007" if "ADMIT_007" in line or term in (FORMAL_BLOCKED_REASON, HISTORICAL_REGISTRY_REASON) else "shared"),
                    "semantic_statement": _occurrence_statement(record.relative_path, term),
                    "contains_concrete_value": _bool(term in concrete_terms),
                    "concrete_value": term if term in concrete_terms else "",
                    "authoritative_for_runtime_semantics": _bool(record.relative_path in authoritative),
                    "occurrence_passed": "true",
                })
    if not rows or set(row["matched_term"] for row in rows) != set(MATCH_TERMS):
        raise ValueError("occurrence inventory term coverage incomplete")
    return tuple(rows)


def _observed_value_rows() -> tuple[dict[str, str], ...]:
    """The fixed committed boundary contains no real provider candidate values."""
    return ()


def _precondition_specs() -> tuple[tuple[str, str, str, str, str, bool, str, str], ...]:
    exact3 = "|".join(CANONICAL_ENUM_MEMBERS)
    exact2 = "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES)
    return (
        ("PRE_001", "candidate_field_name", "single scalar field covalent_event_evidence_source", "sole ADMIT_007 candidate dependency frozen", "responsibility:ADMIT_007", True, "", "frozen_or_implementable"),
        ("PRE_002", "standalone_input_projection", "direct scalar and context objects; missing key excluded", "None is scalar type-invalid; empty exact str is empty-invalid; adapter missing is separate", "enum source plus ADMIT_006 interface precedent", True, "", "frozen_or_implementable"),
        ("PRE_003", "scalar_exact_type", "exact built-in str before all later checks", "type -> nonempty -> ASCII -> syntax -> Exact3 membership", "enum design source", True, "", "frozen_or_implementable"),
        ("PRE_004", "null_empty_handling", "None type-invalid; exact empty str empty-invalid", "exact scalar reasons frozen; no standalone missing reason", "Exact37 truth", True, "", "frozen_or_implementable"),
        ("PRE_005", "canonicalization", "no trim case-fold alias normalization repair", "canonical value retained only after exact validation", "enum source and manifest", True, "", "frozen_or_implementable"),
        ("PRE_006", "allowed_enum", f"Exact3 ordered enum {exact3}", f"Exact3 ordered enum {exact3}", "enum registry", True, "", "frozen_or_implementable"),
        ("PRE_007", "unknown_enum_handling", "unknown syntactically valid value is invalid with exact UNKNOWN reason", SCALAR_REASONS[-1], "Exact37 truth", True, "", "frozen_or_implementable"),
        ("PRE_008", "explicit_vs_distance_only", "two explicit members passed; distance-only blocked", f"{exact2}=passed; distance_only_inference=blocked", "responsibility:ADMIT_007 and Exact37 truth", True, "", "frozen_or_implementable"),
        ("PRE_009", "admit006_admit007_boundary", "shared validation but distinct responsibility and blocked reason", "ADMIT_006=COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT; ADMIT_007=DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE", "responsibility matrix", True, "", "frozen_or_implementable"),
        ("PRE_010", "outcome_vocabulary", "exact outcomes passed|blocked|invalid", "explicit=passed; distance-only=blocked; scalar/context failure=invalid", "Exact37 truth and result contract", True, "", "frozen_or_implementable"),
        ("PRE_011", "reason_vocabulary", "Exact5 scalar + Exact2 context + uppercase ADMIT_007 blocked reason", "|".join((*SCALAR_REASONS, *CONTEXT_REASONS, FORMAL_BLOCKED_REASON)), "enum source truth and responsibility", True, "", "frozen_or_implementable"),
        ("PRE_012", "validated_canonical_mapping", "scalar invalid clears canonical/pair; context invalid retains canonical/pair", "passed/blocked retain canonical and validated pair; context-invalid retains them", "Exact37 truth plus ADMIT_006 result precedent", True, "", "frozen_or_implementable"),
        ("PRE_013", "runtime_context_dependency", f"exact built-in tuple in order {exact2}", "scalar failure precedes context failure; content mismatch fail-closed", "enum source and Exact37 truth", True, "", "frozen_or_implementable"),
        ("PRE_014", "independent_semantic_oracle", INDEPENDENT_ORACLE, "AST-visible oracle returns admit_007 outcome; audit parses but never executes it", "enum design source", True, "", "frozen_or_implementable"),
        ("PRE_015", "standalone_evaluator_safety", "implementable without semantic guessing and production must not call oracle", "all scalar/context/outcome/reason/state semantics frozen", "PRE_001 through PRE_014", True, "", "frozen_or_implementable"),
        ("PRE_016", "real_provider_values", "real provider mapping validation deferred", "zero committed real provider candidate values; normative enum frozen", "header-only observed inventory", False, "", "future_provider_validation_not_required_for_interface"),
        ("PRE_017", "real_candidate_authorization", "real candidate evaluation requires separate authorization", "current scope is synthetic metadata-only audit", "task authorization boundary", False, "", "blocked_by_current_scope"),
        ("PRE_018", "bulk_download_readiness", "all rules and aggregation required", "ADMIT_007 through ADMIT_015 coverage remains open", "current Exact11 issue inventory", False, "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "blocked"),
        ("PRE_019", "training_readiness", "feature-semantics audit required before training", "Step12D smoke legality is not final training-feature contract", "repository training prerequisite", False, "FEATURE_SEMANTICS_AUDIT_REQUIRED", "blocked"),
    )


def _precondition_rows() -> tuple[dict[str, str], ...]:
    specs = _precondition_specs()
    if len(specs) != 19 or tuple(row[0] for row in specs) != tuple(f"PRE_{index:03d}" for index in range(1, 20)):
        raise ValueError("Exact19 precondition shape invalid")
    return tuple({
        "precondition_id": item[0], "semantic_area": item[1],
        "required_contract": item[2], "observed_contract": item[3],
        "source_evidence": item[4], "semantics_complete": _bool(item[5]),
        "blocker_id": item[6], "implementation_disposition": item[7],
        "precondition_passed": "true",
    } for item in specs)


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV row schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest(
    *, snapshot: FrozenSourceSnapshot, occurrence_count: int,
    output_sha256: Mapping[str, str],
) -> dict[str, Any]:
    readiness = {key: True for key in TRUE_READINESS}
    readiness.update({key: False for key in FALSE_READINESS})
    manifest: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_007",
        "admission_rule_name": "distance_only_inference_forbidden",
        "candidate_scalar_field": "covalent_event_evidence_source",
        "evaluation_context_item": "allowed_covalent_evidence_classes",
        "future_standalone_evaluator": "evaluate_admit_007",
        "future_result_type": "Admit007EvaluationResult",
        "historical_registry_blocking_reason": HISTORICAL_REGISTRY_REASON,
        "formal_evaluator_blocked_reason": FORMAL_BLOCKED_REASON,
        "canonical_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "allowed_covalent_evidence_classes": list(ALLOWED_COVALENT_EVIDENCE_CLASSES),
        "scalar_validation_precedence": ["exact_builtin_str", "nonempty", "ASCII", "syntax_[a-z][a-z0-9_]{0,63}", "Exact3_membership"],
        "scalar_reasons": list(SCALAR_REASONS), "context_reasons": list(CONTEXT_REASONS),
        "final_validation_precedence": ["scalar_failure", "context_failure", "canonical_member_classification"],
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "explicit_member_outcome": "passed", "distance_only_outcome": "blocked",
        "invalid_input_outcome": "invalid", "standalone_missing_reason_included": False,
        "independent_semantic_oracle": INDEPENDENT_ORACLE,
        "independent_oracle_called_by_audit_production": False,
        "future_production_evaluator_may_call_oracle": False,
        "source_boundary_count": len(snapshot.records),
        "source_paths": [record.relative_path.as_posix() for record in snapshot.records],
        "source_sha256": {record.relative_path.as_posix(): record.expected_sha256 for record in snapshot.records},
        "source_boundary_all_passed": True,
        "precondition_row_count": 19, "precondition_passed_count": 19,
        "semantics_complete_precondition_count": 15,
        "field_occurrence_row_count": occurrence_count,
        "observed_evidence_value_row_count": 0,
        "real_provider_values_observed": False,
        "normative_contract_frozen_but_real_provider_mapping_unvalidated": True,
        "issue_row_count": 11, "issue_inventory_byte_identical_to_authoritative_predecessor": True,
        "issue_inventory_sha256": SOURCE_SHA256[RUNTIME_ISSUE_PATH],
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "raw_checkpoint_provider_network_accessed": False,
        "readiness": readiness, **readiness,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": True,
    }
    return manifest


def build_audit_state(repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    predecessor = _validate_predecessors(snapshot)
    return {
        "snapshot": snapshot,
        "source_rows": _source_boundary_rows(snapshot),
        "occurrence_rows": _occurrence_rows(snapshot),
        "value_rows": _observed_value_rows(),
        "precondition_rows": _precondition_rows(),
        "issue_rows": predecessor["runtime_issue_rows"],
        "issue_bytes": predecessor["runtime_issue_bytes"],
    }


def _prepare_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
    else:
        root.mkdir(parents=True)
    allowed = set(OUTPUT_FILES)
    for entry in root.iterdir():
        if entry.name not in allowed:
            raise ValueError(f"unexpected output entry: {entry.name}")
        metadata = os.lstat(entry)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"unsafe output entry: {entry.name}")


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path = REPO_ROOT / DEFAULT_OUTPUT_ROOT,
    *, repo_root: Path = REPO_ROOT, head_ref: str = "HEAD",
) -> dict[str, Any]:
    root = Path(output_root)
    _prepare_output_root(root)
    state = build_audit_state(repo_root, head_ref=head_ref)
    payloads = {
        PRECONDITION_FILENAME: _csv_bytes(PRECONDITION_COLUMNS, state["precondition_rows"]),
        OCCURRENCE_FILENAME: _csv_bytes(OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        VALUE_FILENAME: _csv_bytes(VALUE_COLUMNS, state["value_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    for name in CSV_OUTPUTS:
        _atomic_write(root / name, payloads[name])
    hashes = {name: hashlib.sha256(payloads[name]).hexdigest() for name in CSV_OUTPUTS}
    manifest = _manifest(
        snapshot=state["snapshot"], occurrence_count=len(state["occurrence_rows"]),
        output_sha256=hashes,
    )
    _atomic_write(root / MANIFEST_FILENAME, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return {**state, "manifest": manifest}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1()

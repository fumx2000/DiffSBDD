"""Normative V1 covalent-event evidence-source enum contract design gate.

This module freezes design semantics and materializes metadata evidence only.  It
does not implement an admission evaluator, adapter, registry entry, provider, or
candidate evaluation.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "covalent event evidence source enum contract design gate v1"
STAGE = "covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "adcffee211ae07a3d26b363ce1318b0ae515737d"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_006 evaluator preconditions audit v1"
MANIFEST_SCHEMA_VERSION = "covapie_covalent_event_evidence_source_enum_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_006_standalone_evaluator_interface_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

AUDIT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit.py",
    str(AUDIT_ROOT / "covapie_admit_006_formal_evaluator_preconditions_manifest.json"),
    str(AUDIT_ROOT / "covapie_admit_006_evaluator_precondition_matrix.csv"),
    str(AUDIT_ROOT / "covapie_admit_006_field_occurrence_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_006_observed_evidence_value_inventory.csv"),
    str(AUDIT_ROOT / "covapie_admit_006_issue_readiness_inventory.csv"),
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(PRECONDITION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(PRECONDITION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "fabac801a86d3b5e31298e3ad29e2e51d72a3cef46cfb28e5a25a5c3c8d6f3d3",
    "16b787061739dd0d68cfd3f66829a7690e802d1c0fa700d53155384b29c6dac5",
    "34073fad616472a9a8044cd21f498f33d535251e92b1ce7b549c1ad5dbf018ed",
    "bf7a705ffecb0dde8d7b62e6e6c15756614de358401d7055defb82711ce20660",
    "44698a4796be10cc317931df31da4829bccb23eaa95ed23d9797537f5a5feacc",
    "7f815f3358ae3e53d296bc3ec0a129cd459184a76aa5169649b73fb1440e28bc",
    "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "c923d0dfe2edad534a2f530dbbac53870823ff2aa231730acbcd63577edfdb23",
), strict=True))

AUDIT_MANIFEST_PATH = SOURCE_PATHS[1]
OBSERVED_VALUE_PATH = SOURCE_PATHS[4]
AUDIT_ISSUE_PATH = SOURCE_PATHS[5]
SCHEMA_PATH = SOURCE_PATHS[7]
RULE_REGISTRY_PATH = SOURCE_PATHS[8]
FIELD_PATH = SOURCE_PATHS[9]
CONTEXT_PATH = SOURCE_PATHS[10]
RUNTIME_SOURCE_PATH = SOURCE_PATHS[11]

CANONICAL_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
ALLOWED_COVALENT_EVIDENCE_CLASSES = CANONICAL_ENUM_MEMBERS[:2]
CANONICAL_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
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

SOURCE_BOUNDARY_FILENAME = "covapie_covalent_event_evidence_source_enum_source_boundary_audit.csv"
ENUM_REGISTRY_FILENAME = "covapie_covalent_event_evidence_source_enum_registry.csv"
TRUTH_MATRIX_FILENAME = "covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv"
RESPONSIBILITY_FILENAME = "covapie_admit_006_admit_007_evidence_responsibility_matrix.csv"
ISSUE_FILENAME = "covapie_covalent_event_evidence_source_enum_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_event_evidence_source_enum_contract_manifest.json"
CSV_OUTPUTS = (
    SOURCE_BOUNDARY_FILENAME, ENUM_REGISTRY_FILENAME, TRUTH_MATRIX_FILENAME,
    RESPONSIBILITY_FILENAME, ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ENUM_REGISTRY_COLUMNS = (
    "enum_order", "canonical_value", "semantic_definition", "normative_contract_member",
    "observed_in_committed_metadata", "explicit_covalent_evidence", "distance_only",
    "allowed_by_admit_006", "allowed_by_admit_007",
    "included_in_allowed_covalent_evidence_classes", "alias_allowed", "v1_enum_row_passed",
)
TRUTH_MATRIX_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "expected_scalar_classification", "expected_canonical_value",
    "expected_scalar_reason", "expected_context_valid", "expected_context_reason",
    "expected_admit_006_outcome", "expected_admit_006_reason",
    "expected_admit_007_outcome", "expected_admit_007_reason",
    "normative_not_observed", "case_passed",
)
RESPONSIBILITY_COLUMNS = (
    "responsibility_order", "contract_subject", "rule_id", "rule_name",
    "consumed_candidate_fields", "consumed_context_items", "passed_enum_members",
    "blocked_enum_members", "invalid_input_classes", "passed_outcome", "blocked_outcome",
    "blocked_reason", "invalid_outcome", "responsibility_boundary", "responsibility_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "covalent_event_evidence_source_enum_contract_design_completed",
    "covalent_event_evidence_source_candidate_semantics_frozen",
    "covalent_event_evidence_source_enum_frozen",
    "allowed_covalent_evidence_classes_context_contract_frozen",
    "admit_006_admit_007_responsibility_boundary_frozen",
    "admit_006_reason_outcome_contract_frozen",
    "admit_007_reason_outcome_contract_frozen",
    "covalent_event_evidence_source_scalar_validation_contract_frozen",
    "covalent_event_evidence_source_design_oracle_available",
    "ready_for_admit_006_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "normative_enum_values_observed_in_real_provider_metadata",
    "real_provider_enum_mapping_validated",
    "admit_006_standalone_evaluator_implemented",
    "admit_006_unified_adapter_contract_frozen",
    "admit_006_unified_adapter_implemented",
    "admit_006_registered_in_engine",
    "admit_007_standalone_evaluator_implemented",
    "admit_007_unified_adapter_contract_frozen",
    "admit_007_unified_adapter_implemented",
    "admit_007_registered_in_engine",
    "admit_006_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
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


@dataclass(frozen=True)
class ScalarValidationDesign:
    classification: str
    canonical_value: str
    reason: str


@dataclass(frozen=True)
class ContextValidationDesign:
    valid: bool
    reason: str


@dataclass(frozen=True)
class RuleOutcomeDesign:
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str


@dataclass(frozen=True)
class EvidenceClassificationDesign:
    scalar: ScalarValidationDesign
    context: ContextValidationDesign
    admit_006: RuleOutcomeDesign
    admit_007: RuleOutcomeDesign


class _StringSubclass(str):
    """Synthetic truth-only exact-type negative."""


def _bool(value: bool) -> str:
    return "true" if value else "false"


def validate_covalent_event_evidence_source_design(value: object) -> ScalarValidationDesign:
    """Apply exact-type, nonempty, ASCII, syntax, then membership precedence."""
    if type(value) is not str:
        return ScalarValidationDesign("invalid", "", SCALAR_REASONS[0])
    if not value:
        return ScalarValidationDesign("invalid", "", SCALAR_REASONS[1])
    if not value.isascii():
        return ScalarValidationDesign("invalid", "", SCALAR_REASONS[2])
    if re.fullmatch(CANONICAL_SYNTAX, value, flags=re.ASCII) is None:
        return ScalarValidationDesign("invalid", "", SCALAR_REASONS[3])
    if value not in CANONICAL_ENUM_MEMBERS:
        return ScalarValidationDesign("unknown", "", SCALAR_REASONS[4])
    return ScalarValidationDesign("canonical", value, "")


def validate_allowed_covalent_evidence_classes_design(value: object) -> ContextValidationDesign:
    """Require the immutable V1 exact tuple, including member exact types and order."""
    if type(value) is not tuple:
        return ContextValidationDesign(False, CONTEXT_REASONS[0])
    if any(type(member) is not str for member in value) or value != ALLOWED_COVALENT_EVIDENCE_CLASSES:
        return ContextValidationDesign(False, CONTEXT_REASONS[1])
    return ContextValidationDesign(True, "")


def classify_admit_006_admit_007_evidence_design(
    scalar_value: object,
    allowed_classes: object = ALLOWED_COVALENT_EVIDENCE_CLASSES,
) -> EvidenceClassificationDesign:
    """Independent semantic oracle; future production evaluators must not call it."""
    scalar = validate_covalent_event_evidence_source_design(scalar_value)
    context = validate_allowed_covalent_evidence_classes_design(allowed_classes)
    if scalar.classification != "canonical":
        invalid = RuleOutcomeDesign("invalid", False, True, scalar.reason)
        return EvidenceClassificationDesign(scalar, context, invalid, invalid)
    if not context.valid:
        invalid = RuleOutcomeDesign("invalid", False, True, context.reason)
        return EvidenceClassificationDesign(scalar, context, invalid, invalid)
    if scalar.canonical_value == "distance_only_inference":
        return EvidenceClassificationDesign(
            scalar,
            context,
            RuleOutcomeDesign("blocked", False, True, "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"),
            RuleOutcomeDesign("blocked", False, True, "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"),
        )
    passed = RuleOutcomeDesign("passed", True, False, "")
    return EvidenceClassificationDesign(scalar, context, passed, passed)


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


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
    """Metadata-only check: deliberately does not read source content bytes."""
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
    """Complete all Exact12 structural checks before the first explicit byte read."""
    if len(SOURCE_PATHS) != 12 or len(set(SOURCE_PATHS)) != 12 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact12 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural_results = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural_results):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base_read = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base_read.returncode != 0 or type(base_read.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base_read.stdout).hexdigest()
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
        type(value) is FrozenSourceSnapshot and len(value.records) == 12
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
    matches = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"), newline=""))
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
    return ast.parse(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"), filename=path.as_posix())


def _row(document: CsvDocument, key: str, value: str) -> dict[str, str]:
    matches = tuple(row for row in document.rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets):
            continue
        value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
        if isinstance(value, ast.Dict):
            keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant) and type(key.value) is str)
            if len(keys) == len(value.keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    audit_manifest = _json_document(snapshot, AUDIT_MANIFEST_PATH)
    observed = _csv_document(snapshot, OBSERVED_VALUE_PATH)
    issues = _csv_document(snapshot, AUDIT_ISSUE_PATH)
    schema = _csv_document(snapshot, SCHEMA_PATH)
    registry = _csv_document(snapshot, RULE_REGISTRY_PATH)
    fields = _csv_document(snapshot, FIELD_PATH)
    contexts = _csv_document(snapshot, CONTEXT_PATH)
    runtime_tree = _ast_document(snapshot, RUNTIME_SOURCE_PATH)
    field = _row(schema, "admission_field_name", "covalent_event_evidence_source")
    admit006 = _row(registry, "admission_rule_id", "ADMIT_006")
    admit007 = _row(registry, "admission_rule_id", "ADMIT_007")
    field_semantics = _row(fields, "field_name", "covalent_event_evidence_source")
    context = _row(contexts, "context_item", "allowed_covalent_evidence_classes")
    blocker = _row(issues, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    functions = {node.name for node in runtime_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    exact5 = tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    if not (
        observed.header and observed.rows == ()
        and audit_manifest.get("observed_evidence_value_row_count") == 0
        and audit_manifest.get("canonical_evidence_enum_exists") is False
        and audit_manifest.get("ready_for_covapie_covalent_event_evidence_source_enum_contract_design") is True
        and audit_manifest.get("ready_for_admit_006_standalone_evaluator_interface_implementation") is False
        and len(issues.rows) == 11 and blocker["status"] == "open"
        and blocker["affected_fields"] == "covalent_event_evidence_source"
        and blocker["affected_rules"] == "ADMIT_006|ADMIT_007"
        and field["value_contract"] == "explicit non-distance-only evidence source"
        and admit006["admission_rule_name"] == "explicit_covalent_event_evidence"
        and admit006["blocking_reason"] == "covalent_event_evidence_missing"
        and admit007["admission_rule_name"] == "distance_only_inference_forbidden"
        and admit007["blocking_reason"] == "distance_only_inference_not_admissible"
        and field_semantics["dependent_rules"] == "ADMIT_006|ADMIT_007"
        and field_semantics["allowed_values_defined"] == "false"
        and context["required_by_rules"] == "ADMIT_006|ADMIT_007"
        and context["exact_contract_defined"] == "false"
        and _registry_keys(runtime_tree) == exact5
        and "evaluate_admit_006" not in functions and "evaluate_admit_007" not in functions
        and "evaluate_all_rules" not in functions
    ):
        raise ValueError("predecessor contract validation failed")
    return {"issue_rows": issues.rows, "runtime_registry": exact5}


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": record.relative_path.suffix.lstrip(".") or "source",
        "boundary_necessity": "normative predecessor evidence",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "expected_sha256": record.expected_sha256,
        "base_tree_sha256": record.base_tree_sha256, "filesystem_sha256": record.filesystem_sha256,
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _enum_registry_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        "upstream structured source explicitly encodes a covalent bond, link, or bond record; not distance-only",
        "trusted curated annotation explicitly declares a covalent event linked to the candidate ligand/residue; not distance-only",
        "covalent-event judgment comes only from geometric distance or proximity without an explicit bond record or curated annotation",
    )
    rows = []
    for index, (value, definition) in enumerate(zip(CANONICAL_ENUM_MEMBERS, definitions, strict=True), 1):
        explicit = index < 3
        rows.append({
            "enum_order": str(index), "canonical_value": value, "semantic_definition": definition,
            "normative_contract_member": "true", "observed_in_committed_metadata": "false",
            "explicit_covalent_evidence": _bool(explicit), "distance_only": _bool(not explicit),
            "allowed_by_admit_006": _bool(explicit), "allowed_by_admit_007": _bool(explicit),
            "included_in_allowed_covalent_evidence_classes": _bool(explicit),
            "alias_allowed": "false", "v1_enum_row_passed": "true",
        })
    return tuple(rows)


def _display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _truth_definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = ALLOWED_COVALENT_EVIDENCE_CLASSES
    scalar_cases: tuple[tuple[str, str, object], ...] = (
        ("canonical_structure_bond", "canonical", CANONICAL_ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", "canonical", CANONICAL_ENUM_MEMBERS[1]),
        ("canonical_distance_only", "canonical", CANONICAL_ENUM_MEMBERS[2]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True), ("type_str_subclass", "scalar_type", _StringSubclass(CANONICAL_ENUM_MEMBERS[0])),
        ("type_list", "scalar_type", [CANONICAL_ENUM_MEMBERS[0]]),
        ("type_mapping", "scalar_type", {"value": CANONICAL_ENUM_MEMBERS[0]}),
        ("empty", "empty_syntax", ""), ("whitespace_only", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " explicit_structure_bond_record"),
        ("trailing_whitespace", "empty_syntax", "explicit_structure_bond_record "),
        ("uppercase", "empty_syntax", "Explicit_structure_bond_record"),
        ("hyphen", "empty_syntax", "explicit-structure-bond-record"),
        ("dot", "empty_syntax", "explicit.structure"), ("slash", "empty_syntax", "explicit/structure"),
        ("non_ascii", "empty_syntax", "explicit_évidence"),
        ("over_length", "empty_syntax", "a" * 65), ("leading_digit", "empty_syntax", "1explicit"),
        ("unknown_valid", "unknown", "unregistered_value"),
        ("unknown_explicit_looking", "unknown", "explicit_database_bond"),
        ("unknown_manual_review", "unknown", "manual_review"),
        ("unknown_other", "unknown", "other"), ("unknown_unknown", "unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact), ("context_none", None), ("context_list", list(exact)),
        ("context_set", set(exact)), ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))), ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    definitions = [(case_id, group, scalar, "exact_tuple", exact) for case_id, group, scalar in scalar_cases]
    definitions.extend((case_id, "context", CANONICAL_ENUM_MEMBERS[0], case_id.removeprefix("context_"), context) for case_id, context in context_cases)
    return tuple(definitions)


def _truth_matrix_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (case_id, group, scalar, context_kind, context) in enumerate(_truth_definitions(), 1):
        result = classify_admit_006_admit_007_evidence_design(scalar, context)
        rows.append({
            "case_id": f"CASE_{index:03d}_{case_id}", "case_group": group,
            "scalar_input_kind": type(scalar).__name__, "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind,
            "expected_scalar_classification": result.scalar.classification,
            "expected_canonical_value": result.scalar.canonical_value,
            "expected_scalar_reason": result.scalar.reason,
            "expected_context_valid": _bool(result.context.valid),
            "expected_context_reason": result.context.reason,
            "expected_admit_006_outcome": result.admit_006.outcome,
            "expected_admit_006_reason": result.admit_006.reason,
            "expected_admit_007_outcome": result.admit_007.outcome,
            "expected_admit_007_reason": result.admit_007.reason,
            "normative_not_observed": "true", "case_passed": "true",
        })
    assert len(rows) == len(_truth_definitions()) == 37
    return tuple(rows)


def _responsibility_rows() -> tuple[dict[str, str], ...]:
    common = {
        "consumed_candidate_fields": "covalent_event_evidence_source",
        "consumed_context_items": "allowed_covalent_evidence_classes",
        "invalid_input_classes": "scalar_malformed|scalar_unknown|context_invalid",
        "passed_outcome": "passed", "blocked_outcome": "blocked", "invalid_outcome": "invalid",
        "responsibility_passed": "true",
    }
    return (
        {**common, "responsibility_order": "1", "contract_subject": "shared_enum_validator",
         "rule_id": "SHARED", "rule_name": "covalent_event_evidence_source_v1_validation",
         "passed_enum_members": "|".join(CANONICAL_ENUM_MEMBERS), "blocked_enum_members": "",
         "blocked_reason": "", "responsibility_boundary": "shared scalar exact-type/syntax/membership and fixed-context validation only"},
        {**common, "responsibility_order": "2", "contract_subject": "positive_explicit_evidence_permission",
         "rule_id": "ADMIT_006", "rule_name": "explicit_covalent_event_evidence",
         "passed_enum_members": "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES),
         "blocked_enum_members": CANONICAL_ENUM_MEMBERS[2],
         "blocked_reason": "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT",
         "responsibility_boundary": "positive permission requires a V1 allowed explicit evidence category; historical missing reason maps later in adapter"},
        {**common, "responsibility_order": "3", "contract_subject": "negative_distance_only_prohibition",
         "rule_id": "ADMIT_007", "rule_name": "distance_only_inference_forbidden",
         "passed_enum_members": "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES),
         "blocked_enum_members": CANONICAL_ENUM_MEMBERS[2],
         "blocked_reason": "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE",
         "responsibility_boundary": "negative prohibition blocks known distance-only inference; cross-rule aggregation is not frozen"},
    )


def _issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> tuple[dict[str, str], ...]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [row for row in rows if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("Exact11 issue baseline invalid")
    matches[0]["status"] = "resolved"
    matches[0]["integration_transition"] = "covalent_event_evidence_source_enum_contract_frozen_v1"
    return tuple(rows)


def _validate_rows(state: Mapping[str, Any]) -> None:
    if not (
        len(state["source_boundary_rows"]) == 12
        and len(state["enum_registry_rows"]) == 3
        and len(state["truth_matrix_rows"]) == 37
        and len(state["responsibility_rows"]) == 3
        and len(state["issue_rows"]) == 11
        and all(row["v1_enum_row_passed"] == "true" for row in state["enum_registry_rows"])
        and all(row["case_passed"] == "true" for row in state["truth_matrix_rows"])
        and all(row["responsibility_passed"] == "true" for row in state["responsibility_rows"])
        and sum(row["status"] == "open" for row in state["issue_rows"]) == 10
    ):
        raise ValueError("design row validation failed")


def build_design_state(snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    if not validate_frozen_source_snapshot(frozen):
        raise ValueError("invalid frozen snapshot")
    predecessor = _validate_predecessors(frozen)
    state = {
        "source_boundary_rows": _source_boundary_rows(frozen),
        "enum_registry_rows": _enum_registry_rows(),
        "truth_matrix_rows": _truth_matrix_rows(),
        "responsibility_rows": _responsibility_rows(),
        "issue_rows": _issue_rows(predecessor["issue_rows"]),
    }
    _validate_rows(state)
    return state


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    group_counts = {group: sum(row["case_group"] == group for row in state["truth_matrix_rows"])
                    for group in ("canonical", "scalar_type", "empty_syntax", "unknown", "context")}
    readiness = {key: True for key in TRUE_READINESS}
    readiness.update({key: False for key in FALSE_READINESS})
    payload: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_boundary_name": "fixed_exact12_committed_source_boundary",
        "source_input_count": 12, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "normative_enum_member_count": 3, "normative_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "observed_evidence_value_count": 0, "observed_evidence_values": [],
        "normative_enum_values_are_not_observed_values": True,
        "manual_review_member_included": False, "catch_all_member_included": False,
        "alias_support": False, "scalar_normalization_applied": False,
        "scalar_validation_precedence": ["exact_type", "nonempty", "ascii", "syntax", "membership"],
        "scalar_canonical_syntax": CANONICAL_SYNTAX,
        "allowed_covalent_evidence_classes": list(ALLOWED_COVALENT_EVIDENCE_CLASSES),
        "allowed_covalent_evidence_classes_runtime_type": "exact_tuple",
        "truth_matrix_row_count": len(state["truth_matrix_rows"]), "truth_matrix_group_counts": group_counts,
        "responsibility_matrix_row_count": len(state["responsibility_rows"]),
        "issue_row_count": 11, "active_open_issue_count": 10,
        "enum_issue_id": "COVALENT_EVIDENCE_ENUM_UNRESOLVED", "enum_issue_status": "resolved",
        "enum_issue_resolved": True, "current_registered_rule_count": 5,
        "registered_rule_ids": [f"ADMIT_{index:03d}" for index in range(1, 6)],
        "admit_006_registered": False, "admit_007_registered": False,
        "historical_admit_006_design_blocking_reason": "covalent_event_evidence_missing",
        "historical_missing_reason_future_mapping_scope": "future adapter missing-field and missing-value paths",
        "distance_only_is_not_missing": True,
        "cross_rule_aggregation_contract_frozen": False,
        "readiness": readiness, **readiness,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "safety_executed": [
            "exact12_source_verification", "predecessor_audit_validation", "normative_enum_design",
            "scalar_contract_design", "context_contract_design", "admit_006_admit_007_responsibility_design",
            "synthetic_truth_construction", "enum_issue_status_transition", "readiness_derivation",
        ],
        "safety_not_executed": [
            "observed_value_creation", "real_provider_mapping", "raw_read", "artifact_dereference",
            "provider_parser_execution", "network_download", "candidate_materialization",
            "real_candidate_evaluation", "exact11_real_evaluation", "admit_006_evaluator_implementation",
            "admit_007_evaluator_implementation", "adapter_implementation", "registry_modification",
            "evaluate_all_rules", "combined_verdict", "cross_rule_aggregation", "checkpoint",
            "torch_numpy_rdkit", "model_forward_loss_training",
        ],
        "all_checks_passed": True,
    }
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    payloads = {
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_boundary_rows"]),
        ENUM_REGISTRY_FILENAME: _csv_bytes(ENUM_REGISTRY_COLUMNS, state["enum_registry_rows"]),
        TRUTH_MATRIX_FILENAME: _csv_bytes(TRUTH_MATRIX_COLUMNS, state["truth_matrix_rows"]),
        RESPONSIBILITY_FILENAME: _csv_bytes(RESPONSIBILITY_COLUMNS, state["responsibility_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return payloads, manifest


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
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


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
    else:
        root.mkdir(parents=True, exist_ok=False)
    expected = set(OUTPUT_FILES)
    for entry in root.iterdir():
        metadata = os.lstat(entry)
        if entry.name not in expected:
            raise ValueError(f"unexpected output entry: {entry.name}")
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"unsafe output entry: {entry.name}")


def run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    state = build_design_state()
    payloads, manifest = _payloads(state)
    for name in OUTPUT_FILES:
        _atomic_write(root / name, payloads[name])
    return {"manifest": manifest, "output_root": root, "state": state}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1()

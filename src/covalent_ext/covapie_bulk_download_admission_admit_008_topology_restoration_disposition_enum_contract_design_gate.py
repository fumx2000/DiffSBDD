"""Read-only ADMIT_008 topology-restoration disposition enum design gate v1.

This module freezes a standalone direct-scalar contract and an independent
design oracle.  It is not the production evaluator, adapter, or Exact8 runtime.
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
STEP = "ADMIT_008 topology restoration disposition enum contract design gate v1"
STAGE = "covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1"
EXPECTED_BASE_COMMIT = "6c8e563c529a2f60d5ca7a63bdd92ea901ca6d59"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 evaluator preconditions audit v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_008_standalone_evaluator_interface_v1"
PRIMARY_ISSUE = "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

AUDIT_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1")
RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
PRECONDITION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
STEP13M_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0")
STEP13N_ROOT = Path("data/derived/covalent_small/real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit.py",
    str(AUDIT_ROOT / "covapie_admit_008_formal_evaluator_preconditions_manifest.json"),
    str(AUDIT_ROOT / "covapie_admit_008_evaluator_precondition_matrix.csv"),
    str(AUDIT_ROOT / "covapie_admit_008_disposition_vocabulary_inventory.csv"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_007_runtime_manifest.json"),
    str(AUDIT_ROOT / "covapie_admit_008_issue_readiness_inventory.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(PRECONDITION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(PRECONDITION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(STEP13M_ROOT / "covalent_restoration_rule_registry_contract.csv"),
    str(STEP13M_ROOT / "ligand_topology_restoration_candidate_contract.csv"),
    str(STEP13M_ROOT / "ligand_topology_restoration_policy_design_gate_manifest.json"),
    str(STEP13N_ROOT / "ligand_topology_policy_review_decision_contract.csv"),
    str(STEP13N_ROOT / "ligand_topology_policy_review_gate_manifest.json"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "b621b143a0475f69db92a709d2612527595e2fe2fa6cc51fa51db20acfc2c2ac",
    "e93c43df4f64b6ce70c19c526546d3b1090c55f9150a944a76109ed0038cc136",
    "8d9f0dca15b8c851787f3808498f811f72f73f07caa70f4a51b5c88aaf314455",
    "45407488815876ebf2029027dcb42d65e3eeb18f53ece0b9f1454be10887ff71",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "61e00e08ca5d32b2508f0bec3e296bef0edd79fad220e4014a1ac32f5c86f92c",
    "7d506c058e5d4dc49b0c6397db1bb35d11520d157ef1805971acf44283a22751",
    "c104908df85b3a026e5aa83d72483d5698b25b5ed94f35c11b6d15cb4c5c57fc",
    "5b5bb3d4dec353c8dbeb4fce7aa840846464721d9fbd960835c052eaa4ed8a6a",
    "c1e24b4e583fa10c5338a6a9907b0fd683b51b34c8e26aaa5275ad5afb899bb9",
), strict=True))

(
    AUDIT_SOURCE_PATH, AUDIT_MANIFEST_PATH, AUDIT_MATRIX_PATH, AUDIT_VOCABULARY_PATH,
    RUNTIME_MANIFEST_PATH, AUDIT_ISSUE_PATH, RULE_REGISTRY_PATH, SCHEMA_PATH,
    FIELD_PATH, EXECUTABILITY_PATH, RESTORATION_RULE_PATH, CANDIDATE_PATH,
    STEP13M_MANIFEST_PATH, REVIEW_DECISION_PATH, STEP13N_MANIFEST_PATH,
) = SOURCE_PATHS

CANONICAL_ENUM_MEMBERS = (
    "approved_restoration_template",
    "explicit_manual_review_approved",
    "manual_review_required",
    "quarantine_required",
)
ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS = CANONICAL_ENUM_MEMBERS[:2]
CANONICAL_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
SCALAR_REASONS = (
    "TOPOLOGY_RESTORATION_DISPOSITION_TYPE_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_EMPTY",
    "TOPOLOGY_RESTORATION_DISPOSITION_NON_ASCII",
    "TOPOLOGY_RESTORATION_DISPOSITION_SYNTAX_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_UNKNOWN",
)
CONTEXT_REASONS = (
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_TYPE_INVALID",
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_CONTENT_INVALID",
)
BLOCKED_REASONS = {
    "manual_review_required": "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED",
    "quarantine_required": "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED",
}
CANDIDATE_FIELDS = ("topology_restoration_disposition",)
CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)

SOURCE_BOUNDARY_FILENAME = "covapie_admit_008_topology_restoration_disposition_source_boundary_audit.csv"
ENUM_REGISTRY_FILENAME = "covapie_admit_008_topology_restoration_disposition_enum_registry.csv"
TRUTH_MATRIX_FILENAME = "covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv"
CATEGORY_MAPPING_FILENAME = "covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv"
ISSUE_FILENAME = "covapie_admit_008_topology_restoration_disposition_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json"
CSV_OUTPUTS = (ENUM_REGISTRY_FILENAME, TRUTH_MATRIX_FILENAME, CATEGORY_MAPPING_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ENUM_REGISTRY_COLUMNS = (
    "enum_order", "canonical_value", "semantic_definition", "normative_contract_member",
    "passed_by_admit_008", "blocked_by_admit_008", "formal_reason",
    "included_in_allowed_context", "provider_mapping_required", "alias_allowed", "v1_enum_row_passed",
)
TRUTH_MATRIX_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display", "context_input_kind",
    "expected_scalar_classification", "expected_canonical_value", "expected_scalar_reason",
    "expected_context_valid", "expected_context_reason", "expected_outcome", "expected_passed",
    "expected_blocks_candidate", "expected_reason", "expected_validated_candidate_fields",
    "scalar_failure_precedence", "case_passed",
)
CATEGORY_MAPPING_COLUMNS = (
    "mapping_order", "mapping_case_id", "policy_evidence", "expected_canonical_disposition",
    "expected_outcome", "expected_reason", "mapping_precedence",
    "real_provider_mapping_executed", "mapping_contract_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_008_topology_disposition_enum_contract_frozen",
    "admit_008_scalar_exact_type_contract_available",
    "admit_008_null_empty_standalone_contract_available",
    "admit_008_canonicalization_contract_available",
    "admit_008_category_mapping_contract_available",
    "admit_008_provenance_mapping_boundary_frozen",
    "admit_008_reason_outcome_contract_available",
    "admit_008_canonical_state_contract_available",
    "admit_008_context_contract_available",
    "admit_008_independent_semantic_oracle_available",
    "admit_008_standalone_evaluator_preconditions_complete",
    "ready_for_admit_008_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
    "admit_008_standalone_evaluator_implemented", "admit_008_unified_adapter_contract_frozen",
    "admit_008_unified_adapter_implemented", "admit_008_registered_in_engine",
    "exact7_runtime_modified", "admit_009_standalone_evaluator_implemented",
    "admit_009_to_015_registered_in_engine", "all_15_rules_covered",
    "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen",
    "real_candidate_evaluation", "exact11_real_rows_evaluated", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
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
class ScalarClassificationDesign:
    classification: str
    canonical_value: str
    reason: str
    validated_candidate_fields: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ContextClassificationDesign:
    valid: bool
    reason: str


@dataclass(frozen=True)
class Admit008OutcomeDesign:
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_value: str
    validated_candidate_fields: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TopologyDispositionClassificationDesign:
    scalar: ScalarClassificationDesign
    context: ContextClassificationDesign
    admit_008: Admit008OutcomeDesign


class _StringSubclass(str):
    """Synthetic truth-only exact-type negative."""


class _TupleSubclass(tuple):
    """Synthetic truth-only exact-type negative."""


def _bool(value: bool) -> str:
    return "true" if value else "false"


def validate_topology_restoration_disposition_design(value: object) -> ScalarClassificationDesign:
    """Apply exact str, nonempty, ASCII, syntax, then Exact4 membership."""
    if type(value) is not str:
        return ScalarClassificationDesign("invalid", "", SCALAR_REASONS[0], ())
    if value == "":
        return ScalarClassificationDesign("invalid", "", SCALAR_REASONS[1], ())
    if not value.isascii():
        return ScalarClassificationDesign("invalid", "", SCALAR_REASONS[2], ())
    if re.fullmatch(CANONICAL_SYNTAX, value, flags=re.ASCII) is None:
        return ScalarClassificationDesign("invalid", "", SCALAR_REASONS[3], ())
    if value not in CANONICAL_ENUM_MEMBERS:
        return ScalarClassificationDesign("unknown", "", SCALAR_REASONS[4], ())
    pair = ((CANDIDATE_FIELDS[0], value),)
    return ScalarClassificationDesign("canonical", value, "", pair)


def validate_allowed_topology_restoration_dispositions_design(value: object) -> ContextClassificationDesign:
    """Require the exact built-in tuple, exact str members, contents, and order."""
    if type(value) is not tuple:
        return ContextClassificationDesign(False, CONTEXT_REASONS[0])
    if any(type(member) is not str for member in value) or value != ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS:
        return ContextClassificationDesign(False, CONTEXT_REASONS[1])
    return ContextClassificationDesign(True, "")


def classify_admit_008_topology_restoration_disposition_design(
    topology_restoration_disposition: object,
    allowed_topology_restoration_dispositions: object,
) -> TopologyDispositionClassificationDesign:
    """Independent pure design oracle; the future evaluator must not call it."""
    scalar = validate_topology_restoration_disposition_design(topology_restoration_disposition)
    context = validate_allowed_topology_restoration_dispositions_design(allowed_topology_restoration_dispositions)
    if scalar.classification != "canonical":
        outcome = Admit008OutcomeDesign("invalid", False, True, scalar.reason, "", ())
    elif not context.valid:
        outcome = Admit008OutcomeDesign(
            "invalid", False, True, context.reason, scalar.canonical_value,
            scalar.validated_candidate_fields,
        )
    elif scalar.canonical_value in ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS:
        outcome = Admit008OutcomeDesign(
            "passed", True, False, "", scalar.canonical_value, scalar.validated_candidate_fields,
        )
    else:
        outcome = Admit008OutcomeDesign(
            "blocked", False, True, BLOCKED_REASONS[scalar.canonical_value],
            scalar.canonical_value, scalar.validated_candidate_fields,
        )
    return TopologyDispositionClassificationDesign(scalar, context, outcome)


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts) and ".." not in path.parts
        and path.parts[0] != "checkpoints" and path.parts[:2] != ("data", "raw")
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
    """Metadata-only check; no source content bytes are read here."""
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
    """Complete all Exact15 structural checks before the first byte read."""
    if len(SOURCE_PATHS) != 15 or len(set(SOURCE_PATHS)) != 15 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact15 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records = []
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
        type(value) is FrozenSourceSnapshot and len(value.records) == 15
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


def _row(document: CsvDocument, key: str, value: str) -> dict[str, str]:
    matches = tuple(row for row in document.rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    audit_source = ast.parse(_record(snapshot, AUDIT_SOURCE_PATH).content_bytes.decode("utf-8"))
    audit_manifest = _json_document(snapshot, AUDIT_MANIFEST_PATH)
    audit_matrix = _csv_document(snapshot, AUDIT_MATRIX_PATH)
    audit_vocabulary = _csv_document(snapshot, AUDIT_VOCABULARY_PATH)
    runtime_manifest = _json_document(snapshot, RUNTIME_MANIFEST_PATH)
    issues = _csv_document(snapshot, AUDIT_ISSUE_PATH)
    rule = _row(_csv_document(snapshot, RULE_REGISTRY_PATH), "admission_rule_id", "ADMIT_008")
    schema = _row(_csv_document(snapshot, SCHEMA_PATH), "admission_field_name", CANDIDATE_FIELDS[0])
    field = _row(_csv_document(snapshot, FIELD_PATH), "field_name", CANDIDATE_FIELDS[0])
    executable = _row(_csv_document(snapshot, EXECUTABILITY_PATH), "admission_rule_id", "ADMIT_008")
    rules = _csv_document(snapshot, RESTORATION_RULE_PATH)
    candidates = _csv_document(snapshot, CANDIDATE_PATH)
    step13m = _json_document(snapshot, STEP13M_MANIFEST_PATH)
    decisions = _csv_document(snapshot, REVIEW_DECISION_PATH)
    step13n = _json_document(snapshot, STEP13N_MANIFEST_PATH)
    issue = _row(issues, "issue_id", PRIMARY_ISSUE)
    coverage = _row(issues, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    functions = {node.name for node in audit_source.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in audit_source.body if isinstance(node, ast.ClassDef)}
    cys_rule = _row(rules, "rule_id", "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1")
    quarantine = _row(rules, "rule_id", "UNKNOWN_RESIDUE_WARHEAD_PAIR_QUARANTINE")
    required = (
        len(audit_matrix.rows) == 20 and len(audit_vocabulary.rows) == 22,
        audit_manifest["topology_disposition_enum_issue_status"] == "open",
        audit_manifest["ready_for_admit_008_topology_restoration_disposition_enum_contract_design"] is True,
        audit_manifest["ready_for_admit_008_standalone_evaluator_interface_implementation"] is False,
        runtime_manifest["registered_rule_ids"] == [f"ADMIT_{index:03d}" for index in range(1, 8)],
        runtime_manifest["admit_008_registered_in_engine"] is False,
        "evaluate_admit_008" not in functions and "Admit008EvaluationResult" not in classes,
        rule["admission_rule_name"] == CANDIDATE_FIELDS[0],
        rule["evidence_source"] == "approved_template_or_manual_review",
        rule["required_status"] == "approved_or_manual_review",
        rule["blocking_reason"] == "topology_restoration_unapproved",
        schema["value_contract"] == "approved template or explicit manual review",
        field["allowed_values_defined"] == field["normalization_defined"] == field["exact_validation_defined"] == "false",
        executable["evaluation_context_dependencies"] == CONTEXT_ITEMS[0],
        issue["status"] == "open" and issue["affected_fields"] == CANDIDATE_FIELDS[0],
        issue["affected_rules"] == "ADMIT_008" and issue["integration_transition"] == "unchanged_open",
        len(issues.rows) == 11 and coverage["affected_rules"].startswith("ADMIT_008|"),
        cys_rule["validated_for_current_samples"] == "True" and cys_rule["v1_train_ready_scope_allowed"] == "True",
        quarantine["quarantine_if_rule_unknown"] == "True" and quarantine["v1_train_ready_scope_allowed"] == "False",
        len(candidates.rows) == 3 and len(decisions.rows) == 8,
        step13m["unknown_residue_warhead_pair_quarantined"] is True,
        step13m["restoration_rules_residue_warhead_specific"] is True,
        step13n["topology_smoke_must_not_auto_restore_ligand"] is True,
        step13n["topology_smoke_must_not_generalize_to_non_cys"] is True,
        step13n["feature_semantics_audit_required_before_training"] is True,
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")
    return issues.rows


def _source_kind(path: Path) -> str:
    return "production_source" if path.suffix == ".py" else "committed_manifest" if path.suffix == ".json" else "committed_contract_csv"


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": _source_kind(record.relative_path),
        "boundary_necessity": "normative ADMIT_008 identity, policy, issue, and runtime evidence",
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


def _enum_registry_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        "approved reusable restoration template is valid for the current candidate or frozen scope",
        "candidate-specific manual review is complete, traceable, and explicitly approved",
        "topology restoration is not approved and requires completed human review",
        "unknown, untrusted, inapplicable, or quarantined residue-warhead restoration path",
    )
    rows = []
    for index, (value, definition) in enumerate(zip(CANONICAL_ENUM_MEMBERS, definitions, strict=True), 1):
        passed = index <= 2
        rows.append({
            "enum_order": str(index), "canonical_value": value, "semantic_definition": definition,
            "normative_contract_member": "true", "passed_by_admit_008": _bool(passed),
            "blocked_by_admit_008": _bool(not passed), "formal_reason": "" if passed else BLOCKED_REASONS[value],
            "included_in_allowed_context": _bool(passed), "provider_mapping_required": "true",
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
    exact = ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
    scalar_cases: tuple[tuple[str, str, object], ...] = (
        ("canonical_approved_template", "canonical", CANONICAL_ENUM_MEMBERS[0]),
        ("canonical_manual_approved", "canonical", CANONICAL_ENUM_MEMBERS[1]),
        ("canonical_manual_required", "canonical", CANONICAL_ENUM_MEMBERS[2]),
        ("canonical_quarantine", "canonical", CANONICAL_ENUM_MEMBERS[3]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(CANONICAL_ENUM_MEMBERS[0])),
        ("type_list", "scalar_type", [CANONICAL_ENUM_MEMBERS[0]]),
        ("type_mapping", "scalar_type", {"value": CANONICAL_ENUM_MEMBERS[0]}),
        ("empty", "empty_syntax", ""), ("whitespace", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " approved_restoration_template"),
        ("trailing_whitespace", "empty_syntax", "approved_restoration_template "),
        ("uppercase", "empty_syntax", "Approved_restoration_template"),
        ("hyphen", "empty_syntax", "approved-restoration-template"),
        ("dot", "empty_syntax", "approved.restoration"),
        ("slash", "empty_syntax", "approved/restoration"),
        ("non_ascii", "empty_syntax", "approved_restoratión"),
        ("over_length", "empty_syntax", "a" * 65), ("leading_digit", "empty_syntax", "1approved"),
        ("unknown_valid", "unknown", "unregistered_disposition"),
        ("unknown_approved_looking", "unknown", "approved_manual_review"),
        ("unknown_manual_review_looking", "unknown", "manual_review_approved"),
        ("unknown_other", "unknown", "other"), ("unknown_unknown", "unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact), ("context_none", None), ("context_list", list(exact)),
        ("context_set", set(exact)), ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))), ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_blocked_added", (*exact, CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    definitions = [(case_id, group, scalar, "exact_tuple", exact) for case_id, group, scalar in scalar_cases]
    definitions.extend((case_id, "context", CANONICAL_ENUM_MEMBERS[0], case_id.removeprefix("context_"), context) for case_id, context in context_cases)
    return tuple(definitions)


def _validated_display(value: tuple[tuple[str, str], ...]) -> str:
    return "" if not value else f"{value[0][0]}={value[0][1]}"


def _truth_matrix_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (case_id, group, scalar, context_kind, context) in enumerate(_truth_definitions(), 1):
        result = classify_admit_008_topology_restoration_disposition_design(scalar, context)
        rows.append({
            "case_id": f"CASE_{index:03d}_{case_id}", "case_group": group,
            "scalar_input_kind": type(scalar).__name__, "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind, "expected_scalar_classification": result.scalar.classification,
            "expected_canonical_value": result.admit_008.canonical_value,
            "expected_scalar_reason": result.scalar.reason, "expected_context_valid": _bool(result.context.valid),
            "expected_context_reason": result.context.reason, "expected_outcome": result.admit_008.outcome,
            "expected_passed": _bool(result.admit_008.passed),
            "expected_blocks_candidate": _bool(result.admit_008.blocks_candidate),
            "expected_reason": result.admit_008.reason,
            "expected_validated_candidate_fields": _validated_display(result.admit_008.validated_candidate_fields),
            "scalar_failure_precedence": "true", "case_passed": "true",
        })
    if len(rows) != 38:
        raise ValueError("Exact38 truth shape invalid")
    return tuple(rows)


def _category_mapping_rows() -> tuple[dict[str, str], ...]:
    specs = (
        ("validated_current_scope_template", "validated approved reusable template for current candidate/scope", CANONICAL_ENUM_MEMBERS[0], "passed", "", "validated template after quarantine/review checks"),
        ("candidate_specific_manual_approval", "traceable completed candidate-specific manual approval", CANONICAL_ENUM_MEMBERS[1], "passed", "", "explicit manual approval after quarantine checks"),
        ("manual_review_not_completed", "manual review required but no completed approval", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "unfinished review overrides approval claim"),
        ("deferred_or_new_rule", "deferred, unvalidated, or new restoration rule", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "deferred/new rule requires review"),
        ("unknown_residue_warhead_pair", "unknown residue-warhead pair", CANONICAL_ENUM_MEMBERS[3], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]], "unknown pair quarantines"),
        ("quarantine_flag", "quarantine flag is true", CANONICAL_ENUM_MEMBERS[3], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]], "quarantine evidence first"),
        ("quarantine_over_template", "quarantine flag plus template approval claim", CANONICAL_ENUM_MEMBERS[3], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]], "quarantine overrides template claim"),
        ("quarantine_over_manual_approval", "quarantine flag plus manual approval claim", CANONICAL_ENUM_MEMBERS[3], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]], "quarantine overrides manual approval claim"),
        ("unvalidated_template", "template exists but current sample/scope validation absent", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "unvalidated template cannot approve"),
        ("manual_visual_review_required_true", "manual_visual_review_required=true without completed decision", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "review required is not review approved"),
        ("new_residue_or_warhead", "template claim generalized to a new residue or warhead", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "no residue/warhead auto-generalization"),
        ("no_v1_bypass", "not_applicable or no_restoration_required bypass claim", CANONICAL_ENUM_MEMBERS[2], "blocked", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]], "V1 has no bypass member"),
    )
    return tuple({
        "mapping_order": str(index), "mapping_case_id": case_id, "policy_evidence": evidence,
        "expected_canonical_disposition": canonical, "expected_outcome": outcome,
        "expected_reason": reason, "mapping_precedence": precedence,
        "real_provider_mapping_executed": "false", "mapping_contract_passed": "true",
    } for index, (case_id, evidence, canonical, outcome, reason, precedence) in enumerate(specs, 1))


def _issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> tuple[dict[str, str], ...]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [row for row in rows if row["issue_id"] == PRIMARY_ISSUE]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("Exact11 issue baseline invalid")
    before = dict(matches[0])
    matches[0]["status"] = "resolved"
    matches[0]["integration_transition"] = "topology_restoration_disposition_enum_contract_frozen_v1"
    changed = {key for key in matches[0] if matches[0][key] != before[key]}
    if changed != {"status", "integration_transition"}:
        raise ValueError("issue transition exceeded authorization")
    return tuple(rows)


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _validate_rows(state: Mapping[str, Any]) -> None:
    groups = {group: sum(row["case_group"] == group for row in state["truth_matrix_rows"])
              for group in ("canonical", "scalar_type", "empty_syntax", "unknown", "context")}
    enum_issue = next(row for row in state["issue_rows"] if row["issue_id"] == PRIMARY_ISSUE)
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    required = (
        len(state["source_boundary_rows"]) == 15, len(state["enum_registry_rows"]) == 4,
        len(state["truth_matrix_rows"]) == 38, groups == {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12},
        len(state["category_mapping_rows"]) == 12, len(state["issue_rows"]) == 11,
        all(row["v1_enum_row_passed"] == "true" for row in state["enum_registry_rows"]),
        all(row["case_passed"] == "true" for row in state["truth_matrix_rows"]),
        all(row["mapping_contract_passed"] == "true" and row["real_provider_mapping_executed"] == "false" for row in state["category_mapping_rows"]),
        enum_issue["status"] == "resolved",
        enum_issue["integration_transition"] == "topology_restoration_disposition_enum_contract_frozen_v1",
        coverage["status"] == "open" and coverage["affected_rules"].startswith("ADMIT_008|"),
    )
    if not all(required):
        raise ValueError("design row validation failed")


def build_design_state(snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    if not validate_frozen_source_snapshot(frozen):
        raise ValueError("invalid frozen snapshot")
    predecessor_issues = _validate_predecessors(frozen)
    state = {
        "source_boundary_rows": _source_boundary_rows(frozen),
        "enum_registry_rows": _enum_registry_rows(),
        "truth_matrix_rows": _truth_matrix_rows(),
        "category_mapping_rows": _category_mapping_rows(),
        "issue_rows": _issue_rows(predecessor_issues),
        "readiness": _readiness(),
    }
    _validate_rows(state)
    return state


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    groups = {group: sum(row["case_group"] == group for row in state["truth_matrix_rows"])
              for group in ("canonical", "scalar_type", "empty_syntax", "unknown", "context")}
    readiness = dict(state["readiness"])
    payload: dict[str, Any] = {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_008", "admission_rule_name": "topology_restoration_disposition",
        "candidate_field": CANDIDATE_FIELDS[0], "context_item": CONTEXT_ITEMS[0],
        "future_evaluator": "evaluate_admit_008", "future_result": "Admit008EvaluationResult",
        "future_signature_parameters": [CANDIDATE_FIELDS[0], CONTEXT_ITEMS[0]],
        "future_signature_required_positional_or_keyword": True,
        "standalone_interface": "required_direct_scalar_and_direct_context_objects",
        "candidate_mapping_accepted": False, "candidate_key_missing_handled_by_standalone": False,
        "source_boundary_name": "fixed_ordered_exact15_committed_source_boundary",
        "source_input_count": 15, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": int(row["source_order"]), "source_relative_path": row["source_relative_path"],
            "expected_sha256": row["expected_sha256"], "base_tree_sha256": row["base_tree_sha256"],
            "filesystem_sha256": row["filesystem_sha256"], "tracked": True, "base_tree_blob": True,
            "filesystem_regular": True, "non_symlink": True, "source_verified": True,
        } for row in state["source_boundary_rows"]],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "normative_enum_member_count": 4, "normative_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "excluded_enum_members": [
            "approved_template_or_manual_review", "approved_or_manual_review", "topology_restoration_unapproved",
            "accepted", "quarantine_only", "unknown", "other", "unapproved", "deferred",
            "not_applicable", "no_restoration_required",
        ],
        "restoration_rule_ids_are_enum_members": False, "training_or_review_statuses_are_enum_members": False,
        "alias_support": False, "scalar_normalization_applied": False,
        "scalar_exact_runtime_type": "builtins.str", "scalar_canonical_syntax": CANONICAL_SYNTAX,
        "scalar_validation_precedence": ["exact_type", "nonempty", "ascii", "syntax", "membership"],
        "scalar_validation_reasons": list(SCALAR_REASONS),
        "context_exact_runtime_type": "builtins.tuple",
        "allowed_topology_restoration_dispositions": list(ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        "context_validation_precedence": ["exact_tuple_type", "exact_str_member_types", "exact_content_and_order"],
        "context_validation_reasons": list(CONTEXT_REASONS),
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "blocked_reason_mapping": dict(BLOCKED_REASONS),
        "historical_lowercase_reason": "topology_restoration_unapproved",
        "historical_lowercase_reason_is_future_formal_reason": False,
        "candidate_fields": list(CANDIDATE_FIELDS), "context_items": list(CONTEXT_ITEMS),
        "invalid_scalar_canonical_value": "", "invalid_scalar_validated_candidate_fields": [],
        "canonical_scalar_context_invalid_retains_canonical_pair": True,
        "passed_and_blocked_retain_canonical_pair": True,
        "independent_design_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "future_production_evaluator_must_not_call_design_oracle": True,
        "truth_matrix_row_count": 38, "truth_matrix_pass_count": 38,
        "truth_matrix_group_counts": groups, "category_mapping_row_count": 12,
        "category_mapping_pass_count": 12,
        "mapping_precedence": [
            "quarantine_evidence", "unfinished_or_required_manual_review",
            "validated_approved_reusable_template", "explicit_candidate_specific_manual_approval",
            "fail_closed_manual_review_or_quarantine",
        ],
        "provider_mapping_responsibility": "future_provider_or_candidate_materialization_contract",
        "standalone_provider_fields_consumed": [], "real_provider_value_count": 0,
        "real_provider_mapping_executed": False,
        "issue_inventory_row_count": 11, "issue_transition_count": 1,
        "issue_transition_id": PRIMARY_ISSUE, "issue_transition_status": "resolved",
        "issue_integration_transition": "topology_restoration_disposition_enum_contract_frozen_v1",
        "unified_coverage_still_includes_admit_008": True,
        "readiness": readiness, **readiness,
        "output_file_count": 6, "output_files": list(OUTPUT_FILES),
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "no_evaluate_admit_008", "no_Admit008EvaluationResult", "no_adapter",
            "no_exact7_runtime_modification", "no_admit_008_registration", "no_provider_mapping_execution",
            "no_real_candidate_evaluation", "no_admit_009", "no_raw_network_download", "no_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_source_boundary_checks_passed": True, "all_enum_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_category_mapping_checks_passed": True,
        "all_issue_checks_passed": True, "all_readiness_checks_passed": True,
        "all_attestations_passed": True, "validation_failures": [],
    }
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    payloads = {
        ENUM_REGISTRY_FILENAME: _csv_bytes(ENUM_REGISTRY_COLUMNS, state["enum_registry_rows"]),
        TRUTH_MATRIX_FILENAME: _csv_bytes(TRUTH_MATRIX_COLUMNS, state["truth_matrix_rows"]),
        CATEGORY_MAPPING_FILENAME: _csv_bytes(CATEGORY_MAPPING_COLUMNS, state["category_mapping_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_boundary_rows"]),
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


def run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1(
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
    run_covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1()

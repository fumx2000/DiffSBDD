"""Read-only ADMIT_006 formal evaluator interface preconditions audit v1.

This metadata-only design gate inventories committed semantics.  It does not
implement an evaluator, adapter, registry entry, provider, or candidate run.
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
STEP = "ADMIT_006 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "34591c787448880793e54f0a0c980ed16b1873d7"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_005 v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_006_formal_evaluator_preconditions_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_covalent_event_evidence_source_enum_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1"
)

SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
        str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
        str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
        "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
        str(PRECONDITION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
        str(PRECONDITION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
        str(PRECONDITION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
        str(PRECONDITION_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"),
        str(PRECONDITION_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py",
        str(RUNTIME_ROOT / "covapie_admit_001_to_005_runtime_issue_inventory.csv"),
        str(RUNTIME_ROOT / "covapie_admit_001_to_005_runtime_manifest.json"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
            "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
            "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
            "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
            "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
            "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
            "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
            "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
            "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
            "c923d0dfe2edad534a2f530dbbac53870823ff2aa231730acbcd63577edfdb23",
            "7f815f3358ae3e53d296bc3ec0a129cd459184a76aa5169649b73fb1440e28bc",
            "699143ca47d8ff51dbf9779fce2a95ef537d1d6053d93a73f941725d6219256e",
        ),
        strict=True,
    )
)

DESIGN_SOURCE_PATH = SOURCE_PATHS[0]
SCHEMA_PATH = SOURCE_PATHS[1]
RULE_REGISTRY_PATH = SOURCE_PATHS[2]
PRECONDITION_SOURCE_PATH = SOURCE_PATHS[3]
CONTEXT_PATH = SOURCE_PATHS[4]
FIELD_PATH = SOURCE_PATHS[5]
RULE_EXECUTABILITY_PATH = SOURCE_PATHS[6]
PRECONDITION_ISSUE_PATH = SOURCE_PATHS[7]
PRECONDITION_MANIFEST_PATH = SOURCE_PATHS[8]
RUNTIME_SOURCE_PATH = SOURCE_PATHS[9]
RUNTIME_ISSUE_PATH = SOURCE_PATHS[10]
RUNTIME_MANIFEST_PATH = SOURCE_PATHS[11]

MATCH_TERMS = (
    "covalent_event_evidence_source",
    "ADMIT_006",
    "ADMIT_007",
    "explicit_covalent_event_evidence",
    "distance_only_inference_forbidden",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "explicit_evidence_source_present",
    "covalent_event_evidence_missing",
    "distance_only_inference_not_admissible",
)

SOURCE_BOUNDARY_FILENAME = "covapie_admit_006_source_boundary_audit.csv"
OCCURRENCE_FILENAME = "covapie_admit_006_field_occurrence_inventory.csv"
VALUE_FILENAME = "covapie_admit_006_observed_evidence_value_inventory.csv"
PRECONDITION_FILENAME = "covapie_admit_006_evaluator_precondition_matrix.csv"
ISSUE_FILENAME = "covapie_admit_006_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_006_formal_evaluator_preconditions_manifest.json"
CSV_OUTPUTS = (
    SOURCE_BOUNDARY_FILENAME,
    OCCURRENCE_FILENAME,
    VALUE_FILENAME,
    PRECONDITION_FILENAME,
    ISSUE_FILENAME,
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
    "explicit_covalent_evidence_attested", "distance_only_attested",
    "manual_review_attested", "enum_membership_frozen", "safe_for_admit_006_pass",
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
    "admit_006_precondition_audit_completed",
    "admit_006_source_occurrence_inventory_completed",
    "admit_006_observed_value_inventory_completed",
    "feature_semantics_audit_required_before_training",
    "ready_for_covapie_covalent_event_evidence_source_enum_contract_design",
)
FALSE_READINESS = (
    "covalent_event_evidence_source_candidate_semantics_frozen",
    "covalent_event_evidence_source_enum_frozen",
    "admit_006_admit_007_responsibility_boundary_frozen",
    "admit_006_reason_outcome_contract_frozen",
    "admit_006_independent_oracle_available",
    "ready_for_admit_006_standalone_evaluator_interface_implementation",
    "admit_006_standalone_evaluator_implemented",
    "admit_006_unified_adapter_contract_frozen",
    "admit_006_unified_adapter_implemented",
    "admit_006_registered_in_engine",
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


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False
    )


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path)
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] != "checkpoints"
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
    """Inspect metadata only; no source content bytes are read here."""
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
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields) == 3
        and fields[0] in ("100644", "100755")
        and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete every structural check before the first explicit byte read."""
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
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 12
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


def _registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets):
            continue
        value = node.value
        if isinstance(value, ast.Call) and value.args:
            value = value.args[0]
        if isinstance(value, ast.Dict):
            keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant) and type(key.value) is str)
            if len(keys) == len(value.keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    schema = _csv_document(snapshot, SCHEMA_PATH)
    registry = _csv_document(snapshot, RULE_REGISTRY_PATH)
    context = _csv_document(snapshot, CONTEXT_PATH)
    fields = _csv_document(snapshot, FIELD_PATH)
    executability = _csv_document(snapshot, RULE_EXECUTABILITY_PATH)
    precondition_issues = _csv_document(snapshot, PRECONDITION_ISSUE_PATH)
    runtime_issues = _csv_document(snapshot, RUNTIME_ISSUE_PATH)
    precondition_manifest = _json_document(snapshot, PRECONDITION_MANIFEST_PATH)
    runtime_manifest = _json_document(snapshot, RUNTIME_MANIFEST_PATH)
    design_tree = _ast_document(snapshot, DESIGN_SOURCE_PATH)
    precondition_tree = _ast_document(snapshot, PRECONDITION_SOURCE_PATH)
    runtime_tree = _ast_document(snapshot, RUNTIME_SOURCE_PATH)
    field = _row(schema, "admission_field_name", "covalent_event_evidence_source")
    admit006 = _row(registry, "admission_rule_id", "ADMIT_006")
    admit007 = _row(registry, "admission_rule_id", "ADMIT_007")
    field_semantics = _row(fields, "field_name", "covalent_event_evidence_source")
    context_semantics = _row(context, "context_item", "allowed_covalent_evidence_classes")
    exec006 = _row(executability, "admission_rule_id", "ADMIT_006")
    exec007 = _row(executability, "admission_rule_id", "ADMIT_007")
    blocker = _row(runtime_issues, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    predecessor_blocker = _row(precondition_issues, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    top_level_runtime_functions = tuple(
        node.name for node in runtime_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    if not (
        field["requirement_phase"] == "pre_download"
        and field["required_at_phase"] == "true"
        and field["value_contract"] == "explicit non-distance-only evidence source"
        and admit006 == {
            "admission_rule_id": "ADMIT_006", "admission_rule_name": "explicit_covalent_event_evidence",
            "evidence_source": "future_candidate_record", "required_status": "explicit_evidence_source_present",
            "failure_severity": "blocking", "blocking_reason": "covalent_event_evidence_missing",
            "evaluation_phase": "pre_download", "network_required": "false",
            "raw_structure_required": "false", "ready_for_future_implementation": "true",
        }
        and admit007["admission_rule_name"] == "distance_only_inference_forbidden"
        and admit007["required_status"] == "not_distance_only_inference"
        and admit007["blocking_reason"] == "distance_only_inference_not_admissible"
        and field_semantics["candidate_record_field"] == "true"
        and field_semantics["producer_scope"] == "candidate_metadata_provider"
        and field_semantics["dependent_rules"] == "ADMIT_006|ADMIT_007"
        and field_semantics["evaluation_context_dependencies"] == "allowed_covalent_evidence_classes"
        and field_semantics["allowed_values_defined"] == "false"
        and field_semantics["normalization_defined"] == "false"
        and field_semantics["exact_validation_defined"] == "false"
        and field_semantics["implementation_semantics_complete"] == "false"
        and context_semantics["required_by_rules"] == "ADMIT_006|ADMIT_007"
        and context_semantics["exact_contract_defined"] == "false"
        and context_semantics["implementation_ready"] == "false"
        and exec006["semantics_complete"] == "false"
        and exec007["semantics_complete"] == "false"
        and exec006["blocking_reasons"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"
        and exec007["blocking_reasons"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"
        and predecessor_blocker["status"] == "open"
        and blocker["affected_fields"] == "covalent_event_evidence_source"
        and blocker["affected_rules"] == "ADMIT_006|ADMIT_007"
        and blocker["severity"] == "blocking" and blocker["status"] == "open"
        and len(runtime_issues.rows) == 11
        and runtime_manifest.get("registered_rule_ids") == [f"ADMIT_{index:03d}" for index in range(1, 6)]
        and runtime_manifest.get("registered_rule_count") == 5
        and runtime_manifest.get("admit_006_to_015_registered") is False
        and runtime_manifest.get("evaluate_all_rules_implemented") is False
        and runtime_manifest.get("active_issue_count") == 11
        and runtime_manifest.get("all_checks_passed") is True
        and precondition_manifest.get("all_checks_passed") is False
        and _registry_keys(runtime_tree) == tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
        and "evaluate_all_rules" not in top_level_runtime_functions
        and "evaluate_admit_006" not in top_level_runtime_functions
        and any(isinstance(node, ast.Constant) and node.value == "covalent_event_evidence_source" for node in ast.walk(design_tree))
        and any(isinstance(node, ast.Constant) and node.value == "COVALENT_EVIDENCE_ENUM_UNRESOLVED" for node in ast.walk(precondition_tree))
    ):
        raise ValueError("predecessor semantics mismatch")
    return {
        "runtime_issue_rows": tuple(dict(row) for row in runtime_issues.rows),
        "registered_rule_ids": tuple(runtime_manifest["registered_rule_ids"]),
    }


def _source_kind(path: Path) -> str:
    name = path.name
    if path.suffix == ".py":
        return "source_code"
    if "issue" in name:
        return "issue"
    if path.suffix == ".json":
        return "manifest"
    if "schema_contract" in name or "rule_registry" in name or "context_contract" in name:
        return "contract"
    if "field_semantics" in name or "rule_executability" in name:
        return "truth"
    return "metadata"


def _boundary_necessity(path: Path) -> str:
    if path in (DESIGN_SOURCE_PATH, SCHEMA_PATH, RULE_REGISTRY_PATH):
        return "canonical_field_and_rule_contract"
    if path in (PRECONDITION_SOURCE_PATH, CONTEXT_PATH, FIELD_PATH, RULE_EXECUTABILITY_PATH, PRECONDITION_ISSUE_PATH, PRECONDITION_MANIFEST_PATH):
        return "implementation_precondition_and_rule_semantics"
    return "current_exact5_runtime_registry_issue_and_readiness"


def _source_boundary_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "source_order": str(index),
            "source_relative_path": record.relative_path.as_posix(),
            "source_kind": _source_kind(record.relative_path),
            "boundary_necessity": _boundary_necessity(record.relative_path),
            "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
            "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
        }
        for index, record in enumerate(snapshot.records, 1)
    )


def _csv_row_identity(text: str, line_number: int) -> str:
    lines = text.splitlines()
    if line_number <= 1 or line_number > len(lines):
        return f"line:{line_number}"
    header = next(csv.reader([lines[0]]), [])
    row = next(csv.reader([lines[line_number - 1]]), [])
    if header and row:
        return f"{header[0]}={row[0]}"
    return f"line:{line_number}"


def _occurrence_role(line: str) -> str:
    roles: list[str] = []
    if "covalent_event_evidence_source" in line:
        roles.append("candidate_scalar")
    if "candidate_metadata_provider" in line:
        roles.append("provider_metadata")
    if "allowed_covalent_evidence_classes" in line:
        roles.append("context_item")
    if not roles:
        roles.append("rule_or_blocker_declaration")
    return "|".join(roles)


def _rule_scope(line: str) -> str:
    rules = tuple(rule for rule in ("ADMIT_006", "ADMIT_007") if rule in line)
    return "|".join(rules)


def _semantic_statement(line: str) -> str:
    if "COVALENT_EVIDENCE_ENUM_UNRESOLVED" in line:
        return "allowed evidence enum and shared ADMIT_006/ADMIT_007 semantics remain unresolved"
    if "explicit non-distance-only evidence source" in line:
        return "historical value contract only; not an enum member"
    if "explicit_evidence_source_present" in line or "covalent_event_evidence_missing" in line:
        return "ADMIT_006 required-status or blocking-reason declaration"
    if "distance_only_inference_not_admissible" in line or "distance_only_inference_forbidden" in line:
        return "ADMIT_007 rule or blocking-reason declaration"
    if "allowed_covalent_evidence_classes" in line:
        return "shared evaluation-context dependency declaration without frozen payload"
    if "covalent_event_evidence_source" in line:
        return "candidate field or provider-scope declaration without concrete value"
    return "rule coverage or registration declaration"


def _occurrence_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[Path, int, str]] = set()
    for record in snapshot.records:
        text = record.content_bytes.decode("utf-8", errors="strict")
        for line_number, line in enumerate(text.splitlines(), 1):
            for term in MATCH_TERMS:
                identity = (record.relative_path, line_number, term)
                if term not in line or identity in seen:
                    continue
                seen.add(identity)
                row_identity = (
                    _csv_row_identity(text, line_number)
                    if record.relative_path.suffix == ".csv"
                    else f"line:{line_number}"
                )
                rows.append({
                    "occurrence_order": str(len(rows) + 1),
                    "source_relative_path": record.relative_path.as_posix(),
                    "source_sha256": record.expected_sha256,
                    "source_kind": _source_kind(record.relative_path),
                    "symbol_or_row_id": row_identity,
                    "matched_term": term,
                    "field_role": _occurrence_role(line),
                    "rule_scope": _rule_scope(line),
                    "semantic_statement": _semantic_statement(line),
                    "contains_concrete_value": "false",
                    "concrete_value": "",
                    "authoritative_for_runtime_semantics": _bool(record.relative_path in (
                        SCHEMA_PATH, RULE_REGISTRY_PATH, CONTEXT_PATH, FIELD_PATH,
                        RULE_EXECUTABILITY_PATH, RUNTIME_ISSUE_PATH, RUNTIME_MANIFEST_PATH,
                    )),
                    "occurrence_passed": "true",
                })
    return tuple(rows)


def _observed_value_rows() -> tuple[dict[str, str], ...]:
    """No committed candidate values exist in the frozen readable boundary."""
    return ()


def _precondition_specs() -> tuple[tuple[str, str, str, str, str, bool, str, str], ...]:
    blocker = "COVALENT_EVIDENCE_ENUM_UNRESOLVED"
    return (
        ("PRE_001", "candidate_field_name", "one exact candidate field", "covalent_event_evidence_source is the sole named field", "schema_contract:covalent_event_evidence_source", True, "", "frozen"),
        ("PRE_002", "candidate_projection", "exact standalone candidate projection", "candidate_record_field=true but no evaluator projection", "field_semantics:covalent_event_evidence_source", False, blocker, "design_enum_and_interface_contract"),
        ("PRE_003", "scalar_exact_type", "exact scalar type", "no exact type contract", "field_semantics:exact_validation_defined=false", False, blocker, "design_enum_contract"),
        ("PRE_004", "empty_handling", "missing/null/empty semantics", "only missing blocking-reason name; no null or empty mapping", "rule_registry:ADMIT_006", False, blocker, "design_enum_contract"),
        ("PRE_005", "canonicalization", "ASCII whitespace and case rules", "normalization_defined=false", "field_semantics:covalent_event_evidence_source", False, blocker, "design_enum_contract"),
        ("PRE_006", "allowed_enum", "finite canonical evidence enum", "allowed_values_defined=false", "field_semantics:covalent_event_evidence_source", False, blocker, "design_enum_contract"),
        ("PRE_007", "unknown_enum_handling", "fail-closed unknown-value disposition", "no unknown value semantics", "context_contract:allowed_covalent_evidence_classes", False, blocker, "design_enum_contract"),
        ("PRE_008", "explicit_vs_distance_only", "value-level classification boundary", "prose forbids distance-only but provides no member mapping", "schema_contract plus rules ADMIT_006/ADMIT_007", False, blocker, "design_enum_contract"),
        ("PRE_009", "admit006_admit007_boundary", "non-overlapping evaluator responsibilities", "both depend on same unresolved enum/context; value-to-rule ownership absent", "rule_executability:ADMIT_006|ADMIT_007", False, blocker, "design_enum_contract"),
        ("PRE_010", "outcome_vocabulary", "exact evaluator outcome mapping", "required-status labels exist; enum-to-outcome mapping absent", "rule_registry:ADMIT_006|ADMIT_007", False, blocker, "design_enum_contract"),
        ("PRE_011", "reason_vocabulary", "exact reason mapping for every input class", "two blocking reason names exist; input-class mapping absent", "rule_registry:ADMIT_006|ADMIT_007", False, blocker, "design_enum_contract"),
        ("PRE_012", "validated_normalized_mapping", "validated and normalized result fields", "no validation or normalization contract", "field_semantics:covalent_event_evidence_source", False, blocker, "design_enum_contract"),
        ("PRE_013", "runtime_context_dependency", "exact context type and values", "dependency name frozen; exact_contract_defined=false", "context_contract:allowed_covalent_evidence_classes", False, blocker, "design_enum_contract"),
        ("PRE_014", "independent_semantic_oracle", "independent value oracle", "no oracle exists", "runtime registry and frozen sources", False, blocker, "design_enum_contract"),
        ("PRE_015", "standalone_evaluator_safety", "implementable without semantic guessing", "presence-only would accept arbitrary nonempty strings", "PRE_003 through PRE_014", False, blocker, "blocked"),
        ("PRE_016", "real_provider_values", "committed real values sufficient to validate enum", "zero observed values", "observed_evidence_value_inventory", False, blocker, "future_provider_validation_after_contract"),
        ("PRE_017", "candidate_records", "authorized real candidate records", "no candidate materialization or evaluation authorized", "safety boundary", False, blocker, "blocked"),
        ("PRE_018", "bulk_download_readiness", "all rules and combined verdict ready", "ADMIT_006-015 unregistered and aggregation unresolved", "runtime issue inventory", False, "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE", "blocked"),
        ("PRE_019", "training_readiness", "feature-semantics audit and training authorization", "feature-semantics audit remains mandatory; training forbidden", "repository training prerequisite", False, "FEATURE_SEMANTICS_AUDIT_REQUIRED", "blocked"),
    )


def _precondition_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "precondition_id": item[0], "semantic_area": item[1], "required_contract": item[2],
        "observed_contract": item[3], "source_evidence": item[4], "semantics_complete": _bool(item[5]),
        "blocker_id": item[6], "implementation_disposition": item[7], "precondition_passed": "true",
    } for item in _precondition_specs())


def _validate_rows(state: Mapping[str, Any]) -> bool:
    boundary = state["source_boundary_rows"]
    occurrences = state["occurrence_rows"]
    values = state["value_rows"]
    preconditions = state["precondition_rows"]
    issues = state["issue_rows"]
    occurrence_keys = tuple((row["source_relative_path"], row["symbol_or_row_id"], row["matched_term"]) for row in occurrences)
    return (
        len(boundary) == 12
        and tuple(row["source_relative_path"] for row in boundary) == tuple(path.as_posix() for path in SOURCE_PATHS)
        and all(tuple(row) == SOURCE_BOUNDARY_COLUMNS and row["source_boundary_passed"] == "true" for row in boundary)
        and bool(occurrences)
        and len(occurrence_keys) == len(set(occurrence_keys))
        and all(tuple(row) == OCCURRENCE_COLUMNS and row["occurrence_passed"] == "true" and row["contains_concrete_value"] == "false" and row["concrete_value"] == "" for row in occurrences)
        and values == ()
        and len(preconditions) == 19
        and all(tuple(row) == PRECONDITION_COLUMNS and row["precondition_passed"] == "true" for row in preconditions)
        and [row["precondition_id"] for row in preconditions] == [f"PRE_{index:03d}" for index in range(1, 20)]
        and len(issues) == 11
        and all(tuple(row) == ISSUE_COLUMNS for row in issues)
        and next(row for row in issues if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED")["status"] == "open"
    )


def build_audit_state(snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    if not validate_frozen_source_snapshot(frozen):
        raise ValueError("invalid frozen source snapshot")
    predecessor = _validate_predecessors(frozen)
    state: dict[str, Any] = {
        "source_snapshot": frozen,
        "source_boundary_rows": _source_boundary_rows(frozen),
        "occurrence_rows": _occurrence_rows(frozen),
        "value_rows": _observed_value_rows(),
        "precondition_rows": _precondition_rows(),
        "issue_rows": predecessor["runtime_issue_rows"],
        "registered_rule_ids": predecessor["registered_rule_ids"],
    }
    state["all_checks_passed"] = _validate_rows(state)
    if state["all_checks_passed"] is not True:
        raise RuntimeError("ADMIT_006 precondition audit failed closed")
    return state


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    snapshot = state["source_snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {name: False for name in FALSE_READINESS}
    return {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_boundary_name": "fixed_exact12_committed_metadata_boundary",
        "source_input_count": 12,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": index, "source_relative_path": record.relative_path.as_posix(),
            "tracked": True, "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
            "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256, "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "tracked_discovery_completed_before_boundary_freeze": True,
        "discovery_terms": list(MATCH_TERMS),
        "discovery_exclusions": ["data/raw/**", "checkpoints/**", "untracked", "generated_cache", "artifact_reference_targets"],
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "source_boundary_row_count": 12,
        "field_occurrence_row_count": len(state["occurrence_rows"]),
        "observed_evidence_value_row_count": 0, "observed_evidence_values": [],
        "precondition_matrix_row_count": 19, "precondition_semantics_complete_count": 1,
        "active_issue_count": 11, "exact11_issue_baseline_preserved": True,
        "covalent_event_evidence_source_roles": ["candidate_scalar", "provider_metadata_producer_scope"],
        "allowed_covalent_evidence_classes_role": "runtime_context_item_with_unfrozen_contract",
        "canonical_evidence_enum_exists": False,
        "missing_semantics_frozen": False, "unknown_semantics_frozen": False,
        "distance_only_value_semantics_frozen": False, "manual_review_value_semantics_frozen": False,
        "presence_only_nonempty_string_evaluator_safe": False,
        "admit_006_admit_007_responsibility_statement": "shared unresolved enum/context dependency; value-level responsibility boundary is not frozen",
        "covalent_evidence_enum_issue_id": "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
        "covalent_evidence_enum_issue_status": "open", "covalent_evidence_enum_issue_severity": "blocking",
        "covalent_evidence_enum_issue_affected_rules": "ADMIT_006|ADMIT_007",
        "registered_rule_ids": list(state["registered_rule_ids"]), "registered_rule_count": 5,
        "admit_006_registered": False, "admit_007_registered": False,
        "evaluate_all_rules_exists": False,
        "safety_executed": [
            "tracked_occurrence_discovery", "fixed_source_boundary_construction", "source_sha_verification",
            "field_occurrence_classification", "committed_metadata_value_inventory",
            "admit_006_admit_007_responsibility_audit", "evaluator_precondition_audit", "issue_readiness_derivation",
        ],
        "safety_not_executed": [
            "raw_read", "artifact_dereference", "provider_execution", "parser_execution", "network_download",
            "candidate_materialization", "real_candidate_evaluation", "exact11_real_evaluation",
            "admit_006_evaluator_implementation", "adapter_implementation", "registry_modification",
            "admit_007_implementation", "evaluate_all_rules", "combined_verdict", "checkpoint",
            "torch_numpy_rdkit", "model_forward_loss_training",
        ],
        "readiness": readiness, **readiness,
        "all_source_boundary_checks_passed": True, "all_predecessor_checks_passed": True,
        "all_occurrence_inventory_checks_passed": True, "all_observed_value_inventory_checks_passed": True,
        "all_precondition_checks_passed": True, "all_issue_readiness_checks_passed": True,
        "all_safety_checks_passed": True, "all_checks_passed": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_boundary_rows"]),
        OCCURRENCE_FILENAME: _csv_bytes(OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        VALUE_FILENAME: _csv_bytes(VALUE_COLUMNS, state["value_rows"]),
        PRECONDITION_FILENAME: _csv_bytes(PRECONDITION_COLUMNS, state["precondition_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads = {**csv_payloads, MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")}
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
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
    else:
        root.mkdir(parents=True, exist_ok=False)
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root creation was unsafe")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        raise ValueError("output root contains unexpected entries")
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("output root contains unsafe entries")


def run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_audit_state()
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

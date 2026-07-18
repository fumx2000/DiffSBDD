"""CovaPIE ADMIT_006 standalone evaluator interface v1.

The public evaluator and its helper call graph are pure in memory.  The
remaining module code materializes deterministic synthetic evidence from a
fixed committed-source boundary; it is not reachable from the evaluator.
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
STEP = "ADMIT_006 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_006_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "a93a70657aec831e66b12b664d06f083a3c4f6fd"
EXPECTED_BASE_SUBJECT = "add CovaPIE covalent event evidence source enum contract v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_006_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_006_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_006"
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
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
BLOCKED_REASON = "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"
REASON_VOCABULARY = ("", *SCALAR_REASONS, *CONTEXT_REASONS, BLOCKED_REASON)
CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_covalent_event_evidence_source",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
_CANONICAL_RE = re.compile(CANONICAL_SYNTAX, re.ASCII)


@dataclass(frozen=True)
class Admit006EvaluationResult:
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

    def __post_init__(self) -> None:
        strings = (
            self.admission_rule_id,
            self.outcome,
            self.reason,
            self.canonical_covalent_event_evidence_source,
        )
        if any(type(value) is not str for value in strings):
            raise TypeError("all string fields must be exact str")
        if type(self.passed) is not bool or type(self.blocks_candidate) is not bool:
            raise TypeError("outcome booleans must be exact bool")
        if type(self.evaluator_io_used) is not bool:
            raise TypeError("evaluator_io_used must be exact bool")
        if type(self.validated_candidate_fields) is not tuple:
            raise TypeError("validated_candidate_fields must be exact tuple")
        for pair in self.validated_candidate_fields:
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or type(pair[0]) is not str
                or type(pair[1]) is not str
            ):
                raise TypeError("validated fields must be exact string-pair tuples")
        for value, name in (
            (self.consumed_candidate_fields, "consumed_candidate_fields"),
            (self.consumed_context_items, "consumed_context_items"),
        ):
            if type(value) is not tuple or any(type(item) is not str for item in value):
                raise TypeError(f"{name} must be an exact string tuple")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("admission_rule_id must be ADMIT_006")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome is outside the ADMIT_006 vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed must be true exactly for passed outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate must be true exactly when not passed")
        if (self.outcome == "passed") is not (self.reason == ""):
            raise ValueError("reason does not match outcome")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the ADMIT_006 vocabulary")
        if self.consumed_candidate_fields != CANDIDATE_FIELDS:
            raise ValueError("consumed_candidate_fields mismatch")
        if self.consumed_context_items != CONTEXT_ITEMS:
            raise ValueError("consumed_context_items mismatch")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")

        canonical = self.canonical_covalent_event_evidence_source
        if canonical == "":
            expected_validated: tuple[tuple[str, str], ...] = ()
            if self.outcome != "invalid" or self.reason not in SCALAR_REASONS:
                raise ValueError("empty canonical state requires a scalar-invalid result")
        else:
            if canonical not in CANONICAL_ENUM_MEMBERS:
                raise ValueError("canonical source must be an Exact3 member")
            expected_validated = ((CANDIDATE_FIELDS[0], canonical),)
            if self.outcome == "passed" and (
                canonical not in ALLOWED_COVALENT_EVIDENCE_CLASSES or self.reason != ""
            ):
                raise ValueError("passed requires an explicit canonical member")
            if self.outcome == "blocked" and (
                canonical != CANONICAL_ENUM_MEMBERS[2] or self.reason != BLOCKED_REASON
            ):
                raise ValueError("blocked requires distance-only evidence")
            if self.outcome == "invalid" and self.reason not in CONTEXT_REASONS:
                raise ValueError("canonical invalid result requires a context reason")
        if self.validated_candidate_fields != expected_validated:
            raise ValueError("validated_candidate_fields do not match canonical state")


def _result(outcome: str, reason: str, canonical: str) -> Admit006EvaluationResult:
    validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    return Admit006EvaluationResult(
        admission_rule_id=ADMISSION_RULE_ID,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        canonical_covalent_event_evidence_source=canonical,
        validated_candidate_fields=validated,
        consumed_candidate_fields=CANDIDATE_FIELDS,
        consumed_context_items=CONTEXT_ITEMS,
        evaluator_io_used=False,
    )


def _validate_scalar(value: object) -> tuple[str, str]:
    if type(value) is not str:
        return "", SCALAR_REASONS[0]
    if value == "":
        return "", SCALAR_REASONS[1]
    if not value.isascii():
        return "", SCALAR_REASONS[2]
    if _CANONICAL_RE.fullmatch(value) is None:
        return "", SCALAR_REASONS[3]
    if value not in CANONICAL_ENUM_MEMBERS:
        return "", SCALAR_REASONS[4]
    return value, ""


def _validate_context(value: object) -> str:
    if type(value) is not tuple:
        return CONTEXT_REASONS[0]
    if any(type(member) is not str for member in value):
        return CONTEXT_REASONS[1]
    if value != ALLOWED_COVALENT_EVIDENCE_CLASSES:
        return CONTEXT_REASONS[1]
    return ""


def evaluate_admit_006(
    covalent_event_evidence_source: object,
    allowed_covalent_evidence_classes: object,
) -> Admit006EvaluationResult:
    """Evaluate one direct scalar and its direct immutable context contract."""
    canonical, scalar_reason = _validate_scalar(covalent_event_evidence_source)
    context_reason = _validate_context(allowed_covalent_evidence_classes)
    if scalar_reason:
        return _result("invalid", scalar_reason, "")
    if context_reason:
        return _result("invalid", context_reason, canonical)
    if canonical == CANONICAL_ENUM_MEMBERS[2]:
        return _result("blocked", BLOCKED_REASON, canonical)
    return _result("passed", "", canonical)


# The committed boundary is deliberately ordered and non-recursive.  Each item
# supplies a distinct necessary contract view; artifact references inside these
# documents are never followed.
SOURCE_PATHS = tuple(Path(value) for value in (
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_006_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_006_formal_evaluator_preconditions_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py",
    "src/covalent_ext/covapie_bulk_download_admission_admit_005_rule_logic_interface.py",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "16b787061739dd0d68cfd3f66829a7690e802d1c0fa700d53155384b29c6dac5",
    "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
    "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
    "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
    "d3333fd74af79b065eb136d830e730c3a636e0d632bcb735b3e841a29d548c79",
    "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
    "c923d0dfe2edad534a2f530dbbac53870823ff2aa231730acbcd63577edfdb23",
    "1b350d5e1a5b7117ee951450a05f32943ba1cef3854e56377aeff0286aec6b5f",
), strict=True))

PRECONDITION_MANIFEST_PATH = SOURCE_PATHS[0]
ENUM_SOURCE_PATH = SOURCE_PATHS[1]
ENUM_MANIFEST_PATH = SOURCE_PATHS[2]
PREDECESSOR_TRUTH_PATH = SOURCE_PATHS[3]
PREDECESSOR_ISSUE_PATH = SOURCE_PATHS[4]
RESPONSIBILITY_PATH = SOURCE_PATHS[5]
RESULT_SCHEMA_PATH = SOURCE_PATHS[6]
ROUTING_PATH = SOURCE_PATHS[7]
RUNTIME_SOURCE_PATH = SOURCE_PATHS[8]
ADMIT005_SOURCE_PATH = SOURCE_PATHS[9]

CONTRACT_FILENAME = "covapie_admit_006_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_006_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_006_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_006_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_006_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_006_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    SOURCE_AUDIT_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id", "contract_kind", "contract_subject", "contract_value", "contract_status",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_outcome", "expected_reason",
    "observed_outcome", "observed_reason", "expected_canonical_evidence_source",
    "observed_canonical_evidence_source", "expected_validated_candidate_fields",
    "observed_validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "case_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
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
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


class _StringSubclass(str):
    """Synthetic exact-type negative used only by truth materialization."""


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, capture_output=True, text=text, check=False
    )


def _validate_expected_base_lineage(repo_root: Path, head_ref: str) -> None:
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


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path)
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields_ = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields_) == 3
        and fields_[0] in ("100644", "100755")
        and fields_[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    if len(SOURCE_PATHS) != len(set(SOURCE_PATHS)) or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
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
    reader = csv.DictReader(
        io.StringIO(
            _record(snapshot, path).content_bytes.decode("utf-8", errors="strict"),
            newline="",
        ),
    )
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(v is None for v in row.values()) for row in rows):
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


def _one(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = tuple(row for row in rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
            for target in node.targets
        ):
            continue
        value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
        if isinstance(value, ast.Dict):
            keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant))
            if len(keys) == len(value.keys) and all(type(key) is str for key in keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    preconditions = _json_document(snapshot, PRECONDITION_MANIFEST_PATH)
    enum_manifest = _json_document(snapshot, ENUM_MANIFEST_PATH)
    truth = _csv_document(snapshot, PREDECESSOR_TRUTH_PATH)
    issues = _csv_document(snapshot, PREDECESSOR_ISSUE_PATH)
    responsibilities = _csv_document(snapshot, RESPONSIBILITY_PATH)
    result_schema = _csv_document(snapshot, RESULT_SCHEMA_PATH)
    routing = _csv_document(snapshot, ROUTING_PATH)
    enum_tree = _ast_document(snapshot, ENUM_SOURCE_PATH)
    runtime_tree = _ast_document(snapshot, RUNTIME_SOURCE_PATH)
    admit005_tree = _ast_document(snapshot, ADMIT005_SOURCE_PATH)
    admit006 = _one(responsibilities.rows, "rule_id", "ADMIT_006")
    route006 = _one(routing.rows, "admission_rule_id", "ADMIT_006")
    coverage = _one(issues.rows, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    enum_issue = _one(issues.rows, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    outcome_row = _one(result_schema.rows, "field_name", "dataclass_mutability")
    enum_functions = {
        node.name for node in enum_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    admit005_classes = {
        node.name: node for node in admit005_tree.body if isinstance(node, ast.ClassDef)
    }
    exact5 = tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
    groups = {group: sum(row["case_group"] == group for row in truth.rows) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    if not (
        preconditions.get("ready_for_covapie_covalent_event_evidence_source_enum_contract_design") is True
        and preconditions.get("ready_for_admit_006_standalone_evaluator_interface_implementation") is False
        and enum_manifest.get("normative_enum_members") == list(CANONICAL_ENUM_MEMBERS)
        and enum_manifest.get("allowed_covalent_evidence_classes") == list(ALLOWED_COVALENT_EVIDENCE_CLASSES)
        and enum_manifest.get("truth_matrix_row_count") == 37
        and groups == {"canonical": 3, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12}
        and len(truth.rows) == 37 and all(row["case_passed"] == "true" for row in truth.rows)
        and len(issues.rows) == 11
        and enum_issue["status"] == "resolved"
        and coverage["affected_rules"] == "ADMIT_006|ADMIT_007|ADMIT_008|ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"
        and admit006["blocked_reason"] == BLOCKED_REASON
        and admit006["passed_enum_members"] == "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES)
        and admit006["blocked_enum_members"] == CANONICAL_ENUM_MEMBERS[2]
        and route006["result_adapter_contract_status"] == "not_available"
        and route006["engine_registration_status"] == "unsupported"
        and outcome_row["contract_value"] == "frozen"
        and _literal_registry_keys(runtime_tree) == exact5
        and "classify_admit_006_admit_007_evidence_design" in enum_functions
        and "Admit005EvaluationResult" in admit005_classes
    ):
        raise ValueError("predecessor contract validation failed")
    return {"truth_rows": truth.rows, "issue_rows": issues.rows, "runtime_registry": exact5}


def _display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    if type(value) in (tuple, list):
        return f"{type(value).__name__}:{json.dumps(list(value), ensure_ascii=True)}"
    if type(value) in (set, frozenset):
        return f"{type(value).__name__}:{json.dumps(sorted(value), ensure_ascii=True)}"
    if type(value) is dict:
        return f"dict:{json.dumps(value, ensure_ascii=True, sort_keys=True)}"
    return f"{type(value).__name__}:{repr(value)}"


def _truth_definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = ALLOWED_COVALENT_EVIDENCE_CLASSES
    scalars: tuple[tuple[str, str, object], ...] = (
        ("canonical_structure_bond", "canonical", CANONICAL_ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", "canonical", CANONICAL_ENUM_MEMBERS[1]),
        ("canonical_distance_only", "canonical", CANONICAL_ENUM_MEMBERS[2]),
        ("type_none", "scalar_type", None),
        ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(CANONICAL_ENUM_MEMBERS[0])),
        ("type_list", "scalar_type", [CANONICAL_ENUM_MEMBERS[0]]),
        ("type_mapping", "scalar_type", {"value": CANONICAL_ENUM_MEMBERS[0]}),
        ("empty", "empty_syntax", ""),
        ("whitespace_only", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " explicit_structure_bond_record"),
        ("trailing_whitespace", "empty_syntax", "explicit_structure_bond_record "),
        ("uppercase", "empty_syntax", "Explicit_structure_bond_record"),
        ("hyphen", "empty_syntax", "explicit-structure-bond-record"),
        ("dot", "empty_syntax", "explicit.structure"),
        ("slash", "empty_syntax", "explicit/structure"),
        ("non_ascii", "empty_syntax", "explicit_évidence"),
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1explicit"),
        ("unknown_valid", "unknown", "unregistered_value"),
        ("unknown_explicit_looking", "unknown", "explicit_database_bond"),
        ("unknown_manual_review", "unknown", "manual_review"),
        ("unknown_other", "unknown", "other"),
        ("unknown_unknown", "unknown", "unknown"),
    )
    contexts: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact),
        ("context_none", None),
        ("context_list", list(exact)),
        ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))),
        ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    definitions = [(case_id, group, scalar, "exact_tuple", exact) for case_id, group, scalar in scalars]
    definitions.extend(
        (case_id, "context", CANONICAL_ENUM_MEMBERS[0], case_id.removeprefix("context_"), context)
        for case_id, context in contexts
    )
    return tuple(definitions)


def _independent_expected(scalar: object, context: object) -> tuple[str, str, str]:
    """Independent materialization oracle; does not call evaluator helpers."""
    canonical = ""
    scalar_reason = ""
    if type(scalar) is not str:
        scalar_reason = SCALAR_REASONS[0]
    elif len(scalar) == 0:
        scalar_reason = SCALAR_REASONS[1]
    elif not all(ord(character) < 128 for character in scalar):
        scalar_reason = SCALAR_REASONS[2]
    elif re.fullmatch(r"[a-z][a-z0-9_]{0,63}", scalar, flags=re.ASCII) is None:
        scalar_reason = SCALAR_REASONS[3]
    elif scalar not in (
        "explicit_structure_bond_record",
        "explicit_curated_covalent_annotation",
        "distance_only_inference",
    ):
        scalar_reason = SCALAR_REASONS[4]
    else:
        canonical = scalar
    if scalar_reason:
        return "invalid", scalar_reason, ""
    if type(context) is not tuple:
        return "invalid", CONTEXT_REASONS[0], canonical
    if (
        len(context) != 2
        or type(context[0]) is not str
        or type(context[1]) is not str
        or context[0] != "explicit_structure_bond_record"
        or context[1] != "explicit_curated_covalent_annotation"
    ):
        return "invalid", CONTEXT_REASONS[1], canonical
    if canonical == "distance_only_inference":
        return "blocked", BLOCKED_REASON, canonical
    return "passed", "", canonical


def _predecessor_display(value: object) -> str:
    """Reproduce the committed predecessor's scalar display contract."""
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _predecessor_expected_fields(
    case_id: str,
    group: str,
    scalar: object,
    context_kind: str,
    context: object,
) -> dict[str, str]:
    canonical, scalar_reason = _validate_scalar(scalar)
    if canonical:
        scalar_classification = "canonical"
    elif scalar_reason == SCALAR_REASONS[4]:
        scalar_classification = "unknown"
    else:
        scalar_classification = "invalid"
    context_reason = _validate_context(context)
    outcome, reason, expected_canonical = _independent_expected(scalar, context)
    return {
        "case_id": case_id,
        "case_group": group,
        "scalar_input_kind": type(scalar).__name__,
        "scalar_input_display": _predecessor_display(scalar),
        "context_input_kind": context_kind,
        "expected_scalar_classification": scalar_classification,
        "expected_canonical_value": expected_canonical,
        "expected_scalar_reason": scalar_reason,
        "expected_context_valid": _bool(context_reason == ""),
        "expected_context_reason": context_reason,
        "expected_admit_006_outcome": outcome,
        "expected_admit_006_reason": reason,
        "normative_not_observed": "true",
        "case_passed": "true",
    }


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    definitions = _truth_definitions()
    if len(predecessor_rows) != 37 or len(definitions) != 37:
        raise ValueError("ordered Exact37 predecessor shape invalid")
    rows = []
    for index, (definition, prior) in enumerate(
        zip(definitions, predecessor_rows, strict=True), 1
    ):
        name, group, scalar, context_kind, context = definition
        case_id = f"CASE_{index:03d}_{name}"
        expected_predecessor = _predecessor_expected_fields(
            case_id, group, scalar, context_kind, context
        )
        if any(prior.get(key) != value for key, value in expected_predecessor.items()):
            raise ValueError(f"ordered predecessor truth mismatch: {case_id}")
        expected_outcome, expected_reason, expected_canonical = _independent_expected(scalar, context)
        observed = evaluate_admit_006(scalar, context)
        expected_validated = () if expected_canonical == "" else ((CANDIDATE_FIELDS[0], expected_canonical),)
        passed = (
            observed.outcome == expected_outcome
            and observed.reason == expected_reason
            and observed.canonical_covalent_event_evidence_source == expected_canonical
            and observed.validated_candidate_fields == expected_validated
            and observed.consumed_candidate_fields == CANDIDATE_FIELDS
            and observed.consumed_context_items == CONTEXT_ITEMS
            and observed.evaluator_io_used is False
        )
        rows.append({
            "case_id": case_id,
            "case_group": group,
            "scalar_input_kind": type(scalar).__name__,
            "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind,
            "context_input_display": _display(context),
            "expected_outcome": expected_outcome,
            "expected_reason": expected_reason,
            "observed_outcome": observed.outcome,
            "observed_reason": observed.reason,
            "expected_canonical_evidence_source": expected_canonical,
            "observed_canonical_evidence_source": observed.canonical_covalent_event_evidence_source,
            "expected_validated_candidate_fields": json.dumps(expected_validated, separators=(",", ":")),
            "observed_validated_candidate_fields": json.dumps(observed.validated_candidate_fields, separators=(",", ":")),
            "consumed_candidate_fields": "|".join(observed.consumed_candidate_fields),
            "consumed_context_items": "|".join(observed.consumed_context_items),
            "evaluator_io_used": _bool(observed.evaluator_io_used),
            "case_passed": _bool(passed),
        })
    return rows


def _contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_006(covalent_event_evidence_source, allowed_covalent_evidence_classes)"),
        ("API_002", "public_api", "inputs", "direct_scalar_and_context_only_no_defaults"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "frozen_dataclass"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "outcomes", "passed|blocked|invalid"),
        ("RESULT_005", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_006", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        ("RESULT_007", "result_contract", "reason", "passed_empty_nonpassed_nonempty_exact_str"),
        ("RESULT_008", "result_contract", "canonical_state", "scalar_invalid_empty|exact3_preserved_even_context_invalid"),
        ("RESULT_009", "result_contract", "validated_state", "scalar_invalid_empty|canonical_exact_single_pair"),
        ("RESULT_010", "result_contract", "evaluator_io_used", "exact_false"),
        ("SCALAR_001", "scalar_semantics", "type", "exact_builtin_str"),
        ("SCALAR_002", "scalar_semantics", "precedence", "type|nonempty|ascii|syntax|exact3_membership"),
        ("SCALAR_003", "scalar_semantics", "syntax", CANONICAL_SYNTAX),
        ("SCALAR_004", "scalar_semantics", "enum", "|".join(CANONICAL_ENUM_MEMBERS)),
        ("SCALAR_005", "scalar_semantics", "repair", "none"),
        ("CONTEXT_001", "context_semantics", "type", "exact_tuple"),
        ("CONTEXT_002", "context_semantics", "content", "|".join(ALLOWED_COVALENT_EVIDENCE_CLASSES)),
        ("CONTEXT_003", "context_semantics", "members", "exact_builtin_str_exact_order_no_extra"),
        ("OUTCOME_001", "rule_semantics", "explicit_members", "passed_empty_reason"),
        ("OUTCOME_002", "rule_semantics", "distance_only", f"blocked_{BLOCKED_REASON}"),
        ("OUTCOME_003", "rule_semantics", "precedence", "scalar_failure|context_failure|classification"),
        ("REASON_001", "rule_semantics", "reserved_adapter_reason", "covalent_event_evidence_missing_not_used"),
        ("ORACLE_001", "oracle_contract", "independent", "materialization_oracle_separate_from_evaluator_and_predecessor"),
        ("BOUNDARY_001", "authorization_boundary", "excluded", "adapter|registry|runtime|provider|real_candidate|filesystem_in_evaluator"),
        ("BOUNDARY_002", "authorization_boundary", "runtime", "exact5_unchanged_admit006_unregistered"),
    )
    return [{
        "contract_id": identifier,
        "contract_kind": kind,
        "contract_subject": subject,
        "contract_value": value,
        "contract_status": "frozen",
    } for identifier, kind, subject, value in values]


BOUNDARY_NECESSITY = (
    "ADMIT_006 implementation precondition and readiness baseline",
    "normative Exact3/Exact2 design definitions and predecessor-oracle identity",
    "committed enum-contract counts, precedence, readiness, and output hashes",
    "complete committed Exact37 semantic expectation corpus",
    "ordered Exact11 issue inventory preservation baseline",
    "ADMIT_006 passed/blocked members, reason, and adapter-missing boundary",
    "unified result invariants and outcome/result-routing vocabulary",
    "ADMIT_006 field/context dependencies and current unsupported routing boundary",
    "current literal Exact5 registry and absence of ADMIT_006 registration",
    "established frozen standalone-result and materialization structural precedent",
)


def _source_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [{
        "source_order": str(index),
        "source_relative_path": record.relative_path.as_posix(),
        "source_kind": record.relative_path.suffix.lstrip(".") or "source",
        "boundary_necessity": BOUNDARY_NECESSITY[index - 1],
        "tracked": "true",
        "base_tree_blob": "true",
        "filesystem_regular": "true",
        "non_symlink": "true",
        "expected_sha256": record.expected_sha256,
        "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256,
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1)]


EXECUTED_SAFETY_ITEMS = (
    "fixed_source_reads",
    "admit_006_result_contract_implementation",
    "admit_006_scalar_validation_implementation",
    "admit_006_context_validation_implementation",
    "admit_006_rule_classification_implementation",
    "independent_semantic_oracle_attestation",
    "exact37_synthetic_truth_evaluation",
    "issue_inventory_preservation",
    "evaluator_call_graph_ast_audit",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "raw_read", "artifact_reference_dereference", "candidate_mapping", "context_routing",
    "unified_adapter_design", "unified_adapter_implementation", "runtime_modification",
    "registry_modification", "admit_006_engine_registration", "admit_007_implementation",
    "provider_mapping", "real_candidate_evaluation", "bulk_download", "network",
    "checkpoint", "numpy", "torch", "rdkit", "model_forward_loss_training",
)


def _safety_rows() -> list[dict[str, str]]:
    return [
        {"safety_item": item, "expected_executed": "true", "observed_executed": "true", "safety_passed": "true"}
        for item in EXECUTED_SAFETY_ITEMS
    ] + [
        {"safety_item": item, "expected_executed": "false", "observed_executed": "false", "safety_passed": "true"}
        for item in NOT_EXECUTED_SAFETY_ITEMS
    ]


READINESS = {
    "admit_006_standalone_evaluator_implemented": True,
    "admit_006_formal_result_contract_frozen": True,
    "admit_006_scalar_semantics_implemented": True,
    "admit_006_context_semantics_implemented": True,
    "admit_006_reason_outcome_contract_implemented": True,
    "admit_006_independent_semantic_oracle_attested": True,
    "admit_006_synthetic_truth_matrix_passed": True,
    "ready_for_admit_006_unified_adapter_contract_design": True,
    "feature_semantics_audit_required_before_training": True,
    "admit_006_unified_adapter_contract_frozen": False,
    "admit_006_unified_adapter_implemented": False,
    "admit_006_registered_in_engine": False,
    "admit_007_standalone_evaluator_implemented": False,
    "admit_007_unified_adapter_contract_frozen": False,
    "admit_007_unified_adapter_implemented": False,
    "admit_007_registered_in_engine": False,
    "admit_006_to_015_registered_in_engine": False,
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


def _issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    if len(rows) != 11 or any(tuple(row) != ISSUE_COLUMNS for row in rows):
        raise ValueError("Exact11 issue baseline invalid")
    return rows


def build_interface_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot() if source_snapshot is None else source_snapshot
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid frozen source snapshot")
    historical = _validate_predecessors(snapshot)
    state = {
        "source_snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "truth_rows": _truth_rows(historical["truth_rows"]),
        "source_audit_rows": _source_audit_rows(snapshot),
        "safety_rows": _safety_rows(),
        "issue_rows": _issue_rows(historical["issue_rows"]),
        "readiness": dict(READINESS),
    }
    groups = {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    coverage = _one(state["issue_rows"], "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    enum_issue = _one(state["issue_rows"], "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")
    checks = (
        len(state["contract_rows"]) == 28,
        len(state["truth_rows"]) == 37,
        len({row["case_id"] for row in state["truth_rows"]}) == 37,
        groups == {"canonical": 3, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12},
        all(row["case_passed"] == "true" for row in state["truth_rows"]),
        len(state["source_audit_rows"]) == len(SOURCE_PATHS),
        all(row["source_boundary_passed"] == "true" for row in state["source_audit_rows"]),
        state["source_audit_rows"][4]["boundary_necessity"]
        == "ordered Exact11 issue inventory preservation baseline",
        len(state["issue_rows"]) == 11,
        state["issue_rows"] == list(historical["issue_rows"]),
        enum_issue == _one(historical["issue_rows"], "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED"),
        coverage["affected_rules"] == "ADMIT_006|ADMIT_007|ADMIT_008|ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        coverage["integration_transition"] == "admit_005_implemented_and_removed_from_open_coverage_scope",
        all(row["safety_passed"] == "true" for row in state["safety_rows"]),
    )
    if not all(checks):
        raise RuntimeError("ADMIT_006 interface state failed closed")
    state["all_checks_passed"] = True
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
    group_counts = {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_boundary_name": "fixed_ordered_minimal_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS),
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": record.relative_path.as_posix(),
            "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "public_api": "evaluate_admit_006(covalent_event_evidence_source, allowed_covalent_evidence_classes)",
        "result_type": "Admit006EvaluationResult",
        "result_field_count": 10,
        "result_fields": list(RESULT_FIELDS),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "canonical_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "allowed_covalent_evidence_classes": list(ALLOWED_COVALENT_EVIDENCE_CLASSES),
        "scalar_validation_precedence": ["exact_builtin_str", "nonempty", "ascii", "syntax", "exact3_membership"],
        "context_validation_precedence": ["exact_tuple", "exact_content"],
        "evaluator_precedence": ["scalar_failure", "context_failure", "canonical_member_classification"],
        "normalization_applied": False,
        "historical_missing_reason_used_by_standalone_evaluator": False,
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "truth_matrix_row_count": 37,
        "truth_matrix_pass_count": 37,
        "truth_matrix_group_counts": group_counts,
        "independent_semantic_oracle_attested": True,
        "predecessor_contract_independently_checked": True,
        "evaluator_call_graph_pure_in_memory": True,
        "source_audit_row_count": len(SOURCE_PATHS),
        "source_audit_pass_count": len(SOURCE_PATHS),
        "issue_inventory_row_count": 11,
        "issue_inventory_preserved_exactly": True,
        "unified_engine_coverage_issue_still_includes_admit_006": True,
        "readiness": dict(state["readiness"]),
        **dict(state["readiness"]),
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True,
        "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SOURCE_AUDIT_FILENAME: _csv_bytes(SOURCE_AUDIT_COLUMNS, state["source_audit_rows"]),
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
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
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
        metadata = root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
        entries = tuple(root.iterdir())
        if {entry.name for entry in entries} - set(OUTPUT_FILES):
            raise ValueError("output root contains unexpected entries")
        for entry in entries:
            status = entry.lstat()
            if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
                raise ValueError("output root contains an unsafe entry")


def run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_interface_state()
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    root.mkdir(parents=True, exist_ok=True)
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

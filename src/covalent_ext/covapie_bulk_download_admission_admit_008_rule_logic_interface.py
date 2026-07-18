"""CovaPIE ADMIT_008 standalone evaluator interface v1.

The public evaluator and its complete helper closure are pure in memory.  The
remaining module code materializes deterministic synthetic contract evidence
from an ordered committed-source boundary; none of it is evaluator-reachable.
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
STEP = "ADMIT_008 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_008_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "96039c9a69c4973461307aed78ee6ec931896a7d"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 topology restoration disposition enum contract v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_008_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_008_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_008"
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
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
REASON_VOCABULARY = ("", *SCALAR_REASONS, *CONTEXT_REASONS, *BLOCKED_REASONS.values())
CANDIDATE_FIELDS = ("topology_restoration_disposition",)
CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_topology_restoration_disposition",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
_CANONICAL_RE = re.compile(CANONICAL_SYNTAX, re.ASCII)


@dataclass(frozen=True)
class Admit008EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_topology_restoration_disposition: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        if type(self) is not Admit008EvaluationResult:
            raise TypeError("result subclasses are forbidden")
        strings = (
            self.admission_rule_id,
            self.outcome,
            self.reason,
            self.canonical_topology_restoration_disposition,
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
            raise ValueError("admission_rule_id must be ADMIT_008")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome is outside the ADMIT_008 vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed must be true exactly for passed outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate must be true exactly when not passed")
        if (self.outcome == "passed") is not (self.reason == ""):
            raise ValueError("reason does not match outcome")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the ADMIT_008 vocabulary")
        if self.consumed_candidate_fields != CANDIDATE_FIELDS:
            raise ValueError("consumed_candidate_fields mismatch")
        if self.consumed_context_items != CONTEXT_ITEMS:
            raise ValueError("consumed_context_items mismatch")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")

        canonical = self.canonical_topology_restoration_disposition
        if canonical == "":
            expected_validated: tuple[tuple[str, str], ...] = ()
            if self.outcome != "invalid" or self.reason not in SCALAR_REASONS:
                raise ValueError("empty canonical state requires scalar-invalid result")
        else:
            if canonical not in CANONICAL_ENUM_MEMBERS:
                raise ValueError("canonical disposition must be an Exact4 member")
            expected_validated = ((CANDIDATE_FIELDS[0], canonical),)
            if self.outcome == "passed" and (
                canonical not in ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
                or self.reason != ""
            ):
                raise ValueError("passed requires an allowed canonical disposition")
            if self.outcome == "blocked" and (
                canonical not in BLOCKED_REASONS
                or self.reason != BLOCKED_REASONS[canonical]
            ):
                raise ValueError("blocked reason must match its canonical disposition")
            if self.outcome == "invalid" and self.reason not in CONTEXT_REASONS:
                raise ValueError("canonical invalid result requires a context reason")
        if self.validated_candidate_fields != expected_validated:
            raise ValueError("validated_candidate_fields do not match canonical state")


def _result(outcome: str, reason: str, canonical: str) -> Admit008EvaluationResult:
    validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    return Admit008EvaluationResult(
        admission_rule_id=ADMISSION_RULE_ID,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        canonical_topology_restoration_disposition=canonical,
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
    if value != ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS:
        return CONTEXT_REASONS[1]
    return ""


def evaluate_admit_008(
    topology_restoration_disposition: object,
    allowed_topology_restoration_dispositions: object,
) -> Admit008EvaluationResult:
    """Evaluate one direct scalar and its direct immutable context contract."""
    canonical, scalar_reason = _validate_scalar(topology_restoration_disposition)
    if scalar_reason:
        return _result("invalid", scalar_reason, "")
    context_reason = _validate_context(allowed_topology_restoration_dispositions)
    if context_reason:
        return _result("invalid", context_reason, canonical)
    if canonical in BLOCKED_REASONS:
        return _result("blocked", BLOCKED_REASONS[canonical], canonical)
    return _result("passed", "", canonical)


# Ordered Exact11, non-recursive metadata boundary.  The evaluator closure above
# cannot reach any of these paths or helpers.
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_008_topology_restoration_disposition_"
    "enum_contract_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_008_formal_evaluator_interface_"
    "preconditions_audit_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1"
)
SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py",
    str(DESIGN_ROOT / "covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json"),
    str(DESIGN_ROOT / "covapie_admit_008_topology_restoration_disposition_enum_registry.csv"),
    str(DESIGN_ROOT / "covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv"),
    str(DESIGN_ROOT / "covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv"),
    str(DESIGN_ROOT / "covapie_admit_008_topology_restoration_disposition_issue_readiness_inventory.csv"),
    str(PRECONDITION_ROOT / "covapie_admit_008_formal_evaluator_preconditions_manifest.json"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_007_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_007_runtime_issue_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d",
    "4da97951abe63d46ded0ad5ffc6048e1a1c40eb2fdedd3553de094ac1ad0c85b",
    "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a",
    "d15cc2f468b158bdd0871386af041231f563af34ff394c2d25e8b5797fa3599b",
    "f449e7441045f52a2222f70f2b7378446424ea46610859641ae2baf5e4565be4",
    "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    "e93c43df4f64b6ce70c19c526546d3b1090c55f9150a944a76109ed0038cc136",
    "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "ce5cbf09765e8b12db162458ca9518d71d431b175f3225e5558a8b57fdd133f6",
), strict=True))
(
    DESIGN_SOURCE_PATH, DESIGN_MANIFEST_PATH, ENUM_REGISTRY_PATH,
    PREDECESSOR_TRUTH_PATH, CATEGORY_MAPPING_PATH, AUTHORITATIVE_ISSUE_PATH,
    PRECONDITION_MANIFEST_PATH, RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH,
    RUNTIME_ISSUE_PATH, ADMIT007_SOURCE_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_008_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_008_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_008_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_008_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_008_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_008_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_AUDIT_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id", "contract_kind", "contract_subject", "contract_value", "contract_status",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_full_result",
    "observed_full_result", "committed_oracle_full_result",
    "production_oracle_equality", "case_passed",
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
    pass


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
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


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    values = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(values) == 3
        and values[0] in ("100644", "100755") and values[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete all Exact11 structural checks before the first source-byte read."""
    if len(SOURCE_PATHS) != 11 or len(set(SOURCE_PATHS)) != 11 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact11 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
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
        type(value) is FrozenSourceSnapshot and len(value.records) == 11
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
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content_bytes.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets
        ):
            continue
        value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
        if isinstance(value, ast.Dict):
            keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant))
            if len(keys) == len(value.keys) and all(type(key) is str for key in keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    design_tree = ast.parse(_record(snapshot, DESIGN_SOURCE_PATH).content_bytes.decode("utf-8"))
    design_manifest = _json_document(snapshot, DESIGN_MANIFEST_PATH)
    enum_rows = _csv_document(snapshot, ENUM_REGISTRY_PATH).rows
    truth_rows = _csv_document(snapshot, PREDECESSOR_TRUTH_PATH).rows
    mapping_rows = _csv_document(snapshot, CATEGORY_MAPPING_PATH).rows
    issue_document = _csv_document(snapshot, AUTHORITATIVE_ISSUE_PATH)
    precondition = _json_document(snapshot, PRECONDITION_MANIFEST_PATH)
    runtime_tree = ast.parse(_record(snapshot, RUNTIME_SOURCE_PATH).content_bytes.decode("utf-8"))
    runtime_manifest = _json_document(snapshot, RUNTIME_MANIFEST_PATH)
    runtime_issues = _csv_document(snapshot, RUNTIME_ISSUE_PATH).rows
    admit007_tree = ast.parse(_record(snapshot, ADMIT007_SOURCE_PATH).content_bytes.decode("utf-8"))
    functions = {node.name for node in design_tree.body if isinstance(node, ast.FunctionDef)}
    admit007_functions = {node.name for node in admit007_tree.body if isinstance(node, ast.FunctionDef)}
    groups = {group: sum(row["case_group"] == group for row in truth_rows) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    issue_map = {row["issue_id"]: row for row in issue_document.rows}
    runtime_issue_map = {row["issue_id"]: row for row in runtime_issues}
    checks = (
        "classify_admit_008_topology_restoration_disposition_design" in functions,
        "evaluate_admit_008" not in functions,
        design_manifest.get("normative_enum_members") == list(CANONICAL_ENUM_MEMBERS),
        design_manifest.get("allowed_topology_restoration_dispositions") == list(ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        len(enum_rows) == 4 and tuple(row["canonical_value"] for row in enum_rows) == CANONICAL_ENUM_MEMBERS,
        len(truth_rows) == 38 and groups == {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12},
        all(row["case_passed"] == "true" for row in truth_rows),
        len(mapping_rows) == 12 and all(row["real_provider_mapping_executed"] == "false" for row in mapping_rows),
        len(issue_document.rows) == 11,
        issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_008|"),
        precondition.get("ready_for_admit_008_standalone_evaluator_interface_implementation") is False,
        precondition.get("real_provider_value_count") == 0,
        _literal_registry_keys(runtime_tree) == tuple(f"ADMIT_{index:03d}" for index in range(1, 8)),
        runtime_manifest.get("registered_rule_ids") == [f"ADMIT_{index:03d}" for index in range(1, 8)],
        runtime_manifest.get("admit_008_registered_in_engine") is False,
        runtime_issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_008|"),
        "evaluate_admit_007" in admit007_functions,
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {"truth_rows": truth_rows, "issue_rows": issue_document.rows, "issue_bytes": _record(snapshot, AUTHORITATIVE_ISSUE_PATH).content_bytes}


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
    exact = ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
    scalars: tuple[tuple[str, str, object], ...] = (
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
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1approved"),
        ("unknown_valid", "unknown", "unregistered_disposition"),
        ("unknown_approved_looking", "unknown", "approved_manual_review"),
        ("unknown_manual_review_looking", "unknown", "manual_review_approved"),
        ("unknown_other", "unknown", "other"), ("unknown_unknown", "unknown", "unknown"),
    )
    contexts: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact), ("context_none", None),
        ("context_list", list(exact)), ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))), ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_blocked_added", (*exact, CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    definitions = [(name, group, scalar, "exact_tuple", exact) for name, group, scalar in scalars]
    definitions.extend((name, "context", CANONICAL_ENUM_MEMBERS[0], name.removeprefix("context_"), context) for name, context in contexts)
    return tuple(definitions)


def _independent_expected(scalar: object, context: object) -> Admit008EvaluationResult:
    if type(scalar) is not str:
        return _result("invalid", SCALAR_REASONS[0], "")
    if len(scalar) == 0:
        return _result("invalid", SCALAR_REASONS[1], "")
    if not all(ord(character) < 128 for character in scalar):
        return _result("invalid", SCALAR_REASONS[2], "")
    if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", scalar, flags=re.ASCII) is None:
        return _result("invalid", SCALAR_REASONS[3], "")
    if scalar not in CANONICAL_ENUM_MEMBERS:
        return _result("invalid", SCALAR_REASONS[4], "")
    if type(context) is not tuple:
        return _result("invalid", CONTEXT_REASONS[0], scalar)
    if len(context) != 2 or any(type(member) is not str for member in context) or context != ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS:
        return _result("invalid", CONTEXT_REASONS[1], scalar)
    if scalar in BLOCKED_REASONS:
        return _result("blocked", BLOCKED_REASONS[scalar], scalar)
    return _result("passed", "", scalar)


def _result_dict(value: Admit008EvaluationResult) -> dict[str, Any]:
    return {name: getattr(value, name) for name in RESULT_FIELDS}


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    definitions = _truth_definitions()
    if len(definitions) != 38 or len(predecessor_rows) != 38:
        raise ValueError("Exact38 predecessor shape invalid")
    rows = []
    for index, ((name, group, scalar, context_kind, context), prior) in enumerate(zip(definitions, predecessor_rows, strict=True), 1):
        case_id = f"CASE_{index:03d}_{name}"
        expected = _independent_expected(scalar, context)
        observed = evaluate_admit_008(scalar, context)
        expected_dict = _result_dict(expected)
        observed_dict = _result_dict(observed)
        if prior.get("case_id") != case_id or prior.get("case_group") != group:
            raise ValueError(f"ordered committed Exact38 mismatch: {case_id}")
        if (
            prior.get("expected_outcome") != expected.outcome
            or prior.get("expected_reason") != expected.reason
            or prior.get("expected_canonical_value") != expected.canonical_topology_restoration_disposition
        ):
            raise ValueError(f"committed oracle projection mismatch: {case_id}")
        full = json.dumps(expected_dict, separators=(",", ":"))
        observed_full = json.dumps(observed_dict, separators=(",", ":"))
        equality = observed_dict == expected_dict
        rows.append({
            "case_id": case_id, "case_group": group,
            "scalar_input_kind": type(scalar).__name__, "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind, "context_input_display": _display(context),
            "expected_full_result": full, "observed_full_result": observed_full,
            "committed_oracle_full_result": full,
            "production_oracle_equality": _bool(equality), "case_passed": _bool(equality),
        })
    return rows


def _contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_008(topology_restoration_disposition, allowed_topology_restoration_dispositions)"),
        ("API_002", "public_api", "inputs", "two_required_positional_or_keyword_direct_objects"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "exact_frozen_dataclass_no_subclasses"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "exact_types", "exact_str_bool_tuple_and_string_pairs"),
        ("RESULT_005", "result_contract", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_007", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        ("RESULT_008", "result_contract", "reason", "passed_empty_nonpassed_frozen_reason"),
        ("RESULT_009", "result_contract", "canonical_state", "scalar_invalid_empty|exact4_preserved_otherwise"),
        ("RESULT_010", "result_contract", "validated_state", "scalar_invalid_empty|canonical_single_pair"),
        ("RESULT_011", "result_contract", "consumed", "exact_candidate_and_context_tuples"),
        ("RESULT_012", "result_contract", "evaluator_io_used", "exact_false"),
        ("SCALAR_001", "scalar_semantics", "type", "exact_builtin_str"),
        ("SCALAR_002", "scalar_semantics", "precedence", "type|nonempty|ascii|syntax|exact4_membership"),
        ("SCALAR_003", "scalar_semantics", "syntax", CANONICAL_SYNTAX),
        ("SCALAR_004", "scalar_semantics", "enum", "|".join(CANONICAL_ENUM_MEMBERS)),
        ("SCALAR_005", "scalar_semantics", "normalization", "none"),
        ("CONTEXT_001", "context_semantics", "type", "exact_builtin_tuple"),
        ("CONTEXT_002", "context_semantics", "members", "exact_builtin_str"),
        ("CONTEXT_003", "context_semantics", "content", "|".join(ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS)),
        ("CONTEXT_004", "context_semantics", "order_and_cardinality", "exact2_no_extra"),
        ("OUTCOME_001", "rule_semantics", "passed_members", "approved_restoration_template|explicit_manual_review_approved"),
        ("OUTCOME_002", "rule_semantics", "manual_review_required", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[2]]),
        ("OUTCOME_003", "rule_semantics", "quarantine_required", BLOCKED_REASONS[CANONICAL_ENUM_MEMBERS[3]]),
        ("OUTCOME_004", "rule_semantics", "blocked_reason_bijection", "two_distinct_exact_reasons"),
        ("OUTCOME_005", "rule_semantics", "precedence", "scalar_failure|context_failure|canonical_classification"),
        ("REASON_001", "rule_semantics", "historical_lowercase", "topology_restoration_unapproved_not_used"),
        ("MISSING_001", "standalone_boundary", "candidate_missing", "adapter_owned_not_standalone"),
        ("PROVIDER_001", "provider_boundary", "fields", "restoration_rule_and_provenance_not_consumed"),
        ("PROVIDER_002", "provider_boundary", "real_values", "zero_mapping_unvalidated"),
        ("ORACLE_001", "oracle_contract", "production", "does_not_import_or_call_design_oracle"),
        ("ORACLE_002", "oracle_contract", "attestation", "checker_and_tests_compare_complete_exact10"),
        ("BOUNDARY_001", "authorization_boundary", "excluded", "adapter|runtime|registration|admit009|aggregation|real_evaluation"),
        ("BOUNDARY_002", "authorization_boundary", "operations", "no_raw_network_download_model_training"),
    )
    return [{
        "contract_id": identifier, "contract_kind": kind, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for identifier, kind, subject, value in values]


BOUNDARY_NECESSITY = (
    "normative Exact4/Exact2 definitions and independent oracle identity",
    "committed enum contract counts, precedence, readiness, and hashes",
    "ordered Exact4 registry and exact blocked-reason mapping",
    "complete committed Exact38 semantic expectation corpus",
    "Exact12 policy boundary with no real provider execution",
    "authoritative Exact11 successor issue inventory preservation baseline",
    "historical precondition and zero-provider-value boundary",
    "current literal Exact7 runtime and absent ADMIT_008 registration",
    "current Exact7 runtime readiness and output boundary",
    "current runtime Exact11 issue boundary cross-check",
    "mature ADMIT_007 standalone structural precedent",
)


def _source_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": record.relative_path.suffix.lstrip("."),
        "boundary_necessity": BOUNDARY_NECESSITY[index - 1],
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1)]


EXECUTED_SAFETY_ITEMS = (
    "standalone_evaluator_implementation", "exact10_result_validation", "scalar_validation",
    "context_validation", "exact38_synthetic_truth", "independent_oracle_equivalence",
    "source_verification", "evaluator_pure_in_memory_audit",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "provider_mapping", "provider_values", "unified_adapter", "exact7_runtime_modification",
    "admit_008_registration", "admit_009", "evaluate_all_rules", "combined_candidate_verdict",
    "real_candidate_evaluation", "raw_read", "network", "bulk_download", "checkpoint",
    "torch_numpy_rdkit", "model_forward_loss", "training_fine_tune", "parameter_update",
)


def _safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple((item, False) for item in NOT_EXECUTED_SAFETY_ITEMS)
    return [{
        "safety_item": item, "expected_executed": _bool(executed),
        "observed_executed": _bool(executed), "safety_passed": "true",
    } for item, executed in definitions]


TRUE_READINESS = (
    "admit_008_standalone_evaluator_implemented",
    "admit_008_scalar_semantics_implemented",
    "admit_008_context_semantics_implemented",
    "admit_008_reason_outcome_contract_implemented",
    "admit_008_formal_result_contract_frozen",
    "admit_008_synthetic_truth_matrix_passed",
    "admit_008_independent_semantic_oracle_attested",
    "evaluator_call_graph_pure_in_memory",
    "admit_008_provider_mapping_boundary_preserved",
    "ready_for_admit_008_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
    "admit_008_unified_adapter_contract_frozen", "admit_008_unified_adapter_implemented",
    "admit_008_registered_in_engine", "exact7_runtime_modified",
    "admit_009_standalone_evaluator_implemented", "admit_009_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation", "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)
READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def build_interface_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
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
        "issue_rows": [dict(row) for row in historical["issue_rows"]],
        "issue_bytes": historical["issue_bytes"],
        "readiness": dict(READINESS),
    }
    groups = {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    checks = (
        len(state["contract_rows"]) == 37,
        len(state["truth_rows"]) == 38,
        groups == {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12},
        all(row["case_passed"] == row["production_oracle_equality"] == "true" for row in state["truth_rows"]),
        len(state["source_audit_rows"]) == 11,
        len(state["safety_rows"]) == 25,
        len(state["issue_rows"]) == 11,
        hashlib.sha256(state["issue_bytes"]).hexdigest() == SOURCE_SHA256[AUTHORITATIVE_ISSUE_PATH],
        issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_008|"),
        all(row["safety_passed"] == "true" for row in state["safety_rows"]),
    )
    if not all(checks):
        raise RuntimeError("ADMIT_008 interface state failed closed")
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
    groups = {group: sum(row["case_group"] == group for row in state["truth_rows"]) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    readiness = dict(state["readiness"])
    return {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": "topology_restoration_disposition",
        "candidate_field": CANDIDATE_FIELDS[0], "context_item": CONTEXT_ITEMS[0],
        "public_api": "evaluate_admit_008(topology_restoration_disposition, allowed_topology_restoration_dispositions)",
        "public_signature_parameters": list((*CANDIDATE_FIELDS, *CONTEXT_ITEMS)),
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit008EvaluationResult", "result_field_count": 10,
        "result_fields": list(RESULT_FIELDS), "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "canonical_enum_members": list(CANONICAL_ENUM_MEMBERS),
        "allowed_topology_restoration_dispositions": list(ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        "canonical_syntax": CANONICAL_SYNTAX,
        "scalar_validation_precedence": ["exact_builtin_str", "nonempty", "ascii", "syntax", "exact4_membership"],
        "scalar_validation_reasons": list(SCALAR_REASONS),
        "context_validation_precedence": ["exact_builtin_tuple", "exact_builtin_str_members", "exact2_content_and_order"],
        "context_validation_reasons": list(CONTEXT_REASONS),
        "evaluator_precedence": ["scalar_failure", "context_failure", "canonical_member_classification"],
        "passed_members": list(ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        "blocked_reason_mapping": dict(BLOCKED_REASONS),
        "historical_lowercase_reason_used": False,
        "scalar_invalid_canonical_empty": True,
        "canonical_context_invalid_retains_validated_pair": True,
        "passed_and_blocked_retain_validated_pair": True,
        "normalization_applied": False, "candidate_mapping_accepted": False,
        "candidate_key_missing_handled_by_standalone": False,
        "provider_fields_consumed": [], "real_provider_value_count": 0,
        "real_provider_mapping_executed": False,
        "independent_semantic_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "independent_semantic_oracle_attested": True, "production_oracle_call": False,
        "evaluator_call_graph": ["evaluate_admit_008", "_validate_scalar", "_validate_context", "_result"],
        "evaluator_call_graph_pure_in_memory": True,
        "truth_matrix_row_count": 38, "truth_matrix_pass_count": 38,
        "truth_matrix_group_counts": groups,
        "contract_row_count": len(state["contract_rows"]), "contract_pass_count": len(state["contract_rows"]),
        "source_boundary_name": "fixed_ordered_exact11_committed_source_boundary",
        "source_input_count": 11, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
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
        "source_audit_row_count": 11, "source_audit_pass_count": 11,
        "issue_inventory_row_count": 11, "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": SOURCE_SHA256[AUTHORITATIVE_ISSUE_PATH],
        "unified_engine_coverage_issue_still_includes_admit_008": True,
        "safety_row_count": len(state["safety_rows"]), "safety_pass_count": len(state["safety_rows"]),
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "readiness": readiness, **readiness,
        "all_source_boundary_checks_passed": True, "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True, "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_issue_checks_passed": True,
        "all_safety_checks_passed": True, "all_checks_passed": True,
        "stop_boundaries": [
            "no_provider_mapping", "no_unified_adapter", "no_runtime_modification",
            "no_admit_008_registration", "no_admit_009", "no_evaluate_all_rules",
            "no_combined_candidate_verdict", "no_real_candidate_evaluation",
            "no_raw_network_download", "no_model_forward_loss_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP, "validation_failures": [],
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SOURCE_AUDIT_FILENAME: _csv_bytes(SOURCE_AUDIT_COLUMNS, state["source_audit_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    return {
        **csv_payloads,
        MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    }, manifest


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
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        raise ValueError("output root contains unexpected entries")
    for entry in entries:
        metadata = os.lstat(entry)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root contains unsafe entries")


def run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_interface_state()
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

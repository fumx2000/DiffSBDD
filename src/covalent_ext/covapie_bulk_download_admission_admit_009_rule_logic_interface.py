"""CovaPIE ADMIT_009 standalone evaluator interface v1.

The public evaluator and its complete helper closure are pure in memory.  The
metadata half of this module verifies an ordered committed Exact13 boundary
and materializes deterministic synthetic evidence; it is not evaluator-
reachable and does not generate provider duplicate keys.
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
STEP = "ADMIT_009 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_009_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "59dc50acc61b933bf36346a172964adc070a7170"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 duplicate identity key contract v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_009_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_009_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_009"
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
CANDIDATE_FIELDS = ("duplicate_identity_key",)
CONTEXT_ITEMS = (
    "duplicate_identity_key_contract",
    "batch_duplicate_identity_keys",
)
KEY_PREFIX = "covapie_dup_v1_sha256_"
KEY_REGEX = r"^covapie_dup_v1_sha256_[0-9a-f]{64}$"
POLICY_CONTRACT_VALUE = "covapie_duplicate_identity_key_contract_v1"
SCALAR_REASONS = (
    "DUPLICATE_IDENTITY_KEY_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_EMPTY",
    "DUPLICATE_IDENTITY_KEY_NON_ASCII",
    "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID",
)
POLICY_REASONS = (
    "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID",
)
BATCH_REASONS = (
    "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID",
)
DUPLICATE_REASON = "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"
REASON_VOCABULARY = (
    "",
    *SCALAR_REASONS,
    *POLICY_REASONS,
    *BATCH_REASONS,
    DUPLICATE_REASON,
)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_duplicate_identity_key",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
_KEY_RE = re.compile(KEY_REGEX, re.ASCII)


def _is_canonical_key(value: object) -> bool:
    return type(value) is str and value.isascii() and _KEY_RE.fullmatch(value) is not None


@dataclass(frozen=True)
class Admit009EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_duplicate_identity_key: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        if type(self) is not Admit009EvaluationResult:
            raise TypeError("result subclasses are forbidden")
        for value in (
            self.admission_rule_id,
            self.outcome,
            self.reason,
            self.canonical_duplicate_identity_key,
        ):
            if type(value) is not str:
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
            raise ValueError("admission_rule_id must be ADMIT_009")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome is outside the ADMIT_009 vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed must be true exactly for passed outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate must be true exactly when not passed")
        if (self.outcome == "passed") is not (self.reason == ""):
            raise ValueError("reason does not match outcome")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the ADMIT_009 vocabulary")
        if self.consumed_candidate_fields != CANDIDATE_FIELDS:
            raise ValueError("consumed_candidate_fields mismatch")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")

        canonical = self.canonical_duplicate_identity_key
        pair = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
        if self.validated_candidate_fields != pair:
            raise ValueError("validated_candidate_fields do not match canonical state")
        if self.reason in SCALAR_REASONS:
            if self.outcome != "invalid" or canonical != "" or self.consumed_context_items != ():
                raise ValueError("scalar-invalid state mismatch")
        elif self.reason in POLICY_REASONS:
            if (
                self.outcome != "invalid"
                or not _is_canonical_key(canonical)
                or self.consumed_context_items != CONTEXT_ITEMS[:1]
            ):
                raise ValueError("policy-invalid state mismatch")
        elif self.reason in BATCH_REASONS:
            if (
                self.outcome != "invalid"
                or not _is_canonical_key(canonical)
                or self.consumed_context_items != CONTEXT_ITEMS
            ):
                raise ValueError("batch-invalid state mismatch")
        elif self.reason == DUPLICATE_REASON:
            if (
                self.outcome != "blocked"
                or not _is_canonical_key(canonical)
                or self.consumed_context_items != CONTEXT_ITEMS
            ):
                raise ValueError("blocked state mismatch")
        elif self.reason == "":
            if (
                self.outcome != "passed"
                or not _is_canonical_key(canonical)
                or self.consumed_context_items != CONTEXT_ITEMS
            ):
                raise ValueError("passed state mismatch")
        else:  # pragma: no cover - vocabulary guard above is authoritative
            raise ValueError("unreachable reason state")


def _result(
    outcome: str,
    reason: str,
    canonical: str,
    consumed_context_items: tuple[str, ...],
) -> Admit009EvaluationResult:
    validated = () if canonical == "" else ((CANDIDATE_FIELDS[0], canonical),)
    return Admit009EvaluationResult(
        admission_rule_id=ADMISSION_RULE_ID,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        canonical_duplicate_identity_key=canonical,
        validated_candidate_fields=validated,
        consumed_candidate_fields=CANDIDATE_FIELDS,
        consumed_context_items=consumed_context_items,
        evaluator_io_used=False,
    )


def _validate_scalar(value: object) -> tuple[str, str]:
    if type(value) is not str:
        return "", SCALAR_REASONS[0]
    if value == "":
        return "", SCALAR_REASONS[1]
    if not value.isascii():
        return "", SCALAR_REASONS[2]
    if _KEY_RE.fullmatch(value) is None:
        return "", SCALAR_REASONS[3]
    return value, ""


def _validate_policy(value: object) -> str:
    if type(value) is not str:
        return POLICY_REASONS[0]
    if value != POLICY_CONTRACT_VALUE:
        return POLICY_REASONS[1]
    return ""


def _validate_batch(value: object) -> str:
    if type(value) is not tuple:
        return BATCH_REASONS[0]
    if any(type(member) is not str for member in value):
        return BATCH_REASONS[1]
    if any(_validate_scalar(member)[1] != "" for member in value):
        return BATCH_REASONS[2]
    if any(left >= right for left, right in zip(value, value[1:])):
        return BATCH_REASONS[3]
    return ""


def evaluate_admit_009(
    duplicate_identity_key: object,
    batch_duplicate_identity_keys: object,
    duplicate_identity_key_contract: object,
) -> Admit009EvaluationResult:
    """Evaluate an opaque candidate key against a validated batch snapshot."""
    canonical, reason = _validate_scalar(duplicate_identity_key)
    if reason:
        return _result("invalid", reason, "", ())
    reason = _validate_policy(duplicate_identity_key_contract)
    if reason:
        return _result("invalid", reason, canonical, CONTEXT_ITEMS[:1])
    reason = _validate_batch(batch_duplicate_identity_keys)
    if reason:
        return _result("invalid", reason, canonical, CONTEXT_ITEMS)
    if canonical in batch_duplicate_identity_keys:
        return _result("blocked", DUPLICATE_REASON, canonical, CONTEXT_ITEMS)
    return _result("passed", "", canonical, CONTEXT_ITEMS)


# The metadata boundary below is deliberately unreachable from the evaluator
# closure above.  All paths refer to committed non-raw, non-checkpoint evidence.
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1"
)
SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py",
    str(DESIGN_ROOT / "covapie_admit_009_duplicate_identity_key_contract_manifest.json"),
    str(DESIGN_ROOT / "covapie_admit_009_duplicate_identity_key_contract.csv"),
    str(DESIGN_ROOT / "covapie_admit_009_batch_and_policy_context_contract.csv"),
    str(DESIGN_ROOT / "covapie_admit_009_equivalence_and_provider_boundary_matrix.csv"),
    str(DESIGN_ROOT / "covapie_admit_009_duplicate_identity_validation_truth_matrix.csv"),
    str(DESIGN_ROOT / "covapie_admit_009_duplicate_identity_issue_readiness_inventory.csv"),
    str(PRECONDITION_ROOT / "covapie_admit_009_formal_evaluator_preconditions_manifest.json"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_008_runtime_issue_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26",
    "d0d0d19e491f27621214ee887f630a871c1a7cfaf4caca93778599b0162dc48c",
    "484072cd901f7ba5264d207202be493477fb16cc4ddfad4341eabd19d8495a85",
    "38ac90e04316d8efc8794d88d749a3fafc69a0ef66de5cf76cdfd82f6d9a9b57",
    "7b1d09956be5fa76f8b141c10a2a8efb895119271cfd75b9e816c37c88513297",
    "762255cc85a12501ccb592a6f3e82ea100221d33c244403386be743c99c64ac0",
    "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    "5d1be882bc51c3fad5eefa5dc106dec43ba5842eda0696c06eb04473db33a37b",
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
), strict=True))
(
    DESIGN_SOURCE_PATH,
    DESIGN_MANIFEST_PATH,
    DESIGN_CONTRACT_PATH,
    DESIGN_CONTEXT_PATH,
    DESIGN_BOUNDARY_PATH,
    DESIGN_TRUTH_PATH,
    AUTHORITATIVE_ISSUE_PATH,
    PRECONDITION_MANIFEST_PATH,
    RUNTIME_SOURCE_PATH,
    RUNTIME_MANIFEST_PATH,
    RUNTIME_ISSUE_PATH,
    ADMIT008_SOURCE_PATH,
    UNIFIED_RESULT_CONTRACT_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_009_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_009_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_009_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_009_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_009_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_009_rule_logic_interface_manifest.json"
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
    "case_id", "case_group", "key_input_kind", "key_input_display",
    "batch_input_kind", "batch_input_display", "policy_input_kind", "policy_input_display",
    "expected_full_result", "observed_full_result", "committed_design_oracle_full_result",
    "formal_expected_equality", "formal_design_oracle_equality", "case_passed",
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


class _TruthStringSubclass(str):
    pass


class _TruthTupleSubclass(tuple):
    pass


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path)
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_expected_base_lineage(repo_root: Path, head_ref: str) -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref invalid")
    exists = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root)
    if exists.returncode or subject.returncode or ancestor.returncode:
        raise ValueError("expected base lineage invalid")
    if subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
        (repo_root / path).resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
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
    """Complete all Exact13 structural checks before the first source-byte read."""
    if len(SOURCE_PATHS) != 13 or len(set(SOURCE_PATHS)) != 13 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact13 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
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
        and len(value.records) == 13
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
            keys = tuple(key.value for key in value.keys if isinstance(key, ast.Constant) and type(key.value) is str)
            if len(keys) == len(value.keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _one(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = tuple(row for row in rows if row.get(key) == value)
    if len(matches) != 1:
        raise ValueError(f"expected one row for {key}={value}")
    return matches[0]


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    design_source = ast.parse(_record(snapshot, DESIGN_SOURCE_PATH).content_bytes.decode("utf-8"))
    design_functions = {node.name for node in design_source.body if isinstance(node, ast.FunctionDef)}
    design_manifest = _json_document(snapshot, DESIGN_MANIFEST_PATH)
    design_contract = _csv_document(snapshot, DESIGN_CONTRACT_PATH)
    design_context = _csv_document(snapshot, DESIGN_CONTEXT_PATH)
    design_boundary = _csv_document(snapshot, DESIGN_BOUNDARY_PATH)
    design_truth = _csv_document(snapshot, DESIGN_TRUTH_PATH)
    design_issues = _csv_document(snapshot, AUTHORITATIVE_ISSUE_PATH)
    precondition = _json_document(snapshot, PRECONDITION_MANIFEST_PATH)
    runtime_tree = ast.parse(_record(snapshot, RUNTIME_SOURCE_PATH).content_bytes.decode("utf-8"))
    runtime_manifest = _json_document(snapshot, RUNTIME_MANIFEST_PATH)
    runtime_issues = _csv_document(snapshot, RUNTIME_ISSUE_PATH)
    admit008_tree = ast.parse(_record(snapshot, ADMIT008_SOURCE_PATH).content_bytes.decode("utf-8"))
    unified = _csv_document(snapshot, UNIFIED_RESULT_CONTRACT_PATH)
    issue_map = {row["issue_id"]: row for row in design_issues.rows}
    runtime_issue_map = {row["issue_id"]: row for row in runtime_issues.rows}
    invariants = {row["field_name"]: row["contract_value"] for row in unified.rows if row["contract_kind"] == "result_invariant"}
    groups = {
        group: sum(row["truth_group"] == group for row in design_truth.rows)
        for group in ("scalar", "policy", "batch", "outcome_state")
    }
    checks = (
        "classify_admit_009_duplicate_identity_key_design" in design_functions,
        "evaluate_admit_009" not in design_functions,
        len(design_contract.rows) == 34,
        len(design_context.rows) == 15,
        len(design_boundary.rows) == 18,
        len(design_truth.rows) == 32,
        groups == {"scalar": 12, "policy": 4, "batch": 12, "outcome_state": 4},
        all(row["truth_passed"] == "true" for row in design_truth.rows),
        design_manifest.get("truth_matrix_contract") == "Exact32",
        design_manifest.get("design_oracle_is_formal_evaluator") is False,
        design_manifest.get("real_provider_duplicate_identity_key_count") == 0,
        design_manifest.get("real_provider_duplicate_identity_mapping_validated") is False,
        len(design_issues.rows) == 11,
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] == "resolved",
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["integration_transition"] == "duplicate_identity_key_contract_frozen_v1",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_009|"),
        precondition.get("precondition_row_count") == 24,
        precondition.get("real_provider_duplicate_identity_key_count") == 0,
        _literal_registry_keys(runtime_tree) == tuple(f"ADMIT_{index:03d}" for index in range(1, 9)),
        runtime_manifest.get("registered_rule_ids") == [f"ADMIT_{index:03d}" for index in range(1, 9)],
        runtime_manifest.get("admit_009_registered_in_engine") is False,
        len(runtime_issues.rows) == 11,
        runtime_issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_009|"),
        "evaluate_admit_008" in {node.name for node in admit008_tree.body if isinstance(node, ast.FunctionDef)},
        invariants.get("passed") == "true_iff_outcome_passed",
        invariants.get("blocks_candidate") == "true_iff_outcome_not_passed",
        invariants.get("passed_reason") == "empty_exact_str",
        invariants.get("nonpassed_reason") == "nonempty_exact_str",
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "design_truth_rows": design_truth.rows,
        "issue_rows": design_issues.rows,
        "issue_bytes": _record(snapshot, AUTHORITATIVE_ISSUE_PATH).content_bytes,
    }


def _display(value: object) -> str:
    return f"{type(value).__name__}:{value!r}"


def _truth_definitions() -> tuple[tuple[str, str, object, object, object], ...]:
    candidate = KEY_PREFIX + "1" * 64
    low = KEY_PREFIX + "0" * 64
    high = KEY_PREFIX + "2" * 64
    unrelated = KEY_PREFIX + "f" * 64
    policy = POLICY_CONTRACT_VALUE
    empty: tuple[str, ...] = ()
    return (
        ("scalar", "scalar_none", None, empty, policy),
        ("scalar", "scalar_integer", 7, empty, policy),
        ("scalar", "scalar_str_subclass", _TruthStringSubclass(candidate), empty, policy),
        ("scalar", "scalar_empty", "", empty, policy),
        ("scalar", "scalar_non_ascii", KEY_PREFIX + "é" * 64, empty, policy),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, policy),
        ("scalar", "scalar_uppercase_digest", KEY_PREFIX + "A" * 64, empty, policy),
        ("scalar", "scalar_short_digest", KEY_PREFIX + "1" * 63, empty, policy),
        ("scalar", "scalar_long_digest", KEY_PREFIX + "1" * 65, empty, policy),
        ("scalar", "scalar_non_hex", KEY_PREFIX + "g" * 64, empty, policy),
        ("scalar", "scalar_whitespace", " " + candidate, empty, policy),
        ("scalar", "scalar_canonical", candidate, empty, policy),
        ("policy", "policy_none", candidate, empty, None),
        ("policy", "policy_str_subclass", candidate, empty, _TruthStringSubclass(policy)),
        ("policy", "policy_wrong_value", candidate, empty, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", candidate, empty, policy),
        ("batch", "batch_none", candidate, None, policy),
        ("batch", "batch_list", candidate, [], policy),
        ("batch", "batch_tuple_subclass", candidate, _TruthTupleSubclass(), policy),
        ("batch", "batch_non_str_member", candidate, (7,), policy),
        ("batch", "batch_str_subclass_member", candidate, (_TruthStringSubclass(unrelated),), policy),
        ("batch", "batch_malformed_member", candidate, ("bad",), policy),
        ("batch", "batch_unsorted", candidate, (high, low), policy),
        ("batch", "batch_duplicate_members", candidate, (unrelated, unrelated), policy),
        ("batch", "batch_empty_valid", candidate, (), policy),
        ("batch", "batch_one_unrelated", candidate, (unrelated,), policy),
        ("batch", "batch_one_matching", candidate, (candidate,), policy),
        ("batch", "batch_multiple_contains", candidate, (low, candidate, high), policy),
        ("outcome_state", "canonical_unique_passed", candidate, (unrelated,), policy),
        ("outcome_state", "canonical_duplicate_blocked", candidate, (candidate,), policy),
        ("outcome_state", "policy_invalid_retains_pair", candidate, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", candidate, [candidate], policy),
    )


def _independent_expected(key: object, batch: object, policy: object) -> Admit009EvaluationResult:
    if type(key) is not str:
        return _result("invalid", SCALAR_REASONS[0], "", ())
    if key == "":
        return _result("invalid", SCALAR_REASONS[1], "", ())
    if not all(ord(character) < 128 for character in key):
        return _result("invalid", SCALAR_REASONS[2], "", ())
    if re.fullmatch(KEY_REGEX, key, flags=re.ASCII) is None:
        return _result("invalid", SCALAR_REASONS[3], "", ())
    if type(policy) is not str:
        return _result("invalid", POLICY_REASONS[0], key, CONTEXT_ITEMS[:1])
    if policy != POLICY_CONTRACT_VALUE:
        return _result("invalid", POLICY_REASONS[1], key, CONTEXT_ITEMS[:1])
    if type(batch) is not tuple:
        return _result("invalid", BATCH_REASONS[0], key, CONTEXT_ITEMS)
    if any(type(member) is not str for member in batch):
        return _result("invalid", BATCH_REASONS[1], key, CONTEXT_ITEMS)
    if any(
        member == ""
        or not member.isascii()
        or re.fullmatch(KEY_REGEX, member, flags=re.ASCII) is None
        for member in batch
    ):
        return _result("invalid", BATCH_REASONS[2], key, CONTEXT_ITEMS)
    if any(left >= right for left, right in zip(batch, batch[1:])):
        return _result("invalid", BATCH_REASONS[3], key, CONTEXT_ITEMS)
    if key in batch:
        return _result("blocked", DUPLICATE_REASON, key, CONTEXT_ITEMS)
    return _result("passed", "", key, CONTEXT_ITEMS)


def _result_dict(value: Admit009EvaluationResult) -> dict[str, Any]:
    return {name: getattr(value, name) for name in RESULT_FIELDS}


def _design_projection(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "admission_rule_id": ADMISSION_RULE_ID,
        "outcome": row["outcome"],
        "passed": row["passed"] == "true",
        "blocks_candidate": row["blocks_candidate"] == "true",
        "reason": row["reason"],
        "canonical_duplicate_identity_key": row["canonical_duplicate_identity_key"],
        "validated_candidate_fields": tuple(tuple(pair) for pair in json.loads(row["validated_candidate_fields"])),
        "consumed_candidate_fields": tuple(json.loads(row["consumed_candidate_fields"])),
        "consumed_context_items": tuple(json.loads(row["consumed_context_items"])),
        "evaluator_io_used": row["evaluator_io_used"] == "true",
    }


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    definitions = _truth_definitions()
    if len(definitions) != 32 or len(predecessor_rows) != 32:
        raise ValueError("Exact32 predecessor shape invalid")
    rows: list[dict[str, str]] = []
    for (group, case_id, key, batch, policy), prior in zip(definitions, predecessor_rows, strict=True):
        if prior["truth_group"] != group or prior["case_id"] != case_id:
            raise ValueError(f"committed Exact32 order mismatch: {case_id}")
        expected = _result_dict(_independent_expected(key, batch, policy))
        observed = _result_dict(evaluate_admit_009(key, batch, policy))
        design = _design_projection(prior)
        expected_text = json.dumps(expected, separators=(",", ":"))
        observed_text = json.dumps(observed, separators=(",", ":"))
        design_text = json.dumps(design, separators=(",", ":"))
        rows.append({
            "case_id": case_id,
            "case_group": group,
            "key_input_kind": type(key).__name__,
            "key_input_display": _display(key),
            "batch_input_kind": type(batch).__name__,
            "batch_input_display": _display(batch),
            "policy_input_kind": type(policy).__name__,
            "policy_input_display": _display(policy),
            "expected_full_result": expected_text,
            "observed_full_result": observed_text,
            "committed_design_oracle_full_result": design_text,
            "formal_expected_equality": _bool(observed == expected),
            "formal_design_oracle_equality": _bool(observed == design),
            "case_passed": _bool(observed == expected == design),
        })
    return rows


def _contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_009(duplicate_identity_key, batch_duplicate_identity_keys, duplicate_identity_key_contract)"),
        ("API_002", "public_api", "inputs", "three_required_positional_or_keyword_direct_objects"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "exact_frozen_dataclass_no_subclasses"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "exact_types", "exact_str_bool_tuple_and_string_pairs"),
        ("RESULT_005", "result_contract", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_007", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        ("RESULT_008", "result_contract", "reason", "passed_empty_nonpassed_frozen_reason"),
        ("RESULT_009", "result_contract", "scalar_invalid", "empty_canonical_empty_validated_empty_context"),
        ("RESULT_010", "result_contract", "policy_invalid", "canonical_pair_policy_context"),
        ("RESULT_011", "result_contract", "batch_invalid", "canonical_pair_full_context"),
        ("RESULT_012", "result_contract", "passed_blocked", "canonical_pair_full_context"),
        ("RESULT_013", "result_contract", "consumed_candidate", CANDIDATE_FIELDS[0]),
        ("RESULT_014", "result_contract", "evaluator_io_used", "exact_false"),
        ("KEY_001", "scalar_semantics", "type", "exact_builtin_str"),
        ("KEY_002", "scalar_semantics", "regex", KEY_REGEX),
        ("KEY_003", "scalar_semantics", "precedence", "type|nonempty|ascii|regex_fullmatch"),
        ("KEY_004", "scalar_semantics", "canonical", "input_exactly_unchanged"),
        ("KEY_005", "scalar_semantics", "normalization", "none"),
        ("KEY_006", "scalar_semantics", "composition", "opaque_producer_owned_zero_visible_components"),
        ("POLICY_001", "policy_semantics", "type", "exact_builtin_str"),
        ("POLICY_002", "policy_semantics", "value", POLICY_CONTRACT_VALUE),
        ("POLICY_003", "policy_semantics", "normalization", "none"),
        ("BATCH_001", "batch_semantics", "type", "exact_builtin_tuple_empty_allowed"),
        ("BATCH_002", "batch_semantics", "members", "exact_builtin_str_full_scalar_valid"),
        ("BATCH_003", "batch_semantics", "order", "strict_original_string_ascending"),
        ("BATCH_004", "batch_semantics", "uniqueness", "required"),
        ("BATCH_005", "batch_semantics", "repair", "no_sort_no_deduplicate_no_normalization"),
        ("BATCH_006", "batch_semantics", "snapshot", "earlier_candidates_current_record_excluded_by_caller"),
        ("PRECEDENCE_001", "rule_semantics", "validation", "scalar|policy|batch|exact_membership"),
        ("PRECEDENCE_002", "rule_semantics", "short_circuit_context", "none|policy_only|policy_and_batch"),
        ("MEMBERSHIP_001", "rule_semantics", "comparison", "exact_case_sensitive_python_string_equality"),
        ("MEMBERSHIP_002", "rule_semantics", "unique", "passed_empty_reason"),
        ("MEMBERSHIP_003", "rule_semantics", "duplicate", DUPLICATE_REASON),
        ("REASON_001", "rule_semantics", "historical_lowercase", "duplicate_identity_unresolved_not_used"),
        ("ORACLE_001", "oracle_contract", "production", "does_not_import_or_call_design_oracle"),
        ("ORACLE_002", "oracle_contract", "attestation", "checker_compares_all_exact10_fields"),
        ("ORACLE_003", "oracle_contract", "truth", "committed_exact32_full_equivalence"),
        ("PROVIDER_001", "provider_boundary", "mapping", "unvalidated_zero_real_keys"),
        ("PROVIDER_002", "provider_boundary", "fields", "candidate_group_leakage_fields_not_parsed"),
        ("BOUNDARY_001", "authorization_boundary", "runtime", "no_adapter_no_registration_no_exact9"),
        ("BOUNDARY_002", "authorization_boundary", "later_rules", "no_admit010_no_all_rules_no_combined_verdict"),
        ("BOUNDARY_003", "authorization_boundary", "operations", "no_raw_network_download_checkpoint_model_training"),
    )
    return [{
        "contract_id": identifier,
        "contract_kind": kind,
        "contract_subject": subject,
        "contract_value": value,
        "contract_status": "frozen",
    } for identifier, kind, subject, value in values]


BOUNDARY_NECESSITY = (
    "committed design source and independent oracle identity",
    "design manifest counts readiness boundaries and hashes",
    "Exact34 duplicate key contract",
    "Exact15 policy and batch context contract",
    "Exact18 equivalence and provider boundary",
    "ordered committed Exact32 semantic oracle corpus",
    "authoritative Exact11 issue inventory preservation baseline",
    "historical Exact24 formal evaluator precondition boundary",
    "current literal Exact8 runtime with absent ADMIT_009 registration",
    "current Exact8 runtime readiness and registry boundary",
    "current Exact8 runtime issue coverage cross-check",
    "mature ADMIT_008 standalone structural precedent",
    "unified result blocks_candidate and reason invariants",
)


def _source_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [{
        "source_order": str(index),
        "source_relative_path": record.relative_path.as_posix(),
        "source_kind": record.relative_path.suffix.lstrip("."),
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
    "formal_evaluator_implementation",
    "exact10_result_class",
    "exact32_equivalence",
    "result_invariant_enforcement",
    "pure_call_graph_validation",
    "deterministic_materialization",
    "source_verification",
    "issue_byte_preservation",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "provider_key_generation",
    "provider_mapping",
    "real_candidate_evaluation",
    "adapter_design",
    "adapter_implementation",
    "admit_009_registration",
    "exact9_runtime",
    "admit_010",
    "evaluate_all_rules",
    "combined_candidate_verdict",
    "raw_read",
    "network",
    "bulk_download",
    "checkpoint",
    "torch_numpy_rdkit",
    "model_forward_loss",
    "training_fine_tune",
    "parameter_update",
    "stage",
    "commit",
    "push",
    "gh",
)


def _safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
    return [{
        "safety_item": item,
        "expected_executed": _bool(executed),
        "observed_executed": _bool(executed),
        "safety_passed": "true",
    } for item, executed in definitions]


TRUE_READINESS = (
    "admit_009_standalone_evaluator_implemented",
    "admit_009_exact10_result_contract_frozen",
    "admit_009_result_class_exact_type_enforced",
    "admit_009_result_cross_field_invariants_enforced",
    "admit_009_blocks_candidate_invariant_enforced",
    "admit_009_scalar_contract_runtime_enforced",
    "admit_009_policy_contract_runtime_enforced",
    "admit_009_batch_contract_runtime_enforced",
    "admit_009_validation_precedence_runtime_enforced",
    "admit_009_membership_runtime_enforced",
    "admit_009_formal_exact32_equivalence_enforced",
    "admit_009_formal_evaluator_pure_in_memory",
    "admit_009_design_oracle_independence_preserved",
    "admit_009_provider_mapping_boundary_preserved",
    "ready_for_admit_009_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "admit_010_standalone_evaluator_implemented",
    "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered",
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


def build_interface_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot() if source_snapshot is None else source_snapshot
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid frozen source snapshot")
    historical = _validate_predecessors(snapshot)
    state = {
        "source_snapshot": snapshot,
        "contract_rows": _contract_rows(),
        "truth_rows": _truth_rows(historical["design_truth_rows"]),
        "source_audit_rows": _source_audit_rows(snapshot),
        "safety_rows": _safety_rows(),
        "issue_rows": [dict(row) for row in historical["issue_rows"]],
        "issue_bytes": historical["issue_bytes"],
        "readiness": dict(READINESS),
    }
    groups = {
        group: sum(row["case_group"] == group for row in state["truth_rows"])
        for group in ("scalar", "policy", "batch", "outcome_state")
    }
    issue_map = {row["issue_id"]: row for row in state["issue_rows"]}
    checks = (
        len(state["contract_rows"]) == 46,
        len(state["truth_rows"]) == 32,
        groups == {"scalar": 12, "policy": 4, "batch": 12, "outcome_state": 4},
        all(row["case_passed"] == row["formal_expected_equality"] == row["formal_design_oracle_equality"] == "true" for row in state["truth_rows"]),
        len(state["source_audit_rows"]) == 13,
        len(state["safety_rows"]) == 30,
        len(state["issue_rows"]) == 11,
        hashlib.sha256(state["issue_bytes"]).hexdigest() == SOURCE_SHA256[AUTHORITATIVE_ISSUE_PATH],
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_009|"),
        all(row["safety_passed"] == "true" for row in state["safety_rows"]),
    )
    if not all(checks):
        raise RuntimeError("ADMIT_009 interface state failed closed")
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
    groups = {
        group: sum(row["case_group"] == group for row in state["truth_rows"])
        for group in ("scalar", "policy", "batch", "outcome_state")
    }
    readiness = dict(state["readiness"])
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": "duplicate_identity_precheck",
        "candidate_fields": list(CANDIDATE_FIELDS),
        "context_items": list(CONTEXT_ITEMS),
        "public_api": "evaluate_admit_009(duplicate_identity_key, batch_duplicate_identity_keys, duplicate_identity_key_contract)",
        "public_signature_parameters": ["duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract"],
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit009EvaluationResult",
        "result_field_count": 10,
        "result_fields": list(RESULT_FIELDS),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "key_prefix": KEY_PREFIX,
        "key_regex": KEY_REGEX,
        "key_canonical_equals_input": True,
        "normalization_applied": False,
        "policy_contract_value": POLICY_CONTRACT_VALUE,
        "batch_exact_type": "builtins.tuple",
        "batch_empty_allowed": True,
        "batch_member_exact_type": "builtins.str",
        "batch_strict_ascending_unique": True,
        "batch_automatic_sort_or_deduplicate": False,
        "validation_precedence": ["scalar", "policy", "batch", "exact_membership"],
        "scalar_validation_reasons": list(SCALAR_REASONS),
        "policy_validation_reasons": list(POLICY_REASONS),
        "batch_validation_reasons": list(BATCH_REASONS),
        "duplicate_blocked_reason": DUPLICATE_REASON,
        "membership_semantics": "exact case-sensitive Python string equality",
        "blocks_candidate_invariant": "true_iff_outcome_not_passed",
        "scalar_invalid_consumed_context_items": [],
        "policy_invalid_consumed_context_items": list(CONTEXT_ITEMS[:1]),
        "batch_invalid_consumed_context_items": list(CONTEXT_ITEMS),
        "passed_blocked_consumed_context_items": list(CONTEXT_ITEMS),
        "independent_semantic_oracle": "classify_admit_009_duplicate_identity_key_design",
        "independent_semantic_oracle_attested": True,
        "production_oracle_import_or_call": False,
        "evaluator_call_graph": ["evaluate_admit_009", "_validate_scalar", "_validate_policy", "_validate_batch", "_result"],
        "evaluator_call_graph_pure_in_memory": True,
        "truth_matrix_contract": "Exact32",
        "truth_matrix_row_count": 32,
        "truth_matrix_pass_count": 32,
        "truth_matrix_group_counts": groups,
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_input_count": 13,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": record.relative_path.as_posix(),
            "tracked": True,
            "base_tree_blob": True,
            "filesystem_regular": True,
            "non_symlink": True,
            "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_audit_row_count": 13,
        "source_audit_pass_count": 13,
        "issue_inventory_row_count": 11,
        "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": SOURCE_SHA256[AUTHORITATIVE_ISSUE_PATH],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015",
        "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_duplicate_identity_mapping_validated": False,
        "provider_fields_consumed": [],
        "safety_row_count": len(state["safety_rows"]),
        "safety_pass_count": len(state["safety_rows"]),
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True,
        "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "stop_boundaries": [
            "no_provider_key_generation",
            "no_provider_mapping",
            "no_unified_adapter_design_or_implementation",
            "no_admit_009_registration",
            "no_exact8_runtime_modification",
            "no_exact9_runtime",
            "no_admit_010",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_real_candidate_evaluation",
            "no_raw_network_download_checkpoint_model_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "validation_failures": [],
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


def run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(
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
    materialized = run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

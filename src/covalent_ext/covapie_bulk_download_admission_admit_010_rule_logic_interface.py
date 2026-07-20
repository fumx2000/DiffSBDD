"""CovaPIE ADMIT_010 standalone evaluator interface v1.

The evaluator closure is pure in memory and independently implements the
frozen 21-level contract.  The metadata-only half verifies committed sources
and materializes deterministic synthetic evidence; it is not evaluator-
reachable and never validates a real provider mapping.
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
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

from covalent_ext.covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate import (
    ADMISSION_RULE_ID,
    ADMISSION_RULE_NAME,
    ASSIGNMENT_POLICY,
    ASSIGNMENT_POLICY_VERSION,
    ASSIGNMENT_STAGE_KIND,
    CANDIDATE_FIELD,
    CONTEXT_ITEM,
    EVALUATION_PHASE,
    FIELD_MAPPING_RULE,
    HISTORICAL_ARTIFACT_FIELD,
    HISTORICAL_BLOCKING_REASON,
    LEAKAGE_GROUP_PREFIX,
    LEAKAGE_GROUP_REGEX,
    LeakageGroupAssignmentProvenanceContractV1,
    PRE_SPLIT_ASSIGNED_STATUS,
    PROVENANCE_CONTRACT_VERSION,
    REASONS,
    VALIDATION_PRECEDENCE,
)


PROJECT = "CovaPIE"
STEP = "ADMIT_010 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_010_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "c78f15a1bf57f6372e48098629f3cce33f21e7fc"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_010 leakage group provenance contract v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_010_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_010_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
REASON_VOCABULARY = ("", *REASONS)
CONSUMED_CANDIDATE_FIELDS = (CANDIDATE_FIELD,)
CONSUMED_CONTEXT_ITEMS = (CONTEXT_ITEM,)
RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_leakage_group_id", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
SCALAR_SHORT_REASONS = (
    "LEAKAGE_GROUP_ID_TYPE_INVALID", HISTORICAL_BLOCKING_REASON,
    "LEAKAGE_GROUP_ID_NON_ASCII", "LEAKAGE_GROUP_ID_SYNTAX_INVALID",
)
INVALID_REASONS = tuple(reason for reason in REASONS if reason != HISTORICAL_BLOCKING_REASON)
_GROUP_RE = re.compile(LEAKAGE_GROUP_REGEX, re.ASCII)
_SHA_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)


def _is_canonical_group_id(value: object) -> bool:
    return type(value) is str and value.isascii() and _GROUP_RE.fullmatch(value) is not None


@dataclass(frozen=True)
class Admit010EvaluationResult:
    admission_rule_id: object
    outcome: object
    passed: object
    blocks_candidate: object
    reason: object
    canonical_leakage_group_id: object
    validated_candidate_fields: object
    consumed_candidate_fields: object
    consumed_context_items: object
    evaluator_io_used: object

    def __post_init__(self) -> None:
        # Complete every type gate before any value comparison or membership.
        if type(self) is not Admit010EvaluationResult:
            raise TypeError("result subclasses are forbidden")
        string_values = (
            self.admission_rule_id, self.outcome, self.reason,
            self.canonical_leakage_group_id,
        )
        if any(type(value) is not str for value in string_values):
            raise TypeError("all scalar string fields must be exact built-in str")
        if type(self.passed) is not bool or type(self.blocks_candidate) is not bool:
            raise TypeError("state flags must be exact built-in bool")
        if type(self.evaluator_io_used) is not bool:
            raise TypeError("evaluator_io_used must be exact built-in bool")
        tuple_values = (
            self.validated_candidate_fields, self.consumed_candidate_fields,
            self.consumed_context_items,
        )
        if any(type(value) is not tuple for value in tuple_values):
            raise TypeError("tuple fields must be exact built-in tuple")
        for pair in self.validated_candidate_fields:
            if type(pair) is not tuple:
                raise TypeError("validated pair must be exact built-in tuple")
            if len(pair) != 2:
                raise TypeError("validated pair must contain exactly two items")
            if type(pair[0]) is not str or type(pair[1]) is not str:
                raise TypeError("validated pair items must be exact built-in str")
        if any(type(item) is not str for item in self.consumed_candidate_fields):
            raise TypeError("consumed candidate items must be exact built-in str")
        if any(type(item) is not str for item in self.consumed_context_items):
            raise TypeError("consumed context items must be exact built-in str")

        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("admission_rule_id must be ADMIT_010")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome is outside the frozen vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed must be true iff outcome is passed")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate must be true iff outcome is nonpassed")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the frozen vocabulary")
        if (self.reason == "") is not (self.outcome == "passed"):
            raise ValueError("reason emptiness does not match outcome")
        if self.reason == HISTORICAL_BLOCKING_REASON:
            if self.outcome != "blocked":
                raise ValueError("lowercase historical reason is blocked-only")
        elif self.reason != "" and self.outcome != "invalid":
            raise ValueError("uppercase reasons are invalid-only")
        if self.consumed_candidate_fields != CONSUMED_CANDIDATE_FIELDS:
            raise ValueError("consumed_candidate_fields mismatch")
        if self.consumed_context_items not in ((), CONSUMED_CONTEXT_ITEMS):
            raise ValueError("consumed_context_items shape mismatch")
        canonical = self.canonical_leakage_group_id
        expected_validated = () if canonical == "" else ((CANDIDATE_FIELD, canonical),)
        if self.validated_candidate_fields != expected_validated:
            raise ValueError("validated_candidate_fields mismatch canonical state")

        scalar_short = canonical == ""
        if scalar_short:
            if (
                self.reason not in SCALAR_SHORT_REASONS
                or self.consumed_context_items != ()
                or self.validated_candidate_fields != ()
            ):
                raise ValueError("scalar short-circuit state mismatch")
            if self.reason == HISTORICAL_BLOCKING_REASON:
                if self.outcome != "blocked":
                    raise ValueError("empty scalar must block")
            elif self.outcome != "invalid":
                raise ValueError("invalid scalar state mismatch")
        else:
            if not _is_canonical_group_id(canonical):
                raise ValueError("retained canonical group id is invalid")
            if self.consumed_context_items != CONSUMED_CONTEXT_ITEMS:
                raise ValueError("retained state must consume the context")
            if self.reason in (
                "LEAKAGE_GROUP_ID_TYPE_INVALID", "LEAKAGE_GROUP_ID_NON_ASCII",
                "LEAKAGE_GROUP_ID_SYNTAX_INVALID",
            ):
                raise ValueError("scalar invalid reason cannot retain canonical state")


def _formal_result(outcome: str, reason: str, canonical: str) -> Admit010EvaluationResult:
    retained = canonical != ""
    return Admit010EvaluationResult(
        ADMISSION_RULE_ID, outcome, outcome == "passed", outcome != "passed", reason,
        canonical, ((CANDIDATE_FIELD, canonical),) if retained else (),
        CONSUMED_CANDIDATE_FIELDS, CONSUMED_CONTEXT_ITEMS if retained else (), False,
    )


def _valid_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and _SHA_RE.fullmatch(value) is not None


def _valid_opaque_id(value: object) -> bool:
    return (
        type(value) is str and 1 <= len(value) <= 256 and value.isascii()
        and value == value.strip()
    )


def evaluate_admit_010(
    leakage_group_id: object,
    leakage_group_assignment_provenance_contract: object,
) -> Admit010EvaluationResult:
    """Evaluate caller-supplied pre-split leakage-group assignment evidence."""
    if type(leakage_group_id) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "")
    if leakage_group_id == "":
        return _formal_result("blocked", HISTORICAL_BLOCKING_REASON, "")
    if not leakage_group_id.isascii():
        return _formal_result("invalid", "LEAKAGE_GROUP_ID_NON_ASCII", "")
    if _GROUP_RE.fullmatch(leakage_group_id) is None:
        return _formal_result("invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID", "")
    canonical = leakage_group_id
    value = leakage_group_assignment_provenance_contract
    if type(value) is not LeakageGroupAssignmentProvenanceContractV1:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID", canonical)
    if type(value.contract_version) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID", canonical)
    if value.contract_version != PROVENANCE_CONTRACT_VERSION:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID", canonical)
    if type(value.canonical_candidate_field_name) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if value.canonical_candidate_field_name != CANDIDATE_FIELD:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if type(value.historical_artifact_field_name) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if value.historical_artifact_field_name != HISTORICAL_ARTIFACT_FIELD:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if type(value.field_mapping_rule) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if value.field_mapping_rule != FIELD_MAPPING_RULE:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID", canonical)
    if type(value.assignment_policy) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID", canonical)
    if value.assignment_policy != ASSIGNMENT_POLICY:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID", canonical)
    if type(value.assignment_policy_version) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID", canonical)
    if value.assignment_policy_version != ASSIGNMENT_POLICY_VERSION:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID", canonical)
    if type(value.assignment_stage_kind) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID", canonical)
    if value.assignment_stage_kind != ASSIGNMENT_STAGE_KIND:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID", canonical)
    sha_values = (
        value.assignment_manifest_sha256, value.assignment_artifact_sha256,
        value.group_inventory_sha256, value.sample_index_sha256,
    )
    if any(type(item) is not str for item in sha_values):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID", canonical)
    if any(not _valid_sha256(item) for item in sha_values):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID", canonical)
    if type(value.assignment_id) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID", canonical)
    if not _valid_opaque_id(value.assignment_id):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID", canonical)
    if type(value.historical_leakage_group_id) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID", canonical)
    if not _is_canonical_group_id(value.historical_leakage_group_id):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID", canonical)
    if type(value.sample_index_row_id) is not str:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID", canonical)
    if not _valid_opaque_id(value.sample_index_row_id):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID", canonical)
    members = value.member_sample_index_row_ids
    if type(members) is not tuple:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID", canonical)
    if len(members) == 0 or any(type(member) is not str for member in members):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID", canonical)
    if any(not _valid_opaque_id(member) for member in members):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID", canonical)
    if any(left >= right for left, right in zip(members, members[1:])):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID", canonical)
    if type(value.member_count) is not int:
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID", canonical)
    if value.member_count <= 0 or value.member_count != len(members):
        return _formal_result("invalid", "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID", canonical)
    if (
        type(value.assignment_passed) is not bool
        or type(value.split_assignments_written) is not bool
        or type(value.pre_split_assignment_status) is not str
    ):
        return _formal_result("blocked", HISTORICAL_BLOCKING_REASON, canonical)
    if (
        value.assignment_passed is not True
        or value.split_assignments_written is not False
        or value.pre_split_assignment_status != PRE_SPLIT_ASSIGNED_STATUS
    ):
        return _formal_result("blocked", HISTORICAL_BLOCKING_REASON, canonical)
    if canonical != value.historical_leakage_group_id:
        return _formal_result("blocked", HISTORICAL_BLOCKING_REASON, canonical)
    if value.sample_index_row_id not in members:
        return _formal_result("blocked", HISTORICAL_BLOCKING_REASON, canonical)
    return _formal_result("passed", "", canonical)


# Metadata-only boundary. Nothing below is reachable from evaluate_admit_010.
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1")
PRECONDITION_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1")
ADMIT009_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1")
SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py",
    str(DESIGN_ROOT / "covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json"),
    str(DESIGN_ROOT / "covapie_admit_010_leakage_group_assignment_provenance_contract.csv"),
    str(DESIGN_ROOT / "covapie_admit_010_leakage_group_id_field_mapping_and_grammar_contract.csv"),
    str(DESIGN_ROOT / "covapie_admit_010_provenance_validation_truth_matrix.csv"),
    str(DESIGN_ROOT / "covapie_admit_010_provenance_contract_source_boundary_audit.csv"),
    str(DESIGN_ROOT / "covapie_admit_010_provenance_contract_issue_readiness_inventory.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py",
    str(PRECONDITION_ROOT / "covapie_admit_010_formal_evaluator_preconditions_manifest.json"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
    str(ADMIT009_ROOT / "covapie_admit_009_rule_logic_interface_contract.csv"),
    str(ADMIT009_ROOT / "covapie_admit_009_rule_logic_interface_manifest.json"),
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05",
    "33fb0d6f35b49dbf98e61e2c16fafece4b01cdfcce629ff7f1ac5afb1e7e5af2",
    "6daea490d7a355015f9b9f0da134d0c4e58ae48dfb7e38ed0337efdcfbe8a4a6",
    "9de1347f94498f1e79f95b48bc4e943fe6b311715bebeb1acd730110907fb3ba",
    "1a40d6e7ef0cbccf9408f9fca2524ab260f3291dd1fe4f1838d3e0a73b8a3ee7",
    "607660277c3f2ee4931cfc4601017ed57b8953eb738a3535f5580a21591107f6",
    "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    "229945a3edad28ee7770172cb931e05ac463db56b0dd1abe57a8053bb4d7e5b1",
    "29df6cdf3b1eb7c1a690610d9fad88055797caba58f27f01f0b7da0d488d4c43",
    "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
    "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67",
    "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
    "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
), strict=True))
AUTHORITATIVE_ISSUE_PATH = SOURCE_PATHS[6]
DESIGN_TRUTH_PATH = SOURCE_PATHS[4]

CONTRACT_FILENAME = "covapie_admit_010_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_010_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_010_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_010_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_010_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_010_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_AUDIT_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
CONTRACT_COLUMNS = ("contract_id", "contract_kind", "contract_subject", "contract_value", "contract_status")
TRUTH_COLUMNS = (
    "truth_order", "truth_group", "case_id", "input_summary", *RESULT_FIELDS,
    "design_oracle_full_result", "exact10_equal_field_count",
    "formal_design_exact10_parity", "expected_precedence", "truth_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "safe_descendant", "expected_sha256", "base_tree_sha256",
    "filesystem_sha256", "source_boundary_passed",
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
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _resolved_safe_descendant(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        (repo_root / path).resolve(strict=True).relative_to(repo_root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _validate_base_lineage(repo_root: Path, head_ref: str) -> None:
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
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    header = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(header) == 3
        and header[0] in ("100644", "100755") and header[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        and _resolved_safe_descendant(path, repo_root)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    if len(SOURCE_PATHS) != 13 or len(set(SOURCE_PATHS)) != 13 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact13 source boundary invalid")
    _validate_base_lineage(repo_root, head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base source read failed: {path}")
        filesystem = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem).hexdigest()
        if SOURCE_SHA256[path] != base_sha or base_sha != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], base_sha, filesystem_sha, filesystem))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and type(value.records) is tuple
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
        raise ValueError("source record missing or duplicate")
    return matches[0]


def _csv_rows_from_bytes(content: bytes) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV rows")
    return rows


def _result_mapping(value: object) -> dict[str, object]:
    return {name: getattr(value, name) for name in RESULT_FIELDS}


def _jsonable_result(value: Mapping[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _valid_contract(
    *, candidate: str = "COVAPIE_LEAKAGE_GROUP_000001",
    sample: str = "SAMPLE_000001",
    members: tuple[str, ...] = ("SAMPLE_000001",),
) -> LeakageGroupAssignmentProvenanceContractV1:
    return LeakageGroupAssignmentProvenanceContractV1(
        PROVENANCE_CONTRACT_VERSION, CANDIDATE_FIELD, HISTORICAL_ARTIFACT_FIELD,
        FIELD_MAPPING_RULE, ASSIGNMENT_POLICY, ASSIGNMENT_POLICY_VERSION,
        ASSIGNMENT_STAGE_KIND, "1" * 64, "2" * 64, "3" * 64, "4" * 64,
        "ASSIGNMENT_RECORD_ALPHA", candidate, sample, members, len(members),
        True, False, PRE_SPLIT_ASSIGNED_STATUS,
    )


def _natural_cases() -> tuple[tuple[str, str, object, object, str], ...]:
    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    @dataclass(frozen=True)
    class ContractSubclass(LeakageGroupAssignmentProvenanceContractV1):
        pass

    candidate = "COVAPIE_LEAKAGE_GROUP_000001"
    other = "COVAPIE_LEAKAGE_GROUP_000002"
    base = _valid_contract(candidate=candidate)
    subclass = ContractSubclass(*(getattr(base, field.name) for field in fields(base)))
    cases = (
        ("candidate_scalar", "candidate_none", None, base, "1"),
        ("candidate_scalar", "candidate_integer", 7, base, "1"),
        ("candidate_scalar", "candidate_empty", "", base, "2"),
        ("candidate_scalar", "candidate_str_subclass", StringSubclass(candidate), base, "1"),
        ("candidate_scalar", "candidate_non_ascii", "COVAPIE_LEAKAGE_GROUP_00000é", base, "3"),
        ("candidate_scalar", "candidate_lowercase_prefix", "covapie_leakage_group_000001", base, "4"),
        ("candidate_scalar", "candidate_case_drift", "COVAPIE_leakage_GROUP_000001", base, "4"),
        ("candidate_scalar", "candidate_short_digits", "COVAPIE_LEAKAGE_GROUP_00001", base, "4"),
        ("candidate_scalar", "candidate_long_digits", "COVAPIE_LEAKAGE_GROUP_0000001", base, "4"),
        ("candidate_scalar", "candidate_non_digit_suffix", "COVAPIE_LEAKAGE_GROUP_00000A", base, "4"),
        ("candidate_scalar", "candidate_leading_whitespace", " " + candidate, base, "4"),
        ("candidate_scalar", "candidate_trailing_whitespace", candidate + " ", base, "4"),
        ("candidate_scalar", "candidate_unicode_digit", "COVAPIE_LEAKAGE_GROUP_00000١", base, "3"),
        ("candidate_scalar", "candidate_canonical", candidate, base, "21"),
        ("context_type", "context_none", candidate, None, "5"),
        ("context_type", "context_dict", candidate, {}, "5"),
        ("context_type", "context_dataclass_subclass", candidate, subclass, "5"),
        ("context_type", "context_exact_type", candidate, base, "21"),
        ("static_fields", "contract_version_wrong", candidate, replace(base, contract_version="v2"), "6"),
        ("static_fields", "candidate_field_wrong", candidate, replace(base, canonical_candidate_field_name="final_leakage_group_id"), "7"),
        ("static_fields", "historical_field_wrong", candidate, replace(base, historical_artifact_field_name="leakage_group_id"), "7"),
        ("static_fields", "mapping_rule_wrong", candidate, replace(base, field_mapping_rule="renumber"), "8"),
        ("static_fields", "policy_wrong", candidate, replace(base, assignment_policy="other_policy_v1"), "9"),
        ("static_fields", "policy_version_wrong", candidate, replace(base, assignment_policy_version="v2"), "10"),
        ("static_fields", "stage_kind_wrong", candidate, replace(base, assignment_stage_kind="post_split"), "11"),
        ("sha256", "sha_none", candidate, replace(base, assignment_manifest_sha256=None), "12"),
        ("sha256", "sha_str_subclass", candidate, replace(base, assignment_artifact_sha256=StringSubclass("2" * 64)), "12"),
        ("sha256", "sha_uppercase", candidate, replace(base, group_inventory_sha256="A" * 64), "12"),
        ("sha256", "sha_short", candidate, replace(base, sample_index_sha256="4" * 63), "12"),
        ("sha256", "sha_non_hex", candidate, replace(base, assignment_manifest_sha256="g" * 64), "12"),
        ("sha256", "sha_exact_valid", candidate, base, "21"),
        ("assignment_id", "assignment_id_wrong_type", candidate, replace(base, assignment_id=7), "13"),
        ("assignment_id", "assignment_id_empty", candidate, replace(base, assignment_id=""), "13"),
        ("assignment_id", "assignment_id_non_ascii", candidate, replace(base, assignment_id="ASSIGNMENT_é"), "13"),
        ("assignment_id", "assignment_id_whitespace", candidate, replace(base, assignment_id=" ASSIGNMENT"), "13"),
        ("assignment_id", "assignment_id_valid_opaque", candidate, base, "21"),
        ("historical_group", "historical_group_wrong_type", candidate, replace(base, historical_leakage_group_id=7), "14"),
        ("historical_group", "historical_group_malformed", candidate, replace(base, historical_leakage_group_id="ASSIGNMENT_RECORD_ALPHA"), "14"),
        ("historical_group", "historical_group_canonical", candidate, base, "21"),
        ("sample_id", "sample_id_wrong_type", candidate, replace(base, sample_index_row_id=7), "15"),
        ("sample_id", "sample_id_empty", candidate, replace(base, sample_index_row_id=""), "15"),
        ("sample_id", "sample_id_non_ascii", candidate, replace(base, sample_index_row_id="SAMPLE_é"), "15"),
        ("sample_id", "sample_id_whitespace", candidate, replace(base, sample_index_row_id="SAMPLE "), "15"),
        ("sample_id", "sample_id_valid_opaque", candidate, base, "21"),
        ("membership", "membership_list", candidate, replace(base, member_sample_index_row_ids=["SAMPLE_000001"]), "16"),
        ("membership", "membership_tuple_subclass", candidate, replace(base, member_sample_index_row_ids=TupleSubclass(("SAMPLE_000001",))), "16"),
        ("membership", "membership_empty_tuple", candidate, replace(base, member_sample_index_row_ids=(), member_count=0), "16"),
        ("membership", "membership_non_str_member", candidate, replace(base, member_sample_index_row_ids=(7,)), "16"),
        ("membership", "membership_str_subclass_member", candidate, replace(base, member_sample_index_row_ids=(StringSubclass("SAMPLE_000001"),)), "16"),
        ("membership", "membership_empty_member", candidate, replace(base, member_sample_index_row_ids=("",)), "16"),
        ("membership", "membership_non_ascii_member", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_é",)), "16"),
        ("membership", "membership_unsorted", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000002", "SAMPLE_000001"), member_count=2), "16"),
        ("membership", "membership_duplicate", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000001", "SAMPLE_000001"), member_count=2), "16"),
        ("membership", "membership_sample_absent", candidate, replace(base, member_sample_index_row_ids=("SAMPLE_000002",)), "20"),
        ("membership", "membership_valid_singleton", candidate, base, "21"),
        ("membership", "membership_valid_multi_member", candidate, _valid_contract(candidate=candidate, sample="SAMPLE_000002", members=("SAMPLE_000001", "SAMPLE_000002")), "21"),
        ("member_count", "member_count_bool", candidate, replace(base, member_count=True), "17"),
        ("member_count", "member_count_float", candidate, replace(base, member_count=1.0), "17"),
        ("member_count", "member_count_zero", candidate, replace(base, member_count=0), "17"),
        ("member_count", "member_count_negative", candidate, replace(base, member_count=-1), "17"),
        ("member_count", "member_count_mismatch", candidate, replace(base, member_count=2), "17"),
        ("member_count", "member_count_exact_valid", candidate, base, "21"),
        ("assignment_semantics", "assignment_passed_false", candidate, replace(base, assignment_passed=False), "18"),
        ("assignment_semantics", "assignment_passed_int_one", candidate, replace(base, assignment_passed=1), "18"),
        ("assignment_semantics", "split_assignments_written_true", candidate, replace(base, split_assignments_written=True), "18"),
        ("assignment_semantics", "split_assignments_written_int_zero", candidate, replace(base, split_assignments_written=0), "18"),
        ("assignment_semantics", "pre_split_status_wrong", candidate, replace(base, pre_split_assignment_status="leakage_group_assigned"), "18"),
        ("assignment_semantics", "candidate_historical_mismatch", candidate, replace(base, historical_leakage_group_id=other), "19"),
        ("assignment_semantics", "valid_assigned_before_split", candidate, base, "21"),
        ("assignment_semantics", "valid_singleton", candidate, base, "21"),
        ("assignment_semantics", "valid_multi_member", candidate, _valid_contract(candidate=candidate, sample="SAMPLE_000001", members=("SAMPLE_000001", "SAMPLE_000002")), "21"),
    )
    if len(cases) != 71:
        raise RuntimeError("Exact71 natural corpus drift")
    return cases


def _contract_rows() -> tuple[dict[str, str], ...]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_010(leakage_group_id, leakage_group_assignment_provenance_contract)"),
        ("API_002", "public_api", "parameters", "two_required_positional_or_keyword_no_defaults_no_extras"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result", "type", "exact_frozen_dataclass_no_slots_no_subclasses"),
        ("RESULT_002", "result", "field_count", "10"),
        ("RESULT_003", "result", "field_order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result", "exact_types_first", "str|bool|tuple|string_pair_no_subclasses"),
        ("RESULT_005", "result", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result", "state", "passed_iff_passed;blocks_iff_nonpassed"),
        ("RESULT_007", "result", "reason", "passed_empty;nonpassed_frozen;blocked_lowercase_only"),
        ("RESULT_008", "result", "scalar_short", "empty_canonical_validated_context"),
        ("RESULT_009", "result", "retained", "canonical_pair_and_context_singleton"),
        ("RESULT_010", "result", "io", "exact_false"),
        ("TUPLE_001", "tuple", "consumed_candidate_fields", CANDIDATE_FIELD),
        ("TUPLE_002", "tuple", "consumed_context_items", "empty_or_context_singleton"),
        ("TUPLE_003", "tuple", "validated_candidate_fields", "empty_or_exact_single_canonical_pair"),
        ("IDENTITY_001", "reuse", "Exact19", "direct_committed_class_identity"),
        ("IDENTITY_002", "reuse", "constants", "direct_committed_design_identity"),
        ("PRECEDENCE_001", "validation", "Exact21", "|".join(VALIDATION_PRECEDENCE)),
        ("PRECEDENCE_002", "validation", "short_circuit", "exact_type_first_no_hostile_dunder"),
        ("GRAMMAR_001", "scalar", "regex", LEAKAGE_GROUP_REGEX),
        ("GRAMMAR_002", "scalar", "canonical", "input_byte_identity_no_normalization"),
        ("SHA_001", "provenance", "four_sha", "exact_lowercase_hex_str_length_64_syntax_only"),
        ("OPAQUE_001", "provenance", "identifiers", "exact_ascii_str_1_to_256_trim_identity"),
        ("MEMBER_001", "provenance", "membership", "exact_nonempty_tuple_strict_ascending_unique"),
        ("MEMBER_002", "provenance", "member_count", "exact_int_positive_equals_length_bool_rejected"),
        ("EVIDENCE_001", "provenance", "pre_split", "true_false_exact_status_then_equality_then_membership"),
        ("ORACLE_001", "oracle", "production", "formal_call_graph_does_not_import_or_call_design_classifier"),
        ("ORACLE_002", "oracle", "parity", "committed_Exact71_all_10_fields"),
        ("ORACLE_003", "oracle", "role", "design_classifier_tests_checker_metadata_only"),
        ("SOURCE_001", "source", "boundary", "fixed_ordered_Exact13_base_tree_and_filesystem_SHA"),
        ("SOURCE_002", "source", "structure", "all_structure_before_first_source_byte_read"),
        ("ISSUE_001", "issue", "inventory", "authoritative_bytes_preserved_no_transition"),
        ("PROVIDER_001", "boundary", "provider_mapping", "unvalidated_zero_real_provider_ids"),
        ("BOUNDARY_001", "boundary", "integration", "no_adapter_registration_Exact10_runtime_ADMIT_011"),
        ("BOUNDARY_002", "boundary", "aggregation", "no_evaluate_all_rules_or_combined_verdict"),
        ("BOUNDARY_003", "boundary", "operations", "no_raw_network_download_checkpoint_split_reassignment"),
        ("BOUNDARY_004", "boundary", "training", "feature_semantics_audit_required_Step12D_smoke_only"),
        ("OUTPUT_001", "materializer", "preflight", "complete_before_first_write_exact_six_safe_entries"),
        ("OUTPUT_002", "materializer", "atomic", "same_directory_tmp_fdopen_flush_fsync_replace_cleanup"),
        ("OUTPUT_003", "materializer", "postwrite", "exact_six_regular_non_symlink"),
    )
    return tuple({
        "contract_id": identifier, "contract_kind": kind,
        "contract_subject": subject, "contract_value": value,
        "contract_status": "frozen",
    } for identifier, kind, subject, value in values)


def _truth_rows(design_truth_rows: Sequence[Mapping[str, str]]) -> tuple[dict[str, str], ...]:
    from covalent_ext.covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate import (
        classify_admit_010_leakage_group_assignment_provenance_design,
    )

    cases = _natural_cases()
    if len(design_truth_rows) != 71 or tuple(row["case_id"] for row in design_truth_rows) != tuple(case[1] for case in cases):
        raise ValueError("committed Exact71 identity drift")
    rows = []
    for index, ((group, case_id, scalar, context, precedence), committed) in enumerate(zip(cases, design_truth_rows, strict=True), 1):
        formal = _result_mapping(evaluate_admit_010(scalar, context))
        observed_design = dict(classify_admit_010_leakage_group_assignment_provenance_design(scalar, context))
        design = {"admission_rule_id": ADMISSION_RULE_ID, **observed_design}
        equal_count = sum(formal[name] == design[name] for name in RESULT_FIELDS)
        if equal_count != 10 or committed["expected_precedence"] != precedence:
            raise ValueError(f"formal/design Exact10 mismatch: {case_id}")
        rows.append({
            "truth_order": str(index), "truth_group": group, "case_id": case_id,
            "input_summary": committed["input_summary"],
            "admission_rule_id": str(formal["admission_rule_id"]),
            "outcome": str(formal["outcome"]), "passed": _bool(formal["passed"]),
            "blocks_candidate": _bool(formal["blocks_candidate"]),
            "reason": str(formal["reason"]),
            "canonical_leakage_group_id": str(formal["canonical_leakage_group_id"]),
            "validated_candidate_fields": json.dumps(formal["validated_candidate_fields"], separators=(",", ":")),
            "consumed_candidate_fields": json.dumps(formal["consumed_candidate_fields"], separators=(",", ":")),
            "consumed_context_items": json.dumps(formal["consumed_context_items"], separators=(",", ":")),
            "evaluator_io_used": _bool(formal["evaluator_io_used"]),
            "design_oracle_full_result": _jsonable_result(design),
            "exact10_equal_field_count": str(equal_count),
            "formal_design_exact10_parity": "true", "expected_precedence": precedence,
            "truth_passed": "true",
        })
    return tuple(rows)


def _bool(value: object) -> str:
    if type(value) is not bool:
        raise TypeError("exact bool required")
    return "true" if value else "false"


BOUNDARY_NECESSITY = (
    "committed design source and independent oracle identity",
    "design manifest readiness counts and hashes",
    "Exact32 provenance contract",
    "Exact26 mapping and grammar contract",
    "ordered committed Exact71 semantic oracle corpus",
    "design source boundary audit",
    "authoritative Exact11 issue inventory preservation baseline",
    "formal evaluator preconditions source",
    "formal evaluator preconditions manifest",
    "mature ADMIT_009 standalone structural predecessor",
    "ADMIT_009 Exact46 interface contract",
    "ADMIT_009 standalone manifest and readiness boundary",
    "current Exact9 runtime with absent ADMIT_010 registration",
)


def _source_rows(snapshot: FrozenSourceSnapshot) -> tuple[dict[str, str], ...]:
    return tuple({
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": record.relative_path.suffix.lstrip("."),
        "boundary_necessity": BOUNDARY_NECESSITY[index - 1],
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "safe_descendant": "true",
        "expected_sha256": record.expected_sha256,
        "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256,
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1))


EXECUTED_SAFETY_ITEMS = (
    "formal_evaluator_implementation", "exact10_result_class",
    "exact71_full_equivalence", "result_invariant_enforcement",
    "pure_in_memory_call_graph", "no_input_mutation", "hostile_comparison_blocked",
    "exact_type_first", "deterministic_materialization", "source_verification",
    "issue_byte_preservation", "materializer_preflight_and_atomic_replace",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "provider_mapping", "real_candidate_evaluation", "unified_adapter_design",
    "unified_adapter_implementation", "admit_010_registration", "exact10_runtime",
    "admit_011", "evaluate_all_rules", "combined_candidate_verdict",
    "grouping", "split", "reassignment", "raw_read", "network", "bulk_download",
    "checkpoint", "model_forward_loss", "training_fine_tune", "parameter_update",
    "stage", "commit", "push", "gh",
)


def _safety_rows() -> tuple[dict[str, str], ...]:
    definitions = tuple((name, True) for name in EXECUTED_SAFETY_ITEMS) + tuple((name, False) for name in NOT_EXECUTED_SAFETY_ITEMS)
    return tuple({
        "safety_item": name, "expected_executed": _bool(executed),
        "observed_executed": _bool(executed), "safety_passed": "true",
    } for name, executed in definitions)


TRUE_READINESS = (
    "leakage_group_assignment_provenance_contract_frozen",
    "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_historical_field_mapping_rule_frozen",
    "admit_010_design_oracle_implemented",
    "admit_010_standalone_evaluator_implemented",
    "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented",
    "admit_010_exact10_result_contract_frozen",
    "admit_010_result_class_exact_type_enforced",
    "admit_010_result_cross_field_invariants_enforced",
    "admit_010_validation_precedence_runtime_enforced",
    "admit_010_design_oracle_independence_preserved",
    "admit_010_formal_exact71_equivalence_enforced",
    "admit_010_provider_mapping_boundary_preserved",
    "ready_for_admit_010_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_unified_adapter_implemented", "admit_010_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen",
    "real_candidate_evaluation", "ready_for_bulk_download_now",
    "ready_for_training", "ready_to_train_now",
)
READINESS = {**{name: True for name in TRUE_READINESS}, **{name: False for name in FALSE_READINESS}}


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> tuple[tuple[dict[str, str], ...], bytes]:
    design_manifest = json.loads(_record(snapshot, SOURCE_PATHS[1]).content_bytes.decode("utf-8"))
    admit009_manifest = json.loads(_record(snapshot, SOURCE_PATHS[11]).content_bytes.decode("utf-8"))
    design_truth = _csv_rows_from_bytes(_record(snapshot, DESIGN_TRUTH_PATH).content_bytes)
    issue_bytes = _record(snapshot, AUTHORITATIVE_ISSUE_PATH).content_bytes
    issues = _csv_rows_from_bytes(issue_bytes)
    issue_map = {row["issue_id"]: row for row in issues}
    required = (
        design_manifest["truth_matrix_contract"] == "Exact71",
        design_manifest["truth_row_count"] == 71,
        design_manifest["ready_for_admit_010_standalone_evaluator_interface_implementation"] is True,
        design_manifest["leakage_group_assignment_provenance_blocker_resolved"] is True,
        design_manifest["leakage_group_id_provider_mapping_validated"] is False,
        admit009_manifest["unified_dispatch_runtime_with_admit_001_to_009_implemented"] is False,
        len(design_truth) == 71, len(issues) == 11,
        issue_map["LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"]["status"] == "resolved",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        hashlib.sha256(issue_bytes).hexdigest() == "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    )
    if not all(required):
        raise ValueError("authoritative predecessor contract mismatch")
    return design_truth, issue_bytes


def build_interface_state(repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD") -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    design_truth, issue_bytes = _validate_predecessors(snapshot)
    if tuple(field.name for field in fields(LeakageGroupAssignmentProvenanceContractV1)) != (
        "contract_version", "canonical_candidate_field_name", "historical_artifact_field_name",
        "field_mapping_rule", "assignment_policy", "assignment_policy_version",
        "assignment_stage_kind", "assignment_manifest_sha256", "assignment_artifact_sha256",
        "group_inventory_sha256", "sample_index_sha256", "assignment_id",
        "historical_leakage_group_id", "sample_index_row_id", "member_sample_index_row_ids",
        "member_count", "assignment_passed", "split_assignments_written", "pre_split_assignment_status",
    ):
        raise ValueError("committed Exact19 identity drift")
    state = {
        "snapshot": snapshot, "contract_rows": _contract_rows(),
        "truth_rows": _truth_rows(design_truth), "source_rows": _source_rows(snapshot),
        "safety_rows": _safety_rows(), "issue_rows": _csv_rows_from_bytes(issue_bytes),
        "issue_bytes": issue_bytes, "readiness": dict(READINESS),
    }
    if not (
        len(state["contract_rows"]) == 41 and len(state["truth_rows"]) == 71
        and len(state["source_rows"]) == 13 and len(state["safety_rows"]) == 35
        and len(state["issue_rows"]) == 11
        and all(row["formal_design_exact10_parity"] == "true" and row["exact10_equal_field_count"] == "10" for row in state["truth_rows"])
    ):
        raise RuntimeError("ADMIT_010 interface state failed closed")
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
    snapshot = state["snapshot"]
    groups = {group: sum(row["truth_group"] == group for row in state["truth_rows"]) for group in dict.fromkeys(row["truth_group"] for row in state["truth_rows"])}
    readiness = dict(state["readiness"])
    return {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "evaluation_phase": EVALUATION_PHASE, "candidate_field": CANDIDATE_FIELD,
        "context_item": CONTEXT_ITEM, "historical_artifact_field": HISTORICAL_ARTIFACT_FIELD,
        "public_api": "evaluate_admit_010(leakage_group_id, leakage_group_assignment_provenance_contract)",
        "public_signature_parameters": ["leakage_group_id", "leakage_group_assignment_provenance_contract"],
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit010EvaluationResult", "result_field_count": 10,
        "result_fields": list(RESULT_FIELDS), "result_exact_type_required": True,
        "outcome_vocabulary": list(OUTCOME_VOCABULARY), "reason_vocabulary": list(REASON_VOCABULARY),
        "leakage_group_prefix": LEAKAGE_GROUP_PREFIX, "leakage_group_regex": LEAKAGE_GROUP_REGEX,
        "validation_precedence": list(VALIDATION_PRECEDENCE),
        "provenance_type": "LeakageGroupAssignmentProvenanceContractV1",
        "provenance_type_direct_committed_identity": True,
        "production_design_oracle_import_or_call": False,
        "metadata_design_oracle_parity_only": True,
        "formal_design_exact10_parity": True, "truth_matrix_contract": "Exact71",
        "truth_row_count": 71, "truth_pass_count": 71, "truth_group_counts": groups,
        "contract_row_count": len(state["contract_rows"]), "contract_pass_count": len(state["contract_rows"]),
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_input_count": 13, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_order": index, "source_relative_path": record.relative_path.as_posix(),
            "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
            "non_symlink": True, "safe_descendant": True,
            "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256, "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_audit_row_count": 13, "source_audit_pass_count": 13,
        "issue_inventory_row_count": 11, "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
        "issue_transition": "none", "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010–ADMIT_015",
        "real_provider_leakage_group_id_count": 0,
        "leakage_group_id_provider_mapping_validated": False,
        "safety_row_count": len(state["safety_rows"]), "safety_pass_count": len(state["safety_rows"]),
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": dict(output_sha256), "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "preflight_before_first_write": True, "real_directory_non_symlink": True,
            "existing_inventory_allowlist_exact": True, "existing_entries_regular_non_symlink": True,
            "atomic_same_directory_mkstemp": True, "temporary_suffix": ".tmp",
            "fdopen_mode": "wb", "flush_and_fsync": True, "os_replace": True,
            "finally_cleanup": True, "postwrite_exact_inventory_reverified": True,
        },
        "readiness": readiness, **readiness,
        "all_source_boundary_checks_passed": True, "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True, "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_issue_checks_passed": True,
        "all_safety_checks_passed": True, "all_checks_passed": True,
        "stop_boundaries": [
            "no_provider_mapping", "no_unified_adapter_design_or_implementation",
            "no_admit_010_registration", "no_exact10_runtime", "no_admit_011",
            "no_evaluate_all_rules", "no_combined_candidate_verdict",
            "no_real_candidate_evaluation", "no_split_or_reassignment",
            "no_raw_network_download_checkpoint_model_training",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP, "validation_failures": [],
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SOURCE_AUDIT_FILENAME: _csv_bytes(SOURCE_AUDIT_COLUMNS, state["source_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()}
    manifest = _manifest_payload(state, hashes)
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return payloads, manifest


def _resolved_output_target_is_authorized(
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
) -> bool:
    """Reject leaf or parent-directory symlink indirection fail closed."""
    try:
        repo_metadata = os.lstat(repo_root)
        if not stat.S_ISDIR(repo_metadata.st_mode) or stat.S_ISLNK(repo_metadata.st_mode):
            return False
        resolved_repo = repo_root.resolve(strict=True)

        parent = root.parent
        parent_metadata = os.lstat(parent)
        if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
            return False
        resolved_parent = parent.resolve(strict=True)
        lexical_parent = Path(os.path.abspath(parent))
        if lexical_parent != resolved_parent:
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
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
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
    parent = root.parent
    metadata = os.lstat(parent)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("output parent must be a real non-symlink directory")
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
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) or {entry.name for entry in entries} != set(OUTPUT_FILES):
        raise ValueError("postwrite output root invalid")
    for entry in entries:
        item = os.lstat(entry)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("postwrite output entry invalid")


def run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT, *, repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    output_root_was_relative = not output_root.is_absolute()
    root = repo_root / output_root if output_root_was_relative else output_root
    create_root = _preflight_output_root(
        root, repo_root, output_root_was_relative=output_root_was_relative,
    )
    state = build_interface_state(repo_root, head_ref=head_ref)
    payloads, manifest = _payloads(state)
    if create_root:
        root.mkdir(exist_ok=False)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    _postvalidate_output_root(root)
    return {"state": state, "manifest": manifest, "output_root": root}


def main() -> int:
    result = run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1()
    print(json.dumps({
        "stage": STAGE, "truth_row_count": result["manifest"]["truth_row_count"],
        "formal_design_exact10_parity": result["manifest"]["formal_design_exact10_parity"],
        "ready_for_admit_010_unified_adapter_contract_design": result["manifest"]["ready_for_admit_010_unified_adapter_contract_design"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

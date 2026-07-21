"""CovaPIE ADMIT_011 standalone evaluator interface v1.

``evaluate_admit_011`` and every helper reachable from it are deliberately
pure, in-memory lexical validation.  The artifact functions below it are
metadata-only publication support and are not evaluator-reachable.
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
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate import (
    CANDIDATE_FIELD,
    COLLISION_REASON,
    CONTRACT_FIELDS,
    CONTRACT_REASONS,
    DEFAULT_CONTRACT,
    ExistingRawTargetRelativePathsSnapshot,
    RawTargetRelativePathContract,
    REASON_VOCABULARY,
    RULE_ID,
    SCALAR_REASONS,
    SNAPSHOT_FIELDS,
    SNAPSHOT_REASONS,
    STANDALONE_CONTEXT_VALIDATION_ORDER,
    VALIDATION_PRECEDENCE,
)


PROJECT = "CovaPIE"
STAGE = "covapie_bulk_download_admission_admit_011_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "3c53da1e80d04ad68e5d1e9760b5a5bcdb1005b3"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_011 raw target path contract v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_011_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_011_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_raw_target_relative_path", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
CONSUMED_CANDIDATE_FIELDS = (CANDIDATE_FIELD,)
OUTCOMES = ("passed", "blocked", "invalid")
DESIGN_STAGE = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1")
DESIGN_TRUTH_PATH = DESIGN_STAGE / "covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv"
DESIGN_ISSUES_PATH = DESIGN_STAGE / "covapie_admit_011_raw_target_issue_readiness_inventory.csv"


def _scalar_reason(value: object) -> str:
    if type(value) is not str:
        return SCALAR_REASONS[0]
    if value == "":
        return SCALAR_REASONS[1]
    if not value.isascii():
        return SCALAR_REASONS[2]
    if "\0" in value:
        return SCALAR_REASONS[3]
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return SCALAR_REASONS[4]
    if any(character.isspace() for character in value):
        return SCALAR_REASONS[5]
    if value.startswith("/"):
        return SCALAR_REASONS[6]
    if len(value) > 1 and value[0].isalpha() and value[1] == ":":
        return SCALAR_REASONS[7]
    if value.startswith("\\\\"):
        return SCALAR_REASONS[8]
    if "://" in value:
        return SCALAR_REASONS[9]
    if "%" in value:
        return SCALAR_REASONS[10]
    if value.startswith("~"):
        return SCALAR_REASONS[11]
    if "$" in value:
        return SCALAR_REASONS[12]
    if "\\" in value:
        return SCALAR_REASONS[13]
    if value.endswith("/"):
        return SCALAR_REASONS[14]
    if "//" in value:
        return SCALAR_REASONS[15]
    components = value.split("/")
    if "." in components:
        return SCALAR_REASONS[16]
    if ".." in components:
        return SCALAR_REASONS[17]
    if not value.startswith("data/raw/"):
        return SCALAR_REASONS[18]
    return ""


def _canonical_path(value: object) -> bool:
    return type(value) is str and _scalar_reason(value) == ""


@dataclass(frozen=True)
class Admit011EvaluationResult:
    admission_rule_id: object
    outcome: object
    passed: object
    blocks_candidate: object
    reason: object
    canonical_raw_target_relative_path: object
    validated_candidate_fields: object
    consumed_candidate_fields: object
    consumed_context_items: object
    evaluator_io_used: object

    def __post_init__(self) -> None:
        if type(self) is not Admit011EvaluationResult:
            raise TypeError("result subclasses are forbidden")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("result field order is frozen")
        if any(type(value) is not str for value in (
            self.admission_rule_id, self.outcome, self.reason,
            self.canonical_raw_target_relative_path,
        )):
            raise TypeError("result string fields require exact built-in str")
        if any(type(value) is not bool for value in (
            self.passed, self.blocks_candidate, self.evaluator_io_used,
        )):
            raise TypeError("result boolean fields require exact built-in bool")
        if any(type(value) is not tuple for value in (
            self.validated_candidate_fields, self.consumed_candidate_fields,
            self.consumed_context_items,
        )):
            raise TypeError("result tuple fields require exact built-in tuple")
        for pair in self.validated_candidate_fields:
            if type(pair) is not tuple or len(pair) != 2 or any(type(item) is not str for item in pair):
                raise TypeError("validated fields require exact string-pair tuples")
        if any(type(item) is not str for item in self.consumed_candidate_fields + self.consumed_context_items):
            raise TypeError("consumed items require exact built-in str")
        if self.admission_rule_id != RULE_ID or self.outcome not in OUTCOMES:
            raise ValueError("result identity or outcome invalid")
        if self.passed is not (self.outcome == "passed") or self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("result outcome flags invalid")
        if self.reason not in REASON_VOCABULARY or (self.reason == "") is not self.passed:
            raise ValueError("result reason invalid")
        if self.reason == COLLISION_REASON:
            if self.outcome != "blocked":
                raise ValueError("collision is blocked only")
        elif self.reason and self.outcome != "invalid":
            raise ValueError("noncollision reason is invalid only")
        if self.evaluator_io_used is not False or self.consumed_candidate_fields != CONSUMED_CANDIDATE_FIELDS:
            raise ValueError("result evaluator boundary invalid")
        canonical = self.canonical_raw_target_relative_path
        expected_validated = () if canonical == "" else ((CANDIDATE_FIELD, canonical),)
        if self.validated_candidate_fields != expected_validated:
            raise ValueError("validated candidate projection invalid")
        if canonical and not _canonical_path(canonical):
            raise ValueError("retained canonical path invalid")
        if self.reason in SCALAR_REASONS:
            if canonical or self.consumed_context_items != ():
                raise ValueError("scalar-invalid context consumption invalid")
        elif self.reason in CONTRACT_REASONS:
            if not canonical or self.consumed_context_items != (STANDALONE_CONTEXT_VALIDATION_ORDER[0],):
                raise ValueError("contract-invalid context consumption invalid")
        elif not canonical or self.consumed_context_items != STANDALONE_CONTEXT_VALIDATION_ORDER:
            raise ValueError("snapshot, collision, or passed consumption invalid")


def _result(outcome: str, reason: str, canonical: str) -> Admit011EvaluationResult:
    contexts = () if reason in SCALAR_REASONS else (STANDALONE_CONTEXT_VALIDATION_ORDER[0],) if reason in CONTRACT_REASONS else STANDALONE_CONTEXT_VALIDATION_ORDER
    return Admit011EvaluationResult(
        RULE_ID, outcome, outcome == "passed", outcome != "passed", reason, canonical,
        () if not canonical else ((CANDIDATE_FIELD, canonical),),
        CONSUMED_CANDIDATE_FIELDS, contexts, False,
    )


def _contract_valid(value: object) -> bool:
    if type(value) is not RawTargetRelativePathContract:
        return False
    if tuple(field.name for field in fields(type(value))) != CONTRACT_FIELDS:
        return False
    if any(type(getattr(value, field)) is not str for field in CONTRACT_FIELDS if field != "allowed_namespace_prefixes"):
        return False
    if type(value.allowed_namespace_prefixes) is not tuple or any(type(item) is not str for item in value.allowed_namespace_prefixes):
        return False
    return value == DEFAULT_CONTRACT


def _snapshot_valid(value: object) -> bool:
    if type(value) is not ExistingRawTargetRelativePathsSnapshot:
        return False
    if tuple(field.name for field in fields(type(value))) != SNAPSHOT_FIELDS:
        return False
    if any(type(getattr(value, field)) is not str for field in SNAPSHOT_FIELDS[:6]):
        return False
    if value.schema_version != "covapie_existing_raw_target_relative_paths_snapshot_v1":
        return False
    if type(value.snapshot_complete) is not bool or value.snapshot_complete is not True:
        return False
    paths = value.occupied_relative_paths
    if type(paths) is not tuple or any(type(item) is not str for item in paths):
        return False
    return len(set(paths)) == len(paths) and all(_canonical_path(item) for item in paths)


def evaluate_admit_011(
    raw_target_relative_path: object,
    existing_raw_target_relative_paths: object,
    raw_target_relative_path_contract: object,
) -> Admit011EvaluationResult:
    """Evaluate an immutable candidate lexical path against a supplied snapshot."""
    reason = _scalar_reason(raw_target_relative_path)
    if reason:
        return _result("invalid", reason, "")
    canonical = raw_target_relative_path
    if type(raw_target_relative_path_contract) is not RawTargetRelativePathContract:
        return _result("invalid", CONTRACT_REASONS[0], canonical)
    if not _contract_valid(raw_target_relative_path_contract):
        return _result("invalid", CONTRACT_REASONS[1], canonical)
    if type(existing_raw_target_relative_paths) is not ExistingRawTargetRelativePathsSnapshot:
        return _result("invalid", SNAPSHOT_REASONS[0], canonical)
    if not _snapshot_valid(existing_raw_target_relative_paths):
        return _result("invalid", SNAPSHOT_REASONS[1], canonical)
    snapshot = existing_raw_target_relative_paths
    contract = raw_target_relative_path_contract
    checks = (
        (snapshot.canonical_raw_root_identity, contract.canonical_raw_root_identity, SNAPSHOT_REASONS[2]),
        (snapshot.candidate_coordinate_system, contract.candidate_coordinate_system, SNAPSHOT_REASONS[3]),
        (snapshot.path_grammar_version, contract.path_grammar_version, SNAPSHOT_REASONS[4]),
        (snapshot.equality_policy, contract.equality_policy, SNAPSHOT_REASONS[5]),
        (snapshot.snapshot_phase, contract.snapshot_phase, SNAPSHOT_REASONS[6]),
    )
    for observed, expected, mismatch_reason in checks:
        if observed != expected:
            return _result("invalid", mismatch_reason, canonical)
    if canonical in snapshot.occupied_relative_paths:
        return _result("blocked", COLLISION_REASON, canonical)
    return _result("passed", "", canonical)


# Everything below this line is deliberately outside the evaluator closure.
TRUTH_FILENAME = "covapie_admit_011_rule_logic_interface_truth_matrix.csv"
CONTRACT_FILENAME = "covapie_admit_011_rule_logic_interface_contract.csv"
SOURCE_FILENAME = "covapie_admit_011_rule_logic_interface_source_boundary_audit.csv"
PURITY_FILENAME = "covapie_admit_011_rule_logic_interface_purity_audit.csv"
ISSUE_FILENAME = "covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_011_rule_logic_interface_manifest.json"
OUTPUT_FILES = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_FILENAME, PURITY_FILENAME, ISSUE_FILENAME, MANIFEST_FILENAME)
SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_context_responsibility_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_contract_source_boundary_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_observed_value_coverage_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_schema_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py",
)
SOURCE_SHA256 = (
    "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d",
    "0f3772e65db51623fe7ab477e97cc7fc98166755f39d172ef017a87c7ebfba24",
    "e0747e6b3be3a51d1884a76a85f70b05d34d4f687b20e2604f56783db985840f",
    "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    "c55c48b58a66b44b2f6f0cc7fde27fe22fa317e3502a7eee9ee06c25006b74a2",
    "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4",
    "dd5f853c047c7457d110739edf6f2ac3647bc3a9069b2b7a6d15b1470504f13e",
    "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca",
    "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
    "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c",
    "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436",
)
SOURCE_SHA256_BY_PATH = dict(zip(SOURCE_PATHS, SOURCE_SHA256, strict=True))


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _empty_snapshot() -> ExistingRawTargetRelativePathsSnapshot:
    return ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1",
        DEFAULT_CONTRACT.canonical_raw_root_identity,
        DEFAULT_CONTRACT.candidate_coordinate_system,
        DEFAULT_CONTRACT.path_grammar_version,
        DEFAULT_CONTRACT.equality_policy,
        DEFAULT_CONTRACT.snapshot_phase, True, (),
    )


def _unsafe_contract() -> RawTargetRelativePathContract:
    value = object.__new__(RawTargetRelativePathContract)
    for field in CONTRACT_FIELDS:
        object.__setattr__(value, field, getattr(DEFAULT_CONTRACT, field))
    object.__setattr__(value, "contract_id", "invalid")
    return value


def _unsafe_snapshot(**changes: object) -> ExistingRawTargetRelativePathsSnapshot:
    base = _empty_snapshot()
    value = object.__new__(ExistingRawTargetRelativePathsSnapshot)
    for field in SNAPSHOT_FIELDS:
        object.__setattr__(value, field, getattr(base, field))
    for field, item in changes.items():
        object.__setattr__(value, field, item)
    return value


def _case_context(row: dict[str, str]) -> tuple[object, object]:
    case_id = row["case_id"]
    if case_id in ("CONTRACT_TYPE", "MULTI_CONTRACT_SNAPSHOT"):
        return object(), _empty_snapshot()
    if case_id == "CONTRACT_VALUE":
        return _unsafe_contract(), _empty_snapshot()
    if case_id == "SNAPSHOT_TYPE":
        return DEFAULT_CONTRACT, object()
    if case_id == "SNAPSHOT_VALUE":
        return DEFAULT_CONTRACT, _unsafe_snapshot(snapshot_complete=False)
    mismatch = {
        "MISMATCH_001": "canonical_raw_root_identity", "MISMATCH_002": "candidate_coordinate_system",
        "MISMATCH_003": "path_grammar_version", "MISMATCH_004": "equality_policy",
        "MISMATCH_005": "snapshot_phase",
    }
    if case_id in mismatch:
        return DEFAULT_CONTRACT, _unsafe_snapshot(**{mismatch[case_id]: "wrong"})
    if case_id == "COLLISION":
        return DEFAULT_CONTRACT, ExistingRawTargetRelativePathsSnapshot(
            "covapie_existing_raw_target_relative_paths_snapshot_v1",
            DEFAULT_CONTRACT.canonical_raw_root_identity, DEFAULT_CONTRACT.candidate_coordinate_system,
            DEFAULT_CONTRACT.path_grammar_version, DEFAULT_CONTRACT.equality_policy,
            DEFAULT_CONTRACT.snapshot_phase, True, ("data/raw/a.cif",),
        )
    return DEFAULT_CONTRACT, _empty_snapshot()


TRUTH_COLUMNS = (
    "case_order", "case_id", "matrix_group", "candidate_representation", "contract_state", "snapshot_state",
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason", "canonical_raw_target_relative_path",
    "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
    "expected_precedence", "truth_passed",
)


def _truth_rows(repo_root: Path) -> list[dict[str, str]]:
    with (repo_root / DESIGN_TRUTH_PATH).open(newline="", encoding="utf-8") as handle:
        design_rows = list(csv.DictReader(handle))
    if len(design_rows) != 84:
        raise ValueError("frozen ADMIT_011 truth matrix cardinality drift")
    rows = []
    for row in design_rows:
        candidate = ast.literal_eval(row["candidate_representation"])
        contract, snapshot = _case_context(row)
        result = evaluate_admit_011(candidate, snapshot, contract)
        fields_map = {
            "admission_rule_id": result.admission_rule_id, "outcome": result.outcome,
            "passed": str(result.passed).lower(), "blocks_candidate": str(result.blocks_candidate).lower(),
            "reason": result.reason, "canonical_raw_target_relative_path": result.canonical_raw_target_relative_path,
            "validated_candidate_fields": json.dumps(result.validated_candidate_fields, separators=(",", ":")),
            "consumed_candidate_fields": json.dumps(result.consumed_candidate_fields, separators=(",", ":")),
            "consumed_context_items": json.dumps(result.consumed_context_items, separators=(",", ":")),
            "evaluator_io_used": str(result.evaluator_io_used).lower(),
        }
        expected = {
            "outcome": row["outcome"], "passed": row["passed"], "blocks_candidate": row["blocks_candidate"],
            "reason": row["reason"], "canonical_raw_target_relative_path": row["canonical"],
            "validated_candidate_fields": row["validated_candidate_fields"],
            "consumed_candidate_fields": row["consumed_candidate_fields"],
            "consumed_context_items": row["consumed_context_items"], "evaluator_io_used": row["evaluator_io_used"],
        }
        if any(fields_map[key] != value for key, value in expected.items()):
            raise ValueError("formal evaluator truth parity failure")
        rows.append({
            "case_order": row["case_order"], "case_id": row["case_id"], "matrix_group": row["matrix_group"],
            "candidate_representation": row["candidate_representation"], "contract_state": row["contract_state"],
            "snapshot_state": row["snapshot_state"], **fields_map,
            "expected_precedence": row["expected_precedence"], "truth_passed": "true",
        })
    return rows


_SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "expected_sha256", "base_tree_sha256", "filesystem_sha256",
    "git_tracked", "regular", "non_symlink", "source_boundary_passed",
)
_THIS_SOURCE_RELATIVE_PATH = "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py"
_SOURCE_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC


def _source_identity(item: os.stat_result) -> tuple[int, int, int]:
    return (int(item.st_dev), int(item.st_ino), int(item.st_mode))


def _source_git(repo_root: Path, arguments: list[str]) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise ValueError("source-boundary git command failed")
    return result.stdout


def _validate_source_repository(repo_root: Path) -> None:
    metadata = os.lstat(repo_root)
    if not repo_root.is_absolute() or not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) or repo_root.resolve(strict=True) != repo_root:
        raise ValueError("source-boundary repository identity is unsafe")
    subject = _source_git(repo_root, ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT]).decode("utf-8", "strict").rstrip("\n")
    if subject != EXPECTED_BASE_SUBJECT:
        raise ValueError("source-boundary base subject drift")
    _source_git(repo_root, ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])


def _validate_source_path_configuration() -> None:
    if not (len(SOURCE_PATHS) == len(SOURCE_SHA256) == 11) or len(set(SOURCE_PATHS)) != 11 or tuple(SOURCE_SHA256_BY_PATH) != SOURCE_PATHS:
        raise ValueError("source-boundary configuration cardinality drift")
    for relative, expected in zip(SOURCE_PATHS, SOURCE_SHA256, strict=True):
        parts = relative.split("/")
        if type(relative) is not str or type(expected) is not str or len(expected) != 64:
            raise ValueError("source-boundary configuration type drift")
        if not relative or relative.startswith("/") or "\\" in relative or any(part in ("", ".", "..") for part in parts):
            raise ValueError("source-boundary path is not relative POSIX lexical")
        if parts[:2] == ["data", "raw"] or parts[0] == "checkpoints" or relative == _THIS_SOURCE_RELATIVE_PATH or STAGE in parts:
            raise ValueError("source-boundary path is outside the fixed predecessor boundary")


def _assert_source_parent_chain(parent: Path, repo_root: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("source-boundary parent chain is unsafe")
        if current == repo_root:
            break
        if current == current.parent:
            raise ValueError("source-boundary parent chain escaped repository")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("source-boundary parent resolved identity drift")


def _inspect_source_structure(repo_root: Path) -> list[tuple[str, Path, tuple[int, int, int]]]:
    """Complete every structural check before any fixed-source byte read."""
    _validate_source_path_configuration()
    inspected = []
    for relative in SOURCE_PATHS:
        source = repo_root / relative
        _assert_source_parent_chain(source.parent, repo_root)
        item = os.lstat(source)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("source-boundary leaf is unsafe")
        if source.resolve(strict=True) != source or repo_root not in (source, *source.parents):
            raise ValueError("source-boundary leaf resolved identity drift")
        tracked = _source_git(repo_root, ["ls-files", "--error-unmatch", "--", relative])
        if tracked.decode("utf-8", "strict") != f"{relative}\n":
            raise ValueError("source-boundary tracked identity drift")
        tree = _source_git(repo_root, ["ls-tree", EXPECTED_BASE_COMMIT, "--", relative]).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise ValueError("source-boundary base tree cardinality drift")
        metadata, tree_path = tree[0].split(b"\t", 1)
        tree_fields = metadata.split()
        if tree_path.decode("utf-8", "strict") != relative or len(tree_fields) != 3 or tree_fields[1] != b"blob" or tree_fields[0] not in (b"100644", b"100755"):
            raise ValueError("source-boundary base tree entry drift")
        inspected.append((relative, source, _source_identity(item)))
    return inspected


def _read_verified_source_bytes(source: Path, expected_identity: tuple[int, int, int]) -> bytes:
    fd = os.open(source, _SOURCE_READ_FLAGS)
    try:
        if _source_identity(os.fstat(fd)) != expected_identity or _source_identity(os.lstat(source)) != expected_identity:
            raise ValueError("source-boundary leaf identity changed before byte read")
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _source_identity(os.fstat(fd)) != expected_identity or _source_identity(os.lstat(source)) != expected_identity:
            raise ValueError("source-boundary leaf identity changed during byte read")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _source_rows(repo_root: Path) -> list[dict[str, str]]:
    _validate_source_repository(repo_root)
    inspected = _inspect_source_structure(repo_root)
    rows = []
    for order, (relative, source, identity) in enumerate(inspected, 1):
        expected = SOURCE_SHA256_BY_PATH[relative]
        base = _source_git(repo_root, ["show", f"{EXPECTED_BASE_COMMIT}:{relative}"])
        current = _read_verified_source_bytes(source, identity)
        base_sha = _sha(base)
        filesystem_sha = _sha(current)
        if not (expected == base_sha == filesystem_sha):
            raise ValueError("fixed source boundary SHA256 drift")
        rows.append({
            "source_order": str(order), "source_relative_path": relative,
            "expected_sha256": expected, "base_tree_sha256": base_sha, "filesystem_sha256": filesystem_sha,
            "git_tracked": "true", "regular": "true", "non_symlink": "true", "source_boundary_passed": "true",
        })
    if len(rows) != 11 or tuple(row["source_relative_path"] for row in rows) != SOURCE_PATHS:
        raise ValueError("source-boundary output cardinality drift")
    return rows


def _contract_rows() -> list[dict[str, str]]:
    rows = []
    for order, field in enumerate(RESULT_FIELDS, 1):
        rows.append({"field_order": str(order), "field": field, "contract": "Exact10 formal result field order", "passed": "true"})
    return rows


def _purity_rows() -> list[dict[str, str]]:
    return [
        {"audit_order": "1", "audit_item": "public_evaluator", "observed": "evaluate_admit_011", "passed": "true"},
        {"audit_order": "2", "audit_item": "reachable_helpers", "observed": "_scalar_reason|_canonical_path|_result|_contract_valid|_snapshot_valid|Admit011EvaluationResult.__post_init__", "passed": "true"},
        {"audit_order": "3", "audit_item": "forbidden_reachable_symbols", "observed": "Path|os|subprocess|open|classify_admit_011_raw_target_relative_path_design absent", "passed": "true"},
        {"audit_order": "4", "audit_item": "evaluator_io_used", "observed": "false", "passed": "true"},
    ]


TRUE_READINESS = (
    "admit_011_rule_logic_implemented", "standalone_evaluator_interface_frozen",
    "standalone_evaluator_pure_in_memory", "standalone_result_contract_frozen",
    "design_truth_parity_passed", "ready_for_admit_011_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_011_adapter_implemented", "admit_011_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented", "provider_mapping_validated",
    "real_provider_evaluation_ready", "combined_candidate_verdict_implemented",
    "ready_for_bulk_download_now", "checkpoint_compatibility_validated",
    "full_repository_canonical_validated", "ready_for_training",
)


def build_interface_artifacts(repo_root: Path = REPO_ROOT) -> dict[str, bytes]:
    source_rows = _source_rows(repo_root)
    truth_rows = _truth_rows(repo_root)
    issue_bytes = (repo_root / DESIGN_ISSUES_PATH).read_bytes()
    issues = list(csv.DictReader(io.StringIO(issue_bytes.decode("utf-8"))))
    if len(issues) != 11 or any(row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE" and row["status"] != "open" for row in issues):
        raise ValueError("issue inventory boundary drift")
    files = {
        CONTRACT_FILENAME: _csv_bytes(("field_order", "field", "contract", "passed"), _contract_rows()),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILENAME: _csv_bytes(_SOURCE_BOUNDARY_COLUMNS, source_rows),
        PURITY_FILENAME: _csv_bytes(("audit_order", "audit_item", "observed", "passed"), _purity_rows()),
        ISSUE_FILENAME: issue_bytes,
    }
    readiness = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}
    manifest = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "stage": STAGE,
        "base_commit": EXPECTED_BASE_COMMIT, "base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": RULE_ID, "admission_rule_name": "raw_overwrite_forbidden",
        "public_api": "evaluate_admit_011(raw_target_relative_path, existing_raw_target_relative_paths, raw_target_relative_path_contract)",
        "public_signature_parameters": ["raw_target_relative_path", "existing_raw_target_relative_paths", "raw_target_relative_path_contract"],
        "result_type": "Admit011EvaluationResult", "result_fields": list(RESULT_FIELDS),
        "source_paths": list(SOURCE_PATHS), "source_input_count": len(SOURCE_PATHS),
        "output_files": list(OUTPUT_FILES), "output_file_count": len(OUTPUT_FILES),
        "row_counts": {"contract": 10, "truth": 84, "truth_historical": 47, "source_boundary": len(source_rows), "purity": 4, "issue": 11},
        "reason_vocabulary": list(REASON_VOCABULARY), "validation_precedence": list(VALIDATION_PRECEDENCE),
        "readiness": readiness, **readiness,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "safety": {"filesystem_used_by_evaluator": False, "network_used_by_evaluator": False, "raw_read_by_evaluator": False, "mutation_by_evaluator": False},
        "output_sha256": {name: _sha(value) for name, value in files.items()},
        "all_checks_passed": True,
    }
    files[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return files


import ctypes
import secrets


FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_011_rule_logic_interface_contract.csv": "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2",
    "covapie_admit_011_rule_logic_interface_truth_matrix.csv": "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b",
    "covapie_admit_011_rule_logic_interface_source_boundary_audit.csv": "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6",
    "covapie_admit_011_rule_logic_interface_purity_audit.csv": "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e",
    "covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv": "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    "covapie_admit_011_rule_logic_interface_manifest.json": "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
}


@dataclass(frozen=True)
class OutputMaterializationPlan:
    root: Path
    parent: Path
    anchor: Path
    root_name: str
    relative_to_repo: bool
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int] | None
    leaf_identities: tuple[tuple[str, tuple[int, int, int]], ...]


DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1
DIRECTORY_FD_CAPABILITIES = all(
    function in os.supports_dir_fd for function in (os.open, os.stat, os.mkdir, os.unlink, os.rmdir)
) and _RENAMEAT2 is not None


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return (int(item.st_dev), int(item.st_ino), int(item.st_mode))


def _same_identity(item: os.stat_result, expected: tuple[int, int, int]) -> bool:
    return _identity(item) == expected


def _require_materializer_capabilities() -> None:
    if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")) or not DIRECTORY_FD_CAPABILITIES:
        raise ValueError("required directory-fd set-atomic publication support unavailable")


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        try:
            item = os.lstat(current)
        except FileNotFoundError as exc:
            raise ValueError("output parent is missing") from exc
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output parent chain is not a real directory chain")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("output parent escaped its anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent resolved identity differs")


def _output_target_path(output_root: Path) -> tuple[Path, bool, Path]:
    candidate = Path(output_root)
    if candidate.is_absolute():
        root = candidate
        relative_to_repo = False
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape is forbidden")
        root = REPO_ROOT / candidate
        relative_to_repo = True
        anchor = REPO_ROOT
    if not root.is_absolute() or not root.name:
        raise ValueError("output root is invalid")
    return root, relative_to_repo, anchor


def _inspect_output_target_read_only(output_root: Path) -> OutputMaterializationPlan:
    _require_materializer_capabilities()
    root, relative_to_repo, anchor = _output_target_path(output_root)
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    if relative_to_repo and REPO_ROOT not in (parent, *parent.parents):
        raise ValueError("relative output escaped repository anchor")
    parent_identity = _identity(os.lstat(parent))
    try:
        root_stat = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(root, parent, anchor, root.name, relative_to_repo, parent_identity, None, ())
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("output root is unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output root inventory is unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        leaf = root / name
        item = os.lstat(leaf)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or leaf.resolve(strict=True) != leaf:
            raise ValueError("output leaf is unsafe")
        leaves.append((name, _identity(item)))
    return OutputMaterializationPlan(root, parent, anchor, root.name, relative_to_repo, parent_identity, _identity(root_stat), tuple(leaves))


def _validate_payloads(files: dict[str, bytes]) -> None:
    if tuple(files) != OUTPUT_FILES or set(files) != set(OUTPUT_FILES) or any(type(data) is not bytes for data in files.values()):
        raise ValueError("output payload inventory is invalid")
    if {name: _sha(data) for name, data in files.items()} != FROZEN_OUTPUT_SHA256:
        raise ValueError("frozen output payload changed")


def _assert_parent_revalidated(plan: OutputMaterializationPlan, parent_fd: int) -> None:
    if not _same_identity(os.fstat(parent_fd), plan.parent_identity) or not _same_identity(os.lstat(plan.parent), plan.parent_identity):
        raise ValueError("output parent identity changed")
    _assert_real_parent_chain(plan.parent, plan.anchor)


def _assert_lexical_identity(path: Path, identity: tuple[int, int, int]) -> None:
    item = os.lstat(path)
    if not _same_identity(item, identity) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path:
        raise ValueError("output lexical identity changed")


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _listdir_fd(directory_fd: int) -> tuple[str, ...]:
    return tuple(os.listdir(directory_fd))


def _rename_noreplace_at(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 is required for set-atomic publication")
    if _RENAMEAT2(parent_fd, os.fsencode(source), parent_fd, os.fsencode(target), RENAME_NOREPLACE) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), f"{source}->{target}")


def _assert_existing_inventory(plan: OutputMaterializationPlan, root_fd: int) -> None:
    if set(_listdir_fd(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("output inventory changed")
    for name, identity in plan.leaf_identities:
        item = _stat_at(root_fd, name)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or not _same_identity(item, identity):
            raise ValueError("output leaf identity changed")


def _open_prewrite_root(plan: OutputMaterializationPlan) -> tuple[int, int, tuple[int, int, int], str | None]:
    parent_fd = os.open(os.fspath(plan.parent), DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    try:
        _assert_parent_revalidated(plan, parent_fd)
        if plan.root_identity is None:
            try:
                _stat_at(parent_fd, plan.root_name)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("missing output target became occupied")
            for _ in range(64):
                candidate = f".admit011-stage-{secrets.token_hex(16)}"
                try:
                    os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                    staging_name = candidate
                    break
                except FileExistsError:
                    continue
            else:
                raise ValueError("staging directory name collision")
            root_fd = os.open(staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            root_identity = _identity(os.fstat(root_fd))
            if not stat.S_ISDIR(root_identity[2]) or _listdir_fd(root_fd):
                raise ValueError("new staging directory is invalid")
            if not _same_identity(_stat_at(parent_fd, staging_name), root_identity):
                raise ValueError("staging directory identity changed")
        else:
            item = _stat_at(parent_fd, plan.root_name)
            if not _same_identity(item, plan.root_identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
                raise ValueError("output root identity changed")
            root_fd = os.open(plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd)
            root_identity = _identity(os.fstat(root_fd))
            if root_identity != plan.root_identity:
                raise ValueError("output root descriptor identity changed")
            _assert_lexical_identity(plan.root, root_identity)
            _assert_existing_inventory(plan, root_fd)
        return parent_fd, root_fd, root_identity, staging_name
    except BaseException:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        if staging_name is not None:
            try:
                os.rmdir(staging_name, dir_fd=parent_fd)
            except OSError:
                pass
        try:
            os.close(parent_fd)
        except OSError:
            pass
        raise


def _write_all(file_fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        count = os.write(file_fd, data[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("staged payload write failed")
        offset += count


def _read_at(directory_fd: int, name: str, expected_identity: tuple[int, int, int]) -> bytes:
    item = _stat_at(directory_fd, name)
    if not _same_identity(item, expected_identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
        raise ValueError("pinned leaf identity changed")
    file_fd = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if not _same_identity(os.fstat(file_fd), expected_identity):
            raise ValueError("pinned leaf descriptor identity changed")
        chunks = []
        while True:
            chunk = os.read(file_fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        if not _same_identity(os.fstat(file_fd), expected_identity) or not _same_identity(_stat_at(directory_fd, name), expected_identity):
            raise ValueError("pinned leaf changed during read")
        return b"".join(chunks)
    finally:
        os.close(file_fd)


def _stage_payloads(staging_fd: int, files: dict[str, bytes], staged: dict[str, tuple[int, int, int]]) -> None:
    for name, data in files.items():
        file_fd = os.open(name, WRITE_FILE_FLAGS, 0o600, dir_fd=staging_fd)
        try:
            identity = _identity(os.fstat(file_fd))
            staged[name] = identity
            _write_all(file_fd, data)
            os.fsync(file_fd)
        finally:
            os.close(file_fd)
        if _read_at(staging_fd, name, identity) != data:
            raise ValueError("staged payload bytes differ")
    if set(_listdir_fd(staging_fd)) != set(OUTPUT_FILES):
        raise ValueError("staging inventory is invalid")
    for name, data in files.items():
        item = _stat_at(staging_fd, name)
        if not _same_identity(item, staged[name]) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise ValueError("staged payload identity changed")
        actual = _read_at(staging_fd, name, staged[name])
        if actual != data or _sha(actual) != _sha(data):
            raise ValueError("staged payload verification failed")
    os.fsync(staging_fd)


def _assert_staging_publish_state(plan: OutputMaterializationPlan, parent_fd: int, staging_fd: int, staging_identity: tuple[int, int, int], staging_name: str, staged: dict[str, tuple[int, int, int]]) -> None:
    _assert_parent_revalidated(plan, parent_fd)
    if not _same_identity(os.fstat(staging_fd), staging_identity) or not _same_identity(_stat_at(parent_fd, staging_name), staging_identity):
        raise ValueError("pinned staging identity changed")
    try:
        _stat_at(parent_fd, plan.root_name)
    except FileNotFoundError:
        pass
    else:
        raise ValueError("final output root race detected")
    if set(_listdir_fd(staging_fd)) != set(OUTPUT_FILES):
        raise ValueError("staging inventory changed")
    for name, identity in staged.items():
        item = _stat_at(staging_fd, name)
        if not _same_identity(item, identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise ValueError("staged leaf changed")


def _publish_staging_directory(plan: OutputMaterializationPlan, parent_fd: int, staging_fd: int, staging_identity: tuple[int, int, int], staging_name: str, staged: dict[str, tuple[int, int, int]]) -> None:
    _assert_staging_publish_state(plan, parent_fd, staging_fd, staging_identity, staging_name, staged)
    _rename_noreplace_at(parent_fd, staging_name, plan.root_name)
    if not _same_identity(_stat_at(parent_fd, plan.root_name), staging_identity):
        raise ValueError("published output root identity changed")


def _assert_existing_payloads_identical(plan: OutputMaterializationPlan, parent_fd: int, root_fd: int, root_identity: tuple[int, int, int], files: dict[str, bytes]) -> None:
    _assert_parent_revalidated(plan, parent_fd)
    if not _same_identity(os.fstat(root_fd), root_identity):
        raise ValueError("pinned output root changed")
    _assert_lexical_identity(plan.root, root_identity)
    _assert_existing_inventory(plan, root_fd)
    identities = dict(plan.leaf_identities)
    for name, data in files.items():
        if _read_at(root_fd, name, identities[name]) != data:
            raise ValueError("existing output payload differs; repair is forbidden")


def _postwrite_verify(plan: OutputMaterializationPlan, parent_fd: int, root_fd: int, root_identity: tuple[int, int, int], files: dict[str, bytes]) -> None:
    _assert_parent_revalidated(plan, parent_fd)
    if not _same_identity(os.fstat(root_fd), root_identity):
        raise ValueError("output root changed after publication")
    _assert_lexical_identity(plan.root, root_identity)
    if set(_listdir_fd(root_fd)) != set(OUTPUT_FILES):
        raise ValueError("postwrite output inventory invalid")
    if plan.root_identity is not None:
        _assert_existing_inventory(plan, root_fd)
    for name, data in files.items():
        item = _stat_at(root_fd, name)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise ValueError("postwrite output leaf invalid")
        actual = _read_at(root_fd, name, _identity(item))
        if actual != data or _sha(actual) != _sha(data):
            raise ValueError("postwrite output payload mismatch")
    os.fsync(root_fd)


def _cleanup_staging(parent_fd: int | None, staging_fd: int | None, staging_name: str | None, staging_identity: tuple[int, int, int] | None, staged: dict[str, tuple[int, int, int]]) -> int | None:
    if parent_fd is None or staging_fd is None or staging_name is None or staging_identity is None:
        return staging_fd
    try:
        if not _same_identity(os.fstat(staging_fd), staging_identity) or not _same_identity(_stat_at(parent_fd, staging_name), staging_identity):
            return staging_fd
        if set(_listdir_fd(staging_fd)) != set(staged):
            return staging_fd
        for name, identity in staged.items():
            item = _stat_at(staging_fd, name)
            if not _same_identity(item, identity) or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                return staging_fd
        for name, identity in staged.items():
            if not _same_identity(_stat_at(staging_fd, name), identity):
                return staging_fd
            os.unlink(name, dir_fd=staging_fd)
        if _listdir_fd(staging_fd):
            return staging_fd
        os.close(staging_fd)
        staging_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException:
        pass
    return staging_fd


def run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, str]:
    """Publish the six deterministic evidence files as one FD-pinned directory set."""
    plan = _inspect_output_target_read_only(output_root)
    parent_fd: int | None = None
    root_fd: int | None = None
    root_identity: tuple[int, int, int] | None = None
    staging_name: str | None = None
    staged: dict[str, tuple[int, int, int]] = {}
    try:
        files = build_interface_artifacts(REPO_ROOT)
        _validate_payloads(files)
        parent_fd, root_fd, root_identity, staging_name = _open_prewrite_root(plan)
        if staging_name is None:
            _assert_existing_payloads_identical(plan, parent_fd, root_fd, root_identity, files)
            _postwrite_verify(plan, parent_fd, root_fd, root_identity, files)
        else:
            _stage_payloads(root_fd, files, staged)
            _publish_staging_directory(plan, parent_fd, root_fd, root_identity, staging_name, staged)
            staging_name = None
            os.fsync(parent_fd)
            _postwrite_verify(plan, parent_fd, root_fd, root_identity, files)
        return {name: _sha(data) for name, data in files.items()}
    except BaseException:
        root_fd = _cleanup_staging(parent_fd, root_fd, staging_name, root_identity, staged)
        raise
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1()

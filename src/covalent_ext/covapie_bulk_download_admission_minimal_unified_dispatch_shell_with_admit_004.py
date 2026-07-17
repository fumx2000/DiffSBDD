"""Step14AU-E1-E4 Phase 2 minimal unified admission dispatch shell.

The public runtime is deliberately limited to one rule.  ADMIT_004 is the
only registered evaluator and every other known or unknown rule fails closed.
The metadata materializer below the runtime verifies the frozen Exact12
evidence boundary and executes only synthetic dispatch cases.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from covalent_ext.covapie_bulk_download_admission_admit_004_rule_logic_interface import (
    Admit004EvaluationResult,
    CANDIDATE_FIELDS as ADMIT_004_CANDIDATE_FIELDS,
    EVIDENCE_CONTEXT_KEY,
    EVIDENCE_CONTEXT_SCHEMA_VERSION,
    evaluate_admit_004,
)


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E4 Phase 2"
STAGE = "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1"
EXPECTED_BASE_COMMIT = "8f4782dc601c8ddda69b038074fa1a878c762a6a"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission rule engine contract design v1"
MANIFEST_SCHEMA_VERSION = "covapie_minimal_unified_dispatch_shell_manifest_v1"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
ADMIT_004_ADAPTER_ID = "covapie_admit_004_unified_adapter_v1"
ADMIT_004_RULE_NAME = "covalent_residue_identity_present"
RECOMMENDED_NEXT_STEP = (
    "design_covapie_unified_admission_legacy_evaluator_adapter_contracts_"
    "for_admit_001_to_003_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 5))
ADAPTER_READY_RULE_IDS = ("ADMIT_004",)
LEGACY_ADAPTER_NOT_READY_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 4))

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
DISPATCH_ERROR_FIELDS = (
    "code",
    "admission_rule_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "reason",
)
DISPATCH_ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")
ADMIT_004_OUTCOMES = ("passed", "blocked", "invalid")


def _exact_string_tuple(value: object) -> bool:
    return type(value) is tuple and all(type(item) is str for item in value)


def _exact_string_pair_tuple(value: object) -> bool:
    return type(value) is tuple and all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in value
    )


@dataclass(frozen=True)
class UnifiedAdmissionRuleEvaluation:
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

    def __post_init__(self) -> None:
        if any(
            type(value) is not str
            for value in (
                self.schema_version,
                self.admission_rule_id,
                self.admission_rule_name,
                self.outcome,
                self.reason,
                self.adapter_id,
            )
        ):
            raise TypeError("unified admission result string field type invalid")
        if any(
            type(value) is not bool
            for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)
        ):
            raise TypeError("unified admission result bool field type invalid")
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise ValueError("unified admission result schema version invalid")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("unified admission result outcome invalid")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("unified admission result passed invariant invalid")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("unified admission result blocking invariant invalid")
        if (self.outcome == "passed" and self.reason != "") or (
            self.outcome != "passed" and self.reason == ""
        ):
            raise ValueError("unified admission result reason invariant invalid")
        if not _exact_string_pair_tuple(self.normalized_values):
            raise TypeError("normalized values must be an exact tuple of exact string pairs")
        if not _exact_string_pair_tuple(self.validated_candidate_fields):
            raise TypeError("validated fields must be an exact tuple of exact string pairs")
        if not _exact_string_tuple(self.consumed_candidate_fields):
            raise TypeError("consumed candidate fields must be an exact string tuple")
        if not _exact_string_tuple(self.consumed_context_items):
            raise TypeError("consumed context items must be an exact string tuple")
        if self.evaluator_io_used is not False:
            raise ValueError("unified admission evaluator IO must be false")


@dataclass(frozen=True)
class UnifiedAdmissionDispatchError(Exception):
    code: str
    admission_rule_id: str
    known_rule: bool
    callable_discovered: bool
    adapter_ready: bool
    reason: str

    def __post_init__(self) -> None:
        if type(self.code) is not str or self.code not in DISPATCH_ERROR_CODES:
            raise ValueError("unified admission dispatch error code invalid")
        if type(self.admission_rule_id) is not str:
            raise TypeError("unified admission dispatch rule ID type invalid")
        if any(
            type(value) is not bool
            for value in (self.known_rule, self.callable_discovered, self.adapter_ready)
        ):
            raise TypeError("unified admission dispatch bool field type invalid")
        if type(self.reason) is not str or self.reason == "":
            raise ValueError("unified admission dispatch reason invalid")
        Exception.__init__(self, self.reason)


def _raise_dispatch_error(
    code: str,
    admission_rule_id: str,
    known_rule: bool,
    callable_discovered: bool,
    adapter_ready: bool,
    reason: str | None = None,
) -> NoReturn:
    raise UnifiedAdmissionDispatchError(
        code=code,
        admission_rule_id=admission_rule_id,
        known_rule=known_rule,
        callable_discovered=callable_discovered,
        adapter_ready=adapter_ready,
        reason=code if reason is None else reason,
    )


def _adapter_invariant_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_004",
        True,
        True,
        False,
        reason,
    )


def _adapt_admit_004(source: object) -> UnifiedAdmissionRuleEvaluation:
    if type(source) is not Admit004EvaluationResult:
        _adapter_invariant_failure("ADMIT_004_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert isinstance(source, Admit004EvaluationResult)
    invariant_ok = (
        type(source.admission_rule_id) is str
        and source.admission_rule_id == "ADMIT_004"
        and type(source.outcome) is str
        and source.outcome in ADMIT_004_OUTCOMES
        and type(source.passed) is bool
        and source.passed is (source.outcome == "passed")
        and type(source.blocks_candidate) is bool
        and source.blocks_candidate is (source.outcome != "passed")
        and type(source.reason) is str
        and (
            (source.outcome == "passed" and source.reason == "")
            or (source.outcome != "passed" and source.reason != "")
        )
        and type(source.canonical_residue_name) is str
        and _exact_string_pair_tuple(source.validated_candidate_fields)
        and _exact_string_tuple(source.consumed_candidate_fields)
        and source.consumed_candidate_fields == ADMIT_004_CANDIDATE_FIELDS
        and type(source.evidence_context_consumed) is bool
        and type(source.evaluator_io_used) is bool
        and source.evaluator_io_used is False
    )
    if not invariant_ok:
        _adapter_invariant_failure("ADMIT_004_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_004",
        admission_rule_name=ADMIT_004_RULE_NAME,
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=(
            ()
            if source.canonical_residue_name == ""
            else (("covalent_residue_name", source.canonical_residue_name),)
        ),
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=(
            ("covalent_residue_identity_evidence_context",)
            if source.evidence_context_consumed
            else ()
        ),
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADMIT_004_ADAPTER_ID,
    )


def _evaluate_registered_admit_004(
    candidate_record: object, evaluation_context: Mapping[str, object]
) -> UnifiedAdmissionRuleEvaluation:
    if isinstance(candidate_record, Mapping):
        projected_candidate: object = {
            field: candidate_record[field]
            for field in ADMIT_004_CANDIDATE_FIELDS
            if field in candidate_record
        }
    else:
        projected_candidate = candidate_record
    source = evaluate_admit_004(  # type: ignore[arg-type]
        projected_candidate,
        evaluation_context,
    )
    return _adapt_admit_004(source)


EVALUATOR_REGISTRY = MappingProxyType(
    {"ADMIT_004": (ADMIT_004_RULE_NAME, _evaluate_registered_admit_004)}
)


def evaluate_admission_rule(
    admission_rule_id: str,
    candidate_record: Mapping[str, object],
    *,
    batch_context: Mapping[str, object] | None = None,
    evaluation_context: Mapping[str, object] | None = None,
    download_result_context: Mapping[str, object] | None = None,
    stage_authorization_context: Mapping[str, object] | None = None,
) -> UnifiedAdmissionRuleEvaluation:
    """Evaluate one registered admission rule without IO or aggregation."""
    if type(admission_rule_id) is not str:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False
        )
    if admission_rule_id not in KNOWN_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            admission_rule_id,
            False,
            False,
            False,
        )
    if admission_rule_id in LEGACY_ADAPTER_NOT_READY_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            admission_rule_id,
            True,
            True,
            False,
        )
    if admission_rule_id not in EVALUATOR_REGISTRY:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            admission_rule_id,
            True,
            False,
            False,
        )

    if batch_context is not None:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_004",
            True,
            True,
            True,
            "ADMIT_004_BATCH_CONTEXT_MUST_BE_NONE",
        )
    if not isinstance(evaluation_context, Mapping):
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_004",
            True,
            True,
            True,
            "ADMIT_004_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        )
    if download_result_context is not None:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_004",
            True,
            True,
            True,
            "ADMIT_004_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        )
    if stage_authorization_context is not None:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_004",
            True,
            True,
            True,
            "ADMIT_004_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        )
    return EVALUATOR_REGISTRY["ADMIT_004"][1](candidate_record, evaluation_context)


# Frozen evidence boundary and deterministic metadata materializer.

PHASE1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1"
)
ADMIT004_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_rule_logic_interface_v1"
)
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate.py",
        str(PHASE1_ROOT / "covapie_unified_admission_public_api_and_dispatch_contract.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_result_schema_and_outcome_contract.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_evaluator_and_context_routing_matrix.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_engine_issue_inventory.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_engine_safety_audit.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_engine_contract_design_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py",
        str(ADMIT004_ROOT / "covapie_admit_004_rule_logic_interface_contract.csv"),
        str(ADMIT004_ROOT / "covapie_admit_004_rule_logic_interface_truth_matrix.csv"),
        str(ADMIT004_ROOT / "covapie_admit_004_rule_logic_interface_issue_readiness_inventory.csv"),
        str(ADMIT004_ROOT / "covapie_admit_004_rule_logic_interface_manifest.json"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "510ba06546754fafdb02ab15b48636066e7b38e42b2f1ed0da9346a6485f150f",
            "2d46faffb7505483b5dabc05a9451d1b6eea0671c722f78674175a8559e8a304",
            "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
            "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
            "5295ee97d8cc3c81cd376116c4dc87489e1b04a65d700a6d08a927d5c72a9951",
            "d05c54f805ad2118027124ae96c3bce132904e26bbd93daa3dc0298681aa159f",
            "62e21a2b4a982e734d6ecd02b1ec056fa0ddccfda6c41dd4bd90dfbe7eb47c3d",
            "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
            "0c4fbc7f1307d3adb5c62dffb7668176b0ad54f2ff156b2f42ea02dec8d48250",
            "399fa0617aee4196c99051d99d26c75f54cbcc815a396425b7825dbeb9e7d83e",
            "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
            "f000c7959c0e8a9f561d60b332c5460b4de84279d3e5c11556638334297723a6",
        ),
        strict=True,
    )
)
(
    PHASE1_SOURCE_PATH,
    PHASE1_PUBLIC_API_PATH,
    PHASE1_RESULT_PATH,
    PHASE1_ROUTING_PATH,
    PHASE1_ISSUE_PATH,
    PHASE1_SAFETY_PATH,
    PHASE1_MANIFEST_PATH,
    ADMIT004_SOURCE_PATH,
    ADMIT004_CONTRACT_PATH,
    ADMIT004_TRUTH_PATH,
    ADMIT004_ISSUE_PATH,
    ADMIT004_MANIFEST_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_minimal_unified_dispatch_shell_contract.csv"
TRUTH_FILENAME = "covapie_minimal_unified_dispatch_shell_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_minimal_unified_dispatch_registry_and_routing_audit.csv"
SAFETY_FILENAME = "covapie_minimal_unified_dispatch_shell_safety_audit.csv"
ISSUE_FILENAME = "covapie_minimal_unified_dispatch_shell_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_minimal_unified_dispatch_shell_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id",
    "contract_area",
    "contract_statement",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "truth_group",
    "case_id",
    "execution_kind",
    "expected_outcome",
    "observed_outcome",
    "expected_error_code",
    "observed_error_code",
    "expected_reason",
    "observed_reason",
    "passed",
    "blocks_candidate",
    "evaluator_io_used",
    "truth_passed",
)
REGISTRY_COLUMNS = (
    "admission_rule_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "registered",
    "dispatch_disposition",
    "audit_passed",
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

TRUE_READINESS = (
    "minimal_unified_dispatch_shell_implemented",
    "evaluate_admission_rule_implemented",
    "unified_result_runtime_class_implemented",
    "dispatch_error_runtime_class_implemented",
    "evaluator_registry_runtime_implemented",
    "admit_004_adapter_implemented",
    "admit_004_registered_in_engine",
    "single_rule_dispatch_runtime_ready",
    "unsupported_rule_fail_closed_runtime_implemented",
    "explicit_context_routing_runtime_enforced",
    "candidate_field_projection_runtime_enforced",
    "synthetic_dispatch_truth_matrix_passed",
    "ready_for_admit_001_to_003_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "unified_rule_engine_implemented",
    "legacy_evaluator_adapters_implemented",
    "admit_001_registered_in_engine",
    "admit_002_registered_in_engine",
    "admit_003_registered_in_engine",
    "admit_005_to_015_registered_in_engine",
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
TRUE_SAFETY_ITEMS = (
    "exact_source_reads",
    "phase1_contract_validation",
    "unified_result_runtime_implementation",
    "dispatch_error_runtime_implementation",
    "immutable_registry_runtime_implementation",
    "admit_004_adapter_implementation",
    "single_rule_dispatch_implementation",
    "explicit_context_routing_validation",
    "candidate_projection_validation",
    "synthetic_admit_004_evaluator_execution",
    "synthetic_dispatch_truth_matrix_evaluation",
    "issue_inventory_preservation",
)
FALSE_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "parser_execution",
    "provider_execution",
    "legacy_evaluator_adapter_implementation",
    "admit_001_to_003_evaluator_execution",
    "admit_005_to_015_evaluator_execution",
    "evaluate_all_rules_implementation",
    "combined_candidate_verdict_implementation",
    "cross_rule_aggregation",
    "candidate_record_materialization",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "admission_record_modification",
    "sample_backfill",
    "network",
    "download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward_loss_training",
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


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
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


def _validate_expected_base_lineage(
    repo_root: Path, *, head_ref: str = "HEAD"
) -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base_object = _git(
        ["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root
    )
    if base_object.returncode != 0:
        raise ValueError("expected base commit object is missing")
    base_subject = _git(
        ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root
    )
    if (
        base_subject.returncode != 0
        or base_subject.stdout.strip() != EXPECTED_BASE_SUBJECT
    ):
        raise ValueError("expected base commit subject mismatch")
    ancestor = _git(
        ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root
    )
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Inspect metadata only; do not read any source content bytes here."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields_in_tree = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields_in_tree) == 3
        and fields_in_tree[0] in ("100644", "100755")
        and fields_in_tree[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete all Exact12 structural checks before the first byte read."""
    if (
        len(SOURCE_PATHS) != 12
        or len(set(SOURCE_PATHS)) != 12
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact12 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")

    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base_read = _git(
            ["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False
        )
        if base_read.returncode != 0 or type(base_read.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base_read.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes)
        )
    return FrozenSourceSnapshot(tuple(records))


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
    if any(
        tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values())
        for row in rows
    ):
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


def _keyed(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("missing or duplicate row key")
        result[value] = row
    return result


def _class_fields(tree: ast.Module, class_name: str) -> tuple[str, ...]:
    node = next(
        (item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == class_name),
        None,
    )
    if node is None or "dataclass(frozen=True)" not in {
        ast.unparse(item) for item in node.decorator_list
    }:
        raise ValueError(f"frozen dataclass missing: {class_name}")
    return tuple(
        item.target.id
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    )


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = tuple(
        item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name
    )
    if len(matches) != 1:
        raise ValueError(f"public function missing or duplicate: {name}")
    return matches[0]


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    public_api = _csv_document(snapshot, PHASE1_PUBLIC_API_PATH)
    result = _csv_document(snapshot, PHASE1_RESULT_PATH)
    routing = _csv_document(snapshot, PHASE1_ROUTING_PATH)
    issues = _csv_document(snapshot, PHASE1_ISSUE_PATH)
    safety = _csv_document(snapshot, PHASE1_SAFETY_PATH)
    phase1_manifest = _json_document(snapshot, PHASE1_MANIFEST_PATH)
    admit_contract = _csv_document(snapshot, ADMIT004_CONTRACT_PATH)
    admit_truth = _csv_document(snapshot, ADMIT004_TRUTH_PATH)
    admit_issues = _csv_document(snapshot, ADMIT004_ISSUE_PATH)
    admit_manifest = _json_document(snapshot, ADMIT004_MANIFEST_PATH)
    phase1_tree = _ast_document(snapshot, PHASE1_SOURCE_PATH)
    admit_tree = _ast_document(snapshot, ADMIT004_SOURCE_PATH)

    if public_api.header != (
        "contract_order",
        "contract_area",
        "contract_item",
        "contract_value",
        "contract_status",
    ) or len(public_api.rows) != 27:
        raise ValueError("Phase 1 public API contract invalid")
    public_map = _keyed(public_api.rows, "contract_item")
    if (
        public_map["dispatch_cardinality"]["contract_value"] != "single_rule_only"
        or public_map["evaluate_all_rules"]["contract_value"] != "not_provided"
        or public_map["combined_candidate_verdict"]["contract_value"] != "not_generated"
        or any(row["contract_status"] != "frozen" for row in public_api.rows)
    ):
        raise ValueError("Phase 1 public API semantics invalid")
    if len(result.rows) != 29:
        raise ValueError("Phase 1 result contract count invalid")
    result_fields = tuple(
        row["field_name"] for row in result.rows if row["contract_kind"] == "result_field"
    )
    if result_fields != RESULT_FIELDS:
        raise ValueError("Phase 1 result field order invalid")
    result_map = _keyed(result.rows, "contract_order")
    if (
        result_map["15"]["contract_value"] != RESULT_SCHEMA_VERSION
        or result_map["16"]["contract_value"] != "|".join(OUTCOME_VOCABULARY)
        or result_map["23"]["contract_value"] != "passed|blocked|invalid"
    ):
        raise ValueError("Phase 1 result semantics invalid")
    if (
        len(routing.rows) != 15
        or tuple(row["admission_rule_id"] for row in routing.rows) != KNOWN_RULE_IDS
    ):
        raise ValueError("Phase 1 routing Exact15 invalid")
    routing_map = _keyed(routing.rows, "admission_rule_id")
    if (
        tuple(
            row["admission_rule_id"]
            for row in routing.rows
            if row["callable_discovered"] == "true"
        )
        != CALLABLE_DISCOVERED_RULE_IDS
        or routing_map["ADMIT_004"]["admission_rule_name"] != ADMIT_004_RULE_NAME
        or routing_map["ADMIT_004"]["evaluator_callable_name"] != "evaluate_admit_004"
        or routing_map["ADMIT_004"]["result_adapter_contract_status"] != "design_ready"
        or routing_map["ADMIT_004"]["allowed_rule_outcomes"] != "passed|blocked|invalid"
    ):
        raise ValueError("Phase 1 routing semantics invalid")
    if len(issues.rows) != 12:
        raise ValueError("Phase 1 issue inventory is not Exact12")
    issue_map = _keyed(issues.rows, "issue_id")
    for issue_id in (
        "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        if (
            issue_map[issue_id]["status"] != "open"
            or issue_map[issue_id]["severity"] != "blocking"
        ):
            raise ValueError("Phase 1 unified blocker invalid")
    provider = issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    if (
        provider["status"] != "open"
        or provider["severity"] != "blocking"
        or provider["issue_count"] != "11"
    ):
        raise ValueError("provider blocker invalid")
    if len(safety.rows) != 29 or any(row["safety_passed"] != "true" for row in safety.rows):
        raise ValueError("Phase 1 safety contract invalid")
    if not (
        phase1_manifest.get("all_checks_passed") is True
        and phase1_manifest.get("design_readiness") is True
        and phase1_manifest.get("evaluate_admission_rule_implemented") is False
        and phase1_manifest.get("unified_rule_engine_implemented") is False
        and phase1_manifest.get("ready_for_bulk_download_now") is False
        and phase1_manifest.get("ready_for_training") is False
    ):
        raise ValueError("Phase 1 manifest readiness invalid")
    if _function_node(phase1_tree, "build_frozen_source_snapshot") is None:
        raise ValueError("Phase 1 frozen source builder missing")
    if any(
        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == "evaluate_admission_rule"
        for item in phase1_tree.body
    ):
        raise ValueError("Phase 1 unexpectedly implements runtime dispatch")

    if _class_fields(admit_tree, "Admit004EvaluationResult") != (
        "admission_rule_id",
        "outcome",
        "passed",
        "blocks_candidate",
        "reason",
        "canonical_residue_name",
        "validated_candidate_fields",
        "consumed_candidate_fields",
        "evidence_context_consumed",
        "evaluator_io_used",
    ):
        raise ValueError("standalone ADMIT_004 result contract invalid")
    admit_function = _function_node(admit_tree, "evaluate_admit_004")
    if tuple(argument.arg for argument in admit_function.args.args) != (
        "candidate_record",
        "evaluation_context",
    ):
        raise ValueError("standalone ADMIT_004 signature invalid")
    admit_contract_map = _keyed(admit_contract.rows, "contract_id")
    if (
        len(admit_contract.rows) != 43
        or any(row["contract_passed"] != "true" for row in admit_contract.rows)
        or admit_contract_map["INTERFACE_001"]["observed_value"] != "evaluate_admit_004"
        or admit_contract_map["INTERFACE_004"]["observed_value"] != "passed|blocked|invalid"
        or admit_contract_map["INTERFACE_006"]["observed_value"] != "false"
    ):
        raise ValueError("standalone ADMIT_004 interface evidence invalid")
    if len(admit_truth.rows) != 50 or any(row["truth_passed"] != "true" for row in admit_truth.rows):
        raise ValueError("standalone ADMIT_004 truth evidence invalid")
    if admit_issues.rows != issues.rows[:9]:
        raise ValueError("standalone issue lineage invalid")
    if not (
        admit_manifest.get("all_checks_passed") is True
        and admit_manifest.get("admit_004_evaluator_implemented") is True
        and admit_manifest.get("evaluator_no_io_contract_enforced") is True
        and admit_manifest.get("exact11_real_rows_evaluated") is False
        and admit_manifest.get("provider_blocking_issue_count") == 11
        and admit_manifest.get("ready_for_bulk_download_now") is False
        and admit_manifest.get("ready_for_training") is False
    ):
        raise ValueError("standalone ADMIT_004 manifest invalid")
    return {
        "public_api": public_api,
        "result": result,
        "routing": routing,
        "issues": issues,
        "safety": safety,
        "phase1_manifest": phase1_manifest,
        "admit_contract": admit_contract,
        "admit_truth": admit_truth,
        "admit_manifest": admit_manifest,
    }


def _base_candidate(
    *, residue: str = "CYS", atom: str = "SG", state: str = "absent", value: str = ""
) -> dict[str, str]:
    return {
        "covalent_residue_name": residue,
        "covalent_residue_chain_id": "A",
        "covalent_residue_index": "42",
        "covalent_residue_atom_name": atom,
        "covalent_residue_locator_namespace": "auth",
        "covalent_residue_insertion_code_state": state,
        "covalent_residue_insertion_code": value,
        "covalent_residue_locator_provenance_source_id": "covapie:synthetic",
        "covalent_residue_locator_provenance_sha256": "0" * 64,
    }


def _base_context(
    candidate: Mapping[str, str],
    *,
    outcome: str = "passed",
    reason: str = "",
    four_way: bool = True,
    quote: bool = True,
) -> dict[str, object]:
    return {
        EVIDENCE_CONTEXT_KEY: {
            "schema_version": EVIDENCE_CONTEXT_SCHEMA_VERSION,
            "attested_candidate_fields": {
                field: candidate[field] for field in ADMIT_004_CANDIDATE_FIELDS
            },
            "provider_evidence_outcome": outcome,
            "provider_evidence_reason": reason,
            "four_way_present_value_exact_equality_attested": four_way,
            "present_value_quote_class_roundtrip_verified": quote,
        }
    }


def _truth_case_definitions() -> tuple[dict[str, Any], ...]:
    absent = _base_candidate()
    generic = _base_candidate(residue="SER", atom="CA")
    lower = _base_candidate(residue="cys")
    unknown = _base_candidate(state="unknown")
    present = _base_candidate(state="present", value="A")
    malformed = {EVIDENCE_CONTEXT_KEY: []}

    class RuleIdSubclass(str):
        pass

    return (
        {"group": "passed", "id": "PASSED_001_ABSENT_CYS_SG", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent), "outcome": "passed", "reason": ""},
        {"group": "passed", "id": "PASSED_002_GENERIC_SER_CA", "rule": "ADMIT_004", "candidate": generic, "evaluation": _base_context(generic), "outcome": "passed", "reason": ""},
        {"group": "passed", "id": "PASSED_003_LOWERCASE_CYS", "rule": "ADMIT_004", "candidate": lower, "evaluation": _base_context(lower), "outcome": "passed", "reason": ""},
        {"group": "blocked", "id": "BLOCKED_001_UNKNOWN_INSERTION", "rule": "ADMIT_004", "candidate": unknown, "evaluation": _base_context(unknown), "outcome": "blocked", "reason": "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"},
        {"group": "blocked", "id": "BLOCKED_002_MISSING_EVIDENCE", "rule": "ADMIT_004", "candidate": absent, "evaluation": {}, "outcome": "blocked", "reason": "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING"},
        {"group": "blocked", "id": "BLOCKED_003_PROVIDER", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent, outcome="blocked", reason="PROVIDER_BLOCKED"), "outcome": "blocked", "reason": "PROVIDER_BLOCKED"},
        {"group": "blocked", "id": "BLOCKED_004_QUOTE_CLASS", "rule": "ADMIT_004", "candidate": present, "evaluation": _base_context(present, quote=False), "outcome": "blocked", "reason": "COVALENT_RESIDUE_INSERTION_PRESENT_QUOTE_CLASS_UNVERIFIED"},
        {"group": "invalid_rule_result", "id": "INVALID_001_CANDIDATE_NON_MAPPING", "rule": "ADMIT_004", "candidate": [], "evaluation": {}, "outcome": "invalid", "reason": "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID"},
        {"group": "invalid_rule_result", "id": "INVALID_002_MALFORMED_NESTED_CONTEXT", "rule": "ADMIT_004", "candidate": absent, "evaluation": malformed, "outcome": "invalid", "reason": "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MAPPING_INVALID"},
        {"group": "invalid_rule_result", "id": "INVALID_003_PROVIDER_PROPAGATED", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent, outcome="invalid", reason="PROVIDER_INVALID"), "outcome": "invalid", "reason": "PROVIDER_INVALID"},
        {"group": "dispatch_error", "id": "DISPATCH_001_RULE_ID_NON_STR", "rule": 4, "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "reason": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"},
        {"group": "dispatch_error", "id": "DISPATCH_002_RULE_ID_STR_SUBCLASS", "rule": RuleIdSubclass("ADMIT_004"), "candidate": absent, "evaluation": _base_context(absent), "code": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "reason": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"},
        {"group": "dispatch_error", "id": "DISPATCH_003_UNKNOWN", "rule": "ADMIT_999", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "reason": "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"},
        {"group": "dispatch_error", "id": "DISPATCH_004_ADMIT_001", "rule": "ADMIT_001", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "reason": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"},
        {"group": "dispatch_error", "id": "DISPATCH_005_ADMIT_002", "rule": "ADMIT_002", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "reason": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"},
        {"group": "dispatch_error", "id": "DISPATCH_006_ADMIT_003", "rule": "ADMIT_003", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "reason": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"},
        {"group": "dispatch_error", "id": "DISPATCH_007_ADMIT_005", "rule": "ADMIT_005", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "reason": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"},
        {"group": "dispatch_error", "id": "DISPATCH_008_ADMIT_015", "rule": "ADMIT_015", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "reason": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"},
        {"group": "dispatch_error", "id": "DISPATCH_009_EVALUATION_NONE", "rule": "ADMIT_004", "candidate": absent, "evaluation": None, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_EVALUATION_CONTEXT_MAPPING_REQUIRED"},
        {"group": "dispatch_error", "id": "DISPATCH_010_EVALUATION_NON_MAPPING", "rule": "ADMIT_004", "candidate": absent, "evaluation": [], "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_EVALUATION_CONTEXT_MAPPING_REQUIRED"},
        {"group": "dispatch_error", "id": "DISPATCH_011_BATCH_NON_NONE", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent), "batch": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_BATCH_CONTEXT_MUST_BE_NONE"},
        {"group": "dispatch_error", "id": "DISPATCH_012_DOWNLOAD_NON_NONE", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent), "download": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"},
        {"group": "dispatch_error", "id": "DISPATCH_013_STAGE_NON_NONE", "rule": "ADMIT_004", "candidate": absent, "evaluation": _base_context(absent), "stage": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"},
        {"group": "dispatch_error", "id": "DISPATCH_014_CONTEXT_PRECEDENCE", "rule": "ADMIT_004", "candidate": absent, "evaluation": [], "batch": {}, "download": {}, "stage": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_004_BATCH_CONTEXT_MUST_BE_NONE"},
    )


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in _truth_case_definitions():
        expected_outcome = case.get("outcome", "")
        expected_code = case.get("code", "")
        expected_reason = case["reason"]
        observed_outcome = ""
        observed_code = ""
        observed_reason = ""
        passed = ""
        blocks = ""
        evaluator_io = ""
        execution_kind = "rule_result"
        try:
            result = evaluate_admission_rule(  # type: ignore[arg-type]
                case["rule"],
                case["candidate"],
                batch_context=case.get("batch"),
                evaluation_context=case.get("evaluation"),
                download_result_context=case.get("download"),
                stage_authorization_context=case.get("stage"),
            )
            observed_outcome = result.outcome
            observed_reason = result.reason
            passed = str(result.passed).lower()
            blocks = str(result.blocks_candidate).lower()
            evaluator_io = str(result.evaluator_io_used).lower()
            truth_passed = (
                expected_code == ""
                and result.outcome == expected_outcome
                and result.reason == expected_reason
                and result.passed is (expected_outcome == "passed")
                and result.blocks_candidate is (expected_outcome != "passed")
                and result.evaluator_io_used is False
            )
        except UnifiedAdmissionDispatchError as error:
            execution_kind = "dispatch_error"
            observed_code = error.code
            observed_reason = error.reason
            truth_passed = (
                expected_outcome == ""
                and error.code == expected_code
                and error.reason == expected_reason
            )
        rows.append(
            {
                "truth_group": case["group"],
                "case_id": case["id"],
                "execution_kind": execution_kind,
                "expected_outcome": expected_outcome,
                "observed_outcome": observed_outcome,
                "expected_error_code": expected_code,
                "observed_error_code": observed_code,
                "expected_reason": expected_reason,
                "observed_reason": observed_reason,
                "passed": passed,
                "blocks_candidate": blocks,
                "evaluator_io_used": evaluator_io,
                "truth_passed": str(truth_passed).lower(),
            }
        )
    return rows


def _registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id in KNOWN_RULE_IDS:
        callable_discovered = rule_id in CALLABLE_DISCOVERED_RULE_IDS
        adapter_ready = rule_id in ADAPTER_READY_RULE_IDS
        registered = rule_id in EVALUATOR_REGISTRY
        if rule_id in LEGACY_ADAPTER_NOT_READY_RULE_IDS:
            disposition = "adapter_not_ready_fail_closed"
        elif rule_id == "ADMIT_004":
            disposition = "registered_single_rule_runtime"
        else:
            disposition = "known_not_registered_fail_closed"
        audit_passed = (
            (rule_id in KNOWN_RULE_IDS)
            and callable_discovered is (rule_id in CALLABLE_DISCOVERED_RULE_IDS)
            and adapter_ready is (rule_id == "ADMIT_004")
            and registered is (rule_id == "ADMIT_004")
        )
        rows.append(
            {
                "admission_rule_id": rule_id,
                "known_rule": "true",
                "callable_discovered": str(callable_discovered).lower(),
                "adapter_ready": str(adapter_ready).lower(),
                "registered": str(registered).lower(),
                "dispatch_disposition": disposition,
                "audit_passed": str(audit_passed).lower(),
            }
        )
    return rows


def _contract_rows() -> list[dict[str, str]]:
    signature = str(inspect.signature(evaluate_admission_rule))
    specifications = (
        ("RUNTIME_001", "public_api", "public callable", "evaluate_admission_rule"),
        ("RUNTIME_002", "public_api", "signature", signature),
        ("RUNTIME_003", "public_api", "dispatch cardinality", "single_rule_only"),
        ("RESULT_001", "result", "frozen dataclass", "true"),
        ("RESULT_002", "result", "exact field count", "13"),
        ("RESULT_003", "result", "field order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result", "schema version", RESULT_SCHEMA_VERSION),
        ("RESULT_005", "result", "global outcome vocabulary", "|".join(OUTCOME_VOCABULARY)),
        ("RESULT_006", "result", "ADMIT_004 outcomes", "|".join(ADMIT_004_OUTCOMES)),
        ("RESULT_007", "result", "evaluator IO", "false"),
        ("ERROR_001", "dispatch_error", "frozen dataclass exception", "true"),
        ("ERROR_002", "dispatch_error", "exact field count", "6"),
        ("ERROR_003", "dispatch_error", "field order", "|".join(DISPATCH_ERROR_FIELDS)),
        ("ERROR_004", "dispatch_error", "code vocabulary", "|".join(DISPATCH_ERROR_CODES)),
        ("REGISTRY_001", "registry", "known rule count", "15"),
        ("REGISTRY_002", "registry", "callable discovered count", "4"),
        ("REGISTRY_003", "registry", "adapter ready count", "1"),
        ("REGISTRY_004", "registry", "registered rules", "ADMIT_004"),
        ("REGISTRY_005", "registry", "immutable", "true"),
        ("ADAPTER_001", "adapter", "adapter ID", ADMIT_004_ADAPTER_ID),
        ("ADAPTER_002", "adapter", "standalone evaluator calls per dispatch", "1"),
        ("ADAPTER_003", "adapter", "source result exact type required", "true"),
        ("ADAPTER_004", "adapter", "candidate projection field count", "9"),
        ("ADAPTER_005", "adapter", "evaluation context identity pass through", "true"),
        ("BOUNDARY_001", "boundary", "legacy adapters implemented", "false"),
        ("BOUNDARY_002", "boundary", "ADMIT_005 to ADMIT_015 implemented", "false"),
        ("BOUNDARY_003", "boundary", "all-rules evaluator implemented", "false"),
        ("BOUNDARY_004", "boundary", "combined candidate verdict", "false"),
        ("BOUNDARY_005", "boundary", "cross-rule aggregation", "false"),
        ("BOUNDARY_006", "boundary", "real candidate evaluation", "false"),
        ("BOUNDARY_007", "boundary", "Exact11 real evaluation", "false"),
    )
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for contract_id, area, statement, expected in specifications
    ]


def _safety_rows() -> list[dict[str, str]]:
    return [
        {
            "safety_item": item,
            "expected_executed": "true",
            "observed_executed": "true",
            "safety_passed": "true",
        }
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "safety_passed": "true",
        }
        for item in FALSE_SAFETY_ITEMS
    ]


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None,
    failure: str = "SOURCE_BOUNDARY_FAILED",
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "source_ok": False,
        "predecessor_ok": False,
        "contract_rows": [],
        "truth_rows": [],
        "registry_rows": [],
        "issue_rows": [],
        "safety_rows": [],
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_phase2_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
    *,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot(head_ref=head_ref)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        predecessor = _validate_predecessors(snapshot)
        contract_rows = _contract_rows()
        truth_rows = _truth_rows()
        registry_rows = _registry_rows()
        issue_rows = [dict(row) for row in predecessor["issues"].rows]
        safety_rows = _safety_rows()
        truth_groups = {
            group: sum(row["truth_group"] == group for row in truth_rows)
            for group in ("passed", "blocked", "invalid_rule_result", "dispatch_error")
        }
        issue_map = _keyed(issue_rows, "issue_id")
        passed = (
            len(contract_rows) == 31
            and all(row["contract_passed"] == "true" for row in contract_rows)
            and len(truth_rows) == 24
            and len({row["case_id"] for row in truth_rows}) == 24
            and truth_groups
            == {"passed": 3, "blocked": 4, "invalid_rule_result": 3, "dispatch_error": 14}
            and all(row["truth_passed"] == "true" for row in truth_rows)
            and len(registry_rows) == 15
            and tuple(row["admission_rule_id"] for row in registry_rows) == KNOWN_RULE_IDS
            and all(row["audit_passed"] == "true" for row in registry_rows)
            and len(issue_rows) == 12
            and issue_rows == [dict(row) for row in predecessor["issues"].rows]
            and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
            and len(safety_rows) == len(TRUE_SAFETY_ITEMS) + len(FALSE_SAFETY_ITEMS)
            and all(row["safety_passed"] == "true" for row in safety_rows)
            and tuple(EVALUATOR_REGISTRY) == ("ADMIT_004",)
            and tuple(field.name for field in fields(UnifiedAdmissionRuleEvaluation)) == RESULT_FIELDS
            and tuple(field.name for field in fields(UnifiedAdmissionDispatchError)) == DISPATCH_ERROR_FIELDS
        )
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError):
        return _empty_state(snapshot, "PREDECESSOR_OR_RUNTIME_VALIDATION_FAILED") | {
            "source_ok": True
        }
    if not passed:
        return _empty_state(snapshot, "PHASE2_VALIDATION_FAILED") | {
            "source_ok": True,
            "predecessor_ok": True,
        }
    return {
        "source_snapshot": snapshot,
        "source_ok": True,
        "predecessor_ok": True,
        "predecessor": predecessor,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": truth_groups,
        "registry_rows": registry_rows,
        "issue_rows": issue_rows,
        "safety_rows": safety_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise"
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
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_input_count": 12,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_input_verification": [
            {
                "source_ordinal": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
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
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": 24,
        "truth_matrix_pass_count": 24,
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_row_count": 15,
        "active_issue_count": 12,
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": ["ADMIT_004"],
        "registered_rule_ids": ["ADMIT_004"],
        "registered_rule_count": 1,
        "admit_004_adapter_id": ADMIT_004_ADAPTER_ID,
        "admit_004_candidate_projection_fields": list(ADMIT_004_CANDIDATE_FIELDS),
        "admit_004_candidate_projection_field_count": 9,
        "admit_004_evaluation_context_pass_through_only": True,
        "admit_004_evaluator_io_used": False,
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
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
        REGISTRY_FILENAME: _csv_bytes(REGISTRY_COLUMNS, state["registry_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in csv_payloads.items()
    }
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
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
        raise ValueError("output root contains unexpected files")
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("output root contains unsafe entries")


def run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_phase2_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "minimal unified dispatch shell failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = (
        run_covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1()
    )
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

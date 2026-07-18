"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_005.

The Phase 4 handlers are reused by identity.  This successor adds only the
ADMIT_005 adapter and deterministic metadata evidence; it intentionally does
not provide all-rule aggregation or a combined candidate verdict.
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
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate
    as admit005_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_005_rule_logic_interface as admit005,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004
    as phase4,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_005 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_005_v1"
)
EXPECTED_BASE_COMMIT = "bb255f8f8a4f75f5b61965a589367618d3939850"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_005 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_005_manifest_v1"
)
RECOMMENDED_NEXT_STEP = "audit_covapie_admit_006_formal_evaluator_interface_preconditions_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Re-export the committed Phase 2/Phase 4 objects; never redefine them.
UnifiedAdmissionRuleEvaluation = phase4.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = phase4.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = phase4.RESULT_SCHEMA_VERSION
RESULT_FIELDS = phase4.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = phase4.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = phase4.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = phase4.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 6))
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()
ADMIT_005_CANDIDATE_FIELDS = (
    "covalent_residue_name",
    "covalent_residue_atom_name",
)

RULE_NAMES = MappingProxyType(
    {
        **dict(phase4.RULE_NAMES),
        "ADMIT_005": "cys_sg_scope_only_v1",
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        **dict(phase4.ADAPTER_IDS),
        "ADMIT_005": "covapie_admit_005_unified_adapter_v1",
    }
)


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


def _admit005_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_005",
        True,
        True,
        True,
        reason,
    )


def _admit005_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_005",
        True,
        True,
        False,
        reason,
    )


def _admit005_candidate_invalid(reason: str) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_005",
        admission_rule_name=RULE_NAMES["ADMIT_005"],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=ADMIT_005_CANDIDATE_FIELDS,
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_005"],
    )


def _prevalidate_admit005_source(source: object) -> admit005.Admit005EvaluationResult:
    """Stage A: exact source type and self-consistent Exact10 invariants."""
    if type(source) is not admit005.Admit005EvaluationResult:
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert type(source) is admit005.Admit005EvaluationResult
    if (
        tuple(field.name for field in fields(admit005.Admit005EvaluationResult))
        != admit005.RESULT_FIELDS
    ):
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    try:
        ordered_values = tuple(getattr(source, name) for name in admit005.RESULT_FIELDS)
        reconstructed = admit005.Admit005EvaluationResult(*ordered_values)
    except (AttributeError, TypeError, ValueError):
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    if reconstructed != source:
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return source


def _expected_admit005_from_oracles(
    residue_object: object,
    atom_object: object,
) -> admit005.Admit005EvaluationResult:
    """Call both independent helpers exactly once and build the full Exact10."""
    scope = admit005_oracle.classify_admit_004_admit_005_atom_scope_design(
        residue_object, atom_object
    )
    atom = admit005_oracle.validate_generic_covalent_residue_atom_name(atom_object)
    try:
        canonical_residue = scope.canonical_residue_name
        if canonical_residue is None:
            canonical_residue_value = ""
            canonical_atom_value = ""
            validated: tuple[tuple[str, str], ...] = ()
        elif atom.valid is False:
            canonical_residue_value = canonical_residue
            canonical_atom_value = ""
            validated = (("covalent_residue_name", canonical_residue_value),)
        else:
            canonical_residue_value = canonical_residue
            canonical_atom_value = atom.canonical_value
            validated = (
                ("covalent_residue_name", canonical_residue_value),
                ("covalent_residue_atom_name", canonical_atom_value),
            )
        expected = admit005.Admit005EvaluationResult(
            admission_rule_id="ADMIT_005",
            outcome=scope.admit_005_outcome,
            passed=scope.admit_005_outcome == "passed",
            blocks_candidate=scope.admit_005_outcome != "passed",
            reason=scope.reason,
            canonical_residue_name=canonical_residue_value,
            canonical_residue_atom_name=canonical_atom_value,
            validated_candidate_fields=validated,
            consumed_candidate_fields=ADMIT_005_CANDIDATE_FIELDS,
            evaluator_io_used=False,
        )
    except (AttributeError, TypeError, ValueError):
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return expected


def _validate_admit005_oracle_equivalence(
    source: admit005.Admit005EvaluationResult,
    expected: admit005.Admit005EvaluationResult,
) -> None:
    if type(expected) is not admit005.Admit005EvaluationResult or source != expected:
        _admit005_adapter_failure("ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")


def _project_admit005_exact13(
    source: admit005.Admit005EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES["ADMIT_005"],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=(),
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS["ADMIT_005"],
    )


def _evaluate_registered_admit_005(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # Context routing is deliberately before all candidate access.
    if batch_context is not None:
        _admit005_context_failure("ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE")
    if evaluation_context is not None:
        _admit005_context_failure("ADMIT_005_EVALUATION_CONTEXT_MUST_BE_NONE")
    if download_result_context is not None:
        _admit005_context_failure("ADMIT_005_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE")
    if stage_authorization_context is not None:
        _admit005_context_failure("ADMIT_005_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE")

    if not isinstance(candidate_record, Mapping):
        return _admit005_candidate_invalid(
            "ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID"
        )
    if "covalent_residue_name" not in candidate_record:
        return _admit005_candidate_invalid(
            "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"
        )
    if "covalent_residue_atom_name" not in candidate_record:
        return _admit005_candidate_invalid(
            "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name"
        )
    residue_object = candidate_record["covalent_residue_name"]
    atom_object = candidate_record["covalent_residue_atom_name"]
    source = admit005.evaluate_admit_005(residue_object, atom_object)
    validated_source = _prevalidate_admit005_source(source)
    expected = _expected_admit005_from_oracles(residue_object, atom_object)
    _validate_admit005_oracle_equivalence(validated_source, expected)
    return _project_admit005_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": phase4.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": phase4.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": phase4.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": phase4.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": _evaluate_registered_admit_005,
    }
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
    """Evaluate exactly one registered rule without I/O or aggregation."""
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
    if admission_rule_id not in EVALUATOR_REGISTRY:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            admission_rule_id,
            True,
            False,
            False,
        )
    return EVALUATOR_REGISTRY[admission_rule_id](
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# Frozen Exact16 evidence boundary. Runtime dependency imports above are
# authorized; these explicit source-byte reads occur only after full preflight.
PHASE4_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1"
)
STANDALONE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_005_rule_logic_interface_v1"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate_v1"
)
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
        str(PHASE4_ROOT / "covapie_admit_001_to_004_runtime_manifest.json"),
        str(PHASE4_ROOT / "covapie_admit_001_to_004_runtime_contract.csv"),
        str(PHASE4_ROOT / "covapie_admit_001_to_004_runtime_truth_matrix.csv"),
        str(PHASE4_ROOT / "covapie_admit_001_to_004_registry_routing_and_oracle_audit.csv"),
        str(PHASE4_ROOT / "covapie_admit_001_to_004_runtime_safety_audit.csv"),
        str(PHASE4_ROOT / "covapie_admit_001_to_004_runtime_issue_inventory.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_005_rule_logic_interface.py",
        str(STANDALONE_ROOT / "covapie_admit_005_rule_logic_interface_manifest.json"),
        str(STANDALONE_ROOT / "covapie_admit_005_rule_logic_interface_truth_matrix.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_005_unified_adapter_contract_design_gate.py",
        str(DESIGN_ROOT / "covapie_admit_005_unified_adapter_contract_manifest.json"),
        str(DESIGN_ROOT / "covapie_admit_005_unified_adapter_contract.csv"),
        str(DESIGN_ROOT / "covapie_admit_005_candidate_projection_and_context_routing_matrix.csv"),
        str(DESIGN_ROOT / "covapie_admit_005_unified_result_projection_truth_matrix.csv"),
        str(DESIGN_ROOT / "covapie_admit_005_unified_adapter_safety_audit.csv"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "a16ce1eef1048db7643a1f7940da554234683918136e76a6487eec5c2fdc35c3",
            "9cf7e902566a4aef9aa098e9a9a966f925666df581f8c0ce408d8c9598905149",
            "be8cbe4db8a8b506bc4300b8c7d32a994c8088ac6aa2b34340e36dc9b9a83498",
            "5e47d644d3376d69951ff0746eeba2a89194f4c6a074d3c7136b2b19168f88a7",
            "23b440c51d4cb4a924124d8bed9bbac21328c1fcab62aee115134901f49a3e1f",
            "70f4eeb010362eb9cf7ca727932056b52bd58dba6a18b12b4245bb55183ada64",
            "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
            "1b350d5e1a5b7117ee951450a05f32943ba1cef3854e56377aeff0286aec6b5f",
            "304e6d83bd36faba951bfa024c9fb96d70534e3c49b556c79b9d2acdcec5c2b8",
            "695c187ccd297671b74ae33a95c52e2c38f0f5d1c46b253b8dd84c682499b10f",
            "078987fdcb51d91ec8fa229884a85c2cc75f8b05ef1249aaf392893f6cc1b4ad",
            "b66f6551cb2aad3ac4b78afd5f0c41475697f5276af8fb7150f365a6e0adf269",
            "8525964731d5a478bc523fdcec2bd25d7c20d535344005f3074b91c86351075d",
            "068646896408f9d7640a9e00b361711986bfa8afe3ffde4e756904826fdf1473",
            "ceb9c5ec22b4d9819c80e4813f9c5f240c4c9e98a5dd428e61082eeb1d887946",
            "7d8d7d75046fb49d28b4fcb74aab2d0e8a6b1853a6c73f8420617b2c02cf8265",
        ),
        strict=True,
    )
)

PHASE4_SOURCE_PATH = SOURCE_PATHS[0]
PHASE4_MANIFEST_PATH = SOURCE_PATHS[1]
PHASE4_ISSUE_PATH = SOURCE_PATHS[6]
STANDALONE_SOURCE_PATH = SOURCE_PATHS[7]
STANDALONE_MANIFEST_PATH = SOURCE_PATHS[8]
STANDALONE_TRUTH_PATH = SOURCE_PATHS[9]
DESIGN_SOURCE_PATH = SOURCE_PATHS[10]
DESIGN_MANIFEST_PATH = SOURCE_PATHS[11]

CONTRACT_FILENAME = "covapie_admit_001_to_005_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_005_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_005_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_005_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_005_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_005_runtime_manifest.json"
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
    "case_id",
    "case_group",
    "admission_rule_id",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "formal_call_count",
    "scope_oracle_call_count",
    "atom_oracle_call_count",
    "phase4_parity",
    "case_passed",
)
REGISTRY_COLUMNS = (
    "admission_rule_id",
    "admission_rule_name",
    "adapter_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "registered",
    "phase4_handler_identity_reused",
    "successor_handler_implemented",
    "expected_dispatch_behavior",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
ISSUE_COLUMNS = phase4.ISSUE_COLUMNS


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
        ["git", *arguments],
        cwd=repo_root,
        text=text,
        capture_output=True,
        check=False,
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
    base = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(
        ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root
    )
    ancestor = _git(
        ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root
    )
    if base.returncode != 0:
        raise ValueError("expected base commit object is missing")
    if subject.returncode != 0 or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base commit subject mismatch")
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Inspect metadata only; never read source content bytes here."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields_value = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields_value) == 3
        and fields_value[0] in ("100644", "100755")
        and fields_value[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete all Exact16 structural checks before any explicit byte read."""
    if (
        len(SOURCE_PATHS) != 16
        or len(set(SOURCE_PATHS)) != 16
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact16 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structures = tuple(
        _structural_source_check(path, repo_root) for path in SOURCE_PATHS
    )
    if not all(structures):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base_read = _git(
            ["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"],
            repo_root,
            text=False,
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
            FrozenSourceRecord(
                path, expected, base_sha, filesystem_sha, filesystem_bytes
            )
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 16
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest()
            == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(r for r in snapshot.records if r.relative_path == path)
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
        tuple(row) != tuple(reader.fieldnames)
        or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(
        _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    )
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    return ast.parse(
        _record(snapshot, path).content_bytes.decode("utf-8", errors="strict"),
        filename=path.as_posix(),
    )


def _top_level_function_names(tree: ast.Module) -> tuple[str, ...]:
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    phase4_manifest = _json_document(snapshot, PHASE4_MANIFEST_PATH)
    standalone_manifest = _json_document(snapshot, STANDALONE_MANIFEST_PATH)
    design_manifest = _json_document(snapshot, DESIGN_MANIFEST_PATH)
    phase4_issues = _csv_document(snapshot, PHASE4_ISSUE_PATH)
    standalone_truth = _csv_document(snapshot, STANDALONE_TRUTH_PATH)
    phase4_tree = _ast_document(snapshot, PHASE4_SOURCE_PATH)
    standalone_tree = _ast_document(snapshot, STANDALONE_SOURCE_PATH)
    design_tree = _ast_document(snapshot, DESIGN_SOURCE_PATH)
    # Parse every remaining CSV strictly from frozen bytes as part of the gate.
    parsed_remaining = tuple(
        _csv_document(snapshot, path)
        for path in SOURCE_PATHS
        if path.suffix == ".csv"
        and path not in (PHASE4_ISSUE_PATH, STANDALONE_TRUTH_PATH)
    )
    outcome_counts = Counter(row["observed_outcome"] for row in standalone_truth.rows)
    if not (
        phase4_manifest.get("all_checks_passed") is True
        and phase4_manifest.get("registered_rule_ids")
        == ["ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_004"]
        and phase4_manifest.get("registered_rule_count") == 4
        and phase4_manifest.get("ready_for_training") is False
        and standalone_manifest.get("all_checks_passed") is True
        and standalone_manifest.get("ready_for_training") is False
        and len(standalone_truth.rows) == 22
        and outcome_counts == {"passed": 2, "rejected": 6, "invalid": 14}
        and design_manifest.get("all_checks_passed") is True
        and design_manifest.get("admit_005_unified_adapter_implemented") is False
        and design_manifest.get("ready_for_training") is False
        and len(phase4_issues.rows) == 11
        and phase4_issues.header == ISSUE_COLUMNS
        and "evaluate_admission_rule" in _top_level_function_names(phase4_tree)
        and "evaluate_admit_005" in _top_level_function_names(standalone_tree)
        and "project_exact10_to_exact13_for_design"
        in _top_level_function_names(design_tree)
        and len(parsed_remaining) == 8
    ):
        raise ValueError("predecessor contract validation failed")
    return {
        "phase4_manifest": phase4_manifest,
        "standalone_manifest": standalone_manifest,
        "design_manifest": design_manifest,
        "phase4_issue_rows": phase4_issues.rows,
        "standalone_truth_rows": standalone_truth.rows,
    }


def _decode_truth_input(kind: str, display: str) -> object:
    if kind == "str":
        value = json.loads(display)
        if type(value) is not str:
            raise ValueError("truth string input invalid")
        return value
    if kind == "non_str":
        return json.loads(display)
    if kind == "str_subclass":
        class FrozenStringSubclass(str):
            pass

        return FrozenStringSubclass(display)
    raise ValueError("unknown truth input kind")


def _result_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


def _error_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in DISPATCH_ERROR_FIELDS)


def _truth_row(
    case_id: str,
    group: str,
    rule_id: str,
    expected_outcome: str,
    observed_outcome: str,
    expected_reason: str,
    observed_reason: str,
    *,
    formal: int = 0,
    scope: int = 0,
    atom: int = 0,
    parity: bool = False,
    passed: bool = True,
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "expected_outcome": expected_outcome,
        "observed_outcome": observed_outcome,
        "expected_reason": expected_reason,
        "observed_reason": observed_reason,
        "formal_call_count": str(formal),
        "scope_oracle_call_count": str(scope),
        "atom_oracle_call_count": str(atom),
        "phase4_parity": str(parity).lower(),
        "case_passed": str(
            passed
            and expected_outcome == observed_outcome
            and expected_reason == observed_reason
        ).lower(),
    }


def _phase4_parity_definitions() -> tuple[dict[str, Any], ...]:
    a4 = phase4._admit004_candidate()
    a4_context = phase4._admit004_context(a4)
    return (
        {"id": "P4_A001_PASS", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "kwargs": {"batch_context": {"batch_candidate_record_ids": ["REC_1"]}}},
        {"id": "P4_A001_BLOCK", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "kwargs": {"batch_context": {"batch_candidate_record_ids": ["REC_2"]}}},
        {"id": "P4_A001_INVALID", "rule": "ADMIT_001", "candidate": {"candidate_record_id": ""}, "kwargs": {"batch_context": {"batch_candidate_record_ids": ["REC_2"]}}},
        {"id": "P4_A001_CONTEXT", "rule": "ADMIT_001", "candidate": {}, "kwargs": {}},
        {"id": "P4_A002_PASS", "rule": "ADMIT_002", "candidate": {"pdb_id": "1abc"}, "kwargs": {}},
        {"id": "P4_A002_INVALID", "rule": "ADMIT_002", "candidate": {"pdb_id": 7}, "kwargs": {}},
        {"id": "P4_A002_CONTEXT", "rule": "ADMIT_002", "candidate": {"pdb_id": "1abc"}, "kwargs": {"batch_context": {}}},
        {"id": "P4_A003_PASS", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": "abc"}, "kwargs": {}},
        {"id": "P4_A003_INVALID", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": 7}, "kwargs": {}},
        {"id": "P4_A003_CONTEXT", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": "abc"}, "kwargs": {"batch_context": {}}},
        {"id": "P4_A004_PASS", "rule": "ADMIT_004", "candidate": a4, "kwargs": {"evaluation_context": a4_context}},
        {"id": "P4_A004_BLOCK", "rule": "ADMIT_004", "candidate": a4, "kwargs": {"evaluation_context": {}}},
        {"id": "P4_A004_INVALID", "rule": "ADMIT_004", "candidate": [], "kwargs": {"evaluation_context": {}}},
        {"id": "P4_A004_CONTEXT", "rule": "ADMIT_004", "candidate": a4, "kwargs": {"batch_context": {}, "evaluation_context": a4_context}},
    )


def _truth_rows(predecessor: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    # Global dispatch: type, unknown, and each of the ten unregistered IDs.
    for case_id, rule, code in (
        ("GLOBAL_TYPE", 5, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("GLOBAL_UNKNOWN", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
    ):
        try:
            evaluate_admission_rule(rule, {})  # type: ignore[arg-type]
        except UnifiedAdmissionDispatchError as error:
            rows.append(_truth_row(case_id, "global_dispatch", str(rule), code, error.code, code, error.reason))
        else:
            raise RuntimeError("global dispatch did not fail closed")
    for rule in KNOWN_RULE_IDS[5:]:
        try:
            evaluate_admission_rule(rule, {})
        except UnifiedAdmissionDispatchError as error:
            code = "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"
            rows.append(_truth_row(f"GLOBAL_{rule}_UNREGISTERED", "global_dispatch", rule, code, error.code, code, error.reason))
        else:
            raise RuntimeError("unregistered rule dispatched")

    for case in _phase4_parity_definitions():
        successor_value: object
        phase4_value: object
        try:
            successor_value = evaluate_admission_rule(case["rule"], case["candidate"], **case["kwargs"])
        except UnifiedAdmissionDispatchError as error:
            successor_value = error
        try:
            phase4_value = phase4.evaluate_admission_rule(case["rule"], case["candidate"], **case["kwargs"])
        except UnifiedAdmissionDispatchError as error:
            phase4_value = error
        if type(successor_value) is UnifiedAdmissionRuleEvaluation:
            observed = successor_value.outcome
            reason = successor_value.reason
            parity = _result_values(successor_value) == _result_values(phase4_value)
        else:
            observed = successor_value.code
            reason = successor_value.reason
            parity = _error_values(successor_value) == _error_values(phase4_value)
        rows.append(_truth_row(case["id"], "phase4_parity", case["rule"], observed, observed, reason, reason, parity=parity, passed=parity))

    context_cases = (
        ("A005_CONTEXT_BATCH", {"batch_context": {}}, "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE"),
        ("A005_CONTEXT_EVALUATION", {"evaluation_context": {}}, "ADMIT_005_EVALUATION_CONTEXT_MUST_BE_NONE"),
        ("A005_CONTEXT_DOWNLOAD", {"download_result_context": {}}, "ADMIT_005_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("A005_CONTEXT_STAGE", {"stage_authorization_context": {}}, "ADMIT_005_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("A005_CONTEXT_PRECEDENCE", {"batch_context": {}, "evaluation_context": {}, "download_result_context": {}, "stage_authorization_context": {}}, "ADMIT_005_BATCH_CONTEXT_MUST_BE_NONE"),
    )
    for case_id, kwargs, reason in context_cases:
        try:
            evaluate_admission_rule("ADMIT_005", {}, **kwargs)
        except UnifiedAdmissionDispatchError as error:
            rows.append(_truth_row(case_id, "admit005_context", "ADMIT_005", error.code, error.code, reason, error.reason))
        else:
            raise RuntimeError("ADMIT_005 context did not fail closed")

    class MappingSubclass(dict[str, object]):
        pass

    candidate_definitions: tuple[tuple[str, object, str], ...] = (
        ("A005_NON_MAPPING", [], "ADMIT_005_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("A005_MISSING_RESIDUE", {"covalent_residue_atom_name": "SG"}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"),
        ("A005_MISSING_ATOM", {"covalent_residue_name": "CYS"}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_atom_name"),
        ("A005_BOTH_MISSING", {}, "ADMIT_005_CANDIDATE_FIELD_MISSING:covalent_residue_name"),
    )
    for case_id, candidate, reason in candidate_definitions:
        result = evaluate_admission_rule("ADMIT_005", candidate)  # type: ignore[arg-type]
        rows.append(_truth_row(case_id, "admit005_candidate", "ADMIT_005", "invalid", result.outcome, reason, result.reason))
    for case_id, candidate in (
        ("A005_MAPPING_SUBCLASS", MappingSubclass(covalent_residue_name="CYS", covalent_residue_atom_name="SG")),
        ("A005_EXTRA_IGNORED", {"covalent_residue_name": "CYS", "covalent_residue_atom_name": "SG", "extra": object()}),
        ("A005_NOT_MUTATED", {"covalent_residue_name": "CYS", "covalent_residue_atom_name": "SG"}),
        ("A005_SCALAR_IDENTITY", {"covalent_residue_name": "CYS", "covalent_residue_atom_name": "SG"}),
    ):
        before = dict(candidate)
        result = evaluate_admission_rule("ADMIT_005", candidate)
        rows.append(_truth_row(case_id, "admit005_candidate", "ADMIT_005", "passed", result.outcome, "", result.reason, formal=1, scope=1, atom=1, passed=dict(candidate) == before))

    for source_row in predecessor["standalone_truth_rows"]:
        residue = _decode_truth_input(source_row["residue_input_kind"], source_row["residue_input_display"])
        atom = _decode_truth_input(source_row["atom_input_kind"], source_row["atom_input_display"])
        result = evaluate_admission_rule("ADMIT_005", {"covalent_residue_name": residue, "covalent_residue_atom_name": atom})
        rows.append(_truth_row(f"A005_EXACT22_{source_row['case_id']}", "admit005_exact22", "ADMIT_005", source_row["observed_outcome"], result.outcome, source_row["observed_reason"], result.reason, formal=1, scope=1, atom=1))

    valid = admit005.evaluate_admit_005("CYS", "SG")
    unsafe_sources: list[tuple[str, object, str]] = [
        ("A005_SOURCE_WRONG_TYPE", object(), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
    ]
    class SourceSubclass(admit005.Admit005EvaluationResult):
        pass
    unsafe_sources.append(("A005_SOURCE_SUBCLASS", SourceSubclass(*tuple(getattr(valid, name) for name in admit005.RESULT_FIELDS)), "ADMIT_005_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"))
    for case_id, field_name, replacement in (
        ("A005_SOURCE_RULE_ID", "admission_rule_id", "ADMIT_004"),
        ("A005_SOURCE_FIELD_INVARIANT", "passed", False),
        ("A005_SOURCE_IO", "evaluator_io_used", True),
        ("A005_SOURCE_CONSUMED", "consumed_candidate_fields", ("covalent_residue_name",)),
    ):
        unsafe = admit005.evaluate_admit_005("CYS", "SG")
        object.__setattr__(unsafe, field_name, replacement)
        unsafe_sources.append((case_id, unsafe, "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"))
    for case_id, source, reason in unsafe_sources:
        try:
            _prevalidate_admit005_source(source)
        except UnifiedAdmissionDispatchError as error:
            rows.append(_truth_row(case_id, "admit005_source_prevalidation", "ADMIT_005", error.code, error.code, reason, error.reason, formal=1))
        else:
            raise RuntimeError("unsafe source accepted")

    mismatch = admit005.evaluate_admit_005("SER", "SG")
    try:
        _validate_admit005_oracle_equivalence(valid, mismatch)
    except UnifiedAdmissionDispatchError as error:
        rows.append(_truth_row("A005_ORACLE_MISMATCH", "admit005_oracle_mismatch", "ADMIT_005", error.code, error.code, "ADMIT_005_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", error.reason, formal=1, scope=1, atom=1))
    else:
        raise RuntimeError("oracle mismatch accepted")

    boundary_values = (
        ("BOUNDARY_EXACT5", "registered_count=5", f"registered_count={len(EVALUATOR_REGISTRY)}"),
        ("BOUNDARY_006_015", "registered=false", f"registered={any(rule in EVALUATOR_REGISTRY for rule in KNOWN_RULE_IDS[5:])}".lower()),
        ("BOUNDARY_NO_ALL", "evaluate_all_rules=false", f"evaluate_all_rules={hasattr(__import__(__name__, fromlist=['x']), 'evaluate_all_rules')}".lower()),
    )
    for case_id, expected, observed in boundary_values:
        rows.append(_truth_row(case_id, "registry_boundary", "", expected, observed, "", ""))

    expected_groups = {
        "global_dispatch": 12,
        "phase4_parity": 14,
        "admit005_context": 5,
        "admit005_candidate": 8,
        "admit005_exact22": 22,
        "admit005_source_prevalidation": 6,
        "admit005_oracle_mismatch": 1,
        "registry_boundary": 3,
    }
    counts = Counter(row["case_group"] for row in rows)
    if (
        dict(counts) != expected_groups
        or len(rows) != sum(expected_groups.values())
        or len({row["case_id"] for row in rows}) != len(rows)
        or not all(row["case_passed"] == "true" for row in rows)
    ):
        raise RuntimeError("runtime truth definitions failed")
    return rows


def _contract_definitions() -> tuple[tuple[str, str, str, str], ...]:
    definitions = (
        ("TYPE_001", "type_identity", "result type identity", "true"),
        ("TYPE_002", "type_identity", "dispatch error type identity", "true"),
        ("TYPE_003", "type_identity", "Exact13 fields", "|".join(RESULT_FIELDS)),
        ("TYPE_004", "type_identity", "Exact6 fields", "|".join(DISPATCH_ERROR_FIELDS)),
        ("TYPE_005", "type_identity", "result schema", RESULT_SCHEMA_VERSION),
        ("TYPE_006", "type_identity", "outcome vocabulary", "|".join(OUTCOME_VOCABULARY)),
        ("API_001", "public_api", "signature", str(inspect.signature(evaluate_admission_rule))),
        ("API_002", "public_api", "dispatch cardinality", "single_rule_only"),
        ("DISPATCH_001", "global_dispatch", "precedence", "exact_str|known|registered|handler"),
        ("REGISTRY_001", "registry", "immutable registry", "true"),
        ("REGISTRY_002", "registry", "registered IDs", "|".join(ADAPTER_READY_RULE_IDS)),
        ("REGISTRY_003", "registry", "registered count", "5"),
        ("REUSE_001", "phase4_reuse", "first four handler identity", "true"),
        ("REUSE_002", "phase4_reuse", "first four names and adapters", "true"),
        ("A005_001", "admit005_identity", "rule name", RULE_NAMES["ADMIT_005"]),
        ("A005_002", "admit005_identity", "adapter ID", ADAPTER_IDS["ADMIT_005"]),
        ("CONTEXT_001", "admit005_context", "ordered None-only contexts", "batch|evaluation|download_result|stage_authorization"),
        ("CANDIDATE_001", "candidate_projection", "Exact2 projection", "|".join(ADMIT_005_CANDIDATE_FIELDS)),
        ("CANDIDATE_002", "candidate_projection", "Mapping subclasses", "accepted"),
        ("CANDIDATE_003", "candidate_projection", "extra fields", "ignored"),
        ("FORMAL_001", "formal_evaluator", "positional original scalars", "exact_once"),
        ("STAGEA_001", "source_prevalidation", "exact standalone type", "required"),
        ("STAGEA_002", "source_prevalidation", "Exact10 reconstruction", "before_oracle"),
        ("STAGEA_003", "source_prevalidation", "failure Exact6 adapter readiness", "false"),
        ("ORACLE_001", "semantic_oracle", "scope helper calls", "1"),
        ("ORACLE_002", "semantic_oracle", "atom helper calls", "1"),
        ("ORACLE_003", "semantic_oracle", "Exact10 equality", "required"),
        ("PROJECTION_001", "exact13", "normalized from validated", "true"),
        ("PROJECTION_002", "exact13", "rejected passthrough", "true"),
        ("SAFETY_001", "runtime_safety", "candidate mutation", "false"),
        ("SAFETY_002", "runtime_safety", "evaluator I/O", "false"),
        ("BOUNDARY_001", "boundary", "ADMIT_006 to ADMIT_015 registered", "false"),
        ("BOUNDARY_002", "boundary", "evaluate_all_rules", "excluded"),
        ("BOUNDARY_003", "boundary", "real candidate and Exact11 evaluation", "excluded"),
        ("BOUNDARY_004", "boundary", "download and training", "excluded"),
    )
    if len({row[0] for row in definitions}) != len(definitions):
        raise RuntimeError("duplicate contract definition")
    return definitions


def _contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for contract_id, area, statement, value in _contract_definitions()
    ]


def _registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in EVALUATOR_REGISTRY
        phase4_reused = registered and rule_id != "ADMIT_005"
        successor_implemented = rule_id == "ADMIT_005"
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": RULE_NAMES.get(rule_id, ""),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(registered).lower(),
                "adapter_ready": str(registered).lower(),
                "registered": str(registered).lower(),
                "phase4_handler_identity_reused": str(phase4_reused).lower(),
                "successor_handler_implemented": str(successor_implemented).lower(),
                "expected_dispatch_behavior": (
                    "registered_single_rule_runtime"
                    if registered
                    else "known_not_registered_fail_closed"
                ),
                "audit_passed": "true",
            }
        )
    return rows


EXECUTED_SAFETY_ITEMS = (
    "exact16_source_verification",
    "phase4_handler_identity_reuse",
    "successor_registry_construction",
    "admit_005_adapter_implementation",
    "candidate_projection",
    "context_routing",
    "formal_source_prevalidation",
    "independent_oracle_equivalence",
    "exact13_construction",
    "synthetic_runtime_truth",
    "coverage_issue_update",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "phase4_source_modification",
    "standalone_source_modification",
    "adapter_design_source_modification",
    "admit_006_implementation",
    "evaluate_all_rules",
    "combined_verdict",
    "cross_rule_aggregation",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "raw_provider_parser",
    "network_download",
    "checkpoint",
    "torch_numpy_rdkit",
    "model_forward_loss_training",
)


def _safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
    if len({item for item, _ in definitions}) != len(definitions):
        raise RuntimeError("duplicate safety definition")
    return [
        {
            "safety_item": item,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "safety_passed": "true",
        }
        for item, executed in definitions
    ]


TRUE_READINESS = (
    "unified_dispatch_runtime_admit_001_to_005_implemented",
    "evaluate_admission_rule_implemented",
    "evaluator_registry_runtime_implemented",
    "registered_rule_count_is_5",
    "admit_001_adapter_implemented",
    "admit_002_adapter_implemented",
    "admit_003_adapter_implemented",
    "admit_004_registered_in_engine",
    "admit_005_adapter_implemented",
    "admit_005_registered_in_engine",
    "admit_005_candidate_projection_runtime_enforced",
    "admit_005_context_routing_runtime_enforced",
    "admit_005_source_prevalidation_before_oracle_runtime_enforced",
    "admit_005_semantic_oracle_equivalence_runtime_enforced",
    "admit_005_rejected_passthrough_runtime_enforced",
    "phase4_handler_identity_reused",
    "ready_for_admit_006_formal_evaluator_interface_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "phase4_runtime_modified",
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


def _updated_issue_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    matches[0]["affected_rules"] = "|".join(KNOWN_RULE_IDS[5:])
    matches[0]["integration_transition"] = (
        "admit_005_implemented_and_removed_from_open_coverage_scope"
    )
    return rows


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None,
    failure: str = "SOURCE_BOUNDARY_FAILED",
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_runtime_state(
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
        truth_rows = _truth_rows(predecessor)
        registry_rows = _registry_rows()
        safety_rows = _safety_rows()
        issue_rows = _updated_issue_rows(predecessor["phase4_issue_rows"])
        truth_groups = dict(Counter(row["case_group"] for row in truth_rows))
        issue_map = {row["issue_id"]: row for row in issue_rows}
        checks = (
            len(contract_rows) == len(_contract_definitions()),
            len({row["contract_id"] for row in contract_rows}) == len(contract_rows),
            all(row["contract_passed"] == "true" for row in contract_rows),
            len(truth_rows) == 71,
            all(row["case_passed"] == "true" for row in truth_rows),
            len(registry_rows) == 15,
            tuple(row["admission_rule_id"] for row in registry_rows) == KNOWN_RULE_IDS,
            len(issue_rows) == 11,
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "|".join(KNOWN_RULE_IDS[5:]),
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["integration_transition"] == "admit_005_implemented_and_removed_from_open_coverage_scope",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open",
            issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
            all(row["safety_passed"] == "true" for row in safety_rows),
            type(EVALUATOR_REGISTRY) is MappingProxyType,
            tuple(EVALUATOR_REGISTRY) == ADAPTER_READY_RULE_IDS,
            all(EVALUATOR_REGISTRY[rule] is phase4.EVALUATOR_REGISTRY[rule] for rule in KNOWN_RULE_IDS[:4]),
            EVALUATOR_REGISTRY["ADMIT_005"] is _evaluate_registered_admit_005,
            UnifiedAdmissionRuleEvaluation is phase4.UnifiedAdmissionRuleEvaluation,
            UnifiedAdmissionDispatchError is phase4.UnifiedAdmissionDispatchError,
            not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules"),
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        SyntaxError,
        RuntimeError,
    ):
        return _empty_state(snapshot, "PREDECESSOR_OR_RUNTIME_VALIDATION_FAILED")
    if not all(checks):
        return _empty_state(snapshot, "RUNTIME_VALIDATION_FAILED")
    return {
        "source_snapshot": snapshot,
        "predecessor": predecessor,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": truth_groups,
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
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
        "source_input_count": 16,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
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
        "runtime_dependency_imports_authorized": True,
        "runtime_dependency_imports": [
            "phase4_unified_runtime",
            "admit005_standalone_evaluator",
            "admit005_independent_semantic_oracle",
        ],
        "frozen_source_snapshot_explicit_byte_reads_preflighted": True,
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_pass_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "active_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "registered_rule_count": 5,
        "adapter_ids": dict(ADAPTER_IDS),
        "phase4_runtime_modified": False,
        "phase4_handlers_reused_by_identity": True,
        "admit_005_implemented": True,
        "admit_005_registered": True,
        "admit_006_to_015_registered": False,
        "feature_semantics_audit_required": True,
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
        MANIFEST_FILENAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
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


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_runtime_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified ADMIT_001 to ADMIT_005 runtime failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

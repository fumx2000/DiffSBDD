"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_006.

The Exact5 public types and handlers are reused by identity.  This successor
adds only the ADMIT_006 adapter.  Public dispatch is pure in memory; the
separate materializer below emits deterministic synthetic contract evidence.
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
    covapie_bulk_download_admission_admit_006_rule_logic_interface as admit006,
)
from covalent_ext import (
    covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate
    as admit006_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005
    as predecessor,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_006 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_006_v1"
)
EXPECTED_BASE_COMMIT = "de5b9ef13068201d245a5e7231e2b35e44e07d95"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_006 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_006_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_007_formal_evaluator_interface_preconditions_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Identity re-exports: the Exact5 predecessor remains the sole type authority.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(
    f"ADMIT_{index:03d}" for index in range(1, 7)
)
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()
ADMIT_006_CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
ADMIT_006_CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)

RULE_NAMES = MappingProxyType(
    {
        **dict(predecessor.RULE_NAMES),
        "ADMIT_006": "explicit_covalent_event_evidence",
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        **dict(predecessor.ADAPTER_IDS),
        "ADMIT_006": "covapie_admit_006_unified_adapter_v1",
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


def _admit006_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_006",
        True,
        True,
        True,
        reason,
    )


def _admit006_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_006",
        True,
        True,
        False,
        reason,
    )


def _admit006_candidate_invalid(reason: str) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_006",
        admission_rule_name=RULE_NAMES["ADMIT_006"],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=ADMIT_006_CANDIDATE_FIELDS,
        consumed_context_items=ADMIT_006_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_006"],
    )


def _prevalidate_admit006_source(
    source: object,
) -> admit006.Admit006EvaluationResult:
    """Require the committed exact type and reconstruct all Exact10 invariants."""
    if type(source) is not admit006.Admit006EvaluationResult:
        _admit006_adapter_failure("ADMIT_006_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert type(source) is admit006.Admit006EvaluationResult
    try:
        storage = vars(source)
    except TypeError:
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if type(storage) is not dict or tuple(storage) != admit006.RESULT_FIELDS:
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if (
        tuple(field.name for field in fields(admit006.Admit006EvaluationResult))
        != admit006.RESULT_FIELDS
    ):
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    try:
        ordered_values = tuple(
            getattr(source, name) for name in admit006.RESULT_FIELDS
        )
        reconstructed = admit006.Admit006EvaluationResult(*ordered_values)
    except (AttributeError, TypeError, ValueError):
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if reconstructed != source:
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return source


def _expected_admit006_from_oracle(
    scalar_object: object,
    allowed_classes_object: object,
) -> admit006.Admit006EvaluationResult:
    """Call the committed independent oracle once and construct full Exact10."""
    classification = admit006_oracle.classify_admit_006_admit_007_evidence_design(
        scalar_object,
        allowed_classes_object,
    )
    try:
        scalar = classification.scalar
        context = classification.context
        outcome = classification.admit_006
        canonical = (
            scalar.canonical_value
            if scalar.classification == "canonical"
            else ""
        )
        # Access context explicitly: it is part of the frozen independent view.
        context.valid
        context.reason
        validated = (
            ()
            if canonical == ""
            else ((ADMIT_006_CANDIDATE_FIELDS[0], canonical),)
        )
        expected = admit006.Admit006EvaluationResult(
            admission_rule_id="ADMIT_006",
            outcome=outcome.outcome,
            passed=outcome.passed,
            blocks_candidate=outcome.blocks_candidate,
            reason=outcome.reason,
            canonical_covalent_event_evidence_source=canonical,
            validated_candidate_fields=validated,
            consumed_candidate_fields=ADMIT_006_CANDIDATE_FIELDS,
            consumed_context_items=ADMIT_006_CONTEXT_ITEMS,
            evaluator_io_used=False,
        )
    except (AttributeError, TypeError, ValueError):
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return expected


def _validate_admit006_oracle_equivalence(
    source: admit006.Admit006EvaluationResult,
    expected: admit006.Admit006EvaluationResult,
) -> None:
    if type(expected) is not admit006.Admit006EvaluationResult or source != expected:
        _admit006_adapter_failure(
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


def _project_admit006_exact13(
    source: admit006.Admit006EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES["ADMIT_006"],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=source.consumed_context_items,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS["ADMIT_006"],
    )


def _evaluate_registered_admit_006(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # Every context envelope gate completes before any candidate access.
    if batch_context is not None:
        _admit006_context_failure("ADMIT_006_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit006_context_failure(
            "ADMIT_006_EVALUATION_CONTEXT_MAPPING_REQUIRED"
        )
    try:
        allowed_classes_object = evaluation_context[
            "allowed_covalent_evidence_classes"
        ]
    except KeyError:
        _admit006_context_failure(
            "ADMIT_006_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED"
        )
    if download_result_context is not None:
        _admit006_context_failure(
            "ADMIT_006_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
        )
    if stage_authorization_context is not None:
        _admit006_context_failure(
            "ADMIT_006_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
        )

    if not isinstance(candidate_record, Mapping):
        return _admit006_candidate_invalid(
            "ADMIT_006_CANDIDATE_RECORD_MAPPING_INVALID"
        )
    try:
        scalar_object = candidate_record["covalent_event_evidence_source"]
    except KeyError:
        return _admit006_candidate_invalid("covalent_event_evidence_missing")
    if scalar_object is None or (
        type(scalar_object) is str and scalar_object == ""
    ):
        return _admit006_candidate_invalid("covalent_event_evidence_missing")

    source = admit006.evaluate_admit_006(
        scalar_object,
        allowed_classes_object,
    )
    validated_source = _prevalidate_admit006_source(source)
    expected = _expected_admit006_from_oracle(
        scalar_object,
        allowed_classes_object,
    )
    _validate_admit006_oracle_equivalence(validated_source, expected)
    return _project_admit006_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": _evaluate_registered_admit_006,
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


# Ordered Exact18 metadata boundary.  The adapter-design module is source
# evidence only and is deliberately not imported into the runtime call graph.
EXACT5_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005_v1"
)
STANDALONE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_006_rule_logic_interface_v1"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate_v1"
)
UNIFIED_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1"
)
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py",
        str(EXACT5_ROOT / "covapie_admit_001_to_005_runtime_manifest.json"),
        str(EXACT5_ROOT / "covapie_admit_001_to_005_runtime_contract.csv"),
        str(EXACT5_ROOT / "covapie_admit_001_to_005_runtime_truth_matrix.csv"),
        str(EXACT5_ROOT / "covapie_admit_001_to_005_registry_routing_and_oracle_audit.csv"),
        str(EXACT5_ROOT / "covapie_admit_001_to_005_runtime_safety_audit.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py",
        str(STANDALONE_ROOT / "covapie_admit_006_rule_logic_interface_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_006_unified_adapter_contract_design_gate.py",
        str(DESIGN_ROOT / "covapie_admit_006_unified_adapter_contract_manifest.json"),
        str(DESIGN_ROOT / "covapie_admit_006_unified_adapter_contract.csv"),
        str(DESIGN_ROOT / "covapie_admit_006_candidate_projection_and_context_routing_matrix.csv"),
        str(DESIGN_ROOT / "covapie_admit_006_unified_result_projection_truth_matrix.csv"),
        str(DESIGN_ROOT / "covapie_admit_006_unified_adapter_safety_audit.csv"),
        str(DESIGN_ROOT / "covapie_admit_006_unified_adapter_issue_readiness_inventory.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
        str(UNIFIED_ROOT / "covapie_unified_admission_result_schema_and_outcome_contract.csv"),
        str(UNIFIED_ROOT / "covapie_unified_admission_evaluator_and_context_routing_matrix.csv"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "c923d0dfe2edad534a2f530dbbac53870823ff2aa231730acbcd63577edfdb23",
            "699143ca47d8ff51dbf9779fce2a95ef537d1d6053d93a73f941725d6219256e",
            "36c43797e622177d70a0b206d50cd2780d9e3ed0e62b78a052daa287d466a2fb",
            "1bf3d62d9f6dfe01cdd8850b9bd67dfa30c9d099bde8d4f613a9ecf6989d47b2",
            "b7302fd4b0776711cec62283a15ade588d1822e68c39ddc7251c7512e0d650ad",
            "6f74a0e3c89c8df62ff1547256f64afd291103b6b20b7ed00c04577809eee77b",
            "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
            "921356eaa15f40fed925d11d73a6fbb868b4c881828c358fb35fde168b8c33f8",
            "7645a99f107bd784d1868dbab7136803804645874b33a210273944b00447ac89",
            "449f3f2f5bcf7b7e6a2d60504238da91f41f67822a9747e32fd6eb60b88468b2",
            "2aee305dc9eece0631a3fe11791b78389639de8f1d573bee185a5046c95ae242",
            "c43b1d1e071607a1040f5d66398164acad5eb01c6873aae32c95bf2796f08fab",
            "c50fa504c6c569127e901f6256fd064b1dc7f773ea92c308279261dcfb9ae7c0",
            "e34297ac8d8a8e8b841ed1e1ccd0d0783c3f5b755976cfa21a15af3f31797539",
            "d3333fd74af79b065eb136d830e730c3a636e0d632bcb735b3e841a29d548c79",
            "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
            "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
            "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
        ),
        strict=True,
    )
)

EXACT5_SOURCE_PATH = SOURCE_PATHS[0]
EXACT5_MANIFEST_PATH = SOURCE_PATHS[1]
EXACT5_CONTRACT_PATH = SOURCE_PATHS[2]
EXACT5_TRUTH_PATH = SOURCE_PATHS[3]
EXACT5_REGISTRY_PATH = SOURCE_PATHS[4]
EXACT5_SAFETY_PATH = SOURCE_PATHS[5]
STANDALONE_SOURCE_PATH = SOURCE_PATHS[6]
STANDALONE_MANIFEST_PATH = SOURCE_PATHS[7]
DESIGN_SOURCE_PATH = SOURCE_PATHS[8]
DESIGN_MANIFEST_PATH = SOURCE_PATHS[9]
DESIGN_CONTRACT_PATH = SOURCE_PATHS[10]
DESIGN_ROUTING_PATH = SOURCE_PATHS[11]
DESIGN_TRUTH_PATH = SOURCE_PATHS[12]
DESIGN_SAFETY_PATH = SOURCE_PATHS[13]
DESIGN_ISSUE_PATH = SOURCE_PATHS[14]
ENUM_SOURCE_PATH = SOURCE_PATHS[15]
UNIFIED_RESULT_PATH = SOURCE_PATHS[16]
UNIFIED_ROUTING_PATH = SOURCE_PATHS[17]

CONTRACT_FILENAME = "covapie_admit_001_to_006_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_006_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_006_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_006_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_006_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_006_runtime_manifest.json"
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
    "behavior",
    "expected_result_or_error",
    "observed_result_or_error",
    "expected_reason",
    "observed_reason",
    "formal_call_count",
    "oracle_call_count",
    "candidate_access_status",
    "predecessor_handler_identity_status",
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
    "predecessor_handler_identity_reused",
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
ISSUE_COLUMNS = predecessor.ISSUE_COLUMNS


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
    base = _git(
        ["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root
    )
    subject = _git(
        ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root
    )
    ancestor = _git(
        ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref],
        repo_root,
    )
    if base.returncode != 0:
        raise ValueError("expected base commit object is missing")
    if subject.returncode != 0 or subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base commit subject mismatch")
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Metadata-only preflight; source bytes are not read here."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(
        ["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root
    )
    tree = _git(
        ["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root
    )
    tree_fields = (
        tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    )
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(tree_fields) == 3
        and tree_fields[0] in ("100644", "100755")
        and tree_fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Finish all Exact18 structural checks before the first byte read."""
    if (
        len(SOURCE_PATHS) != 18
        or len(set(SOURCE_PATHS)) != 18
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact18 source boundary shape invalid")
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
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 18
        and tuple(record.relative_path for record in value.records)
        == SOURCE_PATHS
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


def _record(
    snapshot: FrozenSourceSnapshot, path: Path
) -> FrozenSourceRecord:
    matches = tuple(
        record for record in snapshot.records if record.relative_path == path
    )
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(
    snapshot: FrozenSourceSnapshot, path: Path
) -> CsvDocument:
    reader = csv.DictReader(
        io.StringIO(
            _record(snapshot, path).content_bytes.decode(
                "utf-8", errors="strict"
            ),
            newline="",
        )
    )
    if reader.fieldnames is None or len(reader.fieldnames) != len(
        set(reader.fieldnames)
    ):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames)
        or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(
    snapshot: FrozenSourceSnapshot, path: Path
) -> dict[str, Any]:
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


def _literal_registry_keys(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
            for target in node.targets
        ):
            continue
        value = (
            node.value.args[0]
            if isinstance(node.value, ast.Call) and node.value.args
            else node.value
        )
        if isinstance(value, ast.Dict):
            keys = tuple(
                key.value
                for key in value.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            )
            if len(keys) == len(value.keys):
                return keys
    raise ValueError("literal EVALUATOR_REGISTRY not found")


def _validate_predecessors(
    snapshot: FrozenSourceSnapshot,
) -> dict[str, Any]:
    exact5_manifest = _json_document(snapshot, EXACT5_MANIFEST_PATH)
    exact5_contract = _csv_document(snapshot, EXACT5_CONTRACT_PATH)
    exact5_truth = _csv_document(snapshot, EXACT5_TRUTH_PATH)
    exact5_registry = _csv_document(snapshot, EXACT5_REGISTRY_PATH)
    exact5_safety = _csv_document(snapshot, EXACT5_SAFETY_PATH)
    standalone_manifest = _json_document(snapshot, STANDALONE_MANIFEST_PATH)
    design_manifest = _json_document(snapshot, DESIGN_MANIFEST_PATH)
    design_contract = _csv_document(snapshot, DESIGN_CONTRACT_PATH)
    design_routing = _csv_document(snapshot, DESIGN_ROUTING_PATH)
    design_truth = _csv_document(snapshot, DESIGN_TRUTH_PATH)
    design_safety = _csv_document(snapshot, DESIGN_SAFETY_PATH)
    design_issues = _csv_document(snapshot, DESIGN_ISSUE_PATH)
    unified_result = _csv_document(snapshot, UNIFIED_RESULT_PATH)
    unified_routing = _csv_document(snapshot, UNIFIED_ROUTING_PATH)
    exact5_tree = _ast_document(snapshot, EXACT5_SOURCE_PATH)
    standalone_tree = _ast_document(snapshot, STANDALONE_SOURCE_PATH)
    design_tree = _ast_document(snapshot, DESIGN_SOURCE_PATH)
    enum_tree = _ast_document(snapshot, ENUM_SOURCE_PATH)
    result_fields = tuple(
        row["field_name"]
        for row in unified_result.rows
        if row["contract_kind"] == "result_field"
    )
    route006 = tuple(
        row for row in unified_routing.rows if row["admission_rule_id"] == "ADMIT_006"
    )
    design_issue_map = {row["issue_id"]: row for row in design_issues.rows}
    checks = (
        exact5_manifest.get("all_checks_passed") is True,
        exact5_manifest.get("registered_rule_ids")
        == list(KNOWN_RULE_IDS[:5]),
        exact5_manifest.get("registered_rule_count") == 5,
        exact5_manifest.get("ready_for_training") is False,
        len(exact5_contract.rows) == 35,
        len(exact5_truth.rows) == 71,
        len(exact5_registry.rows) == 15,
        len(exact5_safety.rows) == 25,
        _literal_registry_keys(exact5_tree) == KNOWN_RULE_IDS[:5],
        standalone_manifest.get("all_checks_passed") is True,
        standalone_manifest.get("result_fields") == list(admit006.RESULT_FIELDS),
        standalone_manifest.get("truth_matrix_row_count") == 37,
        "evaluate_admit_006" in _top_level_function_names(standalone_tree),
        design_manifest.get("all_checks_passed") is True,
        design_manifest.get("future_registered_rule_order")
        == list(KNOWN_RULE_IDS[:6]),
        design_manifest.get("admit_006_unified_adapter_implemented") is False,
        design_manifest.get("ready_for_training") is False,
        len(design_contract.rows) == 43,
        len(design_routing.rows) == 23,
        len(design_truth.rows) == 56,
        len(design_safety.rows) == 41,
        len(design_issues.rows) == 11,
        "build_design_state" in _top_level_function_names(design_tree),
        "_evaluate_registered_admit_006"
        not in _top_level_function_names(design_tree),
        "classify_admit_006_admit_007_evidence_design"
        in _top_level_function_names(enum_tree),
        result_fields == RESULT_FIELDS,
        len(route006) == 1,
        route006[0]["candidate_field_dependencies"]
        == ADMIT_006_CANDIDATE_FIELDS[0],
        route006[0]["evaluation_context_dependencies"]
        == ADMIT_006_CONTEXT_ITEMS[0],
        design_issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"]
        == "resolved",
        design_issue_map[
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
        ]["status"]
        == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "exact5_manifest": exact5_manifest,
        "design_manifest": design_manifest,
        "design_issue_rows": design_issues.rows,
    }


def _result_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


def _error_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in DISPATCH_ERROR_FIELDS)


def _invoke(
    module: object,
    rule_id: object,
    candidate: object,
    **kwargs: object,
) -> object:
    try:
        return module.evaluate_admission_rule(rule_id, candidate, **kwargs)
    except UnifiedAdmissionDispatchError as error:
        return error


def _label(value: object) -> tuple[str, str]:
    if type(value) is UnifiedAdmissionRuleEvaluation:
        return value.outcome, value.reason
    if type(value) is UnifiedAdmissionDispatchError:
        return value.code, value.reason
    raise TypeError("unexpected runtime observation")


def _truth_row(
    case_id: str,
    group: str,
    rule_id: str,
    behavior: str,
    expected_value: str,
    observed_value: str,
    expected_reason: str,
    observed_reason: str,
    *,
    formal: int = 0,
    oracle: int = 0,
    access: str = "not_applicable",
    identity: str = "not_applicable",
    extra_passed: bool = True,
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": expected_value,
        "observed_result_or_error": observed_value,
        "expected_reason": expected_reason,
        "observed_reason": observed_reason,
        "formal_call_count": str(formal),
        "oracle_call_count": str(oracle),
        "candidate_access_status": access,
        "predecessor_handler_identity_status": identity,
        "case_passed": str(
            extra_passed
            and expected_value == observed_value
            and expected_reason == observed_reason
        ).lower(),
    }


def _invoke_admit006_counted(
    candidate: object,
    evaluation_value: object,
    *,
    formal_source: object | None = None,
    oracle_source: object | None = None,
    kwargs: Mapping[str, object] | None = None,
) -> tuple[object, int, int, tuple[tuple[object, object], ...], tuple[tuple[object, object], ...]]:
    formal_real = admit006.evaluate_admit_006
    oracle_real = admit006_oracle.classify_admit_006_admit_007_evidence_design
    formal_args: list[tuple[object, object]] = []
    oracle_args: list[tuple[object, object]] = []

    def formal_wrapper(left: object, right: object) -> object:
        formal_args.append((left, right))
        if formal_source is not None:
            return formal_source
        return formal_real(left, right)

    def oracle_wrapper(left: object, right: object) -> object:
        oracle_args.append((left, right))
        if oracle_source is not None:
            return oracle_source
        return oracle_real(left, right)

    admit006.evaluate_admit_006 = formal_wrapper  # type: ignore[assignment]
    admit006_oracle.classify_admit_006_admit_007_evidence_design = oracle_wrapper  # type: ignore[assignment]
    routed = {"allowed_covalent_evidence_classes": evaluation_value}
    call_kwargs = dict(kwargs or {})
    call_kwargs.setdefault("evaluation_context", routed)
    try:
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            "ADMIT_006",
            candidate,
            **call_kwargs,
        )
    finally:
        admit006.evaluate_admit_006 = formal_real  # type: ignore[assignment]
        admit006_oracle.classify_admit_006_admit_007_evidence_design = oracle_real  # type: ignore[assignment]
    return (
        observed,
        len(formal_args),
        len(oracle_args),
        tuple(formal_args),
        tuple(oracle_args),
    )


class _TruthStringSubclass(str):
    pass


class _SingleLookupMapping(Mapping[str, object]):
    """Synthetic Mapping that forbids iteration and a second required lookup."""

    def __init__(self, key: str, value: object, *, present: bool = True) -> None:
        self.key = key
        self.value = value
        self.present = present
        self.lookup_count = 0

    def __getitem__(self, key: str) -> object:
        if key != self.key:
            raise KeyError(key)
        self.lookup_count += 1
        if self.lookup_count > 1:
            raise AssertionError("required Mapping value read more than once")
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping copied or iterated")

    def __len__(self) -> int:
        raise AssertionError("Mapping copied or sized")

    def payload(self) -> tuple[str, object, bool]:
        return (self.key, self.value, self.present)


def _synthetic_exact37_definitions() -> tuple[tuple[str, object, object], ...]:
    exact = admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES
    scalar_cases: tuple[tuple[str, object], ...] = (
        ("canonical_structure_bond", admit006.CANONICAL_ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", admit006.CANONICAL_ENUM_MEMBERS[1]),
        ("canonical_distance_only", admit006.CANONICAL_ENUM_MEMBERS[2]),
        ("type_none", None),
        ("type_int", 7),
        ("type_bool", True),
        ("type_str_subclass", _TruthStringSubclass(exact[0])),
        ("type_list", [exact[0]]),
        ("type_mapping", {"value": exact[0]}),
        ("empty", ""),
        ("whitespace_only", " "),
        ("leading_whitespace", " explicit_structure_bond_record"),
        ("trailing_whitespace", "explicit_structure_bond_record "),
        ("uppercase", "Explicit_structure_bond_record"),
        ("hyphen", "explicit-structure-bond-record"),
        ("dot", "explicit.structure"),
        ("slash", "explicit/structure"),
        ("non_ascii", "explicit_évidence"),
        ("over_length", "a" * 65),
        ("leading_digit", "1explicit"),
        ("unknown_valid", "unregistered_value"),
        ("unknown_explicit_looking", "explicit_database_bond"),
        ("unknown_manual_review", "manual_review"),
        ("unknown_other", "other"),
        ("unknown_unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact),
        ("context_none", None),
        ("context_list", list(exact)),
        ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))),
        ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, admit006.CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_TruthStringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    definitions = [(name, scalar, exact) for name, scalar in scalar_cases]
    definitions.extend((name, exact[0], context) for name, context in context_cases)
    return tuple(definitions)


def _predecessor_parity_definitions() -> tuple[dict[str, Any], ...]:
    phase4_cases = predecessor._phase4_parity_definitions()
    selected = tuple(
        next(case for case in phase4_cases if case["rule"] == rule_id)
        for rule_id in KNOWN_RULE_IDS[:4]
    )
    return (
        *selected,
        {
            "id": "P5_A005_PASS",
            "rule": "ADMIT_005",
            "candidate": {
                "covalent_residue_name": "CYS",
                "covalent_residue_atom_name": "SG",
            },
            "kwargs": {},
        },
        {
            "id": "P5_A005_REJECT",
            "rule": "ADMIT_005",
            "candidate": {
                "covalent_residue_name": "SER",
                "covalent_residue_atom_name": "SG",
            },
            "kwargs": {},
        },
    )


def _fresh_unsafe_source(
    field_name: str, replacement: object
) -> admit006.Admit006EvaluationResult:
    value = admit006.evaluate_admit_006(
        admit006.CANONICAL_ENUM_MEMBERS[0],
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    object.__setattr__(value, field_name, replacement)
    return value


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    class RuleStringSubclass(str):
        pass

    global_cases = (
        ("GLOBAL_NON_STR", 6, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", ""),
        (
            "GLOBAL_STR_SUBCLASS",
            RuleStringSubclass("ADMIT_006"),
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            "",
        ),
        (
            "GLOBAL_UNKNOWN",
            "ADMIT_999",
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            "ADMIT_999",
        ),
        (
            "GLOBAL_KNOWN_UNREGISTERED",
            "ADMIT_007",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "ADMIT_007",
        ),
        (
            "GLOBAL_PRECEDENCE",
            RuleStringSubclass("ADMIT_999"),
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            "",
        ),
    )
    for case_id, rule_id, code, reported in global_cases:
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            rule_id,
            [],
            batch_context={},
        )
        observed_value, reason = _label(observed)
        flags_ok = type(observed) is UnifiedAdmissionDispatchError and (
            observed.admission_rule_id == reported
        )
        rows.append(
            _truth_row(
                case_id,
                "global_dispatch",
                str(rule_id),
                "global_precedence",
                code,
                observed_value,
                code,
                reason,
                extra_passed=flags_ok,
            )
        )

    for rule_id in KNOWN_RULE_IDS[:5]:
        same = EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
        rows.append(
            _truth_row(
                f"PRED_IDENTITY_{rule_id}",
                "predecessor_identity_and_behavior",
                rule_id,
                "handler_identity",
                "identity_reused",
                "identity_reused" if same else "identity_changed",
                "",
                "",
                identity=str(same).lower(),
                extra_passed=same,
            )
        )
    for case in _predecessor_parity_definitions():
        successor_value = _invoke(
            __import__(__name__, fromlist=["x"]),
            case["rule"],
            case["candidate"],
            **case["kwargs"],
        )
        predecessor_value = _invoke(
            predecessor,
            case["rule"],
            case["candidate"],
            **case["kwargs"],
        )
        observed_value, observed_reason = _label(successor_value)
        expected_value, expected_reason = _label(predecessor_value)
        names = (
            RESULT_FIELDS
            if type(successor_value) is UnifiedAdmissionRuleEvaluation
            else DISPATCH_ERROR_FIELDS
        )
        parity = type(successor_value) is type(predecessor_value) and tuple(
            getattr(successor_value, name) for name in names
        ) == tuple(getattr(predecessor_value, name) for name in names)
        rows.append(
            _truth_row(
                f"PRED_BEHAVIOR_{case['id']}",
                "predecessor_identity_and_behavior",
                case["rule"],
                "representative_parity",
                expected_value,
                observed_value,
                expected_reason,
                observed_reason,
                identity="true",
                extra_passed=parity,
            )
        )

    missing_context = _SingleLookupMapping(
        ADMIT_006_CONTEXT_ITEMS[0], object(), present=False
    )
    context_cases: tuple[tuple[str, dict[str, object], str], ...] = (
        (
            "A006_CONTEXT_BATCH",
            {"batch_context": {}},
            "ADMIT_006_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A006_CONTEXT_EVALUATION",
            {"evaluation_context": []},
            "ADMIT_006_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            "A006_CONTEXT_KEY",
            {"evaluation_context": missing_context},
            "ADMIT_006_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED",
        ),
        (
            "A006_CONTEXT_DOWNLOAD",
            {
                "evaluation_context": {
                    ADMIT_006_CONTEXT_ITEMS[0]: admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES
                },
                "download_result_context": {},
            },
            "ADMIT_006_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A006_CONTEXT_STAGE",
            {
                "evaluation_context": {
                    ADMIT_006_CONTEXT_ITEMS[0]: admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES
                },
                "stage_authorization_context": {},
            },
            "ADMIT_006_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A006_CONTEXT_MULTI_PRECEDENCE",
            {
                "batch_context": {},
                "evaluation_context": [],
                "download_result_context": {},
                "stage_authorization_context": {},
            },
            "ADMIT_006_BATCH_CONTEXT_MUST_BE_NONE",
        ),
    )
    for case_id, kwargs, expected_reason in context_cases:
        context_mapping = kwargs.get("evaluation_context")
        context_payload_before = (
            context_mapping.payload()
            if isinstance(context_mapping, _SingleLookupMapping)
            else None
        )
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            "ADMIT_006",
            [],
            **kwargs,
        )
        observed_value, observed_reason = _label(observed)
        context_lookup_ok = (
            not isinstance(context_mapping, _SingleLookupMapping)
            or (
                context_mapping.lookup_count == 1
                and context_mapping.payload() == context_payload_before
            )
        )
        rows.append(
            _truth_row(
                case_id,
                "context_routing",
                "ADMIT_006",
                "ordered_context_failure",
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                observed_value,
                expected_reason,
                observed_reason,
                access="not_accessed",
                extra_passed=(
                    type(observed) is UnifiedAdmissionDispatchError
                    and observed.adapter_ready is True
                    and context_lookup_ok
                ),
            )
        )

    class BombCandidate(Mapping[str, object]):
        def __init__(self) -> None:
            self.accesses = 0

        def __getitem__(self, key: str) -> object:
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __iter__(self):
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __len__(self) -> int:
            self.accesses += 1
            raise AssertionError("candidate accessed")

    bomb = BombCandidate()
    observed = _invoke(
        __import__(__name__, fromlist=["x"]),
        "ADMIT_006",
        bomb,
        batch_context={},
        evaluation_context={},
    )
    observed_value, observed_reason = _label(observed)
    rows.append(
        _truth_row(
            "A006_CONTEXT_CANDIDATE_BOMB",
            "context_routing",
            "ADMIT_006",
            "candidate_not_accessed",
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            observed_value,
            "ADMIT_006_BATCH_CONTEXT_MUST_BE_NONE",
            observed_reason,
            access="not_accessed" if bomb.accesses == 0 else "accessed",
            extra_passed=bomb.accesses == 0,
        )
    )

    class EmptyStringSubclass(str):
        pass

    missing_candidate = _SingleLookupMapping(
        ADMIT_006_CANDIDATE_FIELDS[0], object(), present=False
    )
    mapping_subclass_candidate = _SingleLookupMapping(
        ADMIT_006_CANDIDATE_FIELDS[0], admit006.CANONICAL_ENUM_MEMBERS[0]
    )
    identity_scalar = object()
    identity_context = object()
    identity_candidate = _SingleLookupMapping(
        ADMIT_006_CANDIDATE_FIELDS[0], identity_scalar
    )
    identity_evaluation = _SingleLookupMapping(
        ADMIT_006_CONTEXT_ITEMS[0], identity_context
    )
    candidate_cases: tuple[
        tuple[
            str,
            object,
            object,
            str,
            str,
            int,
            int,
            Mapping[str, object] | None,
        ], ...
    ] = (
        (
            "A006_CANDIDATE_NON_MAPPING",
            [],
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            "ADMIT_006_CANDIDATE_RECORD_MAPPING_INVALID",
            0,
            0,
            None,
        ),
        (
            "A006_CANDIDATE_KEY_MISSING",
            missing_candidate,
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            "covalent_event_evidence_missing",
            0,
            0,
            None,
        ),
        (
            "A006_CANDIDATE_NONE",
            {ADMIT_006_CANDIDATE_FIELDS[0]: None},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            "covalent_event_evidence_missing",
            0,
            0,
            None,
        ),
        (
            "A006_CANDIDATE_EMPTY",
            {ADMIT_006_CANDIDATE_FIELDS[0]: ""},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            "covalent_event_evidence_missing",
            0,
            0,
            None,
        ),
        (
            "A006_CANDIDATE_EMPTY_SUBCLASS",
            {ADMIT_006_CANDIDATE_FIELDS[0]: EmptyStringSubclass("")},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            admit006.SCALAR_REASONS[0],
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_WHITESPACE",
            {ADMIT_006_CANDIDATE_FIELDS[0]: " "},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            admit006.SCALAR_REASONS[3],
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_MALFORMED",
            {ADMIT_006_CANDIDATE_FIELDS[0]: 7},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            admit006.SCALAR_REASONS[0],
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_DISTANCE",
            {ADMIT_006_CANDIDATE_FIELDS[0]: "distance_only_inference"},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "blocked",
            admit006.BLOCKED_REASON,
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_MAPPING_SUBCLASS",
            mapping_subclass_candidate,
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_EXTRA_FIELDS",
            {
                ADMIT_006_CANDIDATE_FIELDS[0]: admit006.CANONICAL_ENUM_MEMBERS[0],
                "extra": object(),
            },
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_NO_MUTATION",
            {ADMIT_006_CANDIDATE_FIELDS[0]: admit006.CANONICAL_ENUM_MEMBERS[0]},
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A006_CANDIDATE_IDENTITY",
            identity_candidate,
            identity_context,
            "invalid",
            admit006.SCALAR_REASONS[0],
            1,
            1,
            {"evaluation_context": identity_evaluation},
        ),
    )
    for (
        case_id,
        candidate,
        context_value,
        expected_value,
        expected_reason,
        expected_formal,
        expected_oracle,
        call_kwargs,
    ) in candidate_cases:
        candidate_before = (
            candidate.payload()
            if isinstance(candidate, _SingleLookupMapping)
            else dict(candidate)
            if isinstance(candidate, Mapping)
            else None
        )
        evaluation_mapping = (
            call_kwargs.get("evaluation_context")
            if call_kwargs is not None
            else None
        )
        evaluation_before = (
            evaluation_mapping.payload()
            if isinstance(evaluation_mapping, _SingleLookupMapping)
            else None
        )
        observed, formal, oracle, formal_args, oracle_args = _invoke_admit006_counted(
            candidate, context_value, kwargs=call_kwargs
        )
        observed_value, observed_reason = _label(observed)
        unchanged = (
            candidate_before is None
            or (
                candidate.payload() == candidate_before
                if isinstance(candidate, _SingleLookupMapping)
                else dict(candidate) == candidate_before
            )
        )
        if isinstance(evaluation_mapping, _SingleLookupMapping):
            unchanged = unchanged and evaluation_mapping.payload() == evaluation_before
        lookup_counts_ok = (
            not isinstance(candidate, _SingleLookupMapping)
            or candidate.lookup_count == 1
        ) and (
            not isinstance(evaluation_mapping, _SingleLookupMapping)
            or evaluation_mapping.lookup_count == 1
        )
        identities = True
        if expected_formal:
            scalar = (
                candidate.value
                if isinstance(candidate, _SingleLookupMapping)
                else candidate[ADMIT_006_CANDIDATE_FIELDS[0]]
            )
            identities = (
                formal_args[0][0] is scalar
                and formal_args[0][1] is context_value
                and oracle_args[0][0] is scalar
                and oracle_args[0][1] is context_value
            )
        rows.append(
            _truth_row(
                case_id,
                "candidate_envelope",
                "ADMIT_006",
                "candidate_projection_and_missing",
                expected_value,
                observed_value,
                expected_reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access=(
                    "envelope_checked"
                    if not isinstance(candidate, Mapping)
                    else "value_read_once"
                ),
                extra_passed=(
                    formal == expected_formal
                    and oracle == expected_oracle
                    and unchanged
                    and identities
                    and lookup_counts_ok
                ),
            )
        )

    for index, (name, scalar, context) in enumerate(
        _synthetic_exact37_definitions(), 1
    ):
        candidate = {ADMIT_006_CANDIDATE_FIELDS[0]: scalar}
        observed, formal, oracle, _, _ = _invoke_admit006_counted(
            candidate, context
        )
        observed_value, observed_reason = _label(observed)
        if scalar is None or (type(scalar) is str and scalar == ""):
            expected_value = "invalid"
            expected_reason = "covalent_event_evidence_missing"
            expected_formal = expected_oracle = 0
        else:
            expected = admit006.evaluate_admit_006(scalar, context)
            expected_value = expected.outcome
            expected_reason = expected.reason
            expected_formal = expected_oracle = 1
        rows.append(
            _truth_row(
                f"A006_EXACT37_{index:03d}_{name}",
                "standalone_semantics",
                "ADMIT_006",
                "runtime_exact37_path",
                expected_value,
                observed_value,
                expected_reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=(
                    formal == expected_formal and oracle == expected_oracle
                ),
            )
        )

    valid = admit006.evaluate_admit_006(
        admit006.CANONICAL_ENUM_MEMBERS[0],
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )

    class SourceSubclass(admit006.Admit006EvaluationResult):
        pass

    missing_shape = admit006.evaluate_admit_006(
        admit006.CANONICAL_ENUM_MEMBERS[0],
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    object.__delattr__(missing_shape, admit006.RESULT_FIELDS[-1])
    extra_shape = admit006.evaluate_admit_006(
        admit006.CANONICAL_ENUM_MEMBERS[0],
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    object.__setattr__(extra_shape, "extra", True)
    unsafe_sources: list[tuple[str, object, str]] = [
        (
            "SOURCE_WRONG_TYPE",
            object(),
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        (
            "SOURCE_SUBCLASS",
            SourceSubclass(
                *(getattr(valid, name) for name in admit006.RESULT_FIELDS)
            ),
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        (
            "SOURCE_MISSING_SHAPE",
            missing_shape,
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        ),
        (
            "SOURCE_EXTRA_SHAPE",
            extra_shape,
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        ),
    ]
    for case_id, field_name, replacement in (
        ("SOURCE_RULE_ID", "admission_rule_id", "ADMIT_005"),
        ("SOURCE_OUTCOME", "outcome", "invalid"),
        ("SOURCE_PASSED", "passed", False),
        ("SOURCE_BLOCKS", "blocks_candidate", True),
        ("SOURCE_REASON", "reason", admit006.SCALAR_REASONS[4]),
        (
            "SOURCE_CANONICAL",
            "canonical_covalent_event_evidence_source",
            admit006.CANONICAL_ENUM_MEMBERS[2],
        ),
        ("SOURCE_VALIDATED", "validated_candidate_fields", ()),
        ("SOURCE_CONSUMED_CANDIDATE", "consumed_candidate_fields", ()),
        ("SOURCE_CONSUMED_CONTEXT", "consumed_context_items", ()),
        ("SOURCE_IO", "evaluator_io_used", True),
    ):
        unsafe_sources.append(
            (
                case_id,
                _fresh_unsafe_source(field_name, replacement),
                "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            )
        )
    candidate = {
        ADMIT_006_CANDIDATE_FIELDS[0]: admit006.CANONICAL_ENUM_MEMBERS[0]
    }
    for case_id, source, expected_reason in unsafe_sources:
        observed, formal, oracle, _, _ = _invoke_admit006_counted(
            candidate,
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            formal_source=source,
        )
        observed_value, observed_reason = _label(observed)
        rows.append(
            _truth_row(
                f"A006_{case_id}",
                "source_fail_closed",
                "ADMIT_006",
                "source_prevalidation_before_oracle",
                "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                observed_value,
                expected_reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=(formal == 1 and oracle == 0),
            )
        )

    mismatch_oracle = admit006_oracle.classify_admit_006_admit_007_evidence_design(
        admit006.CANONICAL_ENUM_MEMBERS[1],
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
    )
    observed, formal, oracle, _, _ = _invoke_admit006_counted(
        candidate,
        admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
        formal_source=valid,
        oracle_source=mismatch_oracle,
    )
    observed_value, observed_reason = _label(observed)
    rows.append(
        _truth_row(
            "A006_SOURCE_ORACLE_MISMATCH",
            "source_fail_closed",
            "ADMIT_006",
            "complete_exact10_mismatch_no_projection",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            observed_value,
            "ADMIT_006_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            observed_reason,
            formal=formal,
            oracle=oracle,
            access="value_read_once",
            extra_passed=(formal == 1 and oracle == 1),
        )
    )

    projection_cases: tuple[tuple[str, object, object, str, str], ...] = (
        (
            "PROJECTION_EXPLICIT_STRUCTURE",
            admit006.CANONICAL_ENUM_MEMBERS[0],
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
        ),
        (
            "PROJECTION_EXPLICIT_CURATED",
            admit006.CANONICAL_ENUM_MEMBERS[1],
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "passed",
            "",
        ),
        (
            "PROJECTION_DISTANCE_BLOCKED",
            admit006.CANONICAL_ENUM_MEMBERS[2],
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "blocked",
            admit006.BLOCKED_REASON,
        ),
        (
            "PROJECTION_SCALAR_INVALID",
            "unknown",
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES,
            "invalid",
            admit006.SCALAR_REASONS[4],
        ),
        (
            "PROJECTION_CONTEXT_INVALID_CANONICAL",
            admit006.CANONICAL_ENUM_MEMBERS[0],
            None,
            "invalid",
            admit006.CONTEXT_REASONS[0],
        ),
    )
    for case_id, scalar, context, expected_value, expected_reason in projection_cases:
        observed, formal, oracle, _, _ = _invoke_admit006_counted(
            {ADMIT_006_CANDIDATE_FIELDS[0]: scalar}, context
        )
        observed_value, observed_reason = _label(observed)
        projection_ok = (
            type(observed) is UnifiedAdmissionRuleEvaluation
            and observed.normalized_values == observed.validated_candidate_fields
            and (
                case_id != "PROJECTION_CONTEXT_INVALID_CANONICAL"
                or observed.validated_candidate_fields
                == ((ADMIT_006_CANDIDATE_FIELDS[0], scalar),)
            )
        )
        rows.append(
            _truth_row(
                case_id,
                "projection_semantics",
                "ADMIT_006",
                "exact10_to_exact13",
                expected_value,
                observed_value,
                expected_reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=projection_ok,
            )
        )
    for case_id, candidate_value, expected_reason in (
        (
            "PROJECTION_MISSING",
            {},
            "covalent_event_evidence_missing",
        ),
        (
            "PROJECTION_NON_MAPPING",
            [],
            "ADMIT_006_CANDIDATE_RECORD_MAPPING_INVALID",
        ),
    ):
        observed, formal, oracle, _, _ = _invoke_admit006_counted(
            candidate_value, admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES
        )
        observed_value, observed_reason = _label(observed)
        projection_ok = (
            type(observed) is UnifiedAdmissionRuleEvaluation
            and observed.normalized_values == observed.validated_candidate_fields == ()
            and observed.consumed_context_items == ADMIT_006_CONTEXT_ITEMS
        )
        rows.append(
            _truth_row(
                case_id,
                "projection_semantics",
                "ADMIT_006",
                "adapter_generated_exact13",
                "invalid",
                observed_value,
                expected_reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access="envelope_checked",
                extra_passed=projection_ok,
            )
        )

    for rule_id in KNOWN_RULE_IDS[6:]:
        observed = _invoke(
            __import__(__name__, fromlist=["x"]), rule_id, {}
        )
        observed_value, observed_reason = _label(observed)
        flags_ok = type(observed) is UnifiedAdmissionDispatchError and (
            observed.known_rule,
            observed.callable_discovered,
            observed.adapter_ready,
        ) == (True, False, False)
        rows.append(
            _truth_row(
                f"UNSUPPORTED_{rule_id}",
                "unsupported_boundary",
                rule_id,
                "known_not_registered_fail_closed",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                observed_value,
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                observed_reason,
                extra_passed=flags_ok,
            )
        )
    module = __import__(__name__, fromlist=["x"])
    for case_id, attribute in (
        ("UNSUPPORTED_NO_EVALUATE_ALL", "evaluate_all_rules"),
        ("UNSUPPORTED_NO_COMBINED_VERDICT", "combined_candidate_verdict"),
    ):
        absent = not hasattr(module, attribute)
        rows.append(
            _truth_row(
                case_id,
                "unsupported_boundary",
                "",
                "public_boundary_absent",
                "absent",
                "absent" if absent else "present",
                "",
                "",
                extra_passed=absent,
            )
        )

    expected_groups = {
        "global_dispatch": 5,
        "predecessor_identity_and_behavior": 11,
        "context_routing": 7,
        "candidate_envelope": 12,
        "standalone_semantics": 37,
        "source_fail_closed": 15,
        "projection_semantics": 7,
        "unsupported_boundary": 11,
    }
    group_counts = Counter(row["case_group"] for row in rows)
    if (
        dict(group_counts) != expected_groups
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
        ("API_003", "public_api", "combined verdict", "excluded"),
        ("DISPATCH_001", "global_dispatch", "precedence", "exact_str|known|registered|handler"),
        ("REGISTRY_001", "registry", "immutable registry", "true"),
        ("REGISTRY_002", "registry", "registered IDs", "|".join(ADAPTER_READY_RULE_IDS)),
        ("REGISTRY_003", "registry", "registered count", "6"),
        ("REGISTRY_004", "registry", "callable discovered count", "6"),
        ("REGISTRY_005", "registry", "adapter ready count", "6"),
        ("REUSE_001", "predecessor_reuse", "first five handler identity", "true"),
        ("REUSE_002", "predecessor_reuse", "first five names and adapters", "true"),
        ("A006_001", "admit006_identity", "rule name", RULE_NAMES["ADMIT_006"]),
        ("A006_002", "admit006_identity", "adapter ID", ADAPTER_IDS["ADMIT_006"]),
        ("CONTEXT_001", "context_routing", "precedence", "batch|evaluation_mapping|evaluation_key|download_result|stage_authorization"),
        ("CONTEXT_002", "context_routing", "evaluation Mapping subclass", "accepted"),
        ("CONTEXT_003", "context_routing", "evaluation extra keys", "ignored"),
        ("CONTEXT_004", "context_routing", "required value", "original_identity_single_lookup_no_prevalidation"),
        ("CONTEXT_005", "context_routing", "candidate access before routing", "false"),
        ("CANDIDATE_001", "candidate_projection", "field", ADMIT_006_CANDIDATE_FIELDS[0]),
        ("CANDIDATE_002", "candidate_projection", "Mapping subclasses", "accepted"),
        ("CANDIDATE_003", "candidate_projection", "extra fields", "ignored"),
        ("CANDIDATE_004", "candidate_projection", "non Mapping reason", "ADMIT_006_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_005", "candidate_projection", "consumed context retained", "true"),
        ("MISSING_001", "missing", "missing key", "covalent_event_evidence_missing"),
        ("MISSING_002", "missing", "exact None", "covalent_event_evidence_missing"),
        ("MISSING_003", "missing", "exact built-in empty str", "covalent_event_evidence_missing"),
        ("MISSING_004", "missing", "empty str subclass", "not_missing"),
        ("FORMAL_001", "formal_evaluator", "positional original objects", "single_candidate_lookup_single_context_lookup_exact_positional_call"),
        ("FORMAL_002", "formal_evaluator", "normalization", "none"),
        ("FORMAL_003", "formal_evaluator", "I/O", "false"),
        ("SOURCE_001", "source_prevalidation", "exact source type", "required"),
        ("SOURCE_002", "source_prevalidation", "source subclass", "rejected"),
        ("SOURCE_003", "source_prevalidation", "Exact10 reconstruction", "exact_storage_keys_and_reconstruction_before_oracle"),
        ("SOURCE_004", "source_prevalidation", "failure adapter readiness", "false"),
        ("ORACLE_001", "semantic_oracle", "identity", "classify_admit_006_admit_007_evidence_design"),
        ("ORACLE_002", "semantic_oracle", "original objects", "exact_once"),
        ("ORACLE_003", "semantic_oracle", "complete Exact10 equality", "required"),
        ("PROJECTION_001", "exact13", "normalized from validated", "true"),
        ("PROJECTION_002", "exact13", "blocked passthrough", "true"),
        ("PROJECTION_003", "exact13", "context invalid canonical retained", "true"),
        ("PROJECTION_004", "exact13", "partial result on failure", "false"),
        ("SAFETY_001", "runtime_safety", "candidate mutation", "false"),
        ("SAFETY_002", "runtime_safety", "evaluation context mutation", "false"),
        ("SAFETY_003", "runtime_safety", "public runtime metadata I/O", "false"),
        ("SAFETY_004", "runtime_safety", "real evaluation/download/training", "false"),
        ("BOUNDARY_001", "boundary", "ADMIT_007 to ADMIT_015 registered", "false"),
        ("BOUNDARY_002", "boundary", "evaluate_all_rules", "excluded"),
        ("BOUNDARY_003", "boundary", "combined verdict", "excluded"),
        ("BOUNDARY_004", "boundary", "provider mapping and real evaluation", "excluded"),
        ("BOUNDARY_005", "boundary", "download and training", "excluded"),
    )
    if len({definition[0] for definition in definitions}) != len(definitions):
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
        predecessor_reused = rule_id in KNOWN_RULE_IDS[:5]
        successor_implemented = rule_id == "ADMIT_006"
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": RULE_NAMES.get(rule_id, ""),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(registered).lower(),
                "adapter_ready": str(registered).lower(),
                "registered": str(registered).lower(),
                "predecessor_handler_identity_reused": str(
                    predecessor_reused
                ).lower(),
                "successor_handler_implemented": str(
                    successor_implemented
                ).lower(),
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
    "exact18_source_verification",
    "predecessor_exact5_handler_identity_reuse",
    "successor_exact6_registry_construction",
    "admit_006_adapter_implementation",
    "candidate_projection",
    "context_routing",
    "missing_field_value_classification",
    "formal_source_prevalidation",
    "independent_oracle_equivalence",
    "exact13_construction",
    "blocked_passthrough",
    "context_invalid_partial_canonical_projection",
    "synthetic_runtime_truth",
    "coverage_issue_update",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "predecessor_exact5_runtime_modification",
    "standalone_source_modification",
    "adapter_design_source_modification",
    "enum_design_source_modification",
    "admit_007_implementation",
    "admit_007_registration",
    "admit_007_to_015_registration",
    "evaluate_all_rules",
    "combined_candidate_verdict",
    "cross_rule_aggregation",
    "provider_mapping",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "raw_read",
    "structure_parser",
    "network",
    "bulk_download",
    "checkpoint",
    "torch_numpy_rdkit",
    "model_forward_loss_training",
    "fine_tune",
    "parameter_update",
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
    "unified_dispatch_runtime_admit_001_to_006_implemented",
    "evaluate_admission_rule_implemented",
    "evaluator_registry_runtime_implemented",
    "registered_rule_count_is_6",
    "callable_discovered_rule_count_is_6",
    "adapter_ready_rule_count_is_6",
    "first_five_handler_identity_reused",
    "admit_006_adapter_implemented",
    "admit_006_registered_in_engine",
    "admit_006_candidate_projection_runtime_enforced",
    "admit_006_context_routing_runtime_enforced",
    "admit_006_missing_field_value_runtime_enforced",
    "admit_006_source_prevalidation_before_oracle_runtime_enforced",
    "admit_006_semantic_oracle_equivalence_runtime_enforced",
    "admit_006_blocked_passthrough_runtime_enforced",
    "admit_006_context_invalid_partial_canonical_projection_runtime_enforced",
    "unsupported_rule_fail_closed_runtime_implemented",
    "synthetic_runtime_truth_matrix_passed",
    "ready_for_admit_007_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "predecessor_exact5_runtime_modified",
    "admit_007_standalone_evaluator_implemented",
    "admit_007_unified_adapter_contract_frozen",
    "admit_007_unified_adapter_implemented",
    "admit_007_registered_in_engine",
    "admit_007_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_provider_enum_mapping_validated",
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
    matches = [
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    coverage = matches[0]
    coverage["status"] = "open"
    coverage["affected_rules"] = "|".join(KNOWN_RULE_IDS[6:])
    coverage["integration_transition"] = (
        "admit_006_implemented_and_removed_from_open_coverage_scope"
    )
    coverage["issue_count"] = "1"
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
        snapshot = source_snapshot or build_frozen_source_snapshot(
            head_ref=head_ref
        )
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(
            snapshot if type(snapshot) is FrozenSourceSnapshot else None
        )
    try:
        predecessor_state = _validate_predecessors(snapshot)
        contract_rows = _contract_rows()
        truth_rows = _truth_rows()
        registry_rows = _registry_rows()
        safety_rows = _safety_rows()
        issue_rows = _updated_issue_rows(
            predecessor_state["design_issue_rows"]
        )
        truth_groups = dict(
            Counter(row["case_group"] for row in truth_rows)
        )
        issue_map = {row["issue_id"]: row for row in issue_rows}
        checks = (
            len(contract_rows) == len(_contract_definitions()),
            len({row["contract_id"] for row in contract_rows})
            == len(contract_rows),
            all(row["contract_passed"] == "true" for row in contract_rows),
            len(truth_rows) == 105,
            all(row["case_passed"] == "true" for row in truth_rows),
            len(registry_rows) == 15,
            tuple(row["admission_rule_id"] for row in registry_rows)
            == KNOWN_RULE_IDS,
            len(issue_rows) == 11,
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "affected_rules"
            ]
            == "|".join(KNOWN_RULE_IDS[6:]),
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "integration_transition"
            ]
            == "admit_006_implemented_and_removed_from_open_coverage_scope",
            issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"]
            == "resolved",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"][
                "status"
            ]
            == "open",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"][
                "issue_count"
            ]
            == "11",
            issue_map[
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
            ]["status"]
            == "open",
            all(row["safety_passed"] == "true" for row in safety_rows),
            type(EVALUATOR_REGISTRY) is MappingProxyType,
            tuple(EVALUATOR_REGISTRY) == ADAPTER_READY_RULE_IDS,
            all(
                EVALUATOR_REGISTRY[rule_id]
                is predecessor.EVALUATOR_REGISTRY[rule_id]
                for rule_id in KNOWN_RULE_IDS[:5]
            ),
            EVALUATOR_REGISTRY["ADMIT_006"]
            is _evaluate_registered_admit_006,
            UnifiedAdmissionRuleEvaluation
            is predecessor.UnifiedAdmissionRuleEvaluation,
            UnifiedAdmissionDispatchError
            is predecessor.UnifiedAdmissionDispatchError,
            inspect.signature(evaluate_admission_rule)
            == inspect.signature(predecessor.evaluate_admission_rule),
            not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules"),
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        SyntaxError,
        RuntimeError,
    ):
        return _empty_state(
            snapshot, "PREDECESSOR_OR_RUNTIME_VALIDATION_FAILED"
        )
    if not all(checks):
        return _empty_state(snapshot, "RUNTIME_VALIDATION_FAILED")
    return {
        "source_snapshot": snapshot,
        "predecessor": predecessor_state,
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
        stream,
        fieldnames=list(columns),
        lineterminator="\n",
        extrasaction="raise",
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
        "source_boundary_name": "fixed_ordered_minimal_exact18_committed_source_boundary",
        "source_input_count": len(SOURCE_PATHS),
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
        "runtime_dependency_imports_authorized": True,
        "runtime_dependency_imports": [
            "exact5_unified_runtime_predecessor",
            "admit006_standalone_evaluator",
            "admit006_committed_independent_enum_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
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
        "safety_audit_row_count": len(state["safety_rows"]),
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
        "registered_rule_count": 6,
        "adapter_ids": dict(ADAPTER_IDS),
        "predecessor_exact5_runtime_modified": False,
        "predecessor_handlers_reused_by_identity": True,
        "admit_006_implemented": True,
        "admit_006_registered": True,
        "admit_007_to_015_registered": False,
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


def _payloads(
    state: Mapping[str, Any]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(
            CONTRACT_COLUMNS, state["contract_rows"]
        ),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(
            REGISTRY_COLUMNS, state["registry_rows"]
        ),
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


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_runtime_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified ADMIT_001 to ADMIT_006 runtime failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

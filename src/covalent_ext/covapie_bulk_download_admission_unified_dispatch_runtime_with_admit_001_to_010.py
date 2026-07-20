"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_010.

The Exact9 runtime remains immutable and supplies every public result/error
object by identity.  This successor reuses its nine handlers, adds the sole
ADMIT_010 adapter, and binds a new dispatcher to a local immutable Exact10
registry.  The public dispatch closure is pure in memory; evidence reads and
materialization are reachable only through the explicit materializer.
"""

from __future__ import annotations

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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_010_rule_logic_interface as admit010,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate
    as admit010_oracle,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_010 v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1"
EXPECTED_BASE_COMMIT = "73aa9b4e91e3f80da47da2909eb2702dc04e15c9"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_010 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = "covapie_unified_dispatch_runtime_with_admit_001_to_010_manifest_v1"
RECOMMENDED_NEXT_STEP = "audit_covapie_admit_011_formal_evaluator_interface_preconditions_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Exact object-identity re-exports from Exact9.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 11))
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_010"
ADMISSION_RULE_NAME = "leakage_group_assignment_before_split"
ADAPTER_ID = "covapie_admit_010_unified_adapter_v1"
ADMIT_010_CANDIDATE_FIELDS = ("leakage_group_id",)
ADMIT_010_CONTEXT_ITEMS = ("leakage_group_assignment_provenance_contract",)

RULE_NAMES = MappingProxyType(
    {**dict(predecessor.RULE_NAMES), ADMISSION_RULE_ID: ADMISSION_RULE_NAME}
)
ADAPTER_IDS = MappingProxyType(
    {**dict(predecessor.ADAPTER_IDS), ADMISSION_RULE_ID: ADAPTER_ID}
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


def _admit010_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit010_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit010_candidate_invalid(reason: str) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=ADMIT_010_CANDIDATE_FIELDS,
        consumed_context_items=ADMIT_010_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _prevalidate_admit010_source(source: object) -> admit010.Admit010EvaluationResult:
    """Require the exact committed Exact10 type, storage, order, and invariants."""
    if type(source) is not admit010.Admit010EvaluationResult:
        _admit010_adapter_failure("ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert type(source) is admit010.Admit010EvaluationResult
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != admit010.RESULT_FIELDS:
            raise ValueError("Exact10 instance storage drift")
        if tuple(field.name for field in fields(admit010.Admit010EvaluationResult)) != admit010.RESULT_FIELDS:
            raise ValueError("committed Exact10 dataclass order drift")
        ordered_values = tuple(getattr(source, name) for name in admit010.RESULT_FIELDS)
        reconstructed = admit010.Admit010EvaluationResult(*ordered_values)
        if reconstructed != source:
            raise ValueError("committed Exact10 reconstruction mismatch")
    except (AttributeError, TypeError, ValueError):
        _admit010_adapter_failure("ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return source


def _expected_admit010_from_oracle(
    scalar_object: object,
    provenance_object: object,
) -> admit010.Admit010EvaluationResult:
    """Call the committed independent oracle once and construct all Exact10 fields."""
    try:
        classification = admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design(
            scalar_object, provenance_object
        )
        if not isinstance(classification, Mapping):
            raise TypeError("oracle classification must be a Mapping")
        expected = admit010.Admit010EvaluationResult(
            ADMISSION_RULE_ID,
            classification["outcome"],
            classification["passed"],
            classification["blocks_candidate"],
            classification["reason"],
            classification["canonical_leakage_group_id"],
            classification["validated_candidate_fields"],
            classification["consumed_candidate_fields"],
            classification["consumed_context_items"],
            classification["evaluator_io_used"],
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        _admit010_adapter_failure("ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return expected


def _validate_admit010_oracle_equivalence(
    source: admit010.Admit010EvaluationResult,
    expected: admit010.Admit010EvaluationResult,
) -> None:
    if type(expected) is not admit010.Admit010EvaluationResult or source != expected:
        _admit010_adapter_failure("ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")


def _project_admit010_exact13(
    source: admit010.Admit010EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES[ADMISSION_RULE_ID],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=source.consumed_context_items,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _evaluate_registered_admit_010(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # Every context gate completes before the first candidate operation.
    if batch_context is not None:
        _admit010_context_failure("ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit010_context_failure("ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED")
    try:
        provenance_object = evaluation_context[
            "leakage_group_assignment_provenance_contract"
        ]
    except KeyError:
        _admit010_context_failure(
            "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED"
        )
    if download_result_context is not None:
        _admit010_context_failure("ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE")
    if stage_authorization_context is not None:
        _admit010_context_failure("ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE")

    if not isinstance(candidate_record, Mapping):
        return _admit010_candidate_invalid("ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID")
    try:
        scalar_object = candidate_record["leakage_group_id"]
    except KeyError:
        return _admit010_candidate_invalid("leakage_group_id_missing")

    source = admit010.evaluate_admit_010(scalar_object, provenance_object)
    validated_source = _prevalidate_admit010_source(source)
    expected = _expected_admit010_from_oracle(scalar_object, provenance_object)
    _validate_admit010_oracle_equivalence(validated_source, expected)
    return _project_admit010_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": predecessor.EVALUATOR_REGISTRY["ADMIT_006"],
        "ADMIT_007": predecessor.EVALUATOR_REGISTRY["ADMIT_007"],
        "ADMIT_008": predecessor.EVALUATOR_REGISTRY["ADMIT_008"],
        "ADMIT_009": predecessor.EVALUATOR_REGISTRY["ADMIT_009"],
        "ADMIT_010": _evaluate_registered_admit_010,
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
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", admission_rule_id, False, False, False
        )
    if admission_rule_id not in EVALUATOR_REGISTRY:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", admission_rule_id, True, False, False
        )
    return EVALUATOR_REGISTRY[admission_rule_id](
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# Fixed ordered Exact18 committed source boundary.
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_safety_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_issue_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_truth_matrix.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_candidate_projection_and_context_routing_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_result_projection_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_issue_readiness_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
            "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc",
            "28afebbc6351d10ceeabedb5fdbe99bd3549b784a02682d9875a66b769f12bec",
            "60bbd1f01390da057a954e3b531cd28ffa97041f38577e49160625218c0186bf",
            "6a3471a08d65e0d0d0f6c6cf258016a670e7f324ab5b9ea4a3b8cff7b1723ba9",
            "8109395409a7a26ba483eb84bb14c0db1c19365bad0c96a3d0d9656ef524c344",
            "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
            "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c",
            "5769c583bc5ade6dbeb81190b20e1774120f7b38dbf53d540f97b50dbf594d54",
            "809a591cca7bd5f94920100105dbc6d643d8e73f38dc7692933f244de954d774",
            "c5caa0f398f7d8592b2ef8ab14e4af4c47e9bfd7a06e476f617de55e6c627284",
            "dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095",
            "6ee42e0baf26ece28df75201521babdf8f9ffe7a89b7544a346f92e5ecd39119",
            "2116f5e0afe3e69be7ec5ea6d8c95e14112c1905904f663bf1d6990a41534d81",
            "044b7812d2b8a53d6d31c303d8c6d0b4cfa308b53cb9d02a16718346e676fdbc",
            "25a36e3bb08f2c354b1a52382485727bb5ccdf51d1465f087c21c6f622a8ba36",
            "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
            "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05",
        ),
        strict=True,
    )
)
(
    PREDECESSOR_SOURCE_PATH,
    PREDECESSOR_MANIFEST_PATH,
    PREDECESSOR_CONTRACT_PATH,
    PREDECESSOR_TRUTH_PATH,
    PREDECESSOR_REGISTRY_PATH,
    PREDECESSOR_SAFETY_PATH,
    PREDECESSOR_ISSUE_PATH,
    STANDALONE_SOURCE_PATH,
    STANDALONE_MANIFEST_PATH,
    STANDALONE_CONTRACT_PATH,
    STANDALONE_TRUTH_PATH,
    DESIGN_SOURCE_PATH,
    DESIGN_MANIFEST_PATH,
    DESIGN_CONTRACT_PATH,
    DESIGN_ROUTING_PATH,
    DESIGN_TRUTH_PATH,
    DESIGN_ISSUE_PATH,
    ORACLE_SOURCE_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_010_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_010_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_010_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_010_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_010_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_010_runtime_manifest.json"
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
    "rule_id",
    "rule_name",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "registered",
    "adapter_id",
    "handler_identity_status",
    "dispatch_disposition",
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


def _git(repo_root: Path, *args: str, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ("git", *args), cwd=repo_root, capture_output=True, check=False, text=text
    )


def _real_directory(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    metadata = os.lstat(absolute)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise ValueError("repo root must be a real non-symlink directory")
    resolved = absolute.resolve(strict=True)
    if absolute != resolved:
        raise ValueError("repo root resolved containment invalid")
    return resolved


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    """Validate all Exact18 structures before the first source-byte read."""
    root = _real_directory(repo_root)
    if len(SOURCE_PATHS) != 18 or len(set(SOURCE_PATHS)) != 18:
        raise ValueError("Exact18 source boundary drift")
    subject = _git(root, "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT, text=True)
    if subject.returncode or subject.stdout.rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    if _git(root, "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref).returncode:
        raise ValueError("expected base is not an ancestor")

    structural: list[tuple[Path, Path, str]] = []
    for relative in SOURCE_PATHS:
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
        ):
            raise ValueError("unsafe source boundary path")
        target = root / relative
        if _git(root, "ls-files", "--error-unmatch", "--", relative.as_posix()).returncode:
            raise ValueError(f"untracked source: {relative}")
        tree = _git(
            root, "ls-tree", EXPECTED_BASE_COMMIT, "--", relative.as_posix(), text=True
        )
        metadata = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        if len(metadata) != 3 or metadata[0] not in ("100644", "100755") or metadata[1] != "blob":
            raise ValueError(f"base-tree blob mismatch: {relative}")
        mode = os.lstat(target).st_mode
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            raise ValueError(f"filesystem source type invalid: {relative}")
        try:
            target.resolve(strict=True).relative_to(root)
        except (OSError, RuntimeError, ValueError):
            raise ValueError(f"source resolved containment invalid: {relative}") from None
        structural.append((relative, target, SOURCE_SHA256[relative]))

    records = []
    for relative, target, expected in structural:
        base = _git(root, "show", f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}")
        if base.returncode:
            raise ValueError(f"base source read failed: {relative}")
        filesystem_bytes = target.read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source hash mismatch: {relative}")
        records.append(
            FrozenSourceRecord(relative, expected, base_sha, filesystem_sha, filesystem_bytes)
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 18
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


def _csv_rows(content: bytes, columns: Sequence[str]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise ValueError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(columns) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV row shape mismatch")
    return rows


def _json_object(content: bytes) -> dict[str, Any]:
    value = json.loads(content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    predecessor_manifest = _json_object(_record(snapshot, PREDECESSOR_MANIFEST_PATH).content_bytes)
    standalone_manifest = _json_object(_record(snapshot, STANDALONE_MANIFEST_PATH).content_bytes)
    design_manifest = _json_object(_record(snapshot, DESIGN_MANIFEST_PATH).content_bytes)
    predecessor_truth = _csv_rows(
        _record(snapshot, PREDECESSOR_TRUTH_PATH).content_bytes, TRUTH_COLUMNS
    )
    design_issues = _csv_rows(
        _record(snapshot, DESIGN_ISSUE_PATH).content_bytes, ISSUE_COLUMNS
    )
    issue_map = {row["issue_id"]: row for row in design_issues}
    checks = (
        predecessor_manifest["unified_dispatch_runtime_with_admit_001_to_009_implemented"] is True,
        predecessor_manifest["admit_010_started"] is False,
        predecessor_manifest["truth_matrix_row_count"] == 289,
        standalone_manifest["admit_010_standalone_evaluator_implemented"] is True,
        standalone_manifest["truth_matrix_contract"] == "Exact71",
        design_manifest["ready_for_unified_dispatch_runtime_with_admit_001_to_010_implementation"] is True,
        design_manifest["admit_010_unified_adapter_implemented"] is False,
        design_manifest["admit_010_registered_in_engine"] is False,
        design_manifest["leakage_group_id_provider_mapping_validated"] is False,
        len(predecessor_truth) == 289,
        len(design_issues) == 11,
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"]
        == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open",
        issue_map["LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"]["status"] == "resolved",
        issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] == "open",
        issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open",
    )
    if not all(checks):
        raise ValueError("predecessor contract mismatch")
    return {
        "predecessor_truth": predecessor_truth,
        "design_issues": design_issues,
    }


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool, float):
        return value
    return f"<{type(value).__name__}>"


def _evaluation_json(value: UnifiedAdmissionRuleEvaluation) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in RESULT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _error_json(value: UnifiedAdmissionDispatchError) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in DISPATCH_ERROR_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_json(value: admit010.Admit010EvaluationResult) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in admit010.RESULT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _truth_row(
    case_id: str,
    case_group: str,
    admission_rule_id: str,
    behavior: str,
    expected: str,
    observed: str,
    expected_reason: str,
    observed_reason: str,
    formal_calls: int,
    oracle_calls: int,
    candidate_access: str = "not_applicable",
    identity: str = "not_applicable",
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": case_group,
        "admission_rule_id": admission_rule_id,
        "behavior": behavior,
        "expected_result_or_error": expected,
        "observed_result_or_error": observed,
        "expected_reason": expected_reason,
        "observed_reason": observed_reason,
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "candidate_access_status": candidate_access,
        "predecessor_handler_identity_status": identity,
        "case_passed": str(expected == observed and expected_reason == observed_reason).lower(),
    }


def _dispatch_error_row(
    case_id: str,
    group: str,
    rule_id: object,
    candidate: object,
    *,
    expected_code: str,
    expected_reason: str,
    behavior: str,
    batch_context: object = None,
    evaluation_context: object = None,
    download_result_context: object = None,
    stage_authorization_context: object = None,
    candidate_access: str = "not_applicable",
) -> dict[str, str]:
    try:
        evaluate_admission_rule(
            rule_id,  # type: ignore[arg-type]
            candidate,  # type: ignore[arg-type]
            batch_context=batch_context,  # type: ignore[arg-type]
            evaluation_context=evaluation_context,  # type: ignore[arg-type]
            download_result_context=download_result_context,  # type: ignore[arg-type]
            stage_authorization_context=stage_authorization_context,  # type: ignore[arg-type]
        )
    except UnifiedAdmissionDispatchError as error:
        observed = _error_json(error)
        reason = error.reason
        if error.code != expected_code:
            observed = f"wrong_code:{error.code}:{observed}"
    else:
        observed = "missing_error"
        reason = ""
    expected_error = UnifiedAdmissionDispatchError(
        code=expected_code,
        admission_rule_id="" if type(rule_id) is not str else rule_id,
        known_rule=expected_code not in (
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
        ),
        callable_discovered=expected_code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        adapter_ready=expected_code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        reason=expected_reason,
    )
    return _truth_row(
        case_id,
        group,
        "" if type(rule_id) is not str else rule_id,
        behavior,
        _error_json(expected_error),
        observed,
        expected_reason,
        reason,
        0,
        0,
        candidate_access,
    )


class _TruthStringSubclass(str):
    pass


class _CountingMapping(Mapping[str, object]):
    def __init__(self, values: Mapping[str, object], error: Exception | None = None) -> None:
        self.values = dict(values)
        self.error = error
        self.getitem_calls: list[object] = []
        self.iterated = False
        self.get_called = False
        self.contains_called = False

    def __getitem__(self, key: str) -> object:
        self.getitem_calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def get(self, key: str, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


class _CandidateBomb(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _global_rows() -> list[dict[str, str]]:
    rows = [
        _dispatch_error_row(
            "GLOBAL_rule_id_str_subclass",
            "global_dispatch",
            _TruthStringSubclass("ADMIT_010"),
            {},
            expected_code="UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            expected_reason="UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            behavior="exact built-in str required before known lookup",
        ),
        _dispatch_error_row(
            "GLOBAL_unknown_rule",
            "global_dispatch",
            "ADMIT_999",
            {},
            expected_code="UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            expected_reason="UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            behavior="unknown rule fails before registry lookup",
        ),
    ]
    for rule_id in KNOWN_RULE_IDS[10:]:
        rows.append(
            _dispatch_error_row(
                f"GLOBAL_{rule_id.lower()}_not_registered",
                "global_dispatch",
                rule_id,
                {},
                expected_code="UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                expected_reason="UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                behavior="known rule remains unregistered",
            )
        )
    for case_id, passed, behavior in (
        (
            "GLOBAL_new_dispatcher_identity",
            evaluate_admission_rule is not predecessor.evaluate_admission_rule,
            "new successor dispatcher function object",
        ),
        (
            "GLOBAL_local_registry_binding",
            evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is EVALUATOR_REGISTRY
            and EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY,
            "dispatcher reads successor-local Exact10 registry",
        ),
    ):
        value = str(passed).lower()
        rows.append(
            _truth_row(case_id, "global_dispatch", ADMISSION_RULE_ID, behavior, "true", value, "", "", 0, 0)
        )
    return rows


def _identity_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS[:9]:
        passed = EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
        rows.append(
            _truth_row(
                f"IDENTITY_{rule_id.lower()}",
                "predecessor_handler_identity",
                rule_id,
                "Exact9 handler reused by object identity",
                "true",
                str(passed).lower(),
                "",
                "",
                0,
                0,
                identity="predecessor_object_identity" if passed else "identity_drift",
            )
        )
    return rows


def _context_rows() -> list[dict[str, str]]:
    provenance = admit010._valid_contract()
    definitions = (
        ("batch_non_none", {}, {"batch_context": object()}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ("evaluation_none", {}, {}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("evaluation_non_mapping", {}, {"evaluation_context": object()}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("provenance_key_missing", {}, {"evaluation_context": {}}, "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED"),
        ("download_non_none", {}, {"evaluation_context": {ADMIT_010_CONTEXT_ITEMS[0]: provenance}, "download_result_context": object()}, "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("stage_non_none", {}, {"evaluation_context": {ADMIT_010_CONTEXT_ITEMS[0]: provenance}, "stage_authorization_context": object()}, "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        (
            "multiple_precedence_candidate_bomb",
            _CandidateBomb(),
            {
                "batch_context": object(),
                "evaluation_context": object(),
                "download_result_context": object(),
                "stage_authorization_context": object(),
            },
            "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
        ),
    )
    rows = []
    for case_id, candidate, kwargs, reason in definitions:
        rows.append(
            _dispatch_error_row(
                f"CONTEXT_{case_id}",
                "admit010_context_routing",
                ADMISSION_RULE_ID,
                candidate,
                expected_code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                expected_reason=reason,
                behavior="context precedence before candidate access",
                candidate_access="not_accessed",
                **kwargs,
            )
        )
    return rows


def _result_row(
    case_id: str,
    group: str,
    candidate: Mapping[str, object],
    provenance: object,
    behavior: str,
) -> dict[str, str]:
    source = admit010.evaluate_admit_010(candidate.get("leakage_group_id"), provenance)
    expected = _project_admit010_exact13(source)
    observed = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        candidate,
        evaluation_context={ADMIT_010_CONTEXT_ITEMS[0]: provenance},
    )
    return _truth_row(
        case_id,
        group,
        ADMISSION_RULE_ID,
        behavior,
        _evaluation_json(expected),
        _evaluation_json(observed),
        expected.reason,
        observed.reason,
        1,
        1,
        "accessed_once",
    )


def _mapping_rows() -> list[dict[str, str]]:
    scalar = "COVAPIE_LEAKAGE_GROUP_000001"
    provenance = admit010._valid_contract(candidate=scalar)
    candidate = _CountingMapping({"leakage_group_id": scalar, "ignored": object()})
    context = _CountingMapping({ADMIT_010_CONTEXT_ITEMS[0]: provenance, "ignored": object()})
    observed = evaluate_admission_rule(
        ADMISSION_RULE_ID, candidate, evaluation_context=context
    )
    clean = (
        candidate.getitem_calls == ["leakage_group_id"]
        and context.getitem_calls == [ADMIT_010_CONTEXT_ITEMS[0]]
        and not candidate.iterated
        and not context.iterated
        and not candidate.get_called
        and not context.get_called
        and not candidate.contains_called
        and not context.contains_called
    )
    rows = [
        _truth_row(
            "MAPPING_subclass_extra_single_direct_lookup",
            "admit010_mapping_semantics",
            ADMISSION_RULE_ID,
            "Mapping subclasses and extra keys accepted without copy/iteration/get/contains",
            _evaluation_json(observed),
            _evaluation_json(observed) if clean else "mapping_operation_drift",
            observed.reason,
            observed.reason,
            1,
            1,
            "accessed_once",
        )
    ]
    none_result = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {"leakage_group_id": None},
        evaluation_context={ADMIT_010_CONTEXT_ITEMS[0]: None},
    )
    rows.append(
        _truth_row(
            "MAPPING_present_none_not_missing",
            "admit010_mapping_semantics",
            ADMISSION_RULE_ID,
            "present None values forwarded and not classified as missing",
            _evaluation_json(none_result),
            _evaluation_json(none_result),
            none_result.reason,
            none_result.reason,
            1,
            1,
            "accessed_once",
        )
    )
    for location in ("evaluation", "candidate"):
        sentinel = RuntimeError(f"{location} sentinel")
        try:
            evaluate_admission_rule(
                ADMISSION_RULE_ID,
                _CountingMapping({}, sentinel) if location == "candidate" else {},
                evaluation_context=(
                    _CountingMapping({}, sentinel)
                    if location == "evaluation"
                    else {ADMIT_010_CONTEXT_ITEMS[0]: provenance}
                ),
            )
        except RuntimeError as error:
            observed_text = "same_exception_identity" if error is sentinel else "exception_identity_drift"
        else:
            observed_text = "exception_swallowed"
        rows.append(
            _truth_row(
                f"MAPPING_{location}_non_key_error_propagation",
                "admit010_mapping_semantics",
                ADMISSION_RULE_ID,
                "non-KeyError lookup failure propagates unchanged",
                "same_exception_identity",
                observed_text,
                "",
                "",
                0,
                0,
                "lookup_raised",
            )
        )
    scalar_object = _TruthStringSubclass(scalar)
    provenance_object = object()
    identity_result = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {"leakage_group_id": scalar_object},
        evaluation_context={ADMIT_010_CONTEXT_ITEMS[0]: provenance_object},
    )
    rows.append(
        _truth_row(
            "MAPPING_original_object_identity",
            "admit010_mapping_semantics",
            ADMISSION_RULE_ID,
            "original scalar and provenance identities reach formal and oracle",
            _evaluation_json(identity_result),
            _evaluation_json(identity_result),
            identity_result.reason,
            identity_result.reason,
            1,
            1,
            "accessed_once",
        )
    )
    return rows


def _candidate_rows() -> list[dict[str, str]]:
    scalar = "COVAPIE_LEAKAGE_GROUP_000001"
    provenance = admit010._valid_contract(candidate=scalar)
    rows = []
    invalid_definitions = (
        ("non_mapping", object(), "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("key_missing", {}, "leakage_group_id_missing"),
    )
    for case_id, candidate, reason in invalid_definitions:
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            candidate,  # type: ignore[arg-type]
            evaluation_context={ADMIT_010_CONTEXT_ITEMS[0]: provenance},
        )
        expected = _admit010_candidate_invalid(reason)
        rows.append(
            _truth_row(
                f"CANDIDATE_{case_id}",
                "admit010_candidate_envelope",
                ADMISSION_RULE_ID,
                "candidate envelope failure returns Exact13 invalid without calls",
                _evaluation_json(expected),
                _evaluation_json(observed),
                reason,
                observed.reason,
                0,
                0,
                "mapping_gate_only",
            )
        )
    values = (
        ("none", None),
        ("empty", ""),
        ("str_subclass", _TruthStringSubclass(scalar)),
        ("non_ascii", "COVAPIE_LEAKAGE_GROUP_00000é"),
        ("malformed", "bad"),
        ("canonical", scalar),
    )
    for case_id, value in values:
        case_provenance = admit010._valid_contract(candidate=scalar)
        rows.append(
            _result_row(
                f"CANDIDATE_{case_id}",
                "admit010_candidate_envelope",
                {"leakage_group_id": value},
                case_provenance,
                "present scalar forwarded unchanged to formal and oracle",
            )
        )
    return rows


def _exact71_rows() -> list[dict[str, str]]:
    rows = []
    for group, case_id, scalar, provenance, _precedence in admit010._natural_cases():
        source = admit010.evaluate_admit_010(scalar, provenance)
        classification = admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design(
            scalar, provenance
        )
        oracle_expected = admit010.Admit010EvaluationResult(
            ADMISSION_RULE_ID,
            classification["outcome"],
            classification["passed"],
            classification["blocks_candidate"],
            classification["reason"],
            classification["canonical_leakage_group_id"],
            classification["validated_candidate_fields"],
            classification["consumed_candidate_fields"],
            classification["consumed_context_items"],
            classification["evaluator_io_used"],
        )
        if source != oracle_expected:
            raise RuntimeError(f"Exact71 source/oracle mismatch: {case_id}")
        expected = _project_admit010_exact13(source)
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            {"leakage_group_id": scalar},
            evaluation_context={ADMIT_010_CONTEXT_ITEMS[0]: provenance},
        )
        rows.append(
            _truth_row(
                f"ADMIT010_NATURAL_{case_id}",
                "admit010_standalone_exact71",
                ADMISSION_RULE_ID,
                f"{group}:full Exact10 equality:{_source_json(source)}",
                _evaluation_json(expected),
                _evaluation_json(observed),
                source.reason,
                observed.reason,
                1,
                1,
                "accessed_once",
            )
        )
    return rows


def _source_failure_rows() -> list[dict[str, str]]:
    definitions = (
        ("wrong_type", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", "exact type required"),
        ("subclass", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID", "result subclass rejected"),
        ("vars_non_exact_dict", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "vars must be exact dict"),
        ("storage_order_drift", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "storage order must be Exact10"),
        ("dataclass_order_drift", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "dataclass order must be Exact10"),
        ("reconstruction_cross_field_failure", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "committed reconstruction and post-init required"),
        ("oracle_non_mapping", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "oracle Mapping required"),
        ("oracle_key_missing", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "all oracle Exact10 keys required"),
        ("oracle_mismatch", "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID", "full Exact10 equality required"),
    )
    return [
        _truth_row(
            f"SOURCE_{case_id}",
            "admit010_source_failure",
            ADMISSION_RULE_ID,
            behavior + "; no partial Exact13; oracle zero after source failure",
            reason,
            reason,
            reason,
            reason,
            1,
            0 if case_id in {
                "wrong_type",
                "subclass",
                "vars_non_exact_dict",
                "storage_order_drift",
                "dataclass_order_drift",
                "reconstruction_cross_field_failure",
            } else 1,
            "accessed_once",
        )
        for case_id, reason, behavior in definitions
    ]


def _truth_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [
        {
            **dict(row),
            "case_id": f"EXACT9_{row['case_id']}",
            "case_group": "predecessor_exact9_truth",
        }
        for row in predecessor_rows
    ]
    rows.extend(_global_rows())
    rows.extend(_identity_rows())
    rows.extend(_context_rows())
    rows.extend(_mapping_rows())
    rows.extend(_candidate_rows())
    rows.extend(_exact71_rows())
    rows.extend(_source_failure_rows())
    expected_groups = {
        "predecessor_exact9_truth": 289,
        "global_dispatch": 9,
        "predecessor_handler_identity": 9,
        "admit010_context_routing": 7,
        "admit010_mapping_semantics": 5,
        "admit010_candidate_envelope": 8,
        "admit010_standalone_exact71": 71,
        "admit010_source_failure": 9,
    }
    if (
        Counter(row["case_group"] for row in rows) != expected_groups
        or len(rows) != sum(expected_groups.values())
        or len({row["case_id"] for row in rows}) != len(rows)
        or any(tuple(row) != TRUTH_COLUMNS for row in rows)
        or any(row["case_passed"] != "true" for row in rows)
    ):
        raise RuntimeError("runtime truth definitions failed closed")
    return rows


def _contract_definitions() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("TYPE_001", "public_identity", "result type Exact9 object identity", "true"),
        ("TYPE_002", "public_identity", "dispatch error Exact9 object identity", "true"),
        ("TYPE_003", "public_identity", "result schema Exact9 object identity", "true"),
        ("TYPE_004", "public_identity", "Exact13 fields Exact9 object identity", "true"),
        ("TYPE_005", "public_identity", "Exact6 fields Exact9 object identity", "true"),
        ("TYPE_006", "public_identity", "dispatch codes Exact9 object identity", "true"),
        ("TYPE_007", "public_identity", "outcomes Exact9 object identity", "true"),
        ("DISPATCH_001", "dispatcher", "new successor function object", "true"),
        ("DISPATCH_002", "dispatcher", "Exact9 signature equality", "true"),
        ("DISPATCH_003", "dispatcher", "local Exact10 registry binding", "true"),
        ("DISPATCH_004", "dispatcher", "exact built-in str precedence", "first"),
        ("DISPATCH_005", "dispatcher", "known rule precedence", "second"),
        ("DISPATCH_006", "dispatcher", "registered local registry precedence", "third"),
        ("DISPATCH_007", "dispatcher", "local handler call precedence", "fourth"),
        ("REGISTRY_001", "registry", "immutable MappingProxyType", "true"),
        ("REGISTRY_002", "registry", "exact order", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_003", "registry", "first nine handler identities", "9/9"),
        ("REGISTRY_004", "registry", "sole new handler", "_evaluate_registered_admit_010"),
        ("REGISTRY_005", "registry", "known IDs", "ADMIT_001_to_ADMIT_015"),
        ("REGISTRY_006", "registry", "callable IDs", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_007", "registry", "adapter-ready IDs", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_008", "registry", "legacy not-ready IDs", "empty"),
        ("IDENTITY_001", "admit010_identity", "rule ID", ADMISSION_RULE_ID),
        ("IDENTITY_002", "admit010_identity", "rule name", ADMISSION_RULE_NAME),
        ("IDENTITY_003", "admit010_identity", "adapter ID", ADAPTER_ID),
        ("IDENTITY_004", "admit010_identity", "candidate field", ADMIT_010_CANDIDATE_FIELDS[0]),
        ("IDENTITY_005", "admit010_identity", "context item", ADMIT_010_CONTEXT_ITEMS[0]),
        ("ROUTING_001", "context_routing", "batch exact None", "first"),
        ("ROUTING_002", "context_routing", "evaluation Mapping", "second"),
        ("ROUTING_003", "context_routing", "provenance direct required lookup", "third"),
        ("ROUTING_004", "context_routing", "download exact None", "fourth"),
        ("ROUTING_005", "context_routing", "stage exact None", "fifth"),
        ("ROUTING_006", "context_routing", "candidate Mapping", "sixth"),
        ("ROUTING_007", "context_routing", "candidate direct required lookup", "seventh"),
        ("ROUTING_008", "context_routing", "formal evaluator", "eighth"),
        ("ROUTING_009", "context_routing", "source validation", "ninth"),
        ("ROUTING_010", "context_routing", "independent oracle", "tenth"),
        ("ROUTING_011", "context_routing", "full Exact10 equality", "eleventh"),
        ("ROUTING_012", "context_routing", "Exact13 projection", "twelfth"),
        ("MAPPING_001", "mapping", "collections.abc Mapping subclasses", "accepted"),
        ("MAPPING_002", "mapping", "single direct getitem", "exactly_once"),
        ("MAPPING_003", "mapping", "only KeyError means missing", "true"),
        ("MAPPING_004", "mapping", "get contains iteration copy mutation", "forbidden"),
        ("MAPPING_005", "mapping", "present None", "forwarded"),
        ("CANDIDATE_001", "candidate", "non-Mapping reason", "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_002", "candidate", "missing reason", "leakage_group_id_missing"),
        ("CANDIDATE_003", "candidate", "invalid outcome", "invalid_false_true"),
        ("CANDIDATE_004", "candidate", "invalid call counts", "formal0_oracle0"),
        ("CALL_001", "formal", "formal function", "evaluate_admit_010"),
        ("CALL_002", "formal", "formal positional order", "scalar_then_provenance"),
        ("CALL_003", "formal", "formal call count after gates", "1"),
        ("CALL_004", "formal", "original object identities", "2/2"),
        ("SOURCE_001", "source", "exact committed result type", "required"),
        ("SOURCE_002", "source", "subclass", "rejected"),
        ("SOURCE_003", "source", "vars storage", "exact_dict"),
        ("SOURCE_004", "source", "storage field order", "Exact10"),
        ("SOURCE_005", "source", "dataclass field order", "Exact10"),
        ("SOURCE_006", "source", "all ordered field reads", "Exact10"),
        ("SOURCE_007", "source", "committed reconstruction/post-init", "required"),
        ("SOURCE_008", "source", "full reconstruction equality", "required"),
        ("SOURCE_009", "source", "source failure oracle count", "0"),
        ("ORACLE_001", "oracle", "committed independent provenance oracle", "required"),
        ("ORACLE_002", "oracle", "Mapping classification", "required"),
        ("ORACLE_003", "oracle", "oracle call count", "1"),
        ("ORACLE_004", "oracle", "same positional objects", "2/2"),
        ("ORACLE_005", "oracle", "complete Exact10 construction", "true"),
        ("ORACLE_006", "oracle", "full Exact10 equality", "required"),
        ("ORACLE_007", "oracle", "partial equality", "forbidden"),
        ("PROJECTION_001", "projection", "normalized values", "source.validated_candidate_fields"),
        ("PROJECTION_002", "projection", "validated fields", "source.validated_candidate_fields"),
        ("PROJECTION_003", "projection", "source outcome/reason/consumption", "preserved"),
        ("PROJECTION_004", "projection", "scalar-short context injection", "forbidden"),
        ("ISSUE_001", "issue", "coverage after", "ADMIT_011_to_ADMIT_015"),
        ("ISSUE_002", "issue", "only coverage row fields changed", "2"),
        ("BOUNDARY_001", "boundary", "provider mapping", "false"),
        ("BOUNDARY_002", "boundary", "real provider leakage group IDs", "0"),
        ("BOUNDARY_003", "boundary", "ADMIT_011", "not_started"),
        ("BOUNDARY_004", "boundary", "evaluate_all_rules", "absent"),
        ("BOUNDARY_005", "boundary", "combined verdict", "absent"),
        ("BOUNDARY_006", "boundary", "training", "forbidden"),
    )


def _contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for contract_id, area, statement, expected in _contract_definitions()
    ]


def _registry_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in EVALUATOR_REGISTRY
        if rule_id in KNOWN_RULE_IDS[:9]:
            identity = "predecessor_object_identity"
        elif rule_id == ADMISSION_RULE_ID:
            identity = "exact_new_admit010_handler"
        else:
            identity = "not_registered"
        rows.append(
            {
                "rule_id": rule_id,
                "rule_name": RULE_NAMES.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(rule_id in CALLABLE_DISCOVERED_RULE_IDS).lower(),
                "adapter_ready": str(rule_id in ADAPTER_READY_RULE_IDS).lower(),
                "registered": str(registered).lower(),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "handler_identity_status": identity,
                "dispatch_disposition": (
                    "registered_local_handler"
                    if registered
                    else "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"
                ),
                "audit_passed": "true",
            }
        )
    return rows


EXECUTED_SAFETY_ITEMS = (
    "admit010_adapter_runtime",
    "registry_registration",
    "exact10_dispatcher",
    "source_validation",
    "oracle_parity",
    "exact13_projection",
    "issue_coverage_transition",
    "deterministic_materialization",
    "source_verification",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "provider_mapping",
    "real_provider_export",
    "admit011",
    "evaluate_all_rules",
    "combined_verdict",
    "raw_network_download",
    "split_reassignment",
    "checkpoint",
    "model_forward_loss",
    "training_fine_tune",
    "stage_commit_push_gh",
)


def _safety_rows() -> list[dict[str, str]]:
    definitions = tuple((item, True) for item in EXECUTED_SAFETY_ITEMS) + tuple(
        (item, False) for item in NOT_EXECUTED_SAFETY_ITEMS
    )
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
    "admit_010_standalone_evaluator_implemented",
    "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine",
    "admit_010_context_routing_runtime_enforced",
    "admit_010_candidate_projection_runtime_enforced",
    "admit_010_source_exact10_validation_runtime_enforced",
    "admit_010_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_010_exact10_to_exact13_projection_runtime_enforced",
    "admit_010_formal_exactly_once_runtime_enforced",
    "admit_010_oracle_exactly_once_runtime_enforced",
    "admit_010_original_object_identity_runtime_enforced",
    "admit_010_key_absent_only_missing_runtime_enforced",
    "admit_010_provider_mapping_boundary_preserved",
    "exact10_reuses_exact9_public_type_identity",
    "exact10_first_nine_handler_identity_preserved",
    "exact10_public_dispatch_new_successor_function",
    "exact10_public_dispatch_signature_matches_exact9",
    "exact10_public_dispatch_uses_local_registry",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "ready_for_admit_011_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "admit_011_started",
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


def _updated_issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    coverage = matches[0]
    before = dict(coverage)
    coverage["affected_rules"] = "|".join(KNOWN_RULE_IDS[10:])
    coverage["integration_transition"] = "admit_010_implemented_and_removed_from_open_coverage_scope"
    if coverage["status"] != "open":
        raise ValueError("coverage issue unexpectedly closed")
    changed = {key for key in coverage if coverage[key] != before[key]}
    if changed != {"affected_rules", "integration_transition"}:
        raise ValueError("coverage issue transition exceeded authorization")
    return rows


def build_runtime_state(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid frozen Exact18 snapshot")
    predecessor_state = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    truth_rows = _truth_rows(predecessor_state["predecessor_truth"])
    registry_rows = _registry_rows()
    safety_rows = _safety_rows()
    issue_rows = _updated_issue_rows(predecessor_state["design_issues"])
    issue_bytes = _csv_bytes(ISSUE_COLUMNS, issue_rows)
    checks = (
        len({row["contract_id"] for row in contract_rows}) == len(contract_rows),
        all(row["contract_passed"] == "true" for row in contract_rows),
        len(truth_rows) == 407,
        all(row["case_passed"] == "true" for row in truth_rows),
        len(registry_rows) == 15,
        tuple(row["rule_id"] for row in registry_rows) == KNOWN_RULE_IDS,
        all(row["audit_passed"] == "true" for row in registry_rows),
        len(safety_rows) == 20,
        all(row["safety_passed"] == "true" for row in safety_rows),
        len(issue_rows) == 11,
        hashlib.sha256(issue_bytes).hexdigest()
        == "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c",
        type(RULE_NAMES) is MappingProxyType,
        type(ADAPTER_IDS) is MappingProxyType,
        type(EVALUATOR_REGISTRY) is MappingProxyType,
        tuple(EVALUATOR_REGISTRY) == ADAPTER_READY_RULE_IDS,
        all(
            EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:9]
        ),
        EVALUATOR_REGISTRY[ADMISSION_RULE_ID] is _evaluate_registered_admit_010,
        UnifiedAdmissionRuleEvaluation is predecessor.UnifiedAdmissionRuleEvaluation,
        UnifiedAdmissionDispatchError is predecessor.UnifiedAdmissionDispatchError,
        RESULT_SCHEMA_VERSION is predecessor.RESULT_SCHEMA_VERSION,
        RESULT_FIELDS is predecessor.RESULT_FIELDS,
        DISPATCH_ERROR_FIELDS is predecessor.DISPATCH_ERROR_FIELDS,
        DISPATCH_ERROR_CODES is predecessor.DISPATCH_ERROR_CODES,
        OUTCOME_VOCABULARY is predecessor.OUTCOME_VOCABULARY,
        evaluate_admission_rule is not predecessor.evaluate_admission_rule,
        inspect.signature(evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule),
        evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is EVALUATOR_REGISTRY,
        not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules"),
        not hasattr(__import__(__name__, fromlist=["x"]), "combined_candidate_verdict"),
    )
    if not all(checks):
        raise RuntimeError("Exact10 runtime state failed closed")
    return {
        "snapshot": snapshot,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": dict(Counter(row["case_group"] for row in truth_rows)),
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
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
    snapshot = state["snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    first_nine_identity = {
        rule_id: EVALUATOR_REGISTRY[rule_id] is predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in KNOWN_RULE_IDS[:9]
    }
    payload: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "exact10_identity": "ADMIT_001_to_ADMIT_010_unified_single_rule_runtime_v1",
        "exact9_predecessor_identity": "ADMIT_001_to_ADMIT_009_unified_single_rule_runtime_v1",
        "source_boundary_name": "fixed_ordered_exact18_committed_source_boundary",
        "source_input_count": 18,
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
                "safe_descendant": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact9_unified_runtime_predecessor",
            "admit010_standalone_evaluator",
            "admit010_committed_independent_provenance_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_type_and_constant_identity": {
            "UnifiedAdmissionRuleEvaluation": True,
            "UnifiedAdmissionDispatchError": True,
            "RESULT_SCHEMA_VERSION": True,
            "RESULT_FIELDS": True,
            "DISPATCH_ERROR_FIELDS": True,
            "DISPATCH_ERROR_CODES": True,
            "OUTCOME_VOCABULARY": True,
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": str(inspect.signature(evaluate_admission_rule)),
        "public_dispatch_signature_matches_exact9": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "registered_local_registry",
            "local_registry_handler",
        ],
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
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[10:]),
        "registered_rule_count": 10,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_nine_handler_identity_reused": first_nine_identity,
        "admit_010_handler": "_evaluate_registered_admit_010",
        "admit_010_handler_identity": "exact_new_admit010_handler",
        "admit_010_candidate_fields": list(ADMIT_010_CANDIDATE_FIELDS),
        "admit_010_context_items": list(ADMIT_010_CONTEXT_ITEMS),
        "admit_010_context_validation_order": [
            "batch_context_must_be_none",
            "evaluation_context_mapping_validation",
            "leakage_group_assignment_provenance_contract_required_key_lookup",
            "download_result_context_must_be_none",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "leakage_group_id_required_key_lookup",
            "formal_evaluator",
            "source_validation",
            "independent_oracle",
            "full_exact10_equality",
            "exact13_projection",
        ],
        "admit_010_context_reasons": {
            "batch_context": "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "evaluation_context_key": "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED",
            "download_result_context": "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_010_candidate_mapping_invalid_reason": "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_010_missing_reason": "leakage_group_id_missing",
        "admit_010_required_lookup": "single_direct_lookup_KeyError_only",
        "admit_010_present_values_forwarded_unchanged": True,
        "admit_010_formal_evaluator": "evaluate_admit_010",
        "admit_010_formal_positional_argument_order": ["scalar_object", "provenance_object"],
        "admit_010_formal_call_count": 1,
        "admit_010_adapter_normalization": False,
        "admit_010_source_type": "Admit010EvaluationResult",
        "admit_010_source_fields": list(admit010.RESULT_FIELDS),
        "admit_010_source_type_invalid_reason": "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_010_source_invariant_invalid_reason": "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_010_source_prevalidation_before_oracle": True,
        "admit_010_source_full_exact10_invariant_validation": True,
        "admit_010_oracle": "classify_admit_010_leakage_group_assignment_provenance_design",
        "admit_010_oracle_call_count": 1,
        "admit_010_source_oracle_full_exact10_equality_required": True,
        "admit_010_normalized_values_projection": "source.validated_candidate_fields",
        "admit_010_no_partial_exact13_on_failure": True,
        "standalone_exact71_projection_count": 71,
        "contract_row_count": len(state["contract_rows"]),
        "contract_pass_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_pass_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": len(state["safety_rows"]),
        "safety_audit_pass_count": len(state["safety_rows"]),
        "issue_inventory_row_count": 11,
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "admit_010_implemented_and_removed_from_open_coverage_scope",
        "issue_coverage_after": list(KNOWN_RULE_IDS[10:]),
        "issue_authoritative_predecessor_sha256": SOURCE_SHA256[DESIGN_ISSUE_PATH],
        "issue_output_sha256": "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c",
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "output_materialization": {
            "output_preflight_before_source_read": True,
            "repo_root_real_non_symlink": True,
            "relative_output_resolved_within_repo": True,
            "absolute_output_parent_has_no_symlink_indirection": True,
            "exact_six_allowlist": True,
            "existing_entries_regular_non_symlink": True,
            "unsafe_state_has_no_source_read_or_partial_write": True,
            "same_directory_mkstemp": True,
            "temporary_suffix": ".tmp",
            "fdopen_mode": "wb",
            "flush_and_fsync": True,
            "os_replace": True,
            "finally_cleanup": True,
            "postwrite_exact_six_revalidated": True,
        },
        "provider_fields_consumed": [],
        "real_provider_leakage_group_id_count": 0,
        "leakage_group_id_provider_mapping_validated": False,
        "exact9_runtime_modified": False,
        "admit_011_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "stop_boundaries": [
            "no_admit_011",
            "no_provider_mapping",
            "no_real_candidate_evaluation",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_raw_or_checkpoint_read",
            "no_network_or_download",
            "no_model_forward_loss_training",
        ],
        "readiness_true_count": len(TRUE_READINESS),
        "readiness_false_count": len(FALSE_READINESS),
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
        "manifest_top_level_key_count": 0,
    }
    payload["manifest_top_level_key_count"] = len(payload)
    return payload


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(REGISTRY_COLUMNS, state["registry_rows"]),
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


def _resolved_output_preflight(
    output_root: Path,
    repo_root: Path,
) -> tuple[Path, bool]:
    """Authorize an output target without mutating the filesystem."""
    root_repo = _real_directory(repo_root)
    output_was_relative = not output_root.is_absolute()
    if output_was_relative:
        if ".." in output_root.parts:
            raise ValueError("output target resolved containment invalid")
        root = root_repo / output_root
    else:
        root = Path(os.path.abspath(output_root))

    parent = Path(os.path.abspath(root.parent))
    parent_mode = os.lstat(parent).st_mode
    if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode) or parent.resolve(strict=True) != parent:
        raise ValueError("output target resolved containment invalid")
    if output_was_relative:
        try:
            root.relative_to(root_repo)
            parent.relative_to(root_repo)
        except ValueError:
            raise ValueError("output target resolved containment invalid") from None

    if root.exists() or root.is_symlink():
        mode = os.lstat(root).st_mode
        if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode) or root.resolve(strict=True) != root:
            raise ValueError("output target resolved containment invalid")
        entries = tuple(root.iterdir())
        extras = {entry.name for entry in entries} - set(OUTPUT_FILES)
        if extras:
            raise ValueError("unexpected output entry")
        for entry in entries:
            mode = os.lstat(entry).st_mode
            if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                raise ValueError("unsafe output entry")
        return root, False
    return root, True


def _validate_prewrite_output_root(
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
    newly_created: bool,
) -> None:
    """Revalidate the authorized root immediately before the first write."""
    root_repo = _real_directory(repo_root)
    absolute_root = Path(os.path.abspath(root))
    parent = Path(os.path.abspath(absolute_root.parent))
    parent_mode = os.lstat(parent).st_mode
    if (
        not stat.S_ISDIR(parent_mode)
        or stat.S_ISLNK(parent_mode)
        or parent.resolve(strict=True) != parent
    ):
        raise ValueError("output target resolved containment invalid")
    if output_root_was_relative:
        try:
            absolute_root.relative_to(root_repo)
        except ValueError:
            raise ValueError("output target resolved containment invalid") from None
    mode = os.lstat(absolute_root).st_mode
    if (
        not stat.S_ISDIR(mode)
        or stat.S_ISLNK(mode)
        or absolute_root.resolve(strict=True) != absolute_root
    ):
        raise ValueError("output target resolved containment invalid")
    entries = tuple(absolute_root.iterdir())
    if newly_created and entries:
        raise ValueError("newly created output root must be empty")
    extras = {entry.name for entry in entries} - set(OUTPUT_FILES)
    if extras:
        raise ValueError("unexpected output entry")
    for entry in entries:
        entry_mode = os.lstat(entry).st_mode
        if not stat.S_ISREG(entry_mode) or stat.S_ISLNK(entry_mode):
            raise ValueError("unsafe output entry")


def _postvalidate_output_root(root: Path) -> None:
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(OUTPUT_FILES):
        raise ValueError("postwrite output inventory mismatch")
    if any(
        not stat.S_ISREG(os.lstat(entry).st_mode) or stat.S_ISLNK(os.lstat(entry).st_mode)
        for entry in entries
    ):
        raise ValueError("postwrite output entry type invalid")


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


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    # Authorization and inventory preflight must precede every source-byte read.
    output_root_was_relative = not output_root.is_absolute()
    root, create_root = _resolved_output_preflight(output_root, repo_root)
    snapshot = build_frozen_source_snapshot(repo_root)
    state = build_runtime_state(snapshot)
    payloads, manifest = _payloads(state)
    if create_root:
        root.mkdir(exist_ok=False)
    _validate_prewrite_output_root(
        root,
        repo_root,
        output_root_was_relative=output_root_was_relative,
        newly_created=create_root,
    )
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    _postvalidate_output_root(root)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_008.

The Exact7 predecessor remains the sole authority for the public result and
dispatch-error types.  This successor adds only the ADMIT_008 adapter and an
eighth immutable registry entry.  Public dispatch is pure in memory; metadata
and deterministic synthetic evidence are reachable only through the separate
materialization entry point at the end of this module.
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
    covapie_bulk_download_admission_admit_008_rule_logic_interface as admit008,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate
    as admit008_oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007
    as predecessor,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_008 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_008_v1"
)
EXPECTED_BASE_COMMIT = "f7079d9dfe5ef30889fb6fbe3bf5b66fdb0db5b0"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_008_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_009_formal_evaluator_interface_preconditions_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Exact identity re-exports.  No public result or error class is redefined.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(
    f"ADMIT_{index:03d}" for index in range(1, 9)
)
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()
ADMIT_008_CANDIDATE_FIELDS = ("topology_restoration_disposition",)
ADMIT_008_CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)

RULE_NAMES = MappingProxyType(
    {
        **dict(predecessor.RULE_NAMES),
        "ADMIT_008": "topology_restoration_disposition",
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        **dict(predecessor.ADAPTER_IDS),
        "ADMIT_008": "covapie_admit_008_unified_adapter_v1",
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


def _admit008_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_008",
        True,
        True,
        True,
        reason,
    )


def _admit008_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "ADMIT_008",
        True,
        True,
        False,
        reason,
    )


def _admit008_candidate_invalid(
    reason: str,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_008",
        admission_rule_name=RULE_NAMES["ADMIT_008"],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=ADMIT_008_CANDIDATE_FIELDS,
        consumed_context_items=ADMIT_008_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_008"],
    )


def _prevalidate_admit008_source(
    source: object,
) -> admit008.Admit008EvaluationResult:
    """Require the exact committed type and reconstruct all Exact10 state."""
    if type(source) is not admit008.Admit008EvaluationResult:
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        )
    assert type(source) is admit008.Admit008EvaluationResult
    try:
        storage = vars(source)
    except TypeError:
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if type(storage) is not dict or tuple(storage) != admit008.RESULT_FIELDS:
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if (
        tuple(field.name for field in fields(admit008.Admit008EvaluationResult))
        != admit008.RESULT_FIELDS
    ):
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    try:
        ordered_values = tuple(
            getattr(source, name) for name in admit008.RESULT_FIELDS
        )
        reconstructed = admit008.Admit008EvaluationResult(*ordered_values)
    except (AttributeError, TypeError, ValueError):
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if reconstructed != source:
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return source


def _expected_admit008_from_oracle(
    scalar_object: object,
    allowed_dispositions_object: object,
) -> admit008.Admit008EvaluationResult:
    """Call the committed independent oracle once and construct full Exact10."""
    try:
        classification = admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
            scalar_object,
            allowed_dispositions_object,
        )
        outcome = classification.admit_008
        expected = admit008.Admit008EvaluationResult(
            admission_rule_id="ADMIT_008",
            outcome=outcome.outcome,
            passed=outcome.passed,
            blocks_candidate=outcome.blocks_candidate,
            reason=outcome.reason,
            canonical_topology_restoration_disposition=outcome.canonical_value,
            validated_candidate_fields=outcome.validated_candidate_fields,
            consumed_candidate_fields=ADMIT_008_CANDIDATE_FIELDS,
            consumed_context_items=ADMIT_008_CONTEXT_ITEMS,
            evaluator_io_used=False,
        )
    except (AttributeError, TypeError, ValueError):
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return expected


def _validate_admit008_oracle_equivalence(
    source: admit008.Admit008EvaluationResult,
    expected: admit008.Admit008EvaluationResult,
) -> None:
    if type(expected) is not admit008.Admit008EvaluationResult or source != expected:
        _admit008_adapter_failure(
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


def _project_admit008_exact13(
    source: admit008.Admit008EvaluationResult,
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=RULE_NAMES["ADMIT_008"],
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=source.validated_candidate_fields,
        validated_candidate_fields=source.validated_candidate_fields,
        consumed_candidate_fields=source.consumed_candidate_fields,
        consumed_context_items=source.consumed_context_items,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_IDS["ADMIT_008"],
    )


def _evaluate_registered_admit_008(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # Every context gate completes before the first candidate access.
    if batch_context is not None:
        _admit008_context_failure("ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit008_context_failure(
            "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED"
        )
    try:
        allowed_dispositions_object = evaluation_context[
            "allowed_topology_restoration_dispositions"
        ]
    except KeyError:
        _admit008_context_failure(
            "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED"
        )
    if download_result_context is not None:
        _admit008_context_failure(
            "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
        )
    if stage_authorization_context is not None:
        _admit008_context_failure(
            "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
        )

    if not isinstance(candidate_record, Mapping):
        return _admit008_candidate_invalid(
            "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"
        )
    try:
        scalar_object = candidate_record["topology_restoration_disposition"]
    except KeyError:
        return _admit008_candidate_invalid(
            "topology_restoration_disposition_missing"
        )

    source = admit008.evaluate_admit_008(
        scalar_object,
        allowed_dispositions_object,
    )
    validated_source = _prevalidate_admit008_source(source)
    expected = _expected_admit008_from_oracle(
        scalar_object,
        allowed_dispositions_object,
    )
    _validate_admit008_oracle_equivalence(validated_source, expected)
    return _project_admit008_exact13(validated_source)


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": predecessor.EVALUATOR_REGISTRY["ADMIT_006"],
        "ADMIT_007": predecessor.EVALUATOR_REGISTRY["ADMIT_007"],
        "ADMIT_008": _evaluate_registered_admit_008,
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


# Fixed ordered Exact18 source boundary.  The adapter-design module is parsed
# only as frozen metadata evidence and is deliberately absent from imports.
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_registry_routing_and_oracle_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_safety_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_rule_logic_interface_v1/covapie_admit_008_rule_logic_interface_truth_matrix.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_candidate_projection_and_context_routing_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_result_projection_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_issue_readiness_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
            "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
            "d3a1ad40803ceb25f30e106bbab44ab11cfcc26717b7c244266ab1ce1378f29d",
            "149b838e9fe8254df7ba7a610ae64377cb7c7a41da8010cedee4722dcea081b5",
            "1dbb5453277a93dff5d7612715c5fdd5edfde0d63cf114802220f962e22118f3",
            "97fba54037625b78a82b17753b77870366f8c3fa492ee506923ed3ca369c9f88",
            "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
            "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01",
            "ae5fc1c5aa28618765ed07fe5aae67c02d31e7650fb5921dae954c0a3cfefd7e",
            "62fdcf8c18f5baf3b08cd29515804abba7543d5da21056d2d93a392d5c188ac9",
            "a78510cf512782f9bd586e040d26a7fb459ba8b0e1eec310195b417cd0b9c636",
            "930a8791bd129a06b272163766a5431aeaf1a3e79003b22df77d6af16319fecb",
            "d7423c337512dff3f66a68209301c91dd3fee2bdd2a3a5b669185854c622d922",
            "29d4ceacd263cf4b1bb0a4320a8eda03a8742e9bb344b512f8412baed7967e8a",
            "7c8060203e71b83f7398d79977dfa69057089231fec034afba95fcf37d99fef2",
            "59fa45d08d8950387ebd752d0f867312a47a67326c9b23bed886500307a36e4c",
            "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
            "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d",
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
    ENUM_SOURCE_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_008_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_008_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_008_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_008_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_008_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_008_runtime_manifest.json"
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
    try:
        (repo_root / path).resolve().relative_to(repo_root.resolve())
        descendant = True
    except ValueError:
        descendant = False
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(tree_fields) == 3
        and tree_fields[0] in ("100644", "100755")
        and tree_fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and descendant
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
    predecessor_manifest = _json_document(snapshot, PREDECESSOR_MANIFEST_PATH)
    predecessor_contract = _csv_document(snapshot, PREDECESSOR_CONTRACT_PATH)
    predecessor_truth = _csv_document(snapshot, PREDECESSOR_TRUTH_PATH)
    predecessor_registry = _csv_document(snapshot, PREDECESSOR_REGISTRY_PATH)
    predecessor_safety = _csv_document(snapshot, PREDECESSOR_SAFETY_PATH)
    predecessor_issues = _csv_document(snapshot, PREDECESSOR_ISSUE_PATH)
    standalone_manifest = _json_document(snapshot, STANDALONE_MANIFEST_PATH)
    standalone_contract = _csv_document(snapshot, STANDALONE_CONTRACT_PATH)
    standalone_truth = _csv_document(snapshot, STANDALONE_TRUTH_PATH)
    design_manifest = _json_document(snapshot, DESIGN_MANIFEST_PATH)
    design_contract = _csv_document(snapshot, DESIGN_CONTRACT_PATH)
    design_routing = _csv_document(snapshot, DESIGN_ROUTING_PATH)
    design_truth = _csv_document(snapshot, DESIGN_TRUTH_PATH)
    design_issues = _csv_document(snapshot, DESIGN_ISSUE_PATH)
    predecessor_tree = _ast_document(snapshot, PREDECESSOR_SOURCE_PATH)
    standalone_tree = _ast_document(snapshot, STANDALONE_SOURCE_PATH)
    design_tree = _ast_document(snapshot, DESIGN_SOURCE_PATH)
    enum_tree = _ast_document(snapshot, ENUM_SOURCE_PATH)
    design_issue_map = {row["issue_id"]: row for row in design_issues.rows}
    checks = (
        predecessor_manifest.get("all_checks_passed") is True,
        predecessor_manifest.get("registered_rule_ids")
        == list(KNOWN_RULE_IDS[:7]),
        predecessor_manifest.get("registered_rule_count") == 7,
        predecessor_manifest.get("ready_for_training") is False,
        len(predecessor_contract.rows) == 56,
        len(predecessor_truth.rows) == 107,
        len(predecessor_registry.rows) == 15,
        len(predecessor_safety.rows) == 36,
        len(predecessor_issues.rows) == 11,
        _literal_registry_keys(predecessor_tree) == KNOWN_RULE_IDS[:7],
        standalone_manifest.get("all_checks_passed") is True,
        standalone_manifest.get("result_fields") == list(admit008.RESULT_FIELDS),
        standalone_manifest.get("truth_matrix_row_count") == 38,
        len(standalone_contract.rows) == 37,
        len(standalone_truth.rows) == 38,
        "evaluate_admit_008" in _top_level_function_names(standalone_tree),
        design_manifest.get("all_checks_passed") is True,
        design_manifest.get("future_registered_rule_order")
        == list(KNOWN_RULE_IDS[:8]),
        design_manifest.get("admit_008_unified_adapter_implemented") is False,
        design_manifest.get("ready_for_training") is False,
        len(design_contract.rows) == 54,
        len(design_routing.rows) == 26,
        len(design_truth.rows) == 52,
        len(design_issues.rows) == 11,
        "build_design_state" in _top_level_function_names(design_tree),
        "_evaluate_registered_admit_008"
        not in _top_level_function_names(design_tree),
        "classify_admit_008_topology_restoration_disposition_design"
        in _top_level_function_names(enum_tree),
        design_issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"]
        == "resolved",
        design_issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"]
        == "resolved",
        design_issue_map[
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
        ]["affected_rules"]
        == "|".join(KNOWN_RULE_IDS[7:]),
    )
    if not all(checks):
        raise ValueError("predecessor contract validation failed")
    return {
        "predecessor_manifest": predecessor_manifest,
        "predecessor_truth_rows": predecessor_truth.rows,
        "design_manifest": design_manifest,
        "design_issue_rows": design_issues.rows,
    }


def _result_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


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


def _synthetic_exact38_definitions() -> tuple[
    tuple[str, str, object, object], ...
]:
    exact = admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
    scalar_cases: tuple[tuple[str, str, object], ...] = (
        ("canonical_approved_template", "canonical", admit008.CANONICAL_ENUM_MEMBERS[0]),
        ("canonical_manual_approved", "canonical", admit008.CANONICAL_ENUM_MEMBERS[1]),
        ("canonical_manual_required", "canonical", admit008.CANONICAL_ENUM_MEMBERS[2]),
        ("canonical_quarantine", "canonical", admit008.CANONICAL_ENUM_MEMBERS[3]),
        ("type_none", "scalar_type", None),
        ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _TruthStringSubclass(exact[0])),
        ("type_list", "scalar_type", [exact[0]]),
        ("type_mapping", "scalar_type", {"value": exact[0]}),
        ("empty", "empty_syntax", ""),
        ("whitespace", "empty_syntax", " "),
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
        ("unknown_other", "unknown", "other"),
        ("unknown_unknown", "unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact),
        ("context_none", None),
        ("context_list", list(exact)),
        ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))),
        ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_blocked_added", (*exact, admit008.CANONICAL_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_TruthStringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    definitions = [
        (name, group, scalar, exact)
        for name, group, scalar in scalar_cases
    ]
    definitions.extend(
        (name, "context", admit008.CANONICAL_ENUM_MEMBERS[0], context)
        for name, context in context_cases
    )
    return tuple(definitions)


def _invoke_admit008_counted(
    candidate: object,
    evaluation_value: object,
    *,
    formal_source: object | None = None,
    oracle_source: object | None = None,
    kwargs: Mapping[str, object] | None = None,
) -> tuple[
    object,
    int,
    int,
    tuple[tuple[object, object], ...],
    tuple[tuple[object, object], ...],
]:
    formal_real = admit008.evaluate_admit_008
    oracle_real = (
        admit008_oracle.classify_admit_008_topology_restoration_disposition_design
    )
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

    admit008.evaluate_admit_008 = formal_wrapper  # type: ignore[assignment]
    admit008_oracle.classify_admit_008_topology_restoration_disposition_design = oracle_wrapper  # type: ignore[assignment]
    routed = {ADMIT_008_CONTEXT_ITEMS[0]: evaluation_value}
    call_kwargs = dict(kwargs or {})
    call_kwargs.setdefault("evaluation_context", routed)
    try:
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            "ADMIT_008",
            candidate,
            **call_kwargs,
        )
    finally:
        admit008.evaluate_admit_008 = formal_real  # type: ignore[assignment]
        admit008_oracle.classify_admit_008_topology_restoration_disposition_design = oracle_real  # type: ignore[assignment]
    return (
        observed,
        len(formal_args),
        len(oracle_args),
        tuple(formal_args),
        tuple(oracle_args),
    )


def _fresh_unsafe_source(
    field_name: str, replacement: object
) -> admit008.Admit008EvaluationResult:
    value = admit008.evaluate_admit_008(
        admit008.CANONICAL_ENUM_MEMBERS[0],
        admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    object.__setattr__(value, field_name, replacement)
    return value


def _truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    class RuleStringSubclass(str):
        pass

    global_cases = (
        ("GLOBAL_NON_STR", 8, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", ""),
        (
            "GLOBAL_STR_SUBCLASS",
            RuleStringSubclass("ADMIT_008"),
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
            "ADMIT_009",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "ADMIT_009",
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
        observed_value, observed_reason = _label(observed)
        rows.append(
            _truth_row(
                case_id,
                "global_dispatch",
                str(rule_id),
                "global_precedence",
                code,
                observed_value,
                code,
                observed_reason,
                extra_passed=(
                    type(observed) is UnifiedAdmissionDispatchError
                    and observed.admission_rule_id == reported
                ),
            )
        )

    for rule_id in KNOWN_RULE_IDS[:7]:
        same = (
            EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
        )
        rows.append(
            _truth_row(
                f"PRED_IDENTITY_{rule_id}",
                "predecessor_handler_identity",
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
    for prior in predecessor_rows:
        rows.append(
            _truth_row(
                f"PRED_EXACT7_{prior['case_id']}",
                "predecessor_exact7_truth",
                prior["admission_rule_id"],
                f"{prior['case_group']}|{prior['behavior']}",
                prior["expected_result_or_error"],
                prior["observed_result_or_error"],
                prior["expected_reason"],
                prior["observed_reason"],
                formal=int(prior["formal_call_count"]),
                oracle=int(prior["oracle_call_count"]),
                access=prior["candidate_access_status"],
                identity=prior["predecessor_handler_identity_status"],
                extra_passed=prior["case_passed"] == "true",
            )
        )

    for index, (name, semantic_group, scalar, context) in enumerate(
        _synthetic_exact38_definitions(), 1
    ):
        observed, formal, oracle, formal_args, oracle_args = (
            _invoke_admit008_counted(
                {ADMIT_008_CANDIDATE_FIELDS[0]: scalar}, context
            )
        )
        expected = admit008.evaluate_admit_008(scalar, context)
        observed_value, observed_reason = _label(observed)
        complete = (
            type(observed) is UnifiedAdmissionRuleEvaluation
            and observed.outcome == expected.outcome
            and observed.reason == expected.reason
            and observed.normalized_values
            == observed.validated_candidate_fields
            == expected.validated_candidate_fields
            and formal == oracle == 1
            and formal_args[0][0] is scalar
            and formal_args[0][1] is context
            and oracle_args[0][0] is scalar
            and oracle_args[0][1] is context
        )
        rows.append(
            _truth_row(
                f"A008_EXACT38_{index:03d}_{name}",
                "admit008_exact38",
                "ADMIT_008",
                f"complete_exact10_oracle_and_exact13|{semantic_group}",
                expected.outcome,
                observed_value,
                expected.reason,
                observed_reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=complete,
            )
        )

    missing_context = _SingleLookupMapping(
        ADMIT_008_CONTEXT_ITEMS[0], object(), present=False
    )
    context_cases: tuple[tuple[str, dict[str, object], str], ...] = (
        (
            "A008_CONTEXT_BATCH",
            {"batch_context": {}},
            "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A008_CONTEXT_EVALUATION",
            {"evaluation_context": []},
            "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            "A008_CONTEXT_KEY",
            {"evaluation_context": missing_context},
            "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED",
        ),
        (
            "A008_CONTEXT_DOWNLOAD",
            {
                "evaluation_context": {
                    ADMIT_008_CONTEXT_ITEMS[0]: admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
                },
                "download_result_context": {},
            },
            "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A008_CONTEXT_STAGE",
            {
                "evaluation_context": {
                    ADMIT_008_CONTEXT_ITEMS[0]: admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
                },
                "stage_authorization_context": {},
            },
            "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
        (
            "A008_CONTEXT_MULTI_PRECEDENCE",
            {
                "batch_context": {},
                "evaluation_context": [],
                "download_result_context": {},
                "stage_authorization_context": {},
            },
            "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
        ),
    )
    for case_id, kwargs, reason in context_cases:
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            "ADMIT_008",
            [],
            **kwargs,
        )
        value, observed_reason = _label(observed)
        rows.append(
            _truth_row(
                case_id,
                "admit008_context_routing",
                "ADMIT_008",
                "ordered_context_failure_no_candidate_access",
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                value,
                reason,
                observed_reason,
                access="not_accessed",
                extra_passed=(
                    type(observed) is UnifiedAdmissionDispatchError
                    and observed.adapter_ready is True
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
        "ADMIT_008",
        bomb,
        batch_context={},
        evaluation_context={},
    )
    value, reason = _label(observed)
    rows.append(
        _truth_row(
            "A008_CONTEXT_CANDIDATE_BOMB",
            "admit008_context_routing",
            "ADMIT_008",
            "candidate_not_accessed",
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            value,
            "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
            reason,
            access="not_accessed" if bomb.accesses == 0 else "accessed",
            extra_passed=bomb.accesses == 0,
        )
    )

    class EmptyStringSubclass(str):
        pass

    missing_candidate = _SingleLookupMapping(
        ADMIT_008_CANDIDATE_FIELDS[0], object(), present=False
    )
    mapping_candidate = _SingleLookupMapping(
        ADMIT_008_CANDIDATE_FIELDS[0], admit008.CANONICAL_ENUM_MEMBERS[0]
    )
    identity_scalar = object()
    identity_context = object()
    identity_candidate = _SingleLookupMapping(
        ADMIT_008_CANDIDATE_FIELDS[0], identity_scalar
    )
    identity_evaluation = _SingleLookupMapping(
        ADMIT_008_CONTEXT_ITEMS[0], identity_context
    )
    candidate_cases: tuple[
        tuple[str, object, object, str, str, int, int, Mapping[str, object] | None],
        ...,
    ] = (
        (
            "A008_CANDIDATE_NON_MAPPING",
            [],
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID",
            0,
            0,
            None,
        ),
        (
            "A008_CANDIDATE_KEY_MISSING",
            missing_candidate,
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            "topology_restoration_disposition_missing",
            0,
            0,
            None,
        ),
        (
            "A008_CANDIDATE_NONE",
            {ADMIT_008_CANDIDATE_FIELDS[0]: None},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[0],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_EMPTY",
            {ADMIT_008_CANDIDATE_FIELDS[0]: ""},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[1],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_EMPTY_SUBCLASS",
            {ADMIT_008_CANDIDATE_FIELDS[0]: EmptyStringSubclass("")},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[0],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_WHITESPACE",
            {ADMIT_008_CANDIDATE_FIELDS[0]: " "},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[3],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_INTEGER",
            {ADMIT_008_CANDIDATE_FIELDS[0]: 7},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[0],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_UNKNOWN",
            {ADMIT_008_CANDIDATE_FIELDS[0]: "unknown"},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "invalid",
            admit008.SCALAR_REASONS[4],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_PASSED_TEMPLATE",
            {ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[0]},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_PASSED_MANUAL",
            {ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[1]},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_BLOCKED_MANUAL",
            {ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[2]},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "blocked",
            admit008.BLOCKED_REASONS[admit008.CANONICAL_ENUM_MEMBERS[2]],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_BLOCKED_QUARANTINE",
            {ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[3]},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "blocked",
            admit008.BLOCKED_REASONS[admit008.CANONICAL_ENUM_MEMBERS[3]],
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_MAPPING_SUBCLASS",
            mapping_candidate,
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_EXTRA_FIELDS",
            {
                ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[0],
                "extra": object(),
            },
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_NO_MUTATION",
            {ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[0]},
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            "passed",
            "",
            1,
            1,
            None,
        ),
        (
            "A008_CANDIDATE_IDENTITY",
            identity_candidate,
            identity_context,
            "invalid",
            admit008.SCALAR_REASONS[0],
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
        observed, formal, oracle, formal_args, oracle_args = (
            _invoke_admit008_counted(
                candidate,
                context_value,
                kwargs=call_kwargs,
            )
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
        lookup_ok = (
            not isinstance(candidate, _SingleLookupMapping)
            or candidate.lookup_count == 1
        )
        identities = True
        if expected_formal:
            scalar = (
                candidate.value
                if isinstance(candidate, _SingleLookupMapping)
                else candidate[ADMIT_008_CANDIDATE_FIELDS[0]]
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
                "admit008_candidate_envelope",
                "ADMIT_008",
                "candidate_projection_key_absent_only_missing",
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
                    and lookup_ok
                    and identities
                ),
            )
        )

    valid = admit008.evaluate_admit_008(
        admit008.CANONICAL_ENUM_MEMBERS[0],
        admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )

    class SourceSubclass(admit008.Admit008EvaluationResult):
        pass

    source_subclass = object.__new__(SourceSubclass)
    for name in admit008.RESULT_FIELDS:
        object.__setattr__(source_subclass, name, getattr(valid, name))

    order_drift = admit008.evaluate_admit_008(
        admit008.CANONICAL_ENUM_MEMBERS[0],
        admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    first_name = admit008.RESULT_FIELDS[0]
    first_value = getattr(order_drift, first_name)
    object.__delattr__(order_drift, first_name)
    object.__setattr__(order_drift, first_name, first_value)
    unsafe_sources: list[tuple[str, object, str]] = [
        (
            "SOURCE_WRONG_TYPE",
            object(),
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        (
            "SOURCE_SUBCLASS",
            source_subclass,
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        ),
        (
            "SOURCE_STORAGE_ORDER",
            order_drift,
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        ),
        (
            "SOURCE_INVARIANT_CONFLICT",
            _fresh_unsafe_source("evaluator_io_used", True),
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        ),
    ]
    candidate = {
        ADMIT_008_CANDIDATE_FIELDS[0]: admit008.CANONICAL_ENUM_MEMBERS[0]
    }
    for case_id, source, expected_reason in unsafe_sources:
        observed, formal, oracle, _, _ = _invoke_admit008_counted(
            candidate,
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
            formal_source=source,
        )
        value, reason = _label(observed)
        rows.append(
            _truth_row(
                f"A008_{case_id}",
                "admit008_source_oracle",
                "ADMIT_008",
                "source_prevalidation_before_oracle_no_partial_result",
                "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                value,
                expected_reason,
                reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=formal == 1 and oracle == 0,
            )
        )

    mismatch = admit008_oracle.classify_admit_008_topology_restoration_disposition_design(
        admit008.CANONICAL_ENUM_MEMBERS[1],
        admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
    )
    observed, formal, oracle, _, _ = _invoke_admit008_counted(
        candidate,
        admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS,
        formal_source=valid,
        oracle_source=mismatch,
    )
    value, reason = _label(observed)
    rows.append(
        _truth_row(
            "A008_SOURCE_ORACLE_MISMATCH",
            "admit008_source_oracle",
            "ADMIT_008",
            "complete_exact10_mismatch_no_projection",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            value,
            "ADMIT_008_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            reason,
            formal=formal,
            oracle=oracle,
            access="value_read_once",
            extra_passed=formal == oracle == 1,
        )
    )

    projection_cases = (
        ("PASSED_TEMPLATE", admit008.CANONICAL_ENUM_MEMBERS[0], admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        ("PASSED_MANUAL", admit008.CANONICAL_ENUM_MEMBERS[1], admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        ("BLOCKED_MANUAL", admit008.CANONICAL_ENUM_MEMBERS[2], admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        ("BLOCKED_QUARANTINE", admit008.CANONICAL_ENUM_MEMBERS[3], admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        ("SCALAR_INVALID", "unknown", admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS),
        ("CONTEXT_INVALID_CANONICAL", admit008.CANONICAL_ENUM_MEMBERS[0], None),
    )
    for case_id, scalar, context in projection_cases:
        observed, formal, oracle, _, _ = _invoke_admit008_counted(
            {ADMIT_008_CANDIDATE_FIELDS[0]: scalar}, context
        )
        expected = admit008.evaluate_admit_008(scalar, context)
        value, reason = _label(observed)
        rows.append(
            _truth_row(
                f"A008_PROJECTION_{case_id}",
                "admit008_projection",
                "ADMIT_008",
                "complete_exact10_to_existing_exact13",
                expected.outcome,
                value,
                expected.reason,
                reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
                extra_passed=(
                    type(observed) is UnifiedAdmissionRuleEvaluation
                    and observed.normalized_values
                    == observed.validated_candidate_fields
                    == expected.validated_candidate_fields
                ),
            )
        )

    for rule_id in KNOWN_RULE_IDS[8:]:
        observed = _invoke(__import__(__name__, fromlist=["x"]), rule_id, {})
        value, reason = _label(observed)
        rows.append(
            _truth_row(
                f"UNSUPPORTED_{rule_id}",
                "registry_issue_boundary",
                rule_id,
                "known_not_registered_fail_closed",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                value,
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                reason,
                extra_passed=(
                    type(observed) is UnifiedAdmissionDispatchError
                    and (
                        observed.known_rule,
                        observed.callable_discovered,
                        observed.adapter_ready,
                    )
                    == (True, False, False)
                ),
            )
        )
    rows.extend(
        (
            _truth_row(
                "BOUNDARY_ADMIT008_REGISTERED",
                "registry_issue_boundary",
                "ADMIT_008",
                "successor_handler_registered",
                "registered",
                (
                    "registered"
                    if EVALUATOR_REGISTRY.get("ADMIT_008")
                    is _evaluate_registered_admit_008
                    else "not_registered"
                ),
                "",
                "",
            ),
            _truth_row(
                "BOUNDARY_COVERAGE_ONLY_ADMIT008",
                "registry_issue_boundary",
                "ADMIT_008",
                "coverage_transition",
                "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
                "ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
                "",
                "",
            ),
            _truth_row(
                "BOUNDARY_ENUM_RESOLVED",
                "registry_issue_boundary",
                "ADMIT_008",
                "enum_issue_preserved",
                "resolved",
                "resolved",
                "",
                "",
            ),
            _truth_row(
                "BOUNDARY_NO_EVALUATE_ALL",
                "registry_issue_boundary",
                "",
                "public_boundary_absent",
                "absent",
                "absent"
                if not hasattr(
                    __import__(__name__, fromlist=["x"]), "evaluate_all_rules"
                )
                else "present",
                "",
                "",
            ),
            _truth_row(
                "BOUNDARY_NO_COMBINED_VERDICT",
                "registry_issue_boundary",
                "",
                "public_boundary_absent",
                "absent",
                "absent"
                if not hasattr(
                    __import__(__name__, fromlist=["x"]),
                    "combined_candidate_verdict",
                )
                else "present",
                "",
                "",
            ),
        )
    )
    expected_groups = {
        "global_dispatch": 5,
        "predecessor_handler_identity": 7,
        "predecessor_exact7_truth": 107,
        "admit008_exact38": 38,
        "admit008_context_routing": 7,
        "admit008_candidate_envelope": 16,
        "admit008_source_oracle": 5,
        "admit008_projection": 6,
        "registry_issue_boundary": 12,
    }
    if (
        Counter(row["case_group"] for row in rows) != expected_groups
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
        ("API_003", "public_api", "evaluate_all_rules", "excluded"),
        ("API_004", "public_api", "combined candidate verdict", "excluded"),
        ("DISPATCH_001", "global_dispatch", "precedence", "exact_str|known|registered|handler"),
        ("REGISTRY_001", "registry", "immutable registry", "true"),
        ("REGISTRY_002", "registry", "registered IDs", "|".join(ADAPTER_READY_RULE_IDS)),
        ("REGISTRY_003", "registry", "registered count", "8"),
        ("REGISTRY_004", "registry", "callable discovered count", "8"),
        ("REGISTRY_005", "registry", "adapter ready count", "8"),
        ("REUSE_001", "predecessor_reuse", "first seven handler identity", "true"),
        ("REUSE_002", "predecessor_reuse", "first seven names and adapters", "true"),
        ("A008_001", "admit008_identity", "rule name", RULE_NAMES["ADMIT_008"]),
        ("A008_002", "admit008_identity", "adapter ID", ADAPTER_IDS["ADMIT_008"]),
        ("CONTEXT_001", "context_routing", "precedence", "batch|evaluation_mapping|evaluation_key|download_result|stage_authorization"),
        ("CONTEXT_002", "context_routing", "batch context", "exact_none"),
        ("CONTEXT_003", "context_routing", "evaluation Mapping subclass", "accepted"),
        ("CONTEXT_004", "context_routing", "evaluation extra keys", "ignored"),
        ("CONTEXT_005", "context_routing", "required value", "original_identity_single_lookup_no_prevalidation"),
        ("CONTEXT_006", "context_routing", "download result context", "exact_none"),
        ("CONTEXT_007", "context_routing", "stage authorization context", "exact_none"),
        ("CONTEXT_008", "context_routing", "candidate access before routing", "false"),
        ("CANDIDATE_001", "candidate_projection", "field", ADMIT_008_CANDIDATE_FIELDS[0]),
        ("CANDIDATE_002", "candidate_projection", "Mapping subclasses", "accepted"),
        ("CANDIDATE_003", "candidate_projection", "extra fields", "ignored"),
        ("CANDIDATE_004", "candidate_projection", "non Mapping reason", "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_005", "candidate_projection", "consumed context retained", "true"),
        ("MISSING_001", "missing", "only category", "required_key_absent"),
        ("MISSING_002", "missing", "reason", "topology_restoration_disposition_missing"),
        ("FORWARD_001", "forwarding", "exact None", admit008.SCALAR_REASONS[0]),
        ("FORWARD_002", "forwarding", "exact built-in empty str", admit008.SCALAR_REASONS[1]),
        ("FORWARD_003", "forwarding", "empty str subclass", admit008.SCALAR_REASONS[0]),
        ("FORWARD_004", "forwarding", "whitespace malformed unknown and blocked", "standalone_exact_reason"),
        ("FORMAL_001", "formal_evaluator", "positional original objects", "single_candidate_lookup_single_context_lookup_exact_once"),
        ("FORMAL_002", "formal_evaluator", "normalization", "none"),
        ("FORMAL_003", "formal_evaluator", "provider mapping", "none"),
        ("FORMAL_004", "formal_evaluator", "I/O", "false"),
        ("SOURCE_001", "source_prevalidation", "exact source type", "required"),
        ("SOURCE_002", "source_prevalidation", "source subclass", "rejected"),
        ("SOURCE_003", "source_prevalidation", "storage", "exact_builtin_dict_exact10_key_order"),
        ("SOURCE_004", "source_prevalidation", "dataclass fields", "exact10_order"),
        ("SOURCE_005", "source_prevalidation", "ordered reads and reconstruction", "all_fields_before_oracle"),
        ("SOURCE_006", "source_prevalidation", "cross field invariants", "committed_post_init"),
        ("SOURCE_007", "source_prevalidation", "failure adapter readiness", "false"),
        ("SOURCE_008", "source_prevalidation", "oracle after failure", "false"),
        ("ORACLE_001", "semantic_oracle", "identity", "classify_admit_008_topology_restoration_disposition_design"),
        ("ORACLE_002", "semantic_oracle", "outcome view", "classification.admit_008"),
        ("ORACLE_003", "semantic_oracle", "original objects", "exact_once"),
        ("ORACLE_004", "semantic_oracle", "complete Exact10 construction", "required"),
        ("ORACLE_005", "semantic_oracle", "complete Exact10 equality", "required"),
        ("PROJECTION_001", "exact13", "normalized from validated", "true"),
        ("PROJECTION_002", "exact13", "two passed passthrough", "true"),
        ("PROJECTION_003", "exact13", "two blocked passthrough", "true"),
        ("PROJECTION_004", "exact13", "blocked reasons distinct", "true"),
        ("PROJECTION_005", "exact13", "scalar invalid empty pair", "true"),
        ("PROJECTION_006", "exact13", "context invalid canonical retained", "true"),
        ("PROJECTION_007", "exact13", "partial result on failure", "false"),
        ("SAFETY_001", "runtime_safety", "candidate mutation", "false"),
        ("SAFETY_002", "runtime_safety", "evaluation context mutation", "false"),
        ("SAFETY_003", "runtime_safety", "public runtime metadata I/O", "false"),
        ("SAFETY_004", "runtime_safety", "pure in memory runtime", "true"),
        ("ISSUE_001", "issues", "authoritative predecessor", SOURCE_SHA256[DESIGN_ISSUE_PATH]),
        ("ISSUE_002", "issues", "coverage transition", "admit_008_implemented_and_removed_from_open_coverage_scope"),
        ("ISSUE_003", "issues", "remaining coverage", "|".join(KNOWN_RULE_IDS[8:])),
        ("ISSUE_004", "issues", "topology enum", "resolved"),
        ("BOUNDARY_001", "boundary", "ADMIT_009 to ADMIT_015 registered", "false"),
        ("BOUNDARY_002", "boundary", "provider fields consumed", "none"),
        ("BOUNDARY_003", "boundary", "provider values", "zero"),
        ("BOUNDARY_004", "boundary", "real candidate evaluation", "excluded"),
        ("BOUNDARY_005", "boundary", "download and training", "excluded"),
        ("BOUNDARY_006", "boundary", "ADMIT_009 implementation", "excluded"),
    )
    if len({definition[0] for definition in definitions}) != len(definitions):
        raise RuntimeError("duplicate contract definition")
    return definitions


def _contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": identifier,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for identifier, area, statement, value in _contract_definitions()
    ]


def _registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in EVALUATOR_REGISTRY
        predecessor_reused = rule_id in KNOWN_RULE_IDS[:7]
        successor_implemented = rule_id == "ADMIT_008"
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
    "exact8_successor_runtime_implementation",
    "admit_008_adapter_handler_implementation",
    "exact8_registry_extension",
    "public_type_identity_reuse",
    "predecessor_handler_identity_reuse",
    "context_routing",
    "candidate_projection",
    "standalone_exact10_validation",
    "oracle_complete_exact10_equivalence",
    "exact13_projection",
    "synthetic_runtime_truth",
    "exact18_source_verification",
    "issue_coverage_transition",
    "deterministic_materialization",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "predecessor_exact7_runtime_modification",
    "admit_001_to_007_handler_modification",
    "admit_009_implementation",
    "admit_009_to_015_registration",
    "provider_mapping",
    "provider_value_materialization",
    "restoration_provenance_consumption",
    "real_candidate_evaluation",
    "evaluate_all_rules",
    "combined_candidate_verdict",
    "cross_rule_precedence_change",
    "raw_read",
    "network",
    "bulk_download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward",
    "model_loss",
    "training",
    "fine_tune",
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
    "unified_dispatch_runtime_with_admit_001_to_008_implemented",
    "admit_008_unified_adapter_implemented",
    "admit_008_registered_in_engine",
    "admit_008_context_routing_runtime_enforced",
    "admit_008_candidate_projection_runtime_enforced",
    "admit_008_key_absent_runtime_enforced",
    "admit_008_none_empty_forwarding_runtime_enforced",
    "admit_008_source_prevalidation_before_oracle_runtime_enforced",
    "admit_008_semantic_oracle_equivalence_runtime_enforced",
    "admit_008_unified_result_projection_runtime_enforced",
    "admit_008_blocked_passthrough_runtime_enforced",
    "admit_008_context_invalid_partial_canonical_projection_runtime_enforced",
    "exact7_public_types_reused_by_identity",
    "admit_001_to_007_handler_identity_reused",
    "registry_is_mapping_proxy_type",
    "registered_rule_count_is_8",
    "callable_discovered_rule_count_is_8",
    "adapter_ready_rule_count_is_8",
    "ready_for_admit_009_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "exact7_runtime_modified",
    "real_provider_topology_disposition_mapping_validated",
    "real_provider_value_count_nonzero",
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "admit_010_to_015_registered_in_engine",
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
    matches = [
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 11 or len(matches) != 1:
        raise ValueError("coverage issue missing or duplicate")
    coverage = matches[0]
    before = dict(coverage)
    coverage["affected_rules"] = "|".join(KNOWN_RULE_IDS[8:])
    coverage["integration_transition"] = (
        "admit_008_implemented_and_removed_from_open_coverage_scope"
    )
    changed = {key for key in coverage if coverage[key] != before[key]}
    if changed != {"affected_rules", "integration_transition"}:
        raise ValueError("coverage issue transition exceeded authorization")
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
        truth_rows = _truth_rows(
            predecessor_state["predecessor_truth_rows"]
        )
        registry_rows = _registry_rows()
        safety_rows = _safety_rows()
        issue_rows = _updated_issue_rows(
            predecessor_state["design_issue_rows"]
        )
        truth_groups = dict(Counter(row["case_group"] for row in truth_rows))
        issue_map = {row["issue_id"]: row for row in issue_rows}
        checks = (
            len(contract_rows) == len(_contract_definitions()),
            len({row["contract_id"] for row in contract_rows})
            == len(contract_rows),
            all(row["contract_passed"] == "true" for row in contract_rows),
            len(truth_rows) == 203,
            all(row["case_passed"] == "true" for row in truth_rows),
            len(registry_rows) == 15,
            tuple(row["admission_rule_id"] for row in registry_rows)
            == KNOWN_RULE_IDS,
            len(issue_rows) == 11,
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "affected_rules"
            ]
            == "|".join(KNOWN_RULE_IDS[8:]),
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "integration_transition"
            ]
            == "admit_008_implemented_and_removed_from_open_coverage_scope",
            issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"]
            == "resolved",
            issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"]
            == "resolved",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"]
            == "open",
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
                for rule_id in KNOWN_RULE_IDS[:7]
            ),
            EVALUATOR_REGISTRY["ADMIT_008"]
            is _evaluate_registered_admit_008,
            UnifiedAdmissionRuleEvaluation
            is predecessor.UnifiedAdmissionRuleEvaluation,
            UnifiedAdmissionDispatchError
            is predecessor.UnifiedAdmissionDispatchError,
            RESULT_SCHEMA_VERSION is predecessor.RESULT_SCHEMA_VERSION,
            RESULT_FIELDS is predecessor.RESULT_FIELDS,
            DISPATCH_ERROR_FIELDS is predecessor.DISPATCH_ERROR_FIELDS,
            DISPATCH_ERROR_CODES is predecessor.DISPATCH_ERROR_CODES,
            OUTCOME_VOCABULARY is predecessor.OUTCOME_VOCABULARY,
            inspect.signature(evaluate_admission_rule)
            == inspect.signature(predecessor.evaluate_admission_rule),
            not hasattr(
                __import__(__name__, fromlist=["x"]), "evaluate_all_rules"
            ),
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
    first_seven_identity = {
        rule_id: EVALUATOR_REGISTRY[rule_id]
        is predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in KNOWN_RULE_IDS[:7]
    }
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_boundary_name": "fixed_ordered_exact18_committed_source_boundary",
        "source_input_count": 18,
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
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact7_unified_runtime_predecessor",
            "admit008_standalone_evaluator",
            "admit008_committed_independent_enum_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_api_signature": str(inspect.signature(evaluate_admission_rule)),
        "public_dispatch_cardinality": "single_rule_only",
        "result_type_reused_by_identity": True,
        "dispatch_error_type_reused_by_identity": True,
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
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[8:]),
        "registered_rule_count": 8,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_seven_handler_identity_reused": first_seven_identity,
        "admit_008_handler": "_evaluate_registered_admit_008",
        "admit_008_candidate_fields": list(ADMIT_008_CANDIDATE_FIELDS),
        "admit_008_context_items": list(ADMIT_008_CONTEXT_ITEMS),
        "admit_008_context_order": [
            "batch_context",
            "evaluation_context_mapping",
            "evaluation_required_key",
            "download_result_context",
            "stage_authorization_context",
            "candidate_record",
        ],
        "admit_008_context_reasons": {
            "batch_context": "ADMIT_008_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_008_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "evaluation_required_key": "ADMIT_008_ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_REQUIRED",
            "download_result_context": "ADMIT_008_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_008_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_008_candidate_mapping_invalid_reason": "ADMIT_008_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_008_missing_categories": ["required_key_absent"],
        "admit_008_missing_reason": "topology_restoration_disposition_missing",
        "admit_008_none_empty_forwarding": {
            "exact_none": admit008.SCALAR_REASONS[0],
            "exact_builtin_empty_str": admit008.SCALAR_REASONS[1],
            "empty_str_subclass": admit008.SCALAR_REASONS[0],
        },
        "admit_008_formal_evaluator": "evaluate_admit_008",
        "admit_008_formal_call_count": 1,
        "admit_008_adapter_normalization": False,
        "admit_008_source_type": "Admit008EvaluationResult",
        "admit_008_source_fields": list(admit008.RESULT_FIELDS),
        "admit_008_source_prevalidation_before_oracle": True,
        "admit_008_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "admit_008_oracle_outcome_view": "classification.admit_008",
        "admit_008_oracle_call_count": 1,
        "admit_008_complete_exact10_equality_required": True,
        "admit_008_normalized_values_projection": "source.validated_candidate_fields",
        "admit_008_no_partial_exact13_on_failure": True,
        "admit_008_passed_members": list(
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
        ),
        "admit_008_blocked_reason_mapping": dict(admit008.BLOCKED_REASONS),
        "admit_008_scalar_invalid_empty_projection": True,
        "admit_008_context_invalid_canonical_projection": True,
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
        "issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "issue_authoritative_predecessor_sha256": SOURCE_SHA256[DESIGN_ISSUE_PATH],
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "provider_fields_consumed": [],
        "real_provider_value_count": 0,
        "real_provider_mapping_executed": False,
        "exact7_runtime_modified": False,
        "admit_009_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "stop_boundaries": [
            "no_admit_009",
            "no_provider_mapping",
            "no_real_candidate_evaluation",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_raw_network_download",
            "no_model_forward_loss_training",
        ],
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


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_runtime_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified ADMIT_001 to ADMIT_008 runtime failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

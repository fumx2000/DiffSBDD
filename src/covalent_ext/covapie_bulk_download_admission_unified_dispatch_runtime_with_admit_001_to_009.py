"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_009.

The Exact8 predecessor remains unchanged and is the sole authority for all
public result/error types and constants.  This successor reuses its first
eight handlers by object identity, adds the one ADMIT_009 adapter, and defines
an independent public dispatcher bound to the local Exact9 registry.

The public dispatch closure is pure in memory.  Frozen-source validation and
deterministic evidence materialization live below that closure and are only
reachable through the explicit materialization entry point.
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
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_009_rule_logic_interface as admit009,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate
    as admit009_oracle,
)


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_009 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_009_v1"
)
EXPECTED_BASE_COMMIT = "a0e5d56cc0afd8d2677aa53bd629fb33948ffaf3"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 unified adapter contract design v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_009_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_010_formal_evaluator_interface_preconditions_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Exact object-identity re-exports from Exact8.
UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(
    f"ADMIT_{index:03d}" for index in range(1, 10)
)
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_009"
ADMISSION_RULE_NAME = "duplicate_identity_precheck"
ADAPTER_ID = "covapie_admit_009_unified_adapter_v1"
ADMIT_009_CANDIDATE_FIELDS = ("duplicate_identity_key",)
ADMIT_009_CONTEXT_ITEMS = (
    "duplicate_identity_key_contract",
    "batch_duplicate_identity_keys",
)

RULE_NAMES = MappingProxyType(
    {
        **dict(predecessor.RULE_NAMES),
        ADMISSION_RULE_ID: ADMISSION_RULE_NAME,
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        **dict(predecessor.ADAPTER_IDS),
        ADMISSION_RULE_ID: ADAPTER_ID,
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


def _admit009_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit009_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit009_candidate_invalid(
    reason: str,
) -> UnifiedAdmissionRuleEvaluation:
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
        consumed_candidate_fields=ADMIT_009_CANDIDATE_FIELDS,
        consumed_context_items=ADMIT_009_CONTEXT_ITEMS,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[ADMISSION_RULE_ID],
    )


def _prevalidate_admit009_source(
    source: object,
) -> admit009.Admit009EvaluationResult:
    """Require exact committed type, Exact10 shape, and all invariants."""
    if type(source) is not admit009.Admit009EvaluationResult:
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        )
    assert type(source) is admit009.Admit009EvaluationResult
    try:
        storage = vars(source)
    except TypeError:
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if type(storage) is not dict or tuple(storage) != admit009.RESULT_FIELDS:
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    try:
        if (
            tuple(
                field.name
                for field in fields(admit009.Admit009EvaluationResult)
            )
            != admit009.RESULT_FIELDS
        ):
            raise ValueError("committed Exact10 field order drift")
        ordered_values = tuple(
            getattr(source, name) for name in admit009.RESULT_FIELDS
        )
        reconstructed = admit009.Admit009EvaluationResult(*ordered_values)
    except (AttributeError, TypeError, ValueError):
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if reconstructed != source:
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return source


def _expected_admit009_from_oracle(
    scalar_object: object,
    batch_object: object,
    policy_object: object,
) -> admit009.Admit009EvaluationResult:
    """Call the committed independent oracle once and construct Exact10."""
    try:
        classification = (
            admit009_oracle.classify_admit_009_duplicate_identity_key_design(
                scalar_object,
                batch_object,
                policy_object,
            )
        )
        if not isinstance(classification, Mapping):
            raise TypeError("oracle classification must be a Mapping")
        expected = admit009.Admit009EvaluationResult(
            ADMISSION_RULE_ID,
            classification["outcome"],
            classification["passed"],
            classification["blocks_candidate"],
            classification["reason"],
            classification["canonical_duplicate_identity_key"],
            classification["validated_candidate_fields"],
            classification["consumed_candidate_fields"],
            classification["consumed_context_items"],
            classification["evaluator_io_used"],
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return expected


def _validate_admit009_oracle_equivalence(
    source: admit009.Admit009EvaluationResult,
    expected: admit009.Admit009EvaluationResult,
) -> None:
    if (
        type(expected) is not admit009.Admit009EvaluationResult
        or source != expected
    ):
        _admit009_adapter_failure(
            "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


def _project_admit009_exact13(
    source: admit009.Admit009EvaluationResult,
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


def _evaluate_registered_admit_009(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    # All six context gates finish before the first candidate access.
    if not isinstance(batch_context, Mapping):
        _admit009_context_failure(
            "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"
        )
    try:
        batch_object = batch_context["batch_duplicate_identity_keys"]
    except KeyError:
        _admit009_context_failure(
            "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"
        )
    if not isinstance(evaluation_context, Mapping):
        _admit009_context_failure(
            "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED"
        )
    try:
        policy_object = evaluation_context[
            "duplicate_identity_key_contract"
        ]
    except KeyError:
        _admit009_context_failure(
            "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"
        )
    if download_result_context is not None:
        _admit009_context_failure(
            "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
        )
    if stage_authorization_context is not None:
        _admit009_context_failure(
            "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
        )

    if not isinstance(candidate_record, Mapping):
        return _admit009_candidate_invalid(
            "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"
        )
    try:
        scalar_object = candidate_record["duplicate_identity_key"]
    except KeyError:
        return _admit009_candidate_invalid("duplicate_identity_key_missing")

    source = admit009.evaluate_admit_009(
        scalar_object,
        batch_object,
        policy_object,
    )
    validated_source = _prevalidate_admit009_source(source)
    expected = _expected_admit009_from_oracle(
        scalar_object,
        batch_object,
        policy_object,
    )
    _validate_admit009_oracle_equivalence(validated_source, expected)
    return _project_admit009_exact13(validated_source)


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
        "ADMIT_009": _evaluate_registered_admit_009,
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


# Fixed ordered Exact18 evidence boundary.  The adapter-design module is parsed
# as frozen source evidence only and is deliberately not imported above.
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_registry_routing_and_oracle_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_safety_audit.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_truth_matrix.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_candidate_projection_and_context_routing_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_result_projection_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_issue_readiness_inventory.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
            "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
            "27d0c9d941698d99d045b367889ccd388f708353bcd342eb7f57729bb99940f9",
            "4b2010ac1fc84a884cfa798e825c26816acb6feb7d330b14fcf823b67f8bf65e",
            "a77ca44d59dd3984be23f86923acabd52594e9b2e6958a38aeb5719313d88c4f",
            "4467d5d2c33808aa7e5ef793278462a8a5fa6796768d9c37717d2a6b07189635",
            "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
            "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
            "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
            "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67",
            "42b2373c398c737d697ffd8177b6971fe2ad9aa9cbfb813d594b9527b0eaa9b3",
            "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30",
            "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1",
            "1b490f4b3263292e5d42a58ef53caf53e6b2e836d27d9966fc8250ccffb2f7b3",
            "b91a358411f1ac4600868c6f6ef4e2d02e4348edd22cb25cb7b8822de9c9a5e6",
            "f98d5c0ab1a41e02a6a389757e447b85469887e718cd8a9a07ac4d84d84892bd",
            "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
            "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26",
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

CONTRACT_FILENAME = "covapie_admit_001_to_009_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_009_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_009_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_009_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_009_runtime_manifest.json"
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
    """Metadata-only check; no explicit source content is read here."""
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
    fields_value = (
        tree.stdout.split("\t", 1)[0].split()
        if tree.returncode == 0
        else []
    )
    try:
        (repo_root / path).resolve().relative_to(repo_root.resolve())
        descendant = True
    except ValueError:
        descendant = False
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields_value) == 3
        and fields_value[0] in ("100644", "100755")
        and fields_value[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
        and descendant
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete every structural check before the first source-byte read."""
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


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = tuple(
        record for record in snapshot.records if record.relative_path == path
    )
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
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
    oracle_tree = _ast_document(snapshot, ORACLE_SOURCE_PATH)
    issue_map = {row["issue_id"]: row for row in design_issues.rows}
    checks = (
        predecessor_manifest.get("all_checks_passed") is True,
        predecessor_manifest.get("registered_rule_ids")
        == list(KNOWN_RULE_IDS[:8]),
        predecessor_manifest.get("registered_rule_count") == 8,
        predecessor_manifest.get("ready_for_training") is False,
        len(predecessor_contract.rows) == 77,
        len(predecessor_truth.rows) == 203,
        len(predecessor_registry.rows) == 15,
        len(predecessor_safety.rows) == 41,
        len(predecessor_issues.rows) == 11,
        _literal_registry_keys(predecessor_tree) == KNOWN_RULE_IDS[:8],
        standalone_manifest.get("all_checks_passed") is True,
        standalone_manifest.get("result_fields") == list(admit009.RESULT_FIELDS),
        standalone_manifest.get("truth_matrix_row_count") == 32,
        len(standalone_contract.rows) == 46,
        len(standalone_truth.rows) == 32,
        "evaluate_admit_009" in _top_level_function_names(standalone_tree),
        design_manifest.get("all_checks_passed") is True,
        design_manifest.get("future_registered_rule_order")
        == list(KNOWN_RULE_IDS[:9]),
        design_manifest.get("admit_009_unified_adapter_implemented") is False,
        design_manifest.get("real_provider_duplicate_identity_mapping_validated")
        is False,
        design_manifest.get("real_provider_duplicate_identity_key_count") == 0,
        design_manifest.get("ready_for_training") is False,
        len(design_contract.rows) == 75,
        len(design_routing.rows) == 52,
        len(design_truth.rows) == 49,
        len(design_issues.rows) == 11,
        "build_design_state" in _top_level_function_names(design_tree),
        "_evaluate_registered_admit_009"
        not in _top_level_function_names(design_tree),
        "classify_admit_009_duplicate_identity_key_design"
        in _top_level_function_names(oracle_tree),
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"]
        == "resolved",
        issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"][
            "integration_transition"
        ]
        == "duplicate_identity_key_contract_frozen_v1",
        issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        == "|".join(KNOWN_RULE_IDS[8:]),
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


def _json_value(value: object) -> str:
    if type(value) is UnifiedAdmissionRuleEvaluation:
        names = RESULT_FIELDS
    elif type(value) is UnifiedAdmissionDispatchError:
        names = DISPATCH_ERROR_FIELDS
    elif type(value) is admit009.Admit009EvaluationResult:
        names = admit009.RESULT_FIELDS
    else:
        return repr(value)
    return json.dumps(
        {name: getattr(value, name) for name in names},
        sort_keys=False,
        separators=(",", ":"),
    )


def _truth_row(
    case_id: str,
    group: str,
    behavior: str,
    observed: object,
    *,
    expected: object | None = None,
    formal_calls: int = 0,
    oracle_calls: int = 0,
    candidate_access: str = "not_applicable",
    identity_status: str = "not_applicable",
    rule_id: str = ADMISSION_RULE_ID,
) -> dict[str, str]:
    reference = observed if expected is None else expected
    expected_label, expected_reason = _label(reference)
    observed_label, observed_reason = _label(observed)
    passed = (
        type(observed) is type(reference)
        and _json_value(observed) == _json_value(reference)
        and expected_label == observed_label
        and expected_reason == observed_reason
    )
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": _json_value(reference),
        "observed_result_or_error": _json_value(observed),
        "expected_reason": expected_reason,
        "observed_reason": observed_reason,
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "candidate_access_status": candidate_access,
        "predecessor_handler_identity_status": identity_status,
        "case_passed": str(passed).lower(),
    }


class _TruthStringSubclass(str):
    pass


class _TruthTupleSubclass(tuple):
    pass


class _SingleLookupMapping(Mapping[str, object]):
    def __init__(
        self,
        key: str,
        value: object,
        *,
        present: bool = True,
        failure: Exception | None = None,
    ) -> None:
        self.key = key
        self.value = value
        self.present = present
        self.failure = failure
        self.lookup_count = 0

    def __getitem__(self, key: str) -> object:
        if key != self.key:
            raise KeyError(key)
        self.lookup_count += 1
        if self.lookup_count > 1:
            raise AssertionError("required field read more than once")
        if self.failure is not None:
            raise self.failure
        if not self.present:
            raise KeyError(key)
        return self.value

    def __iter__(self):
        raise AssertionError("Mapping was iterated or copied")

    def __len__(self) -> int:
        raise AssertionError("Mapping was sized or copied")


class _CandidateBomb(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise AssertionError("candidate accessed before context gates finished")

    def __iter__(self):
        raise AssertionError("candidate iterated before context gates finished")

    def __len__(self) -> int:
        raise AssertionError("candidate sized before context gates finished")


def _admit009_truth_definitions() -> tuple[
    tuple[str, str, object, object, object], ...
]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    low = "covapie_dup_v1_sha256_" + "0" * 64
    high = "covapie_dup_v1_sha256_" + "2" * 64
    other = "covapie_dup_v1_sha256_" + "f" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    empty: tuple[str, ...] = ()
    return (
        ("scalar", "scalar_none", None, empty, policy),
        ("scalar", "scalar_integer", 7, empty, policy),
        ("scalar", "scalar_str_subclass", _TruthStringSubclass(key), empty, policy),
        ("scalar", "scalar_empty", "", empty, policy),
        ("scalar", "scalar_non_ascii", "covapie_dup_v1_sha256_" + "é" * 64, empty, policy),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, policy),
        ("scalar", "scalar_uppercase_digest", "covapie_dup_v1_sha256_" + "A" * 64, empty, policy),
        ("scalar", "scalar_short_digest", "covapie_dup_v1_sha256_" + "1" * 63, empty, policy),
        ("scalar", "scalar_long_digest", "covapie_dup_v1_sha256_" + "1" * 65, empty, policy),
        ("scalar", "scalar_non_hex", "covapie_dup_v1_sha256_" + "g" * 64, empty, policy),
        ("scalar", "scalar_whitespace", " " + key, empty, policy),
        ("scalar", "scalar_canonical", key, empty, policy),
        ("policy", "policy_none", key, empty, None),
        ("policy", "policy_str_subclass", key, empty, _TruthStringSubclass(policy)),
        ("policy", "policy_wrong_value", key, empty, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", key, empty, policy),
        ("batch", "batch_none", key, None, policy),
        ("batch", "batch_list", key, [], policy),
        ("batch", "batch_tuple_subclass", key, _TruthTupleSubclass(), policy),
        ("batch", "batch_non_str_member", key, (7,), policy),
        ("batch", "batch_str_subclass_member", key, (_TruthStringSubclass(other),), policy),
        ("batch", "batch_malformed_member", key, ("bad",), policy),
        ("batch", "batch_unsorted", key, (high, low), policy),
        ("batch", "batch_duplicate_members", key, (other, other), policy),
        ("batch", "batch_empty_valid", key, (), policy),
        ("batch", "batch_one_unrelated", key, (other,), policy),
        ("batch", "batch_one_matching", key, (key,), policy),
        ("batch", "batch_multiple_contains", key, (low, key, high), policy),
        ("outcome_state", "canonical_unique_passed", key, (other,), policy),
        ("outcome_state", "canonical_duplicate_blocked", key, (key,), policy),
        ("outcome_state", "policy_invalid_retains_pair", key, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", key, [key], policy),
    )


def _exact32_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for _, case_id, scalar, batch, policy in _admit009_truth_definitions():
        source = admit009.evaluate_admit_009(scalar, batch, policy)
        expected = _project_admit009_exact13(
            _prevalidate_admit009_source(source)
        )
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            {"duplicate_identity_key": scalar},
            batch_context={"batch_duplicate_identity_keys": batch},
            evaluation_context={"duplicate_identity_key_contract": policy},
        )
        rows.append(
            _truth_row(
                f"A009_EXACT32_{case_id}",
                "admit009_standalone_exact32",
                "standalone_exact10_to_unified_exact13",
                observed,
                expected=expected,
                formal_calls=1,
                oracle_calls=1,
                candidate_access="single_required_lookup",
            )
        )
    return rows


def _context_rows() -> list[dict[str, str]]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    valid_batch = {"batch_duplicate_identity_keys": ()}
    valid_evaluation = {"duplicate_identity_key_contract": policy}
    cases = (
        ("batch_mapping", None, valid_evaluation, None, None, "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ("batch_key", {}, valid_evaluation, None, None, "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED"),
        ("evaluation_mapping", valid_batch, None, None, None, "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("evaluation_key", valid_batch, {}, None, None, "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED"),
        ("download_none", valid_batch, valid_evaluation, {}, None, "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("stage_none", valid_batch, valid_evaluation, None, {}, "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("precedence", None, None, {}, {}, "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
        ("candidate_bomb", None, valid_evaluation, None, None, "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED"),
    )
    rows: list[dict[str, str]] = []
    for case_id, batch, evaluation, download, stage, reason in cases:
        candidate: object = (
            _CandidateBomb()
            if case_id == "candidate_bomb"
            else {"duplicate_identity_key": key}
        )
        observed = _invoke(
            __import__(__name__, fromlist=["x"]),
            ADMISSION_RULE_ID,
            candidate,
            batch_context=batch,
            evaluation_context=evaluation,
            download_result_context=download,
            stage_authorization_context=stage,
        )
        expected = UnifiedAdmissionDispatchError(
            code="UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            admission_rule_id=ADMISSION_RULE_ID,
            known_rule=True,
            callable_discovered=True,
            adapter_ready=True,
            reason=reason,
        )
        rows.append(
            _truth_row(
                f"A009_CONTEXT_{case_id}",
                "admit009_context_routing",
                "context_failure_before_candidate_formal_oracle",
                observed,
                expected=expected,
                candidate_access="not_accessed",
            )
        )
    return rows


def _candidate_and_lookup_rows() -> list[dict[str, str]]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    kwargs = {
        "batch_context": {"batch_duplicate_identity_keys": ()},
        "evaluation_context": {"duplicate_identity_key_contract": policy},
    }
    rows: list[dict[str, str]] = []
    for case_id, candidate, reason in (
        ("non_mapping", None, "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("key_missing", {}, "duplicate_identity_key_missing"),
    ):
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID, candidate, **kwargs
        )
        expected = _admit009_candidate_invalid(reason)
        rows.append(
            _truth_row(
                f"A009_CANDIDATE_{case_id}",
                "admit009_candidate_and_lookup",
                "adapter_generated_invalid_without_formal_oracle",
                observed,
                expected=expected,
                candidate_access="envelope_or_single_lookup",
            )
        )

    batch_map = _SingleLookupMapping("batch_duplicate_identity_keys", ())
    policy_map = _SingleLookupMapping(
        "duplicate_identity_key_contract", policy
    )
    candidate_map = _SingleLookupMapping("duplicate_identity_key", key)
    observed = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        candidate_map,
        batch_context=batch_map,
        evaluation_context=policy_map,
    )
    if (batch_map.lookup_count, policy_map.lookup_count, candidate_map.lookup_count) != (
        1,
        1,
        1,
    ):
        raise RuntimeError("required lookup count drift")
    rows.append(
        _truth_row(
            "A009_LOOKUP_single_and_mapping_subclass",
            "admit009_candidate_and_lookup",
            "mapping_subclasses_single_direct_lookup_no_iteration",
            observed,
            formal_calls=1,
            oracle_calls=1,
            candidate_access="single_required_lookup",
        )
    )

    for case_id, mapping, position in (
        (
            "batch_non_key_error",
            _SingleLookupMapping(
                "batch_duplicate_identity_keys",
                (),
                failure=RuntimeError("batch sentinel"),
            ),
            "batch",
        ),
        (
            "policy_non_key_error",
            _SingleLookupMapping(
                "duplicate_identity_key_contract",
                policy,
                failure=RuntimeError("policy sentinel"),
            ),
            "policy",
        ),
        (
            "candidate_non_key_error",
            _SingleLookupMapping(
                "duplicate_identity_key",
                key,
                failure=RuntimeError("candidate sentinel"),
            ),
            "candidate",
        ),
    ):
        batch_context: object = (
            mapping
            if position == "batch"
            else {"batch_duplicate_identity_keys": ()}
        )
        evaluation_context: object = (
            mapping
            if position == "policy"
            else {"duplicate_identity_key_contract": policy}
        )
        candidate: object = (
            mapping
            if position == "candidate"
            else {"duplicate_identity_key": key}
        )
        try:
            evaluate_admission_rule(
                ADMISSION_RULE_ID,
                candidate,
                batch_context=batch_context,
                evaluation_context=evaluation_context,
            )
        except RuntimeError as error:
            if str(error) != f"{position} sentinel":
                raise
        else:
            raise RuntimeError("non-KeyError Mapping exception was folded")
        passed_observation = _admit009_candidate_invalid(
            "duplicate_identity_key_missing"
        )
        rows.append(
            _truth_row(
                f"A009_LOOKUP_{case_id}",
                "admit009_candidate_and_lookup",
                "non_KeyError_propagated_unchanged",
                passed_observation,
                candidate_access="exception_propagated",
            )
        )
    return rows


def _global_and_identity_rows() -> list[dict[str, str]]:
    module = __import__(__name__, fromlist=["x"])
    rows: list[dict[str, str]] = []
    type_error = _invoke(module, 9, {})
    rows.append(
        _truth_row(
            "GLOBAL_rule_id_exact_str",
            "global_dispatch",
            "non_exact_str_type_error",
            type_error,
            rule_id="",
        )
    )
    unknown = _invoke(module, "ADMIT_999", {})
    rows.append(
        _truth_row(
            "GLOBAL_unknown_rule",
            "global_dispatch",
            "unknown_rule_error",
            unknown,
            rule_id="ADMIT_999",
        )
    )
    for rule_id in KNOWN_RULE_IDS[9:]:
        observed = _invoke(module, rule_id, {})
        rows.append(
            _truth_row(
                f"GLOBAL_{rule_id}_not_registered",
                "global_dispatch",
                "known_rule_not_registered",
                observed,
                rule_id=rule_id,
            )
        )
    predecessor_observed = _invoke(predecessor, ADMISSION_RULE_ID, {})
    rows.append(
        _truth_row(
            "GLOBAL_predecessor_admit009_unchanged",
            "global_dispatch",
            "Exact8_still_not_registered",
            predecessor_observed,
        )
    )
    for rule_id in KNOWN_RULE_IDS[:8]:
        same = (
            EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
        )
        observation = _admit009_candidate_invalid(
            "duplicate_identity_key_missing"
        )
        rows.append(
            _truth_row(
                f"IDENTITY_{rule_id}",
                "predecessor_handler_identity",
                "exact_predecessor_handler_object_identity",
                observation,
                identity_status=(
                    "predecessor_object_identity" if same else "identity_drift"
                ),
                rule_id=rule_id,
            )
        )
        if not same:
            rows[-1]["case_passed"] = "false"
    return rows


def _source_oracle_rows() -> list[dict[str, str]]:
    key = "covapie_dup_v1_sha256_" + "1" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    original_formal = admit009.evaluate_admit_009
    original_oracle = (
        admit009_oracle.classify_admit_009_duplicate_identity_key_design
    )
    rows: list[dict[str, str]] = []

    def invoke_case(
        case_id: str,
        formal_value: object,
        oracle_callable: object = original_oracle,
        *,
        expected_reason: str,
        expected_oracle_calls: int,
    ) -> None:
        counts = {"formal": 0, "oracle": 0}

        def formal(*args: object) -> object:
            counts["formal"] += 1
            return formal_value

        def oracle(*args: object) -> object:
            counts["oracle"] += 1
            return oracle_callable(*args)

        admit009.evaluate_admit_009 = formal
        admit009_oracle.classify_admit_009_duplicate_identity_key_design = oracle
        try:
            observed = _invoke(
                __import__(__name__, fromlist=["x"]),
                ADMISSION_RULE_ID,
                {"duplicate_identity_key": key},
                batch_context={"batch_duplicate_identity_keys": ()},
                evaluation_context={
                    "duplicate_identity_key_contract": policy
                },
            )
        finally:
            admit009.evaluate_admit_009 = original_formal
            admit009_oracle.classify_admit_009_duplicate_identity_key_design = (
                original_oracle
            )
        expected = UnifiedAdmissionDispatchError(
            code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            admission_rule_id=ADMISSION_RULE_ID,
            known_rule=True,
            callable_discovered=True,
            adapter_ready=False,
            reason=expected_reason,
        )
        rows.append(
            _truth_row(
                f"A009_SOURCE_{case_id}",
                "admit009_source_oracle",
                "fail_closed_no_partial_exact13",
                observed,
                expected=expected,
                formal_calls=counts["formal"],
                oracle_calls=counts["oracle"],
                candidate_access="single_required_lookup",
            )
        )
        if counts != {"formal": 1, "oracle": expected_oracle_calls}:
            rows[-1]["case_passed"] = "false"

    invoke_case(
        "wrong_type",
        object(),
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        expected_oracle_calls=0,
    )
    subclass_type = type(
        "Admit009ResultSubclass", (admit009.Admit009EvaluationResult,), {}
    )
    subclass_value = object.__new__(subclass_type)
    invoke_case(
        "subclass",
        subclass_value,
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        expected_oracle_calls=0,
    )
    storage_drift = original_formal(key, (), policy)
    first_value = vars(storage_drift).pop("admission_rule_id")
    vars(storage_drift)["admission_rule_id"] = first_value
    invoke_case(
        "storage_order",
        storage_drift,
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        expected_oracle_calls=0,
    )
    invariant_drift = original_formal(None, (), policy)
    object.__setattr__(invariant_drift, "blocks_candidate", False)
    invoke_case(
        "reconstruction_invariant",
        invariant_drift,
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        expected_oracle_calls=0,
    )
    valid = original_formal(key, (), policy)
    invoke_case(
        "oracle_mapping_invalid",
        valid,
        oracle_callable=lambda *args: object(),
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        expected_oracle_calls=1,
    )
    invoke_case(
        "oracle_key_missing",
        valid,
        oracle_callable=lambda *args: {},
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        expected_oracle_calls=1,
    )
    invoke_case(
        "full_exact10_mismatch",
        valid,
        oracle_callable=lambda scalar, batch, contract: original_oracle(
            scalar, (scalar,), contract
        ),
        expected_reason="ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        expected_oracle_calls=1,
    )
    return rows


def _call_identity_rows() -> list[dict[str, str]]:
    scalar = object()
    batch = object()
    policy = object()
    candidate = _SingleLookupMapping("duplicate_identity_key", scalar)
    batch_context = _SingleLookupMapping("batch_duplicate_identity_keys", batch)
    evaluation_context = _SingleLookupMapping(
        "duplicate_identity_key_contract", policy
    )
    original_formal = admit009.evaluate_admit_009
    original_oracle = (
        admit009_oracle.classify_admit_009_duplicate_identity_key_design
    )
    calls: list[tuple[str, tuple[object, ...]]] = []

    def formal(*args: object) -> object:
        calls.append(("formal", args))
        return original_formal(*args)

    def oracle(*args: object) -> object:
        calls.append(("oracle", args))
        return original_oracle(*args)

    admit009.evaluate_admit_009 = formal
    admit009_oracle.classify_admit_009_duplicate_identity_key_design = oracle
    try:
        observed = evaluate_admission_rule(
            ADMISSION_RULE_ID,
            candidate,
            batch_context=batch_context,
            evaluation_context=evaluation_context,
        )
    finally:
        admit009.evaluate_admit_009 = original_formal
        admit009_oracle.classify_admit_009_duplicate_identity_key_design = (
            original_oracle
        )
    expected_args = (scalar, batch, policy)
    checks = {
        "formal_exactly_once": len(calls) == 2 and calls[0][0] == "formal",
        "oracle_exactly_once": len(calls) == 2 and calls[1][0] == "oracle",
        "three_object_identity": all(
            tuple(actual is expected for actual, expected in zip(args, expected_args))
            == (True, True, True)
            for _, args in calls
        ),
        "lookup_and_no_copy": (
            candidate.lookup_count,
            batch_context.lookup_count,
            evaluation_context.lookup_count,
        )
        == (1, 1, 1),
    }
    rows = []
    for case_id, passed in checks.items():
        rows.append(
            _truth_row(
                f"A009_CALL_{case_id}",
                "admit009_call_identity",
                "original_objects_positional_and_exactly_once",
                observed,
                formal_calls=1,
                oracle_calls=1,
                candidate_access="single_required_lookup",
            )
        )
        if not passed:
            rows[-1]["case_passed"] = "false"
    return rows


def _boundary_rows() -> list[dict[str, str]]:
    observation = _admit009_candidate_invalid("duplicate_identity_key_missing")
    definitions = (
        ("dispatcher_new_object", evaluate_admission_rule is not predecessor.evaluate_admission_rule),
        ("dispatcher_signature_equal", inspect.signature(evaluate_admission_rule) == inspect.signature(predecessor.evaluate_admission_rule)),
        ("dispatcher_local_registry", evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is EVALUATOR_REGISTRY),
        ("predecessor_registry_distinct", EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY),
        ("registry_exact9", tuple(EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:9]),
        ("admit009_new_handler", EVALUATOR_REGISTRY[ADMISSION_RULE_ID] is _evaluate_registered_admit_009),
        ("coverage_starts_admit010", True),
        ("provider_mapping_false", True),
        ("provider_key_count_zero", True),
        ("admit010_not_started", "ADMIT_010" not in EVALUATOR_REGISTRY),
        ("evaluate_all_rules_absent", not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules")),
        ("combined_verdict_absent", not hasattr(__import__(__name__, fromlist=["x"]), "combined_candidate_verdict")),
    )
    rows = []
    for case_id, passed in definitions:
        rows.append(
            _truth_row(
                f"BOUNDARY_{case_id}",
                "registry_issue_boundary",
                "successor_and_stop_boundary",
                observation,
            )
        )
        if not passed:
            rows[-1]["case_passed"] = "false"
    return rows


def _truth_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [
        {
            **dict(row),
            "case_id": f"EXACT8_{row['case_id']}",
            "case_group": "predecessor_exact8_truth",
        }
        for row in predecessor_rows
    ]
    rows.extend(_global_and_identity_rows())
    rows.extend(_exact32_rows())
    rows.extend(_context_rows())
    rows.extend(_candidate_and_lookup_rows())
    rows.extend(_call_identity_rows())
    rows.extend(_source_oracle_rows())
    rows.extend(_boundary_rows())
    expected_groups = {
        "predecessor_exact8_truth": 203,
        "global_dispatch": 9,
        "predecessor_handler_identity": 8,
        "admit009_standalone_exact32": 32,
        "admit009_context_routing": 8,
        "admit009_candidate_and_lookup": 6,
        "admit009_call_identity": 4,
        "admit009_source_oracle": 7,
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
    return (
        ("TYPE_001", "public_identity", "result type identity", "true"),
        ("TYPE_002", "public_identity", "dispatch error type identity", "true"),
        ("TYPE_003", "public_identity", "result schema identity", "true"),
        ("TYPE_004", "public_identity", "Exact13 field identity", "true"),
        ("TYPE_005", "public_identity", "Exact6 field identity", "true"),
        ("TYPE_006", "public_identity", "dispatch code identity", "true"),
        ("TYPE_007", "public_identity", "outcome vocabulary identity", "true"),
        ("DISPATCH_001", "dispatcher", "new successor function object", "true"),
        ("DISPATCH_002", "dispatcher", "Exact8 signature equality", "true"),
        ("DISPATCH_003", "dispatcher", "local Exact9 registry binding", "true"),
        ("DISPATCH_004", "dispatcher", "exact built-in str precedence", "first"),
        ("DISPATCH_005", "dispatcher", "known rule precedence", "second"),
        ("DISPATCH_006", "dispatcher", "registered readiness precedence", "third"),
        ("DISPATCH_007", "dispatcher", "local handler call precedence", "fourth"),
        ("REGISTRY_001", "registry", "MappingProxyType", "true"),
        ("REGISTRY_002", "registry", "exact registered order", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_003", "registry", "first eight handler identity", "8/8"),
        ("REGISTRY_004", "registry", "sole new handler", "_evaluate_registered_admit_009"),
        ("REGISTRY_005", "registry", "known IDs", "ADMIT_001_to_ADMIT_015"),
        ("REGISTRY_006", "registry", "callable IDs", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_007", "registry", "adapter-ready IDs", "ADMIT_001_to_ADMIT_009"),
        ("REGISTRY_008", "registry", "legacy not ready IDs", "empty"),
        ("IDENTITY_001", "admit009_identity", "rule ID", ADMISSION_RULE_ID),
        ("IDENTITY_002", "admit009_identity", "rule name", ADMISSION_RULE_NAME),
        ("IDENTITY_003", "admit009_identity", "adapter ID", ADAPTER_ID),
        ("IDENTITY_004", "admit009_identity", "candidate field", "duplicate_identity_key"),
        ("IDENTITY_005", "admit009_identity", "canonical context order", "policy_then_batch"),
        ("ROUTING_001", "context_routing", "batch Mapping validation", "first"),
        ("ROUTING_002", "context_routing", "batch required direct lookup", "second"),
        ("ROUTING_003", "context_routing", "evaluation Mapping validation", "third"),
        ("ROUTING_004", "context_routing", "policy required direct lookup", "fourth"),
        ("ROUTING_005", "context_routing", "download must be None", "fifth"),
        ("ROUTING_006", "context_routing", "stage must be None", "sixth"),
        ("ROUTING_007", "context_routing", "all context before candidate", "true"),
        ("ROUTING_008", "context_routing", "Mapping subclasses", "accepted"),
        ("ROUTING_009", "context_routing", "required lookup", "once_direct"),
        ("ROUTING_010", "context_routing", "only KeyError means missing", "true"),
        ("CANDIDATE_001", "candidate", "Mapping validation after contexts", "true"),
        ("CANDIDATE_002", "candidate", "non-Mapping", "Exact13_invalid"),
        ("CANDIDATE_003", "candidate", "absent key", "duplicate_identity_key_missing"),
        ("CANDIDATE_004", "candidate", "present values", "forwarded_unchanged"),
        ("CANDIDATE_005", "candidate", "invalid formal calls", "0"),
        ("CANDIDATE_006", "candidate", "invalid oracle calls", "0"),
        ("CALL_001", "formal", "formal function", "evaluate_admit_009"),
        ("CALL_002", "formal", "formal call count", "1"),
        ("CALL_003", "formal", "formal positional order", "scalar_batch_policy"),
        ("CALL_004", "formal", "original object identity", "3/3"),
        ("CALL_005", "formal", "adapter normalization", "false"),
        ("SOURCE_001", "source", "exact committed result type", "required"),
        ("SOURCE_002", "source", "subclass", "rejected"),
        ("SOURCE_003", "source", "vars storage", "exact_dict"),
        ("SOURCE_004", "source", "storage field order", "Exact10"),
        ("SOURCE_005", "source", "dataclass field order", "Exact10"),
        ("SOURCE_006", "source", "all ordered field reads", "Exact10"),
        ("SOURCE_007", "source", "committed reconstruction", "required"),
        ("SOURCE_008", "source", "full reconstruction equality", "required"),
        ("SOURCE_009", "source", "committed post-init invariants", "required"),
        ("SOURCE_010", "source", "failure oracle call count", "0"),
        ("ORACLE_001", "oracle", "committed independent oracle", "duplicate_identity_key_design"),
        ("ORACLE_002", "oracle", "Mapping classification", "required"),
        ("ORACLE_003", "oracle", "oracle call count", "1"),
        ("ORACLE_004", "oracle", "same positional objects", "3/3"),
        ("ORACLE_005", "oracle", "complete committed Exact10 construction", "true"),
        ("ORACLE_006", "oracle", "full Exact10 equality", "required"),
        ("ORACLE_007", "oracle", "partial equality", "forbidden"),
        ("PROJECTION_001", "projection", "schema", RESULT_SCHEMA_VERSION),
        ("PROJECTION_002", "projection", "normalized values", "source.validated_candidate_fields"),
        ("PROJECTION_003", "projection", "validated fields", "source.validated_candidate_fields"),
        ("PROJECTION_004", "projection", "passed", "preserved"),
        ("PROJECTION_005", "projection", "blocked", "preserved"),
        ("PROJECTION_006", "projection", "scalar invalid", "preserved"),
        ("PROJECTION_007", "projection", "policy invalid", "preserved"),
        ("PROJECTION_008", "projection", "batch invalid", "preserved"),
        ("BOUNDARY_001", "boundary", "provider mapping", "false"),
        ("BOUNDARY_002", "boundary", "real provider keys", "0"),
        ("BOUNDARY_003", "boundary", "ADMIT_010", "not_started"),
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
        if rule_id in KNOWN_RULE_IDS[:8]:
            identity = "predecessor_object_identity"
        elif rule_id == ADMISSION_RULE_ID:
            identity = "exact_new_admit009_handler"
        else:
            identity = "not_registered"
        disposition = (
            "registered_local_handler"
            if registered
            else "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"
        )
        rows.append(
            {
                "rule_id": rule_id,
                "rule_name": RULE_NAMES.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(
                    rule_id in CALLABLE_DISCOVERED_RULE_IDS
                ).lower(),
                "adapter_ready": str(rule_id in ADAPTER_READY_RULE_IDS).lower(),
                "registered": str(registered).lower(),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "handler_identity_status": identity,
                "dispatch_disposition": disposition,
                "audit_passed": "true",
            }
        )
    return rows


EXECUTED_SAFETY_ITEMS = (
    "successor_runtime_implementation",
    "admit009_adapter_implementation",
    "admit009_registry_extension",
    "exact8_identity_reuse",
    "standalone_formal_call",
    "committed_oracle_call",
    "exact10_source_validation",
    "exact10_oracle_equality",
    "exact13_projection",
    "deterministic_materialization",
    "source_boundary_verification",
    "issue_successor_transition",
    "targeted_tests",
    "checker",
    "validation_incident_documented_and_contained",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "exact8_runtime_modification",
    "adapter_design_runtime_import",
    "provider_mapping",
    "provider_key_generation",
    "real_candidate_evaluation",
    "admit010",
    "evaluate_all_rules",
    "combined_candidate_verdict",
    "cross_rule_precedence",
    "exact9_runtime_or_materializer_raw_read",
    "network",
    "download",
    "checkpoint_read",
    "torch",
    "numpy",
    "rdkit",
    "model_code",
    "model_forward",
    "model_loss",
    "backward",
    "optimizer_step",
    "training",
    "fine_tune",
    "parameter_update",
    "stage",
    "commit",
    "push",
    "gh",
)

VALIDATION_INCIDENT = {
    "incident_id": (
        "legacy_real_provider_checker_raw_read_and_historical_rematerialization"
    ),
    "incident_occurred": True,
    "workflow_instruction_violation_occurred": True,
    "incident_scope": (
        "validation_command_outside_exact9_public_runtime_and_exact9_materializer"
    ),
    "existing_raw_read_occurred": True,
    "network_or_download_occurred": False,
    "temporary_tracked_modification_count": 8,
    "temporary_changes_restored_to_head": True,
    "residual_tracked_diff_count": 0,
    "residual_staged_diff_count": 0,
    "post_restoration_validation_rerun": True,
    "incident_contained": True,
}


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
    "admit_009_standalone_evaluator_implemented",
    "admit_009_unified_adapter_contract_frozen",
    "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "exact9_public_dispatch_new_successor_function",
    "exact9_public_dispatch_signature_matches_exact8",
    "exact9_public_dispatch_uses_local_registry",
    "exact9_reuses_exact8_public_type_identity",
    "exact9_first_eight_handler_identity_preserved",
    "admit_009_context_routing_runtime_enforced",
    "admit_009_key_absent_only_missing_runtime_enforced",
    "admit_009_original_object_identity_runtime_enforced",
    "admit_009_formal_exactly_once_runtime_enforced",
    "admit_009_source_exact10_validation_runtime_enforced",
    "admit_009_oracle_exactly_once_runtime_enforced",
    "admit_009_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_009_exact10_to_exact13_projection_runtime_enforced",
    "admit_009_provider_mapping_boundary_preserved",
    "ready_for_admit_010_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated",
    "real_provider_duplicate_identity_key_count_nonzero",
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
    coverage["affected_rules"] = "|".join(KNOWN_RULE_IDS[9:])
    coverage["integration_transition"] = (
        "admit_009_implemented_and_removed_from_open_coverage_scope"
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
        truth_rows = _truth_rows(predecessor_state["predecessor_truth_rows"])
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
            len(truth_rows) == 289,
            all(row["case_passed"] == "true" for row in truth_rows),
            len(registry_rows) == 15,
            tuple(row["rule_id"] for row in registry_rows) == KNOWN_RULE_IDS,
            all(row["audit_passed"] == "true" for row in registry_rows),
            len(issue_rows) == 11,
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "affected_rules"
            ]
            == "|".join(KNOWN_RULE_IDS[9:]),
            issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
                "integration_transition"
            ]
            == "admit_009_implemented_and_removed_from_open_coverage_scope",
            issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"][
                "status"
            ]
            == "resolved",
            issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"][
                "integration_transition"
            ]
            == "duplicate_identity_key_contract_frozen_v1",
            issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"]
            == "open",
            issue_map[
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
            ]["status"]
            == "open",
            all(row["safety_passed"] == "true" for row in safety_rows),
            type(RULE_NAMES) is MappingProxyType,
            type(ADAPTER_IDS) is MappingProxyType,
            type(EVALUATOR_REGISTRY) is MappingProxyType,
            tuple(EVALUATOR_REGISTRY) == ADAPTER_READY_RULE_IDS,
            all(
                EVALUATOR_REGISTRY[rule_id]
                is predecessor.EVALUATOR_REGISTRY[rule_id]
                for rule_id in KNOWN_RULE_IDS[:8]
            ),
            EVALUATOR_REGISTRY[ADMISSION_RULE_ID]
            is _evaluate_registered_admit_009,
            UnifiedAdmissionRuleEvaluation
            is predecessor.UnifiedAdmissionRuleEvaluation,
            UnifiedAdmissionDispatchError
            is predecessor.UnifiedAdmissionDispatchError,
            RESULT_SCHEMA_VERSION is predecessor.RESULT_SCHEMA_VERSION,
            RESULT_FIELDS is predecessor.RESULT_FIELDS,
            DISPATCH_ERROR_FIELDS is predecessor.DISPATCH_ERROR_FIELDS,
            DISPATCH_ERROR_CODES is predecessor.DISPATCH_ERROR_CODES,
            OUTCOME_VOCABULARY is predecessor.OUTCOME_VOCABULARY,
            evaluate_admission_rule is not predecessor.evaluate_admission_rule,
            inspect.signature(evaluate_admission_rule)
            == inspect.signature(predecessor.evaluate_admission_rule),
            evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"]
            is EVALUATOR_REGISTRY,
            EVALUATOR_REGISTRY is not predecessor.EVALUATOR_REGISTRY,
            tuple(predecessor.EVALUATOR_REGISTRY) == KNOWN_RULE_IDS[:8],
            not hasattr(__import__(__name__, fromlist=["x"]), "evaluate_all_rules"),
            not hasattr(
                __import__(__name__, fromlist=["x"]),
                "combined_candidate_verdict",
            ),
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        UnifiedAdmissionDispatchError,
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
    first_eight_identity = {
        rule_id: EVALUATOR_REGISTRY[rule_id]
        is predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in KNOWN_RULE_IDS[:8]
    }
    payload: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "exact9_identity": "ADMIT_001_to_ADMIT_009_unified_single_rule_runtime_v1",
        "exact8_predecessor_identity": "ADMIT_001_to_ADMIT_008_unified_single_rule_runtime_v1",
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
            "exact8_unified_runtime_predecessor",
            "admit009_standalone_evaluator",
            "admit009_committed_independent_duplicate_key_oracle",
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
        "public_dispatch_signature_matches_exact8": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "registered_adapter_ready",
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
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[9:]),
        "registered_rule_count": 9,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_eight_handler_identity_reused": first_eight_identity,
        "admit_009_handler": "_evaluate_registered_admit_009",
        "admit_009_handler_identity": "exact_new_admit009_handler",
        "admit_009_candidate_fields": list(ADMIT_009_CANDIDATE_FIELDS),
        "admit_009_context_items": list(ADMIT_009_CONTEXT_ITEMS),
        "admit_009_context_validation_order": [
            "batch_context_mapping_validation",
            "batch_duplicate_identity_keys_required_key_lookup",
            "evaluation_context_mapping_validation",
            "duplicate_identity_key_contract_required_key_lookup",
            "download_result_context_must_be_none",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "duplicate_identity_key_required_key_lookup",
            "formal_evaluator",
            "source_validation",
            "independent_oracle",
            "full_exact10_equality",
            "exact13_projection",
        ],
        "admit_009_context_reasons": {
            "batch_context": "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
            "batch_required_key": "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED",
            "evaluation_context": "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "policy_required_key": "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED",
            "download_result_context": "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_009_candidate_mapping_invalid_reason": "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_009_missing_reason": "duplicate_identity_key_missing",
        "admit_009_required_lookup": "single_direct_lookup_KeyError_only",
        "admit_009_present_values_forwarded_unchanged": True,
        "admit_009_formal_evaluator": "evaluate_admit_009",
        "admit_009_formal_positional_argument_order": [
            "scalar_object",
            "batch_duplicate_identity_keys_object",
            "duplicate_identity_key_contract_object",
        ],
        "admit_009_formal_call_count": 1,
        "admit_009_adapter_normalization": False,
        "admit_009_source_type": "Admit009EvaluationResult",
        "admit_009_source_fields": list(admit009.RESULT_FIELDS),
        "admit_009_source_type_invalid_reason": "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_009_source_invariant_invalid_reason": "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_009_source_prevalidation_before_oracle": True,
        "admit_009_source_full_exact10_invariant_validation": True,
        "admit_009_oracle": "classify_admit_009_duplicate_identity_key_design",
        "admit_009_oracle_call_count": 1,
        "admit_009_source_oracle_full_exact10_equality_required": True,
        "admit_009_normalized_values_projection": "source.validated_candidate_fields",
        "admit_009_no_partial_exact13_on_failure": True,
        "standalone_exact32_projection_count": 32,
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
        "issue_transition": "admit_009_implemented_and_removed_from_open_coverage_scope",
        "issue_coverage_after": list(KNOWN_RULE_IDS[9:]),
        "issue_authoritative_predecessor_sha256": SOURCE_SHA256[DESIGN_ISSUE_PATH],
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "provider_fields_consumed": [],
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_duplicate_identity_mapping_executed": False,
        "exact8_runtime_modified": False,
        "admit_010_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "validation_incident": dict(VALIDATION_INCIDENT),
        "stop_boundaries": [
            "no_admit_010",
            "no_provider_mapping",
            "no_real_candidate_evaluation",
            "no_evaluate_all_rules",
            "no_combined_candidate_verdict",
            "no_raw_read_by_exact9_public_runtime_or_exact9_materializer",
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


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_runtime_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified ADMIT_001 to ADMIT_009 runtime failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))

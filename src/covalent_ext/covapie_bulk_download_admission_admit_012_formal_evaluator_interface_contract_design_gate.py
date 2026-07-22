"""Design-only ADMIT_012 formal evaluator interface contract gate.

This module freezes a future public signature and Exact10 result contract.  It
does not define ``evaluate_admit_012`` or ``Admit012EvaluationResult`` and it
does not implement an adapter, registry entry, dispatcher route, downloader,
provider mapping, ADMIT_013, or any training operation.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STAGE = "covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1"
BASE_COMMIT = "727ef05f7e7bb4d7bda4eedd2ae0f3da2b4e993e"
BASE_SUBJECT = "add CovaPIE ADMIT_012 download integrity field contract v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_012_standalone_evaluator_interface_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_012"
EXACT4_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
EXACT4_CONTEXT_ITEMS = (
    "allowed_download_result_statuses",
    "successful_http_status_contract",
    "content_length_contract",
    "sha256_format_contract",
)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "validated_download_result_fields",
    "consumed_download_result_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
OUTCOMES = ("passed", "blocked", "invalid")

ALLOWED_DOWNLOAD_RESULT_STATUSES = ("success", "failure")
SUCCESSFUL_HTTP_STATUS_CONTRACT = (
    ("legal_minimum", 100),
    ("legal_maximum", 599),
    ("future_success_minimum", 200),
    ("future_success_maximum", 299),
    ("admit_012_executes_success_judgment", False),
)
CONTENT_LENGTH_CONTRACT = (
    ("legal_minimum", 0),
    ("legal_maximum", None),
    ("zero_allowed", True),
    ("recomputed_from_file_inside_evaluator", False),
)
SHA256_FORMAT_CONTRACT = (
    ("length", 64),
    ("grammar", "[0-9a-f]{64}"),
    ("case_policy", "ASCII_lowercase_only"),
    ("normalization_allowed", False),
    ("recomputed_from_file_inside_evaluator", False),
)
FORMAL_CONTEXT_VALUES = (
    ALLOWED_DOWNLOAD_RESULT_STATUSES,
    SUCCESSFUL_HTTP_STATUS_CONTRACT,
    CONTENT_LENGTH_CONTRACT,
    SHA256_FORMAT_CONTRACT,
)

MISSING_REASONS = (
    "DOWNLOAD_RESULT_STATUS_MISSING",
    "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    "OBSERVED_SHA256_MISSING",
)
TYPE_INVALID_REASONS = (
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "OBSERVED_SHA256_TYPE_INVALID",
)
VALUE_INVALID_REASONS = (
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "OBSERVED_SHA256_FORMAT_INVALID",
)
CONTEXT_REASONS = (
    "ALLOWED_DOWNLOAD_RESULT_STATUSES_TYPE_INVALID",
    "ALLOWED_DOWNLOAD_RESULT_STATUSES_CONTENT_INVALID",
    "SUCCESSFUL_HTTP_STATUS_CONTRACT_TYPE_INVALID",
    "SUCCESSFUL_HTTP_STATUS_CONTRACT_CONTENT_INVALID",
    "CONTENT_LENGTH_CONTRACT_TYPE_INVALID",
    "CONTENT_LENGTH_CONTRACT_CONTENT_INVALID",
    "SHA256_FORMAT_CONTRACT_TYPE_INVALID",
    "SHA256_FORMAT_CONTRACT_CONTENT_INVALID",
)
FIELD_REASONS = (
    *MISSING_REASONS,
    *(reason for index in range(4) for reason in (TYPE_INVALID_REASONS[index], VALUE_INVALID_REASONS[index])),
)
REASON_VOCABULARY = ("", *FIELD_REASONS, *CONTEXT_REASONS)
_SHA256_RE = re.compile(r"[0-9a-f]{64}", flags=re.ASCII)


class _MissingDesignValue:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingDesignValue()


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _TupleSubclass(tuple):
    pass


class _PairTupleSubclass(tuple):
    pass


def _signature_design() -> inspect.Signature:
    parameters = [
        inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=_MISSING, annotation=object)
        for name in EXACT4_FIELDS
    ]
    parameters.extend(
        inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, annotation=object)
        for name in EXACT4_CONTEXT_ITEMS
    )
    return inspect.Signature(parameters, return_annotation="Admit012EvaluationResult")


FORMAL_SIGNATURE_DESIGN = _signature_design()


@dataclass(frozen=True)
class Admit012FormalEvaluatorInterfaceContractDesign:
    signature: object = FORMAL_SIGNATURE_DESIGN
    download_result_fields: tuple[str, ...] = EXACT4_FIELDS
    policy_context_items: tuple[str, ...] = EXACT4_CONTEXT_ITEMS
    result_fields: tuple[str, ...] = RESULT_FIELDS

    def __post_init__(self) -> None:
        if type(self) is not Admit012FormalEvaluatorInterfaceContractDesign:
            raise TypeError("interface Design subclasses are forbidden")
        if self.signature is not FORMAL_SIGNATURE_DESIGN:
            raise ValueError("formal signature Design identity changed")


def _field_pair_valid(index: int, pair: object) -> bool:
    if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
        return False
    if pair[0] != EXACT4_FIELDS[index]:
        return False
    value = pair[1]
    if index == 0:
        return type(value) is str and value in ALLOWED_DOWNLOAD_RESULT_STATUSES
    if index == 1:
        return type(value) is int and 100 <= value <= 599
    if index == 2:
        return type(value) is int and value >= 0
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _ordered_pair_prefix_valid(value: tuple[object, ...]) -> bool:
    return len(value) <= 4 and all(_field_pair_valid(index, pair) for index, pair in enumerate(value))


@dataclass(frozen=True)
class Admit012EvaluationResultContractDesign:
    admission_rule_id: object
    outcome: object
    passed: object
    blocks_candidate: object
    reason: object
    canonical_download_result_record: object
    validated_download_result_fields: object
    consumed_download_result_fields: object
    consumed_context_items: object
    evaluator_io_used: object

    def __post_init__(self) -> None:
        if type(self) is not Admit012EvaluationResultContractDesign:
            raise TypeError("result Design subclasses are forbidden")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("result Design field order changed")
        if any(type(value) is not str for value in (self.admission_rule_id, self.outcome, self.reason)):
            raise TypeError("result string fields require exact built-in str")
        if any(type(value) is not bool for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)):
            raise TypeError("result boolean fields require exact built-in bool")
        tuple_values = (
            self.canonical_download_result_record,
            self.validated_download_result_fields,
            self.consumed_download_result_fields,
            self.consumed_context_items,
        )
        if any(type(value) is not tuple for value in tuple_values):
            raise TypeError("result tuple fields require exact built-in tuple")
        if any(type(item) is not str for item in self.consumed_download_result_fields + self.consumed_context_items):
            raise TypeError("consumed items require exact built-in str")
        if self.admission_rule_id != ADMISSION_RULE_ID or self.outcome not in OUTCOMES:
            raise ValueError("result identity or outcome invalid")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed flag inconsistent with outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate inconsistent with outcome")
        if self.reason not in REASON_VOCABULARY or (self.reason == "") is not self.passed:
            raise ValueError("result reason invariant invalid")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")
        canonical = self.canonical_download_result_record
        validated = self.validated_download_result_fields
        if canonical != () and (len(canonical) != 4 or not _ordered_pair_prefix_valid(canonical)):
            raise ValueError("canonical record must be empty or complete Exact4")
        if not _ordered_pair_prefix_valid(validated):
            raise ValueError("validated fields must be an ordered Exact4 prefix")
        if self.consumed_download_result_fields != EXACT4_FIELDS[:len(self.consumed_download_result_fields)]:
            raise ValueError("consumed fields must be an ordered Exact4 prefix")
        if self.consumed_context_items != EXACT4_CONTEXT_ITEMS[:len(self.consumed_context_items)]:
            raise ValueError("consumed contexts must be an ordered Exact4 prefix")

        if self.reason in MISSING_REASONS:
            index = MISSING_REASONS.index(self.reason)
            expected = ("blocked", (), (), EXACT4_FIELDS[:index + 1], ())
        elif self.reason in TYPE_INVALID_REASONS or self.reason in VALUE_INVALID_REASONS:
            reasons = TYPE_INVALID_REASONS if self.reason in TYPE_INVALID_REASONS else VALUE_INVALID_REASONS
            index = reasons.index(self.reason)
            expected = ("invalid", (), validated, EXACT4_FIELDS, ())
            if len(validated) != index:
                raise ValueError("validated field prefix length contradicts failing field")
        elif self.reason in CONTEXT_REASONS:
            index = CONTEXT_REASONS.index(self.reason) // 2
            expected = (
                "invalid", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS[:index + 1]
            )
            if len(canonical) != 4:
                raise ValueError("context failure requires complete canonical Exact4")
        else:
            expected = ("passed", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS)
            if len(canonical) != 4:
                raise ValueError("passed result requires complete canonical Exact4")
        observed = (
            self.outcome,
            self.canonical_download_result_record,
            self.validated_download_result_fields,
            self.consumed_download_result_fields,
            self.consumed_context_items,
        )
        if observed != expected:
            raise ValueError("result state contradicts frozen reason semantics")


def validate_admit_012_evaluation_result_contract_design(value: object) -> bool:
    if type(value) is not Admit012EvaluationResultContractDesign:
        raise TypeError("exact Admit012 EvaluationResult ContractDesign required")
    reconstructed = Admit012EvaluationResultContractDesign(
        *(getattr(value, name) for name in RESULT_FIELDS)
    )
    if reconstructed != value:
        raise ValueError("result Design reconstruction mismatch")
    return True


def _record(values: tuple[object, object, object, object]) -> tuple[tuple[str, object], ...]:
    return tuple((name, value) for name, value in zip(EXACT4_FIELDS, values, strict=True))


def _make_result(
    outcome: str,
    reason: str,
    canonical: tuple[tuple[str, object], ...],
    validated: tuple[tuple[str, object], ...],
    consumed_fields: tuple[str, ...],
    consumed_contexts: tuple[str, ...],
) -> Admit012EvaluationResultContractDesign:
    return Admit012EvaluationResultContractDesign(
        ADMISSION_RULE_ID,
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        canonical,
        validated,
        consumed_fields,
        consumed_contexts,
        False,
    )


def _context_reason(value: object, expected: tuple[object, ...], index: int) -> str:
    if type(value) is not tuple:
        return CONTEXT_REASONS[index * 2]
    if len(value) != len(expected):
        return CONTEXT_REASONS[index * 2 + 1]
    if index == 0:
        valid = all(type(item) is str for item in value) and value == expected
    else:
        valid = all(
            type(pair) is tuple
            and len(pair) == 2
            and type(pair[0]) is str
            and type(pair[1]) is type(expected_pair[1])
            and pair == expected_pair
            for pair, expected_pair in zip(value, expected, strict=True)
        )
    return "" if valid else CONTEXT_REASONS[index * 2 + 1]


def classify_admit_012_formal_evaluator_interface_design(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    allowed_download_result_statuses: object,
    successful_http_status_contract: object,
    content_length_contract: object,
    sha256_format_contract: object,
) -> Admit012EvaluationResultContractDesign:
    """Pure in-memory Design oracle for the frozen future interface semantics."""
    values = (
        download_result_status,
        observed_http_status,
        observed_content_length_bytes,
        observed_sha256,
    )
    contexts = (
        allowed_download_result_statuses,
        successful_http_status_contract,
        content_length_contract,
        sha256_format_contract,
    )
    for index, value in enumerate(values):
        if value is _MISSING:
            return _make_result("blocked", MISSING_REASONS[index], (), (), EXACT4_FIELDS[:index + 1], ())

    validators = (
        lambda value: (type(value) is str, value in ALLOWED_DOWNLOAD_RESULT_STATUSES if type(value) is str else False),
        lambda value: (type(value) is int, 100 <= value <= 599 if type(value) is int else False),
        lambda value: (type(value) is int, value >= 0 if type(value) is int else False),
        lambda value: (type(value) is str, _SHA256_RE.fullmatch(value) is not None if type(value) is str else False),
    )
    validated: list[tuple[str, object]] = []
    for index, (value, validator) in enumerate(zip(values, validators, strict=True)):
        type_valid, value_valid = validator(value)
        if not type_valid:
            return _make_result("invalid", TYPE_INVALID_REASONS[index], (), tuple(validated), EXACT4_FIELDS, ())
        if not value_valid:
            return _make_result("invalid", VALUE_INVALID_REASONS[index], (), tuple(validated), EXACT4_FIELDS, ())
        validated.append((EXACT4_FIELDS[index], value))
    canonical = tuple(validated)
    for index, (value, expected) in enumerate(zip(contexts, FORMAL_CONTEXT_VALUES, strict=True)):
        reason = _context_reason(value, expected, index)
        if reason:
            return _make_result(
                "invalid", reason, canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS[:index + 1]
            )
    return _make_result("passed", "", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS)


CONTRACT_FILE = "covapie_admit_012_formal_evaluator_interface_and_result_contract.csv"
ROUTING_FILE = "covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv"
TRUTH_FILE = "covapie_admit_012_formal_evaluator_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_012_formal_evaluator_interface_source_boundary_audit.csv"
ISSUE_FILE = "covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_012_formal_evaluator_interface_contract_manifest.json"
OUTPUT_FILES = (CONTRACT_FILE, ROUTING_FILE, TRUTH_FILE, SOURCE_FILE, ISSUE_FILE, MANIFEST_FILE)

FIELD_STAGE = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1")
PRECONDITION_STAGE = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1")
CONTEXT_STAGE = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")

SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py": "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f",
    "scripts/check_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py": "bd2fda1bb9f1d623fb33037df2f7d569f366a8c3f66df69b6c4d348f65057cd7",
    "tests/test_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py": "270d6eb0a5b21f521d3568044179572bddad8f962cc81cded431b22d318470e0",
    "docs/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1_summary.md": "b9351a65f4065bfcd5f06f275c0c26f3f83c357de66744d4ed8d03d0cc05f345",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_validation_truth_matrix.csv": "766506f8c0bf2d7734b9c379c9437e1a48a2117873f7e974325b00ab685a39e1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_contract_source_boundary_audit.csv": "73393c6c540cb00d040fa8154948f544e445bbcb63323d9f463709c7ee8b16ed",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv": "dfe8e16d741548323cddfcdf3db86bdf0c098d6bb2a86fcb8ec0914ebe924855",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_preconditions_manifest.json": "712caa27add06784db5cfe2e59a65952ae4b1c5a369ff43772d8e4f95b18c4de",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_precondition_matrix.csv": "c667c5f195a1d834672564835380896553339833041d17cc2f689db23f9d319f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_issue_readiness_inventory.csv": "5ebe9332137bfa9c7804c82041ff695b3379ba505a5eb006fa5c7798510e8529",
    "docs/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit_v1_summary.md": "76f93106cf52b3f205d1cce0daa2c64999c16f0283c878ea6a401b14c8b93d91",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "scripts/check_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py": "a26c48830cccf580987bade69c375ccb2a2a18add65abe15c7e3dffe2cf74c27",
    "tests/test_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py": "a2ec0e56f53bf6eb6644e007505318efed4bc7d84cd83fa31ae30a9696c6e0e3",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_006_rule_logic_interface_v1/covapie_admit_006_rule_logic_interface_manifest.json": "921356eaa15f40fed925d11d73a6fbb868b4c881828c358fb35fde168b8c33f8",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py": "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
    "scripts/check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "72f33b9371c4eda533374e0535ba0da22467459da6a6488147e58ad680b7c7f1",
    "tests/test_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "10c8a798e99a9e8d8b4adab86f06ba259c1d721fac47dabbf4941850ff70581c",
    "docs/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1_summary.md": "abc525efa000206f1c3c80e56f73055c85895b0011dbf13f5a684be13a65243d",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv": "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json": "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv": "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json": "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py": "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv": "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)
SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps(list(SOURCE_PATHS), separators=(",", ":")).encode()
).hexdigest()
SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps([[path, SOURCE_SHA256[path]] for path in SOURCE_PATHS], separators=(",", ":")).encode()
).hexdigest()


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent chain")
        current = current.parent


def _pinned_read(path: Path, identity: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    if _identity(os.lstat(absolute)) != identity:
        raise ValueError("source identity drift before open")
    descriptor = os.open(absolute, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise ValueError("source descriptor identity drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(absolute)) != identity:
            raise ValueError("source identity drift during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    root_item = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(root_item.st_mode) or not stat.S_ISDIR(root_item.st_mode) or REPO_ROOT.resolve(strict=True) != REPO_ROOT:
        raise ValueError("unsafe repository root")
    if len(SOURCE_PATHS) != 30 or len(set(SOURCE_PATHS)) != 30:
        raise ValueError("source boundary must be fixed Exact30")
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if subject.returncode or subject.stdout.strip() != BASE_SUBJECT or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for relative in SOURCE_PATHS:
        path = Path(relative)
        if path.is_absolute() or not path.parts or ".." in path.parts or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints" or STAGE in path.parts:
            raise ValueError("source path outside boundary")
        _parent_chain(path)
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        tracked = _git(["ls-files", "--error-unmatch", "--", relative])
        tree = _git(["ls-tree", BASE_COMMIT, "--", relative])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        if (
            tracked.returncode or tracked.stdout.splitlines() != [relative]
            or tree.returncode or not separator or tree_path.strip() != relative
            or len(parts) != 3 or parts[0] not in {"100644", "100755"} or parts[1] != "blob"
            or stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe source: {relative}")
        structures.append((path, parts[0], _identity(item)))
    records = []
    for path, mode, identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, identity)
        digest = hashlib.sha256(current).hexdigest()
        if base.returncode or hashlib.sha256(base.stdout).hexdigest() != digest or digest != SOURCE_SHA256[path.as_posix()]:
            raise ValueError(f"source SHA drift: {path}")
        records.append(_Source(path, current, digest, mode))
    return tuple(records)


def _source(snapshot: tuple[_Source, ...], path: Path) -> _Source:
    return next(record for record in snapshot if record.path == path)


def _csv_rows(snapshot: tuple[_Source, ...], path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(snapshot, path).content.decode(), newline="")))


def _validate_predecessors(snapshot: tuple[_Source, ...]) -> None:
    field_manifest = json.loads(_source(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_field_contract_manifest.json").content)
    field_contract = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_field_contract.csv")
    enum_rows = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_result_status_enum.csv")
    field_truth = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_validation_truth_matrix.csv")
    field_sources = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_contract_source_boundary_audit.csv")
    field_issues = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv")
    precondition_manifest = json.loads(_source(snapshot, PRECONDITION_STAGE / "covapie_admit_012_formal_evaluator_preconditions_manifest.json").content)
    preconditions = _csv_rows(snapshot, PRECONDITION_STAGE / "covapie_admit_012_formal_evaluator_precondition_matrix.csv")
    precondition_issues = _csv_rows(snapshot, PRECONDITION_STAGE / "covapie_admit_012_issue_readiness_inventory.csv")
    contexts = _csv_rows(snapshot, CONTEXT_STAGE / "covapie_bulk_download_admission_evaluation_context_contract.csv")
    context_rows = [row for row in contexts if row["context_item"] in EXACT4_CONTEXT_ITEMS]
    admit006_manifest = json.loads(_source(snapshot, Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_006_rule_logic_interface_v1/covapie_admit_006_rule_logic_interface_manifest.json")).content)
    admit011_manifest = json.loads(_source(snapshot, Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json")).content)
    adapter_manifest = json.loads(_source(snapshot, Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json")).content)
    runtime_contract = _csv_rows(snapshot, Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv"))
    source_text = {record.path.as_posix(): record.content.decode() for record in snapshot if record.path.suffix in {".py", ".md"}}
    open_ids = {
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
        "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    }
    if not (
        field_manifest["exact4_fields"] == list(EXACT4_FIELDS)
        and field_manifest["row_counts"]["truth_matrix"] == 52
        and field_manifest["reason_vocabulary"] == list(FIELD_REASONS)
        and [row["field_name"] for row in field_contract] == list(EXACT4_FIELDS)
        and [row["status_value"] for row in enum_rows[:2]] == list(ALLOWED_DOWNLOAD_RESULT_STATUSES)
        and len(field_truth) == 52 and all(row["case_passed"] == "true" for row in field_truth)
        and len(field_sources) == 29 and len(field_issues) == len(precondition_issues) == 16
        and len(preconditions) == 24
        and precondition_manifest["authorized_admit_012_download_execution_count"] == 0
        and all(next(row for row in precondition_issues if row["issue_id"] == issue)["status"] == "open" for issue in open_ids)
        and [row["context_item"] for row in context_rows] == list(EXACT4_CONTEXT_ITEMS)
        and all(row["context_scope"] == "evaluation_policy" for row in context_rows)
        and admit006_manifest["result_fields"] == list(RESULT_FIELDS[:5]) + ["canonical_covalent_event_evidence_source", "validated_candidate_fields", "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used"]
        and admit011_manifest["result_fields"][:5] == list(RESULT_FIELDS[:5])
        and admit011_manifest["result_fields"][-2:] == list(RESULT_FIELDS[-2:])
        and adapter_manifest["standalone_result_fields"] == admit011_manifest["result_fields"]
        and any(row["contract_subject"] == "Exact10 to Exact13" for row in runtime_contract)
        and "def evaluate_admit_006" in source_text["src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py"]
        and "class Admit011EvaluationResult" in source_text["src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py"]
        and "_evaluate_registered_admit_011" in source_text["src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py"]
        and "semantic_tamper" in source_text["tests/test_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py"]
        and "_checker_oracle" in source_text["scripts/check_covapie_bulk_download_admission_admit_006_rule_logic_interface_v1.py"]
        and "test_public_signature" in source_text["tests/test_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py"]
    ):
        raise ValueError("predecessor interface evidence mismatch")


CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name", "formal_type",
    "default_or_missing_behavior", "required", "source_envelope", "validation_rule",
    "invariant", "contract_passed",
)
ROUTING_COLUMNS = (
    "route_consumption_order", "case_id", "contract_kind", "source_envelope", "source_key",
    "formal_parameter", "required", "missing_representation", "consumed_on_case",
    "validated_on_case", "adapter_responsibility", "evaluator_responsibility", "route_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "allowed_download_result_statuses_representation",
    "successful_http_status_contract_representation", "content_length_contract_representation",
    "sha256_format_contract_representation", "expected_outcome", "expected_reason",
    "expected_canonical_download_result_record", "expected_validated_download_result_fields",
    "expected_consumed_download_result_fields", "expected_consumed_context_items",
    "expected_evaluator_io_used", "observed_design_result", "case_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode", "expected_sha256",
    "base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256", "git_tracked",
    "base_tree_blob", "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed", "source_boundary_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(section: str, name: str, type_name: str, default: str, required: bool,
            source: str, validation: str, invariant: str) -> None:
        rows.append({
            "contract_order": str(len(rows) + 1), "contract_section": section,
            "section_order": str(1 + sum(row["contract_section"] == section for row in rows)),
            "public_name": name, "formal_type": type_name,
            "default_or_missing_behavior": default, "required": str(required).lower(),
            "source_envelope": source, "validation_rule": validation,
            "invariant": invariant, "contract_passed": "true",
        })

    for name in EXACT4_FIELDS:
        add("signature_parameter", name, "object", "private_singleton_missing_default", False,
            "download_result_context", "keyword_only; exact field contract", "Exact4 field order; no Mapping record")
    for name in EXACT4_CONTEXT_ITEMS:
        add("signature_parameter", name, "object", "no_default", True, "evaluation_context",
            "keyword_only; required by Python signature", "missing is signature failure, not result semantics")
    context_types = (
        "exact tuple[str,str]",
        "exact tuple[exact tuple[str,int_or_bool],...]",
        "exact tuple[exact tuple[str,int_or_bool_or_None],...]",
        "exact tuple[exact tuple[str,int_or_bool],...]",
    )
    for name, formal_type, value in zip(EXACT4_CONTEXT_ITEMS, context_types, FORMAL_CONTEXT_VALUES, strict=True):
        add("policy_context_shape", name, formal_type, "not_applicable", True, "evaluation_context",
            repr(value), "exact outer type, pair shape/order/key/value/type; no normalization")
    result_types = ("exact str", "exact str", "exact bool", "exact bool", "exact str", "exact tuple", "exact tuple", "exact tuple[str,...]", "exact tuple[str,...]", "exact bool")
    for name, formal_type in zip(RESULT_FIELDS, result_types, strict=True):
        add("result_field", name, formal_type, "not_applicable", True, "standalone_evaluator_result",
            "Exact10 ordered field", "see frozen outcome/canonical/validated/consumed invariants")
    invariants = (
        ("passed_iff_outcome", "passed == (outcome == 'passed')"),
        ("blocks_iff_not_passed", "blocks_candidate == (outcome != 'passed')"),
        ("reason_empty_iff_passed", "reason empty iff outcome passed"),
        ("missing_outcome", "field missing reasons imply blocked"),
        ("field_invalid_outcome", "field type/value reasons imply invalid"),
        ("context_invalid_outcome", "context reasons imply invalid"),
        ("canonical_shape", "empty on field failure; complete Exact4 on context failure/pass"),
        ("validated_prefix", "ordered prefix excluding failure field"),
        ("consumption_prefix", "fields/contexts reflect actual ordered consumption"),
        ("io", "evaluator_io_used is exact false"),
    )
    for name, rule in invariants:
        add("outcome_invariant", name, "invariant", "not_applicable", True, "result_contract", rule, rule)
    for reason in REASON_VOCABULARY:
        add("reason_vocabulary", reason if reason else "<empty>", "exact str", "not_applicable", True,
            "result_contract", "closed vocabulary member", "no catch-all reason")
    precedence = [
        *(f"presence:{name}" for name in EXACT4_FIELDS),
        *(f"type_then_value:{name}" for name in EXACT4_FIELDS),
        *(f"context_type:{name}" for name in EXACT4_CONTEXT_ITEMS),
        *(f"context_content:{name}" for name in EXACT4_CONTEXT_ITEMS),
        "passed",
    ]
    for item in precedence:
        add("validation_precedence", item, "precedence_step", "not_applicable", True,
            "standalone_evaluator", item, "first failure returns immediately")
    return rows


def _routing_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(case_id: str, kind: str, envelope: str, key: str, parameter: str, required: bool,
            missing: str, consumed: str, validated: str, adapter: str, evaluator: str) -> None:
        rows.append({
            "route_consumption_order": str(len(rows) + 1), "case_id": case_id,
            "contract_kind": kind, "source_envelope": envelope, "source_key": key,
            "formal_parameter": parameter, "required": str(required).lower(),
            "missing_representation": missing, "consumed_on_case": consumed,
            "validated_on_case": validated, "adapter_responsibility": adapter,
            "evaluator_responsibility": evaluator, "route_passed": "true",
        })

    for name in EXACT4_FIELDS:
        add(f"ROUTE_{name.upper()}", "route", "download_result_context", name, name, True,
            "private_missing_singleton", "case_dependent_field_prefix", "case_dependent_validated_prefix",
            "extract exactly once and pass by identity", "presence and exact field validation")
    for name in EXACT4_CONTEXT_ITEMS:
        add(f"ROUTE_{name.upper()}", "route", "evaluation_context", name, name, True,
            "adapter routing failure before call", "case_dependent_context_prefix", "not_applicable",
            "require key and pass by identity", "exact context type/content validation")
    for envelope in ("candidate_record", "batch_context", "stage_authorization_context"):
        add(f"FORBIDDEN_{envelope.upper()}", "forbidden_route", envelope, "*", "", False, "not_applicable",
            "none", "none", "must not source ADMIT_012 formal parameters", "does not consume envelope")
    for index, name in enumerate(EXACT4_FIELDS):
        add(f"MISSING_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "private_missing_singleton", "|".join(EXACT4_FIELDS[:index + 1]), "", "route Exact4 before call",
            "blocked at first missing during presence phase")
    for index, name in enumerate(EXACT4_FIELDS):
        add(f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "present_invalid", "|".join(EXACT4_FIELDS), "|".join(EXACT4_FIELDS[:index]),
            "route Exact4 before call", "invalid at first type/value failure")
    for index, name in enumerate(EXACT4_CONTEXT_ITEMS):
        add(f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name, True,
            "present_invalid", "|".join(EXACT4_CONTEXT_ITEMS[:index + 1]), "|".join(EXACT4_FIELDS),
            "route Exact4 contexts before call", "invalid at first context type/content failure")
    for case_id in ("PASSED", "PASSED_FAILURE_STATUS", "PASSED_HTTP_4XX", "PASSED_HTTP_5XX"):
        add(case_id, "consumption_case", "standalone_evaluator", "Exact4", "Exact8", True, "all_present",
            "|".join((*EXACT4_FIELDS, *EXACT4_CONTEXT_ITEMS)), "|".join(EXACT4_FIELDS),
            "route only download/evaluation envelopes", "passed; success/2xx judgment belongs to ADMIT_013")
    return rows


def _representation(value: object) -> str:
    if value is _MISSING:
        return "<MISSING>"
    if type(value) is _StringSubclass:
        return f"<str-subclass:{str(value)!r}>"
    if type(value) is _IntSubclass:
        return f"<int-subclass:{int(value)}>"
    if type(value) is _TupleSubclass:
        return f"<tuple-subclass:{tuple(value)!r}>"
    if type(value) is _PairTupleSubclass:
        return f"<pair-tuple-subclass:{tuple(value)!r}>"
    if type(value) is object:
        return "<object>"
    if type(value) is tuple:
        for index, item in enumerate(value):
            if type(item) is _StringSubclass:
                plain = tuple(str(member) if position == index else member for position, member in enumerate(value))
                return f"<tuple-member-str-subclass:{index}:{plain!r}>"
            if type(item) is _PairTupleSubclass:
                plain = tuple(tuple(member) if position == index else member for position, member in enumerate(value))
                return f"<tuple-pair-subclass:{index}:{plain!r}>"
    if isinstance(value, re.Pattern):
        return f"<regex:{value.pattern!r}>"
    return repr(value)


def _decode_field_representation(value: str) -> object:
    if value == "<MISSING>":
        return _MISSING
    if value.startswith("<str-subclass:"):
        return _StringSubclass(ast.literal_eval(value[14:-1]))
    if value.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(value[14:-1]))
    return ast.literal_eval(value)


def _result_values(result: Admit012EvaluationResultContractDesign) -> tuple[object, ...]:
    return tuple(getattr(result, name) for name in RESULT_FIELDS)


def _expected_from_reason(
    values: tuple[object, object, object, object], outcome: str, reason: str
) -> Admit012EvaluationResultContractDesign:
    if reason in MISSING_REASONS:
        index = MISSING_REASONS.index(reason)
        return _make_result("blocked", reason, (), (), EXACT4_FIELDS[:index + 1], ())
    if reason in TYPE_INVALID_REASONS or reason in VALUE_INVALID_REASONS:
        reasons = TYPE_INVALID_REASONS if reason in TYPE_INVALID_REASONS else VALUE_INVALID_REASONS
        index = reasons.index(reason)
        return _make_result("invalid", reason, (), _record(values[:index] + (_MISSING,) * (4 - index))[:index], EXACT4_FIELDS, ())
    canonical = _record(values)
    if reason in CONTEXT_REASONS:
        index = CONTEXT_REASONS.index(reason) // 2
        return _make_result("invalid", reason, canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS[:index + 1])
    if outcome != "passed":
        raise ValueError("explicit expected outcome/reason contradiction")
    return _make_result("passed", "", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS)


@dataclass(frozen=True)
class _Case:
    case_id: str
    group: str
    values: tuple[object, object, object, object]
    contexts: tuple[object, object, object, object]
    outcome: str
    reason: str
    negative_result_case: str = ""


def _context_cases() -> tuple[_Case, ...]:
    valid = ("success", 200, 1, "0123456789abcdef" * 4)
    a, h, c, s = FORMAL_CONTEXT_VALUES
    definitions: list[tuple[str, int, object, str]] = [
        ("ALLOWED_OUTER_LIST", 0, list(a), CONTEXT_REASONS[0]),
        ("ALLOWED_TUPLE_SUBCLASS", 0, _TupleSubclass(a), CONTEXT_REASONS[0]),
        ("ALLOWED_MEMBER_SUBCLASS", 0, (_StringSubclass("success"), "failure"), CONTEXT_REASONS[1]),
        ("ALLOWED_DUPLICATE", 0, ("success", "success"), CONTEXT_REASONS[1]),
        ("ALLOWED_REORDERED", 0, tuple(reversed(a)), CONTEXT_REASONS[1]),
        ("ALLOWED_EXTRA", 0, (*a, "pending"), CONTEXT_REASONS[1]),
        ("ALLOWED_MISSING", 0, a[:1], CONTEXT_REASONS[1]),
    ]
    names = ("HTTP", "CONTENT", "SHA")
    expected_values = (h, c, s)
    for context_index, (name, expected) in enumerate(zip(names, expected_values, strict=True), 1):
        definitions.extend((
            (f"{name}_OUTER_LIST", context_index, list(expected), CONTEXT_REASONS[context_index * 2]),
            (f"{name}_TUPLE_SUBCLASS", context_index, _TupleSubclass(expected), CONTEXT_REASONS[context_index * 2]),
            (f"{name}_PAIR_LIST", context_index, (list(expected[0]), *expected[1:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_PAIR_TUPLE_SUBCLASS", context_index, (_PairTupleSubclass(expected[0]), *expected[1:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_WRONG_KEY", context_index, (("wrong", expected[0][1]), *expected[1:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_KEY_ORDER", context_index, (expected[1], expected[0], *expected[2:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_WRONG_VALUE", context_index, ((expected[0][0], "wrong"), *expected[1:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_BOOL_INT_MIX", context_index, ((expected[0][0], True), *expected[1:]), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_EXTRA_PAIR", context_index, (*expected, ("extra", 1)), CONTEXT_REASONS[context_index * 2 + 1]),
            (f"{name}_MISSING_PAIR", context_index, expected[:-1], CONTEXT_REASONS[context_index * 2 + 1]),
        ))
    definitions.extend((
        ("SHA_MAPPING", 3, {key: value for key, value in s}, CONTEXT_REASONS[6]),
        ("SHA_REGEX", 3, re.compile("[0-9a-f]{64}"), CONTEXT_REASONS[6]),
    ))
    cases = []
    for case_id, index, value, reason in definitions:
        contexts = list(FORMAL_CONTEXT_VALUES)
        contexts[index] = value
        cases.append(_Case(case_id, "context_validation", valid, tuple(contexts), "invalid", reason))
    return tuple(cases)


def _cross_phase_cases() -> tuple[_Case, ...]:
    sha = "0123456789abcdef" * 4
    invalid_first_context = list(FORMAL_CONTEXT_VALUES)
    invalid_first_context[0] = ["success", "failure"]
    invalid_later_context = list(FORMAL_CONTEXT_VALUES)
    invalid_later_context[2] = (("legal_minimum", -1), *CONTENT_LENGTH_CONTRACT[1:])
    multiple_context = ([], object(), object(), object())
    return (
        _Case("CROSS_MISSING_FIELD_INVALID_CONTEXT", "cross_phase_precedence", (_MISSING, "bad", -1, sha), tuple(invalid_first_context), "blocked", MISSING_REASONS[0]),
        _Case("CROSS_FIELD_TYPE_CONTEXT", "cross_phase_precedence", (None, 200, 1, sha), tuple(invalid_first_context), "invalid", TYPE_INVALID_REASONS[0]),
        _Case("CROSS_FIELD_VALUE_CONTEXT", "cross_phase_precedence", ("unknown", 200, 1, sha), tuple(invalid_first_context), "invalid", VALUE_INVALID_REASONS[0]),
        _Case("CROSS_VALID_MULTIPLE_CONTEXT", "cross_phase_precedence", ("success", 200, 1, sha), multiple_context, "invalid", CONTEXT_REASONS[0]),
        _Case("CROSS_EARLIER_CONTEXT", "cross_phase_precedence", ("success", 200, 1, sha), tuple(invalid_later_context), "invalid", CONTEXT_REASONS[5]),
        _Case("CROSS_CONTEXT_TYPE_OVER_CONTENT", "cross_phase_precedence", ("success", 200, 1, sha), (_TupleSubclass(("wrong",)), *FORMAL_CONTEXT_VALUES[1:]), "invalid", CONTEXT_REASONS[0]),
    )


NEGATIVE_RESULT_CASES = (
    "WRONG_RESULT_FIELD_ORDER",
    "WRONG_OUTCOME_BOOL",
    "WRONG_CANONICAL_SHAPE",
    "PARTIAL_CANONICAL_RECORD",
    "VALIDATED_NOT_PREFIX",
    "CONSUMED_ORDER_DRIFT",
    "EVALUATOR_IO_TRUE",
    "UNKNOWN_REASON",
)


@dataclass(frozen=True)
class _WrongOrderResultDesign:
    outcome: object
    admission_rule_id: object


def _assert_negative_result_case(case_id: str, baseline: Admit012EvaluationResultContractDesign) -> str:
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    try:
        if case_id == "WRONG_RESULT_FIELD_ORDER":
            validate_admit_012_evaluation_result_contract_design(_WrongOrderResultDesign("passed", ADMISSION_RULE_ID))
        else:
            if case_id == "WRONG_OUTCOME_BOOL":
                values["passed"] = False
            elif case_id == "WRONG_CANONICAL_SHAPE":
                values["canonical_download_result_record"] = {"download_result_status": "success"}
            elif case_id == "PARTIAL_CANONICAL_RECORD":
                values["canonical_download_result_record"] = baseline.canonical_download_result_record[:2]
            elif case_id == "VALIDATED_NOT_PREFIX":
                values["validated_download_result_fields"] = tuple(reversed(baseline.validated_download_result_fields))
            elif case_id == "CONSUMED_ORDER_DRIFT":
                values["consumed_download_result_fields"] = tuple(reversed(EXACT4_FIELDS))
            elif case_id == "EVALUATOR_IO_TRUE":
                values["evaluator_io_used"] = True
            elif case_id == "UNKNOWN_REASON":
                values.update(outcome="invalid", passed=False, blocks_candidate=True, reason="UNKNOWN_REASON")
            Admit012EvaluationResultContractDesign(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _truth_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    predecessor = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_validation_truth_matrix.csv")
    cases: list[_Case] = []
    for row in predecessor:
        values = tuple(_decode_field_representation(row[column]) for column in (
            "download_result_status_representation", "observed_http_status_representation",
            "observed_content_length_bytes_representation", "observed_sha256_representation",
        ))
        outcome = {"contract_valid": "passed", "missing": "blocked", "invalid": "invalid"}[row["expected_contract_outcome"]]
        cases.append(_Case(f"FIELD52_{row['case_id']}", f"field52_{row['case_group']}", values, FORMAL_CONTEXT_VALUES, outcome, row["expected_reason"]))
    cases.extend(_context_cases())
    cases.extend(_cross_phase_cases())
    valid = ("success", 200, 1, "0123456789abcdef" * 4)
    cases.extend(_Case(case_id, "result_invariant_negative", valid, FORMAL_CONTEXT_VALUES, "passed", "", case_id) for case_id in NEGATIVE_RESULT_CASES)

    rows = []
    for order, case in enumerate(cases, 1):
        expected = _expected_from_reason(case.values, case.outcome, case.reason)
        if case.negative_result_case:
            observed = _assert_negative_result_case(case.negative_result_case, expected)
            passed = observed.startswith("RESULT_CONTRACT_REJECTED:")
            assertion_kind = "result_contract_rejection"
        else:
            observed_result = classify_admit_012_formal_evaluator_interface_design(
                download_result_status=case.values[0], observed_http_status=case.values[1],
                observed_content_length_bytes=case.values[2], observed_sha256=case.values[3],
                allowed_download_result_statuses=case.contexts[0],
                successful_http_status_contract=case.contexts[1],
                content_length_contract=case.contexts[2], sha256_format_contract=case.contexts[3],
            )
            observed = repr(_result_values(observed_result))
            passed = observed_result == expected
            assertion_kind = "formal_projection"
        rows.append({
            "case_order": str(order), "case_id": case.case_id, "case_group": case.group,
            "assertion_kind": assertion_kind,
            **{f"{name}_representation": _representation(value) for name, value in zip(EXACT4_FIELDS, case.values, strict=True)},
            **{f"{name}_representation": _representation(value) for name, value in zip(EXACT4_CONTEXT_ITEMS, case.contexts, strict=True)},
            "expected_outcome": expected.outcome, "expected_reason": expected.reason,
            "expected_canonical_download_result_record": repr(expected.canonical_download_result_record),
            "expected_validated_download_result_fields": repr(expected.validated_download_result_fields),
            "expected_consumed_download_result_fields": repr(expected.consumed_download_result_fields),
            "expected_consumed_context_items": repr(expected.consumed_context_items),
            "expected_evaluator_io_used": "false", "observed_design_result": observed,
            "case_passed": str(passed).lower(),
        })
    if not all(row["case_passed"] == "true" for row in rows):
        raise ValueError("Design truth mismatch")
    return rows


RESOLVED_INTERFACE_ISSUES = {
    "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
    "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
}
FIELD_RESOLVED_ISSUES = {
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
    "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
}
REQUIRED_OPEN_ISSUES = {
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
}
ISSUE_TRANSITION = "admit_012_formal_evaluator_interface_contract_frozen_v1"


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    rows = _csv_rows(snapshot, FIELD_STAGE / "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv")
    if len(rows) != 16 or tuple(rows[0]) != ISSUE_COLUMNS:
        raise ValueError("predecessor Exact16 issue contract drift")
    for row in rows:
        if row["issue_id"] in RESOLVED_INTERFACE_ISSUES:
            row["status"] = "resolved"
            row["integration_transition"] = ISSUE_TRANSITION
    by_id = {row["issue_id"]: row for row in rows}
    if not all(by_id[issue]["status"] == "resolved" for issue in FIELD_RESOLVED_ISSUES | RESOLVED_INTERFACE_ISSUES):
        raise ValueError("required resolved issue regressed")
    if not all(by_id[issue]["status"] == "open" for issue in REQUIRED_OPEN_ISSUES):
        raise ValueError("required open issue closed")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage issue drift")
    return rows


def _source_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.path.as_posix(),
        "source_kind": "python_source" if record.path.suffix == ".py" else "committed_csv" if record.path.suffix == ".csv" else "committed_manifest" if record.path.suffix == ".json" else "tracked_text",
        "base_tree_mode": record.base_mode, "expected_sha256": record.sha256,
        "base_tree_sha256": record.sha256, "filesystem_sha256": record.sha256,
        "frozen_snapshot_sha256": record.sha256, "git_tracked": "true", "base_tree_blob": "true",
        "filesystem_regular": "true", "non_symlink": "true", "parent_chain_non_symlink": "true",
        "safe_descendant": "true", "pinned_fd_read": "true", "triple_sha256_passed": "true",
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot, 1)]


TRUE_READINESS = (
    "admit_012_preconditions_audited",
    "admit_012_download_integrity_field_contract_frozen",
    "admit_012_download_result_status_enum_frozen",
    "admit_012_field_semantics_complete",
    "admit_012_presence_semantics_resolved",
    "admit_012_validation_precedence_resolved",
    "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen",
    "admit_012_formal_result_contract_frozen",
    "admit_012_formal_evaluator_interface_contract_frozen",
    "ready_for_admit_012_standalone_evaluator_interface_implementation",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented",
    "Admit012EvaluationResult_implemented",
    "admit_012_unified_adapter_contract_frozen",
    "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _readiness() -> dict[str, bool]:
    return {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(snapshot: tuple[_Source, ...] | None = None) -> dict[str, bytes]:
    snapshot = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    routing_rows = _routing_rows()
    truth_rows = _truth_rows(snapshot)
    source_rows = _source_rows(snapshot)
    issue_rows = _issue_rows(snapshot)
    files = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        ROUTING_FILE: _csv_bytes(ROUTING_COLUMNS, routing_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        ISSUE_FILE: _csv_bytes(ISSUE_COLUMNS, issue_rows),
    }
    readiness = _readiness()
    group_counts = {
        group: sum(row["case_group"] == group for row in truth_rows)
        for group in sorted({row["case_group"] for row in truth_rows})
    }
    manifest: dict[str, Any] = {
        "manifest_schema_version": "covapie_admit_012_formal_evaluator_interface_contract_manifest_v1",
        "project": PROJECT, "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "routing_responsibility": {
            "download_result_context": list(EXACT4_FIELDS),
            "evaluation_context": list(EXACT4_CONTEXT_ITEMS),
            "forbidden_sources": ["candidate_record", "batch_context", "stage_authorization_context", "filesystem", "network", "raw", "provider", "download_execution_inside_evaluator"],
        },
        "future_public_signature": "evaluate_admit_012(*, download_result_status: object = _MISSING, observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, observed_sha256: object = _MISSING, allowed_download_result_statuses: object, successful_http_status_contract: object, content_length_contract: object, sha256_format_contract: object) -> Admit012EvaluationResult",
        "signature_parameters": list((*EXACT4_FIELDS, *EXACT4_CONTEXT_ITEMS)),
        "signature_all_keyword_only": True, "signature_varargs": False, "signature_varkw": False,
        "field_missing_defaults_private_singleton": True, "policy_context_parameters_required": True,
        "policy_context_values": {
            name: repr(value) for name, value in zip(EXACT4_CONTEXT_ITEMS, FORMAL_CONTEXT_VALUES, strict=True)
        },
        "outcome_vocabulary": list(OUTCOMES), "reason_vocabulary": list(REASON_VOCABULARY),
        "context_reason_vocabulary": list(CONTEXT_REASONS), "result_type": "Admit012EvaluationResult",
        "result_fields": list(RESULT_FIELDS), "result_field_count": 10,
        "validation_phase_order": ["Exact4_presence", "Exact4_type_value", "policy_context_type_content", "passed"],
        "field_order": list(EXACT4_FIELDS), "context_order": list(EXACT4_CONTEXT_ITEMS),
        "canonical_record_representation": "exact ordered tuple of Exact4 exact pair tuples",
        "validated_representation": "ordered Exact4 pair-tuple prefix excluding failing field",
        "consumption_semantics": "actual ordered field/context prefixes; all fields consumed after complete presence phase",
        "failure_status_4xx_5xx_outcome": "passed",
        "admit_013_success_or_integrity_judgment_executed": False,
        "design_oracle": "classify_admit_012_formal_evaluator_interface_design",
        "design_result_type": "Admit012EvaluationResultContractDesign",
        "formal_evaluator_implemented": False, "formal_result_type_defined": False,
        "unified_adapter_or_runtime_changed": False, "admit_013_implemented": False,
        "source_count": len(snapshot), "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "row_counts": {
            "interface_result_contract": len(contract_rows), "routing_consumption": len(routing_rows),
            "truth_matrix": len(truth_rows), "field52_projection": 52,
            "source_boundary": len(source_rows), "issue_inventory": len(issue_rows),
        },
        "truth_matrix_group_counts": group_counts,
        "resolved_issue_ids": sorted(FIELD_RESOLVED_ISSUES | RESOLVED_INTERFACE_ISSUES),
        "issue_integration_transition": ISSUE_TRANSITION,
        "required_open_issue_ids": sorted(REQUIRED_OPEN_ISSUES),
        "readiness": readiness, **readiness,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "authorized_admit_012_download_execution_count": 0,
        "safety": {
            "network": False, "raw": False, "provider_mapping": False, "real_download": False,
            "model_or_checkpoint": False, "runtime_change": False, "training": False,
        },
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        "all_checks_passed": True,
    }
    files[MANIFEST_FILE] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return {name: files[name] for name in OUTPUT_FILES}


def _rename_noreplace(source: Path, destination: Path) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316, -100, os.fsencode(source), -100, os.fsencode(destination), 1
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _write_leaf(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    item = os.lstat(root)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode) or root.resolve(strict=True) != root:
        raise ValueError("unsafe output root")
    if {entry.name for entry in root.iterdir()} != set(OUTPUT_FILES):
        return False
    for name, expected in payloads.items():
        leaf = root / name
        before = os.lstat(leaf)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError("unsafe output leaf")
        descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            identity = _identity(before)
            if _identity(os.fstat(descriptor)) != identity:
                raise ValueError("output stat/open race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(descriptor)) != identity or _identity(os.lstat(leaf)) != identity:
                raise ValueError("output identity drift")
        finally:
            os.close(descriptor)
        if b"".join(chunks) != expected:
            return False
    return True


def _cleanup_staging(staging: Path) -> None:
    if not staging.exists() or staging.is_symlink() or not staging.is_dir():
        return
    entries = tuple(staging.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        return
    for entry in entries:
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if stat.S_ISLNK(parent_item.st_mode) or not stat.S_ISDIR(parent_item.st_mode) or parent.resolve(strict=True) != parent:
        raise ValueError("unsafe output parent")
    payloads = build_artifacts()
    if root.exists():
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent))
    try:
        for name, data in payloads.items():
            _write_leaf(staging / name, data)
        descriptor = os.open(staging, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _rename_noreplace(staging, root)
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if not _read_exact_output_set(root, payloads):
            raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_staging(staging)
        raise
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    return materialize_contract(output_root)

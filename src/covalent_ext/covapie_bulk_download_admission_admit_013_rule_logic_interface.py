"""Pure ADMIT_013 standalone evaluator and deterministic evidence builder."""

import re
from dataclasses import dataclass, fields


ADMISSION_RULE_ID = "ADMIT_013"
DOWNLOAD_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
PARAMETERS = (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
VALIDATION_PHASES = (
    "Exact4_presence",
    "Exact4_type_value",
    "Exact3_optional_authority_type_value",
    "Exact7_business_outcome",
    "passed",
)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "canonical_integrity_authority_record",
    "validated_download_result_fields",
    "validated_integrity_authority_fields",
    "consumed_download_result_fields",
    "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
MISSING_REASONS = (
    "DOWNLOAD_RESULT_STATUS_MISSING",
    "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    "OBSERVED_SHA256_MISSING",
)
DOWNLOAD_TYPE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "OBSERVED_SHA256_TYPE_INVALID",
)
DOWNLOAD_VALUE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "OBSERVED_SHA256_FORMAT_INVALID",
)
AUTHORITY_TYPE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "EXPECTED_SHA256_TYPE_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
)
AUTHORITY_VALUE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "EXPECTED_SHA256_FORMAT_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID",
)
BUSINESS_REASONS = (
    "DOWNLOAD_RESULT_STATUS_FAILURE",
    "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY",
    "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED",
    "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
REASON_VOCABULARY = (
    "",
    "DOWNLOAD_RESULT_STATUS_MISSING",
    "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    "OBSERVED_SHA256_MISSING",
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "OBSERVED_SHA256_TYPE_INVALID",
    "OBSERVED_SHA256_FORMAT_INVALID",
    "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "EXPECTED_SHA256_TYPE_INVALID",
    "EXPECTED_SHA256_FORMAT_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID",
    "DOWNLOAD_RESULT_STATUS_FAILURE",
    "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY",
    "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED",
    "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}", flags=re.ASCII)


class _MissingAdmit013Value:
    __slots__ = ()


_MISSING = _MissingAdmit013Value()


def _download_value_valid(index: int, value: object) -> bool:
    if index == 0:
        return type(value) is str and value in {"success", "failure"}
    if index == 1:
        return type(value) is int and 100 <= value <= 599
    if index == 2:
        return type(value) is int and value >= 0
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _authority_value_valid(index: int, value: object) -> bool:
    if index == 0:
        return type(value) is int and value >= 0
    if index == 1:
        return type(value) is str and _SHA256_RE.fullmatch(value) is not None
    return type(value) is str and value in {"verified", "failed"}


def _pair_record_shape_valid(
    value: object, names: tuple[str, ...], *, require_complete: bool
) -> bool:
    if type(value) is not tuple:
        return False
    if require_complete and len(value) != len(names):
        return False
    positions = []
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
            return False
        if pair[0] not in names:
            return False
        positions.append(names.index(pair[0]))
    return positions == sorted(set(positions))


def _name_tuple_valid(value: object, names: tuple[str, ...], *, prefix: bool) -> bool:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        return False
    if prefix:
        return value == names[:len(value)]
    positions = [names.index(item) for item in value if item in names]
    return len(positions) == len(value) and positions == sorted(set(positions))


def _business_reason(
    download: tuple[tuple[str, object], ...],
    authority: tuple[tuple[str, object], ...],
) -> str:
    values = dict(download)
    authorities = dict(authority)
    if values[DOWNLOAD_FIELDS[0]] == "failure":
        return BUSINESS_REASONS[0]
    if not 200 <= values[DOWNLOAD_FIELDS[1]] <= 299:
        return BUSINESS_REASONS[1]
    if values[DOWNLOAD_FIELDS[2]] == 0:
        return BUSINESS_REASONS[2]
    if (
        AUTHORITY_FIELDS[1] in authorities
        and authorities[AUTHORITY_FIELDS[1]] != values[DOWNLOAD_FIELDS[3]]
    ):
        return BUSINESS_REASONS[3]
    if authorities.get(AUTHORITY_FIELDS[2]) == "failed":
        return BUSINESS_REASONS[4]
    if (
        AUTHORITY_FIELDS[0] in authorities
        and authorities[AUTHORITY_FIELDS[0]] != values[DOWNLOAD_FIELDS[2]]
    ):
        return BUSINESS_REASONS[5]
    strong_authority = (
        authorities.get(AUTHORITY_FIELDS[1]) == values[DOWNLOAD_FIELDS[3]]
        or authorities.get(AUTHORITY_FIELDS[2]) == "verified"
    )
    return "" if strong_authority else BUSINESS_REASONS[6]


@dataclass(frozen=True)
class Admit013EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_download_result_record: tuple
    canonical_integrity_authority_record: tuple
    validated_download_result_fields: tuple[str, ...]
    validated_integrity_authority_fields: tuple[str, ...]
    consumed_download_result_fields: tuple[str, ...]
    consumed_integrity_authority_fields: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        if type(self) is not Admit013EvaluationResult:
            raise TypeError("exact Admit013EvaluationResult required")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("exact result field order required")
        if any(
            type(value) is not str
            for value in (self.admission_rule_id, self.outcome, self.reason)
        ):
            raise TypeError("result string fields require exact built-in str")
        if any(
            type(value) is not bool
            for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)
        ):
            raise TypeError("result boolean fields require exact built-in bool")
        tuple_values = (
            self.canonical_download_result_record,
            self.canonical_integrity_authority_record,
            self.validated_download_result_fields,
            self.validated_integrity_authority_fields,
            self.consumed_download_result_fields,
            self.consumed_integrity_authority_fields,
        )
        if any(type(value) is not tuple for value in tuple_values):
            raise TypeError("result record and name fields require exact built-in tuple")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("admission rule identity mismatch")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome outside closed Exact3 vocabulary")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason outside closed Exact26 vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed flag contradicts outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate flag contradicts outcome")
        if (self.reason == "") is not (self.outcome == "passed"):
            raise ValueError("reason must be empty exactly when passed")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be exact false")
        download = self.canonical_download_result_record
        authority = self.canonical_integrity_authority_record
        if not _pair_record_shape_valid(
            download, DOWNLOAD_FIELDS, require_complete=download != ()
        ) or any(
            not _download_value_valid(DOWNLOAD_FIELDS.index(pair[0]), pair[1])
            for pair in download
        ):
            raise ValueError("canonical download record malformed")
        if not _pair_record_shape_valid(
            authority, AUTHORITY_FIELDS, require_complete=False
        ) or any(
            not _authority_value_valid(AUTHORITY_FIELDS.index(pair[0]), pair[1])
            for pair in authority
        ):
            raise ValueError("canonical integrity authority record malformed")
        if not _name_tuple_valid(
            self.validated_download_result_fields, DOWNLOAD_FIELDS, prefix=True
        ) or not _name_tuple_valid(
            self.consumed_download_result_fields, DOWNLOAD_FIELDS, prefix=True
        ):
            raise ValueError("download validated/consumed sequence malformed")
        if not _name_tuple_valid(
            self.validated_integrity_authority_fields, AUTHORITY_FIELDS, prefix=False
        ) or not _name_tuple_valid(
            self.consumed_integrity_authority_fields, AUTHORITY_FIELDS, prefix=True
        ):
            raise ValueError("authority validated/consumed sequence malformed")
        if self.validated_integrity_authority_fields != tuple(
            pair[0] for pair in authority
        ):
            raise ValueError("authority canonical and validated names disagree")

        if self.reason in MISSING_REASONS:
            index = MISSING_REASONS.index(self.reason)
            expected = (
                "blocked", (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS[:index + 1], (),
            )
        elif self.reason in DOWNLOAD_TYPE_REASONS or self.reason in DOWNLOAD_VALUE_REASONS:
            reasons = (
                DOWNLOAD_TYPE_REASONS
                if self.reason in DOWNLOAD_TYPE_REASONS
                else DOWNLOAD_VALUE_REASONS
            )
            index = reasons.index(self.reason)
            expected = (
                "invalid", (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, (),
            )
        elif self.reason in AUTHORITY_TYPE_REASONS or self.reason in AUTHORITY_VALUE_REASONS:
            reasons = (
                AUTHORITY_TYPE_REASONS
                if self.reason in AUTHORITY_TYPE_REASONS
                else AUTHORITY_VALUE_REASONS
            )
            index = reasons.index(self.reason)
            if len(download) != len(DOWNLOAD_FIELDS):
                raise ValueError("authority failure requires complete canonical Exact4")
            if any(AUTHORITY_FIELDS.index(pair[0]) >= index for pair in authority):
                raise ValueError("authority record includes failing or later field")
            expected = (
                "invalid", download, authority, DOWNLOAD_FIELDS,
                self.validated_integrity_authority_fields, DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        else:
            if len(download) != len(DOWNLOAD_FIELDS):
                raise ValueError("business outcome requires complete canonical Exact4")
            business_reason = _business_reason(download, authority)
            if self.reason != business_reason:
                raise ValueError("business reason contradicts Exact7 precedence")
            expected = (
                "passed" if business_reason == "" else "blocked",
                download, authority, DOWNLOAD_FIELDS,
                self.validated_integrity_authority_fields,
                DOWNLOAD_FIELDS, AUTHORITY_FIELDS,
            )
        observed = (
            self.outcome,
            download,
            authority,
            self.validated_download_result_fields,
            self.validated_integrity_authority_fields,
            self.consumed_download_result_fields,
            self.consumed_integrity_authority_fields,
        )
        if observed != expected:
            raise ValueError("result state contradicts frozen reason semantics")


def _make_result(
    outcome: str,
    reason: str,
    download: tuple,
    authority: tuple,
    validated_download: tuple[str, ...],
    validated_authority: tuple[str, ...],
    consumed_download: tuple[str, ...],
    consumed_authority: tuple[str, ...],
) -> Admit013EvaluationResult:
    return Admit013EvaluationResult(
        ADMISSION_RULE_ID,
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        download,
        authority,
        validated_download,
        validated_authority,
        consumed_download,
        consumed_authority,
        False,
    )


def evaluate_admit_013(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    expected_content_length_bytes: object = _MISSING,
    expected_sha256: object = _MISSING,
    explicit_integrity_verdict: object = _MISSING,
) -> Admit013EvaluationResult:
    """Evaluate the frozen ADMIT_013 post-download rule in memory."""
    download_values = (
        download_result_status,
        observed_http_status,
        observed_content_length_bytes,
        observed_sha256,
    )
    authority_values = (
        expected_content_length_bytes,
        expected_sha256,
        explicit_integrity_verdict,
    )
    for index, value in enumerate(download_values):
        if value is _MISSING:
            return _make_result(
                "blocked", MISSING_REASONS[index], (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS[:index + 1], (),
            )

    download_record = []
    for index, value in enumerate(download_values):
        expected_type = (str, int, int, str)[index]
        if type(value) is not expected_type:
            return _make_result(
                "invalid", DOWNLOAD_TYPE_REASONS[index], (), (),
                DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, (),
            )
        if not _download_value_valid(index, value):
            return _make_result(
                "invalid", DOWNLOAD_VALUE_REASONS[index], (), (),
                DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, (),
            )
        download_record.append((DOWNLOAD_FIELDS[index], value))
    canonical_download = tuple(download_record)

    authority_record = []
    for index, value in enumerate(authority_values):
        if value is _MISSING:
            continue
        expected_type = (int, str, str)[index]
        if type(value) is not expected_type:
            return _make_result(
                "invalid", AUTHORITY_TYPE_REASONS[index], canonical_download,
                tuple(authority_record), DOWNLOAD_FIELDS,
                tuple(pair[0] for pair in authority_record), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        if not _authority_value_valid(index, value):
            return _make_result(
                "invalid", AUTHORITY_VALUE_REASONS[index], canonical_download,
                tuple(authority_record), DOWNLOAD_FIELDS,
                tuple(pair[0] for pair in authority_record), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        authority_record.append((AUTHORITY_FIELDS[index], value))
    canonical_authority = tuple(authority_record)
    reason = _business_reason(canonical_download, canonical_authority)
    return _make_result(
        "passed" if reason == "" else "blocked", reason,
        canonical_download, canonical_authority, DOWNLOAD_FIELDS,
        tuple(pair[0] for pair in canonical_authority), DOWNLOAD_FIELDS,
        AUTHORITY_FIELDS,
    )


# === ADMIT_013 FORMAL EVALUATOR CLOSURE END ===


import ast
import csv
import ctypes
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
BASE_COMMIT = "79e63dce368722b126ad21208a3de13f7ea4b6df"
BASE_PARENT = "2eea08835c4ef88d5b810509134f8eef94e3e99e"
BASE_TREE = "ac3633abc2cf52a715faf36faea827f76d4236d9"
BASE_SUBJECT = "add CovaPIE ADMIT_013 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_013_rule_logic_interface_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_013_unified_adapter_contract_v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
DESIGN_STAGE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1"
)

CONTRACT_FILE = "covapie_admit_013_rule_logic_interface_contract.csv"
TRUTH_FILE = "covapie_admit_013_rule_logic_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_013_rule_logic_interface_source_boundary_audit.csv"
PURITY_FILE = "covapie_admit_013_rule_logic_interface_purity_audit.csv"
ISSUE_FILE = "covapie_admit_013_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_013_rule_logic_interface_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILE, TRUTH_FILE, SOURCE_FILE, PURITY_FILE, ISSUE_FILE, MANIFEST_FILE,
)
FORMAL_MARKER = "# === ADMIT_013 FORMAL " + "EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "evaluate_admit_013",
    "_make_result",
    "_business_reason",
    "Admit013EvaluationResult",
    "Admit013EvaluationResult.__post_init__",
    "_download_value_valid",
    "_authority_value_valid",
    "_pair_record_shape_valid",
    "_name_tuple_valid",
    "_MissingAdmit013Value",
)

CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name",
    "formal_type", "required", "frozen_value", "formal_invariant",
    "implementation_source", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind", "inherited_case_id",
    *(f"{name}_representation" for name in PARAMETERS),
    "expected_design_result", "observed_formal_result", "exact_type_value_equality",
    "evaluator_io_used", "formal_source", "truth_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256",
    "frozen_snapshot_sha256", "git_tracked", "base_tree_blob",
    "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed",
    "source_boundary_passed",
)
PURITY_COLUMNS = (
    "audit_order", "audit_kind", "definition_name", "definition_kind",
    "reachable_from", "normalized_ast_sha256", "permitted_global_bindings",
    "permitted_calls", "observed", "forbidden_io_absent", "mutation_absent",
    "dynamic_dispatch_absent", "purity_passed",
)

SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py": "256d5d0bfd54fe5accc4493051809aafec58a41b6cf56b9090dbf19f80b2a2e3",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_and_result_contract.csv": "655ff7c2af7f95a9eef8742e3fac3635b3a914be39aa1bf0cb5efc392d3ee6a7",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv": "55b78fdf124efc0310d4e55b8564568c7cd88c5e3155666a75162d6c54c1af90",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_truth_matrix.csv": "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv": "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_contract_manifest.json": "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv": "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json": "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py": "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json": "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py": "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json": "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
}
SOURCE_PATHS = tuple(Path(path) for path in SOURCE_SHA256)
SOURCE_PATH_LIST_SHA256 = "d61ddc0b6b0063d41b9b063a744412c079e3e6c529169141371ca8f73f79dcd0"
SOURCE_PATH_SHA256_PAIRS_SHA256 = "4399ae88529132a7e872419c95490e0978857248205956b63515b154b3d0aae7"


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _TupleSubclass(tuple):
    pass


class _PairSubclass(tuple):
    pass


class _ResultSubclass(Admit013EvaluationResult):
    pass


@dataclass(frozen=True)
class _WrongOrderResult:
    outcome: object
    admission_rule_id: object


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(version) != CANONICAL_PYTHON_VERSION
    ):
        observed_version = ".".join(str(part) for part in version)
        raise RuntimeError(
            "canonical evidence runtime required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed_version}; "
            "frozen AST evidence is version-sensitive; noncanonical Python may only "
            "be used for evaluator-only semantic smoke"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name,
        tuple(sys.version_info[:3]),
    )


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _assert_repo_root() -> tuple[int, int, int]:
    item = os.lstat(REPO_ROOT)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISDIR(item.st_mode)
        or REPO_ROOT.resolve(strict=True) != REPO_ROOT
    ):
        raise ValueError("unsafe repository root")
    return _identity(item)


def _assert_parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent chain")
        current = current.parent


def _pinned_read(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    if _identity(os.lstat(absolute)) != expected_identity:
        raise ValueError("source identity drift before open")
    descriptor = os.open(
        absolute,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source FD identity drift")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError("source lexical identity drift")
        _assert_parent_chain(path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _assert_base_lineage() -> None:
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    if identity.stdout.splitlines() != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    root_identity = _assert_repo_root()
    _assert_base_lineage()
    if len(SOURCE_PATHS) != 12 or len(set(SOURCE_PATHS)) != 12:
        raise ValueError("source boundary must be fixed Exact12")
    structures = []
    for path in SOURCE_PATHS:
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] == ("data", "raw")
            or path.parts[0] == "checkpoints"
            or STAGE in path.parts
        ):
            raise ValueError("unsafe source path")
        _assert_parent_chain(path)
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        if (
            tree.returncode
            or tracked.returncode
            or tracked.stdout.splitlines() != [path.as_posix()]
            or not separator
            or tree_path.strip() != path.as_posix()
            or len(parts) != 3
            or parts[0] not in {"100644", "100755"}
            or parts[1] != "blob"
            or stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe committed source: {path}")
        structures.append((path, parts[0], _identity(item)))
    records = []
    for path, mode, frozen_identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, frozen_identity)
        digest = hashlib.sha256(current).hexdigest()
        if (
            base.returncode
            or not isinstance(base.stdout, bytes)
            or hashlib.sha256(base.stdout).hexdigest() != digest
            or digest != SOURCE_SHA256[path.as_posix()]
        ):
            raise ValueError(f"source SHA drift: {path}")
        records.append(_Source(path, current, digest, mode))
    if _assert_repo_root() != root_identity:
        raise ValueError("repository root identity drift")
    return tuple(records)


def _source(snapshot: tuple[_Source, ...], suffix: str) -> _Source:
    matches = [record for record in snapshot if record.path.as_posix().endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"source lookup not unique: {suffix}")
    return matches[0]


def _source_csv(snapshot: tuple[_Source, ...], suffix: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(snapshot, suffix).content.decode())))


def _source_json(snapshot: tuple[_Source, ...], suffix: str) -> dict[str, Any]:
    return json.loads(_source(snapshot, suffix).content)


def _validate_predecessors(snapshot: tuple[_Source, ...]) -> None:
    formal = _source_json(
        snapshot, "covapie_admit_013_formal_evaluator_interface_contract_manifest.json"
    )
    formal_truth = _source_csv(
        snapshot, "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv"
    )
    formal_issues = _source_csv(
        snapshot, "covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv"
    )
    outcome = _source_json(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_contract_manifest.json"
    )
    outcome_truth = _source_csv(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
    )
    admit012 = _source_json(snapshot, "covapie_admit_012_rule_logic_interface_manifest.json")
    runtime = _source_json(snapshot, "covapie_admit_001_to_012_runtime_manifest.json")
    if not (
        formal["base_commit"] == BASE_PARENT
        and formal["future_function_name"] == "evaluate_admit_013"
        and formal["future_result_type_name"] == "Admit013EvaluationResult"
        and formal["signature_parameters"] == list(PARAMETERS)
        and formal["result_fields"] == list(RESULT_FIELDS)
        and formal["reason_vocabulary"] == list(REASON_VOCABULARY)
        and len(formal_truth) == 128
        and len(formal_issues) == 23
        and outcome["business_failure_precedence"] == list(BUSINESS_REASONS)
        and len(outcome_truth) == 23
        and admit012["evaluate_admit_012_implemented"] is True
        and admit012["admit_012_standalone_evaluator_interface_implemented"] is True
        and runtime["registered_rule_count"] == 12
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_013", "ADMIT_014", "ADMIT_015"]
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
    ):
        raise ValueError("predecessor evidence mismatch")


def _formal_source_attestation() -> tuple[bytes, str, str, dict[str, str]]:
    _assert_canonical_evidence_runtime()
    relative = Path(
        "src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py"
    )
    _assert_parent_chain(relative)
    item = os.lstat(REPO_ROOT / relative)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
        raise ValueError("unsafe formal production source")
    source = _pinned_read(relative, _identity(item))
    text = source.decode()
    if text.count(FORMAL_MARKER) != 1:
        raise ValueError("formal closure marker drift")
    prefix = text.split(FORMAL_MARKER, 1)[0].encode()
    tree = ast.parse(prefix)
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    if set(definitions) != {
        "_MissingAdmit013Value", "_download_value_valid", "_authority_value_valid",
        "_pair_record_shape_valid", "_name_tuple_valid", "_business_reason",
        "Admit013EvaluationResult", "_make_result", "evaluate_admit_013",
    }:
        raise ValueError("formal closure definition set drift")
    result_class = definitions["Admit013EvaluationResult"]
    post = next(
        node for node in result_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    nodes = {
        name: post if name.endswith(".__post_init__") else definitions[name]
        for name in FORMAL_CLOSURE
    }
    forbidden_names = {
        "open", "eval", "exec", "getattr", "globals", "locals", "__import__",
        "subprocess", "socket", "Path",
    }
    for name, node in nodes.items():
        if any(isinstance(item, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for item in ast.walk(node)):
            raise ValueError(f"formal purity statement forbidden: {name}")
        if any(isinstance(item, ast.Name) and item.id in forbidden_names for item in ast.walk(node)):
            raise ValueError(f"formal purity binding forbidden: {name}")
        if any(
            isinstance(item, ast.Attribute)
            and item.attr in {"open", "read", "write", "fsync", "replace"}
            for item in ast.walk(node)
        ):
            raise ValueError(f"formal I/O attribute forbidden: {name}")
    digests = {
        name: hashlib.sha256(
            ast.dump(node, annotate_fields=True, include_attributes=False).encode()
        ).hexdigest()
        for name, node in nodes.items()
    }
    return (
        source,
        hashlib.sha256(source).hexdigest(),
        hashlib.sha256(prefix).hexdigest(),
        digests,
    )


def _contract_rows(ast_digests: dict[str, str]) -> list[dict[str, str]]:
    rows = []

    def add(section: str, name: str, formal_type: str, required: bool, value: str, invariant: str) -> None:
        section_order = 1 + sum(row["contract_section"] == section for row in rows)
        rows.append({
            "contract_order": str(len(rows) + 1), "contract_section": section,
            "section_order": str(section_order), "public_name": name,
            "formal_type": formal_type, "required": str(required).lower(),
            "frozen_value": value, "formal_invariant": invariant,
            "implementation_source": "formal_closure", "contract_passed": "true",
        })

    for index, name in enumerate(PARAMETERS):
        add(
            "signature_parameter", name, "object", index < 4,
            "keyword_only|private_shared_missing_singleton",
            "Exact7 order; no positional/varargs/varkw/Mapping/normalization",
        )
    result_types = (
        "str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple",
        "tuple", "tuple", "tuple", "bool",
    )
    for name, formal_type in zip(RESULT_FIELDS, result_types, strict=True):
        add(
            "result_field", name, formal_type, True, "Exact12_ordered",
            "exact built-in top-level type and reason-phase state invariant",
        )
    for reason in REASON_VOCABULARY:
        add(
            "reason_vocabulary", reason or "<empty>", "str", True, reason,
            "closed Exact26 ordered vocabulary; no catch-all or free text",
        )
    for phase in VALIDATION_PHASES:
        add(
            "validation_phase", phase, "phase", True, phase,
            "first failure returns; frozen Exact5 order",
        )
    for name in FORMAL_CLOSURE:
        add(
            "formal_closure", name, "normalized_ast_sha256", True,
            ast_digests[name], "pure in-memory reachable definition",
        )
    invariants = (
        ("exact_result_type", "type(self) is Admit013EvaluationResult"),
        ("exact_result_storage", "dataclass fields equal RESULT_FIELDS"),
        ("exact_top_level_types", "exact str/bool/tuple only"),
        ("identity", "admission_rule_id == ADMIT_013"),
        ("outcome", "closed Exact3"),
        ("reason", "closed Exact26"),
        ("passed", "passed iff outcome passed"),
        ("blocks_candidate", "blocks iff outcome not passed"),
        ("reason_emptiness", "reason empty iff outcome passed"),
        ("evaluator_io", "evaluator_io_used is False"),
        ("canonical_records", "exact ordered raw pair tuples; no sentinel"),
        ("phase_state", "canonical/validated/consumed agree with reason phase"),
    )
    for name, invariant in invariants:
        add("result_invariant", name, "invariant", True, invariant, "fail closed")
    for name in (
        "no_adapter_or_runtime", "no_provider_or_network", "no_raw_or_download",
        "no_model_checkpoint_dataloader_training",
    ):
        add("safety_boundary", name, "boolean", True, "true", "absence attested")
    if len(rows) != 76:
        raise ValueError("formal implementation contract row count drift")
    return rows


def _decode_representation(text: str) -> object:
    if text == "<MISSING>":
        return _MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _StrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<bytes:"):
        return ast.literal_eval(text[7:-1]).encode()
    return ast.literal_eval(text)


def _result_values(value: Admit013EvaluationResult) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


def _validate_exact_result(value: object) -> None:
    if type(value) is not Admit013EvaluationResult:
        raise TypeError("exact formal result type required")
    reconstructed = Admit013EvaluationResult(*(getattr(value, name) for name in RESULT_FIELDS))
    if reconstructed != value:
        raise ValueError("formal result reconstruction mismatch")


NEGATIVE_RESULT_CASES = (
    "WRONG_TOP_LEVEL_RESULT_TYPE", "RESULT_SUBCLASS", "STORAGE_NOT_EXACT_DATACLASS",
    "MISSING_FIELD", "EXTRA_FIELD", "FIELD_REORDER", "PASSED_INT_ONE",
    "BLOCKS_INT_ZERO", "CANONICAL_OUTER_LIST", "MALFORMED_PAIR", "PAIR_LIST",
    "PAIR_SUBCLASS", "TUPLE_SUBCLASS", "WRONG_PAIR_NAME", "WRONG_PAIR_ORDER",
    "DUPLICATE_PAIR", "EXTRA_PAIR", "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD",
    "VALIDATED_TUPLE_LIST", "CONSUMED_TUPLE_LIST", "VALIDATED_NAME_NOT_EXACT_STR",
    "CONSUMED_NAME_NOT_EXACT_STR", "DESIGN_SENTINEL_LEAK", "EVALUATOR_IO_TRUE",
    "OUTCOME_REASON_INVARIANT_CONFLICT", "ADMISSION_RULE_ID_DRIFT",
)


def _reject_negative_result(case_id: str, baseline: Admit013EvaluationResult) -> str:
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    download = baseline.canonical_download_result_record
    try:
        if case_id == "WRONG_TOP_LEVEL_RESULT_TYPE":
            _validate_exact_result(object())
        elif case_id == "RESULT_SUBCLASS":
            _ResultSubclass(*(values[name] for name in RESULT_FIELDS))
        elif case_id in {"STORAGE_NOT_EXACT_DATACLASS", "MISSING_FIELD", "EXTRA_FIELD"}:
            mapping = dict(values)
            if case_id == "MISSING_FIELD":
                mapping.pop("reason")
            elif case_id == "EXTRA_FIELD":
                mapping["extra"] = True
            _validate_exact_result(mapping)
        elif case_id == "FIELD_REORDER":
            _validate_exact_result(_WrongOrderResult("passed", ADMISSION_RULE_ID))
        else:
            if case_id == "PASSED_INT_ONE":
                values["passed"] = 1
            elif case_id == "BLOCKS_INT_ZERO":
                values["blocks_candidate"] = 0
            elif case_id == "CANONICAL_OUTER_LIST":
                values["canonical_download_result_record"] = list(download)
            elif case_id == "MALFORMED_PAIR":
                values["canonical_download_result_record"] = ((DOWNLOAD_FIELDS[0],), *download[1:])
            elif case_id == "PAIR_LIST":
                values["canonical_download_result_record"] = (list(download[0]), *download[1:])
            elif case_id == "PAIR_SUBCLASS":
                values["canonical_download_result_record"] = (_PairSubclass(download[0]), *download[1:])
            elif case_id == "TUPLE_SUBCLASS":
                values["canonical_download_result_record"] = _TupleSubclass(download)
            elif case_id == "WRONG_PAIR_NAME":
                values["canonical_download_result_record"] = (("wrong", download[0][1]), *download[1:])
            elif case_id == "WRONG_PAIR_ORDER":
                values["canonical_download_result_record"] = tuple(reversed(download))
            elif case_id == "DUPLICATE_PAIR":
                values["canonical_download_result_record"] = (download[0], download[0], *download[2:])
            elif case_id == "EXTRA_PAIR":
                values["canonical_download_result_record"] = (*download, ("extra", "value"))
            elif case_id == "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD":
                values["canonical_integrity_authority_record"] = ((AUTHORITY_FIELDS[0], _MISSING),)
                values["validated_integrity_authority_fields"] = (AUTHORITY_FIELDS[0],)
            elif case_id == "VALIDATED_TUPLE_LIST":
                values["validated_download_result_fields"] = list(DOWNLOAD_FIELDS)
            elif case_id == "CONSUMED_TUPLE_LIST":
                values["consumed_download_result_fields"] = list(DOWNLOAD_FIELDS)
            elif case_id == "VALIDATED_NAME_NOT_EXACT_STR":
                values["validated_download_result_fields"] = (_StrSubclass(DOWNLOAD_FIELDS[0]), *DOWNLOAD_FIELDS[1:])
            elif case_id == "CONSUMED_NAME_NOT_EXACT_STR":
                values["consumed_integrity_authority_fields"] = (_StrSubclass(AUTHORITY_FIELDS[0]), *AUTHORITY_FIELDS[1:])
            elif case_id == "DESIGN_SENTINEL_LEAK":
                values["canonical_download_result_record"] = ((DOWNLOAD_FIELDS[0], _MISSING), *download[1:])
            elif case_id == "EVALUATOR_IO_TRUE":
                values["evaluator_io_used"] = True
            elif case_id == "OUTCOME_REASON_INVARIANT_CONFLICT":
                values.update(outcome="blocked", passed=False, blocks_candidate=True, reason="")
            elif case_id == "ADMISSION_RULE_ID_DRIFT":
                values["admission_rule_id"] = "ADMIT_012"
            Admit013EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _truth_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    predecessor = _source_csv(
        snapshot, "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv"
    )
    if len(predecessor) != 128:
        raise ValueError("predecessor truth must be Exact128")
    representation_columns = tuple(f"{name}_representation" for name in PARAMETERS)
    baseline = evaluate_admit_013(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=10, observed_sha256="0123456789abcdef" * 4,
        expected_sha256="0123456789abcdef" * 4,
    )
    rows = []
    for prior in predecessor:
        if prior["case_id"] in NEGATIVE_RESULT_CASES:
            observed = _reject_negative_result(prior["case_id"], baseline)
            equal = observed == prior["observed_design_result"]
        else:
            decoded = tuple(_decode_representation(prior[column]) for column in representation_columns)
            observed_result = evaluate_admit_013(**dict(zip(PARAMETERS, decoded, strict=True)))
            observed = repr(_result_values(observed_result))
            expected = ast.literal_eval(prior["observed_design_result"])
            equal = _result_values(observed_result) == expected and all(
                type(left) is type(right)
                for left, right in zip(_result_values(observed_result), expected, strict=True)
            )
        rows.append({
            "case_order": prior["case_order"], "case_id": prior["case_id"],
            "case_group": prior["case_group"], "assertion_kind": prior["assertion_kind"],
            "inherited_case_id": prior["inherited_case_id"],
            **{column: prior[column] for column in representation_columns},
            "expected_design_result": prior["observed_design_result"],
            "observed_formal_result": observed,
            "exact_type_value_equality": str(equal).lower(),
            "evaluator_io_used": "false",
            "formal_source": "evaluate_admit_013|Admit013EvaluationResult",
            "truth_passed": str(equal).lower(),
        })
    if not all(row["truth_passed"] == "true" for row in rows):
        raise ValueError("formal truth projection mismatch")
    return rows


def _source_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.path.as_posix(),
        "source_kind": (
            "python_source" if record.path.suffix == ".py"
            else "committed_csv" if record.path.suffix == ".csv"
            else "committed_manifest"
        ),
        "base_tree_mode": record.base_mode, "expected_sha256": record.sha256,
        "base_tree_sha256": record.sha256, "filesystem_sha256": record.sha256,
        "frozen_snapshot_sha256": record.sha256, "git_tracked": "true",
        "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "parent_chain_non_symlink": "true",
        "safe_descendant": "true", "pinned_fd_read": "true",
        "triple_sha256_passed": "true", "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot, 1)]


def _purity_rows(full_sha: str, prefix_sha: str, digests: dict[str, str]) -> list[dict[str, str]]:
    parents = (
        "root", "evaluate_admit_013", "evaluate_admit_013",
        "_make_result|_business_reason", "Admit013EvaluationResult",
        "evaluate_admit_013|Admit013EvaluationResult.__post_init__",
        "evaluate_admit_013|Admit013EvaluationResult.__post_init__",
        "Admit013EvaluationResult.__post_init__",
        "Admit013EvaluationResult.__post_init__",
        "evaluate_admit_013|signature_defaults|_MISSING",
    )
    kinds = (
        "function", "function", "function", "frozen_dataclass", "method",
        "function", "function", "function", "function",
        "private sentinel class",
    )
    rows = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append({
            "audit_order": str(index + 1), "audit_kind": "closure_definition",
            "definition_name": name, "definition_kind": kinds[index],
            "reachable_from": parents[index], "normalized_ast_sha256": digests[name],
            "permitted_global_bindings": "immutable_formal_constants|pure_helpers",
            "permitted_calls": "exact_builtin_and_formal_helper_calls",
            "observed": "reachable_and_frozen", "forbidden_io_absent": "true",
            "mutation_absent": "true", "dynamic_dispatch_absent": "true",
            "purity_passed": "true",
        })
    metadata = (
        ("production_full_sha256", full_sha),
        ("marker_prefix_sha256", prefix_sha),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
        ("forbidden_io", "open|Path_IO|os_IO|subprocess|socket|provider|raw absent"),
        ("forbidden_dynamic_dispatch", "import_in_function|eval|exec|getattr|globals|locals absent"),
        ("mutable_global_state", "absent"),
    )
    for name, observed in metadata:
        rows.append({
            "audit_order": str(len(rows) + 1), "audit_kind": "closure_metadata",
            "definition_name": name, "definition_kind": "attestation",
            "reachable_from": "checker_recomputed", "normalized_ast_sha256": "",
            "permitted_global_bindings": "", "permitted_calls": "",
            "observed": observed, "forbidden_io_absent": "true",
            "mutation_absent": "true", "dynamic_dispatch_absent": "true",
            "purity_passed": "true",
        })
    return rows


TRUE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_standalone_signature_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_validation_precedence_resolved",
    "admit_013_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_013_standalone_evaluator_interface_implementation",
    "evaluate_admit_013_implemented",
    "Admit013EvaluationResult_implemented",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "ready_for_admit_013_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_013_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(snapshot: tuple[_Source, ...] | None = None) -> dict[str, bytes]:
    _assert_canonical_evidence_runtime()
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_predecessors(frozen)
    formal_source, full_sha, prefix_sha, ast_digests = _formal_source_attestation()
    if not formal_source:
        raise ValueError("formal source attestation failed")
    contract_rows = _contract_rows(ast_digests)
    truth_rows = _truth_rows(frozen)
    source_rows = _source_rows(frozen)
    purity_rows = _purity_rows(full_sha, prefix_sha, ast_digests)
    issue_source = _source(
        frozen, "covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv"
    )
    issue_rows = list(csv.DictReader(io.StringIO(issue_source.content.decode())))
    if len(issue_rows) != 23:
        raise ValueError("Exact23 issue inventory drift")
    by_id = {row["issue_id"]: row for row in issue_rows}
    required_open = (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    )
    if any(by_id[name]["successor_effective_status"] != "open" for name in required_open):
        raise ValueError("required open issue state drift")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage affected-rules drift")
    payloads = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        PURITY_FILE: _csv_bytes(PURITY_COLUMNS, purity_rows),
        ISSUE_FILE: issue_source.content,
    }
    group_counts = {
        group: sum(row["case_group"] == group for row in truth_rows)
        for group in dict.fromkeys(row["case_group"] for row in truth_rows)
    }
    readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    manifest = {
        "manifest_schema_version": "covapie_admit_013_rule_logic_interface_manifest_v1",
        "project": PROJECT,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "public_evaluator": "evaluate_admit_013",
        "public_signature": "evaluate_admit_013(*, download_result_status: object = _MISSING, observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, observed_sha256: object = _MISSING, expected_content_length_bytes: object = _MISSING, expected_sha256: object = _MISSING, explicit_integrity_verdict: object = _MISSING) -> Admit013EvaluationResult",
        "result_type": "Admit013EvaluationResult",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": len(RESULT_FIELDS),
        "download_fields": list(DOWNLOAD_FIELDS),
        "authority_fields": list(AUTHORITY_FIELDS),
        "parameter_order": list(PARAMETERS),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "reason_vocabulary_count_including_empty": len(REASON_VOCABULARY),
        "validation_phase_order": list(VALIDATION_PHASES),
        "business_failure_precedence": list(BUSINESS_REASONS),
        "private_missing_singleton": True,
        "formal_evaluator_implemented": True,
        "formal_result_type_defined": True,
        "formal_production_sha256": full_sha,
        "formal_marker_prefix_sha256": prefix_sha,
        "formal_closure": list(FORMAL_CLOSURE),
        "formal_closure_count": len(FORMAL_CLOSURE),
        "formal_ast_sha256": ast_digests,
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": ".".join(
            str(part) for part in CANONICAL_PYTHON_VERSION
        ),
        "ast_attestation_cross_python_version_portable": (
            AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE
        ),
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "source_count": len(frozen),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_boundary": [
            {"path": record.path.as_posix(), "sha256": record.sha256, "base_tree_mode": record.base_mode}
            for record in frozen
        ],
        "output_files": list(OUTPUT_FILES),
        "output_file_count": len(OUTPUT_FILES),
        "row_counts": {
            "formal_contract": len(contract_rows), "truth_matrix": len(truth_rows),
            "evaluator_result_projection": 102, "inherited_business_projection": 23,
            "result_negative_projection": len(NEGATIVE_RESULT_CASES),
            "source_boundary": len(source_rows), "purity_audit": len(purity_rows),
            "issue_inventory": len(issue_rows),
        },
        "truth_matrix_group_counts": group_counts,
        "actual_evaluator_design_oracle_projection_passed": 102,
        "inherited_business_projection_passed": 23,
        "result_negative_projection_rejected": len(NEGATIVE_RESULT_CASES),
        "truth_matrix_passed": 128,
        "purity_closure_complete": True,
        "issue_transition_count": 0,
        "issue_inventory_byte_identical_to_formal_interface": True,
        "remaining_open_issue_ids": list(required_open),
        "coverage_affected_rules": "ADMIT_013|ADMIT_014|ADMIT_015",
        "readiness": readiness,
        **readiness,
        "safety": {
            "provider": False, "network": False, "download": False, "raw": False,
            "model_or_checkpoint": False, "dataloader": False,
            "runtime_change": False, "training": False, "stage_commit_push": False,
        },
        "adapter_registry_runtime_changed": False,
        "authorized_admit_013_download_execution_count": 0,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "feature_semantics_audit_requirement": "required_before_training; historical UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False require audit",
        "materialization_policy": {
            "build_before_mutation": True, "exact_output_inventory": True,
            "o_excl_staging_leaves": True, "leaf_and_directory_fsync": True,
            "rename_noreplace_required": True, "gpfs_einval_fails_closed": True,
            "os_replace_fallback": False, "root_fd_no_follow": True,
            "leaf_open_dir_fd": True, "inode_preserving_exact_set_noop": True,
        },
        "output_sha256": {
            name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()
        },
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILE] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


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
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_output_at(root_fd: int, name: str, expected_identity: tuple[int, int, int]) -> bytes:
    if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
        raise ValueError("output leaf identity drift before open")
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        dir_fd=root_fd,
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf FD identity drift")
        if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
            raise ValueError("output leaf lexical identity drift")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        stat.S_ISLNK(root_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("unsafe output root")
    root_fd = os.open(
        root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            return False
        leaf_identities = {}
        for name in OUTPUT_FILES:
            item = os.lstat(name, dir_fd=root_fd)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise ValueError("unsafe output leaf")
            leaf_identities[name] = _identity(item)
        matches = all(
            _read_output_at(root_fd, name, leaf_identities[name]) == payloads[name]
            for name in OUTPUT_FILES
        )
        if _identity(os.lstat(root.parent)) != parent_identity:
            raise ValueError("output parent identity drift")
        if _identity(os.fstat(root_fd)) != root_identity or _identity(os.lstat(root)) != root_identity:
            raise ValueError("output root identity drift")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift")
        if any(
            _identity(os.lstat(name, dir_fd=root_fd)) != leaf_identities[name]
            for name in OUTPUT_FILES
        ):
            raise ValueError("output leaf identity drift after traversal")
        return matches
    finally:
        os.close(root_fd)


def _cleanup_owned_staging(staging: Path) -> None:
    if not staging.exists() or staging.is_symlink() or not staging.is_dir():
        return
    entries = {entry.name: entry for entry in staging.iterdir()}
    if set(entries) - set(OUTPUT_FILES):
        return
    for entry in entries.values():
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    _assert_canonical_evidence_runtime()
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if (
        stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
        or parent.resolve(strict=True) != parent
    ):
        raise ValueError("unsafe output parent")
    payloads = build_artifacts()
    if root.exists() or root.is_symlink():
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent))
    try:
        for name in OUTPUT_FILES:
            _write_leaf(staging / name, payloads[name])
        _fsync_directory(staging)
        _rename_noreplace(staging, root)
        _fsync_directory(parent)
        if not _read_exact_output_set(root, payloads):
            raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_owned_staging(staging)
        raise
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_013_rule_logic_interface_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the deterministic Exact6 evidence set."""
    return materialize_contract(output_root)


if __name__ == "__main__":
    materialize_contract()

"""Design-only ADMIT_012 download-integrity field contract gate.

The classifier in this module is a pure in-memory truth oracle.  It is not
``evaluate_admit_012`` and does not freeze a public evaluator signature,
formal result, unified adapter, registry entry, dispatcher route, downloader,
or ADMIT_013 implementation.
"""
from __future__ import annotations

import csv
import ctypes
import hashlib
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
STAGE = "covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1"
BASE_COMMIT = "62b2ba8de9a38f48ae35b1fd217897191a0519cd"
BASE_SUBJECT = "add CovaPIE ADMIT_012 formal evaluator interface preconditions audit v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_012"
ADMISSION_RULE_NAME = "future_download_integrity_fields_required"
EVIDENCE_SOURCE = "future_download_result"
EVALUATION_PHASE = "post_download"
REQUIRED_STATUS = "download_status_http_status_content_length_and_sha256_present"
BLOCKING_REASON = "download_integrity_fields_missing"
EXACT4_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
STATUS_ENUM_VERSION = "covapie_download_result_status_v1"
ALLOWED_DOWNLOAD_RESULT_STATUSES = ("success", "failure")
SUCCESS_DOWNLOAD_RESULT_STATUSES = ("success",)
HTTP_LEGAL_MINIMUM = 100
HTTP_LEGAL_MAXIMUM = 599
HTTP_SUCCESS_MINIMUM = 200
HTTP_SUCCESS_MAXIMUM = 299
SHA256_PATTERN = r"[0-9a-f]{64}"
_SHA256_RE = re.compile(SHA256_PATTERN, flags=re.ASCII)

MISSING_REASONS = {
    "download_result_status": "DOWNLOAD_RESULT_STATUS_MISSING",
    "observed_http_status": "OBSERVED_HTTP_STATUS_MISSING",
    "observed_content_length_bytes": "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    "observed_sha256": "OBSERVED_SHA256_MISSING",
}
TYPE_INVALID_REASONS = {
    "download_result_status": "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    "observed_http_status": "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "observed_content_length_bytes": "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "observed_sha256": "OBSERVED_SHA256_TYPE_INVALID",
}
VALUE_INVALID_REASONS = {
    "download_result_status": "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "observed_http_status": "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "observed_content_length_bytes": "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "observed_sha256": "OBSERVED_SHA256_FORMAT_INVALID",
}
REASON_VOCABULARY = tuple(MISSING_REASONS.values()) + tuple(
    reason
    for field_name in EXACT4_FIELDS
    for reason in (TYPE_INVALID_REASONS[field_name], VALUE_INVALID_REASONS[field_name])
)
PRESENCE_ORDER = EXACT4_FIELDS
VALIDATION_ORDER = EXACT4_FIELDS
WITHIN_FIELD_PRECEDENCE = ("exact_type", "enum_range_or_grammar")

CONTRACT_FILE = "covapie_admit_012_download_integrity_field_contract.csv"
ENUM_FILE = "covapie_admit_012_download_result_status_enum.csv"
TRUTH_FILE = "covapie_admit_012_download_integrity_validation_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_012_download_integrity_contract_source_boundary_audit.csv"
ISSUE_FILE = "covapie_admit_012_download_integrity_contract_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_012_download_integrity_field_contract_manifest.json"
OUTPUT_FILES = (CONTRACT_FILE, ENUM_FILE, TRUTH_FILE, SOURCE_FILE, ISSUE_FILE, MANIFEST_FILE)

AUDIT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1"
)
STEP14AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
STEP14AUA_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
ADMIT011_RAW_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1"
)
ADMIT011_ADAPTER_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1"
)

SOURCE_SHA256 = {
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json": "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json": "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_precondition_matrix.csv": "c667c5f195a1d834672564835380896553339833041d17cc2f689db23f9d319f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_formal_evaluator_preconditions_manifest.json": "712caa27add06784db5cfe2e59a65952ae4b1c5a369ff43772d8e4f95b18c4de",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_issue_readiness_inventory.csv": "5ebe9332137bfa9c7804c82041ff695b3379ba505a5eb006fa5c7798510e8529",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_observed_value_inventory.csv": "dc47865f2f176b9e37aac0caf71fdacee1275eece19351cb69d31f64ad14104f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_preconditions_audit_v1/covapie_admit_012_source_boundary_audit.csv": "4272d31320a9b32e503d4fda49df5c21778238b46e5f2b51bb1dbbb1a3d5ce5e",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_design_gate_manifest.json": "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv": "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv": "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv": "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv": "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_precondition_manifest.json": "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv": "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "data/derived/covalent_small/real_covalent_pilot_download_execution_gate_v0/real_covalent_pilot_download_provenance.csv": "0c280d377091df6d6e269cd7ac0bac5fc02c9883daaca46ce23a71b390704f2d",
    "data/derived/covalent_small/real_covalent_pilot_download_integrity_gate_v0/real_covalent_pilot_download_integrity_gate_manifest.json": "00eda1c687d83d813ecd411ab769ec2d500fa56b80c009dda85b93d1cf757868",
    "docs/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1_summary.md": "86cd3da95b990d0143ee8df1eafe2f7d974bf09cef06142965b09aed67c7a9d2",
    "scripts/check_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py": "f5e1c695869f21c149ea441ea878c9005c1015ec3bc5ece25d0784b38496774e",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py": "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_preconditions_audit.py": "3547991855ab8a828e89174b5c725e1c1ef9627a56dc9c22b2d5769b7830035b",
    "src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py": "68335a0991772a5c57af476f4d538a3d1d8f40d71a2836715707c1c2d9aa5c8c",
    "src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py": "30f80efb146689eb88c0f94962703a447aec8613e9eef78d6be012d0548e17d0",
    "src/covalent_ext/covapie_small_pilot_download_manifest_gate.py": "3f45d0d97bbbf087e6258e8fd87d82c830697b0a24f7bb914ef4593a82da4bb4",
    "src/covalent_ext/real_covalent_pilot_download_execution_gate.py": "ecf2bbafd25dfe8da746dc56974eecbddb703cbc144dbf20a8f0c50fbf840a78",
    "src/covalent_ext/real_covalent_pilot_download_integrity_gate.py": "df5a8bfe9935db416a934535ffa33285d6b0aea466617c1ae1a89a934e1dd20c",
    "tests/test_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py": "47784344fccdf94a3b285d5ba3423bd34cd6fd11441184952a67e26c2555b71e",
    "tests/test_real_covalent_pilot_download_integrity_gate_v0.py": "29a341fb066d170bc2b2a10fa3d58d7cb899e225af94b6a7267cec6fc497e708",
}
SOURCE_PATHS = tuple(sorted(SOURCE_SHA256))
EXPECTED_SOURCE_COUNT = 29
EXPECTED_SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps(list(SOURCE_PATHS), separators=(",", ":")).encode()
).hexdigest()
EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps([[path, SOURCE_SHA256[path]] for path in SOURCE_PATHS], separators=(",", ":")).encode()
).hexdigest()

HISTORICAL_STATUS_LITERALS = (
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "downloaded"),
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "existing_reused"),
    ("src/covalent_ext/covapie_cys_sg_discovery_download_smoke.py", "download_status", "failed_with_reason"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "blocked_invalid_existing_raw"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "blocked_network_execution_not_requested"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "download_failed_or_invalid_payload"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "downloaded"),
    ("src/covalent_ext/covapie_independent_group_expansion_acquisition_execution_smoke.py", "download_status", "reused_existing_valid_raw"),
    ("src/covalent_ext/covapie_small_pilot_download_manifest_gate.py", "download_status", "pending_not_downloaded"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "download_failed"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "downloaded_raw_file_recorded"),
    ("src/covalent_ext/real_covalent_pilot_download_execution_gate.py", "provenance_status", "recorded_without_raw_file_copy"),
    ("src/covalent_ext/real_covalent_pilot_download_integrity_gate.py", "integrity_status", "failed"),
    ("src/covalent_ext/real_covalent_pilot_download_integrity_gate.py", "integrity_status", "passed"),
)


class _MissingDesignValue:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingDesignValue()


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


@dataclass(frozen=True)
class Admit012DownloadIntegrityFieldContractDesign:
    field_order: tuple[str, ...] = EXACT4_FIELDS
    status_enum_version: str = STATUS_ENUM_VERSION
    ordered_allowed_statuses: tuple[str, ...] = ALLOWED_DOWNLOAD_RESULT_STATUSES
    success_status_subset: tuple[str, ...] = SUCCESS_DOWNLOAD_RESULT_STATUSES
    presence_order: tuple[str, ...] = PRESENCE_ORDER
    validation_order: tuple[str, ...] = VALIDATION_ORDER
    within_field_precedence: tuple[str, ...] = WITHIN_FIELD_PRECEDENCE


@dataclass(frozen=True)
class Admit012DownloadIntegrityClassificationDesign:
    contract_outcome: str
    reason: str
    first_failing_field: str
    rule_blocking_reason: str

    def __post_init__(self) -> None:
        if type(self) is not Admit012DownloadIntegrityClassificationDesign:
            raise TypeError("exact Design result required")
        if tuple(item.name for item in fields(type(self))) != (
            "contract_outcome", "reason", "first_failing_field", "rule_blocking_reason"
        ):
            raise TypeError("Design result shape changed")
        if any(type(value) is not str for value in (
            self.contract_outcome, self.reason, self.first_failing_field, self.rule_blocking_reason
        )):
            raise TypeError("Design result fields require exact built-in str")
        if self.contract_outcome not in {"contract_valid", "missing", "invalid"}:
            raise ValueError("unknown Design contract outcome")
        valid = self.contract_outcome == "contract_valid"
        if valid != (self.reason == self.first_failing_field == self.rule_blocking_reason == ""):
            raise ValueError("Design result outcome invariant invalid")
        if not valid:
            if self.reason not in REASON_VOCABULARY:
                raise ValueError("Design result reason outside contract")
            if self.first_failing_field not in EXACT4_FIELDS or self.rule_blocking_reason != BLOCKING_REASON:
                raise ValueError("Design result failure invariant invalid")


def _invalid(outcome: str, reason: str, field_name: str) -> Admit012DownloadIntegrityClassificationDesign:
    return Admit012DownloadIntegrityClassificationDesign(outcome, reason, field_name, BLOCKING_REASON)


def classify_admit_012_download_integrity_fields_design(
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
) -> Admit012DownloadIntegrityClassificationDesign:
    """Classify one design case; this call shape is not a future public signature."""
    values = {
        "download_result_status": download_result_status,
        "observed_http_status": observed_http_status,
        "observed_content_length_bytes": observed_content_length_bytes,
        "observed_sha256": observed_sha256,
    }
    for field_name in PRESENCE_ORDER:
        if values[field_name] is _MISSING:
            return _invalid("missing", MISSING_REASONS[field_name], field_name)

    if type(download_result_status) is not str:
        return _invalid("invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0])
    if download_result_status not in ALLOWED_DOWNLOAD_RESULT_STATUSES:
        return _invalid("invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0])
    if type(observed_http_status) is not int:
        return _invalid("invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1])
    if not HTTP_LEGAL_MINIMUM <= observed_http_status <= HTTP_LEGAL_MAXIMUM:
        return _invalid("invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1])
    if type(observed_content_length_bytes) is not int:
        return _invalid("invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2])
    if observed_content_length_bytes < 0:
        return _invalid("invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2])
    if type(observed_sha256) is not str:
        return _invalid("invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3])
    if _SHA256_RE.fullmatch(observed_sha256) is None:
        return _invalid("invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3])
    return Admit012DownloadIntegrityClassificationDesign("contract_valid", "", "", "")


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False)


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _safe_source_path(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and STAGE not in path.as_posix()
    )


def _real_repo_root() -> None:
    item = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode) or REPO_ROOT.resolve(strict=True) != REPO_ROOT:
        raise ValueError("unsafe repository root")


def _parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent")
        current = current.parent


def _pinned_read(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    _real_repo_root()
    _parent_chain(path)
    if _identity(os.lstat(absolute)) != expected_identity:
        raise ValueError("source identity drift before open")
    descriptor = os.open(
        absolute,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source stat/open race")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source descriptor identity drift")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError("source lexical replacement")
        _parent_chain(path)
        _real_repo_root()
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    if len(SOURCE_PATHS) != EXPECTED_SOURCE_COUNT or not all(_safe_source_path(Path(path)) for path in SOURCE_PATHS):
        raise ValueError("source path boundary invalid")
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if subject.returncode or subject.stdout.strip() != BASE_SUBJECT or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for value in SOURCE_PATHS:
        path = Path(value)
        absolute = REPO_ROOT / path
        _parent_chain(path)
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", value])
        tracked = _git(["ls-files", "--error-unmatch", "--", value])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split() if tree.returncode == 0 else []
        if (
            tracked.returncode
            or tracked.stdout.splitlines() != [value]
            or tree.returncode
            or not separator
            or tree_path.strip() != value
            or len(parts) != 3
            or parts[0] not in {"100644", "100755"}
            or parts[1] != "blob"
            or stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe source: {value}")
        structures.append((path, parts[0], _identity(item)))
    records: list[_Source] = []
    for path, mode, identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, identity)
        digest = hashlib.sha256(current).hexdigest()
        if base.returncode or not isinstance(base.stdout, bytes):
            raise ValueError(f"base source unavailable: {path}")
        if hashlib.sha256(base.stdout).hexdigest() != digest or digest != SOURCE_SHA256[path.as_posix()]:
            raise ValueError(f"source SHA drift: {path}")
        records.append(_Source(path, current, digest, mode))
    return tuple(records)


def _record(snapshot: tuple[_Source, ...], path: Path) -> _Source:
    return next(source for source in snapshot if source.path == path)


def _csv_rows(snapshot: tuple[_Source, ...], path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_record(snapshot, path).content.decode(), newline="")))


def _validate_committed_contracts(snapshot: tuple[_Source, ...]) -> None:
    audit_manifest = json.loads(_record(snapshot, AUDIT_ROOT / "covapie_admit_012_formal_evaluator_preconditions_manifest.json").content)
    preconditions = _csv_rows(snapshot, AUDIT_ROOT / "covapie_admit_012_formal_evaluator_precondition_matrix.csv")
    observed = _csv_rows(snapshot, AUDIT_ROOT / "covapie_admit_012_observed_value_inventory.csv")
    prior_boundary = _csv_rows(snapshot, AUDIT_ROOT / "covapie_admit_012_source_boundary_audit.csv")
    prior_issues = _csv_rows(snapshot, AUDIT_ROOT / "covapie_admit_012_issue_readiness_inventory.csv")
    registry = _csv_rows(snapshot, STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv")
    schema = _csv_rows(snapshot, STEP14AT_ROOT / "covapie_bulk_download_admission_schema_contract.csv")
    executable = _csv_rows(snapshot, STEP14AUA_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv")
    field_rows = _csv_rows(snapshot, STEP14AUA_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv")
    contexts = _csv_rows(snapshot, STEP14AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv")
    rule12 = next(row for row in registry if row["admission_rule_id"] == "ADMIT_012")
    rule13 = next(row for row in registry if row["admission_rule_id"] == "ADMIT_013")
    exec12 = next(row for row in executable if row["admission_rule_id"] == "ADMIT_012")
    exact4_schema = [row for row in schema if row["admission_field_name"] in EXACT4_FIELDS]
    exact4_fields = [row for row in field_rows if row["field_name"] in EXACT4_FIELDS]
    exact4_contexts = [
        row for row in contexts
        if row["context_item"] in {
            "allowed_download_result_statuses", "successful_http_status_contract",
            "content_length_contract", "sha256_format_contract"
        }
    ]
    if not (
        audit_manifest["exact4_fields"] == list(EXACT4_FIELDS)
        and audit_manifest["authorized_admit_012_download_execution_count"] == 0
        and len(preconditions) == 24
        and len(prior_boundary) == 129
        and len(prior_issues) == 16
        and all(row["produced_by_download_execution"] == "false" for row in observed)
        and rule12 == {
            "admission_rule_id": ADMISSION_RULE_ID,
            "admission_rule_name": ADMISSION_RULE_NAME,
            "evidence_source": EVIDENCE_SOURCE,
            "required_status": REQUIRED_STATUS,
            "failure_severity": "blocking",
            "blocking_reason": BLOCKING_REASON,
            "evaluation_phase": EVALUATION_PHASE,
            "network_required": "false",
            "raw_structure_required": "false",
            "ready_for_future_implementation": "true",
        }
        and rule13["admission_rule_name"] == "download_failure_fail_closed"
        and rule13["blocking_reason"] == "download_failure_must_fail_closed"
        and rule13["admission_rule_id"] != rule12["admission_rule_id"]
        and [row["admission_field_name"] for row in exact4_schema] == list(EXACT4_FIELDS)
        and all(row["requirement_phase"] == "post_download" for row in exact4_schema)
        and exec12["candidate_field_dependencies"].split("|") == list(EXACT4_FIELDS)
        and exec12["download_execution_result_required"] == "true"
        and exec12["pure_in_memory_interface_possible"] == "true"
        and [row["field_name"] for row in exact4_fields] == list(EXACT4_FIELDS)
        and all(row["producer_scope"] == "download_execution_result" for row in exact4_fields)
        and len(exact4_contexts) == 4
        and all(row["required_by_rules"] == "ADMIT_012|ADMIT_013" for row in exact4_contexts)
    ):
        raise ValueError("committed ADMIT_012/013 contract evidence mismatch")
    source_text = {source.path.as_posix(): source.content.decode() for source in snapshot}
    for path, _field_name, literal in HISTORICAL_STATUS_LITERALS:
        if f'"{literal}"' not in source_text[path]:
            raise ValueError(f"historical status literal drift: {path}:{literal}")
    raw_precedent = source_text[
        "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py"
    ]
    adapter_precedent = source_text[
        "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py"
    ]
    tamper_precedent = source_text[
        "tests/test_covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1.py"
    ]
    if (
        "EvaluationResultDesign" not in raw_precedent
        or "INDEPENDENT_ORACLE_NAME" not in adapter_precedent
        or "semantic_tamper" not in tamper_precedent
    ):
        raise ValueError("design-only or synchronized-tamper precedent unavailable")


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _bool(value: bool) -> str:
    return str(value).lower()


CONTRACT_COLUMNS = (
    "field_order", "field_name", "requirement_phase", "producer_scope", "exact_builtin_type",
    "subclasses_allowed", "normalization_allowed", "presence_required", "missing_reason",
    "type_invalid_reason", "value_invalid_reason", "value_contract", "enum_version",
    "ordered_allowed_values", "success_subset", "legal_minimum", "legal_maximum",
    "future_success_minimum", "future_success_maximum", "admit_012_executes_success_judgment",
    "used_by_admit_012", "reserved_for_admit_013", "contract_passed",
)
ENUM_COLUMNS = (
    "row_order", "row_kind", "enum_version", "canonical_order", "status_value",
    "canonical_allowed", "success_member", "future_admit_013_disposition",
    "historical_source_path", "historical_field_name", "historical_literal",
    "promoted_to_canonical", "notes", "row_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "presence_representation",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "expected_contract_outcome", "expected_reason", "expected_first_failing_field",
    "expected_rule_blocking_reason", "future_admit_013_disposition",
    "observed_contract_outcome", "observed_reason", "observed_first_failing_field",
    "observed_rule_blocking_reason", "case_passed",
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
    specs = (
        ("download_result_status", "str", "exact member of ordered canonical enum success|failure"),
        ("observed_http_status", "int", "integer HTTP status in inclusive structural range 100..599"),
        ("observed_content_length_bytes", "int", "integer observed byte count >= 0; no V1 upper bound"),
        ("observed_sha256", "str", "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}"),
    )
    rows: list[dict[str, str]] = []
    for index, (field_name, type_name, value_contract) in enumerate(specs, 1):
        status = field_name == "download_result_status"
        http = field_name == "observed_http_status"
        rows.append({
            "field_order": str(index),
            "field_name": field_name,
            "requirement_phase": EVALUATION_PHASE,
            "producer_scope": "download_execution_result",
            "exact_builtin_type": type_name,
            "subclasses_allowed": "false",
            "normalization_allowed": "false",
            "presence_required": "true",
            "missing_reason": MISSING_REASONS[field_name],
            "type_invalid_reason": TYPE_INVALID_REASONS[field_name],
            "value_invalid_reason": VALUE_INVALID_REASONS[field_name],
            "value_contract": value_contract,
            "enum_version": STATUS_ENUM_VERSION if status else "",
            "ordered_allowed_values": "|".join(ALLOWED_DOWNLOAD_RESULT_STATUSES) if status else "",
            "success_subset": "|".join(SUCCESS_DOWNLOAD_RESULT_STATUSES) if status else "",
            "legal_minimum": str(HTTP_LEGAL_MINIMUM) if http else "",
            "legal_maximum": str(HTTP_LEGAL_MAXIMUM) if http else "",
            "future_success_minimum": str(HTTP_SUCCESS_MINIMUM) if http else "",
            "future_success_maximum": str(HTTP_SUCCESS_MAXIMUM) if http else "",
            "admit_012_executes_success_judgment": "false",
            "used_by_admit_012": "true",
            "reserved_for_admit_013": "true",
            "contract_passed": "true",
        })
    return rows


def _enum_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, value in enumerate(ALLOWED_DOWNLOAD_RESULT_STATUSES, 1):
        success = value in SUCCESS_DOWNLOAD_RESULT_STATUSES
        rows.append({
            "row_order": str(len(rows) + 1), "row_kind": "canonical_enum",
            "enum_version": STATUS_ENUM_VERSION, "canonical_order": str(index),
            "status_value": value, "canonical_allowed": "true", "success_member": _bool(success),
            "future_admit_013_disposition": (
                "pending_integrity_match_checks_not_implemented_here" if success
                else "blocked_not_implemented_here"
            ),
            "historical_source_path": "", "historical_field_name": "", "historical_literal": "",
            "promoted_to_canonical": "not_applicable", "notes": "closed V1 canonical enum",
            "row_passed": "true",
        })
    for path, field_name, literal in HISTORICAL_STATUS_LITERALS:
        rows.append({
            "row_order": str(len(rows) + 1), "row_kind": "historical_literal",
            "enum_version": STATUS_ENUM_VERSION, "canonical_order": "", "status_value": "",
            "canonical_allowed": "false", "success_member": "false",
            "future_admit_013_disposition": "not_applicable_historical_noncontract_evidence",
            "historical_source_path": path, "historical_field_name": field_name,
            "historical_literal": literal, "promoted_to_canonical": "false",
            "notes": "static historical naming evidence only; no alias conversion or semantic promotion",
            "row_passed": "true",
        })
    return rows


@dataclass(frozen=True)
class _TruthCase:
    case_id: str
    group: str
    values: tuple[object, object, object, object]
    outcome: str
    reason: str
    field_name: str
    future_disposition: str


def _truth_cases() -> tuple[_TruthCase, ...]:
    valid_sha = "0123456789abcdef" * 4
    pending = "pending_integrity_match_checks_not_implemented_here"
    blocked = "blocked_not_implemented_here"
    invalid = "not_reached_admit_012_contract_invalid"
    valid = ("success", 200, 1, valid_sha)

    def case(case_id: str, group: str, values: tuple[object, object, object, object],
             outcome: str = "contract_valid", reason: str = "", field_name: str = "",
             disposition: str = pending) -> _TruthCase:
        return _TruthCase(case_id, group, values, outcome, reason, field_name, disposition)

    cases = [
        case("VALID_STATUS_SUCCESS", "canonical_valid", valid),
        case("VALID_STATUS_FAILURE", "canonical_valid", ("failure", 200, 1, valid_sha), disposition=blocked),
        case("VALID_HTTP_100", "canonical_valid", ("success", 100, 1, valid_sha), disposition=blocked),
        case("VALID_HTTP_299", "canonical_valid", ("success", 299, 1, valid_sha)),
        case("VALID_HTTP_300", "canonical_valid", ("success", 300, 1, valid_sha), disposition=blocked),
        case("VALID_HTTP_599", "canonical_valid", ("success", 599, 1, valid_sha), disposition=blocked),
        case("VALID_CONTENT_ZERO", "canonical_valid", ("success", 200, 0, valid_sha)),
        case("VALID_CONTENT_LARGE", "canonical_valid", ("success", 200, 10**30, valid_sha)),
        case("VALID_SHA_LOWERCASE64", "canonical_valid", ("success", 200, 1, "abcdef0123456789" * 4)),
        case("MISSING_STATUS", "missing", (_MISSING, 200, 1, valid_sha), "missing", MISSING_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("MISSING_HTTP", "missing", ("success", _MISSING, 1, valid_sha), "missing", MISSING_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("MISSING_CONTENT", "missing", ("success", 200, _MISSING, valid_sha), "missing", MISSING_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("MISSING_SHA", "missing", ("success", 200, 1, _MISSING), "missing", MISSING_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("MULTI_MISSING_STATUS_HTTP", "missing", (_MISSING, _MISSING, 1, valid_sha), "missing", MISSING_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("MULTI_MISSING_HTTP_SHA", "missing", ("success", _MISSING, 1, _MISSING), "missing", MISSING_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("STATUS_NONE_PRESENT", "status_invalid", (None, 200, 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("STATUS_EMPTY_PRESENT", "status_invalid", ("", 200, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("STATUS_UNKNOWN", "status_invalid", ("unknown", 200, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("STATUS_UPPERCASE_ALIAS", "status_invalid", ("SUCCESS", 200, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("STATUS_STR_SUBCLASS", "status_invalid", (_StringSubclass("success"), 200, 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("STATUS_NON_STR", "status_invalid", (1, 200, 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("HTTP_BOOL", "http_invalid", ("success", False, 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("HTTP_INT_SUBCLASS", "http_invalid", ("success", _IntSubclass(200), 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("HTTP_STRING", "http_invalid", ("success", "200", 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("HTTP_99", "http_invalid", ("success", 99, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("HTTP_600", "http_invalid", ("success", 600, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("CONTENT_BOOL", "content_invalid", ("success", 200, False, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("CONTENT_INT_SUBCLASS", "content_invalid", ("success", 200, _IntSubclass(1), valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("CONTENT_STRING", "content_invalid", ("success", 200, "1", valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("CONTENT_NEGATIVE", "content_invalid", ("success", 200, -1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("SHA_NONE_PRESENT", "sha_invalid", ("success", 200, 1, None), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_BYTES", "sha_invalid", ("success", 200, 1, valid_sha.encode()), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_STR_SUBCLASS", "sha_invalid", ("success", 200, 1, _StringSubclass(valid_sha)), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_EMPTY", "sha_invalid", ("success", 200, 1, ""), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_63", "sha_invalid", ("success", 200, 1, "a" * 63), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_65", "sha_invalid", ("success", 200, 1, "a" * 65), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_UPPERCASE", "sha_invalid", ("success", 200, 1, valid_sha.upper()), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_MIXED_CASE", "sha_invalid", ("success", 200, 1, "A" + valid_sha[1:]), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_NONHEX", "sha_invalid", ("success", 200, 1, "g" + valid_sha[1:]), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_WHITESPACE", "sha_invalid", ("success", 200, 1, " " + valid_sha[:63]), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_0X_PREFIX", "sha_invalid", ("success", 200, 1, "0x" + valid_sha[:62]), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("SHA_SHA256_PREFIX", "sha_invalid", ("success", 200, 1, "sha256:" + valid_sha[:57]), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("MULTI_EARLIER_INVALID_LATER_MISSING", "multi_invalid_precedence", ("unknown", 200, 1, _MISSING), "missing", MISSING_REASONS[EXACT4_FIELDS[3]], EXACT4_FIELDS[3], invalid),
        case("MULTI_MISSING_PRECEDENCE", "multi_invalid_precedence", (_MISSING, 200, _MISSING, valid_sha), "missing", MISSING_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("MULTI_TYPE_FAILURES", "multi_invalid_precedence", (None, False, 1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("MULTI_TYPE_VALUE_FAILURES", "multi_invalid_precedence", ("success", "200", -1, valid_sha), "invalid", TYPE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("MULTI_STATUS_HTTP_INVALID", "multi_invalid_precedence", ("unknown", 99, 1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[0]], EXACT4_FIELDS[0], invalid),
        case("MULTI_HTTP_CONTENT_INVALID", "multi_invalid_precedence", ("success", 99, -1, valid_sha), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[1]], EXACT4_FIELDS[1], invalid),
        case("MULTI_CONTENT_SHA_INVALID", "multi_invalid_precedence", ("success", 200, -1, valid_sha.upper()), "invalid", VALUE_INVALID_REASONS[EXACT4_FIELDS[2]], EXACT4_FIELDS[2], invalid),
        case("BOUNDARY_FAILURE_STATUS", "admit_013_boundary", ("failure", 200, 1, valid_sha), disposition=blocked),
        case("BOUNDARY_VALID_4XX", "admit_013_boundary", ("success", 404, 1, valid_sha), disposition=blocked),
        case("BOUNDARY_VALID_5XX_FAILURE", "admit_013_boundary", ("failure", 503, 1, valid_sha), disposition=blocked),
    ]
    return tuple(cases)


def _representation(value: object) -> str:
    if value is _MISSING:
        return "<MISSING>"
    if type(value) is _StringSubclass:
        return f"<str-subclass:{str(value)!r}>"
    if type(value) is _IntSubclass:
        return f"<int-subclass:{int(value)}>"
    return repr(value)


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for order, case in enumerate(_truth_cases(), 1):
        result = classify_admit_012_download_integrity_fields_design(*case.values)
        expected_blocker = "" if case.outcome == "contract_valid" else BLOCKING_REASON
        passed = (
            result.contract_outcome == case.outcome
            and result.reason == case.reason
            and result.first_failing_field == case.field_name
            and result.rule_blocking_reason == expected_blocker
        )
        rows.append({
            "case_order": str(order), "case_id": case.case_id, "case_group": case.group,
            "presence_representation": "|".join(
                f"{field_name}={'missing' if value is _MISSING else 'present'}"
                for field_name, value in zip(EXACT4_FIELDS, case.values)
            ),
            "download_result_status_representation": _representation(case.values[0]),
            "observed_http_status_representation": _representation(case.values[1]),
            "observed_content_length_bytes_representation": _representation(case.values[2]),
            "observed_sha256_representation": _representation(case.values[3]),
            "expected_contract_outcome": case.outcome, "expected_reason": case.reason,
            "expected_first_failing_field": case.field_name,
            "expected_rule_blocking_reason": expected_blocker,
            "future_admit_013_disposition": case.future_disposition,
            "observed_contract_outcome": result.contract_outcome, "observed_reason": result.reason,
            "observed_first_failing_field": result.first_failing_field,
            "observed_rule_blocking_reason": result.rule_blocking_reason,
            "case_passed": _bool(passed),
        })
    if not all(row["case_passed"] == "true" for row in rows):
        raise ValueError("truth oracle disagrees with explicit matrix")
    return rows


def _source_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "python_source"
    if path.suffix == ".csv":
        return "committed_csv"
    if path.suffix == ".json":
        return "committed_manifest"
    return "tracked_text"


def _source_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": source.path.as_posix(),
        "source_kind": _source_kind(source.path), "base_tree_mode": source.base_mode,
        "expected_sha256": SOURCE_SHA256[source.path.as_posix()], "base_tree_sha256": source.sha256,
        "filesystem_sha256": source.sha256, "frozen_snapshot_sha256": source.sha256,
        "git_tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true",
        "non_symlink": "true", "parent_chain_non_symlink": "true", "safe_descendant": "true",
        "pinned_fd_read": "true", "triple_sha256_passed": "true", "source_boundary_passed": "true",
    } for index, source in enumerate(snapshot, 1)]


RESOLVED_ISSUES = {
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
    "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
}
OPEN_REQUIRED_ISSUES = {
    "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
    "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
}
ISSUE_TRANSITION = "admit_012_download_integrity_field_contract_frozen_v1"


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    rows = _csv_rows(snapshot, AUDIT_ROOT / "covapie_admit_012_issue_readiness_inventory.csv")
    if tuple(rows[0]) != ISSUE_COLUMNS or len(rows) != 16:
        raise ValueError("predecessor Exact16 issue contract drift")
    for row in rows:
        if row["issue_id"] in RESOLVED_ISSUES:
            row["status"] = "resolved"
            row["integration_transition"] = ISSUE_TRANSITION
    by_id = {row["issue_id"]: row for row in rows}
    if not all(by_id[issue]["status"] == "resolved" for issue in RESOLVED_ISSUES):
        raise ValueError("required issue transition incomplete")
    if not all(by_id[issue]["status"] == "open" for issue in OPEN_REQUIRED_ISSUES):
        raise ValueError("required open issue was closed")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage issue affected-rule set changed")
    return rows


def _readiness() -> dict[str, bool]:
    true_keys = (
        "admit_012_preconditions_audited",
        "admit_012_download_integrity_field_contract_frozen",
        "admit_012_download_result_status_enum_frozen",
        "admit_012_field_semantics_complete",
        "admit_012_presence_semantics_resolved",
        "admit_012_validation_precedence_resolved",
        "admit_012_admit_013_field_contract_boundary_frozen",
        "feature_semantics_audit_required_before_training",
    )
    false_keys = (
        "admit_012_routing_responsibility_resolved",
        "ready_for_admit_012_standalone_evaluator_interface_implementation",
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
    return {**{key: True for key in true_keys}, **{key: False for key in false_keys}}


def build_artifacts(snapshot: tuple[_Source, ...] | None = None) -> dict[str, bytes]:
    snapshot = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_committed_contracts(snapshot)
    contract_rows = _contract_rows()
    enum_rows = _enum_rows()
    truth_rows = _truth_rows()
    source_rows = _source_rows(snapshot)
    issue_rows = _issue_rows(snapshot)
    files = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        ENUM_FILE: _csv_bytes(ENUM_COLUMNS, enum_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        ISSUE_FILE: _csv_bytes(ISSUE_COLUMNS, issue_rows),
    }
    output_sha = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    group_counts = {
        group: sum(row["case_group"] == group for row in truth_rows)
        for group in sorted({row["case_group"] for row in truth_rows})
    }
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "manifest_schema_version": "covapie_admit_012_download_integrity_field_contract_manifest_v1",
        "project": PROJECT, "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": EVIDENCE_SOURCE, "evaluation_phase": EVALUATION_PHASE,
        "required_status": REQUIRED_STATUS, "blocking_reason": BLOCKING_REASON,
        "exact4_fields": list(EXACT4_FIELDS), "exact4_presence_required": True,
        "status_enum_version": STATUS_ENUM_VERSION,
        "ordered_allowed_download_result_statuses": list(ALLOWED_DOWNLOAD_RESULT_STATUSES),
        "success_download_result_status_subset": list(SUCCESS_DOWNLOAD_RESULT_STATUSES),
        "historical_status_literal_count": len(HISTORICAL_STATUS_LITERALS),
        "historical_status_literals_promoted_automatically": False,
        "observed_http_status_contract": {
            "exact_builtin_type": "int", "subclasses_allowed": False,
            "legal_minimum": HTTP_LEGAL_MINIMUM, "legal_maximum": HTTP_LEGAL_MAXIMUM,
            "future_success_minimum": HTTP_SUCCESS_MINIMUM, "future_success_maximum": HTTP_SUCCESS_MAXIMUM,
            "admit_012_executes_success_judgment": False,
        },
        "observed_content_length_bytes_contract": {
            "exact_builtin_type": "int", "subclasses_allowed": False,
            "legal_minimum": 0, "legal_maximum": None, "zero_allowed": True,
            "recomputed_from_file_inside_classifier": False,
        },
        "observed_sha256_contract": {
            "exact_builtin_type": "str", "subclasses_allowed": False,
            "length": 64, "grammar": SHA256_PATTERN, "case_policy": "ASCII_lowercase_only",
            "normalization_allowed": False, "recomputed_from_file_inside_classifier": False,
        },
        "presence_semantics": {
            "order": list(PRESENCE_ORDER), "phase_before_type_value_validation": True,
            "only_private_design_missing_sentinel_means_missing": True,
            "none_empty_zero_false_implicitly_missing": False,
        },
        "validation_precedence": {
            "phase_order": ["presence", "type_and_value"],
            "presence_order": list(PRESENCE_ORDER), "validation_order": list(VALIDATION_ORDER),
            "within_field_order": list(WITHIN_FIELD_PRECEDENCE),
        },
        "reason_vocabulary": list(REASON_VOCABULARY),
        "contract_outcomes": ["contract_valid", "missing", "invalid"],
        "admit_012_responsibilities": [
            "Exact4_presence", "exact_builtin_types", "status_enum_membership", "HTTP_structural_range",
            "content_length_structural_range", "SHA256_representation_grammar", "deterministic_reason_precedence",
        ],
        "admit_012_non_responsibilities": [
            "status_success_judgment", "HTTP_2xx_judgment", "content_length_header_or_file_match",
            "SHA256_expected_digest_match", "candidate_materialization_admission",
        ],
        "future_admit_013_responsibilities_not_implemented_here": [
            "non_success_status_fail_closed", "non_2xx_fail_closed", "integrity_mismatch_fail_closed",
            "combined_download_admission_verdict",
        ],
        "admit_012_routing_responsibility_resolved": False,
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED": "open",
        "ADMIT_012_RESULT_CONTRACT_UNRESOLVED": "open",
        "design_classifier_only": True, "formal_evaluator_implemented": False,
        "formal_result_contract_defined": False, "unified_adapter_or_runtime_changed": False,
        "source_count": len(snapshot), "source_path_list_sha256": EXPECTED_SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": EXPECTED_SOURCE_PATH_SHA256_PAIRS_SHA256,
        "output_files": list(OUTPUT_FILES), "output_file_count": len(OUTPUT_FILES),
        "row_counts": {
            "field_contract": len(contract_rows), "status_enum_and_history": len(enum_rows),
            "truth_matrix": len(truth_rows), "source_boundary": len(source_rows), "issue_inventory": len(issue_rows),
        },
        "truth_matrix_group_counts": group_counts,
        "resolved_issue_ids": sorted(RESOLVED_ISSUES), "issue_integration_transition": ISSUE_TRANSITION,
        "required_open_issue_ids": sorted(OPEN_REQUIRED_ISSUES),
        "authorized_admit_012_download_execution_count": 0,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": "design_covapie_admit_012_formal_evaluator_interface_contract_v1",
        "readiness": readiness,
        "safety": {
            "network": False, "raw": False, "provider_mapping": False, "real_download": False,
            "model_or_checkpoint": False, "runtime_change": False, "training": False,
        },
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": output_sha, "all_checks_passed": True,
    }
    manifest.update(readiness)
    files[MANIFEST_FILE] = _json_bytes(manifest)
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
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
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
        descriptor = os.open(leaf, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
        try:
            identity = _identity(before)
            if _identity(os.fstat(descriptor)) != identity:
                raise ValueError("output stat/open race")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(descriptor)) != identity:
                raise ValueError("output descriptor identity drift")
        finally:
            os.close(descriptor)
        if _identity(os.lstat(leaf)) != identity:
            raise ValueError("output lexical replacement")
        if b"".join(chunks) != expected:
            return False
    return True


def _cleanup_staging(staging: Path) -> None:
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
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if (
        stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
        or parent.resolve(strict=True) != parent
    ):
        raise ValueError("unsafe output parent")
    root_exists = root.exists()
    payloads = build_artifacts()
    if root_exists:
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent))
    try:
        for name, data in payloads.items():
            _write_leaf(staging / name, data)
        descriptor = os.open(staging, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _rename_noreplace(staging, root)
        descriptor = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
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


def run_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    return materialize_contract(output_root)

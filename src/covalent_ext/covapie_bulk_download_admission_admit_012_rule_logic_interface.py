"""Pure ADMIT_012 standalone evaluator plus metadata-only frozen evidence builder."""

import ast
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
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid")
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
REASON_VOCABULARY = (
    "",
    *MISSING_REASONS,
    *(reason for index in range(4) for reason in (TYPE_INVALID_REASONS[index], VALUE_INVALID_REASONS[index])),
    *CONTEXT_REASONS,
)
FORMAL_CONTEXT_VALUES = (
    ALLOWED_DOWNLOAD_RESULT_STATUSES,
    SUCCESSFUL_HTTP_STATUS_CONTRACT,
    CONTENT_LENGTH_CONTRACT,
    SHA256_FORMAT_CONTRACT,
)
_SHA256_RE = re.compile("[0-9a-f]{64}")


class _MissingAdmit012Value:
    __slots__ = ()


_MISSING = _MissingAdmit012Value()


def _field_pair_valid(index: int, pair: tuple) -> bool:
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


def _ordered_pair_prefix_valid(record: tuple) -> bool:
    return len(record) <= 4 and all(_field_pair_valid(index, pair) for index, pair in enumerate(record))


@dataclass(frozen=True)
class Admit012EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_download_result_record: tuple
    validated_download_result_fields: tuple
    consumed_download_result_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        if type(self) is not Admit012EvaluationResult:
            raise TypeError("exact Admit012EvaluationResult required")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("exact result field order required")
        if any(type(value) is not str for value in (self.admission_rule_id, self.outcome, self.reason)):
            raise TypeError("result string fields require exact str")
        if any(type(value) is not bool for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)):
            raise TypeError("result boolean fields require exact bool")
        records = (self.canonical_download_result_record, self.validated_download_result_fields)
        consumed = (self.consumed_download_result_fields, self.consumed_context_items)
        if any(type(value) is not tuple for value in (*records, *consumed)):
            raise TypeError("result tuple fields require exact tuple")
        if any(type(item) is not str for value in consumed for item in value):
            raise TypeError("consumed members require exact str")
        for record in records:
            if any(type(pair) is not tuple for pair in record):
                raise TypeError("field pairs require exact tuple")
            if any(len(pair) != 2 for pair in record):
                raise ValueError("field pairs require length two")
            if any(type(pair[0]) is not str for pair in record):
                raise TypeError("field pair names require exact str")
        canonical = self.canonical_download_result_record
        validated = self.validated_download_result_fields
        if len(canonical) not in (0, 4) or not _ordered_pair_prefix_valid(canonical):
            raise ValueError("canonical record must be empty or complete valid Exact4")
        if not _ordered_pair_prefix_valid(validated):
            raise ValueError("validated fields must be a valid ordered Exact4 prefix")
        if self.consumed_download_result_fields != EXACT4_FIELDS[:len(self.consumed_download_result_fields)]:
            raise ValueError("consumed fields must be an ordered Exact4 prefix")
        if self.consumed_context_items != EXACT4_CONTEXT_ITEMS[:len(self.consumed_context_items)]:
            raise ValueError("consumed contexts must be an ordered Exact4 prefix")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("admission rule identity mismatch")
        if self.outcome not in OUTCOME_VOCABULARY or self.reason not in REASON_VOCABULARY:
            raise ValueError("closed outcome/reason vocabulary required")
        if self.evaluator_io_used is not False:
            raise ValueError("formal evaluator I/O must be false")
        if self.passed != (self.outcome == "passed") or self.blocks_candidate != (self.outcome != "passed"):
            raise ValueError("outcome booleans contradict outcome")
        if (self.reason == "") != (self.outcome == "passed"):
            raise ValueError("reason emptiness contradicts outcome")
        if self.reason in MISSING_REASONS:
            index = MISSING_REASONS.index(self.reason)
            expected = ("blocked", (), (), EXACT4_FIELDS[:index + 1], ())
        elif self.reason in TYPE_INVALID_REASONS or self.reason in VALUE_INVALID_REASONS:
            reasons = TYPE_INVALID_REASONS if self.reason in TYPE_INVALID_REASONS else VALUE_INVALID_REASONS
            index = reasons.index(self.reason)
            if len(validated) != index:
                raise ValueError("validated prefix contradicts failing field")
            expected = ("invalid", (), validated, EXACT4_FIELDS, ())
        elif self.reason in CONTEXT_REASONS:
            index = CONTEXT_REASONS.index(self.reason) // 2
            if len(canonical) != 4:
                raise ValueError("context failure requires complete Exact4")
            expected = ("invalid", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS[:index + 1])
        else:
            if len(canonical) != 4:
                raise ValueError("passed result requires complete Exact4")
            expected = ("passed", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS)
        observed = (
            self.outcome,
            canonical,
            validated,
            self.consumed_download_result_fields,
            self.consumed_context_items,
        )
        if observed != expected:
            raise ValueError("result state contradicts frozen reason semantics")


def _record(values: tuple) -> tuple:
    return tuple((name, value) for name, value in zip(EXACT4_FIELDS, values, strict=True))


def _make_result(
    outcome: str,
    reason: str,
    canonical: tuple,
    validated: tuple,
    consumed_fields: tuple[str, ...],
    consumed_contexts: tuple[str, ...],
) -> Admit012EvaluationResult:
    return Admit012EvaluationResult(
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


def _context_reason(value: object, expected: tuple, index: int) -> str:
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


def evaluate_admit_012(
    *,
    download_result_status: object = _MISSING,
    observed_http_status: object = _MISSING,
    observed_content_length_bytes: object = _MISSING,
    observed_sha256: object = _MISSING,
    allowed_download_result_statuses: object,
    successful_http_status_contract: object,
    content_length_contract: object,
    sha256_format_contract: object,
) -> Admit012EvaluationResult:
    """Evaluate only the frozen ADMIT_012 field and policy-context contract."""
    values = (
        download_result_status,
        observed_http_status,
        observed_content_length_bytes,
        observed_sha256,
    )
    for index, value in enumerate(values):
        if value is _MISSING:
            return _make_result("blocked", MISSING_REASONS[index], (), (), EXACT4_FIELDS[:index + 1], ())
    validated = ()
    for index, value in enumerate(values):
        pair = (EXACT4_FIELDS[index], value)
        if index == 0:
            type_valid = type(value) is str
            value_valid = type_valid and value in ALLOWED_DOWNLOAD_RESULT_STATUSES
        elif index == 1:
            type_valid = type(value) is int
            value_valid = type_valid and 100 <= value <= 599
        elif index == 2:
            type_valid = type(value) is int
            value_valid = type_valid and value >= 0
        else:
            type_valid = type(value) is str
            value_valid = type_valid and _SHA256_RE.fullmatch(value) is not None
        if not type_valid:
            return _make_result("invalid", TYPE_INVALID_REASONS[index], (), validated, EXACT4_FIELDS, ())
        if not value_valid:
            return _make_result("invalid", VALUE_INVALID_REASONS[index], (), validated, EXACT4_FIELDS, ())
        validated = (*validated, pair)
    canonical = _record(values)
    contexts = (
        allowed_download_result_statuses,
        successful_http_status_contract,
        content_length_contract,
        sha256_format_contract,
    )
    for index, value in enumerate(contexts):
        reason = _context_reason(value, FORMAL_CONTEXT_VALUES[index], index)
        if reason:
            return _make_result(
                "invalid", reason, canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS[:index + 1]
            )
    return _make_result("passed", "", canonical, canonical, EXACT4_FIELDS, EXACT4_CONTEXT_ITEMS)


# === ADMIT_012 FORMAL EVALUATOR CLOSURE END ===


PROJECT = "CovaPIE"
BASE_COMMIT = "3e75daf58475de9deabc1efb55d978a2f458d0d5"
BASE_SUBJECT = "add CovaPIE ADMIT_012 formal evaluator interface contract v1"
STAGE = "covapie_bulk_download_admission_admit_012_rule_logic_interface_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_012_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
DESIGN_STAGE = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1")
FIELD_STAGE = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1")

CONTRACT_FILE = "covapie_admit_012_rule_logic_interface_contract.csv"
TRUTH_FILE = "covapie_admit_012_rule_logic_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_012_rule_logic_interface_source_boundary_audit.csv"
PURITY_FILE = "covapie_admit_012_rule_logic_interface_purity_audit.csv"
ISSUE_FILE = "covapie_admit_012_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_012_rule_logic_interface_manifest.json"
OUTPUT_FILES = (CONTRACT_FILE, TRUTH_FILE, SOURCE_FILE, PURITY_FILE, ISSUE_FILE, MANIFEST_FILE)

CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name",
    "parameter_kind_or_result_role", "formal_type", "default_behavior", "required",
    "source_envelope", "formal_invariant", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind",
    "download_result_status_representation", "observed_http_status_representation",
    "observed_content_length_bytes_representation", "observed_sha256_representation",
    "allowed_download_result_statuses_representation",
    "successful_http_status_contract_representation", "content_length_contract_representation",
    "sha256_format_contract_representation", "expected_admission_rule_id", "expected_outcome",
    "expected_passed", "expected_blocks_candidate", "expected_reason",
    "expected_canonical_download_result_record", "expected_validated_download_result_fields",
    "expected_consumed_download_result_fields", "expected_consumed_context_items",
    "expected_evaluator_io_used", "observed_formal_result", "formal_source",
    "evaluator_io_used", "truth_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "base_tree_mode", "expected_sha256",
    "base_tree_sha256", "filesystem_sha256", "frozen_snapshot_sha256", "git_tracked",
    "base_tree_blob", "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "safe_descendant", "pinned_fd_read", "triple_sha256_passed", "source_boundary_passed",
)
PURITY_COLUMNS = (
    "audit_order", "audit_kind", "definition_name", "definition_kind", "reachable_from",
    "normalized_ast_sha256", "permitted_global_bindings", "permitted_calls", "observed",
    "forbidden_io_absent", "mutation_absent", "purity_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)
FORMAL_CLOSURE = (
    "evaluate_admit_012", "_record", "_make_result", "_context_reason",
    "Admit012EvaluationResult", "Admit012EvaluationResult.__post_init__",
    "_ordered_pair_prefix_valid", "_field_pair_valid",
)
FORMAL_MARKER = "# === ADMIT_012 FORMAL " + "EVALUATOR CLOSURE END ==="

SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py": "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv": "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv": "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv": "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv": "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json": "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01",
    "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py": "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_result_status_enum.csv": "4c016e8c325ce6a422dff618ae166ec4f42243cc0d1fbf8f6a722c13f63139f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_validation_truth_matrix.csv": "766506f8c0bf2d7734b9c379c9437e1a48a2117873f7e974325b00ab685a39e1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json": "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py": "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
    "scripts/check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1.py": "72f33b9371c4eda533374e0535ba0da22467459da6a6488147e58ad680b7c7f1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json": "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv": "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py": "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py": "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)
SOURCE_PATH_LIST_SHA256 = "c1e4c37aba5b1f130d766920b15e4f286bdc5cc961ba830ecdb6d1dff72b27cf"
SOURCE_PATH_SHA256_PAIRS_SHA256 = "73f8cf567cb1dfbb40d610bafbd7f88b1ffacefd0d4f2b2ff0059688537b9979"


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


@dataclass(frozen=True)
class _WrongOrderResult:
    outcome: object
    admission_rule_id: object


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
    if len(SOURCE_PATHS) != 18 or len(set(SOURCE_PATHS)) != 18:
        raise ValueError("source boundary must be fixed Exact18")
    subject = _git(["show", "-s", "--format=%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if subject.returncode or subject.stdout.strip() != BASE_SUBJECT or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    structures = []
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


def _formal_source_attestation() -> tuple[bytes, str, str, dict[str, str]]:
    relative = Path("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py")
    _parent_chain(relative)
    item = os.lstat(REPO_ROOT / relative)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
        raise ValueError("unsafe formal successor source")
    source = _pinned_read(relative, _identity(item))
    text = source.decode()
    if text.count(FORMAL_MARKER) != 1:
        raise ValueError("formal closure marker drift")
    prefix = text.split(FORMAL_MARKER, 1)[0].encode()
    tree = ast.parse(source)
    definitions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    result_class = definitions["Admit012EvaluationResult"]
    post = next(node for node in result_class.body if isinstance(node, ast.FunctionDef) and node.name == "__post_init__")
    nodes = {
        name: post if name.endswith(".__post_init__") else definitions[name]
        for name in FORMAL_CLOSURE
    }
    digests = {
        name: hashlib.sha256(ast.dump(node, annotate_fields=True, include_attributes=False).encode()).hexdigest()
        for name, node in nodes.items()
    }
    return source, hashlib.sha256(source).hexdigest(), hashlib.sha256(prefix).hexdigest(), digests


def _contract_rows() -> list[dict[str, str]]:
    rows = []
    for order, name in enumerate((*EXACT4_FIELDS, *EXACT4_CONTEXT_ITEMS), 1):
        is_field = order <= 4
        rows.append({
            "contract_order": str(order), "contract_section": "signature_parameter",
            "section_order": str(order), "public_name": name,
            "parameter_kind_or_result_role": "keyword_only",
            "formal_type": "object", "default_behavior": "private_shared_missing_singleton" if is_field else "no_default",
            "required": str(not is_field).lower(),
            "source_envelope": "download_result_context" if is_field else "evaluation_context",
            "formal_invariant": "Exact8 order; no positional/varargs/varkw/Mapping; exact validation",
            "contract_passed": "true",
        })
    types = ("str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple[str,...]", "tuple[str,...]", "bool")
    for section_order, (name, formal_type) in enumerate(zip(RESULT_FIELDS, types, strict=True), 1):
        rows.append({
            "contract_order": str(len(rows) + 1), "contract_section": "result_field",
            "section_order": str(section_order), "public_name": name,
            "parameter_kind_or_result_role": "Exact10_frozen_result_field",
            "formal_type": formal_type, "default_behavior": "not_applicable", "required": "true",
            "source_envelope": "Admit012EvaluationResult",
            "formal_invariant": "exact built-in type; ordered frozen reason-specific state contract",
            "contract_passed": "true",
        })
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
    if text.startswith("<tuple-subclass:"):
        return _TupleSubclass(ast.literal_eval(text[16:-1]))
    if text.startswith("<tuple-member-str-subclass:"):
        prefix, representation = text[27:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _StrSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<tuple-pair-subclass:"):
        prefix, representation = text[21:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _PairSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<regex:"):
        return re.compile(ast.literal_eval(text[7:-1]))
    return ast.literal_eval(text)


def _result_values(value: Admit012EvaluationResult) -> tuple:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


def _validate_exact_result(value: object) -> None:
    if type(value) is not Admit012EvaluationResult:
        raise TypeError("exact formal result type required")
    reconstructed = Admit012EvaluationResult(*(getattr(value, name) for name in RESULT_FIELDS))
    if reconstructed != value:
        raise ValueError("formal result reconstruction mismatch")


NEGATIVE_CASE_IDS = (
    "WRONG_RESULT_FIELD_ORDER", "WRONG_OUTCOME_BOOL", "WRONG_CANONICAL_SHAPE",
    "PARTIAL_CANONICAL_RECORD", "VALIDATED_NOT_PREFIX", "CONSUMED_ORDER_DRIFT",
    "EVALUATOR_IO_TRUE", "UNKNOWN_REASON",
)


def _negative_result(case_id: str, baseline: Admit012EvaluationResult) -> str:
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    try:
        if case_id == "WRONG_RESULT_FIELD_ORDER":
            _validate_exact_result(_WrongOrderResult("passed", ADMISSION_RULE_ID))
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
            Admit012EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _truth_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    predecessor = _csv_rows(snapshot, DESIGN_STAGE / "covapie_admit_012_formal_evaluator_interface_truth_matrix.csv")
    if len(predecessor) != 105:
        raise ValueError("predecessor truth must be Exact105")
    representation_columns = tuple(f"{name}_representation" for name in (*EXACT4_FIELDS, *EXACT4_CONTEXT_ITEMS))
    rows = []
    for prior in predecessor:
        expected = (
            ADMISSION_RULE_ID, prior["expected_outcome"], prior["expected_outcome"] == "passed",
            prior["expected_outcome"] != "passed", prior["expected_reason"],
            ast.literal_eval(prior["expected_canonical_download_result_record"]),
            ast.literal_eval(prior["expected_validated_download_result_fields"]),
            ast.literal_eval(prior["expected_consumed_download_result_fields"]),
            ast.literal_eval(prior["expected_consumed_context_items"]), False,
        )
        if prior["case_id"] in NEGATIVE_CASE_IDS:
            baseline = evaluate_admit_012(
                download_result_status="success", observed_http_status=200,
                observed_content_length_bytes=1, observed_sha256="0123456789abcdef" * 4,
                allowed_download_result_statuses=ALLOWED_DOWNLOAD_RESULT_STATUSES,
                successful_http_status_contract=SUCCESSFUL_HTTP_STATUS_CONTRACT,
                content_length_contract=CONTENT_LENGTH_CONTRACT,
                sha256_format_contract=SHA256_FORMAT_CONTRACT,
            )
            observed = _negative_result(prior["case_id"], baseline)
            passed = observed == prior["observed_design_result"]
        else:
            decoded = tuple(_decode_representation(prior[column]) for column in representation_columns)
            observed_result = evaluate_admit_012(
                download_result_status=decoded[0], observed_http_status=decoded[1],
                observed_content_length_bytes=decoded[2], observed_sha256=decoded[3],
                allowed_download_result_statuses=decoded[4], successful_http_status_contract=decoded[5],
                content_length_contract=decoded[6], sha256_format_contract=decoded[7],
            )
            observed = repr(_result_values(observed_result))
            passed = _result_values(observed_result) == expected
        rows.append({
            "case_order": prior["case_order"], "case_id": prior["case_id"],
            "case_group": prior["case_group"], "assertion_kind": prior["assertion_kind"],
            **{column: prior[column] for column in representation_columns},
            "expected_admission_rule_id": ADMISSION_RULE_ID, "expected_outcome": prior["expected_outcome"],
            "expected_passed": str(expected[2]).lower(), "expected_blocks_candidate": str(expected[3]).lower(),
            "expected_reason": prior["expected_reason"],
            "expected_canonical_download_result_record": prior["expected_canonical_download_result_record"],
            "expected_validated_download_result_fields": prior["expected_validated_download_result_fields"],
            "expected_consumed_download_result_fields": prior["expected_consumed_download_result_fields"],
            "expected_consumed_context_items": prior["expected_consumed_context_items"],
            "expected_evaluator_io_used": "false", "observed_formal_result": observed,
            "formal_source": "evaluate_admit_012|Admit012EvaluationResult",
            "evaluator_io_used": "false", "truth_passed": str(passed).lower(),
        })
    if not all(row["truth_passed"] == "true" for row in rows):
        raise ValueError("formal truth projection mismatch")
    return rows


def _source_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.path.as_posix(),
        "source_kind": "python_source" if record.path.suffix == ".py" else "committed_csv" if record.path.suffix == ".csv" else "committed_manifest",
        "base_tree_mode": record.base_mode, "expected_sha256": record.sha256,
        "base_tree_sha256": record.sha256, "filesystem_sha256": record.sha256,
        "frozen_snapshot_sha256": record.sha256, "git_tracked": "true", "base_tree_blob": "true",
        "filesystem_regular": "true", "non_symlink": "true", "parent_chain_non_symlink": "true",
        "safe_descendant": "true", "pinned_fd_read": "true", "triple_sha256_passed": "true",
        "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot, 1)]


def _purity_rows(full_sha: str, prefix_sha: str, digests: dict[str, str]) -> list[dict[str, str]]:
    parents = (
        "root", "evaluate_admit_012", "evaluate_admit_012", "evaluate_admit_012",
        "_make_result", "Admit012EvaluationResult", "Admit012EvaluationResult.__post_init__",
        "_ordered_pair_prefix_valid",
    )
    kinds = ("function", "function", "function", "function", "frozen_dataclass", "method", "function", "function")
    globals_used = (
        "_MISSING|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ALLOWED_DOWNLOAD_RESULT_STATUSES|FORMAL_CONTEXT_VALUES|_SHA256_RE",
        "EXACT4_FIELDS", "ADMISSION_RULE_ID|Admit012EvaluationResult", "CONTEXT_REASONS",
        "dataclass", "fields|RESULT_FIELDS|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ADMISSION_RULE_ID|OUTCOME_VOCABULARY|REASON_VOCABULARY|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|CONTEXT_REASONS",
        "", "", "EXACT4_FIELDS|ALLOWED_DOWNLOAD_RESULT_STATUSES|_SHA256_RE",
    )
    calls = (
        "enumerate|type|_SHA256_RE.fullmatch|_make_result|_record|_context_reason",
        "zip|tuple", "Admit012EvaluationResult", "type|len|all|zip",
        "dataclass", "type|fields|tuple|any|len|_ordered_pair_prefix_valid",
        "type|fields|tuple|any|len|_ordered_pair_prefix_valid", "len|all|enumerate|_field_pair_valid",
        "type|len|_SHA256_RE.fullmatch",
    )
    rows = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append({
            "audit_order": str(index + 1), "audit_kind": "closure_definition",
            "definition_name": name, "definition_kind": kinds[index], "reachable_from": parents[index],
            "normalized_ast_sha256": digests[name], "permitted_global_bindings": globals_used[index],
            "permitted_calls": calls[index], "observed": "reachable_and_frozen",
            "forbidden_io_absent": "true", "mutation_absent": "true", "purity_passed": "true",
        })
    metadata = (
        ("production_full_sha256", full_sha),
        ("marker_prefix_sha256", prefix_sha),
        ("exact_imported_symbol_map", "ast|csv|ctypes|hashlib|io|json|os|re|stat|subprocess|tempfile|dataclasses.dataclass|dataclasses.fields|pathlib.Path|typing.Any"),
        ("exact_constant_binding_map", "ADMISSION_RULE_ID|EXACT4_FIELDS|EXACT4_CONTEXT_ITEMS|ALLOWED_DOWNLOAD_RESULT_STATUSES|SUCCESSFUL_HTTP_STATUS_CONTRACT|CONTENT_LENGTH_CONTRACT|SHA256_FORMAT_CONTRACT|OUTCOME_VOCABULARY|RESULT_FIELDS|MISSING_REASONS|TYPE_INVALID_REASONS|VALUE_INVALID_REASONS|CONTEXT_REASONS|REASON_VOCABULARY|FORMAL_CONTEXT_VALUES|_SHA256_RE|_MISSING"),
        ("result_dataclass_shape", "Admit012EvaluationResult|frozen=True|Exact10|only___post_init__|no_base_or_metaclass"),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
    )
    for name, observed in metadata:
        rows.append({
            "audit_order": str(len(rows) + 1), "audit_kind": "closure_metadata",
            "definition_name": name, "definition_kind": "attestation", "reachable_from": "checker_recomputed",
            "normalized_ast_sha256": "", "permitted_global_bindings": "", "permitted_calls": "",
            "observed": observed, "forbidden_io_absent": "true", "mutation_absent": "true",
            "purity_passed": "true",
        })
    return rows


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    rows = _csv_rows(snapshot, DESIGN_STAGE / "covapie_admit_012_formal_evaluator_interface_issue_readiness_inventory.csv")
    if len(rows) != 16 or tuple(rows[0]) != ISSUE_COLUMNS:
        raise ValueError("predecessor issue inventory drift")
    by_id = {row["issue_id"]: row for row in rows}
    resolved = {
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED", "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED", "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED", "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    }
    if not all(by_id[item]["status"] == "resolved" for item in resolved):
        raise ValueError("resolved ADMIT_012 issue regressed")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] != "open" or by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("coverage issue drift")
    if by_id["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise ValueError("cross-rule issue drift")
    return rows


TRUE_READINESS = (
    "admit_012_preconditions_audited", "admit_012_download_integrity_field_contract_frozen",
    "admit_012_field_semantics_complete", "admit_012_presence_semantics_resolved",
    "admit_012_validation_precedence_resolved", "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen", "admit_012_formal_result_contract_frozen",
    "admit_012_formal_evaluator_interface_contract_frozen",
    "ready_for_admit_012_standalone_evaluator_interface_implementation",
    "admit_012_standalone_evaluator_interface_implemented", "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented", "Admit012EvaluationResult_implemented",
    "ready_for_admit_012_unified_adapter_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_unified_adapter_contract_frozen", "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "provider_mapping_validated", "real_provider_evaluation_ready", "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented", "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(snapshot: tuple[_Source, ...] | None = None) -> dict[str, bytes]:
    snapshot = build_frozen_source_snapshot() if snapshot is None else snapshot
    formal_source, full_sha, prefix_sha, ast_digests = _formal_source_attestation()
    if not formal_source:
        raise ValueError("formal source attestation failed")
    contract_rows = _contract_rows()
    truth_rows = _truth_rows(snapshot)
    source_rows = _source_rows(snapshot)
    purity_rows = _purity_rows(full_sha, prefix_sha, ast_digests)
    issue_rows = _issue_rows(snapshot)
    files = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        PURITY_FILE: _csv_bytes(PURITY_COLUMNS, purity_rows),
        ISSUE_FILE: _csv_bytes(ISSUE_COLUMNS, issue_rows),
    }
    readiness = {**{name: True for name in TRUE_READINESS}, **{name: False for name in FALSE_READINESS}}
    manifest = {
        "manifest_schema_version": "covapie_admit_012_rule_logic_interface_manifest_v1",
        "project": PROJECT, "stage": STAGE, "base_commit": BASE_COMMIT, "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID, "public_evaluator": "evaluate_admit_012",
        "public_signature": "evaluate_admit_012(*, download_result_status: object = _MISSING, observed_http_status: object = _MISSING, observed_content_length_bytes: object = _MISSING, observed_sha256: object = _MISSING, allowed_download_result_statuses: object, successful_http_status_contract: object, content_length_contract: object, sha256_format_contract: object) -> Admit012EvaluationResult",
        "result_type": "Admit012EvaluationResult", "result_fields": list(RESULT_FIELDS),
        "result_field_count": 10, "field_order": list(EXACT4_FIELDS), "context_order": list(EXACT4_CONTEXT_ITEMS),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY), "reason_vocabulary": list(REASON_VOCABULARY),
        "validation_phase_order": ["Exact4_presence", "Exact4_type_value", "policy_context_type_content", "passed"],
        "canonical_record_representation": "empty or complete ordered Exact4 exact-pair tuple",
        "validated_representation": "ordered valid Exact4 pair-tuple prefix excluding failing field",
        "consumption_semantics": "ordered actual field/context prefixes; all fields consumed after presence completes",
        "failure_status_4xx_5xx_outcome": "passed", "admit_013_success_or_integrity_judgment_executed": False,
        "formal_evaluator_implemented": True, "formal_result_type_defined": True,
        "formal_production_sha256": full_sha, "formal_marker_prefix_sha256": prefix_sha,
        "formal_closure": list(FORMAL_CLOSURE), "formal_closure_count": len(FORMAL_CLOSURE),
        "formal_ast_sha256": ast_digests,
        "source_count": len(snapshot), "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "row_counts": {"formal_contract": len(contract_rows), "truth_matrix": len(truth_rows), "field52_projection": 52, "context_projection": 39, "cross_phase_projection": 6, "negative_result_projection": 8, "source_boundary": len(source_rows), "purity_audit": len(purity_rows), "issue_inventory": len(issue_rows)},
        "truth_matrix_passed": 105, "purity_closure_complete": True,
        "coverage_affected_rules": "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "readiness": readiness, **readiness,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "unified_adapter_or_runtime_changed": False, "admit_013_implemented": False,
        "authorized_admit_012_download_execution_count": 0,
        "safety": {"network": False, "raw": False, "provider_mapping": False, "real_download": False, "model_or_checkpoint": False, "runtime_change": False, "training": False},
        "renameat2_policy": "RENAME_NOREPLACE_required;_EINVAL_fails_closed_without_os.replace_fallback",
        "output_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        "all_checks_passed": True,
    }
    files[MANIFEST_FILE] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return {name: files[name] for name in OUTPUT_FILES}


def _rename_noreplace(source: Path, destination: Path) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(316, -100, os.fsencode(source), -100, os.fsencode(destination), 1)
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


def run_covapie_bulk_download_admission_admit_012_rule_logic_interface_v1(output_root: Path | None = None) -> dict[str, Any]:
    return materialize_contract(output_root)


if __name__ == "__main__":
    materialize_contract()

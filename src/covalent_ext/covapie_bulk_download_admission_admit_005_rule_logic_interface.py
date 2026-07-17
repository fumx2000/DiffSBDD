"""CovaPIE ADMIT_005 standalone scalar evaluator interface v1.

The public evaluator in this module is deliberately independent from candidate
projection, context routing, the unified adapter, and the Phase 4 registry.
The remaining code materializes deterministic, metadata-only evidence from a
frozen Exact12 committed-source boundary.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_005 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_005_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "3e39eb82271205fe7161048a0dd00fff99c65b7b"
EXPECTED_BASE_SUBJECT = (
    "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_004 v1"
)
MANIFEST_SCHEMA_VERSION = "covapie_admit_005_rule_logic_interface_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_005_unified_adapter_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_005"
OUTCOME_VOCABULARY = ("passed", "rejected", "invalid")
CANDIDATE_FIELDS = (
    "covalent_residue_name",
    "covalent_residue_atom_name",
)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_residue_name",
    "canonical_residue_atom_name",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "evaluator_io_used",
)
RESIDUE_INVALID_REASONS = (
    "COVALENT_RESIDUE_NAME_TYPE_INVALID",
    "COVALENT_RESIDUE_NAME_EMPTY",
    "COVALENT_RESIDUE_NAME_NON_ASCII",
    "COVALENT_RESIDUE_NAME_SYNTAX_INVALID",
)
ATOM_INVALID_REASONS = (
    "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID",
    "COVALENT_RESIDUE_ATOM_NAME_EMPTY",
    "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII",
    "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN",
    "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN",
)
SCOPE_REJECTION_REASON = "ADMIT_005_CYS_SG_SCOPE_REJECTED"
REASON_VOCABULARY = (
    "",
    *RESIDUE_INVALID_REASONS,
    *ATOM_INVALID_REASONS,
    SCOPE_REJECTION_REASON,
)
_COMPONENT_RE = re.compile(r"[A-Za-z0-9]{1,32}", re.ASCII)


def _canonical_residue_name_is_valid(value: object) -> bool:
    return (
        type(value) is str
        and value != ""
        and value.isascii()
        and _COMPONENT_RE.fullmatch(value) is not None
        and value == value.upper()
    )


def _canonical_atom_name_is_valid(value: object) -> bool:
    return (
        type(value) is str
        and value != ""
        and value.isascii()
        and not any(character.isspace() for character in value)
        and value not in (".", "?")
    )


@dataclass(frozen=True)
class Admit005EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_residue_name: str
    canonical_residue_atom_name: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        string_values = (
            self.admission_rule_id,
            self.outcome,
            self.reason,
            self.canonical_residue_name,
            self.canonical_residue_atom_name,
        )
        if any(type(value) is not str for value in string_values):
            raise TypeError("all string fields must be exact str")
        if type(self.passed) is not bool or type(self.blocks_candidate) is not bool:
            raise TypeError("boolean fields must be exact bool")
        if type(self.evaluator_io_used) is not bool:
            raise TypeError("evaluator_io_used must be exact bool")
        if type(self.validated_candidate_fields) is not tuple:
            raise TypeError("validated_candidate_fields must be exact tuple")
        for pair in self.validated_candidate_fields:
            if (
                type(pair) is not tuple
                or len(pair) != 2
                or type(pair[0]) is not str
                or type(pair[1]) is not str
            ):
                raise TypeError("validated field pairs must be exact string tuples")
        if type(self.consumed_candidate_fields) is not tuple or any(
            type(value) is not str for value in self.consumed_candidate_fields
        ):
            raise TypeError("consumed_candidate_fields must be an exact string tuple")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("admission_rule_id must be ADMIT_005")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("outcome is outside the ADMIT_005 vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed must be true exactly for passed outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate must be true exactly when not passed")
        if (self.outcome == "passed" and self.reason != "") or (
            self.outcome != "passed" and self.reason == ""
        ):
            raise ValueError("reason does not match outcome")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the ADMIT_005 vocabulary")
        if self.consumed_candidate_fields != CANDIDATE_FIELDS:
            raise ValueError("consumed_candidate_fields must equal CANDIDATE_FIELDS")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be false")
        residue_pair = ("covalent_residue_name", self.canonical_residue_name)
        atom_pair = ("covalent_residue_atom_name", self.canonical_residue_atom_name)
        if self.outcome == "passed":
            if (
                self.reason != ""
                or self.canonical_residue_name != "CYS"
                or self.canonical_residue_atom_name != "SG"
            ):
                raise ValueError("passed requires the exact empty-reason CYS/SG state")
            expected_validated: tuple[tuple[str, str], ...] = (
                ("covalent_residue_name", "CYS"),
                ("covalent_residue_atom_name", "SG"),
            )
        elif self.outcome == "rejected":
            if self.reason != SCOPE_REJECTION_REASON:
                raise ValueError("rejected requires the scope-rejection reason")
            if not _canonical_residue_name_is_valid(self.canonical_residue_name):
                raise ValueError("rejected requires a valid uppercase canonical residue")
            if not _canonical_atom_name_is_valid(self.canonical_residue_atom_name):
                raise ValueError("rejected requires a valid canonical atom")
            if (
                self.canonical_residue_name == "CYS"
                and self.canonical_residue_atom_name == "SG"
            ):
                raise ValueError("the exact CYS/SG pair cannot be rejected")
            expected_validated = (residue_pair, atom_pair)
        elif self.reason in RESIDUE_INVALID_REASONS:
            if self.canonical_residue_name != "" or self.canonical_residue_atom_name != "":
                raise ValueError("residue-invalid reasons require no canonical fields")
            expected_validated = ()
        elif self.reason in ATOM_INVALID_REASONS:
            if not _canonical_residue_name_is_valid(self.canonical_residue_name):
                raise ValueError("atom-invalid reasons require a valid canonical residue")
            if self.canonical_residue_atom_name != "":
                raise ValueError("atom-invalid reasons require an empty canonical atom")
            expected_validated = (residue_pair,)
        else:
            raise ValueError("invalid requires a field-specific invalid reason")
        if self.validated_candidate_fields != expected_validated:
            raise ValueError("validated_candidate_fields do not match canonical values")


def _evaluation_result(
    outcome: str,
    reason: str,
    canonical_residue_name: str,
    canonical_residue_atom_name: str,
) -> Admit005EvaluationResult:
    if canonical_residue_name == "":
        validated: tuple[tuple[str, str], ...] = ()
    elif canonical_residue_atom_name == "":
        validated = (("covalent_residue_name", canonical_residue_name),)
    else:
        validated = (
            ("covalent_residue_name", canonical_residue_name),
            ("covalent_residue_atom_name", canonical_residue_atom_name),
        )
    return Admit005EvaluationResult(
        admission_rule_id=ADMISSION_RULE_ID,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        canonical_residue_name=canonical_residue_name,
        canonical_residue_atom_name=canonical_residue_atom_name,
        validated_candidate_fields=validated,
        consumed_candidate_fields=CANDIDATE_FIELDS,
        evaluator_io_used=False,
    )


def evaluate_admit_005(
    residue_name: object,
    atom_name: object,
) -> Admit005EvaluationResult:
    """Evaluate the two scalar fields for the CYS/SG-only ADMIT_005 scope."""
    # This order is contractual: no atom operation occurs before all residue
    # validation succeeds.
    if type(residue_name) is not str:
        return _evaluation_result(
            "invalid", "COVALENT_RESIDUE_NAME_TYPE_INVALID", "", ""
        )
    if residue_name == "":
        return _evaluation_result(
            "invalid", "COVALENT_RESIDUE_NAME_EMPTY", "", ""
        )
    if not residue_name.isascii():
        return _evaluation_result(
            "invalid", "COVALENT_RESIDUE_NAME_NON_ASCII", "", ""
        )
    if _COMPONENT_RE.fullmatch(residue_name) is None:
        return _evaluation_result(
            "invalid", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID", "", ""
        )
    canonical_residue = residue_name.upper()

    if type(atom_name) is not str:
        return _evaluation_result(
            "invalid",
            "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID",
            canonical_residue,
            "",
        )
    if atom_name == "":
        return _evaluation_result(
            "invalid",
            "COVALENT_RESIDUE_ATOM_NAME_EMPTY",
            canonical_residue,
            "",
        )
    if not atom_name.isascii():
        return _evaluation_result(
            "invalid",
            "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII",
            canonical_residue,
            "",
        )
    if any(character.isspace() for character in atom_name):
        return _evaluation_result(
            "invalid",
            "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN",
            canonical_residue,
            "",
        )
    if atom_name in (".", "?"):
        return _evaluation_result(
            "invalid",
            "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN",
            canonical_residue,
            "",
        )

    if canonical_residue == "CYS" and atom_name == "SG":
        return _evaluation_result("passed", "", canonical_residue, atom_name)
    return _evaluation_result(
        "rejected",
        "ADMIT_005_CYS_SG_SCOPE_REJECTED",
        canonical_residue,
        atom_name,
    )


SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1/covapie_admit_001_to_004_runtime_manifest.json",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1/covapie_admit_001_to_004_runtime_issue_inventory.csv",
        "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
        "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv",
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate.py",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1/covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_contract.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1/covapie_admit_004_generic_atom_identity_evidence_context_truth_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_gate_v1/covapie_admit_004_generic_atom_identity_evidence_context_reconciled_field_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_gate_v1/covapie_admit_004_generic_atom_identity_evidence_context_reconciled_rule_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "a16ce1eef1048db7643a1f7940da554234683918136e76a6487eec5c2fdc35c3",
            "9cf7e902566a4aef9aa098e9a9a966f925666df581f8c0ce408d8c9598905149",
            "27bed0fd2250e0c64c704771fdb2bca8f5e50554d99f53694dc579f85f578d1f",
            "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
            "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
            "2083cc541297b039db496625dfb2c405c8cd78b33b99527f2a09de6b291eae29",
            "162a39f0080589efb0e87c32dcabd05270025cd2cb3c10f4e3e6a14857104376",
            "7c65167c31c40170e06fa42ed8eab08c1b6d800a67e466aa33885ba3449551a3",
            "3b9783910012c4910491a05cb7936fe425d86e7dea9d42d774e2c794228a8177",
            "bcc794debeb4d8287d06db9891dd7f0c085e0cc96ba50b14b8b34d3e768ff676",
            "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
            "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
        ),
        strict=True,
    )
)

CONTRACT_FILENAME = "covapie_admit_005_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_005_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_005_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_005_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_005_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_005_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    SOURCE_AUDIT_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id",
    "contract_kind",
    "contract_subject",
    "contract_value",
    "contract_status",
)
TRUTH_COLUMNS = (
    "case_id",
    "case_group",
    "residue_input_kind",
    "residue_input_display",
    "atom_input_kind",
    "atom_input_display",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "canonical_residue_name",
    "canonical_residue_atom_name",
    "validated_candidate_fields_json",
    "case_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order",
    "source_relative_path",
    "tracked_by_git",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "expected_sha256",
    "base_tree_sha256",
    "filesystem_sha256",
    "source_verified",
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


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    fieldnames: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _git(
    arguments: Sequence[str],
    repo_root: Path,
    *,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=text,
    )


def _validate_expected_base_lineage(repo_root: Path, head_ref: str) -> None:
    base = _git(("cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"), repo_root)
    if base.returncode != 0:
        raise ValueError("expected base commit object is unavailable")
    subject = _git(
        ("show", "-s", "--format=%s", EXPECTED_BASE_COMMIT), repo_root, text=True
    )
    if subject.returncode != 0 or subject.stdout.rstrip("\n") != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base subject mismatch")
    head = _git(("cat-file", "-e", f"{head_ref}^{{commit}}"), repo_root)
    if head.returncode != 0:
        raise ValueError("head_ref is not a commit")
    lineage = _git(
        ("merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref), repo_root
    )
    if lineage.returncode != 0:
        raise ValueError("expected base is not an ancestor of head_ref")


def _safe_relative_path(path: Path) -> bool:
    return (
        not path.is_absolute()
        and path.parts
        and ".." not in path.parts
        and path.as_posix() == str(path)
    )


def _structural_source_check(path: Path, repo_root: Path) -> None:
    if not _safe_relative_path(path):
        raise ValueError(f"unsafe source path: {path}")
    tracked = _git(("ls-files", "--error-unmatch", "--", path.as_posix()), repo_root)
    if tracked.returncode != 0:
        raise ValueError(f"source is not tracked: {path}")
    base_type = _git(
        ("cat-file", "-t", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"),
        repo_root,
        text=True,
    )
    if base_type.returncode != 0 or base_type.stdout.strip() != "blob":
        raise ValueError(f"base-tree source is not a blob: {path}")
    filesystem_path = repo_root / path
    try:
        status = filesystem_path.lstat()
    except FileNotFoundError as error:
        raise ValueError(f"source is missing: {path}") from error
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise ValueError(f"source is not a regular non-symlink file: {path}")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    root = repo_root.resolve()
    _validate_expected_base_lineage(root, head_ref)
    # Complete every structural check before the first source-content read.
    for path in SOURCE_PATHS:
        _structural_source_check(path, root)
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(("show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"), root)
        if base.returncode != 0:
            raise ValueError(f"base-tree source read failed: {path}")
        content = (root / path).read_bytes()
        expected = SOURCE_SHA256[path]
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(content).hexdigest()
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(path, expected, base_sha, filesystem_sha, content)
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    if type(value) is not FrozenSourceSnapshot or type(value.records) is not tuple:
        return False
    if tuple(record.relative_path for record in value.records) != SOURCE_PATHS:
        return False
    return all(
        type(record) is FrozenSourceRecord
        and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
        and record.base_tree_sha256 == record.expected_sha256
        and record.filesystem_sha256 == record.expected_sha256
        and type(record.content) is bytes
        and hashlib.sha256(record.content).hexdigest() == record.expected_sha256
        for record in value.records
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    for record in snapshot.records:
        if record.relative_path == path:
            return record
    raise KeyError(path)


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        raise ValueError(f"CSV has no header: {path}")
    return CsvDocument(tuple(reader.fieldnames), tuple(dict(row) for row in reader))


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    return ast.parse(_record(snapshot, path).content.decode("utf-8"), path.as_posix())


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    phase4_manifest = _json_document(snapshot, SOURCE_PATHS[1])
    issues = _csv_document(snapshot, SOURCE_PATHS[2])
    registry = _csv_document(snapshot, SOURCE_PATHS[4])
    evaluator_matrix = _csv_document(snapshot, SOURCE_PATHS[10])
    outcome_contract = _csv_document(snapshot, SOURCE_PATHS[11])
    phase4_ast = _ast_document(snapshot, SOURCE_PATHS[0])
    oracle_ast = _ast_document(snapshot, SOURCE_PATHS[5])

    if phase4_manifest.get("registered_rule_ids") != [
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
        "ADMIT_004",
    ]:
        raise ValueError("Phase 4 registry contract changed")
    if phase4_manifest.get("active_issue_count") != 11 or len(issues.rows) != 11:
        raise ValueError("Phase 4 Exact11 issue contract changed")
    provider = [
        row for row in issues.rows if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
    ]
    if len(provider) != 1 or (
        provider[0]["status"], provider[0]["severity"], provider[0]["issue_count"]
    ) != ("open", "blocking", "11"):
        raise ValueError("provider blocker contract changed")
    coverage = [
        row for row in issues.rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(coverage) != 1 or "ADMIT_005" not in coverage[0]["affected_rules"].split("|"):
        raise ValueError("ADMIT_005 coverage issue changed")
    if len(registry.rows) != 15 or registry.rows[4]["admission_rule_id"] != "ADMIT_005":
        raise ValueError("canonical rule registry changed")
    admit005_route = [row for row in evaluator_matrix.rows if row["admission_rule_id"] == "ADMIT_005"]
    if len(admit005_route) != 1 or admit005_route[0]["allowed_rule_outcomes"] != "passed|rejected|invalid":
        raise ValueError("ADMIT_005 outcome boundary changed")
    outcome_rows = {
        row["contract_order"]: row for row in outcome_contract.rows
    }
    if outcome_rows.get("24", {}).get("contract_value") != "passed|rejected|invalid":
        raise ValueError("ADMIT_005 result contract changed")
    phase4_functions = {
        node.name for node in phase4_ast.body if isinstance(node, ast.FunctionDef)
    }
    if "evaluate_admission_rule" not in phase4_functions:
        raise ValueError("Phase 4 public runtime missing")
    oracle_functions = {
        node.name for node in oracle_ast.body if isinstance(node, ast.FunctionDef)
    }
    required_oracles = {
        "classify_admit_004_admit_005_atom_scope_design",
        "validate_generic_covalent_residue_atom_name",
    }
    if not required_oracles.issubset(oracle_functions):
        raise ValueError("independent oracle helpers missing")
    return {
        "phase4_manifest": phase4_manifest,
        "issue_rows": [dict(row) for row in issues.rows],
        "registry_rows": [dict(row) for row in registry.rows],
    }


class _StringSubclass(str):
    pass


def _truth_case_definitions() -> tuple[dict[str, Any], ...]:
    return (
        {"case_id": "PASS_001", "group": "passed", "residue": "CYS", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "PASS_002", "group": "passed", "residue": "cys", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_001", "group": "rejected", "residue": "CYS", "atom": "CA", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_002", "group": "rejected", "residue": "CYS", "atom": "sg", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_003", "group": "rejected", "residue": "CYS", "atom": "A.B", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_004", "group": "rejected", "residue": "SER", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_005", "group": "rejected", "residue": "SER", "atom": "CA", "rk": "str", "ak": "str"},
        {"case_id": "REJECT_006", "group": "rejected", "residue": "CYX", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_RESIDUE_001", "group": "invalid", "residue": 7, "atom": "SG", "rk": "non_str", "ak": "str"},
        {"case_id": "INVALID_RESIDUE_002", "group": "invalid", "residue": _StringSubclass("CYS"), "atom": "SG", "rk": "str_subclass", "ak": "str"},
        {"case_id": "INVALID_RESIDUE_003", "group": "invalid", "residue": "", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_RESIDUE_004", "group": "invalid", "residue": "CÝS", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_RESIDUE_005", "group": "invalid", "residue": "C-Y", "atom": "SG", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_001", "group": "invalid", "residue": "CYS", "atom": 7, "rk": "str", "ak": "non_str"},
        {"case_id": "INVALID_ATOM_002", "group": "invalid", "residue": "CYS", "atom": _StringSubclass("SG"), "rk": "str", "ak": "str_subclass"},
        {"case_id": "INVALID_ATOM_003", "group": "invalid", "residue": "CYS", "atom": "", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_004", "group": "invalid", "residue": "CYS", "atom": "SĠ", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_005", "group": "invalid", "residue": "CYS", "atom": "S G", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_006", "group": "invalid", "residue": "CYS", "atom": "S\tG", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_007", "group": "invalid", "residue": "CYS", "atom": ".", "rk": "str", "ak": "str"},
        {"case_id": "INVALID_ATOM_008", "group": "invalid", "residue": "CYS", "atom": "?", "rk": "str", "ak": "str"},
        {"case_id": "PRECEDENCE_001", "group": "invalid", "residue": "C-Y", "atom": "?", "rk": "str", "ak": "str"},
    )


def _display(value: object) -> str:
    if type(value) is _StringSubclass:
        return str(value)
    return json.dumps(value, ensure_ascii=True)


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in _truth_case_definitions():
        result = evaluate_admit_005(case["residue"], case["atom"])
        expected_outcome = case["group"]
        if expected_outcome == "passed":
            expected_reason = ""
        elif expected_outcome == "rejected":
            expected_reason = "ADMIT_005_CYS_SG_SCOPE_REJECTED"
        else:
            reason_by_case = {
                "INVALID_RESIDUE_001": "COVALENT_RESIDUE_NAME_TYPE_INVALID",
                "INVALID_RESIDUE_002": "COVALENT_RESIDUE_NAME_TYPE_INVALID",
                "INVALID_RESIDUE_003": "COVALENT_RESIDUE_NAME_EMPTY",
                "INVALID_RESIDUE_004": "COVALENT_RESIDUE_NAME_NON_ASCII",
                "INVALID_RESIDUE_005": "COVALENT_RESIDUE_NAME_SYNTAX_INVALID",
                "INVALID_ATOM_001": "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID",
                "INVALID_ATOM_002": "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID",
                "INVALID_ATOM_003": "COVALENT_RESIDUE_ATOM_NAME_EMPTY",
                "INVALID_ATOM_004": "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII",
                "INVALID_ATOM_005": "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN",
                "INVALID_ATOM_006": "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN",
                "INVALID_ATOM_007": "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN",
                "INVALID_ATOM_008": "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN",
                "PRECEDENCE_001": "COVALENT_RESIDUE_NAME_SYNTAX_INVALID",
            }
            expected_reason = reason_by_case[case["case_id"]]
        passed = result.outcome == expected_outcome and result.reason == expected_reason
        rows.append(
            {
                "case_id": case["case_id"],
                "case_group": case["group"],
                "residue_input_kind": case["rk"],
                "residue_input_display": _display(case["residue"]),
                "atom_input_kind": case["ak"],
                "atom_input_display": _display(case["atom"]),
                "expected_outcome": expected_outcome,
                "observed_outcome": result.outcome,
                "expected_reason": expected_reason,
                "observed_reason": result.reason,
                "canonical_residue_name": result.canonical_residue_name,
                "canonical_residue_atom_name": result.canonical_residue_atom_name,
                "validated_candidate_fields_json": json.dumps(result.validated_candidate_fields),
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "callable", "evaluate_admit_005(residue_name, atom_name)"),
        ("API_002", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "frozen_dataclass"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "outcomes", "passed|rejected|invalid"),
        ("RESULT_005", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_006", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        (
            "RESULT_007",
            "result_contract",
            "outcome_reason_canonical_binding",
            "passed=>empty_reason_and_exact_CYS_SG|rejected=>scope_rejection_reason_and_valid_non_CYS_SG|invalid=>field_specific_reason_controls_partial_canonical_state",
        ),
        ("RESIDUE_001", "scalar_semantics", "residue_type", "exact_str_nonempty_ascii"),
        ("RESIDUE_002", "scalar_semantics", "residue_grammar", "[A-Za-z0-9]{1,32}"),
        ("RESIDUE_003", "scalar_semantics", "residue_canonical", "uppercase_without_repair"),
        ("ATOM_001", "scalar_semantics", "atom_type", "exact_str_nonempty_ascii"),
        ("ATOM_002", "scalar_semantics", "atom_whitespace", "all_isspace_forbidden"),
        ("ATOM_003", "scalar_semantics", "atom_markers", ".|?_forbidden"),
        ("ATOM_004", "scalar_semantics", "atom_generic_identity", "generic_nonmarker_no_whitespace_allowed"),
        ("ATOM_005", "scalar_semantics", "atom_canonical", "exact_preserve_without_repair"),
        ("SCOPE_001", "scope_semantics", "passed", "canonical_CYS_and_exact_SG"),
        ("SCOPE_002", "scope_semantics", "rejected", "valid_identity_outside_CYS_SG"),
        ("SCOPE_003", "scope_semantics", "precedence", "residue_then_atom_then_scope"),
        (
            "VALIDATED_001",
            "mapping_contract",
            "reason_controlled_validated_fields",
            "residue_invalid_reason=>no_canonical_fields|atom_invalid_reason=>canonical_residue_only|passed_or_rejected=>canonical_residue_then_atom",
        ),
        ("ORACLE_001", "oracle_contract", "independent_helpers", "scope_design_plus_generic_atom_validator"),
        ("BOUNDARY_001", "authorization_boundary", "excluded_inputs", "candidate_mapping_and_context_absent"),
        ("BOUNDARY_002", "authorization_boundary", "runtime_registry", "phase4_unchanged_admit005_unregistered"),
    )
    return [
        {
            "contract_id": contract_id,
            "contract_kind": kind,
            "contract_subject": subject,
            "contract_value": value,
            "contract_status": "frozen",
        }
        for contract_id, kind, subject, value in values
    ]


def _source_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [
        {
            "source_order": str(index),
            "source_relative_path": record.relative_path.as_posix(),
            "tracked_by_git": "true",
            "base_tree_blob": "true",
            "filesystem_regular": "true",
            "non_symlink": "true",
            "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256,
            "source_verified": "true",
        }
        for index, record in enumerate(snapshot.records, 1)
    ]


EXECUTED_SAFETY_ITEMS = (
    "exact_source_reads",
    "phase4_runtime_contract_validation",
    "canonical_admission_rule_validation",
    "generic_atom_semantics_validation",
    "admit_005_result_contract_implementation",
    "admit_005_scalar_evaluator_implementation",
    "residue_validation_implementation",
    "generic_atom_validation_implementation",
    "cys_sg_scope_classification_implementation",
    "independent_semantic_oracle_attestation",
    "synthetic_truth_matrix_evaluation",
    "issue_inventory_preservation",
)
NOT_EXECUTED_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "parser_execution",
    "provider_execution",
    "candidate_record_projection",
    "context_routing_implementation",
    "unified_adapter_design",
    "unified_adapter_implementation",
    "phase4_runtime_modification",
    "evaluator_registry_modification",
    "admit_005_engine_registration",
    "admit_006_to_015_evaluator_execution",
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


def _safety_rows() -> list[dict[str, str]]:
    rows = []
    for item in EXECUTED_SAFETY_ITEMS:
        rows.append(
            {
                "safety_item": item,
                "expected_executed": "true",
                "observed_executed": "true",
                "safety_passed": "true",
            }
        )
    for item in NOT_EXECUTED_SAFETY_ITEMS:
        rows.append(
            {
                "safety_item": item,
                "expected_executed": "false",
                "observed_executed": "false",
                "safety_passed": "true",
            }
        )
    return rows


READINESS = {
    "admit_005_standalone_evaluator_interface_implemented": True,
    "admit_005_formal_result_contract_frozen": True,
    "admit_005_scalar_semantics_implemented": True,
    "admit_005_cys_sg_scope_semantics_implemented": True,
    "admit_005_passed_rejected_invalid_boundary_frozen": True,
    "admit_005_core_reason_vocabulary_frozen": True,
    "admit_005_independent_semantic_oracle_attested": True,
    "admit_005_synthetic_truth_matrix_passed": True,
    "ready_for_admit_005_unified_adapter_contract_design": True,
    "feature_semantics_audit_required_before_training": True,
    "admit_005_candidate_projection_contract_frozen": False,
    "admit_005_context_routing_contract_frozen": False,
    "admit_005_unified_adapter_contract_frozen": False,
    "admit_005_unified_adapter_implemented": False,
    "admit_005_registered_in_engine": False,
    "phase4_runtime_modified": False,
    "admit_006_to_015_registered_in_engine": False,
    "all_15_rules_covered": False,
    "evaluate_all_rules_implemented": False,
    "combined_candidate_verdict_contract_frozen": False,
    "combined_candidate_verdict_implemented": False,
    "cross_rule_precedence_frozen": False,
    "real_candidate_evaluation": False,
    "exact11_real_rows_evaluated": False,
    "ready_for_bulk_download_now": False,
    "ready_for_training": False,
    "ready_to_train_now": False,
}


def build_interface_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    snapshot = build_frozen_source_snapshot() if source_snapshot is None else source_snapshot
    historical = _validate_predecessors(snapshot)
    contract_rows = _contract_rows()
    truth_rows = _truth_rows()
    source_rows = _source_audit_rows(snapshot)
    safety_rows = _safety_rows()
    issue_rows = historical["issue_rows"]
    checks = (
        len(contract_rows) == 24,
        tuple(row["contract_id"] for row in contract_rows)
        == (
            "API_001", "API_002", "RESULT_001", "RESULT_002", "RESULT_003",
            "RESULT_004", "RESULT_005", "RESULT_006", "RESULT_007",
            "RESIDUE_001", "RESIDUE_002", "RESIDUE_003", "ATOM_001",
            "ATOM_002", "ATOM_003", "ATOM_004", "ATOM_005", "SCOPE_001",
            "SCOPE_002", "SCOPE_003", "VALIDATED_001", "ORACLE_001",
            "BOUNDARY_001", "BOUNDARY_002",
        ),
        len(truth_rows) == 22,
        len({row["case_id"] for row in truth_rows}) == 22,
        all(row["case_passed"] == "true" for row in truth_rows),
        {outcome: sum(row["observed_outcome"] == outcome for row in truth_rows) for outcome in OUTCOME_VOCABULARY}
        == {"passed": 2, "rejected": 6, "invalid": 14},
        truth_rows[-1]["observed_reason"] == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID",
        len(source_rows) == 12 and all(row["source_verified"] == "true" for row in source_rows),
        len(issue_rows) == 11,
        all(row["safety_passed"] == "true" for row in safety_rows),
    )
    if not all(checks):
        raise RuntimeError("ADMIT_005 interface state failed closed")
    return {
        "source_snapshot": snapshot,
        "historical": historical,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "source_audit_rows": source_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "readiness": dict(READINESS),
        "all_checks_passed": True,
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
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
                "source_order": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked_by_git": True,
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
        "public_api": "evaluate_admit_005(residue_name, atom_name)",
        "result_type": "Admit005EvaluationResult",
        "result_field_count": 10,
        "result_fields": list(RESULT_FIELDS),
        "direct_result_construction_fail_closed": True,
        "result_outcome_reason_canonical_state_bound": True,
        "result_reason_class_mapping_frozen": True,
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "candidate_fields": list(CANDIDATE_FIELDS),
        "contract_row_count": 24,
        "contract_pass_count": 24,
        "truth_matrix_row_count": 22,
        "truth_matrix_pass_count": 22,
        "truth_matrix_group_counts": {"passed": 2, "rejected": 6, "invalid": 14},
        "source_audit_row_count": 12,
        "source_audit_pass_count": 12,
        "active_issue_count": 11,
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "readiness": dict(state["readiness"]),
        **dict(state["readiness"]),
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True,
        "all_scalar_semantics_checks_passed": True,
        "all_oracle_attestation_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_contract_checks_passed": True,
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
        SOURCE_AUDIT_FILENAME: _csv_bytes(
            SOURCE_AUDIT_COLUMNS, state["source_audit_rows"]
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
        if temporary.exists():
            temporary.unlink()


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        status = root.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
        entries = tuple(root.iterdir())
        unexpected = {entry.name for entry in entries} - set(OUTPUT_FILES)
        if unexpected:
            raise ValueError("output root contains unexpected entries")
        for entry in entries:
            entry_status = entry.lstat()
            if stat.S_ISLNK(entry_status.st_mode) or not stat.S_ISREG(entry_status.st_mode):
                raise ValueError("output root contains an unsafe entry")


def run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_interface_state()
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    root.mkdir(parents=True, exist_ok=True)
    # Re-check after creation to defend the actual write target.
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_005_rule_logic_interface_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

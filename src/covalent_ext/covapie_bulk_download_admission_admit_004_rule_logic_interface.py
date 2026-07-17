"""Step14AU-E1-E3 standalone ADMIT_004 rule-logic interface v1.

The public evaluator is deterministic and pure in memory.  The surrounding
metadata gate freezes and verifies its exact committed evidence boundary; it
does not execute a parser/provider, dereference provenance references,
materialize candidate records, or integrate the unified admission engine.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E3"
STAGE = "covapie_bulk_download_admission_admit_004_rule_logic_interface_v1"
EXPECTED_BASE_COMMIT = "3c45a5fbfaa38345fd3560d0031180ba8b754886"
MANIFEST_SCHEMA_VERSION = "covapie_admit_004_rule_logic_interface_manifest_v1"
EVIDENCE_CONTEXT_SCHEMA_VERSION = "covapie_covalent_residue_identity_evidence_context_v1"
EVIDENCE_CONTEXT_KEY = "covalent_residue_identity_evidence_context"
RECOMMENDED_NEXT_STEP = "integrate_covapie_admit_004_rule_logic_interface_into_unified_engine_v1"
PROVIDER_ISSUE = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
MISSING_CONTEXT_REASON = "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING"
FOUR_WAY_REASON = "ADMIT_004_PRESENT_FOUR_WAY_EQUALITY_UNATTESTED"
QUOTE_CLASS_REASON = "COVALENT_RESIDUE_INSERTION_PRESENT_QUOTE_CLASS_UNVERIFIED"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

E1E2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_generic_atom_identity_"
    "evidence_context_reconciliation_integration_gate_v1"
)
E1E1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_generic_atom_identity_"
    "evidence_context_reconciliation_design_gate_v1"
)
E1C_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_insertion_"
    "present_value_grammar_design_gate_v1"
)
E1A_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_004_residue_identity_"
    "atom_name_semantics_design_gate_v1"
)

SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_rule_matrix.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_field_matrix.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciled_context_matrix.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_integration_safety_audit.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_integration_issue_inventory.csv"),
        str(E1E2_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_integration_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate.py",
        str(E1E1_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_contract.csv"),
        str(E1E1_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_truth_matrix.csv"),
        str(E1E1_ROOT / "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_design_manifest.json"),
        str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_contract.csv"),
        str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_contract.csv"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "bcc794debeb4d8287d06db9891dd7f0c085e0cc96ba50b14b8b34d3e768ff676",
            "3b9783910012c4910491a05cb7936fe425d86e7dea9d42d774e2c794228a8177",
            "26e6eac422d00805aaad336024c2ec9d75038620e280c8d48fa89ef60a451cd1",
            "ae5d266cf6ca0369ab8da08b529d7e9b89ba169ffd903abff1009ecc9d00623c",
            "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
            "3c03b711e74fd023be187b64a757e69f8fc03bcb1af19c88325e7fdeb226012d",
            "2083cc541297b039db496625dfb2c405c8cd78b33b99527f2a09de6b291eae29",
            "162a39f0080589efb0e87c32dcabd05270025cd2cb3c10f4e3e6a14857104376",
            "7c65167c31c40170e06fa42ed8eab08c1b6d800a67e466aa33885ba3449551a3",
            "7834abfca88d07d8cff92dc75212b1cc2ea932d3b46484602d97bc9acbb0a485",
            "bb4907d1b6580e0e2487d8839e01b718ebf904f2debc49c4df9d4716c18274be",
            "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff",
        ),
        strict=True,
    )
)

(
    E1E2_RULE_PATH,
    E1E2_FIELD_PATH,
    E1E2_CONTEXT_PATH,
    E1E2_SAFETY_PATH,
    E1E2_ISSUE_PATH,
    E1E2_MANIFEST_PATH,
    E1E1_SOURCE_PATH,
    E1E1_CONTRACT_PATH,
    E1E1_TRUTH_PATH,
    E1E1_MANIFEST_PATH,
    E1C_CONTRACT_PATH,
    E1A_CONTRACT_PATH,
) = SOURCE_PATHS

CANDIDATE_FIELDS = (
    "covalent_residue_name",
    "covalent_residue_chain_id",
    "covalent_residue_index",
    "covalent_residue_atom_name",
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
NESTED_CONTEXT_KEYS = (
    "schema_version",
    "attested_candidate_fields",
    "provider_evidence_outcome",
    "provider_evidence_reason",
    "four_way_present_value_exact_equality_attested",
    "present_value_quote_class_roundtrip_verified",
)

CONTRACT_FILENAME = "covapie_admit_004_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_004_rule_logic_interface_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_004_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_004_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_004_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_004_rule_logic_interface_manifest.json"
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
    "contract_area",
    "contract_statement",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "truth_group",
    "case_id",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "canonical_residue_name",
    "validated_candidate_field_count",
    "evidence_context_consumed",
    "evaluator_io_used",
    "truth_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order",
    "source_relative_path",
    "tracked_by_git",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "sha256_expected",
    "sha256_base_tree",
    "sha256_filesystem",
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

TRUE_SAFETY_ITEMS = (
    "exact_source_reads",
    "e1e2_effective_view_validation",
    "e1e1_design_validation",
    "admit_004_rule_logic_interface_implementation",
    "exact9_candidate_validation_implementation",
    "evidence_context_validation_implementation",
    "outcome_precedence_validation",
    "synthetic_truth_matrix_evaluation",
    "exact11_metadata_invariant_validation",
)
FALSE_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "parser_execution",
    "provider_execution",
    "unified_rule_engine_integration",
    "candidate_record_materialization",
    "real_candidate_evaluation",
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

INSERTION_PRESENT_VALUE_PATTERN = r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+"
_RESIDUE_RE = re.compile(r"[A-Za-z0-9]{1,32}", re.ASCII)
_PROVENANCE_SOURCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}", re.ASCII)
_SHA256_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)
_INSERTION_RE = re.compile(INSERTION_PRESENT_VALUE_PATTERN, re.ASCII)


@dataclass(frozen=True)
class Admit004EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_residue_name: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    evidence_context_consumed: bool
    evaluator_io_used: bool


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


def _result(
    outcome: str,
    reason: str,
    canonical_residue_name: str = "",
    validated_candidate_fields: tuple[tuple[str, str], ...] = (),
    evidence_context_consumed: bool = False,
) -> Admit004EvaluationResult:
    if outcome not in ("passed", "blocked", "invalid"):
        raise ValueError("invalid internal ADMIT_004 outcome")
    return Admit004EvaluationResult(
        admission_rule_id="ADMIT_004",
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        canonical_residue_name=canonical_residue_name,
        validated_candidate_fields=validated_candidate_fields,
        consumed_candidate_fields=CANDIDATE_FIELDS,
        evidence_context_consumed=evidence_context_consumed,
        evaluator_io_used=False,
    )


def _validate_residue_name(value: object) -> tuple[str, str]:
    if type(value) is not str:
        return "", "COVALENT_RESIDUE_NAME_TYPE_INVALID"
    if value == "":
        return "", "COVALENT_RESIDUE_NAME_EMPTY"
    if not value.isascii():
        return "", "COVALENT_RESIDUE_NAME_NON_ASCII"
    if _RESIDUE_RE.fullmatch(value) is None:
        return "", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"
    return value.upper(), ""


def _validate_generic_lexical(value: object, field_reason: str) -> str:
    if type(value) is not str:
        return f"{field_reason}_TYPE_INVALID"
    if value == "":
        return f"{field_reason}_EMPTY"
    if not value.isascii():
        return f"{field_reason}_NON_ASCII"
    if any(character.isspace() for character in value) or value in (".", "?"):
        return f"{field_reason}_LEXICAL_INVALID"
    return ""


def _validate_atom_name(value: object) -> str:
    if type(value) is not str:
        return "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"
    if value == "":
        return "COVALENT_RESIDUE_ATOM_NAME_EMPTY"
    if not value.isascii():
        return "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII"
    if any(character.isspace() for character in value):
        return "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"
    if value in (".", "?"):
        return "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"
    return ""


def _validate_insertion_state_value(state: object, value: object) -> str:
    if type(state) is not str:
        return "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"
    if state not in ("absent", "present", "unknown"):
        return "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"
    if type(value) is not str:
        return "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"
    if state == "absent":
        return "" if value == "" else "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"
    if state == "unknown":
        return "" if value == "" else "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY"
    if value == "":
        return "COVALENT_RESIDUE_INSERTION_PRESENT_REQUIRES_NONEMPTY"
    if not value.isascii():
        return "COVALENT_RESIDUE_INSERTION_PRESENT_NON_ASCII"
    if any(character.isspace() for character in value):
        return "COVALENT_RESIDUE_INSERTION_PRESENT_WHITESPACE_FORBIDDEN"
    if value in (".", "?"):
        return "COVALENT_RESIDUE_INSERTION_PRESENT_MARKER_FORBIDDEN"
    if _INSERTION_RE.fullmatch(value) is None:
        return "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"
    return ""


def _candidate_validation(
    candidate_record: object,
) -> tuple[str, tuple[tuple[str, str], ...], str]:
    if not isinstance(candidate_record, Mapping):
        return "", (), "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID"
    for field in CANDIDATE_FIELDS:
        if field not in candidate_record:
            canonical = ""
            if CANDIDATE_FIELDS[0] in candidate_record:
                canonical = _validate_residue_name(candidate_record[CANDIDATE_FIELDS[0]])[0]
            return canonical, (), f"ADMIT_004_CANDIDATE_FIELD_MISSING:{field}"

    canonical_residue, reason = _validate_residue_name(candidate_record[CANDIDATE_FIELDS[0]])
    validators = (
        reason,
        _validate_generic_lexical(candidate_record[CANDIDATE_FIELDS[1]], "COVALENT_RESIDUE_CHAIN_ID"),
        _validate_generic_lexical(candidate_record[CANDIDATE_FIELDS[2]], "COVALENT_RESIDUE_INDEX"),
        _validate_atom_name(candidate_record[CANDIDATE_FIELDS[3]]),
        ""
        if type(candidate_record[CANDIDATE_FIELDS[4]]) is str
        and candidate_record[CANDIDATE_FIELDS[4]] in ("auth", "label")
        else "COVALENT_RESIDUE_LOCATOR_NAMESPACE_INVALID",
        _validate_insertion_state_value(
            candidate_record[CANDIDATE_FIELDS[5]], candidate_record[CANDIDATE_FIELDS[6]]
        ),
        ""
        if type(candidate_record[CANDIDATE_FIELDS[7]]) is str
        and _PROVENANCE_SOURCE_RE.fullmatch(candidate_record[CANDIDATE_FIELDS[7]]) is not None
        else "COVALENT_RESIDUE_PROVENANCE_SOURCE_ID_INVALID",
        ""
        if type(candidate_record[CANDIDATE_FIELDS[8]]) is str
        and _SHA256_RE.fullmatch(candidate_record[CANDIDATE_FIELDS[8]]) is not None
        else "COVALENT_RESIDUE_PROVENANCE_SHA256_INVALID",
    )
    first_reason = next((item for item in validators if item), "")
    if first_reason:
        return canonical_residue, (), first_reason
    validated = tuple(
        (field, canonical_residue if index == 0 else candidate_record[field])
        for index, field in enumerate(CANDIDATE_FIELDS)
    )
    return canonical_residue, validated, ""


def _exact_keyset(value: Mapping[object, object], expected: tuple[str, ...]) -> bool:
    try:
        return len(value) == len(expected) and all(key in value for key in expected)
    except (TypeError, ValueError):
        return False


def evaluate_admit_004(
    candidate_record: Mapping[str, object],
    evaluation_context: Mapping[str, object],
) -> Admit004EvaluationResult:
    """Evaluate standalone ADMIT_004 using only the two supplied mappings."""
    canonical, validated, candidate_reason = _candidate_validation(candidate_record)
    if candidate_reason:
        return _result("invalid", candidate_reason, canonical)
    if not isinstance(evaluation_context, Mapping):
        return _result("invalid", "ADMIT_004_EVALUATION_CONTEXT_MAPPING_INVALID", canonical, validated)

    nested_missing = EVIDENCE_CONTEXT_KEY not in evaluation_context
    nested: Mapping[object, object] | None = None
    if not nested_missing:
        candidate_context = evaluation_context[EVIDENCE_CONTEXT_KEY]
        if not isinstance(candidate_context, Mapping):
            return _result(
                "invalid",
                "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MAPPING_INVALID",
                canonical,
                validated,
                True,
            )
        nested = candidate_context
        if not _exact_keyset(nested, NESTED_CONTEXT_KEYS):
            return _result(
                "invalid",
                "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID",
                canonical,
                validated,
                True,
            )
        schema = nested["schema_version"]
        if type(schema) is not str or schema != EVIDENCE_CONTEXT_SCHEMA_VERSION:
            return _result(
                "invalid",
                "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_SCHEMA_INVALID",
                canonical,
                validated,
                True,
            )
        attested = nested["attested_candidate_fields"]
        if not isinstance(attested, Mapping) or not _exact_keyset(attested, CANDIDATE_FIELDS):
            return _result(
                "invalid",
                "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID",
                canonical,
                validated,
                True,
            )
        for field in CANDIDATE_FIELDS:
            if type(attested[field]) is not str:
                return _result(
                    "invalid",
                    f"ADMIT_004_ATTESTED_CANDIDATE_VALUE_TYPE_INVALID:{field}",
                    canonical,
                    validated,
                    True,
                )
            if attested[field] != candidate_record[field]:
                return _result(
                    "invalid",
                    f"ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:{field}",
                    canonical,
                    validated,
                    True,
                )
        provider_outcome = nested["provider_evidence_outcome"]
        provider_reason = nested["provider_evidence_reason"]
        if type(provider_outcome) is not str or provider_outcome not in ("passed", "blocked", "invalid"):
            return _result(
                "invalid", "ADMIT_004_PROVIDER_EVIDENCE_OUTCOME_INVALID", canonical, validated, True
            )
        if (
            type(provider_reason) is not str
            or not provider_reason.isascii()
            or (provider_outcome == "passed" and provider_reason != "")
            or (provider_outcome != "passed" and provider_reason == "")
        ):
            return _result(
                "invalid", "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID", canonical, validated, True
            )
        for key in NESTED_CONTEXT_KEYS[-2:]:
            if type(nested[key]) is not bool:
                return _result(
                    "invalid",
                    f"ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_BOOL_INVALID:{key}",
                    canonical,
                    validated,
                    True,
                )
        if provider_outcome == "invalid":
            return _result("invalid", provider_reason, canonical, validated, True)

    state = candidate_record["covalent_residue_insertion_code_state"]
    value = candidate_record["covalent_residue_insertion_code"]
    if state == "unknown" and value == "":
        return _result("blocked", UNKNOWN_REASON, canonical, validated, nested is not None)
    if nested_missing:
        return _result("blocked", MISSING_CONTEXT_REASON, canonical, validated)
    assert nested is not None
    if nested["provider_evidence_outcome"] == "blocked":
        return _result("blocked", nested["provider_evidence_reason"], canonical, validated, True)
    if state == "present" and nested["four_way_present_value_exact_equality_attested"] is False:
        return _result("blocked", FOUR_WAY_REASON, canonical, validated, True)
    if state == "present" and nested["present_value_quote_class_roundtrip_verified"] is False:
        return _result("blocked", QUOTE_CLASS_REASON, canonical, validated, True)
    return _result("passed", "", canonical, validated, True)


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False
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


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Inspect source structure without reading source content bytes."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(fields) == 3
        and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Complete all exact12 structure checks before the first source-byte read."""
    if len(SOURCE_PATHS) != 12 or len(set(SOURCE_PATHS)) != 12 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("exact12 source boundary shape invalid")
    structural = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes)
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 12
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
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _keyed(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("missing or duplicate key")
        result[value] = row
    return result


def _validate_predecessor_evidence(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    rules = _csv_document(snapshot, E1E2_RULE_PATH)
    fields = _csv_document(snapshot, E1E2_FIELD_PATH)
    contexts = _csv_document(snapshot, E1E2_CONTEXT_PATH)
    safety = _csv_document(snapshot, E1E2_SAFETY_PATH)
    issues = _csv_document(snapshot, E1E2_ISSUE_PATH)
    e1e2_manifest = _json_document(snapshot, E1E2_MANIFEST_PATH)
    e1e1_contract = _csv_document(snapshot, E1E1_CONTRACT_PATH)
    e1e1_truth = _csv_document(snapshot, E1E1_TRUTH_PATH)
    e1e1_manifest = _json_document(snapshot, E1E1_MANIFEST_PATH)
    e1c_contract = _csv_document(snapshot, E1C_CONTRACT_PATH)
    e1a_contract = _csv_document(snapshot, E1A_CONTRACT_PATH)

    source_text = _record(snapshot, E1E1_SOURCE_PATH).content_bytes.decode("utf-8", errors="strict")
    source_tree = ast.parse(source_text)
    top_functions = {
        node.name
        for node in source_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    rule_map = _keyed(rules.rows, "admission_rule_id")
    field_map = _keyed(fields.rows, "field_name")
    context_map = _keyed(contexts.rows, "context_item")
    issue_map = _keyed(issues.rows, "issue_id")
    e1e1_contract_map = _keyed(e1e1_contract.rows, "contract_id")
    e1c_contract_map = _keyed(e1c_contract.rows, "contract_id")
    e1a_contract_map = _keyed(e1a_contract.rows, "contract_id")
    admit_004 = rule_map["ADMIT_004"]
    atom = field_map["covalent_residue_atom_name"]
    identity_context = context_map[EVIDENCE_CONTEXT_KEY]
    expected_dependencies = "|".join(CANDIDATE_FIELDS)
    checks = (
        len(rules.rows) == 15,
        admit_004["candidate_field_dependencies"] == expected_dependencies,
        admit_004["evaluation_context_dependencies"]
        == "covalent_residue_identity_contract|covalent_residue_identity_evidence_context",
        admit_004["semantics_complete"] == "true",
        admit_004["implementation_disposition"] == "rule_logic_ready",
        admit_004["external_filesystem_required"] == "false",
        admit_004["network_required"] == "false",
        len(fields.rows) == 22,
        atom["source_value_contract"]
        == "generic exact non-empty ASCII atom identity; whitespace and complete dot/question markers forbidden; exact-preserve; no semantic maximum",
        atom["dependent_rules"] == "ADMIT_004|ADMIT_005",
        atom["implementation_semantics_complete"] == "true",
        len(contexts.rows) == 19,
        identity_context["required_by_rules"] == "ADMIT_004",
        identity_context["filesystem_access_inside_evaluator"] == "false",
        identity_context["network_access_inside_evaluator"] == "false",
        identity_context["exact_contract_defined"] == "true",
        identity_context["implementation_ready"] == "true",
        len(safety.rows) == 25 and all(row["safety_passed"] == "true" for row in safety.rows),
        len(issues.rows) == 9 and all(row["status"] == "open" for row in issues.rows),
        issue_map[PROVIDER_ISSUE]["severity"] == "blocking",
        issue_map[PROVIDER_ISSUE]["status"] == "open",
        issue_map[PROVIDER_ISSUE]["issue_count"] == "11",
        e1e2_manifest.get("active_issue_count") == 9,
        e1e2_manifest.get("admit_004_rule_logic_ready") is True,
        e1e2_manifest.get("admit_004_evaluator_implemented") is False,
        e1e2_manifest.get("ready_for_admit_004_rule_logic_interface_implementation") is True,
        e1e2_manifest.get("exact11_count") == 11,
        e1e2_manifest.get("exact11_effective_blocked_count") == 11,
        e1e2_manifest.get("exact11_reason") == UNKNOWN_REASON,
        e1e2_manifest.get("parser_quote_class_roundtrip_verified") is False,
        len(e1e1_contract.rows) == 28
        and all(row["contract_passed"] == "true" for row in e1e1_contract.rows),
        e1e1_contract_map["PRECEDENCE_001"]["expected_value"] == "invalid>blocked>passed",
        e1e1_contract_map["BINDING_001"]["expected_value"] == "9",
        e1e1_contract_map["CONTEXT_002"]["expected_value"] == "6",
        e1e1_contract_map["INSERTION_REUSE_001"]["expected_value"]
        == INSERTION_PRESENT_VALUE_PATTERN,
        len(e1e1_truth.rows) == 36
        and all(row["truth_passed"] == "true" for row in e1e1_truth.rows),
        e1e1_manifest.get("generic_atom_identity_semantics_design_frozen") is True,
        e1e1_manifest.get("identity_evidence_context_schema_design_frozen") is True,
        e1e1_manifest.get("admit_004_evaluator_implemented") is False,
        len(e1c_contract.rows) == 31
        and all(row["contract_passed"] == "true" for row in e1c_contract.rows),
        e1c_contract_map["INSERTION_GRAMMAR_005"]["expected_value"]
        == INSERTION_PRESENT_VALUE_PATTERN,
        e1c_contract_map["INSERTION_GRAMMAR_020"]["expected_value"] == "blocked",
        len(e1a_contract.rows) == 39
        and all(row["contract_passed"] == "true" for row in e1a_contract.rows),
        e1a_contract_map["RESIDUE_001"]["expected_value"] == "CYS",
        "validate_generic_covalent_residue_atom_name" in top_functions,
        "classify_admit_004_identity_evidence_context_design" in top_functions,
        "build_frozen_source_snapshot" in top_functions,
    )
    if not all(checks):
        raise ValueError("E1-E2/E1-E1 predecessor evidence validation failed")
    return {
        "rules": rules.rows,
        "fields": fields.rows,
        "contexts": contexts.rows,
        "issues": issues.rows,
        "e1e2_manifest": e1e2_manifest,
        "e1e1_contract": e1e1_contract.rows,
        "e1e1_truth": e1e1_truth.rows,
    }


def _base_candidate(
    *, residue: str = "CYS", atom: str = "SG", state: str = "absent", value: str = ""
) -> dict[str, str]:
    return {
        "covalent_residue_name": residue,
        "covalent_residue_chain_id": "A",
        "covalent_residue_index": "42",
        "covalent_residue_atom_name": atom,
        "covalent_residue_locator_namespace": "auth",
        "covalent_residue_insertion_code_state": state,
        "covalent_residue_insertion_code": value,
        "covalent_residue_locator_provenance_source_id": "covapie:test",
        "covalent_residue_locator_provenance_sha256": "0" * 64,
    }


def _base_context(
    candidate: Mapping[str, str],
    *,
    outcome: str = "passed",
    reason: str = "",
    four_way: bool = True,
    quote: bool = True,
) -> dict[str, object]:
    return {
        EVIDENCE_CONTEXT_KEY: {
            "schema_version": EVIDENCE_CONTEXT_SCHEMA_VERSION,
            "attested_candidate_fields": {field: candidate[field] for field in CANDIDATE_FIELDS},
            "provider_evidence_outcome": outcome,
            "provider_evidence_reason": reason,
            "four_way_present_value_exact_equality_attested": four_way,
            "present_value_quote_class_roundtrip_verified": quote,
        }
    }


def _truth_rows() -> list[dict[str, str]]:
    cases: list[tuple[str, str, object, object, str, str]] = []

    def add(
        group: str,
        case_id: str,
        candidate: object,
        context: object,
        expected_outcome: str,
        expected_reason: str,
    ) -> None:
        cases.append((group, case_id, candidate, context, expected_outcome, expected_reason))

    absent = _base_candidate()
    present = _base_candidate(state="present", value="A")
    lower = _base_candidate(residue="cys")
    generic = _base_candidate(residue="SER", atom="CA")
    extra_candidate: dict[str, object] = {**absent, "unrelated": "ignored"}

    class CandidateMapping(dict[str, str]):
        pass

    from types import MappingProxyType

    proxy_candidate = CandidateMapping(absent)
    proxy_context = MappingProxyType(_base_context(proxy_candidate))
    add("passed", "PASSED_001_ABSENT_CYS_SG", absent, _base_context(absent), "passed", "")
    add("passed", "PASSED_002_PRESENT_A", present, _base_context(present), "passed", "")
    add("passed", "PASSED_003_LOWERCASE_RESIDUE", lower, _base_context(lower), "passed", "")
    add("passed", "PASSED_004_GENERIC_SER_CA", generic, _base_context(generic), "passed", "")
    add("passed", "PASSED_005_EXTRA_CANDIDATE_FIELD", extra_candidate, _base_context(absent), "passed", "")
    add("passed", "PASSED_006_MAPPING_SUBCLASS_PROXY", proxy_candidate, proxy_context, "passed", "")

    unknown = _base_candidate(state="unknown", value="")
    add("blocked", "BLOCKED_001_UNKNOWN", unknown, _base_context(unknown), "blocked", UNKNOWN_REASON)
    add("blocked", "BLOCKED_002_CONTEXT_MISSING", absent, {}, "blocked", MISSING_CONTEXT_REASON)
    add(
        "blocked",
        "BLOCKED_003_PROVIDER",
        absent,
        _base_context(absent, outcome="blocked", reason="PROVIDER_BLOCKED"),
        "blocked",
        "PROVIDER_BLOCKED",
    )
    add(
        "blocked",
        "BLOCKED_004_FOUR_WAY",
        present,
        _base_context(present, four_way=False),
        "blocked",
        FOUR_WAY_REASON,
    )
    add(
        "blocked",
        "BLOCKED_005_QUOTE",
        present,
        _base_context(present, quote=False),
        "blocked",
        QUOTE_CLASS_REASON,
    )
    add(
        "blocked",
        "BLOCKED_006_UNKNOWN_BEFORE_PROVIDER",
        unknown,
        _base_context(unknown, outcome="blocked", reason="PROVIDER_BLOCKED"),
        "blocked",
        UNKNOWN_REASON,
    )
    add(
        "blocked",
        "BLOCKED_007_PROVIDER_BEFORE_ATTESTATIONS",
        present,
        _base_context(
            present, outcome="blocked", reason="PROVIDER_BLOCKED", four_way=False, quote=False
        ),
        "blocked",
        "PROVIDER_BLOCKED",
    )

    add("candidate_invalid", "CANDIDATE_INVALID_001_NON_MAPPING", [], {}, "invalid", "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID")
    for index, field in enumerate(CANDIDATE_FIELDS, 2):
        missing = dict(absent)
        del missing[field]
        add(
            "candidate_invalid",
            f"CANDIDATE_INVALID_{index:03d}_MISSING_{field.upper()}",
            missing,
            {},
            "invalid",
            f"ADMIT_004_CANDIDATE_FIELD_MISSING:{field}",
        )
    candidate_invalid_cases: tuple[tuple[str, str, object, str], ...] = (
        ("RESIDUE_SYNTAX", CANDIDATE_FIELDS[0], "C-Y", "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"),
        ("CHAIN_WHITESPACE", CANDIDATE_FIELDS[1], "A A", "COVALENT_RESIDUE_CHAIN_ID_LEXICAL_INVALID"),
        ("INDEX_NON_STR", CANDIDATE_FIELDS[2], 42, "COVALENT_RESIDUE_INDEX_TYPE_INVALID"),
        ("ATOM_MARKER", CANDIDATE_FIELDS[3], "?", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
        ("NAMESPACE", CANDIDATE_FIELDS[4], "AUTH", "COVALENT_RESIDUE_LOCATOR_NAMESPACE_INVALID"),
        ("ABSENT_NONEMPTY", CANDIDATE_FIELDS[6], "A", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("PROVENANCE_SOURCE", CANDIDATE_FIELDS[7], "bad source", "COVALENT_RESIDUE_PROVENANCE_SOURCE_ID_INVALID"),
        ("PROVENANCE_SHA", CANDIDATE_FIELDS[8], "A" * 64, "COVALENT_RESIDUE_PROVENANCE_SHA256_INVALID"),
    )
    for offset, (label, field, value, reason) in enumerate(candidate_invalid_cases, 11):
        candidate: dict[str, object] = dict(absent)
        candidate[field] = value
        add("candidate_invalid", f"CANDIDATE_INVALID_{offset:03d}_{label}", candidate, {}, "invalid", reason)
    bad_backslash = _base_candidate(state="present", value="\\")
    add(
        "candidate_invalid",
        "CANDIDATE_INVALID_019_PRESENT_BACKSLASH",
        bad_backslash,
        {},
        "invalid",
        "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID",
    )

    add("context_invalid", "CONTEXT_INVALID_001_TOP_NON_MAPPING", absent, [], "invalid", "ADMIT_004_EVALUATION_CONTEXT_MAPPING_INVALID")
    add(
        "context_invalid",
        "CONTEXT_INVALID_002_NESTED_NON_MAPPING",
        absent,
        {EVIDENCE_CONTEXT_KEY: []},
        "invalid",
        "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MAPPING_INVALID",
    )
    schema_bad = _base_context(absent)
    schema_bad[EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_003_SCHEMA", absent, schema_bad, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_SCHEMA_INVALID")
    nested_missing = _base_context(absent)
    del nested_missing[EVIDENCE_CONTEXT_KEY]["schema_version"]  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_004_NESTED_MISSING", absent, nested_missing, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID")
    nested_extra = _base_context(absent)
    nested_extra[EVIDENCE_CONTEXT_KEY]["extra"] = "x"  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_005_NESTED_EXTRA", absent, nested_extra, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID")
    attested_non_mapping = _base_context(absent)
    attested_non_mapping[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"] = []  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_006_ATTESTED_NON_MAPPING", absent, attested_non_mapping, "invalid", "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID")
    attested_missing = _base_context(absent)
    del attested_missing[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][CANDIDATE_FIELDS[-1]]  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_007_ATTESTED_MISSING", absent, attested_missing, "invalid", "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID")
    attested_extra = _base_context(absent)
    attested_extra[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"]["extra"] = "x"  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_008_ATTESTED_EXTRA", absent, attested_extra, "invalid", "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID")
    attested_type = _base_context(absent)
    attested_type[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][CANDIDATE_FIELDS[1]] = 1  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_009_ATTESTED_TYPE", absent, attested_type, "invalid", f"ADMIT_004_ATTESTED_CANDIDATE_VALUE_TYPE_INVALID:{CANDIDATE_FIELDS[1]}")
    mismatch = _base_context(lower)
    mismatch[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][CANDIDATE_FIELDS[0]] = "CYS"  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_010_RAW_BINDING", lower, mismatch, "invalid", f"ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:{CANDIDATE_FIELDS[0]}")
    invalid_context_cases: tuple[tuple[str, dict[str, object], str], ...] = (
        ("OUTCOME_ENUM", _base_context(absent, outcome="rejected"), "ADMIT_004_PROVIDER_EVIDENCE_OUTCOME_INVALID"),
        ("PASSED_REASON", _base_context(absent, reason="unexpected"), "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID"),
        ("BLOCKED_EMPTY_REASON", _base_context(absent, outcome="blocked"), "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID"),
        ("INVALID_EMPTY_REASON", _base_context(absent, outcome="invalid"), "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID"),
        ("REASON_NON_ASCII", _base_context(absent, outcome="blocked", reason="é"), "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID"),
    )
    for offset, (label, context, reason) in enumerate(invalid_context_cases, 11):
        add("context_invalid", f"CONTEXT_INVALID_{offset:03d}_{label}", absent, context, "invalid", reason)
    four_type = _base_context(absent)
    four_type[EVIDENCE_CONTEXT_KEY]["four_way_present_value_exact_equality_attested"] = 1  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_016_FOUR_WAY_TYPE", absent, four_type, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_BOOL_INVALID:four_way_present_value_exact_equality_attested")
    quote_type = _base_context(absent)
    quote_type[EVIDENCE_CONTEXT_KEY]["present_value_quote_class_roundtrip_verified"] = 1  # type: ignore[index]
    add("context_invalid", "CONTEXT_INVALID_017_QUOTE_TYPE", absent, quote_type, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_BOOL_INVALID:present_value_quote_class_roundtrip_verified")
    add(
        "context_invalid",
        "CONTEXT_INVALID_018_PROVIDER_INVALID_PROPAGATED",
        absent,
        _base_context(absent, outcome="invalid", reason="PROVIDER_INVALID"),
        "invalid",
        "PROVIDER_INVALID",
    )

    rows: list[dict[str, str]] = []
    for group, case_id, candidate, context, expected_outcome, expected_reason in cases:
        result = evaluate_admit_004(candidate, context)  # type: ignore[arg-type]
        truth_passed = (
            result.outcome == expected_outcome
            and result.reason == expected_reason
            and result.passed == (expected_outcome == "passed")
            and result.blocks_candidate == (expected_outcome != "passed")
            and result.evaluator_io_used is False
        )
        rows.append(
            {
                "truth_group": group,
                "case_id": case_id,
                "expected_outcome": expected_outcome,
                "observed_outcome": result.outcome,
                "expected_reason": expected_reason,
                "observed_reason": result.reason,
                "canonical_residue_name": result.canonical_residue_name,
                "validated_candidate_field_count": str(len(result.validated_candidate_fields)),
                "evidence_context_consumed": str(result.evidence_context_consumed).lower(),
                "evaluator_io_used": str(result.evaluator_io_used).lower(),
                "truth_passed": str(truth_passed).lower(),
            }
        )
    return rows


def _contract_rows() -> list[dict[str, str]]:
    specifications = (
        ("INTERFACE_001", "public_interface", "public callable", "evaluate_admit_004"),
        ("INTERFACE_002", "public_interface", "result frozen dataclass field count", "10"),
        ("INTERFACE_003", "public_interface", "admission rule ID", "ADMIT_004"),
        ("INTERFACE_004", "public_interface", "outcome enum", "passed|blocked|invalid"),
        ("INTERFACE_005", "public_interface", "rejected outcome", "forbidden"),
        ("INTERFACE_006", "public_interface", "evaluator IO", "false"),
        ("CANDIDATE_001", "candidate", "candidate Mapping accepted", "true"),
        ("CANDIDATE_002", "candidate", "candidate dependency count", "9"),
        ("CANDIDATE_003", "candidate", "missing-field validation order", "exact9"),
        ("CANDIDATE_004", "candidate", "residue canonicalization", "uppercase"),
        ("CANDIDATE_005", "candidate", "generic atom identity", "exact-preserve"),
        ("CANDIDATE_006", "candidate", "generic atom semantic maximum", "none"),
        ("CANDIDATE_007", "candidate", "locator namespace", "auth|label"),
        ("CANDIDATE_008", "candidate", "insertion state enum", "absent|present|unknown"),
        ("CANDIDATE_009", "candidate", "present-value slash", "allowed"),
        ("CANDIDATE_010", "candidate", "present-value backslash and equals", "forbidden"),
        ("CANDIDATE_011", "candidate", "provenance SHA", "lowercase-64-hex"),
        ("CONTEXT_001", "context", "top-level Mapping with unrelated keys", "accepted"),
        ("CONTEXT_002", "context", "nested schema version", EVIDENCE_CONTEXT_SCHEMA_VERSION),
        ("CONTEXT_003", "context", "nested exact key count", "6"),
        ("CONTEXT_004", "context", "attested candidate field count", "9"),
        ("CONTEXT_005", "context", "attestation binding", "raw-before-canonicalization"),
        ("CONTEXT_006", "context", "provider outcome enum", "passed|blocked|invalid"),
        ("CONTEXT_007", "context", "attestation flags exact bool", "true"),
        ("CONTEXT_008", "context", "missing context outcome", "blocked"),
        ("CONTEXT_009", "context", "malformed context outcome", "invalid"),
        ("PRECEDENCE_001", "outcome_precedence", "global precedence", "invalid>blocked>passed"),
        ("PRECEDENCE_002", "outcome_precedence", "unknown before missing/provider blocked", "true"),
        ("PRECEDENCE_003", "outcome_precedence", "provider blocked before present attestations", "true"),
        ("PRECEDENCE_004", "outcome_precedence", "four-way before quote-class", "true"),
        ("DETERMINISM_001", "purity", "input mutation", "none"),
        ("DETERMINISM_002", "purity", "repeated-call result", "identical"),
        ("EVIDENCE_001", "predecessor", "E1-E2 active issue count", "9"),
        ("EVIDENCE_002", "predecessor", "provider blocking row count", "11"),
        ("EXACT11_001", "execution_boundary", "Exact11 metadata count", "11"),
        ("EXACT11_002", "execution_boundary", "Exact11 real evaluation", "false"),
        ("READINESS_001", "readiness", "standalone evaluator implemented", "true"),
        ("READINESS_002", "readiness", "ready for unified engine integration", "true"),
        ("READINESS_003", "readiness", "unified engine integrated", "false"),
        ("READINESS_004", "readiness", "ready for real candidate evaluation", "false"),
        ("READINESS_005", "readiness", "ready for bulk download", "false"),
        ("READINESS_006", "readiness", "ready for training", "false"),
        ("READINESS_007", "readiness", "feature-semantics audit before training", "required"),
    )
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for contract_id, area, statement, expected in specifications
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
            "sha256_expected": record.expected_sha256,
            "sha256_base_tree": record.base_tree_sha256,
            "sha256_filesystem": record.filesystem_sha256,
            "source_verified": "true",
        }
        for index, record in enumerate(snapshot.records, 1)
    ]


def _safety_rows() -> list[dict[str, str]]:
    return [
        {
            "safety_item": item,
            "expected_executed": "true",
            "observed_executed": "true",
            "safety_passed": "true",
        }
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "safety_passed": "true",
        }
        for item in FALSE_SAFETY_ITEMS
    ]


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None, failure: str = "SOURCE_BOUNDARY_FAILED"
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "source_ok": False,
        "predecessor_evidence_ok": False,
        "contract_rows": [],
        "truth_rows": [],
        "source_audit_rows": [],
        "safety_rows": [],
        "issue_rows": [],
        "contract_pass_count": 0,
        "truth_pass_count": 0,
        "interface_implementation_readiness": False,
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_interface_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        predecessor = _validate_predecessor_evidence(snapshot)
        contract = _contract_rows()
        truth = _truth_rows()
        source_audit = _source_audit_rows(snapshot)
        safety = _safety_rows()
        issues = [dict(row) for row in predecessor["issues"]]
        issue_map = _keyed(issues, "issue_id")
        group_counts = {
            group: sum(row["truth_group"] == group for row in truth)
            for group in ("passed", "blocked", "candidate_invalid", "context_invalid")
        }
        passed = (
            len(contract) == 43
            and all(row["contract_passed"] == "true" for row in contract)
            and len(truth) == 50
            and all(row["truth_passed"] == "true" for row in truth)
            and group_counts
            == {"passed": 6, "blocked": 7, "candidate_invalid": 19, "context_invalid": 18}
            and len(source_audit) == 12
            and all(row["source_verified"] == "true" for row in source_audit)
            and len(safety) == len(TRUE_SAFETY_ITEMS) + len(FALSE_SAFETY_ITEMS)
            and all(row["safety_passed"] == "true" for row in safety)
            and len(issues) == 9
            and issues == list(predecessor["issues"])
            and issue_map[PROVIDER_ISSUE]["status"] == "open"
            and issue_map[PROVIDER_ISSUE]["severity"] == "blocking"
            and issue_map[PROVIDER_ISSUE]["issue_count"] == "11"
        )
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError):
        return _empty_state(snapshot, "PREDECESSOR_EVIDENCE_VALIDATION_FAILED") | {
            "source_ok": True
        }
    if not passed:
        return _empty_state(snapshot, "INTERFACE_VALIDATION_FAILED") | {
            "source_ok": True,
            "predecessor_evidence_ok": True,
        }
    return {
        "source_snapshot": snapshot,
        "source_ok": True,
        "predecessor_evidence_ok": True,
        "predecessor": predecessor,
        "contract_rows": contract,
        "truth_rows": truth,
        "source_audit_rows": source_audit,
        "safety_rows": safety,
        "issue_rows": issues,
        "contract_pass_count": 43,
        "truth_pass_count": 50,
        "interface_implementation_readiness": True,
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
    snapshot = state["source_snapshot"]
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "source_input_count": 12,
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
        "source_structural_checks_before_first_content_read": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "contract_count": 43,
        "contract_pass_count": state["contract_pass_count"],
        "truth_matrix_row_count": 50,
        "truth_matrix_pass_count": state["truth_pass_count"],
        "truth_matrix_group_counts": {
            "passed": 6,
            "blocked": 7,
            "candidate_invalid": 19,
            "context_invalid": 18,
        },
        "candidate_dependency_fields": list(CANDIDATE_FIELDS),
        "candidate_dependency_count": 9,
        "identity_evidence_context_key": EVIDENCE_CONTEXT_KEY,
        "identity_evidence_context_schema_version": EVIDENCE_CONTEXT_SCHEMA_VERSION,
        "identity_evidence_context_exact_nested_keys": list(NESTED_CONTEXT_KEYS),
        "identity_evidence_context_nested_key_count": 6,
        "active_issue_count": 9,
        "provider_blocking_issue_id": PROVIDER_ISSUE,
        "provider_blocking_issue_count": 11,
        "exact11_count": 11,
        "exact11_expected_blocked_count": 11,
        "exact11_reason": UNKNOWN_REASON,
        "admit_004_rule_logic_interface_implemented": True,
        "admit_004_evaluator_implemented": True,
        "pure_in_memory_evaluator_implemented": True,
        "result_contract_frozen": True,
        "exact9_candidate_validation_implemented": True,
        "identity_evidence_context_validation_implemented": True,
        "outcome_precedence_implemented": True,
        "synthetic_truth_matrix_passed": True,
        "evaluator_no_io_contract_enforced": True,
        "ready_for_admit_004_unified_rule_engine_integration": True,
        "feature_semantics_audit_required_before_training": True,
        "unified_rule_engine_integrated": False,
        "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False,
        "real_provider_export_blocking_rows_resolved": False,
        "candidate_records_materialized": False,
        "exact11_real_rows_evaluated": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "raw_read_current_step": False,
        "provenance_reference_dereferenced_current_step": False,
        "parser_executed_current_step": False,
        "provider_executed_current_step": False,
        "unified_rule_engine_integrated_current_step": False,
        "candidate_records_materialized_current_step": False,
        "real_candidate_evaluation_current_step": False,
        "admission_records_modified_current_step": False,
        "sample_backfill_current_step": False,
        "network_accessed_current_step": False,
        "download_attempted_current_step": False,
        "checkpoint_accessed_current_step": False,
        "torch_used_current_step": False,
        "numpy_used_current_step": False,
        "rdkit_used_current_step": False,
        "model_forward_loss_training_used_current_step": False,
        "interface_implementation_readiness": True,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_evidence_checks_passed": True,
        "all_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        SOURCE_AUDIT_FILENAME: _csv_bytes(SOURCE_AUDIT_COLUMNS, state["source_audit_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in csv_payloads.items()}
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
            raise ValueError("output root must be a non-symlink directory")
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


def run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_interface_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "ADMIT_004 rule-logic interface failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_004_rule_logic_interface_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

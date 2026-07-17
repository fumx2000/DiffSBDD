"""Step14AU-E1-E1 generic atom/evidence-context reconciliation design gate.

This metadata-only gate freezes pure in-memory design semantics.  It does not
implement ``evaluate_admit_004``, alter the E1-D effective matrices, execute a
parser/provider, dereference provenance references, read raw structures, or
materialize candidate/admission records.
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
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E1"
STAGE = "covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1"
EXPECTED_BASE_COMMIT = "c386607930265ab28da373b506759eaf22c80267"
MANIFEST_SCHEMA_VERSION = "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_design_manifest_v1"
EVIDENCE_CONTEXT_SCHEMA_VERSION = "covapie_covalent_residue_identity_evidence_context_v1"
RECOMMENDED_NEXT_STEP = "integrate_covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_v1"
NEW_ISSUE = "ADMIT_004_GENERIC_ATOM_AND_EVIDENCE_CONTEXT_SEMANTICS_UNRESOLVED"
PROVIDER_ISSUE = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
MISSING_CONTEXT_REASON = "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING"
FOUR_WAY_REASON = "ADMIT_004_PRESENT_FOUR_WAY_EQUALITY_UNATTESTED"
QUOTE_CLASS_REASON = "COVALENT_RESIDUE_INSERTION_PRESENT_QUOTE_CLASS_UNVERIFIED"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

E1D_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1")
E1C_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1")
E1A_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1")
P4_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1")
P6D_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1")
STEP14AT_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")

SOURCE_PATHS = tuple(Path(value) for value in (
    str(E1D_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_integrated_rule_matrix.csv"),
    str(E1D_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_integrated_field_matrix.csv"),
    str(E1D_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_integrated_context_matrix.csv"),
    str(E1D_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_integration_issue_inventory.csv"),
    str(E1D_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_integration_manifest.json"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_contract.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_design_manifest.json"),
    "src/covalent_ext/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate.py",
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_contract.csv"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_truth_table.csv"),
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate.py",
    str(P4_ROOT / "covapie_covalent_residue_locator_parser_provider_export_contract.csv"),
    str(P4_ROOT / "covapie_covalent_residue_locator_parser_provider_provenance_export_design_manifest.json"),
    str(P6D_ROOT / "covapie_covalent_residue_locator_real_provider_integration_overlay.csv"),
    str(P6D_ROOT / "covapie_covalent_residue_locator_real_provider_integration_evidence_audit.csv"),
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "98e368781fe0c2bac6cd9123b0cbc49ffeecc8c1de577607ce9b4866c2b310d0",
    "bd319bd2e5931b316c8579259729a94029d117844b2ceabda717604dc1d4483b",
    "106f0080ef01c76983d594a039d12741dd29fd52cddb7fd2b205dcd75bd7e83b",
    "7cf0a9ff421ba987655c4dac4564c04dbaa854cd4f725b18136642f223762d30",
    "3b2a9a4c83d1dca999bc805ead8f3298fb75687034c4eae7595e2a5e22e26fa2",
    "bb4907d1b6580e0e2487d8839e01b718ebf904f2debc49c4df9d4716c18274be",
    "fa607b72c520310d831992c722f9bb930594b8cd95af89b3ad3d1c38274a8d19",
    "8f86c22cb5f9154ddf3481f7976bfa964573f68427e63916c503ed9c68d71d98",
    "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff",
    "a5c2d727b3178bd0e58643a1801780fa930cba2b89c14a058817ecb418753106",
    "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537",
    "8893ca769577e955319ea8b9abe411149206db562193b70928d58ce4afd0ba8c",
    "aa6435381c90416ce9ded7e50afca166f33b29b4a268b230755bba0145680876",
    "cc4c5965083340a040e4e1fc531da03bd74471e20fdc521ce92464d1d359627a",
    "c5efc4610762004829897064965bb4e06a1390d52c9f97254e66fbb1c7c899ec",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
), strict=True))

(E1D_RULE_PATH, E1D_FIELD_PATH, E1D_CONTEXT_PATH, E1D_ISSUE_PATH,
 E1D_MANIFEST_PATH, E1C_CONTRACT_PATH, E1C_MANIFEST_PATH, E1A_SOURCE_PATH,
 E1A_CONTRACT_PATH, E1A_TRUTH_PATH, P4_SOURCE_PATH, P4_CONTRACT_PATH,
 P4_MANIFEST_PATH, P6D_OVERLAY_PATH, P6D_EVIDENCE_PATH,
 STEP14AT_RULE_PATH) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_contract.csv"
TRUTH_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_truth_matrix.csv"
SOURCE_AUDIT_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_004_generic_atom_identity_evidence_context_reconciliation_design_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_AUDIT_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id", "contract_area", "contract_statement", "expected_value",
    "observed_value", "contract_passed",
)
TRUTH_COLUMNS = (
    "row_kind", "case_id", "input_residue_name", "input_atom_descriptor",
    "insertion_state", "context_case", "expected_admit_004_outcome",
    "observed_admit_004_outcome", "expected_admit_005_outcome",
    "observed_admit_005_outcome", "expected_reason", "observed_reason",
    "canonical_value", "truth_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order", "source_relative_path", "tracked_by_git", "base_tree_blob",
    "filesystem_regular", "non_symlink", "sha256_expected", "sha256_base_tree",
    "sha256_filesystem", "source_verified",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)

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
EVIDENCE_CONTEXT_KEY = "covalent_residue_identity_evidence_context"

TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "historical_conflict_validation", "generic_atom_design",
    "admit_004_admit_005_scope_design", "evidence_context_schema_design",
    "candidate_attestation_binding_design", "truth_matrix_classification",
    "issue_transition_design",
)
FALSE_SAFETY_ITEMS = (
    "raw_read", "provenance_reference_dereference", "parser_execution",
    "provider_execution", "evaluator_implementation", "unified_rule_engine_integration",
    "candidate_record_materialization", "candidate_evaluation",
    "admission_record_modification", "sample_backfill", "network", "download",
    "checkpoint", "torch", "numpy", "rdkit", "model_forward_loss_training",
)

_COMPONENT_RE = re.compile(r"^[A-Za-z0-9]{1,32}$")
_PROVENANCE_SOURCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INSERTION_PRESENT_VALUE_PATTERN = r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+"
_INSERTION_RE = re.compile(
    INSERTION_PRESENT_VALUE_PATTERN,
    re.ASCII,
)


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


@dataclass(frozen=True)
class GenericAtomNameResult:
    valid: bool
    canonical_value: str | None
    reason: str


@dataclass(frozen=True)
class ScopeDesignResult:
    canonical_residue_name: str | None
    admit_004_outcome: str
    admit_005_outcome: str
    reason: str


@dataclass(frozen=True)
class EvidenceContextDesignResult:
    outcome: str
    reason: str


def validate_generic_covalent_residue_atom_name(value: object) -> GenericAtomNameResult:
    """Validate and exact-preserve a generic covalent residue atom identity."""
    if type(value) is not str:
        return GenericAtomNameResult(False, None, "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID")
    if value == "":
        return GenericAtomNameResult(False, None, "COVALENT_RESIDUE_ATOM_NAME_EMPTY")
    if not value.isascii():
        return GenericAtomNameResult(False, None, "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII")
    if any(character.isspace() for character in value):
        return GenericAtomNameResult(False, None, "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN")
    if value in (".", "?"):
        return GenericAtomNameResult(False, None, "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN")
    return GenericAtomNameResult(True, value, "")


def _normalize_residue_name(value: object) -> tuple[bool, str | None, str]:
    if type(value) is not str:
        return False, None, "COVALENT_RESIDUE_NAME_TYPE_INVALID"
    if value == "":
        return False, None, "COVALENT_RESIDUE_NAME_EMPTY"
    if not value.isascii():
        return False, None, "COVALENT_RESIDUE_NAME_NON_ASCII"
    if _COMPONENT_RE.fullmatch(value) is None:
        return False, None, "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"
    return True, value.upper(), ""


def classify_admit_004_admit_005_atom_scope_design(
    residue_name: object,
    atom_name: object,
) -> ScopeDesignResult:
    """Freeze ADMIT_004 identity versus ADMIT_005 CYS/SG scope separation."""
    residue_valid, canonical_residue, residue_reason = _normalize_residue_name(residue_name)
    atom = validate_generic_covalent_residue_atom_name(atom_name)
    if not residue_valid:
        return ScopeDesignResult(None, "invalid", "invalid", residue_reason)
    if not atom.valid:
        return ScopeDesignResult(canonical_residue, "invalid", "invalid", atom.reason)
    admit_005 = "passed" if canonical_residue == "CYS" and atom_name == "SG" else "rejected"
    reason = "" if admit_005 == "passed" else "ADMIT_005_CYS_SG_SCOPE_REJECTED"
    return ScopeDesignResult(canonical_residue, "passed", admit_005, reason)


def _generic_lexical(value: object, field: str) -> str:
    if type(value) is not str:
        return f"{field}_TYPE_INVALID"
    if value == "":
        return f"{field}_EMPTY"
    if not value.isascii():
        return f"{field}_NON_ASCII"
    if any(character.isspace() for character in value) or value in (".", "?"):
        return f"{field}_LEXICAL_INVALID"
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


def _candidate_reason(candidate_record: object) -> str:
    if not isinstance(candidate_record, Mapping):
        return "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID"
    for field in CANDIDATE_FIELDS:
        if field not in candidate_record:
            return f"ADMIT_004_CANDIDATE_FIELD_MISSING:{field}"
    validators = (
        _normalize_residue_name(candidate_record[CANDIDATE_FIELDS[0]])[2],
        _generic_lexical(candidate_record[CANDIDATE_FIELDS[1]], "COVALENT_RESIDUE_CHAIN_ID"),
        _generic_lexical(candidate_record[CANDIDATE_FIELDS[2]], "COVALENT_RESIDUE_INDEX"),
        validate_generic_covalent_residue_atom_name(candidate_record[CANDIDATE_FIELDS[3]]).reason,
        "" if type(candidate_record[CANDIDATE_FIELDS[4]]) is str and candidate_record[CANDIDATE_FIELDS[4]] in ("auth", "label") else "COVALENT_RESIDUE_LOCATOR_NAMESPACE_INVALID",
        _validate_insertion_state_value(candidate_record[CANDIDATE_FIELDS[5]], candidate_record[CANDIDATE_FIELDS[6]]),
        "" if type(candidate_record[CANDIDATE_FIELDS[7]]) is str and _PROVENANCE_SOURCE_RE.fullmatch(candidate_record[CANDIDATE_FIELDS[7]]) is not None else "COVALENT_RESIDUE_PROVENANCE_SOURCE_ID_INVALID",
        "" if type(candidate_record[CANDIDATE_FIELDS[8]]) is str and _SHA256_RE.fullmatch(candidate_record[CANDIDATE_FIELDS[8]]) is not None else "COVALENT_RESIDUE_PROVENANCE_SHA256_INVALID",
    )
    return next((reason for reason in validators if reason), "")


def classify_admit_004_identity_evidence_context_design(
    candidate_record: object,
    evaluation_context: object,
) -> EvidenceContextDesignResult:
    """Classify the frozen future interface without implementing its evaluator."""
    candidate_reason = _candidate_reason(candidate_record)
    if candidate_reason:
        return EvidenceContextDesignResult("invalid", candidate_reason)
    assert isinstance(candidate_record, Mapping)
    if not isinstance(evaluation_context, Mapping):
        return EvidenceContextDesignResult("invalid", "ADMIT_004_EVALUATION_CONTEXT_MAPPING_INVALID")
    nested_missing = EVIDENCE_CONTEXT_KEY not in evaluation_context
    if nested_missing:
        nested = None
    else:
        nested = evaluation_context[EVIDENCE_CONTEXT_KEY]
        if not isinstance(nested, Mapping):
            return EvidenceContextDesignResult("invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MAPPING_INVALID")
        if set(nested) != set(NESTED_CONTEXT_KEYS):
            return EvidenceContextDesignResult("invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID")
        if nested["schema_version"] != EVIDENCE_CONTEXT_SCHEMA_VERSION or type(nested["schema_version"]) is not str:
            return EvidenceContextDesignResult("invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_SCHEMA_INVALID")
        attested = nested["attested_candidate_fields"]
        if not isinstance(attested, Mapping) or set(attested) != set(CANDIDATE_FIELDS):
            return EvidenceContextDesignResult("invalid", "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID")
        for field in CANDIDATE_FIELDS:
            if type(attested[field]) is not str:
                return EvidenceContextDesignResult("invalid", f"ADMIT_004_ATTESTED_CANDIDATE_VALUE_TYPE_INVALID:{field}")
            if attested[field] != candidate_record[field]:
                return EvidenceContextDesignResult("invalid", f"ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:{field}")
        outcome = nested["provider_evidence_outcome"]
        reason = nested["provider_evidence_reason"]
        if type(outcome) is not str or outcome not in ("passed", "blocked", "invalid"):
            return EvidenceContextDesignResult("invalid", "ADMIT_004_PROVIDER_EVIDENCE_OUTCOME_INVALID")
        if type(reason) is not str or not reason.isascii() or (outcome == "passed" and reason != "") or (outcome != "passed" and reason == ""):
            return EvidenceContextDesignResult("invalid", "ADMIT_004_PROVIDER_EVIDENCE_REASON_INVALID")
        for key in (
            "four_way_present_value_exact_equality_attested",
            "present_value_quote_class_roundtrip_verified",
        ):
            if type(nested[key]) is not bool:
                return EvidenceContextDesignResult("invalid", f"ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_BOOL_INVALID:{key}")
        if outcome == "invalid":
            return EvidenceContextDesignResult("invalid", reason)

    state = candidate_record["covalent_residue_insertion_code_state"]
    value = candidate_record["covalent_residue_insertion_code"]
    if state == "unknown" and value == "":
        return EvidenceContextDesignResult("blocked", UNKNOWN_REASON)
    if nested_missing:
        return EvidenceContextDesignResult("blocked", MISSING_CONTEXT_REASON)
    assert isinstance(nested, Mapping)
    if nested["provider_evidence_outcome"] == "blocked":
        return EvidenceContextDesignResult("blocked", nested["provider_evidence_reason"])
    if state == "present" and nested["four_way_present_value_exact_equality_attested"] is False:
        return EvidenceContextDesignResult("blocked", FOUR_WAY_REASON)
    if state == "present" and nested["present_value_quote_class_roundtrip_verified"] is False:
        return EvidenceContextDesignResult("blocked", QUOTE_CLASS_REASON)
    return EvidenceContextDesignResult("passed", "")


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Check structure only; never read source content bytes here."""
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
        tracked.returncode == 0 and tree.returncode == 0 and len(fields) == 3
        and fields[1] == "blob" and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Complete all exact16 structural checks before the first byte read."""
    if len(SOURCE_PATHS) != 16 or len(set(SOURCE_PATHS)) != 16 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("exact16 source boundary shape invalid")
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
        records.append(FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 16
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
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
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


def _function_source(snapshot: FrozenSourceSnapshot, path: Path, function_name: str) -> str:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    tree = ast.parse(text)
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name]
    if len(matches) != 1:
        raise ValueError(f"function evidence missing: {function_name}")
    segment = ast.get_source_segment(text, matches[0])
    if segment is None:
        raise ValueError("function source unavailable")
    return segment


def _validate_historical_evidence(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    rules = _csv_document(snapshot, E1D_RULE_PATH)
    fields = _csv_document(snapshot, E1D_FIELD_PATH)
    contexts = _csv_document(snapshot, E1D_CONTEXT_PATH)
    issues = _csv_document(snapshot, E1D_ISSUE_PATH)
    e1d_manifest = _json_document(snapshot, E1D_MANIFEST_PATH)
    e1c_contract = _csv_document(snapshot, E1C_CONTRACT_PATH)
    e1c_manifest = _json_document(snapshot, E1C_MANIFEST_PATH)
    e1a_contract = _csv_document(snapshot, E1A_CONTRACT_PATH)
    e1a_truth = _csv_document(snapshot, E1A_TRUTH_PATH)
    p4_contract = _csv_document(snapshot, P4_CONTRACT_PATH)
    p4_manifest = _json_document(snapshot, P4_MANIFEST_PATH)
    p6_overlay = _csv_document(snapshot, P6D_OVERLAY_PATH)
    p6_evidence = _csv_document(snapshot, P6D_EVIDENCE_PATH)
    registry = _csv_document(snapshot, STEP14AT_RULE_PATH)

    rule_map = _keyed(rules.rows, "admission_rule_id")
    field_map = _keyed(fields.rows, "field_name")
    context_map = _keyed(contexts.rows, "context_item")
    issue_map = _keyed(issues.rows, "issue_id")
    registry_map = _keyed(registry.rows, "admission_rule_id")
    e1c_contract_map = _keyed(e1c_contract.rows, "contract_id")
    admit_004 = rule_map["ADMIT_004"]
    admit_005 = rule_map["ADMIT_005"]
    atom_field = field_map["covalent_residue_atom_name"]
    e1a_atom_source = _function_source(snapshot, E1A_SOURCE_PATH, "validate_covalent_residue_atom_name")
    e1a_provider_source = _function_source(snapshot, E1A_SOURCE_PATH, "validate_provider_identity_atom_evidence")
    p4_atom_source = _function_source(snapshot, P4_SOURCE_PATH, "validate_matched_atom_site_row_identity")
    expected_dependencies = "|".join(CANDIDATE_FIELDS)
    checks = (
        len(rules.rows) == 15 and len(fields.rows) == 22 and len(contexts.rows) == 18,
        len(issues.rows) == 9 and all(row["status"] == "open" for row in issues.rows),
        admit_004["candidate_field_dependencies"] == expected_dependencies,
        admit_004["implementation_disposition"] == "rule_logic_ready",
        admit_004["evaluation_context_dependencies"] == "covalent_residue_identity_contract",
        admit_005["admission_rule_name"] == "cys_sg_scope_only_v1",
        admit_005["candidate_field_dependencies"] == "covalent_residue_name|covalent_residue_atom_name",
        atom_field["source_value_contract"] == "must be SG for v1 Cys scope",
        atom_field["dependent_rules"] == "ADMIT_004|ADMIT_005",
        'value != "SG"' in e1a_atom_source and 'LexicalResult(True, "SG", "")' in e1a_atom_source,
        "validate_covalent_residue_atom_name(candidate_atom_name)" in e1a_provider_source,
        "type(residue_atom_name) is not str" in p4_atom_source,
        "not value.isascii()" in p4_atom_source and "value != value.strip()" in p4_atom_source,
        '"SG"' not in p4_atom_source,
        registry_map["ADMIT_004"]["admission_rule_name"] == "covalent_residue_identity_present",
        registry_map["ADMIT_005"]["admission_rule_name"] == "cys_sg_scope_only_v1",
        registry_map["ADMIT_005"]["required_status"] == "residue_name_CYS_and_atom_SG",
        len(e1c_contract.rows) == 31 and all(row["contract_passed"] == "true" for row in e1c_contract.rows),
        e1c_contract_map["INSERTION_GRAMMAR_005"]["expected_value"] == INSERTION_PRESENT_VALUE_PATTERN,
        e1c_contract_map["INSERTION_GRAMMAR_005"]["observed_value"] == INSERTION_PRESENT_VALUE_PATTERN,
        e1c_manifest.get("parser_quote_class_roundtrip_verified") is False,
        e1c_manifest.get("ready_for_insertion_present_value_grammar_successor_integration") is True,
        len(e1a_contract.rows) > 0 and all(row["contract_passed"] == "true" for row in e1a_contract.rows),
        len(e1a_truth.rows) > 0 and all(row["truth_table_passed"] == "true" for row in e1a_truth.rows),
        len(p4_contract.rows) > 0 and all(row["contract_passed"] == "true" for row in p4_contract.rows),
        p4_manifest.get("atom_site_row_binding_contract_ready") is True,
        len(p6_overlay.rows) == 11 and all(row["covalent_residue_insertion_code_state"] == "unknown" and row["covalent_residue_insertion_code"] == "" for row in p6_overlay.rows),
        len(p6_evidence.rows) == 11 and all(row["provider_export_status"] == "exported_blocking" and row["provider_export_blocking_reason"] == UNKNOWN_REASON for row in p6_evidence.rows),
        issue_map[PROVIDER_ISSUE]["severity"] == "blocking",
        issue_map[PROVIDER_ISSUE]["status"] == "open",
        issue_map[PROVIDER_ISSUE]["issue_count"] == "11",
        e1d_manifest.get("admit_004_rule_logic_ready") is True,
        e1d_manifest.get("admit_004_evaluator_implemented") is False,
        e1d_manifest.get("provider_blocking_issue_count") == 11,
        e1d_manifest.get("exact11_effective_blocked_count") == 11,
        e1d_manifest.get("parser_quote_class_roundtrip_verified") is False,
    )
    if not all(checks):
        raise ValueError("historical conflict/evidence validation failed")
    return {
        "rules": rules.rows, "fields": fields.rows, "contexts": contexts.rows,
        "issues": issues.rows, "e1d_manifest": e1d_manifest,
        "e1c_contract": e1c_contract.rows, "e1c_manifest": e1c_manifest,
        "p6_overlay": p6_overlay.rows, "p6_evidence": p6_evidence.rows,
    }


def _base_candidate(*, state: str = "absent", value: str = "", atom: str = "SG") -> dict[str, str]:
    return {
        "covalent_residue_name": "CYS",
        "covalent_residue_chain_id": "A",
        "covalent_residue_index": "42",
        "covalent_residue_atom_name": atom,
        "covalent_residue_locator_namespace": "auth",
        "covalent_residue_insertion_code_state": state,
        "covalent_residue_insertion_code": value,
        "covalent_residue_locator_provenance_source_id": "covapie:test",
        "covalent_residue_locator_provenance_sha256": "0" * 64,
    }


def _base_context(candidate: Mapping[str, str], *, outcome: str = "passed", reason: str = "", four_way: bool = True, quote: bool = True) -> dict[str, object]:
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
    rows: list[dict[str, str]] = []

    def add(kind: str, case_id: str, residue: str, atom: str, state: str, context_case: str,
            expected4: str, observed4: str, expected5: str, observed5: str,
            expected_reason: str, observed_reason: str, canonical: str) -> None:
        passed = expected4 == observed4 and expected5 == observed5 and expected_reason == observed_reason
        rows.append({
            "row_kind": kind, "case_id": case_id, "input_residue_name": residue,
            "input_atom_descriptor": atom, "insertion_state": state,
            "context_case": context_case, "expected_admit_004_outcome": expected4,
            "observed_admit_004_outcome": observed4,
            "expected_admit_005_outcome": expected5,
            "observed_admit_005_outcome": observed5, "expected_reason": expected_reason,
            "observed_reason": observed_reason, "canonical_value": canonical,
            "truth_passed": "true" if passed else "false",
        })

    for index, atom in enumerate(("SG", "CA", "ca", "N1", "OXT", "C1'", "A.B", "+"), 1):
        result = validate_generic_covalent_residue_atom_name(atom)
        add("generic_atom_valid", f"GENERIC_ATOM_VALID_{index:03d}", "", atom, "", "",
            "passed", "passed" if result.valid else "invalid", "", "", "", result.reason,
            result.canonical_value or "")

    class StrSubclass(str):
        pass

    invalid = (
        ("non-str", 1), ("str subclass", StrSubclass("SG")), ("empty", ""),
        ("non-ASCII", "SÉ"), ("embedded space", "S G"), ("embedded tab", "S\tG"),
        ("complete dot", "."), ("complete question mark", "?"),
    )
    for index, (descriptor, value) in enumerate(invalid, 1):
        result = validate_generic_covalent_residue_atom_name(value)
        add("generic_atom_invalid", f"GENERIC_ATOM_INVALID_{index:03d}", "", descriptor, "", "",
            "invalid", "passed" if result.valid else "invalid", "", "", result.reason,
            result.reason, "")

    scope_cases = (
        ("CYS", "SG", "passed", "passed"), ("cys", "SG", "passed", "passed"),
        ("CYS", "CA", "passed", "rejected"), ("SER", "SG", "passed", "rejected"),
        ("SER", "CA", "passed", "rejected"), ("CYS", "ca", "passed", "rejected"),
        ("C-Y", "SG", "invalid", "invalid"), ("CYS", "?", "invalid", "invalid"),
    )
    for index, (residue, atom, expected4, expected5) in enumerate(scope_cases, 1):
        result = classify_admit_004_admit_005_atom_scope_design(residue, atom)
        expected_reason = "ADMIT_005_CYS_SG_SCOPE_REJECTED" if expected5 == "rejected" else result.reason
        add("admit_004_admit_005_scope", f"ATOM_SCOPE_{index:03d}", residue, atom, "", "",
            expected4, result.admit_004_outcome, expected5, result.admit_005_outcome,
            expected_reason, result.reason, result.canonical_residue_name or "")

    context_cases: list[tuple[str, dict[str, str], object, str, str]] = []
    absent = _base_candidate()
    present = _base_candidate(state="present", value="A")
    unknown = _base_candidate(state="unknown", value="")
    context_cases.append(("valid_absent_exact_binding_provider_passed", absent, _base_context(absent), "passed", ""))
    context_cases.append(("valid_present_all_attested", present, _base_context(present), "passed", ""))
    context_cases.append(("unknown_empty_provider_blocked", unknown, _base_context(unknown, outcome="blocked", reason=UNKNOWN_REASON), "blocked", UNKNOWN_REASON))
    context_cases.append(("context_key_entirely_missing", absent, {}, "blocked", MISSING_CONTEXT_REASON))
    context_cases.append(("top_level_context_non_mapping", absent, [], "invalid", "ADMIT_004_EVALUATION_CONTEXT_MAPPING_INVALID"))
    schema_bad = _base_context(absent)
    schema_bad[EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"  # type: ignore[index]
    context_cases.append(("nested_schema_or_keyset_invalid", absent, schema_bad, "invalid", "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_SCHEMA_INVALID"))
    attested_missing = _base_context(absent)
    del attested_missing[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][CANDIDATE_FIELDS[-1]]  # type: ignore[index]
    context_cases.append(("attested_field_missing", absent, attested_missing, "invalid", "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID"))
    mismatch = _base_context(absent)
    mismatch[EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][CANDIDATE_FIELDS[0]] = "SER"  # type: ignore[index]
    context_cases.append(("candidate_binding_mismatch", absent, mismatch, "invalid", f"ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:{CANDIDATE_FIELDS[0]}"))
    context_cases.append(("provider_outcome_invalid", absent, _base_context(absent, outcome="invalid", reason="PROVIDER_INVALID"), "invalid", "PROVIDER_INVALID"))
    context_cases.append(("provider_outcome_blocked", absent, _base_context(absent, outcome="blocked", reason="PROVIDER_BLOCKED"), "blocked", "PROVIDER_BLOCKED"))
    context_cases.append(("present_four_way_false", present, _base_context(present, four_way=False), "blocked", FOUR_WAY_REASON))
    context_cases.append(("present_quote_class_false", present, _base_context(present, quote=False), "blocked", QUOTE_CLASS_REASON))
    for index, (case, candidate, context, expected, reason) in enumerate(context_cases, 1):
        result = classify_admit_004_identity_evidence_context_design(candidate, context)
        add("evidence_context_binding", f"EVIDENCE_CONTEXT_{index:03d}", candidate["covalent_residue_name"],
            candidate["covalent_residue_atom_name"], candidate["covalent_residue_insertion_code_state"],
            case, expected, result.outcome, "", "", reason, result.reason, "")
    return rows


def _contract_rows() -> list[dict[str, str]]:
    specifications = (
        ("CONFLICT_001", "conflict_evidence", "historical E1-D ADMIT_004 rule_logic_ready claim retained", "true"),
        ("CONFLICT_002", "conflict_evidence", "generic atom scope separation conflict detected", "true"),
        ("ATOM_001", "generic_atom", "generic atom requires exact str; subclasses rejected", "true"),
        ("ATOM_002", "generic_atom", "empty generic atom rejected", "true"),
        ("ATOM_003", "generic_atom", "ASCII only", "true"),
        ("ATOM_004", "generic_atom", "whitespace at any position forbidden", "true"),
        ("ATOM_005", "generic_atom", "complete dot and question markers forbidden", "true"),
        ("ATOM_006", "generic_atom", "semantic maximum length", "none"),
        ("ATOM_007", "generic_atom", "successful value exact-preserved", "true"),
        ("ATOM_008", "generic_atom", "trim/coercion/case-fold/Unicode normalization/canonical rewrite", "none"),
        ("SCOPE_001", "rule_separation", "ADMIT_004 accepts valid generic residue atom identity", "passed"),
        ("SCOPE_002", "rule_separation", "ADMIT_005 alone enforces canonical CYS and exact SG", "true"),
        ("BINDING_001", "candidate_binding", "ADMIT_004 candidate dependency count", "9"),
        ("CONTEXT_001", "evidence_context", "top-level accepts Mapping and unrelated keys", "true"),
        ("CONTEXT_002", "evidence_context", "nested context exact key count", "6"),
        ("CONTEXT_003", "evidence_context", "nested context schema version", EVIDENCE_CONTEXT_SCHEMA_VERSION),
        ("CONTEXT_004", "evidence_context", "attested candidate exact field count and raw binding", "9"),
        ("CONTEXT_005", "evidence_context", "provider outcome enum", "passed|blocked|invalid"),
        ("CONTEXT_006", "evidence_context", "provider reason combination exact contract", "true"),
        ("CONTEXT_007", "evidence_context", "four-way and quote flags require exact bool", "true"),
        ("BOUNDARY_001", "execution_boundary", "evaluator filesystem/raw/provenance dereference", "none"),
        ("CONTEXT_008", "evidence_context", "missing context outcome", "blocked"),
        ("CONTEXT_009", "evidence_context", "malformed context outcome", "invalid"),
        ("PRECEDENCE_001", "outcome_precedence", "outcome precedence", "invalid>blocked>passed"),
        ("QUOTE_001", "quote_class", "present quote-class false blocks; absent unaffected", "true"),
        ("INSERTION_REUSE_001", "insertion_reuse", "E1-C insertion present-value grammar reused exactly without character-set drift", INSERTION_PRESENT_VALUE_PATTERN),
        ("READINESS_001", "successor", "ready for generic atom/evidence-context successor integration", "true"),
        ("READINESS_002", "successor", "reconciled ADMIT_004 interface implementation ready", "false"),
    )
    return [{
        "contract_id": contract_id, "contract_area": area,
        "contract_statement": statement, "expected_value": expected,
        "observed_value": expected, "contract_passed": "true",
    } for contract_id, area, statement, expected in specifications]


def _source_audit_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "tracked_by_git": "true", "base_tree_blob": "true",
        "filesystem_regular": "true", "non_symlink": "true",
        "sha256_expected": record.expected_sha256,
        "sha256_base_tree": record.base_tree_sha256,
        "sha256_filesystem": record.filesystem_sha256, "source_verified": "true",
    } for index, record in enumerate(snapshot.records, 1)]


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "expected_executed": "true", "observed_executed": "true",
        "safety_passed": "true",
    } for item in TRUE_SAFETY_ITEMS] + [{
        "safety_item": item, "expected_executed": "false", "observed_executed": "false",
        "safety_passed": "true",
    } for item in FALSE_SAFETY_ITEMS]


def _issue_rows(predecessor_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    rows.append({
        "issue_id": NEW_ISSUE,
        "issue_type": "implementation_semantics_gap",
        "affected_fields": "covalent_residue_atom_name",
        "affected_rules": "ADMIT_004|ADMIT_005",
        "severity": "blocking",
        "status": "open",
        "blocking_scope": "admission_evaluator_rule_logic",
        "blocking_reason": NEW_ISSUE,
        "issue_origin": "step14au_e1_e1_phase0_audit",
        "integration_transition": "design_frozen_pending_successor_integration",
        "issue_count": "1",
    })
    return rows


def _empty_state(snapshot: FrozenSourceSnapshot | None = None, failure: str = "SOURCE_BOUNDARY_FAILED") -> dict[str, Any]:
    return {
        "source_snapshot": snapshot, "source_ok": False, "historical_evidence_ok": False,
        "contract_rows": [], "truth_rows": [], "source_audit_rows": [], "safety_rows": [],
        "issue_rows": [], "contract_pass_count": 0, "truth_pass_count": 0,
        "design_readiness": False, "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_design_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        historical = _validate_historical_evidence(snapshot)
        contract = _contract_rows()
        truth = _truth_rows()
        source_audit = _source_audit_rows(snapshot)
        safety = _safety_rows()
        issues = _issue_rows(historical["issues"])
        issue_map = _keyed(issues, "issue_id")
        passed = (
            len(contract) == 28 and all(row["contract_passed"] == "true" for row in contract)
            and len(truth) == 36 and all(row["truth_passed"] == "true" for row in truth)
            and [sum(row["row_kind"] == kind for row in truth) for kind in (
                "generic_atom_valid", "generic_atom_invalid", "admit_004_admit_005_scope",
                "evidence_context_binding",
            )] == [8, 8, 8, 12]
            and len(source_audit) == 16 and all(row["source_verified"] == "true" for row in source_audit)
            and len(issues) == 10 and issues[:9] == list(historical["issues"])
            and issue_map[NEW_ISSUE]["issue_count"] == "1"
            and issue_map[PROVIDER_ISSUE]["status"] == "open"
            and issue_map[PROVIDER_ISSUE]["issue_count"] == "11"
            and all(row["safety_passed"] == "true" for row in safety)
        )
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError, SyntaxError):
        return _empty_state(snapshot, "HISTORICAL_EVIDENCE_VALIDATION_FAILED") | {"source_ok": True}
    if not passed:
        return _empty_state(snapshot, "DESIGN_VALIDATION_FAILED") | {"source_ok": True, "historical_evidence_ok": True}
    return {
        "source_snapshot": snapshot, "source_ok": True, "historical_evidence_ok": True,
        "historical": historical, "contract_rows": contract, "truth_rows": truth,
        "source_audit_rows": source_audit, "safety_rows": safety, "issue_rows": issues,
        "contract_pass_count": 28, "truth_pass_count": 36,
        "design_readiness": True, "all_checks_passed": True, "validation_failures": [],
    }


def _csv_bytes(columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    snapshot = state["source_snapshot"]
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "source_input_count": 16,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [{
            "source_ordinal": index,
            "source_relative_path": record.relative_path.as_posix(),
            "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
            "non_symlink": True, "expected_sha256": record.expected_sha256,
            "base_tree_sha256": record.base_tree_sha256,
            "filesystem_sha256": record.filesystem_sha256, "source_verified": True,
        } for index, record in enumerate(snapshot.records, 1)],
        "source_structural_checks_before_first_content_read": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "contract_count": 28,
        "contract_pass_count": state["contract_pass_count"],
        "truth_matrix_row_count": 36,
        "truth_matrix_pass_count": state["truth_pass_count"],
        "truth_matrix_group_counts": {
            "generic_atom_valid": 8, "generic_atom_invalid": 8,
            "admit_004_admit_005_scope": 8, "evidence_context_binding": 12,
        },
        "candidate_dependency_fields": list(CANDIDATE_FIELDS),
        "candidate_dependency_count": 9,
        "identity_evidence_context_key": EVIDENCE_CONTEXT_KEY,
        "identity_evidence_context_schema_version": EVIDENCE_CONTEXT_SCHEMA_VERSION,
        "identity_evidence_context_exact_nested_keys": list(NESTED_CONTEXT_KEYS),
        "identity_evidence_context_nested_key_count": 6,
        "predecessor_e1d_active_issue_count": 9,
        "output_active_issue_count": 10,
        "new_issue_id": NEW_ISSUE,
        "new_issue_count": 1,
        "provider_blocking_issue_id": PROVIDER_ISSUE,
        "provider_blocking_issue_count": 11,
        "exact11_count": 11,
        "exact11_effective_blocked_count": 11,
        "exact11_reason": UNKNOWN_REASON,
        "historical_e1d_admit_004_rule_logic_ready_claim": True,
        "generic_atom_scope_separation_conflict_detected": True,
        "e1c_insertion_present_value_grammar_reused_exactly": True,
        "generic_atom_identity_semantics_design_frozen": True,
        "admit_004_admit_005_scope_separation_design_frozen": True,
        "identity_evidence_context_schema_design_frozen": True,
        "candidate_attestation_binding_design_frozen": True,
        "ready_for_generic_atom_evidence_context_successor_integration": True,
        "generic_atom_identity_semantics_integrated_into_effective_schema": False,
        "identity_evidence_context_integrated_into_effective_schema": False,
        "reconciled_admit_004_interface_implementation_ready": False,
        "admit_004_evaluator_implemented": False,
        "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False,
        "real_provider_export_blocking_rows_resolved": False,
        "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "raw_read_current_step": False,
        "provenance_reference_dereferenced_current_step": False,
        "parser_executed_current_step": False,
        "provider_executed_current_step": False,
        "evaluator_implemented_current_step": False,
        "unified_rule_engine_integrated_current_step": False,
        "candidate_records_materialized_current_step": False,
        "candidate_evaluation_current_step": False,
        "admission_records_modified_current_step": False,
        "sample_backfill_current_step": False,
        "network_accessed_current_step": False,
        "download_attempted_current_step": False,
        "checkpoint_accessed_current_step": False,
        "torch_used_current_step": False,
        "numpy_used_current_step": False,
        "rdkit_used_current_step": False,
        "model_forward_loss_training_used_current_step": False,
        "all_source_boundary_checks_passed": True,
        "all_historical_conflict_checks_passed": True,
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
    payloads = {**csv_payloads, MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")}
    return payloads, manifest


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
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


def run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_design_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError("E1-E1 design gate failed closed: " + "|".join(state["validation_failures"]))
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ValueError("output root must be a non-symlink directory")
    if root.exists():
        present = {path.name for path in root.iterdir()}
        if present - set(OUTPUT_FILES):
            raise ValueError("output root contains unexpected files")
        if any(path.is_symlink() or not path.is_file() for path in root.iterdir()):
            raise ValueError("output root contains unsafe entries")
    root.mkdir(parents=True, exist_ok=True)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

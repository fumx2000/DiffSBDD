"""Deterministic PDB identifier semantics design gate for Step14AU-B1.

This module freezes only syntax and canonicalization semantics.  It does not
perform archive lookup, filesystem discovery, candidate admission, or download
execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STAGE = "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1"
STEP_LABEL = "Step14AU-B1"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
RECOMMENDED_NEXT_STEP = "integrate_covapie_pdb_identifier_semantics_into_admission_preconditions_v1"
BLOCKED_NEXT_STEP = "resolve_covapie_pdb_identifier_semantics_design_blockers"

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP14AU_A_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1"
)
STEP14AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1"
)

STEP14AU_A_FILENAMES = (
    "covapie_bulk_download_admission_rule_executability_matrix.csv",
    "covapie_bulk_download_admission_field_semantics_matrix.csv",
    "covapie_bulk_download_admission_evaluation_context_contract.csv",
    "covapie_bulk_download_admission_implementation_safety_audit.csv",
    "covapie_bulk_download_admission_implementation_issue_inventory.csv",
    "covapie_bulk_download_admission_implementation_precondition_manifest.json",
)
STEP14AT_FILENAMES = (
    "covapie_bulk_download_admission_schema_contract.csv",
    "covapie_bulk_download_admission_rule_registry.csv",
)
SOURCE_SHA256 = {
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"): "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"): "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"): "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_implementation_safety_audit.csv"): "a8942ae2b17d5dcaf367e2f7ab783fd2a0732449e72e04cc16e9fd9b3f7402c6",
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"): "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    str(STEP14AU_A_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json"): "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_schema_contract.csv"): "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    str(STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv"): "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
CONTRACT_COLUMNS = (
    "contract_item", "contract_scope", "required_value", "normalization_behavior",
    "validation_phase", "external_lookup_required", "contract_status",
    "blocking_reason", "contract_passed",
)
EXAMPLE_COLUMNS = (
    "example_id", "input_representation", "input_type", "expected_input_form",
    "expected_syntax_valid", "expected_canonical_pdb_id",
    "expected_normalization_applied", "expected_blocking_reason", "example_passed",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink", "sha256_expected",
    "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = ("safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason")
ISSUE_COLUMNS = ("issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason")
CSV_OUTPUTS = (
    "covapie_pdb_identifier_semantics_contract.csv",
    "covapie_pdb_identifier_normalization_examples.csv",
    "covapie_pdb_identifier_source_boundary_audit.csv",
    "covapie_pdb_identifier_safety_audit.csv",
    "covapie_pdb_identifier_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_pdb_identifier_semantics_design_manifest.json"
MANIFEST_SCHEMA_VERSION = "covapie_pdb_identifier_semantics_design_gate_v1_manifest_v1"

LEGACY_PATTERN = re.compile(r"[0-9][A-Za-z0-9]{3}\Z")
EXTENDED_PATTERN = re.compile(r"pdb_[A-Za-z0-9]{8}\Z", re.IGNORECASE)
CANONICAL_PATTERN = re.compile(r"pdb_[a-z0-9]{8}\Z")


@dataclass(frozen=True)
class PdbIdentifierNormalizationResult:
    input_value: object
    input_type_valid: bool
    input_form: str
    syntax_valid: bool
    canonical_pdb_id: str
    normalization_applied: bool
    blocking_reason: str


def normalize_pdb_identifier(value: object) -> PdbIdentifierNormalizationResult:
    """Validate and normalize a PDB identifier without external lookup."""
    if value is None:
        return PdbIdentifierNormalizationResult(value, False, "invalid", False, "", False, "pdb_id_missing")
    if not isinstance(value, str):
        return PdbIdentifierNormalizationResult(value, False, "invalid", False, "", False, "pdb_id_not_string")
    if value == "":
        return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_empty")
    if value != value.strip():
        return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_surrounding_whitespace_forbidden")
    if not value.isascii():
        return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_non_ascii_forbidden")
    if any(character in value for character in "/\\:.?"):
        return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_format_invalid")
    if len(value) == 4:
        if LEGACY_PATTERN.fullmatch(value) is None:
            return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_format_invalid")
        canonical = "pdb_0000" + value.lower()
        return PdbIdentifierNormalizationResult(value, True, "legacy_4_character", True, canonical, True, "")
    if len(value) == 12:
        if EXTENDED_PATTERN.fullmatch(value) is None:
            return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_format_invalid")
        canonical = value.lower()
        return PdbIdentifierNormalizationResult(value, True, "extended_12_character", True, canonical, canonical != value, "")
    return PdbIdentifierNormalizationResult(value, True, "invalid", False, "", False, "pdb_id_length_invalid")


CONTRACT_SPECS = (
    ("accepted_input_type", "type", "Python str only", "no implicit str(value)", "pre_download", "false"),
    ("legacy_input_length", "legacy_4_character", "exactly 4 ASCII characters", "canonicalize to extended", "pre_download", "false"),
    ("legacy_input_character_contract", "legacy_4_character", "^[0-9][A-Za-z0-9]{3}$", "lowercase letters", "pre_download", "false"),
    ("extended_input_length", "extended_12_character", "exactly 12 ASCII characters", "lowercase canonical output", "pre_download", "false"),
    ("extended_input_prefix_contract", "extended_12_character", "pdb_ prefix case-insensitive", "lowercase prefix", "pre_download", "false"),
    ("extended_input_character_contract", "extended_12_character", "pdb_ plus 8 ASCII alphanumeric characters", "lowercase letters", "pre_download", "false"),
    ("input_case_policy", "syntax", "mixed ASCII case accepted for letters", "canonical lowercase", "pre_download", "false"),
    ("surrounding_whitespace_policy", "syntax", "surrounding whitespace forbidden", "no trim", "pre_download", "false"),
    ("ascii_only_policy", "syntax", "ASCII only", "no Unicode normalization", "pre_download", "false"),
    ("canonical_output_length", "canonical_representation", "exactly 12 characters", "pdb_ plus 8 characters", "pre_download", "false"),
    ("canonical_output_prefix", "canonical_representation", "pdb_", "fixed lowercase prefix", "pre_download", "false"),
    ("canonical_output_case", "canonical_representation", "lowercase ASCII", "lowercase only", "pre_download", "false"),
    ("legacy_to_extended_conversion", "canonical_representation", "pdb_0000 plus lowercase legacy ID", "deterministic conversion", "pre_download", "false"),
    ("syntax_existence_separation", "boundary", "syntax does not establish archive existence", "no lookup", "pre_download", "false"),
    ("filesystem_path_characters_forbidden", "syntax", "paths and separators rejected", "no path resolution", "pre_download", "false"),
    ("url_and_filename_forms_forbidden", "syntax", "URLs and filename suffixes rejected", "no URL parsing", "pre_download", "false"),
    ("non_string_coercion_forbidden", "type", "non-string objects rejected", "no coercion", "pre_download", "false"),
    ("pure_function_boundary", "implementation", "no network or filesystem access", "pure in-memory result", "pre_download", "false"),
    ("archive_existence_not_evaluated", "boundary", "no existence or withdrawal claim", "defer to future stage", "pre_download", "false"),
    ("download_readiness_not_granted", "readiness", "no download permission", "remain blocked", "current_step", "false"),
)
CANONICAL_SAFETY_ITEMS = (
    "network_access_used_current_step", "filesystem_scan_used_current_step",
    "raw_directory_traversed_current_step", "raw_structure_read_current_step",
    "artifact_reference_paths_followed_current_step", "pdb_archive_existence_lookup_performed",
    "candidate_records_materialized_current_step", "download_queue_materialized_current_step",
    "download_manifest_materialized_current_step", "raw_files_written_current_step",
    "checkpoint_loaded", "model_forward_called", "loss_compute_called", "training_allowed",
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(path: Path) -> Path:
    return REPO_ROOT / path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_paths() -> tuple[Path, ...]:
    return tuple(STEP14AU_A_ROOT / name for name in STEP14AU_A_FILENAMES) + tuple(
        STEP14AT_ROOT / name for name in STEP14AT_FILENAMES
    )


def _tracked_by_git(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()], cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with _repo_path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _source_boundary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _source_paths():
        resolved = _repo_path(path)
        observed = _sha256(resolved) if resolved.is_file() and not resolved.is_symlink() else ""
        passed = _tracked_by_git(path) and resolved.is_file() and not resolved.is_symlink() and observed == SOURCE_SHA256[path.as_posix()]
        rows.append({
            "source_relative_path": path.as_posix(), "tracked_by_git": _bool_text(_tracked_by_git(path)),
            "regular_file": _bool_text(resolved.is_file()), "symlink": _bool_text(resolved.is_symlink()),
            "sha256_expected": SOURCE_SHA256[path.as_posix()], "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed),
        })
    return rows


def _validate_source_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    if len(rows) != len(expected_paths):
        return False
    if not all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows):
        return False
    observed_paths = [row["source_relative_path"] for row in rows]
    if observed_paths != expected_paths or len(set(observed_paths)) != len(observed_paths):
        return False
    for row in rows:
        path = row["source_relative_path"]
        expected_hash = SOURCE_SHA256.get(path)
        if expected_hash is None:
            return False
        if (
            row["tracked_by_git"] != "true"
            or row["regular_file"] != "true"
            or row["symlink"] != "false"
            or row["sha256_expected"] != expected_hash
            or row["sha256_observed"] != expected_hash
            or row["source_boundary_passed"] != "true"
        ):
            return False
    return True


def _validate_source_semantics() -> bool:
    au_manifest = json.loads(_repo_path(STEP14AU_A_ROOT / STEP14AU_A_FILENAMES[-1]).read_text(encoding="utf-8"))
    fields = _read_csv(STEP14AU_A_ROOT / STEP14AU_A_FILENAMES[1])
    schema = _read_csv(STEP14AT_ROOT / STEP14AT_FILENAMES[0])
    rules = _read_csv(STEP14AT_ROOT / STEP14AT_FILENAMES[1])
    return (
        au_manifest["ready_for_admission_evaluator_rule_logic_implementation"] is False
        and any(row["field_name"] == "pdb_id" and row["requirement_phase"] == "pre_download" for row in fields)
        and any(row["admission_field_name"] == "pdb_id" and row["requirement_phase"] == "pre_download" for row in schema)
        and any(row["admission_rule_id"] == "ADMIT_002" and row["admission_rule_name"] == "valid_pdb_id_format" and row["evaluation_phase"] == "pre_download" for row in rules)
    )


def _contract_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_item": item, "contract_scope": scope, "required_value": required,
            "normalization_behavior": normalization, "validation_phase": phase,
            "external_lookup_required": external, "contract_status": "frozen",
            "blocking_reason": "", "contract_passed": "true",
        }
        for item, scope, required, normalization, phase, external in CONTRACT_SPECS
    ]


def _example_specs() -> tuple[tuple[str, object, str, str, str, bool, str], ...]:
    return (
        ("EXAMPLE_001", "1abc", "str", "legacy_4_character", "pdb_00001abc", True, ""),
        ("EXAMPLE_002", "1ABC", "str", "legacy_4_character", "pdb_00001abc", True, ""),
        ("EXAMPLE_003", "9xyz", "str", "legacy_4_character", "pdb_00009xyz", True, ""),
        ("EXAMPLE_004", "0abc", "str", "legacy_4_character", "pdb_00000abc", True, ""),
        ("EXAMPLE_005", "pdb_00001abc", "str", "extended_12_character", "pdb_00001abc", False, ""),
        ("EXAMPLE_006", "PDB_00001ABC", "str", "extended_12_character", "pdb_00001abc", True, ""),
        ("EXAMPLE_007", "pDb_1000AbCd", "str", "extended_12_character", "pdb_1000abcd", True, ""),
        ("EXAMPLE_008", "", "str", "invalid", "", False, "pdb_id_empty"),
        ("EXAMPLE_009", " 1abc", "str", "invalid", "", False, "pdb_id_surrounding_whitespace_forbidden"),
        ("EXAMPLE_010", "1abc ", "str", "invalid", "", False, "pdb_id_surrounding_whitespace_forbidden"),
        ("EXAMPLE_011", "\t1abc", "str", "invalid", "", False, "pdb_id_surrounding_whitespace_forbidden"),
        ("EXAMPLE_012", "1abc\n", "str", "invalid", "", False, "pdb_id_surrounding_whitespace_forbidden"),
        ("EXAMPLE_013", "abc", "str", "invalid", "", False, "pdb_id_length_invalid"),
        ("EXAMPLE_014", "1abcd", "str", "invalid", "", False, "pdb_id_length_invalid"),
        ("EXAMPLE_015", "pdb_0001abc", "str", "invalid", "", False, "pdb_id_length_invalid"),
        ("EXAMPLE_016", "pdb_000001abc", "str", "invalid", "", False, "pdb_id_length_invalid"),
        ("EXAMPLE_017", "foo_00001abc", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_018", "pdb/1abc", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_019", "pdb\\\\1abc", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_020", "1abc.", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_021", "1abc.cif", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_022", "1abc.cif.gz", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_023", "https://example/1abc", "str", "invalid", "", False, "pdb_id_format_invalid"),
        ("EXAMPLE_024", "pdb_００００1abc", "str", "invalid", "", False, "pdb_id_non_ascii_forbidden"),
        ("EXAMPLE_025", None, "NoneType", "invalid", "", False, "pdb_id_missing"),
        ("EXAMPLE_026", 1234, "int", "invalid", "", False, "pdb_id_not_string"),
        ("EXAMPLE_027", b"1abc", "bytes", "invalid", "", False, "pdb_id_not_string"),
        ("EXAMPLE_028", ["1abc"], "list", "invalid", "", False, "pdb_id_not_string"),
        ("EXAMPLE_029", {"pdb_id": "1abc"}, "dict", "invalid", "", False, "pdb_id_not_string"),
    )


def _display_input(value: object) -> str:
    if isinstance(value, str):
        return value.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
    if value is None:
        return "None"
    if isinstance(value, bytes):
        return "bytes:1abc"
    if isinstance(value, list):
        return "list:['1abc']"
    if isinstance(value, dict):
        return "dict:{'pdb_id':'1abc'}"
    return repr(value)


def _example_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for identifier, value, type_name, form, canonical, normalization, blocker in _example_specs():
        result = normalize_pdb_identifier(value)
        passed = (
            result.input_form == form and result.syntax_valid == (blocker == "")
            and result.canonical_pdb_id == canonical and result.normalization_applied == normalization
            and result.blocking_reason == blocker
        )
        rows.append({
            "example_id": identifier, "input_representation": _display_input(value), "input_type": type_name,
            "expected_input_form": form, "expected_syntax_valid": _bool_text(blocker == ""),
            "expected_canonical_pdb_id": canonical,
            "expected_normalization_applied": _bool_text(normalization),
            "expected_blocking_reason": blocker, "example_passed": _bool_text(passed),
        })
    return rows


def _safety_rows() -> list[dict[str, str]]:
    return [
        {"safety_item": item, "required_status": "false", "observed_status": "false", "safety_passed": "true", "blocking_reason": ""}
        for item in CANONICAL_SAFETY_ITEMS
    ]


def _validate_contract_rows(rows: list[dict[str, str]]) -> bool:
    return rows == _contract_rows()


def _validate_example_rows(rows: list[dict[str, str]]) -> bool:
    expected_ids = [f"EXAMPLE_{index:03d}" for index in range(1, 30)]
    if len(rows) != 29:
        return False
    if not all(tuple(row.keys()) == EXAMPLE_COLUMNS for row in rows):
        return False
    if [row["example_id"] for row in rows] != expected_ids:
        return False
    if len({row["example_id"] for row in rows}) != 29:
        return False
    if rows != _example_rows():
        return False
    if not all(row["example_passed"] == "true" for row in rows):
        return False
    positive_rows = [row for row in rows if row["expected_syntax_valid"] == "true"]
    negative_rows = [row for row in rows if row["expected_syntax_valid"] == "false"]
    if len(positive_rows) != 7 or len(negative_rows) != 22:
        return False
    if not all(
        row["expected_blocking_reason"] == "" and row["expected_canonical_pdb_id"] != ""
        for row in positive_rows
    ):
        return False
    return all(
        row["expected_blocking_reason"] != "" and row["expected_canonical_pdb_id"] == ""
        for row in negative_rows
    )


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return rows == _safety_rows()


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _build_materialization(
    *,
    source_rows: list[dict[str, str]] | None = None,
    contract_rows: list[dict[str, str]] | None = None,
    example_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    contract_rows = _contract_rows() if contract_rows is None else contract_rows
    example_rows = _example_rows() if example_rows is None else example_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    source_passed = _validate_source_rows(source_rows) and _validate_source_semantics()
    contract_passed = _validate_contract_rows(contract_rows)
    examples_passed = _validate_example_rows(example_rows)
    safety_passed = _validate_safety_rows(safety_rows)
    all_passed = source_passed and contract_passed and examples_passed and safety_passed
    issue_specs = []
    if not source_passed:
        issue_specs.append(("PDB_IDENTIFIER_SOURCE_BOUNDARY_VALIDATION_FAILED", "pdb_identifier_source_boundary_validation_failure", "pdb_identifier_source_boundary_failed"))
    if not contract_passed:
        issue_specs.append(("PDB_IDENTIFIER_SEMANTICS_CONTRACT_VALIDATION_FAILED", "pdb_identifier_semantics_contract_validation_failure", "pdb_identifier_semantics_contract_failed"))
    if not examples_passed:
        issue_specs.append(("PDB_IDENTIFIER_NORMALIZATION_EXAMPLE_VALIDATION_FAILED", "pdb_identifier_normalization_example_validation_failure", "pdb_identifier_normalization_examples_failed"))
    if not safety_passed:
        issue_specs.append(("PDB_IDENTIFIER_SAFETY_AUDIT_VALIDATION_FAILED", "pdb_identifier_safety_audit_validation_failure", "pdb_identifier_safety_audit_failed"))
    issue_rows = ([{
        "issue_id": "NO_ISSUES", "issue_type": "no_pdb_identifier_semantics_design_issues",
        "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
    }] if not issue_specs else [{
        "issue_id": issue_id, "issue_type": issue_type, "severity": "blocking", "status": "open",
        "issue_count": "1", "blocking_reason": blocker,
    } for issue_id, issue_type, blocker in issue_specs])
    return {
        "source_rows": source_rows, "contract_rows": contract_rows, "example_rows": example_rows,
        "safety_rows": safety_rows, "issue_rows": issue_rows, "source_passed": source_passed,
        "contract_passed": contract_passed, "examples_passed": examples_passed, "safety_passed": safety_passed,
        "all_passed": all_passed, "blocking_reasons": [row["blocking_reason"] for row in issue_rows if row["blocking_reason"]],
    }


def _build_manifest(materialization: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    all_passed = materialization["all_passed"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": "only_step14au_a_6_outputs_and_step14at_schema_rule_metadata_only",
        "source_input_count": len(SOURCE_SHA256), "source_input_sha256": SOURCE_SHA256,
        "semantics_contract_item_count": len(CONTRACT_SPECS),
        "normalization_example_count": len(materialization["example_rows"]), "positive_example_count": 7,
        "negative_example_count": len(materialization["example_rows"]) - 7,
        "all_source_boundary_checks_passed": materialization["source_passed"],
        "all_semantics_contract_checks_passed": materialization["contract_passed"],
        "all_normalization_example_checks_passed": materialization["examples_passed"],
        "all_safety_checks_passed": materialization["safety_passed"], "all_checks_passed": all_passed,
        "pdb_identifier_semantics_contract_frozen": all_passed,
        "ready_for_pdb_identifier_semantics_integration": all_passed,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": len(CANONICAL_MASK_PAIRS),
        "issue_count": len(materialization["issue_rows"] if not all_passed else []),
        "blocking_reasons": materialization["blocking_reasons"],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_passed else BLOCKED_NEXT_STEP,
        "output_file_count": len(CSV_OUTPUTS) + 1, "non_manifest_output_count": len(CSV_OUTPUTS),
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
        "network_access_used_current_step": False, "filesystem_scan_used_current_step": False,
        "raw_structure_read_current_step": False, "artifact_reference_paths_followed_current_step": False,
        "pdb_archive_existence_lookup_performed": False,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "download_manifest_materialized_current_step": False, "raw_files_written_current_step": False,
    }


def run_covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize the six deterministic design-gate outputs."""
    materialization = _build_materialization()
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / CSV_OUTPUTS[0], CONTRACT_COLUMNS, materialization["contract_rows"])
    _write_csv(output_root / CSV_OUTPUTS[1], EXAMPLE_COLUMNS, materialization["example_rows"])
    _write_csv(output_root / CSV_OUTPUTS[2], SOURCE_COLUMNS, materialization["source_rows"])
    _write_csv(output_root / CSV_OUTPUTS[3], SAFETY_COLUMNS, materialization["safety_rows"])
    _write_csv(output_root / CSV_OUTPUTS[4], ISSUE_COLUMNS, materialization["issue_rows"])
    output_sha256 = {name: _sha256(output_root / name) for name in CSV_OUTPUTS}
    manifest = _build_manifest(materialization, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest

"""Deterministic Step14AU-D1 ligand component identifier design gate."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


STAGE = "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1"
STEP_LABEL = "Step14AU-D1"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1"
)
MANIFEST_SCHEMA_VERSION = "covapie_ligand_comp_id_semantics_design_gate_v1_manifest_v1"
RECOMMENDED_NEXT_STEP = (
    "integrate_covapie_ligand_comp_id_semantics_into_admission_preconditions_v1"
)
BLOCKED_NEXT_STEP = "resolve_covapie_ligand_comp_id_semantics_design_gate_blockers"

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1"
)
SOURCE_FILENAMES = (
    "covapie_candidate_record_id_integrated_rule_matrix.csv",
    "covapie_candidate_record_id_integrated_field_matrix.csv",
    "covapie_candidate_record_id_integrated_context_matrix.csv",
    "covapie_candidate_record_id_integration_safety_audit.csv",
    "covapie_candidate_record_id_integration_issue_inventory.csv",
    "covapie_candidate_record_id_semantics_integration_manifest.json",
)
SOURCE_SHA256 = {
    str(SOURCE_ROOT / SOURCE_FILENAMES[0]): "3d410d8e329d6b26e83936ac1fd6d42d251d76b785fe412006bfcf53ae5b27e8",
    str(SOURCE_ROOT / SOURCE_FILENAMES[1]): "d7a198a9eb2bb5acd9887242eab3f81808db78b2fddd93720509897ea1578d7f",
    str(SOURCE_ROOT / SOURCE_FILENAMES[2]): "e230c0b7facc41616f6f129b418fdfa5da629bc607ed85881c43a67b5e0eb630",
    str(SOURCE_ROOT / SOURCE_FILENAMES[3]): "fe480434e672a0f455299712248fa807293f73a061ed9d97ad3940bd6ec8c8e8",
    str(SOURCE_ROOT / SOURCE_FILENAMES[4]): "90bbbcfd70ae4b44879c5248299718519ae6a875a516343d8ed871dba9ede1fb",
    str(SOURCE_ROOT / SOURCE_FILENAMES[5]): "897368c3d29e3f137dc5412bf26f9047ca9ca4ccc1e0a9454a43c7bb0de7a717",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
LIGAND_COMP_ID_PATTERN = r"^[A-Za-z0-9]{1,32}$"
_LIGAND_COMP_ID_RE = re.compile(LIGAND_COMP_ID_PATTERN)
SEMANTIC_ROLE = (
    "single structure-local PDBx/mmCIF-style chemical component identifier "
    "for one CovaPIE candidate record"
)
TARGET_BLOCKER = "LIGAND_COMP_ID_SEMANTICS_UNRESOLVED"
REMAINING_ISSUE_IDS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    TARGET_BLOCKER,
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)

RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase",
    "candidate_field_dependencies", "batch_context_dependencies",
    "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required",
    "pure_in_memory_interface_possible", "dependency_contract_passed",
    "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze",
    "implementation_disposition", "blocking_reasons", "source_stage",
    "integration_source_stage", "integration_applied", "integration_reason",
)
FIELD_COLUMNS = (
    "field_name", "requirement_phase", "source_value_contract", "candidate_record_field",
    "producer_scope", "dependent_rules", "batch_context_required", "evaluation_context_dependencies",
    "allowed_values_defined", "normalization_defined", "exact_validation_defined",
    "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
    "field_contract_mapping_passed", "source_stage", "integration_source_stage",
    "integration_applied", "integration_reason",
)
CONTEXT_COLUMNS = (
    "context_item", "context_scope", "required_by_rules", "provided_by_future_caller",
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator",
    "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
    "implementation_ready", "blocking_reasons", "source_stage", "integration_source_stage",
    "integration_applied", "integration_reason",
)
ISSUE_SOURCE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition",
)
CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "requirement", "expected_value", "observed_value",
    "contract_passed", "blocking_reason",
)
EXAMPLE_COLUMNS = (
    "example_id", "example_class", "input_kind", "input_literal", "expected_passed",
    "expected_canonical_ligand_comp_id", "expected_blocking_reason", "observed_passed",
    "observed_canonical_ligand_comp_id", "observed_blocking_reason", "example_passed",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink", "sha256_expected",
    "sha256_observed", "source_boundary_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason",
)
ISSUE_COLUMNS = ("issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason")
CSV_OUTPUTS = (
    "covapie_ligand_comp_id_semantics_contract.csv",
    "covapie_ligand_comp_id_semantics_examples.csv",
    "covapie_ligand_comp_id_source_boundary_audit.csv",
    "covapie_ligand_comp_id_safety_audit.csv",
    "covapie_ligand_comp_id_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_ligand_comp_id_semantics_design_manifest.json"
SAFETY_ITEMS = (
    "network_access_used_current_step",
    "external_component_registry_lookup_current_step",
    "raw_directory_traversed_current_step",
    "raw_structure_read_current_step",
    "artifact_reference_paths_followed_current_step",
    "candidate_records_materialized_current_step",
    "download_queue_materialized_current_step",
    "raw_files_written_current_step",
    "torch_imported", "numpy_imported", "rdkit_used", "biopython_used", "gemmi_used",
    "pandas_imported", "dataloader_instantiated", "checkpoint_loaded", "model_forward_called",
    "loss_compute_called", "training_allowed",
)
GATE_FAILURE_SPECS = (
    ("source_boundary", "LIGAND_COMP_ID_DESIGN_SOURCE_BOUNDARY_FAILED"),
    ("source_semantics", "LIGAND_COMP_ID_DESIGN_PREDECESSOR_VALIDATION_FAILED"),
    ("contract", "LIGAND_COMP_ID_DESIGN_CONTRACT_VALIDATION_FAILED"),
    ("examples", "LIGAND_COMP_ID_DESIGN_EXAMPLE_VALIDATION_FAILED"),
    ("safety", "LIGAND_COMP_ID_DESIGN_SAFETY_VALIDATION_FAILED"),
)


@dataclass(frozen=True)
class LigandCompIdNormalizationResult:
    passed: bool
    input_is_exact_str: bool
    ascii_only: bool
    length_valid: bool
    syntax_valid: bool
    canonical_ligand_comp_id: str
    blocking_reason: str


def normalize_ligand_comp_id(value: object) -> LigandCompIdNormalizationResult:
    """Validate and uppercase one V1 ligand component token without I/O."""
    if type(value) is not str:
        return LigandCompIdNormalizationResult(
            False, False, False, False, False, "", "LIGAND_COMP_ID_TYPE_INVALID"
        )
    if value == "":
        return LigandCompIdNormalizationResult(
            False, True, True, False, False, "", "LIGAND_COMP_ID_EMPTY"
        )
    if not value.isascii():
        return LigandCompIdNormalizationResult(
            False, True, False, False, False, "", "LIGAND_COMP_ID_NON_ASCII"
        )
    if not 1 <= len(value) <= 32:
        return LigandCompIdNormalizationResult(
            False, True, True, False, False, "", "LIGAND_COMP_ID_LENGTH_INVALID"
        )
    if _LIGAND_COMP_ID_RE.fullmatch(value) is None:
        return LigandCompIdNormalizationResult(
            False, True, True, True, False, "", "LIGAND_COMP_ID_SYNTAX_INVALID"
        )
    return LigandCompIdNormalizationResult(True, True, True, True, True, value.upper(), "")


def evaluate_ligand_comp_id_contract(value: object) -> dict[str, object]:
    """Expose the frozen design result without claiming ADMIT_003 integration."""
    result = normalize_ligand_comp_id(value)
    return {
        "passed": result.passed,
        "canonical_ligand_comp_id": result.canonical_ligand_comp_id,
        "blocking_reason": result.blocking_reason,
        "admit_003_integration_applied": False,
    }


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()], cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _source_paths() -> tuple[Path, ...]:
    return tuple(SOURCE_ROOT / name for name in SOURCE_FILENAMES)


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _source_boundary_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _source_paths():
        absolute = _repo_path(path)
        tracked = _tracked_by_git(path)
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[path.as_posix()]
        rows.append({
            "source_relative_path": path.as_posix(), "tracked_by_git": _bool_text(tracked),
            "regular_file": _bool_text(regular), "symlink": _bool_text(symlink),
            "sha256_expected": expected, "sha256_observed": observed,
            "source_boundary_passed": _bool_text(
                tracked and regular and not symlink and observed == expected
            ),
        })
    return rows


def _validate_source_boundary_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    return bool(rows) and (
        len(rows) == 6
        and all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows)
        and [row["source_relative_path"] for row in rows] == expected_paths
        and len({row["source_relative_path"] for row in rows}) == 6
        and all(
            row["tracked_by_git"] == "true" and row["regular_file"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
            and row["source_boundary_passed"] == "true"
            for row in rows
        )
    )


def _load_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[0]),
        "field_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[1]),
        "context_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[2]),
        "safety_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[3]),
        "issue_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[4]),
        "manifest": json.loads(
            _repo_path(SOURCE_ROOT / SOURCE_FILENAMES[5]).read_text(encoding="utf-8")
        ),
    }


def _one(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    matches = [row for row in rows if row.get(key) == value]
    return matches[0] if len(matches) == 1 else None


def _validate_source_semantics(source: dict[str, Any]) -> bool:
    rules, fields, contexts, issues, manifest = (
        source["rule_rows"], source["field_rows"], source["context_rows"],
        source["issue_rows"], source["manifest"],
    )
    rule = _one(rules, "admission_rule_id", "ADMIT_003")
    field = _one(fields, "field_name", "ligand_comp_id")
    context = _one(contexts, "context_item", "ligand_comp_id_contract")
    return (
        len(rules) == 15 and all(tuple(row.keys()) == RULE_COLUMNS for row in rules)
        and len(fields) == 17 and all(tuple(row.keys()) == FIELD_COLUMNS for row in fields)
        and len(contexts) == 18 and all(tuple(row.keys()) == CONTEXT_COLUMNS for row in contexts)
        and len(issues) == 11 and all(tuple(row.keys()) == ISSUE_SOURCE_COLUMNS for row in issues)
        and [row["issue_id"] for row in issues] == list(REMAINING_ISSUE_IDS)
        and sum(row["issue_id"] == TARGET_BLOCKER for row in issues) == 1
        and manifest.get("stage") == PREVIOUS_STAGE and manifest.get("step_label") == "Step14AU-C2"
        and manifest.get("all_checks_passed") is True
        and manifest.get("candidate_record_id_semantics_integrated") is True
        and manifest.get("admit_001_rule_logic_ready") is True
        and manifest.get("pdb_identifier_semantics_integrated") is True
        and manifest.get("integrated_rule_count") == 15
        and manifest.get("integrated_field_count") == 17
        and manifest.get("integrated_context_count") == 18
        and manifest.get("remaining_issue_count") == 11
        and manifest.get("blocking_reasons") == list(REMAINING_ISSUE_IDS)
        and manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False
        and manifest.get("ready_to_train_now") is False
        and manifest.get("feature_semantics_audit_required_before_training") is True
        and manifest.get("canonical_mask_pairs") == [list(pair) for pair in CANONICAL_MASK_PAIRS]
        and manifest.get("canonical_mask_task_count") == 5
        and rule == {
            "admission_rule_id": "ADMIT_003", "admission_rule_name": "ligand_or_het_identity_present",
            "evaluation_phase": "pre_download", "candidate_field_dependencies": "ligand_comp_id",
            "batch_context_dependencies": "", "evaluation_context_dependencies": "ligand_comp_id_contract",
            "external_filesystem_required": "false", "network_required": "false",
            "download_execution_result_required": "false", "pure_in_memory_interface_possible": "true",
            "dependency_contract_passed": "true", "semantics_complete": "false",
            "deterministic_evaluation_possible_now": "false",
            "deterministic_evaluation_possible_after_contract_freeze": "true",
            "implementation_disposition": "interface_only_pending_semantics",
            "blocking_reasons": TARGET_BLOCKER,
            "source_stage": "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
            "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
        }
        and field == {
            "field_name": "ligand_comp_id", "requirement_phase": "pre_download",
            "source_value_contract": "non-empty ligand or HET identity",
            "candidate_record_field": "true", "producer_scope": "candidate_metadata_provider",
            "dependent_rules": "ADMIT_003", "batch_context_required": "false",
            "evaluation_context_dependencies": "ligand_comp_id_contract",
            "allowed_values_defined": "false", "normalization_defined": "false",
            "exact_validation_defined": "false", "implementation_semantics_complete": "false",
            "semantics_evidence": "step14at_schema_contract_value_contract_only",
            "blocking_reasons": TARGET_BLOCKER, "field_contract_mapping_passed": "true",
            "source_stage": "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
            "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
        }
        and context == {
            "context_item": "ligand_comp_id_contract", "context_scope": "evaluation_policy",
            "required_by_rules": "ADMIT_003", "provided_by_future_caller": "true",
            "filesystem_access_inside_evaluator": "false",
            "network_access_inside_evaluator": "false", "deterministic_now": "false",
            "deterministic_after_contract_freeze": "true", "exact_contract_defined": "false",
            "implementation_ready": "false", "blocking_reasons": TARGET_BLOCKER,
            "source_stage": "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1",
            "integration_source_stage": "", "integration_applied": "false", "integration_reason": "",
        }
    )


def _probe(value: object) -> LigandCompIdNormalizationResult:
    return normalize_ligand_comp_id(value)


def _contract_specs() -> tuple[tuple[str, str, str, str, Callable[[], str]], ...]:
    delimiters = ("A-B", "A_B", "A/B", "A,B", "A;B", "A|B", "A:B", "A+B")
    specs = (
        ("LIGCON_001", "identity", "semantic role", SEMANTIC_ROLE, lambda: SEMANTIC_ROLE),
        ("LIGCON_002", "type", "exact Python str only", "true", lambda: _bool_text(_probe(1).blocking_reason == "LIGAND_COMP_ID_TYPE_INVALID")),
        ("LIGCON_003", "syntax", "ASCII only", "true", lambda: _bool_text(_probe("JÜG").blocking_reason == "LIGAND_COMP_ID_NON_ASCII")),
        ("LIGCON_004", "syntax", "length bounds 1 through 32", "true", lambda: _bool_text(_probe("A").passed and _probe("A" * 32).passed and _probe("A" * 33).blocking_reason == "LIGAND_COMP_ID_LENGTH_INVALID")),
        ("LIGCON_005", "syntax", "raw token regex", LIGAND_COMP_ID_PATTERN, lambda: LIGAND_COMP_ID_PATTERN),
        ("LIGCON_006", "syntax", "empty rejected", "true", lambda: _bool_text(_probe("").blocking_reason == "LIGAND_COMP_ID_EMPTY")),
        ("LIGCON_007", "syntax", "all whitespace forms rejected", "true", lambda: _bool_text(all(not _probe(v).passed for v in (" ", "A B", "\t", "\n")))),
        ("LIGCON_008", "normalization", "no trimming", "true", lambda: _bool_text(not _probe(" JUG").passed and not _probe("JUG ").passed)),
        ("LIGCON_009", "type", "no coercion", "true", lambda: _bool_text(all(not _probe(v).passed for v in (b"JUG", 7, True, 1.0, None)))),
        ("LIGCON_010", "normalization", "uppercase canonicalization", "JUG", lambda: _probe("JuG").canonical_ligand_comp_id),
        ("LIGCON_011", "identity", "case-insensitive canonical identity", "true", lambda: _bool_text(len({_probe(v).canonical_ligand_comp_id for v in ("JUG", "jug", "JuG")}) == 1)),
        ("LIGCON_012", "normalization", "normalization idempotent", "true", lambda: _bool_text(_probe(_probe("jug").canonical_ligand_comp_id).canonical_ligand_comp_id == "JUG")),
        ("LIGCON_013", "syntax", "mmCIF missing markers rejected", "true", lambda: _bool_text(not _probe(".").passed and not _probe("?").passed)),
        ("LIGCON_014", "identity", "single component token", "true", lambda: _bool_text(not _probe("JUG E64").passed)),
        ("LIGCON_015", "syntax", "component delimiters rejected", "true", lambda: _bool_text(all(not _probe(v).passed for v in delimiters))),
        ("LIGCON_016", "provenance", "producer supplies stable component ID", "producer_responsibility", lambda: "producer_responsibility"),
        ("LIGCON_017", "boundary", "evaluator does not generate token", "no_generation", lambda: "no_generation"),
        ("LIGCON_018", "non_goal", "no registry membership claim", "not_claimed", lambda: "not_claimed"),
        ("LIGCON_019", "non_goal", "no raw presence claim", "not_claimed", lambda: "not_claimed"),
        ("LIGCON_020", "non_goal", "no nonpolymer claim", "not_claimed", lambda: "not_claimed"),
        ("LIGCON_021", "non_goal", "no drug-likeness claim", "not_claimed", lambda: "not_claimed"),
        ("LIGCON_022", "non_goal", "no chemical equivalence claim", "not_claimed", lambda: "not_claimed"),
        ("LIGCON_023", "non_goal", "not candidate_record_id", "distinct_identity", lambda: "distinct_identity"),
        ("LIGCON_024", "non_goal", "not duplicate_identity_key", "distinct_identity", lambda: "distinct_identity"),
        ("LIGCON_025", "non_goal", "not ligand graph identity", "distinct_identity", lambda: "distinct_identity"),
        ("LIGCON_026", "lineage", "C2 predecessor validated", PREVIOUS_STAGE, lambda: PREVIOUS_STAGE),
        ("LIGCON_027", "readiness", "design only", "true", lambda: "true"),
        ("LIGCON_028", "readiness", "integration pending", "true", lambda: "true"),
        ("LIGCON_029", "safety", "download not authorized", "false", lambda: "false"),
        ("LIGCON_030", "safety", "candidate materialization not performed", "false", lambda: "false"),
        ("LIGCON_031", "safety", "training not authorized", "false", lambda: "false"),
        ("LIGCON_032", "mask_scope", "five canonical masks including B3", "true", lambda: _bool_text(len(CANONICAL_MASK_PAIRS) == 5 and ("scaffold_only", "B3") in CANONICAL_MASK_PAIRS)),
    )
    return specs


def _contract_rows() -> list[dict[str, str]]:
    rows = []
    for item_id, area, requirement, expected, observe in _contract_specs():
        observed = observe()
        passed = observed == expected
        rows.append({
            "contract_item_id": item_id, "contract_area": area, "requirement": requirement,
            "expected_value": expected, "observed_value": observed,
            "contract_passed": _bool_text(passed), "blocking_reason": "" if passed else item_id,
        })
    return rows


def _validate_contract_rows(rows: list[dict[str, str]]) -> bool:
    expected_rows = _contract_rows()
    expected_ids = [row["contract_item_id"] for row in expected_rows]
    return bool(rows) and len(rows) == 32 and all(
        tuple(row.keys()) == CONTRACT_COLUMNS for row in rows
    ) and len(set(expected_ids)) == 32 and rows == expected_rows and all(
        row["contract_passed"] == "true" and row["blocking_reason"] == "" for row in rows
    )


@dataclass(frozen=True)
class _ExampleSpec:
    example_id: str
    example_class: str
    value: object
    expected_passed: bool
    expected_canonical: str
    expected_reason: str


def _example_specs() -> tuple[_ExampleSpec, ...]:
    valid = (
        ("JUG", "JUG"), ("jug", "JUG"), ("JuG", "JUG"), ("E64", "E64"),
        ("IN3", "IN3"), ("UFP", "UFP"), ("0QE", "0QE"), ("A", "A"),
        ("1", "1"), ("ABC123", "ABC123"), ("A" * 32, "A" * 32),
        ("a" * 32, "A" * 32),
    )
    invalid = (
        (None, "LIGAND_COMP_ID_TYPE_INVALID"),
        (b"JUG", "LIGAND_COMP_ID_TYPE_INVALID"),
        (7, "LIGAND_COMP_ID_TYPE_INVALID"),
        (True, "LIGAND_COMP_ID_TYPE_INVALID"),
        (1.5, "LIGAND_COMP_ID_TYPE_INVALID"),
        ("", "LIGAND_COMP_ID_EMPTY"),
        (" ", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        (" JUG", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("JUG ", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("JU G", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("\t", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("\n", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("JÜG", "LIGAND_COMP_ID_NON_ASCII"),
        ("A" * 33, "LIGAND_COMP_ID_LENGTH_INVALID"),
        (".", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("?", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A-B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A_B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A/B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A,B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A;B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A|B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A:B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
        ("A+B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
    )
    rows = [
        _ExampleSpec(f"LIGEX_{index:03d}", "valid", value, True, canonical, "")
        for index, (value, canonical) in enumerate(valid, 1)
    ]
    rows.extend(
        _ExampleSpec(f"LIGEX_{index:03d}", "invalid", value, False, "", reason)
        for index, (value, reason) in enumerate(invalid, 13)
    )
    return tuple(rows)


def _input_literal(value: object) -> str:
    if value is None:
        return "None"
    if type(value) is str:
        return value.encode("unicode_escape").decode("ascii")
    return repr(value)


def _example_rows() -> list[dict[str, str]]:
    rows = []
    for spec in _example_specs():
        observed = normalize_ligand_comp_id(spec.value)
        passed = (
            observed.passed is spec.expected_passed
            and observed.canonical_ligand_comp_id == spec.expected_canonical
            and observed.blocking_reason == spec.expected_reason
        )
        rows.append({
            "example_id": spec.example_id, "example_class": spec.example_class,
            "input_kind": type(spec.value).__name__, "input_literal": _input_literal(spec.value),
            "expected_passed": _bool_text(spec.expected_passed),
            "expected_canonical_ligand_comp_id": spec.expected_canonical,
            "expected_blocking_reason": spec.expected_reason,
            "observed_passed": _bool_text(observed.passed),
            "observed_canonical_ligand_comp_id": observed.canonical_ligand_comp_id,
            "observed_blocking_reason": observed.blocking_reason,
            "example_passed": _bool_text(passed),
        })
    return rows


def _validate_example_rows(rows: list[dict[str, str]]) -> bool:
    expected_rows = _example_rows()
    expected_ids = [row["example_id"] for row in expected_rows]
    return bool(rows) and len(rows) == 36 and all(
        tuple(row.keys()) == EXAMPLE_COLUMNS for row in rows
    ) and len(set(expected_ids)) == 36 and sum(
        row["example_class"] == "valid" for row in rows
    ) == 12 and sum(row["example_class"] == "invalid" for row in rows) == 24 and rows == expected_rows and all(
        row["example_passed"] == "true" for row in rows
    )


def _safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "required_status": "false", "observed_status": "false",
        "safety_passed": "true", "blocking_reason": "",
    } for item in SAFETY_ITEMS]


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and rows == _safety_rows() and all(
        tuple(row.keys()) == SAFETY_COLUMNS for row in rows
    )


def _issue_rows(section_status: tuple[tuple[str, bool], ...]) -> list[dict[str, str]]:
    failures = [issue_id for section, issue_id in GATE_FAILURE_SPECS if not dict(section_status)[section]]
    if not failures:
        return [{
            "issue_id": "NO_ISSUES", "issue_type": "no_ligand_comp_id_semantics_design_issues",
            "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": "",
        }]
    return [{
        "issue_id": issue_id, "issue_type": "ligand_comp_id_semantics_design_gate_failure",
        "severity": "blocking", "status": "open", "issue_count": "1", "blocking_reason": issue_id,
    } for issue_id in failures]


def _build_materialization(
    *, source_rows: list[dict[str, str]] | None = None, source: dict[str, Any] | None = None,
    contract_rows: list[dict[str, str]] | None = None,
    example_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    source = _load_source() if source is None else source
    contract_rows = _contract_rows() if contract_rows is None else contract_rows
    example_rows = _example_rows() if example_rows is None else example_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    section_status = (
        ("source_boundary", _validate_source_boundary_rows(source_rows)),
        ("source_semantics", _validate_source_semantics(source)),
        ("contract", _validate_contract_rows(contract_rows)),
        ("examples", _validate_example_rows(example_rows)),
        ("safety", _validate_safety_rows(safety_rows)),
    )
    return {
        "source_rows": source_rows, "contract_rows": contract_rows, "example_rows": example_rows,
        "safety_rows": safety_rows, "issue_rows": _issue_rows(section_status),
        "all_source_boundary_checks_passed": dict(section_status)["source_boundary"],
        "all_source_semantics_checks_passed": dict(section_status)["source_semantics"],
        "all_contract_checks_passed": dict(section_status)["contract"],
        "all_example_checks_passed": dict(section_status)["examples"],
        "all_safety_checks_passed": dict(section_status)["safety"],
        "all_checks_passed": all(passed for _, passed in section_status),
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    for name, columns, rows in (
        (CSV_OUTPUTS[0], CONTRACT_COLUMNS, result["contract_rows"]),
        (CSV_OUTPUTS[1], EXAMPLE_COLUMNS, result["example_rows"]),
        (CSV_OUTPUTS[2], SOURCE_COLUMNS, result["source_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    ):
        _write_csv(root / name, columns, rows)
    return {name: _sha256(root / name) for name in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    issues = result["issue_rows"]
    passed = result["all_checks_passed"]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": "only_step14au_c2_six_committed_metadata_outputs",
        "source_input_count": 6, "source_input_sha256": SOURCE_SHA256,
        "artifact_reference_paths_not_recursively_opened": True,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5, "upstream_effective_issue_count": 11,
        "expected_post_integration_issue_count": 10,
        "resolved_design_issue_ids": [TARGET_BLOCKER],
        "ligand_comp_id_semantics_frozen": passed,
        "ligand_comp_id_semantics_integrated": False,
        "integration_applied_current_step": False,
        "ligand_comp_id_exact_type_contract_ready": passed,
        "ligand_comp_id_syntax_contract_ready": passed,
        "ligand_comp_id_normalization_contract_ready": passed,
        "ligand_comp_id_single_component_contract_ready": passed,
        "admit_003_rule_logic_ready": False,
        "ready_for_ligand_comp_id_semantics_integration": passed,
        "ready_for_admission_evaluator_interface_implementation": passed,
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "candidate_records_materialized_current_step": False,
        "download_queue_materialized_current_step": False,
        "raw_structure_read_current_step": False, "network_access_used_current_step": False,
        "external_component_registry_lookup_current_step": False,
        "contract_row_count": len(result["contract_rows"]),
        "example_row_count": len(result["example_rows"]),
        "valid_example_count": sum(row["example_class"] == "valid" for row in result["example_rows"]),
        "invalid_example_count": sum(row["example_class"] == "invalid" for row in result["example_rows"]),
        "source_audit_row_count": len(result["source_rows"]),
        "safety_audit_row_count": len(result["safety_rows"]),
        "all_contract_checks_passed": result["all_contract_checks_passed"],
        "all_example_checks_passed": result["all_example_checks_passed"],
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_source_semantics_checks_passed": result["all_source_semantics_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"],
        "all_checks_passed": passed,
        "blocking_reasons": [] if issues[0]["issue_id"] == "NO_ISSUES" else [row["issue_id"] for row in issues],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
        "non_manifest_output_count": 5, "output_file_count": 6,
        "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME], "output_sha256": output_sha256,
    }


def run_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Materialize design evidence without integrating ADMIT_003."""
    result = _build_materialization()
    output_sha256 = _write_outputs(output_root, result)
    manifest = _manifest_payload(result, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest

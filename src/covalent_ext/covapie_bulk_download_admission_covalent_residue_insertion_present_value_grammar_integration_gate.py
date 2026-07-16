"""Step14AU-E1-D insertion present-value grammar successor integration gate.

This metadata-only gate reads exactly the six committed E1-B outputs and the
six committed E1-C outputs.  It validates them from a frozen byte snapshot and
changes only the effective ADMIT_004 residue-insertion semantics metadata.  It
does not import predecessor production code, execute a parser/provider, read
raw structures, implement an evaluator, or materialize candidate records.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-D"
STAGE = "covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1"
E1C_STAGE = "covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1"
EXPECTED_BASE_COMMIT = "c1779bb0755469c06c311f3a440683cf41e7b2f1"
MANIFEST_SCHEMA_VERSION = "covapie_covalent_residue_insertion_present_value_grammar_integration_manifest_v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_004_rule_logic_interface_v1"
BLOCKED_NEXT_STEP = "repair_covapie_covalent_residue_insertion_present_value_grammar_integration_evidence_v1"
IDENTITY_ISSUE = "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
PROVIDER_ISSUE = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
INTEGRATION_REASON = (
    "covalent residue identity, insertion-code state/value, exact-preserve, fail-closed, "
    "and four-way agreement semantics contract frozen"
)
INSERTION_SOURCE_VALUE_CONTRACT = (
    "insertion-code value paired with absent/present/unknown state; present value uses "
    "exact nonempty PDBx/mmCIF code grammar"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

E1B_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1")
E1C_ROOT = Path("data/derived/covalent_small") / E1C_STAGE
SOURCE_PATHS = tuple(Path(value) for value in (
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_integrated_rule_matrix.csv"),
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_integrated_field_matrix.csv"),
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_integrated_context_matrix.csv"),
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_integration_safety_audit.csv"),
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_integration_issue_inventory.csv"),
    str(E1B_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_integration_manifest.json"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_contract.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_examples_and_state_value_truth_table.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_source_boundary_audit.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_safety_audit.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_issue_transition_inventory.csv"),
    str(E1C_ROOT / "covapie_covalent_residue_insertion_present_value_grammar_design_manifest.json"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "b4a3d876acaf1c521b06fe2a35f3da2448662e632cb0f44fab355e30c7861d99",
    "940724c739c6da6a9f76a7e66e03d4261abfc152df552756faea614f54fd68df",
    "1e3dd997d2baa2421b77d0e75a0751dca7c2d8025132a6f615e41d9172c9e2a1",
    "2019039c72e393fa625d2615c76a82ac91cac6a1f5438e395370a156df9c6cbf",
    "a011d21b73182f27898df69ccbe3ef0eda061d46ced7e095aebcdda31fab3903",
    "d9bd804936c2405d6baa97bf2bd207def4d596e64ed4fd05edb341db4327bfc3",
    "bb4907d1b6580e0e2487d8839e01b718ebf904f2debc49c4df9d4716c18274be",
    "1c2d75f10fb04718efa61b73e1f8b190bf21b73202b23d6569bc8bd6cc8888bd",
    "6b46941e8b0a54da7db77d2a48ad4f0db93555ca4afccd1fb2ddae068399d75a",
    "77bbe42e6083b8423dfc6a22bd73030509851edef8620852b832c090f2b4df38",
    "f28b7cfa0f2faf9b85ffafd7fe8a15abcb6fa3023896439b40a9b2c57c2e2c05",
    "fa607b72c520310d831992c722f9bb930594b8cd95af89b3ad3d1c38274a8d19",
), strict=True))

(E1B_RULE_PATH, E1B_FIELD_PATH, E1B_CONTEXT_PATH, E1B_SAFETY_PATH,
 E1B_ISSUE_PATH, E1B_MANIFEST_PATH, E1C_CONTRACT_PATH, E1C_EXAMPLES_PATH,
 E1C_SOURCE_AUDIT_PATH, E1C_SAFETY_PATH, E1C_ISSUE_PATH,
 E1C_MANIFEST_PATH) = SOURCE_PATHS

RULE_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integrated_rule_matrix.csv"
FIELD_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integrated_field_matrix.csv"
CONTEXT_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integrated_context_matrix.csv"
SAFETY_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integration_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integration_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_insertion_present_value_grammar_integration_manifest.json"
CSV_OUTPUTS = (RULE_FILENAME, FIELD_FILENAME, CONTEXT_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

RULE_COLUMNS = (
    "admission_rule_id", "admission_rule_name", "evaluation_phase", "candidate_field_dependencies",
    "batch_context_dependencies", "evaluation_context_dependencies", "external_filesystem_required",
    "network_required", "download_execution_result_required", "pure_in_memory_interface_possible",
    "dependency_contract_passed", "semantics_complete", "deterministic_evaluation_possible_now",
    "deterministic_evaluation_possible_after_contract_freeze", "implementation_disposition",
    "blocking_reasons", "source_stage", "integration_source_stage", "integration_applied",
    "integration_reason",
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
    "filesystem_access_inside_evaluator", "network_access_inside_evaluator", "deterministic_now",
    "deterministic_after_contract_freeze", "exact_contract_defined", "implementation_ready",
    "blocking_reasons", "source_stage", "integration_source_stage", "integration_applied",
    "integration_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
CONTRACT_COLUMNS = (
    "contract_id", "contract_area", "contract_statement", "expected_value", "observed_value",
    "contract_passed",
)
EXAMPLE_COLUMNS = (
    "row_kind", "case_id", "input_descriptor", "input_type", "input_length", "expected_outcome",
    "observed_outcome", "expected_reason", "observed_reason", "canonical_descriptor",
    "exact_preserved", "case_preserved", "example_passed",
)
SOURCE_AUDIT_COLUMNS = (
    "source_order", "source_relative_path", "tracked_by_git", "base_tree_blob",
    "filesystem_regular", "symlink", "sha256_expected", "sha256_observed", "source_verified",
)

TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "e1b_effective_matrix_validation", "e1c_grammar_design_validation",
    "target_rule_overlay", "target_field_overlay", "target_context_overlay",
    "issue_resolution_overlay", "exact11_invariant_validation",
)
FALSE_SAFETY_ITEMS = (
    "raw_read", "parser_execution", "provider_execution", "evaluator_implementation",
    "candidate_record_materialization", "candidate_evaluation", "admission_record_modification",
    "sample_backfill", "network", "download", "checkpoint", "torch", "numpy", "rdkit",
    "model_forward_loss_training",
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


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False,
    )


def _safe_relative_path(path: Path) -> bool:
    return isinstance(path, Path) and not path.is_absolute() and bool(path.parts) and ".." not in path.parts


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Check structure only; this function must not read source content bytes."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    tree_fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(tree_fields) == 3
        and tree_fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Complete every exact12 structural check before reading the first source byte."""
    if len(SOURCE_PATHS) != 12 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("exact12 source boundary shape invalid")
    structural_results = tuple(_structural_source_check(path, repo_root) for path in SOURCE_PATHS)
    if not all(structural_results):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        filesystem_bytes = (repo_root / path).read_bytes()
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, base_sha, filesystem_sha, filesystem_bytes))
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
    matches = [record for record in snapshot.records if record.relative_path == path]
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    source_text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(source_text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(item is None for item in row.values()) for row in rows):
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


def _validate_e1b(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    rules = _csv_document(snapshot, E1B_RULE_PATH)
    fields = _csv_document(snapshot, E1B_FIELD_PATH)
    contexts = _csv_document(snapshot, E1B_CONTEXT_PATH)
    safety = _csv_document(snapshot, E1B_SAFETY_PATH)
    issues = _csv_document(snapshot, E1B_ISSUE_PATH)
    manifest = _json_document(snapshot, E1B_MANIFEST_PATH)
    if (rules.header, fields.header, contexts.header, issues.header) != (
        RULE_COLUMNS, FIELD_COLUMNS, CONTEXT_COLUMNS, ISSUE_COLUMNS,
    ):
        raise ValueError("E1-B schema mismatch")
    if (len(rules.rows), len(fields.rows), len(contexts.rows), len(issues.rows)) != (15, 22, 18, 10):
        raise ValueError("E1-B count mismatch")
    rule_map = _keyed(rules.rows, "admission_rule_id")
    field_map = _keyed(fields.rows, "field_name")
    context_map = _keyed(contexts.rows, "context_item")
    admit_004 = rule_map["ADMIT_004"]
    insertion = field_map["covalent_residue_insertion_code"]
    identity = context_map["covalent_residue_identity_contract"]
    expected_manifest = {
        "integrated_rule_count": 15, "integrated_field_count": 22,
        "integrated_context_count": 18, "active_issue_count": 10,
        "semantics_complete_rule_count": 6,
        "implementation_semantics_complete_field_count": 11,
        "implementation_ready_context_count": 8,
        "exact11_identity_atom_audit_count": 11,
        "exact11_insertion_unknown_empty_count": 11,
        "exact11_insertion_blocked_count": 11,
        "exact11_effective_blocked_count": 11,
        "exact11_auth_label_conflict_count": 3,
        "exact11_auth_label_no_conflict_count": 8,
    }
    checks = (
        sum(row["semantics_complete"] == "true" for row in rules.rows) == 6,
        sum(row["implementation_semantics_complete"] == "true" for row in fields.rows) == 11,
        sum(row["implementation_ready"] == "true" for row in contexts.rows) == 8,
        admit_004["semantics_complete"] == "false",
        admit_004["deterministic_evaluation_possible_now"] == "false",
        admit_004["deterministic_evaluation_possible_after_contract_freeze"] == "true",
        admit_004["implementation_disposition"] == "interface_only_pending_semantics",
        admit_004["blocking_reasons"] == IDENTITY_ISSUE,
        admit_004["integration_applied"] == "true",
        insertion["allowed_values_defined"] == "false",
        insertion["normalization_defined"] == "true",
        insertion["exact_validation_defined"] == "false",
        insertion["implementation_semantics_complete"] == "false",
        insertion["blocking_reasons"] == IDENTITY_ISSUE,
        identity["deterministic_now"] == "false",
        identity["deterministic_after_contract_freeze"] == "true",
        identity["exact_contract_defined"] == "false",
        identity["implementation_ready"] == "false",
        identity["blocking_reasons"] == IDENTITY_ISSUE,
        rule_map["ADMIT_005"]["implementation_disposition"] == "rule_logic_ready",
        rule_map["ADMIT_005"]["semantics_complete"] == "true",
        safety.header == SAFETY_COLUMNS and all(row["safety_passed"] == "true" for row in safety.rows),
        all(manifest.get(key) == value for key, value in expected_manifest.items()),
        manifest.get("all_checks_passed") is True,
        manifest.get("admit_004_rule_logic_ready") is False,
        manifest.get("admit_005_rule_logic_ready") is True,
        manifest.get("ready_for_real_candidate_evaluation") is False,
        manifest.get("ready_for_bulk_download_now") is False,
        manifest.get("ready_for_training") is False,
        manifest.get("ready_to_train_now") is False,
    )
    if not all(checks):
        raise ValueError("E1-B direct evidence validation failed")
    return {
        "rules": rules.rows, "fields": fields.rows, "contexts": contexts.rows,
        "issues": issues.rows, "manifest": manifest,
    }


def _validate_e1c(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    contract = _csv_document(snapshot, E1C_CONTRACT_PATH)
    examples = _csv_document(snapshot, E1C_EXAMPLES_PATH)
    source_audit = _csv_document(snapshot, E1C_SOURCE_AUDIT_PATH)
    safety = _csv_document(snapshot, E1C_SAFETY_PATH)
    issues = _csv_document(snapshot, E1C_ISSUE_PATH)
    manifest = _json_document(snapshot, E1C_MANIFEST_PATH)
    if (contract.header, examples.header, source_audit.header, safety.header, issues.header) != (
        CONTRACT_COLUMNS, EXAMPLE_COLUMNS, SOURCE_AUDIT_COLUMNS, SAFETY_COLUMNS, ISSUE_COLUMNS,
    ):
        raise ValueError("E1-C schema mismatch")
    if (len(contract.rows), len(examples.rows), len(source_audit.rows), len(issues.rows)) != (31, 64, 39, 10):
        raise ValueError("E1-C count mismatch")
    contract_map = _keyed(contract.rows, "contract_id")
    issue_map = _keyed(issues.rows, "issue_id")
    kinds = {
        kind: sum(row["row_kind"] == kind for row in examples.rows)
        for kind in ("present_valid_example", "present_invalid_example", "state_value_truth")
    }
    punctuation_rows = [
        row for row in examples.rows
        if row["row_kind"] == "present_valid_example" and 8 <= int(row["case_id"].split("_")[-1]) <= 35
    ]
    unknown_truth = next(row for row in examples.rows if row["case_id"] == "STATE_VALUE_007")
    required_contract_values = {
        "INSERTION_GRAMMAR_005": r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+",
        "INSERTION_GRAMMAR_012": "exact", "INSERTION_GRAMMAR_013": "none",
        "INSERTION_GRAMMAR_014": "none", "INSERTION_GRAMMAR_015": "none",
        "INSERTION_GRAMMAR_016": "exact", "INSERTION_GRAMMAR_018": "absent|present|unknown",
        "INSERTION_GRAMMAR_019": "passed", "INSERTION_GRAMMAR_020": "blocked",
        "INSERTION_GRAMMAR_021": "passed", "INSERTION_GRAMMAR_022": "true",
        "INSERTION_GRAMMAR_024": "true", "INSERTION_GRAMMAR_025": "exact",
        "INSERTION_GRAMMAR_026": "exact", "INSERTION_GRAMMAR_027": "false",
        "INSERTION_GRAMMAR_028": "false", "INSERTION_GRAMMAR_029": "false",
        "INSERTION_GRAMMAR_030": "true", "INSERTION_GRAMMAR_031": "false",
    }
    expected_flags = {
        "insertion_present_value_grammar_design_frozen": True,
        "state_value_combination_contract_frozen": True,
        "exact_preserve_policy_frozen": True,
        "struct_conn_atom_site_agreement_design_frozen": True,
        "invalid_state_value_outcomes_fail_closed": True,
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality": True,
        "ready_for_insertion_present_value_grammar_successor_integration": True,
        "insertion_present_value_grammar_integrated_into_effective_schema": False,
        "covalent_residue_identity_contract_fully_integrated": False,
        "admit_004_rule_logic_ready": False,
        "admit_004_evaluator_implemented": False,
        "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False,
        "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
    }
    checks = (
        all(row["contract_passed"] == "true" and row["expected_value"] == row["observed_value"] for row in contract.rows),
        all(contract_map[key]["observed_value"] == value for key, value in required_contract_values.items()),
        kinds == {"present_valid_example": 35, "present_invalid_example": 15, "state_value_truth": 14},
        all(row["example_passed"] == "true" for row in examples.rows),
        len(punctuation_rows) == 28 and all(row["exact_preserved"] == "true" for row in punctuation_rows),
        unknown_truth["observed_outcome"] == "blocked",
        unknown_truth["observed_reason"] == UNKNOWN_REASON,
        unknown_truth["input_length"] == "0",
        all(
            row["source_order"] == str(index)
            and row["tracked_by_git"] == row["base_tree_blob"] == row["filesystem_regular"] == "true"
            and row["symlink"] == "false"
            and row["sha256_expected"] == row["sha256_observed"]
            and row["source_verified"] == "true"
            for index, row in enumerate(source_audit.rows, 1)
        ),
        all(row["safety_passed"] == "true" for row in safety.rows),
        all(row["status"] == "open" for row in issues.rows),
        issue_map[IDENTITY_ISSUE]["integration_transition"] == "insertion_present_value_grammar_design_frozen_pending_successor_integration",
        issue_map[PROVIDER_ISSUE]["severity"] == "blocking",
        issue_map[PROVIDER_ISSUE]["issue_count"] == "11",
        manifest.get("examples_and_state_value_truth_row_count") == 64,
        manifest.get("allowed_punctuation_count") == 28,
        manifest.get("exact11_count") == manifest.get("exact11_unknown_count") == manifest.get("exact11_blocked_count") == 11,
        manifest.get("exact11_auth_label_conflict_count") == 3,
        manifest.get("exact11_auth_label_no_conflict_count") == 8,
        all(manifest.get(key) is value for key, value in expected_flags.items()),
        manifest.get("all_checks_passed") is True,
    )
    if not all(checks):
        raise ValueError("E1-C direct evidence validation failed")
    return {"contract": contract.rows, "examples": examples.rows, "issues": issues.rows, "manifest": manifest}


def _overlay_rules(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    target = _keyed(rows, "admission_rule_id")["ADMIT_004"]
    target.update({
        "semantics_complete": "true",
        "deterministic_evaluation_possible_now": "true",
        "deterministic_evaluation_possible_after_contract_freeze": "true",
        "implementation_disposition": "rule_logic_ready",
        "blocking_reasons": "",
        "integration_source_stage": E1C_STAGE,
        "integration_applied": "true",
        "integration_reason": INTEGRATION_REASON,
    })
    return rows


def _overlay_fields(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    target = _keyed(rows, "field_name")["covalent_residue_insertion_code"]
    target.update({
        "source_value_contract": INSERTION_SOURCE_VALUE_CONTRACT,
        "allowed_values_defined": "true", "normalization_defined": "true",
        "exact_validation_defined": "true", "implementation_semantics_complete": "true",
        "semantics_evidence": E1C_STAGE, "blocking_reasons": "",
        "integration_source_stage": E1C_STAGE, "integration_applied": "true",
        "integration_reason": INTEGRATION_REASON,
    })
    return rows


def _overlay_contexts(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    target = _keyed(rows, "context_item")["covalent_residue_identity_contract"]
    target.update({
        "deterministic_now": "true", "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true", "implementation_ready": "true",
        "blocking_reasons": "", "integration_source_stage": E1C_STAGE,
        "integration_applied": "true", "integration_reason": INTEGRATION_REASON,
    })
    return rows


def _overlay_issues(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in source if row["issue_id"] != IDENTITY_ISSUE]


def _safety_rows() -> list[dict[str, str]]:
    return [
        {"safety_item": item, "expected_executed": "true", "observed_executed": "true", "safety_passed": "true"}
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {"safety_item": item, "expected_executed": "false", "observed_executed": "false", "safety_passed": "true"}
        for item in FALSE_SAFETY_ITEMS
    ]


def _unchanged_except(
    rows: Sequence[Mapping[str, str]], source: Sequence[Mapping[str, str]], key: str,
    target: str, allowed: set[str],
) -> bool:
    if len(rows) != len(source) or [row[key] for row in rows] != [row[key] for row in source]:
        return False
    for row, original in zip(rows, source):
        if row[key] != target and row != original:
            return False
        if row[key] == target and any(row[column] != original[column] for column in original if column not in allowed):
            return False
    return True


def _validate_exact11_invariant(e1b: Mapping[str, Any], e1c: Mapping[str, Any]) -> bool:
    b = e1b["manifest"]
    c = e1c["manifest"]
    return (
        b.get("exact11_identity_atom_audit_count") == 11
        and b.get("exact11_insertion_unknown_empty_count") == 11
        and b.get("exact11_insertion_blocked_count") == 11
        and b.get("exact11_effective_blocked_count") == 11
        and b.get("exact11_auth_label_conflict_count") == 3
        and b.get("exact11_auth_label_no_conflict_count") == 8
        and c.get("exact11_count") == c.get("exact11_unknown_count") == c.get("exact11_blocked_count") == 11
        and c.get("exact11_auth_label_conflict_count") == 3
        and c.get("exact11_auth_label_no_conflict_count") == 8
        and any(
            row["case_id"] == "STATE_VALUE_007"
            and row["observed_outcome"] == "blocked"
            and row["observed_reason"] == UNKNOWN_REASON
            for row in e1c["examples"]
        )
    )


def _validate_overlays(
    rules: Sequence[Mapping[str, str]], fields: Sequence[Mapping[str, str]],
    contexts: Sequence[Mapping[str, str]], issues: Sequence[Mapping[str, str]],
    safety: Sequence[Mapping[str, str]], e1b: Mapping[str, Any], e1c: Mapping[str, Any],
) -> bool:
    rule_allowed = {
        "semantics_complete", "deterministic_evaluation_possible_now",
        "deterministic_evaluation_possible_after_contract_freeze", "implementation_disposition",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    }
    field_allowed = {
        "source_value_contract", "allowed_values_defined", "normalization_defined",
        "exact_validation_defined", "implementation_semantics_complete", "semantics_evidence",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    }
    context_allowed = {
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
        "implementation_ready", "blocking_reasons", "integration_source_stage",
        "integration_applied", "integration_reason",
    }
    rule_map = _keyed(rules, "admission_rule_id")
    field_map = _keyed(fields, "field_name")
    context_map = _keyed(contexts, "context_item")
    source_issue_ids = [row["issue_id"] for row in e1c["issues"]]
    expected_issue_ids = [item for item in source_issue_ids if item != IDENTITY_ISSUE]
    source_issue_map = _keyed(e1c["issues"], "issue_id")
    issue_map = _keyed(issues, "issue_id")
    target_rule = rule_map["ADMIT_004"]
    target_field = field_map["covalent_residue_insertion_code"]
    target_context = context_map["covalent_residue_identity_contract"]
    locator_fields = (
        "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
        "covalent_residue_locator_provenance_source_id", "covalent_residue_locator_provenance_sha256",
    )
    return (
        _unchanged_except(rules, e1b["rules"], "admission_rule_id", "ADMIT_004", rule_allowed)
        and _unchanged_except(fields, e1b["fields"], "field_name", "covalent_residue_insertion_code", field_allowed)
        and _unchanged_except(contexts, e1b["contexts"], "context_item", "covalent_residue_identity_contract", context_allowed)
        and target_rule["semantics_complete"] == target_rule["deterministic_evaluation_possible_now"] == "true"
        and target_rule["implementation_disposition"] == "rule_logic_ready"
        and target_rule["blocking_reasons"] == ""
        and target_rule["integration_source_stage"] == E1C_STAGE
        and target_rule["integration_reason"] == INTEGRATION_REASON
        and target_field["source_value_contract"] == INSERTION_SOURCE_VALUE_CONTRACT
        and all(target_field[column] == "true" for column in (
            "allowed_values_defined", "normalization_defined", "exact_validation_defined",
            "implementation_semantics_complete", "integration_applied",
        ))
        and target_field["semantics_evidence"] == target_field["integration_source_stage"] == E1C_STAGE
        and target_field["blocking_reasons"] == ""
        and all(field_map[name] == _keyed(e1b["fields"], "field_name")[name] for name in locator_fields)
        and all(target_context[column] == "true" for column in (
            "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
            "implementation_ready", "integration_applied",
        ))
        and target_context["blocking_reasons"] == ""
        and target_context["integration_source_stage"] == E1C_STAGE
        and [row["issue_id"] for row in issues] == expected_issue_ids
        and IDENTITY_ISSUE not in issue_map
        and all(issue_map[item] == source_issue_map[item] for item in expected_issue_ids)
        and issue_map[PROVIDER_ISSUE]["status"] == "open"
        and issue_map[PROVIDER_ISSUE]["severity"] == "blocking"
        and issue_map[PROVIDER_ISSUE]["issue_count"] == "11"
        and list(safety) == _safety_rows()
        and (len(rules), len(fields), len(contexts), len(issues)) == (15, 22, 18, 9)
        and sum(row["semantics_complete"] == "true" for row in rules) == 7
        and sum(row["implementation_semantics_complete"] == "true" for row in fields) == 12
        and sum(row["implementation_ready"] == "true" for row in contexts) == 9
        and _validate_exact11_invariant(e1b, e1c)
    )


def _empty_state(snapshot: FrozenSourceSnapshot | None = None, failure: str = "SOURCE_BOUNDARY_FAILED") -> dict[str, Any]:
    return {
        "source_snapshot": snapshot, "source_ok": False, "e1b_ok": False, "e1c_ok": False,
        "rule_rows": [], "field_rows": [], "context_rows": [], "safety_rows": [], "issue_rows": [],
        "integrated_rule_count": 0, "integrated_field_count": 0, "integrated_context_count": 0,
        "active_issue_count": 0, "semantics_complete_rule_count": 0,
        "implementation_semantics_complete_field_count": 0,
        "implementation_ready_context_count": 0, "integration_readiness": False,
        "all_checks_passed": False, "validation_failures": [failure],
    }


def build_integration_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        e1b = _validate_e1b(snapshot)
        e1b_ok = True
    except (KeyError, StopIteration, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        e1b = {}
        e1b_ok = False
    try:
        e1c = _validate_e1c(snapshot)
        e1c_ok = True
    except (KeyError, StopIteration, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        e1c = {}
        e1c_ok = False
    if not e1b_ok or not e1c_ok:
        state = _empty_state(snapshot, "PREDECESSOR_VALIDATION_FAILED")
        state.update({"source_ok": True, "e1b_ok": e1b_ok, "e1c_ok": e1c_ok})
        return state
    try:
        rules = _overlay_rules(e1b["rules"])
        fields = _overlay_fields(e1b["fields"])
        contexts = _overlay_contexts(e1b["contexts"])
        issues = _overlay_issues(e1c["issues"])
        safety = _safety_rows()
        passed = _validate_overlays(rules, fields, contexts, issues, safety, e1b, e1c)
    except (KeyError, TypeError, ValueError):
        passed = False
        rules, fields, contexts, issues, safety = [], [], [], [], []
    if not passed:
        state = _empty_state(snapshot, "OVERLAY_VALIDATION_FAILED")
        state.update({"source_ok": True, "e1b_ok": True, "e1c_ok": True})
        return state
    return {
        "source_snapshot": snapshot, "source_ok": True, "e1b_ok": True, "e1c_ok": True,
        "rule_rows": rules, "field_rows": fields, "context_rows": contexts,
        "safety_rows": safety, "issue_rows": issues,
        "integrated_rule_count": 15, "integrated_field_count": 22,
        "integrated_context_count": 18, "active_issue_count": 9,
        "semantics_complete_rule_count": 7,
        "implementation_semantics_complete_field_count": 12,
        "implementation_ready_context_count": 9, "integration_readiness": True,
        "all_checks_passed": True, "validation_failures": [],
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
    remaining_ids = [row["issue_id"] for row in state["issue_rows"]]
    return {
        "project": PROJECT, "step": STEP, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "source_input_count": 12,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {
                "source_ordinal": index, "source_relative_path": record.relative_path.as_posix(),
                "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
                "non_symlink": True, "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256, "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "predecessor_e1b_rule_count": 15, "predecessor_e1b_field_count": 22,
        "predecessor_e1b_context_count": 18, "predecessor_e1b_issue_count": 10,
        "predecessor_e1b_semantics_complete_rule_count": 6,
        "predecessor_e1b_implementation_semantics_complete_field_count": 11,
        "predecessor_e1b_implementation_ready_context_count": 8,
        "predecessor_e1c_contract_count": 31, "predecessor_e1c_examples_truth_count": 64,
        "predecessor_e1c_present_valid_count": 35, "predecessor_e1c_present_invalid_count": 15,
        "predecessor_e1c_state_value_truth_count": 14, "predecessor_e1c_punctuation_count": 28,
        "predecessor_e1c_source_audit_count": 39, "predecessor_e1c_issue_count": 10,
        "integrated_rule_count": state["integrated_rule_count"],
        "integrated_field_count": state["integrated_field_count"],
        "integrated_context_count": state["integrated_context_count"],
        "active_issue_count": state["active_issue_count"],
        "semantics_complete_rule_count": state["semantics_complete_rule_count"],
        "implementation_semantics_complete_field_count": state["implementation_semantics_complete_field_count"],
        "implementation_ready_context_count": state["implementation_ready_context_count"],
        "resolved_issue_ids": [IDENTITY_ISSUE], "remaining_issue_ids": remaining_ids,
        "provider_blocking_issue_id": PROVIDER_ISSUE, "provider_blocking_issue_count": 11,
        "exact11_count": 11, "exact11_insertion_unknown_count": 11,
        "exact11_insertion_value_empty_count": 11, "exact11_insertion_blocked_count": 11,
        "exact11_effective_blocked_count": 11, "exact11_reason": UNKNOWN_REASON,
        "exact11_auth_label_conflict_count": 3, "exact11_auth_label_no_conflict_count": 8,
        "insertion_present_value_grammar_integrated_into_effective_schema": True,
        "residue_identity_semantics_integrated_into_effective_schema": True,
        "covalent_residue_identity_contract_fully_integrated": True,
        "admit_004_rule_logic_ready": True,
        "ready_for_admit_004_rule_logic_implementation": True,
        "admit_005_rule_logic_ready": True,
        "invalid_state_value_outcomes_fail_closed": True,
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality": True,
        "admit_004_evaluator_implemented": False,
        "parser_quote_class_roundtrip_verified": False,
        "real_provider_present_value_roundtrip_ready": False,
        "real_provider_export_blocking_rows_resolved": False,
        "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "raw_read_current_step": False, "parser_executed_current_step": False,
        "provider_executed_current_step": False, "evaluator_implemented_current_step": False,
        "candidate_records_materialized_current_step": False,
        "candidate_evaluation_current_step": False,
        "admission_records_modified_current_step": False, "sample_backfill_current_step": False,
        "network_accessed_current_step": False, "download_attempted_current_step": False,
        "checkpoint_accessed_current_step": False, "torch_used_current_step": False,
        "numpy_used_current_step": False, "rdkit_used_current_step": False,
        "model_forward_loss_training_used_current_step": False,
        "all_source_boundary_checks_passed": True,
        "all_e1b_predecessor_checks_passed": True,
        "all_e1c_predecessor_checks_passed": True,
        "all_overlay_checks_passed": True, "all_safety_checks_passed": True,
        "all_checks_passed": True, "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


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


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        RULE_FILENAME: _csv_bytes(RULE_COLUMNS, state["rule_rows"]),
        FIELD_FILENAME: _csv_bytes(FIELD_COLUMNS, state["field_rows"]),
        CONTEXT_FILENAME: _csv_bytes(CONTEXT_COLUMNS, state["context_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in csv_payloads.items()}
    manifest = _manifest_payload(state, hashes)
    return {**csv_payloads, MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")}, manifest


def run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_integration_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError("E1-D integration gate failed closed: " + "|".join(state["validation_failures"]))
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
    result = run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

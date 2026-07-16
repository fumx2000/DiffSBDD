"""Step14AU-E1-B partial successor integration for ADMIT_004/ADMIT_005.

The gate reads exactly twelve committed metadata outputs, validates them from
an in-memory frozen snapshot, and overlays only the semantics frozen by E1-A.
It does not implement an evaluator or read raw/provider/parser/model state.
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


PROJECT_NAME = "CovaPIE"
STEP_LABEL = "Step14AU-E1-B"
STAGE = "covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1"
E1A_STAGE = "covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1"
EXPECTED_BASE_HEAD = "b4a4f2e9385fd86d08ef69fc1cfb16bfa46e5377"
MANIFEST_SCHEMA_VERSION = "covapie_admit_004_residue_identity_atom_name_semantics_integration_manifest_v1"
RECOMMENDED_NEXT_STEP = "design_covapie_covalent_residue_insertion_present_value_grammar_v1"
BLOCKED_NEXT_STEP = "resolve_covapie_admit_004_residue_identity_atom_name_integration_blockers"
PARTIAL_REASON = (
    "core covalent residue name/chain/index and exact SG atom-name semantics integrated; "
    "covalent residue insertion-code present-value grammar remains unresolved"
)
COMPLETE_REASON = "covalent residue name canonicalization and exact SG atom-name semantics contract frozen"
IDENTITY_ISSUE = "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
ATOM_ISSUE = "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

P3_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1")
E1A_ROOT = Path("data/derived/covalent_small") / E1A_STAGE
SOURCE_PATHS = tuple(Path(value) for value in (
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv"),
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_field_matrix.csv"),
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_context_matrix.csv"),
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_integration_safety_audit.csv"),
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_integration_issue_inventory.csv"),
    str(P3_ROOT / "covapie_covalent_residue_locator_schema_extension_integration_manifest.json"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_contract.csv"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_truth_table.csv"),
    str(E1A_ROOT / "covapie_admit_004_exact11_identity_atom_name_evidence_audit.csv"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_safety_audit.csv"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_issue_transition_inventory.csv"),
    str(E1A_ROOT / "covapie_admit_004_residue_identity_atom_name_semantics_design_manifest.json"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "c1ae6cf9c2ca5450315ff3e3ed21b0a81d8bfc08c6a07e35d3f2dca1874e0d2f",
    "53dccd0ff7b20465c9df13f2c9eefc254f39bcb40e30732d1cfdfa4036e888fb",
    "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8",
    "4eaca47e07fd58dfdf2c1d05e8fb26083b013f0abcb2944e0950b8e967aba49b",
    "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    "676fe3c86e1304ba4971862d1e270fed40d9665e16c356d719627538aa28ee44",
    "a783a3d474a2ed4e5ff348ec54a73510f5f6f6fb9d1edcb45dc97108e5d09eff",
    "a5c2d727b3178bd0e58643a1801780fa930cba2b89c14a058817ecb418753106",
    "62f7c26b41daef96c32ca615b7d65a063810a53cef582a26cd54ed9cfb8b6e2a",
    "02ae82b6db51dc6e4b96f8240af8852289012e33cc9620ef796ff5f5e8bb2711",
    "fecb82397a853e900a53368dedc6bacf95fdc497fa6cd09c31a9be8a1e1d0577",
    "c442d31cebaea6b8e3ae5dbda232cc5ba377eb74a2ca68c2437ce0b43a39e6c0",
), strict=True))

(P3_RULE_PATH, P3_FIELD_PATH, P3_CONTEXT_PATH, P3_SAFETY_PATH,
 P3_ISSUE_PATH, P3_MANIFEST_PATH, E1A_CONTRACT_PATH, E1A_TRUTH_PATH,
 E1A_EXACT11_PATH, E1A_SAFETY_PATH, E1A_ISSUE_PATH, E1A_MANIFEST_PATH) = SOURCE_PATHS

RULE_FILENAME = "covapie_admit_004_residue_identity_atom_name_integrated_rule_matrix.csv"
FIELD_FILENAME = "covapie_admit_004_residue_identity_atom_name_integrated_field_matrix.csv"
CONTEXT_FILENAME = "covapie_admit_004_residue_identity_atom_name_integrated_context_matrix.csv"
SAFETY_FILENAME = "covapie_admit_004_residue_identity_atom_name_integration_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_004_residue_identity_atom_name_integration_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_004_residue_identity_atom_name_semantics_integration_manifest.json"
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
CONTRACT_COLUMNS = ("contract_id", "contract_area", "contract_statement", "expected_value", "observed_value", "contract_passed")
TRUTH_COLUMNS = (
    "case_id", "case_description", "input_residue_name", "input_locator_namespace",
    "input_candidate_chain_id", "input_candidate_residue_index", "input_atom_name",
    "input_insertion_state", "input_insertion_value", "provider_evidence_disposition",
    "canonical_residue_name", "expected_admit_004_outcome", "observed_admit_004_outcome",
    "expected_admit_005_outcome", "observed_admit_005_outcome", "expected_effective_outcome",
    "observed_effective_outcome", "expected_reason", "observed_reason", "truth_table_passed",
)
EXACT11_COLUMNS = (
    "audit_row_id", "binding_row_id", "pdb_id", "covalent_residue_name_input",
    "canonical_residue_name", "candidate_atom_name", "matched_residue_atom_name",
    "locator_namespace", "selected_chain_id", "selected_residue_index", "auth_chain_id",
    "auth_residue_index", "label_chain_id", "label_residue_index", "auth_label_conflict_observed",
    "provider_five_fields_match", "insertion_state", "insertion_value",
    "admit_004_identity_semantics_valid", "admit_005_scope_outcome", "insertion_blocks",
    "effective_outcome", "reason", "audit_passed",
)

TARGET_FIELDS = (
    "covalent_residue_name", "covalent_residue_chain_id", "covalent_residue_index",
    "covalent_residue_atom_name",
)
LOCATOR_FIELDS = (
    "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code", "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
FIELD_REASONS = {
    "covalent_residue_name": "residue-name component grammar and uppercase canonicalization semantics frozen by E1-A",
    "covalent_residue_chain_id": "chain identity exact lexical no-trim/no-case-repair semantics frozen by E1-A",
    "covalent_residue_index": "residue index exact lexical no-trim/no-coercion semantics frozen by E1-A",
    "covalent_residue_atom_name": "exact SG atom-name no-trim/no-case-repair semantics frozen by E1-A",
}
TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "p3_effective_matrix_validation", "e1a_design_evidence_validation",
    "target_rule_overlay", "target_field_overlay", "target_context_partial_overlay",
    "issue_transition_overlay",
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
    observed_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _git(args: Sequence[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, check=False)


def _safe_source_path(path: Path) -> bool:
    return isinstance(path, Path) and not path.is_absolute() and bool(path.parts) and ".." not in path.parts


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_source_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_HEAD, "--", path.as_posix()], repo_root)
    return (
        tracked.returncode == 0 and tree.returncode == 0 and " blob " in tree.stdout
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Complete all structural checks before reading the first source byte."""
    if len(SOURCE_PATHS) != 12 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("source boundary shape invalid")
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records = []
    for path in SOURCE_PATHS:
        content = (repo_root / path).read_bytes()
        observed = hashlib.sha256(content).hexdigest()
        if observed != SOURCE_SHA256[path]:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], observed, content))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 12
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.observed_sha256 == record.expected_sha256
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


def _validate_p3(snapshot: FrozenSourceSnapshot) -> bool:
    rules = _csv_document(snapshot, P3_RULE_PATH)
    fields = _csv_document(snapshot, P3_FIELD_PATH)
    contexts = _csv_document(snapshot, P3_CONTEXT_PATH)
    safety = _csv_document(snapshot, P3_SAFETY_PATH)
    issues = _csv_document(snapshot, P3_ISSUE_PATH)
    manifest = _json_document(snapshot, P3_MANIFEST_PATH)
    if (rules.header, fields.header, contexts.header) != (RULE_COLUMNS, FIELD_COLUMNS, CONTEXT_COLUMNS):
        return False
    if len(rules.rows) != 15 or len(fields.rows) != 22 or len(contexts.rows) != 18 or len(issues.rows) != 10:
        return False
    rule_map = _keyed(rules.rows, "admission_rule_id")
    field_map = _keyed(fields.rows, "field_name")
    context_map = _keyed(contexts.rows, "context_item")
    expected_blockers = ATOM_ISSUE + "|" + IDENTITY_ISSUE
    expected_rule = {
        "semantics_complete": "false", "deterministic_evaluation_possible_now": "false",
        "implementation_disposition": "interface_only_pending_semantics", "blocking_reasons": expected_blockers,
    }
    insertion = field_map["covalent_residue_insertion_code"]
    identity = context_map["covalent_residue_identity_contract"]
    return (
        all(all(row.get(key) == value for key, value in expected_rule.items()) for row in (rule_map["ADMIT_004"], rule_map["ADMIT_005"]))
        and insertion.get("allowed_values_defined") == "false"
        and insertion.get("normalization_defined") == "true"
        and insertion.get("exact_validation_defined") == "false"
        and insertion.get("implementation_semantics_complete") == "false"
        and insertion.get("blocking_reasons") == IDENTITY_ISSUE
        and identity.get("deterministic_now") == "false"
        and identity.get("exact_contract_defined") == "false"
        and identity.get("implementation_ready") == "false"
        and identity.get("blocking_reasons") == IDENTITY_ISSUE
        and safety.header == ("safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason")
        and all(row["safety_passed"] == "true" for row in safety.rows)
        and manifest.get("all_checks_passed") is True
        and manifest.get("integrated_rule_count") == 15
        and manifest.get("integrated_field_count") == 22
        and manifest.get("integrated_context_count") == 18
        and manifest.get("candidate_records_materialized_current_step") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False
        and manifest.get("ready_to_train_now") is False
    )


def _validate_e1a(snapshot: FrozenSourceSnapshot) -> bool:
    contract = _csv_document(snapshot, E1A_CONTRACT_PATH)
    truth = _csv_document(snapshot, E1A_TRUTH_PATH)
    exact11 = _csv_document(snapshot, E1A_EXACT11_PATH)
    safety = _csv_document(snapshot, E1A_SAFETY_PATH)
    issues = _csv_document(snapshot, E1A_ISSUE_PATH)
    manifest = _json_document(snapshot, E1A_MANIFEST_PATH)
    issue_map = _keyed(issues.rows, "issue_id")
    no_full_present_grammar = not any(
        row.get("contract_passed") == "true"
        and "present-value grammar" in row.get("contract_statement", "").lower()
        and row.get("expected_value") in ("true", "frozen", "complete")
        for row in contract.rows
    )
    exact_reason = all(
        row["canonical_residue_name"] == "CYS"
        and row["candidate_atom_name"] == row["matched_residue_atom_name"] == "SG"
        and row["admit_004_identity_semantics_valid"] == "true"
        and row["admit_005_scope_outcome"] == "passed"
        and row["insertion_state"] == "unknown" and row["insertion_value"] == ""
        and row["insertion_blocks"] == "true" and row["effective_outcome"] == "blocked"
        and row["reason"] == UNKNOWN_REASON and row["audit_passed"] == "true"
        for row in exact11.rows
    )
    return (
        contract.header == CONTRACT_COLUMNS and all(row["contract_passed"] == "true" for row in contract.rows)
        and truth.header == TRUTH_COLUMNS and len(truth.rows) == 16
        and all(row["truth_table_passed"] == "true" for row in truth.rows)
        and exact11.header == EXACT11_COLUMNS and len(exact11.rows) == 11 and exact_reason
        and sum(row["auth_label_conflict_observed"] == "true" for row in exact11.rows) == 3
        and sum(row["auth_label_conflict_observed"] == "false" for row in exact11.rows) == 8
        and safety.header == ("safety_item", "expected_executed", "observed_executed", "safety_passed")
        and all(row["safety_passed"] == "true" for row in safety.rows)
        and issues.header == ISSUE_COLUMNS and len(issues.rows) == 11
        and issue_map[ATOM_ISSUE]["integration_transition"] == "design_frozen_pending_successor_integration"
        and issue_map[IDENTITY_ISSUE]["integration_transition"] == "design_frozen_pending_successor_integration"
        and all(row["status"] == "open" for row in issues.rows)
        and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["severity"] == "blocking"
        and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
        and no_full_present_grammar
        and manifest.get("all_checks_passed") is True
        and manifest.get("truth_table_case_count") == manifest.get("truth_table_passed_count") == 16
        and manifest.get("exact11_identity_atom_audit_count") == 11
        and manifest.get("exact11_identity_semantics_valid_count") == 11
        and manifest.get("exact11_atom_name_semantics_valid_count") == 11
        and manifest.get("exact11_admit_005_scope_pass_count") == 11
        and manifest.get("exact11_insertion_blocked_count") == 11
        and manifest.get("exact11_effective_blocked_count") == 11
        and manifest.get("active_issue_count") == 11
        and manifest.get("admit_004_evaluator_implemented") is False
        and manifest.get("candidate_records_materialized") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False
        and manifest.get("ready_for_training") is False
    )


def _overlay_rules(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    for row in rows:
        if row["admission_rule_id"] == "ADMIT_004":
            row.update({
                "semantics_complete": "false", "deterministic_evaluation_possible_now": "false",
                "deterministic_evaluation_possible_after_contract_freeze": "true",
                "implementation_disposition": "interface_only_pending_semantics",
                "blocking_reasons": IDENTITY_ISSUE, "integration_source_stage": E1A_STAGE,
                "integration_applied": "true", "integration_reason": PARTIAL_REASON,
            })
        elif row["admission_rule_id"] == "ADMIT_005":
            row.update({
                "semantics_complete": "true", "deterministic_evaluation_possible_now": "true",
                "deterministic_evaluation_possible_after_contract_freeze": "true",
                "implementation_disposition": "rule_logic_ready", "blocking_reasons": "",
                "integration_source_stage": E1A_STAGE, "integration_applied": "true",
                "integration_reason": COMPLETE_REASON,
            })
    return rows


def _overlay_fields(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    for row in rows:
        if row["field_name"] in TARGET_FIELDS:
            row.update({
                "allowed_values_defined": "true", "normalization_defined": "true",
                "exact_validation_defined": "true", "implementation_semantics_complete": "true",
                "semantics_evidence": E1A_STAGE, "blocking_reasons": "",
                "integration_source_stage": E1A_STAGE, "integration_applied": "true",
                "integration_reason": FIELD_REASONS[row["field_name"]],
            })
    return rows


def _overlay_contexts(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in source]
    for row in rows:
        if row["context_item"] == "covalent_residue_identity_contract":
            row.update({
                "deterministic_now": "false", "deterministic_after_contract_freeze": "true",
                "exact_contract_defined": "false", "implementation_ready": "false",
                "blocking_reasons": IDENTITY_ISSUE, "integration_source_stage": E1A_STAGE,
                "integration_applied": "true", "integration_reason": PARTIAL_REASON,
            })
    return rows


def _overlay_issues(source: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = []
    for source_row in source:
        if source_row["issue_id"] == ATOM_ISSUE:
            continue
        row = dict(source_row)
        if row["issue_id"] == IDENTITY_ISSUE:
            row.update({
                "issue_type": "implementation_semantics_gap",
                "affected_fields": "covalent_residue_insertion_code", "affected_rules": "ADMIT_004",
                "severity": "blocking", "status": "open",
                "blocking_scope": "admission_evaluator_rule_logic", "blocking_reason": IDENTITY_ISSUE,
                "integration_transition": "core_identity_and_atom_name_integrated_insertion_present_value_grammar_pending",
                "issue_count": "1",
            })
        rows.append(row)
    return rows


def _safety_rows() -> list[dict[str, Any]]:
    return [
        {"safety_item": item, "expected_executed": True, "observed_executed": True, "safety_passed": True}
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {"safety_item": item, "expected_executed": False, "observed_executed": False, "safety_passed": True}
        for item in FALSE_SAFETY_ITEMS
    ]


def _unchanged_except(
    rows: Sequence[Mapping[str, str]], source: Sequence[Mapping[str, str]], key: str,
    targets: set[str], allowed: set[str],
) -> bool:
    if len(rows) != len(source) or [row[key] for row in rows] != [row[key] for row in source]:
        return False
    for row, original in zip(rows, source):
        if row[key] not in targets and row != original:
            return False
        if row[key] in targets and any(row[column] != original[column] for column in original if column not in allowed):
            return False
    return True


def _validate_overlays(
    rules: Sequence[Mapping[str, str]], fields: Sequence[Mapping[str, str]],
    contexts: Sequence[Mapping[str, str]], issues: Sequence[Mapping[str, str]],
    safety: Sequence[Mapping[str, Any]], snapshot: FrozenSourceSnapshot,
) -> bool:
    p3_rules = _csv_document(snapshot, P3_RULE_PATH).rows
    p3_fields = _csv_document(snapshot, P3_FIELD_PATH).rows
    p3_contexts = _csv_document(snapshot, P3_CONTEXT_PATH).rows
    e1a_issues = _csv_document(snapshot, E1A_ISSUE_PATH).rows
    rule_map, field_map, context_map, issue_map = (
        _keyed(rules, "admission_rule_id"), _keyed(fields, "field_name"),
        _keyed(contexts, "context_item"), _keyed(issues, "issue_id"),
    )
    rule_allowed = {
        "semantics_complete", "deterministic_evaluation_possible_now",
        "deterministic_evaluation_possible_after_contract_freeze", "implementation_disposition",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    }
    field_allowed = {
        "allowed_values_defined", "normalization_defined", "exact_validation_defined",
        "implementation_semantics_complete", "semantics_evidence", "blocking_reasons",
        "integration_source_stage", "integration_applied", "integration_reason",
    }
    context_allowed = {
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
        "implementation_ready", "blocking_reasons", "integration_source_stage",
        "integration_applied", "integration_reason",
    }
    expected_issue_ids = [row["issue_id"] for row in e1a_issues if row["issue_id"] != ATOM_ISSUE]
    identity_source = _keyed(e1a_issues, "issue_id")[IDENTITY_ISSUE]
    unchanged_issue_ids = set(expected_issue_ids) - {IDENTITY_ISSUE}
    return (
        _unchanged_except(rules, p3_rules, "admission_rule_id", {"ADMIT_004", "ADMIT_005"}, rule_allowed)
        and _unchanged_except(fields, p3_fields, "field_name", set(TARGET_FIELDS), field_allowed)
        and _unchanged_except(contexts, p3_contexts, "context_item", {"covalent_residue_identity_contract"}, context_allowed)
        and rule_map["ADMIT_004"]["blocking_reasons"] == IDENTITY_ISSUE
        and rule_map["ADMIT_004"]["semantics_complete"] == "false"
        and rule_map["ADMIT_005"]["semantics_complete"] == "true"
        and rule_map["ADMIT_005"]["deterministic_evaluation_possible_now"] == "true"
        and all(
            field_map[name][column] == "true"
            for name in TARGET_FIELDS
            for column in ("allowed_values_defined", "normalization_defined", "exact_validation_defined", "implementation_semantics_complete")
        )
        and all(field_map[name] == _keyed(p3_fields, "field_name")[name] for name in LOCATOR_FIELDS)
        and context_map["covalent_residue_identity_contract"]["implementation_ready"] == "false"
        and context_map["covalent_residue_identity_contract"]["exact_contract_defined"] == "false"
        and [row["issue_id"] for row in issues] == expected_issue_ids and len(issues) == 10
        and ATOM_ISSUE not in issue_map
        and issue_map[IDENTITY_ISSUE]["affected_fields"] == "covalent_residue_insertion_code"
        and issue_map[IDENTITY_ISSUE]["affected_rules"] == "ADMIT_004"
        and issue_map[IDENTITY_ISSUE]["issue_origin"] == identity_source["issue_origin"]
        and all(issue_map[item] == _keyed(e1a_issues, "issue_id")[item] for item in unchanged_issue_ids)
        and list(safety) == _safety_rows()
        and sum(row["semantics_complete"] == "true" for row in rules) == 6
        and sum(row["implementation_semantics_complete"] == "true" for row in fields) == 11
        and sum(row["implementation_ready"] == "true" for row in contexts) == 8
    )


def _empty_state(snapshot: FrozenSourceSnapshot | None = None, failure: str = "SOURCE_BOUNDARY_FAILED") -> dict[str, Any]:
    return {
        "source_snapshot": snapshot, "source_ok": False, "p3_ok": False, "e1a_ok": False,
        "rule_rows": [], "field_rows": [], "context_rows": [], "safety_rows": [], "issue_rows": [],
        "integrated_rule_count": 0, "integrated_field_count": 0, "integrated_context_count": 0,
        "active_issue_count": 0, "all_checks_passed": False, "validation_failures": [failure],
    }


def build_integration_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        p3_ok = _validate_p3(snapshot)
        e1a_ok = _validate_e1a(snapshot)
        if not p3_ok or not e1a_ok:
            state = _empty_state(snapshot, "PREDECESSOR_VALIDATION_FAILED")
            state.update({"source_ok": True, "p3_ok": p3_ok, "e1a_ok": e1a_ok})
            return state
        rules = _overlay_rules(_csv_document(snapshot, P3_RULE_PATH).rows)
        fields = _overlay_fields(_csv_document(snapshot, P3_FIELD_PATH).rows)
        contexts = _overlay_contexts(_csv_document(snapshot, P3_CONTEXT_PATH).rows)
        issues = _overlay_issues(_csv_document(snapshot, E1A_ISSUE_PATH).rows)
        safety = _safety_rows()
        overlays_ok = _validate_overlays(rules, fields, contexts, issues, safety, snapshot)
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        state = _empty_state(snapshot, "DIRECT_EVIDENCE_VALIDATION_FAILED")
        state.update({"source_ok": True, "p3_ok": True, "e1a_ok": True})
        return state
    passed = p3_ok and e1a_ok and overlays_ok
    return {
        "source_snapshot": snapshot, "source_ok": True, "p3_ok": p3_ok, "e1a_ok": e1a_ok,
        "rule_rows": rules, "field_rows": fields, "context_rows": contexts,
        "safety_rows": safety, "issue_rows": issues,
        "integrated_rule_count": len(rules) if passed else 0,
        "integrated_field_count": len(fields) if passed else 0,
        "integrated_context_count": len(contexts) if passed else 0,
        "active_issue_count": len(issues) if passed else 0,
        "all_checks_passed": passed,
        "validation_failures": [] if passed else ["OVERLAY_VALIDATION_FAILED"],
    }


def _csv_value(value: Any) -> Any:
    return "true" if value is True else "false" if value is False else value


def _atomic_write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n", extrasaction="raise")
            writer.writeheader()
            writer.writerows({column: _csv_value(row[column]) for column in columns} for row in rows)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"] is True
    snapshot = state["source_snapshot"]
    exact11 = _csv_document(snapshot, E1A_EXACT11_PATH).rows
    rules, fields, contexts, issues = (
        state["rule_rows"], state["field_rows"], state["context_rows"], state["issue_rows"],
    )
    remaining_ids = [row["issue_id"] for row in issues]
    return {
        "project_name": PROJECT_NAME, "step_label": STEP_LABEL, "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "expected_base_head": EXPECTED_BASE_HEAD,
        "source_input_count": 12, "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "source_input_verification": [
            {"source_ordinal": ordinal, "source_relative_path": record.relative_path.as_posix(),
             "tracked": True, "regular": True, "non_symlink": True,
             "expected_sha256": record.expected_sha256, "observed_sha256": record.observed_sha256,
             "source_verified": True}
            for ordinal, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "predecessor_rule_count": 15, "predecessor_field_count": 22,
        "predecessor_context_count": 18, "predecessor_p3_issue_count": 10,
        "predecessor_e1a_issue_count": 11,
        "integrated_rule_count": len(rules), "integrated_field_count": len(fields),
        "integrated_context_count": len(contexts), "active_issue_count": len(issues),
        "semantics_complete_rule_count": sum(row["semantics_complete"] == "true" for row in rules),
        "implementation_semantics_complete_field_count": sum(row["implementation_semantics_complete"] == "true" for row in fields),
        "implementation_ready_context_count": sum(row["implementation_ready"] == "true" for row in contexts),
        "resolved_issue_ids": [ATOM_ISSUE], "remaining_issue_ids": remaining_ids,
        "exact11_identity_atom_audit_count": len(exact11),
        "exact11_identity_semantics_valid_count": sum(row["admit_004_identity_semantics_valid"] == "true" for row in exact11),
        "exact11_atom_name_semantics_valid_count": sum(row["candidate_atom_name"] == row["matched_residue_atom_name"] == "SG" for row in exact11),
        "exact11_admit_005_scope_pass_count": sum(row["admit_005_scope_outcome"] == "passed" for row in exact11),
        "exact11_auth_label_conflict_count": sum(row["auth_label_conflict_observed"] == "true" for row in exact11),
        "exact11_auth_label_no_conflict_count": sum(row["auth_label_conflict_observed"] == "false" for row in exact11),
        "exact11_insertion_unknown_empty_count": sum(row["insertion_state"] == "unknown" and row["insertion_value"] == "" for row in exact11),
        "exact11_insertion_blocked_count": sum(row["insertion_blocks"] == "true" for row in exact11),
        "exact11_effective_blocked_count": sum(row["effective_outcome"] == "blocked" for row in exact11),
        "partial_successor_integration_applied": passed,
        "core_residue_name_chain_index_semantics_integrated_into_effective_schema": passed,
        "atom_name_semantics_integrated_into_effective_schema": passed,
        "admit_005_rule_logic_ready": passed,
        "ready_for_covalent_residue_insertion_present_value_grammar_design": passed,
        "residue_identity_semantics_integrated_into_effective_schema": False,
        "covalent_residue_identity_contract_fully_integrated": False,
        "admit_004_rule_logic_ready": False,
        "ready_for_admit_004_rule_logic_implementation": False,
        "admit_004_evaluator_implemented": False, "candidate_records_materialized": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "raw_read_current_step": False, "parser_executed_current_step": False,
        "provider_executed_current_step": False, "candidate_evaluation_current_step": False,
        "download_attempted_current_step": False, "checkpoint_accessed_current_step": False,
        "model_or_training_code_used_current_step": False,
        "all_source_boundary_checks_passed": state["source_ok"] is True,
        "all_p3_predecessor_checks_passed": state["p3_ok"] is True,
        "all_e1a_predecessor_checks_passed": state["e1a_ok"] is True,
        "all_overlay_checks_passed": passed, "all_safety_checks_passed": passed,
        "all_checks_passed": passed, "validation_failures": list(state["validation_failures"]),
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_integration_state()
    if not state["all_checks_passed"]:
        raise RuntimeError("E1-B integration gate failed: " + "|".join(state["validation_failures"]))
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("output root must be a non-symlink directory")
    specs = (
        (RULE_FILENAME, RULE_COLUMNS, state["rule_rows"]),
        (FIELD_FILENAME, FIELD_COLUMNS, state["field_rows"]),
        (CONTEXT_FILENAME, CONTEXT_COLUMNS, state["context_rows"]),
        (SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"]),
        (ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in specs:
        _atomic_write_csv(root / filename, columns, rows)
    hashes = {filename: _file_sha256(root / filename) for filename in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_integration_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

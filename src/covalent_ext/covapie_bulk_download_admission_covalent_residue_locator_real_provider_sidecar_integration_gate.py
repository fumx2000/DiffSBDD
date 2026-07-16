"""Step14AU-E0-P6-D real-provider sidecar value-integration gate.

This gate joins the frozen exact11 P6-C sidecar to the frozen P6-A binding
identity layer and emits an additive six-column value overlay.  It never
dereferences raw or sample-artifact paths and never materializes admission
candidate records.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Sequence


STEP_LABEL = "Step14AU-E0-P6-D"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_sidecar_integration_gate_v1"
)
PROJECT_NAME = "CovaPIE"
EXPECTED_BASE_HEAD = "4958f9124dd831cccc3a1a22b981764f279e85d7"
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_real_provider_sidecar_"
    "integration_gate_v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_admit_004_residue_identity_and_atom_name_semantics_resolution_v1"
)
BLOCKED_NEXT_STEP = "resolve_covapie_real_provider_sidecar_integration_gate_blockers"
RESOLVED_PREDECESSOR_ISSUE_ID = (
    "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA"
)
ACTIVE_PROVIDER_ISSUE_ID = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
UNKNOWN_REASON = "COVALENT_RESIDUE_INSERTION_CODE_PROVENANCE_UNKNOWN"
REPO_ROOT = Path(__file__).resolve().parents[2]

P2_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_design_gate.py"
)
P3_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_integration_gate.py"
)
P4_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate.py"
)
P6A_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate.py"
)
P6C_MODULE_PATH = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke.py"
)

P3_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_minimal_schema_extension_integration_gate_v1"
)
P6A_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
)
P6C_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_provider_export_execution_smoke_v1"
)

P3_RULE_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_rule_matrix.csv"
P3_FIELD_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_field_matrix.csv"
P3_CONTEXT_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_integrated_context_matrix.csv"
P3_SAFETY_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_integration_safety_audit.csv"
P3_ISSUE_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_integration_issue_inventory.csv"
P3_MANIFEST_PATH = P3_ROOT / "covapie_covalent_residue_locator_schema_extension_integration_manifest.json"
P6A_BINDING_PATH = P6A_ROOT / "covapie_covalent_residue_locator_real_sample_binding_matrix.csv"
P6A_MANIFEST_PATH = P6A_ROOT / "covapie_covalent_residue_locator_real_parser_provider_pipeline_integration_design_manifest.json"
P6C_CONTRACT_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_execution_contract.csv"
P6C_SIDECAR_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
P6C_EVIDENCE_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_execution_evidence_audit.csv"
P6C_SAFETY_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_safety_audit.csv"
P6C_ISSUE_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_issue_inventory.csv"
P6C_MANIFEST_PATH = P6C_ROOT / "covapie_covalent_residue_locator_real_provider_export_execution_manifest.json"

SOURCE_PATHS = (
    P2_MODULE_PATH,
    P3_MODULE_PATH,
    P4_MODULE_PATH,
    P3_RULE_PATH,
    P3_FIELD_PATH,
    P3_CONTEXT_PATH,
    P3_SAFETY_PATH,
    P3_ISSUE_PATH,
    P3_MANIFEST_PATH,
    P6A_MODULE_PATH,
    P6A_BINDING_PATH,
    P6A_MANIFEST_PATH,
    P6C_MODULE_PATH,
    P6C_CONTRACT_PATH,
    P6C_SIDECAR_PATH,
    P6C_EVIDENCE_PATH,
    P6C_SAFETY_PATH,
    P6C_ISSUE_PATH,
    P6C_MANIFEST_PATH,
)
SOURCE_SHA256 = {
    P2_MODULE_PATH: "abe6f364f0cc0297e2695f42753885e45aaf10580e4ed42deab62a39676be079",
    P3_MODULE_PATH: "fcf3c3ede7db23dd131a8bdc7b06eff8b3936326ebbff6701a270694325c2286",
    P4_MODULE_PATH: "b1a874e402180a361b6940541c95710797ed10cabfdb19f7426c0b04d0532537",
    P3_RULE_PATH: "c1ae6cf9c2ca5450315ff3e3ed21b0a81d8bfc08c6a07e35d3f2dca1874e0d2f",
    P3_FIELD_PATH: "53dccd0ff7b20465c9df13f2c9eefc254f39bcb40e30732d1cfdfa4036e888fb",
    P3_CONTEXT_PATH: "8eac50078260e0567f6a99024d04ac92b512a0be10d2dcb66a4fa6dab52d1ef8",
    P3_SAFETY_PATH: "4eaca47e07fd58dfdf2c1d05e8fb26083b013f0abcb2944e0950b8e967aba49b",
    P3_ISSUE_PATH: "80954e517a2425c3a5659114d08999b59aed2410be9f1af0f43eef79c22dbedd",
    P3_MANIFEST_PATH: "676fe3c86e1304ba4971862d1e270fed40d9665e16c356d719627538aa28ee44",
    P6A_MODULE_PATH: "7d43c30f87b3e4c8a44d27b63ec51ba63307dcf23c16571be1d562d0b737c650",
    P6A_BINDING_PATH: "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
    P6A_MANIFEST_PATH: "cc3f824bb196847fcb175589e4682e2d39037177eb3564629498ae004ae7816e",
    P6C_MODULE_PATH: "5df4288eff9475ae6017fb57049a19790b6c278cfcb9a6eb22071ddef6c176b8",
    P6C_CONTRACT_PATH: "82f3f225cb2e18ba19ff386e612670279ebcdf4a0435b7b4642ff8167ccb09b7",
    P6C_SIDECAR_PATH: "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    P6C_EVIDENCE_PATH: "4048efdfe373fe955995ded43639fcbd7baf67560e867662dbd18fe22a4fb1ab",
    P6C_SAFETY_PATH: "e7736e3567d6ef76d19b13f46741f297000ea130644dd8b8b4b653b9a04bc6dc",
    P6C_ISSUE_PATH: "5bda40b683d649fb28a2172291f329c1f87d10f3a2bd122e1d5a6ab887a071c4",
    P6C_MANIFEST_PATH: "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
}

P2_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_design_gate"
)
P4_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_design_gate"
)
FORBIDDEN_RUNTIME_MODULE_NAMES = (
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "minimal_schema_extension_integration_gate",
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate",
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "real_raw_source_precondition_gate",
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "real_provider_export_execution_smoke",
    "covalent_ext.covapie_bulk_download_admission_covalent_residue_locator_"
    "parser_provider_provenance_export_smoke",
)
_MISSING_RUNTIME_MODULE = object()

DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
CONTRACT_FILENAME = "covapie_covalent_residue_locator_real_provider_sidecar_integration_contract.csv"
OVERLAY_FILENAME = "covapie_covalent_residue_locator_real_provider_integration_overlay.csv"
EVIDENCE_FILENAME = "covapie_covalent_residue_locator_real_provider_integration_evidence_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_real_provider_integration_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_real_provider_integration_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_locator_real_provider_sidecar_integration_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, OVERLAY_FILENAME, EVIDENCE_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

PROVIDER_FIELDS = (
    "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state",
    "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256",
)
OVERLAY_COLUMNS = ("binding_row_id", *PROVIDER_FIELDS)
EVIDENCE_COLUMNS = (
    "integration_evidence_row_id", "binding_row_id", "source_pipeline",
    "sample_preparation_input_id", "sample_execution_id", "pdb_id",
    "ligand_comp_id", "conn_id", "smoke_case_id", "residue_partner_side",
    "locator_namespace", "auth_label_conflict_observed", "matched_atom_site_id",
    "matched_residue_atom_name", "expected_raw_sha256", "observed_raw_sha256",
    "provider_export_status", "provider_export_blocking_reason", "insertion_state",
    "insertion_value", "insertion_blocks_admit_004",
    "expected_provenance_source_id", "observed_provenance_source_id",
    "provenance_source_id_matches", "expected_provenance_sha256",
    "observed_provenance_sha256", "provenance_sha256_matches",
    "provider_five_fields_match", "integration_status",
    "integration_blocking_reason", "evidence_audit_passed",
)
CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "requirement", "expected_value",
    "observed_value", "contract_passed", "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)

EXPECTED_BINDING_COLUMNS = (
    "binding_row_id", "source_pipeline", "sample_preparation_input_id",
    "sample_execution_id", "pdb_id", "ligand_comp_id", "conn_id",
    "covalent_residue_name", "selected_residue_chain_id",
    "selected_residue_index", "selected_residue_atom_name",
    "raw_target_relative_path", "sample_artifact_root",
    "covalent_event_table_relative_path",
    "ligand_residue_atom_pair_table_relative_path", "metadata_join_status",
    "raw_path_persisted", "conn_id_persisted", "residue_locator_hint_persisted",
    "partner_side_requires_raw_reparse", "namespace_evidence_requires_raw_reparse",
    "insertion_evidence_requires_raw_reparse",
    "matched_atom_site_row_requires_raw_reparse",
    "real_export_execution_allowed_current_step", "binding_status",
    "blocking_reason",
)
EXPECTED_SIDECAR_COLUMNS = (
    "binding_row_id", "source_pipeline", "sample_execution_id",
    "raw_target_relative_path", "expected_raw_sha256", "observed_raw_sha256",
    "raw_source_precondition_status", "raw_source_precondition_blocking_reason",
    "smoke_case_id", "sample_preparation_input_id", "pdb_id", "conn_id",
    "residue_partner_side", "locator_namespace",
    "struct_conn_residue_auth_asym_id", "struct_conn_residue_auth_seq_id",
    "struct_conn_residue_label_asym_id", "struct_conn_residue_label_seq_id",
    "selected_chain_id", "selected_residue_index", "auth_label_conflict_observed",
    "matched_atom_site_id", "matched_residue_atom_name",
    "struct_conn_insertion_source_tag", "struct_conn_insertion_raw_value",
    "struct_conn_token_class", "atom_site_insertion_source_tag",
    "atom_site_insertion_raw_value", "atom_site_token_class",
    "resolved_insertion_state", "resolved_insertion_value",
    "insertion_evidence_agreement", "insertion_blocks_admit_004",
    "insertion_blocking_reason", *PROVIDER_FIELDS, "provider_export_status",
    "provider_export_blocking_reason",
)
EXPECTED_P6C_EVIDENCE_COLUMNS = (
    "execution_evidence_row_id", "binding_row_id", "smoke_case_id", "pdb_id",
    "ligand_comp_id", "raw_target_relative_path", "expected_raw_sha256",
    "observed_raw_sha256", "expected_raw_size_bytes", "observed_raw_size_bytes",
    "raw_secure_read_status", "strict_decode_status", "struct_conn_parse_status",
    "struct_conn_row_count", "selected_struct_conn_row_ordinal_1based",
    "selected_struct_conn_match_count", "residue_partner_side",
    "locator_namespace", "atom_site_parse_status", "atom_site_row_count",
    "selected_atom_site_row_ordinal_1based", "selected_atom_site_match_count",
    "provider_export_status", "provider_export_blocking_reason",
    "evidence_audit_passed",
)
VALID_SHA256 = re.compile(r"[0-9a-f]{64}")
ADMIT_004_DEPENDENCIES = (
    "covalent_residue_name|covalent_residue_chain_id|covalent_residue_index|"
    "covalent_residue_atom_name|" + "|".join(PROVIDER_FIELDS)
)
ADMIT_004_BLOCKERS = (
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED|"
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED"
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


def _git(args: Sequence[str], repo_root: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo_root, text=True, capture_output=True,
        check=False,
    )


def _safe_source_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.as_posix() == str(path)
    )


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_source_path(path):
        return False
    full = repo_root / path
    try:
        value = os.lstat(full)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    return (
        tracked.returncode == 0 and stat.S_ISREG(value.st_mode)
        and not stat.S_ISLNK(value.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT) -> FrozenSourceSnapshot:
    """Validate all 19 structures before reading the first source byte."""
    if tuple(SOURCE_SHA256) != SOURCE_PATHS or len(SOURCE_PATHS) != 19:
        raise ValueError("source boundary shape invalid")
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        content = (repo_root / path).read_bytes()
        observed = hashlib.sha256(content).hexdigest()
        expected = SOURCE_SHA256[path]
        if observed != expected:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, expected, observed, content))
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(snapshot: object) -> bool:
    return (
        type(snapshot) is FrozenSourceSnapshot
        and len(snapshot.records) == 19
        and tuple(record.relative_path for record in snapshot.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.observed_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
            for record in snapshot.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    matches = [item for item in snapshot.records if item.relative_path == path]
    if len(matches) != 1:
        raise ValueError(f"missing frozen source: {path}")
    return matches[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError(f"invalid CSV header: {path}")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"invalid CSV row: {path}")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError(f"invalid JSON object: {path}")
    return value


def _snapshot_sha(snapshot: FrozenSourceSnapshot, path: Path) -> str:
    return _record(snapshot, path).observed_sha256


def _bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("non-canonical boolean")


def _validate_output_hashes(
    snapshot: FrozenSourceSnapshot,
    manifest: Mapping[str, Any],
    root: Path,
    non_manifest_paths: Sequence[Path],
    manifest_path: Path,
) -> bool:
    names = [path.name for path in non_manifest_paths] + [manifest_path.name]
    return (
        manifest.get("output_files") == names
        and manifest.get("output_file_count") == len(names)
        and manifest.get("output_sha256")
        == {path.name: _snapshot_sha(snapshot, path) for path in non_manifest_paths}
        and all(path.parent == root for path in (*non_manifest_paths, manifest_path))
    )


def validate_p3_predecessor(snapshot: FrozenSourceSnapshot) -> tuple[bool, dict[str, Any]]:
    try:
        rules = _csv_document(snapshot, P3_RULE_PATH)
        fields = _csv_document(snapshot, P3_FIELD_PATH)
        contexts = _csv_document(snapshot, P3_CONTEXT_PATH)
        safety = _csv_document(snapshot, P3_SAFETY_PATH)
        issues = _csv_document(snapshot, P3_ISSUE_PATH)
        manifest = _json_document(snapshot, P3_MANIFEST_PATH)
        field_by_name = {row["field_name"]: row for row in fields.rows}
        admit = [row for row in rules.rows if row.get("admission_rule_id") == "ADMIT_004"]
        target_fields = [field_by_name.get(name) for name in PROVIDER_FIELDS]
        p3_outputs = (P3_RULE_PATH, P3_FIELD_PATH, P3_CONTEXT_PATH, P3_SAFETY_PATH, P3_ISSUE_PATH)
        valid = (
            _validate_output_hashes(snapshot, manifest, P3_ROOT, p3_outputs, P3_MANIFEST_PATH)
            and manifest.get("stage")
            == "covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate_v1"
            and manifest.get("step_label") == "Step14AU-E0-P3"
            and manifest.get("all_checks_passed") is True
            and manifest.get("validation_failures") == []
            and manifest.get("integrated_field_count") == 22
            and manifest.get("integrated_rule_count") == 15
            and manifest.get("integrated_context_count") == 18
            and manifest.get("candidate_records_materialized_current_step") is False
            and manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
            and len(fields.rows) == 22 and len(field_by_name) == 22
            and len(rules.rows) == 15 and len(contexts.rows) == 18
            and len(target_fields) == 5 and all(row is not None for row in target_fields)
            and all(
                row["candidate_record_field"] == "true"
                and row["producer_scope"] == "candidate_metadata_provider"
                and row["dependent_rules"] == "ADMIT_004"
                and row["integration_applied"] == "true"
                and row["field_contract_mapping_passed"] == "true"
                for row in target_fields if row is not None
            )
            and field_by_name[PROVIDER_FIELDS[0]]["allowed_values_defined"] == "true"
            and "auth or label" in field_by_name[PROVIDER_FIELDS[0]]["source_value_contract"]
            and field_by_name[PROVIDER_FIELDS[1]]["allowed_values_defined"] == "true"
            and "absent, present, or unknown" in field_by_name[PROVIDER_FIELDS[1]]["source_value_contract"]
            and field_by_name[PROVIDER_FIELDS[3]]["exact_validation_defined"] == "true"
            and field_by_name[PROVIDER_FIELDS[4]]["exact_validation_defined"] == "true"
            and len(admit) == 1
            and admit[0]["candidate_field_dependencies"] == ADMIT_004_DEPENDENCIES
            and admit[0]["blocking_reasons"] == ADMIT_004_BLOCKERS
            and admit[0]["semantics_complete"] == "false"
            and len(issues.rows) == 10
            and all(row["severity"] == "blocking" and row["status"] == "open" for row in issues.rows)
            and len(safety.rows) == 20
            and all(row["safety_passed"] == "true" for row in safety.rows)
        )
        return valid, {
            "rules": [dict(row) for row in rules.rows],
            "fields": [dict(row) for row in fields.rows],
            "contexts": [dict(row) for row in contexts.rows],
            "issues": [dict(row) for row in issues.rows],
            "manifest": manifest,
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return False, {}


def validate_p6a_target(snapshot: FrozenSourceSnapshot) -> tuple[bool, list[dict[str, str]]]:
    try:
        bindings = _csv_document(snapshot, P6A_BINDING_PATH)
        manifest = _json_document(snapshot, P6A_MANIFEST_PATH)
        ids = [row["binding_row_id"] for row in bindings.rows]
        prep_ids = [row["sample_preparation_input_id"] for row in bindings.rows]
        identities = [(row["pdb_id"], row["ligand_comp_id"]) for row in bindings.rows]
        valid = (
            bindings.header == EXPECTED_BINDING_COLUMNS
            and len(bindings.rows) == 11
            and ids == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
            and len(set(ids)) == len(set(prep_ids)) == len(set(identities)) == 11
            and [row["source_pipeline"] for row in bindings.rows[:3]]
            == ["historical_sample_preparation_execution_smoke_v0"] * 3
            and [row["source_pipeline"] for row in bindings.rows[3:]]
            == ["independent_group_expansion_batch_sample_preparation_execution_smoke_v0"] * 8
            and all(row["metadata_join_status"] == "one_to_one_metadata_join_complete" for row in bindings.rows)
            and all(row["raw_path_persisted"] == "true" for row in bindings.rows)
            and all(row["conn_id_persisted"] == "true" for row in bindings.rows)
            and all(row["residue_locator_hint_persisted"] == "true" for row in bindings.rows)
            and all(row["covalent_residue_name"] == "CYS" for row in bindings.rows)
            and all(row["selected_residue_atom_name"] == "SG" for row in bindings.rows)
            and manifest.get("stage")
            == "covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
            and manifest.get("step_label") == "Step14AU-E0-P6-A"
            and manifest.get("all_checks_passed") is True
            and manifest.get("real_sample_binding_count") == 11
            and manifest.get("metadata_join_complete_count") == 11
            and manifest.get("output_sha256", {}).get(P6A_BINDING_PATH.name)
            == _snapshot_sha(snapshot, P6A_BINDING_PATH)
        )
        return valid, [dict(row) for row in bindings.rows]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return False, []


def validate_p6c_predecessor(snapshot: FrozenSourceSnapshot) -> tuple[bool, dict[str, Any]]:
    try:
        contract = _csv_document(snapshot, P6C_CONTRACT_PATH)
        sidecar = _csv_document(snapshot, P6C_SIDECAR_PATH)
        evidence = _csv_document(snapshot, P6C_EVIDENCE_PATH)
        safety = _csv_document(snapshot, P6C_SAFETY_PATH)
        issues = _csv_document(snapshot, P6C_ISSUE_PATH)
        manifest = _json_document(snapshot, P6C_MANIFEST_PATH)
        p6c_outputs = (P6C_CONTRACT_PATH, P6C_SIDECAR_PATH, P6C_EVIDENCE_PATH, P6C_SAFETY_PATH, P6C_ISSUE_PATH)
        ids = [row["binding_row_id"] for row in sidecar.rows]
        source_ids = [row[PROVIDER_FIELDS[3]] for row in sidecar.rows]
        provider_shas = [row[PROVIDER_FIELDS[4]] for row in sidecar.rows]
        issue_map = {row["issue_id"]: row for row in issues.rows}
        valid = (
            _validate_output_hashes(snapshot, manifest, P6C_ROOT, p6c_outputs, P6C_MANIFEST_PATH)
            and manifest.get("stage") == PREVIOUS_STAGE
            and manifest.get("step_label") == "Step14AU-E0-P6-C"
            and manifest.get("all_checks_passed") is True
            and manifest.get("validation_failures") == []
            and manifest.get("source_input_count") == 11
            and manifest.get("binding_count") == 11
            and manifest.get("secure_raw_read_count") == 11
            and manifest.get("strict_decode_count") == 11
            and manifest.get("struct_conn_parse_count") == 11
            and manifest.get("atom_site_parse_count") == 11
            and manifest.get("provider_call_count") == 11
            and manifest.get("sidecar_column_count") == 41
            and manifest.get("sidecar_row_count") == 11
            and manifest.get("evidence_audit_passed_count") == 11
            and manifest.get("provider_row_count") == 11
            and manifest.get("provenance_source_id_unique_count") == 11
            and manifest.get("provenance_sha_valid_count") == 11
            and manifest.get("provenance_sha_unique_count") == 11
            and manifest.get("exported_pass_count") == 0
            and manifest.get("exported_blocking_count") == 11
            and manifest.get("rejected_count") == 0
            and manifest.get("present_insertion_count") == 0
            and manifest.get("absent_insertion_count") == 0
            and manifest.get("unknown_insertion_count") == 11
            and manifest.get("ready_for_real_provider_sidecar_integration") is True
            and manifest.get("admission_records_modified_current_step") is False
            and manifest.get("real_samples_backfilled_current_step") == 0
            and all(manifest.get(key) is False for key in (
                "admit_004_rule_logic_ready",
                "ready_for_e1_residue_identity_semantics_design",
                "ready_for_real_candidate_evaluation", "ready_for_bulk_download_now",
                "ready_for_training", "ready_to_train_now",
            ))
            and contract.header == (
                "contract_item_id", "contract_area", "requirement", "expected_value",
                "observed_value", "contract_passed", "blocking_reason",
            )
            and len(contract.rows) == 32
            and all(row["contract_passed"] == "true" for row in contract.rows)
            and sidecar.header == EXPECTED_SIDECAR_COLUMNS and len(sidecar.rows) == 11
            and ids == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
            and len(set(ids)) == 11
            and evidence.header == EXPECTED_P6C_EVIDENCE_COLUMNS and len(evidence.rows) == 11
            and all(row["evidence_audit_passed"] == "true" for row in evidence.rows)
            and all(row["provider_export_status"] == "exported_blocking" for row in sidecar.rows)
            and all(row["provider_export_blocking_reason"] == UNKNOWN_REASON for row in sidecar.rows)
            and all(row["expected_raw_sha256"] == row["observed_raw_sha256"] for row in sidecar.rows)
            and all(row["expected_raw_sha256"] == row["observed_raw_sha256"] for row in evidence.rows)
            and len(source_ids) == len(set(source_ids)) == 11 and all(source_ids)
            and len(provider_shas) == len(set(provider_shas)) == 11
            and all(VALID_SHA256.fullmatch(value) for value in provider_shas)
            and len(safety.rows) == 19 and all(row["safety_passed"] == "true" for row in safety.rows)
            and set(issue_map) == {RESOLVED_PREDECESSOR_ISSUE_ID, ACTIVE_PROVIDER_ISSUE_ID}
            and issue_map[ACTIVE_PROVIDER_ISSUE_ID]["issue_count"] == "11"
        )
        return valid, {
            "sidecar": [dict(row) for row in sidecar.rows],
            "evidence": [dict(row) for row in evidence.rows],
            "manifest": manifest,
            "issues": [dict(row) for row in issues.rows],
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return False, {}


def _load_runtime_modules() -> tuple[ModuleType, ModuleType]:
    p2 = importlib.import_module(P2_RUNTIME_MODULE_NAME)
    p4 = importlib.import_module(P4_RUNTIME_MODULE_NAME)
    return p2, p4


def _snapshot_forbidden_runtime_modules() -> dict[str, object]:
    return {
        name: sys.modules.get(name, _MISSING_RUNTIME_MODULE)
        for name in FORBIDDEN_RUNTIME_MODULE_NAMES
    }


def _forbidden_runtime_module_delta(before: Mapping[str, object]) -> dict[str, int | bool]:
    new_import_count = 0
    replacement_count = 0
    deletion_count = 0
    for name in FORBIDDEN_RUNTIME_MODULE_NAMES:
        before_module = before.get(name, _MISSING_RUNTIME_MODULE)
        after_module = sys.modules.get(name, _MISSING_RUNTIME_MODULE)
        if before_module is _MISSING_RUNTIME_MODULE:
            new_import_count += int(after_module is not _MISSING_RUNTIME_MODULE)
        elif after_module is _MISSING_RUNTIME_MODULE:
            deletion_count += 1
        elif after_module is not before_module:
            replacement_count += 1
    return {
        "runtime_forbidden_module_delta_ok": (
            new_import_count == replacement_count == deletion_count == 0
        ),
        "runtime_forbidden_module_new_import_count": new_import_count,
        "runtime_forbidden_module_replacement_count": replacement_count,
        "runtime_forbidden_module_deletion_count": deletion_count,
    }


def _validate_runtime_module(
    module: ModuleType,
    expected_name: str,
    expected_path: Path,
    snapshot: FrozenSourceSnapshot,
    callables: Sequence[str],
) -> bool:
    try:
        module_file = Path(module.__file__).resolve(strict=True)
        expected_file = (REPO_ROOT / expected_path).resolve(strict=True)
        source_lstat = os.lstat(REPO_ROOT / expected_path)
        content = (REPO_ROOT / expected_path).read_bytes()
    except (AttributeError, OSError, TypeError):
        return False
    return (
        module.__name__ == expected_name and module_file == expected_file
        and stat.S_ISREG(source_lstat.st_mode) and not stat.S_ISLNK(source_lstat.st_mode)
        and content == _record(snapshot, expected_path).content_bytes
        and hashlib.sha256(content).hexdigest() == SOURCE_SHA256[expected_path]
        and all(callable(getattr(module, name, None)) for name in callables)
    )


def validate_runtime_modules(
    snapshot: FrozenSourceSnapshot, p2: ModuleType, p4: ModuleType,
) -> bool:
    return (
        _validate_runtime_module(
            p2, P2_RUNTIME_MODULE_NAME, P2_MODULE_PATH, snapshot,
            (
                "validate_covalent_residue_insertion_code",
                "normalize_covalent_residue_locator_namespace",
                "normalize_covalent_residue_locator_provenance_source_id",
                "validate_covalent_residue_locator_provenance_sha256",
            ),
        )
        and _validate_runtime_module(
            p4, P4_RUNTIME_MODULE_NAME, P4_MODULE_PATH, snapshot,
            (
                "build_locator_provider_export_fields",
                "build_locator_provenance_source_id",
                "build_canonical_locator_provenance_payload",
                "sha256_canonical_locator_provenance_payload",
            ),
        )
    )


def keyed_join_exact11(
    targets: Sequence[Mapping[str, str]],
    sidecar_rows: Sequence[Mapping[str, str]],
    evidence_rows: Sequence[Mapping[str, str]],
) -> tuple[list[tuple[dict[str, str], dict[str, str], dict[str, str]]], int]:
    expected_ids = [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]

    def unique_map(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for source in rows:
            row = dict(source)
            value = row.get(key, "")
            if not value or value in result:
                raise ValueError(f"duplicate or empty {key}")
            result[value] = row
        return result

    try:
        target_map = unique_map(targets, "binding_row_id")
        sidecar_map = unique_map(sidecar_rows, "binding_row_id")
        evidence_map = unique_map(evidence_rows, "binding_row_id")
    except (TypeError, ValueError):
        return [], 0
    expected = set(expected_ids)
    if set(target_map) != expected or set(sidecar_map) != expected or set(evidence_map) != expected:
        return [], 0
    joined: list[tuple[dict[str, str], dict[str, str], dict[str, str]]] = []
    matches = 0
    for binding_id in expected_ids:
        target, sidecar, evidence = target_map[binding_id], sidecar_map[binding_id], evidence_map[binding_id]
        primary_secondary = (
            target["binding_row_id"], target["source_pipeline"],
            target["sample_preparation_input_id"], target["sample_execution_id"],
            target["pdb_id"], target["conn_id"],
        ) == (
            sidecar["binding_row_id"], sidecar["source_pipeline"],
            sidecar["sample_preparation_input_id"], sidecar["sample_execution_id"],
            sidecar["pdb_id"], sidecar["conn_id"],
        )
        target_evidence = (
            target["binding_row_id"], target["pdb_id"], target["ligand_comp_id"],
            target["raw_target_relative_path"],
        ) == (
            evidence["binding_row_id"], evidence["pdb_id"], evidence["ligand_comp_id"],
            evidence["raw_target_relative_path"],
        )
        sidecar_evidence = (
            sidecar["smoke_case_id"], sidecar["expected_raw_sha256"],
            sidecar["observed_raw_sha256"], sidecar["provider_export_status"],
            sidecar["provider_export_blocking_reason"],
        ) == (
            evidence["smoke_case_id"], evidence["expected_raw_sha256"],
            evidence["observed_raw_sha256"], evidence["provider_export_status"],
            evidence["provider_export_blocking_reason"],
        )
        invariants = (
            primary_secondary and target_evidence and sidecar_evidence
            and sidecar["matched_residue_atom_name"] == target["selected_residue_atom_name"] == "SG"
            and sidecar["locator_namespace"] == sidecar[PROVIDER_FIELDS[0]]
            and sidecar["expected_raw_sha256"] == sidecar["observed_raw_sha256"]
            and evidence["evidence_audit_passed"] == "true"
        )
        if not invariants:
            return [], 0
        matches += 1
        joined.append((target, sidecar, evidence))
    return joined, matches


def recompute_integration_rows(
    joined: Sequence[tuple[Mapping[str, str], Mapping[str, str], Mapping[str, str]]],
    p2: ModuleType,
    p4: ModuleType,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
    overlays: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    recomputations = 0
    matches = 0
    try:
        for index, (target, sidecar, evidence) in enumerate(joined, 1):
            insertion = p2.validate_covalent_residue_insertion_code(
                sidecar[PROVIDER_FIELDS[1]], sidecar[PROVIDER_FIELDS[2]],
            )
            if not (
                insertion.schema_combination_valid and not insertion.passed
                and insertion.blocks_admit_004 and insertion.blocking_reason == UNKNOWN_REASON
                and sidecar[PROVIDER_FIELDS[1]] == "unknown"
                and sidecar[PROVIDER_FIELDS[2]] == ""
                and sidecar["insertion_blocks_admit_004"] == "true"
                and sidecar["insertion_blocking_reason"] == UNKNOWN_REASON
                and sidecar["provider_export_status"] == "exported_blocking"
                and sidecar["provider_export_blocking_reason"] == UNKNOWN_REASON
            ):
                raise ValueError("unknown insertion contract mismatch")
            provider = p4.build_locator_provider_export_fields(
                locator_namespace=sidecar["locator_namespace"],
                sample_preparation_input_id=sidecar["sample_preparation_input_id"],
                pdb_id=sidecar["pdb_id"], conn_id=sidecar["conn_id"],
                residue_partner_side=sidecar["residue_partner_side"],
                struct_conn_residue_auth_asym_id=sidecar["struct_conn_residue_auth_asym_id"],
                struct_conn_residue_auth_seq_id=sidecar["struct_conn_residue_auth_seq_id"],
                struct_conn_residue_label_asym_id=sidecar["struct_conn_residue_label_asym_id"],
                struct_conn_residue_label_seq_id=sidecar["struct_conn_residue_label_seq_id"],
                selected_chain_id=sidecar["selected_chain_id"],
                selected_residue_index=sidecar["selected_residue_index"],
                matched_atom_site_id=sidecar["matched_atom_site_id"],
                matched_residue_atom_name=sidecar["matched_residue_atom_name"],
                struct_conn_insertion_source_tag=sidecar["struct_conn_insertion_source_tag"],
                struct_conn_insertion_raw_value=sidecar["struct_conn_insertion_raw_value"],
                atom_site_insertion_source_tag=sidecar["atom_site_insertion_source_tag"],
                atom_site_insertion_raw_value=sidecar["atom_site_insertion_raw_value"],
            )
            expected_source = p4.build_locator_provenance_source_id(
                sidecar["sample_preparation_input_id"], sidecar["conn_id"],
                sidecar["residue_partner_side"],
            )
            payload = p4.build_canonical_locator_provenance_payload(
                **{
                    key: sidecar[key]
                    for key in p4.CANONICAL_PAYLOAD_KEYS
                    if key != "schema_version"
                }
            )
            expected_sha = p4.sha256_canonical_locator_provenance_payload(payload)
            recomputations += 1
            observed = {name: sidecar[name] for name in PROVIDER_FIELDS}
            five_match = provider == observed
            source_match = expected_source == sidecar[PROVIDER_FIELDS[3]]
            sha_match = expected_sha == sidecar[PROVIDER_FIELDS[4]]
            if not (five_match and source_match and sha_match):
                raise ValueError("provider recomputation mismatch")
            matches += 1
            overlays.append({"binding_row_id": target["binding_row_id"], **provider})
            audits.append({
                "integration_evidence_row_id": f"P6D_INTEGRATION_EVIDENCE_{index:06d}",
                "binding_row_id": target["binding_row_id"],
                "source_pipeline": target["source_pipeline"],
                "sample_preparation_input_id": target["sample_preparation_input_id"],
                "sample_execution_id": target["sample_execution_id"],
                "pdb_id": target["pdb_id"], "ligand_comp_id": target["ligand_comp_id"],
                "conn_id": target["conn_id"], "smoke_case_id": sidecar["smoke_case_id"],
                "residue_partner_side": sidecar["residue_partner_side"],
                "locator_namespace": sidecar["locator_namespace"],
                "auth_label_conflict_observed": sidecar["auth_label_conflict_observed"],
                "matched_atom_site_id": sidecar["matched_atom_site_id"],
                "matched_residue_atom_name": sidecar["matched_residue_atom_name"],
                "expected_raw_sha256": sidecar["expected_raw_sha256"],
                "observed_raw_sha256": sidecar["observed_raw_sha256"],
                "provider_export_status": sidecar["provider_export_status"],
                "provider_export_blocking_reason": sidecar["provider_export_blocking_reason"],
                "insertion_state": sidecar[PROVIDER_FIELDS[1]],
                "insertion_value": sidecar[PROVIDER_FIELDS[2]],
                "insertion_blocks_admit_004": sidecar["insertion_blocks_admit_004"],
                "expected_provenance_source_id": expected_source,
                "observed_provenance_source_id": sidecar[PROVIDER_FIELDS[3]],
                "provenance_source_id_matches": source_match,
                "expected_provenance_sha256": expected_sha,
                "observed_provenance_sha256": sidecar[PROVIDER_FIELDS[4]],
                "provenance_sha256_matches": sha_match,
                "provider_five_fields_match": five_match,
                "integration_status": "integrated_blocking",
                "integration_blocking_reason": UNKNOWN_REASON,
                "evidence_audit_passed": True,
            })
    except (AttributeError, KeyError, TypeError, ValueError):
        return [], [], 0, 0
    return overlays, audits, recomputations, matches


def validate_overlay_rows(rows: Sequence[Mapping[str, Any]], p2: ModuleType) -> bool:
    try:
        actual = [dict(row) for row in rows]
        ids = [row["binding_row_id"] for row in actual]
        source_ids = [row[PROVIDER_FIELDS[3]] for row in actual]
        shas = [row[PROVIDER_FIELDS[4]] for row in actual]
        return (
            len(actual) == 11 and all(tuple(row) == OVERLAY_COLUMNS for row in actual)
            and ids == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
            and len(set(ids)) == 11
            and all(row[PROVIDER_FIELDS[0]] == "auth" for row in actual)
            and all(row[PROVIDER_FIELDS[1]] == "unknown" for row in actual)
            and all(row[PROVIDER_FIELDS[2]] == "" for row in actual)
            and all(
                p2.validate_covalent_residue_insertion_code("unknown", "").schema_combination_valid
                for row in actual
            )
            and len(source_ids) == len(set(source_ids)) == 11 and all(source_ids)
            and len(shas) == len(set(shas)) == 11
            and all(VALID_SHA256.fullmatch(value) for value in shas)
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def validate_evidence_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    try:
        actual = [dict(row) for row in rows]
        return (
            len(actual) == 11 and all(tuple(row) == EVIDENCE_COLUMNS for row in actual)
            and [row["integration_evidence_row_id"] for row in actual]
            == [f"P6D_INTEGRATION_EVIDENCE_{index:06d}" for index in range(1, 12)]
            and [row["binding_row_id"] for row in actual]
            == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)]
            and all(row["integration_status"] == "integrated_blocking" for row in actual)
            and all(row["integration_blocking_reason"] == UNKNOWN_REASON for row in actual)
            and all(row["insertion_state"] == "unknown" and row["insertion_value"] == "" for row in actual)
            and all(row["insertion_blocks_admit_004"] == "true" for row in actual)
            and all(row["provider_export_status"] == "exported_blocking" for row in actual)
            and all(row["provider_export_blocking_reason"] == UNKNOWN_REASON for row in actual)
            and all(row["expected_raw_sha256"] == row["observed_raw_sha256"] for row in actual)
            and all(
                row["provenance_source_id_matches"] is True
                and row["provenance_sha256_matches"] is True
                and row["provider_five_fields_match"] is True
                and row["evidence_audit_passed"] is True
                for row in actual
            )
        )
    except (KeyError, TypeError, ValueError):
        return False


CONTRACT_SPECS = (
    ("source", "exact frozen source count", "19", "source_count"),
    ("source", "all source SHA256 exact", "19", "source_sha_count"),
    ("schema", "P3 effective schema validated", "true", "p3"),
    ("schema", "effective field rule context counts", "22|15|18", "p3_shape"),
    ("target", "P6-A target validated", "true", "p6a"),
    ("target", "exact target binding count", "11", "target_count"),
    ("predecessor", "P6-C direct predecessor validated", "true", "p6c"),
    ("predecessor", "P6-C sidecar and evidence counts", "11|11", "p6c_shape"),
    ("join", "explicit keyed joins", "11", "joins"),
    ("join", "secondary identity matches", "11", "identity_matches"),
    ("provider", "P4 provider provenance recomputations", "11", "recomputations"),
    ("provider", "provider five-field matches", "11", "provider_matches"),
    ("overlay", "overlay exact shape", "11x6", "overlay_shape"),
    ("evidence", "integration evidence passed", "11", "evidence_passed"),
    ("insertion", "unknown plus empty schema-valid integrations", "11", "unknown_valid"),
    ("insertion", "ADMIT_004 blocking overlay rows", "11", "blocking_rows"),
    ("boundary", "candidate records materialized", "false", "candidate_records"),
    ("boundary", "admission records modified", "false", "admission_modified"),
    ("boundary", "real samples backfilled", "0", "backfill"),
    ("readiness", "ADMIT_004 and E1 ready", "false|false", "admit_e1"),
    ("readiness", "candidate and bulk download ready", "false|false", "candidate_download"),
    ("readiness", "training readiness", "false|false", "training"),
)


def _contract_rows(observations: Mapping[str, str]) -> list[dict[str, Any]]:
    rows = []
    for index, (area, requirement, expected, key) in enumerate(CONTRACT_SPECS, 1):
        observed = observations.get(key, "")
        passed = observed == expected
        rows.append({
            "contract_item_id": f"P6D_C{index:03d}", "contract_area": area,
            "requirement": requirement, "expected_value": expected,
            "observed_value": observed, "contract_passed": passed,
            "blocking_reason": "" if passed else f"P6D_{area.upper()}_CONTRACT_FAILED",
        })
    return rows


def validate_contract_rows(rows: Sequence[Mapping[str, Any]], observations: Mapping[str, str]) -> bool:
    return [dict(row) for row in rows] == _contract_rows(observations) and all(
        row["contract_passed"] is True for row in rows
    )


TRUE_SAFETY_ITEMS = (
    "exact_source_reads", "p3_schema_validation", "keyed_integration_join",
    "p2_insertion_validation", "p4_provider_provenance_recomputation",
    "overlay_materialization",
)
FALSE_SAFETY_ITEMS = (
    "raw_read", "parser_execution", "raw_directory_scan", "raw_write",
    "network_access", "download", "admission_modification",
    "candidate_record_materialization", "sample_backfill", "checkpoint_access",
    "torch_imported", "numpy_imported", "model_forward", "loss_compute", "training",
)


def _safety_rows(execution: Mapping[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for item in TRUE_SAFETY_ITEMS:
        observed = execution.get(item, False)
        rows.append({
            "safety_item": item, "required_status": True, "observed_status": observed,
            "safety_passed": observed is True,
            "blocking_reason": "" if observed is True else f"{item.upper()}_NOT_COMPLETED",
        })
    for item in FALSE_SAFETY_ITEMS:
        observed = execution.get(item, False)
        rows.append({
            "safety_item": item, "required_status": False, "observed_status": observed,
            "safety_passed": observed is False,
            "blocking_reason": "" if observed is False else f"{item.upper()}_FORBIDDEN",
        })
    return rows


def _issue_rows(p3_issues: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = [{**dict(row), "issue_count": "1"} for row in p3_issues]
    rows.append({
        "issue_id": ACTIVE_PROVIDER_ISSUE_ID,
        "issue_type": "provider_export",
        "affected_fields": "covalent_residue_insertion_code_state|covalent_residue_insertion_code",
        "affected_rules": "ADMIT_004", "severity": "blocking", "status": "open",
        "blocking_scope": "admission_evaluator_rule_logic",
        "blocking_reason": ACTIVE_PROVIDER_ISSUE_ID,
        "issue_origin": PREVIOUS_STAGE, "integration_transition": "unchanged",
        "issue_count": "11",
    })
    return [{column: row[column] for column in ISSUE_COLUMNS} for row in rows]


def validate_issue_rows(rows: Sequence[Mapping[str, str]], p3_issues: Sequence[Mapping[str, str]]) -> bool:
    actual = [dict(row) for row in rows]
    return (
        actual == _issue_rows(p3_issues) and len(actual) == 11
        and all(row["status"] == "open" and row["severity"] == "blocking" for row in actual)
        and all(row["issue_id"] != RESOLVED_PREDECESSOR_ISSUE_ID for row in actual)
        and actual[-1]["issue_id"] == ACTIVE_PROVIDER_ISSUE_ID
        and actual[-1]["issue_count"] == "11"
    )


def _empty_state(source_snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    observations = {
        "source_count": "0", "source_sha_count": "0", "p3": "false",
        "p3_shape": "0|0|0", "p6a": "false", "target_count": "0",
        "p6c": "false", "p6c_shape": "0|0", "joins": "0",
        "identity_matches": "0", "recomputations": "0", "provider_matches": "0",
        "overlay_shape": "0x6", "evidence_passed": "0", "unknown_valid": "0",
        "blocking_rows": "0", "candidate_records": "false",
        "admission_modified": "false", "backfill": "0", "admit_e1": "false|false",
        "candidate_download": "false|false", "training": "false|false",
    }
    execution = {item: False for item in (*TRUE_SAFETY_ITEMS, *FALSE_SAFETY_ITEMS)}
    return {
        "source_snapshot": source_snapshot, "source_ok": False, "p3_ok": False,
        "p6a_ok": False, "p6c_ok": False, "runtime_modules_ok": False,
        "runtime_forbidden_module_delta_ok": False,
        "runtime_forbidden_module_new_import_count": 0,
        "runtime_forbidden_module_replacement_count": 0,
        "runtime_forbidden_module_deletion_count": 0,
        "joined_rows": [], "keyed_join_count": 0, "secondary_identity_match_count": 0,
        "overlay_rows": [], "evidence_rows": [], "p4_recomputation_count": 0,
        "provider_five_field_match_count": 0, "p3_source": {}, "p6c_source": {},
        "observations": observations, "contract_rows": _contract_rows(observations),
        "safety_rows": _safety_rows(execution), "issue_rows": [],
        "all_checks_passed": False, "validation_failures": ["SOURCE_BOUNDARY_FAILED"],
    }


def build_integration_state(
    *,
    source_snapshot: FrozenSourceSnapshot | None = None,
    runtime_modules: tuple[ModuleType, ModuleType] | None = None,
    module_loader: Callable[[], tuple[ModuleType, ModuleType]] = _load_runtime_modules,
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot()
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    p3_ok, p3_source = validate_p3_predecessor(snapshot)
    p6a_ok, targets = validate_p6a_target(snapshot)
    p6c_ok, p6c_source = validate_p6c_predecessor(snapshot)
    if not (p3_ok and p6a_ok and p6c_ok):
        state = _empty_state(snapshot)
        state.update({"source_ok": True, "p3_ok": p3_ok, "p6a_ok": p6a_ok, "p6c_ok": p6c_ok})
        state["validation_failures"] = [
            name for name, passed in (("P3_PREDECESSOR_FAILED", p3_ok), ("P6A_TARGET_FAILED", p6a_ok), ("P6C_PREDECESSOR_FAILED", p6c_ok))
            if not passed
        ]
        return state
    forbidden_before = _snapshot_forbidden_runtime_modules()
    try:
        p2, p4 = runtime_modules if runtime_modules is not None else module_loader()
    except (ImportError, RuntimeError):
        runtime_delta = _forbidden_runtime_module_delta(forbidden_before)
        state = _empty_state(snapshot)
        state.update({
            "source_ok": True, "p3_ok": True, "p6a_ok": True, "p6c_ok": True,
            **runtime_delta,
        })
        state["validation_failures"] = ["RUNTIME_MODULE_IMPORT_FAILED"]
        return state
    runtime_delta = _forbidden_runtime_module_delta(forbidden_before)
    runtime_ok = (
        bool(runtime_delta["runtime_forbidden_module_delta_ok"])
        and validate_runtime_modules(snapshot, p2, p4)
    )
    if not runtime_ok:
        state = _empty_state(snapshot)
        state.update({
            "source_ok": True, "p3_ok": True, "p6a_ok": True, "p6c_ok": True,
            **runtime_delta,
        })
        state["validation_failures"] = ["RUNTIME_MODULE_VALIDATION_FAILED"]
        return state
    joined, identity_matches = keyed_join_exact11(targets, p6c_source["sidecar"], p6c_source["evidence"])
    overlays, audits, recomputations, provider_matches = recompute_integration_rows(joined, p2, p4)
    overlay_ok = validate_overlay_rows(overlays, p2)
    evidence_ok = validate_evidence_rows(audits)
    observations = {
        "source_count": str(len(snapshot.records)), "source_sha_count": str(len(snapshot.records)),
        "p3": "true", "p3_shape": "22|15|18", "p6a": "true",
        "target_count": str(len(targets)), "p6c": "true",
        "p6c_shape": f"{len(p6c_source['sidecar'])}|{len(p6c_source['evidence'])}",
        "joins": str(len(joined)), "identity_matches": str(identity_matches),
        "recomputations": str(recomputations), "provider_matches": str(provider_matches),
        "overlay_shape": f"{len(overlays)}x{len(OVERLAY_COLUMNS)}",
        "evidence_passed": str(sum(row.get("evidence_audit_passed") is True for row in audits)),
        "unknown_valid": str(sum(row.get(PROVIDER_FIELDS[1]) == "unknown" and row.get(PROVIDER_FIELDS[2]) == "" for row in overlays)),
        "blocking_rows": str(sum(row.get("integration_status") == "integrated_blocking" for row in audits)),
        "candidate_records": "false", "admission_modified": "false", "backfill": "0",
        "admit_e1": "false|false", "candidate_download": "false|false",
        "training": "false|false",
    }
    contract = _contract_rows(observations)
    execution = {item: False for item in FALSE_SAFETY_ITEMS}
    execution.update({item: True for item in TRUE_SAFETY_ITEMS})
    safety = _safety_rows(execution)
    issues = _issue_rows(p3_source["issues"])
    checks = {
        "source": True, "p3": p3_ok, "p6a": p6a_ok, "p6c": p6c_ok,
        "runtime": runtime_ok, "join": len(joined) == identity_matches == 11,
        "provider": recomputations == provider_matches == 11,
        "overlay": overlay_ok, "evidence": evidence_ok,
        "contract": validate_contract_rows(contract, observations),
        "safety": all(row["safety_passed"] is True for row in safety),
        "issues": validate_issue_rows(issues, p3_source["issues"]),
    }
    failures = [f"{name.upper()}_FAILED" for name, passed in checks.items() if not passed]
    return {
        "source_snapshot": snapshot, "source_ok": True, "p3_ok": p3_ok,
        "p6a_ok": p6a_ok, "p6c_ok": p6c_ok, "runtime_modules_ok": runtime_ok,
        **runtime_delta,
        "runtime_module_names": (p2.__name__, p4.__name__), "targets": targets,
        "p3_source": p3_source, "p6c_source": p6c_source, "joined_rows": joined,
        "keyed_join_count": len(joined), "secondary_identity_match_count": identity_matches,
        "overlay_rows": overlays, "evidence_rows": audits,
        "p4_recomputation_count": recomputations,
        "provider_five_field_match_count": provider_matches,
        "observations": observations, "contract_rows": contract, "safety_rows": safety,
        "issue_rows": issues, "all_checks_passed": all(checks.values()),
        "validation_failures": failures,
    }


def _csv_value(value: Any) -> Any:
    if type(value) is bool:
        return "true" if value else "false"
    return value


def _ensure_output_root(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("output root must be a non-symlink directory")


def _atomic_write_csv(
    path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, Any]],
) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
            writer.writeheader()
            writer.writerows({column: _csv_value(row[column]) for column in columns} for row in rows)
            handle.flush()
            os.fsync(handle.fileno())
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
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_payload(state: Mapping[str, Any], output_sha256: Mapping[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"] is True
    overlay = state["overlay_rows"]
    evidence = state["evidence_rows"]
    source_ids = [row[PROVIDER_FIELDS[3]] for row in overlay]
    provider_shas = [row[PROVIDER_FIELDS[4]] for row in overlay]
    return {
        "project_name": PROJECT_NAME, "step_label": STEP_LABEL, "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE, "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_head": EXPECTED_BASE_HEAD,
        "source_input_count": len(SOURCE_PATHS),
        "source_input_sha256": {path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS},
        "output_files": list(OUTPUT_FILES), "output_file_count": len(OUTPUT_FILES),
        "output_sha256": dict(output_sha256),
        "all_checks_passed": passed, "validation_failures": list(state["validation_failures"]),
        "p3_schema_validated": state["p3_ok"] is True,
        "target_binding_count": len(state.get("targets", [])),
        "predecessor_sidecar_count": len(state.get("p6c_source", {}).get("sidecar", [])),
        "keyed_join_count": state["keyed_join_count"],
        "secondary_identity_match_count": state["secondary_identity_match_count"],
        "p4_recomputation_count": state["p4_recomputation_count"],
        "provider_five_field_match_count": state["provider_five_field_match_count"],
        "overlay_column_count": len(OVERLAY_COLUMNS), "overlay_row_count": len(overlay),
        "evidence_audit_passed_count": sum(row["evidence_audit_passed"] is True for row in evidence),
        "unknown_insertion_integrated_count": sum(row[PROVIDER_FIELDS[1]] == "unknown" and row[PROVIDER_FIELDS[2]] == "" for row in overlay),
        "admit_004_blocking_overlay_count": sum(row["integration_status"] == "integrated_blocking" for row in evidence),
        "provider_source_id_valid_count": sum(bool(value) for value in source_ids),
        "provider_source_id_unique_count": len(set(source_ids)),
        "provider_sha_valid_count": sum(VALID_SHA256.fullmatch(value) is not None for value in provider_shas),
        "provider_sha_unique_count": len(set(provider_shas)),
        "real_provider_sidecar_integration_gate_passed": passed,
        "real_provider_sidecar_integrated_into_additive_overlay": passed,
        "five_locator_fields_integrated_row_count": len(overlay) if passed else 0,
        "provider_provenance_available_count": len(overlay) if passed else 0,
        "candidate_records_materialized": False, "admission_records_modified": False,
        "real_samples_backfilled": 0, "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False, "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "resolved_predecessor_issue_ids": [RESOLVED_PREDECESSOR_ISSUE_ID] if passed else [],
        "active_issue_count": len(state["issue_rows"]),
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
        "raw_read_current_step": False, "parser_executed_current_step": False,
        "network_access_used_current_step": False, "download_attempted_current_step": False,
        "model_or_training_code_used_current_step": False,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_integration_state()
    if not state["all_checks_passed"]:
        raise RuntimeError("P6-D integration gate validation failed: " + "|".join(state["validation_failures"]))
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _ensure_output_root(root)
    specs = (
        (CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"]),
        (OVERLAY_FILENAME, OVERLAY_COLUMNS, state["overlay_rows"]),
        (EVIDENCE_FILENAME, EVIDENCE_COLUMNS, state["evidence_rows"]),
        (SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"]),
        (ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, rows in specs:
        _atomic_write_csv(root / filename, columns, rows)
    hashes = {name: _file_sha256(root / name) for name in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    result = run_covapie_bulk_download_admission_covalent_residue_locator_real_provider_sidecar_integration_gate_v1()
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))

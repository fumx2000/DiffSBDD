"""Step14AU-E0-P6-B0 historical fingerprint authority consolidation.

This gate reads ten explicit committed metadata/code inputs. Raw paths are
handled as strings only; no raw path is dereferenced, stat'ed, read, or hashed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

STEP_LABEL = "Step14AU-E0-P6-B0"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_historical_"
    "raw_fingerprint_authority_consolidation_gate_v1"
)
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_real_parser_"
    "provider_pipeline_integration_design_gate_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_historical_raw_fingerprint_authority_"
    "consolidation_gate_v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_covalent_residue_locator_real_raw_source_precondition_gate_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_historical_raw_fingerprint_"
    "authority_consolidation_gate_blockers"
)
SOURCE_READ_BOUNDARY = (
    "only_p6a_seven_committed_sources_and_three_frozen_historical_"
    "fingerprint_metadata_sources_no_raw_dereference"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
P6A_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1"
)
P6A_MODULE = Path(
    "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_locator_"
    "real_parser_provider_pipeline_integration_design_gate.py"
)
P6A_FILENAMES = (
    "covapie_covalent_residue_locator_real_pipeline_integration_contract.csv",
    "covapie_covalent_residue_locator_real_sample_binding_matrix.csv",
    "covapie_covalent_residue_locator_real_pipeline_source_boundary_audit.csv",
    "covapie_covalent_residue_locator_real_pipeline_safety_audit.csv",
    "covapie_covalent_residue_locator_real_pipeline_issue_inventory.csv",
    "covapie_covalent_residue_locator_real_parser_provider_pipeline_integration_design_manifest.json",
)
HISTORICAL_INDEPENDENCE_SOURCE_PATH = Path(
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
    "independence_evidence_materialization_smoke_v0/"
    "covapie_unified_independence_evidence_source_inventory.csv"
)
HISTORICAL_AVAILABILITY_SOURCE_PATH = Path(
    "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_"
    "controlled_raw_acquisition_gate_v0/"
    "covapie_cys_sg_controlled_raw_file_availability_manifest.csv"
)
HISTORICAL_INTEGRITY_SOURCE_PATH = Path(
    "data/derived/covalent_small/covapie_cys_sg_future_struct_conn_crosscheck_"
    "controlled_raw_acquisition_gate_v0/"
    "covapie_cys_sg_controlled_raw_file_integrity_audit.csv"
)
SOURCE_PATHS = (
    P6A_MODULE,
    *(P6A_ROOT / name for name in P6A_FILENAMES),
    HISTORICAL_INDEPENDENCE_SOURCE_PATH,
    HISTORICAL_AVAILABILITY_SOURCE_PATH,
    HISTORICAL_INTEGRITY_SOURCE_PATH,
)
SOURCE_SHA256 = {
    str(P6A_MODULE): "7d43c30f87b3e4c8a44d27b63ec51ba63307dcf23c16571be1d562d0b737c650",
    str(P6A_ROOT / P6A_FILENAMES[0]): "10950aeeb123be6ca3758c5001d57bdf80c1175e7585fbcbe234ed626b872958",
    str(P6A_ROOT / P6A_FILENAMES[1]): "61a1e77c81a8a0d335bbafd454d2926be442c2dd794bce8b75dc8a1451f78e98",
    str(P6A_ROOT / P6A_FILENAMES[2]): "5ff1578cc4a1dd3e939bc8eddea862f5875abfcc478c43477887197a358a84c2",
    str(P6A_ROOT / P6A_FILENAMES[3]): "bb159ee4a8d2ddedb941e221f85bb2f42fc314064be17f9c3c0aa0a0f3eb296b",
    str(P6A_ROOT / P6A_FILENAMES[4]): "9d1e4fe7e7f6f4149ab57826b5dadbab1b98679f9441fd99d4870ba681861e83",
    str(P6A_ROOT / P6A_FILENAMES[5]): "cc3f824bb196847fcb175589e4682e2d39037177eb3564629498ae004ae7816e",
    str(HISTORICAL_INDEPENDENCE_SOURCE_PATH): "9e9d8de870b4c6d149c8f414f04cb88e6d88495535c23cd2f7b161180faa0501",
    str(HISTORICAL_AVAILABILITY_SOURCE_PATH): "a3f08ef9ce402b083be6fe0582e9d37921a921c0c95e97481640a606de4d85b8",
    str(HISTORICAL_INTEGRITY_SOURCE_PATH): "85ff6671f7f750f1451477068aca3a5948a163197edd6647de31de446f91bffd",
}

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
HISTORICAL_IDENTITIES = (("6BV6", "JUG"), ("6BV8", "JUG"), ("6BV5", "JUG"))
HISTORICAL_RAW_PATHS = (
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv6.cif",
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv8.cif",
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0/6bv5.cif",
)
DOMAIN_BLOCKING_REASONS = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "COVALENT_EVIDENCE_ENUM_UNRESOLVED",
    "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
    "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED",
    "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
    "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
    "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED",
    "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED",
    "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
)

AVAILABILITY_HEADER = (
    "pdb_id", "expected_het_id", "raw_path", "raw_file_available",
    "raw_file_sha256", "raw_file_size_bytes", "git_tracked", "git_staged",
    "available_for_future_struct_conn_parse", "ready_candidate_current_step",
    "ready_for_training_current_step",
)
INTEGRITY_HEADER = (
    "pdb_id", "raw_path", "raw_file_size_bytes", "raw_file_sha256",
    "first_nonempty_line", "starts_with_data_block",
    "html_or_error_page_detected",
    "contains_struct_conn_string_current_step_check_only",
    "struct_conn_parsed_current_step", "integrity_audit_passed", "qa_comment",
)
INDEPENDENCE_HEADER = (
    "sample_order", "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "source_stage", "protein_atom_table_path", "ligand_atom_table_path",
    "pocket_atom_table_path", "covalent_event_table_path",
    "ligand_residue_atom_pair_table_path", "sample_preparation_audit_path",
    "pilot_csv_json_consistent", "expansion_csv_json_consistent",
    "all_source_tables_exist", "protein_atom_table_nonempty",
    "ligand_atom_table_nonempty", "covalent_event_table_exactly_one_row",
    "ligand_residue_atom_pair_table_exactly_one_row",
    "sample_preparation_audit_expected_row_count",
    "sample_preparation_audit_row_count", "sample_preparation_audit_all_passed",
    "event_identity_consistent", "pair_attachment_consistent", "raw_source_path",
    "raw_source_path_consistent", "raw_file_exists",
    "raw_filename_matches_pdb_id", "raw_sha256_before", "raw_sha256_after",
    "raw_sha256_unchanged", "source_inventory_passed", "blocking_reasons",
)
SOURCE_ROLE_HEADERS = {
    "availability": AVAILABILITY_HEADER,
    "integrity": INTEGRITY_HEADER,
    "independence": INDEPENDENCE_HEADER,
}

P6A_BINDING_HEADER = (
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

CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "requirement", "expected_value",
    "observed_value", "contract_passed", "blocking_reason",
)
AUTHORITY_COLUMNS = (
    "authority_row_id", "binding_row_id", "sample_preparation_input_id", "pdb_id",
    "ligand_comp_id", "raw_target_relative_path", "availability_source_row_id",
    "integrity_source_row_id", "independence_source_row_id", "expected_sha256",
    "prior_observed_sha256", "sha256_matches", "independence_sha256_before",
    "independence_sha256_after", "independence_sha256_unchanged",
    "expected_file_size_bytes", "prior_observed_file_size_bytes",
    "file_size_matches", "identity_match", "raw_path_match",
    "all_source_statuses_passed", "authority_source_count", "authority_status",
    "permitted_for_raw_source_precondition", "blocking_reason",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "sha256_expected", "sha256_observed",
    "tracked", "regular_file", "symlink", "source_check_passed",
    "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count",
    "blocking_reason",
)
CONTRACT_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_authority_contract.csv"
AUTHORITY_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_authority.csv"
SOURCE_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_covalent_residue_locator_historical_raw_fingerprint_authority_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME, AUTHORITY_FILENAME, SOURCE_FILENAME, SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
SECTION_NAMES = (
    "source_boundary", "p6a_predecessor", "source_role_contract",
    "authority_rows", "authority_contract", "issue_inventory", "safety",
)


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    status: str
    blocking_reason: str


@dataclass(frozen=True)
class JsonDocument:
    payload: dict[str, Any]
    status: str
    blocking_reason: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv_document(path: Path) -> CsvDocument:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return CsvDocument((), (), "blocked", "CSV_HEADER_MISSING")
            header = tuple(reader.fieldnames)
            if not header or any(field == "" for field in header):
                return CsvDocument(header, (), "blocked", "CSV_HEADER_EMPTY")
            if len(set(header)) != len(header):
                return CsvDocument(header, (), "blocked", "CSV_HEADER_DUPLICATE")
            rows: list[dict[str, str]] = []
            for row in reader:
                if None in row or tuple(key for key in row if key is not None) != header:
                    return CsvDocument(header, tuple(rows), "blocked", "CSV_ROW_HEADER_MISMATCH")
                if any(type(value) is not str for value in row.values()):
                    return CsvDocument(header, tuple(rows), "blocked", "CSV_ROW_VALUE_INVALID")
                rows.append(dict(row))
            if not rows:
                return CsvDocument(header, (), "blocked", "CSV_DATA_ROWS_EMPTY")
            return CsvDocument(header, tuple(rows), "passed", "")
    except (OSError, UnicodeError, csv.Error):
        return CsvDocument((), (), "blocked", "CSV_READ_FAILED")


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Compatibility helper for checks; fail closed rather than returning partial rows."""
    document = _read_csv_document(path)
    return [dict(row) for row in document.rows] if document.status == "passed" else []


def _source_access_allowed(
    relative_path: Path,
    source_row: Mapping[str, Any],
) -> bool:
    """Authorize parsing only after the exact frozen source boundary passed."""
    return (
        type(relative_path) is type(SOURCE_PATHS[0])
        and relative_path in SOURCE_PATHS
        and source_row.get("source_relative_path") == str(relative_path)
        and source_row.get("tracked") is True
        and source_row.get("regular_file") is True
        and source_row.get("symlink") is False
        and source_row.get("source_check_passed") is True
        and source_row.get("sha256_expected") == source_row.get("sha256_observed")
        and source_row.get("sha256_expected") == SOURCE_SHA256.get(str(relative_path))
    )


def _read_frozen_csv_document(
    relative_path: Path,
    source_rows_by_path: Mapping[str, Mapping[str, Any]],
) -> CsvDocument:
    source_row = source_rows_by_path.get(str(relative_path), {})
    if not _source_access_allowed(relative_path, source_row):
        return CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    return _read_csv_document(REPO_ROOT / relative_path)


def _read_frozen_json(
    relative_path: Path,
    source_rows_by_path: Mapping[str, Mapping[str, Any]],
) -> JsonDocument:
    source_row = source_rows_by_path.get(str(relative_path), {})
    if not _source_access_allowed(relative_path, source_row):
        return JsonDocument({}, "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
    try:
        payload = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return JsonDocument({}, "blocked", "JSON_READ_FAILED")
    if type(payload) is not dict:
        return JsonDocument({}, "blocked", "JSON_PAYLOAD_NOT_OBJECT")
    return JsonDocument(payload, "passed", "")


def _csv_true(value: object) -> bool:
    return type(value) is str and value == "True"


def _csv_false(value: object) -> bool:
    return type(value) is str and value == "False"


def _valid_hash(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_size(value: object) -> bool:
    return type(value) is str and value.isdecimal() and int(value) > 0


def _safe_relative_path(value: object) -> bool:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or "\\" in value
        or "\x00" in value
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value)
    ):
        return False
    components = value.split("/")
    if any(component in {"", ".", "..", "?"} for component in components):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and value == path.as_posix()


def _safe_raw_target_relative_path(value: object) -> bool:
    if not _safe_relative_path(value):
        return False
    path = PurePosixPath(value)
    return (
        path.parts[:3] == ("data", "raw", "covalent_sources")
        and path.suffix in {".cif", ".mmcif"}
    )


def _git_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path.as_posix()],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _source_rows() -> list[dict[str, Any]]:
    rows = []
    for order, path in enumerate(SOURCE_PATHS, 1):
        absolute = REPO_ROOT / path
        tracked = _git_tracked(path)
        try:
            mode = absolute.lstat().st_mode
            symlink = stat.S_ISLNK(mode)
            regular = stat.S_ISREG(mode)
        except OSError:
            symlink = False
            regular = False
        observed = _sha256(absolute) if tracked and regular and not symlink else ""
        expected = SOURCE_SHA256.get(str(path), "")
        passed = tracked and regular and not symlink and observed == expected
        rows.append({
            "source_order": order,
            "source_relative_path": str(path),
            "sha256_expected": expected,
            "sha256_observed": observed,
            "tracked": tracked,
            "regular_file": regular,
            "symlink": symlink,
            "source_check_passed": passed,
            "blocking_reason": "" if passed else "SOURCE_BOUNDARY_CHECK_FAILED",
        })
    return rows


def _canonical_source_rows() -> list[dict[str, Any]]:
    return [{
        "source_order": order,
        "source_relative_path": str(path),
        "sha256_expected": SOURCE_SHA256[str(path)],
        "sha256_observed": SOURCE_SHA256[str(path)],
        "tracked": True,
        "regular_file": True,
        "symlink": False,
        "source_check_passed": True,
        "blocking_reason": "",
    } for order, path in enumerate(SOURCE_PATHS, 1)]


def validate_source_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    return list(rows) == _canonical_source_rows()


def _historical_documents(
    source_rows_by_path: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, CsvDocument]:
    if source_rows_by_path is None:
        source_rows = _source_rows()
        source_rows_by_path = {
            row["source_relative_path"]: row for row in source_rows
        }
    return {
        "availability": _read_frozen_csv_document(
            HISTORICAL_AVAILABILITY_SOURCE_PATH, source_rows_by_path
        ),
        "integrity": _read_frozen_csv_document(
            HISTORICAL_INTEGRITY_SOURCE_PATH, source_rows_by_path
        ),
        "independence": _read_frozen_csv_document(
            HISTORICAL_INDEPENDENCE_SOURCE_PATH, source_rows_by_path
        ),
    }


def _source_role_checks(documents: Mapping[str, CsvDocument]) -> dict[str, bool]:
    return {
        "exact_roles": tuple(documents) == ("availability", "integrity", "independence"),
        "availability_document_passed": documents.get("availability", CsvDocument((), (), "blocked", "")).status == "passed",
        "availability_exact_header": documents.get("availability", CsvDocument((), (), "blocked", "")).header == AVAILABILITY_HEADER,
        "integrity_document_passed": documents.get("integrity", CsvDocument((), (), "blocked", "")).status == "passed",
        "integrity_exact_header": documents.get("integrity", CsvDocument((), (), "blocked", "")).header == INTEGRITY_HEADER,
        "independence_document_passed": documents.get("independence", CsvDocument((), (), "blocked", "")).status == "passed",
        "independence_exact_header": documents.get("independence", CsvDocument((), (), "blocked", "")).header == INDEPENDENCE_HEADER,
    }


def _p6a_inputs(
    source_rows_by_path: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], CsvDocument]:
    if source_rows_by_path is None:
        source_rows = _source_rows()
        source_rows_by_path = {
            row["source_relative_path"]: row for row in source_rows
        }
    manifest_path = P6A_ROOT / P6A_FILENAMES[-1]
    binding_path = P6A_ROOT / P6A_FILENAMES[1]
    manifest_document = _read_frozen_json(manifest_path, source_rows_by_path)
    binding = _read_frozen_csv_document(binding_path, source_rows_by_path)
    return manifest_document.payload, binding


def _p6a_checks(
    manifest: Mapping[str, Any] | None = None,
    binding_document: CsvDocument | None = None,
) -> dict[str, bool]:
    if manifest is None or binding_document is None:
        actual_manifest, actual_binding = _p6a_inputs()
        manifest = actual_manifest if manifest is None else manifest
        binding_document = actual_binding if binding_document is None else binding_document
    bindings = list(binding_document.rows)
    first_three = bindings[:3]
    return {
        "stage": manifest.get("stage") == PREVIOUS_STAGE,
        "step_label": manifest.get("step_label") == "Step14AU-E0-P6-A",
        "all_checks_passed": manifest.get("all_checks_passed") is True,
        "validation_failures": manifest.get("validation_failures") == [],
        "architecture": manifest.get("integration_architecture") == "ADDITIVE_EXTERNAL_REAL_EXPORT_EXECUTOR",
        "binding_manifest_count": manifest.get("real_sample_binding_count") == 11,
        "historical_count": manifest.get("historical_binding_count") == 3,
        "expansion_count": manifest.get("expansion_binding_count") == 8,
        "unique_samples": manifest.get("unique_sample_preparation_input_count") == 11,
        "unique_identities": manifest.get("unique_pdb_ligand_identity_count") == 11,
        "metadata_joins": manifest.get("metadata_join_complete_count") == 11,
        "raw_paths": manifest.get("raw_relative_path_persisted_count") == 11,
        "raw_sha_frozen": manifest.get("raw_sha256_precondition_frozen_count") == 0,
        "execution_allowed": manifest.get("real_export_execution_allowed_count") == 0,
        "future_inputs": len(manifest.get("future_executor_input_fields", [])) == 13,
        "future_sidecar": manifest.get("future_real_sidecar_column_count") == 41 and manifest.get("future_real_sidecar_expected_row_count") == 11,
        "executor_false": manifest.get("real_executor_implemented") is False,
        "parser_false": manifest.get("real_parser_pipeline_integration_implemented") is False,
        "provider_false": manifest.get("real_provider_pipeline_integration_implemented") is False,
        "samples": (manifest.get("existing_real_sample_count"), manifest.get("real_insertion_unknown_sample_count"), manifest.get("real_insertion_absence_proven_sample_count")) == (11, 11, 0),
        "admit_false": manifest.get("admit_004_rule_logic_ready") is False,
        "e1_false": manifest.get("ready_for_e1_residue_identity_semantics_design") is False,
        "candidate_false": manifest.get("ready_for_real_candidate_evaluation") is False,
        "download_false": manifest.get("ready_for_bulk_download_now") is False,
        "training_false": manifest.get("ready_for_training") is False and manifest.get("ready_to_train_now") is False,
        "feature_audit": manifest.get("feature_semantics_audit_required_before_training") is True,
        "masks": manifest.get("canonical_mask_pairs") == [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "next_step": manifest.get("recommended_next_step") == RECOMMENDED_NEXT_STEP,
        "binding_document": binding_document.status == "passed" and binding_document.header == P6A_BINDING_HEADER,
        "binding_shape": len(bindings) == 11 and all(tuple(row) == P6A_BINDING_HEADER for row in bindings),
        "binding_order": [row.get("binding_row_id") for row in bindings] == [f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12)],
        "historical_identities": [(row.get("pdb_id"), row.get("ligand_comp_id")) for row in first_three] == list(HISTORICAL_IDENTITIES),
        "historical_sample_ids": [row.get("sample_preparation_input_id") for row in first_three] == [f"CYS_SG_SAMPLE_PREP_INPUT_{index:06d}" for index in range(1, 4)],
        "historical_raw_paths": [row.get("raw_target_relative_path") for row in first_three] == list(HISTORICAL_RAW_PATHS),
        "binding_statuses": len(bindings) == 11 and all(row.get("metadata_join_status") == "one_to_one_metadata_join_complete" and row.get("raw_path_persisted") == "true" and row.get("real_export_execution_allowed_current_step") == "false" and row.get("binding_status") == "design_bound_raw_source_precondition_pending" and row.get("blocking_reason") == "REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN" for row in bindings),
    }


def _availability_status(row: Mapping[str, str]) -> bool:
    return (
        _csv_true(row.get("raw_file_available"))
        and _csv_false(row.get("git_tracked"))
        and _csv_false(row.get("git_staged"))
        and _csv_true(row.get("available_for_future_struct_conn_parse"))
        and _csv_false(row.get("ready_candidate_current_step"))
        and _csv_false(row.get("ready_for_training_current_step"))
    )


def _integrity_status(row: Mapping[str, str], pdb_id: str) -> bool:
    return (
        _csv_true(row.get("starts_with_data_block"))
        and _csv_false(row.get("html_or_error_page_detected"))
        and _csv_false(row.get("struct_conn_parsed_current_step"))
        and _csv_true(row.get("integrity_audit_passed"))
        and row.get("first_nonempty_line") == "data_" + pdb_id
        and row.get("qa_comment") == "byte_integrity_only_no_struct_conn_parse"
    )


def _independence_status(row: Mapping[str, str]) -> bool:
    return (
        row.get("source_stage") == "pilot"
        and _csv_true(row.get("raw_source_path_consistent"))
        and _csv_true(row.get("raw_file_exists"))
        and _csv_true(row.get("raw_filename_matches_pdb_id"))
        and _csv_true(row.get("raw_sha256_unchanged"))
        and _csv_true(row.get("source_inventory_passed"))
        and row.get("blocking_reasons") == ""
    )


def _authority_rows(
    binding_document: CsvDocument | None = None,
    documents: Mapping[str, CsvDocument] | None = None,
) -> list[dict[str, Any]]:
    if binding_document is None:
        _, binding_document = _p6a_inputs()
    if documents is None:
        documents = _historical_documents()
    bindings = list(binding_document.rows[:3])
    availability = list(documents.get("availability", CsvDocument((), (), "blocked", "")).rows)
    integrity = list(documents.get("integrity", CsvDocument((), (), "blocked", "")).rows)
    independence = list(documents.get("independence", CsvDocument((), (), "blocked", "")).rows)
    rows: list[dict[str, Any]] = []
    for authority_order, binding in enumerate(bindings, 1):
        pdb_id = binding.get("pdb_id", "")
        ligand = binding.get("ligand_comp_id", "")
        raw_path = binding.get("raw_target_relative_path", "")
        availability_matches = [(ordinal, row) for ordinal, row in enumerate(availability, 1) if row.get("pdb_id") == pdb_id]
        integrity_matches = [(ordinal, row) for ordinal, row in enumerate(integrity, 1) if (row.get("pdb_id"), row.get("raw_path")) == (pdb_id, raw_path)]
        independence_matches = [(ordinal, row) for ordinal, row in enumerate(independence, 1) if row.get("pdb_id") == pdb_id]
        joined = all(len(matches) == 1 for matches in (availability_matches, integrity_matches, independence_matches))
        availability_ordinal, availability_row = availability_matches[0] if len(availability_matches) == 1 else (0, {})
        integrity_ordinal, integrity_row = integrity_matches[0] if len(integrity_matches) == 1 else (0, {})
        _, independence_row = independence_matches[0] if len(independence_matches) == 1 else (0, {})
        identity_match = joined and (
            (availability_row.get("pdb_id"), availability_row.get("expected_het_id"))
            == (pdb_id, ligand)
            == (independence_row.get("pdb_id"), independence_row.get("ligand_comp_id"))
            and integrity_row.get("pdb_id") == pdb_id
        )
        path_match = joined and (
            availability_row.get("raw_path")
            == integrity_row.get("raw_path")
            == independence_row.get("raw_source_path")
            == raw_path
        )
        hashes = (
            availability_row.get("raw_file_sha256", ""),
            integrity_row.get("raw_file_sha256", ""),
            independence_row.get("raw_sha256_before", ""),
            independence_row.get("raw_sha256_after", ""),
        )
        sizes = (
            availability_row.get("raw_file_size_bytes", ""),
            integrity_row.get("raw_file_size_bytes", ""),
        )
        hash_valid = all(_valid_hash(value) for value in hashes)
        size_valid = all(_valid_size(value) for value in sizes)
        sha_matches = hash_valid and len(set(hashes)) == 1
        file_size_matches = size_valid and sizes[0] == sizes[1]
        statuses_passed = joined and _availability_status(availability_row) and _integrity_status(integrity_row, pdb_id) and _independence_status(independence_row)
        raw_path_safe = _safe_raw_target_relative_path(raw_path)
        if not joined:
            reason = "HISTORICAL_AUTHORITY_SOURCE_JOIN_NOT_ONE_TO_ONE"
        elif not identity_match:
            reason = "HISTORICAL_AUTHORITY_IDENTITY_MISMATCH"
        elif not path_match:
            reason = "HISTORICAL_AUTHORITY_RAW_PATH_MISMATCH"
        elif not hash_valid:
            reason = "HISTORICAL_AUTHORITY_INVALID_HASH"
        elif not sha_matches:
            reason = "HISTORICAL_AUTHORITY_HASH_MISMATCH"
        elif not size_valid:
            reason = "HISTORICAL_AUTHORITY_INVALID_SIZE"
        elif not file_size_matches:
            reason = "HISTORICAL_AUTHORITY_SIZE_MISMATCH"
        elif not statuses_passed:
            reason = "HISTORICAL_AUTHORITY_SOURCE_STATUS_FAILED"
        elif not raw_path_safe:
            reason = "HISTORICAL_AUTHORITY_UNSAFE_RAW_PATH"
        else:
            reason = ""
        passed = reason == ""
        rows.append({
            "authority_row_id": f"HISTORICAL_RAW_AUTHORITY_{authority_order:06d}",
            "binding_row_id": binding.get("binding_row_id", ""),
            "sample_preparation_input_id": binding.get("sample_preparation_input_id", ""),
            "pdb_id": pdb_id,
            "ligand_comp_id": ligand,
            "raw_target_relative_path": raw_path,
            "availability_source_row_id": f"AVAILABILITY_ROW_{availability_ordinal:06d}" if availability_ordinal else "",
            "integrity_source_row_id": f"INTEGRITY_ROW_{integrity_ordinal:06d}" if integrity_ordinal else "",
            "independence_source_row_id": independence_row.get("sample_index_row_id", ""),
            "expected_sha256": hashes[0],
            "prior_observed_sha256": hashes[1],
            "sha256_matches": sha_matches,
            "independence_sha256_before": hashes[2],
            "independence_sha256_after": hashes[3],
            "independence_sha256_unchanged": _csv_true(independence_row.get("raw_sha256_unchanged")),
            "expected_file_size_bytes": sizes[0],
            "prior_observed_file_size_bytes": sizes[1],
            "file_size_matches": file_size_matches,
            "identity_match": identity_match,
            "raw_path_match": path_match,
            "all_source_statuses_passed": statuses_passed,
            "authority_source_count": 3,
            "authority_status": "passed" if passed else "blocked",
            "permitted_for_raw_source_precondition": passed,
            "blocking_reason": reason,
        })
    return rows


def validate_authority_rows(
    rows: Sequence[Mapping[str, Any]],
) -> bool:
    expected = _authority_rows()
    return (
        len(rows) == 3
        and all(tuple(row) == AUTHORITY_COLUMNS for row in rows)
        and list(rows) == expected
        and [(row["pdb_id"], row["ligand_comp_id"]) for row in rows] == list(HISTORICAL_IDENTITIES)
        and all(row["authority_status"] == "passed" and row["permitted_for_raw_source_precondition"] is True and row["blocking_reason"] == "" for row in rows)
    )


def _safety_rows() -> list[dict[str, Any]]:
    observations = (
        ("network", False), ("external_registry", False),
        ("raw_directory_traversal", False), ("raw_lstat_stat", False),
        ("raw_read", False), ("raw_hash", False), ("raw_parse", False),
        ("checkpoint", False), ("p5b_parser", False), ("p4_provider", False),
        ("real_provider_rows", False), ("admission_modification", False),
        ("queue_download", False), ("torch", False), ("numpy", False),
        ("model_forward", False), ("loss", False), ("training", False),
        ("historical_metadata_sources_read", True),
        ("tracked_metadata_sources_hashed", True),
    )
    return [{
        "safety_item": item,
        "required_status": status,
        "observed_status": status,
        "safety_passed": True,
        "blocking_reason": "",
    } for item, status in observations]


def validate_safety_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    return list(rows) == _safety_rows()


def _issue_rows() -> list[dict[str, Any]]:
    return [
        {"issue_id": "REAL_RAW_SOURCE_PRECONDITION_NOT_YET_EXECUTED", "issue_type": "execution_followup", "severity": "blocking", "status": "open", "issue_count": 11, "blocking_reason": "CURRENT_RAW_FINGERPRINTS_NOT_YET_REVALIDATED"},
        {"issue_id": "REAL_RESIDUE_LOCATOR_PROVIDER_EXPORT_NOT_YET_EXECUTED", "issue_type": "execution_followup", "severity": "blocking", "status": "open", "issue_count": 11, "blocking_reason": "REAL_PROVIDER_EXPORT_NOT_IMPLEMENTED"},
        {"issue_id": "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA", "issue_type": "schema_followup", "severity": "blocking", "status": "open", "issue_count": 1, "blocking_reason": "REAL_PROVIDER_SIDECAR_NOT_MERGED"},
    ]


def validate_issue_rows(rows: Sequence[Mapping[str, Any]]) -> bool:
    return list(rows) == _issue_rows()


def _validator_contract_checks() -> dict[str, bool]:
    class StringSubclass(str):
        pass
    return {
        "invalid_hash_rejected": not _valid_hash("x" * 64) and not _valid_hash("A" * 64),
        "invalid_size_rejected": not _valid_size("0") and not _valid_size("-1"),
        "unsafe_path_rejected": all(not _safe_raw_target_relative_path(value) for value in (None, StringSubclass(HISTORICAL_RAW_PATHS[0]), " data/raw/covalent_sources/a.cif", "data\\raw\\a.cif", "data/raw/../a.cif", "https://example/a.cif", "C:/a.cif", "data/raw/covalent_sources/a.CIF")),
        "strict_true_rejected": all(not _csv_true(value) for value in (True, "true", "TRUE", "1", " True")),
        "strict_false_rejected": all(not _csv_false(value) for value in (False, "false", "FALSE", "0", "False ")),
    }


CONTRACT_SPECS = (
    ("lineage", "P6-A predecessor stage and state", "true", "p6a_all"),
    ("lineage", "source input count", "10", "source_count"),
    ("lineage", "P6-A binding shape", "11x26", "p6a_binding_shape"),
    ("lineage", "historical binding count", "3", "historical_binding_count"),
    ("lineage", "canonical five masks include B3", "true", "p6a_masks"),
    ("roles", "availability exact expected-snapshot header", "true", "availability_header"),
    ("roles", "integrity exact prior-observed header", "true", "integrity_header"),
    ("roles", "independence exact corroboration header", "true", "independence_header"),
    ("roles", "source role mapping exact", "true", "roles_exact"),
    ("roles", "current raw used to define expected hash", "false", "current_raw_expected"),
    ("joins", "target identity count", "3", "target_identity_count"),
    ("joins", "target identity order", "true", "target_identity_order"),
    ("joins", "binding ID match count", "3", "binding_match_count"),
    ("joins", "raw path match count", "3", "raw_path_match_count"),
    ("joins", "identity match count", "3", "identity_match_count"),
    ("joins", "source status pass count", "3", "source_status_count"),
    ("joins", "authority source count per row", "3", "authority_source_count"),
    ("fingerprints", "expected hash count", "3", "expected_hash_count"),
    ("fingerprints", "prior observed hash count", "3", "observed_hash_count"),
    ("fingerprints", "before hash count", "3", "before_hash_count"),
    ("fingerprints", "after hash count", "3", "after_hash_count"),
    ("fingerprints", "four-hash match count", "3", "hash_match_count"),
    ("fingerprints", "expected size count", "3", "expected_size_count"),
    ("fingerprints", "observed size count", "3", "observed_size_count"),
    ("validators", "malformed hashes rejected", "true", "invalid_hash_rejected"),
    ("validators", "nonpositive sizes rejected", "true", "invalid_size_rejected"),
    ("validators", "unsafe paths rejected", "true", "unsafe_path_rejected"),
    ("authority", "authority output shape", "3x25", "authority_shape"),
    ("authority", "authority passed count", "3", "authority_passed_count"),
    ("authority", "authority permitted count", "3", "authority_permitted_count"),
    ("authority", "authority blocked count", "0", "authority_blocked_count"),
    ("authority", "size match count", "3", "size_match_count"),
    ("authority", "grounded source locator count", "3", "grounded_locator_count"),
    ("readiness", "ready for P6-B raw precondition", "true", "ready_for_p6b"),
    ("safety", "raw stat current step", "false", "raw_stat"),
    ("safety", "raw read current step", "false", "raw_read"),
    ("safety", "raw hash current step", "false", "raw_hash"),
    ("safety", "raw parse current step", "false", "raw_parse"),
    ("safety", "parser and provider called", "false", "parser_provider_called"),
    ("readiness", "real samples remain 11/11/0", "true", "sample_truth"),
    ("readiness", "ADMIT_004 ready", "false", "admit_ready"),
    ("readiness", "E1 ready", "false", "e1_ready"),
    ("readiness", "candidate evaluation ready", "false", "candidate_ready"),
    ("readiness", "bulk download ready", "false", "download_ready"),
    ("readiness", "training ready", "false", "training_ready"),
    ("readiness", "feature semantics audit required", "true", "feature_audit"),
    ("issues", "follow-up issue count", "3", "issue_count"),
    ("sources", "source boundary pass count", "10", "source_pass_count"),
)
assert len(CONTRACT_SPECS) == 48


def _text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _contract_observations(
    source_rows: Sequence[Mapping[str, Any]],
    p6a_checks: Mapping[str, bool],
    role_checks: Mapping[str, bool],
    authority_rows: Sequence[Mapping[str, Any]],
    validator_checks: Mapping[str, bool],
    safety_rows: Sequence[Mapping[str, Any]],
    issue_rows: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    safety = {row["safety_item"]: row["observed_status"] for row in safety_rows}
    identities = [(row["pdb_id"], row["ligand_comp_id"]) for row in authority_rows]
    locators = sum(
        bool(re.fullmatch(r"AVAILABILITY_ROW_\d{6}", row["availability_source_row_id"]))
        and bool(re.fullmatch(r"INTEGRITY_ROW_\d{6}", row["integrity_source_row_id"]))
        and bool(row["independence_source_row_id"])
        for row in authority_rows
    )
    return {
        "p6a_all": _text(bool(p6a_checks) and all(p6a_checks.values())),
        "source_count": _text(len(source_rows)),
        "p6a_binding_shape": "11x26" if p6a_checks.get("binding_shape") else "invalid",
        "historical_binding_count": "3" if p6a_checks.get("historical_count") else "invalid",
        "p6a_masks": _text(p6a_checks.get("masks", False)),
        "availability_header": _text(role_checks.get("availability_exact_header", False)),
        "integrity_header": _text(role_checks.get("integrity_exact_header", False)),
        "independence_header": _text(role_checks.get("independence_exact_header", False)),
        "roles_exact": _text(bool(role_checks) and all(role_checks.values())),
        "current_raw_expected": "false",
        "target_identity_count": _text(len(set(identities))),
        "target_identity_order": _text(identities == list(HISTORICAL_IDENTITIES)),
        "binding_match_count": _text(sum(row["binding_row_id"] == f"REAL_LOCATOR_BINDING_{index:06d}" for index, row in enumerate(authority_rows, 1))),
        "raw_path_match_count": _text(sum(bool(row["raw_path_match"]) for row in authority_rows)),
        "identity_match_count": _text(sum(bool(row["identity_match"]) for row in authority_rows)),
        "source_status_count": _text(sum(bool(row["all_source_statuses_passed"]) for row in authority_rows)),
        "authority_source_count": _text(min((int(row["authority_source_count"]) for row in authority_rows), default=0)),
        "expected_hash_count": _text(sum(_valid_hash(row["expected_sha256"]) for row in authority_rows)),
        "observed_hash_count": _text(sum(_valid_hash(row["prior_observed_sha256"]) for row in authority_rows)),
        "before_hash_count": _text(sum(_valid_hash(row["independence_sha256_before"]) for row in authority_rows)),
        "after_hash_count": _text(sum(_valid_hash(row["independence_sha256_after"]) for row in authority_rows)),
        "hash_match_count": _text(sum(bool(row["sha256_matches"]) for row in authority_rows)),
        "expected_size_count": _text(sum(_valid_size(row["expected_file_size_bytes"]) for row in authority_rows)),
        "observed_size_count": _text(sum(_valid_size(row["prior_observed_file_size_bytes"]) for row in authority_rows)),
        **{key: _text(value) for key, value in validator_checks.items()},
        "authority_shape": f"{len(authority_rows)}x{len(AUTHORITY_COLUMNS)}" if authority_rows and all(tuple(row) == AUTHORITY_COLUMNS for row in authority_rows) else "invalid",
        "authority_passed_count": _text(sum(row["authority_status"] == "passed" for row in authority_rows)),
        "authority_permitted_count": _text(sum(bool(row["permitted_for_raw_source_precondition"]) for row in authority_rows)),
        "authority_blocked_count": _text(sum(row["authority_status"] == "blocked" for row in authority_rows)),
        "size_match_count": _text(sum(bool(row["file_size_matches"]) for row in authority_rows)),
        "grounded_locator_count": _text(locators),
        "ready_for_p6b": _text(len(authority_rows) == 3 and all(row["authority_status"] == "passed" for row in authority_rows)),
        "raw_stat": _text(safety.get("raw_lstat_stat", "missing")),
        "raw_read": _text(safety.get("raw_read", "missing")),
        "raw_hash": _text(safety.get("raw_hash", "missing")),
        "raw_parse": _text(safety.get("raw_parse", "missing")),
        "parser_provider_called": _text(bool(safety.get("p5b_parser", True)) or bool(safety.get("p4_provider", True))),
        "sample_truth": _text(p6a_checks.get("samples", False)),
        "admit_ready": "false" if p6a_checks.get("admit_false") else "invalid",
        "e1_ready": "false" if p6a_checks.get("e1_false") else "invalid",
        "candidate_ready": "false" if p6a_checks.get("candidate_false") else "invalid",
        "download_ready": "false" if p6a_checks.get("download_false") else "invalid",
        "training_ready": "false" if p6a_checks.get("training_false") else "invalid",
        "feature_audit": _text(p6a_checks.get("feature_audit", False)),
        "issue_count": _text(len(issue_rows)),
        "source_pass_count": _text(sum(bool(row["source_check_passed"]) for row in source_rows)),
    }


def _contract_rows(observations: Mapping[str, str]) -> list[dict[str, Any]]:
    rows = []
    for index, (area, requirement, expected, key) in enumerate(CONTRACT_SPECS, 1):
        observed = observations.get(key, "missing")
        passed = observed == expected
        rows.append({
            "contract_item_id": f"P6B0_C{index:03d}",
            "contract_area": area,
            "requirement": requirement,
            "expected_value": expected,
            "observed_value": observed,
            "contract_passed": passed,
            "blocking_reason": "" if passed else "CONTRACT_OBSERVATION_MISMATCH",
        })
    return rows


def validate_contract_rows(
    rows: Sequence[Mapping[str, Any]], observations: Mapping[str, str]
) -> bool:
    expected = _contract_rows(observations)
    return (
        len(rows) == 48
        and all(tuple(row) == CONTRACT_COLUMNS for row in rows)
        and list(rows) == expected
        and all(row["contract_passed"] is True and row["blocking_reason"] == "" for row in rows)
    )


def build_authority_state(
    forced_section_failures: Iterable[str] = (),
) -> dict[str, Any]:
    forced = tuple(forced_section_failures)
    if len(set(forced)) != len(forced) or any(name not in SECTION_NAMES for name in forced):
        raise ValueError("forced_section_failures must contain unique canonical sections")
    source_rows = _source_rows()
    source_boundary_passed = validate_source_rows(source_rows)
    source_read_allowed = (
        source_boundary_passed and "source_boundary" not in forced
    )
    if source_read_allowed:
        source_rows_by_path = {
            row["source_relative_path"]: row for row in source_rows
        }
        manifest, binding_document = _p6a_inputs(source_rows_by_path)
        p6a_checks = _p6a_checks(manifest, binding_document)
        documents = _historical_documents(source_rows_by_path)
        role_checks = _source_role_checks(documents)
        authority_rows = _authority_rows(binding_document, documents)
        authority_rows_passed = validate_authority_rows(authority_rows)
    else:
        blocked = CsvDocument((), (), "blocked", "SOURCE_ACCESS_NOT_ALLOWED")
        p6a_checks = {"source_access_allowed": False}
        documents = {
            "availability": blocked,
            "integrity": blocked,
            "independence": blocked,
        }
        role_checks = _source_role_checks(documents)
        authority_rows = []
        authority_rows_passed = False
    safety_rows = _safety_rows()
    issue_rows = _issue_rows()
    validator_checks = _validator_contract_checks()
    observations = _contract_observations(
        source_rows, p6a_checks, role_checks, authority_rows, validator_checks,
        safety_rows, issue_rows,
    )
    contract_rows = _contract_rows(observations)
    sections = {
        "source_boundary": source_boundary_passed,
        "p6a_predecessor": source_read_allowed and bool(p6a_checks) and all(p6a_checks.values()),
        "source_role_contract": source_read_allowed and bool(role_checks) and all(role_checks.values()),
        "authority_rows": source_read_allowed and authority_rows_passed,
        "authority_contract": source_read_allowed and validate_contract_rows(contract_rows, observations),
        "issue_inventory": validate_issue_rows(issue_rows),
        "safety": validate_safety_rows(safety_rows),
    }
    for name in forced:
        sections[name] = False
    validation_failures = [
        f"P6B0_{name.upper()}_VALIDATION_FAILED"
        for name in SECTION_NAMES if not sections[name]
    ]
    all_checks_passed = len(sections) == 7 and not validation_failures
    return {
        "source_rows": source_rows,
        "p6a_checks": p6a_checks,
        "source_role_checks": role_checks,
        "authority_rows": authority_rows,
        "validator_checks": validator_checks,
        "contract_observations": observations,
        "contract_rows": contract_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "sections": sections,
        "validation_failures": validation_failures,
        "all_checks_passed": all_checks_passed,
    }


def _csv_value(value: Any) -> str:
    return _text(value)


def _atomic_write_csv(
    path: Path, columns: tuple[str, ...], rows: Sequence[Mapping[str, Any]]
) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows([
                {column: _csv_value(row[column]) for column in columns}
                for row in rows
            ])
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _manifest_payload(
    state: Mapping[str, Any], output_sha256: Mapping[str, str]
) -> dict[str, Any]:
    authority = state["authority_rows"]
    sections = state["sections"]
    all_checks = state["all_checks_passed"]
    return {
        "stage": STAGE,
        "step_label": STEP_LABEL,
        "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": SOURCE_READ_BOUNDARY,
        "source_input_count": len(SOURCE_PATHS),
        "source_input_sha256": SOURCE_SHA256,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": len(OUTPUT_FILES),
        "non_manifest_output_count": len(CSV_OUTPUTS),
        "output_sha256": dict(output_sha256),
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": len(CANONICAL_MASK_PAIRS),
        "p6a_design_frozen": sections["p6a_predecessor"],
        "p6a_binding_count": 11,
        "p6a_historical_binding_count": 3,
        "p6a_expansion_binding_count": 8,
        "p6a_raw_sha_frozen_count": 0,
        "predecessor_field_count": 22,
        "predecessor_domain_issue_count": len(DOMAIN_BLOCKING_REASONS),
        "historical_expected_authority_source_relative_path": str(HISTORICAL_AVAILABILITY_SOURCE_PATH),
        "historical_prior_observed_source_relative_path": str(HISTORICAL_INTEGRITY_SOURCE_PATH),
        "historical_independence_corroboration_source_relative_path": str(HISTORICAL_INDEPENDENCE_SOURCE_PATH),
        "source_role_contract_frozen": sections["source_role_contract"],
        "current_raw_used_to_define_expected_hash": False,
        "historical_authority_row_count": len(authority),
        "authority_passed_count": sum(row["authority_status"] == "passed" for row in authority),
        "authority_blocked_count": sum(row["authority_status"] == "blocked" for row in authority),
        "authority_expected_hash_count": sum(_valid_hash(row["expected_sha256"]) for row in authority),
        "authority_prior_observed_hash_count": sum(_valid_hash(row["prior_observed_sha256"]) for row in authority),
        "authority_hash_match_count": sum(bool(row["sha256_matches"]) for row in authority),
        "authority_size_match_count": sum(bool(row["file_size_matches"]) for row in authority),
        "authority_identity_match_count": sum(bool(row["identity_match"]) for row in authority),
        "authority_raw_path_match_count": sum(bool(row["raw_path_match"]) for row in authority),
        "authority_conflict_count": sum(row["authority_status"] == "blocked" for row in authority),
        "historical_single_authority_file_materialized": all_checks,
        "real_raw_sources_stat_current_step": False,
        "real_raw_sources_read_current_step": False,
        "real_raw_sources_hashed_current_step": False,
        "real_raw_sources_parsed_current_step": False,
        "p5b_parser_called_current_step": False,
        "p4_provider_called_current_step": False,
        "real_executor_implemented": False,
        "real_provider_rows_materialized_current_step": False,
        "real_samples_backfilled_current_step": 0,
        "existing_real_sample_count": 11,
        "real_insertion_unknown_sample_count": 11,
        "real_insertion_absence_proven_sample_count": 0,
        "real_fully_provable_pre_download_sample_count": 0,
        "historical_raw_fingerprint_authority_consolidation_passed": all_checks,
        "ready_for_real_raw_source_precondition_gate": all_checks,
        "ready_for_real_provider_export_execution_smoke": False,
        "insertion_code_provenance_export_ready_for_real_samples": False,
        "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "current_domain_blocking_reasons": list(DOMAIN_BLOCKING_REASONS),
        "authority_followup_issue_ids": [row["issue_id"] for row in state["issue_rows"]],
        "all_source_boundary_checks_passed": sections["source_boundary"],
        "all_p6a_predecessor_checks_passed": sections["p6a_predecessor"],
        "all_source_role_contract_checks_passed": sections["source_role_contract"],
        "all_authority_row_checks_passed": sections["authority_rows"],
        "all_authority_contract_checks_passed": sections["authority_contract"],
        "all_issue_inventory_checks_passed": sections["issue_inventory"],
        "all_safety_checks_passed": sections["safety"],
        "all_checks_passed": all_checks,
        "validation_failures": list(state["validation_failures"]),
        "recommended_next_step": RECOMMENDED_NEXT_STEP if all_checks else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1(
    output_root: Path | None = None,
    forced_section_failures: Iterable[str] = (),
) -> dict[str, Any]:
    state = build_authority_state(forced_section_failures)
    root = REPO_ROOT / (DEFAULT_OUTPUT_ROOT if output_root is None else output_root)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise RuntimeError("OUTPUT_ROOT_NOT_REGULAR_DIRECTORY")
    root.mkdir(parents=True, exist_ok=True)
    _atomic_write_csv(root / CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"])
    _atomic_write_csv(root / AUTHORITY_FILENAME, AUTHORITY_COLUMNS, state["authority_rows"])
    _atomic_write_csv(root / SOURCE_FILENAME, SOURCE_COLUMNS, state["source_rows"])
    _atomic_write_csv(root / SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"])
    _atomic_write_csv(root / ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"])
    output_hashes = {name: _sha256(root / name) for name in CSV_OUTPUTS}
    manifest = _manifest_payload(state, output_hashes)
    _atomic_write_json(root / MANIFEST_FILENAME, manifest)
    return {**state, "manifest": manifest}

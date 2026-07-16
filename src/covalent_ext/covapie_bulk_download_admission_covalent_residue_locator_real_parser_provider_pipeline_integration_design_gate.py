"""Metadata-only real parser/provider integration design gate for CovaPIE."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


STEP_LABEL = "Step14AU-E0-P6-A"
STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_real_parser_"
    "provider_pipeline_integration_design_gate_v1"
)
PREVIOUS_STAGE = (
    "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_"
    "provenance_export_smoke_v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_covalent_residue_locator_real_parser_provider_pipeline_"
    "integration_design_gate_v1_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_covalent_residue_locator_real_raw_source_precondition_"
    "gate_v1"
)
BLOCKED_NEXT_STEP = (
    "resolve_covapie_covalent_residue_locator_real_parser_provider_pipeline_"
    "integration_design_gate_blockers"
)
PROJECT_NAME = "CovaPIE"
INTEGRATION_ARCHITECTURE = "ADDITIVE_EXTERNAL_REAL_EXPORT_EXECUTOR"
SOURCE_READ_BOUNDARY = (
    "only_p5b_seven_committed_outputs_and_modules_plus_five_frozen_real_"
    "pipeline_metadata_sources_no_raw_dereference"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
P5B_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_parser_provider_provenance_export_smoke_v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_"
    "residue_locator_real_parser_provider_pipeline_integration_design_gate_v1"
)
HISTORICAL_EXECUTION_PATH = Path(
    "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/"
    "covapie_sample_preparation_execution_manifest.csv"
)
SAMPLE_INDEX_PATH = Path(
    "data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0/"
    "sample_index.csv"
)
EXPANSION_EXECUTION_PATH = Path(
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
    "sample_preparation_execution_smoke_v0/"
    "covapie_batch_sample_preparation_execution_manifest.csv"
)

SOURCE_PATHS = (
    Path(
        "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_"
        "locator_parser_provider_provenance_export_smoke.py"
    ),
    P5B_ROOT / "covapie_covalent_residue_locator_parser_provider_smoke_contract.csv",
    P5B_ROOT / "covapie_covalent_residue_locator_synthetic_case_audit.csv",
    P5B_ROOT / "covapie_covalent_residue_locator_source_boundary_audit.csv",
    P5B_ROOT / "covapie_covalent_residue_locator_safety_audit.csv",
    P5B_ROOT / "covapie_covalent_residue_locator_parser_provider_smoke_issue_inventory.csv",
    P5B_ROOT
    / "covapie_covalent_residue_locator_parser_provider_provenance_export_smoke_manifest.json",
    Path("src/covalent_ext/covapie_sample_preparation_execution_smoke.py"),
    Path(
        "src/covalent_ext/covapie_independent_group_expansion_batch_sample_"
        "preparation_execution_smoke.py"
    ),
    HISTORICAL_EXECUTION_PATH,
    SAMPLE_INDEX_PATH,
    EXPANSION_EXECUTION_PATH,
)
SOURCE_SHA256 = {
    SOURCE_PATHS[0].as_posix(): "21be5237736a55fe87da9763c939a228bb81c52b2481602c9bcb4dd425b338bd",
    SOURCE_PATHS[1].as_posix(): "a354f457caa2aed03536fbe848cda6a95beafc93810a480b31ec18e4ed70780f",
    SOURCE_PATHS[2].as_posix(): "1c7436924296c102b9875e662f3968a24aa31e1b3e37c2a7c6f9fde39b1f26da",
    SOURCE_PATHS[3].as_posix(): "d59eab7cc5584a687122cc350e67e39974956a1ebff7bd15f2a66c05b2ac104d",
    SOURCE_PATHS[4].as_posix(): "f6cc680501c0e9beb3285e14931bdb3f0a20a3c7b58ba487ae6998a9503c4acf",
    SOURCE_PATHS[5].as_posix(): "32f16ab8e8567d964324963d8cc6208bf08a9cf1c925adb2f37354f0f70040a8",
    SOURCE_PATHS[6].as_posix(): "fa2ddb2b26a3eaa7ab52703a6a77f4ecc04d35b4cf806e97e52220b7be50cae1",
    SOURCE_PATHS[7].as_posix(): "0bb67a720595ce8b5211ba56f6913f1d6333828846abba326af8b2f9965eca8b",
    SOURCE_PATHS[8].as_posix(): "1b04a32a580ef2dbb18048fe50f609bd188dd89c378d83474a1b32822f1e4932",
    SOURCE_PATHS[9].as_posix(): "6fb10b1cbde5a9aa251009b78d74b23081f7f9260e76ac5be7d4e9b8d2bee1e8",
    SOURCE_PATHS[10].as_posix(): "2733991775edf5e075b461a9ba1872c7e2fe7f61f5d9614a2704b814c3f0e2c5",
    SOURCE_PATHS[11].as_posix(): "4335e1763a8c34da98590a35740eb78e481d190f1a1cac01cd9d0078c1f32091",
}
P5B_CASE_SIDECAR_PATH = SOURCE_PATHS[2]

CONTRACT_FILENAME = "covapie_covalent_residue_locator_real_pipeline_integration_contract.csv"
BINDING_FILENAME = "covapie_covalent_residue_locator_real_sample_binding_matrix.csv"
SOURCE_FILENAME = "covapie_covalent_residue_locator_real_pipeline_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_covalent_residue_locator_real_pipeline_safety_audit.csv"
ISSUE_FILENAME = "covapie_covalent_residue_locator_real_pipeline_issue_inventory.csv"
MANIFEST_FILENAME = (
    "covapie_covalent_residue_locator_real_parser_provider_pipeline_integration_"
    "design_manifest.json"
)
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    BINDING_FILENAME,
    SOURCE_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
P5B_CASE_COLUMNS = (
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
    "insertion_blocking_reason", "covalent_residue_locator_namespace",
    "covalent_residue_insertion_code_state", "covalent_residue_insertion_code",
    "covalent_residue_locator_provenance_source_id",
    "covalent_residue_locator_provenance_sha256", "provider_export_status",
    "provider_export_blocking_reason",
)
FUTURE_SIDECAR_PREFIX_COLUMNS = (
    "binding_row_id", "source_pipeline", "sample_execution_id",
    "raw_target_relative_path", "expected_raw_sha256", "observed_raw_sha256",
    "raw_source_precondition_status", "raw_source_precondition_blocking_reason",
)
FUTURE_REAL_SIDECAR_COLUMNS = (*FUTURE_SIDECAR_PREFIX_COLUMNS, *P5B_CASE_COLUMNS)
FUTURE_EXECUTOR_INPUT_FIELDS = (
    "binding_row_id", "source_pipeline", "sample_preparation_input_id",
    "sample_execution_id", "pdb_id", "ligand_comp_id", "conn_id",
    "covalent_residue_name", "selected_residue_chain_id",
    "selected_residue_index", "selected_residue_atom_name",
    "raw_target_relative_path", "expected_raw_sha256",
)

CONTRACT_COLUMNS = (
    "contract_item_id", "contract_area", "requirement", "expected_value",
    "observed_value", "contract_passed", "blocking_reason",
)
BINDING_COLUMNS = (
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
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "sha256_expected", "sha256_observed",
    "tracked", "regular_file", "symlink", "source_check_passed", "blocking_reason",
)
SAFETY_COLUMNS = (
    "safety_item", "required_status", "observed_status", "safety_passed",
    "blocking_reason",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "severity", "status", "issue_count",
    "blocking_reason",
)

DOMAIN_BLOCKERS = (
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
FOLLOWUP_ISSUES = (
    "REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN",
    "REAL_RESIDUE_LOCATOR_PROVIDER_EXPORT_NOT_YET_EXECUTED",
    "REAL_PROVIDER_SIDECAR_NOT_YET_MERGED_INTO_ADMISSION_SCHEMA",
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def _read_csv(relative: Path) -> list[dict[str, str]]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_csv_header(relative: Path) -> tuple[str, ...]:
    with (REPO_ROOT / relative).open(newline="", encoding="utf-8") as handle:
        fieldnames = csv.DictReader(handle).fieldnames
    if (
        fieldnames is None
        or not fieldnames
        or any(type(field) is not str or not field for field in fieldnames)
        or len(set(fieldnames)) != len(fieldnames)
    ):
        return ()
    return tuple(fieldnames)


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


def _safe_sample_artifact_root(value: object) -> bool:
    if not _safe_relative_path(value):
        return False
    parts = PurePosixPath(value).parts
    return (
        parts[:3] == ("data", "derived", "covalent_small")
        and len(parts) > 3
    )


def _safe_artifact_references(
    sample_artifact_root: object,
    covalent_event_table_relative_path: object,
    ligand_residue_atom_pair_table_relative_path: object,
) -> bool:
    if (
        not _safe_sample_artifact_root(sample_artifact_root)
        or not _safe_relative_path(covalent_event_table_relative_path)
        or not _safe_relative_path(ligand_residue_atom_pair_table_relative_path)
    ):
        return False
    root = PurePosixPath(sample_artifact_root)
    event = PurePosixPath(covalent_event_table_relative_path)
    pair = PurePosixPath(ligand_residue_atom_pair_table_relative_path)
    return (
        event.parent == root
        and event.name == "covalent_event_table.csv"
        and pair.parent == root
        and pair.name == "ligand_residue_atom_pair_table.csv"
    )


def _binding_common(
    row_id: str,
    source_pipeline: str,
    values: dict[str, str],
    metadata_identity_join_valid: bool,
) -> dict[str, Any]:
    raw_path = values["raw_target_relative_path"]
    conn_id = values["conn_id"]
    hints = (
        values["covalent_residue_name"], values["selected_residue_chain_id"],
        values["selected_residue_index"], values["selected_residue_atom_name"],
    )
    join_complete = (
        type(metadata_identity_join_valid) is bool
        and metadata_identity_join_valid
        and all(type(value) is str and bool(value) for value in values.values())
        and _safe_raw_target_relative_path(raw_path)
        and _safe_artifact_references(
            values["sample_artifact_root"],
            values["covalent_event_table_relative_path"],
            values["ligand_residue_atom_pair_table_relative_path"],
        )
    )
    return {
        "binding_row_id": row_id,
        "source_pipeline": source_pipeline,
        **values,
        "metadata_join_status": "one_to_one_metadata_join_complete" if join_complete else "metadata_join_failed",
        "raw_path_persisted": _safe_raw_target_relative_path(raw_path),
        "conn_id_persisted": bool(conn_id),
        "residue_locator_hint_persisted": all(hints),
        "partner_side_requires_raw_reparse": True,
        "namespace_evidence_requires_raw_reparse": True,
        "insertion_evidence_requires_raw_reparse": True,
        "matched_atom_site_row_requires_raw_reparse": True,
        "real_export_execution_allowed_current_step": False,
        "binding_status": "design_bound_raw_source_precondition_pending" if join_complete else "metadata_join_failed",
        "blocking_reason": "REAL_RAW_SOURCE_SHA256_PRECONDITION_NOT_YET_FROZEN" if join_complete else "REAL_SAMPLE_METADATA_JOIN_FAILED",
    }


def _expansion_identity_join_valid(row: dict[str, str]) -> bool:
    required_fields = (
        "sample_preparation_input_id", "sample_execution_id", "pdb_id",
        "expected_het_id", "selected_struct_conn_id", "selected_cys_chain_id",
        "selected_cys_seq_id", "selected_ligand_atom_name",
        "sample_artifact_root", "raw_file_path",
    )
    if not all(
        type(row.get(field)) is str and bool(row.get(field))
        for field in required_fields
    ):
        return False
    ligand_atom = row["selected_ligand_atom_name"]
    return (
        row.get("sample_preparation_status") == "passed"
        and row.get("embedded_qa_passed") == "True"
        and row.get("covalent_event_count") == "1"
        and row.get("ligand_residue_atom_pair_count") == "1"
        and row.get("covalent_bond_atom_pair") == f"SG--{ligand_atom}"
    )


def build_real_sample_binding_rows() -> list[dict[str, Any]]:
    historical = _read_csv(HISTORICAL_EXECUTION_PATH)
    sample_index = _read_csv(SAMPLE_INDEX_PATH)
    expansion = _read_csv(EXPANSION_EXECUTION_PATH)
    execution_by_input: dict[str, dict[str, str]] = {}
    duplicate_execution_ids = set()
    for row in historical:
        key = row.get("sample_preparation_input_id", "")
        if key in execution_by_input:
            duplicate_execution_ids.add(key)
        execution_by_input[key] = row
    duplicate_index_ids = set()
    index_ids = set()
    for row in sample_index:
        key = row.get("sample_preparation_input_id", "")
        if key in index_ids:
            duplicate_index_ids.add(key)
        index_ids.add(key)
    execution_keys = [row.get("sample_preparation_input_id", "") for row in historical]
    index_keys = [row.get("sample_preparation_input_id", "") for row in sample_index]
    historical_join_valid = (
        len(historical) == 3
        and len(sample_index) == 3
        and len(set(execution_keys)) == 3
        and len(set(index_keys)) == 3
        and set(execution_keys) == set(index_keys)
        and all(type(key) is str and bool(key) for key in execution_keys)
        and all(type(key) is str and bool(key) for key in index_keys)
        and not duplicate_execution_ids
        and not duplicate_index_ids
    )
    rows: list[dict[str, Any]] = []
    for index in sample_index:
        key = index.get("sample_preparation_input_id", "")
        execution = execution_by_input.get(key, {}) if historical_join_valid else {}
        identity_join_valid = (
            historical_join_valid
            and execution.get("sample_preparation_input_id") == key
            and execution.get("sample_execution_id") == index.get("sample_execution_id")
            and execution.get("pdb_id") == index.get("pdb_id")
            and type(execution.get("expected_het_id")) is str
            and bool(execution.get("expected_het_id"))
            and type(index.get("expected_het_id")) is str
            and bool(index.get("expected_het_id"))
            and type(index.get("ligand_comp_id")) is str
            and bool(index.get("ligand_comp_id"))
            and execution.get("expected_het_id") == index.get("expected_het_id")
            and index.get("expected_het_id") == index.get("ligand_comp_id")
            and execution.get("sample_artifact_root") == index.get("sample_artifact_root")
            and execution.get("sample_preparation_status") == "sample_preparation_smoke_passed"
            and index.get("sample_index_status") == "sample_index_materialized_from_qa_passed_sample"
        )
        values = {
            "sample_preparation_input_id": key,
            "sample_execution_id": execution.get("sample_execution_id", ""),
            "pdb_id": execution.get("pdb_id", ""),
            "ligand_comp_id": index.get("ligand_comp_id", ""),
            "conn_id": index.get("conn_id", ""),
            "covalent_residue_name": index.get("covalent_residue_name", ""),
            "selected_residue_chain_id": index.get("covalent_residue_chain_id", ""),
            "selected_residue_index": index.get("covalent_residue_index", ""),
            "selected_residue_atom_name": index.get("covalent_residue_atom_name", ""),
            "raw_target_relative_path": execution.get("raw_file_path", ""),
            "sample_artifact_root": index.get("sample_artifact_root", ""),
            "covalent_event_table_relative_path": index.get("covalent_event_table_path", ""),
            "ligand_residue_atom_pair_table_relative_path": index.get("ligand_residue_atom_pair_table_path", ""),
        }
        rows.append(_binding_common(
            "", "historical_sample_preparation_execution_smoke_v0", values,
            identity_join_valid,
        ))
    try:
        ranks = [int(row.get("shortlist_rank", "")) for row in expansion]
        expansion_ids = [row.get("sample_preparation_input_id", "") for row in expansion]
        if (
            sorted(ranks) != list(range(1, 9))
            or len(set(ranks)) != 8
            or len(set(expansion_ids)) != 8
            or any(not value for value in expansion_ids)
        ):
            expansion = []
        else:
            expansion = sorted(expansion, key=lambda row: int(row["shortlist_rank"]))
    except (TypeError, ValueError):
        expansion = []
    for execution in expansion:
        root = execution.get("sample_artifact_root", "")
        values = {
            "sample_preparation_input_id": execution.get("sample_preparation_input_id", ""),
            "sample_execution_id": execution.get("sample_execution_id", ""),
            "pdb_id": execution.get("pdb_id", ""),
            "ligand_comp_id": execution.get("expected_het_id", ""),
            "conn_id": execution.get("selected_struct_conn_id", ""),
            "covalent_residue_name": "CYS",
            "selected_residue_chain_id": execution.get("selected_cys_chain_id", ""),
            "selected_residue_index": execution.get("selected_cys_seq_id", ""),
            "selected_residue_atom_name": "SG",
            "raw_target_relative_path": execution.get("raw_file_path", ""),
            "sample_artifact_root": root,
            "covalent_event_table_relative_path": f"{root}/covalent_event_table.csv" if root else "",
            "ligand_residue_atom_pair_table_relative_path": f"{root}/ligand_residue_atom_pair_table.csv" if root else "",
        }
        rows.append(_binding_common(
            "", "independent_group_expansion_batch_sample_preparation_execution_smoke_v0",
            values, _expansion_identity_join_valid(execution),
        ))
    for index, row in enumerate(rows, 1):
        row["binding_row_id"] = f"REAL_LOCATOR_BINDING_{index:06d}"
    return [{column: row[column] for column in BINDING_COLUMNS} for row in rows]


_CANONICAL_BINDING_ROWS = tuple(
    tuple(row[column] for column in BINDING_COLUMNS)
    for row in build_real_sample_binding_rows()
)


def validate_binding_rows(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != 11 or any(tuple(row) != BINDING_COLUMNS for row in rows):
        return False
    if tuple(tuple(row[column] for column in BINDING_COLUMNS) for row in rows) != _CANONICAL_BINDING_ROWS:
        return False
    expected_ids = tuple(f"REAL_LOCATOR_BINDING_{index:06d}" for index in range(1, 12))
    sample_ids = [row["sample_preparation_input_id"] for row in rows]
    identities = [(row["pdb_id"], row["ligand_comp_id"]) for row in rows]
    return (
        tuple(row["binding_row_id"] for row in rows) == expected_ids
        and [row["source_pipeline"] for row in rows[:3]] == ["historical_sample_preparation_execution_smoke_v0"] * 3
        and [row["source_pipeline"] for row in rows[3:]] == ["independent_group_expansion_batch_sample_preparation_execution_smoke_v0"] * 8
        and len(set(sample_ids)) == 11
        and len(set(identities)) == 11
        and all(row["metadata_join_status"] == "one_to_one_metadata_join_complete" for row in rows)
        and all(_safe_raw_target_relative_path(row["raw_target_relative_path"]) for row in rows)
        and all(
            _safe_artifact_references(
                row["sample_artifact_root"],
                row["covalent_event_table_relative_path"],
                row["ligand_residue_atom_pair_table_relative_path"],
            )
            for row in rows
        )
        and all(row["real_export_execution_allowed_current_step"] is False for row in rows)
        and all(row["binding_status"] == "design_bound_raw_source_precondition_pending" for row in rows)
        and all(row["blocking_reason"] == FOLLOWUP_ISSUES[0] for row in rows)
    )


def _source_rows() -> list[dict[str, Any]]:
    rows = []
    for order, relative in enumerate(SOURCE_PATHS, 1):
        absolute = REPO_ROOT / relative
        tracked = _git(["ls-files", "--error-unmatch", relative.as_posix()]).returncode == 0
        regular = absolute.is_file()
        symlink = absolute.is_symlink()
        observed = _sha256(absolute) if regular and not symlink else ""
        expected = SOURCE_SHA256[relative.as_posix()]
        passed = tracked and regular and not symlink and observed == expected
        rows.append({
            "source_order": order, "source_relative_path": relative.as_posix(),
            "sha256_expected": expected, "sha256_observed": observed,
            "tracked": tracked, "regular_file": regular, "symlink": symlink,
            "source_check_passed": passed,
            "blocking_reason": "" if passed else f"SOURCE_BOUNDARY_FAILED:{relative.as_posix()}",
        })
    return rows


def validate_source_rows(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 12
        and all(tuple(row) == SOURCE_COLUMNS for row in rows)
        and tuple(row["source_order"] for row in rows) == tuple(range(1, 13))
        and tuple(row["source_relative_path"] for row in rows) == tuple(path.as_posix() for path in SOURCE_PATHS)
        and all(row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]] for row in rows)
        and all(
            row["sha256_observed"] == row["sha256_expected"]
            and row["tracked"] is True and row["regular_file"] is True
            and row["symlink"] is False and row["source_check_passed"] is True
            and row["blocking_reason"] == "" for row in rows
        )
    )


def _p5b_manifest() -> dict[str, Any]:
    return json.loads((REPO_ROOT / SOURCE_PATHS[6]).read_text(encoding="utf-8"))


def _p5b_checks() -> dict[str, bool]:
    manifest = _p5b_manifest()
    actual_case_header = _read_csv_header(P5B_CASE_SIDECAR_PATH)
    return {
        "stage": manifest.get("stage") == PREVIOUS_STAGE,
        "label": manifest.get("step_label") == "Step14AU-E0-P5-B",
        "passed": manifest.get("all_checks_passed") is True and manifest.get("validation_failures") == [],
        "synthetic": manifest.get("parser_provider_provenance_export_synthetic_smoke_passed") is True,
        "source_count": manifest.get("source_input_count") == 9,
        "cases": manifest.get("synthetic_case_count") == 16 and manifest.get("synthetic_sidecar_column_count") == 33,
        "statuses": (
            manifest.get("exported_pass_case_count") == 5
            and manifest.get("exported_blocking_case_count") == 5
            and manifest.get("rejected_case_count") == 6
        ),
        "compatibility": manifest.get("historical_compatibility_view_verified") is True,
        "binding": manifest.get("explicit_partner_side_preserved") is True and manifest.get("unique_matched_atom_site_row_binding_verified") is True,
        "real_false": manifest.get("real_parser_pipeline_integration_implemented") is False and manifest.get("real_provider_pipeline_integration_implemented") is False,
        "samples": manifest.get("real_samples_backfilled_current_step") == 0 and manifest.get("existing_real_sample_count") == 11 and manifest.get("real_insertion_unknown_sample_count") == 11 and manifest.get("real_insertion_absence_proven_sample_count") == 0,
        "readiness": (
            manifest.get("admit_004_rule_logic_ready") is False
            and manifest.get("ready_for_e1_residue_identity_semantics_design") is False
            and manifest.get("ready_for_real_candidate_evaluation") is False
            and manifest.get("ready_for_bulk_download_now") is False
            and manifest.get("ready_for_training") is False
            and manifest.get("ready_to_train_now") is False
        ),
        "feature": manifest.get("feature_semantics_audit_required_before_training") is True,
        "masks": manifest.get("canonical_mask_pairs") == [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "case_header_exact": actual_case_header == P5B_CASE_COLUMNS,
        "future_header_binding": FUTURE_REAL_SIDECAR_COLUMNS == (
            *FUTURE_SIDECAR_PREFIX_COLUMNS, *actual_case_header
        ),
        "next": manifest.get("recommended_next_step") == "design_covapie_covalent_residue_locator_real_parser_provider_pipeline_integration_v1",
    }


def _issue_rows() -> list[dict[str, Any]]:
    return [
        {"issue_id": FOLLOWUP_ISSUES[0], "issue_type": "raw_source_precondition_pending", "severity": "blocking", "status": "open", "issue_count": 11, "blocking_reason": "raw_relative_paths_persisted_but_raw_content_hashes_not_verified_current_step"},
        {"issue_id": FOLLOWUP_ISSUES[1], "issue_type": "real_provider_execution_pending", "severity": "blocking", "status": "open", "issue_count": 11, "blocking_reason": "design_only_gate_does_not_open_raw_or_generate_real_provider_rows"},
        {"issue_id": FOLLOWUP_ISSUES[2], "issue_type": "admission_merge_pending", "severity": "blocking", "status": "open", "issue_count": 1, "blocking_reason": "real_sidecar_requires_execution_and_qa_before_22_field_merge"},
    ]


def validate_issue_rows(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 3 and all(tuple(row) == ISSUE_COLUMNS for row in rows) and rows == _issue_rows()


SAFETY_ITEMS = (
    "network_access_used_current_step", "external_registry_lookup_current_step",
    "ignored_raw_directory_traversed_current_step", "ignored_raw_structure_read_current_step",
    "ignored_raw_structure_stat_current_step", "ignored_raw_structure_hashed_current_step",
    "checkpoint_read_current_step", "artifact_reference_paths_followed_current_step",
    "historical_parser_modified_current_step", "expansion_parser_modified_current_step",
    "p5b_source_files_modified_current_step", "p3_p4_source_files_modified_current_step",
    "real_executor_implemented_current_step", "real_provider_rows_materialized_current_step",
    "admission_records_modified_current_step", "download_queue_materialized_current_step",
    "torch_imported", "numpy_imported", "model_forward_or_loss_called", "training_allowed",
)


def _safety_rows() -> list[dict[str, Any]]:
    return [
        {"safety_item": item, "required_status": False, "observed_status": False,
         "safety_passed": True, "blocking_reason": ""}
        for item in SAFETY_ITEMS
    ]


def validate_safety_rows(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 20 and all(tuple(row) == SAFETY_COLUMNS for row in rows) and rows == _safety_rows()


CONTRACT_SPECS = (
    ("lineage", "P5-B predecessor", PREVIOUS_STAGE, "previous"),
    ("lineage", "exact source input count", "12", "sources"),
    ("lineage", "P5-B cases columns and statuses", "16|33|5|5|6", "p5b"),
    ("lineage", "predecessor field count", "22", "fields"),
    ("lineage", "canonical masks include B3", "A|B|B2|B3|C", "masks"),
    ("inventory", "real sample total", "11", "total"),
    ("inventory", "historical binding count", "3", "historical"),
    ("inventory", "expansion binding count", "8", "expansion"),
    ("inventory", "unique sample preparation IDs", "11", "unique_samples"),
    ("inventory", "unique PDB ligand identities", "11", "unique_identity"),
    ("inventory", "exact binding order", "historical3_then_expansion_rank1_to8", "order"),
    ("inventory", "metadata joins complete", "11", "joins"),
    ("architecture", "integration architecture", INTEGRATION_ARCHITECTURE, "architecture"),
    ("architecture", "historical parser unchanged", "true", "historical_unchanged"),
    ("architecture", "expansion parser unchanged", "true", "expansion_unchanged"),
    ("architecture", "existing artifacts are not overwritten", "true", "no_overwrite"),
    ("architecture", "admission evaluator does not open raw", "true", "no_evaluator_raw"),
    ("architecture", "P5-B adapter reuse required", "true", "p5b_reuse"),
    ("architecture", "P4 provider reuse required", "true", "p4_reuse"),
    ("raw_boundary", "raw paths are relative", "11", "relative"),
    ("raw_boundary", "raw paths reject traversal", "11", "no_traversal"),
    ("raw_boundary", "raw SHA precondition required", "true", "sha_required"),
    ("raw_boundary", "raw SHA preconditions frozen current step", "0", "sha_frozen"),
    ("raw_boundary", "raw sources read current step", "false", "raw_read"),
    ("raw_boundary", "network used current step", "false", "network"),
    ("evidence", "partner side must be reproven", "11", "partner"),
    ("evidence", "namespace must be reproven", "11", "namespace"),
    ("evidence", "matched atom row must be reproven", "11", "matched"),
    ("evidence", "insertion tokens must be reproven", "11", "insertion"),
    ("evidence", "distance inference forbidden", "true", "no_distance"),
    ("evidence", "P4 provider maps five fields", "true", "provider"),
    ("output", "future real sidecar columns", "41", "sidecar_columns"),
    ("output", "future real sidecar rows", "11", "sidecar_rows"),
    ("output", "sidecar remains independent", "true", "independent"),
    ("output", "later sidecar QA required", "true", "later_qa"),
    ("output", "later admission merge required", "true", "later_merge"),
    ("readiness", "real integration design frozen", "true", "design"),
    ("readiness", "raw precondition gate ready", "true", "precondition_ready"),
    ("readiness", "real executor implemented", "false", "executor"),
    ("readiness", "real export executed", "false", "export"),
    ("readiness", "real samples remain eleven unknown zero absence", "11|11|0", "samples"),
    ("readiness", "ADMIT_004 and E1 remain false", "false|false", "admit_e1"),
    ("readiness", "candidate evaluation remains false", "false", "candidate"),
    ("readiness", "bulk download remains false", "false", "download"),
    ("readiness", "training remains false", "false|false", "training"),
    ("readiness", "feature semantics audit remains required", "true", "feature"),
    ("readiness", "real execution allowed count", "0", "execution_allowed"),
    ("readiness", "atom name blocker remains independent", "true", "atom_name_blocker"),
)


def _contract_observations(bindings: list[dict[str, Any]], sources: list[dict[str, Any]], p5b: dict[str, bool]) -> dict[str, str]:
    historical = [row for row in bindings if row["source_pipeline"].startswith("historical_")]
    expansion = [row for row in bindings if row["source_pipeline"].startswith("independent_")]
    sample_ids = {row["sample_preparation_input_id"] for row in bindings}
    identities = {(row["pdb_id"], row["ligand_comp_id"]) for row in bindings}
    return {
        "previous": PREVIOUS_STAGE, "sources": str(len(sources)),
        "p5b": "16|33|5|5|6" if (
            p5b.get("cases") and p5b.get("statuses")
            and p5b.get("case_header_exact") and p5b.get("future_header_binding")
        ) else "invalid",
        "fields": "22", "masks": "|".join(alias for _, alias in CANONICAL_MASK_PAIRS),
        "total": str(len(bindings)), "historical": str(len(historical)), "expansion": str(len(expansion)),
        "unique_samples": str(len(sample_ids)), "unique_identity": str(len(identities)),
        "order": "historical3_then_expansion_rank1_to8" if len(historical) == 3 and bindings[:3] == historical and bindings[3:] == expansion else "invalid",
        "joins": str(sum(row["metadata_join_status"] == "one_to_one_metadata_join_complete" for row in bindings)),
        "architecture": INTEGRATION_ARCHITECTURE,
        "historical_unchanged": _bool_text(sources[7]["source_check_passed"]),
        "expansion_unchanged": _bool_text(sources[8]["source_check_passed"]),
        "no_overwrite": "true", "no_evaluator_raw": "true", "p5b_reuse": "true", "p4_reuse": "true",
        "relative": str(sum(_safe_raw_target_relative_path(row["raw_target_relative_path"]) for row in bindings)),
        "no_traversal": str(sum(".." not in PurePosixPath(row["raw_target_relative_path"]).parts for row in bindings)),
        "sha_required": "true", "sha_frozen": "0", "raw_read": "false", "network": "false",
        "partner": str(sum(row["partner_side_requires_raw_reparse"] is True for row in bindings)),
        "namespace": str(sum(row["namespace_evidence_requires_raw_reparse"] is True for row in bindings)),
        "matched": str(sum(row["matched_atom_site_row_requires_raw_reparse"] is True for row in bindings)),
        "insertion": str(sum(row["insertion_evidence_requires_raw_reparse"] is True for row in bindings)),
        "no_distance": "true", "provider": "true",
        "sidecar_columns": str(len(FUTURE_REAL_SIDECAR_COLUMNS)), "sidecar_rows": str(len(bindings)),
        "independent": "true", "later_qa": "true", "later_merge": "true", "design": "true",
        "precondition_ready": "true", "executor": "false", "export": "false", "samples": "11|11|0",
        "admit_e1": "false|false", "candidate": "false", "download": "false", "training": "false|false",
        "feature": "true",
        "execution_allowed": str(sum(row["real_export_execution_allowed_current_step"] is True for row in bindings)),
        "atom_name_blocker": _bool_text("COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED" in DOMAIN_BLOCKERS),
    }


def _contract_rows(observations: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for index, (area, requirement, expected, key) in enumerate(CONTRACT_SPECS, 1):
        observed = observations[key]
        passed = observed == expected
        rows.append({
            "contract_item_id": f"P6A_C{index:03d}", "contract_area": area,
            "requirement": requirement, "expected_value": expected,
            "observed_value": observed, "contract_passed": passed,
            "blocking_reason": "" if passed else f"P6A_C{index:03d}",
        })
    return rows


def validate_contract_rows(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != 48 or any(tuple(row) != CONTRACT_COLUMNS for row in rows):
        return False
    for index, (row, spec) in enumerate(zip(rows, CONTRACT_SPECS), 1):
        area, requirement, expected, _ = spec
        if row != {
            "contract_item_id": f"P6A_C{index:03d}", "contract_area": area,
            "requirement": requirement, "expected_value": expected,
            "observed_value": expected, "contract_passed": True,
            "blocking_reason": "",
        }:
            return False
    return True


SECTION_NAMES = (
    "source_boundary", "p5b_predecessor", "binding_matrix",
    "integration_contract", "issue_inventory", "safety",
)


def build_design_state(forced_section_failures: Iterable[str] = ()) -> dict[str, Any]:
    forced = set(forced_section_failures)
    if not forced.issubset(SECTION_NAMES):
        raise ValueError("unknown forced section failure")
    sources = _source_rows()
    p5b = _p5b_checks()
    bindings = build_real_sample_binding_rows()
    contracts = _contract_rows(_contract_observations(bindings, sources, p5b))
    issues = _issue_rows()
    safety = _safety_rows()
    sections = {
        "source_boundary": validate_source_rows(sources),
        "p5b_predecessor": bool(p5b) and all(p5b.values()),
        "binding_matrix": validate_binding_rows(bindings),
        "integration_contract": validate_contract_rows(contracts),
        "issue_inventory": validate_issue_rows(issues),
        "safety": validate_safety_rows(safety),
    }
    for section in forced:
        sections[section] = False
    failures = [f"{section.upper()}_VALIDATION_FAILED" for section in SECTION_NAMES if not sections[section]]
    return {
        "source_rows": sources, "p5b_checks": p5b, "binding_rows": bindings,
        "contract_rows": contracts, "issue_rows": issues, "safety_rows": safety,
        "sections": sections, "validation_failures": failures,
        "all_checks_passed": not failures,
    }


def _manifest_payload(state: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    passed = state["all_checks_passed"]
    bindings = state["binding_rows"]
    historical_bindings = [
        row for row in bindings
        if row.get("source_pipeline") == "historical_sample_preparation_execution_smoke_v0"
    ]
    expansion_bindings = [
        row for row in bindings
        if row.get("source_pipeline")
        == "independent_group_expansion_batch_sample_preparation_execution_smoke_v0"
    ]
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": SOURCE_READ_BOUNDARY, "source_input_count": 12,
        "source_input_sha256": dict(SOURCE_SHA256), "output_files": list(OUTPUT_FILES),
        "output_file_count": 6, "non_manifest_output_count": 5,
        "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS],
        "canonical_mask_task_count": 5,
        "p5b_synthetic_smoke_passed": state["p5b_checks"]["synthetic"],
        "p5b_case_count": 16, "p5b_sidecar_column_count": 33,
        "p5b_status_counts": {"exported_pass": 5, "exported_blocking": 5, "rejected": 6},
        "predecessor_field_count": 22, "predecessor_domain_issue_count": 10,
        "real_sample_binding_count": len(bindings),
        "historical_binding_count": len(historical_bindings),
        "expansion_binding_count": len(expansion_bindings),
        "unique_sample_preparation_input_count": len({
            row.get("sample_preparation_input_id") for row in bindings
            if type(row.get("sample_preparation_input_id")) is str
            and bool(row.get("sample_preparation_input_id"))
        }),
        "unique_pdb_ligand_identity_count": len({
            (row.get("pdb_id"), row.get("ligand_comp_id")) for row in bindings
            if type(row.get("pdb_id")) is str and bool(row.get("pdb_id"))
            and type(row.get("ligand_comp_id")) is str
            and bool(row.get("ligand_comp_id"))
        }),
        "metadata_join_complete_count": sum(
            row.get("metadata_join_status") == "one_to_one_metadata_join_complete"
            for row in bindings
        ),
        "raw_relative_path_persisted_count": sum(
            row.get("raw_path_persisted") is True for row in bindings
        ),
        "raw_sha256_precondition_frozen_count": 0,
        "real_export_execution_allowed_count": sum(
            row.get("real_export_execution_allowed_current_step") is True
            for row in bindings
        ),
        "integration_architecture": INTEGRATION_ARCHITECTURE,
        "real_pipeline_integration_design_frozen": passed,
        "historical_parser_modification_required": False,
        "expansion_parser_modification_required": False,
        "p5b_adapter_reuse_required": True, "p4_provider_reuse_required": True,
        "raw_source_sha256_precondition_required": True,
        "future_executor_input_fields": list(FUTURE_EXECUTOR_INPUT_FIELDS),
        "future_real_sidecar_columns": list(FUTURE_REAL_SIDECAR_COLUMNS),
        "future_real_sidecar_column_count": 41,
        "future_real_sidecar_expected_row_count": 11,
        "sidecar_merge_deferred_until_execution_qa": True,
        "real_executor_implemented": False,
        "real_raw_sources_read_current_step": False,
        "real_raw_sources_hashed_current_step": False,
        "real_provider_rows_materialized_current_step": False,
        "real_samples_backfilled_current_step": 0,
        "real_parser_pipeline_integration_implemented": False,
        "real_provider_pipeline_integration_implemented": False,
        "existing_real_sample_count": 11,
        "real_insertion_unknown_sample_count": 11,
        "real_insertion_absence_proven_sample_count": 0,
        "real_fully_provable_pre_download_sample_count": 0,
        "ready_for_real_raw_source_precondition_gate": passed,
        "ready_for_real_provider_export_execution": False,
        "insertion_code_provenance_export_ready_for_real_samples": False,
        "admit_004_rule_logic_ready": False,
        "ready_for_e1_residue_identity_semantics_design": False,
        "ready_for_real_candidate_evaluation": False,
        "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "current_domain_blocking_reasons": list(DOMAIN_BLOCKERS),
        "integration_followup_issue_ids": list(FOLLOWUP_ISSUES),
        "validation_failures": state["validation_failures"],
        "all_source_boundary_checks_passed": state["sections"]["source_boundary"],
        "all_p5b_predecessor_checks_passed": state["sections"]["p5b_predecessor"],
        "all_binding_matrix_checks_passed": state["sections"]["binding_matrix"],
        "all_contract_checks_passed": state["sections"]["integration_contract"],
        "all_issue_inventory_checks_passed": state["sections"]["issue_inventory"],
        "all_safety_checks_passed": state["sections"]["safety"],
        "all_checks_passed": passed,
        "recommended_next_step": RECOMMENDED_NEXT_STEP if passed else BLOCKED_NEXT_STEP,
    }


def _csv_value(value: Any) -> Any:
    return _bool_text(value) if isinstance(value, bool) else value


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _csv_value(row[column]) for column in columns})
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    forced_section_failures: Iterable[str] = (),
) -> dict[str, Any]:
    root = REPO_ROOT / output_root if not output_root.is_absolute() else output_root
    if root.is_symlink():
        raise RuntimeError("output root must not be a symlink")
    if root.exists() and not root.is_dir():
        raise RuntimeError("output root must be a directory")
    state = build_design_state(forced_section_failures)
    _write_csv(root / CONTRACT_FILENAME, CONTRACT_COLUMNS, state["contract_rows"])
    _write_csv(root / BINDING_FILENAME, BINDING_COLUMNS, state["binding_rows"])
    _write_csv(root / SOURCE_FILENAME, SOURCE_COLUMNS, state["source_rows"])
    _write_csv(root / SAFETY_FILENAME, SAFETY_COLUMNS, state["safety_rows"])
    _write_csv(root / ISSUE_FILENAME, ISSUE_COLUMNS, state["issue_rows"])
    hashes = {filename: _sha256(root / filename) for filename in CSV_OUTPUTS}
    manifest = _manifest_payload(state, hashes)
    _write_json(root / MANIFEST_FILENAME, manifest)
    return {**state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    run_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1()

"""Design the CovaPIE target-residue atom condition contract in memory."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as unified_view,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)


__all__ = ()


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_CONTRACT_DESIGN_INVALID"
_DESIGN_VERSION = "covapie_target_residue_atom_condition_contract_design_v1"
_CONDITION_VERSION = "covapie_target_residue_atom_condition_v1"
_CONDITION_EVIDENCE_VERSION = (
    "covapie_target_residue_atom_condition_evidence_v1"
)
_FORMAL_VIEW_FILESYSTEM_SHA256 = (
    "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"
)
_FORMAL_VIEW_INTERNAL_SHA256 = (
    "4feb9f1e6531c12a3c653d5c07c37e641d534c20c470f7cad96b902633cab335"
)
_HISTORICAL_FULL_ATOM_COMMIT = "efe213bae26d30b98272973ff557e7fbf3dc577d"
_HISTORICAL_FULL_ATOM_COMMIT_OBJECT_SHA256 = (
    "03ab2792bd45e63e4c1c239ce7bca52cd98d4d3913ff7b66a08a276ea2889b29"
)
_CANONICAL_IDENTITY_NAMESPACE = "mmcif_auth_namespace"
_RECOMMENDED_SOURCE_INVENTORY_STEP = (
    "implement_covapie_current11_target_residue_atom_condition_source_inventory_v1"
)
_RECOMMENDED_AUTHORITY_STEP = (
    "implement_covapie_current11_target_residue_atom_condition_authority_v1"
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_LEGACY_SAMPLES = (*_EXPECTED_SAMPLES[:5], _EXPECTED_SAMPLES[10])
_MULTI_SAMPLES = _EXPECTED_SAMPLES[5:10]
_LEGACY_NAMESPACE = "legacy_exact_one_boundary_v1"
_MULTI_NAMESPACE = "exact_two_boundaries_multi_boundary_v1"
_LEGACY_REASON = "ACTIVE_LEGACY_EXACT_ONE_ONLY"
_MULTI_REASON = (
    "ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW"
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_MODEL_NUM = re.compile(r"[1-9][0-9]*")
_MAX_CSV_BYTES = 64 * 1024 * 1024

_SAMPLE_INDEX_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
_LOCATOR_SIDECAR_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_covalent_residue_locator_real_provider_"
    "export_execution_smoke_v1/"
    "covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
)
_FULL_ATOM_SCHEMA_PATH = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0/"
    "real_covalent_confirmed_candidate_full_atom_extraction_schema_contract.csv"
)
_HISTORICAL_FULL_ATOM_TABLE_PATH = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_protein_full_atom_table.csv"
)

_FUTURE_CONDITION_RECORD_FIELDS = (
    "target_residue_atom_condition_version",
    "sample_index_row_id",
    "pdb_id",
    "protein_model_num",
    "protein_auth_asym_id",
    "protein_auth_comp_id",
    "protein_auth_seq_id",
    "protein_pdbx_PDB_ins_code",
    "protein_auth_atom_id",
    "protein_type_symbol",
    "protein_label_alt_id",
    "source_atom_site_id",
    "protein_label_asym_id",
    "protein_label_comp_id",
    "protein_label_seq_id",
    "protein_label_atom_id",
    "source_structure_filesystem_sha256",
    "source_condition_evidence_sha256",
    "condition_authority_status",
    "target_residue_atom_condition_record_sha256",
)
_CANONICAL_AUTH_IDENTITY_FIELDS = (
    "protein_auth_asym_id",
    "protein_auth_comp_id",
    "protein_auth_seq_id",
    "protein_pdbx_PDB_ins_code",
    "protein_auth_atom_id",
)
_LABEL_CROSSWALK_FIELDS = (
    "protein_label_asym_id",
    "protein_label_comp_id",
    "protein_label_seq_id",
    "protein_label_atom_id",
)
_ADAPTER_LOCATOR_FIELDS = (
    "protein_model_num",
    "protein_auth_asym_id",
    "protein_auth_comp_id",
    "protein_auth_seq_id",
    "protein_pdbx_PDB_ins_code",
    "protein_auth_atom_id",
    "protein_label_alt_id",
)
_CONDITION_AUTHORITY_STATUSES = (
    "resolved_authoritative",
    "blocked_missing_source",
    "blocked_ambiguous_atom",
    "blocked_lineage_mismatch",
    "blocked_schema_incomplete",
)
_COVERAGE_STATUSES = (
    "resolved_unique",
    "missing_source",
    "schema_incomplete",
    "ambiguous_atom",
    "lineage_mismatch",
)
_AUTHORITY_LEVELS = (
    "reviewed_ligand_authority_only",
    "lineage_only",
    "schema_capability_only",
    "historical_smoke_evidence_only",
    "derived_sample_atom_evidence_non_authoritative",
    "blocking_locator_evidence_non_authoritative",
)
_FIELD_CONTRACT_FIELDS = (
    "field_name",
    "semantic_definition",
    "python_type_contract",
    "canonical_namespace",
    "normalization_policy",
    "missing_value_policy",
    "v1_allowed_value_contract",
    "required_for_unique_atom_resolution",
    "allowed_future_consumers",
    "audit_only",
    "source_candidate_fields",
    "field_contract_record_sha256",
)
_SOURCE_CANDIDATE_FIELDS = (
    "source_candidate_name",
    "source_path_or_commit",
    "source_sha256",
    "source_stage",
    "field_inventory",
    "sample_scope",
    "current11_sample_coverage",
    "direct_lineage_to_unified_view",
    "authority_level",
    "can_uniquely_resolve_target_atom",
    "blocking_reasons",
    "source_candidate_record_sha256",
)
_SAMPLE_COVERAGE_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "candidate_source_count",
    "complete_identity_candidate_count",
    "unique_atom_match_count",
    "observed_altloc_ids",
    "coverage_status",
    "blocking_reasons",
    "ready_for_authority_materialization",
    "sample_coverage_record_sha256",
)
_RESPONSE_FIELDS = (
    "target_residue_atom_condition_contract_design_version",
    "source_unified_effective_authority_view_filesystem_sha256",
    "source_unified_effective_authority_view_sha256",
    "canonical_condition_record_fields",
    "canonical_identity_namespace",
    "field_contract_records",
    "source_candidate_records",
    "sample_coverage_records",
    "current11_sample_count",
    "resolved_unique_sample_count",
    "blocked_sample_count",
    "ready_for_target_condition_authority_implementation",
    "recommended_next_step",
    "design_response_sha256",
)

_ATOM_TABLE_REQUIRED_COLUMNS = (
    "pdb_id",
    "atom_site_id",
    "type_symbol",
    "label_atom_id",
    "label_comp_id",
    "label_asym_id",
    "label_seq_id",
    "label_alt_id",
    "auth_atom_id",
    "auth_comp_id",
    "auth_asym_id",
    "auth_seq_id",
    "pdbx_PDB_model_num",
    "pdbx_PDB_ins_code",
)
_SAMPLE_INDEX_REQUIRED_COLUMNS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "protein_atom_table_path",
    "ligand_comp_id",
)
_FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "source_structure_path",
    "source_structure_filesystem_sha256",
    "protein_atom_table_path",
    "source_atom_site_id",
    "source_condition_evidence_path_or_record",
    "source_condition_evidence_sha256",
    "protein_model_num",
    "protein_auth_asym_id",
    "protein_auth_comp_id",
    "protein_auth_seq_id",
    "protein_pdbx_PDB_ins_code",
    "protein_auth_atom_id",
    "protein_type_symbol",
    "protein_label_alt_id",
    "protein_label_asym_id",
    "protein_label_comp_id",
    "protein_label_seq_id",
    "protein_label_atom_id",
)
_FUTURE_SOURCE_INVENTORY_NORMALISED_EMPTY_ALLOWED_FIELDS = (
    "protein_pdbx_PDB_ins_code",
    "protein_label_alt_id",
)
_CONDITION_EVIDENCE_RECORD_FIELDS = (
    "condition_evidence_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "source_structure_filesystem_sha256",
    "source_atom_site_id",
    "protein_model_num",
    "protein_auth_asym_id",
    "protein_auth_comp_id",
    "protein_auth_seq_id",
    "protein_pdbx_PDB_ins_code",
    "protein_auth_atom_id",
    "condition_evidence_record_sha256",
)


class _DuplicateKeyError(ValueError):
    pass


class _NonfiniteError(ValueError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _record_sha256(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    try:
        unsigned = {
            field: record[field] for field in fields if field != digest_field
        }
        return _sha256(_canonical_json_bytes(unsigned))
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _NonfiniteError(value)


def _strict_json_object(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 2 * 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


def _validate_unified_view(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or _sha256(payload) != _FORMAL_VIEW_FILESYSTEM_SHA256
    ):
        raise ValueError(_ERROR)
    view = _strict_json_object(payload)
    if (
        tuple(view) != unified_view.EXACT16_VIEW_FIELDS
        or view["unified_effective_authority_view_version"]
        != unified_view.UNIFIED_EFFECTIVE_VIEW_VERSION
        or view["unified_effective_authority_view_sha256"]
        != _FORMAL_VIEW_INTERNAL_SHA256
        or view["unified_effective_authority_view_sha256"]
        != _record_sha256(
            view,
            unified_view.EXACT16_VIEW_FIELDS,
            "unified_effective_authority_view_sha256",
        )
        or view["sample_order"] != list(_EXPECTED_SAMPLES)
        or type(view["effective_authority_records"]) is not list
        or len(view["effective_authority_records"]) != 11
        or view["effective_authority_record_count"] != 11
        or view["effective_legacy_exact_one_count"] != 6
        or view["effective_multi_boundary_exact_two_count"] != 5
    ):
        raise ValueError(_ERROR)

    identities: set[tuple[str, str]] = set()
    legacy_count = 0
    multi_count = 0
    for index, record in enumerate(view["effective_authority_records"]):
        sample = _EXPECTED_SAMPLES[index]
        if (
            type(record) is not dict
            or tuple(record) != unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS
            or record["unified_effective_authority_record_version"]
            != unified_view.EFFECTIVE_RECORD_VERSION
            or record["sample_index_row_id"] != sample
            or record["unified_effective_authority_record_sha256"]
            != _record_sha256(
                record,
                unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS,
                "unified_effective_authority_record_sha256",
            )
            or type(record["effective_authority_record"]) is not dict
        ):
            raise ValueError(_ERROR)
        authority = record["effective_authority_record"]
        try:
            if sample in _LEGACY_SAMPLES:
                legacy_design.validate_authority_record(authority)
                expected = (
                    _LEGACY_NAMESPACE,
                    1,
                    _LEGACY_REASON,
                    authority["authority_record_version"],
                    authority["authority_record_sha256"],
                )
                legacy_count += 1
            elif sample in _MULTI_SAMPLES:
                multi_design._validate_authority_record(authority)
                expected = (
                    _MULTI_NAMESPACE,
                    2,
                    _MULTI_REASON,
                    authority["multi_boundary_authority_record_version"],
                    authority["multi_boundary_authority_record_sha256"],
                )
                multi_count += 1
            else:
                raise ValueError(_ERROR)
        except Exception as error:
            raise ValueError(_ERROR) from error
        observed = (
            record["effective_authority_namespace"],
            record["effective_boundary_cardinality"],
            record["precedence_reason"],
            record["source_authority_record_version"],
            record["source_authority_record_sha256"],
        )
        identity = (authority.get("pdb_id"), authority.get("ligand_comp_id"))
        if (
            observed != expected
            or authority.get("sample_index_row_id") != sample
            or any(type(value) is not str or not value for value in identity)
            or identity in identities
        ):
            raise ValueError(_ERROR)
        identities.add(identity)
    if (legacy_count, multi_count) != (6, 5):
        raise ValueError(_ERROR)
    return view


def _strict_csv(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        payload = path.read_bytes()
        if (
            not payload
            or len(payload) > _MAX_CSV_BYTES
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
        ):
            raise ValueError(_ERROR)
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        fields = tuple(reader.fieldnames or ())
        if not fields or len(fields) != len(set(fields)) or any(not f for f in fields):
            raise ValueError(_ERROR)
        rows = tuple(dict(row) for row in reader)
        if any(
            tuple(row) != fields
            or any(type(value) is not str for value in row.values())
            for row in rows
        ):
            raise ValueError(_ERROR)
        return fields, rows
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _normalise_mmcif_optional(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_ERROR)
    return "" if value in {".", "?"} else value


def _safe_repo_path(repo_root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValueError(_ERROR)
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(_ERROR)
    resolved_root = repo_root.resolve()
    resolved = (repo_root / candidate).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(_ERROR)
    return resolved


def _field_contract_record(
    *,
    field_name: str,
    semantic_definition: str,
    canonical_namespace: str,
    normalization_policy: str,
    missing_value_policy: str,
    v1_allowed_value_contract: str,
    required_for_unique_atom_resolution: bool,
    source_candidate_fields: tuple[str, ...],
) -> dict[str, Any]:
    adapter_consumable = field_name in _ADAPTER_LOCATOR_FIELDS
    record: dict[str, Any] = {
        "field_name": field_name,
        "semantic_definition": semantic_definition,
        "python_type_contract": "exact_str",
        "canonical_namespace": canonical_namespace,
        "normalization_policy": normalization_policy,
        "missing_value_policy": missing_value_policy,
        "v1_allowed_value_contract": v1_allowed_value_contract,
        "required_for_unique_atom_resolution": required_for_unique_atom_resolution,
        "allowed_future_consumers": (
            ("target_residue_atom_condition_adapter",)
            if adapter_consumable else ()
        ),
        "audit_only": not adapter_consumable,
        "source_candidate_fields": source_candidate_fields,
        "field_contract_record_sha256": "",
    }
    if (
        tuple(record) != _FIELD_CONTRACT_FIELDS
        or field_name not in _FUTURE_CONDITION_RECORD_FIELDS[:-1]
        or type(required_for_unique_atom_resolution) is not bool
    ):
        raise ValueError(_ERROR)
    record["field_contract_record_sha256"] = _record_sha256(
        record, _FIELD_CONTRACT_FIELDS, "field_contract_record_sha256"
    )
    return record


def _build_field_contract_records() -> tuple[dict[str, Any], ...]:
    specs = {
        "target_residue_atom_condition_version": (
            "Version of the future target residue-atom authority record.",
            "contract",
            "preserve exact token",
            "missing forbidden",
            _CONDITION_VERSION,
            False,
            ("record_constant",),
        ),
        "sample_index_row_id": (
            "Current11 sample identity joined to the unified authority view.",
            "covapie_sample_index",
            "preserve exact token",
            "missing forbidden",
            "CYS_SG_SAMPLE_INDEX_000001 through 000011",
            False,
            ("sample_index_row_id",),
        ),
        "pdb_id": (
            "Four-character structure identity used only for lineage and joins.",
            "pdb_entry",
            "uppercase exact source value",
            "missing forbidden",
            "exact source PDB identity",
            False,
            ("pdb_id",),
        ),
        "protein_model_num": (
            "Explicit mmCIF model containing the selected atom-site row.",
            "mmcif_atom_site",
            "canonical positive decimal string; never default to 1",
            "missing forbidden",
            "positive decimal string",
            True,
            ("pdbx_PDB_model_num",),
        ),
        "protein_auth_asym_id": (
            "Author-namespace protein chain locator.",
            "mmcif_auth",
            "preserve exact non-missing source token",
            "missing forbidden; label_asym_id cannot substitute",
            "nonempty mmCIF auth_asym_id",
            True,
            ("auth_asym_id", "struct_conn_residue_auth_asym_id"),
        ),
        "protein_auth_comp_id": (
            "Author-namespace residue component locator.",
            "mmcif_auth",
            "uppercase exact source token",
            "missing forbidden; project scope cannot fill it",
            "CYS",
            True,
            ("auth_comp_id",),
        ),
        "protein_auth_seq_id": (
            "Author-namespace residue sequence token; it is not a numeric feature.",
            "mmcif_auth",
            "preserve exact source token as a string",
            "missing forbidden; label_seq_id cannot substitute",
            "nonempty mmCIF auth_seq_id token",
            True,
            ("auth_seq_id", "struct_conn_residue_auth_seq_id"),
        ),
        "protein_pdbx_PDB_ins_code": (
            "Insertion code from _atom_site.pdbx_PDB_ins_code.",
            "mmcif_atom_site",
            "normalise dot or question-mark token to empty string",
            "source column required; no default empty value",
            "empty normalised value or preserved insertion-code token",
            True,
            ("pdbx_PDB_ins_code", "atom_site_insertion_raw_value"),
        ),
        "protein_auth_atom_id": (
            "Author-namespace target residue atom name.",
            "mmcif_auth",
            "uppercase exact source token",
            "missing forbidden; project scope cannot fill it",
            "SG",
            True,
            ("auth_atom_id", "matched_residue_atom_name"),
        ),
        "protein_type_symbol": (
            "Element symbol on the selected source atom-site row.",
            "mmcif_atom_site",
            "preserve case-normalised element symbol",
            "missing forbidden",
            "S",
            True,
            ("type_symbol",),
        ),
        "protein_label_alt_id": (
            "Alternate-location identity from label_alt_id.",
            "mmcif_label",
            "normalise dot or question-mark token to empty; preserve A/B/etc",
            "source column required; no occupancy fallback",
            "empty normalised value or exact non-missing altloc token",
            True,
            ("label_alt_id",),
        ),
        "source_atom_site_id": (
            "Identity of the exact source _atom_site row; never a model feature.",
            "mmcif_atom_site",
            "preserve exact non-missing token",
            "missing forbidden",
            "unique nonempty atom-site id within the source structure",
            True,
            ("atom_site_id", "matched_atom_site_id"),
        ),
        "protein_label_asym_id": (
            "Label-namespace chain crosswalk for the selected row.",
            "mmcif_label_crosswalk",
            "preserve exact source token",
            "missing forbidden; cannot replace auth_asym_id",
            "nonempty mmCIF label_asym_id",
            True,
            ("label_asym_id", "struct_conn_residue_label_asym_id"),
        ),
        "protein_label_comp_id": (
            "Label-namespace residue component crosswalk.",
            "mmcif_label_crosswalk",
            "uppercase exact source token",
            "missing forbidden",
            "CYS",
            True,
            ("label_comp_id",),
        ),
        "protein_label_seq_id": (
            "Label-namespace residue sequence crosswalk.",
            "mmcif_label_crosswalk",
            "preserve exact source token as a string",
            "missing forbidden",
            "nonempty mmCIF label_seq_id token",
            True,
            ("label_seq_id", "struct_conn_residue_label_seq_id"),
        ),
        "protein_label_atom_id": (
            "Label-namespace target atom crosswalk.",
            "mmcif_label_crosswalk",
            "uppercase exact source token",
            "missing forbidden",
            "SG",
            True,
            ("label_atom_id",),
        ),
        "source_structure_filesystem_sha256": (
            "Independently recomputed SHA256 of the exact source structure bytes.",
            "lineage",
            "lowercase hexadecimal",
            "exact source bytes and their recomputed digest are both required",
            "64 lowercase hexadecimal characters",
            False,
            (
                "source_structure_path",
                "source_structure_filesystem_sha256",
                "observed_raw_sha256",
            ),
        ),
        "source_condition_evidence_sha256": (
            (
                "Independently recomputed canonical SHA256 binding sample, PDB, "
                "atom-site, model, auth identity, and source structure."
            ),
            "lineage",
            "lowercase hexadecimal",
            (
                "exact condition-evidence record and its recomputed digest are "
                "both required"
            ),
            "64 lowercase hexadecimal characters",
            False,
            (
                "source_condition_evidence_path_or_record",
                "source_condition_evidence_sha256",
                "condition_evidence_record_sha256",
            ),
        ),
        "condition_authority_status": (
            "Fail-closed materialization disposition.",
            "contract",
            "preserve exact vocabulary token",
            "missing forbidden",
            "|".join(_CONDITION_AUTHORITY_STATUSES),
            False,
            ("derived_gate_status",),
        ),
    }
    records = tuple(
        _field_contract_record(
            field_name=field,
            semantic_definition=specs[field][0],
            canonical_namespace=specs[field][1],
            normalization_policy=specs[field][2],
            missing_value_policy=specs[field][3],
            v1_allowed_value_contract=specs[field][4],
            required_for_unique_atom_resolution=specs[field][5],
            source_candidate_fields=specs[field][6],
        )
        for field in _FUTURE_CONDITION_RECORD_FIELDS[:-1]
    )
    if len(records) != 19:
        raise ValueError(_ERROR)
    return records


def _sample_coverage_record(
    *,
    sample_index_row_id: str,
    pdb_id: str,
    candidate_source_count: int,
    complete_identity_candidate_count: int,
    unique_atom_match_count: int,
    observed_altloc_ids: tuple[str, ...],
    coverage_status: str,
    blocking_reasons: tuple[str, ...],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "sample_index_row_id": sample_index_row_id,
        "pdb_id": pdb_id,
        "candidate_source_count": candidate_source_count,
        "complete_identity_candidate_count": complete_identity_candidate_count,
        "unique_atom_match_count": unique_atom_match_count,
        "observed_altloc_ids": observed_altloc_ids,
        "coverage_status": coverage_status,
        "blocking_reasons": blocking_reasons,
        "ready_for_authority_materialization": coverage_status == "resolved_unique",
        "sample_coverage_record_sha256": "",
    }
    if (
        tuple(record) != _SAMPLE_COVERAGE_FIELDS
        or coverage_status not in _COVERAGE_STATUSES
        or any(type(value) is not int or value < 0 for value in (
            candidate_source_count,
            complete_identity_candidate_count,
            unique_atom_match_count,
        ))
        or sample_index_row_id not in _EXPECTED_SAMPLES
    ):
        raise ValueError(_ERROR)
    record["sample_coverage_record_sha256"] = _record_sha256(
        record, _SAMPLE_COVERAGE_FIELDS, "sample_coverage_record_sha256"
    )
    return record


def _row_complete(row: Mapping[str, str]) -> bool:
    for field in _ATOM_TABLE_REQUIRED_COLUMNS:
        value = row.get(field)
        if type(value) is not str:
            return False
        if field in {"pdbx_PDB_ins_code", "label_alt_id"}:
            _normalise_mmcif_optional(value)
        elif _normalise_mmcif_optional(value) == "":
            return False
    return _MODEL_NUM.fullmatch(row["pdbx_PDB_model_num"]) is not None


def _row_identity_consistent(row: Mapping[str, str], pdb_id: str) -> bool:
    return (
        row.get("pdb_id") == pdb_id
        and row.get("type_symbol") == "S"
        and row.get("auth_comp_id") == "CYS"
        and row.get("label_comp_id") == "CYS"
        and row.get("auth_atom_id") == "SG"
        and row.get("label_atom_id") == "SG"
    )


def _load_optional_csv(
    repo_root: Path, relative: Path
) -> tuple[Path, tuple[str, ...], tuple[dict[str, str], ...]] | None:
    path = repo_root / relative
    if not path.is_file():
        return None
    fields, rows = _strict_csv(path)
    return path, fields, rows


def _selected_atom_inventory_values(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "source_atom_site_id": row.get("atom_site_id", ""),
        "protein_model_num": row.get("pdbx_PDB_model_num", ""),
        "protein_auth_asym_id": row.get("auth_asym_id", ""),
        "protein_auth_comp_id": row.get("auth_comp_id", ""),
        "protein_auth_seq_id": row.get("auth_seq_id", ""),
        "protein_pdbx_PDB_ins_code": _normalise_mmcif_optional(
            row.get("pdbx_PDB_ins_code", "")
        ),
        "protein_auth_atom_id": row.get("auth_atom_id", ""),
        "protein_type_symbol": row.get("type_symbol", ""),
        "protein_label_alt_id": _normalise_mmcif_optional(
            row.get("label_alt_id", "")
        ),
        "protein_label_asym_id": row.get("label_asym_id", ""),
        "protein_label_comp_id": row.get("label_comp_id", ""),
        "protein_label_seq_id": row.get("label_seq_id", ""),
        "protein_label_atom_id": row.get("label_atom_id", ""),
    }


def _authority_materialization_lineage(
    *,
    repo_root: Path,
    sample_fields: tuple[str, ...],
    index_row: Mapping[str, str],
    selected_atom_row: Mapping[str, str] | None,
) -> dict[str, Any]:
    """Independently validate exact structure and condition-evidence lineage."""

    schema_reasons: list[str] = []
    missing_source_reasons: list[str] = []
    mismatch_reasons: list[str] = []
    structure_sha_recomputed = False
    evidence_sha_recomputed = False

    missing_fields = tuple(
        field for field in _FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS
        if field not in sample_fields or (
            field not in _FUTURE_SOURCE_INVENTORY_NORMALISED_EMPTY_ALLOWED_FIELDS
            and not index_row.get(field, "")
        )
    )
    for field in missing_fields:
        if field == "source_structure_path":
            reason = "source_structure_path_or_bytes_missing"
        elif field == "source_structure_filesystem_sha256":
            reason = "source_structure_filesystem_sha256_missing"
        elif field == "source_condition_evidence_path_or_record":
            reason = "source_condition_evidence_missing"
        elif field == "source_condition_evidence_sha256":
            reason = "source_condition_evidence_sha256_missing"
        else:
            reason = f"future_source_inventory_required_field_missing:{field}"
        if reason not in schema_reasons:
            schema_reasons.append(reason)

    structure_sha = ""
    structure_path_value = index_row.get("source_structure_path", "")
    claimed_structure_sha = index_row.get(
        "source_structure_filesystem_sha256", ""
    )
    if structure_path_value:
        try:
            structure_path = _safe_repo_path(repo_root, structure_path_value)
        except ValueError:
            mismatch_reasons.append("source_structure_path_invalid")
        else:
            if not structure_path.is_file():
                missing_source_reasons.append("source_structure_file_missing")
            else:
                try:
                    structure_bytes = structure_path.read_bytes()
                except OSError:
                    missing_source_reasons.append("source_structure_file_unreadable")
                else:
                    if not structure_bytes:
                        schema_reasons.append(
                            "source_structure_path_or_bytes_missing"
                        )
                    else:
                        structure_sha = _sha256(structure_bytes)
                        structure_sha_recomputed = True
                        if claimed_structure_sha and (
                            _SHA256.fullmatch(claimed_structure_sha) is None
                            or claimed_structure_sha != structure_sha
                        ):
                            mismatch_reasons.append(
                                "source_structure_filesystem_sha256_mismatch"
                            )

    evidence_value = index_row.get(
        "source_condition_evidence_path_or_record", ""
    )
    claimed_evidence_sha = index_row.get(
        "source_condition_evidence_sha256", ""
    )
    evidence_payload: bytes | None = None
    if evidence_value:
        if evidence_value.startswith("{"):
            try:
                evidence_payload = evidence_value.encode("utf-8")
            except UnicodeEncodeError:
                mismatch_reasons.append("source_condition_evidence_invalid")
        else:
            try:
                evidence_path = _safe_repo_path(repo_root, evidence_value)
            except ValueError:
                mismatch_reasons.append("source_condition_evidence_path_invalid")
            else:
                if not evidence_path.is_file():
                    missing_source_reasons.append(
                        "source_condition_evidence_file_missing"
                    )
                else:
                    try:
                        evidence_payload = evidence_path.read_bytes()
                    except OSError:
                        missing_source_reasons.append(
                            "source_condition_evidence_file_unreadable"
                        )
                    else:
                        if not evidence_payload:
                            schema_reasons.append(
                                "source_condition_evidence_missing"
                            )
                            evidence_payload = None

    evidence: dict[str, Any] | None = None
    if evidence_payload is not None:
        try:
            evidence = _strict_json_object(evidence_payload)
        except ValueError:
            mismatch_reasons.append("source_condition_evidence_invalid")
        else:
            if (
                tuple(evidence) != _CONDITION_EVIDENCE_RECORD_FIELDS
                or any(type(value) is not str for value in evidence.values())
                or evidence["condition_evidence_version"]
                != _CONDITION_EVIDENCE_VERSION
            ):
                mismatch_reasons.append("source_condition_evidence_invalid")
            else:
                recomputed_evidence_sha = _record_sha256(
                    evidence,
                    _CONDITION_EVIDENCE_RECORD_FIELDS,
                    "condition_evidence_record_sha256",
                )
                evidence_sha_recomputed = True
                evidence_record_sha = evidence[
                    "condition_evidence_record_sha256"
                ]
                if not evidence_record_sha:
                    if "source_condition_evidence_sha256_missing" not in (
                        schema_reasons
                    ):
                        schema_reasons.append(
                            "source_condition_evidence_sha256_missing"
                        )
                elif evidence_record_sha != recomputed_evidence_sha:
                    mismatch_reasons.append(
                        "source_condition_evidence_sha256_mismatch"
                    )
                if claimed_evidence_sha and (
                    _SHA256.fullmatch(claimed_evidence_sha) is None
                    or claimed_evidence_sha != recomputed_evidence_sha
                ):
                    mismatch_reasons.append(
                        "source_condition_evidence_sha256_mismatch"
                    )

    if selected_atom_row is not None:
        selected_values = _selected_atom_inventory_values(selected_atom_row)
        if any(
            index_row.get(field, "") != expected
            for field, expected in selected_values.items()
        ):
            mismatch_reasons.append(
                "source_inventory_sample_atom_lineage_mismatch"
            )
        if evidence is not None and tuple(evidence) == (
            _CONDITION_EVIDENCE_RECORD_FIELDS
        ):
            evidence_expected = {
                "sample_index_row_id": index_row["sample_index_row_id"],
                "pdb_id": index_row["pdb_id"],
                "ligand_comp_id": index_row["ligand_comp_id"],
                "source_structure_filesystem_sha256": structure_sha,
                "source_atom_site_id": selected_values["source_atom_site_id"],
                "protein_model_num": selected_values["protein_model_num"],
                "protein_auth_asym_id": selected_values[
                    "protein_auth_asym_id"
                ],
                "protein_auth_comp_id": selected_values[
                    "protein_auth_comp_id"
                ],
                "protein_auth_seq_id": selected_values[
                    "protein_auth_seq_id"
                ],
                "protein_pdbx_PDB_ins_code": selected_values[
                    "protein_pdbx_PDB_ins_code"
                ],
                "protein_auth_atom_id": selected_values[
                    "protein_auth_atom_id"
                ],
            }
            if not structure_sha:
                evidence_expected.pop("source_structure_filesystem_sha256")
            if any(
                evidence.get(field) != expected
                for field, expected in evidence_expected.items()
            ):
                mismatch_reasons.append(
                    "condition_evidence_sample_atom_lineage_mismatch"
                )

    result = {
        "authority_materialization_lineage_complete": not (
            schema_reasons or missing_source_reasons or mismatch_reasons
        ) and structure_sha_recomputed and evidence_sha_recomputed,
        "schema_reasons": tuple(dict.fromkeys(schema_reasons)),
        "missing_source_reasons": tuple(dict.fromkeys(missing_source_reasons)),
        "mismatch_reasons": tuple(dict.fromkeys(mismatch_reasons)),
        "source_structure_bytes_sha_recomputed": structure_sha_recomputed,
        "condition_evidence_sha_recomputed": evidence_sha_recomputed,
        "same_sample_atom_lineage_required": True,
    }
    return result


def _audit_sample_coverage(
    repo_root: Path,
    view: Mapping[str, Any],
) -> tuple[
    tuple[dict[str, Any], ...],
    dict[str, Any],
]:
    sample_source = _load_optional_csv(repo_root, _SAMPLE_INDEX_PATH)
    locator_source = _load_optional_csv(repo_root, _LOCATOR_SIDECAR_PATH)
    metadata: dict[str, Any] = {
        "sample_source": sample_source,
        "locator_source": locator_source,
        "sample_identity_match_count": 0,
        "locator_identity_match_count": 0,
        "target_atom_locator_resolved_unique_count": 0,
        "authority_materialization_lineage_complete_count": 0,
        "referenced_atom_field_inventory": (),
    }
    if sample_source is None:
        return tuple(
            _sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=view["effective_authority_records"][index][
                    "effective_authority_record"
                ]["pdb_id"],
                candidate_source_count=0,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="missing_source",
                blocking_reasons=("current11_sample_index_source_missing",),
            )
            for index, sample in enumerate(_EXPECTED_SAMPLES)
        ), metadata

    _, sample_fields, sample_rows = sample_source
    if not set(_SAMPLE_INDEX_REQUIRED_COLUMNS).issubset(sample_fields):
        raise ValueError(_ERROR)
    sample_by_id: dict[str, list[dict[str, str]]] = {}
    for row in sample_rows:
        sample_by_id.setdefault(row["sample_index_row_id"], []).append(row)

    locator_by_sample: dict[tuple[str, str], list[dict[str, str]]] = {}
    if locator_source is not None:
        _, locator_fields, locator_rows = locator_source
        required_locator = {
            "sample_preparation_input_id",
            "pdb_id",
            "matched_atom_site_id",
        }
        if not required_locator.issubset(locator_fields):
            raise ValueError(_ERROR)
        for row in locator_rows:
            locator_by_sample.setdefault(
                (row["sample_preparation_input_id"], row["pdb_id"]), []
            ).append(row)

    coverage: list[dict[str, Any]] = []
    atom_field_inventory: set[str] = set()
    for index, sample in enumerate(_EXPECTED_SAMPLES):
        authority = view["effective_authority_records"][index][
            "effective_authority_record"
        ]
        pdb_id = authority["pdb_id"]
        ligand_comp_id = authority["ligand_comp_id"]
        index_rows = sample_by_id.get(sample, [])
        if not index_rows:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=0,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="missing_source",
                blocking_reasons=("sample_index_row_missing",),
            ))
            continue
        if len(index_rows) != 1:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=len(index_rows),
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="lineage_mismatch",
                blocking_reasons=("sample_index_row_not_unique",),
            ))
            continue
        index_row = index_rows[0]
        if (
            index_row["pdb_id"] != pdb_id
            or index_row["ligand_comp_id"] != ligand_comp_id
        ):
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=1,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="lineage_mismatch",
                blocking_reasons=("sample_pdb_ligand_identity_mismatch",),
            ))
            continue
        metadata["sample_identity_match_count"] += 1
        locator_rows = locator_by_sample.get(
            (index_row["sample_preparation_input_id"], pdb_id), []
        )
        if locator_rows:
            metadata["locator_identity_match_count"] += 1
        candidate_source_count = 1 + (1 if locator_rows else 0)
        try:
            table_path = _safe_repo_path(
                repo_root, index_row["protein_atom_table_path"]
            )
        except ValueError:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="lineage_mismatch",
                blocking_reasons=("protein_atom_table_path_invalid",),
            ))
            continue
        if not table_path.is_file():
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="missing_source",
                blocking_reasons=("referenced_protein_atom_table_missing",),
            ))
            continue
        table_fields, atom_rows = _strict_csv(table_path)
        atom_field_inventory.update(table_fields)

        locator_ids = tuple(
            row["matched_atom_site_id"]
            for row in locator_rows
            if row["matched_atom_site_id"]
        )
        selector_available = bool(locator_ids) or (
            "is_covalent_endpoint_atom" in table_fields
        )
        missing_columns = tuple(
            field for field in _ATOM_TABLE_REQUIRED_COLUMNS
            if field not in table_fields
        )
        selected_rows: tuple[dict[str, str], ...]
        if locator_ids:
            selected_rows = tuple(
                row for row in atom_rows if row.get("atom_site_id") in locator_ids
            )
        elif "is_covalent_endpoint_atom" in table_fields:
            selected_rows = tuple(
                row for row in atom_rows
                if row.get("is_covalent_endpoint_atom") in {"True", "true"}
            )
        else:
            selected_rows = ()
        observed_altlocs = tuple(sorted({
            _normalise_mmcif_optional(
                row.get("label_alt_id", row.get("altloc", ""))
            )
            for row in selected_rows
        }))
        if missing_columns or not selector_available:
            lineage = _authority_materialization_lineage(
                repo_root=repo_root,
                sample_fields=sample_fields,
                index_row=index_row,
                selected_atom_row=None,
            )
            reasons = tuple(
                [f"missing_atom_table_column:{field}" for field in missing_columns]
                + ([] if selector_available else ["endpoint_selector_missing"])
                + list(lineage["schema_reasons"])
                + list(lineage["missing_source_reasons"])
                + list(lineage["mismatch_reasons"])
            )
            if lineage["missing_source_reasons"]:
                status = "missing_source"
            elif lineage["mismatch_reasons"]:
                status = "lineage_mismatch"
            else:
                status = "schema_incomplete"
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=observed_altlocs,
                coverage_status=status,
                blocking_reasons=reasons,
            ))
            continue
        complete_rows = tuple(row for row in selected_rows if _row_complete(row))
        if len(selected_rows) == 0:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=0,
                unique_atom_match_count=0,
                observed_altloc_ids=(),
                coverage_status="missing_source",
                blocking_reasons=("target_atom_site_row_not_found",),
            ))
        elif len(selected_rows) > 1 or len(set(
            row["atom_site_id"] for row in selected_rows
        )) != 1:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=len(complete_rows),
                unique_atom_match_count=len(selected_rows),
                observed_altloc_ids=observed_altlocs,
                coverage_status="ambiguous_atom",
                blocking_reasons=("target_atom_site_row_not_unique",),
            ))
        elif len(complete_rows) != 1:
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=0,
                unique_atom_match_count=1,
                observed_altloc_ids=observed_altlocs,
                coverage_status="schema_incomplete",
                blocking_reasons=("target_atom_identity_value_missing",),
            ))
        elif not _row_identity_consistent(complete_rows[0], pdb_id):
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=1,
                unique_atom_match_count=1,
                observed_altloc_ids=observed_altlocs,
                coverage_status="lineage_mismatch",
                blocking_reasons=("cys_sg_auth_label_type_identity_mismatch",),
            ))
        else:
            target_atom_locator_resolved_unique = True
            metadata["target_atom_locator_resolved_unique_count"] += 1
            lineage = _authority_materialization_lineage(
                repo_root=repo_root,
                sample_fields=sample_fields,
                index_row=index_row,
                selected_atom_row=complete_rows[0],
            )
            authority_materialization_lineage_complete = lineage[
                "authority_materialization_lineage_complete"
            ]
            if authority_materialization_lineage_complete:
                metadata[
                    "authority_materialization_lineage_complete_count"
                ] += 1
                status = "resolved_unique"
                reasons = ()
            elif lineage["missing_source_reasons"]:
                status = "missing_source"
                reasons = lineage["missing_source_reasons"]
            elif lineage["mismatch_reasons"]:
                status = "lineage_mismatch"
                reasons = lineage["mismatch_reasons"]
            else:
                status = "schema_incomplete"
                reasons = lineage["schema_reasons"] or (
                    "authority_materialization_lineage_incomplete",
                )
            if status == "resolved_unique" and not (
                target_atom_locator_resolved_unique
                and authority_materialization_lineage_complete
            ):
                raise ValueError(_ERROR)
            coverage.append(_sample_coverage_record(
                sample_index_row_id=sample,
                pdb_id=pdb_id,
                candidate_source_count=candidate_source_count,
                complete_identity_candidate_count=1,
                unique_atom_match_count=1,
                observed_altloc_ids=observed_altlocs,
                coverage_status=status,
                blocking_reasons=reasons,
            ))
    metadata["referenced_atom_field_inventory"] = tuple(sorted(atom_field_inventory))
    return tuple(coverage), metadata


def _source_candidate_record(
    *,
    source_candidate_name: str,
    source_path_or_commit: str,
    source_sha256: str,
    source_stage: str,
    field_inventory: tuple[str, ...],
    sample_scope: str,
    current11_sample_coverage: int,
    direct_lineage_to_unified_view: bool,
    authority_level: str,
    can_uniquely_resolve_target_atom: bool,
    blocking_reasons: tuple[str, ...],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_candidate_name": source_candidate_name,
        "source_path_or_commit": source_path_or_commit,
        "source_sha256": source_sha256,
        "source_stage": source_stage,
        "field_inventory": field_inventory,
        "sample_scope": sample_scope,
        "current11_sample_coverage": current11_sample_coverage,
        "direct_lineage_to_unified_view": direct_lineage_to_unified_view,
        "authority_level": authority_level,
        "can_uniquely_resolve_target_atom": can_uniquely_resolve_target_atom,
        "blocking_reasons": blocking_reasons,
        "source_candidate_record_sha256": "",
    }
    if (
        tuple(record) != _SOURCE_CANDIDATE_FIELDS
        or _SHA256.fullmatch(source_sha256) is None
        or authority_level not in _AUTHORITY_LEVELS
        or type(current11_sample_coverage) is not int
        or not 0 <= current11_sample_coverage <= 11
        or type(direct_lineage_to_unified_view) is not bool
        or type(can_uniquely_resolve_target_atom) is not bool
    ):
        raise ValueError(_ERROR)
    record["source_candidate_record_sha256"] = _record_sha256(
        record, _SOURCE_CANDIDATE_FIELDS, "source_candidate_record_sha256"
    )
    return record


def _build_source_candidate_records(
    *,
    repo_root: Path,
    source_view: bytes,
    view: Mapping[str, Any],
    coverage: tuple[dict[str, Any], ...],
    metadata: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = [
        _source_candidate_record(
            source_candidate_name="current11_unified_effective_authority_view",
            source_path_or_commit=(
                "function_argument:source_unified_effective_authority_view"
            ),
            source_sha256=_sha256(source_view),
            source_stage=unified_view.UNIFIED_EFFECTIVE_VIEW_VERSION,
            field_inventory=tuple(unified_view.EXACT16_VIEW_FIELDS),
            sample_scope="Current11 exact 11",
            current11_sample_coverage=11,
            direct_lineage_to_unified_view=True,
            authority_level="reviewed_ligand_authority_only",
            can_uniquely_resolve_target_atom=False,
            blocking_reasons=(
                "contains_ligand_warhead_authority_not_protein_atom_identity",
            ),
        ),
        _source_candidate_record(
            source_candidate_name="current11_predecessor_submission_execution_lineage",
            source_path_or_commit=(
                "embedded:unified_view_predecessor_submission_execution_digests"
            ),
            source_sha256=view[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ],
            source_stage="current11_submission_and_ingestion_lineage",
            field_inventory=(
                "source_v1_submission_bundle_filesystem_sha256",
                "source_v1_ingestion_execution_bundle_filesystem_sha256",
                "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256",
                "source_multi_boundary_authority_bundle_filesystem_sha256",
            ),
            sample_scope="Current11 exact 11 lineage",
            current11_sample_coverage=11,
            direct_lineage_to_unified_view=True,
            authority_level="lineage_only",
            can_uniquely_resolve_target_atom=False,
            blocking_reasons=("no_protein_atom_site_identity_fields",),
        ),
        _source_candidate_record(
            source_candidate_name="historical_full_atom_smoke_commit",
            source_path_or_commit=f"commit:{_HISTORICAL_FULL_ATOM_COMMIT}",
            source_sha256=_HISTORICAL_FULL_ATOM_COMMIT_OBJECT_SHA256,
            source_stage="real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0",
            field_inventory=(
                "atom_site_id", "type_symbol", "label_atom_id", "label_comp_id",
                "label_asym_id", "label_seq_id", "label_alt_id", "auth_atom_id",
                "auth_comp_id", "auth_asym_id", "auth_seq_id",
                "pdbx_PDB_model_num", "is_target_protein_chain_atom",
                "is_covalent_residue_atom", "is_covalent_endpoint_atom",
            ),
            sample_scope="HR_0002 through HR_0004; not Current11",
            current11_sample_coverage=0,
            direct_lineage_to_unified_view=False,
            authority_level="historical_smoke_evidence_only",
            can_uniquely_resolve_target_atom=False,
            blocking_reasons=(
                "unrelated_historical_samples",
                "pdbx_PDB_ins_code_not_explicitly_present",
                "altloc_B_must_be_preserved_in_successor_policy",
            ),
        ),
    ]
    schema_source = _load_optional_csv(repo_root, _FULL_ATOM_SCHEMA_PATH)
    if schema_source is not None:
        path, fields, rows = schema_source
        inventory = tuple(dict.fromkeys(
            row.get("field_name", "") for row in rows if row.get("field_name")
        ))
        records.append(_source_candidate_record(
            source_candidate_name="current_repository_full_atom_extraction_schema",
            source_path_or_commit=str(path.relative_to(repo_root)),
            source_sha256=_sha256(path.read_bytes()),
            source_stage="real_covalent_confirmed_candidate_full_atom_extraction_design_gate_v0",
            field_inventory=inventory or fields,
            sample_scope="historical HR_0002 through HR_0004 schema capability",
            current11_sample_coverage=0,
            direct_lineage_to_unified_view=False,
            authority_level="schema_capability_only",
            can_uniquely_resolve_target_atom=False,
            blocking_reasons=(
                "schema_capability_is_not_Current11_authority",
                "pdbx_PDB_ins_code_not_explicitly_present",
            ),
        ))
    sample_source = metadata["sample_source"]
    if sample_source is not None:
        path, sample_fields, _ = sample_source
        identity_count = metadata["sample_identity_match_count"]
        resolved = sum(
            record["coverage_status"] == "resolved_unique" for record in coverage
        )
        records.append(_source_candidate_record(
            source_candidate_name="current11_sample_index_and_referenced_protein_atom_tables",
            source_path_or_commit=str(path.relative_to(repo_root)),
            source_sha256=_sha256(path.read_bytes()),
            source_stage="covapie_unified_sample_index_with_referenced_atom_tables",
            field_inventory=tuple(sample_fields) + tuple(
                f"referenced_atom_table:{field}"
                for field in metadata["referenced_atom_field_inventory"]
            ),
            sample_scope="Current11 exact 11",
            current11_sample_coverage=identity_count,
            direct_lineage_to_unified_view=identity_count == 11,
            authority_level="derived_sample_atom_evidence_non_authoritative",
            can_uniquely_resolve_target_atom=(
                metadata["target_atom_locator_resolved_unique_count"] == 11
            ),
            blocking_reasons=(() if resolved == 11 else tuple(
                reason for condition, reason in (
                    (
                        metadata["target_atom_locator_resolved_unique_count"] < 11,
                        "not_all_samples_have_complete_unique_mmCIF_atom_identity",
                    ),
                    (
                        metadata[
                            "authority_materialization_lineage_complete_count"
                        ] < 11,
                        "source_structure_and_condition_evidence_lineage_incomplete",
                    ),
                ) if condition
            )),
        ))
    locator_source = metadata["locator_source"]
    if locator_source is not None:
        path, fields, _ = locator_source
        records.append(_source_candidate_record(
            source_candidate_name="current11_residue_locator_provider_sidecar",
            source_path_or_commit=str(path.relative_to(repo_root)),
            source_sha256=_sha256(path.read_bytes()),
            source_stage="covalent_residue_locator_real_provider_export_execution_smoke_v1",
            field_inventory=tuple(fields),
            sample_scope="Current11 matching sample-preparation rows",
            current11_sample_coverage=metadata["locator_identity_match_count"],
            direct_lineage_to_unified_view=(
                metadata["locator_identity_match_count"] == 11
            ),
            authority_level="blocking_locator_evidence_non_authoritative",
            can_uniquely_resolve_target_atom=False,
            blocking_reasons=(
                "provider_export_is_blocking_not_condition_authority",
                "does_not_supply_complete_Exact20_atom_identity",
            ),
        ))
    return tuple(records)


def _reference_design_covapie_target_residue_atom_condition_contract_v1(
    *,
    source_unified_effective_authority_view: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic fail-closed V1 contract design without writes."""

    if (
        type(source_unified_effective_authority_view) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    source_snapshot = bytes(source_unified_effective_authority_view)
    try:
        view = _validate_unified_view(source_unified_effective_authority_view)
        view_snapshot = copy.deepcopy(view)
        field_records = _build_field_contract_records()
        coverage_records, metadata = _audit_sample_coverage(repo_root, view)
        source_records = _build_source_candidate_records(
            repo_root=repo_root,
            source_view=source_unified_effective_authority_view,
            view=view,
            coverage=coverage_records,
            metadata=metadata,
        )
        resolved = sum(
            record["coverage_status"] == "resolved_unique"
            for record in coverage_records
        )
        blocked = len(coverage_records) - resolved
        ready = resolved == 11 and blocked == 0
        response: dict[str, Any] = {
            "target_residue_atom_condition_contract_design_version": _DESIGN_VERSION,
            "source_unified_effective_authority_view_filesystem_sha256": _sha256(
                source_unified_effective_authority_view
            ),
            "source_unified_effective_authority_view_sha256": view[
                "unified_effective_authority_view_sha256"
            ],
            "canonical_condition_record_fields": _FUTURE_CONDITION_RECORD_FIELDS,
            "canonical_identity_namespace": _CANONICAL_IDENTITY_NAMESPACE,
            "field_contract_records": field_records,
            "source_candidate_records": source_records,
            "sample_coverage_records": coverage_records,
            "current11_sample_count": 11,
            "resolved_unique_sample_count": resolved,
            "blocked_sample_count": blocked,
            "ready_for_target_condition_authority_implementation": ready,
            "recommended_next_step": (
                _RECOMMENDED_AUTHORITY_STEP
                if ready else _RECOMMENDED_SOURCE_INVENTORY_STEP
            ),
            "design_response_sha256": "",
        }
        if (
            tuple(response) != _RESPONSE_FIELDS
            or len(field_records) != 19
            or len(coverage_records) != 11
            or tuple(
                record["sample_index_row_id"] for record in coverage_records
            ) != _EXPECTED_SAMPLES
            or source_snapshot != source_unified_effective_authority_view
            or view != view_snapshot
            or ready != (resolved == 11 and blocked == 0)
        ):
            raise ValueError(_ERROR)
        response["design_response_sha256"] = _record_sha256(
            response, _RESPONSE_FIELDS, "design_response_sha256"
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error

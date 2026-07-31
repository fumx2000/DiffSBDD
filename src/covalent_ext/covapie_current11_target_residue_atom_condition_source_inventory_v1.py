"""Build the Current11 target-residue atom-condition source inventory in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


__all__ = (
    "build_covapie_current11_target_residue_atom_condition_source_inventory_v1",
)


SOURCE_INVENTORY_VERSION = (
    "covapie_current11_target_residue_atom_condition_source_inventory_v1"
)
FIELD_OBSERVATION_VERSION = (
    "covapie_target_residue_atom_condition_source_field_observation_v1"
)
ARTIFACT_STATUS_VERSION = (
    "covapie_target_residue_atom_condition_source_artifact_status_v1"
)
SAMPLE_INVENTORY_RECORD_VERSION = (
    "covapie_current11_target_residue_atom_condition_source_inventory_record_v1"
)
CONTRACT_DESIGN_COMMIT = "fb59a976f6faaa58829f9a761ae4634bcb05a273"
CONTRACT_DESIGN_PRODUCTION_SHA256 = (
    "481d39d420a32a1a5fc2897907453c3c66f85a99cc4e1ff48dee1f8055de61be"
)

_ERROR = "COVAPIE_CURRENT11_TARGET_RESIDUE_ATOM_CONDITION_SOURCE_INVENTORY_INVALID"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_SOURCE_JSON_BYTES = 2 * 1024 * 1024
_MAX_CSV_BYTES = 64 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_SAMPLE_INDEX_PATH = contract_design._SAMPLE_INDEX_PATH
_LOCATOR_SIDECAR_PATH = contract_design._LOCATOR_SIDECAR_PATH
_NORMALISED_EMPTY_FIELDS = (
    "protein_pdbx_PDB_ins_code",
    "protein_label_alt_id",
)
_OBSERVATION_STATUSES = (
    "present_nonempty",
    "present_normalised_empty_with_explicit_provenance",
    "missing_column",
    "missing_value",
    "missing_normalisation_provenance",
)
_ARTIFACT_ROLES = (
    "source_structure",
    "protein_atom_table",
    "condition_evidence",
)
_LOCATOR_KINDS = ("relative_path", "inline_json", "missing", "unsafe")
_DIGEST_MATCH_STATUSES = (
    "matched",
    "mismatched",
    "not_claimed",
    "not_available",
)
_ARTIFACT_STATUSES = (
    "available_verified",
    "available_unverified",
    "missing_declaration",
    "declared_file_missing",
    "unsafe_path",
    "symlink_rejected",
    "invalid_payload",
    "digest_mismatch",
)
_COVERAGE_STATUSES = (
    "resolved_unique",
    "missing_source",
    "schema_incomplete",
    "ambiguous_atom",
    "lineage_mismatch",
)

FIELD_OBSERVATION_RECORD_FIELDS = (
    "field_observation_version",
    "field_name",
    "column_present",
    "raw_value",
    "normalised_value",
    "observation_source",
    "observation_status",
    "blocking_reasons",
    "field_observation_record_sha256",
)
ARTIFACT_STATUS_RECORD_FIELDS = (
    "artifact_status_version",
    "artifact_role",
    "declared_locator",
    "locator_kind",
    "artifact_available",
    "claimed_sha256",
    "recomputed_sha256",
    "digest_match_status",
    "artifact_status",
    "artifact_status_record_sha256",
)
SAMPLE_INVENTORY_RECORD_FIELDS = (
    "source_inventory_record_version",
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "sample_preparation_input_id",
    "sample_index_row_sha256",
    "field_observation_records",
    "field_observation_record_count",
    "complete_required_field_count",
    "missing_required_field_count",
    "source_artifact_status_records",
    "locator_sidecar_match_count",
    "locator_matched_atom_site_ids",
    "atom_table_field_inventory",
    "coverage_status",
    "blocking_reasons",
    "ready_for_authority_materialization",
    "source_inventory_record_sha256",
)
SOURCE_INVENTORY_BUNDLE_FIELDS = (
    "target_residue_atom_condition_source_inventory_version",
    "source_unified_effective_authority_view_filesystem_sha256",
    "source_unified_effective_authority_view_sha256",
    "source_contract_design_commit",
    "source_contract_design_production_sha256",
    "source_contract_design_version",
    "source_contract_design_response_sha256",
    "future_source_inventory_required_fields",
    "condition_evidence_record_fields",
    "field_observation_record_fields",
    "artifact_status_record_fields",
    "sample_inventory_record_fields",
    "source_candidate_records",
    "source_candidate_record_count",
    "sample_order",
    "source_inventory_records",
    "source_inventory_record_count",
    "resolved_unique_sample_count",
    "missing_source_sample_count",
    "schema_incomplete_sample_count",
    "ambiguous_atom_sample_count",
    "lineage_mismatch_sample_count",
    "ready_for_target_condition_authority_implementation",
    "source_inventory_bundle_sha256",
)

_ATOM_TO_INVENTORY_FIELD = {
    "source_atom_site_id": "atom_site_id",
    "protein_model_num": "pdbx_PDB_model_num",
    "protein_auth_asym_id": "auth_asym_id",
    "protein_auth_comp_id": "auth_comp_id",
    "protein_auth_seq_id": "auth_seq_id",
    "protein_pdbx_PDB_ins_code": "pdbx_PDB_ins_code",
    "protein_auth_atom_id": "auth_atom_id",
    "protein_type_symbol": "type_symbol",
    "protein_label_alt_id": "label_alt_id",
    "protein_label_asym_id": "label_asym_id",
    "protein_label_comp_id": "label_comp_id",
    "protein_label_seq_id": "label_seq_id",
    "protein_label_atom_id": "label_atom_id",
}


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
    record: Mapping[str, Any], fields: Sequence[str], digest_field: str
) -> str:
    try:
        unsigned = {field: record[field] for field in fields if field != digest_field}
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


def _strict_json_object(payload: bytes, *, maximum: int) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= maximum
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


def _strict_csv_bytes(payload: bytes) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) > _MAX_CSV_BYTES
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
        ):
            raise ValueError(_ERROR)
        reader = csv.DictReader(
            io.StringIO(payload.decode("utf-8"), newline=""), strict=True
        )
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


def _json_ready_copy(value: Any) -> Any:
    if type(value) is dict:
        return {key: _json_ready_copy(item) for key, item in value.items()}
    if type(value) in {tuple, list}:
        return [_json_ready_copy(item) for item in value]
    if type(value) in {str, int, bool} or value is None:
        return value
    raise ValueError(_ERROR)


def _source_file_snapshot(path: Path) -> bytes:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(_ERROR)
        return path.read_bytes()
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _safe_relative_path(repo_root: Path, locator: str) -> tuple[Path | None, str | None]:
    if type(locator) is not str or not locator:
        return None, "missing"
    if "\\" in locator:
        return None, "unsafe"
    relative = Path(locator)
    if relative.is_absolute() or ".." in relative.parts:
        return None, "unsafe"
    try:
        root = repo_root.resolve(strict=True)
        candidate = repo_root / relative
        cursor = repo_root
        for part in relative.parts:
            cursor = cursor / part
            try:
                metadata = cursor.lstat()
            except FileNotFoundError:
                break
            if stat.S_ISLNK(metadata.st_mode):
                return candidate, "symlink"
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(root):
            return None, "unsafe"
        return candidate, None
    except Exception as error:
        raise ValueError(_ERROR) from error


def _validate_design_source() -> None:
    try:
        path = Path(contract_design.__file__)
        if _sha256(_source_file_snapshot(path)) != CONTRACT_DESIGN_PRODUCTION_SHA256:
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_view_independently(payload: bytes) -> dict[str, Any]:
    view = _strict_json_object(payload, maximum=_MAX_SOURCE_JSON_BYTES)
    records = view.get("effective_authority_records")
    if (
        view.get("sample_order") != list(_EXPECTED_SAMPLES)
        or type(records) is not list
        or len(records) != 11
        or view.get("effective_authority_record_count") != 11
        or view.get("effective_legacy_exact_one_count") != 6
        or view.get("effective_multi_boundary_exact_two_count") != 5
        or type(view.get("unified_effective_authority_view_sha256")) is not str
    ):
        raise ValueError(_ERROR)
    observed_order: list[str] = []
    for record in records:
        if type(record) is not dict or type(record.get("effective_authority_record")) is not dict:
            raise ValueError(_ERROR)
        authority = record["effective_authority_record"]
        sample = record.get("sample_index_row_id")
        if (
            sample != authority.get("sample_index_row_id")
            or type(authority.get("pdb_id")) is not str
            or not authority["pdb_id"]
            or type(authority.get("ligand_comp_id")) is not str
            or not authority["ligand_comp_id"]
        ):
            raise ValueError(_ERROR)
        observed_order.append(sample)
    if observed_order != list(_EXPECTED_SAMPLES):
        raise ValueError(_ERROR)
    return view


def _validate_design_response(
    response: object, view: Mapping[str, Any], source_payload: bytes
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    if type(response) is not dict or tuple(response) != contract_design._RESPONSE_FIELDS:
        raise ValueError(_ERROR)
    if (
        response["target_residue_atom_condition_contract_design_version"]
        != contract_design._DESIGN_VERSION
        or response["canonical_condition_record_fields"]
        != contract_design._FUTURE_CONDITION_RECORD_FIELDS
        or response[
            "source_unified_effective_authority_view_filesystem_sha256"
        ]
        != _sha256(source_payload)
        or response["source_unified_effective_authority_view_sha256"]
        != view["unified_effective_authority_view_sha256"]
        or response["design_response_sha256"]
        != _record_sha256(
            response, contract_design._RESPONSE_FIELDS, "design_response_sha256"
        )
        or response["current11_sample_count"] != 11
        or type(response["source_candidate_records"]) not in {tuple, list}
        or type(response["sample_coverage_records"]) not in {tuple, list}
        or len(response["sample_coverage_records"]) != 11
    ):
        raise ValueError(_ERROR)
    candidates_by_name: dict[str, dict[str, Any]] = {}
    for candidate in response["source_candidate_records"]:
        if (
            type(candidate) is not dict
            or tuple(candidate) != contract_design._SOURCE_CANDIDATE_FIELDS
            or type(candidate["source_candidate_name"]) is not str
            or not candidate["source_candidate_name"]
            or candidate["source_candidate_record_sha256"]
            != _record_sha256(
                candidate,
                contract_design._SOURCE_CANDIDATE_FIELDS,
                "source_candidate_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        name = candidate["source_candidate_name"]
        if name in candidates_by_name:
            raise ValueError(_ERROR)
        candidates_by_name[name] = candidate
    by_sample: dict[str, dict[str, Any]] = {}
    for index, coverage in enumerate(response["sample_coverage_records"]):
        authority = view["effective_authority_records"][index][
            "effective_authority_record"
        ]
        if (
            type(coverage) is not dict
            or tuple(coverage) != contract_design._SAMPLE_COVERAGE_FIELDS
            or coverage["sample_index_row_id"] != _EXPECTED_SAMPLES[index]
            or coverage["pdb_id"] != authority["pdb_id"]
            or coverage["coverage_status"] not in _COVERAGE_STATUSES
            or type(coverage["blocking_reasons"]) not in {tuple, list}
            or any(type(reason) is not str or not reason for reason in coverage["blocking_reasons"])
            or type(coverage["ready_for_authority_materialization"]) is not bool
            or coverage["ready_for_authority_materialization"]
            != (coverage["coverage_status"] == "resolved_unique")
            or coverage["sample_coverage_record_sha256"]
            != _record_sha256(
                coverage,
                contract_design._SAMPLE_COVERAGE_FIELDS,
                "sample_coverage_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        by_sample[coverage["sample_index_row_id"]] = coverage
    resolved = sum(
        record["coverage_status"] == "resolved_unique" for record in by_sample.values()
    )
    ready = resolved == 11
    if (
        len(by_sample) != 11
        or response["resolved_unique_sample_count"] != resolved
        or response["blocked_sample_count"] != 11 - resolved
        or response["ready_for_target_condition_authority_implementation"] is not ready
    ):
        raise ValueError(_ERROR)
    return response, by_sample, candidates_by_name


def _validate_design_source_snapshot_binding(
    *,
    candidates_by_name: Mapping[str, Mapping[str, Any]],
    sample_payload: bytes,
    locator_payload: bytes | None,
) -> None:
    sample_candidate = candidates_by_name.get(
        "current11_sample_index_and_referenced_protein_atom_tables"
    )
    if (
        type(sample_candidate) is not dict
        or sample_candidate["source_path_or_commit"]
        != str(contract_design._SAMPLE_INDEX_PATH)
        or sample_candidate["source_sha256"] != _sha256(sample_payload)
        or sample_candidate["direct_lineage_to_unified_view"] is not True
        or sample_candidate["current11_sample_coverage"] != 11
    ):
        raise ValueError(_ERROR)

    locator_candidate = candidates_by_name.get(
        "current11_residue_locator_provider_sidecar"
    )
    if locator_payload is None:
        if locator_candidate is not None:
            raise ValueError(_ERROR)
        return
    if (
        type(locator_candidate) is not dict
        or locator_candidate["source_path_or_commit"]
        != str(contract_design._LOCATOR_SIDECAR_PATH)
        or locator_candidate["source_sha256"] != _sha256(locator_payload)
        or locator_candidate["authority_level"]
        != "blocking_locator_evidence_non_authoritative"
        or locator_candidate["can_uniquely_resolve_target_atom"] is not False
    ):
        raise ValueError(_ERROR)


def _read_required_csv(repo_root: Path, relative: Path) -> tuple[bytes, tuple[str, ...], tuple[dict[str, str], ...]]:
    path, problem = _safe_relative_path(repo_root, relative.as_posix())
    if path is None or problem is not None:
        raise ValueError(_ERROR)
    payload = _source_file_snapshot(path)
    fields, rows = _strict_csv_bytes(payload)
    return payload, fields, rows


def _sample_rows(
    repo_root: Path,
) -> tuple[
    bytes,
    tuple[str, ...],
    dict[str, dict[str, str]],
    bytes | None,
    tuple[str, ...],
    dict[tuple[str, str], tuple[dict[str, str], ...]],
]:
    sample_payload, sample_fields, rows = _read_required_csv(
        repo_root, _SAMPLE_INDEX_PATH
    )
    required = {
        "sample_index_row_id",
        "sample_preparation_input_id",
        "pdb_id",
        "ligand_comp_id",
        "protein_atom_table_path",
    }
    if not required.issubset(sample_fields) or len(rows) != 11:
        raise ValueError(_ERROR)
    by_sample: dict[str, dict[str, str]] = {}
    for row in rows:
        sample = row["sample_index_row_id"]
        if sample in by_sample:
            raise ValueError(_ERROR)
        by_sample[sample] = row
    if set(by_sample) != set(_EXPECTED_SAMPLES):
        raise ValueError(_ERROR)

    locator_path, locator_problem = _safe_relative_path(
        repo_root, _LOCATOR_SIDECAR_PATH.as_posix()
    )
    locator_payload: bytes | None = None
    locator_fields: tuple[str, ...] = ()
    locator_by_identity: dict[tuple[str, str], list[dict[str, str]]] = {}
    if locator_path is not None and locator_problem is None:
        try:
            metadata = locator_path.lstat()
        except FileNotFoundError:
            pass
        except OSError as error:
            raise ValueError(_ERROR) from error
        else:
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise ValueError(_ERROR)
            locator_payload = locator_path.read_bytes()
            locator_fields, locator_rows = _strict_csv_bytes(locator_payload)
            if not {
                "sample_preparation_input_id",
                "pdb_id",
                "matched_atom_site_id",
            }.issubset(locator_fields):
                raise ValueError(_ERROR)
            for row in locator_rows:
                locator_by_identity.setdefault(
                    (row["sample_preparation_input_id"], row["pdb_id"]), []
                ).append(row)
    elif locator_problem != "missing":
        raise ValueError(_ERROR)
    return (
        sample_payload,
        sample_fields,
        by_sample,
        locator_payload,
        locator_fields,
        {key: tuple(value) for key, value in locator_by_identity.items()},
    )


def _artifact_record(
    *,
    role: str,
    declared_locator: str,
    claimed_sha256: str,
    repo_root: Path,
) -> tuple[dict[str, Any], bytes | None, dict[str, Any] | None]:
    if role not in _ARTIFACT_ROLES or type(declared_locator) is not str or type(claimed_sha256) is not str:
        raise ValueError(_ERROR)
    locator_kind = "missing"
    available = False
    recomputed = ""
    digest_status = "not_available"
    artifact_status = "missing_declaration"
    payload: bytes | None = None
    evidence: dict[str, Any] | None = None

    if declared_locator:
        if role == "condition_evidence" and declared_locator.startswith("{"):
            locator_kind = "inline_json"
            available = True
            try:
                payload = declared_locator.encode("utf-8")
                evidence = _validate_condition_evidence(payload)
            except (UnicodeEncodeError, ValueError):
                artifact_status = "invalid_payload"
            else:
                recomputed = _record_sha256(
                    evidence,
                    contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
                    "condition_evidence_record_sha256",
                )
                internal = evidence["condition_evidence_record_sha256"]
                if internal != recomputed or (claimed_sha256 and (
                    _SHA256.fullmatch(claimed_sha256) is None
                    or claimed_sha256 != recomputed
                )):
                    digest_status = "mismatched"
                    artifact_status = "digest_mismatch"
                elif claimed_sha256:
                    digest_status = "matched"
                    artifact_status = "available_verified"
                else:
                    digest_status = "not_claimed"
                    artifact_status = "available_unverified"
        else:
            path, problem = _safe_relative_path(repo_root, declared_locator)
            if problem == "unsafe":
                locator_kind = "unsafe"
                artifact_status = "unsafe_path"
            elif problem == "symlink":
                locator_kind = "relative_path"
                artifact_status = "symlink_rejected"
            elif problem == "missing" or path is None:
                raise ValueError(_ERROR)
            else:
                locator_kind = "relative_path"
                try:
                    metadata = path.lstat()
                except FileNotFoundError:
                    artifact_status = "declared_file_missing"
                except OSError as error:
                    raise ValueError(_ERROR) from error
                else:
                    if stat.S_ISLNK(metadata.st_mode):
                        artifact_status = "symlink_rejected"
                    elif not stat.S_ISREG(metadata.st_mode):
                        artifact_status = "declared_file_missing"
                    else:
                        try:
                            payload = path.read_bytes()
                        except OSError as error:
                            raise ValueError(_ERROR) from error
                        available = True
                        if role == "condition_evidence":
                            try:
                                evidence = _validate_condition_evidence(payload)
                            except ValueError:
                                artifact_status = "invalid_payload"
                            else:
                                recomputed = _record_sha256(
                                    evidence,
                                    contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
                                    "condition_evidence_record_sha256",
                                )
                                if evidence["condition_evidence_record_sha256"] != recomputed:
                                    digest_status = "mismatched"
                                    artifact_status = "digest_mismatch"
                        else:
                            recomputed = _sha256(payload)
                            if not payload and role == "source_structure":
                                artifact_status = "invalid_payload"
                        if artifact_status not in {"invalid_payload", "digest_mismatch"}:
                            if claimed_sha256:
                                if (
                                    _SHA256.fullmatch(claimed_sha256) is not None
                                    and claimed_sha256 == recomputed
                                ):
                                    digest_status = "matched"
                                    artifact_status = "available_verified"
                                else:
                                    digest_status = "mismatched"
                                    artifact_status = "digest_mismatch"
                            else:
                                digest_status = "not_claimed"
                                artifact_status = "available_unverified"
                        elif digest_status != "mismatched":
                            digest_status = "not_available"

    record: dict[str, Any] = {
        "artifact_status_version": ARTIFACT_STATUS_VERSION,
        "artifact_role": role,
        "declared_locator": declared_locator,
        "locator_kind": locator_kind,
        "artifact_available": available,
        "claimed_sha256": claimed_sha256,
        "recomputed_sha256": recomputed,
        "digest_match_status": digest_status,
        "artifact_status": artifact_status,
        "artifact_status_record_sha256": "",
    }
    if (
        tuple(record) != ARTIFACT_STATUS_RECORD_FIELDS
        or locator_kind not in _LOCATOR_KINDS
        or digest_status not in _DIGEST_MATCH_STATUSES
        or artifact_status not in _ARTIFACT_STATUSES
    ):
        raise ValueError(_ERROR)
    record["artifact_status_record_sha256"] = _record_sha256(
        record, ARTIFACT_STATUS_RECORD_FIELDS, "artifact_status_record_sha256"
    )
    return record, payload, evidence


def _validate_condition_evidence(payload: bytes) -> dict[str, Any]:
    evidence = _strict_json_object(payload, maximum=_MAX_SOURCE_JSON_BYTES)
    if (
        tuple(evidence) != contract_design._CONDITION_EVIDENCE_RECORD_FIELDS
        or any(type(value) is not str for value in evidence.values())
        or evidence["condition_evidence_version"]
        != contract_design._CONDITION_EVIDENCE_VERSION
    ):
        raise ValueError(_ERROR)
    return evidence


def _selected_atom_rows(
    table_fields: tuple[str, ...],
    atom_rows: tuple[dict[str, str], ...],
    locator_ids: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    if locator_ids:
        identifiers = set(locator_ids)
        return tuple(row for row in atom_rows if row.get("atom_site_id") in identifiers)
    if "is_covalent_endpoint_atom" in table_fields:
        return tuple(
            row
            for row in atom_rows
            if row.get("is_covalent_endpoint_atom") in {"True", "true"}
        )
    return ()


def _explicit_optional_raw_value(
    *,
    field: str,
    selected_atom: Mapping[str, str] | None,
    locator_rows: tuple[dict[str, str], ...],
) -> tuple[str | None, str]:
    if selected_atom is not None:
        atom_field = _ATOM_TO_INVENTORY_FIELD[field]
        raw = selected_atom.get(atom_field)
        if raw in {".", "?"}:
            return raw, "selected_atom_table_row"
    if field == "protein_pdbx_PDB_ins_code":
        raw_values = tuple(
            row.get("atom_site_insertion_raw_value", "") for row in locator_rows
        )
        explicit = tuple(value for value in raw_values if value in {".", "?"})
        if explicit and len(set(explicit)) == 1:
            return explicit[0], "locator_sidecar"
    return None, "unavailable"


def _field_observation(
    *,
    field: str,
    sample_fields: tuple[str, ...],
    index_row: Mapping[str, str],
    selected_atom: Mapping[str, str] | None,
    locator_rows: tuple[dict[str, str], ...],
    evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    column_present = field in sample_fields
    raw = index_row.get(field, "") if column_present else ""
    normalised = raw
    source = "sample_index" if column_present else "unavailable"
    reasons: tuple[str, ...] = ()
    if not column_present:
        status = "missing_column"
        reasons = (f"future_source_inventory_required_field_missing:{field}",)
    elif field in _NORMALISED_EMPTY_FIELDS:
        if raw in {".", "?"}:
            normalised = ""
            explicit, explicit_source = _explicit_optional_raw_value(
                field=field,
                selected_atom=selected_atom,
                locator_rows=locator_rows,
            )
            if explicit is not None:
                source = "crosschecked_multiple_sources"
                status = "present_normalised_empty_with_explicit_provenance"
            else:
                source = "unavailable"
                status = "missing_normalisation_provenance"
                reasons = (
                    f"normalised_empty_source_provenance_missing:{field}",
                )
        elif raw:
            status = "present_nonempty"
        else:
            explicit, explicit_source = _explicit_optional_raw_value(
                field=field,
                selected_atom=selected_atom,
                locator_rows=locator_rows,
            )
            if explicit is not None:
                normalised = ""
                source = (
                    "crosschecked_multiple_sources"
                    if evidence is not None and field in evidence
                    else explicit_source
                )
                status = "present_normalised_empty_with_explicit_provenance"
            else:
                status = "missing_normalisation_provenance"
                source = "unavailable"
                reasons = (f"normalised_empty_source_provenance_missing:{field}",)
    elif raw:
        status = "present_nonempty"
        if selected_atom is not None and field in _ATOM_TO_INVENTORY_FIELD:
            atom_value = selected_atom.get(_ATOM_TO_INVENTORY_FIELD[field], "")
            if atom_value == raw:
                source = "crosschecked_multiple_sources"
        if evidence is not None and field in evidence and evidence[field] == raw:
            source = "crosschecked_multiple_sources"
    else:
        status = "missing_value"
        reasons = (f"future_source_inventory_required_value_missing:{field}",)
    record: dict[str, Any] = {
        "field_observation_version": FIELD_OBSERVATION_VERSION,
        "field_name": field,
        "column_present": column_present,
        "raw_value": raw,
        "normalised_value": normalised,
        "observation_source": source,
        "observation_status": status,
        "blocking_reasons": reasons,
        "field_observation_record_sha256": "",
    }
    if (
        tuple(record) != FIELD_OBSERVATION_RECORD_FIELDS
        or status not in _OBSERVATION_STATUSES
    ):
        raise ValueError(_ERROR)
    record["field_observation_record_sha256"] = _record_sha256(
        record,
        FIELD_OBSERVATION_RECORD_FIELDS,
        "field_observation_record_sha256",
    )
    return record


def _transport(bundle: dict[str, Any]) -> bytes:
    try:
        payload = json.dumps(
            bundle,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error
    if (
        not payload
        or len(payload) >= _MAX_JSON_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\n" in payload
        or b"\r" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    decoded = _strict_json_object(payload, maximum=_MAX_JSON_BYTES)
    if tuple(decoded) != SOURCE_INVENTORY_BUNDLE_FIELDS or decoded != bundle:
        raise ValueError(_ERROR)
    try:
        round_trip = json.dumps(
            decoded,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error
    if round_trip != payload:
        raise ValueError(_ERROR)
    return payload


def build_covapie_current11_target_residue_atom_condition_source_inventory_v1(
    *,
    source_unified_effective_authority_view: bytes,
    repo_root: Path,
) -> bytes:
    """Return deterministic audited source-inventory JSON bytes without writes."""

    if (
        type(source_unified_effective_authority_view) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    source_snapshot = bytes(source_unified_effective_authority_view)
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        _validate_design_source()
        design_response_raw = (
            contract_design._reference_design_covapie_target_residue_atom_condition_contract_v1(
                source_unified_effective_authority_view=(
                    source_unified_effective_authority_view
                ),
                repo_root=repo_root,
            )
        )
        view = _validate_view_independently(source_unified_effective_authority_view)
        (
            design_response,
            coverage_by_sample,
            candidates_by_name,
        ) = _validate_design_response(
            design_response_raw, view, source_unified_effective_authority_view
        )
        (
            sample_payload,
            sample_fields,
            sample_by_id,
            locator_payload,
            _locator_fields,
            locator_by_identity,
        ) = _sample_rows(repo_root)
        _validate_design_source_snapshot_binding(
            candidates_by_name=candidates_by_name,
            sample_payload=sample_payload,
            locator_payload=locator_payload,
        )
        sample_payload_snapshot = bytes(sample_payload)
        locator_payload_snapshot = (
            None if locator_payload is None else bytes(locator_payload)
        )
        file_snapshots: dict[Path, bytes] = {}
        inventory_records: list[dict[str, Any]] = []

        for index, sample in enumerate(_EXPECTED_SAMPLES):
            authority = view["effective_authority_records"][index][
                "effective_authority_record"
            ]
            row = sample_by_id[sample]
            coverage = coverage_by_sample[sample]
            if (
                row["pdb_id"] != authority["pdb_id"]
                or row["ligand_comp_id"] != authority["ligand_comp_id"]
            ):
                raise ValueError(_ERROR)
            locator_rows = locator_by_identity.get(
                (row["sample_preparation_input_id"], row["pdb_id"]), ()
            )
            locator_ids = tuple(
                dict.fromkeys(
                    item["matched_atom_site_id"]
                    for item in locator_rows
                    if item["matched_atom_site_id"]
                )
            )

            structure_record, structure_payload, _ = _artifact_record(
                role="source_structure",
                declared_locator=row.get("source_structure_path", ""),
                claimed_sha256=row.get(
                    "source_structure_filesystem_sha256", ""
                ),
                repo_root=repo_root,
            )
            table_record, table_payload, _ = _artifact_record(
                role="protein_atom_table",
                declared_locator=row["protein_atom_table_path"],
                claimed_sha256="",
                repo_root=repo_root,
            )
            evidence_record, evidence_payload, evidence = _artifact_record(
                role="condition_evidence",
                declared_locator=row.get(
                    "source_condition_evidence_path_or_record", ""
                ),
                claimed_sha256=row.get("source_condition_evidence_sha256", ""),
                repo_root=repo_root,
            )
            artifact_records = (
                structure_record,
                table_record,
                evidence_record,
            )
            if table_payload is None:
                table_fields: tuple[str, ...] = ()
                atom_rows: tuple[dict[str, str], ...] = ()
            else:
                table_fields, atom_rows = _strict_csv_bytes(table_payload)
            selected_rows = _selected_atom_rows(table_fields, atom_rows, locator_ids)
            selected_atom = selected_rows[0] if len(selected_rows) == 1 else None

            for locator, payload in (
                (row.get("source_structure_path", ""), structure_payload),
                (row["protein_atom_table_path"], table_payload),
                (row.get("source_condition_evidence_path_or_record", ""), evidence_payload),
            ):
                if payload is not None and locator and not locator.startswith("{"):
                    path, problem = _safe_relative_path(repo_root, locator)
                    if path is None or problem is not None:
                        raise ValueError(_ERROR)
                    existing = file_snapshots.get(path)
                    if existing is not None and existing != payload:
                        raise ValueError(_ERROR)
                    file_snapshots[path] = bytes(payload)

            observations = tuple(
                _field_observation(
                    field=field,
                    sample_fields=sample_fields,
                    index_row=row,
                    selected_atom=selected_atom,
                    locator_rows=locator_rows,
                    evidence=evidence,
                )
                for field in contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS
            )
            complete = sum(
                observation["observation_status"]
                in {
                    "present_nonempty",
                    "present_normalised_empty_with_explicit_provenance",
                }
                for observation in observations
            )
            record: dict[str, Any] = {
                "source_inventory_record_version": SAMPLE_INVENTORY_RECORD_VERSION,
                "sample_index_row_id": sample,
                "pdb_id": row["pdb_id"],
                "ligand_comp_id": row["ligand_comp_id"],
                "sample_preparation_input_id": row[
                    "sample_preparation_input_id"
                ],
                "sample_index_row_sha256": _sha256(_canonical_json_bytes(row)),
                "field_observation_records": observations,
                "field_observation_record_count": len(observations),
                "complete_required_field_count": complete,
                "missing_required_field_count": len(observations) - complete,
                "source_artifact_status_records": artifact_records,
                "locator_sidecar_match_count": len(locator_rows),
                "locator_matched_atom_site_ids": locator_ids,
                "atom_table_field_inventory": table_fields,
                "coverage_status": coverage["coverage_status"],
                "blocking_reasons": coverage["blocking_reasons"],
                "ready_for_authority_materialization": coverage[
                    "ready_for_authority_materialization"
                ],
                "source_inventory_record_sha256": "",
            }
            if (
                tuple(record) != SAMPLE_INVENTORY_RECORD_FIELDS
                or len(observations) != 21
                or len(artifact_records) != 3
                or record["coverage_status"] not in _COVERAGE_STATUSES
                or (
                    record["sample_index_row_id"],
                    record["pdb_id"],
                    record["coverage_status"],
                    record["blocking_reasons"],
                    record["ready_for_authority_materialization"],
                )
                != (
                    coverage["sample_index_row_id"],
                    coverage["pdb_id"],
                    coverage["coverage_status"],
                    coverage["blocking_reasons"],
                    coverage["ready_for_authority_materialization"],
                )
            ):
                raise ValueError(_ERROR)
            record["source_inventory_record_sha256"] = _record_sha256(
                record,
                SAMPLE_INVENTORY_RECORD_FIELDS,
                "source_inventory_record_sha256",
            )
            inventory_records.append(record)

        for path, snapshot in file_snapshots.items():
            if _source_file_snapshot(path) != snapshot:
                raise ValueError(_ERROR)
        current_sample_payload, _, _ = _read_required_csv(repo_root, _SAMPLE_INDEX_PATH)
        if current_sample_payload != sample_payload_snapshot:
            raise ValueError(_ERROR)
        current_locator_path, locator_problem = _safe_relative_path(
            repo_root, _LOCATOR_SIDECAR_PATH.as_posix()
        )
        if locator_payload_snapshot is None:
            if current_locator_path is not None and locator_problem is None:
                try:
                    current_locator_path.lstat()
                except FileNotFoundError:
                    pass
                else:
                    raise ValueError(_ERROR)
        elif (
            current_locator_path is None
            or locator_problem is not None
            or _source_file_snapshot(current_locator_path)
            != locator_payload_snapshot
        ):
            raise ValueError(_ERROR)

        counts = {
            status: sum(
                record["coverage_status"] == status for record in inventory_records
            )
            for status in _COVERAGE_STATUSES
        }
        bundle: dict[str, Any] = {
            "target_residue_atom_condition_source_inventory_version": SOURCE_INVENTORY_VERSION,
            "source_unified_effective_authority_view_filesystem_sha256": _sha256(
                source_unified_effective_authority_view
            ),
            "source_unified_effective_authority_view_sha256": view[
                "unified_effective_authority_view_sha256"
            ],
            "source_contract_design_commit": CONTRACT_DESIGN_COMMIT,
            "source_contract_design_production_sha256": CONTRACT_DESIGN_PRODUCTION_SHA256,
            "source_contract_design_version": design_response[
                "target_residue_atom_condition_contract_design_version"
            ],
            "source_contract_design_response_sha256": design_response[
                "design_response_sha256"
            ],
            "future_source_inventory_required_fields": contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS,
            "condition_evidence_record_fields": contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
            "field_observation_record_fields": FIELD_OBSERVATION_RECORD_FIELDS,
            "artifact_status_record_fields": ARTIFACT_STATUS_RECORD_FIELDS,
            "sample_inventory_record_fields": SAMPLE_INVENTORY_RECORD_FIELDS,
            "source_candidate_records": design_response[
                "source_candidate_records"
            ],
            "source_candidate_record_count": len(
                design_response["source_candidate_records"]
            ),
            "sample_order": _EXPECTED_SAMPLES,
            "source_inventory_records": inventory_records,
            "source_inventory_record_count": len(inventory_records),
            "resolved_unique_sample_count": counts["resolved_unique"],
            "missing_source_sample_count": counts["missing_source"],
            "schema_incomplete_sample_count": counts["schema_incomplete"],
            "ambiguous_atom_sample_count": counts["ambiguous_atom"],
            "lineage_mismatch_sample_count": counts["lineage_mismatch"],
            "ready_for_target_condition_authority_implementation": design_response[
                "ready_for_target_condition_authority_implementation"
            ],
            "source_inventory_bundle_sha256": "",
        }
        bundle = _json_ready_copy(bundle)
        if (
            tuple(bundle) != SOURCE_INVENTORY_BUNDLE_FIELDS
            or len(bundle) != 24
            or bundle["source_inventory_record_count"] != 11
            or bundle["resolved_unique_sample_count"]
            != design_response["resolved_unique_sample_count"]
            or bundle["ready_for_target_condition_authority_implementation"]
            != (bundle["resolved_unique_sample_count"] == 11)
        ):
            raise ValueError(_ERROR)
        bundle["source_inventory_bundle_sha256"] = _record_sha256(
            bundle,
            SOURCE_INVENTORY_BUNDLE_FIELDS,
            "source_inventory_bundle_sha256",
        )
        payload = _transport(bundle)
        if source_snapshot != source_unified_effective_authority_view:
            raise ValueError(_ERROR)
        return bytes(payload)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error

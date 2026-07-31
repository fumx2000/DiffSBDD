"""Audit Current11 target-atom source recovery from already-local files."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import stat
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_inventory_v1
    as source_inventory,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


__all__ = ()


_ERROR = (
    "COVAPIE_CURRENT11_TARGET_RESIDUE_ATOM_CONDITION_"
    "OFFLINE_SOURCE_RECOVERY_DESIGN_INVALID"
)
_DESIGN_VERSION = (
    "covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1"
)
_RECORD_VERSION = (
    "covapie_current11_target_residue_atom_condition_offline_source_recovery_record_v1"
)
_FORMAL_INVENTORY_VERSION = (
    "covapie_current11_target_residue_atom_condition_source_inventory_v1"
)
_FORMAL_INVENTORY_TRANSPORT_SHA256 = (
    "3b061bdcb802dce93cea624e2d79cf82505973471ac70aa88a5313990680d9ec"
)
_FORMAL_INVENTORY_INTERNAL_SHA256 = (
    "1994be44df4412ab2f69d43889bbca054748f3c638b02393f5750c0e111aa351"
)
_SOURCE_INVENTORY_PRODUCTION_SHA256 = (
    "34d1fb66cbb0f20551a5d13a6158f23f68f04583055823e38cfd37e589b50b0e"
)
_SAMPLE_INDEX_SHA256 = (
    "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326"
)
_LOCATOR_SIDECAR_SHA256 = (
    "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7"
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_MAX_INVENTORY_BYTES = 2 * 1024 * 1024
_MAX_CSV_BYTES = 64 * 1024 * 1024
_MAX_RAW_BYTES = 128 * 1024 * 1024
_MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MODEL_RE = re.compile(r"[1-9][0-9]*")

_FORMAL_FIELDS = (
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
_OBSERVATION_FIELDS = (
    "field_observation_version", "field_name", "column_present", "raw_value",
    "normalised_value", "observation_source", "observation_status",
    "blocking_reasons", "field_observation_record_sha256",
)
_ARTIFACT_FIELDS = (
    "artifact_status_version", "artifact_role", "declared_locator",
    "locator_kind", "artifact_available", "claimed_sha256",
    "recomputed_sha256", "digest_match_status", "artifact_status",
    "artifact_status_record_sha256",
)
_SAMPLE_INVENTORY_FIELDS = (
    "source_inventory_record_version", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "sample_preparation_input_id", "sample_index_row_sha256",
    "field_observation_records", "field_observation_record_count",
    "complete_required_field_count", "missing_required_field_count",
    "source_artifact_status_records", "locator_sidecar_match_count",
    "locator_matched_atom_site_ids", "atom_table_field_inventory",
    "coverage_status", "blocking_reasons", "ready_for_authority_materialization",
    "source_inventory_record_sha256",
)
_SOURCE_CANDIDATE_FIELDS = (
    "source_candidate_name", "source_path_or_commit", "source_sha256",
    "source_stage", "field_inventory", "sample_scope",
    "current11_sample_coverage", "direct_lineage_to_unified_view",
    "authority_level", "can_uniquely_resolve_target_atom", "blocking_reasons",
    "source_candidate_record_sha256",
)
_RECORD_FIELDS = (
    "offline_source_recovery_record_version", "sample_index_row_id", "pdb_id",
    "ligand_comp_id", "sample_preparation_input_id", "raw_locator_candidates",
    "selected_raw_locator", "raw_filesystem_status", "claimed_raw_sha256s",
    "recomputed_raw_sha256", "locator_sidecar_match_count",
    "matched_atom_site_ids", "raw_atom_site_match_count",
    "recovered_source_inventory_fields", "unrecovered_source_inventory_fields",
    "proposed_condition_evidence_record", "recovery_status", "blocking_reasons",
    "ready_for_offline_source_evidence_compiler",
    "offline_source_recovery_record_sha256",
)
_RESPONSE_FIELDS = (
    "offline_source_recovery_design_version",
    "source_formal_inventory_transport_sha256", "source_formal_inventory_sha256",
    "source_snapshot_binding_verified", "sample_order",
    "offline_source_recovery_records", "sample_count",
    "recoverable_offline_unique_count", "blocked_sample_count",
    "recovery_status_counts", "ready_for_offline_source_evidence_compiler",
    "recommended_next_step", "feature_semantics_audit_required_before_training",
    "design_response_sha256",
)
_RECOVERY_STATUSES = (
    "recoverable_offline_unique", "blocked_raw_not_declared",
    "blocked_raw_source_missing", "blocked_raw_locator_conflict",
    "blocked_raw_unsafe", "blocked_raw_sha_mismatch",
    "blocked_raw_decode_invalid", "blocked_mmcif_schema_incomplete",
    "blocked_atom_site_row_missing", "blocked_atom_site_row_ambiguous",
    "blocked_identity_mismatch", "blocked_cys_sg_identity_mismatch",
    "blocked_insertion_provenance",
)
_RAW_FILESYSTEM_STATUSES = (
    "available_regular", "missing", "unsafe", "symlink_rejected", "not_declared"
)
_RAW_ATOM_FIELDS = {
    "source_atom_site_id": "_atom_site.id",
    "protein_model_num": "_atom_site.pdbx_PDB_model_num",
    "protein_auth_asym_id": "_atom_site.auth_asym_id",
    "protein_auth_comp_id": "_atom_site.auth_comp_id",
    "protein_auth_seq_id": "_atom_site.auth_seq_id",
    "protein_pdbx_PDB_ins_code": "_atom_site.pdbx_PDB_ins_code",
    "protein_auth_atom_id": "_atom_site.auth_atom_id",
    "protein_type_symbol": "_atom_site.type_symbol",
    "protein_label_alt_id": "_atom_site.label_alt_id",
    "protein_label_asym_id": "_atom_site.label_asym_id",
    "protein_label_comp_id": "_atom_site.label_comp_id",
    "protein_label_seq_id": "_atom_site.label_seq_id",
    "protein_label_atom_id": "_atom_site.label_atom_id",
}
_ATOM_SITE_REQUIRED = tuple(_RAW_ATOM_FIELDS.values()) + (
    "_atom_site.Cartn_x", "_atom_site.Cartn_y", "_atom_site.Cartn_z",
    "_atom_site.occupancy",
)
_SAMPLE_REQUIRED = (
    "sample_index_row_id", "sample_preparation_input_id", "pdb_id",
    "ligand_comp_id", "protein_atom_table_path", "covalent_residue_name",
    "covalent_residue_chain_id", "covalent_residue_index",
    "covalent_residue_atom_name", "ligand_covalent_atom_name", "conn_id",
)
_LOCATOR_REQUIRED = (
    "sample_preparation_input_id", "pdb_id", "raw_target_relative_path",
    "expected_raw_sha256", "observed_raw_sha256",
    "raw_source_precondition_status", "raw_source_precondition_blocking_reason",
    "matched_atom_site_id", "matched_residue_atom_name",
    "struct_conn_residue_auth_asym_id", "struct_conn_residue_auth_seq_id",
    "struct_conn_residue_label_asym_id", "struct_conn_residue_label_seq_id",
    "selected_chain_id", "selected_residue_index",
    "struct_conn_insertion_source_tag", "struct_conn_insertion_raw_value",
    "atom_site_insertion_source_tag", "atom_site_insertion_raw_value",
    "resolved_insertion_state", "resolved_insertion_value",
    "insertion_evidence_agreement",
)
_TABLE_REQUIRED = (
    "sample_preparation_input_id", "pdb_id", "source_raw_file", "atom_site_id",
    "type_symbol", "atom_name", "residue_name", "chain_id", "residue_index",
    "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id", "altloc",
    "model_num", "x", "y", "z", "occupancy",
)
_PROVENANCE_SHA_FIELDS = (
    "source_raw_sha256", "raw_sha256", "source_structure_filesystem_sha256",
    "source_raw_file_sha256",
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
            value, sort_keys=True, ensure_ascii=True, allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _record_sha256(
    record: Mapping[str, Any], fields: Sequence[str], digest_field: str
) -> str:
    try:
        if tuple(record) != tuple(fields):
            raise ValueError(_ERROR)
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


def _strict_json(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes or not payload
        or len(payload) >= _MAX_INVENTORY_BYTES
        or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
        or b"\n" in payload or b"\r" in payload
    ):
        raise ValueError(_ERROR)
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


def _strict_csv(payload: bytes) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        if (
            type(payload) is not bytes or not payload or len(payload) > _MAX_CSV_BYTES
            or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
        ):
            raise ValueError(_ERROR)
        reader = csv.DictReader(
            io.StringIO(payload.decode("utf-8"), newline=""), strict=True
        )
        fields = tuple(reader.fieldnames or ())
        if not fields or len(fields) != len(set(fields)) or any(not f for f in fields):
            raise ValueError(_ERROR)
        rows = tuple(dict(row) for row in reader)
        if any(tuple(row) != fields or any(type(v) is not str for v in row.values()) for row in rows):
            raise ValueError(_ERROR)
        return fields, rows
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_regular(path: Path, *, maximum: int) -> bytes:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(_ERROR)
        if metadata.st_size > maximum:
            raise ValueError(_ERROR)
        payload = path.read_bytes()
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_formal_inventory(
    payload: bytes,
) -> tuple[dict[str, Any], dict[str, dict[str, dict[str, Any]]]]:
    if _sha256(payload) != _FORMAL_INVENTORY_TRANSPORT_SHA256:
        raise ValueError(_ERROR)
    value = _strict_json(payload)
    if (
        tuple(value) != _FORMAL_FIELDS or len(value) != 24
        or value["target_residue_atom_condition_source_inventory_version"]
        != _FORMAL_INVENTORY_VERSION
        or value["source_inventory_bundle_sha256"]
        != _FORMAL_INVENTORY_INTERNAL_SHA256
        or value["source_inventory_bundle_sha256"]
        != _record_sha256(value, _FORMAL_FIELDS, "source_inventory_bundle_sha256")
        or value["future_source_inventory_required_fields"]
        != list(contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS)
        or value["condition_evidence_record_fields"]
        != list(contract_design._CONDITION_EVIDENCE_RECORD_FIELDS)
        or value["field_observation_record_fields"] != list(_OBSERVATION_FIELDS)
        or value["artifact_status_record_fields"] != list(_ARTIFACT_FIELDS)
        or value["sample_inventory_record_fields"] != list(_SAMPLE_INVENTORY_FIELDS)
        or value["sample_order"] != list(_EXPECTED_SAMPLES)
        or value["source_candidate_record_count"] != 6
        or value["source_inventory_record_count"] != 11
        or type(value["source_candidate_records"]) is not list
        or type(value["source_inventory_records"]) is not list
        or len(value["source_candidate_records"]) != 6
        or len(value["source_inventory_records"]) != 11
    ):
        raise ValueError(_ERROR)

    names: set[str] = set()
    for candidate in value["source_candidate_records"]:
        if (
            type(candidate) is not dict or tuple(candidate) != _SOURCE_CANDIDATE_FIELDS
            or candidate["source_candidate_record_sha256"]
            != _record_sha256(candidate, _SOURCE_CANDIDATE_FIELDS, "source_candidate_record_sha256")
            or type(candidate["source_candidate_name"]) is not str
            or not candidate["source_candidate_name"]
            or candidate["source_candidate_name"] in names
        ):
            raise ValueError(_ERROR)
        names.add(candidate["source_candidate_name"])
    if {
        "current11_sample_index_and_referenced_protein_atom_tables",
        "current11_residue_locator_provider_sidecar",
    } - names:
        raise ValueError(_ERROR)

    coverage = Counter()
    artifact_records_by_sample_and_role: dict[
        str, dict[str, dict[str, Any]]
    ] = {}
    for index, record in enumerate(value["source_inventory_records"]):
        if (
            type(record) is not dict or tuple(record) != _SAMPLE_INVENTORY_FIELDS
            or record["sample_index_row_id"] != _EXPECTED_SAMPLES[index]
            or record["source_inventory_record_sha256"]
            != _record_sha256(record, _SAMPLE_INVENTORY_FIELDS, "source_inventory_record_sha256")
            or type(record["field_observation_records"]) is not list
            or len(record["field_observation_records"]) != 21
            or record["field_observation_record_count"] != 21
            or type(record["source_artifact_status_records"]) is not list
            or len(record["source_artifact_status_records"]) != 3
            or record["complete_required_field_count"] + record["missing_required_field_count"] != 21
        ):
            raise ValueError(_ERROR)
        for observation in record["field_observation_records"]:
            if (
                type(observation) is not dict or tuple(observation) != _OBSERVATION_FIELDS
                or observation["field_observation_record_sha256"]
                != _record_sha256(observation, _OBSERVATION_FIELDS, "field_observation_record_sha256")
            ):
                raise ValueError(_ERROR)
        artifacts_by_role: dict[str, dict[str, Any]] = {}
        for artifact in record["source_artifact_status_records"]:
            if (
                type(artifact) is not dict or tuple(artifact) != _ARTIFACT_FIELDS
                or artifact["artifact_status_record_sha256"]
                != _record_sha256(artifact, _ARTIFACT_FIELDS, "artifact_status_record_sha256")
                or artifact["artifact_role"] not in {
                    "source_structure", "protein_atom_table", "condition_evidence"
                }
                or artifact["artifact_role"] in artifacts_by_role
            ):
                raise ValueError(_ERROR)
            artifacts_by_role[artifact["artifact_role"]] = artifact
        if set(artifacts_by_role) != {
            "source_structure", "protein_atom_table", "condition_evidence"
        }:
            raise ValueError(_ERROR)
        artifact_records_by_sample_and_role[
            record["sample_index_row_id"]
        ] = artifacts_by_role
        coverage[record["coverage_status"]] += 1
    expected_counts = {
        "resolved_unique": value["resolved_unique_sample_count"],
        "missing_source": value["missing_source_sample_count"],
        "schema_incomplete": value["schema_incomplete_sample_count"],
        "ambiguous_atom": value["ambiguous_atom_sample_count"],
        "lineage_mismatch": value["lineage_mismatch_sample_count"],
    }
    if (
        any(coverage[key] != count for key, count in expected_counts.items())
        or sum(expected_counts.values()) != 11
        or value["ready_for_target_condition_authority_implementation"]
        is not (value["resolved_unique_sample_count"] == 11)
    ):
        raise ValueError(_ERROR)
    try:
        round_trip = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error
    if round_trip != payload:
        raise ValueError(_ERROR)
    return value, artifact_records_by_sample_and_role


def _safe_relative(
    repo_root: Path, locator: str
) -> tuple[str, Path | None, str | None]:
    if type(locator) is not str or not locator:
        return "", None, "not_declared"
    if "\\" in locator:
        return "", None, "unsafe"
    relative = Path(locator)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        return "", None, "unsafe"
    normalised = relative.as_posix()
    try:
        root = repo_root.resolve(strict=True)
        cursor = repo_root
        for part in relative.parts:
            cursor = cursor / part
            try:
                metadata = cursor.lstat()
            except FileNotFoundError:
                break
            if stat.S_ISLNK(metadata.st_mode):
                return normalised, cursor, "symlink_rejected"
        candidate = repo_root / relative
        if not candidate.resolve(strict=False).is_relative_to(root):
            return "", None, "unsafe"
        return normalised, candidate, None
    except Exception as error:
        raise ValueError(_ERROR) from error


def _read_bound_csv(
    repo_root: Path, locator: str, expected_sha: str
) -> tuple[bytes, tuple[str, ...], tuple[dict[str, str], ...]]:
    normalised, path, problem = _safe_relative(repo_root, locator)
    if not normalised or path is None or problem is not None:
        raise ValueError(_ERROR)
    payload = _read_regular(path, maximum=_MAX_CSV_BYTES)
    if _sha256(payload) != expected_sha:
        raise ValueError(_ERROR)
    fields, rows = _strict_csv(payload)
    return payload, fields, rows


def _mmcif_tokens(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith(";"):
            block: list[str] = [line[1:]]
            index += 1
            while index < len(lines) and not lines[index].startswith(";"):
                block.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError(_ERROR)
            tokens.append("\n".join(block))
            index += 1
            continue
        position = 0
        while position < len(line):
            while position < len(line) and line[position].isspace():
                position += 1
            if position >= len(line) or line[position] == "#":
                break
            if line[position] in {"'", '"'}:
                quote = line[position]
                position += 1
                start = position
                while position < len(line):
                    if line[position] == quote and (
                        position + 1 == len(line) or line[position + 1].isspace()
                    ):
                        break
                    position += 1
                if position >= len(line):
                    raise ValueError(_ERROR)
                tokens.append(line[start:position])
                position += 1
            else:
                start = position
                while position < len(line) and not line[position].isspace():
                    if line[position] == "#" and position == start:
                        break
                    position += 1
                token = line[start:position]
                if token:
                    tokens.append(token)
                if position < len(line) and line[position] == "#":
                    break
        index += 1
    return tuple(tokens)


def _parse_atom_site(text: str) -> tuple[str, tuple[str, ...], tuple[dict[str, str], ...]]:
    tokens = _mmcif_tokens(text)
    data_blocks = tuple(token[5:] for token in tokens if token.lower().startswith("data_"))
    atom_loop: tuple[tuple[str, ...], tuple[dict[str, str], ...]] | None = None
    index = 0
    while index < len(tokens):
        if tokens[index].lower() != "loop_":
            index += 1
            continue
        index += 1
        headers: list[str] = []
        while index < len(tokens) and tokens[index].startswith("_"):
            headers.append(tokens[index])
            index += 1
        if not headers:
            raise ValueError(_ERROR)
        if len(headers) != len(set(headers)):
            raise ValueError(_ERROR)
        values: list[str] = []
        while index < len(tokens):
            token = tokens[index]
            lower = token.lower()
            if (
                lower in {"loop_", "stop_"} or lower.startswith("data_")
                or lower.startswith("save_") or (token.startswith("_") and len(values) % len(headers) == 0)
            ):
                break
            values.append(token)
            index += 1
        if len(values) % len(headers):
            raise ValueError(_ERROR)
        if any(header.startswith("_atom_site.") for header in headers):
            if not all(header.startswith("_atom_site.") for header in headers) or atom_loop is not None:
                raise ValueError(_ERROR)
            rows = tuple(
                dict(zip(headers, values[offset:offset + len(headers)]))
                for offset in range(0, len(values), len(headers))
            )
            atom_loop = (tuple(headers), rows)
    if len(data_blocks) != 1 or atom_loop is None:
        raise ValueError(_ERROR)
    return data_blocks[0], atom_loop[0], atom_loop[1]


def _decode_raw(payload: bytes, locator: str) -> str:
    try:
        if locator.lower().endswith(".gz"):
            output = bytearray()
            with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > _MAX_DECOMPRESSED_BYTES:
                        raise ValueError(_ERROR)
            decoded = bytes(output)
        else:
            if len(payload) > _MAX_DECOMPRESSED_BYTES:
                raise ValueError(_ERROR)
            decoded = payload
        return decoded.decode("utf-8")
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _normalise_optional(value: str) -> str:
    if type(value) is not str:
        raise ValueError(_ERROR)
    return "" if value in {".", "?"} else value


def _decimal_equal(left: str, right: str) -> bool:
    try:
        return Decimal(left) == Decimal(right)
    except (InvalidOperation, ValueError):
        return False


def _candidate_by_name(inventory: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    matches = tuple(
        candidate for candidate in inventory["source_candidate_records"]
        if candidate["source_candidate_name"] == name
    )
    if len(matches) != 1:
        raise ValueError(_ERROR)
    return matches[0]


def _primary_status(blockers: Sequence[str]) -> str:
    priority = (
        "blocked_raw_not_declared", "blocked_raw_source_missing",
        "blocked_raw_locator_conflict", "blocked_raw_unsafe",
        "blocked_raw_sha_mismatch", "blocked_raw_decode_invalid",
        "blocked_mmcif_schema_incomplete", "blocked_atom_site_row_missing",
        "blocked_atom_site_row_ambiguous", "blocked_cys_sg_identity_mismatch",
        "blocked_identity_mismatch", "blocked_insertion_provenance",
    )
    for status in priority:
        if status in blockers:
            return status
    return "recoverable_offline_unique"


def _recommended(records: Sequence[Mapping[str, Any]]) -> str:
    counts = Counter(record["recovery_status"] for record in records)
    if counts["recoverable_offline_unique"] == 11:
        return "implement_covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1"
    groups = (
        (("blocked_raw_not_declared", "blocked_raw_source_missing"),
         "resolve_covapie_current11_missing_raw_structure_sources_v1"),
        (("blocked_raw_sha_mismatch",), "resolve_covapie_current11_raw_sha_mismatch_v1"),
        (("blocked_raw_locator_conflict", "blocked_raw_unsafe"),
         "resolve_covapie_current11_raw_locator_conflicts_v1"),
        (("blocked_raw_decode_invalid", "blocked_mmcif_schema_incomplete"),
         "resolve_covapie_current11_raw_mmcif_schema_v1"),
    )
    for statuses, step in groups:
        if any(counts[status] for status in statuses):
            return step
    return "resolve_covapie_current11_atom_site_identity_conflicts_v1"


def _recovery_record(
    *, inventory_record: Mapping[str, Any], sample_row: Mapping[str, str],
    locator_rows: tuple[dict[str, str], ...],
    formal_protein_table_artifact: Mapping[str, Any], repo_root: Path,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    blockers: list[str] = []
    details: list[str] = []
    snapshots: dict[Path, bytes] = {}
    required_fields = tuple(contract_design._FUTURE_SOURCE_INVENTORY_REQUIRED_FIELDS)
    recovered: list[str] = ["sample_index_row_id", "pdb_id", "ligand_comp_id", "protein_atom_table_path"]
    locator_candidates: list[str] = []
    selected_locator = ""
    raw_status = "not_declared"
    claims: list[str] = []
    recomputed = ""
    matched_ids = tuple(
        dict.fromkeys(row.get("matched_atom_site_id", "") for row in locator_rows if row.get("matched_atom_site_id", ""))
    )
    raw_match_count = 0
    proposed: dict[str, Any] = {}

    if len(locator_rows) != 1:
        blockers.append("blocked_identity_mismatch")
        details.append(f"locator_sidecar_match_count:{len(locator_rows)}")
    locator = locator_rows[0] if len(locator_rows) == 1 else {}
    locator_path = locator.get("raw_target_relative_path", "")
    if locator_path:
        locator_candidates.append(locator_path)
    claims.extend(
        value for value in (
            locator.get("expected_raw_sha256", ""), locator.get("observed_raw_sha256", "")
        ) if value and value not in claims
    )

    table_payload: bytes | None = None
    table_rows: tuple[dict[str, str], ...] = ()
    table_fields: tuple[str, ...] = ()
    table_path_value = sample_row.get("protein_atom_table_path", "")
    if (
        formal_protein_table_artifact.get("artifact_role") != "protein_atom_table"
        or formal_protein_table_artifact.get("declared_locator") != table_path_value
        or formal_protein_table_artifact.get("locator_kind") != "relative_path"
        or formal_protein_table_artifact.get("artifact_available") is not True
        or formal_protein_table_artifact.get("artifact_status")
        not in {"available_unverified", "available_verified"}
        or formal_protein_table_artifact.get("digest_match_status")
        not in {"not_claimed", "matched"}
        or type(formal_protein_table_artifact.get("recomputed_sha256")) is not str
        or _SHA256_RE.fullmatch(
            formal_protein_table_artifact["recomputed_sha256"]
        ) is None
    ):
        raise ValueError(_ERROR)
    table_normalised, table_path, table_problem = _safe_relative(repo_root, table_path_value)
    if not table_normalised or table_path is None or table_problem is not None:
        raise ValueError(_ERROR)
    else:
        table_payload = _read_regular(table_path, maximum=_MAX_CSV_BYTES)
        if _sha256(table_payload) != formal_protein_table_artifact["recomputed_sha256"]:
            raise ValueError(_ERROR)
        snapshots[table_path] = bytes(table_payload)
        try:
            table_fields, table_rows = _strict_csv(table_payload)
        except ValueError:
            blockers.append("blocked_mmcif_schema_incomplete")
            details.append("protein_atom_table_invalid")
        else:
            if not set(_TABLE_REQUIRED).issubset(table_fields):
                blockers.append("blocked_mmcif_schema_incomplete")
                details.append("protein_atom_table_schema_incomplete")
            table_locators = tuple(dict.fromkeys(row.get("source_raw_file", "") for row in table_rows if row.get("source_raw_file", "")))
            locator_candidates.extend(path for path in table_locators if path not in locator_candidates)
            for row in table_rows:
                for field in _PROVENANCE_SHA_FIELDS:
                    value = row.get(field, "")
                    if value and value not in claims:
                        claims.append(value)

    normalised_candidates: list[str] = []
    path_problems: list[str] = []
    paths: dict[str, Path] = {}
    for candidate in locator_candidates:
        normalised, path, problem = _safe_relative(repo_root, candidate)
        if problem is not None:
            path_problems.append(problem)
        elif path is not None and normalised:
            if normalised not in normalised_candidates:
                normalised_candidates.append(normalised)
                paths[normalised] = path
    if not locator_candidates:
        blockers.append("blocked_raw_not_declared")
        details.append("raw_locator_not_declared")
    elif path_problems:
        blockers.append("blocked_raw_unsafe")
        raw_status = "symlink_rejected" if "symlink_rejected" in path_problems else "unsafe"
        details.extend(f"raw_locator_{problem}" for problem in path_problems)
    elif len(normalised_candidates) != 1:
        blockers.append("blocked_raw_locator_conflict")
        details.append("locator_sidecar_protein_table_raw_locator_conflict")
    else:
        selected_locator = normalised_candidates[0]
        recovered.append("source_structure_path")
        raw_path = paths[selected_locator]
        try:
            metadata = raw_path.lstat()
        except FileNotFoundError:
            raw_status = "missing"
            blockers.append("blocked_raw_source_missing")
            details.append("raw_structure_file_missing")
        except OSError:
            raw_status = "missing"
            blockers.append("blocked_raw_source_missing")
            details.append("raw_structure_file_unreadable")
        else:
            if stat.S_ISLNK(metadata.st_mode):
                raw_status = "symlink_rejected"
                blockers.append("blocked_raw_unsafe")
                details.append("raw_structure_symlink_rejected")
            elif not stat.S_ISREG(metadata.st_mode) or metadata.st_size > _MAX_RAW_BYTES:
                raw_status = "unsafe"
                blockers.append("blocked_raw_unsafe")
                details.append("raw_structure_not_bounded_regular")
            else:
                raw_status = "available_regular"
                try:
                    raw_payload = _read_regular(raw_path, maximum=_MAX_RAW_BYTES)
                except ValueError:
                    blockers.append("blocked_raw_unsafe")
                    details.append("raw_structure_read_invalid")
                else:
                    snapshots[raw_path] = bytes(raw_payload)
                    recomputed = _sha256(raw_payload)
                    if (
                        not claims or any(_SHA256_RE.fullmatch(claim) is None for claim in claims)
                        or len(set(claims)) != 1 or claims[0] != recomputed
                    ):
                        blockers.append("blocked_raw_sha_mismatch")
                        details.append("raw_sha_claims_or_filesystem_digest_mismatch")
                    else:
                        recovered.append("source_structure_filesystem_sha256")
                    try:
                        text = _decode_raw(raw_payload, selected_locator)
                    except ValueError:
                        blockers.append("blocked_raw_decode_invalid")
                        details.append("raw_structure_decode_invalid")
                    else:
                        try:
                            data_block, atom_fields, atom_rows = _parse_atom_site(text)
                        except ValueError:
                            blockers.append("blocked_mmcif_schema_incomplete")
                            details.append("mmcif_atom_site_loop_invalid")
                        else:
                            if not set(_ATOM_SITE_REQUIRED).issubset(atom_fields):
                                blockers.append("blocked_mmcif_schema_incomplete")
                                details.append("mmcif_atom_site_required_column_missing")
                            elif len(matched_ids) != 1:
                                blockers.append("blocked_identity_mismatch")
                                details.append("matched_atom_site_id_not_unique_in_locator")
                            else:
                                selected_rows = tuple(row for row in atom_rows if row["_atom_site.id"] == matched_ids[0])
                                raw_match_count = len(selected_rows)
                                if not selected_rows:
                                    blockers.append("blocked_atom_site_row_missing")
                                    details.append("matched_atom_site_id_absent_from_raw")
                                elif len(selected_rows) > 1:
                                    blockers.append("blocked_atom_site_row_ambiguous")
                                    details.append("matched_atom_site_id_duplicated_in_raw")
                                else:
                                    raw = selected_rows[0]
                                    for field in _RAW_ATOM_FIELDS:
                                        if field not in {"protein_pdbx_PDB_ins_code", "protein_label_alt_id"}:
                                            recovered.append(field)
                                    identity_mismatch = data_block.upper() != sample_row["pdb_id"].upper()
                                    identity_mismatch = identity_mismatch or any(
                                        locator.get(key, "") != expected for key, expected in (
                                            ("sample_preparation_input_id", sample_row["sample_preparation_input_id"]),
                                            ("pdb_id", sample_row["pdb_id"]),
                                            ("matched_atom_site_id", raw["_atom_site.id"]),
                                            ("struct_conn_residue_auth_asym_id", raw["_atom_site.auth_asym_id"]),
                                            ("struct_conn_residue_auth_seq_id", raw["_atom_site.auth_seq_id"]),
                                            ("struct_conn_residue_label_asym_id", raw["_atom_site.label_asym_id"]),
                                            ("struct_conn_residue_label_seq_id", raw["_atom_site.label_seq_id"]),
                                            ("matched_residue_atom_name", raw["_atom_site.auth_atom_id"]),
                                            ("selected_chain_id", raw["_atom_site.auth_asym_id"]),
                                            ("selected_residue_index", raw["_atom_site.auth_seq_id"]),
                                        )
                                    )
                                    identity_mismatch = identity_mismatch or any(
                                        sample_row.get(key, "") != expected for key, expected in (
                                            ("sample_index_row_id", inventory_record["sample_index_row_id"]),
                                            ("sample_preparation_input_id", inventory_record["sample_preparation_input_id"]),
                                            ("pdb_id", inventory_record["pdb_id"]),
                                            ("ligand_comp_id", inventory_record["ligand_comp_id"]),
                                            ("covalent_residue_chain_id", raw["_atom_site.auth_asym_id"]),
                                            ("covalent_residue_index", raw["_atom_site.auth_seq_id"]),
                                        )
                                    )
                                    selected_table = tuple(row for row in table_rows if row.get("atom_site_id") == raw["_atom_site.id"])
                                    if len(selected_table) != 1:
                                        identity_mismatch = True
                                    else:
                                        table = selected_table[0]
                                        direct = (
                                            ("sample_preparation_input_id", sample_row["sample_preparation_input_id"]),
                                            ("pdb_id", sample_row["pdb_id"]),
                                            ("type_symbol", raw["_atom_site.type_symbol"]),
                                            ("atom_name", raw["_atom_site.auth_atom_id"]),
                                            ("residue_name", raw["_atom_site.auth_comp_id"]),
                                            ("chain_id", raw["_atom_site.auth_asym_id"]),
                                            ("residue_index", raw["_atom_site.auth_seq_id"]),
                                            ("auth_asym_id", raw["_atom_site.auth_asym_id"]),
                                            ("auth_seq_id", raw["_atom_site.auth_seq_id"]),
                                            ("label_asym_id", raw["_atom_site.label_asym_id"]),
                                            ("label_seq_id", raw["_atom_site.label_seq_id"]),
                                            ("altloc", _normalise_optional(raw["_atom_site.label_alt_id"])),
                                            ("model_num", raw["_atom_site.pdbx_PDB_model_num"]),
                                        )
                                        identity_mismatch = identity_mismatch or any(table.get(key, "") != expected for key, expected in direct)
                                        identity_mismatch = identity_mismatch or any(
                                            not _decimal_equal(table.get(key, ""), raw[raw_key])
                                            for key, raw_key in (
                                                ("x", "_atom_site.Cartn_x"), ("y", "_atom_site.Cartn_y"),
                                                ("z", "_atom_site.Cartn_z"), ("occupancy", "_atom_site.occupancy"),
                                            )
                                        )
                                    if _MODEL_RE.fullmatch(raw["_atom_site.pdbx_PDB_model_num"]) is None:
                                        identity_mismatch = True
                                    if identity_mismatch:
                                        blockers.append("blocked_identity_mismatch")
                                        details.append("sample_locator_or_protein_table_identity_mismatch")
                                    cys_mismatch = (
                                        raw["_atom_site.auth_comp_id"] != "CYS"
                                        or raw["_atom_site.label_comp_id"] != "CYS"
                                        or raw["_atom_site.auth_atom_id"] != "SG"
                                        or raw["_atom_site.label_atom_id"] != "SG"
                                        or raw["_atom_site.type_symbol"] != "S"
                                    )
                                    if cys_mismatch:
                                        blockers.append("blocked_cys_sg_identity_mismatch")
                                        details.append("raw_cys_sg_s_identity_not_observed")
                                    raw_insertion = raw["_atom_site.pdbx_PDB_ins_code"]
                                    raw_altloc = raw["_atom_site.label_alt_id"]
                                    insertion_ok = (
                                        locator.get("struct_conn_insertion_source_tag")
                                        == "_struct_conn.pdbx_ptnr1_PDB_ins_code"
                                        and locator.get("atom_site_insertion_source_tag")
                                        == "_atom_site.pdbx_PDB_ins_code"
                                        and locator.get("atom_site_insertion_raw_value") == raw_insertion
                                        and locator.get("struct_conn_insertion_raw_value") == raw_insertion
                                        and locator.get("insertion_evidence_agreement") == "true"
                                        and locator.get("resolved_insertion_value") == _normalise_optional(raw_insertion)
                                        and locator.get("resolved_insertion_state")
                                        == ("present" if raw_insertion not in {".", "?"} else ("absent" if raw_insertion == "." else "unknown"))
                                    )
                                    if not insertion_ok:
                                        blockers.append("blocked_insertion_provenance")
                                        details.append("raw_struct_conn_atom_site_insertion_provenance_not_agreed")
                                    else:
                                        recovered.append("protein_pdbx_PDB_ins_code")
                                    recovered.append("protein_label_alt_id")
                                    if not blockers:
                                        values = {
                                            field: (_normalise_optional(raw[column]) if field == "protein_pdbx_PDB_ins_code" else raw[column])
                                            for field, column in _RAW_ATOM_FIELDS.items()
                                        }
                                        proposed = {
                                            "condition_evidence_version": contract_design._CONDITION_EVIDENCE_VERSION,
                                            "sample_index_row_id": sample_row["sample_index_row_id"],
                                            "pdb_id": sample_row["pdb_id"],
                                            "ligand_comp_id": sample_row["ligand_comp_id"],
                                            "source_structure_filesystem_sha256": recomputed,
                                            "source_atom_site_id": values["source_atom_site_id"],
                                            "protein_model_num": values["protein_model_num"],
                                            "protein_auth_asym_id": values["protein_auth_asym_id"],
                                            "protein_auth_comp_id": values["protein_auth_comp_id"],
                                            "protein_auth_seq_id": values["protein_auth_seq_id"],
                                            "protein_pdbx_PDB_ins_code": values["protein_pdbx_PDB_ins_code"],
                                            "protein_auth_atom_id": values["protein_auth_atom_id"],
                                            "condition_evidence_record_sha256": "",
                                        }
                                        if tuple(proposed) != tuple(contract_design._CONDITION_EVIDENCE_RECORD_FIELDS):
                                            raise ValueError(_ERROR)
                                        proposed["condition_evidence_record_sha256"] = _record_sha256(
                                            proposed, contract_design._CONDITION_EVIDENCE_RECORD_FIELDS,
                                            "condition_evidence_record_sha256",
                                        )
                                        recovered.extend(("source_condition_evidence_path_or_record", "source_condition_evidence_sha256"))

    blockers = list(dict.fromkeys(blockers))
    details = list(dict.fromkeys(details))
    status = _primary_status(blockers)
    recovered_tuple = tuple(field for field in required_fields if field in set(recovered))
    unrecovered = tuple(field for field in required_fields if field not in set(recovered_tuple))
    record: dict[str, Any] = {
        "offline_source_recovery_record_version": _RECORD_VERSION,
        "sample_index_row_id": inventory_record["sample_index_row_id"],
        "pdb_id": inventory_record["pdb_id"],
        "ligand_comp_id": inventory_record["ligand_comp_id"],
        "sample_preparation_input_id": inventory_record["sample_preparation_input_id"],
        "raw_locator_candidates": tuple(locator_candidates),
        "selected_raw_locator": selected_locator,
        "raw_filesystem_status": raw_status,
        "claimed_raw_sha256s": tuple(claims),
        "recomputed_raw_sha256": recomputed,
        "locator_sidecar_match_count": len(locator_rows),
        "matched_atom_site_ids": matched_ids,
        "raw_atom_site_match_count": raw_match_count,
        "recovered_source_inventory_fields": recovered_tuple,
        "unrecovered_source_inventory_fields": unrecovered,
        "proposed_condition_evidence_record": proposed,
        "recovery_status": status,
        "blocking_reasons": tuple(details),
        "ready_for_offline_source_evidence_compiler": status == "recoverable_offline_unique",
        "offline_source_recovery_record_sha256": "",
    }
    if tuple(record) != _RECORD_FIELDS or len(record) != 20 or raw_status not in _RAW_FILESYSTEM_STATUSES:
        raise ValueError(_ERROR)
    record["offline_source_recovery_record_sha256"] = _record_sha256(
        record, _RECORD_FIELDS, "offline_source_recovery_record_sha256"
    )
    return record, snapshots


def _reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
    *, source_formal_inventory: bytes, repo_root: Path,
) -> dict[str, Any]:
    """Return a deterministic, in-memory feasibility audit; never write files."""

    if type(source_formal_inventory) is not bytes or type(repo_root) is not type(Path()):
        raise ValueError(_ERROR)
    source_snapshot = bytes(source_formal_inventory)
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        production_path = Path(source_inventory.__file__)
        if _sha256(_read_regular(production_path, maximum=4 * 1024 * 1024)) != _SOURCE_INVENTORY_PRODUCTION_SHA256:
            raise ValueError(_ERROR)
        (
            inventory,
            artifact_records_by_sample_and_role,
        ) = _validate_formal_inventory(source_formal_inventory)
        sample_candidate = _candidate_by_name(
            inventory, "current11_sample_index_and_referenced_protein_atom_tables"
        )
        locator_candidate = _candidate_by_name(
            inventory, "current11_residue_locator_provider_sidecar"
        )
        if (
            sample_candidate["source_sha256"] != _SAMPLE_INDEX_SHA256
            or locator_candidate["source_sha256"] != _LOCATOR_SIDECAR_SHA256
        ):
            raise ValueError(_ERROR)
        sample_payload, sample_fields, sample_rows = _read_bound_csv(
            repo_root, sample_candidate["source_path_or_commit"], _SAMPLE_INDEX_SHA256
        )
        locator_payload, locator_fields, locator_rows = _read_bound_csv(
            repo_root, locator_candidate["source_path_or_commit"], _LOCATOR_SIDECAR_SHA256
        )
        if not set(_SAMPLE_REQUIRED).issubset(sample_fields) or not set(_LOCATOR_REQUIRED).issubset(locator_fields):
            raise ValueError(_ERROR)
        sample_by_id: dict[str, list[dict[str, str]]] = {}
        for row in sample_rows:
            sample_by_id.setdefault(row["sample_index_row_id"], []).append(row)
        locator_by_identity: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in locator_rows:
            locator_by_identity.setdefault((row["sample_preparation_input_id"], row["pdb_id"]), []).append(row)
        if set(sample_by_id) != set(_EXPECTED_SAMPLES) or any(len(rows) != 1 for rows in sample_by_id.values()):
            raise ValueError(_ERROR)

        formal_table_locators = tuple(
            artifact_records_by_sample_and_role[sample]["protein_atom_table"][
                "declared_locator"
            ]
            for sample in _EXPECTED_SAMPLES
        )
        if len(set(formal_table_locators)) != len(_EXPECTED_SAMPLES):
            raise ValueError(_ERROR)

        snapshots: dict[Path, bytes] = {}
        sample_path = repo_root / Path(sample_candidate["source_path_or_commit"])
        locator_path = repo_root / Path(locator_candidate["source_path_or_commit"])
        snapshots[sample_path] = bytes(sample_payload)
        snapshots[locator_path] = bytes(locator_payload)
        records: list[dict[str, Any]] = []
        for inventory_record in inventory["source_inventory_records"]:
            sample = inventory_record["sample_index_row_id"]
            row = sample_by_id[sample][0]
            if any(row[field] != inventory_record[field] for field in (
                "sample_index_row_id", "pdb_id", "ligand_comp_id", "sample_preparation_input_id"
            )):
                raise ValueError(_ERROR)
            locators = tuple(locator_by_identity.get((row["sample_preparation_input_id"], row["pdb_id"]), ()))
            record, record_snapshots = _recovery_record(
                inventory_record=inventory_record, sample_row=row,
                locator_rows=locators,
                formal_protein_table_artifact=(
                    artifact_records_by_sample_and_role[sample][
                        "protein_atom_table"
                    ]
                ),
                repo_root=repo_root,
            )
            records.append(record)
            for path, payload in record_snapshots.items():
                existing = snapshots.get(path)
                if existing is not None and existing != payload:
                    raise ValueError(_ERROR)
                snapshots[path] = payload
        for path, payload in snapshots.items():
            if _read_regular(path, maximum=max(_MAX_CSV_BYTES, _MAX_RAW_BYTES)) != payload:
                raise ValueError(_ERROR)
        if source_snapshot != source_formal_inventory:
            raise ValueError(_ERROR)

        counts = {status: sum(record["recovery_status"] == status for record in records) for status in _RECOVERY_STATUSES}
        recoverable = counts["recoverable_offline_unique"]
        ready = recoverable == 11
        response: dict[str, Any] = {
            "offline_source_recovery_design_version": _DESIGN_VERSION,
            "source_formal_inventory_transport_sha256": _sha256(source_formal_inventory),
            "source_formal_inventory_sha256": inventory["source_inventory_bundle_sha256"],
            "source_snapshot_binding_verified": True,
            "sample_order": _EXPECTED_SAMPLES,
            "offline_source_recovery_records": tuple(records),
            "sample_count": len(records),
            "recoverable_offline_unique_count": recoverable,
            "blocked_sample_count": len(records) - recoverable,
            "recovery_status_counts": counts,
            "ready_for_offline_source_evidence_compiler": ready,
            "recommended_next_step": _recommended(records),
            "feature_semantics_audit_required_before_training": True,
            "design_response_sha256": "",
        }
        if tuple(response) != _RESPONSE_FIELDS or len(response) != 14 or response["sample_count"] != 11:
            raise ValueError(_ERROR)
        response["design_response_sha256"] = _record_sha256(
            response, _RESPONSE_FIELDS, "design_response_sha256"
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error

"""Deterministic Current11 pocket-row to retained-model-node alignment V1.

The public compiler is pure and in-memory.  It binds the physical CSV row
order to an order-preserving checkpoint-vocabulary projection; it does not
build an adapter, a training label, an NPZ, or a tensor file.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import secrets
import stat
import struct
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as adapter_design
from covalent_ext.real_covalent_feature_semantics_audit import (
    CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX,
    CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL,
)


__all__ = (
    "compile_covapie_current11_pocket_atom_identity_alignment_v1",
)


_ERROR = "COVAPIE_CURRENT11_POCKET_ATOM_IDENTITY_ALIGNMENT_INVALID"
_RECORD_VERSION = "covapie_current11_pocket_atom_identity_alignment_record_v1"
_BUNDLE_VERSION = "covapie_current11_pocket_atom_identity_alignment_bundle_v1"
_BOUND = "bound_by_order_preserving_checkpoint_projection_v1"
_PROJECTION_POLICY = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"
_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_AUTHORITY_INTERNAL_SHA256 = "d22073b7c70580d7968533775df42ca64507a6d7911e52efc1b10acd4473f39a"
_ADAPTER_DESIGN_PRODUCTION_SHA256 = "570dcb016ce37fb680253d4d04e2b72b3e572e907b79e13cef181651447a1e06"
_ADAPTER_DESIGN_RESPONSE_SHA256 = "f3ffe161b46269003398af36a1965941a987e685aa7e521dd06e936d37a33539"
_AUTHORITY_PRODUCTION_SHA256 = "1cf8839382bccfb595a841493a0e22c550578c02f2592dc7481ff67b078d7248"
_VOCAB_POLICY_PATH = "src/covalent_ext/real_covalent_feature_semantics_audit.py"
_VOCAB_POLICY_SHA256 = "c08779e2206a093059a4bb8f959d2a675c39c947373a463301b99d13f99b2d69"
_CHECKPOINT_PATH = "checkpoints/crossdocked_fullatom_cond.ckpt"
_CHECKPOINT_SHA256 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
_FILTER_POLICY_PATH = "src/covalent_ext/real_covalent_noncheckpoint_pocket_atom_filter_gate.py"
_FILTER_POLICY_SHA256 = "613ca88ace814a637a9c3117d81a173d2b7b50509cc921e65dc8310795c5dec0"
_FLATTEN_POLICY_PATH = "src/covalent_ext/diffsbdd_input_adapter.py"
_FLATTEN_POLICY_SHA256 = "c9fb07156e4643561a8d2902d021cd27637cc4c76d50f80d3cf45d4ab1b42ae6"
_MAX_BYTES = 16 * 1024 * 1024
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_FORMAL_ALIGNMENT_BUNDLE_INTERNAL_SHA256 = (
    "a777aa4058198d5abbf9212c8212b488a0ffb201a376b3689142fc2690f2352b"
)
_FORMAL_ALIGNMENT_BUNDLE_TRANSPORT_SHA256 = (
    "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
)
_EXPECTED_ALIGNMENT_RECORD_SHA256S = (
    "919a89db648781b076c2e8bbb49232e83e547aeb680181ebedb41be8b3e730f1",
    "8662c9781e963eae36d2797925dedb5beab6666aac7de852600caf4285b218d5",
    "0bd38a812e0b47e173264cb4677f0728697aff7b2360e024aff915c463ed181e",
    "9fb3bf1905f5670feac186c3c508879bf96e75f8fea0eb2c524b649b54760cb4",
    "36ddb5e45ea8c058f82a562b9dbe8dee5f7c4604319afbf7332964c0a4546456",
    "59b7af58be204bb8c1ba8fedd2cb86869f4bb2e3d2f7f05e366ede1bdbb76ad2",
    "eda6fcc77393e1e19bb4ab35db1e64748edb4cee077d5bf8d53b2332fa890888",
    "c6f43913b0557275016c568eb569a6eaf60be1b1741e24b3654508fae51850da",
    "1a2cc9437e3e5d5f8b61754d58177be4ed5773598e8886c33347390801ef8db2",
    "71681324fb6e829e70689dbae11be9c2d0600a1e1344998532e2b8c7c9e5b364",
    "e3c36166716130e0850263ee5bb3ed68fd4349b494b9d44d1cc07946cdaef06a",
)

_RECORD_LINEAGE_SHA256_FIELDS = (
    "source_authority_record_sha256",
    "source_condition_evidence_sha256",
    "source_pocket_atom_table_sha256",
    "source_pocket_identity_sequence_sha256",
    "source_pocket_coordinate_sequence_sha256",
    "source_pocket_type_sequence_sha256",
    "retained_pocket_identity_sequence_sha256",
    "retained_pocket_coordinate_float32_bytes_sha256",
    "retained_pocket_one_hot_bytes_sha256",
    "pocket_atom_identity_alignment_record_sha256",
)

POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS = (
    "pocket_atom_identity_alignment_record_version",
    "sample_index_row_id",
    "pdb_id",
    "source_authority_record_sha256",
    "source_condition_evidence_sha256",
    "source_atom_site_id",
    "source_pocket_atom_table_path",
    "source_pocket_atom_table_sha256",
    "source_pocket_row_count",
    "source_pocket_identity_sequence_sha256",
    "source_pocket_coordinate_sequence_sha256",
    "source_pocket_type_sequence_sha256",
    "target_source_pocket_row_index",
    "checkpoint_projection_policy",
    "retained_source_pocket_row_indices",
    "source_row_to_retained_model_local_index",
    "retained_source_atom_site_ids",
    "retained_pocket_identity_sequence_sha256",
    "retained_pocket_coordinate_float32_bytes_sha256",
    "retained_pocket_one_hot_bytes_sha256",
    "retained_pocket_node_count",
    "dropped_pocket_node_count",
    "target_retained",
    "target_retained_model_local_index",
    "target_indicator_true_count",
    "pocket_row_order_binding_status",
    "alignment_status",
    "alignment_blocking_reasons",
    "pocket_atom_identity_alignment_record_sha256",
)

POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS = (
    "pocket_atom_identity_alignment_bundle_version",
    "source_authority_bundle_transport_sha256",
    "source_authority_bundle_sha256",
    "source_authority_production_sha256",
    "source_adapter_design_production_sha256",
    "source_adapter_design_response_sha256",
    "source_checkpoint_vocab_policy_path",
    "source_checkpoint_vocab_policy_sha256",
    "source_checkpoint_path",
    "source_checkpoint_sha256",
    "sample_order",
    "pocket_atom_identity_alignment_record_fields",
    "pocket_atom_identity_alignment_records",
    "pocket_atom_identity_alignment_record_count",
    "aligned_unique_count",
    "blocked_alignment_count",
    "ready_for_adapter_implementation",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "pocket_atom_identity_alignment_bundle_sha256",
)

ALIGNMENT_STATUSES = (
    "alignment_ready_unique",
    "blocked_predecessor_not_row_order_only",
    "blocked_pocket_table_missing",
    "blocked_pocket_table_sha_mismatch",
    "blocked_schema_incomplete",
    "blocked_source_identity_sequence_invalid",
    "blocked_target_atom_missing",
    "blocked_target_atom_ambiguous",
    "blocked_target_identity_mismatch",
    "blocked_target_dropped_by_checkpoint_projection",
    "blocked_projection_invariant",
    "blocked_tensor_projection_invalid",
)

ROW_ORDER_BINDING_STATUSES = (_BOUND, "unbound")

_IDENTITY_FIELDS = (
    "atom_site_id",
    "pdb_id",
    "type_symbol",
    "atom_name",
    "residue_name",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
    "source_raw_file",
)
_REQUIRED_POCKET_FIELDS = set(_IDENTITY_FIELDS) | {"x", "y", "z"}


class _DuplicateKeyError(ValueError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest_record(record: Mapping[str, Any], fields: Sequence[str], digest_field: str) -> str:
    if tuple(record) != tuple(fields):
        raise ValueError(_ERROR)
    return _sha256(
        _canonical_json_bytes({field: record[field] for field in fields if field != digest_field})
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _strict_json(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= _MAX_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError(_ERROR)),
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        raise ValueError(_ERROR)
    return value


def _read_regular(repo_root: Path, relative_path: str, *, maximum: int = _MAX_BYTES) -> bytes:
    try:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(_ERROR)
        path = repo_root / relative
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(_ERROR)
        if metadata.st_size <= 0 or metadata.st_size >= maximum:
            raise ValueError(_ERROR)
        payload = path.read_bytes()
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        text = payload.decode("utf-8")
        if text.startswith("\ufeff") or "\x00" in text:
            raise ValueError(_ERROR)
        reader = csv.DictReader(io.StringIO(text, newline=""))
        fields = tuple(reader.fieldnames or ())
        if not fields or len(fields) != len(set(fields)):
            raise ValueError(_ERROR)
        rows = list(reader)
        if not rows or any(None in row for row in rows):
            raise ValueError(_ERROR)
        if any(type(value) is not str for row in rows for value in row.values()):
            raise ValueError(_ERROR)
        return fields, rows
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _identity_sequence(rows: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "source_pocket_row_index": index,
            **{field: row[field] for field in _IDENTITY_FIELDS},
        }
        for index, row in enumerate(rows)
    ]


def _authority_identity_matches(authority: Mapping[str, Any], row: Mapping[str, str]) -> bool:
    return all(
        (
            row.get("pdb_id") == authority.get("pdb_id"),
            row.get("atom_site_id") == authority.get("source_atom_site_id"),
            row.get("type_symbol") == authority.get("protein_type_symbol"),
            row.get("atom_name") == authority.get("protein_auth_atom_id"),
            row.get("atom_name") == authority.get("protein_label_atom_id"),
            row.get("residue_name") == authority.get("protein_auth_comp_id"),
            row.get("residue_name") == authority.get("protein_label_comp_id"),
            row.get("auth_asym_id") == authority.get("protein_auth_asym_id"),
            row.get("auth_seq_id") == authority.get("protein_auth_seq_id"),
            row.get("label_asym_id") == authority.get("protein_label_asym_id"),
            row.get("label_seq_id") == authority.get("protein_label_seq_id"),
        )
    )


def _validate_projection(
    *, source_count: int, retained_indices: Sequence[int], source_to_retained: Sequence[int | None]
) -> bool:
    try:
        if (
            type(source_count) is not int
            or source_count <= 0
            or type(retained_indices) not in {list, tuple}
            or type(source_to_retained) not in {list, tuple}
            or len(source_to_retained) != source_count
            or not retained_indices
            or any(type(value) is not int for value in retained_indices)
            or list(retained_indices) != sorted(set(retained_indices))
            or retained_indices[0] < 0
            or retained_indices[-1] >= source_count
        ):
            raise ValueError(_ERROR)
        expected: list[int | None] = [None] * source_count
        for local_index, source_index in enumerate(retained_indices):
            expected[source_index] = local_index
        if list(source_to_retained) != expected:
            raise ValueError(_ERROR)
        nonnull = [value for value in source_to_retained if value is not None]
        if nonnull != list(range(len(retained_indices))):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _float32_bytes(rows: Sequence[Mapping[str, str]]) -> bytes:
    payload = bytearray()
    try:
        for row in rows:
            for field in ("x", "y", "z"):
                value = float(row[field])
                if not math.isfinite(value):
                    raise ValueError(_ERROR)
                packed = struct.pack("<f", value)
                if not math.isfinite(struct.unpack("<f", packed)[0]):
                    raise ValueError(_ERROR)
                payload.extend(packed)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
    return bytes(payload)


def _checkpoint_symbol_to_index() -> dict[str, int]:
    try:
        mapping: dict[str, int] = {}
        if len(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX) != 10:
            raise ValueError(_ERROR)
        for atomic_number, feature_index in CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX.items():
            symbol = CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL.get(feature_index)
            if type(atomic_number) is not int or type(feature_index) is not int or type(symbol) is not str:
                raise ValueError(_ERROR)
            if symbol in mapping or feature_index < 0 or feature_index >= 10:
                raise ValueError(_ERROR)
            mapping[symbol] = feature_index
        if set(mapping.values()) != set(range(10)) or mapping.get("S") != 3:
            raise ValueError(_ERROR)
        return mapping
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _one_hot_float32_bytes(rows: Sequence[Mapping[str, str]], symbol_to_index: Mapping[str, int]) -> bytes:
    payload = bytearray()
    try:
        width = len(symbol_to_index)
        for row in rows:
            feature_index = symbol_to_index[row["type_symbol"]]
            values = [0.0] * width
            values[feature_index] = 1.0
            payload.extend(struct.pack(f"<{width}f", *values))
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
    return bytes(payload)


def _align_record(
    *,
    authority: Mapping[str, Any],
    predecessor_mapping: Mapping[str, Any],
    source_path: str,
    expected_source_sha256: str,
    source_payload: bytes,
    symbol_to_index: Mapping[str, int],
) -> dict[str, Any]:
    """Build one Exact29 record; private so tests can exercise synthetic rows."""
    try:
        if _sha256(source_payload) != expected_source_sha256:
            raise ValueError(_ERROR)
        fieldnames, rows = _csv_rows(source_payload)
        if not _REQUIRED_POCKET_FIELDS <= set(fieldnames):
            raise ValueError(_ERROR)
        if any(any(row[field] == "" for field in _IDENTITY_FIELDS) for row in rows):
            raise ValueError(_ERROR)
        if any(row["pdb_id"] != authority.get("pdb_id") for row in rows):
            raise ValueError(_ERROR)
        atom_site_ids = [row["atom_site_id"] for row in rows]
        if len(atom_site_ids) != len(set(atom_site_ids)):
            raise ValueError(_ERROR)

        # Validate every coordinate token before any projection.  Coordinates
        # are never consulted for identity matching.
        _float32_bytes(rows)
        target_matches = [
            index for index, row in enumerate(rows)
            if row["atom_site_id"] == authority.get("source_atom_site_id")
        ]
        if len(target_matches) != 1:
            raise ValueError(_ERROR)
        target_source_index = target_matches[0]
        target_row = rows[target_source_index]
        if not _authority_identity_matches(authority, target_row):
            raise ValueError(_ERROR)
        if (
            authority.get("protein_type_symbol") != "S"
            or authority.get("protein_auth_comp_id") != "CYS"
            or authority.get("protein_auth_atom_id") != "SG"
            or target_row["type_symbol"] != "S"
        ):
            raise ValueError(_ERROR)
        if predecessor_mapping.get("proposed_local_pocket_index") != target_source_index:
            raise ValueError(_ERROR)

        retained_indices = [
            index for index, row in enumerate(rows)
            if row["type_symbol"] in symbol_to_index
        ]
        source_to_retained: list[int | None] = [None] * len(rows)
        for local_index, source_index in enumerate(retained_indices):
            source_to_retained[source_index] = local_index
        _validate_projection(
            source_count=len(rows),
            retained_indices=retained_indices,
            source_to_retained=source_to_retained,
        )
        target_retained_index = source_to_retained[target_source_index]
        if target_retained_index is None:
            raise ValueError(_ERROR)
        retained_rows = [rows[index] for index in retained_indices]
        coordinate_bytes = _float32_bytes(retained_rows)
        one_hot_bytes = _one_hot_float32_bytes(retained_rows, symbol_to_index)
        width = len(symbol_to_index)
        if (
            len(coordinate_bytes) != len(retained_rows) * 3 * 4
            or len(one_hot_bytes) != len(retained_rows) * width * 4
        ):
            raise ValueError(_ERROR)
        one_hot_values = struct.unpack(f"<{len(retained_rows) * width}f", one_hot_bytes)
        if any(
            sum(one_hot_values[start : start + width]) != 1.0
            for start in range(0, len(one_hot_values), width)
        ):
            raise ValueError(_ERROR)

        identities = _identity_sequence(rows)
        retained_identities = [identities[index] for index in retained_indices]
        record: dict[str, Any] = {
            "pocket_atom_identity_alignment_record_version": _RECORD_VERSION,
            "sample_index_row_id": authority["sample_index_row_id"],
            "pdb_id": authority["pdb_id"],
            "source_authority_record_sha256": authority["target_residue_atom_condition_record_sha256"],
            "source_condition_evidence_sha256": authority["source_condition_evidence_sha256"],
            "source_atom_site_id": authority["source_atom_site_id"],
            "source_pocket_atom_table_path": source_path,
            "source_pocket_atom_table_sha256": expected_source_sha256,
            "source_pocket_row_count": len(rows),
            "source_pocket_identity_sequence_sha256": _sha256(_canonical_json_bytes(identities)),
            "source_pocket_coordinate_sequence_sha256": _sha256(
                _canonical_json_bytes([[row["x"], row["y"], row["z"]] for row in rows])
            ),
            "source_pocket_type_sequence_sha256": _sha256(
                _canonical_json_bytes([row["type_symbol"] for row in rows])
            ),
            "target_source_pocket_row_index": target_source_index,
            "checkpoint_projection_policy": _PROJECTION_POLICY,
            "retained_source_pocket_row_indices": retained_indices,
            "source_row_to_retained_model_local_index": source_to_retained,
            "retained_source_atom_site_ids": [row["atom_site_id"] for row in retained_rows],
            "retained_pocket_identity_sequence_sha256": _sha256(
                _canonical_json_bytes(retained_identities)
            ),
            "retained_pocket_coordinate_float32_bytes_sha256": _sha256(coordinate_bytes),
            "retained_pocket_one_hot_bytes_sha256": _sha256(one_hot_bytes),
            "retained_pocket_node_count": len(retained_rows),
            "dropped_pocket_node_count": len(rows) - len(retained_rows),
            "target_retained": True,
            "target_retained_model_local_index": target_retained_index,
            "target_indicator_true_count": 1,
            "pocket_row_order_binding_status": _BOUND,
            "alignment_status": "alignment_ready_unique",
            "alignment_blocking_reasons": [],
            "pocket_atom_identity_alignment_record_sha256": "",
        }
        record["pocket_atom_identity_alignment_record_sha256"] = _digest_record(
            record,
            POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
            "pocket_atom_identity_alignment_record_sha256",
        )
        _validate_alignment_record(record)
        return record
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_alignment_record(
    record: Mapping[str, Any], *, require_field_order: bool = True
) -> bool:
    try:
        ordered = {
            field: record[field]
            for field in POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS
        }
        if (
            type(record) is not dict
            or len(record) != 29
            or set(record) != set(POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS)
            or (
                require_field_order
                and tuple(record) != POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS
            )
            or record["pocket_atom_identity_alignment_record_version"] != _RECORD_VERSION
            or record["sample_index_row_id"] not in _EXPECTED_SAMPLES
            or type(record["pdb_id"]) is not str
            or not record["pdb_id"]
            or type(record["source_atom_site_id"]) is not str
            or not record["source_atom_site_id"]
            or type(record["source_pocket_atom_table_path"]) is not str
            or not record["source_pocket_atom_table_path"]
            or Path(record["source_pocket_atom_table_path"]).is_absolute()
            or ".." in Path(record["source_pocket_atom_table_path"]).parts
            or any(
                type(record[field]) is not str
                or _SHA256_RE.fullmatch(record[field]) is None
                for field in _RECORD_LINEAGE_SHA256_FIELDS
            )
            or record["alignment_status"] not in ALIGNMENT_STATUSES
            or record["pocket_row_order_binding_status"] not in ROW_ORDER_BINDING_STATUSES
            or record["pocket_atom_identity_alignment_record_sha256"]
            != _digest_record(
                ordered,
                POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS,
                "pocket_atom_identity_alignment_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        if record["alignment_status"] == "alignment_ready_unique":
            if (
                record["pocket_row_order_binding_status"] != _BOUND
                or record["alignment_blocking_reasons"] != []
                or record["target_retained"] is not True
                or record["target_indicator_true_count"] != 1
                or type(record["target_source_pocket_row_index"]) is not int
                or record["target_source_pocket_row_index"] < 0
                or record["target_source_pocket_row_index"]
                >= record["source_pocket_row_count"]
                or type(record["target_retained_model_local_index"]) is not int
                or record["target_retained_model_local_index"] < 0
                or record["target_retained_model_local_index"]
                >= record["retained_pocket_node_count"]
                or record["target_retained_model_local_index"]
                != record["source_row_to_retained_model_local_index"][
                    record["target_source_pocket_row_index"]
                ]
            ):
                raise ValueError(_ERROR)
        _validate_projection(
            source_count=record["source_pocket_row_count"],
            retained_indices=record["retained_source_pocket_row_indices"],
            source_to_retained=record["source_row_to_retained_model_local_index"],
        )
        if (
            record["retained_pocket_node_count"]
            != len(record["retained_source_pocket_row_indices"])
            or record["retained_pocket_node_count"]
            != len(record["retained_source_atom_site_ids"])
            or record["dropped_pocket_node_count"]
            != record["source_pocket_row_count"] - record["retained_pocket_node_count"]
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_predecessor(response: Mapping[str, Any]) -> list[dict[str, Any]]:
    try:
        records = response["mapping_audit_records"]
        if (
            tuple(response) != adapter_design.ADAPTER_DESIGN_RESPONSE_FIELDS
            or response["adapter_design_response_sha256"] != _ADAPTER_DESIGN_RESPONSE_SHA256
            or response["current11_unique_mapping_count"] != 0
            or response["current11_blocked_mapping_count"] != 11
            or response["ready_for_adapter_implementation"] is not False
            or response["recommended_next_step"]
            != "implement_covapie_current11_pocket_atom_identity_alignment_v1"
            or response["feature_semantics_audit_required_before_training"] is not True
            or type(records) is not list
            or len(records) != 11
        ):
            raise ValueError(_ERROR)
        for record in records:
            if (
                record.get("identity_match_count") != 1
                or record.get("pocket_row_order_binding_observed") is not False
                or record.get("mapping_status") != "blocked_pocket_row_order_unbound"
                or record.get("mapping_blocking_reasons")
                != ["pocket_table_row_order_not_bound_to_pocket_coords_and_pocket_one_hot"]
            ):
                raise ValueError(_ERROR)
        return records
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_alignment_bundle(bundle: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {
            field: bundle[field]
            for field in POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS
        }
        if (
            type(bundle) is not dict
            or len(bundle) != 20
            or set(bundle) != set(POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS)
            or (require_field_order and tuple(bundle) != POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS)
            or bundle["pocket_atom_identity_alignment_bundle_version"] != _BUNDLE_VERSION
            or bundle["source_authority_bundle_transport_sha256"]
            != _AUTHORITY_TRANSPORT_SHA256
            or bundle["source_authority_bundle_sha256"] != _AUTHORITY_INTERNAL_SHA256
            or bundle["source_authority_production_sha256"]
            != _AUTHORITY_PRODUCTION_SHA256
            or bundle["source_adapter_design_production_sha256"]
            != _ADAPTER_DESIGN_PRODUCTION_SHA256
            or bundle["source_adapter_design_response_sha256"]
            != _ADAPTER_DESIGN_RESPONSE_SHA256
            or bundle["source_checkpoint_vocab_policy_path"] != _VOCAB_POLICY_PATH
            or bundle["source_checkpoint_vocab_policy_sha256"] != _VOCAB_POLICY_SHA256
            or bundle["source_checkpoint_path"] != _CHECKPOINT_PATH
            or bundle["source_checkpoint_sha256"] != _CHECKPOINT_SHA256
            or tuple(bundle["sample_order"]) != _EXPECTED_SAMPLES
            or tuple(bundle["pocket_atom_identity_alignment_record_fields"])
            != POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS
            or type(bundle["pocket_atom_identity_alignment_records"]) is not list
            or bundle["pocket_atom_identity_alignment_record_count"]
            != len(bundle["pocket_atom_identity_alignment_records"])
            or bundle["pocket_atom_identity_alignment_record_count"] != 11
            or bundle["aligned_unique_count"] + bundle["blocked_alignment_count"] != 11
            or bundle["feature_semantics_audit_required_before_training"] is not True
            or bundle["pocket_atom_identity_alignment_bundle_sha256"]
            != _FORMAL_ALIGNMENT_BUNDLE_INTERNAL_SHA256
            or bundle["pocket_atom_identity_alignment_bundle_sha256"]
            != _digest_record(
                ordered,
                POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
                "pocket_atom_identity_alignment_bundle_sha256",
            )
        ):
            raise ValueError(_ERROR)
        records = bundle["pocket_atom_identity_alignment_records"]
        for record in records:
            _validate_alignment_record(record, require_field_order=require_field_order)
        sample_ids = tuple(record["sample_index_row_id"] for record in records)
        record_sha256s = tuple(
            record["pocket_atom_identity_alignment_record_sha256"] for record in records
        )
        authority_sha256s = tuple(
            record["source_authority_record_sha256"] for record in records
        )
        evidence_sha256s = tuple(
            record["source_condition_evidence_sha256"] for record in records
        )
        aligned = sum(record["alignment_status"] == "alignment_ready_unique" for record in records)
        ready = aligned == 11
        if (
            sample_ids != _EXPECTED_SAMPLES
            or len(set(sample_ids)) != 11
            or record_sha256s != _EXPECTED_ALIGNMENT_RECORD_SHA256S
            or len(set(record_sha256s)) != 11
            or len(set(authority_sha256s)) != 11
            or len(set(evidence_sha256s)) != 11
            or bundle["aligned_unique_count"] != aligned
            or bundle["blocked_alignment_count"] != 11 - aligned
            or bundle["ready_for_adapter_implementation"] is not ready
            or bundle["recommended_next_step"]
            != (
                "implement_covapie_target_residue_atom_condition_adapter_v1"
                if ready
                else "resolve_covapie_current11_pocket_atom_identity_alignment_blockers_v1"
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def compile_covapie_current11_pocket_atom_identity_alignment_v1(
    *,
    source_authority_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Compile the formal Current11 identity-alignment bundle without writes."""

    if type(source_authority_bundle) is not bytes or type(repo_root) is not type(Path()):
        raise ValueError(_ERROR)
    authority_snapshot = bytes(source_authority_bundle)
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)

        design_path = Path(adapter_design.__file__)
        if _sha256(design_path.read_bytes()) != _ADAPTER_DESIGN_PRODUCTION_SHA256:
            raise ValueError(_ERROR)
        for source_path, expected_sha in (
            (_VOCAB_POLICY_PATH, _VOCAB_POLICY_SHA256),
            (_FILTER_POLICY_PATH, _FILTER_POLICY_SHA256),
            (_FLATTEN_POLICY_PATH, _FLATTEN_POLICY_SHA256),
        ):
            if _sha256(_read_regular(repo_root, source_path, maximum=4 * 1024 * 1024)) != expected_sha:
                raise ValueError(_ERROR)

        design_response = adapter_design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
            source_authority_bundle=source_authority_bundle,
            repo_root=repo_root,
        )
        mapping_records = _validate_predecessor(design_response)
        authority_bundle = _strict_json(source_authority_bundle)
        authority_records = authority_bundle.get("target_residue_atom_condition_records")
        sample_order = authority_bundle.get("sample_order")
        if (
            type(authority_records) is not list
            or len(authority_records) != 11
            or type(sample_order) is not list
            or len(sample_order) != 11
            or [record.get("sample_index_row_id") for record in authority_records] != sample_order
            or authority_bundle.get("target_residue_atom_condition_authority_bundle_sha256")
            != design_response["source_authority_bundle_sha256"]
            or design_response["source_authority_production_sha256"] != _AUTHORITY_PRODUCTION_SHA256
        ):
            raise ValueError(_ERROR)

        symbol_to_index = _checkpoint_symbol_to_index()
        records: list[dict[str, Any]] = []
        for authority, mapping in zip(authority_records, mapping_records):
            if (
                mapping.get("sample_index_row_id") != authority.get("sample_index_row_id")
                or mapping.get("pdb_id") != authority.get("pdb_id")
                or mapping.get("source_authority_record_sha256")
                != authority.get("target_residue_atom_condition_record_sha256")
                or mapping.get("source_atom_site_id") != authority.get("source_atom_site_id")
            ):
                raise ValueError(_ERROR)
            path = mapping.get("matched_identity_source_path")
            expected_sha = mapping.get("matched_identity_source_sha256")
            if type(path) is not str or not path or not _SHA256_RE.fullmatch(str(expected_sha)):
                raise ValueError(_ERROR)
            payload = _read_regular(repo_root, path)
            records.append(
                _align_record(
                    authority=authority,
                    predecessor_mapping=mapping,
                    source_path=path,
                    expected_source_sha256=expected_sha,
                    source_payload=payload,
                    symbol_to_index=symbol_to_index,
                )
            )

        aligned = sum(record["alignment_status"] == "alignment_ready_unique" for record in records)
        blocked = len(records) - aligned
        ready = aligned == len(records) == 11 and blocked == 0
        checkpoint = design_response["checkpoint_compatibility_decision"]
        bundle: dict[str, Any] = {
            "pocket_atom_identity_alignment_bundle_version": _BUNDLE_VERSION,
            "source_authority_bundle_transport_sha256": _sha256(source_authority_bundle),
            "source_authority_bundle_sha256": authority_bundle[
                "target_residue_atom_condition_authority_bundle_sha256"
            ],
            "source_authority_production_sha256": _AUTHORITY_PRODUCTION_SHA256,
            "source_adapter_design_production_sha256": _ADAPTER_DESIGN_PRODUCTION_SHA256,
            "source_adapter_design_response_sha256": _ADAPTER_DESIGN_RESPONSE_SHA256,
            "source_checkpoint_vocab_policy_path": _VOCAB_POLICY_PATH,
            "source_checkpoint_vocab_policy_sha256": _VOCAB_POLICY_SHA256,
            "source_checkpoint_path": checkpoint["checkpoint_path"],
            "source_checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "sample_order": list(sample_order),
            "pocket_atom_identity_alignment_record_fields": list(
                POCKET_ATOM_IDENTITY_ALIGNMENT_RECORD_FIELDS
            ),
            "pocket_atom_identity_alignment_records": records,
            "pocket_atom_identity_alignment_record_count": len(records),
            "aligned_unique_count": aligned,
            "blocked_alignment_count": blocked,
            "ready_for_adapter_implementation": ready,
            "recommended_next_step": (
                "implement_covapie_target_residue_atom_condition_adapter_v1"
                if ready
                else "resolve_covapie_current11_pocket_atom_identity_alignment_blockers_v1"
            ),
            "feature_semantics_audit_required_before_training": True,
            "pocket_atom_identity_alignment_bundle_sha256": "",
        }
        bundle["pocket_atom_identity_alignment_bundle_sha256"] = _digest_record(
            bundle,
            POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
            "pocket_atom_identity_alignment_bundle_sha256",
        )
        _validate_alignment_bundle(bundle, require_field_order=True)
        if source_authority_bundle != authority_snapshot:
            raise ValueError(_ERROR)
        return bundle
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    try:
        _validate_alignment_bundle(bundle, require_field_order=True)
        payload = _canonical_json_bytes(bundle)
        if not payload or len(payload) >= _MAX_BUNDLE_BYTES:
            raise ValueError(_ERROR)
        if _sha256(payload) != _FORMAL_ALIGNMENT_BUNDLE_TRANSPORT_SHA256:
            raise ValueError(_ERROR)
        decoded = _strict_json(payload)
        if (
            decoded["pocket_atom_identity_alignment_bundle_sha256"]
            != _FORMAL_ALIGNMENT_BUNDLE_INTERNAL_SHA256
        ):
            raise ValueError(_ERROR)
        _validate_alignment_bundle(decoded, require_field_order=False)
        if _canonical_json_bytes(decoded) != payload:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_fd_all(file_descriptor: int, expected_size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = expected_size
    while remaining:
        chunk = os.read(file_descriptor, min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError(_ERROR)
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(file_descriptor, 1):
        raise ValueError(_ERROR)
    return b"".join(chunks)


def _existing_output(path: Path, expected: bytes) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or metadata.st_nlink != 1
            or metadata.st_size != len(expected)
            or path.read_bytes() != expected
        ):
            raise ValueError(_ERROR)
        return {
            "publication_mode": "idempotent_existing",
            "bundle_inode": metadata.st_ino,
            "bundle_mtime_ns": metadata.st_mtime_ns,
            "bundle_size": metadata.st_size,
            "bundle_sha256": _sha256(expected),
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _remove_created_inode(path: Path, device: int, inode: int) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if (
        not stat.S_ISLNK(metadata.st_mode)
        and stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == device
        and metadata.st_ino == inode
    ):
        path.unlink()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _materialize_covapie_current11_pocket_atom_identity_alignment_bundle_v1(
    *, bundle: Mapping[str, Any], output_path: Path
) -> dict[str, Any]:
    """Publish canonical bundle bytes atomically without replacing a target."""

    if type(output_path) is not type(Path()):
        raise ValueError(_ERROR)
    try:
        if bundle.get("ready_for_adapter_implementation") is not True:
            raise ValueError(_ERROR)
        payload = _bundle_bytes(bundle)
        parent = output_path.parent
        parent_metadata = parent.lstat()
        if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
            raise ValueError(_ERROR)
        try:
            output_path.lstat()
        except FileNotFoundError:
            pass
        else:
            return _existing_output(output_path, payload)

        temporary: Path | None = None
        descriptor: int | None = None
        created_device: int | None = None
        created_inode: int | None = None
        published = False
        try:
            for _ in range(128):
                candidate = parent / f".{output_path.name}.{secrets.token_hex(16)}.tmp"
                try:
                    descriptor = os.open(
                        candidate,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                        0o600,
                    )
                except FileExistsError:
                    continue
                temporary = candidate
                metadata = os.fstat(descriptor)
                created_device, created_inode = metadata.st_dev, metadata.st_ino
                break
            if temporary is None or descriptor is None:
                raise ValueError(_ERROR)
            view = memoryview(payload)
            offset = 0
            while offset < len(view):
                written = os.write(descriptor, view[offset:])
                if written <= 0:
                    raise ValueError(_ERROR)
                offset += written
            os.fchmod(descriptor, 0o644)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None

            read_descriptor = os.open(temporary, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                metadata = os.fstat(read_descriptor)
                reread = _read_fd_all(read_descriptor, metadata.st_size)
            finally:
                os.close(read_descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or metadata.st_nlink != 1
                or metadata.st_dev != created_device
                or metadata.st_ino != created_inode
                or reread != payload
            ):
                raise ValueError(_ERROR)
            try:
                os.link(temporary, output_path, follow_symlinks=False)
            except FileExistsError:
                result = _existing_output(output_path, payload)
                _remove_created_inode(temporary, created_device, created_inode)
                _fsync_directory(parent)
                return result
            published = True
            linked = output_path.lstat()
            temporary_metadata = temporary.lstat()
            if (
                linked.st_dev != temporary_metadata.st_dev
                or linked.st_ino != temporary_metadata.st_ino
                or linked.st_nlink != 2
            ):
                raise ValueError(_ERROR)
            _remove_created_inode(temporary, created_device, created_inode)
            _fsync_directory(parent)
            final = output_path.lstat()
            if (
                final.st_dev != created_device
                or final.st_ino != created_inode
                or final.st_nlink != 1
                or stat.S_IMODE(final.st_mode) != 0o644
                or output_path.read_bytes() != payload
            ):
                raise ValueError(_ERROR)
            return {
                "publication_mode": "published_new",
                "bundle_inode": final.st_ino,
                "bundle_mtime_ns": final.st_mtime_ns,
                "bundle_size": final.st_size,
                "bundle_sha256": _sha256(payload),
            }
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            if published and created_device is not None and created_inode is not None:
                _remove_created_inode(output_path, created_device, created_inode)
            if temporary is not None and created_device is not None and created_inode is not None:
                _remove_created_inode(temporary, created_device, created_inode)
            try:
                _fsync_directory(parent)
            except Exception:
                pass
            raise
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error

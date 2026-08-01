"""Current11 target-residue atom condition adapter V1.

The public builder is deterministic, pure, and in-memory.  It converts the
frozen retained-node alignment into one boolean sequence per sample.  It does
not create a training label, tensor/NPZ artifact, or model input.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as adapter_design


__all__ = (
    "build_covapie_target_residue_atom_condition_adapter_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_INVALID"
_RECORD_VERSION = "covapie_target_residue_atom_condition_adapter_record_v1"
_BUNDLE_VERSION = "covapie_current11_target_residue_atom_condition_adapter_bundle_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_BOUND = "bound_by_order_preserving_checkpoint_projection_v1"
_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_AUTHORITY_INTERNAL_SHA256 = "d22073b7c70580d7968533775df42ca64507a6d7911e52efc1b10acd4473f39a"
_ALIGNMENT_TRANSPORT_SHA256 = "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
_ALIGNMENT_INTERNAL_SHA256 = "a777aa4058198d5abbf9212c8212b488a0ffb201a376b3689142fc2690f2352b"
_ALIGNMENT_PRODUCTION_SHA256 = "7441321f30943769934fea02519600a09a1408602433951aa3f155ae7ac030a5"
_ADAPTER_DESIGN_PRODUCTION_SHA256 = "570dcb016ce37fb680253d4d04e2b72b3e572e907b79e13cef181651447a1e06"
_ADAPTER_DESIGN_RESPONSE_SHA256 = "f3ffe161b46269003398af36a1965941a987e685aa7e521dd06e936d37a33539"
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12))
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

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS = (
    "target_residue_atom_condition_adapter_record_version",
    "sample_index_row_id",
    "pdb_id",
    "source_authority_record_sha256",
    "source_condition_evidence_sha256",
    "source_alignment_record_sha256",
    "source_atom_site_id",
    "retained_pocket_node_count",
    "target_retained_model_local_index",
    "adapter_field_name",
    "adapter_field_storage_domain",
    "adapter_field_numpy_dtype",
    "adapter_field_torch_dtype",
    "adapter_field_sample_shape",
    "pocket_target_residue_atom_condition_indicator",
    "indicator_length",
    "indicator_true_count",
    "indicator_uint8_bytes_sha256",
    "adapter_record_status",
    "target_residue_atom_condition_adapter_record_sha256",
)

TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS = (
    "target_residue_atom_condition_adapter_bundle_version",
    "source_authority_bundle_transport_sha256",
    "source_authority_bundle_sha256",
    "source_alignment_bundle_transport_sha256",
    "source_alignment_bundle_sha256",
    "source_alignment_production_sha256",
    "source_adapter_design_production_sha256",
    "source_adapter_design_response_sha256",
    "selected_adapter_field_name",
    "canonical_mask_semantic_names",
    "sample_order",
    "target_residue_atom_condition_adapter_record_fields",
    "target_residue_atom_condition_adapter_records",
    "target_residue_atom_condition_adapter_record_count",
    "total_indicator_length",
    "total_indicator_true_count",
    "all_records_adapter_ready_unique",
    "ready_for_adapter_gate",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "target_residue_atom_condition_adapter_bundle_sha256",
)


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
    unsigned = {field: record[field] for field in fields if field != digest_field}
    return _sha256(_canonical_json_bytes(unsigned))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError(_ERROR)


def _strict_json(payload: bytes, *, maximum: int) -> dict[str, Any]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= maximum
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or payload.endswith((b"\n", b"\r"))
        ):
            raise ValueError(_ERROR)
        decoded = payload.decode("utf-8", errors="strict")
        value = json.loads(
            decoded,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if type(value) is not dict:
            raise ValueError(_ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _internal_bundle_sha(bundle: Mapping[str, Any], digest_field: str) -> str:
    try:
        if digest_field not in bundle:
            raise ValueError(_ERROR)
        unsigned = {key: value for key, value in bundle.items() if key != digest_field}
        return _sha256(_canonical_json_bytes(unsigned))
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_indicator(indicator: object, *, length: int, true_index: int) -> bool:
    try:
        if (
            type(indicator) is not list
            or len(indicator) != length
            or any(type(value) is not bool for value in indicator)
            or sum(value is True for value in indicator) != 1
            or indicator[true_index] is not True
            or next(index for index, value in enumerate(indicator) if value) != true_index
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _build_adapter_record(
    *, authority_record: Mapping[str, Any], alignment_record: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        count = alignment_record.get("retained_pocket_node_count")
        target_index = alignment_record.get("target_retained_model_local_index")
        if (
            alignment_record.get("alignment_status") != "alignment_ready_unique"
            or alignment_record.get("pocket_row_order_binding_status") != _BOUND
            or alignment_record.get("target_retained") is not True
            or alignment_record.get("target_indicator_true_count") != 1
            or type(count) is not int
            or type(count) is bool
            or count <= 0
            or type(target_index) is not int
            or type(target_index) is bool
            or not 0 <= target_index < count
            or authority_record.get("sample_index_row_id")
            != alignment_record.get("sample_index_row_id")
            or authority_record.get("pdb_id") != alignment_record.get("pdb_id")
            or authority_record.get("target_residue_atom_condition_record_sha256")
            != alignment_record.get("source_authority_record_sha256")
            or authority_record.get("source_condition_evidence_sha256")
            != alignment_record.get("source_condition_evidence_sha256")
            or authority_record.get("source_atom_site_id")
            != alignment_record.get("source_atom_site_id")
        ):
            raise ValueError(_ERROR)

        indicator = [False] * count
        indicator[target_index] = True
        _validate_indicator(indicator, length=count, true_index=target_index)
        record: dict[str, Any] = {
            "target_residue_atom_condition_adapter_record_version": _RECORD_VERSION,
            "sample_index_row_id": authority_record["sample_index_row_id"],
            "pdb_id": authority_record["pdb_id"],
            "source_authority_record_sha256": authority_record[
                "target_residue_atom_condition_record_sha256"
            ],
            "source_condition_evidence_sha256": authority_record[
                "source_condition_evidence_sha256"
            ],
            "source_alignment_record_sha256": alignment_record[
                "pocket_atom_identity_alignment_record_sha256"
            ],
            "source_atom_site_id": authority_record["source_atom_site_id"],
            "retained_pocket_node_count": count,
            "target_retained_model_local_index": target_index,
            "adapter_field_name": _FIELD,
            "adapter_field_storage_domain": "per_pocket_node",
            "adapter_field_numpy_dtype": "bool",
            "adapter_field_torch_dtype": "torch.bool",
            "adapter_field_sample_shape": "[num_pocket_nodes]",
            _FIELD: indicator,
            "indicator_length": len(indicator),
            "indicator_true_count": sum(value is True for value in indicator),
            "indicator_uint8_bytes_sha256": _sha256(
                bytes(1 if value else 0 for value in indicator)
            ),
            "adapter_record_status": "adapter_ready_unique",
            "target_residue_atom_condition_adapter_record_sha256": "",
        }
        record["target_residue_atom_condition_adapter_record_sha256"] = _digest_record(
            record,
            TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
            "target_residue_atom_condition_adapter_record_sha256",
        )
        _validate_adapter_record(record, require_field_order=True)
        return record
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_adapter_record(record: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {
            field: record[field]
            for field in TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS
        }
        count = record["retained_pocket_node_count"]
        target_index = record["target_retained_model_local_index"]
        indicator = record[_FIELD]
        if (
            type(record) is not dict
            or len(record) != 20
            or set(record) != set(TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS)
            or (
                require_field_order
                and tuple(record) != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS
            )
            or record["target_residue_atom_condition_adapter_record_version"]
            != _RECORD_VERSION
            or type(record["sample_index_row_id"]) is not str
            or not record["sample_index_row_id"]
            or type(record["pdb_id"]) is not str
            or not record["pdb_id"]
            or type(record["source_atom_site_id"]) is not str
            or not record["source_atom_site_id"]
            or any(
                not _SHA256_RE.fullmatch(str(record[field]))
                for field in (
                    "source_authority_record_sha256",
                    "source_condition_evidence_sha256",
                    "source_alignment_record_sha256",
                    "indicator_uint8_bytes_sha256",
                    "target_residue_atom_condition_adapter_record_sha256",
                )
            )
            or type(count) is not int
            or type(count) is bool
            or count <= 0
            or type(target_index) is not int
            or type(target_index) is bool
            or not 0 <= target_index < count
            or record["adapter_field_name"] != _FIELD
            or record["adapter_field_storage_domain"] != "per_pocket_node"
            or record["adapter_field_numpy_dtype"] != "bool"
            or record["adapter_field_torch_dtype"] != "torch.bool"
            or record["adapter_field_sample_shape"] != "[num_pocket_nodes]"
            or record["indicator_length"] != count
            or record["indicator_true_count"] != 1
            or record["adapter_record_status"] != "adapter_ready_unique"
        ):
            raise ValueError(_ERROR)
        _validate_indicator(indicator, length=count, true_index=target_index)
        if (
            record["indicator_uint8_bytes_sha256"]
            != _sha256(bytes(1 if value else 0 for value in indicator))
            or record["target_residue_atom_condition_adapter_record_sha256"]
            != _digest_record(
                ordered,
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
                "target_residue_atom_condition_adapter_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_adapter_bundle(bundle: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {
            field: bundle[field]
            for field in TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS
        }
        records = bundle["target_residue_atom_condition_adapter_records"]
        if (
            type(bundle) is not dict
            or len(bundle) != 21
            or set(bundle) != set(TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS)
            or (
                require_field_order
                and tuple(bundle) != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS
            )
            or bundle["target_residue_atom_condition_adapter_bundle_version"]
            != _BUNDLE_VERSION
            or bundle["source_authority_bundle_transport_sha256"]
            != _AUTHORITY_TRANSPORT_SHA256
            or bundle["source_authority_bundle_sha256"] != _AUTHORITY_INTERNAL_SHA256
            or bundle["source_alignment_bundle_transport_sha256"]
            != _ALIGNMENT_TRANSPORT_SHA256
            or bundle["source_alignment_bundle_sha256"] != _ALIGNMENT_INTERNAL_SHA256
            or bundle["source_alignment_production_sha256"]
            != _ALIGNMENT_PRODUCTION_SHA256
            or bundle["source_adapter_design_production_sha256"]
            != _ADAPTER_DESIGN_PRODUCTION_SHA256
            or bundle["source_adapter_design_response_sha256"]
            != _ADAPTER_DESIGN_RESPONSE_SHA256
            or bundle["selected_adapter_field_name"] != _FIELD
            or tuple(bundle["canonical_mask_semantic_names"])
            != CANONICAL_MASK_SEMANTIC_NAMES
            or tuple(bundle["sample_order"]) != _EXPECTED_SAMPLES
            or tuple(bundle["target_residue_atom_condition_adapter_record_fields"])
            != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS
            or type(records) is not list
            or len(records) != 11
            or bundle["target_residue_atom_condition_adapter_record_count"] != 11
            or bundle["total_indicator_length"]
            != sum(record.get("indicator_length", -1) for record in records)
            or bundle["total_indicator_true_count"]
            != sum(record.get("indicator_true_count", -1) for record in records)
            or bundle["total_indicator_true_count"] != 11
            or bundle["all_records_adapter_ready_unique"] is not True
            or bundle["ready_for_adapter_gate"] is not True
            or bundle["recommended_next_step"]
            != "implement_covapie_target_residue_atom_condition_adapter_gate_v1"
            or bundle["feature_semantics_audit_required_before_training"] is not True
        ):
            raise ValueError(_ERROR)
        for record in records:
            _validate_adapter_record(record, require_field_order=require_field_order)
        sample_ids = tuple(record["sample_index_row_id"] for record in records)
        alignment_sha256s = tuple(record["source_alignment_record_sha256"] for record in records)
        adapter_sha256s = tuple(
            record["target_residue_atom_condition_adapter_record_sha256"] for record in records
        )
        if (
            sample_ids != _EXPECTED_SAMPLES
            or len(set(sample_ids)) != 11
            or alignment_sha256s != _EXPECTED_ALIGNMENT_RECORD_SHA256S
            or len(set(alignment_sha256s)) != 11
            or len(set(adapter_sha256s)) != 11
            or bundle["target_residue_atom_condition_adapter_bundle_sha256"]
            != _digest_record(
                ordered,
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
                "target_residue_atom_condition_adapter_bundle_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def build_covapie_target_residue_atom_condition_adapter_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the frozen Current11 per-pocket-node boolean adapter bundle."""

    if (
        type(source_authority_bundle) is not bytes
        or type(source_alignment_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    authority_snapshot = bytes(source_authority_bundle)
    alignment_snapshot = bytes(source_alignment_bundle)
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        if (
            _sha256(source_authority_bundle) != _AUTHORITY_TRANSPORT_SHA256
            or _sha256(source_alignment_bundle) != _ALIGNMENT_TRANSPORT_SHA256
            or _sha256(Path(alignment.__file__).read_bytes())
            != _ALIGNMENT_PRODUCTION_SHA256
            or _sha256(Path(adapter_design.__file__).read_bytes())
            != _ADAPTER_DESIGN_PRODUCTION_SHA256
        ):
            raise ValueError(_ERROR)

        authority_bundle = _strict_json(source_authority_bundle, maximum=_MAX_BUNDLE_BYTES)
        if (
            authority_bundle.get("target_residue_atom_condition_authority_bundle_sha256")
            != _AUTHORITY_INTERNAL_SHA256
            or _internal_bundle_sha(
                authority_bundle,
                "target_residue_atom_condition_authority_bundle_sha256",
            )
            != _AUTHORITY_INTERNAL_SHA256
            or authority_bundle.get("target_residue_atom_condition_record_count") != 11
            or authority_bundle.get("resolved_authoritative_count") != 11
            or authority_bundle.get("all_records_resolved_authoritative") is not True
            or authority_bundle.get("feature_semantics_audit_required_before_training")
            is not True
        ):
            raise ValueError(_ERROR)

        compiled_alignment = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
            source_authority_bundle=source_authority_bundle,
            repo_root=repo_root,
        )
        recompiled_alignment_bytes = alignment._bundle_bytes(compiled_alignment)
        if recompiled_alignment_bytes != source_alignment_bundle:
            raise ValueError(_ERROR)
        supplied_alignment = _strict_json(source_alignment_bundle, maximum=_MAX_BUNDLE_BYTES)
        if (
            supplied_alignment.get("pocket_atom_identity_alignment_bundle_sha256")
            != _ALIGNMENT_INTERNAL_SHA256
            or _internal_bundle_sha(
                supplied_alignment,
                "pocket_atom_identity_alignment_bundle_sha256",
            )
            != _ALIGNMENT_INTERNAL_SHA256
            or supplied_alignment.get("source_authority_bundle_transport_sha256")
            != _AUTHORITY_TRANSPORT_SHA256
            or supplied_alignment.get("source_authority_bundle_sha256")
            != _AUTHORITY_INTERNAL_SHA256
            or supplied_alignment.get("source_adapter_design_production_sha256")
            != _ADAPTER_DESIGN_PRODUCTION_SHA256
            or supplied_alignment.get("source_adapter_design_response_sha256")
            != _ADAPTER_DESIGN_RESPONSE_SHA256
            or supplied_alignment.get("pocket_atom_identity_alignment_record_count") != 11
            or supplied_alignment.get("aligned_unique_count") != 11
            or supplied_alignment.get("blocked_alignment_count") != 0
            or supplied_alignment.get("ready_for_adapter_implementation") is not True
            or supplied_alignment.get("feature_semantics_audit_required_before_training")
            is not True
        ):
            raise ValueError(_ERROR)

        authority_records = authority_bundle.get("target_residue_atom_condition_records")
        alignment_records = compiled_alignment.get("pocket_atom_identity_alignment_records")
        sample_order = authority_bundle.get("sample_order")
        if (
            type(authority_records) is not list
            or type(alignment_records) is not list
            or len(authority_records) != 11
            or len(alignment_records) != 11
            or tuple(sample_order) != _EXPECTED_SAMPLES
            or tuple(compiled_alignment.get("sample_order", ())) != _EXPECTED_SAMPLES
            or tuple(
                record.get("pocket_atom_identity_alignment_record_sha256")
                for record in alignment_records
            )
            != _EXPECTED_ALIGNMENT_RECORD_SHA256S
        ):
            raise ValueError(_ERROR)

        records = [
            _build_adapter_record(
                authority_record=authority_record,
                alignment_record=alignment_record,
            )
            for authority_record, alignment_record in zip(authority_records, alignment_records)
        ]
        if (
            len({record["sample_index_row_id"] for record in records}) != 11
            or len({record["source_alignment_record_sha256"] for record in records}) != 11
        ):
            raise ValueError(_ERROR)
        bundle: dict[str, Any] = {
            "target_residue_atom_condition_adapter_bundle_version": _BUNDLE_VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_authority_bundle_sha256": _AUTHORITY_INTERNAL_SHA256,
            "source_alignment_bundle_transport_sha256": _ALIGNMENT_TRANSPORT_SHA256,
            "source_alignment_bundle_sha256": _ALIGNMENT_INTERNAL_SHA256,
            "source_alignment_production_sha256": _ALIGNMENT_PRODUCTION_SHA256,
            "source_adapter_design_production_sha256": _ADAPTER_DESIGN_PRODUCTION_SHA256,
            "source_adapter_design_response_sha256": _ADAPTER_DESIGN_RESPONSE_SHA256,
            "selected_adapter_field_name": _FIELD,
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "sample_order": list(sample_order),
            "target_residue_atom_condition_adapter_record_fields": list(
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS
            ),
            "target_residue_atom_condition_adapter_records": records,
            "target_residue_atom_condition_adapter_record_count": len(records),
            "total_indicator_length": sum(record["indicator_length"] for record in records),
            "total_indicator_true_count": sum(
                record["indicator_true_count"] for record in records
            ),
            "all_records_adapter_ready_unique": all(
                record["adapter_record_status"] == "adapter_ready_unique" for record in records
            ),
            "ready_for_adapter_gate": True,
            "recommended_next_step": (
                "implement_covapie_target_residue_atom_condition_adapter_gate_v1"
            ),
            "feature_semantics_audit_required_before_training": True,
            "target_residue_atom_condition_adapter_bundle_sha256": "",
        }
        bundle["target_residue_atom_condition_adapter_bundle_sha256"] = _digest_record(
            bundle,
            TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
            "target_residue_atom_condition_adapter_bundle_sha256",
        )
        _validate_adapter_bundle(bundle, require_field_order=True)
        if (
            source_authority_bundle != authority_snapshot
            or source_alignment_bundle != alignment_snapshot
        ):
            raise ValueError(_ERROR)
        return bundle
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    try:
        _validate_adapter_bundle(bundle, require_field_order=True)
        payload = _canonical_json_bytes(bundle)
        if not payload or len(payload) >= _MAX_BUNDLE_BYTES:
            raise ValueError(_ERROR)
        decoded = _strict_json(payload, maximum=_MAX_BUNDLE_BYTES)
        _validate_adapter_bundle(decoded, require_field_order=False)
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


def _materialize_covapie_current11_target_residue_atom_condition_adapter_bundle_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Rebuild and publish canonical adapter bytes without replacing a target."""

    if type(output_path) is not type(Path()):
        raise ValueError(_ERROR)
    try:
        bundle = build_covapie_target_residue_atom_condition_adapter_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            repo_root=repo_root,
        )
        if bundle["ready_for_adapter_gate"] is not True:
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
                        os.O_WRONLY
                        | os.O_CREAT
                        | os.O_EXCL
                        | getattr(os, "O_NOFOLLOW", 0),
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

            read_descriptor = os.open(
                temporary, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            )
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

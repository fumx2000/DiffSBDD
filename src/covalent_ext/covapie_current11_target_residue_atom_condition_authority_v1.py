"""Materialize exact-row Current11 target-residue atom-condition authority."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as offline_recovery,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1
    as source_evidence_compiler,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_contract_design_v1 as contract_design,
)


__all__ = (
    "build_covapie_current11_target_residue_atom_condition_authority_v1",
)


_ERROR = "COVAPIE_CURRENT11_TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_INVALID"
_AUTHORITY_BUNDLE_VERSION = (
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1"
)
_CONDITION_VERSION = "covapie_target_residue_atom_condition_v1"
_FORMAL_INVENTORY_TRANSPORT_SHA256 = (
    "3b061bdcb802dce93cea624e2d79cf82505973471ac70aa88a5313990680d9ec"
)
_FORMAL_INVENTORY_INTERNAL_SHA256 = (
    "1994be44df4412ab2f69d43889bbca054748f3c638b02393f5750c0e111aa351"
)
_SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256 = (
    "d95453fdc358efbe22bd6badeee2ee110b5f68fa08b361a32564453977db5b71"
)
_SOURCE_EVIDENCE_BUNDLE_TRANSPORT_SHA256 = (
    "30bb02e83fbe262c281b4bc2ae220dda7831532e5496d7dfca59e585e1fd0df6"
)
_SOURCE_EVIDENCE_BUNDLE_INTERNAL_SHA256 = (
    "3f3b312de66d5272bdb138d56033a88aabc53c736f1f4a2495fbc41b16549836"
)
_OFFLINE_RECOVERY_PRODUCTION_SHA256 = (
    "ebc661f283df7218ddd416fb24651cc3e2422ded87a0ba9d3ee4c251f80216b2"
)
_OFFLINE_RECOVERY_RESPONSE_SHA256 = (
    "ec875fa158d41fe2a0cc45374f3ce3d2b94bb9e46a54fac90a54cedff007c938"
)
_CONTRACT_DESIGN_VERSION = "covapie_target_residue_atom_condition_contract_design_v1"
_CONTRACT_DESIGN_PRODUCTION_SHA256 = (
    "481d39d420a32a1a5fc2897907453c3c66f85a99cc4e1ff48dee1f8055de61be"
)
_CONTRACT_DESIGN_MODULE_SHA256 = (
    "481d39d420a32a1a5fc2897907453c3c66f85a99cc4e1ff48dee1f8055de61be"
)
_CONTRACT_DESIGN_RESPONSE_SHA256 = (
    "8f2e3742d2e88340b4530fe6e7be403ae849d36d1f8c99fe78698f3b40aff592"
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_EXPECTED_RECOVERY_RECORD_SHA256S = (
    "4ae7eb51e1aeeedbec1936432123a0f7fd74e2f22a021963fac2058d801f4476",
    "362eb9f81e941ae1f38c82795c1560b35880d70e9b2ca895ca0cafd507b3ea8f",
    "3d89242075d1681562c2b1b46072bb951093b22be9ffa7e01dfbdef6894024f5",
    "8a6793c6c78f0649f4e7dd3fe49f2d4367ee5ba8a0cff63d8722d0681531a1a6",
    "94b9cf3a085776b9d787d73eb1952b969298239202831e3dd686676101b6fdbe",
    "d6e799d9e4af646e201c187394146279955e88103b444b2061e2251da99a1a19",
    "cfd5f8373951f4a76135336e74dc9796dcb01e98fe99292d04a14cdd1df61706",
    "dd4ce370564ac86629a93baedfed14b2e5f40a0600ed2d7dac6c00d0944bb504",
    "22a3b1f4266fac4f97a129179d504a24bb1df2a282b4558d97f3519d5afbaad3",
    "631b1c8664930e171d2b4eebbd61f261ab10ef489888dc51fb85fbbc9beb6003",
    "558fbc3df361a4902cb758bf17efc3bed971299b9bbe89fb1a4f35fd832a5b5c",
)
_EXPECTED_EVIDENCE_RECORD_SHA256S = (
    "9d5b2f8424c48f846b816a64aa8cd9d2267830475f50705216fa4660d866fa69",
    "12092df3536cbbd677e77fed8277c1eceee889b981f50a4af3ceebc06baecb25",
    "ae01bc69427bb499739eded2303ef2188dece1e9dc6e9a7570fb0c5670077abb",
    "d5be286ac6b96ac8ba04eb47e73afd80bb3e648adf899d5018061d00caba35c1",
    "81bf86f4a9786626464ec6bb38f93b522c6dcfe4c948412fddd3f443cc0a3da9",
    "8dcc9f75ba8ffc6a0fe8221f906b73090938295cc135299e064bc1a3e4e91fd7",
    "ef70efa238eb72df57c7d4cd4f677c0ba5b70b5ca9602f13ea84aee224cfae3d",
    "a04a409bcaf0bda6b18ed5d0743589da549a290c16deaca4f64a9d83469492a6",
    "9ef8237dcd4fbede7658cc97d4dbe4d06c420ead49863c2ea7645c3bfc6d91a6",
    "3bfd7c3c1aa7e3ea229ef2ea006d4a13d36b44af0e308a1c1cd6e7e03dbf5735",
    "5899a929c9c8fcca5f4db97a4c3de4d74594074d6c8c5a281a2f96ebe7ad51b8",
)
_MAX_JSON_BYTES = 2 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}")

TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS = (
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

TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS = (
    "target_residue_atom_condition_authority_bundle_version",
    "source_formal_inventory_transport_sha256",
    "source_formal_inventory_sha256",
    "source_condition_contract_design_version",
    "source_condition_contract_design_production_sha256",
    "source_condition_contract_design_response_sha256",
    "source_evidence_compiler_production_sha256",
    "source_evidence_bundle_transport_sha256",
    "source_evidence_bundle_sha256",
    "source_offline_recovery_design_response_sha256",
    "source_condition_evidence_record_sha256s",
    "sample_order",
    "target_residue_atom_condition_record_fields",
    "target_residue_atom_condition_records",
    "target_residue_atom_condition_record_count",
    "resolved_authoritative_count",
    "all_records_resolved_authoritative",
    "ready_for_target_residue_atom_condition_adapter_design",
    "feature_semantics_audit_required_before_training",
    "target_residue_atom_condition_authority_bundle_sha256",
)

_RAW_REQUIRED_COLUMNS = (
    "_atom_site.id",
    "_atom_site.pdbx_PDB_model_num",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_seq_id",
    "_atom_site.pdbx_PDB_ins_code",
    "_atom_site.auth_atom_id",
    "_atom_site.type_symbol",
    "_atom_site.label_alt_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_seq_id",
    "_atom_site.label_atom_id",
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
    record: Mapping[str, Any], fields: Sequence[str], digest_field: str,
) -> str:
    try:
        if tuple(record) != tuple(fields):
            raise ValueError(_ERROR)
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
        or len(payload) >= _MAX_JSON_BYTES
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


def _read_regular(path: Path, *, maximum: int) -> bytes:
    try:
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


def _authority_record(evidence: Mapping[str, Any], row: Mapping[str, str]) -> dict[str, Any]:
    insertion = offline_recovery._normalise_optional(
        row["_atom_site.pdbx_PDB_ins_code"]
    )
    raw_altloc = row["_atom_site.label_alt_id"]
    if (
        type(raw_altloc) is not str
        or not raw_altloc
        or raw_altloc != raw_altloc.strip()
    ):
        raise ValueError(_ERROR)
    altloc = offline_recovery._normalise_optional(raw_altloc)
    if (
        row["_atom_site.pdbx_PDB_model_num"] != evidence["protein_model_num"]
        or row["_atom_site.auth_asym_id"] != evidence["protein_auth_asym_id"]
        or row["_atom_site.auth_comp_id"] != evidence["protein_auth_comp_id"]
        or row["_atom_site.auth_seq_id"] != evidence["protein_auth_seq_id"]
        or insertion != evidence["protein_pdbx_PDB_ins_code"]
        or row["_atom_site.auth_atom_id"] != evidence["protein_auth_atom_id"]
        or row["_atom_site.type_symbol"] != "S"
        or row["_atom_site.auth_comp_id"] != "CYS"
        or row["_atom_site.label_comp_id"] != "CYS"
        or row["_atom_site.auth_atom_id"] != "SG"
        or row["_atom_site.label_atom_id"] != "SG"
        or any(
            type(row[field]) is not str or row[field] in {"", ".", "?"}
            for field in (
                "_atom_site.label_asym_id",
                "_atom_site.label_comp_id",
                "_atom_site.label_seq_id",
                "_atom_site.label_atom_id",
            )
        )
    ):
        raise ValueError(_ERROR)
    record: dict[str, Any] = {
        "target_residue_atom_condition_version": _CONDITION_VERSION,
        "sample_index_row_id": evidence["sample_index_row_id"],
        "pdb_id": evidence["pdb_id"],
        "protein_model_num": evidence["protein_model_num"],
        "protein_auth_asym_id": evidence["protein_auth_asym_id"],
        "protein_auth_comp_id": evidence["protein_auth_comp_id"],
        "protein_auth_seq_id": evidence["protein_auth_seq_id"],
        "protein_pdbx_PDB_ins_code": evidence["protein_pdbx_PDB_ins_code"],
        "protein_auth_atom_id": evidence["protein_auth_atom_id"],
        "protein_type_symbol": row["_atom_site.type_symbol"],
        "protein_label_alt_id": altloc,
        "source_atom_site_id": evidence["source_atom_site_id"],
        "protein_label_asym_id": row["_atom_site.label_asym_id"],
        "protein_label_comp_id": row["_atom_site.label_comp_id"],
        "protein_label_seq_id": row["_atom_site.label_seq_id"],
        "protein_label_atom_id": row["_atom_site.label_atom_id"],
        "source_structure_filesystem_sha256": evidence[
            "source_structure_filesystem_sha256"
        ],
        "source_condition_evidence_sha256": evidence[
            "condition_evidence_record_sha256"
        ],
        "condition_authority_status": "resolved_authoritative",
        "target_residue_atom_condition_record_sha256": "",
    }
    record["target_residue_atom_condition_record_sha256"] = _record_sha256(
        record,
        TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS,
        "target_residue_atom_condition_record_sha256",
    )
    return record


def _validate_bundle(bundle: object, *, require_field_order: bool) -> dict[str, Any]:
    if (
        type(bundle) is not dict
        or len(bundle) != 20
        or set(bundle) != set(TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS)
        or (
            require_field_order
            and tuple(bundle) != TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS
        )
    ):
        raise ValueError(_ERROR)
    try:
        samples = tuple(bundle["sample_order"])
        record_fields = tuple(bundle["target_residue_atom_condition_record_fields"])
        records = bundle["target_residue_atom_condition_records"]
        evidence_digests = tuple(bundle["source_condition_evidence_record_sha256s"])
    except Exception as error:
        raise ValueError(_ERROR) from error
    if (
        bundle["target_residue_atom_condition_authority_bundle_version"]
        != _AUTHORITY_BUNDLE_VERSION
        or bundle["source_formal_inventory_transport_sha256"]
        != _FORMAL_INVENTORY_TRANSPORT_SHA256
        or bundle["source_formal_inventory_sha256"]
        != _FORMAL_INVENTORY_INTERNAL_SHA256
        or bundle["source_condition_contract_design_version"]
        != _CONTRACT_DESIGN_VERSION
        or bundle["source_condition_contract_design_production_sha256"]
        != _CONTRACT_DESIGN_PRODUCTION_SHA256
        or bundle["source_condition_contract_design_response_sha256"]
        != _CONTRACT_DESIGN_RESPONSE_SHA256
        or bundle["source_evidence_compiler_production_sha256"]
        != _SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256
        or bundle["source_evidence_bundle_transport_sha256"]
        != _SOURCE_EVIDENCE_BUNDLE_TRANSPORT_SHA256
        or bundle["source_evidence_bundle_sha256"]
        != _SOURCE_EVIDENCE_BUNDLE_INTERNAL_SHA256
        or bundle["source_offline_recovery_design_response_sha256"]
        != _OFFLINE_RECOVERY_RESPONSE_SHA256
        or evidence_digests != _EXPECTED_EVIDENCE_RECORD_SHA256S
        or samples != _EXPECTED_SAMPLES
        or record_fields != TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS
        or type(records) not in (tuple, list)
        or len(records) != 11
        or bundle["target_residue_atom_condition_record_count"] != 11
        or bundle["resolved_authoritative_count"] != 11
        or bundle["all_records_resolved_authoritative"] is not True
        or bundle["ready_for_target_residue_atom_condition_adapter_design"] is not True
        or bundle["feature_semantics_audit_required_before_training"] is not True
        or bundle["target_residue_atom_condition_authority_bundle_sha256"]
        != _record_sha256(
            {
                field: bundle[field]
                for field in TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS
            },
            TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS,
            "target_residue_atom_condition_authority_bundle_sha256",
        )
    ):
        raise ValueError(_ERROR)
    identities: list[tuple[str, ...]] = []
    record_digests: list[str] = []
    observed_evidence_digests: list[str] = []
    for index, record in enumerate(records):
        if (
            type(record) is not dict
            or set(record) != set(TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS)
        ):
            raise ValueError(_ERROR)
        ordered = {
            field: record[field]
            for field in TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS
        }
        if (
            ordered["sample_index_row_id"] != _EXPECTED_SAMPLES[index]
            or ordered["target_residue_atom_condition_version"] != _CONDITION_VERSION
            or ordered["condition_authority_status"] != "resolved_authoritative"
            or ordered["protein_type_symbol"] != "S"
            or ordered["protein_auth_comp_id"] != "CYS"
            or ordered["protein_label_comp_id"] != "CYS"
            or ordered["protein_auth_atom_id"] != "SG"
            or ordered["protein_label_atom_id"] != "SG"
            or ordered["target_residue_atom_condition_record_sha256"]
            != _record_sha256(
                ordered,
                TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS,
                "target_residue_atom_condition_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        identities.append(
            tuple(
                ordered[field]
                for field in (
                    "pdb_id",
                    "protein_model_num",
                    "protein_auth_asym_id",
                    "protein_auth_comp_id",
                    "protein_auth_seq_id",
                    "protein_pdbx_PDB_ins_code",
                    "protein_auth_atom_id",
                    "source_atom_site_id",
                )
            )
        )
        record_digests.append(
            ordered["target_residue_atom_condition_record_sha256"]
        )
        observed_evidence_digests.append(ordered["source_condition_evidence_sha256"])
    if (
        len(set(identities)) != 11
        or len(set(record_digests)) != 11
        or tuple(observed_evidence_digests) != _EXPECTED_EVIDENCE_RECORD_SHA256S
        or len(set(observed_evidence_digests)) != 11
    ):
        raise ValueError(_ERROR)
    return {
        field: bundle[field]
        for field in TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS
    }


def _bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    validated = _validate_bundle(bundle, require_field_order=True)
    payload = _canonical_json_bytes(validated)
    decoded = _strict_json_object(payload)
    _validate_bundle(decoded, require_field_order=False)
    if _canonical_json_bytes(decoded) != payload:
        raise ValueError(_ERROR)
    return payload


def build_covapie_current11_target_residue_atom_condition_authority_v1(
    *,
    source_formal_inventory: bytes,
    source_evidence_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the all-or-nothing Current11 exact-row authority bundle."""

    if (
        type(source_formal_inventory) is not bytes
        or type(source_evidence_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    inventory_snapshot = bytes(source_formal_inventory)
    evidence_snapshot = bytes(source_evidence_bundle)
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        if (
            tuple(contract_design._FUTURE_CONDITION_RECORD_FIELDS)
            != TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS
            or contract_design._CONDITION_VERSION != _CONDITION_VERSION
            or _sha256(source_formal_inventory)
            != _FORMAL_INVENTORY_TRANSPORT_SHA256
            or _sha256(source_evidence_bundle)
            != _SOURCE_EVIDENCE_BUNDLE_TRANSPORT_SHA256
        ):
            raise ValueError(_ERROR)

        compiler_path = Path(source_evidence_compiler.__file__)
        contract_path = Path(contract_design.__file__)
        offline_path = Path(offline_recovery.__file__)
        if (
            _sha256(_read_regular(compiler_path, maximum=4 * 1024 * 1024))
            != _SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256
            or _sha256(_read_regular(contract_path, maximum=4 * 1024 * 1024))
            != _CONTRACT_DESIGN_MODULE_SHA256
            or _sha256(_read_regular(offline_path, maximum=4 * 1024 * 1024))
            != _OFFLINE_RECOVERY_PRODUCTION_SHA256
        ):
            raise ValueError(_ERROR)

        inventory = _strict_json_object(source_formal_inventory)
        if (
            inventory.get("source_inventory_bundle_sha256")
            != _FORMAL_INVENTORY_INTERNAL_SHA256
            or inventory.get("source_contract_design_version")
            != _CONTRACT_DESIGN_VERSION
            or inventory.get("source_contract_design_production_sha256")
            != _CONTRACT_DESIGN_PRODUCTION_SHA256
            or inventory.get("source_contract_design_response_sha256")
            != _CONTRACT_DESIGN_RESPONSE_SHA256
            or _SHA256_RE.fullmatch(
                inventory.get("source_contract_design_response_sha256", "")
                if type(inventory.get("source_contract_design_response_sha256")) is str
                else ""
            )
            is None
        ):
            raise ValueError(_ERROR)

        compiled = source_evidence_compiler.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
            source_formal_inventory=source_formal_inventory,
            repo_root=repo_root,
        )
        compiled_bytes = source_evidence_compiler._bundle_bytes(compiled)
        if compiled_bytes != source_evidence_bundle:
            raise ValueError(_ERROR)
        evidence_bundle = _strict_json_object(source_evidence_bundle)
        if (
            evidence_bundle.get("source_evidence_bundle_sha256")
            != _SOURCE_EVIDENCE_BUNDLE_INTERNAL_SHA256
            or evidence_bundle.get("source_formal_inventory_transport_sha256")
            != _FORMAL_INVENTORY_TRANSPORT_SHA256
            or evidence_bundle.get("source_formal_inventory_sha256")
            != _FORMAL_INVENTORY_INTERNAL_SHA256
            or evidence_bundle.get("source_offline_recovery_design_response_sha256")
            != _OFFLINE_RECOVERY_RESPONSE_SHA256
            or tuple(evidence_bundle.get("source_offline_recovery_record_sha256s", ()))
            != _EXPECTED_RECOVERY_RECORD_SHA256S
            or tuple(evidence_bundle.get("sample_order", ())) != _EXPECTED_SAMPLES
            or evidence_bundle.get("condition_evidence_record_count") != 11
            or evidence_bundle.get("all_source_recovery_records_ready") is not True
            or evidence_bundle.get(
                "ready_for_target_residue_atom_condition_authority_materialization"
            )
            is not True
        ):
            raise ValueError(_ERROR)
        evidence_records = evidence_bundle.get("condition_evidence_records")
        if type(evidence_records) is not list or len(evidence_records) != 11:
            raise ValueError(_ERROR)
        evidence_digests = tuple(
            record.get("condition_evidence_record_sha256")
            if type(record) is dict
            else None
            for record in evidence_records
        )
        if evidence_digests != _EXPECTED_EVIDENCE_RECORD_SHA256S:
            raise ValueError(_ERROR)

        response = offline_recovery._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=source_formal_inventory,
            repo_root=repo_root,
        )
        recovery_records = response.get("offline_source_recovery_records")
        if (
            response.get("design_response_sha256") != _OFFLINE_RECOVERY_RESPONSE_SHA256
            or response.get("ready_for_offline_source_evidence_compiler") is not True
            or response.get("feature_semantics_audit_required_before_training") is not True
            or type(recovery_records) not in (tuple, list)
            or len(recovery_records) != 11
            or tuple(
                record.get("offline_source_recovery_record_sha256")
                if type(record) is dict
                else None
                for record in recovery_records
            )
            != _EXPECTED_RECOVERY_RECORD_SHA256S
        ):
            raise ValueError(_ERROR)

        raw_snapshots: dict[Path, bytes] = {}
        authority_records: list[dict[str, Any]] = []
        for index, (evidence, recovery) in enumerate(
            zip(evidence_records, recovery_records)
        ):
            if (
                type(evidence) is not dict
                or type(recovery) is not dict
                or evidence.get("sample_index_row_id") != _EXPECTED_SAMPLES[index]
                or recovery.get("sample_index_row_id") != _EXPECTED_SAMPLES[index]
                or recovery.get("recovery_status") != "recoverable_offline_unique"
                or recovery.get("ready_for_offline_source_evidence_compiler") is not True
                or recovery.get("proposed_condition_evidence_record") != evidence
                or tuple(recovery.get("matched_atom_site_ids", ()))
                != (evidence.get("source_atom_site_id"),)
                or recovery.get("raw_atom_site_match_count") != 1
                or recovery.get("recomputed_raw_sha256")
                != evidence.get("source_structure_filesystem_sha256")
            ):
                raise ValueError(_ERROR)
            locator = recovery.get("selected_raw_locator")
            normalised, raw_path, problem = offline_recovery._safe_relative(
                repo_root, locator
            )
            if (
                type(locator) is not str
                or normalised != locator
                or raw_path is None
                or problem is not None
            ):
                raise ValueError(_ERROR)
            raw_payload = offline_recovery._read_regular(
                raw_path, maximum=offline_recovery._MAX_RAW_BYTES
            )
            if _sha256(raw_payload) != evidence["source_structure_filesystem_sha256"]:
                raise ValueError(_ERROR)
            existing_snapshot = raw_snapshots.get(raw_path)
            if existing_snapshot is not None and existing_snapshot != raw_payload:
                raise ValueError(_ERROR)
            raw_snapshots[raw_path] = bytes(raw_payload)
            data_block, headers, rows = offline_recovery._parse_atom_site(
                offline_recovery._decode_raw(raw_payload, locator)
            )
            if (
                data_block != evidence["pdb_id"]
                or not set(_RAW_REQUIRED_COLUMNS).issubset(headers)
            ):
                raise ValueError(_ERROR)
            matches = tuple(
                row
                for row in rows
                if row["_atom_site.id"] == evidence["source_atom_site_id"]
            )
            if len(matches) != 1:
                raise ValueError(_ERROR)
            authority_records.append(_authority_record(evidence, matches[0]))

        if (
            len(raw_snapshots) != 11
            or len(authority_records) != 11
            or inventory_snapshot != source_formal_inventory
            or evidence_snapshot != source_evidence_bundle
        ):
            raise ValueError(_ERROR)
        for path, payload in raw_snapshots.items():
            if (
                offline_recovery._read_regular(
                    path, maximum=offline_recovery._MAX_RAW_BYTES
                )
                != payload
            ):
                raise ValueError(_ERROR)

        bundle: dict[str, Any] = {
            "target_residue_atom_condition_authority_bundle_version": _AUTHORITY_BUNDLE_VERSION,
            "source_formal_inventory_transport_sha256": _FORMAL_INVENTORY_TRANSPORT_SHA256,
            "source_formal_inventory_sha256": _FORMAL_INVENTORY_INTERNAL_SHA256,
            "source_condition_contract_design_version": inventory[
                "source_contract_design_version"
            ],
            "source_condition_contract_design_production_sha256": inventory[
                "source_contract_design_production_sha256"
            ],
            "source_condition_contract_design_response_sha256": inventory[
                "source_contract_design_response_sha256"
            ],
            "source_evidence_compiler_production_sha256": _SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256,
            "source_evidence_bundle_transport_sha256": _SOURCE_EVIDENCE_BUNDLE_TRANSPORT_SHA256,
            "source_evidence_bundle_sha256": _SOURCE_EVIDENCE_BUNDLE_INTERNAL_SHA256,
            "source_offline_recovery_design_response_sha256": _OFFLINE_RECOVERY_RESPONSE_SHA256,
            "source_condition_evidence_record_sha256s": _EXPECTED_EVIDENCE_RECORD_SHA256S,
            "sample_order": _EXPECTED_SAMPLES,
            "target_residue_atom_condition_record_fields": TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS,
            "target_residue_atom_condition_records": tuple(authority_records),
            "target_residue_atom_condition_record_count": 11,
            "resolved_authoritative_count": 11,
            "all_records_resolved_authoritative": True,
            "ready_for_target_residue_atom_condition_adapter_design": True,
            "feature_semantics_audit_required_before_training": True,
            "target_residue_atom_condition_authority_bundle_sha256": "",
        }
        bundle["target_residue_atom_condition_authority_bundle_sha256"] = _record_sha256(
            bundle,
            TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS,
            "target_residue_atom_condition_authority_bundle_sha256",
        )
        return _validate_bundle(bundle, require_field_order=True)
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


def _materialize_target_residue_atom_condition_authority_bundle_v1(
    *, bundle: Mapping[str, Any], output_path: Path,
) -> dict[str, Any]:
    """Publish canonical authority bytes without replacing an existing target."""

    if type(output_path) is not type(Path()):
        raise ValueError(_ERROR)
    try:
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
                created = os.fstat(descriptor)
                created_device, created_inode = created.st_dev, created.st_ino
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
                or _sha256(reread) != _sha256(payload)
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

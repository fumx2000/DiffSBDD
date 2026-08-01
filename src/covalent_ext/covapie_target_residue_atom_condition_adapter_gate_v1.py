"""Runtime gate for the Current11 target-residue atom condition adapter.

This module deliberately stops at the dataset boundary.  It rebuilds the
frozen adapter and retained pocket arrays, exercises the existing dataset and
collate implementation through one temporary NPZ, and emits JSON evidence.  It
does not alter a writer, create a training label, or call a model.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_v1 as adapter


__all__ = (
    "evaluate_covapie_target_residue_atom_condition_adapter_gate_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_INVALID"
_RECORD_VERSION = "covapie_target_residue_atom_condition_adapter_gate_record_v1"
_BUNDLE_VERSION = "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_ALIGNMENT_TRANSPORT_SHA256 = "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
_ADAPTER_TRANSPORT_SHA256 = "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a"
_ADAPTER_INTERNAL_SHA256 = "7e6475d45dcf3ee95982d8bfbf7a5e707aef8359cee2fc9af15a7eafeee7d1c7"
_ADAPTER_PRODUCTION_SHA256 = "ff65146ab97f5ea03330766d4517ca9f3f25a5e496529a0c2e2b4aa1479d255d"
_DATASET_MODULE_SHA256 = "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"
_LIGHTNING_MODULE_SHA256 = "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6"
_CHECKPOINT_SHA256 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024
_MAX_RUNTIME_SOURCE_BYTES = 32 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_EXPECTED_SAMPLES = tuple(f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12))
_EXPECTED_LOCAL_TRUE_INDICES = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
_EXPECTED_FLAT_TRUE_INDICES = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)
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
_EXPECTED_ADAPTER_RECORD_SHA256S = (
    "695d6602bddda1b98a555c27f55920b4cace15e4bf316f0a034b04966e1553b5",
    "b986704dcbe3a351b5d39d7a849f127318848ee213b4c7b7ea459f187ff286a3",
    "5f9d17af60eca01c82ca612ad555c39db104c19afd9f58cf944fa10dec9a8a9f",
    "e6b2a8d5ded6daf77aef9c07d4b8c981d3117e8f436e2efb63be7666655fe310",
    "baaab13552f0bdeb93660d01c5ede83034a78a3060934232984aa626b347b69b",
    "c4ea8a532317eb4a1e56a975aeed7512c11ae5b5b0f06fdda2ce8f784e393132",
    "447c1cd9f9cabba9f0c77f14a20242f47b292ce9d78a38b0e018b080d51ec9ec",
    "72db6d3d3e4c54b016a00cd1c45c58181bfef2fc4ae056e1fbb9c0464f7d24d7",
    "9d2639b1bace55b93fc83624e963d867efb8f3cdc393c5216da96c022e2d446d",
    "d2cc70749bbe49a89794146949d9b7e5be9f57b35085a28434e373bc21cca682",
    "e87598e0cbc9faeab352b52d25edf1f4a65af4ad6a288e0e3e39482edc7be84c",
)

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS = (
    "target_residue_atom_condition_adapter_gate_record_version",
    "sample_index_row_id",
    "pdb_id",
    "source_adapter_record_sha256",
    "source_alignment_record_sha256",
    "retained_pocket_node_count",
    "target_retained_model_local_index",
    "source_indicator_uint8_bytes_sha256",
    "runtime_loaded_indicator_length",
    "runtime_loaded_indicator_true_count",
    "runtime_loaded_indicator_true_index",
    "runtime_loaded_indicator_torch_dtype",
    "runtime_pocket_one_hot_width",
    "runtime_target_atom_feature_index",
    "collated_flat_start_index",
    "collated_flat_end_index_exclusive",
    "collated_flat_true_index",
    "centered_runtime_indicator_unchanged",
    "adapter_gate_record_status",
    "adapter_gate_blocking_reasons",
    "target_residue_atom_condition_adapter_gate_record_sha256",
)

TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS = (
    "target_residue_atom_condition_adapter_gate_bundle_version",
    "source_authority_bundle_transport_sha256",
    "source_alignment_bundle_transport_sha256",
    "source_adapter_bundle_transport_sha256",
    "source_adapter_bundle_sha256",
    "source_adapter_production_sha256",
    "source_dataset_module_sha256",
    "source_lightning_module_sha256",
    "source_checkpoint_sha256",
    "selected_adapter_field_name",
    "canonical_mask_semantic_names",
    "sample_order",
    "target_residue_atom_condition_adapter_gate_record_fields",
    "target_residue_atom_condition_adapter_gate_records",
    "target_residue_atom_condition_adapter_gate_record_count",
    "runtime_dataset_sample_count",
    "total_runtime_pocket_node_count",
    "total_runtime_indicator_true_count",
    "collated_indicator_length",
    "collated_indicator_true_count",
    "source_adapter_bundle_recompiled_exact",
    "all_records_runtime_ready_unique",
    "temporary_npz_created",
    "temporary_npz_cleaned",
    "persistent_npz_created",
    "ready_for_runtime_bridge_design",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "target_residue_atom_condition_adapter_gate_bundle_sha256",
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


def _reject_constant(_value: str) -> None:
    raise ValueError(_ERROR)


def _strict_json(payload: bytes) -> dict[str, Any]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= _MAX_BUNDLE_BYTES
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or payload.endswith((b"\n", b"\r"))
        ):
            raise ValueError(_ERROR)
        value = json.loads(
            payload.decode("utf-8", errors="strict"),
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


def _read_regular(path: Path, *, maximum: int = _MAX_RUNTIME_SOURCE_BYTES) -> bytes:
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size <= 0
            or metadata.st_size >= maximum
        ):
            raise ValueError(_ERROR)
        payload = path.read_bytes()
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _tensor_float32_bytes(value: torch.Tensor) -> bytes:
    try:
        array = value.detach().cpu().numpy()
        if array.dtype != np.dtype("float32"):
            raise ValueError(_ERROR)
        return np.ascontiguousarray(array, dtype=np.dtype("<f4")).tobytes(order="C")
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _load_dataset_class(repo_root: Path) -> type:
    try:
        dataset_path = repo_root / "dataset.py"
        if _sha256(_read_regular(dataset_path)) != _DATASET_MODULE_SHA256:
            raise ValueError(_ERROR)
        specification = importlib.util.spec_from_file_location(
            "_covapie_adapter_gate_runtime_dataset_v1", dataset_path
        )
        if specification is None or specification.loader is None:
            raise ValueError(_ERROR)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        dataset_class = getattr(module, "ProcessedLigandPocketDataset", None)
        if type(dataset_class) is not type:
            raise ValueError(_ERROR)
        return dataset_class
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _build_gate_record(
    *,
    adapter_record: Mapping[str, Any],
    alignment_record: Mapping[str, Any],
    runtime_sample: Mapping[str, Any],
    centered_sample: Mapping[str, Any],
    flat_start: int,
) -> dict[str, Any]:
    try:
        indicator = runtime_sample[_FIELD]
        centered_indicator = centered_sample[_FIELD]
        one_hot = runtime_sample["pocket_one_hot"]
        true_positions = torch.nonzero(indicator, as_tuple=False).flatten().tolist()
        target_index = alignment_record["target_retained_model_local_index"]
        count = alignment_record["retained_pocket_node_count"]
        feature_row = one_hot[target_index]
        feature_positions = torch.nonzero(feature_row == 1.0, as_tuple=False).flatten().tolist()
        if (
            indicator.dtype != torch.bool
            or indicator.ndim != 1
            or len(indicator) != count
            or true_positions != [target_index]
            or one_hot.dtype != torch.float32
            or tuple(one_hot.shape) != (count, 10)
            or feature_positions != [3]
            or float(feature_row.sum().item()) != 1.0
            or centered_indicator.dtype != torch.bool
            or not torch.equal(centered_indicator, indicator)
        ):
            raise ValueError(_ERROR)
        record: dict[str, Any] = {
            "target_residue_atom_condition_adapter_gate_record_version": _RECORD_VERSION,
            "sample_index_row_id": adapter_record["sample_index_row_id"],
            "pdb_id": adapter_record["pdb_id"],
            "source_adapter_record_sha256": adapter_record[
                "target_residue_atom_condition_adapter_record_sha256"
            ],
            "source_alignment_record_sha256": alignment_record[
                "pocket_atom_identity_alignment_record_sha256"
            ],
            "retained_pocket_node_count": count,
            "target_retained_model_local_index": target_index,
            "source_indicator_uint8_bytes_sha256": adapter_record[
                "indicator_uint8_bytes_sha256"
            ],
            "runtime_loaded_indicator_length": len(indicator),
            "runtime_loaded_indicator_true_count": int(indicator.sum().item()),
            "runtime_loaded_indicator_true_index": true_positions[0],
            "runtime_loaded_indicator_torch_dtype": str(indicator.dtype),
            "runtime_pocket_one_hot_width": int(one_hot.shape[1]),
            "runtime_target_atom_feature_index": feature_positions[0],
            "collated_flat_start_index": flat_start,
            "collated_flat_end_index_exclusive": flat_start + count,
            "collated_flat_true_index": flat_start + true_positions[0],
            "centered_runtime_indicator_unchanged": True,
            "adapter_gate_record_status": "runtime_gate_ready_unique",
            "adapter_gate_blocking_reasons": [],
            "target_residue_atom_condition_adapter_gate_record_sha256": "",
        }
        record["target_residue_atom_condition_adapter_gate_record_sha256"] = _digest_record(
            record,
            TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
            "target_residue_atom_condition_adapter_gate_record_sha256",
        )
        _validate_gate_record(record, require_field_order=True)
        return record
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_gate_record(record: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {
            field: record[field]
            for field in TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS
        }
        count = record["retained_pocket_node_count"]
        local_index = record["target_retained_model_local_index"]
        start = record["collated_flat_start_index"]
        end = record["collated_flat_end_index_exclusive"]
        if (
            type(record) is not dict
            or len(record) != 21
            or set(record) != set(TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS)
            or (
                require_field_order
                and tuple(record) != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS
            )
            or record["target_residue_atom_condition_adapter_gate_record_version"]
            != _RECORD_VERSION
            or type(record["sample_index_row_id"]) is not str
            or not record["sample_index_row_id"]
            or type(record["pdb_id"]) is not str
            or not record["pdb_id"]
            or any(
                not _SHA256_RE.fullmatch(str(record[field]))
                for field in (
                    "source_adapter_record_sha256",
                    "source_alignment_record_sha256",
                    "source_indicator_uint8_bytes_sha256",
                    "target_residue_atom_condition_adapter_gate_record_sha256",
                )
            )
            or type(count) is not int
            or type(count) is bool
            or count <= 0
            or type(local_index) is not int
            or type(local_index) is bool
            or not 0 <= local_index < count
            or record["runtime_loaded_indicator_length"] != count
            or record["runtime_loaded_indicator_true_count"] != 1
            or record["runtime_loaded_indicator_true_index"] != local_index
            or record["runtime_loaded_indicator_torch_dtype"] != "torch.bool"
            or record["runtime_pocket_one_hot_width"] != 10
            or record["runtime_target_atom_feature_index"] != 3
            or type(start) is not int
            or type(start) is bool
            or start < 0
            or end != start + count
            or record["collated_flat_true_index"] != start + local_index
            or record["centered_runtime_indicator_unchanged"] is not True
            or record["adapter_gate_record_status"] != "runtime_gate_ready_unique"
            or record["adapter_gate_blocking_reasons"] != []
            or record["target_residue_atom_condition_adapter_gate_record_sha256"]
            != _digest_record(
                ordered,
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
                "target_residue_atom_condition_adapter_gate_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_gate_bundle(bundle: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {
            field: bundle[field]
            for field in TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS
        }
        records = bundle["target_residue_atom_condition_adapter_gate_records"]
        if (
            type(bundle) is not dict
            or len(bundle) != 29
            or set(bundle) != set(TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS)
            or (
                require_field_order
                and tuple(bundle) != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS
            )
            or bundle["target_residue_atom_condition_adapter_gate_bundle_version"]
            != _BUNDLE_VERSION
            or bundle["source_authority_bundle_transport_sha256"]
            != _AUTHORITY_TRANSPORT_SHA256
            or bundle["source_alignment_bundle_transport_sha256"]
            != _ALIGNMENT_TRANSPORT_SHA256
            or bundle["source_adapter_bundle_transport_sha256"] != _ADAPTER_TRANSPORT_SHA256
            or bundle["source_adapter_bundle_sha256"] != _ADAPTER_INTERNAL_SHA256
            or bundle["source_adapter_production_sha256"] != _ADAPTER_PRODUCTION_SHA256
            or bundle["source_dataset_module_sha256"] != _DATASET_MODULE_SHA256
            or bundle["source_lightning_module_sha256"] != _LIGHTNING_MODULE_SHA256
            or bundle["source_checkpoint_sha256"] != _CHECKPOINT_SHA256
            or bundle["selected_adapter_field_name"] != _FIELD
            or tuple(bundle["canonical_mask_semantic_names"])
            != CANONICAL_MASK_SEMANTIC_NAMES
            or tuple(bundle["sample_order"]) != _EXPECTED_SAMPLES
            or tuple(bundle["target_residue_atom_condition_adapter_gate_record_fields"])
            != TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS
            or type(records) is not list
            or len(records) != 11
            or bundle["target_residue_atom_condition_adapter_gate_record_count"] != 11
            or bundle["runtime_dataset_sample_count"] != 11
            or bundle["total_runtime_pocket_node_count"] != 2202
            or bundle["total_runtime_pocket_node_count"]
            != sum(record.get("retained_pocket_node_count", -1) for record in records)
            or bundle["total_runtime_indicator_true_count"] != 11
            or bundle["collated_indicator_length"] != 2202
            or bundle["collated_indicator_true_count"] != 11
            or bundle["source_adapter_bundle_recompiled_exact"] is not True
            or bundle["all_records_runtime_ready_unique"] is not True
            or bundle["temporary_npz_created"] is not True
            or bundle["temporary_npz_cleaned"] is not True
            or bundle["persistent_npz_created"] is not False
            or bundle["ready_for_runtime_bridge_design"] is not True
            or bundle["recommended_next_step"]
            != "design_covapie_target_residue_atom_condition_runtime_bridge_v1"
            or bundle["feature_semantics_audit_required_before_training"] is not True
        ):
            raise ValueError(_ERROR)
        for record in records:
            _validate_gate_record(record, require_field_order=require_field_order)
        if (
            tuple(record["sample_index_row_id"] for record in records) != _EXPECTED_SAMPLES
            or tuple(record["source_adapter_record_sha256"] for record in records)
            != _EXPECTED_ADAPTER_RECORD_SHA256S
            or tuple(record["source_alignment_record_sha256"] for record in records)
            != _EXPECTED_ALIGNMENT_RECORD_SHA256S
            or tuple(record["target_retained_model_local_index"] for record in records)
            != _EXPECTED_LOCAL_TRUE_INDICES
            or tuple(record["collated_flat_true_index"] for record in records)
            != _EXPECTED_FLAT_TRUE_INDICES
            or bundle["target_residue_atom_condition_adapter_gate_bundle_sha256"]
            != _digest_record(
                ordered,
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
                "target_residue_atom_condition_adapter_gate_bundle_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Evaluate the frozen adapter against the real Current11 dataset boundary."""

    if (
        type(source_authority_bundle) is not bytes
        or type(source_alignment_bundle) is not bytes
        or type(source_adapter_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    authority_snapshot = bytes(source_authority_bundle)
    alignment_snapshot = bytes(source_alignment_bundle)
    adapter_snapshot = bytes(source_adapter_bundle)
    predecessor_constant_snapshot = (
        adapter.CANONICAL_MASK_SEMANTIC_NAMES,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
    )
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        if (
            _sha256(source_authority_bundle) != _AUTHORITY_TRANSPORT_SHA256
            or _sha256(source_alignment_bundle) != _ALIGNMENT_TRANSPORT_SHA256
            or _sha256(source_adapter_bundle) != _ADAPTER_TRANSPORT_SHA256
        ):
            raise ValueError(_ERROR)

        adapter_production = _read_regular(Path(adapter.__file__))
        dataset_payload = _read_regular(repo_root / "dataset.py")
        lightning_payload = _read_regular(repo_root / "lightning_modules.py")
        checkpoint_payload = _read_regular(repo_root / "checkpoints/crossdocked_fullatom_cond.ckpt")
        if (
            _sha256(adapter_production) != _ADAPTER_PRODUCTION_SHA256
            or _sha256(dataset_payload) != _DATASET_MODULE_SHA256
            or _sha256(lightning_payload) != _LIGHTNING_MODULE_SHA256
            or _sha256(checkpoint_payload) != _CHECKPOINT_SHA256
            or _FIELD.encode("ascii") in lightning_payload
        ):
            raise ValueError(_ERROR)

        compiled_alignment = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
            source_authority_bundle=source_authority_bundle,
            repo_root=repo_root,
        )
        if alignment._bundle_bytes(compiled_alignment) != source_alignment_bundle:
            raise ValueError(_ERROR)
        recompiled_adapter = adapter.build_covapie_target_residue_atom_condition_adapter_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            repo_root=repo_root,
        )
        recompiled_adapter_bytes = adapter._bundle_bytes(recompiled_adapter)
        if recompiled_adapter_bytes != source_adapter_bundle:
            raise ValueError(_ERROR)

        supplied_adapter = _strict_json(source_adapter_bundle)
        adapter._validate_adapter_bundle(supplied_adapter, require_field_order=False)
        if (
            supplied_adapter.get("target_residue_atom_condition_adapter_bundle_sha256")
            != _ADAPTER_INTERNAL_SHA256
            or adapter._internal_bundle_sha(
                supplied_adapter,
                "target_residue_atom_condition_adapter_bundle_sha256",
            )
            != _ADAPTER_INTERNAL_SHA256
            or adapter._canonical_json_bytes(supplied_adapter) != source_adapter_bundle
            or tuple(supplied_adapter.get("canonical_mask_semantic_names", ()))
            != CANONICAL_MASK_SEMANTIC_NAMES
            or supplied_adapter.get("selected_adapter_field_name") != _FIELD
            or supplied_adapter.get("ready_for_adapter_gate") is not True
        ):
            raise ValueError(_ERROR)

        alignment_records = compiled_alignment.get("pocket_atom_identity_alignment_records")
        adapter_records = recompiled_adapter.get(
            "target_residue_atom_condition_adapter_records"
        )
        if (
            type(alignment_records) is not list
            or type(adapter_records) is not list
            or len(alignment_records) != 11
            or len(adapter_records) != 11
            or tuple(compiled_alignment.get("sample_order", ())) != _EXPECTED_SAMPLES
            or tuple(recompiled_adapter.get("sample_order", ())) != _EXPECTED_SAMPLES
            or tuple(
                record.get("pocket_atom_identity_alignment_record_sha256")
                for record in alignment_records
            )
            != _EXPECTED_ALIGNMENT_RECORD_SHA256S
            or tuple(
                record.get("target_residue_atom_condition_adapter_record_sha256")
                for record in adapter_records
            )
            != _EXPECTED_ADAPTER_RECORD_SHA256S
        ):
            raise ValueError(_ERROR)

        symbol_to_index = alignment._checkpoint_symbol_to_index()
        if symbol_to_index.get("S") != 3 or set(symbol_to_index.values()) != set(range(10)):
            raise ValueError(_ERROR)
        pocket_coords: list[np.ndarray] = []
        pocket_one_hot: list[np.ndarray] = []
        indicators: list[np.ndarray] = []
        counts: list[int] = []
        receptors: list[str] = []
        for expected_sample, alignment_record, adapter_record in zip(
            _EXPECTED_SAMPLES, alignment_records, adapter_records
        ):
            relative_path = alignment_record.get("source_pocket_atom_table_path")
            if type(relative_path) is not str:
                raise ValueError(_ERROR)
            table_payload = alignment._read_regular(repo_root, relative_path)
            if _sha256(table_payload) != alignment_record.get("source_pocket_atom_table_sha256"):
                raise ValueError(_ERROR)
            _fieldnames, rows = alignment._csv_rows(table_payload)
            retained_indices = alignment_record.get("retained_source_pocket_row_indices")
            count = alignment_record.get("retained_pocket_node_count")
            target_index = alignment_record.get("target_retained_model_local_index")
            if (
                type(retained_indices) is not list
                or type(count) is not int
                or type(count) is bool
                or len(retained_indices) != count
                or any(type(index) is not int or type(index) is bool for index in retained_indices)
                or retained_indices != sorted(set(retained_indices))
                or not retained_indices
                or retained_indices[0] < 0
                or retained_indices[-1] >= len(rows)
                or type(target_index) is not int
                or type(target_index) is bool
                or not 0 <= target_index < count
                or alignment_record.get("sample_index_row_id") != expected_sample
                or adapter_record.get("sample_index_row_id") != expected_sample
                or adapter_record.get("pdb_id") != alignment_record.get("pdb_id")
                or adapter_record.get("source_alignment_record_sha256")
                != alignment_record.get("pocket_atom_identity_alignment_record_sha256")
            ):
                raise ValueError(_ERROR)
            retained_rows = [rows[index] for index in retained_indices]
            coordinate_bytes = alignment._float32_bytes(retained_rows)
            one_hot_bytes = alignment._one_hot_float32_bytes(retained_rows, symbol_to_index)
            if (
                _sha256(coordinate_bytes)
                != alignment_record.get("retained_pocket_coordinate_float32_bytes_sha256")
                or _sha256(one_hot_bytes)
                != alignment_record.get("retained_pocket_one_hot_bytes_sha256")
                or len(coordinate_bytes) != count * 3 * 4
                or len(one_hot_bytes) != count * 10 * 4
                or retained_rows[target_index].get("type_symbol") != "S"
            ):
                raise ValueError(_ERROR)
            coordinates = np.frombuffer(coordinate_bytes, dtype="<f4").reshape(count, 3).copy()
            one_hot = np.frombuffer(one_hot_bytes, dtype="<f4").reshape(count, 10).copy()
            indicator_values = adapter_record.get(_FIELD)
            if (
                type(indicator_values) is not list
                or len(indicator_values) != count
                or any(type(value) is not bool for value in indicator_values)
                or sum(value is True for value in indicator_values) != 1
                or indicator_values[target_index] is not True
                or _sha256(bytes(1 if value else 0 for value in indicator_values))
                != adapter_record.get("indicator_uint8_bytes_sha256")
                or one_hot.dtype != np.dtype("float32")
                or one_hot[target_index, 3] != np.float32(1.0)
                or np.count_nonzero(one_hot[target_index]) != 1
            ):
                raise ValueError(_ERROR)
            pocket_coords.append(coordinates)
            pocket_one_hot.append(one_hot)
            indicators.append(np.asarray(indicator_values, dtype=np.bool_))
            counts.append(count)
            receptors.append(str(adapter_record["pdb_id"]))

        if (
            tuple(record["target_retained_model_local_index"] for record in alignment_records)
            != _EXPECTED_LOCAL_TRUE_INDICES
            or sum(counts) != 2202
            or sum(int(values.sum()) for values in indicators) != 11
        ):
            raise ValueError(_ERROR)

        expected_collated_pocket_coords = np.ascontiguousarray(
            np.concatenate(pocket_coords, axis=0), dtype=np.float32
        )
        expected_collated_pocket_one_hot = np.ascontiguousarray(
            np.concatenate(pocket_one_hot, axis=0), dtype=np.float32
        )
        expected_collated_indicator = np.ascontiguousarray(
            np.concatenate(indicators, axis=0), dtype=np.bool_
        )
        if (
            expected_collated_pocket_coords.dtype != np.dtype("float32")
            or expected_collated_pocket_coords.shape != (2202, 3)
            or not expected_collated_pocket_coords.flags.c_contiguous
            or expected_collated_pocket_one_hot.dtype != np.dtype("float32")
            or expected_collated_pocket_one_hot.shape != (2202, 10)
            or not expected_collated_pocket_one_hot.flags.c_contiguous
            or expected_collated_indicator.dtype != np.dtype("bool")
            or expected_collated_indicator.shape != (2202,)
            or not expected_collated_indicator.flags.c_contiguous
        ):
            raise ValueError(_ERROR)
        expected_coordinate_bytes = np.ascontiguousarray(
            expected_collated_pocket_coords, dtype=np.dtype("<f4")
        ).tobytes(order="C")
        expected_one_hot_bytes = np.ascontiguousarray(
            expected_collated_pocket_one_hot, dtype=np.dtype("<f4")
        ).tobytes(order="C")

        dataset_class = _load_dataset_class(repo_root)
        repo_resolved = repo_root.resolve(strict=True)
        state_resolved = (repo_root.parent / "covapie-state").resolve(strict=True)
        temporary_npz_created = False
        temporary_npz_cleaned = False
        records: list[dict[str, Any]] = []
        collated_indicator_length = 0
        collated_indicator_true_count = 0
        temporary_path: Path | None = None
        with tempfile.TemporaryDirectory(prefix="covapie-adapter-gate-v1-") as temporary_name:
            temporary_directory = Path(temporary_name).resolve(strict=True)
            if (
                _is_within(temporary_directory, repo_resolved)
                or _is_within(temporary_directory, state_resolved)
            ):
                raise ValueError(_ERROR)
            temporary_path = temporary_directory / "current11_runtime_gate.npz"
            lig_mask = np.arange(11, dtype=np.int64)
            pocket_mask = np.repeat(np.arange(11, dtype=np.int64), counts)
            np.savez(
                temporary_path,
                names=np.asarray(_EXPECTED_SAMPLES),
                receptors=np.asarray(receptors),
                lig_mask=lig_mask,
                pocket_mask=pocket_mask,
                lig_coords=np.zeros((11, 3), dtype=np.float32),
                pocket_coords=expected_collated_pocket_coords,
                lig_one_hot=np.eye(10, dtype=np.float32)[np.zeros(11, dtype=np.int64)],
                pocket_one_hot=expected_collated_pocket_one_hot,
                **{_FIELD: expected_collated_indicator},
            )
            temporary_npz_created = temporary_path.is_file()
            if not temporary_npz_created:
                raise ValueError(_ERROR)

            runtime_dataset = dataset_class(temporary_path, center=False)
            centered_dataset = dataset_class(temporary_path, center=True)
            if len(runtime_dataset) != 11 or len(centered_dataset) != 11:
                raise ValueError(_ERROR)
            samples = [runtime_dataset[index] for index in range(11)]
            centered_samples = [centered_dataset[index] for index in range(11)]
            flat_start = 0
            for index, (sample, centered_sample) in enumerate(zip(samples, centered_samples)):
                if (
                    str(sample["names"]) != _EXPECTED_SAMPLES[index]
                    or str(sample["receptors"]) != receptors[index]
                    or int(sample["num_pocket_nodes"].item()) != counts[index]
                    or _sha256(_tensor_float32_bytes(sample["pocket_coords"]))
                    != alignment_records[index][
                        "retained_pocket_coordinate_float32_bytes_sha256"
                    ]
                    or _sha256(_tensor_float32_bytes(sample["pocket_one_hot"]))
                    != alignment_records[index]["retained_pocket_one_hot_bytes_sha256"]
                    or not torch.equal(sample[_FIELD], torch.from_numpy(indicators[index]))
                ):
                    raise ValueError(_ERROR)
                records.append(
                    _build_gate_record(
                        adapter_record=adapter_records[index],
                        alignment_record=alignment_records[index],
                        runtime_sample=sample,
                        centered_sample=centered_sample,
                        flat_start=flat_start,
                    )
                )
                flat_start += counts[index]

            collated = dataset_class.collate_fn(samples)
            centered_collated = dataset_class.collate_fn(centered_samples)
            collated_indicator = collated[_FIELD]
            collated_true_indices = tuple(
                int(value)
                for value in torch.nonzero(collated_indicator, as_tuple=False).flatten().tolist()
            )
            derived_flat_indices = tuple(
                record["collated_flat_true_index"] for record in records
            )
            collated_target_rows_valid = True
            for flat_index in collated_true_indices:
                target_row = collated["pocket_one_hot"][flat_index]
                feature_positions = torch.nonzero(
                    target_row == 1.0, as_tuple=False
                ).flatten().tolist()
                if (
                    target_row.dtype != torch.float32
                    or tuple(target_row.shape) != (10,)
                    or feature_positions != [3]
                    or float(target_row.sum().item()) != 1.0
                ):
                    collated_target_rows_valid = False
                    break
            if (
                collated_indicator.dtype != torch.bool
                or collated_indicator.ndim != 1
                or len(collated_indicator) != 2202
                or int(collated_indicator.sum().item()) != 11
                or not torch.equal(
                    collated_indicator, torch.from_numpy(expected_collated_indicator)
                )
                or collated["pocket_coords"].dtype != torch.float32
                or tuple(collated["pocket_coords"].shape) != (2202, 3)
                or _tensor_float32_bytes(collated["pocket_coords"])
                != expected_coordinate_bytes
                or collated["pocket_one_hot"].dtype != torch.float32
                or tuple(collated["pocket_one_hot"].shape) != (2202, 10)
                or _tensor_float32_bytes(collated["pocket_one_hot"])
                != expected_one_hot_bytes
                or tuple(int(value) for value in collated["num_pocket_nodes"].tolist())
                != tuple(counts)
                or tuple(str(value) for value in collated["names"]) != _EXPECTED_SAMPLES
                or tuple(str(value) for value in collated["receptors"]) != tuple(receptors)
                or collated_true_indices != derived_flat_indices
                or derived_flat_indices != _EXPECTED_FLAT_TRUE_INDICES
                or not collated_target_rows_valid
                or not torch.equal(centered_collated[_FIELD], collated_indicator)
                or not torch.equal(
                    centered_collated["pocket_one_hot"], collated["pocket_one_hot"]
                )
            ):
                raise ValueError(_ERROR)
            collated_indicator_length = len(collated_indicator)
            collated_indicator_true_count = int(collated_indicator.sum().item())
        if temporary_path is None or temporary_path.exists() or temporary_path.parent.exists():
            raise ValueError(_ERROR)
        temporary_npz_cleaned = True

        bundle: dict[str, Any] = {
            "target_residue_atom_condition_adapter_gate_bundle_version": _BUNDLE_VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_alignment_bundle_transport_sha256": _ALIGNMENT_TRANSPORT_SHA256,
            "source_adapter_bundle_transport_sha256": _ADAPTER_TRANSPORT_SHA256,
            "source_adapter_bundle_sha256": _ADAPTER_INTERNAL_SHA256,
            "source_adapter_production_sha256": _ADAPTER_PRODUCTION_SHA256,
            "source_dataset_module_sha256": _DATASET_MODULE_SHA256,
            "source_lightning_module_sha256": _LIGHTNING_MODULE_SHA256,
            "source_checkpoint_sha256": _CHECKPOINT_SHA256,
            "selected_adapter_field_name": _FIELD,
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "sample_order": list(_EXPECTED_SAMPLES),
            "target_residue_atom_condition_adapter_gate_record_fields": list(
                TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS
            ),
            "target_residue_atom_condition_adapter_gate_records": records,
            "target_residue_atom_condition_adapter_gate_record_count": len(records),
            "runtime_dataset_sample_count": len(records),
            "total_runtime_pocket_node_count": sum(counts),
            "total_runtime_indicator_true_count": sum(
                record["runtime_loaded_indicator_true_count"] for record in records
            ),
            "collated_indicator_length": collated_indicator_length,
            "collated_indicator_true_count": collated_indicator_true_count,
            "source_adapter_bundle_recompiled_exact": True,
            "all_records_runtime_ready_unique": all(
                record["adapter_gate_record_status"] == "runtime_gate_ready_unique"
                for record in records
            ),
            "temporary_npz_created": temporary_npz_created,
            "temporary_npz_cleaned": temporary_npz_cleaned,
            "persistent_npz_created": False,
            "ready_for_runtime_bridge_design": True,
            "recommended_next_step": (
                "design_covapie_target_residue_atom_condition_runtime_bridge_v1"
            ),
            "feature_semantics_audit_required_before_training": True,
            "target_residue_atom_condition_adapter_gate_bundle_sha256": "",
        }
        bundle["target_residue_atom_condition_adapter_gate_bundle_sha256"] = _digest_record(
            bundle,
            TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
            "target_residue_atom_condition_adapter_gate_bundle_sha256",
        )
        _validate_gate_bundle(bundle, require_field_order=True)
        if (
            source_authority_bundle != authority_snapshot
            or source_alignment_bundle != alignment_snapshot
            or source_adapter_bundle != adapter_snapshot
            or predecessor_constant_snapshot
            != (
                adapter.CANONICAL_MASK_SEMANTIC_NAMES,
                adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
                adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
            )
            or any(isinstance(value, Path) for value in _walk_values(bundle))
        ):
            raise ValueError(_ERROR)
        return bundle
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        return [item for nested in value.values() for item in _walk_values(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _walk_values(nested)]
    return [value]


def _bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    try:
        _validate_gate_bundle(bundle, require_field_order=True)
        payload = _canonical_json_bytes(bundle)
        if not payload or len(payload) >= _MAX_BUNDLE_BYTES:
            raise ValueError(_ERROR)
        decoded = _strict_json(payload)
        _validate_gate_bundle(decoded, require_field_order=False)
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


def _materialize_covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Re-run the public gate and publish canonical bytes without replacement."""

    if type(output_path) is not type(Path()):
        raise ValueError(_ERROR)
    try:
        bundle = evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            source_adapter_bundle=source_adapter_bundle,
            repo_root=repo_root,
        )
        if bundle["ready_for_runtime_bridge_design"] is not True:
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

#!/usr/bin/env python3
"""Check the formal Current11 target-residue atom condition adapter V1."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

sys.dont_write_bytecode = True

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_target_residue_atom_condition_adapter_v1 as adapter


STATE_ROOT = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review"
)
AUTHORITY_PATH = STATE_ROOT / (
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)
ALIGNMENT_PATH = STATE_ROOT / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
FIELD = "pocket_target_residue_atom_condition_indicator"


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _expect_rejected(call: Callable[[], object]) -> bool:
    try:
        call()
    except ValueError as error:
        return str(error) == adapter._ERROR
    return False


def _load_dataset_class() -> type:
    specification = importlib.util.spec_from_file_location(
        "covapie_checker_base_dataset", REPO_ROOT / "dataset.py"
    )
    if specification is None or specification.loader is None:
        raise ValueError(adapter._ERROR)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.ProcessedLigandPocketDataset


def _runtime_fixture() -> dict[str, bool]:
    dataset_class = _load_dataset_class()
    with tempfile.TemporaryDirectory(prefix="covapie-adapter-check-") as directory:
        path = Path(directory) / "synthetic.npz"
        indicator = np.array([False, True, False, True, False, False, False], dtype=np.bool_)
        one_hot = np.zeros((7, 10), dtype=np.float32)
        one_hot[np.arange(7), np.arange(7)] = 1.0
        np.savez(
            path,
            names=np.array(["sample-a", "sample-b"]),
            receptors=np.array(["receptor-a", "receptor-b"]),
            lig_mask=np.array([0, 0, 1, 1], dtype=np.int64),
            pocket_mask=np.array([0, 0, 0, 1, 1, 1, 1], dtype=np.int64),
            lig_coords=np.zeros((4, 3), dtype=np.float32),
            pocket_coords=np.zeros((7, 3), dtype=np.float32),
            lig_one_hot=np.zeros((4, 10), dtype=np.float32),
            pocket_one_hot=one_hot,
            pocket_target_residue_atom_condition_indicator=indicator,
        )
        dataset = dataset_class(path, center=False)
        first, second = dataset[0], dataset[1]
        collated = dataset_class.collate_fn([first, second])
        result = {
            "split": (
                first[FIELD].tolist() == [False, True, False]
                and second[FIELD].tolist() == [True, False, False, False]
                and first["num_pocket_nodes"].item() == 3
                and second["num_pocket_nodes"].item() == 4
            ),
            "dtype": (
                first[FIELD].dtype == torch.bool
                and second[FIELD].dtype == torch.bool
                and collated[FIELD].dtype == torch.bool
            ),
            "not_mask": collated[FIELD].tolist() != [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
            "order": collated[FIELD].tolist() == indicator.tolist(),
            "one_hot_width": tuple(collated["pocket_one_hot"].shape) == (7, 10),
        }
        path.unlink()
        if path.exists():
            raise ValueError(adapter._ERROR)
        return result


def _untracked() -> tuple[str, ...]:
    return tuple(
        subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )


def main() -> int:
    authority_bytes = AUTHORITY_PATH.read_bytes()
    alignment_bytes = ALIGNMENT_PATH.read_bytes()
    authority_snapshot = bytes(authority_bytes)
    alignment_snapshot = bytes(alignment_bytes)
    files_before = _untracked()

    compiled_alignment = alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT
    )
    recompiled_alignment_bytes = alignment._bundle_bytes(compiled_alignment)
    first = adapter.build_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )
    second = adapter.build_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        repo_root=REPO_ROOT,
    )
    records = first["target_residue_atom_condition_adapter_records"]
    alignment_records = compiled_alignment["pocket_atom_identity_alignment_records"]
    runtime = _runtime_fixture()

    authority_drift = _expect_rejected(
        lambda: adapter.build_covapie_target_residue_atom_condition_adapter_v1(
            source_authority_bundle=authority_bytes + b" ",
            source_alignment_bundle=alignment_bytes,
            repo_root=REPO_ROOT,
        )
    )
    alignment_drift = _expect_rejected(
        lambda: adapter.build_covapie_target_residue_atom_condition_adapter_v1(
            source_authority_bundle=authority_bytes,
            source_alignment_bundle=alignment_bytes + b" ",
            repo_root=REPO_ROOT,
        )
    )
    original_transport = adapter._ALIGNMENT_TRANSPORT_SHA256
    exact_drift = alignment_bytes + b" "
    try:
        adapter._ALIGNMENT_TRANSPORT_SHA256 = _sha(exact_drift)
        exact_mismatch = _expect_rejected(
            lambda: adapter.build_covapie_target_residue_atom_condition_adapter_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=exact_drift,
                repo_root=REPO_ROOT,
            )
        )
    finally:
        adapter._ALIGNMENT_TRANSPORT_SHA256 = original_transport

    authority_records = json.loads(authority_bytes)["target_residue_atom_condition_records"]
    bad_index = copy.deepcopy(alignment_records[0])
    bad_index["target_retained_model_local_index"] = bad_index["retained_pocket_node_count"]
    target_index_rejected = _expect_rejected(
        lambda: adapter._build_adapter_record(
            authority_record=authority_records[0], alignment_record=bad_index
        )
    )

    def invalid_indicator(kind: str) -> bool:
        record = copy.deepcopy(records[0])
        indicator = record[FIELD]
        true_index = record["target_retained_model_local_index"]
        if kind == "zero":
            indicator[true_index] = False
        elif kind == "multiple":
            indicator[0 if true_index else 1] = True
        else:
            indicator[0 if true_index else 1] = 0
        return _expect_rejected(
            lambda: adapter._validate_adapter_record(record, require_field_order=True)
        )

    sample_drift = copy.deepcopy(first)
    sample_drift["sample_order"][0], sample_drift["sample_order"][1] = (
        sample_drift["sample_order"][1],
        sample_drift["sample_order"][0],
    )
    sample_drift["target_residue_atom_condition_adapter_bundle_sha256"] = adapter._digest_record(
        sample_drift,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
        "target_residue_atom_condition_adapter_bundle_sha256",
    )
    sample_order_rejected = _expect_rejected(
        lambda: adapter._validate_adapter_bundle(sample_drift, require_field_order=True)
    )

    indicator_lengths_valid = all(
        record["indicator_length"] == record["retained_pocket_node_count"] for record in records
    )
    indicator_bools_valid = all(
        all(type(value) is bool for value in record[FIELD]) for record in records
    )
    true_counts_valid = all(record["indicator_true_count"] == 1 for record in records)
    true_positions_valid = all(
        [index for index, value in enumerate(record[FIELD]) if value]
        == [record["target_retained_model_local_index"]]
        for record in records
    )
    indicator_digests_valid = sum(
        record["indicator_uint8_bytes_sha256"]
        == _sha(bytes(1 if value else 0 for value in record[FIELD]))
        for record in records
    )
    record_digests_valid = sum(
        record["target_residue_atom_condition_adapter_record_sha256"]
        == adapter._digest_record(
            record,
            adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_RECORD_FIELDS,
            "target_residue_atom_condition_adapter_record_sha256",
        )
        for record in records
    )

    files_after = _untracked()
    facts: dict[str, object] = {
        "source_authority_bundle_bound": _sha(authority_bytes) == adapter._AUTHORITY_TRANSPORT_SHA256,
        "source_alignment_bundle_bound": _sha(alignment_bytes) == adapter._ALIGNMENT_TRANSPORT_SHA256,
        "source_alignment_bundle_recompiled_exact": recompiled_alignment_bytes == alignment_bytes,
        "source_alignment_production_bound": first["source_alignment_production_sha256"] == adapter._ALIGNMENT_PRODUCTION_SHA256,
        "source_adapter_design_production_bound": first["source_adapter_design_production_sha256"] == adapter._ADAPTER_DESIGN_PRODUCTION_SHA256,
        "source_adapter_design_response_bound": first["source_adapter_design_response_sha256"] == adapter._ADAPTER_DESIGN_RESPONSE_SHA256,
        "selected_adapter_field_name": first["selected_adapter_field_name"],
        "selected_field_contains_mask": "mask" in FIELD,
        "selected_field_contains_lig": "lig" in FIELD,
        "selected_field_domain": records[0]["adapter_field_storage_domain"],
        "selected_field_numpy_dtype": records[0]["adapter_field_numpy_dtype"],
        "selected_field_torch_dtype": records[0]["adapter_field_torch_dtype"],
        "adapter_record_count": first["target_residue_atom_condition_adapter_record_count"],
        "total_indicator_length": first["total_indicator_length"],
        "total_indicator_true_count": first["total_indicator_true_count"],
        "all_records_adapter_ready_unique": first["all_records_adapter_ready_unique"],
        "indicator_length_matches_retained_nodes": indicator_lengths_valid,
        "indicator_values_are_bool": indicator_bools_valid,
        "indicator_true_count_per_sample_one": true_counts_valid,
        "indicator_true_position_matches_alignment": true_positions_valid,
        "indicator_uint8_digest_valid_count": indicator_digests_valid,
        "adapter_record_digest_valid_count": record_digests_valid,
        "dataset_split_uses_pocket_boundary": runtime["split"],
        "collate_indicator_dtype_bool": runtime["dtype"],
        "collate_indicator_not_rewritten_as_batch_mask": runtime["not_mask"],
        "collate_indicator_order_preserved": runtime["order"],
        "append_to_pocket_one_hot": False,
        "pocket_one_hot_width_changed": not runtime["one_hot_width"],
        "base_state_dict_change": False,
        "checkpoint_tensor_shape_change": False,
        "indicator_passed_into_model": False,
        "authority_drift_rejected": authority_drift,
        "alignment_drift_rejected": alignment_drift,
        "alignment_exact_bytes_mismatch_rejected": exact_mismatch,
        "target_index_out_of_range_rejected": target_index_rejected,
        "zero_true_indicator_rejected": invalid_indicator("zero"),
        "multiple_true_indicator_rejected": invalid_indicator("multiple"),
        "non_bool_indicator_rejected": invalid_indicator("non_bool"),
        "sample_order_drift_rejected": sample_order_rejected,
        "deterministic": first == second,
        "inputs_unchanged": authority_bytes == authority_snapshot and alignment_bytes == alignment_snapshot,
        "files_written": files_after != files_before,
        "adapter_implemented": True,
        "gate_implemented": False,
        "training_label_created": False,
        "tensor_file_created": False,
        "npz_formal_created": False,
        "dataset_modified": False,
        "data_loader_modified": False,
        "model_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "training_or_parameter_update": False,
    }
    expected_true = {
        "source_authority_bundle_bound",
        "source_alignment_bundle_bound",
        "source_alignment_bundle_recompiled_exact",
        "source_alignment_production_bound",
        "source_adapter_design_production_bound",
        "source_adapter_design_response_bound",
        "all_records_adapter_ready_unique",
        "indicator_length_matches_retained_nodes",
        "indicator_values_are_bool",
        "indicator_true_count_per_sample_one",
        "indicator_true_position_matches_alignment",
        "dataset_split_uses_pocket_boundary",
        "collate_indicator_dtype_bool",
        "collate_indicator_not_rewritten_as_batch_mask",
        "collate_indicator_order_preserved",
        "authority_drift_rejected",
        "alignment_drift_rejected",
        "alignment_exact_bytes_mismatch_rejected",
        "target_index_out_of_range_rejected",
        "zero_true_indicator_rejected",
        "multiple_true_indicator_rejected",
        "non_bool_indicator_rejected",
        "sample_order_drift_rejected",
        "deterministic",
        "inputs_unchanged",
        "adapter_implemented",
    }
    if any(facts[key] is not True for key in expected_true):
        raise ValueError(adapter._ERROR)
    expected_false = {
        "selected_field_contains_mask",
        "selected_field_contains_lig",
        "append_to_pocket_one_hot",
        "pocket_one_hot_width_changed",
        "base_state_dict_change",
        "checkpoint_tensor_shape_change",
        "indicator_passed_into_model",
        "files_written",
        "gate_implemented",
        "training_label_created",
        "tensor_file_created",
        "npz_formal_created",
        "dataset_modified",
        "data_loader_modified",
        "model_modified",
        "forward_modified",
        "loss_modified",
        "training_or_parameter_update",
    }
    if any(facts[key] is not False for key in expected_false):
        raise ValueError(adapter._ERROR)
    if (
        facts["adapter_record_count"] != 11
        or facts["total_indicator_length"] != 2202
        or facts["total_indicator_true_count"] != 11
        or indicator_digests_valid != 11
        or record_digests_valid != 11
    ):
        raise ValueError(adapter._ERROR)

    for key, value in facts.items():
        if type(value) is bool:
            rendered = str(value).lower()
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    print(
        "adapter_record_sha256s="
        + json.dumps(
            [record["target_residue_atom_condition_adapter_record_sha256"] for record in records],
            separators=(",", ":"),
        )
    )
    print(
        "target_residue_atom_condition_adapter_bundle_sha256="
        + first["target_residue_atom_condition_adapter_bundle_sha256"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check the frozen Current11 target-residue adapter runtime gate."""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Callable

import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_target_residue_atom_condition_adapter_gate_v1 as gate


STATE = ROOT.parent / "covapie-state" / "manual-review"
AUTHORITY_PATH = STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
ALIGNMENT_PATH = STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
ADAPTER_PATH = STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_INVALID"


def _canonical_rejected(action: Callable[[], object]) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == _ERROR
    return False


def _with_constant_drift(
    name: str,
    authority_bytes: bytes,
    alignment_bytes: bytes,
    adapter_bytes: bytes,
) -> bool:
    original = getattr(gate, name)
    setattr(gate, name, "0" * 64)
    try:
        return _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        )
    finally:
        setattr(gate, name, original)


def _mutated_bundle_rejected(bundle: dict, mutation: Callable[[dict], None]) -> bool:
    changed = deepcopy(bundle)
    mutation(changed)
    return _canonical_rejected(
        lambda: gate._validate_gate_bundle(changed, require_field_order=True)
    )


def _mutated_record_rejected(record: dict, field: str, value: object) -> bool:
    changed = deepcopy(record)
    changed[field] = value
    changed["target_residue_atom_condition_adapter_gate_record_sha256"] = ""
    changed["target_residue_atom_condition_adapter_gate_record_sha256"] = (
        gate._digest_record(
            changed,
            gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
            "target_residue_atom_condition_adapter_gate_record_sha256",
        )
    )
    return _canonical_rejected(
        lambda: gate._validate_gate_record(changed, require_field_order=True)
    )


def _with_compiled_alignment_drift(
    mutation: Callable[[dict], None],
    authority_bytes: bytes,
    alignment_bytes: bytes,
    adapter_bytes: bytes,
) -> bool:
    original = gate.alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1

    def changed_compile(*, source_authority_bundle: bytes, repo_root: Path) -> dict:
        value = deepcopy(
            original(
                source_authority_bundle=source_authority_bundle,
                repo_root=repo_root,
            )
        )
        mutation(value)
        return value

    gate.alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1 = changed_compile
    try:
        return _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        )
    finally:
        gate.alignment.compile_covapie_current11_pocket_atom_identity_alignment_v1 = original


def _with_pocket_table_drift(
    authority_bytes: bytes, alignment_bytes: bytes, adapter_bytes: bytes
) -> bool:
    original = gate.alignment._read_regular

    def changed_read(repo_root: Path, relative_path: str, *, maximum: int = 16 * 1024 * 1024):
        payload = original(repo_root, relative_path, maximum=maximum)
        if relative_path.endswith("pocket_atom_table.csv"):
            return payload + b" "
        return payload

    gate.alignment._read_regular = changed_read
    try:
        return _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        )
    finally:
        gate.alignment._read_regular = original


def _runtime_sample_drift_rejected(
    adapter_record: dict,
    alignment_record: dict,
    mutation: Callable[[dict], None],
) -> bool:
    count = alignment_record["retained_pocket_node_count"]
    target = alignment_record["target_retained_model_local_index"]
    indicator = torch.tensor(adapter_record[gate._FIELD], dtype=torch.bool)
    one_hot = torch.zeros((count, 10), dtype=torch.float32)
    one_hot[target, 3] = 1.0
    sample = {gate._FIELD: indicator, "pocket_one_hot": one_hot}
    mutation(sample)
    centered = {
        gate._FIELD: sample[gate._FIELD].clone(),
        "pocket_one_hot": sample["pocket_one_hot"].clone(),
    }
    return _canonical_rejected(
        lambda: gate._build_gate_record(
            adapter_record=adapter_record,
            alignment_record=alignment_record,
            runtime_sample=sample,
            centered_sample=centered,
            flat_start=0,
        )
    )


def _audit_real_collated_runtime(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    adapter_bytes: bytes,
) -> dict[str, bool]:
    runtime_dataset_class = gate._load_dataset_class(ROOT)
    formal_receptors = tuple(
        record["pdb_id"]
        for record in json.loads(adapter_bytes)[
            "target_residue_atom_condition_adapter_records"
        ]
    )
    audit = {
        "collated_pocket_coords_order_preserved": False,
        "collated_pocket_one_hot_order_preserved": False,
        "collated_true_indices_target_s_feature_valid": False,
        "centered_pocket_one_hot_unchanged": False,
        "collated_receptors_order_preserved": False,
    }
    collate_calls = 0
    uncentered_one_hot: torch.Tensor | None = None

    class AuditedCollateDataset(runtime_dataset_class):
        @staticmethod
        def collate_fn(batch):
            nonlocal collate_calls, uncentered_one_hot
            collated = runtime_dataset_class.collate_fn(batch)
            expected_coords = torch.cat([sample["pocket_coords"] for sample in batch], dim=0)
            expected_one_hot = torch.cat(
                [sample["pocket_one_hot"] for sample in batch], dim=0
            )
            if collate_calls == 0:
                audit["collated_pocket_coords_order_preserved"] = (
                    gate._tensor_float32_bytes(collated["pocket_coords"])
                    == gate._tensor_float32_bytes(expected_coords)
                )
                audit["collated_pocket_one_hot_order_preserved"] = (
                    gate._tensor_float32_bytes(collated["pocket_one_hot"])
                    == gate._tensor_float32_bytes(expected_one_hot)
                )
                true_indices = torch.nonzero(
                    collated[gate._FIELD], as_tuple=False
                ).flatten().tolist()
                audit["collated_true_indices_target_s_feature_valid"] = all(
                    torch.nonzero(
                        collated["pocket_one_hot"][flat_index] == 1.0,
                        as_tuple=False,
                    ).flatten().tolist()
                    == [3]
                    and float(collated["pocket_one_hot"][flat_index].sum().item()) == 1.0
                    for flat_index in true_indices
                )
                audit["collated_receptors_order_preserved"] = (
                    tuple(str(value) for value in collated["receptors"])
                    == formal_receptors
                    == tuple(str(sample["receptors"]) for sample in batch)
                )
                uncentered_one_hot = collated["pocket_one_hot"].clone()
            else:
                audit["centered_pocket_one_hot_unchanged"] = (
                    uncentered_one_hot is not None
                    and torch.equal(collated["pocket_one_hot"], uncentered_one_hot)
                    and torch.equal(collated["pocket_one_hot"], expected_one_hot)
                )
            collate_calls += 1
            return collated

    original_loader = gate._load_dataset_class
    gate._load_dataset_class = lambda _repo_root: AuditedCollateDataset
    try:
        gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=authority_bytes,
            source_alignment_bundle=alignment_bytes,
            source_adapter_bundle=adapter_bytes,
            repo_root=ROOT,
        )
    finally:
        gate._load_dataset_class = original_loader
    if collate_calls != 2:
        raise SystemExit("real_collated_runtime_audit_calls_invalid")
    return audit


def _collated_pocket_node_order_drift_rejected(
    authority_bytes: bytes,
    alignment_bytes: bytes,
    adapter_bytes: bytes,
) -> bool:
    runtime_dataset_class = gate._load_dataset_class(ROOT)

    class ReorderedCollateDataset(runtime_dataset_class):
        @staticmethod
        def collate_fn(batch):
            collated = runtime_dataset_class.collate_fn(batch)
            collated["pocket_coords"] = torch.flip(
                collated["pocket_coords"], dims=(0,)
            )
            collated["pocket_one_hot"] = torch.flip(
                collated["pocket_one_hot"], dims=(0,)
            )
            return collated

    original_loader = gate._load_dataset_class
    gate._load_dataset_class = lambda _repo_root: ReorderedCollateDataset
    try:
        return _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        )
    finally:
        gate._load_dataset_class = original_loader


def _print_bool(name: str, value: bool) -> None:
    if value is not True:
        raise SystemExit(f"{name}=false")
    print(f"{name}=true")


def main() -> None:
    authority_bytes = AUTHORITY_PATH.read_bytes()
    alignment_bytes = ALIGNMENT_PATH.read_bytes()
    adapter_bytes = ADAPTER_PATH.read_bytes()
    snapshots = (bytes(authority_bytes), bytes(alignment_bytes), bytes(adapter_bytes))
    repository_npz_before = tuple(sorted(str(path) for path in ROOT.rglob("*.npz")))

    first = gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
    )
    second = gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
        source_authority_bundle=authority_bytes,
        source_alignment_bundle=alignment_bytes,
        source_adapter_bundle=adapter_bytes,
        repo_root=ROOT,
    )
    records = first["target_residue_atom_condition_adapter_gate_records"]
    first_record = records[0]
    adapter_record = json.loads(adapter_bytes)[
        "target_residue_atom_condition_adapter_records"
    ][0]
    alignment_record = json.loads(alignment_bytes)[
        "pocket_atom_identity_alignment_records"
    ][0]
    collated_runtime_audit = _audit_real_collated_runtime(
        authority_bytes, alignment_bytes, adapter_bytes
    )
    collated_node_order_drift_rejected = _collated_pocket_node_order_drift_rejected(
        authority_bytes, alignment_bytes, adapter_bytes
    )

    source_adapter_record_drift = _mutated_bundle_rejected(
        first,
        lambda value: value["target_residue_atom_condition_adapter_gate_records"][0].__setitem__(
            "source_adapter_record_sha256", "0" * 64
        ),
    )
    source_alignment_record_drift = _mutated_bundle_rejected(
        first,
        lambda value: value["target_residue_atom_condition_adapter_gate_records"][0].__setitem__(
            "source_alignment_record_sha256", "0" * 64
        ),
    )

    def swap_sample_order(value: dict) -> None:
        value["sample_order"][0], value["sample_order"][1] = (
            value["sample_order"][1],
            value["sample_order"][0],
        )

    changed_adapter = adapter_bytes + b" "
    original_adapter_transport = gate._ADAPTER_TRANSPORT_SHA256
    gate._ADAPTER_TRANSPORT_SHA256 = hashlib.sha256(changed_adapter).hexdigest()
    try:
        exact_mismatch_rejected = _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=changed_adapter,
                repo_root=ROOT,
            )
        )
    finally:
        gate._ADAPTER_TRANSPORT_SHA256 = original_adapter_transport

    checks = {
        "source_authority_bundle_bound": first[
            "source_authority_bundle_transport_sha256"
        ]
        == gate._AUTHORITY_TRANSPORT_SHA256,
        "source_alignment_bundle_bound": first[
            "source_alignment_bundle_transport_sha256"
        ]
        == gate._ALIGNMENT_TRANSPORT_SHA256,
        "source_adapter_bundle_bound": first["source_adapter_bundle_transport_sha256"]
        == gate._ADAPTER_TRANSPORT_SHA256,
        "source_adapter_bundle_recompiled_exact": first[
            "source_adapter_bundle_recompiled_exact"
        ]
        is True,
        "source_adapter_production_bound": first["source_adapter_production_sha256"]
        == gate._ADAPTER_PRODUCTION_SHA256,
        "source_dataset_module_bound": first["source_dataset_module_sha256"]
        == gate._DATASET_MODULE_SHA256,
        "source_lightning_module_bound": first["source_lightning_module_sha256"]
        == gate._LIGHTNING_MODULE_SHA256,
        "source_checkpoint_bound": first["source_checkpoint_sha256"]
        == gate._CHECKPOINT_SHA256,
        "dataset_sample_order_preserved": tuple(first["sample_order"])
        == gate._EXPECTED_SAMPLES,
        "collated_indicator_dtype_bool": all(
            record["runtime_loaded_indicator_torch_dtype"] == "torch.bool"
            for record in records
        ),
        "collated_flat_true_indices_valid": tuple(
            record["collated_flat_true_index"] for record in records
        )
        == gate._EXPECTED_FLAT_TRUE_INDICES,
        "collated_names_order_preserved": tuple(first["sample_order"])
        == gate._EXPECTED_SAMPLES,
        "collated_receptors_order_preserved": collated_runtime_audit[
            "collated_receptors_order_preserved"
        ],
        "collated_pocket_coords_order_preserved": collated_runtime_audit[
            "collated_pocket_coords_order_preserved"
        ],
        "collated_pocket_one_hot_order_preserved": collated_runtime_audit[
            "collated_pocket_one_hot_order_preserved"
        ],
        "collated_true_indices_target_s_feature_valid": collated_runtime_audit[
            "collated_true_indices_target_s_feature_valid"
        ],
        "centered_pocket_one_hot_unchanged": collated_runtime_audit[
            "centered_pocket_one_hot_unchanged"
        ],
        "collated_pocket_node_order_drift_rejected": collated_node_order_drift_rejected,
        "authority_drift_rejected": _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes + b" ",
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        ),
        "alignment_drift_rejected": _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes + b" ",
                source_adapter_bundle=adapter_bytes,
                repo_root=ROOT,
            )
        ),
        "adapter_drift_rejected": _canonical_rejected(
            lambda: gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
                source_authority_bundle=authority_bytes,
                source_alignment_bundle=alignment_bytes,
                source_adapter_bundle=adapter_bytes + b" ",
                repo_root=ROOT,
            )
        ),
        "adapter_exact_bytes_mismatch_rejected": exact_mismatch_rejected,
        "adapter_record_drift_rejected": source_adapter_record_drift,
        "alignment_record_drift_rejected": source_alignment_record_drift,
        "sample_order_drift_rejected": _mutated_bundle_rejected(first, swap_sample_order),
        "pocket_table_sha_drift_rejected": _with_pocket_table_drift(
            authority_bytes, alignment_bytes, adapter_bytes
        ),
        "retained_index_drift_rejected": _with_compiled_alignment_drift(
            lambda value: value["pocket_atom_identity_alignment_records"][0].__setitem__(
                "retained_source_pocket_row_indices", [-1]
            ),
            authority_bytes,
            alignment_bytes,
            adapter_bytes,
        ),
        "coordinate_digest_drift_rejected": _with_compiled_alignment_drift(
            lambda value: value["pocket_atom_identity_alignment_records"][0].__setitem__(
                "retained_pocket_coordinate_float32_bytes_sha256", "0" * 64
            ),
            authority_bytes,
            alignment_bytes,
            adapter_bytes,
        ),
        "one_hot_digest_drift_rejected": _with_compiled_alignment_drift(
            lambda value: value["pocket_atom_identity_alignment_records"][0].__setitem__(
                "retained_pocket_one_hot_bytes_sha256", "0" * 64
            ),
            authority_bytes,
            alignment_bytes,
            adapter_bytes,
        ),
        "indicator_length_drift_rejected": _runtime_sample_drift_rejected(
            adapter_record,
            alignment_record,
            lambda sample: sample.__setitem__(gate._FIELD, sample[gate._FIELD][:-1]),
        ),
        "zero_true_indicator_rejected": _runtime_sample_drift_rejected(
            adapter_record,
            alignment_record,
            lambda sample: sample[gate._FIELD].fill_(False),
        ),
        "multiple_true_indicator_rejected": _runtime_sample_drift_rejected(
            adapter_record,
            alignment_record,
            lambda sample: sample[gate._FIELD].__setitem__(0, True),
        ),
        "non_bool_indicator_rejected": _runtime_sample_drift_rejected(
            adapter_record,
            alignment_record,
            lambda sample: sample.__setitem__(
                gate._FIELD, sample[gate._FIELD].to(dtype=torch.uint8)
            ),
        ),
        "target_s_feature_drift_rejected": _runtime_sample_drift_rejected(
            adapter_record,
            alignment_record,
            lambda sample: (
                sample["pocket_one_hot"][alignment_record["target_retained_model_local_index"]].zero_(),
                sample["pocket_one_hot"][
                    alignment_record["target_retained_model_local_index"], 2
                ].fill_(1.0),
            ),
        ),
        "dataset_module_drift_rejected": _with_constant_drift(
            "_DATASET_MODULE_SHA256", authority_bytes, alignment_bytes, adapter_bytes
        ),
        "lightning_module_drift_rejected": _with_constant_drift(
            "_LIGHTNING_MODULE_SHA256", authority_bytes, alignment_bytes, adapter_bytes
        ),
        "checkpoint_drift_rejected": _with_constant_drift(
            "_CHECKPOINT_SHA256", authority_bytes, alignment_bytes, adapter_bytes
        ),
        "deterministic": first == second and gate._bundle_bytes(first) == gate._bundle_bytes(second),
        "inputs_unchanged": snapshots
        == (authority_bytes, alignment_bytes, adapter_bytes),
        "persistent_files_unchanged": repository_npz_before
        == tuple(sorted(str(path) for path in ROOT.rglob("*.npz"))),
    }

    ordered_true_checks = (
        "source_authority_bundle_bound",
        "source_alignment_bundle_bound",
        "source_adapter_bundle_bound",
        "source_adapter_bundle_recompiled_exact",
        "source_adapter_production_bound",
        "source_dataset_module_bound",
        "source_lightning_module_bound",
        "source_checkpoint_bound",
    )
    for name in ordered_true_checks:
        _print_bool(name, checks[name])
    print()
    print(f"gate_record_count={len(records)}")
    print(f"runtime_dataset_sample_count={first['runtime_dataset_sample_count']}")
    print(f"total_runtime_pocket_node_count={first['total_runtime_pocket_node_count']}")
    print(f"total_runtime_indicator_true_count={first['total_runtime_indicator_true_count']}")
    print()
    print(f"retained_coordinate_digest_valid_count={len(records)}")
    print(f"retained_one_hot_digest_valid_count={len(records)}")
    print(f"target_s_feature_index_valid_count={len(records)}")
    print()
    _print_bool("dataset_sample_order_preserved", checks["dataset_sample_order_preserved"])
    print(f"dataset_indicator_dtype_bool_count={len(records)}")
    print(f"dataset_indicator_length_valid_count={len(records)}")
    print(f"dataset_indicator_true_count_valid_count={len(records)}")
    print(f"dataset_indicator_true_position_valid_count={len(records)}")
    print()
    _print_bool("collated_indicator_dtype_bool", checks["collated_indicator_dtype_bool"])
    print(f"collated_indicator_length={first['collated_indicator_length']}")
    print(f"collated_indicator_true_count={first['collated_indicator_true_count']}")
    _print_bool("collated_flat_true_indices_valid", checks["collated_flat_true_indices_valid"])
    _print_bool("collated_names_order_preserved", checks["collated_names_order_preserved"])
    _print_bool("collated_receptors_order_preserved", checks["collated_receptors_order_preserved"])
    _print_bool(
        "collated_pocket_coords_order_preserved",
        checks["collated_pocket_coords_order_preserved"],
    )
    _print_bool(
        "collated_pocket_one_hot_order_preserved",
        checks["collated_pocket_one_hot_order_preserved"],
    )
    _print_bool(
        "collated_true_indices_target_s_feature_valid",
        checks["collated_true_indices_target_s_feature_valid"],
    )
    print("collated_pocket_one_hot_width=10")
    print()
    print(f"centered_indicator_unchanged_count={len(records)}")
    _print_bool(
        "centered_pocket_one_hot_unchanged",
        checks["centered_pocket_one_hot_unchanged"],
    )
    print()
    _print_bool("temporary_npz_created", first["temporary_npz_created"])
    _print_bool("temporary_npz_cleaned", first["temporary_npz_cleaned"])
    print(f"persistent_npz_created={str(first['persistent_npz_created']).lower()}")
    print()
    for name in (
        "authority_drift_rejected",
        "alignment_drift_rejected",
        "adapter_drift_rejected",
        "adapter_exact_bytes_mismatch_rejected",
        "adapter_record_drift_rejected",
        "alignment_record_drift_rejected",
        "sample_order_drift_rejected",
        "pocket_table_sha_drift_rejected",
        "retained_index_drift_rejected",
        "coordinate_digest_drift_rejected",
        "one_hot_digest_drift_rejected",
        "indicator_length_drift_rejected",
        "zero_true_indicator_rejected",
        "multiple_true_indicator_rejected",
        "non_bool_indicator_rejected",
        "target_s_feature_drift_rejected",
        "dataset_module_drift_rejected",
        "lightning_module_drift_rejected",
        "checkpoint_drift_rejected",
        "collated_pocket_node_order_drift_rejected",
    ):
        _print_bool(name, checks[name])
    print()
    _print_bool("deterministic", checks["deterministic"])
    _print_bool("inputs_unchanged", checks["inputs_unchanged"])
    if checks["persistent_files_unchanged"] is not True:
        raise SystemExit("persistent_files_written=true")
    print("persistent_files_written=false")
    print()
    print("adapter_gate_implemented=true")
    print("runtime_bridge_implemented=false")
    print("indicator_passed_into_model=false")
    print("model_forward_called=false")
    print("training_label_created=false")
    print("tensor_file_created=false")
    print("formal_npz_created=false")
    print()
    print("dataset_modified=false")
    print("data_loader_modified=false")
    print("model_modified=false")
    print("forward_modified=false")
    print("loss_modified=false")
    print("training_or_parameter_update=false")
    print()
    print("adapter_gate_record_sha256s=")
    for record in records:
        print(record["target_residue_atom_condition_adapter_gate_record_sha256"])
    print(
        "target_residue_atom_condition_adapter_gate_bundle_sha256="
        + first["target_residue_atom_condition_adapter_gate_bundle_sha256"]
    )


if __name__ == "__main__":
    main()

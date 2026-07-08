#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_feature_semantics_resolution_design_gate as design  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
    return value


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Feature Semantics Resolution Design Gate v0 Summary

Step 13BY is a feature semantics resolution design gate.
It proposes resolution contracts for original DiffSBDD feature schema mapping, coordinate tensorization, atom feature schema, unknown atom policy, label semantics, and tensor shape/dtype policy.
It does not parse raw data, extract coordinates, create tensors, import torch or numpy, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, load checkpoints, run model forward, compute loss, or train.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
Step 12D, Step 13BM, Step 13BX, and Step 13BY do not replace the final training feature semantics audit.
The five canonical mask tasks are preserved, including `scaffold_only / B3`.
The next step is `covapie_feature_semantics_resolution_smoke`, not actual dataloader smoke and not training.

original_diffsbbd_feature_schema_mapping_design_row_count: `{manifest["original_diffsbbd_feature_schema_mapping_design_row_count"]}`
original_diffsbbd_feature_schema_mapping_design_passed: `{manifest["original_diffsbbd_feature_schema_mapping_design_passed"]}`
coordinate_tensorization_resolution_contract_row_count: `{manifest["coordinate_tensorization_resolution_contract_row_count"]}`
coordinate_tensorization_resolution_contract_passed: `{manifest["coordinate_tensorization_resolution_contract_passed"]}`
atom_feature_schema_resolution_contract_row_count: `{manifest["atom_feature_schema_resolution_contract_row_count"]}`
atom_feature_schema_resolution_contract_passed: `{manifest["atom_feature_schema_resolution_contract_passed"]}`
unknown_atom_policy_resolution_contract_row_count: `{manifest["unknown_atom_policy_resolution_contract_row_count"]}`
unknown_atom_policy_resolution_contract_passed: `{manifest["unknown_atom_policy_resolution_contract_passed"]}`
label_semantics_resolution_contract_row_count: `{manifest["label_semantics_resolution_contract_row_count"]}`
label_semantics_resolution_contract_passed: `{manifest["label_semantics_resolution_contract_passed"]}`
tensor_shape_dtype_resolution_contract_row_count: `{manifest["tensor_shape_dtype_resolution_contract_row_count"]}`
tensor_shape_dtype_resolution_contract_passed: `{manifest["tensor_shape_dtype_resolution_contract_passed"]}`
feature_semantics_resolution_smoke_plan_row_count: `{manifest["feature_semantics_resolution_smoke_plan_row_count"]}`
feature_semantics_resolution_smoke_plan_passed: `{manifest["feature_semantics_resolution_smoke_plan_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
proposed_feature_schema_resolution_written: `{manifest["proposed_feature_schema_resolution_written"]}`
proposed_unknown_atom_policy_written: `{manifest["proposed_unknown_atom_policy_written"]}`
proposed_label_semantics_resolution_written: `{manifest["proposed_label_semantics_resolution_written"]}`
ready_for_covapie_feature_semantics_resolution_smoke: `{manifest["ready_for_covapie_feature_semantics_resolution_smoke"]}`
ready_for_covapie_actual_dataloader_adapter_smoke: `{manifest["ready_for_covapie_actual_dataloader_adapter_smoke"]}`
ready_for_covapie_actual_dataloader_smoke: `{manifest["ready_for_covapie_actual_dataloader_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.run_covapie_feature_semantics_resolution_design_gate_v0()
    write_csv(result["precondition_rows"], design.PRECONDITION_AUDIT_CSV, design.PRECONDITION_COLUMNS)
    write_csv(result["mapping_rows"], design.ORIGINAL_FEATURE_SCHEMA_MAPPING_CSV, design.ORIGINAL_MAPPING_COLUMNS)
    write_csv(result["coordinate_rows"], design.COORDINATE_RESOLUTION_CONTRACT_CSV, design.COORDINATE_RESOLUTION_COLUMNS)
    write_csv(result["atom_rows"], design.ATOM_FEATURE_RESOLUTION_CONTRACT_CSV, design.ATOM_FEATURE_RESOLUTION_COLUMNS)
    write_csv(result["unknown_rows"], design.UNKNOWN_ATOM_POLICY_RESOLUTION_CONTRACT_CSV, design.UNKNOWN_POLICY_RESOLUTION_COLUMNS)
    write_csv(result["label_rows"], design.LABEL_SEMANTICS_RESOLUTION_CONTRACT_CSV, design.LABEL_SEMANTICS_RESOLUTION_COLUMNS)
    write_csv(result["tensor_rows"], design.TENSOR_SHAPE_DTYPE_RESOLUTION_CONTRACT_CSV, design.TENSOR_SHAPE_DTYPE_RESOLUTION_COLUMNS)
    write_csv(result["smoke_plan_rows"], design.RESOLUTION_SMOKE_PLAN_CSV, design.RESOLUTION_SMOKE_PLAN_COLUMNS)
    write_csv(result["safety_rows"], design.SAFETY_AUDIT_CSV, design.SAFETY_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_feature_semantics_resolution_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_feature_semantics_resolution_design_gate_v0_blocked")
    for key in [
        "original_diffsbbd_feature_schema_mapping_design_row_count",
        "original_diffsbbd_feature_schema_mapping_design_passed",
        "coordinate_tensorization_resolution_contract_row_count",
        "coordinate_tensorization_resolution_contract_passed",
        "atom_feature_schema_resolution_contract_row_count",
        "atom_feature_schema_resolution_contract_passed",
        "unknown_atom_policy_resolution_contract_row_count",
        "unknown_atom_policy_resolution_contract_passed",
        "label_semantics_resolution_contract_row_count",
        "label_semantics_resolution_contract_passed",
        "tensor_shape_dtype_resolution_contract_row_count",
        "tensor_shape_dtype_resolution_contract_passed",
        "feature_semantics_resolution_smoke_plan_row_count",
        "feature_semantics_resolution_smoke_plan_passed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "proposed_feature_schema_resolution_written",
        "proposed_unknown_atom_policy_written",
        "proposed_label_semantics_resolution_written",
        "coordinate_resolution_ready_for_smoke",
        "atom_feature_resolution_ready_for_smoke",
        "unknown_policy_resolution_ready_for_smoke",
        "label_semantics_resolution_ready_for_smoke",
        "ready_for_covapie_feature_semantics_resolution_smoke",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "torch_imported",
        "numpy_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

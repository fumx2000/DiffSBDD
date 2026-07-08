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

from covalent_ext import covapie_actual_dataloader_design_gate as design  # noqa: E402


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
    text = f"""# CovaPIE Actual Dataloader Design Gate v0 Summary

Step 13BW designs the future CovaPIE actual dataloader / adapter path.
It is a design gate only: it does not implement an actual dataloader, write actual dataloader smoke, write `dataloader_smoke.csv/json`, create tensors, import torch or numpy, load checkpoints, call model forward, compute loss, or train.
It reads `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, and `equivariant_diffusion/` as static references only and does not modify original DiffSBDD dataloader/model/loss code.
It keeps the five canonical masks unchanged, including `scaffold_only / B3`.
Because `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`, the next step is a feature semantics tensorization audit gate, not actual dataloader smoke and not training.

original_dataloader_static_reference_audit_row_count: `{manifest["original_dataloader_static_reference_audit_row_count"]}`
original_dataloader_static_reference_audit_passed: `{manifest["original_dataloader_static_reference_audit_passed"]}`
actual_dataloader_adapter_design_contract_row_count: `{manifest["actual_dataloader_adapter_design_contract_row_count"]}`
actual_dataloader_adapter_design_contract_passed: `{manifest["actual_dataloader_adapter_design_contract_passed"]}`
tensorization_input_contract_row_count: `{manifest["tensorization_input_contract_row_count"]}`
tensorization_input_contract_passed: `{manifest["tensorization_input_contract_passed"]}`
batch_collate_contract_row_count: `{manifest["batch_collate_contract_row_count"]}`
batch_collate_contract_passed: `{manifest["batch_collate_contract_passed"]}`
checkpoint_compatibility_contract_row_count: `{manifest["checkpoint_compatibility_contract_row_count"]}`
checkpoint_compatibility_contract_passed: `{manifest["checkpoint_compatibility_contract_passed"]}`
feature_semantics_blocker_contract_row_count: `{manifest["feature_semantics_blocker_contract_row_count"]}`
feature_semantics_blocker_contract_passed: `{manifest["feature_semantics_blocker_contract_passed"]}`
future_smoke_plan_row_count: `{manifest["future_smoke_plan_row_count"]}`
future_smoke_plan_passed: `{manifest["future_smoke_plan_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
actual_dataloader_design_completed_current_step: `{manifest["actual_dataloader_design_completed_current_step"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
original_dataloader_modified: `{manifest["original_dataloader_modified"]}`
torch_imported: `{manifest["torch_imported"]}`
numpy_imported: `{manifest["numpy_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
loss_compute_called: `{manifest["loss_compute_called"]}`
training_allowed: `{manifest["training_allowed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
ready_for_covapie_feature_semantics_tensorization_audit_gate: `{manifest["ready_for_covapie_feature_semantics_tensorization_audit_gate"]}`
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
    result = design.run_covapie_actual_dataloader_design_gate_v0()
    write_csv(result["precondition_rows"], design.PRECONDITION_AUDIT_CSV, design.PRECONDITION_COLUMNS)
    write_csv(result["static_rows"], design.STATIC_REFERENCE_AUDIT_CSV, design.STATIC_REFERENCE_COLUMNS)
    write_csv(result["adapter_rows"], design.ADAPTER_DESIGN_CONTRACT_CSV, design.ADAPTER_DESIGN_COLUMNS)
    write_csv(result["tensor_rows"], design.TENSORIZATION_INPUT_CONTRACT_CSV, design.TENSORIZATION_INPUT_COLUMNS)
    write_csv(result["batch_rows"], design.BATCH_COLLATE_CONTRACT_CSV, design.BATCH_COLLATE_COLUMNS)
    write_csv(result["checkpoint_rows"], design.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV, design.CHECKPOINT_COMPATIBILITY_COLUMNS)
    write_csv(result["feature_rows"], design.FEATURE_SEMANTICS_BLOCKER_CONTRACT_CSV, design.FEATURE_SEMANTICS_BLOCKER_COLUMNS)
    write_csv(result["plan_rows"], design.FUTURE_SMOKE_PLAN_CSV, design.FUTURE_SMOKE_PLAN_COLUMNS)
    write_csv(result["safety_rows"], design.SAFETY_AUDIT_CSV, design.SAFETY_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_actual_dataloader_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_actual_dataloader_design_gate_v0_blocked")
    for key in [
        "original_dataloader_static_reference_audit_row_count",
        "original_dataloader_static_reference_audit_passed",
        "actual_dataloader_adapter_design_contract_row_count",
        "actual_dataloader_adapter_design_contract_passed",
        "tensorization_input_contract_row_count",
        "tensorization_input_contract_passed",
        "batch_collate_contract_row_count",
        "batch_collate_contract_passed",
        "checkpoint_compatibility_contract_row_count",
        "checkpoint_compatibility_contract_passed",
        "feature_semantics_blocker_contract_row_count",
        "feature_semantics_blocker_contract_passed",
        "future_smoke_plan_row_count",
        "future_smoke_plan_passed",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "torch_imported",
        "numpy_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_feature_semantics_tensorization_audit_gate",
        "ready_for_covapie_actual_dataloader_adapter_smoke",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

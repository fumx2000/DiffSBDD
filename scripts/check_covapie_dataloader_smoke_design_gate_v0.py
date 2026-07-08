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

from covalent_ext import covapie_dataloader_smoke_design_gate as design  # noqa: E402


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
    text = f"""# CovaPIE Dataloader Smoke Design Gate v0 Summary

Step 13BT designs the next minimal metadata-only dataloader smoke.
It does not write metadata dataloader smoke, actual dataloader smoke, a real dataloader, final dataset artifacts, a new sample index, split assignments, leakage matrix, tensors, checkpoints, or training artifacts.
It does not import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or original DiffSBDD model/dataloader/loss code.
The next allowed step is `covapie_metadata_dataloader_smoke`, which is still metadata-only and must not become actual PyTorch dataloader smoke.
The five canonical masks are preserved, including `scaffold_only / B3`.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.

runtime_boundary_contract_row_count: `{manifest["runtime_boundary_contract_row_count"]}`
runtime_boundary_contract_passed: `{manifest["runtime_boundary_contract_passed"]}`
metadata_dataset_api_contract_row_count: `{manifest["metadata_dataset_api_contract_row_count"]}`
metadata_dataset_api_contract_passed: `{manifest["metadata_dataset_api_contract_passed"]}`
metadata_getitem_output_mapping_contract_row_count: `{manifest["metadata_getitem_output_mapping_contract_row_count"]}`
metadata_getitem_output_mapping_contract_passed: `{manifest["metadata_getitem_output_mapping_contract_passed"]}`
tensorization_blocker_contract_row_count: `{manifest["tensorization_blocker_contract_row_count"]}`
tensorization_blocker_contract_passed: `{manifest["tensorization_blocker_contract_passed"]}`
batch_collate_design_contract_row_count: `{manifest["batch_collate_design_contract_row_count"]}`
batch_collate_design_contract_passed: `{manifest["batch_collate_design_contract_passed"]}`
checkpoint_runtime_risk_contract_row_count: `{manifest["checkpoint_runtime_risk_contract_row_count"]}`
checkpoint_runtime_risk_contract_passed: `{manifest["checkpoint_runtime_risk_contract_passed"]}`
metadata_dataloader_smoke_plan_row_count: `{manifest["metadata_dataloader_smoke_plan_row_count"]}`
metadata_dataloader_smoke_plan_passed: `{manifest["metadata_dataloader_smoke_plan_passed"]}`
metadata_dataloader_smoke_written: `{manifest["metadata_dataloader_smoke_written"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
original_dataloader_modified: `{manifest["original_dataloader_modified"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
ready_for_covapie_metadata_dataloader_smoke: `{manifest["ready_for_covapie_metadata_dataloader_smoke"]}`
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
    result = design.run_covapie_dataloader_smoke_design_gate_v0()
    write_csv(result["precondition_rows"], design.PRECONDITION_AUDIT_CSV, design.PRECONDITION_COLUMNS)
    write_csv(result["runtime_rows"], design.RUNTIME_BOUNDARY_CONTRACT_CSV, design.RUNTIME_BOUNDARY_COLUMNS)
    write_csv(result["api_rows"], design.METADATA_DATASET_API_CONTRACT_CSV, design.METADATA_DATASET_API_COLUMNS)
    write_csv(result["mapping_rows"], design.GETITEM_OUTPUT_MAPPING_CONTRACT_CSV, design.GETITEM_OUTPUT_MAPPING_COLUMNS)
    write_csv(result["blocker_rows"], design.TENSORIZATION_BLOCKER_CONTRACT_CSV, design.TENSORIZATION_BLOCKER_COLUMNS)
    write_csv(result["batch_rows"], design.BATCH_COLLATE_DESIGN_CONTRACT_CSV, design.BATCH_COLLATE_DESIGN_COLUMNS)
    write_csv(result["checkpoint_rows"], design.CHECKPOINT_RUNTIME_RISK_CONTRACT_CSV, design.CHECKPOINT_RUNTIME_RISK_COLUMNS)
    write_csv(result["plan_rows"], design.METADATA_DATALOADER_SMOKE_PLAN_CSV, design.METADATA_DATALOADER_SMOKE_PLAN_COLUMNS)
    write_csv(result["safety_rows"], design.SAFETY_AUDIT_CSV, design.SAFETY_AUDIT_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_dataloader_smoke_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_dataloader_smoke_design_gate_v0_blocked")
    for key in [
        "runtime_boundary_contract_row_count",
        "runtime_boundary_contract_passed",
        "metadata_dataset_api_contract_row_count",
        "metadata_dataset_api_contract_passed",
        "metadata_getitem_output_mapping_contract_row_count",
        "metadata_getitem_output_mapping_contract_passed",
        "tensorization_blocker_contract_row_count",
        "tensorization_blocker_contract_passed",
        "batch_collate_design_contract_row_count",
        "batch_collate_design_contract_passed",
        "checkpoint_runtime_risk_contract_row_count",
        "checkpoint_runtime_risk_contract_passed",
        "metadata_dataloader_smoke_plan_row_count",
        "metadata_dataloader_smoke_plan_passed",
        "metadata_dataloader_smoke_written",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_metadata_dataloader_smoke",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

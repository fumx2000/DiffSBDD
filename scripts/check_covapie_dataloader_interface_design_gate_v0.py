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

from covalent_ext import covapie_dataloader_interface_design_gate as design_gate  # noqa: E402


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
    text = f"""# CovaPIE Dataloader Interface Design Gate v0 Summary

Step 13BQ designs the interface between the CovaPIE final dataset smoke preview and a future dataloader.
It does not implement a dataloader, write dataloader interface smoke, write actual dataloader smoke, import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or any original DiffSBDD model/dataloader/loss code.
It does not write real `final_dataset.csv/json`, generic `final_dataset_smoke.csv/json`, a new sample index, split assignments, or a leakage matrix.
It reads Step 13BP/13BO/13BN/13BM/13BK/13BH/13BE derived artifacts and uses original DiffSBDD files only as static interface references.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.
This design gate allows dataloader interface smoke next, not actual dataloader smoke and not training.

dataloader_input_source_contract_row_count: `{manifest["dataloader_input_source_contract_row_count"]}`
dataloader_input_source_contract_passed: `{manifest["dataloader_input_source_contract_passed"]}`
dataloader_field_mapping_contract_row_count: `{manifest["dataloader_field_mapping_contract_row_count"]}`
dataloader_field_mapping_contract_passed: `{manifest["dataloader_field_mapping_contract_passed"]}`
dataloader_feature_interface_contract_row_count: `{manifest["dataloader_feature_interface_contract_row_count"]}`
dataloader_feature_interface_contract_passed: `{manifest["dataloader_feature_interface_contract_passed"]}`
dataloader_mask_interface_contract_row_count: `{manifest["dataloader_mask_interface_contract_row_count"]}`
dataloader_mask_interface_contract_passed: `{manifest["dataloader_mask_interface_contract_passed"]}`
dataloader_batch_collate_contract_row_count: `{manifest["dataloader_batch_collate_contract_row_count"]}`
dataloader_batch_collate_contract_passed: `{manifest["dataloader_batch_collate_contract_passed"]}`
checkpoint_compatibility_contract_row_count: `{manifest["checkpoint_compatibility_contract_row_count"]}`
checkpoint_compatibility_contract_passed: `{manifest["checkpoint_compatibility_contract_passed"]}`
dataloader_interface_smoke_plan_row_count: `{manifest["dataloader_interface_smoke_plan_row_count"]}`
dataloader_interface_smoke_plan_passed: `{manifest["dataloader_interface_smoke_plan_passed"]}`
dataloader_interface_smoke_written: `{manifest["dataloader_interface_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
original_dataloader_modified: `{manifest["original_dataloader_modified"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
ready_for_covapie_dataloader_interface_smoke: `{manifest["ready_for_covapie_dataloader_interface_smoke"]}`
ready_for_covapie_dataloader_smoke: `{manifest["ready_for_covapie_dataloader_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design_gate.run_covapie_dataloader_interface_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["input_rows"], design_gate.INPUT_SOURCE_CONTRACT_CSV, design_gate.INPUT_SOURCE_COLUMNS)
    write_csv(result["field_rows"], design_gate.FIELD_MAPPING_CONTRACT_CSV, design_gate.FIELD_MAPPING_COLUMNS)
    write_csv(result["feature_rows"], design_gate.FEATURE_INTERFACE_CONTRACT_CSV, design_gate.FEATURE_INTERFACE_COLUMNS)
    write_csv(result["mask_rows"], design_gate.MASK_INTERFACE_CONTRACT_CSV, design_gate.MASK_INTERFACE_COLUMNS)
    write_csv(result["batch_rows"], design_gate.BATCH_COLLATE_CONTRACT_CSV, design_gate.BATCH_COLLATE_COLUMNS)
    write_csv(result["checkpoint_rows"], design_gate.CHECKPOINT_COMPATIBILITY_CONTRACT_CSV, design_gate.CHECKPOINT_COMPATIBILITY_COLUMNS)
    write_csv(result["plan_rows"], design_gate.INTERFACE_SMOKE_PLAN_CSV, design_gate.SMOKE_PLAN_COLUMNS)
    write_csv(result["boundary_rows"], design_gate.BOUNDARY_SAFETY_CSV, design_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], design_gate.GIT_SAFETY_CSV, design_gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_dataloader_interface_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_dataloader_interface_design_gate_v0_blocked")
    for key in [
        "dataloader_input_source_contract_row_count",
        "dataloader_input_source_contract_passed",
        "dataloader_field_mapping_contract_row_count",
        "dataloader_field_mapping_contract_passed",
        "dataloader_feature_interface_contract_row_count",
        "dataloader_feature_interface_contract_passed",
        "dataloader_mask_interface_contract_row_count",
        "dataloader_mask_interface_contract_passed",
        "dataloader_batch_collate_contract_row_count",
        "dataloader_batch_collate_contract_passed",
        "checkpoint_compatibility_contract_row_count",
        "checkpoint_compatibility_contract_passed",
        "dataloader_interface_smoke_plan_row_count",
        "dataloader_interface_smoke_plan_passed",
        "dataloader_interface_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "ready_for_covapie_dataloader_interface_smoke",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

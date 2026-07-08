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

from covalent_ext import covapie_dataloader_interface_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Dataloader Interface Smoke v0 Summary

Step 13BR writes a metadata-only dataloader interface smoke preview.
It writes only `covapie_dataloader_interface_smoke_preview.csv` and `covapie_dataloader_interface_smoke_preview.json` as interface preview artifacts.
It does not write actual dataloader smoke, instantiate a dataloader, import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or original DiffSBDD model/dataloader/loss code.
It does not write real final dataset artifacts, a new sample index, split assignments, or a leakage matrix.
It preserves the five canonical masks, including `scaffold_only / B3`, and does not introduce extra masks.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.
This smoke step allows dataloader interface QA gate next, not actual dataloader smoke and not training.

dataloader_interface_smoke_preview_row_count: `{manifest["dataloader_interface_smoke_preview_row_count"]}`
dataloader_interface_smoke_preview_column_count: `{manifest["dataloader_interface_smoke_preview_column_count"]}`
input_source_smoke_audit_row_count: `{manifest["input_source_smoke_audit_row_count"]}`
input_source_smoke_audit_passed: `{manifest["input_source_smoke_audit_passed"]}`
field_mapping_smoke_audit_row_count: `{manifest["field_mapping_smoke_audit_row_count"]}`
field_mapping_smoke_audit_passed: `{manifest["field_mapping_smoke_audit_passed"]}`
feature_batch_smoke_audit_row_count: `{manifest["feature_batch_smoke_audit_row_count"]}`
feature_batch_smoke_audit_passed: `{manifest["feature_batch_smoke_audit_passed"]}`
mask_interface_smoke_audit_row_count: `{manifest["mask_interface_smoke_audit_row_count"]}`
mask_interface_smoke_audit_passed: `{manifest["mask_interface_smoke_audit_passed"]}`
checkpoint_compatibility_smoke_audit_row_count: `{manifest["checkpoint_compatibility_smoke_audit_row_count"]}`
checkpoint_compatibility_smoke_audit_passed: `{manifest["checkpoint_compatibility_smoke_audit_passed"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
original_dataloader_modified: `{manifest["original_dataloader_modified"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
ready_for_covapie_dataloader_interface_qa_gate: `{manifest["ready_for_covapie_dataloader_interface_qa_gate"]}`
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
    result = smoke.run_covapie_dataloader_interface_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["preview_rows"], smoke.INTERFACE_SMOKE_PREVIEW_CSV, smoke.INTERFACE_SMOKE_PREVIEW_COLUMNS)
    write_json(result["json_rows"], smoke.INTERFACE_SMOKE_PREVIEW_JSON)
    write_csv(result["input_rows"], smoke.INPUT_SOURCE_SMOKE_AUDIT_CSV, smoke.INPUT_SOURCE_SMOKE_COLUMNS)
    write_csv(result["field_rows"], smoke.FIELD_MAPPING_SMOKE_AUDIT_CSV, smoke.FIELD_MAPPING_SMOKE_COLUMNS)
    write_csv(result["feature_batch_rows"], smoke.FEATURE_BATCH_SMOKE_AUDIT_CSV, smoke.FEATURE_BATCH_SMOKE_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_INTERFACE_SMOKE_AUDIT_CSV, smoke.MASK_INTERFACE_SMOKE_COLUMNS)
    write_csv(result["checkpoint_rows"], smoke.CHECKPOINT_COMPATIBILITY_SMOKE_AUDIT_CSV, smoke.CHECKPOINT_COMPATIBILITY_SMOKE_COLUMNS)
    write_csv(result["boundary_rows"], smoke.BOUNDARY_SAFETY_CSV, smoke.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_dataloader_interface_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_dataloader_interface_smoke_v0_blocked")
    for key in [
        "dataloader_interface_smoke_preview_row_count",
        "dataloader_interface_smoke_preview_column_count",
        "input_source_smoke_audit_row_count",
        "input_source_smoke_audit_passed",
        "field_mapping_smoke_audit_row_count",
        "field_mapping_smoke_audit_passed",
        "feature_batch_smoke_audit_row_count",
        "feature_batch_smoke_audit_passed",
        "mask_interface_smoke_audit_row_count",
        "mask_interface_smoke_audit_passed",
        "checkpoint_compatibility_smoke_audit_row_count",
        "checkpoint_compatibility_smoke_audit_passed",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_dataloader_interface_qa_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

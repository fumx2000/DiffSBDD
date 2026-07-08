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

from covalent_ext import covapie_metadata_dataloader_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Metadata Dataloader Smoke v0 Summary

Step 13BU implements a minimal metadata-only Dataset-like shim under `src/covalent_ext`.
The shim reads the Step 13BR dataloader interface smoke preview and supports `__len__` plus `__getitem__`.
It returns Python dict metadata records only.
It does not inherit from torch Dataset, use torch DataLoader, import torch, create tensors, return numpy arrays, load checkpoints, call model forward, compute loss, train, or modify original DiffSBDD dataloader/model/loss code.
It does not read raw structures, parse mmCIF, download data, use RDKit/Bio.PDB/gemmi/gzip, write actual dataloader smoke, write real final dataset artifacts, write a new sample index, write split assignments, or write a leakage matrix.
It preserves the five canonical masks, including `scaffold_only / B3`.
The next step is metadata dataloader smoke QA gate, not actual dataloader smoke and not training.

metadata_dataset_len: `{manifest["metadata_dataset_len"]}`
metadata_dataloader_smoke_preview_row_count: `{manifest["metadata_dataloader_smoke_preview_row_count"]}`
metadata_dataloader_smoke_preview_column_count: `{manifest["metadata_dataloader_smoke_preview_column_count"]}`
len_getitem_audit_row_count: `{manifest["len_getitem_audit_row_count"]}`
len_getitem_audit_passed: `{manifest["len_getitem_audit_passed"]}`
out_of_range_index_error_checked: `{manifest["out_of_range_index_error_checked"]}`
key_coverage_audit_row_count: `{manifest["key_coverage_audit_row_count"]}`
key_coverage_audit_passed: `{manifest["key_coverage_audit_passed"]}`
mask_distribution_audit_row_count: `{manifest["mask_distribution_audit_row_count"]}`
mask_distribution_audit_passed: `{manifest["mask_distribution_audit_passed"]}`
blocker_runtime_audit_row_count: `{manifest["blocker_runtime_audit_row_count"]}`
blocker_runtime_audit_passed: `{manifest["blocker_runtime_audit_passed"]}`
metadata_dataloader_smoke_written: `{manifest["metadata_dataloader_smoke_written"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
original_dataloader_modified: `{manifest["original_dataloader_modified"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
ready_for_covapie_metadata_dataloader_smoke_qa_gate: `{manifest["ready_for_covapie_metadata_dataloader_smoke_qa_gate"]}`
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
    result = smoke.run_covapie_metadata_dataloader_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["preview_rows"], smoke.SMOKE_PREVIEW_CSV, smoke.PREVIEW_COLUMNS)
    write_json(result["json_rows"], smoke.SMOKE_PREVIEW_JSON)
    write_csv(result["len_getitem_rows"], smoke.LEN_GETITEM_AUDIT_CSV, smoke.LEN_GETITEM_COLUMNS)
    write_csv(result["key_rows"], smoke.KEY_COVERAGE_AUDIT_CSV, smoke.KEY_COVERAGE_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_DISTRIBUTION_AUDIT_CSV, smoke.MASK_DISTRIBUTION_COLUMNS)
    write_csv(result["blocker_rows"], smoke.BLOCKER_RUNTIME_AUDIT_CSV, smoke.BLOCKER_RUNTIME_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_metadata_dataloader_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_metadata_dataloader_smoke_v0_blocked")
    for key in [
        "metadata_dataset_len",
        "metadata_dataloader_smoke_preview_row_count",
        "metadata_dataloader_smoke_preview_column_count",
        "len_getitem_audit_row_count",
        "len_getitem_audit_passed",
        "out_of_range_index_error_checked",
        "key_coverage_audit_row_count",
        "key_coverage_audit_passed",
        "mask_distribution_audit_row_count",
        "mask_distribution_audit_passed",
        "blocker_runtime_audit_row_count",
        "blocker_runtime_audit_passed",
        "metadata_dataloader_smoke_written",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_metadata_dataloader_smoke_qa_gate",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

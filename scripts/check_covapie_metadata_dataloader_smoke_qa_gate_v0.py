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

from covalent_ext import covapie_metadata_dataloader_smoke_qa_gate as qa  # noqa: E402


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
    text = f"""# CovaPIE Metadata Dataloader Smoke QA Gate v0 Summary

Step 13BV validates the Step 13BU metadata-only Dataset-like shim and smoke artifacts.
It reads but does not rewrite `covapie_metadata_dataloader_smoke_preview.csv` or `.json`.
It instantiates the pure Python metadata shim only; it does not use torch Dataset, torch DataLoader, tensors, numpy arrays, checkpoints, model forward, loss, or training.
It does not write actual dataloader smoke, real dataloader artifacts, final dataset artifacts, a new sample index, split assignments, or a leakage matrix.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or original DiffSBDD model/dataloader/loss code.
The next step is actual dataloader design gate, not actual dataloader smoke and not training.

metadata_dataset_len_rechecked: `{manifest["metadata_dataset_len_rechecked"]}`
shim_api_qa_row_count: `{manifest["shim_api_qa_row_count"]}`
shim_api_qa_passed: `{manifest["shim_api_qa_passed"]}`
preview_integrity_qa_row_count: `{manifest["preview_integrity_qa_row_count"]}`
preview_integrity_qa_passed: `{manifest["preview_integrity_qa_passed"]}`
getitem_contract_qa_row_count: `{manifest["getitem_contract_qa_row_count"]}`
getitem_contract_qa_passed: `{manifest["getitem_contract_qa_passed"]}`
mask_distribution_qa_row_count: `{manifest["mask_distribution_qa_row_count"]}`
mask_distribution_qa_passed: `{manifest["mask_distribution_qa_passed"]}`
blocker_runtime_qa_row_count: `{manifest["blocker_runtime_qa_row_count"]}`
blocker_runtime_qa_passed: `{manifest["blocker_runtime_qa_passed"]}`
readiness_qa_row_count: `{manifest["readiness_qa_row_count"]}`
readiness_qa_passed: `{manifest["readiness_qa_passed"]}`
metadata_dataloader_smoke_preview_written_current_step: `{manifest["metadata_dataloader_smoke_preview_written_current_step"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
real_dataloader_written: `{manifest["real_dataloader_written"]}`
torch_imported: `{manifest["torch_imported"]}`
numpy_imported: `{manifest["numpy_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
checkpoint_loaded: `{manifest["checkpoint_loaded"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
ready_for_covapie_actual_dataloader_design_gate: `{manifest["ready_for_covapie_actual_dataloader_design_gate"]}`
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
    result = qa.run_covapie_metadata_dataloader_smoke_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["shim_rows"], qa.SHIM_API_QA_CSV, qa.SHIM_API_QA_COLUMNS)
    write_csv(result["preview_rows"], qa.PREVIEW_INTEGRITY_QA_CSV, qa.PREVIEW_INTEGRITY_QA_COLUMNS)
    write_csv(result["getitem_rows"], qa.GETITEM_CONTRACT_QA_CSV, qa.GETITEM_CONTRACT_QA_COLUMNS)
    write_csv(result["mask_rows"], qa.MASK_DISTRIBUTION_QA_CSV, qa.MASK_DISTRIBUTION_QA_COLUMNS)
    write_csv(result["blocker_rows"], qa.BLOCKER_RUNTIME_QA_CSV, qa.BLOCKER_RUNTIME_QA_COLUMNS)
    write_csv(result["readiness_rows"], qa.READINESS_QA_CSV, qa.READINESS_QA_COLUMNS)
    write_csv(result["safety_rows"], qa.SAFETY_AUDIT_CSV, qa.SAFETY_COLUMNS)
    write_csv(result["git_safety_rows"], qa.GIT_SAFETY_CSV, qa.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_metadata_dataloader_smoke_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_metadata_dataloader_smoke_qa_gate_v0_blocked")
    for key in [
        "metadata_dataset_len_rechecked",
        "shim_api_qa_row_count",
        "shim_api_qa_passed",
        "preview_integrity_qa_row_count",
        "preview_integrity_qa_passed",
        "getitem_contract_qa_row_count",
        "getitem_contract_qa_passed",
        "mask_distribution_qa_row_count",
        "mask_distribution_qa_passed",
        "blocker_runtime_qa_row_count",
        "blocker_runtime_qa_passed",
        "readiness_qa_row_count",
        "readiness_qa_passed",
        "metadata_dataloader_smoke_preview_written_current_step",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "torch_imported",
        "numpy_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_actual_dataloader_design_gate",
        "ready_for_covapie_actual_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

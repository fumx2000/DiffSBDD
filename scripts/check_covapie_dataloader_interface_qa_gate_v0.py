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

from covalent_ext import covapie_dataloader_interface_qa_gate as qa  # noqa: E402


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
    text = f"""# CovaPIE Dataloader Interface QA Gate v0 Summary

Step 13BS is a QA gate for the Step 13BR metadata-only dataloader interface smoke preview.
It reads, but does not rewrite, `covapie_dataloader_interface_smoke_preview.csv` or `.json`.
It validates preview integrity, input source smoke, field mapping smoke, feature and batch interface smoke, mask interface smoke, checkpoint compatibility smoke, readiness, boundary safety, and git safety.
It does not write actual dataloader smoke, instantiate a dataloader, import torch, create tensors, load checkpoints, call model forward, compute loss, run backward, create optimizers, call trainer.fit, or train.
It does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, `equivariant_diffusion/`, or original DiffSBDD model/dataloader/loss code.
It does not write real final dataset artifacts, a new sample index, split assignments, or a leakage matrix.
It preserves the five canonical masks, including `scaffold_only / B3`, and does not introduce extra masks.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.
This QA gate allows dataloader smoke design gate next, not actual dataloader smoke and not training.

preview_integrity_qa_row_count: `{manifest["preview_integrity_qa_row_count"]}`
preview_integrity_qa_passed: `{manifest["preview_integrity_qa_passed"]}`
input_source_qa_row_count: `{manifest["input_source_qa_row_count"]}`
input_source_qa_passed: `{manifest["input_source_qa_passed"]}`
field_mapping_qa_row_count: `{manifest["field_mapping_qa_row_count"]}`
field_mapping_qa_passed: `{manifest["field_mapping_qa_passed"]}`
feature_batch_qa_row_count: `{manifest["feature_batch_qa_row_count"]}`
feature_batch_qa_passed: `{manifest["feature_batch_qa_passed"]}`
mask_interface_qa_row_count: `{manifest["mask_interface_qa_row_count"]}`
mask_interface_qa_passed: `{manifest["mask_interface_qa_passed"]}`
checkpoint_compatibility_qa_row_count: `{manifest["checkpoint_compatibility_qa_row_count"]}`
checkpoint_compatibility_qa_passed: `{manifest["checkpoint_compatibility_qa_passed"]}`
readiness_qa_row_count: `{manifest["readiness_qa_row_count"]}`
readiness_qa_passed: `{manifest["readiness_qa_passed"]}`
dataloader_interface_smoke_preview_written_current_step: `{manifest["dataloader_interface_smoke_preview_written_current_step"]}`
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
ready_for_covapie_dataloader_smoke_design_gate: `{manifest["ready_for_covapie_dataloader_smoke_design_gate"]}`
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
    result = qa.run_covapie_dataloader_interface_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["preview_rows"], qa.PREVIEW_INTEGRITY_QA_CSV, qa.PREVIEW_INTEGRITY_COLUMNS)
    write_csv(result["input_rows"], qa.INPUT_SOURCE_QA_CSV, qa.INPUT_SOURCE_QA_COLUMNS)
    write_csv(result["field_rows"], qa.FIELD_MAPPING_QA_CSV, qa.FIELD_MAPPING_QA_COLUMNS)
    write_csv(result["feature_batch_rows"], qa.FEATURE_BATCH_QA_CSV, qa.FEATURE_BATCH_QA_COLUMNS)
    write_csv(result["mask_rows"], qa.MASK_QA_CSV, qa.MASK_QA_COLUMNS)
    write_csv(result["checkpoint_rows"], qa.CHECKPOINT_COMPATIBILITY_QA_CSV, qa.CHECKPOINT_COMPATIBILITY_QA_COLUMNS)
    write_csv(result["readiness_rows"], qa.READINESS_QA_CSV, qa.READINESS_QA_COLUMNS)
    write_csv(result["boundary_rows"], qa.BOUNDARY_SAFETY_CSV, qa.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa.GIT_SAFETY_CSV, qa.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_dataloader_interface_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_dataloader_interface_qa_gate_v0_blocked")
    for key in [
        "preview_integrity_qa_row_count",
        "preview_integrity_qa_passed",
        "input_source_qa_row_count",
        "input_source_qa_passed",
        "field_mapping_qa_row_count",
        "field_mapping_qa_passed",
        "feature_batch_qa_row_count",
        "feature_batch_qa_passed",
        "mask_interface_qa_row_count",
        "mask_interface_qa_passed",
        "checkpoint_compatibility_qa_row_count",
        "checkpoint_compatibility_qa_passed",
        "readiness_qa_row_count",
        "readiness_qa_passed",
        "dataloader_interface_smoke_preview_written_current_step",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "original_dataloader_modified",
        "torch_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_dataloader_smoke_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_feature_semantics_tensorization_audit_gate as audit  # noqa: E402


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
    text = f"""# CovaPIE Feature Semantics Tensorization Audit Gate v0 Summary

Step 13BX audits feature semantics and tensorization blockers before any actual CovaPIE tensor dataloader work.
It does not implement actual dataloader smoke, torch Dataset, torch DataLoader, tensor creation, numpy arrays, checkpoint loading, model forward, loss, or training.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
Coordinates are recorded only as future tensorization candidates; atom features, unknown atom policy, mask boolean tensors, auxiliary labels, loss targets, and training remain blocked.
It reads original DiffSBDD source files only as static references and does not modify `dataset.py`, `data/prepare_crossdocked.py`, `lightning_modules.py`, or `equivariant_diffusion/`.
The five canonical masks are preserved, including `scaffold_only / B3`.
The next step is `covapie_feature_semantics_resolution_design_gate`, not actual dataloader smoke and not training.

original_feature_source_static_audit_row_count: `{manifest["original_feature_source_static_audit_row_count"]}`
original_feature_source_static_audit_passed: `{manifest["original_feature_source_static_audit_passed"]}`
coordinate_tensorization_semantics_audit_row_count: `{manifest["coordinate_tensorization_semantics_audit_row_count"]}`
coordinate_tensorization_semantics_audit_passed: `{manifest["coordinate_tensorization_semantics_audit_passed"]}`
atom_feature_semantics_audit_row_count: `{manifest["atom_feature_semantics_audit_row_count"]}`
atom_feature_semantics_audit_passed: `{manifest["atom_feature_semantics_audit_passed"]}`
unknown_atom_policy_audit_row_count: `{manifest["unknown_atom_policy_audit_row_count"]}`
unknown_atom_policy_audit_passed: `{manifest["unknown_atom_policy_audit_passed"]}`
label_tensorization_blocker_audit_row_count: `{manifest["label_tensorization_blocker_audit_row_count"]}`
label_tensorization_blocker_audit_passed: `{manifest["label_tensorization_blocker_audit_passed"]}`
tensorization_readiness_decision_contract_row_count: `{manifest["tensorization_readiness_decision_contract_row_count"]}`
tensorization_readiness_decision_contract_passed: `{manifest["tensorization_readiness_decision_contract_passed"]}`
feature_semantics_resolution_plan_row_count: `{manifest["feature_semantics_resolution_plan_row_count"]}`
feature_semantics_resolution_plan_passed: `{manifest["feature_semantics_resolution_plan_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
coordinate_tensor_candidate_for_future_design: `{manifest["coordinate_tensor_candidate_for_future_design"]}`
atom_feature_tensorization_ready: `{manifest["atom_feature_tensorization_ready"]}`
mask_boolean_tensorization_ready: `{manifest["mask_boolean_tensorization_ready"]}`
auxiliary_label_tensorization_ready: `{manifest["auxiliary_label_tensorization_ready"]}`
actual_dataloader_adapter_smoke_written: `{manifest["actual_dataloader_adapter_smoke_written"]}`
actual_dataloader_smoke_written: `{manifest["actual_dataloader_smoke_written"]}`
torch_imported: `{manifest["torch_imported"]}`
numpy_imported: `{manifest["numpy_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
model_forward_called: `{manifest["model_forward_called"]}`
training_allowed: `{manifest["training_allowed"]}`
ready_for_covapie_feature_semantics_resolution_design_gate: `{manifest["ready_for_covapie_feature_semantics_resolution_design_gate"]}`
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
    result = audit.run_covapie_feature_semantics_tensorization_audit_gate_v0()
    write_csv(result["precondition_rows"], audit.PRECONDITION_AUDIT_CSV, audit.PRECONDITION_COLUMNS)
    write_csv(result["static_rows"], audit.STATIC_SOURCE_AUDIT_CSV, audit.STATIC_SOURCE_COLUMNS)
    write_csv(result["coordinate_rows"], audit.COORDINATE_TENSORIZATION_AUDIT_CSV, audit.COORDINATE_COLUMNS)
    write_csv(result["atom_rows"], audit.ATOM_FEATURE_AUDIT_CSV, audit.ATOM_FEATURE_COLUMNS)
    write_csv(result["unknown_rows"], audit.UNKNOWN_ATOM_POLICY_AUDIT_CSV, audit.UNKNOWN_POLICY_COLUMNS)
    write_csv(result["label_rows"], audit.LABEL_TENSORIZATION_BLOCKER_AUDIT_CSV, audit.LABEL_BLOCKER_COLUMNS)
    write_csv(result["readiness_rows"], audit.READINESS_DECISION_CONTRACT_CSV, audit.READINESS_COLUMNS)
    write_csv(result["resolution_rows"], audit.RESOLUTION_PLAN_CSV, audit.RESOLUTION_PLAN_COLUMNS)
    write_csv(result["safety_rows"], audit.SAFETY_AUDIT_CSV, audit.SAFETY_COLUMNS)
    write_json(result["manifest"], audit.MANIFEST_JSON)
    write_summary(result["manifest"], audit.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_feature_semantics_tensorization_audit_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_feature_semantics_tensorization_audit_gate_v0_blocked")
    for key in [
        "original_feature_source_static_audit_row_count",
        "original_feature_source_static_audit_passed",
        "coordinate_tensorization_semantics_audit_row_count",
        "coordinate_tensorization_semantics_audit_passed",
        "atom_feature_semantics_audit_row_count",
        "atom_feature_semantics_audit_passed",
        "unknown_atom_policy_audit_row_count",
        "unknown_atom_policy_audit_passed",
        "label_tensorization_blocker_audit_row_count",
        "label_tensorization_blocker_audit_passed",
        "tensorization_readiness_decision_contract_row_count",
        "tensorization_readiness_decision_contract_passed",
        "feature_semantics_resolution_plan_row_count",
        "feature_semantics_resolution_plan_passed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "coordinate_tensor_candidate_for_future_design",
        "atom_feature_tensorization_ready",
        "mask_boolean_tensorization_ready",
        "auxiliary_label_tensorization_ready",
        "actual_dataloader_adapter_smoke_written",
        "actual_dataloader_smoke_written",
        "real_dataloader_written",
        "torch_imported",
        "numpy_imported",
        "torch_tensor_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "training_allowed",
        "ready_for_covapie_feature_semantics_resolution_design_gate",
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

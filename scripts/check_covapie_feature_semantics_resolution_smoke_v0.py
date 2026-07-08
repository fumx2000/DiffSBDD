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

from covalent_ext import covapie_feature_semantics_resolution_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Feature Semantics Resolution Smoke v0 Summary

Step 13BZ reads the Step 13BY resolution design contracts and validates them against existing derived metadata previews and derived atom table CSVs.
It is a CSV/JSON-level feature semantics resolution smoke only.
It does not create tensors, import torch or numpy, instantiate a Dataset/DataLoader, load checkpoints, run model forward, compute loss, train, parse raw mmCIF, or extract coordinates from raw files.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
It preserves the five canonical mask tasks, including `scaffold_only / B3`.
Step 12D, Step 13BM, Step 13BX, Step 13BY, and Step 13BZ do not replace the final training feature semantics audit.
The next step is `covapie_feature_semantics_resolution_smoke_qa_gate`, not actual dataloader smoke and not training.

original_feature_schema_mapping_smoke_audit_row_count: `{manifest["original_feature_schema_mapping_smoke_audit_row_count"]}`
original_feature_schema_mapping_smoke_audit_passed: `{manifest["original_feature_schema_mapping_smoke_audit_passed"]}`
coordinate_policy_resolution_smoke_audit_row_count: `{manifest["coordinate_policy_resolution_smoke_audit_row_count"]}`
coordinate_policy_resolution_smoke_audit_passed: `{manifest["coordinate_policy_resolution_smoke_audit_passed"]}`
atom_feature_policy_resolution_smoke_audit_row_count: `{manifest["atom_feature_policy_resolution_smoke_audit_row_count"]}`
atom_feature_policy_resolution_smoke_audit_passed: `{manifest["atom_feature_policy_resolution_smoke_audit_passed"]}`
unknown_atom_policy_resolution_smoke_audit_row_count: `{manifest["unknown_atom_policy_resolution_smoke_audit_row_count"]}`
unknown_atom_policy_resolution_smoke_audit_passed: `{manifest["unknown_atom_policy_resolution_smoke_audit_passed"]}`
label_policy_resolution_smoke_audit_row_count: `{manifest["label_policy_resolution_smoke_audit_row_count"]}`
label_policy_resolution_smoke_audit_passed: `{manifest["label_policy_resolution_smoke_audit_passed"]}`
tensor_shape_dtype_policy_smoke_audit_row_count: `{manifest["tensor_shape_dtype_policy_smoke_audit_row_count"]}`
tensor_shape_dtype_policy_smoke_audit_passed: `{manifest["tensor_shape_dtype_policy_smoke_audit_passed"]}`
feature_semantics_resolution_readiness_audit_row_count: `{manifest["feature_semantics_resolution_readiness_audit_row_count"]}`
feature_semantics_resolution_readiness_audit_passed: `{manifest["feature_semantics_resolution_readiness_audit_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
proposed_feature_schema_resolution_validated_by_smoke: `{manifest["proposed_feature_schema_resolution_validated_by_smoke"]}`
proposed_unknown_atom_policy_validated_by_smoke: `{manifest["proposed_unknown_atom_policy_validated_by_smoke"]}`
proposed_label_semantics_validated_by_smoke: `{manifest["proposed_label_semantics_validated_by_smoke"]}`
derived_atom_tables_read_only: `{manifest["derived_atom_tables_read_only"]}`
ready_for_covapie_feature_semantics_resolution_smoke_qa_gate: `{manifest["ready_for_covapie_feature_semantics_resolution_smoke_qa_gate"]}`
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
    result = smoke.run_covapie_feature_semantics_resolution_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["mapping_rows"], smoke.ORIGINAL_MAPPING_SMOKE_AUDIT_CSV, smoke.ORIGINAL_MAPPING_SMOKE_COLUMNS)
    write_csv(result["coordinate_rows"], smoke.COORDINATE_POLICY_SMOKE_AUDIT_CSV, smoke.COORDINATE_POLICY_SMOKE_COLUMNS)
    write_csv(result["atom_rows"], smoke.ATOM_FEATURE_POLICY_SMOKE_AUDIT_CSV, smoke.ATOM_FEATURE_POLICY_SMOKE_COLUMNS)
    write_csv(result["unknown_rows"], smoke.UNKNOWN_POLICY_SMOKE_AUDIT_CSV, smoke.UNKNOWN_POLICY_SMOKE_COLUMNS)
    write_csv(result["label_rows"], smoke.LABEL_POLICY_SMOKE_AUDIT_CSV, smoke.LABEL_POLICY_SMOKE_COLUMNS)
    write_csv(result["tensor_rows"], smoke.TENSOR_POLICY_SMOKE_AUDIT_CSV, smoke.TENSOR_POLICY_SMOKE_COLUMNS)
    write_csv(result["readiness_rows"], smoke.READINESS_AUDIT_CSV, smoke.READINESS_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_feature_semantics_resolution_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_feature_semantics_resolution_smoke_v0_blocked")
    for key in [
        "original_feature_schema_mapping_smoke_audit_row_count",
        "original_feature_schema_mapping_smoke_audit_passed",
        "coordinate_policy_resolution_smoke_audit_row_count",
        "coordinate_policy_resolution_smoke_audit_passed",
        "atom_feature_policy_resolution_smoke_audit_row_count",
        "atom_feature_policy_resolution_smoke_audit_passed",
        "unknown_atom_policy_resolution_smoke_audit_row_count",
        "unknown_atom_policy_resolution_smoke_audit_passed",
        "label_policy_resolution_smoke_audit_row_count",
        "label_policy_resolution_smoke_audit_passed",
        "tensor_shape_dtype_policy_smoke_audit_row_count",
        "tensor_shape_dtype_policy_smoke_audit_passed",
        "feature_semantics_resolution_readiness_audit_row_count",
        "feature_semantics_resolution_readiness_audit_passed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "proposed_feature_schema_resolution_validated_by_smoke",
        "proposed_unknown_atom_policy_validated_by_smoke",
        "proposed_label_semantics_validated_by_smoke",
        "derived_atom_tables_read_only",
        "ready_for_covapie_feature_semantics_resolution_smoke_qa_gate",
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

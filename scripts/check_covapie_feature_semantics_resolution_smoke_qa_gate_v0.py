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

from covalent_ext import covapie_feature_semantics_resolution_smoke_qa_gate as qa  # noqa: E402


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
    text = f"""# CovaPIE Feature Semantics Resolution Smoke QA Gate v0 Summary

Step 14A is a QA gate for the Step 13BZ feature semantics resolution smoke.
It validates the CSV/JSON-level smoke artifacts, row counts, pass flags, read-only derived atom table use, and safety/readiness boundaries.
It does not create tensors, import torch or numpy, write actual dataloader smoke, write final datasets, write sample indexes, write split assignments, write leakage matrices, load checkpoints, run model forward, compute loss, or train.
It keeps `feature_semantics_known_for_training=false` and `unknown_atom_feature_policy_finalized_for_training=false`.
The five canonical mask tasks are preserved, including `scaffold_only / B3`.
Step 12D, Step 13BM, Step 13BX, Step 13BY, Step 13BZ, and Step 14A do not replace the final training feature semantics audit.
The next step is `covapie_bulk_download_design_gate`, not actual dataloader smoke and not training.

feature_schema_mapping_smoke_qa_row_count: `{manifest["feature_schema_mapping_smoke_qa_row_count"]}`
feature_schema_mapping_smoke_qa_passed: `{manifest["feature_schema_mapping_smoke_qa_passed"]}`
coordinate_policy_smoke_qa_row_count: `{manifest["coordinate_policy_smoke_qa_row_count"]}`
coordinate_policy_smoke_qa_passed: `{manifest["coordinate_policy_smoke_qa_passed"]}`
atom_feature_policy_smoke_qa_row_count: `{manifest["atom_feature_policy_smoke_qa_row_count"]}`
atom_feature_policy_smoke_qa_passed: `{manifest["atom_feature_policy_smoke_qa_passed"]}`
unknown_atom_policy_smoke_qa_row_count: `{manifest["unknown_atom_policy_smoke_qa_row_count"]}`
unknown_atom_policy_smoke_qa_passed: `{manifest["unknown_atom_policy_smoke_qa_passed"]}`
label_policy_smoke_qa_row_count: `{manifest["label_policy_smoke_qa_row_count"]}`
label_policy_smoke_qa_passed: `{manifest["label_policy_smoke_qa_passed"]}`
tensor_shape_dtype_policy_smoke_qa_row_count: `{manifest["tensor_shape_dtype_policy_smoke_qa_row_count"]}`
tensor_shape_dtype_policy_smoke_qa_passed: `{manifest["tensor_shape_dtype_policy_smoke_qa_passed"]}`
readiness_smoke_qa_row_count: `{manifest["readiness_smoke_qa_row_count"]}`
readiness_smoke_qa_passed: `{manifest["readiness_smoke_qa_passed"]}`
safety_audit_passed: `{manifest["safety_audit_passed"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
derived_atom_tables_read_only: `{manifest["derived_atom_tables_read_only"]}`
ready_for_covapie_bulk_download_design_gate: `{manifest["ready_for_covapie_bulk_download_design_gate"]}`
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
    result = qa.run_covapie_feature_semantics_resolution_smoke_qa_gate_v0()
    write_csv(result["precondition_rows"], qa.PRECONDITION_AUDIT_CSV, qa.PRECONDITION_COLUMNS)
    write_csv(result["feature_schema_rows"], qa.FEATURE_SCHEMA_QA_CSV, qa.FEATURE_SCHEMA_QA_COLUMNS)
    write_csv(result["coordinate_rows"], qa.COORDINATE_QA_CSV, qa.COORDINATE_QA_COLUMNS)
    write_csv(result["atom_rows"], qa.ATOM_FEATURE_QA_CSV, qa.ATOM_FEATURE_QA_COLUMNS)
    write_csv(result["unknown_rows"], qa.UNKNOWN_POLICY_QA_CSV, qa.UNKNOWN_POLICY_QA_COLUMNS)
    write_csv(result["label_rows"], qa.LABEL_POLICY_QA_CSV, qa.LABEL_POLICY_QA_COLUMNS)
    write_csv(result["tensor_rows"], qa.TENSOR_POLICY_QA_CSV, qa.TENSOR_POLICY_QA_COLUMNS)
    write_csv(result["readiness_rows"], qa.READINESS_QA_CSV, qa.READINESS_QA_COLUMNS)
    write_csv(result["safety_rows"], qa.SAFETY_AUDIT_CSV, qa.SAFETY_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_feature_semantics_resolution_smoke_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_feature_semantics_resolution_smoke_qa_gate_v0_blocked")
    for key in [
        "feature_schema_mapping_smoke_qa_row_count",
        "feature_schema_mapping_smoke_qa_passed",
        "coordinate_policy_smoke_qa_row_count",
        "coordinate_policy_smoke_qa_passed",
        "atom_feature_policy_smoke_qa_row_count",
        "atom_feature_policy_smoke_qa_passed",
        "unknown_atom_policy_smoke_qa_row_count",
        "unknown_atom_policy_smoke_qa_passed",
        "label_policy_smoke_qa_row_count",
        "label_policy_smoke_qa_passed",
        "tensor_shape_dtype_policy_smoke_qa_row_count",
        "tensor_shape_dtype_policy_smoke_qa_passed",
        "readiness_smoke_qa_row_count",
        "readiness_smoke_qa_passed",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "proposed_feature_schema_resolution_validated_by_smoke",
        "proposed_unknown_atom_policy_validated_by_smoke",
        "proposed_label_semantics_validated_by_smoke",
        "derived_atom_tables_read_only",
        "ready_for_covapie_bulk_download_design_gate",
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

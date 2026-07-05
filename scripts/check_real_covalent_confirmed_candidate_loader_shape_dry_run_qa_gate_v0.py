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

from covalent_ext import real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate as qa  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        rows.append(
            {
                "stage": qa.STAGE,
                "previous_stage": qa.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "loader shape dry run QA gate passed"
                if manifest["all_checks_passed"]
                else "loader shape dry run QA gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Loader Shape Dry Run QA Gate v0 Summary

Step 13AA is a loader shape dry run QA gate only.
It reads but does not modify Step 13Z execution smoke artifacts.
It does not instantiate a loader, import torch, create tensors, persist tensors, create PT/NPZ, or train.
It verifies Step 13Z transient shape observations, batch audit, execution boundary, and feature semantics audit.
It preserves the five canonical mask tasks, including scaffold_only/B3.
It keeps feature semantics audit required before formal training.
It allows a DiffSBDD loader adapter design gate next, not implementation and not training.

loader_shape_dry_run_sample_qa_audit_row_count: `{manifest["loader_shape_dry_run_sample_qa_audit_row_count"]}`
loader_shape_dry_run_shape_observation_qa_audit_row_count: `{manifest["loader_shape_dry_run_shape_observation_qa_audit_row_count"]}`
loader_shape_dry_run_batch_qa_audit_row_count: `{manifest["loader_shape_dry_run_batch_qa_audit_row_count"]}`
loader_shape_dry_run_execution_boundary_qa_audit_row_count: `{manifest["loader_shape_dry_run_execution_boundary_qa_audit_row_count"]}`
loader_shape_dry_run_feature_semantics_qa_audit_row_count: `{manifest["loader_shape_dry_run_feature_semantics_qa_audit_row_count"]}`
loader_shape_dry_run_dependency_qa_audit_row_count: `{manifest["loader_shape_dry_run_dependency_qa_audit_row_count"]}`
loader_shape_dry_run_qa_gate_passed: `{manifest["loader_shape_dry_run_qa_gate_passed"]}`
smoke_dataset_instantiated_in_step13z: `{manifest["smoke_dataset_instantiated_in_step13z"]}`
loader_instantiated_in_step13z: `{manifest["loader_instantiated_in_step13z"]}`
torch_tensor_created_in_step13z: `{manifest["torch_tensor_created_in_step13z"]}`
smoke_dataset_instantiated: `{manifest["smoke_dataset_instantiated"]}`
loader_instantiated: `{manifest["loader_instantiated"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
ready_for_diffsbdd_loader_adapter_design_gate: `{manifest["ready_for_diffsbdd_loader_adapter_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa.run_loader_shape_dry_run_qa_gate_v0()
    write_csv(result["sample_qa_rows"], qa.SAMPLE_QA_AUDIT_CSV, qa.SAMPLE_QA_COLUMNS)
    write_csv(result["shape_observation_qa_rows"], qa.SHAPE_OBSERVATION_QA_AUDIT_CSV, qa.SHAPE_OBSERVATION_QA_COLUMNS)
    write_csv(result["batch_qa_rows"], qa.BATCH_QA_AUDIT_CSV, qa.BATCH_QA_COLUMNS)
    write_csv(result["execution_boundary_qa_rows"], qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV, qa.EXECUTION_BOUNDARY_QA_COLUMNS)
    write_csv(result["feature_semantics_qa_rows"], qa.FEATURE_SEMANTICS_QA_AUDIT_CSV, qa.FEATURE_SEMANTICS_QA_COLUMNS)
    write_csv(result["dependency_qa_rows"], qa.DEPENDENCY_QA_AUDIT_CSV, qa.DEPENDENCY_QA_COLUMNS)
    write_csv(build_report_rows(result), qa.REPORT_CSV, qa.REPORT_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0_blocked")
    print(f"loader_shape_dry_run_sample_qa_audit_row_count={manifest['loader_shape_dry_run_sample_qa_audit_row_count']}")
    print(
        "loader_shape_dry_run_shape_observation_qa_audit_row_count="
        f"{manifest['loader_shape_dry_run_shape_observation_qa_audit_row_count']}"
    )
    print(f"loader_shape_dry_run_batch_qa_audit_row_count={manifest['loader_shape_dry_run_batch_qa_audit_row_count']}")
    print(
        "loader_shape_dry_run_execution_boundary_qa_audit_row_count="
        f"{manifest['loader_shape_dry_run_execution_boundary_qa_audit_row_count']}"
    )
    print(
        "loader_shape_dry_run_feature_semantics_qa_audit_row_count="
        f"{manifest['loader_shape_dry_run_feature_semantics_qa_audit_row_count']}"
    )
    print(
        "loader_shape_dry_run_dependency_qa_audit_row_count="
        f"{manifest['loader_shape_dry_run_dependency_qa_audit_row_count']}"
    )
    print(f"loader_shape_dry_run_qa_gate_passed={manifest['loader_shape_dry_run_qa_gate_passed']}")
    print(f"smoke_dataset_instantiated_in_step13z={manifest['smoke_dataset_instantiated_in_step13z']}")
    print(f"loader_instantiated_in_step13z={manifest['loader_instantiated_in_step13z']}")
    print(f"torch_tensor_created_in_step13z={manifest['torch_tensor_created_in_step13z']}")
    print(f"smoke_dataset_instantiated={manifest['smoke_dataset_instantiated']}")
    print(f"loader_instantiated={manifest['loader_instantiated']}")
    print(f"torch_imported={manifest['torch_imported']}")
    print(f"torch_tensor_created={manifest['torch_tensor_created']}")
    print(f"ready_for_diffsbdd_loader_adapter_design_gate={manifest['ready_for_diffsbdd_loader_adapter_design_gate']}")
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

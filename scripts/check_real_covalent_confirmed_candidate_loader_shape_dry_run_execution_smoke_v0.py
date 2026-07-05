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

from covalent_ext import real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke as smoke  # noqa: E402


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
                "stage": smoke.STAGE,
                "previous_stage": smoke.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "loader shape dry run execution smoke passed"
                if manifest["all_checks_passed"]
                else "loader shape dry run execution smoke blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Loader Shape Dry Run Execution Smoke v0 Summary

Step 13Z is a loader shape dry run execution smoke.
It instantiates only a minimal read-only smoke dataset and loader for 3 CYS/SG golden samples.
It creates transient in-memory tensors only for shape inspection.
It does not persist tensors and does not create PT or NPZ artifacts.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.
It does not call model forward, loss, backward, optimizer, trainer fit, or training.
It preserves the five canonical mask tasks, including scaffold_only/B3.
It validates observed transient shapes against the Step 13Y shape expectation contract.
It keeps feature semantics audit required before formal training.
It allows loader shape dry run QA gate next, not training.

loader_shape_dry_run_sample_audit_row_count: `{manifest["loader_shape_dry_run_sample_audit_row_count"]}`
loader_shape_dry_run_shape_observation_row_count: `{manifest["loader_shape_dry_run_shape_observation_row_count"]}`
loader_shape_dry_run_batch_audit_row_count: `{manifest["loader_shape_dry_run_batch_audit_row_count"]}`
loader_shape_dry_run_execution_boundary_audit_row_count: `{manifest["loader_shape_dry_run_execution_boundary_audit_row_count"]}`
loader_shape_dry_run_feature_semantics_audit_row_count: `{manifest["loader_shape_dry_run_feature_semantics_audit_row_count"]}`
smoke_dataset_instantiated: `{manifest["smoke_dataset_instantiated"]}`
loader_instantiated: `{manifest["loader_instantiated"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
loader_shape_dry_run_execution_smoke_passed: `{manifest["loader_shape_dry_run_execution_smoke_passed"]}`
ready_for_loader_shape_dry_run_qa_gate: `{manifest["ready_for_loader_shape_dry_run_qa_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_loader_shape_dry_run_execution_smoke_v0()
    write_csv(result["sample_audit_rows"], smoke.SAMPLE_AUDIT_CSV, smoke.SAMPLE_AUDIT_COLUMNS)
    write_csv(result["shape_observation_rows"], smoke.SHAPE_OBSERVATION_CSV, smoke.SHAPE_OBSERVATION_COLUMNS)
    write_csv(result["batch_audit_rows"], smoke.BATCH_AUDIT_CSV, smoke.BATCH_AUDIT_COLUMNS)
    write_csv(
        result["execution_boundary_audit_rows"],
        smoke.EXECUTION_BOUNDARY_AUDIT_CSV,
        smoke.EXECUTION_BOUNDARY_AUDIT_COLUMNS,
    )
    write_csv(
        result["feature_semantics_audit_rows"],
        smoke.FEATURE_SEMANTICS_AUDIT_CSV,
        smoke.FEATURE_SEMANTICS_AUDIT_COLUMNS,
    )
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0_blocked")
    print(f"loader_shape_dry_run_sample_audit_row_count={manifest['loader_shape_dry_run_sample_audit_row_count']}")
    print(f"loader_shape_dry_run_shape_observation_row_count={manifest['loader_shape_dry_run_shape_observation_row_count']}")
    print(f"loader_shape_dry_run_batch_audit_row_count={manifest['loader_shape_dry_run_batch_audit_row_count']}")
    print(f"loader_shape_dry_run_execution_boundary_audit_row_count={manifest['loader_shape_dry_run_execution_boundary_audit_row_count']}")
    print(f"loader_shape_dry_run_feature_semantics_audit_row_count={manifest['loader_shape_dry_run_feature_semantics_audit_row_count']}")
    print(f"loader_batch_count={manifest['loader_batch_count']}")
    print(f"loader_batch_size={manifest['loader_batch_size']}")
    print(f"smoke_dataset_instantiated={manifest['smoke_dataset_instantiated']}")
    print(f"loader_instantiated={manifest['loader_instantiated']}")
    print(f"torch_tensor_created={manifest['torch_tensor_created']}")
    print(f"loader_shape_dry_run_execution_smoke_passed={manifest['loader_shape_dry_run_execution_smoke_passed']}")
    print(f"ready_for_loader_shape_dry_run_qa_gate={manifest['ready_for_loader_shape_dry_run_qa_gate']}")
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

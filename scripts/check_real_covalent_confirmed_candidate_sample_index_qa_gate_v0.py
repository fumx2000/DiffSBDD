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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_qa_gate as qa  # noqa: E402


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
                "decision": "sample_index QA gate passed"
                if manifest["all_checks_passed"]
                else "sample_index QA gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Sample Index QA Gate v0 Summary

Step 13U is a sample_index QA gate only.
It reads but does not rewrite the Step 13T sample_index smoke artifact.
It validates identity, lineage, CYS/SG scope, topology counts, topology table paths, five canonical mask tasks, B3 scaffold_only, readiness fields, and dependency artifacts.

This step does not write enriched_sample_index, final_dataset, model input, split assignments, or leakage matrix.
It does not run forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.
It allows the model_input design gate next.
It does not allow model_input materialization and does not allow training.
Feature semantics audit remains required before formal training.

sample_index_smoke_row_count: `{manifest["sample_index_smoke_row_count"]}`
sample_index_row_qa_audit_row_count: `{manifest["sample_index_row_qa_audit_row_count"]}`
sample_index_dependency_qa_audit_row_count: `{manifest["sample_index_dependency_qa_audit_row_count"]}`
sample_index_schema_qa_audit_row_count: `{manifest["sample_index_schema_qa_audit_row_count"]}`
sample_index_qa_passed: `{manifest["sample_index_qa_passed"]}`
sample_index_written: `{manifest["sample_index_written"]}`
sample_index_modified: `{manifest["sample_index_modified"]}`
model_input_materialized: `{manifest["model_input_materialized"]}`
ready_for_model_input_design_gate: `{manifest["ready_for_model_input_design_gate"]}`
ready_for_model_input_materialization_smoke: `{manifest["ready_for_model_input_materialization_smoke"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa.build_real_covalent_confirmed_candidate_sample_index_qa_gate_v0()
    write_csv(result["row_qa_rows"], qa.ROW_QA_AUDIT_CSV, qa.ROW_QA_COLUMNS)
    write_csv(result["dependency_qa_rows"], qa.DEPENDENCY_QA_AUDIT_CSV, qa.DEPENDENCY_QA_COLUMNS)
    write_csv(result["schema_qa_rows"], qa.SCHEMA_QA_AUDIT_CSV, qa.SCHEMA_QA_COLUMNS)
    write_csv(build_report_rows(result), qa.REPORT_CSV, qa.REPORT_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_sample_index_qa_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_sample_index_qa_gate_v0_blocked")
    print(f"sample_index_row_qa_audit_row_count={manifest['sample_index_row_qa_audit_row_count']}")
    print(f"sample_index_dependency_qa_audit_row_count={manifest['sample_index_dependency_qa_audit_row_count']}")
    print(f"sample_index_schema_qa_audit_row_count={manifest['sample_index_schema_qa_audit_row_count']}")
    print(f"sample_index_qa_passed={manifest['sample_index_qa_passed']}")
    print(f"ready_for_model_input_design_gate={manifest['ready_for_model_input_design_gate']}")
    print(f"ready_for_model_input_materialization_smoke={manifest['ready_for_model_input_materialization_smoke']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import real_covalent_confirmed_candidate_model_input_materialization_smoke as smoke  # noqa: E402


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
                "decision": "model_input materialization smoke passed"
                if manifest["all_checks_passed"]
                else "model_input materialization smoke blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Model Input Materialization Smoke v0 Summary

Step 13W writes CSV/JSON-level model-input-like smoke artifacts.
It does not write real tensor or training model input.
It does not create PT or NPZ artifacts.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.
It preserves the five canonical mask tasks, including scaffold_only/B3.
It keeps feature semantics audit required before formal training.

This smoke allows the model_input QA gate next.
It does not allow loader shape dry run and does not allow training.

model_input_smoke_index_row_count: `{manifest["model_input_smoke_index_row_count"]}`
model_input_smoke_feature_status_row_count: `{manifest["model_input_smoke_feature_status_row_count"]}`
model_input_smoke_mask_status_row_count: `{manifest["model_input_smoke_mask_status_row_count"]}`
model_input_materialization_smoke_audit_row_count: `{manifest["model_input_materialization_smoke_audit_row_count"]}`
model_input_smoke_written: `{manifest["model_input_smoke_written"]}`
model_input_smoke_materialized: `{manifest["model_input_smoke_materialized"]}`
model_input_materialized: `{manifest["model_input_materialized"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
ready_for_model_input_qa_gate: `{manifest["ready_for_model_input_qa_gate"]}`
ready_for_loader_shape_dry_run: `{manifest["ready_for_loader_shape_dry_run"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.build_real_covalent_confirmed_candidate_model_input_materialization_smoke_v0()
    write_csv(result["index_rows"], smoke.MODEL_INPUT_SMOKE_INDEX_CSV, smoke.INDEX_COLUMNS)
    write_csv(result["feature_rows"], smoke.FEATURE_STATUS_CSV, smoke.FEATURE_STATUS_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_STATUS_CSV, smoke.MASK_STATUS_COLUMNS)
    write_csv(result["audit_rows"], smoke.AUDIT_CSV, smoke.AUDIT_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_model_input_materialization_smoke_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_model_input_materialization_smoke_v0_blocked")
    print(f"model_input_smoke_index_row_count={manifest['model_input_smoke_index_row_count']}")
    print(f"model_input_smoke_feature_status_row_count={manifest['model_input_smoke_feature_status_row_count']}")
    print(f"model_input_smoke_mask_status_row_count={manifest['model_input_smoke_mask_status_row_count']}")
    print(f"model_input_materialization_smoke_audit_row_count={manifest['model_input_materialization_smoke_audit_row_count']}")
    print(f"model_input_smoke_written={manifest['model_input_smoke_written']}")
    print(f"model_input_smoke_materialized={manifest['model_input_smoke_materialized']}")
    print(f"model_input_materialized={manifest['model_input_materialized']}")
    print(f"ready_for_model_input_qa_gate={manifest['ready_for_model_input_qa_gate']}")
    print(f"ready_for_loader_shape_dry_run={manifest['ready_for_loader_shape_dry_run']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

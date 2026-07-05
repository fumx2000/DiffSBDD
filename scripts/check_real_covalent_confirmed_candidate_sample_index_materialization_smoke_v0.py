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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_materialization_smoke as smoke  # noqa: E402


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
                "decision": "sample_index materialization smoke passed"
                if manifest["all_checks_passed"]
                else "sample_index materialization smoke blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Sample Index Materialization Smoke v0 Summary

Step 13T writes a 3-row sample_index smoke artifact for the current CYS/SG golden samples.
It is not an enriched_sample_index, not a final_dataset, and not model input.
It does not run molecule parsing, raw structure parsing, forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.

The materialized smoke sample_index preserves all five V1 canonical mask tasks:
`warhead_only`/`A`, `linker_plus_warhead`/`B`, `scaffold_plus_warhead`/`B2`, `scaffold_only`/`B3`, and `scaffold_plus_linker_plus_warhead`/`C`.
B3 scaffold_only remains included as a formal canonical task.
No extra mask task was added.

This smoke allows the next sample_index QA gate.
It does not allow model input materialization and does not allow training.
Feature semantics audit remains required before formal training.

sample_index_smoke_row_count: `{manifest["sample_index_smoke_row_count"]}`
sample_index_audit_row_count: `{manifest["sample_index_audit_row_count"]}`
sample_index_written: `{manifest["sample_index_written"]}`
enriched_sample_index_written: `{manifest["enriched_sample_index_written"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
model_input_materialized: `{manifest["model_input_materialized"]}`
ready_for_sample_index_qa_gate: `{manifest["ready_for_sample_index_qa_gate"]}`
ready_for_model_input_design_gate: `{manifest["ready_for_model_input_design_gate"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.build_real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0()
    write_csv(result["sample_index_rows"], smoke.SAMPLE_INDEX_SMOKE_CSV, smoke.SAMPLE_INDEX_COLUMNS)
    write_csv(result["audit_rows"], smoke.AUDIT_CSV, smoke.AUDIT_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0_blocked")
    print(f"sample_index_smoke_row_count={manifest['sample_index_smoke_row_count']}")
    print(f"sample_index_audit_row_count={manifest['sample_index_audit_row_count']}")
    print(f"canonical_mask_task_names={','.join(manifest['canonical_mask_task_names'])}")
    print(f"canonical_mask_task_aliases={','.join(manifest['canonical_mask_task_aliases'])}")
    print(f"b3_scaffold_only_included={manifest['b3_scaffold_only_included']}")
    print(f"sample_index_written={manifest['sample_index_written']}")
    print(f"model_input_materialized={manifest['model_input_materialized']}")
    print(f"ready_for_sample_index_qa_gate={manifest['ready_for_sample_index_qa_gate']}")
    print(f"ready_for_model_input_design_gate={manifest['ready_for_model_input_design_gate']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

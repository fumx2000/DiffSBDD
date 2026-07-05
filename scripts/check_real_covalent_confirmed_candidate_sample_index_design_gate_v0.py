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

from covalent_ext import real_covalent_confirmed_candidate_sample_index_design_gate as design  # noqa: E402


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
                "stage": design.STAGE,
                "previous_stage": design.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "sample_index design gate passed"
                if manifest["all_checks_passed"]
                else "sample_index design gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Sample Index Design Gate v0 Summary

Step 13S is a sample_index design gate only.
It defines the future sample_index schema, dependency contract, candidate contract, mask task contract, readiness boundary, and safety gate.
It does not write a real sample_index.
It does not write enriched_sample_index, final_dataset, split assignments, leakage matrix, or model input.
It does not run forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.

The canonical V1 mask task set remains five tasks:
1. `warhead_only` with display alias `A`
2. `linker_plus_warhead` with display alias `B`
3. `scaffold_plus_warhead` with display alias `B2`
4. `scaffold_only` with display alias `B3`
5. `scaffold_plus_linker_plus_warhead` with display alias `C`

Long semantic mask names are the source of truth.
A/B/B2/B3/C aliases are display-only.
B3 scaffold_only is a formal V1 canonical mask task.
No sixth or seventh mask task was added.

This gate allows the next sample_index materialization smoke to begin.
It does not allow model input materialization and does not allow training.
Feature semantics audit remains required before formal training.

schema_contract_row_count: `{manifest["schema_contract_row_count"]}`
dependency_contract_row_count: `{manifest["dependency_contract_row_count"]}`
candidate_contract_row_count: `{manifest["candidate_contract_row_count"]}`
mask_task_contract_row_count: `{manifest["mask_task_contract_row_count"]}`
ready_for_sample_index_materialization_smoke: `{manifest["ready_for_sample_index_materialization_smoke"]}`
ready_to_write_sample_index_now: `{manifest["ready_to_write_sample_index_now"]}`
ready_for_model_input_design_gate: `{manifest["ready_for_model_input_design_gate"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_confirmed_candidate_sample_index_design_gate_v0()
    write_csv(result["schema_rows"], design.SCHEMA_CONTRACT_CSV, design.SCHEMA_COLUMNS)
    write_csv(result["dependency_rows"], design.DEPENDENCY_CONTRACT_CSV, design.DEPENDENCY_COLUMNS)
    write_csv(result["candidate_rows"], design.CANDIDATE_CONTRACT_CSV, design.CANDIDATE_COLUMNS)
    write_csv(result["mask_task_rows"], design.MASK_TASK_CONTRACT_CSV, design.MASK_TASK_COLUMNS)
    write_csv(build_report_rows(result), design.REPORT_CSV, design.REPORT_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_sample_index_design_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_sample_index_design_gate_v0_blocked")
    print(f"schema_contract_row_count={manifest['schema_contract_row_count']}")
    print(f"dependency_contract_row_count={manifest['dependency_contract_row_count']}")
    print(f"candidate_contract_row_count={manifest['candidate_contract_row_count']}")
    print(f"mask_task_contract_row_count={manifest['mask_task_contract_row_count']}")
    print(f"canonical_mask_task_names={','.join(manifest['canonical_mask_task_names'])}")
    print(f"canonical_mask_task_aliases={','.join(manifest['canonical_mask_task_aliases'])}")
    print(f"b3_scaffold_only_included={manifest['b3_scaffold_only_included']}")
    print(f"ready_for_sample_index_materialization_smoke={manifest['ready_for_sample_index_materialization_smoke']}")
    print(f"ready_to_write_sample_index_now={manifest['ready_to_write_sample_index_now']}")
    print(f"ready_for_model_input_design_gate={manifest['ready_for_model_input_design_gate']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

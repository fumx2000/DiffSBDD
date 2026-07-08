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

from covalent_ext import covapie_sample_index_design_gate as design_gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
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
    text = f"""# CovaPIE Sample Index Design Gate v0 Summary

Step 13BG is a design gate for a future sample index smoke step.
It reads only Step 13BF/13BE derived CSV and JSON artifacts and designs source artifact references, a 31-field sample index schema, and a 4 events x 5 mask task expansion contract.
It does not write `sample_index.csv`, `sample_index.json`, final_dataset, split assignments, leakage matrix, tensors, or training inputs.
It does not read raw CIF files, parse mmCIF, extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit, scaffold/linker/warhead annotation, auxiliary labels, and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows sample index smoke next, not sample index QA, not split/leakage design, and not training.

future_sample_index_schema_field_count: `{manifest["future_sample_index_schema_field_count"]}`
future_mask_task_expansion_row_count: `{manifest["future_mask_task_expansion_row_count"]}`
future_unique_event_count: `{manifest["future_unique_event_count"]}`
future_mask_task_count: `{manifest["future_mask_task_count"]}`
future_planned_sample_count: `{manifest["future_planned_sample_count"]}`
sample_index_materialized_current_step: `{manifest["sample_index_materialized_current_step"]}`
sample_index_written: `{manifest["sample_index_written"]}`
ready_for_covapie_sample_index_smoke: `{manifest["ready_for_covapie_sample_index_smoke"]}`
ready_for_covapie_sample_index_qa_gate: `{manifest["ready_for_covapie_sample_index_qa_gate"]}`
ready_for_covapie_split_leakage_design_gate: `{manifest["ready_for_covapie_split_leakage_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design_gate.run_covapie_sample_index_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["source_rows"], design_gate.SOURCE_ARTIFACT_CONTRACT_CSV, design_gate.SOURCE_ARTIFACT_COLUMNS)
    write_csv(result["schema_rows"], design_gate.SCHEMA_CONTRACT_CSV, design_gate.SCHEMA_COLUMNS)
    write_csv(result["mask_rows"], design_gate.MASK_TASK_EXPANSION_CONTRACT_CSV, design_gate.MASK_EXPANSION_COLUMNS)
    write_csv(result["plan_rows"], design_gate.SMOKE_PLAN_CSV, design_gate.PLAN_COLUMNS)
    write_csv(result["boundary_rows"], design_gate.BOUNDARY_SAFETY_CSV, design_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], design_gate.GIT_SAFETY_CSV, design_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], design_gate.TRAINING_BLOCKERS_CSV, design_gate.TRAINING_BLOCKER_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_sample_index_design_gate_v0_passed")
    else:
        print("covapie_sample_index_design_gate_v0_blocked")
    for key in [
        "future_sample_index_schema_field_count",
        "future_mask_task_expansion_row_count",
        "future_planned_sample_count",
        "source_artifact_contract_passed",
        "sample_index_schema_contract_passed",
        "mask_task_expansion_contract_passed",
        "sample_index_smoke_plan_passed",
        "ready_for_covapie_sample_index_smoke",
        "ready_for_covapie_sample_index_qa_gate",
        "ready_for_covapie_split_leakage_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

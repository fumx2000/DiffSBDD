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

from covalent_ext import covapie_sample_index_smoke as smoke  # noqa: E402


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
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Sample Index Smoke v0 Summary

Step 13BH writes the minimal CovaPIE sample index smoke artifacts.
It materializes only CSV/JSON smoke rows: 4 extracted covalent events expanded across 5 canonical mask tasks for 20 rows.
It reads Step 13BG design contracts, Step 13BF QA artifacts, and Step 13BE extracted derived tables.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, download data, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
It does not write final_dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This step allows sample index QA gate next, not split/leakage design, not final dataset, and not training.

sample_index_row_count: `{manifest["sample_index_row_count"]}`
sample_index_column_count: `{manifest["sample_index_column_count"]}`
sample_index_json_row_count: `{manifest["sample_index_json_row_count"]}`
unique_event_count: `{manifest["unique_event_count"]}`
canonical_mask_task_count: `{manifest["canonical_mask_task_count"]}`
planned_sample_count: `{manifest["planned_sample_count"]}`
observed_sample_count: `{manifest["observed_sample_count"]}`
sample_id_unique_count: `{manifest["sample_id_unique_count"]}`
b3_scaffold_only_included: `{manifest["b3_scaffold_only_included"]}`
no_extra_mask_tasks_added: `{manifest["no_extra_mask_tasks_added"]}`
row_qa_passed: `{manifest["row_qa_passed"]}`
mask_distribution_qa_passed: `{manifest["mask_distribution_qa_passed"]}`
source_traceability_qa_passed: `{manifest["source_traceability_qa_passed"]}`
boundary_safety_passed: `{manifest["boundary_safety_passed"]}`
git_safety_passed: `{manifest["git_safety_passed"]}`
training_blockers_passed: `{manifest["training_blockers_passed"]}`
ready_for_covapie_sample_index_qa_gate: `{manifest["ready_for_covapie_sample_index_qa_gate"]}`
ready_for_covapie_split_leakage_design_gate: `{manifest["ready_for_covapie_split_leakage_design_gate"]}`
ready_for_covapie_final_dataset_design_gate: `{manifest["ready_for_covapie_final_dataset_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_sample_index_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["sample_rows"], smoke.SAMPLE_INDEX_SMOKE_CSV, smoke.SAMPLE_INDEX_FIELDS)
    write_json(result["sample_rows"], smoke.SAMPLE_INDEX_SMOKE_JSON)
    write_csv(result["row_qa_rows"], smoke.ROW_QA_AUDIT_CSV, smoke.ROW_QA_COLUMNS)
    write_csv(result["mask_distribution_rows"], smoke.MASK_DISTRIBUTION_AUDIT_CSV, smoke.MASK_DISTRIBUTION_COLUMNS)
    write_csv(result["traceability_rows"], smoke.SOURCE_TRACEABILITY_AUDIT_CSV, smoke.SOURCE_TRACEABILITY_COLUMNS)
    write_csv(result["boundary_rows"], smoke.BOUNDARY_SAFETY_CSV, smoke.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], smoke.TRAINING_BLOCKERS_CSV, smoke.TRAINING_BLOCKER_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_sample_index_smoke_v0_passed")
    else:
        print("covapie_sample_index_smoke_v0_blocked")
    for key in [
        "sample_index_row_count",
        "sample_index_column_count",
        "sample_index_json_row_count",
        "unique_event_count",
        "canonical_mask_task_count",
        "planned_sample_count",
        "observed_sample_count",
        "sample_id_unique_count",
        "mask_warhead_only_A_count",
        "mask_linker_plus_warhead_B_count",
        "mask_scaffold_plus_warhead_B2_count",
        "mask_scaffold_only_B3_count",
        "mask_scaffold_plus_linker_plus_warhead_C_count",
        "row_qa_passed",
        "mask_distribution_qa_passed",
        "source_traceability_qa_passed",
        "boundary_safety_passed",
        "git_safety_passed",
        "training_blockers_passed",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "ready_for_covapie_sample_index_qa_gate",
        "ready_for_covapie_split_leakage_design_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

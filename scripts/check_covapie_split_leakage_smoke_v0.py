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

from covalent_ext import covapie_split_leakage_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Split/Leakage Smoke v0 Summary

Step 13BK is a split/leakage smoke preview for the Step 13BH/13BI 20-row sample index and Step 13BJ design contract.
It materializes split units, parent-event grouping integrity, candidate-metadata grouping integrity, mask grouping integrity, and leakage risk smoke audits.
It does not write real train/val/test split assignments, a leakage matrix, final_dataset, a new sample_index, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
The current 20-row smoke remains too small for a real train/val/test split.
Feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.
Leakage/split QA remains required before final dataset design and training.
This smoke allows split/leakage QA gate next, not feature audit, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `{manifest["source_sample_index_row_count"]}`
source_unique_event_count: `{manifest["source_unique_event_count"]}`
source_canonical_mask_task_count: `{manifest["source_canonical_mask_task_count"]}`
split_unit_smoke_preview_row_count: `{manifest["split_unit_smoke_preview_row_count"]}`
parent_event_group_integrity_row_count: `{manifest["parent_event_group_integrity_row_count"]}`
candidate_metadata_group_integrity_row_count: `{manifest["candidate_metadata_group_integrity_row_count"]}`
mask_task_grouping_integrity_row_count: `{manifest["mask_task_grouping_integrity_row_count"]}`
split_leakage_risk_smoke_audit_row_count: `{manifest["split_leakage_risk_smoke_audit_row_count"]}`
split_unit_smoke_preview_passed: `{manifest["split_unit_smoke_preview_passed"]}`
parent_event_group_integrity_passed: `{manifest["parent_event_group_integrity_passed"]}`
candidate_metadata_group_integrity_passed: `{manifest["candidate_metadata_group_integrity_passed"]}`
mask_task_grouping_integrity_passed: `{manifest["mask_task_grouping_integrity_passed"]}`
split_leakage_risk_smoke_audit_passed: `{manifest["split_leakage_risk_smoke_audit_passed"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
ready_for_covapie_split_leakage_qa_gate: `{manifest["ready_for_covapie_split_leakage_qa_gate"]}`
ready_for_covapie_feature_semantics_audit_gate: `{manifest["ready_for_covapie_feature_semantics_audit_gate"]}`
ready_for_covapie_final_dataset_design_gate: `{manifest["ready_for_covapie_final_dataset_design_gate"]}`
ready_for_covapie_dataloader_smoke: `{manifest["ready_for_covapie_dataloader_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_split_leakage_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["split_unit_rows"], smoke.SPLIT_UNIT_SMOKE_PREVIEW_CSV, smoke.SPLIT_UNIT_COLUMNS)
    write_json(result["split_unit_rows"], smoke.SPLIT_UNIT_SMOKE_PREVIEW_JSON)
    write_csv(result["parent_rows"], smoke.PARENT_EVENT_GROUP_INTEGRITY_AUDIT_CSV, smoke.PARENT_EVENT_COLUMNS)
    write_csv(result["candidate_rows"], smoke.CANDIDATE_METADATA_GROUP_INTEGRITY_AUDIT_CSV, smoke.CANDIDATE_COLUMNS)
    write_csv(result["mask_rows"], smoke.MASK_TASK_GROUPING_INTEGRITY_AUDIT_CSV, smoke.MASK_GROUPING_COLUMNS)
    write_csv(result["risk_rows"], smoke.RISK_SMOKE_AUDIT_CSV, smoke.RISK_SMOKE_COLUMNS)
    write_csv(result["boundary_rows"], smoke.BOUNDARY_SAFETY_CSV, smoke.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_split_leakage_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_split_leakage_smoke_v0_blocked")
    for key in [
        "source_sample_index_row_count",
        "source_unique_event_count",
        "source_canonical_mask_task_count",
        "split_unit_smoke_preview_row_count",
        "parent_event_group_integrity_row_count",
        "candidate_metadata_group_integrity_row_count",
        "mask_task_grouping_integrity_row_count",
        "split_leakage_risk_smoke_audit_row_count",
        "split_unit_smoke_preview_passed",
        "parent_event_group_integrity_passed",
        "candidate_metadata_group_integrity_passed",
        "mask_task_grouping_integrity_passed",
        "split_leakage_risk_smoke_audit_passed",
        "boundary_safety_passed",
        "git_safety_passed",
        "split_assignments_written",
        "leakage_matrix_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "ready_for_covapie_split_leakage_qa_gate",
        "ready_for_covapie_feature_semantics_audit_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

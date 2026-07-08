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

from covalent_ext import covapie_split_leakage_design_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Split/Leakage Design Gate v0 Summary

Step 13BJ is a split/leakage design gate for the Step 13BH/13BI 20-row sample index smoke.
It designs future split grouping keys, leakage rules, leakage risk classes, split unit preview, and the next split/leakage smoke plan.
It does not write split assignments, a leakage matrix, final_dataset, a new sample_index, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
The 20-row smoke is too small for a real train/val/test split, so this step only designs the policy.
Feature semantics audit remains required before formal training, fine-tuning, or real parameter updates.
Leakage/split gates remain required before final dataset design and training.
This gate allows split/leakage smoke next, not split QA, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `{manifest["source_sample_index_row_count"]}`
source_unique_event_count: `{manifest["source_unique_event_count"]}`
source_canonical_mask_task_count: `{manifest["source_canonical_mask_task_count"]}`
split_grouping_key_contract_row_count: `{manifest["split_grouping_key_contract_row_count"]}`
leakage_rule_contract_row_count: `{manifest["leakage_rule_contract_row_count"]}`
leakage_risk_design_audit_row_count: `{manifest["leakage_risk_design_audit_row_count"]}`
split_unit_design_preview_row_count: `{manifest["split_unit_design_preview_row_count"]}`
split_leakage_smoke_plan_row_count: `{manifest["split_leakage_smoke_plan_row_count"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
ready_for_covapie_split_leakage_smoke: `{manifest["ready_for_covapie_split_leakage_smoke"]}`
ready_for_covapie_split_leakage_qa_gate: `{manifest["ready_for_covapie_split_leakage_qa_gate"]}`
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
    result = gate.run_covapie_split_leakage_design_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["grouping_rows"], gate.GROUPING_KEY_CONTRACT_CSV, gate.GROUPING_KEY_COLUMNS)
    write_csv(result["leakage_rule_rows"], gate.LEAKAGE_RULE_CONTRACT_CSV, gate.LEAKAGE_RULE_COLUMNS)
    write_csv(result["risk_rows"], gate.LEAKAGE_RISK_DESIGN_AUDIT_CSV, gate.RISK_AUDIT_COLUMNS)
    write_csv(result["split_unit_rows"], gate.SPLIT_UNIT_DESIGN_PREVIEW_CSV, gate.SPLIT_UNIT_COLUMNS)
    write_csv(result["smoke_plan_rows"], gate.SMOKE_PLAN_CSV, gate.SMOKE_PLAN_COLUMNS)
    write_csv(result["boundary_rows"], gate.BOUNDARY_SAFETY_CSV, gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], gate.GIT_SAFETY_CSV, gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_split_leakage_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_split_leakage_design_gate_v0_blocked")
    for key in [
        "source_sample_index_row_count",
        "source_unique_event_count",
        "source_canonical_mask_task_count",
        "split_grouping_key_contract_row_count",
        "leakage_rule_contract_row_count",
        "leakage_risk_design_audit_row_count",
        "split_unit_design_preview_row_count",
        "split_leakage_smoke_plan_row_count",
        "split_grouping_key_contract_passed",
        "leakage_rule_contract_passed",
        "leakage_risk_design_audit_passed",
        "split_unit_design_preview_passed",
        "split_leakage_smoke_plan_passed",
        "boundary_safety_passed",
        "git_safety_passed",
        "split_assignments_written",
        "leakage_matrix_written",
        "final_dataset_written",
        "sample_index_written_current_step",
        "ready_for_covapie_split_leakage_smoke",
        "ready_for_covapie_split_leakage_qa_gate",
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

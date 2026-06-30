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

from covalent_ext import real_covalent_leakage_aware_split_design_gate as design  # noqa: E402


REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]

DESIGN_TABLE_COLUMNS = [
    "row_type",
    "status",
    "policy_name",
    "evidence",
    "current_sample_count",
    "current_dataset_feasibility_label",
    "blocking_reasons",
    "recommended_next_step",
]


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
    sections = [
        ("step12l_precondition", manifest["step12l_training_loop_design_gate_validated"]),
        ("sample_index_audit", manifest["current_sample_index_inspected"]),
        ("required_split_metadata_schema", manifest["required_split_metadata_schema_defined"]),
        ("hard_overlap_split_policy", manifest["hard_overlap_split_policy_defined"]),
        ("soft_overlap_split_policy", manifest["soft_overlap_split_policy_defined"]),
        ("leakage_matrix_schema", manifest["leakage_matrix_schema_defined"]),
        ("future_split_output_schema", manifest["future_split_output_schema_defined"]),
        ("split_feasibility_decision", manifest["split_feasibility_decision_defined"]),
        ("safety_and_next_step_decision", manifest["real_covalent_leakage_aware_split_design_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": design.STAGE,
                "previous_stage": design.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"].get(section, {})),
                "decision": "schema defined" if passed else "schema blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Leakage-Aware Split Design Gate v0 Summary

Step 12M is a leakage-aware split design gate, not split implementation, not training.
Step 12L training loop design gate verified: {str(manifest["step12l_training_loop_design_gate_validated"]).lower()}.
The current real covalent sample_index was read from {manifest["selected_sample_index"]}.

## Current Data Scope
- current_sample_count: {manifest["current_sample_count"]}
- sample_ids: {", ".join(manifest["sample_ids"])}
- current_dataset_is_small_smoke_set: {str(manifest["current_dataset_is_small_smoke_set"]).lower()}
- current_dataset_final_split_feasible: {str(manifest["current_dataset_final_split_feasible"]).lower()}
- This three-sample real covalent set is an engineering smoke set, insufficient for final train/valid/test leakage-aware split.

## Hard Overlap Policy
- Hard overlap zero tolerance is required.
- parent_complex_id, mask_parent_id, sample_id, PDB, UniProt, ligand InChIKey, canonical SMILES, and covalent bond atom pair cannot leak across claim-bearing splits.
- A/B/B2/B3/C mask levels follow the same parent complex and are not cross split.

## Soft Overlap Policy
- Protein sequence identity threshold: 0.90.
- Ligand ECFP4 Tanimoto threshold: 0.90.
- Protein cluster plus high ligand similarity is treated as risk.
- Scaffold, warhead, reaction family, target family, and NLRP3 external overlap reports are required.

## Required Future Outputs
- train/valid/test leakage matrix schema is defined.
- split manifest, split assignments, leakage matrix, scaffold holdout report, target cluster holdout report, warhead distribution report, reaction family distribution report, Cys train-ready inventory, and NLRP3 external overlap report are required later.
- No formal split, no split assignments, and no leakage matrix were written in this step.

## Safety Boundary
- No forward, no loss compute, no backward, no optimizer creation, no parameter update, no training loop call, no checkpoint/model/tensor dump.
- formal_training_allowed: {str(manifest["formal_training_allowed"]).lower()}
- final_train_valid_test_split_allowed: {str(manifest["final_train_valid_test_split_allowed"]).lower()}

## Decision
- real_covalent_leakage_aware_split_design_gate_passed: {str(manifest["real_covalent_leakage_aware_split_design_gate_passed"]).lower()}
- split_design_contract_defined: {str(manifest["split_design_contract_defined"]).lower()}
- metadata_inventory_required_before_split: {str(manifest["metadata_inventory_required_before_split"]).lower()}
- recommended_next_step: real_covalent_split_metadata_inventory_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_leakage_aware_split_design_gate_v0()
    write_csv(build_report_rows(result), design.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["design_table_rows"], design.DESIGN_TABLE_CSV, DESIGN_TABLE_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    print("real_covalent_leakage_aware_split_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import real_covalent_split_metadata_inventory_gate as inventory  # noqa: E402


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

INVENTORY_TABLE_COLUMNS = [
    "row_type",
    "field_group",
    "field_name",
    "availability_status",
    "observed_in_sample_index",
    "candidate_source_field",
    "enrichment_requirement",
    "authoritative_now",
    "blocks_final_split",
    "current_sample_count",
    "evidence",
    "status",
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
        ("step12m_precondition", manifest["step12m_leakage_aware_split_design_gate_validated"]),
        ("sample_index_audit", manifest["current_sample_index_inspected"]),
        ("required_metadata_schema_loaded", manifest["required_split_metadata_schema_loaded_from_step12m"]),
        ("exact_field_coverage_inventory", manifest["present_required_metadata_field_count"] == 2),
        ("metadata_group_summary", manifest["missing_required_metadata_field_count"] == 36),
        ("observed_nonrequired_fields", manifest["observed_nonrequired_field_count"] > 0),
        ("candidate_derivation_plan", manifest["candidate_derivation_plan_defined"]),
        ("future_metadata_enrichment_output_plan", manifest["future_metadata_enrichment_output_plan_defined"]),
        ("metadata_inventory_feasibility_decision", manifest["metadata_inventory_feasibility_decision_defined"]),
        ("safety_and_next_step_decision", manifest["real_covalent_split_metadata_inventory_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": inventory.STAGE,
                "previous_stage": inventory.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"].get(section, {})),
                "decision": "inventory defined" if passed else "inventory blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Split Metadata Inventory Gate v0 Summary

Step 12N is a split metadata inventory gate, not enrichment, not split implementation, not training.
Step 12M leakage-aware split design gate was verified: {str(manifest["step12m_leakage_aware_split_design_gate_validated"]).lower()}.

## Current Sample Index
- current_sample_count: {manifest["current_sample_count"]} samples.
- sample_index_observed_field_count: {manifest["sample_index_observed_field_count"]}.
- sample_index_observed_fields: {", ".join(manifest["sample_index_observed_fields"])}.
- No NPZ contents read.
- npz_files_loaded: {str(manifest["npz_files_loaded"]).lower()}.
- npz_contents_read: {str(manifest["npz_contents_read"]).lower()}.

## Required Metadata Coverage
- Step 12M required split metadata field count: {manifest["required_split_metadata_field_count"]}.
- exact present required fields: sample_id, ligand_reactive_atom_index.
- missing required metadata count: {manifest["missing_required_metadata_field_count"]}.
- metadata completeness: 2/38.
- metadata_complete_for_final_split: {str(manifest["metadata_complete_for_final_split"]).lower()}.

## Useful Non-Required Fields
- Useful but non-required sample_index fields include atom counts, materialization_status, npz_path, npz_sha256, source_sample_id, and split.
- split field is not final leakage-aware split and must not be used for paper claim.

## Candidate Enrichment Plan
- Candidate derivation plan is defined.
- Candidate metadata parsed from sample_id or source_sample_id is not authoritative.
- ligand identity requires RDKit/ligand structure.
- protein identity requires sequence/UniProt/CD-HIT.
- geometry requires coordinate calculation.

## Output Boundary
- No enriched sample_index written.
- No split assignments written.
- No leakage matrix written.
- No forward, no loss compute, no backward, no optimizer creation, no parameter update, no training loop call, no checkpoint/model/tensor dump.

## Decision
- metadata gap level: {manifest["metadata_gap_level"]}.
- metadata_enrichment_required: {str(manifest["metadata_enrichment_required"]).lower()}.
- final_train_valid_test_split_allowed: {str(manifest["final_train_valid_test_split_allowed"]).lower()}.
- real_covalent_split_metadata_inventory_gate_passed: {str(manifest["real_covalent_split_metadata_inventory_gate_passed"]).lower()}.
- recommended_next_step: real_covalent_split_metadata_enrichment_design_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = inventory.build_real_covalent_split_metadata_inventory_gate_v0()
    write_csv(build_report_rows(result), inventory.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["inventory_table_rows"], inventory.INVENTORY_TABLE_CSV, INVENTORY_TABLE_COLUMNS)
    write_json(result["manifest"], inventory.MANIFEST_JSON)
    write_summary(result["manifest"], inventory.SUMMARY_MD)
    print("real_covalent_split_metadata_inventory_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

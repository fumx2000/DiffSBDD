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

from covalent_ext import real_covalent_split_metadata_enrichment_design_gate as design  # noqa: E402


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
    "missing_required_metadata_field_count",
    "recommended_next_step",
    "blocking_reasons",
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
            writer.writerow({key: _csv_value(row[key]) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    sections = [
        ("step12n_precondition", manifest["step12n_split_metadata_inventory_gate_validated"]),
        ("metadata_enrichment_concept", manifest["metadata_enrichment_concept_defined"]),
        ("multi_source_adapter_architecture", manifest["multi_source_adapter_architecture_defined"]),
        ("required_source_adapter_design", manifest["required_source_adapter_design_defined"]),
        ("enrichment_field_derivation_plan", manifest["enrichment_field_derivation_plan_defined"]),
        ("enrichment_quality_policy", manifest["enrichment_quality_policy_defined"]),
        ("enrichment_output_schema", manifest["enrichment_output_schema_defined"]),
        ("large_scale_data_transition_plan", manifest["large_scale_data_transition_plan_defined"]),
        ("safety_and_next_step_decision", manifest["real_covalent_split_metadata_enrichment_design_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": design.STAGE,
                "previous_stage": design.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"][section]),
                "decision": "design defined" if passed else "design blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Split Metadata Enrichment Design Gate v0 Summary

Step 12O is a metadata enrichment design gate, not actual enrichment, not downloading, not split, not training.

## Definition
Metadata enrichment converts a thin materialization index to authoritative leakage-aware split metadata.
Current sample_index metadata completeness is {manifest["metadata_completeness_ratio_text"]}, so enrichment is required before final split or training.

## Multi-Source Architecture
Different datasets can enter via source-specific adapters, then normalize into a canonical raw covalent record schema.
They cannot one-pot merge before normalization.
Required source-specific adapters: CovPDB, CovBinderInPDB, CovalentInDB, PDB/mmCIF direct, local curated.
The common enrichment pipeline includes ligand identity enrichment, protein identity enrichment, covalent identity enrichment, geometry/diversity enrichment, quality control enrichment, and leakage metadata enrichment.

## Enrichment Methods
Ligand identity requires RDKit.
Protein identity requires UniProt and CD-HIT-compatible sequence clustering.
Geometry/diversity requires coordinate geometry calculation.
Warhead and reaction metadata require a SMARTS library, reaction family classifier, and reconstruction template registry.

## Quality Policy
Heuristic metadata may be used for inventory only.
Authoritative metadata missing blocks final split and training.
Low-confidence, ambiguous covalent bond, ligand sanitization fail, protein mapping fail, duplicate, and non-Cys records are deferred or flagged according to the policy.

## Data Transition
ready_to_design_multi_source_ingestion=true.
ready_to_download_large_scale_data_now=false.
Raw downloads and large binary structures cannot be committed.
Allowed git outputs for this design stage: csv, json, md, py.

## Safety Boundary
No data download/network/RDKit/UniProt/CD-HIT/geometry run occurred.
No NPZ contents were read.
No enriched sample_index, split assignments, leakage matrix, or final split were written.
No forward, loss compute, backward, optimizer creation, parameter update, training loop call, checkpoint/model/tensor dump occurred.

## Decision
- real_covalent_split_metadata_enrichment_design_gate_passed: {str(manifest["real_covalent_split_metadata_enrichment_design_gate_passed"]).lower()}
- metadata_enrichment_design_contract_defined: {str(manifest["metadata_enrichment_design_contract_defined"]).lower()}
- recommended_next_step: real_covalent_multi_source_dataset_ingestion_design_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_split_metadata_enrichment_design_gate_v0()
    write_csv(build_report_rows(result), design.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["design_table_rows"], design.DESIGN_TABLE_CSV, DESIGN_TABLE_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    print("real_covalent_split_metadata_enrichment_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

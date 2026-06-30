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

from covalent_ext import real_covalent_multi_source_dataset_ingestion_design_gate as design  # noqa: E402


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
    "source_count",
    "ready_to_download_large_scale_data_now",
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
        ("step12o_precondition", manifest["step12o_split_metadata_enrichment_design_gate_validated"]),
        ("multi_source_ingestion_concept", manifest["multi_source_ingestion_concept_defined"]),
        ("source_registry_schema", manifest["source_registry_schema_defined"]),
        ("raw_storage_layout_design", manifest["raw_storage_layout_defined"]),
        ("download_job_manifest_schema", manifest["download_job_manifest_schema_defined"]),
        ("source_adapter_interface_contract", manifest["source_adapter_interface_contract_defined"]),
        ("source_specific_ingestion_design_details", manifest["source_specific_ingestion_design_details_defined"]),
        ("duplicate_provenance_priority_policy", manifest["duplicate_provenance_priority_policy_defined"]),
        ("small_pilot_ingestion_plan", manifest["small_pilot_ingestion_plan_defined"]),
        ("git_data_policy", manifest["git_data_policy_defined"]),
        (
            "safety_and_next_step_decision",
            manifest["real_covalent_multi_source_dataset_ingestion_design_gate_passed"],
        ),
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
    text = f"""# Real Covalent Multi-Source Dataset Ingestion Design Gate v0 Summary

Step 12P is a multi-source dataset ingestion design gate, not downloading, not enrichment, not split, not training.

## Scope
This step defines the pre-download engineering contract for covalent dataset ingestion. It does not write real source URLs, does not verify current URLs, and does not verify license terms. Source URL placeholders and usage notes must be resolved in the source registry license audit.

## Planned Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB
- PDB/mmCIF direct
- local curated

## Adapter Contract
Different datasets must enter through source-specific adapters. Each adapter must output canonical raw covalent records.
Different sources cannot one-pot merge before normalization.
The canonical raw covalent record schema is required before metadata enrichment.

## Raw Storage
Raw storage design is data/raw/covalent_sources/{{source_name}}/... with downloads, structures, tables, manifests, logs, and checksums subdirectories.
This step created no raw dirs and wrote no raw files.

## Download Controls
Download manifest, checksum, resume, and provenance records are required before any download job.
Raw downloads and large binary structures cannot commit to git.
Small pilot scope is 1-3 records per source after license audit.

## Safety Boundary
No data download/network/source registry/raw dirs/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- source_registry_entry_count: {manifest["source_registry_entry_count"]}
- ready_to_create_source_registry_license_audit: {str(manifest["ready_to_create_source_registry_license_audit"]).lower()}
- ready_to_download_large_scale_data_now: {str(manifest["ready_to_download_large_scale_data_now"]).lower()}
- recommended_next_step: real_covalent_source_registry_license_audit_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_multi_source_dataset_ingestion_design_gate_v0()
    write_csv(build_report_rows(result), design.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["design_table_rows"], design.DESIGN_TABLE_CSV, DESIGN_TABLE_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    print("real_covalent_multi_source_dataset_ingestion_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

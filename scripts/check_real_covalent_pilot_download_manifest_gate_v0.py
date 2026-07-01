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

from covalent_ext import real_covalent_pilot_download_manifest_gate as gate  # noqa: E402


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
        ("step12q_precondition", manifest["step12q_source_registry_license_audit_gate_validated"]),
        ("sample_index_pilot_id_audit", manifest["sample_index_exists"]),
        ("pilot_download_manifest_rows", manifest["pilot_download_manifest_row_count"] == 9),
        ("pdb_direct_pilot_jobs", manifest["pdb_direct_pilot_job_count"] == 3),
        ("local_curated_pilot_jobs", manifest["local_curated_pilot_job_count"] == 3),
        ("blocked_source_rows", manifest["blocked_source_row_count"] == 3),
        ("download_dry_run_readiness_policy", manifest["download_dry_run_readiness_policy_defined"]),
        ("safety_and_next_step_decision", manifest["real_covalent_pilot_download_manifest_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"][section]),
                "decision": "pilot manifest gate defined" if passed else "pilot manifest gate blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Pilot Download Manifest Gate v0 Summary

Step 12R is a pilot download manifest gate, not download execution, not network, not adapter execution, not enrichment, not split, not training.

This step created a small pilot download manifest only. It did not download data, create raw dirs, write raw files, run adapters, run RDKit/UniProt/CD-HIT/geometry, read NPZ contents, or run training.

## PDB/mmCIF Direct Pilot
- 6DI9
- 5F2E
- 6OIM

RCSB mmCIF URL template:
- https://files.rcsb.org/download/{{pdb_id}}.cif.gz

PDB/mmCIF direct license status:
- verified_cc0_for_pdb_archive

## Local Curated Pilot
- BTK_C481_6DI9_pre_reaction
- KRAS_G12C_5F2E_pre_reaction
- KRAS_G12C_6OIM_pre_reaction

## Blocked Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB

All downloads disabled in this step.
All pilot jobs ready_for_execution=false.

## Dry-Run Readiness
- pilot_download_manifest_row_count: {manifest["pilot_download_manifest_row_count"]}
- pilot_download_job_count: {manifest["pilot_download_job_count"]}
- ready_to_run_pilot_download_dry_run=true
- ready_to_execute_pilot_download=false
- ready_to_download_large_scale_data_now=false

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- real_covalent_pilot_download_manifest_gate_passed: {str(manifest["real_covalent_pilot_download_manifest_gate_passed"]).lower()}
- recommended_next_step: real_covalent_pilot_download_dry_run_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_pilot_download_manifest_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(
        result["pilot_download_manifest_rows"],
        gate.PILOT_DOWNLOAD_MANIFEST_CSV,
        gate.PILOT_DOWNLOAD_MANIFEST_COLUMNS,
    )
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_pilot_download_manifest_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

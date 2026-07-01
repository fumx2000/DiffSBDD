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

from covalent_ext import real_covalent_source_registry_license_audit_gate as audit  # noqa: E402


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
        ("step12p_precondition", manifest["step12p_multi_source_dataset_ingestion_design_gate_validated"]),
        ("source_registry_license_audit_seed", manifest["source_registry_license_audit_seed_defined"]),
        ("source_registry_audit_records", manifest["source_registry_audit_record_count"] == 5),
        ("license_decision_policy", manifest["license_decision_policy_defined"]),
        ("pilot_eligibility_decision", manifest["pilot_eligibility_decision_defined"]),
        ("audit_output_schema", manifest["source_registry_audit_output_schema_defined"]),
        ("safety_boundary", not manifest["data_downloaded"] and not manifest["external_network_called"]),
        ("next_step_decision", manifest["real_covalent_source_registry_license_audit_gate_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": audit.STAGE,
                "previous_stage": audit.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"][section]),
                "decision": "audit gate defined" if passed else "audit gate blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Source Registry License Audit Gate v0 Summary

Step 12Q is a source registry license audit gate, not downloading, not adapter implementation, not enrichment, not split, not training.

This step uses manual web-audit seed information to generate a small source registry license audit table.

## Planned Sources
- CovPDB
- CovBinderInPDB
- CovalentInDB
- PDB/mmCIF direct
- local curated

## License Audit
PDB/mmCIF direct has PDB archive license status verified CC0.
Local curated is local project controlled.
CovPDB / CovBinderInPDB / CovalentInDB require manual license review.
Publication found is not license clearance.
Free web access is not bulk download permission.
All bulk downloads disabled.

## Pilot Decision
Pilot candidates after audit are PDB/mmCIF direct and local curated.
Pilot download is still not allowed in this step; the next step must create a pilot download manifest.

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Decision
- source_registry_audit_record_count: {manifest["source_registry_audit_record_count"]}
- sources_requiring_manual_license_review_count: {manifest["sources_requiring_manual_license_review_count"]}
- ready_to_create_pilot_download_manifest: {str(manifest["ready_to_create_pilot_download_manifest"]).lower()}
- ready_to_download_large_scale_data_now: {str(manifest["ready_to_download_large_scale_data_now"]).lower()}
- recommended_next_step: real_covalent_pilot_download_manifest_gate
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = audit.build_real_covalent_source_registry_license_audit_gate_v0()
    write_csv(build_report_rows(result), audit.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["audit_table_rows"], audit.SOURCE_REGISTRY_AUDIT_TABLE_CSV, audit.AUDIT_TABLE_COLUMNS)
    write_json(result["manifest"], audit.MANIFEST_JSON)
    write_summary(result["manifest"], audit.SUMMARY_MD)
    print("real_covalent_source_registry_license_audit_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

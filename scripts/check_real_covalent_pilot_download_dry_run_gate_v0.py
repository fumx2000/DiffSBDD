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

from covalent_ext import real_covalent_pilot_download_dry_run_gate as gate  # noqa: E402


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
        ("step12r_precondition", manifest["step12r_pilot_download_manifest_gate_validated"]),
        ("manifest_schema_validation", manifest["dry_run_validated_manifest_schema"]),
        ("pdb_direct_url_path_checksum_validation", manifest["dry_run_pdb_direct_passed_rows"] == 3),
        ("local_curated_validation", manifest["dry_run_local_curated_passed_rows"] == 3),
        ("blocked_source_policy_validation", manifest["dry_run_blocked_source_rows"] == 3),
        ("dry_run_safety_boundary", not manifest["dry_run_network_called"] and not manifest["dry_run_files_downloaded"]),
        ("dry_run_execution_readiness", manifest["ready_to_execute_pilot_download_after_dry_run"]),
        ("next_step_decision", manifest["real_covalent_pilot_download_dry_run_gate_passed"]),
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
                "decision": "pilot dry-run gate defined" if passed else "pilot dry-run gate blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Pilot Download Dry-Run Gate v0 Summary

Step 12S is a pilot download dry-run gate, not download execution, not network, not adapter execution, not enrichment, not split, not training.

This step only validates manifest schema, URL strings, local output paths, checksum policy, provenance policy, and blocked source policy.

## PDB/mmCIF Direct Dry-Run Passed
- 6DI9
- 5F2E
- 6OIM

## Local Curated Dry-Run Passed
- BTK_C481_6DI9_pre_reaction
- KRAS_G12C_5F2E_pre_reaction
- KRAS_G12C_6OIM_pre_reaction

## Blocked As Expected
- CovPDB
- CovBinderInPDB
- CovalentInDB

## Dry-Run Result
- dry_run_total_rows: {manifest["dry_run_total_rows"]}
- dry_run_passed_rows: {manifest["dry_run_passed_rows"]}
- dry_run_blocked_as_expected_rows: {manifest["dry_run_blocked_as_expected_rows"]}
- dry_run_failed_rows: {manifest["dry_run_failed_rows"]}
- ready_to_execute_pilot_download_after_dry_run=true
- pilot_download_execution_allowed_in_this_step=false
- ready_to_download_large_scale_data_now=false

## Safety Boundary
No data download/network/raw dirs/raw files/adapters occurred.
No RDKit/UniProt/CD-HIT/geometry/NPZ/training occurred.
No enriched sample_index, split assignments, leakage matrix, final split, checkpoint, model, or tensor dump was written.

## Next Step
The next step is real_covalent_pilot_download_execution_gate.
That next step should actually download 3 PDB/mmCIF .cif.gz files, but raw files cannot commit.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_pilot_download_dry_run_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["dry_run_rows"], gate.DRY_RUN_TABLE_CSV, gate.DRY_RUN_TABLE_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_pilot_download_dry_run_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

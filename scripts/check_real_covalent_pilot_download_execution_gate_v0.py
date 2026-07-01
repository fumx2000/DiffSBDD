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

from covalent_ext import real_covalent_pilot_download_execution_gate as gate  # noqa: E402


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
        ("step12s_precondition", manifest["step12s_pilot_download_dry_run_gate_validated"]),
        ("raw_ignore_guard", manifest["data_raw_gitignored"] and not manifest["gitignore_modified"]),
        ("pdb_mmcif_download_execution", manifest["pdb_mmcif_download_success_count"] == 3),
        ("download_integrity_observation", manifest["all_downloaded_files_sha256_recorded"]),
        ("local_curated_provenance", manifest["local_curated_provenance_row_count"] == 3),
        ("prohibited_operations_boundary", not manifest["adapter_execution_run"] and not manifest["npz_contents_read"]),
        ("git_raw_safety", not manifest["raw_files_staged"] and not manifest["raw_files_committed_allowed"]),
        ("next_step_decision", manifest["real_covalent_pilot_download_execution_gate_passed"]),
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
                "decision": "pilot download execution completed" if passed else "pilot download execution blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    raw_paths = "\n".join(f"- `{path}`" for path in manifest["downloaded_raw_paths"])
    text = f"""# Real Covalent Pilot Download Execution Gate v0 Summary

Step 12T is a pilot download execution gate.

This step actually used the network to download 3 PDB/mmCIF .cif.gz files.

## Downloaded PDB IDs
- 6DI9
- 5F2E
- 6OIM

## Raw File Paths
{raw_paths}

Raw files are not committed and must never be committed.

## Recorded Integrity Metadata
This step recorded SHA256, file size, gzip magic validation, and download provenance.

## Local Curated Provenance
Local curated provenance only records sample_index rows and does not read NPZ contents.

## Safety Boundary
No mmCIF parsing occurred.
No adapters, RDKit/UniProt/CD-HIT/geometry, or training ran.
No enriched sample_index, split assignments, leakage matrix, checkpoint, model, or tensor dump was written.

## Decision
- pdb_mmcif_download_success_count: {manifest["pdb_mmcif_download_success_count"]}
- provenance_row_count: {manifest["provenance_row_count"]}
- data_raw_gitignored: {str(manifest["data_raw_gitignored"]).lower()}
- raw_files_staged: {str(manifest["raw_files_staged"]).lower()}
- ready_for_pilot_download_integrity_gate: {str(manifest["ready_for_pilot_download_integrity_gate"]).lower()}
- recommended_next_step: real_covalent_pilot_download_integrity_gate

The next step is real_covalent_pilot_download_integrity_gate: it should only check raw files, checksum, provenance, git-ignore, and staging. It should still not parse mmCIF. The step after that can start the minimal parser/adapter smoke.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_pilot_download_execution_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["provenance_rows"], gate.PROVENANCE_CSV, gate.PROVENANCE_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_pilot_download_execution_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

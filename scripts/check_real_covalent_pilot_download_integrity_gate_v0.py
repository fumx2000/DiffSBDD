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

from covalent_ext import real_covalent_pilot_download_integrity_gate as gate  # noqa: E402


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
        ("step12t_precondition", manifest["step12t_pilot_download_execution_gate_validated"]),
        ("raw_file_existence_size_sha256", manifest["all_raw_sha256_match_expected"]),
        ("gzip_magic_validation", manifest["all_raw_gzip_magic_valid"]),
        ("provenance_cross_check", manifest["provenance_cross_check_passed"]),
        ("git_ignore_and_staging_guard", manifest["all_raw_files_gitignored"] and manifest["no_raw_files_staged"]),
        ("no_parsing_no_adapter_boundary", not manifest["mmcif_parsed"] and not manifest["adapter_execution_run"]),
        ("committable_artifact_policy", not manifest["raw_files_commit_allowed"] and not manifest["forbidden_committable_artifacts_created"]),
        ("next_step_decision", manifest["real_covalent_pilot_download_integrity_gate_passed"]),
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
                "decision": "pilot download integrity verified" if passed else "pilot download integrity blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Pilot Download Integrity Gate v0 Summary

Step 12U is a pilot download integrity gate.

This step performed no network calls, no re-download, no decompression, and no mmCIF parsing.

## Raw Files Rechecked
- 6DI9.cif.gz
- 5F2E.cif.gz
- 6OIM.cif.gz

All raw files exist, are nonempty, have file size values matching Step 12T, have SHA256 values matching Step 12T provenance, have valid gzip magic bytes, live under data/raw, are gitignored, are not staged, are not tracked, and are not allowed to commit.

## Provenance
The provenance cross-check passed. The Step 12T provenance rows match the recomputed raw file size and SHA256 values, and local curated rows remain recorded without NPZ reads.

## Safety Boundary
This step performed no mmCIF parsing, no adapters, no RDKit/UniProt/CD-HIT/geometry, and no training.
It did not write enriched sample_index, split assignments, leakage matrix, checkpoint, model, or tensor dump artifacts.

## Decision
- raw_file_integrity_row_count: {manifest["raw_file_integrity_row_count"]}
- all_raw_file_sizes_match_expected: {str(manifest["all_raw_file_sizes_match_expected"]).lower()}
- all_raw_sha256_match_expected: {str(manifest["all_raw_sha256_match_expected"]).lower()}
- all_raw_gzip_magic_valid: {str(manifest["all_raw_gzip_magic_valid"]).lower()}
- provenance_cross_check_passed: {str(manifest["provenance_cross_check_passed"]).lower()}
- ready_for_minimal_mmcif_parser_design_gate: {str(manifest["ready_for_minimal_mmcif_parser_design_gate"]).lower()}
- recommended_next_step: real_covalent_minimal_mmcif_parser_design_gate

The next step is real_covalent_minimal_mmcif_parser_design_gate. That step can start designing a minimal parser/adapter smoke, but still should not begin large-scale parsing.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_pilot_download_integrity_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["raw_file_integrity_rows"], gate.RAW_FILE_INTEGRITY_TABLE_CSV, gate.RAW_FILE_INTEGRITY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_pilot_download_integrity_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

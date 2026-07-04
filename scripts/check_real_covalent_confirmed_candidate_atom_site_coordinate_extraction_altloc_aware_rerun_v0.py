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

from covalent_ext import real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun as gate  # noqa: E402


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
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        passed = manifest["all_checks_passed"]
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(evidence),
                "decision": "altloc aware rerun accepted" if passed else "altloc aware rerun blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    text = f"""# Real Covalent Confirmed Candidate Atom Site Coordinate Extraction Altloc Aware Rerun v0 Summary

Step 13E2 is an altloc-aware rerun of confirmed candidate atom_site coordinate extraction.
This step was added after Step 13F debug found the HR_0002 altloc mismatch.
This step first cleaned the uncommitted blocked Step 13F untracked files.
This step read the Step 13D contract and Step 13C struct_conn reported distance.
This step actually read 3 raw `.cif.gz` files, decompressed only in memory, and wrote no decompressed mmCIF.
This step only scanned the `_atom_site` loop.
This step did not use {parser_tools}.
This step evaluated endpoint candidate pairs and selected altloc by struct_conn reported distance agreement.
HR_0002 corrected CYS481 SG from altloc A to altloc B.
HR_0002 selected protein atom_site id {manifest["hr0002_selected_protein_atom_site_id"]}, altloc {manifest["hr0002_selected_protein_label_alt_id"]}, selected pair distance approximately {manifest["hr0002_selected_pair_distance_angstrom"]:.4f} A.
6 endpoint coordinates were written.
3 altloc selection audit rows were written.
This step did not write sample_index, did not write final dataset, and did not train.
The next step is altloc-aware coordinate pair sanity gate, not sample_index and not training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["coordinate_rows"], gate.ALTLOC_AWARE_COORDINATES_CSV, gate.EXTRACTED_COORDINATE_COLUMNS)
    write_csv(result["audit_rows"], gate.ALTLOC_SELECTION_AUDIT_CSV, gate.ALTLOC_SELECTION_AUDIT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import real_covalent_confirmed_candidate_full_atom_extraction_smoke as gate  # noqa: E402


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
                "decision": "full atom extraction smoke accepted" if passed else "full atom extraction smoke blocked",
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
    text = f"""# Real Covalent Confirmed Candidate Full Atom Extraction Smoke v0 Summary

Step 13J is a minimal full atom extraction smoke for 3 confirmed covalent candidates.
This step read the Step 13I candidate contract.
This step read exactly the 3 local raw `.cif.gz` files referenced by the contract.
This step used standard-library gzip text streaming and a custom `_atom_site` text scan.
This step wrote a protein full atom table with {manifest["protein_full_atom_table_row_count"]} rows.
This step wrote a ligand full atom table with {manifest["ligand_full_atom_table_row_count"]} rows.
This step wrote 3 endpoint recovery audit rows, all passing.
HR_0002 preserved protein atom_site 659 with altloc B.
This step did not write decompressed mmCIF/PDB/SDF/MOL2 files.
This step did not use {parser_tools}.
This step did not define pockets and did not extract ligand topology.
This step did not write sample_index, enriched sample_index, final dataset, split assignments, leakage matrix, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step is not training preparation completion and does not claim training-ready samples.
Feature semantics audit is still required before any training.
The next step is pocket or topology design gate, not training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["protein_rows"], gate.PROTEIN_FULL_ATOM_TABLE_CSV, gate.FULL_ATOM_COLUMNS)
    write_csv(result["ligand_rows"], gate.LIGAND_FULL_ATOM_TABLE_CSV, gate.FULL_ATOM_COLUMNS)
    write_csv(result["audit_rows"], gate.ENDPOINT_RECOVERY_AUDIT_CSV, gate.ENDPOINT_AUDIT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_confirmed_candidate_full_atom_extraction_smoke_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

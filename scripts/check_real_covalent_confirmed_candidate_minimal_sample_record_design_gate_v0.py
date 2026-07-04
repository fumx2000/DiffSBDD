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

from covalent_ext import real_covalent_confirmed_candidate_minimal_sample_record_design_gate as gate  # noqa: E402


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
                "decision": "minimal sample record design accepted" if passed else "minimal sample record design blocked",
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
    text = f"""# Real Covalent Confirmed Candidate Minimal Sample Record Design Gate v0 Summary

Step 13G is a minimal sample record design gate.
This step read the Step 13F-v1 pair sanity table.
This step converts 3 confirmed covalent candidates that passed altloc-aware pair sanity into a future minimal sample record contract.
This step did not read raw `.cif.gz`, did not decompress raw files, did not use {gate.GZIP_TEXT}, and did not parse mmCIF.
This step did not recompute geometry distance.
This step did not use {parser_tools}.
This step did not write sample_index, did not write final dataset, and did not train.
This step wrote a schema contract and a candidate contract.
The candidate contract keeps training_ready=false.
Future steps still require full protein atom extraction, full ligand atom extraction, pocket definition, ligand bond topology, feature semantics audit, and split/leakage check.
HR_0002 altloc B atom_site 659 was preserved.
The next step is minimal sample record write smoke, not direct training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["schema_rows"], gate.SCHEMA_CONTRACT_CSV, gate.SCHEMA_CONTRACT_COLUMNS)
    write_csv(result["candidate_rows"], gate.CANDIDATE_CONTRACT_CSV, gate.CANDIDATE_CONTRACT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_confirmed_candidate_minimal_sample_record_design_gate_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

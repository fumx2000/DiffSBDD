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

from covalent_ext import real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate as gate  # noqa: E402


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
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "step8 topology evidence export design gate passed"
                if manifest["all_checks_passed"]
                else "step8 topology evidence export design gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    text = f"""# Real Covalent Confirmed Candidate Step 8 Topology Evidence Export Design Gate v0 Summary

Step 13P is a Step 8 topology evidence export design gate.
Step 13O correctly blocked because current Step 8 evidence lacks per-atom and per-bond topology.
This step did not run {gate.RDKIT_TEXT}.
This step did not read, generate, modify, or copy SDF files.
This step did not use {parser_tools}, raw structure files, compressed raw input, or atom_site scanning.
This step only designs a future read-only topology export from Step 8 manual-reviewed pre-reaction provenance.
Future read-only export may parse Step 8 manual-reviewed pre-reaction SDF only when hash and manual review provenance exist.
Future export must not automatically restore ligands again.
Future export must not generalize the CYS-only V1 scope to non-CYS residues.
Schema and provenance outputs are not training inputs.
No ligand topology table, sample_index, final_dataset, or model input was written.
No training, fine-tuning, or parameter update was run.
Feature semantics audit is still required before formal training.

readonly_rdkit_export_allowed_next_step: `{manifest["readonly_rdkit_export_allowed_next_step"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0()
    write_csv(result["source_discovery_rows"], gate.SOURCE_DISCOVERY_CONTRACT_CSV, gate.SOURCE_DISCOVERY_COLUMNS)
    write_csv(result["schema_rows"], gate.EXPORT_SCHEMA_CONTRACT_CSV, gate.EXPORT_SCHEMA_COLUMNS)
    write_csv(result["candidate_rows"], gate.EXPORT_CANDIDATE_CONTRACT_CSV, gate.EXPORT_CANDIDATE_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("real_covalent_confirmed_candidate_step8_topology_evidence_export_design_gate_v0_passed")
    print(f"source_discovery_contract_row_count={manifest['source_discovery_contract_row_count']}")
    print(f"export_schema_contract_row_count={manifest['export_schema_contract_row_count']}")
    print(f"export_candidate_contract_row_count={manifest['export_candidate_contract_row_count']}")
    print(f"readonly_rdkit_export_allowed_next_step={manifest['readonly_rdkit_export_allowed_next_step']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

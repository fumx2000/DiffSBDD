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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_policy_review_gate as gate  # noqa: E402


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
                "decision": "ligand topology policy review accepted" if passed else "policy review blocked",
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
    text = f"""# Real Covalent Confirmed Candidate Ligand Topology Policy Review Gate v0 Summary

Step 13N is a ligand topology policy review gate.
This step reviewed and accepted the Step 13M CYS-only V1 scope.
The schema remains residue-agnostic.
The restoration rule remains residue-warhead-specific.
Current topology smoke scope is limited to the 3 CYS/SG golden samples.
The topology smoke must not automatically restore ligands again.
The topology smoke must not generalize to non-CYS residue classes.
The topology smoke may use Step 8 manual-reviewed pre-reaction provenance or existing graph preview only.
This step did not read raw `.cif.gz`, did not use {gate.GZIP_OPEN_KEY}, did not parse mmCIF, and did not run atom_site scan.
This step did not use {parser_tools}.
This step did not generate SDF, did not modify SDF, and did not write ligand_topology_table.
This step did not write sample_index, final_dataset, split assignments, leakage matrix, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step did not train.
Feature semantics audit is still required before formal training.
The next step can enter current CYS golden samples ligand topology smoke, but it is not training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0()
    write_csv(result["decision_rows"], gate.DECISION_CONTRACT_CSV, gate.DECISION_CONTRACT_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_confirmed_candidate_ligand_topology_policy_review_gate_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import (  # noqa: E402
    real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate as gate,
)


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
                "decision": "topology restoration policy accepted" if passed else "topology restoration policy blocked",
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
    text = f"""# Real Covalent Confirmed Candidate Ligand Topology Restoration Policy Design Gate v0 Summary

Step 13M is a ligand topology plus restoration policy design gate.
V1 can be CYS-only, but the ligand observed topology schema is residue-agnostic and does not hard-code CYS as the only semantic shape.
The current 3 candidates are CYS/SG golden smoke samples.
Step 8 already performed pre-reaction SDF manual review, graph preview, and packaging QA for this sample family.
This step acknowledges Step 8 manual review history; Step 8 artifact found is {manifest["step8_pre_reaction_manual_review_artifact_found"]}.
This step did not restore ligands again, did not generate SDF, did not modify SDF, and did not run {gate.RDKIT_TEXT}.
Observed ligand topology and pre-reaction restoration are separate contracts.
The pre-reaction restoration rule is residue-warhead-specific.
The CYS-acrylamide-like restoration rule is not generalized to other residues or other warheads.
Unknown residue-warhead pairs must be quarantined.
New residue-warhead classes require manual visual review before any restoration rule can be trusted.
This step did not read raw `.cif.gz`, did not use {gate.GZIP_OPEN_KEY}, did not decompress raw files, and did not parse mmCIF.
This step did not use {parser_tools}.
This step did not write ligand_topology_table, sample_index, final_dataset, or model input.
This step did not train and did not save checkpoint, model, or tensor dump.
Feature semantics audit is still required before formal training.
The next step is topology policy review or design refinement, not training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0()
    write_csv(
        result["schema_rows"],
        gate.OBSERVED_TOPOLOGY_SCHEMA_CONTRACT_CSV,
        gate.OBSERVED_TOPOLOGY_SCHEMA_COLUMNS,
    )
    write_csv(
        result["rule_rows"],
        gate.COVALENT_RESTORATION_RULE_REGISTRY_CONTRACT_CSV,
        gate.RESTORATION_RULE_COLUMNS,
    )
    write_csv(
        result["candidate_rows"],
        gate.LIGAND_TOPOLOGY_RESTORATION_CANDIDATE_CONTRACT_CSV,
        gate.CANDIDATE_CONTRACT_COLUMNS,
    )
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_confirmed_candidate_ligand_topology_restoration_policy_design_gate_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

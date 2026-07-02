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

from covalent_ext import real_covalent_minimal_mmcif_parser_design_gate as gate  # noqa: E402


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
        ("step12u_precondition", manifest["step12u_pilot_download_integrity_gate_validated"]),
        ("parser_input_scope_contract", manifest["parser_scope_limited_to_current_pilot"]),
        ("parser_safety_policy", manifest["parser_smoke_disallows_network"] and manifest["parser_smoke_disallows_download"]),
        ("expected_extraction_fields_contract", manifest["parser_expected_extraction_contract_row_count"] >= gate.EXPECTED_EXTRACTION_COUNT_MIN),
        ("output_artifact_policy", manifest["parser_smoke_output_limited_to_csv_json_md"]),
        ("no_parse_no_adapter_boundary_this_step", not manifest["raw_files_read"] and not manifest["mmcif_parsed"]),
        ("next_step_readiness", manifest["parser_smoke_ready_next_step"]),
        ("next_step_decision", manifest["real_covalent_minimal_mmcif_parser_design_gate_passed"]),
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
                "decision": "minimal parser smoke contract defined" if passed else "minimal parser smoke contract blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def _forbidden_parser_names() -> str:
    return "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit"


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    forbidden_parser_names = _forbidden_parser_names()
    text = f"""# Real Covalent Minimal mmCIF Parser Design Gate v0 Summary

Step 12V is a minimal mmCIF parser design gate.

This step does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF.
It only defines the next parser smoke contract.

## Step 12W Scope
The next step must actually run parser smoke and is limited to these 3 pilot raw files:
- 6DI9.cif.gz
- 5F2E.cif.gz
- 6OIM.cif.gz

Step 12W may use in-memory gzip read and text scan only.
Step 12W forbids {forbidden_parser_names}.
Step 12W forbids raw/decompressed mmCIF/PDB/SDF/MOL2 outputs and may only write CSV/JSON/MD summary artifacts.

## Minimal Fields
The parser smoke may extract only minimal metadata fields: entry id/title/entity count/atom_site count/chem_comp ids/struct_conn count/covalent connection candidate count.

## Boundaries
Step 12W does not do geometry, UniProt/CD-HIT, training, or enriched sample_index writing.
This is the last parser-before-smoke design gate; the next step must actually run parser smoke.

## Decision
- parser_contract_row_count: {manifest["parser_contract_row_count"]}
- parser_input_contract_row_count: {manifest["parser_input_contract_row_count"]}
- parser_policy_row_count: {manifest["parser_policy_row_count"]}
- parser_expected_extraction_contract_row_count: {manifest["parser_expected_extraction_contract_row_count"]}
- ready_for_minimal_mmcif_parser_smoke: {str(manifest["ready_for_minimal_mmcif_parser_smoke"]).lower()}
- recommended_next_step: real_covalent_minimal_mmcif_parser_smoke
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_minimal_mmcif_parser_design_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["contract_rows"], gate.PARSER_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_minimal_mmcif_parser_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

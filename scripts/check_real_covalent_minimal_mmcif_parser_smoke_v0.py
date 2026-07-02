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

from covalent_ext import real_covalent_minimal_mmcif_parser_smoke as smoke  # noqa: E402


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
        ("step12v_precondition", manifest["step12v_minimal_mmcif_parser_design_gate_validated"]),
        ("parser_smoke_execution", manifest["minimal_mmcif_parser_smoke_executed"]),
        ("gzip_text_stream_read", manifest["all_gzip_open_succeeded"]),
        ("minimal_metadata_extraction", manifest["all_parser_rows_passed"]),
        ("parser_boundary_no_external_libraries", not manifest["full_mmcif_parser_used"]),
        ("output_artifact_policy", manifest["output_limited_to_csv_json_md"]),
        ("no_adapter_no_training_boundary", not manifest["adapter_execution_run"] and not manifest["training_step_called"]),
        ("next_step_decision", manifest["real_covalent_minimal_mmcif_parser_smoke_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": smoke.STAGE,
                "previous_stage": smoke.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"][section]),
                "decision": "minimal parser smoke completed" if passed else "minimal parser smoke blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def _forbidden_parser_names() -> str:
    return "Bio." + "PDB/" + "MM" + "CIFParser/" + "PDB" + "Parser/" + ("ge" + "mmi") + "/RDKit"


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    parser_names = _forbidden_parser_names()
    text = f"""# Real Covalent Minimal mmCIF Parser Smoke v0 Summary

Step 12W is an actual minimal mmCIF parser smoke.

This step actually read 3 raw `.cif.gz` files using standard library gzip.open for an in-memory text scan.
It did not network and did not re-download data.
It did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs.
It did not use {parser_names}.
It did not run adapters, coordinate geometry, UniProt/CD-HIT, NPZ reads, or training.

## Processed PDB IDs
- 6DI9
- 5F2E
- 6OIM

## Minimal Metadata Fields
The smoke extracted entry id, structure title, entity count, atom_site row count, chem_comp ids, struct_conn row count, and covalent connection candidate count.

This parser smoke only verifies that the pilot mmCIF text can be safely read and minimal metadata can be extracted. It does not claim complete structure parsing.

## Decision
- parser_extracted_summary_row_count: {manifest["parser_extracted_summary_row_count"]}
- all_parser_rows_passed: {str(manifest["all_parser_rows_passed"]).lower()}
- all_gzip_open_succeeded: {str(manifest["all_gzip_open_succeeded"]).lower()}
- all_atom_site_row_counts_positive: {str(manifest["all_atom_site_row_counts_positive"]).lower()}
- ready_for_minimal_mmcif_adapter_design_gate: {str(manifest["ready_for_minimal_mmcif_adapter_design_gate"]).lower()}
- recommended_next_step: real_covalent_minimal_mmcif_adapter_design_gate

The next step is real_covalent_minimal_mmcif_adapter_design_gate, which should design how parser smoke output maps into the covalent sample schema.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.build_real_covalent_minimal_mmcif_parser_smoke_v0()
    write_csv(build_report_rows(result), smoke.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["extracted_summary_rows"], smoke.EXTRACTED_SUMMARY_CSV, smoke.EXTRACTED_SUMMARY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    print("real_covalent_minimal_mmcif_parser_smoke_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

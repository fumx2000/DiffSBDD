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

from covalent_ext import real_covalent_struct_conn_candidate_extraction_smoke as gate  # noqa: E402


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
        ("step12y_precondition", manifest["step12y_minimal_mmcif_adapter_smoke_validated"]),
        ("raw_gzip_text_read", manifest["all_raw_gzip_open_succeeded"]),
        ("struct_conn_loop_scan", manifest["struct_conn_text_scan_run"]),
        ("candidate_table_written", manifest["candidate_table_csv_written"]),
        ("candidate_status_classification", manifest["total_candidate_like_struct_conn_count"] >= 1),
        ("no_geometry_no_chemistry_inference_boundary", not manifest["coordinate_geometry_calculation_run"]),
        ("no_adapter_no_training_boundary", not manifest["adapter_execution_run"] and not manifest["training_allowed"]),
        ("next_step_decision", manifest["real_covalent_struct_conn_candidate_extraction_smoke_passed"]),
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
                "decision": "struct_conn candidate extraction smoke satisfied" if passed else "struct_conn smoke blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    no_parser_tools = f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    text = f"""# Real Covalent Struct Conn Candidate Extraction Smoke v0 Summary

Step 12Z is an actual struct_conn candidate extraction smoke.

This step actually read 3 raw `.cif.gz` files and used standard library `{gate.GZIP_OPEN_TEXT}` for an in-memory text scan.
It only scanned the `_struct_conn` loop.
It did not network and did not re-download files.
It did not write raw/decompressed mmCIF/PDB/SDF/MOL2 outputs.
It did not use {no_parser_tools}.
It did not run coordinate geometry, UniProt/CD-HIT, NPZ reads, adapter merge, or training.

The candidate table records struct_conn partner atom identifiers and conn_type_id.
It may record mmCIF-provided pdbx_dist_value, but it does not calculate distance.
It does not infer ligand/residue role, does not infer warhead_type, and does not claim covalent_bond_atom_pair is chemically verified.
It does not claim samples are training-ready.

## Counts
- candidate_table_row_count: {manifest["candidate_table_row_count"]}
- total_struct_conn_row_count: {manifest["total_struct_conn_row_count"]}
- total_candidate_like_struct_conn_count: {manifest["total_candidate_like_struct_conn_count"]}
- processed_pdb_ids: {", ".join(manifest["processed_pdb_ids"])}

Next step: `real_covalent_struct_conn_candidate_adapter_merge_smoke`, which should merge the struct_conn candidate table with the minimal adapter summary into a candidate-enriched stub.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_struct_conn_candidate_extraction_smoke_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["candidate_rows"], gate.CANDIDATE_TABLE_CSV, gate.CANDIDATE_TABLE_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_struct_conn_candidate_extraction_smoke_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

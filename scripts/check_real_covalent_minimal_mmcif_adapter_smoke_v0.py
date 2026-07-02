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

from covalent_ext import real_covalent_minimal_mmcif_adapter_smoke as gate  # noqa: E402


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
        ("step12x_precondition", manifest["step12x_minimal_mmcif_adapter_design_gate_validated"]),
        ("adapter_smoke_execution", manifest["minimal_mmcif_adapter_smoke_executed"]),
        ("parser_summary_to_adapter_mapping", manifest["parser_metadata_mapped_to_adapter_summary"]),
        ("unresolved_schema_fields", manifest["all_unresolved_fields_set_to_unresolved"]),
        ("no_training_ready_claim", manifest["all_training_ready_false"]),
        ("output_artifact_policy", manifest["output_limited_to_csv_json_md"]),
        ("no_raw_no_parser_no_training_boundary", not manifest["raw_files_read"] and not manifest["mmcif_parsed"]),
        ("next_step_decision", manifest["real_covalent_minimal_mmcif_adapter_smoke_passed"]),
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
                "decision": "minimal adapter smoke satisfied" if passed else "minimal adapter smoke blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    no_parser_tools = f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    text = f"""# Real Covalent Minimal mmCIF Adapter Smoke v0 Summary

Step 12Y is an actual minimal mmCIF adapter smoke.

This step actually read the Step 12W extracted summary CSV and mapped parser metadata into a minimal adapter summary.
It did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
It did not use {no_parser_tools}.
It did not run coordinate geometry, UniProt/CD-HIT, NPZ reads, or training.

## Adapter Summary Rows
The smoke generated 3 minimal adapter summary rows:
- 6DI9
- 5F2E
- 6OIM

The adapter summary maps:
- sample_id
- pdb_id
- source_name
- source_stage
- raw_path
- entry_id
- data_block_id
- structure_title
- entity_count
- atom_site_row_count
- chem_comp_ids
- struct_conn_row_count
- covalent_connection_candidate_count
- covalent_annotation_status
- adapter_status

The smoke marks covalent_bond_atom_pair, residue/ligand atom annotation, coordinates, warhead_type, and pre/post reaction geometry as unresolved.
It does not claim samples are training-ready.
It did not write sample stub JSON and did not write enriched sample_index.

## Decision
- adapter_summary_row_count: {manifest["adapter_summary_row_count"]}
- unresolved_schema_field_count: {manifest["unresolved_schema_field_count"]}
- all_unresolved_fields_set_to_unresolved: {str(manifest["all_unresolved_fields_set_to_unresolved"]).lower()}
- all_training_ready_false: {str(manifest["all_training_ready_false"]).lower()}
- ready_for_struct_conn_candidate_extraction_smoke: {str(manifest["ready_for_struct_conn_candidate_extraction_smoke"]).lower()}
- recommended_next_step: real_covalent_struct_conn_candidate_extraction_smoke

Next step: `real_covalent_struct_conn_candidate_extraction_smoke`, which should actually extract candidate covalent linkage information from the mmCIF struct_conn loop.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_minimal_mmcif_adapter_smoke_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["adapter_rows"], gate.ADAPTER_SUMMARY_CSV, gate.ADAPTER_SUMMARY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_minimal_mmcif_adapter_smoke_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

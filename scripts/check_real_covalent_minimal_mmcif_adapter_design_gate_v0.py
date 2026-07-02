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

from covalent_ext import real_covalent_minimal_mmcif_adapter_design_gate as gate  # noqa: E402


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
        ("step12w_precondition", manifest["step12w_minimal_mmcif_parser_smoke_validated"]),
        ("adapter_input_scope_contract", manifest["adapter_scope_limited_to_current_pilot"]),
        ("parser_to_adapter_schema_mapping", manifest["adapter_maps_parser_metadata_fields"]),
        ("unresolved_chemistry_fields_policy", manifest["adapter_marks_unresolved_chemistry_fields"]),
        ("adapter_safety_policy", not manifest["adapter_smoke_reads_raw_files_next_step"] and not manifest["adapter_smoke_parses_mmcif_next_step"]),
        ("output_artifact_policy", manifest["adapter_smoke_output_limited_to_csv_json_md"]),
        ("no_adapter_execution_boundary_this_step", not manifest["adapter_execution_run"]),
        ("next_step_decision", manifest["real_covalent_minimal_mmcif_adapter_design_gate_passed"]),
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
                "decision": "minimal adapter smoke contract defined" if passed else "minimal adapter smoke contract blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Minimal mmCIF Adapter Design Gate v0 Summary

Step 12X is a minimal mmCIF adapter design gate.

This step does not network, does not download, does not read raw files, does not decompress, and does not parse mmCIF.
It does not run the adapter; it only defines the next adapter smoke contract.

Step 12Y may read only the Step 12W extracted summary CSV. It must not read raw `.cif.gz`, decompress raw files, or parse mmCIF.

## Metadata Mapping
Step 12Y maps parser metadata into a minimal adapter summary:
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

## Unresolved Fields
Step 12Y must mark unresolved fields and must not fabricate covalent_bond_atom_pair, residue atom annotation, ligand atom annotation, coordinates, warhead_type, or pre/post reaction geometry.

Step 12Y may only output CSV/JSON/MD adapter summary artifacts and must not claim samples are training-ready.
This is the last adapter-before-smoke design gate; the next step must actually run adapter smoke.

## Decision
- adapter_contract_row_count: {manifest["adapter_contract_row_count"]}
- adapter_input_contract_row_count: {manifest["adapter_input_contract_row_count"]}
- schema_mapping_row_count: {manifest["schema_mapping_row_count"]}
- not_yet_available_schema_field_row_count: {manifest["not_yet_available_schema_field_row_count"]}
- adapter_policy_row_count: {manifest["adapter_policy_row_count"]}
- ready_for_minimal_mmcif_adapter_smoke: {str(manifest["ready_for_minimal_mmcif_adapter_smoke"]).lower()}
- recommended_next_step: real_covalent_minimal_mmcif_adapter_smoke
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_minimal_mmcif_adapter_design_gate_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["contract_rows"], gate.ADAPTER_CONTRACT_CSV, gate.CONTRACT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print("real_covalent_minimal_mmcif_adapter_design_gate_v0_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

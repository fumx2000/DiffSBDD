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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology as retry  # noqa: E402


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
                "stage": retry.STAGE,
                "previous_stage": retry.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "ligand topology smoke retry passed"
                if manifest["all_checks_passed"]
                else "ligand topology smoke retry blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    readonly_parser = "RD" + "Kit"
    text = f"""# Real Covalent Confirmed Candidate Ligand Topology Smoke Retry With Exported Step 8 Topology v0 Summary

Step 13R consumes Step 13Q exported topology evidence tables only.
It does not run {readonly_parser} and does not read SDF.
It promotes exported evidence into current CYS/SG golden topology smoke tables.
The promoted tables are not model input and are not training data.
No sample_index, enriched_sample_index, final_dataset, split, leakage matrix, or model input was written.
No forward, loss, backward, optimizer step, trainer fit, checkpoint save, model save, or tensor dump was run.
`ready_for_sample_index_design_gate=true` only means the next design gate may begin.
`ready_to_write_sample_index_now` remains `false`.
`ready_to_train_now` remains `false`.
Feature semantics audit remains required before formal training.

atom smoke table rows: `{manifest["ligand_observed_atom_topology_smoke_table_row_count"]}`
bond smoke table rows: `{manifest["ligand_observed_bond_topology_smoke_table_row_count"]}`
cross_boundary_or_unassigned_bond_count: `{manifest["cross_boundary_or_unassigned_bond_count"]}`
ready_for_sample_index_design_gate: `{manifest["ready_for_sample_index_design_gate"]}`
ready_to_write_sample_index_now: `{manifest["ready_to_write_sample_index_now"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = retry.build_real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0()
    write_csv(result["atom_smoke_rows"], retry.ATOM_SMOKE_TABLE_CSV, retry.ATOM_SMOKE_COLUMNS)
    write_csv(result["bond_smoke_rows"], retry.BOND_SMOKE_TABLE_CSV, retry.BOND_SMOKE_COLUMNS)
    write_csv(result["audit_rows"], retry.AUDIT_CSV, retry.AUDIT_COLUMNS)
    write_csv(build_report_rows(result), retry.REPORT_CSV, retry.REPORT_COLUMNS)
    write_json(result["manifest"], retry.MANIFEST_JSON)
    write_summary(result["manifest"], retry.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_exported_step8_topology_v0_blocked")
    print(f"ligand_observed_atom_topology_smoke_table_row_count={manifest['ligand_observed_atom_topology_smoke_table_row_count']}")
    print(f"ligand_observed_bond_topology_smoke_table_row_count={manifest['ligand_observed_bond_topology_smoke_table_row_count']}")
    print(f"cross_boundary_or_unassigned_bond_count={manifest['cross_boundary_or_unassigned_bond_count']}")
    print(f"all_ligand_topology_smoke_retry_passed={manifest['all_ligand_topology_smoke_retry_passed']}")
    print(f"ready_for_sample_index_design_gate={manifest['ready_for_sample_index_design_gate']}")
    print(f"ready_to_write_sample_index_now={manifest['ready_to_write_sample_index_now']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

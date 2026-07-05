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

from covalent_ext import real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke as smoke  # noqa: E402


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
                "stage": smoke.STAGE,
                "previous_stage": smoke.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "readonly Step 8 topology evidence export smoke passed"
                if manifest["all_checks_passed"]
                else "readonly Step 8 topology evidence export smoke blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Step 8 Readonly Topology Evidence Export Smoke v0 Summary

Step 13Q is a read-only RDKit topology evidence export smoke.
It only reads the three Step 8 manual-reviewed pre-reaction SDF files listed in the Step 13P candidate contract.
It does not glob extra SDF files and does not read raw `.cif.gz` or parse mmCIF.
It uses RDKit only for read-only SDF topology export.
It does not generate, modify, or copy SDF files.
It does not automatically restore ligands.
It does not generalize the current CYS/SG golden sample scope to non-CYS residues.
It writes exported Step 8 evidence tables, not final ligand topology or training tables.
`ligand_topology_table_written` remains `false`.
No sample_index, final_dataset, or model input was written.
No forward, loss, backward, optimizer step, trainer fit, checkpoint save, model save, or tensor dump was run.
Feature semantics audit is still required before formal training.

atom topology evidence rows: `{manifest["atom_topology_table_row_count"]}`
bond topology evidence rows: `{manifest["bond_topology_table_row_count"]}`
ready_for_ligand_topology_smoke_retry: `{manifest["ready_for_ligand_topology_smoke_retry"]}`
ready_for_sample_index_design_gate: `{manifest["ready_for_sample_index_design_gate"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.build_real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0()
    write_csv(result["atom_rows"], smoke.ATOM_TOPOLOGY_TABLE_CSV, smoke.ATOM_TOPOLOGY_COLUMNS)
    write_csv(result["bond_rows"], smoke.BOND_TOPOLOGY_TABLE_CSV, smoke.BOND_TOPOLOGY_COLUMNS)
    write_csv(result["audit_rows"], smoke.EXPORT_AUDIT_CSV, smoke.EXPORT_AUDIT_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_step8_readonly_topology_evidence_export_smoke_v0_blocked")
    print(f"atom_topology_table_row_count={manifest['atom_topology_table_row_count']}")
    print(f"bond_topology_table_row_count={manifest['bond_topology_table_row_count']}")
    print(f"all_readonly_exports_passed={manifest['all_readonly_exports_passed']}")
    print(f"ready_for_ligand_topology_smoke_retry={manifest['ready_for_ligand_topology_smoke_retry']}")
    print(f"ready_for_sample_index_design_gate={manifest['ready_for_sample_index_design_gate']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

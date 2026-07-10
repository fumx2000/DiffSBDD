#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_preparation_execution_smoke as gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
    return value


def atomic_write_text(path: str | Path, text: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, output)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})
    os.replace(tmp, output)


def write_json(data: Any, path: str | Path) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    accepted = ", ".join(manifest["accepted_pdb_het_pairs"])
    text = f"""# CovaPIE Sample Preparation Execution Smoke v0 Summary

Step 14AA executes sample preparation smoke for the three Step 14Z small pilot inputs.

This step reads ignored raw CIF/mmCIF files, parses atom_site and struct_conn, and writes per-sample protein, ligand, pocket, covalent event, and ligand-residue atom-pair CSV tables.

It is not a sample index, not a final dataset, not a dataloader smoke, and not a training sample.

input_sample_preparation_count: `{manifest["input_sample_preparation_count"]}`
sample_execution_count: `{manifest["sample_execution_count"]}`
sample_preparation_passed_count: `{manifest["sample_preparation_passed_count"]}`
raw_file_resolved_count: `{manifest["raw_file_resolved_count"]}`
protein_atom_table_written_count: `{manifest["protein_atom_table_written_count"]}`
ligand_atom_table_written_count: `{manifest["ligand_atom_table_written_count"]}`
pocket_atom_table_written_count: `{manifest["pocket_atom_table_written_count"]}`
covalent_event_table_written_count: `{manifest["covalent_event_table_written_count"]}`
ligand_residue_atom_pair_table_written_count: `{manifest["ligand_residue_atom_pair_table_written_count"]}`
accepted_pdb_het_pairs: `{accepted}`
ready_for_covapie_sample_preparation_qa_gate: `{manifest["ready_for_covapie_sample_preparation_qa_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def write_sample_artifacts(result: dict[str, Any]) -> None:
    for sample_result in result["sample_results"]:
        sample = sample_result["sample"]
        root = gate.OUTPUT_ROOT / "samples" / f"{sample['pdb_id']}_{sample['expected_het_id']}"
        write_csv(sample_result["protein_rows"], root / "protein_atom_table.csv", gate.PROTEIN_ATOM_COLUMNS)
        write_csv(sample_result["ligand_rows"], root / "ligand_atom_table.csv", gate.LIGAND_ATOM_COLUMNS)
        write_csv(sample_result["pocket_rows"], root / "pocket_atom_table.csv", gate.POCKET_ATOM_COLUMNS)
        write_csv(sample_result["event_rows"], root / "covalent_event_table.csv", gate.COVALENT_EVENT_COLUMNS)
        write_csv(sample_result["pair_rows"], root / "ligand_residue_atom_pair_table.csv", gate.PAIR_TABLE_COLUMNS)
        write_csv(sample_result["audit_rows"], root / "sample_preparation_audit.csv", gate.SAMPLE_AUDIT_COLUMNS)


def run() -> int:
    result = gate.run_covapie_sample_preparation_execution_smoke_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["execution_rows"], gate.EXECUTION_MANIFEST_CSV, gate.EXECUTION_MANIFEST_COLUMNS)
    write_json(result["execution_rows"], gate.EXECUTION_MANIFEST_JSON)
    write_csv(result["sample_inventory_rows"], gate.SAMPLE_INVENTORY_CSV, gate.SAMPLE_INVENTORY_COLUMNS)
    write_json(result["sample_inventory_rows"], gate.SAMPLE_INVENTORY_JSON)
    write_csv(result["traceability_rows"], gate.TRACEABILITY_AUDIT_CSV, gate.TRACEABILITY_COLUMNS)
    write_csv(result["quality_rows"], gate.QUALITY_AUDIT_CSV, gate.QUALITY_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_sample_artifacts(result)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_sample_preparation_execution_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_preparation_execution_smoke_v0_blocked")
    for key in [
        "input_sample_preparation_count",
        "sample_execution_count",
        "sample_preparation_passed_count",
        "raw_file_resolved_count",
        "protein_atom_table_written_count",
        "ligand_atom_table_written_count",
        "pocket_atom_table_written_count",
        "covalent_event_table_written_count",
        "ligand_residue_atom_pair_table_written_count",
        "accepted_pdb_het_pairs",
        "ready_for_covapie_sample_preparation_qa_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

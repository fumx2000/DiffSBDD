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

from covalent_ext import covapie_extraction_qa_gate as qa_gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE Extraction QA Gate v0 Summary

Step 13BF is an extraction QA gate for the Step 13BE derived extraction tables.
It reads only Step 13BE/13BD CSV and JSON artifacts and does not read raw CIF files, parse mmCIF, scan atom_site/struct_conn, or re-extract coordinates.
It validates event table schema and identity, atom table schema and endpoint coverage, geometry recomputation, traceability, boundary safety, git safety, and training blockers.
It does not write sample_index, final_dataset, split assignments, leakage matrix, or training inputs.
It does not use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows the sample index design gate next, not sample index smoke and not training.

source_extracted_event_row_count: `{manifest["source_extracted_event_row_count"]}`
source_extracted_event_column_count: `{manifest["source_extracted_event_column_count"]}`
source_protein_pocket_atom_row_count: `{manifest["source_protein_pocket_atom_row_count"]}`
source_ligand_atom_row_count: `{manifest["source_ligand_atom_row_count"]}`
extracted_event_table_qa_passed: `{manifest["extracted_event_table_qa_passed"]}`
extracted_atom_table_qa_passed: `{manifest["extracted_atom_table_qa_passed"]}`
geometry_qa_passed: `{manifest["geometry_qa_passed"]}`
traceability_qa_passed: `{manifest["traceability_qa_passed"]}`
raw_data_read: `{manifest["raw_data_read"]}`
mmcif_parse_current_step: `{manifest["mmcif_parse_current_step"]}`
ready_for_covapie_sample_index_design_gate: `{manifest["ready_for_covapie_sample_index_design_gate"]}`
ready_for_covapie_sample_index_smoke: `{manifest["ready_for_covapie_sample_index_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa_gate.run_covapie_extraction_qa_gate_v0()
    write_csv(result["precondition_rows"], qa_gate.PRECONDITION_AUDIT_CSV, qa_gate.PRECONDITION_COLUMNS)
    write_csv(result["event_qa_rows"], qa_gate.EVENT_TABLE_QA_CSV, qa_gate.EVENT_QA_COLUMNS)
    write_csv(result["atom_qa_rows"], qa_gate.ATOM_TABLE_QA_CSV, qa_gate.ATOM_QA_COLUMNS)
    write_csv(result["geometry_qa_rows"], qa_gate.GEOMETRY_QA_CSV, qa_gate.GEOMETRY_QA_COLUMNS)
    write_csv(result["traceability_rows"], qa_gate.TRACEABILITY_QA_CSV, qa_gate.TRACEABILITY_QA_COLUMNS)
    write_csv(result["boundary_rows"], qa_gate.BOUNDARY_SAFETY_CSV, qa_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa_gate.GIT_SAFETY_CSV, qa_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], qa_gate.TRAINING_BLOCKERS_CSV, qa_gate.TRAINING_BLOCKER_COLUMNS)
    write_json(result["manifest"], qa_gate.MANIFEST_JSON)
    write_summary(result["manifest"], qa_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_extraction_qa_gate_v0_passed")
    else:
        print("covapie_extraction_qa_gate_v0_blocked")
    for key in [
        "source_extracted_event_row_count",
        "source_extracted_event_column_count",
        "source_protein_pocket_atom_row_count",
        "source_ligand_atom_row_count",
        "extracted_event_table_qa_passed",
        "extracted_atom_table_qa_passed",
        "geometry_qa_passed",
        "traceability_qa_passed",
        "ready_for_covapie_sample_index_design_gate",
        "ready_for_covapie_sample_index_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

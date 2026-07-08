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

from covalent_ext import covapie_batch_raw_read_extraction_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE Batch Raw Read Extraction Smoke v0 Summary

Step 13BE is the first controlled raw read / extraction smoke for the four CovaPIE allowlist CIF files.
It reads only the four allowlist raw `.cif` files, parses `_atom_site` and `_struct_conn` with a small Python standard-library parser, extracts event rows, writes protein pocket atom rows, and writes ligand atom rows.
It does not download raw data, create or copy raw files, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This smoke allows the extraction QA gate next, not sample index design and not training.

raw_file_read_count: `{manifest["raw_file_read_count"]}`
extracted_event_table_row_count: `{manifest["extracted_event_table_row_count"]}`
extracted_protein_pocket_atom_row_count: `{manifest["extracted_protein_pocket_atom_row_count"]}`
extracted_ligand_atom_row_count: `{manifest["extracted_ligand_atom_row_count"]}`
extraction_success_count: `{manifest["extraction_success_count"]}`
extraction_blocked_count: `{manifest["extraction_blocked_count"]}`
covalent_connection_found_count: `{manifest["covalent_connection_found_count"]}`
residue_atom_found_count: `{manifest["residue_atom_found_count"]}`
ligand_atom_found_count: `{manifest["ligand_atom_found_count"]}`
raw_data_read: `{manifest["raw_data_read"]}`
mmcif_text_read: `{manifest["mmcif_text_read"]}`
sample_index_written: `{manifest["sample_index_written"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
ready_for_covapie_extraction_qa_gate: `{manifest["ready_for_covapie_extraction_qa_gate"]}`
ready_for_sample_index_design_gate: `{manifest["ready_for_sample_index_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_batch_raw_read_extraction_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["raw_read_rows"], smoke.RAW_READ_AUDIT_CSV, smoke.RAW_READ_COLUMNS)
    write_csv(result["parse_rows"], smoke.MMCIF_LOOP_PARSE_AUDIT_CSV, smoke.MMCIF_PARSE_COLUMNS)
    write_csv(result["event_rows"], smoke.EXTRACTED_EVENT_TABLE_CSV, smoke.EVENT_FIELDS)
    write_csv(result["protein_rows"], smoke.EXTRACTED_PROTEIN_ATOM_TABLE_CSV, smoke.ATOM_FIELDS)
    write_csv(result["ligand_rows"], smoke.EXTRACTED_LIGAND_ATOM_TABLE_CSV, smoke.ATOM_FIELDS)
    write_csv(result["qa_rows"], smoke.EXTRACTION_QA_AUDIT_CSV, smoke.EXTRACTION_QA_COLUMNS)
    write_csv(result["boundary_rows"], smoke.BOUNDARY_SAFETY_CSV, smoke.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_batch_raw_read_extraction_smoke_v0_passed")
    else:
        print("covapie_batch_raw_read_extraction_smoke_v0_blocked")
    for key in [
        "raw_file_read_count",
        "extracted_event_table_row_count",
        "extracted_protein_pocket_atom_row_count",
        "extracted_ligand_atom_row_count",
        "extraction_success_count",
        "extraction_blocked_count",
        "covalent_connection_found_count",
        "residue_atom_found_count",
        "ligand_atom_found_count",
        "ready_for_covapie_extraction_qa_gate",
        "ready_for_sample_index_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_batch_raw_read_extraction_design_gate as design_gate  # noqa: E402


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
    text = f"""# CovaPIE Batch Raw Read Extraction Design Gate v0 Summary

Step 13BD is a design gate for a future batch raw read / extraction smoke step.
It designs contracts for reading raw `.cif` files later, extracting event-level records later, and writing atom-level smoke tables later.
It does not read raw file content, parse mmCIF text, scan `atom_site` or `struct_conn`, extract coordinates, write extracted event or atom tables, write sample_index/final_dataset/split/leakage artifacts, or train.
The current step only checks raw file path existence and git tracking/staging status without opening raw files.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows `covapie_batch_raw_read_extraction_smoke` next, not extraction QA, not sample_index design, and not training.

source_allowlist_row_count: `{manifest["source_allowlist_row_count"]}`
batch_raw_read_input_contract_row_count: `{manifest["batch_raw_read_input_contract_row_count"]}`
raw_file_path_contract_row_count: `{manifest["raw_file_path_contract_row_count"]}`
raw_file_path_exists_count: `{manifest["raw_file_path_exists_count"]}`
extracted_event_schema_field_count: `{manifest["extracted_event_schema_field_count"]}`
extracted_atom_schema_row_count: `{manifest["extracted_atom_schema_row_count"]}`
raw_read_extraction_smoke_plan_row_count: `{manifest["raw_read_extraction_smoke_plan_row_count"]}`
raw_file_content_read_current_step: `{manifest["raw_file_content_read_current_step"]}`
mmcif_parse_current_step: `{manifest["mmcif_parse_current_step"]}`
atom_site_scan_current_step: `{manifest["atom_site_scan_current_step"]}`
struct_conn_scan_current_step: `{manifest["struct_conn_scan_current_step"]}`
coordinate_extraction_current_step: `{manifest["coordinate_extraction_current_step"]}`
extracted_event_table_written: `{manifest["extracted_event_table_written"]}`
extracted_atom_table_written: `{manifest["extracted_atom_table_written"]}`
ready_for_covapie_batch_raw_read_extraction_smoke: `{manifest["ready_for_covapie_batch_raw_read_extraction_smoke"]}`
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
    result = design_gate.run_covapie_batch_raw_read_extraction_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["input_rows"], design_gate.INPUT_CONTRACT_CSV, design_gate.INPUT_COLUMNS)
    write_csv(result["raw_path_rows"], design_gate.RAW_FILE_PATH_CONTRACT_CSV, design_gate.RAW_PATH_COLUMNS)
    write_csv(result["event_schema_rows"], design_gate.EXTRACTED_EVENT_SCHEMA_CONTRACT_CSV, design_gate.EVENT_SCHEMA_COLUMNS)
    write_csv(result["atom_schema_rows"], design_gate.EXTRACTED_ATOM_SCHEMA_CONTRACT_CSV, design_gate.ATOM_SCHEMA_COLUMNS)
    write_csv(result["plan_rows"], design_gate.SMOKE_PLAN_CSV, design_gate.PLAN_COLUMNS)
    write_csv(result["boundary_rows"], design_gate.BOUNDARY_SAFETY_CSV, design_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], design_gate.GIT_SAFETY_CSV, design_gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_batch_raw_read_extraction_design_gate_v0_passed")
    else:
        print("covapie_batch_raw_read_extraction_design_gate_v0_blocked")
    for key in [
        "batch_raw_read_input_contract_row_count",
        "raw_file_path_contract_row_count",
        "raw_file_path_exists_count",
        "extracted_event_schema_field_count",
        "extracted_atom_schema_row_count",
        "raw_read_extraction_smoke_plan_row_count",
        "raw_file_content_read_current_step",
        "mmcif_parse_current_step",
        "atom_site_scan_current_step",
        "struct_conn_scan_current_step",
        "coordinate_extraction_current_step",
        "extracted_event_table_written",
        "extracted_atom_table_written",
        "ready_for_covapie_batch_raw_read_extraction_smoke",
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

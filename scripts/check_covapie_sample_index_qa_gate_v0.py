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

from covalent_ext import covapie_sample_index_qa_gate as qa_gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
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
    text = f"""# CovaPIE Sample Index QA Gate v0 Summary

Step 13BI is a QA gate for the Step 13BH 20-row sample index smoke.
It reads but does not modify the Step 13BH sample index CSV/JSON.
It validates schema order, CSV/JSON consistency, sample identity, mask distribution, source traceability, boundary safety, git safety, and training blockers.
It does not write a new sample index, final_dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF files, parse mmCIF, re-extract coordinates, use network, RDKit, Bio.PDB, gemmi, gzip, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows split/leakage design gate next, not final dataset, not dataloader smoke, and not training.

source_sample_index_row_count: `{manifest["source_sample_index_row_count"]}`
source_sample_index_column_count: `{manifest["source_sample_index_column_count"]}`
source_sample_index_json_row_count: `{manifest["source_sample_index_json_row_count"]}`
source_unique_event_count: `{manifest["source_unique_event_count"]}`
source_sample_id_unique_count: `{manifest["source_sample_id_unique_count"]}`
source_canonical_mask_task_count: `{manifest["source_canonical_mask_task_count"]}`
schema_csv_json_qa_passed: `{manifest["schema_csv_json_qa_passed"]}`
row_identity_qa_passed: `{manifest["row_identity_qa_passed"]}`
mask_distribution_qa_passed: `{manifest["mask_distribution_qa_passed"]}`
source_traceability_qa_passed: `{manifest["source_traceability_qa_passed"]}`
boundary_safety_passed: `{manifest["boundary_safety_passed"]}`
git_safety_passed: `{manifest["git_safety_passed"]}`
training_blockers_passed: `{manifest["training_blockers_passed"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
ready_for_covapie_split_leakage_design_gate: `{manifest["ready_for_covapie_split_leakage_design_gate"]}`
ready_for_covapie_final_dataset_design_gate: `{manifest["ready_for_covapie_final_dataset_design_gate"]}`
ready_for_covapie_dataloader_smoke: `{manifest["ready_for_covapie_dataloader_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa_gate.run_covapie_sample_index_qa_gate_v0()
    write_csv(result["precondition_rows"], qa_gate.PRECONDITION_AUDIT_CSV, qa_gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_rows"], qa_gate.SCHEMA_CSV_JSON_QA_AUDIT_CSV, qa_gate.SCHEMA_QA_COLUMNS)
    write_csv(result["row_identity_rows"], qa_gate.ROW_IDENTITY_QA_AUDIT_CSV, qa_gate.ROW_IDENTITY_COLUMNS)
    write_csv(result["mask_distribution_rows"], qa_gate.MASK_DISTRIBUTION_QA_AUDIT_CSV, qa_gate.MASK_DISTRIBUTION_COLUMNS)
    write_csv(result["traceability_rows"], qa_gate.SOURCE_TRACEABILITY_QA_AUDIT_CSV, qa_gate.SOURCE_TRACEABILITY_COLUMNS)
    write_csv(result["boundary_rows"], qa_gate.BOUNDARY_SAFETY_CSV, qa_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa_gate.GIT_SAFETY_CSV, qa_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], qa_gate.TRAINING_BLOCKERS_CSV, qa_gate.TRAINING_BLOCKER_COLUMNS)
    write_json(result["manifest"], qa_gate.MANIFEST_JSON)
    write_summary(result["manifest"], qa_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_sample_index_qa_gate_v0_passed")
    else:
        print("covapie_sample_index_qa_gate_v0_blocked")
    for key in [
        "source_sample_index_row_count",
        "source_sample_index_column_count",
        "source_sample_index_json_row_count",
        "source_unique_event_count",
        "source_sample_id_unique_count",
        "source_canonical_mask_task_count",
        "schema_csv_json_qa_passed",
        "row_identity_qa_passed",
        "mask_distribution_qa_passed",
        "source_traceability_qa_passed",
        "boundary_safety_passed",
        "git_safety_passed",
        "training_blockers_passed",
        "sample_index_written_current_step",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "ready_for_covapie_split_leakage_design_gate",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

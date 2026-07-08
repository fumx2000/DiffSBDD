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

from covalent_ext import covapie_final_dataset_qa_gate as qa_gate  # noqa: E402


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
    text = f"""# CovaPIE Final Dataset QA Gate v0 Summary

Step 13BP is a final dataset smoke preview QA gate only.
It reads the Step 13BO 20-row / 45-column CSV/JSON smoke preview and validates schema order, CSV/JSON consistency, row lineage, mask distribution, feature blockers, readiness, and safety boundaries.
It does not rewrite the Step 13BO smoke preview.
It does not write real `final_dataset.csv/json`, generic `final_dataset_smoke.csv/json`, a new sample index, split assignments, a leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF/mmCIF/SDF/PDB/gzip, parse atom_site/struct_conn, extract coordinates, access network, download data, run RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics and leakage/split blockers remain required before formal training, fine-tuning, or real parameter updates.
This QA gate allows the dataloader interface design gate next, not dataloader smoke and not training.

source_preview_row_count: `{manifest["source_preview_row_count"]}`
source_preview_column_count: `{manifest["source_preview_column_count"]}`
source_preview_json_row_count: `{manifest["source_preview_json_row_count"]}`
schema_order_qa_row_count: `{manifest["schema_order_qa_row_count"]}`
schema_order_qa_passed: `{manifest["schema_order_qa_passed"]}`
csv_json_consistency_qa_passed: `{manifest["csv_json_consistency_qa_passed"]}`
row_lineage_qa_row_count: `{manifest["row_lineage_qa_row_count"]}`
row_lineage_qa_passed: `{manifest["row_lineage_qa_passed"]}`
mask_distribution_qa_row_count: `{manifest["mask_distribution_qa_row_count"]}`
mask_distribution_qa_passed: `{manifest["mask_distribution_qa_passed"]}`
feature_blocker_qa_row_count: `{manifest["feature_blocker_qa_row_count"]}`
feature_blocker_qa_passed: `{manifest["feature_blocker_qa_passed"]}`
readiness_qa_row_count: `{manifest["readiness_qa_row_count"]}`
readiness_qa_passed: `{manifest["readiness_qa_passed"]}`
final_dataset_smoke_preview_written_current_step: `{manifest["final_dataset_smoke_preview_written_current_step"]}`
real_final_dataset_written: `{manifest["real_final_dataset_written"]}`
generic_final_dataset_written: `{manifest["generic_final_dataset_written"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
dataloader_smoke_written: `{manifest["dataloader_smoke_written"]}`
training_artifacts_written: `{manifest["training_artifacts_written"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
ready_for_covapie_dataloader_interface_design_gate: `{manifest["ready_for_covapie_dataloader_interface_design_gate"]}`
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
    result = qa_gate.run_covapie_final_dataset_qa_gate_v0()
    write_csv(result["precondition_rows"], qa_gate.PRECONDITION_AUDIT_CSV, qa_gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_rows"], qa_gate.SCHEMA_ORDER_QA_CSV, qa_gate.SCHEMA_ORDER_QA_COLUMNS)
    write_csv(result["consistency_rows"], qa_gate.CSV_JSON_CONSISTENCY_QA_CSV, qa_gate.CSV_JSON_CONSISTENCY_QA_COLUMNS)
    write_csv(result["lineage_rows"], qa_gate.ROW_LINEAGE_QA_CSV, qa_gate.ROW_LINEAGE_QA_COLUMNS)
    write_csv(result["mask_rows"], qa_gate.MASK_DISTRIBUTION_QA_CSV, qa_gate.MASK_DISTRIBUTION_QA_COLUMNS)
    write_csv(result["blocker_rows"], qa_gate.FEATURE_BLOCKER_QA_CSV, qa_gate.FEATURE_BLOCKER_QA_COLUMNS)
    write_csv(result["readiness_rows"], qa_gate.READINESS_QA_CSV, qa_gate.READINESS_QA_COLUMNS)
    write_csv(result["boundary_rows"], qa_gate.BOUNDARY_SAFETY_CSV, qa_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa_gate.GIT_SAFETY_CSV, qa_gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], qa_gate.MANIFEST_JSON)
    write_summary(result["manifest"], qa_gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_final_dataset_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_final_dataset_qa_gate_v0_blocked")
    for key in [
        "source_preview_row_count",
        "source_preview_column_count",
        "source_preview_json_row_count",
        "schema_order_qa_row_count",
        "schema_order_qa_passed",
        "csv_json_consistency_qa_passed",
        "row_lineage_qa_row_count",
        "row_lineage_qa_passed",
        "mask_distribution_qa_row_count",
        "mask_distribution_qa_passed",
        "feature_blocker_qa_row_count",
        "feature_blocker_qa_passed",
        "readiness_qa_row_count",
        "readiness_qa_passed",
        "final_dataset_smoke_preview_written_current_step",
        "real_final_dataset_written",
        "generic_final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "raw_data_read",
        "network_access_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "ready_for_covapie_dataloader_interface_design_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

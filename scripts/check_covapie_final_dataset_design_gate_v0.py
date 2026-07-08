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

from covalent_ext import covapie_final_dataset_design_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Final Dataset Design Gate v0 Summary

Step 13BN is a final dataset design gate.
It designs the final dataset schema, row lineage contract, future materialization plan, feature requirement contract, split policy contract, and final dataset smoke plan.
It does not write `final_dataset.csv`, `final_dataset.json`, a final dataset smoke artifact, a new sample index, real split assignments, a leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It reads only derived Step 13BM/13BL/13BK/13BH/13BE CSV/JSON artifacts.
It does not read raw CIF/mmCIF/SDF/PDB/gzip, parse atom_site/struct_conn, extract coordinates, access network, download data, run RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
The five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Feature semantics and leakage/split blockers remain preserved before formal training, fine-tuning, or real parameter updates.
This design gate allows a final dataset smoke step next, not final dataset QA, not dataloader smoke, and not training.

source_sample_index_row_count: `{manifest["source_sample_index_row_count"]}`
source_unique_event_count: `{manifest["source_unique_event_count"]}`
source_canonical_mask_task_count: `{manifest["source_canonical_mask_task_count"]}`
source_split_unit_preview_row_count: `{manifest["source_split_unit_preview_row_count"]}`
final_dataset_schema_contract_row_count: `{manifest["final_dataset_schema_contract_row_count"]}`
final_dataset_row_lineage_contract_row_count: `{manifest["final_dataset_row_lineage_contract_row_count"]}`
final_dataset_materialization_plan_row_count: `{manifest["final_dataset_materialization_plan_row_count"]}`
final_dataset_feature_requirement_contract_row_count: `{manifest["final_dataset_feature_requirement_contract_row_count"]}`
final_dataset_split_policy_contract_row_count: `{manifest["final_dataset_split_policy_contract_row_count"]}`
final_dataset_smoke_plan_row_count: `{manifest["final_dataset_smoke_plan_row_count"]}`
final_dataset_design_completed_current_step: `{manifest["final_dataset_design_completed_current_step"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
final_dataset_smoke_written: `{manifest["final_dataset_smoke_written"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
ready_for_covapie_final_dataset_smoke: `{manifest["ready_for_covapie_final_dataset_smoke"]}`
ready_for_covapie_final_dataset_qa_gate: `{manifest["ready_for_covapie_final_dataset_qa_gate"]}`
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
    result = gate.run_covapie_final_dataset_design_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_rows"], gate.SCHEMA_CONTRACT_CSV, gate.SCHEMA_COLUMNS)
    write_csv(result["lineage_rows"], gate.ROW_LINEAGE_CONTRACT_CSV, gate.ROW_LINEAGE_COLUMNS)
    write_csv(result["materialization_rows"], gate.MATERIALIZATION_PLAN_CSV, gate.MATERIALIZATION_PLAN_COLUMNS)
    write_csv(result["feature_requirement_rows"], gate.FEATURE_REQUIREMENT_CONTRACT_CSV, gate.FEATURE_REQUIREMENT_COLUMNS)
    write_csv(result["split_policy_rows"], gate.SPLIT_POLICY_CONTRACT_CSV, gate.SPLIT_POLICY_COLUMNS)
    write_csv(result["smoke_plan_rows"], gate.SMOKE_PLAN_CSV, gate.SMOKE_PLAN_COLUMNS)
    write_csv(result["boundary_rows"], gate.BOUNDARY_SAFETY_CSV, gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], gate.GIT_SAFETY_CSV, gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_final_dataset_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_final_dataset_design_gate_v0_blocked")
    for key in [
        "source_sample_index_row_count",
        "source_unique_event_count",
        "source_canonical_mask_task_count",
        "source_split_unit_preview_row_count",
        "final_dataset_schema_contract_row_count",
        "final_dataset_row_lineage_contract_row_count",
        "final_dataset_materialization_plan_row_count",
        "final_dataset_feature_requirement_contract_row_count",
        "final_dataset_split_policy_contract_row_count",
        "final_dataset_smoke_plan_row_count",
        "final_dataset_schema_contract_passed",
        "final_dataset_row_lineage_contract_passed",
        "final_dataset_materialization_plan_passed",
        "final_dataset_feature_requirement_contract_passed",
        "final_dataset_split_policy_contract_passed",
        "final_dataset_smoke_plan_passed",
        "final_dataset_design_completed_current_step",
        "final_dataset_written",
        "final_dataset_smoke_written",
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
        "ready_for_covapie_final_dataset_smoke",
        "ready_for_covapie_final_dataset_qa_gate",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

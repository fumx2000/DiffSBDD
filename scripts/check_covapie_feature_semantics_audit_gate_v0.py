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

from covalent_ext import covapie_feature_semantics_audit_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Feature Semantics Audit Gate v0 Summary

Step 13BM is a feature semantics audit gate after the split/leakage QA gate.
It reads derived CSV/JSON artifacts and static source text only.
It records current feature semantics for sample identity, event identity, ligand/protein atom sources, coordinates, canonical masks, conditioning, auxiliary labels, training blockers, and git safety.
It does not write final_dataset, a new sample_index, split assignments, a leakage matrix, dataloader smoke, tensors, checkpoints, or training outputs.
It does not read raw CIF/mmCIF/SDF/PDB/gzip, parse atom_site/struct_conn, run RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.
All five canonical masks remain unchanged, including `scaffold_only / B3`; no sixth mask is introduced.
Step 12D remains recorded as smoke legality only, not final feature semantics audit.
This gate allows CovaPIE final dataset design gate next, not final dataset smoke, dataloader smoke, or training.
Feature semantics are audited at the current contract level, but `feature_semantics_known_for_training` remains false and training remains blocked.

source_sample_index_row_count: `{manifest["source_sample_index_row_count"]}`
source_unique_event_count: `{manifest["source_unique_event_count"]}`
source_canonical_mask_task_count: `{manifest["source_canonical_mask_task_count"]}`
feature_source_inventory_audit_row_count: `{manifest["feature_source_inventory_audit_row_count"]}`
feature_semantics_contract_row_count: `{manifest["feature_semantics_contract_row_count"]}`
coordinate_geometry_semantics_audit_row_count: `{manifest["coordinate_geometry_semantics_audit_row_count"]}`
mask_conditioning_semantics_audit_row_count: `{manifest["mask_conditioning_semantics_audit_row_count"]}`
auxiliary_label_semantics_audit_row_count: `{manifest["auxiliary_label_semantics_audit_row_count"]}`
feature_semantics_training_blocker_row_count: `{manifest["feature_semantics_training_blocker_row_count"]}`
feature_semantics_audit_completed_current_step: `{manifest["feature_semantics_audit_completed_current_step"]}`
feature_semantics_known_for_training: `{manifest["feature_semantics_known_for_training"]}`
unknown_atom_feature_policy_finalized_for_training: `{manifest["unknown_atom_feature_policy_finalized_for_training"]}`
final_dataset_written: `{manifest["final_dataset_written"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
split_assignments_written: `{manifest["split_assignments_written"]}`
leakage_matrix_written: `{manifest["leakage_matrix_written"]}`
dataloader_smoke_written: `{manifest["dataloader_smoke_written"]}`
training_artifacts_written: `{manifest["training_artifacts_written"]}`
ready_for_covapie_final_dataset_design_gate: `{manifest["ready_for_covapie_final_dataset_design_gate"]}`
ready_for_covapie_final_dataset_smoke: `{manifest["ready_for_covapie_final_dataset_smoke"]}`
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
    result = gate.run_covapie_feature_semantics_audit_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["source_inventory_rows"], gate.SOURCE_INVENTORY_AUDIT_CSV, gate.SOURCE_INVENTORY_COLUMNS)
    write_csv(result["feature_semantics_contract_rows"], gate.FEATURE_SEMANTICS_CONTRACT_CSV, gate.FEATURE_CONTRACT_COLUMNS)
    write_csv(result["coordinate_geometry_rows"], gate.COORDINATE_GEOMETRY_AUDIT_CSV, gate.GEOMETRY_COLUMNS)
    write_csv(result["mask_conditioning_rows"], gate.MASK_CONDITIONING_AUDIT_CSV, gate.MASK_CONDITIONING_COLUMNS)
    write_csv(result["auxiliary_label_rows"], gate.AUXILIARY_LABEL_AUDIT_CSV, gate.AUXILIARY_COLUMNS)
    write_csv(result["training_blocker_rows"], gate.TRAINING_BLOCKERS_CSV, gate.TRAINING_BLOCKER_COLUMNS)
    write_csv(result["boundary_rows"], gate.BOUNDARY_SAFETY_CSV, gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], gate.GIT_SAFETY_CSV, gate.GIT_SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_feature_semantics_audit_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_feature_semantics_audit_gate_v0_blocked")
    for key in [
        "source_sample_index_row_count",
        "source_unique_event_count",
        "source_canonical_mask_task_count",
        "feature_source_inventory_audit_row_count",
        "feature_semantics_contract_row_count",
        "coordinate_geometry_semantics_audit_row_count",
        "mask_conditioning_semantics_audit_row_count",
        "auxiliary_label_semantics_audit_row_count",
        "feature_semantics_training_blocker_row_count",
        "feature_source_inventory_audit_passed",
        "feature_semantics_contract_passed",
        "coordinate_geometry_semantics_audit_passed",
        "mask_conditioning_semantics_audit_passed",
        "auxiliary_label_semantics_audit_passed",
        "feature_semantics_training_blockers_passed",
        "feature_semantics_audit_completed_current_step",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "step12d_was_smoke_legality_only",
        "final_dataset_written",
        "sample_index_written_current_step",
        "split_assignments_written",
        "leakage_matrix_written",
        "dataloader_smoke_written",
        "training_artifacts_written",
        "raw_data_read",
        "network_access_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "torch_imported",
        "ready_for_covapie_final_dataset_design_gate",
        "ready_for_covapie_final_dataset_smoke",
        "ready_for_covapie_dataloader_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

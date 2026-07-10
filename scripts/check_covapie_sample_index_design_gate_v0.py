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

from covalent_ext import covapie_sample_index_design_gate as design_gate  # noqa: E402


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
    text = f"""# CovaPIE Sample Index Design Gate v0 Summary

Step 14AC is a design gate for a future sample index materialization smoke.
It reads only Step 14AB QA-passed derived outputs and Step 14AA derived sample-preparation outputs.
It defines the source inventory, 33-field sample-index schema contract, field mapping, per-sample materialization plan, policy, safety, and downstream readiness contracts.

This step does not write `sample_index.csv` or `sample_index.json`.
It does not create a final dataset, split assignments, leakage matrix, dataloader smoke, tensors, checkpoints, or training artifacts.
It does not read raw mmCIF, parse raw `struct_conn` or `atom_site`, modify atom/event tables, use network, RDKit, Bio.PDB, gemmi, torch, model forward, loss, backward, optimizer, trainer.fit, or training.

The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics remain unknown for formal training, `UNKNOWN_ATOM_FEATURE_POLICY` remains not finalized for training, and feature-semantics audit plus leakage/split design remain required before formal training, fine-tuning, or real parameter updates.

sample_index_source_inventory_count: `{manifest["sample_index_source_inventory_count"]}`
sample_index_schema_field_count: `{manifest["sample_index_schema_field_count"]}`
sample_index_field_mapping_count: `{manifest["sample_index_field_mapping_count"]}`
sample_index_materialization_plan_count: `{manifest["sample_index_materialization_plan_count"]}`
eligible_for_sample_index_materialization_count: `{manifest["eligible_for_sample_index_materialization_count"]}`
sample_index_written_current_step: `{manifest["sample_index_written_current_step"]}`
ready_for_covapie_sample_index_materialization_smoke: `{manifest["ready_for_covapie_sample_index_materialization_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design_gate.run_covapie_sample_index_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["source_rows"], design_gate.SOURCE_INVENTORY_CSV, design_gate.SOURCE_INVENTORY_COLUMNS)
    write_json(result["source_rows"], design_gate.SOURCE_INVENTORY_JSON)
    write_csv(result["schema_rows"], design_gate.SCHEMA_CONTRACT_CSV, design_gate.SCHEMA_COLUMNS)
    write_csv(result["mapping_rows"], design_gate.FIELD_MAPPING_CSV, design_gate.FIELD_MAPPING_COLUMNS)
    write_csv(result["plan_rows"], design_gate.MATERIALIZATION_PLAN_CSV, design_gate.MATERIALIZATION_PLAN_COLUMNS)
    write_csv(result["policy_rows"], design_gate.POLICY_CONTRACT_CSV, design_gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], design_gate.DOWNSTREAM_READINESS_CSV, design_gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], design_gate.SAFETY_AUDIT_CSV, design_gate.SAFETY_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_sample_index_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_index_design_gate_v0_blocked")
    for key in [
        "sample_index_source_inventory_count",
        "sample_index_schema_field_count",
        "sample_index_field_mapping_count",
        "sample_index_materialization_plan_count",
        "eligible_for_sample_index_materialization_count",
        "sample_index_written_current_step",
        "ready_for_covapie_sample_index_materialization_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "feature_semantics_known_for_training",
        "unknown_atom_feature_policy_finalized_for_training",
        "feature_semantics_audit_required_before_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

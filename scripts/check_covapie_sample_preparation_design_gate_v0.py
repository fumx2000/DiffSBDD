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

from covalent_ext import covapie_sample_preparation_design_gate as gate  # noqa: E402


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
    blocked = ", ".join(manifest["blocked_pdb_het_pairs"])
    text = f"""# CovaPIE Sample Preparation Design Gate v0 Summary

Step 14Z designs the next sample preparation execution smoke for the three Step 14Y small pilot ready candidates.

This is a design gate only. It does not read raw CIF/mmCIF, parse struct_conn or atom_site, write atom tables, create a sample index, create a final dataset, write split/leakage artifacts, run a dataloader smoke, or train.

sample_preparation_input_count: `{manifest["sample_preparation_input_count"]}`
required_artifact_plan_count: `{manifest["required_artifact_plan_count"]}`
raw_access_plan_count: `{manifest["raw_access_plan_count"]}`
ready_for_sample_preparation_execution_smoke_count: `{manifest["ready_for_sample_preparation_execution_smoke_count"]}`
ready_for_training_candidate_count_current_step: `{manifest["ready_for_training_candidate_count_current_step"]}`
accepted_pdb_het_pairs: `{accepted}`
blocked_pdb_het_pairs: `{blocked}`
ready_for_covapie_sample_preparation_execution_smoke: `{manifest["ready_for_covapie_sample_preparation_execution_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_sample_preparation_design_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["input_rows"], gate.INPUT_MANIFEST_CSV, gate.INPUT_MANIFEST_COLUMNS)
    write_json(result["input_rows"], gate.INPUT_MANIFEST_JSON)
    write_csv(result["artifact_rows"], gate.REQUIRED_ARTIFACT_PLAN_CSV, gate.REQUIRED_ARTIFACT_COLUMNS)
    write_csv(result["raw_rows"], gate.RAW_ACCESS_PLAN_CSV, gate.RAW_ACCESS_COLUMNS)
    write_csv(result["schema_rows"], gate.SCHEMA_CONTRACT_CSV, gate.SCHEMA_CONTRACT_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_CONTRACT_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CSV, gate.DOWNSTREAM_READINESS_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_AUDIT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_sample_preparation_design_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_preparation_design_gate_v0_blocked")
    for key in [
        "sample_preparation_input_count",
        "required_artifact_plan_count",
        "raw_access_plan_count",
        "ready_for_sample_preparation_execution_smoke_count",
        "ready_for_training_candidate_count_current_step",
        "accepted_pdb_het_pairs",
        "blocked_pdb_het_pairs",
        "ready_for_covapie_sample_preparation_execution_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_next_batch_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Targeted Metadata Expansion Next Batch Gate v0 Summary

Step 14M plans the next batch of CYS/SG ligand covalent metadata acquisition. It reads Step 14L/14K/14J artifacts only, writes design contracts and a future acquisition manifest, and does not use network access, download files, read raw CIF content, write raw files, create ready candidates, create sample/final/split/leakage artifacts, instantiate dataloaders, or train.

current_candidate_count: `{manifest["current_candidate_count"]}`
total_candidate_target: `{manifest["total_candidate_target"]}`
additional_candidate_needed_count: `{manifest["additional_candidate_needed_count"]}`
next_batch_source_strategy_row_count: `{manifest["next_batch_source_strategy_row_count"]}`
next_batch_acquisition_manifest_row_count: `{manifest["next_batch_acquisition_manifest_row_count"]}`
ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke: `{manifest["ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

The existing nine candidates remain pending manual review and are not ready candidates. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["existing_rows"], gate.EXISTING_CANDIDATE_AUDIT_CSV, gate.EXISTING_COLUMNS)
    write_csv(result["strategy_rows"], gate.SOURCE_STRATEGY_CONTRACT_CSV, gate.STRATEGY_COLUMNS)
    write_csv(result["exclusion_rows"], gate.EXCLUSION_REGISTRY_CSV, gate.EXCLUSION_COLUMNS)
    write_csv(result["next_batch_rows"], gate.NEXT_BATCH_ACQUISITION_MANIFEST_CSV, gate.NEXT_BATCH_COLUMNS)
    write_json(result["next_batch_rows"], gate.NEXT_BATCH_ACQUISITION_MANIFEST_JSON)
    write_csv(result["threshold_rows"], gate.THRESHOLD_CONTRACT_CSV, gate.THRESHOLD_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate_v0_blocked")
    for key in [
        "input_acquired_annotation_candidate_count",
        "existing_candidate_exclusion_registry_count",
        "current_candidate_count",
        "total_candidate_target",
        "additional_candidate_needed_count",
        "next_batch_minimum_new_candidate_target",
        "next_batch_source_strategy_row_count",
        "next_batch_acquisition_manifest_row_count",
        "next_batch_acquisition_manifest_csv_json_consistent",
        "ready_for_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_cys_sg_targeted_metadata_expansion_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Targeted Metadata Expansion Gate v0 Summary

Step 14K defines event-level field sources and a future targeted annotation acquisition manifest. It does not use network access, download files, read raw CIF content, create ready candidates, create sample/final/split/leakage artifacts, instantiate a dataloader, or train.

seed_candidate_count: `{manifest["seed_candidate_count"]}`
source_registry_row_count: `{manifest["source_registry_row_count"]}`
acquisition_manifest_row_count: `{manifest["acquisition_manifest_row_count"]}`
ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke: `{manifest["ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_cys_sg_targeted_metadata_expansion_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["field_rows"], gate.FIELD_SOURCE_CONTRACT_CSV, gate.FIELD_SOURCE_COLUMNS)
    write_csv(result["seed_rows"], gate.SEED_CANDIDATE_AUDIT_CSV, gate.SEED_COLUMNS)
    write_csv(result["registry_rows"], gate.SOURCE_REGISTRY_CSV, gate.SOURCE_REGISTRY_COLUMNS)
    write_csv(result["acquisition_rows"], gate.ACQUISITION_MANIFEST_CSV, gate.ACQUISITION_MANIFEST_COLUMNS)
    write_json(result["acquisition_rows"], gate.ACQUISITION_MANIFEST_JSON)
    write_csv(result["stop_rows"], gate.STOP_CONDITION_CONTRACT_CSV, gate.STOP_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_targeted_metadata_expansion_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_targeted_metadata_expansion_gate_v0_blocked")
    for key in ["input_annotation_alignment_candidate_count", "seed_candidate_count", "source_registry_row_count", "acquisition_manifest_row_count", "acquisition_manifest_csv_json_consistent", "ready_for_covapie_cys_sg_targeted_annotation_acquisition_smoke", "ready_for_training", "recommended_next_step", "blocking_reasons"]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

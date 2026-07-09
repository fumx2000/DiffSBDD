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

from covalent_ext import covapie_cys_sg_targeted_annotation_acquisition_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Targeted Annotation Acquisition Smoke v0 Summary

Step 14L performs a controlled metadata-only annotation acquisition smoke from CovPDB ligand/complex pages and the RCSB Chemical Component Dictionary. It does not download raw coordinate files, read raw CIF content, write raw files, save HTML, create ready candidates, create sample/final/split/leakage artifacts, instantiate dataloaders, or train.

input_seed_candidate_count: `{manifest["input_seed_candidate_count"]}`
input_acquisition_manifest_row_count: `{manifest["input_acquisition_manifest_row_count"]}`
ligand_card_fetch_success_count: `{manifest["ligand_card_fetch_success_count"]}`
complex_card_resolved_count: `{manifest["complex_card_resolved_count"]}`
complex_card_event_annotation_acquired_count: `{manifest["complex_card_event_annotation_acquired_count"]}`
rcsb_ccd_fetch_success_count: `{manifest["rcsb_ccd_fetch_success_count"]}`
acquired_annotation_candidate_count: `{manifest["acquired_annotation_candidate_count"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

All acquired annotation candidates remain pending manual review and are not event identities until review. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = smoke.run_covapie_cys_sg_targeted_annotation_acquisition_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["execution_rows"], smoke.EXECUTION_AUDIT_CSV, smoke.EXECUTION_COLUMNS)
    write_csv(result["ligand_rows"], smoke.LIGAND_CARD_AUDIT_CSV, smoke.LIGAND_COLUMNS)
    write_csv(result["complex_rows"], smoke.COMPLEX_CARD_AUDIT_CSV, smoke.COMPLEX_COLUMNS)
    write_csv(result["ccd_rows"], smoke.RCSB_CCD_AUDIT_CSV, smoke.CCD_COLUMNS)
    write_csv(result["acquired_rows"], smoke.ACQUIRED_CANDIDATES_CSV, smoke.ACQUIRED_COLUMNS)
    write_json(result["acquired_rows"], smoke.ACQUIRED_CANDIDATES_JSON)
    write_csv(result["gap_rows"], smoke.GAP_AUDIT_CSV, smoke.GAP_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_targeted_annotation_acquisition_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_targeted_annotation_acquisition_smoke_v0_blocked")
    for key in [
        "input_seed_candidate_count",
        "input_acquisition_manifest_row_count",
        "ligand_card_fetch_success_count",
        "complex_card_resolved_count",
        "complex_card_event_annotation_acquired_count",
        "rcsb_ccd_fetch_success_count",
        "acquired_annotation_candidate_count",
        "partial_annotation_count",
        "failed_annotation_count",
        "ready_candidate_count_current_step",
        "ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate",
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_next_batch_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

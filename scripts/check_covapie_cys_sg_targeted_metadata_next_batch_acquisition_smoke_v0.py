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

from covalent_ext import covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Targeted Metadata Next Batch Acquisition Smoke v0 Summary

Step 14N performs a controlled metadata-only next-batch acquisition smoke from CovPDB HTML annotation pages and RCSB CCD metadata. It excludes the existing nine Step 14L acquired annotation candidates, writes only derived CSV/JSON/MD metadata artifacts, and does not save raw coordinates, HTML files, candidate-ready labels, sample indexes, final datasets, split/leakage artifacts, dataloader artifacts, checkpoints, tensors, or training outputs.

CovPDB optional ligand/protein name fields are cleaned when page navigation boilerplate is detected. The RCSB CCD `ccd_ligand_name` field remains the reliable ligand chemical name source in this smoke.

existing_candidate_count: `{manifest["existing_candidate_count"]}`
total_candidate_target: `{manifest["total_candidate_target"]}`
additional_candidate_needed_before_step: `{manifest["additional_candidate_needed_before_step"]}`
complex_card_fetch_attempt_count: `{manifest["complex_card_fetch_attempt_count"]}`
complex_card_fetch_success_count: `{manifest["complex_card_fetch_success_count"]}`
complex_card_cys_event_annotation_count: `{manifest["complex_card_cys_event_annotation_count"]}`
new_candidate_count: `{manifest["new_candidate_count"]}`
combined_candidate_count: `{manifest["combined_candidate_count"]}`
additional_candidate_needed_after_step: `{manifest["additional_candidate_needed_after_step"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate: `{manifest["ready_for_covapie_cys_sg_acquired_annotation_manual_review_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

All next-batch acquired annotation candidates remain pending manual review and are not event identities until review. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = smoke.run_covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["source_discovery_rows"], smoke.SOURCE_DISCOVERY_AUDIT_CSV, smoke.SOURCE_DISCOVERY_COLUMNS)
    write_csv(result["acquisition_execution_rows"], smoke.ACQUISITION_EXECUTION_AUDIT_CSV, smoke.ACQUISITION_EXECUTION_COLUMNS)
    write_csv(result["complex_extraction_rows"], smoke.COMPLEX_EXTRACTION_AUDIT_CSV, smoke.COMPLEX_EXTRACTION_COLUMNS)
    write_csv(result["rcsb_ccd_rows"], smoke.RCSB_CCD_EXTRACTION_AUDIT_CSV, smoke.RCSB_CCD_COLUMNS)
    write_csv(result["candidate_rows"], smoke.ACQUIRED_CANDIDATES_CSV, smoke.ACQUIRED_COLUMNS)
    write_json(result["candidate_rows"], smoke.ACQUIRED_CANDIDATES_JSON)
    write_csv(result["threshold_gap_rows"], smoke.THRESHOLD_GAP_AUDIT_CSV, smoke.THRESHOLD_GAP_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke_v0_blocked")
    for key in [
        "existing_candidate_count",
        "total_candidate_target",
        "additional_candidate_needed_before_step",
        "complex_card_fetch_attempt_count",
        "complex_card_fetch_success_count",
        "complex_card_cys_event_annotation_count",
        "duplicate_existing_candidate_count",
        "new_candidate_count",
        "combined_candidate_count",
        "additional_candidate_needed_after_step",
        "rcsb_ccd_fetch_success_count",
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

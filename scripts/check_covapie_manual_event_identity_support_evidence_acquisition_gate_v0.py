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

from covalent_ext import covapie_manual_event_identity_support_evidence_acquisition_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Manual Event Identity Support Evidence Acquisition Gate v0 Summary

Step 14F reads existing local CIF/mmCIF evidence, if present, to propose event-level identity support for the Step 14E pending manual curation template.
It does not modify the template, mark proposals ready, use PDB-only joins, download files, write raw structures, write a download manifest, write actual dataloader smoke, or train.

template_candidate_count: `{manifest["template_candidate_count"]}`
local_raw_available_count: `{manifest["local_raw_available_count"]}`
local_raw_read_count: `{manifest["local_raw_read_count"]}`
struct_conn_rows_detected_count: `{manifest["struct_conn_rows_detected_count"]}`
cys_sg_struct_conn_candidate_count: `{manifest["cys_sg_struct_conn_candidate_count"]}`
support_proposal_count: `{manifest["support_proposal_count"]}`
support_proposals_all_pending_manual_review: `{manifest["support_proposals_all_pending_manual_review"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
ready_for_covapie_manual_event_identity_support_review_gate: `{manifest["ready_for_covapie_manual_event_identity_support_review_gate"]}`
ready_for_covapie_small_pilot_manual_event_identity_validation_gate: `{manifest["ready_for_covapie_small_pilot_manual_event_identity_validation_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_manual_event_identity_support_evidence_acquisition_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["input_template_rows"], gate.INPUT_TEMPLATE_AUDIT_CSV, gate.INPUT_TEMPLATE_AUDIT_COLUMNS)
    write_csv(result["source_inventory_rows"], gate.SOURCE_INVENTORY_CSV, gate.SOURCE_INVENTORY_COLUMNS)
    write_csv(result["raw_rows"], gate.LOCAL_RAW_AVAILABILITY_AUDIT_CSV, gate.LOCAL_RAW_COLUMNS)
    write_csv(result["struct_conn_rows"], gate.STRUCT_CONN_PROPOSAL_AUDIT_CSV, gate.STRUCT_CONN_AUDIT_COLUMNS)
    write_csv(result["proposals"], gate.SUPPORT_PROPOSALS_CSV, gate.SUPPORT_PROPOSAL_COLUMNS)
    write_json(result["proposals"], gate.SUPPORT_PROPOSALS_JSON)
    write_csv(result["validation_rows"], gate.PROPOSAL_VALIDATION_AUDIT_CSV, gate.VALIDATION_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_manual_event_identity_support_evidence_acquisition_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_manual_event_identity_support_evidence_acquisition_gate_v0_blocked")
    for key in [
        "template_candidate_count",
        "local_raw_available_count",
        "local_raw_read_count",
        "struct_conn_rows_detected_count",
        "cys_sg_struct_conn_candidate_count",
        "support_proposal_count",
        "support_proposals_csv_json_consistent",
        "support_proposals_all_pending_manual_review",
        "ready_candidate_count_current_step",
        "no_ready_candidates_created",
        "raw_file_content_read_current_step",
        "mmcif_text_read",
        "mmcif_struct_conn_parse_current_step",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "ready_for_covapie_manual_event_identity_support_review_gate",
        "ready_for_covapie_small_pilot_manual_event_identity_validation_gate",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

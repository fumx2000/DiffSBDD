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

from covalent_ext import covapie_cys_sg_discovery_download_smoke as smoke  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Discovery Download Smoke v0 Summary

Step 14H downloads raw CIF files only for CYS/SG evidence discovery and parses `_struct_conn` with the Python standard library.
PDB IDs are used only as raw evidence fetch keys, never as event identity. Proposals remain pending manual review and no ready candidates, sample manifest, dataloader artifact, or training artifact is created.

download_success_count: `{manifest["download_success_count"]}`
download_failure_count: `{manifest["download_failure_count"]}`
struct_conn_rows_detected_count: `{manifest["struct_conn_rows_detected_count"]}`
cys_sg_struct_conn_candidate_count: `{manifest["cys_sg_struct_conn_candidate_count"]}`
support_proposal_count: `{manifest["support_proposal_count"]}`
ready_for_covapie_cys_sg_discovery_support_review_gate: `{manifest["ready_for_covapie_cys_sg_discovery_support_review_gate"]}`
ready_for_covapie_cys_sg_targeted_metadata_expansion_gate: `{manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Raw CIF files are intentionally left untracked and uncommitted. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_cys_sg_discovery_download_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["execution_rows"], smoke.DOWNLOAD_EXECUTION_AUDIT_CSV, smoke.DOWNLOAD_EXECUTION_COLUMNS)
    write_csv(result["status_rows"], smoke.DOWNLOAD_STATUS_MANIFEST_CSV, smoke.DOWNLOAD_STATUS_COLUMNS)
    write_json(result["status_rows"], smoke.DOWNLOAD_STATUS_MANIFEST_JSON)
    write_csv(result["struct_conn_rows"], smoke.STRUCT_CONN_DISCOVERY_AUDIT_CSV, smoke.STRUCT_CONN_AUDIT_COLUMNS)
    write_csv(result["proposals"], smoke.EVENT_PROPOSALS_CSV, smoke.EVENT_PROPOSAL_COLUMNS)
    write_json(result["proposals"], smoke.EVENT_PROPOSALS_JSON)
    write_csv(result["readiness_rows"], smoke.STOP_DECISION_READINESS_AUDIT_CSV, smoke.READINESS_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_cys_sg_discovery_download_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_discovery_download_smoke_v0_blocked")
    for key in [
        "discovery_manifest_row_count",
        "download_attempted",
        "network_access_used",
        "download_success_count",
        "download_failure_count",
        "raw_files_written_current_step",
        "raw_files_tracked",
        "raw_files_staged",
        "temp_part_files_remaining_count",
        "struct_conn_parse_attempt_count",
        "struct_conn_parse_success_count",
        "struct_conn_rows_detected_count",
        "cys_sg_struct_conn_candidate_count",
        "support_proposal_count",
        "support_proposals_all_pending_manual_review",
        "ready_candidate_count_current_step",
        "pdb_id_used_as_event_identity",
        "ready_for_covapie_cys_sg_discovery_support_review_gate",
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

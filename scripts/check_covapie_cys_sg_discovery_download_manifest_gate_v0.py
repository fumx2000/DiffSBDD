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

from covalent_ext import covapie_cys_sg_discovery_download_manifest_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Discovery Download Manifest Gate v0 Summary

Step 14G writes a discovery-only raw structure download manifest for the Step 14E pending candidates.
PDB ID remains forbidden for event-level identity or training sample joins; it is only allowed here as a future raw evidence fetch key.
This step does not download, write raw files, parse raw files, create ready candidates, write sample manifests, write dataloader smoke, or train.

discovery_manifest_row_count: `{manifest["discovery_manifest_row_count"]}`
purpose: `{manifest["purpose"]}`
pdb_id_for_raw_evidence_discovery_allowed: `{manifest["pdb_id_for_raw_evidence_discovery_allowed"]}`
pdb_id_for_event_identity_allowed: `{manifest["pdb_id_for_event_identity_allowed"]}`
ready_for_covapie_cys_sg_discovery_download_smoke: `{manifest["ready_for_covapie_cys_sg_discovery_download_smoke"]}`
ready_for_covapie_small_pilot_download_smoke: `{manifest["ready_for_covapie_small_pilot_download_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_cys_sg_discovery_download_manifest_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_EXCEPTION_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["candidate_rows"], gate.CANDIDATE_SOURCE_AUDIT_CSV, gate.CANDIDATE_SOURCE_COLUMNS)
    write_csv(result["discovery_rows"], gate.DISCOVERY_MANIFEST_CSV, gate.DISCOVERY_MANIFEST_COLUMNS)
    write_json(result["discovery_rows"], gate.DISCOVERY_MANIFEST_JSON)
    write_csv(result["schema_rows"], gate.MANIFEST_SCHEMA_AUDIT_CSV, gate.SCHEMA_AUDIT_COLUMNS)
    write_csv(result["stop_rows"], gate.STOP_CONDITION_CONTRACT_CSV, gate.STOP_CONDITION_COLUMNS)
    write_csv(result["readiness_rows"], gate.READINESS_CONTRACT_CSV, gate.READINESS_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_cys_sg_discovery_download_manifest_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_discovery_download_manifest_gate_v0_blocked")
    for key in [
        "discovery_manifest_row_count",
        "purpose",
        "pdb_id_for_raw_evidence_discovery_allowed",
        "pdb_id_for_event_identity_allowed",
        "ready_candidate_count_current_step",
        "ready_for_covapie_cys_sg_discovery_download_smoke",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_training",
        "network_access_used",
        "download_attempted",
        "raw_files_written_current_step",
        "download_manifest_is_discovery_only",
        "sample_download_manifest_written",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

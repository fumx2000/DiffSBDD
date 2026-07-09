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

from covalent_ext import covapie_small_pilot_candidate_expansion_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Small Pilot Candidate Expansion Gate v0 Summary

Step 14D expands candidates for the current `{manifest["current_source_profile"]}` / `{manifest["current_source_database"]}` source profile using only existing derived evidence.
It does not use PDB-only joins, fabricate event-level identity, auto-restore ligand topology, use the network, download files, write raw structures, read raw content, parse mmCIF, extract coordinates, write a new download manifest, write actual dataloader smoke, or train.

selected_for_manifest_rerun_count: `{manifest["selected_for_manifest_rerun_count"]}`
insufficient_candidate_count_for_20_to_50_pilot: `{manifest["insufficient_candidate_count_for_20_to_50_pilot"]}`
pdb_only_join_used: `{manifest["pdb_only_join_used"]}`
ready_for_covapie_small_pilot_download_manifest_rerun_gate: `{manifest["ready_for_covapie_small_pilot_download_manifest_rerun_gate"]}`
ready_for_covapie_small_pilot_manual_event_identity_curation_gate: `{manifest["ready_for_covapie_small_pilot_manual_event_identity_curation_gate"]}`
ready_for_covapie_small_pilot_download_smoke: `{manifest["ready_for_covapie_small_pilot_download_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_small_pilot_candidate_expansion_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["inventory_rows"], gate.EVIDENCE_SOURCE_INVENTORY_CSV, gate.EVIDENCE_SOURCE_COLUMNS)
    write_csv(result["mapping_rows"], gate.EVENT_IDENTITY_MAPPING_CONTRACT_CSV, gate.EVENT_IDENTITY_MAPPING_COLUMNS)
    write_csv(result["expansion_rows"], gate.CANDIDATE_EXPANSION_AUDIT_CSV, gate.CANDIDATE_EXPANSION_AUDIT_COLUMNS)
    write_csv(result["expanded_rows"], gate.EXPANDED_EVENT_CANDIDATES_CSV, gate.EXPANDED_CANDIDATE_COLUMNS)
    write_json(result["expanded_rows"], gate.EXPANDED_EVENT_CANDIDATES_JSON)
    write_csv(result["gap_rows"], gate.CANDIDATE_GAP_TAXONOMY_CSV, gate.GAP_TAXONOMY_COLUMNS)
    write_csv(result["readiness_rows"], gate.READINESS_CONTRACT_CSV, gate.READINESS_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_small_pilot_candidate_expansion_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_small_pilot_candidate_expansion_gate_v0_blocked")
    for key in [
        "current_source_profile",
        "current_source_database",
        "evidence_source_inventory_row_count",
        "evidence_source_inventory_passed",
        "event_identity_mapping_contract_row_count",
        "event_identity_mapping_contract_passed",
        "candidate_expansion_audit_row_count",
        "candidate_expansion_audit_passed",
        "expanded_event_candidates_row_count",
        "expanded_event_candidates_csv_json_consistent",
        "selected_for_manifest_rerun_count",
        "insufficient_candidate_count_for_20_to_50_pilot",
        "pdb_only_join_used",
        "pdb_only_join_blocked",
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate",
        "ready_for_covapie_small_pilot_manual_event_identity_curation_gate",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_small_pilot_manual_event_identity_curation_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Small Pilot Manual Event Identity Curation Gate v0 Summary

Step 14E creates a manual event identity curation template for the `{manifest["current_source_profile"]}` / `{manifest["current_source_database"]}` source profile.
It does not fill real answers, use PDB-only joins, expand beyond CYS/SG V1 scope, use the network, download files, write raw structures, write a new download manifest, write actual dataloader smoke, or train.

manual_curation_template_row_count: `{manifest["manual_curation_template_row_count"]}`
selected_for_manual_curation_count: `{manifest["selected_for_manual_curation_count"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
manual_review_status_all_pending: `{manifest["manual_review_status_all_pending"]}`
ready_for_covapie_small_pilot_manual_event_identity_validation_gate: `{manifest["ready_for_covapie_small_pilot_manual_event_identity_validation_gate"]}`
ready_for_covapie_small_pilot_download_manifest_rerun_gate: `{manifest["ready_for_covapie_small_pilot_download_manifest_rerun_gate"]}`
ready_for_covapie_small_pilot_download_smoke: `{manifest["ready_for_covapie_small_pilot_download_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Pending template rows are not ready candidates. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_small_pilot_manual_event_identity_curation_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["field_rows"], gate.FIELD_CONTRACT_CSV, gate.FIELD_CONTRACT_COLUMNS)
    write_csv(result["template_rows"], gate.CURATION_TEMPLATE_CSV, gate.CURATION_TEMPLATE_COLUMNS)
    write_json(result["template_rows"], gate.CURATION_TEMPLATE_JSON)
    write_csv(result["instruction_rows"], gate.INSTRUCTION_SHEET_CSV, gate.INSTRUCTION_COLUMNS)
    write_csv(result["evidence_rows"], gate.REQUIRED_EVIDENCE_CONTRACT_CSV, gate.EVIDENCE_COLUMNS)
    write_csv(result["v1_scope_rows"], gate.V1_SCOPE_CONTRACT_CSV, gate.V1_SCOPE_COLUMNS)
    write_csv(result["readiness_rows"], gate.READINESS_CONTRACT_CSV, gate.READINESS_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_small_pilot_manual_event_identity_curation_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_small_pilot_manual_event_identity_curation_gate_v0_blocked")
    for key in [
        "current_source_profile",
        "current_source_database",
        "manual_curation_template_row_count",
        "selected_for_manual_curation_count",
        "ready_candidate_count_current_step",
        "field_contract_row_count",
        "field_contract_passed",
        "instruction_sheet_row_count",
        "instruction_sheet_passed",
        "required_evidence_contract_row_count",
        "required_evidence_contract_passed",
        "v1_scope_contract_row_count",
        "v1_scope_contract_passed",
        "readiness_contract_row_count",
        "readiness_contract_passed",
        "safety_audit_passed",
        "manual_review_status_all_pending",
        "ready_for_covapie_small_pilot_manual_event_identity_validation_gate",
        "ready_for_covapie_small_pilot_download_manifest_rerun_gate",
        "ready_for_covapie_small_pilot_download_smoke",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

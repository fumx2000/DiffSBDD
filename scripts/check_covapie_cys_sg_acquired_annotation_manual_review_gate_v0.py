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

from covalent_ext import covapie_cys_sg_acquired_annotation_manual_review_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Acquired Annotation Manual Review Gate v0 Summary

Step 14O prepares a manual review packet for the combined Step 14L and Step 14N acquired annotation candidates. It writes a combined inventory, event identity audit, criteria contract, decision template, auto-flag audit, downstream readiness contract, safety audit, and manifest.

This step does not make manual decisions, does not accept or reject candidates, does not create ready candidates, does not read raw CIF/mmCIF/SDF/PDB content, does not use network access, does not write sample/final/split/leakage artifacts, and does not train.

step14l_input_candidate_count: `{manifest["step14l_input_candidate_count"]}`
step14n_input_candidate_count: `{manifest["step14n_input_candidate_count"]}`
combined_manual_review_candidate_count: `{manifest["combined_manual_review_candidate_count"]}`
manual_review_template_row_count: `{manifest["manual_review_template_row_count"]}`
pending_manual_review_count: `{manifest["pending_manual_review_count"]}`
accepted_candidate_count_current_step: `{manifest["accepted_candidate_count_current_step"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
step14n_requires_future_struct_conn_crosscheck_count: `{manifest["step14n_requires_future_struct_conn_crosscheck_count"]}`
ready_for_manual_review_input_by_user: `{manifest["ready_for_manual_review_input_by_user"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

The next action is user/manual curator input into the decision template. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_cys_sg_acquired_annotation_manual_review_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["inventory_rows"], gate.COMBINED_INVENTORY_CSV, gate.INVENTORY_COLUMNS)
    write_csv(result["event_identity_rows"], gate.EVENT_IDENTITY_AUDIT_CSV, gate.EVENT_IDENTITY_COLUMNS)
    write_csv(result["criteria_rows"], gate.CRITERIA_CONTRACT_CSV, gate.CRITERIA_COLUMNS)
    write_csv(result["decision_rows"], gate.DECISION_TEMPLATE_CSV, gate.DECISION_TEMPLATE_COLUMNS)
    write_json(result["decision_rows"], gate.DECISION_TEMPLATE_JSON)
    write_csv(result["auto_flag_rows"], gate.AUTO_FLAG_AUDIT_CSV, gate.AUTO_FLAG_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_acquired_annotation_manual_review_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_acquired_annotation_manual_review_gate_v0_blocked")
    for key in [
        "step14l_input_candidate_count",
        "step14n_input_candidate_count",
        "combined_manual_review_candidate_count",
        "threshold_20_met",
        "manual_review_template_row_count",
        "pending_manual_review_count",
        "accepted_candidate_count_current_step",
        "ready_candidate_count_current_step",
        "step14n_requires_future_struct_conn_crosscheck_count",
        "duplicate_candidate_count",
        "ready_for_manual_review_input_by_user",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

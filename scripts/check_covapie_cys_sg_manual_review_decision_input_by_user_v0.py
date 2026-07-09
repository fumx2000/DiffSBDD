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

from covalent_ext import covapie_cys_sg_manual_review_decision_input_by_user as decision_input  # noqa: E402


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
    accepted = ", ".join(manifest["accepted_pdb_het_pairs"])
    text = f"""# CovaPIE CYS/SG Manual Review Decision Input By User v0 Summary

Step 14P records user-supplied manual review decision input. It copies the Step 14O decision template into a new decision input artifact and marks only the five user-selected Step 14N rows as `accept_for_future_struct_conn_crosscheck`.

This step does not modify Step 14O artifacts, does not create ready candidates, does not run raw/mmCIF struct_conn cross-check, does not use network access, does not write sample/final/split/leakage artifacts, and does not train.

input_manual_review_candidate_count: `{manifest["input_manual_review_candidate_count"]}`
accepted_for_future_struct_conn_crosscheck_count: `{manifest["accepted_for_future_struct_conn_crosscheck_count"]}`
pending_manual_review_count: `{manifest["pending_manual_review_count"]}`
rejected_candidate_count_current_step: `{manifest["rejected_candidate_count_current_step"]}`
needs_more_evidence_count_current_step: `{manifest["needs_more_evidence_count_current_step"]}`
ready_candidate_count_current_step: `{manifest["ready_candidate_count_current_step"]}`
accepted_pdb_het_pairs: `{accepted}`
ready_for_covapie_cys_sg_manual_review_decision_application_gate: `{manifest["ready_for_covapie_cys_sg_manual_review_decision_application_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Accepted for future struct_conn cross-check is not a ready-candidate label. Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = decision_input.run_covapie_cys_sg_manual_review_decision_input_by_user_v0()
    write_csv(result["precondition_rows"], decision_input.PRECONDITION_AUDIT_CSV, decision_input.PRECONDITION_COLUMNS)
    write_csv(result["decision_rows"], decision_input.DECISION_INPUT_CSV, decision_input.DECISION_INPUT_COLUMNS)
    write_json(result["decision_rows"], decision_input.DECISION_INPUT_JSON)
    write_csv(result["diff_rows"], decision_input.DECISION_DIFF_AUDIT_CSV, decision_input.DIFF_AUDIT_COLUMNS)
    write_csv(result["policy_rows"], decision_input.POLICY_CONTRACT_CSV, decision_input.POLICY_COLUMNS)
    write_csv(result["accepted_rows"], decision_input.ACCEPTED_CROSSCHECK_MANIFEST_CSV, decision_input.ACCEPTED_MANIFEST_COLUMNS)
    write_json(result["accepted_rows"], decision_input.ACCEPTED_CROSSCHECK_MANIFEST_JSON)
    write_csv(result["downstream_rows"], decision_input.DOWNSTREAM_READINESS_CONTRACT_CSV, decision_input.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], decision_input.SAFETY_AUDIT_CSV, decision_input.SAFETY_COLUMNS)
    write_json(result["manifest"], decision_input.MANIFEST_JSON)
    write_summary(result["manifest"], decision_input.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_manual_review_decision_input_by_user_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_manual_review_decision_input_by_user_v0_blocked")
    for key in [
        "input_manual_review_candidate_count",
        "accepted_for_future_struct_conn_crosscheck_count",
        "pending_manual_review_count",
        "rejected_candidate_count_current_step",
        "needs_more_evidence_count_current_step",
        "ready_candidate_count_current_step",
        "ready_for_training_candidate_count_current_step",
        "accepted_candidate_ids",
        "accepted_pdb_het_pairs",
        "accepted_crosscheck_manifest_row_count",
        "ready_for_covapie_cys_sg_manual_review_decision_application_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

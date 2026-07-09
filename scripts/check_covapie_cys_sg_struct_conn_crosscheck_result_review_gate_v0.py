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

from covalent_ext import covapie_cys_sg_struct_conn_crosscheck_result_review_gate as gate  # noqa: E402


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
    matched = ", ".join(manifest["matched_pdb_het_pairs"])
    blocked = ", ".join(manifest["blocked_pdb_het_pairs"])
    text = f"""# CovaPIE CYS/SG Struct Conn Cross-check Result Review Gate v0 Summary

Step 14U converts the Step 14T struct_conn evidence candidates into a result review packet and carries unmatched inputs into a blocked review inventory.

This step does not automatically accept or reject evidence, does not create ready candidates, does not read raw mmCIF files, does not parse struct_conn, does not write sample/final/split/leakage/training artifacts, and does not train.

result_review_evidence_count: `{manifest["result_review_evidence_count"]}`
unmatched_blocked_count: `{manifest["unmatched_blocked_count"]}`
pending_result_review_count: `{manifest["pending_result_review_count"]}`
matched_pdb_het_pairs: `{matched}`
blocked_pdb_het_pairs: `{blocked}`
ready_for_covapie_cys_sg_result_review_decision_input_by_user: `{manifest["ready_for_covapie_cys_sg_result_review_decision_input_by_user"]}`
ready_for_covapie_cys_sg_ready_candidate_materialization_gate: `{manifest["ready_for_covapie_cys_sg_ready_candidate_materialization_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["evidence_inventory_rows"], gate.EVIDENCE_INVENTORY_CSV, gate.EVIDENCE_INVENTORY_COLUMNS)
    write_json(result["evidence_inventory_rows"], gate.EVIDENCE_INVENTORY_JSON)
    write_csv(result["unmatched_rows"], gate.UNMATCHED_BLOCKED_INVENTORY_CSV, gate.UNMATCHED_COLUMNS)
    write_csv(result["decision_rows"], gate.DECISION_TEMPLATE_CSV, gate.DECISION_TEMPLATE_COLUMNS)
    write_json(result["decision_rows"], gate.DECISION_TEMPLATE_JSON)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_struct_conn_crosscheck_result_review_gate_v0_blocked")
    for key in [
        "result_review_evidence_count",
        "unmatched_blocked_count",
        "pending_result_review_count",
        "matched_pdb_het_pairs",
        "blocked_pdb_het_pairs",
        "ready_for_covapie_cys_sg_result_review_decision_input_by_user",
        "ready_for_covapie_cys_sg_ready_candidate_materialization_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

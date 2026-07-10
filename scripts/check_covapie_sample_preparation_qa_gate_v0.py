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

from covalent_ext import covapie_sample_preparation_qa_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE Sample Preparation QA Gate v0 Summary

Step 14AB performs QA over Step 14AA sample preparation execution smoke outputs.

This QA gate reads derived execution outputs only. It does not read raw CIF/mmCIF, parse raw struct_conn or atom_site, modify atom tables, create a sample index, create a final dataset, write split/leakage artifacts, run a dataloader smoke, or train.

sample_qa_count: `{manifest["sample_qa_count"]}`
table_integrity_qa_count: `{manifest["table_integrity_qa_count"]}`
event_pair_qa_count: `{manifest["event_pair_qa_count"]}`
qa_issue_count: `{manifest["qa_issue_count"]}`
sample_qa_passed_count: `{manifest["sample_qa_passed_count"]}`
table_integrity_passed_count: `{manifest["table_integrity_passed_count"]}`
event_pair_qa_passed_count: `{manifest["event_pair_qa_passed_count"]}`
accepted_pdb_het_pairs: `{accepted}`
ready_for_covapie_sample_index_design_gate: `{manifest["ready_for_covapie_sample_index_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

Formal training, fine-tuning, or real parameter updates still require separate feature semantics audit and leakage/split design gates.
"""
    atomic_write_text(path, text)


def run() -> int:
    result = gate.run_covapie_sample_preparation_qa_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["sample_rows"], gate.SAMPLE_LEVEL_QA_CSV, gate.SAMPLE_LEVEL_QA_COLUMNS)
    write_json(result["sample_rows"], gate.SAMPLE_LEVEL_QA_JSON)
    write_csv(result["table_rows"], gate.TABLE_INTEGRITY_QA_CSV, gate.TABLE_INTEGRITY_QA_COLUMNS)
    write_csv(result["event_rows"], gate.EVENT_PAIR_QA_CSV, gate.EVENT_PAIR_QA_COLUMNS)
    write_csv(result["issue_rows"], gate.ISSUE_INVENTORY_CSV, gate.ISSUE_INVENTORY_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_sample_preparation_qa_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_preparation_qa_gate_v0_blocked")
    for key in [
        "sample_qa_count",
        "table_integrity_qa_count",
        "event_pair_qa_count",
        "qa_issue_count",
        "sample_qa_passed_count",
        "table_integrity_passed_count",
        "event_pair_qa_passed_count",
        "accepted_pdb_het_pairs",
        "ready_for_covapie_sample_index_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

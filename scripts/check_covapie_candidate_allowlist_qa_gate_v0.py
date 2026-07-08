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

from covalent_ext import covapie_candidate_allowlist_qa_gate as qa_gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
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
    text = f"""# CovaPIE Candidate Allowlist QA Gate v0 Summary

Step 13BC is a QA gate for the Step 13BB four-row candidate allowlist smoke artifact.
It reads but does not rewrite the materialized allowlist CSV or JSON.
It validates schema and identity, CSV/JSON consistency, traceability to Step 13BA/13AY/13AZ/13BB evidence, the unresolved `1A54/MDC` exclusion, boundary safety, git safety, and training blockers.
It does not download or read raw structure files, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, leakage matrix, or a new materialized allowlist.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.
This gate allows the batch raw read / extraction design gate next, not raw read smoke and not training.

source_allowlist_row_count: `{manifest["source_allowlist_row_count"]}`
source_allowlist_column_count: `{manifest["source_allowlist_column_count"]}`
source_allowlist_json_row_count: `{manifest["source_allowlist_json_row_count"]}`
schema_identity_qa_passed: `{manifest["schema_identity_qa_passed"]}`
csv_json_consistency_qa_passed: `{manifest["csv_json_consistency_qa_passed"]}`
traceability_qa_passed: `{manifest["traceability_qa_passed"]}`
unresolved_exclusion_qa_passed: `{manifest["unresolved_exclusion_qa_passed"]}`
candidate_allowlist_materialized_current_step: `{manifest["candidate_allowlist_materialized_current_step"]}`
ready_for_covapie_batch_scale_raw_read_design_gate: `{manifest["ready_for_covapie_batch_scale_raw_read_design_gate"]}`
ready_for_covapie_batch_scale_raw_read_smoke: `{manifest["ready_for_covapie_batch_scale_raw_read_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa_gate.run_covapie_candidate_allowlist_qa_gate_v0()
    write_csv(result["precondition_rows"], qa_gate.PRECONDITION_AUDIT_CSV, qa_gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_identity_rows"], qa_gate.SCHEMA_IDENTITY_AUDIT_CSV, qa_gate.SCHEMA_IDENTITY_COLUMNS)
    write_csv(result["csv_json_rows"], qa_gate.CSV_JSON_CONSISTENCY_AUDIT_CSV, qa_gate.CSV_JSON_COLUMNS)
    write_csv(result["traceability_rows"], qa_gate.TRACEABILITY_AUDIT_CSV, qa_gate.TRACEABILITY_COLUMNS)
    write_csv(result["unresolved_rows"], qa_gate.UNRESOLVED_EXCLUSION_AUDIT_CSV, qa_gate.UNRESOLVED_COLUMNS)
    write_csv(result["boundary_rows"], qa_gate.BOUNDARY_SAFETY_CSV, qa_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], qa_gate.GIT_SAFETY_CSV, qa_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], qa_gate.TRAINING_BLOCKERS_CSV, qa_gate.TRAINING_BLOCKERS_COLUMNS)
    write_json(result["manifest"], qa_gate.MANIFEST_JSON)
    write_summary(result["manifest"], qa_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_allowlist_qa_gate_v0_passed")
    else:
        print("covapie_candidate_allowlist_qa_gate_v0_blocked")
    for key in [
        "source_allowlist_row_count",
        "source_allowlist_column_count",
        "source_allowlist_json_row_count",
        "schema_identity_qa_passed",
        "csv_json_consistency_qa_passed",
        "traceability_qa_passed",
        "unresolved_exclusion_qa_passed",
        "candidate_allowlist_materialized_current_step",
        "ready_for_covapie_batch_scale_raw_read_design_gate",
        "ready_for_covapie_batch_scale_raw_read_smoke",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

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

from covalent_ext import covapie_candidate_allowlist_materialization_smoke as smoke  # noqa: E402


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


def write_summary(manifest: dict[str, Any], allowlist_rows: list[dict[str, str]], path: str | Path) -> None:
    ids = "\n".join(f"- `{row['allowlist_entry_id']}`" for row in allowlist_rows)
    text = f"""# CovaPIE Candidate Allowlist Materialization Smoke v0 Summary

Step 13BB materializes a first-four candidate allowlist smoke artifact from the Step 13BA design preview.
It writes CSV/JSON allowlist smoke rows only for the four eligible entries and preserves the unresolved `1A54/MDC` exclusion.
It does not download raw data, read raw `.cif/.pdb/.mmcif/.sdf/.gz` text, use RDKit/Bio.PDB/gemmi/gzip/torch, instantiate models, compute loss, or train.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
The five canonical masks remain unchanged, including `scaffold_only / B3`.
Feature semantics audit and leakage/split design remain required before formal training, fine-tuning, or real parameter updates.

Materialized allowlist entry IDs:
{ids}

materialized_allowlist_row_count: `{manifest["materialized_allowlist_row_count"]}`
materialized_allowlist_column_count: `{manifest["materialized_allowlist_column_count"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
candidate_allowlist_materialized_current_step: `{manifest["candidate_allowlist_materialized_current_step"]}`
candidate_metadata_materialized_current_step: `{manifest["candidate_metadata_materialized_current_step"]}`
ready_for_covapie_candidate_allowlist_qa_gate: `{manifest["ready_for_covapie_candidate_allowlist_qa_gate"]}`
ready_for_covapie_batch_scale_raw_read_design_gate: `{manifest["ready_for_covapie_batch_scale_raw_read_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_candidate_allowlist_materialization_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["allowlist_rows"], smoke.ALLOWLIST_SMOKE_CSV, smoke.ALLOWLIST_FIELDS)
    write_json(result["allowlist_rows"], smoke.ALLOWLIST_SMOKE_JSON)
    write_csv(result["qa_rows"], smoke.QA_AUDIT_CSV, smoke.QA_COLUMNS)
    write_csv(result["unresolved_rows"], smoke.UNRESOLVED_EXCLUSION_AUDIT_CSV, smoke.UNRESOLVED_COLUMNS)
    write_csv(result["boundary_rows"], smoke.BOUNDARY_SAFETY_CSV, smoke.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], smoke.GIT_SAFETY_CSV, smoke.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], smoke.TRAINING_BLOCKERS_CSV, smoke.TRAINING_BLOCKERS_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], result["allowlist_rows"], smoke.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_allowlist_materialization_smoke_v0_passed")
    else:
        print("covapie_candidate_allowlist_materialization_smoke_v0_blocked")
    for key in [
        "materialized_allowlist_row_count",
        "materialized_allowlist_column_count",
        "allowlist_entry_id_unique_count",
        "unresolved_exclusion_preserved",
        "candidate_allowlist_materialized",
        "candidate_allowlist_materialized_current_step",
        "ready_for_covapie_candidate_allowlist_qa_gate",
        "ready_for_covapie_batch_scale_raw_read_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())

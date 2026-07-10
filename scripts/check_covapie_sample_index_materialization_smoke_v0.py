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

from covalent_ext import covapie_sample_index_materialization_smoke as smoke  # noqa: E402


def _csv_value(value: Any) -> Any:
    return json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value


def write_csv(rows: list[dict[str, Any]], path: str | Path, fields: list[str]) -> None:
    output = REPO_ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field, "")) for field in fields})


def write_json(value: Any, path: str | Path) -> None:
    output = REPO_ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any]) -> None:
    text = f"""# CovaPIE Sample Index Materialization Smoke v0 Summary

Step 14AD materializes a three-row `sample_index.csv` and matching `sample_index.json` from Step 14AC's validated design contracts and Step 14AA's committed derived atom/event tables. This is a structured index of prepared source artifacts, not a final dataset or training dataset.

The step does not read raw mmCIF, parse raw `struct_conn` or `atom_site`, access a network, modify source atom/event tables, create final-dataset, split, leakage, dataloader, tensor, checkpoint, or training artifacts, or modify DiffSBDD source code.

The five canonical masks remain unchanged, including `scaffold_only / B3`. Feature semantics are not known or finalized for training. A feature-semantics audit and leakage/split design gate remain required before formal training, fine-tuning, or real parameter updates.

- sample_index_row_count: `{manifest['sample_index_row_count']}`
- sample_index_schema_field_count: `{manifest['sample_index_schema_field_count']}`
- schema_validation_passed_count: `{manifest['schema_validation_passed_count']}`
- row_traceability_passed_count: `{manifest['row_traceability_passed_count']}`
- materialization_issue_count: `{manifest['materialization_issue_count']}`
- ready_for_covapie_sample_index_qa_gate: `{manifest['ready_for_covapie_sample_index_qa_gate']}`
- ready_for_training: `{manifest['ready_for_training']}`
- recommended_next_step: `{manifest['recommended_next_step']}`
"""
    output = REPO_ROOT / smoke.SUMMARY_MD
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_covapie_sample_index_materialization_smoke_v0()
    write_csv(result["precondition_rows"], smoke.PRECONDITION_AUDIT_CSV, smoke.PRECONDITION_COLUMNS)
    write_csv(result["sample_rows"], smoke.SAMPLE_INDEX_CSV, smoke.SAMPLE_INDEX_FIELDS)
    write_json(result["json_rows"], smoke.SAMPLE_INDEX_JSON)
    write_csv(result["schema_validation_rows"], smoke.SCHEMA_VALIDATION_CSV, smoke.SCHEMA_VALIDATION_COLUMNS)
    write_csv(result["traceability_rows"], smoke.ROW_TRACEABILITY_CSV, smoke.TRACEABILITY_COLUMNS)
    write_csv(result["issue_rows"], smoke.ISSUE_INVENTORY_CSV, smoke.ISSUE_COLUMNS)
    write_csv(result["policy_rows"], smoke.POLICY_CONTRACT_CSV, smoke.POLICY_COLUMNS)
    write_csv(result["downstream_rows"], smoke.DOWNSTREAM_READINESS_CSV, smoke.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], smoke.SAFETY_AUDIT_CSV, smoke.SAFETY_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"])
    manifest = result["manifest"]
    print("covapie_sample_index_materialization_smoke_v0_passed" if manifest["all_checks_passed"] else "covapie_sample_index_materialization_smoke_v0_blocked")
    for key in [
        "sample_index_row_count", "sample_index_schema_field_count", "schema_validation_passed_count",
        "row_traceability_passed_count", "materialization_issue_count",
        "ready_for_covapie_sample_index_qa_gate", "ready_for_training", "ready_to_train_now",
        "feature_semantics_known_for_training", "unknown_atom_feature_policy_finalized_for_training",
        "feature_semantics_audit_required_before_training", "recommended_next_step", "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
